"""Bell-fidelity analysis: pure Python/NumPy, no Qiskit needed.

Implements exactly the estimator of the challenge prompt

    F(Phi+) = [1 + <XX> - <YY> + <ZZ>] / 4,
    sigma_PP = sqrt((1 - <PP>^2) / N),
    sigma_F  = (1/4) sqrt(sigma_XX^2 + sigma_YY^2 + sigma_ZZ^2),
    verified  <=>  F - 2 sigma_F > 0.5,

and extends it with three things the protection / routing studies need:

* **Post-selection.** Check bits ("flags") must read 0 for a shot to be kept. The same flag
  rule is applied in all three measurement settings, so the conditional state is one and the
  same state in XX, YY and ZZ (the checks are measured before / commute with the basis
  rotation). Per-setting accepted-shot counts N_acc are used inside sigma_PP.
* **Pauli-frame correction** (measurement-based routing). The X-basis outcomes of the
  intermediate qubits flip the sign of <XX> and <YY> (a Z error on one port) and leave <ZZ>
  alone. We multiply those correlators by the parity of the frame bits: this is *exactly*
  the classical feed-forward Z correction, done in post-processing.
* **Bootstrap** confidence interval (multinomial resampling of the counts, including the
  random acceptance), as the prompt allows.

Bit convention: Qiskit prints counts with classical bit 0 on the RIGHT, so bit ``i`` of a
key is ``key.replace(" ", "")[::-1][i]``.
"""

from __future__ import annotations

import math

import numpy as np

SETTINGS = ("XX", "YY", "ZZ")


def _bits(key: str, min_len: int = 0) -> str:
    """Bit string with classical bit 0 first (reversed Qiskit key, spaces removed)."""
    b = key.replace(" ", "")[::-1]
    return b.ljust(min_len, "0")


def tally(counts, data_bits=(0, 1), flag_bits=(), frame_bits=(), use_frame=False):
    """Split counts into (total, even-parity accepted, odd-parity accepted).

    A shot is *accepted* if every flag bit is 0. Parity is that of the two data bits,
    optionally XORed with the frame bits.
    """
    need = max([*data_bits, *flag_bits, *frame_bits, 0]) + 1
    n_total = n_even = n_odd = 0
    for key, c in counts.items():
        n_total += c
        b = _bits(key, need)
        if any(b[i] != "0" for i in flag_bits):
            continue
        par = (b[data_bits[0]] == "1") ^ (b[data_bits[1]] == "1")
        if use_frame:
            for i in frame_bits:
                par ^= b[i] == "1"
        if par:
            n_odd += c
        else:
            n_even += c
    return n_total, n_even, n_odd


def correlator(n_even, n_odd):
    """(<PP>, sigma_PP) from even/odd parity counts of the accepted shots."""
    n = n_even + n_odd
    if n <= 0:
        return float("nan"), float("nan")
    corr = (n_even - n_odd) / n
    return corr, math.sqrt(max(0.0, 1.0 - corr * corr) / n)


def fidelity_from_correlators(xx, yy, zz):
    return (1.0 + xx - yy + zz) / 4.0


def evaluate(counts_by_setting, info, n_boot: int = 1000, seed: int = 0) -> dict:
    """Bell fidelity (with uncertainty, acceptance, bootstrap) from the three settings.

    Parameters
    ----------
    counts_by_setting : dict  {"XX": counts, "YY": counts, "ZZ": counts}
    info : dict with ``data_bits``, ``flag_bits``, ``frame_bits`` (see circuits.build_circuit)
    """
    data_bits = tuple(info.get("data_bits", (0, 1)))
    flag_bits = tuple(info.get("flag_bits", ()))
    frame_bits = tuple(info.get("frame_bits", ()))

    stats, corr, sig = {}, {}, {}
    for s in SETTINGS:
        stats[s] = tally(
            counts_by_setting[s], data_bits, flag_bits, frame_bits, use_frame=s in ("XX", "YY")
        )
        corr[s], sig[s] = correlator(stats[s][1], stats[s][2])

    f = fidelity_from_correlators(corr["XX"], corr["YY"], corr["ZZ"])
    sigma_f = 0.25 * math.sqrt(sum(sig[s] ** 2 for s in SETTINGS))
    n_total = sum(stats[s][0] for s in SETTINGS)
    n_acc = sum(stats[s][1] + stats[s][2] for s in SETTINGS)

    out = {
        "F": f,
        "sigma_F": sigma_f,
        "verified": bool(f - 2.0 * sigma_f > 0.5) if not math.isnan(f) else False,
        "F_minus_2sigma": f - 2.0 * sigma_f,
        "XX": corr["XX"], "YY": corr["YY"], "ZZ": corr["ZZ"],
        "sXX": sig["XX"], "sYY": sig["YY"], "sZZ": sig["ZZ"],
        "accept": n_acc / n_total if n_total else float("nan"),
        "accept_by_setting": {s: (stats[s][1] + stats[s][2]) / stats[s][0] for s in SETTINGS},
        "n_total": n_total,
        "n_acc": n_acc,
        "n_discarded": n_total - n_acc,
        "yield": (n_acc / n_total) * max(0.0, 2.0 * f - 1.0) if n_total else float("nan"),
    }

    # ---- bootstrap -------------------------------------------------------------------
    if n_boot and not math.isnan(f):
        rng = np.random.default_rng(seed)
        fb = np.zeros(n_boot)
        fb += 1.0
        sign = {"XX": +1.0, "YY": -1.0, "ZZ": +1.0}
        for s in SETTINGS:
            n_tot, ne, no = stats[s]
            n_tot_i = int(round(n_tot))
            probs = np.array([ne, no, max(n_tot - ne - no, 0)], dtype=float) / n_tot
            probs = probs / probs.sum()
            d = rng.multinomial(n_tot_i, probs, size=n_boot)
            acc = np.maximum(d[:, 0] + d[:, 1], 1)
            fb += sign[s] * (d[:, 0] - d[:, 1]) / acc
        fb /= 4.0
        out["F_boot_mean"] = float(fb.mean())
        out["F_boot_std"] = float(fb.std(ddof=1))
        out["F_lo"], out["F_hi"] = (float(x) for x in np.percentile(fb, [2.5, 97.5]))
    else:
        out["F_boot_mean"] = out["F_boot_std"] = out["F_lo"] = out["F_hi"] = float("nan")
    return out


def compare(base: dict, other: dict) -> dict:
    """Difference of two fidelity results with a z-score (independent estimates)."""
    delta = other["F"] - base["F"]
    sigma = math.sqrt(base["sigma_F"] ** 2 + other["sigma_F"] ** 2)
    z = delta / sigma if sigma > 0 else (float("inf") if delta > 0 else 0.0)
    return {"delta_F": delta, "sigma_delta": sigma, "z": z}


def calibration_summary(fs, sigmas) -> dict:
    """Do the quoted sigmas match the real scatter across independent seeds?"""
    fs = np.asarray(fs, float)
    sg = np.asarray(sigmas, float)
    std = float(fs.std(ddof=1)) if len(fs) > 1 else float("nan")
    mean_sigma = float(sg.mean())
    return {
        "n": len(fs),
        "F_mean": float(fs.mean()),
        "F_std_empirical": std,
        "sigma_analytic_mean": mean_sigma,
        "ratio": std / mean_sigma if mean_sigma > 0 else float("nan"),
    }
