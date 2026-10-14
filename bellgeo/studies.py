"""Studies that produce flat result rows (list of dicts) for tables, plots and the report."""

from __future__ import annotations

import time

import qff_basic_benchmark as qb

from . import analysis, geometry, runner

MODELS = list(qb.MODEL_NAMES)  # ["2016", "contemporary", "hyperbolic"]
CASE_IDS = {"2016": (1, 2, 3), "contemporary": (4, 5, 6), "hyperbolic": (7, 8, 9)}
ALL_SCHEMES = ["plain", "zz", "xx", "zzxx", "mbr"]

_METRIC_KEYS = ("depth", "depth_max_over_settings", "n2q", "n2q_logical", "swaps",
                "swaps_from_gate_count", "phys_qubits", "n_phys", "ancillas", "intermediates",
                "esp", "data_measured_on", "data_on_ports", "valid")
_RES_KEYS = ("F", "sigma_F", "verified", "F_minus_2sigma", "XX", "YY", "ZZ", "sXX", "sYY", "sZZ",
             "accept", "accept_by_setting", "n_total", "n_acc", "n_discarded", "yield",
             "F_boot_std", "F_lo", "F_hi", "seed_sim", "shots")


class Log:
    def __init__(self, verbose=True):
        self.t0, self.verbose = time.time(), verbose

    def __call__(self, msg):
        if self.verbose:
            print(f"[{time.time() - self.t0:7.1f}s] {msg}", flush=True)


def make_row(plan, res, mode, study, **extra):
    r = {"study": study, "model": plan.model_name, "noise_variant": plan.noise_variant,
         "scheme": plan.scheme, "mode": mode, "layout": plan.layout,
         "seed_t": plan.seed_t, "opt": plan.opt}
    r.update({k: plan.metrics[k] for k in _METRIC_KEYS})
    r.update({k: res[k] for k in _RES_KEYS})
    r.update(extra)
    return r


def run_matrix(noise, schemes, cfg, study, log, models=None):
    """Plan every (model, scheme) once; run ideal and noisy. Returns (rows, plans, models)."""
    rows, plans, loaded = [], {}, {}
    for name in models or MODELS:
        m = qb.load_model(name, noise=noise)
        loaded[name] = m
        log(f"{study}: model {name} ({noise} noise, {m.num_qubits} qubits, ports {m.ports})")
        for scheme in schemes:
            plan = runner.plan_scheme(m, scheme, cfg["seed_t"], cfg["opt"])
            plans[(name, scheme)] = plan
            for mode, backend in (("ideal", m.ideal_backend), ("noisy", m.backend)):
                res = runner.execute(plan, backend, cfg["shots"], cfg["seed_s"], cfg["n_boot"])
                rows.append(make_row(plan, res, mode, study))
            pm = plan.metrics
            noisy = rows[-1]
            log(f"   {scheme:5s} layout={plan.layout} n2q={pm['n2q']:2d} swaps={pm['swaps']} "
                f"depth={pm['depth']:3d} | noisy F={noisy['F']:.4f}±{noisy['sigma_F']:.4f} "
                f"acc={noisy['accept']:.3f} valid={pm['valid']}")
    return rows, plans, loaded


def noise_sweep(models, plans, scales, schemes, cfg, log):
    """Re-run the compiled circuits on common-noise backends with all error rates x scale."""
    rows = []
    for name, m in models.items():
        for sc in scales:
            sm = runner.scaled_model(m, sc)
            for scheme in schemes:
                plan = plans[(name, scheme)]
                res = runner.execute(plan, sm.backend, cfg["shots"], cfg["seed_s"], cfg["n_boot"])
                rows.append(make_row(plan, res, "noisy", "noise_sweep", scale=sc))
            log(f"noise sweep: {name} x{sc} done")
    return rows


def seed_validation(models, plans, schemes, n_seeds, cfg, log):
    rows = []
    for name in models:
        m = models[name]
        for scheme in schemes:
            plan = plans[(name, scheme)]
            for k in range(n_seeds):
                res = runner.execute(plan, m.backend, cfg["shots"], 1000 + 17 * k, 0)
                rows.append(make_row(plan, res, "noisy", "seed_validation", seed_index=k))
        log(f"seed validation: {name} ({n_seeds} seeds) done")
    return rows


def opt_level_study(models, log):
    """How much does the Qiskit optimisation level change the plain Bell circuit cost?"""
    rows = []
    for name, m in models.items():
        for lvl in (0, 1, 2, 3):
            plan = runner.plan_scheme(m, "plain", 1, lvl)
            rows.append({"study": "opt_levels", "model": name, "opt": lvl,
                         "n2q": plan.metrics["n2q"], "depth": plan.metrics["depth"],
                         "swaps": plan.metrics["swaps"], "valid": plan.metrics["valid"]})
        log(f"opt levels: {name}")
    return rows


def geometry_table(models):
    return {name: geometry.graph_metrics(m.edges, m.num_qubits, m.ports) for name, m in models.items()}


def select(rows, **kw):
    return [r for r in rows if all(r.get(k) == v for k, v in kw.items())]


def core_table(rows, headline):
    """The 3x3 grid (cases 1-9): ideal / noisy / noisy+headline protection."""
    out = []
    for name in MODELS:
        ideal = select(rows, study="native", model=name, scheme="plain", mode="ideal")[0]
        noisy = select(rows, study="native", model=name, scheme="plain", mode="noisy")[0]
        prot = select(rows, study="native", model=name, scheme=headline, mode="noisy")[0]
        c1, c2, c3 = CASE_IDS[name]
        out += [dict(ideal, case=c1, label="ideal"), dict(noisy, case=c2, label="noisy"),
                dict(prot, case=c3, label=f"noisy+{headline}")]
    return out


def selfcheck(rows):
    """Hard sanity checks: ideal F must be 1, all compiled circuits valid."""
    problems = []
    for r in rows:
        if r.get("mode") == "ideal" and abs(r["F"] - 1.0) > 1e-9:
            problems.append(f"ideal F != 1: {r['model']} {r['scheme']} F={r['F']}")
        if r.get("mode") == "ideal" and abs(r["accept"] - 1.0) > 1e-12:
            problems.append(f"ideal acceptance != 1: {r['model']} {r['scheme']}")
        if r.get("valid") is False:
            problems.append(f"invalid compiled circuit: {r['model']} {r['scheme']}")
    return problems
