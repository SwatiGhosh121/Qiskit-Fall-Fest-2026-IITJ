"""Tiny NumPy density-matrix simulator (<= 7 qubits) for offline logic tests.

It is NOT part of the benchmark. It exists so the circuit builders, the parity / post-selection
/ Pauli-frame logic and the uncertainty formulas can be tested without Qiskit, against exact
analytic results (e.g. a Bell state with one depolarizing CX of average error e has F = 1 - e).

Conventions follow Qiskit: qubit 0 is the least significant bit; counts keys put classical
bit 0 on the right. Noise (all optional): average-error depolarizing after every ``cx`` (e2)
and after every ``h`` (e1, standing in for one sx), symmetric readout flip. ``sdg`` and
``barrier`` are noiseless (rz is virtual on IBM hardware).
"""

from __future__ import annotations

import itertools
from functools import reduce

import numpy as np

_I = np.eye(2, dtype=complex)
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
_Z = np.array([[1, 0], [0, -1]], dtype=complex)
_H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
_SDG = np.diag([1, -1j]).astype(complex)
_P0 = np.diag([1, 0]).astype(complex)
_P1 = np.diag([0, 1]).astype(complex)
_PAULIS = [_I, _X, _Y, _Z]


class MiniCircuit:
    """Records h / sdg / cx / measure / barrier like a QuantumCircuit."""

    def __init__(self, nq, nc):
        self.nq, self.nc, self.ops = nq, nc, []

    def h(self, q): self.ops.append(("h", (q,)))
    def sdg(self, q): self.ops.append(("sdg", (q,)))
    def cx(self, c, t): self.ops.append(("cx", (c, t)))
    def barrier(self): pass
    def measure(self, q, c): self.ops.append(("measure", (q, c)))

    def num_two_qubit(self):
        return sum(1 for n, _ in self.ops if n == "cx")


def _embed(nq, ops: dict):
    mats = [ops.get(q, _I) for q in range(nq)]
    return reduce(np.kron, mats[::-1])  # qubit 0 = least significant


def _depolarize(rho, nq, qubits, e):
    """Aer-style depolarizing channel with average gate error e on ``qubits``."""
    if e <= 0:
        return rho
    k = len(qubits)
    d = 2**k
    lam = e * d / (d - 1)
    out = (1 - lam + lam / d**2) * rho
    for combo in itertools.product(range(4), repeat=k):
        if all(c == 0 for c in combo):
            continue
        p = _embed(nq, {q: _PAULIS[c] for q, c in zip(qubits, combo)})
        out = out + (lam / d**2) * (p @ rho @ p.conj().T)
    return out


def simulate(mc: MiniCircuit, e1=0.0, e2=0.0, readout=0.0):
    """Exact outcome distribution {key: prob} over the classical bits."""
    nq = mc.nq
    psi = np.zeros(2**nq, dtype=complex)
    psi[0] = 1.0
    rho = np.outer(psi, psi.conj())
    meas = []
    for name, args in mc.ops:
        if name == "measure":
            meas.append(args)
            continue
        if name in ("h", "sdg"):
            u = _embed(nq, {args[0]: _H if name == "h" else _SDG})
            rho = u @ rho @ u.conj().T
            if name == "h":
                rho = _depolarize(rho, nq, args, e1)
        elif name == "cx":
            c, t = args
            u = _embed(nq, {c: _P0}) + _embed(nq, {c: _P1, t: _X})
            rho = u @ rho @ u.conj().T
            rho = _depolarize(rho, nq, args, e2)
    p_basis = np.real(np.diag(rho))
    p_basis = np.clip(p_basis, 0, None)
    p_basis /= p_basis.sum()

    arr = np.zeros(2**mc.nc)
    for idx, p in enumerate(p_basis):
        cidx = 0
        for q, c in meas:
            cidx |= ((idx >> q) & 1) << c
        arr[cidx] += p
    ids = np.arange(2**mc.nc)
    for c in sorted({c for _, c in meas}):
        arr = (1 - readout) * arr + readout * arr[ids ^ (1 << c)]
    return {format(i, f"0{mc.nc}b"): float(p) for i, p in enumerate(arr) if p > 1e-15}


def sample_counts(probs: dict, shots: int, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    keys = list(probs)
    p = np.array([probs[k] for k in keys])
    draw = rng.multinomial(shots, p / p.sum())
    return {k: int(c) for k, c in zip(keys, draw) if c}
