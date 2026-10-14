"""Qiskit side: noise-aware layout, compilation, validity checks, execution.

Everything uses the organizers' ``ProcessorModel`` (``qff_basic_benchmark.load_model``)
unchanged: ``model.backend`` / ``model.ideal_backend`` / ``model.target`` / ``model.ports``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from qiskit import QuantumCircuit, transpile

import qff_basic_benchmark as qb

from . import analysis, geometry
from .circuits import SETTINGS_ORDER, build_circuit

SETTINGS = SETTINGS_ORDER  # ("XX", "YY", "ZZ")


def make_qc(nq, nc):
    return QuantumCircuit(nq, nc)


# --------------------------------------------------------------------------------------
# Error lookup -> estimated success probability (ESP) used to rank layouts
# --------------------------------------------------------------------------------------

_FALLBACK = {"2q": 1e-2, "1q": 5e-4, "ro": 1e-2}


class ErrorLookup:
    """Per-gate error rates of a model (calibration data or synthetic constants)."""

    def __init__(self, model):
        self.rates = model.error_rates
        self.tgt = None
        if self.rates is None:
            try:
                self.tgt = qb.fake_backend(model.name).target
            except Exception:  # pragma: no cover - fall back to constants
                self.tgt = None

    def gate(self, name, qubits):
        if name in ("barrier", "delay", "rz", "u1", "id"):
            return 0.0
        if self.rates is not None:
            if name == "measure":
                return self.rates["readout"]
            return self.rates["two_qubit"] if len(qubits) == 2 else self.rates["one_qubit"]
        if self.tgt is not None and name in self.tgt.operation_names:
            props = self.tgt[name].get(tuple(qubits))
            if props is not None and props.error is not None:
                return float(props.error)
        if name == "measure":
            return _FALLBACK["ro"]
        return _FALLBACK["2q"] if len(qubits) == 2 else _FALLBACK["1q"]


def esp(tc, lookup: ErrorLookup) -> float:
    """Estimated success probability = product of (1 - error) over every operation."""
    p = 1.0
    for inst in tc.data:
        name = inst.operation.name
        if name in ("barrier", "delay"):
            continue
        qs = [tc.find_bit(q).index for q in inst.qubits]
        p *= 1.0 - lookup.gate(name, qs)
    return p


# --------------------------------------------------------------------------------------
# Compilation + metrics + validity
# --------------------------------------------------------------------------------------


def compile_one(model, qc, layout, seed, opt):
    return transpile(
        qc, model.backend, initial_layout=list(layout),
        optimization_level=opt, seed_transpiler=seed,
    )


def count_swaps(model, qc, layout, seed):
    """SWAPs inserted by the routing pass (kept as `swap` gates: no basis translation)."""
    try:
        routed = transpile(
            qc, coupling_map=model.coupling_map, initial_layout=list(layout),
            optimization_level=0, seed_transpiler=seed,
        )
        return int(routed.count_ops().get("swap", 0))
    except Exception:  # pragma: no cover
        return None


def validate_compiled(tc, model) -> list[str]:
    """Return a list of problems: gates outside the basis or on uncoupled pairs."""
    allowed = set(model.basis_gates) | {"measure", "barrier", "delay", "id", "reset"}
    edges = {frozenset(e) for e in model.edges}
    problems = []
    for inst in tc.data:
        name = inst.operation.name
        qs = [tc.find_bit(q).index for q in inst.qubits]
        if name not in allowed:
            problems.append(f"gate {name} not in basis")
        if name != "barrier" and len(qs) == 2 and frozenset(qs) not in edges:
            problems.append(f"{name} on uncoupled pair {qs}")
    return problems


def physical_qubits_used(tc):
    used = set()
    for inst in tc.data:
        if inst.operation.name == "barrier":
            continue
        used.update(tc.find_bit(q).index for q in inst.qubits)
    return sorted(used)


def measured_on(tc):
    """Map classical bit -> physical qubit it is measured on (where the data really sit)."""
    m = {}
    for inst in tc.data:
        if inst.operation.name == "measure":
            m[tc.find_bit(inst.clbits[0]).index] = tc.find_bit(inst.qubits[0]).index
    return m


# --------------------------------------------------------------------------------------
# Plans (layout + compiled circuits for the three settings)
# --------------------------------------------------------------------------------------


@dataclass
class Plan:
    model_name: str
    noise_variant: str
    scheme: str
    layout: list
    info: dict
    compiled: dict  # setting -> compiled circuit
    logical: dict   # setting -> logical circuit
    metrics: dict
    placement_table: list = field(default_factory=list)
    seed_t: int = 1
    opt: int = 2


def _compile_zz(model, scheme, layout, n_int, seed, opt):
    qc, _ = build_circuit(scheme, "ZZ", make_qc, n_int)
    return compile_one(model, qc, layout, seed, opt), qc


def _search_ancilla(model, scheme, base_layout, n_int, taken, lookup, seed, opt):
    """Try every nearby qubit as the next ancilla; rank by ESP (then depth)."""
    adj = geometry.adjacency(model.edges, model.num_qubits)
    cands = [c for c in geometry.ancilla_candidates(adj, model.ports) if c not in taken]
    table = []
    for c in cands:
        layout = [*base_layout, c]
        try:
            tc, _ = _compile_zz(model, scheme, layout, n_int, seed, opt)
        except Exception:
            continue
        table.append({
            "ancilla": c, "n2q": tc.num_nonlocal_gates(), "depth": tc.depth(),
            "esp": esp(tc, lookup),
        })
    table.sort(key=lambda r: (-r["esp"], r["depth"], r["ancilla"]))
    return table


def plan_scheme(model, scheme, seed_t=1, opt=2) -> Plan:
    """Choose a layout for ``scheme`` (noise-aware, geometry-aware) and compile 3 settings."""
    A, B = model.ports
    adj = geometry.adjacency(model.edges, model.num_qubits)
    lookup = ErrorLookup(model)
    table: list = []
    n_int = 0

    if scheme == "plain":
        layout = [A, B]
    elif scheme == "mbr":
        paths = geometry.all_shortest_paths(adj, A, B)
        best = None
        for p in paths[:50]:
            layout_try = [A, B, *p[1:-1]]
            tc, _ = _compile_zz(model, "mbr", layout_try, len(p) - 2, seed_t, opt)
            score = esp(tc, lookup)
            if best is None or score > best[0]:
                best = (score, p)
        path = best[1]
        n_int = len(path) - 2
        layout = [A, B, *path[1:-1]]
    elif scheme in ("zz", "xx"):
        table = _search_ancilla(model, scheme, [A, B], 0, set(model.ports), lookup, seed_t, opt)
        layout = [A, B, table[0]["ancilla"]]
    elif scheme == "zzxx":
        # greedy: first ancilla placed for the ZZ check, then the second for the full circuit
        t1 = _search_ancilla(model, "zz", [A, B], 0, set(model.ports), lookup, seed_t, opt)
        a1 = t1[0]["ancilla"]
        table = _search_ancilla(model, "zzxx", [A, B, a1], 0, {A, B, a1}, lookup, seed_t, opt)
        layout = [A, B, a1, table[0]["ancilla"]]
    else:
        raise ValueError(scheme)

    logical, compiled, info = {}, {}, None
    for s in SETTINGS:
        qc, info = build_circuit(scheme, s, make_qc, n_int)
        logical[s] = qc
        compiled[s] = compile_one(model, qc, layout, seed_t, opt)

    zz = compiled["ZZ"]
    problems = [p for tc in compiled.values() for p in validate_compiled(tc, model)]
    n2q_logical = logical["ZZ"].num_nonlocal_gates()
    swaps = count_swaps(model, logical["ZZ"], layout, seed_t)
    mo = measured_on(zz)
    metrics = {
        "depth": zz.depth(),
        "depth_max_over_settings": max(tc.depth() for tc in compiled.values()),
        "n2q": zz.num_nonlocal_gates(),
        "n2q_logical": n2q_logical,
        "swaps": swaps,
        "swaps_from_gate_count": max(0, (zz.num_nonlocal_gates() - n2q_logical) // 3),
        "phys_qubits": physical_qubits_used(zz),
        "n_phys": len(physical_qubits_used(zz)),
        "ancillas": layout[2:] if scheme in ("zz", "xx", "zzxx") else [],
        "intermediates": layout[2:] if scheme == "mbr" else [],
        "esp": esp(zz, lookup),
        "data_measured_on": [mo.get(0), mo.get(1)],
        "data_on_ports": bool(mo.get(0) == A and mo.get(1) == B),
        "valid": not problems,
        "problems": problems[:5],
    }
    return Plan(model.name, model.noise_variant, scheme, list(layout), info, compiled,
                logical, metrics, table, seed_t, opt)


# --------------------------------------------------------------------------------------
# Execution
# --------------------------------------------------------------------------------------


def execute(plan: Plan, backend, shots: int, seed_sim: int, n_boot: int = 1000) -> dict:
    counts = {}
    for i, s in enumerate(SETTINGS):
        job = backend.run(plan.compiled[s], shots=shots, seed_simulator=seed_sim + i)
        counts[s] = job.result().get_counts()
    res = analysis.evaluate(counts, plan.info, n_boot=n_boot, seed=seed_sim)
    res["seed_sim"] = seed_sim
    res["shots"] = shots
    return res


def scaled_model(model, scale: float):
    """Copy of a ``noise='common'`` model with all three synthetic error rates times ``scale``."""
    from dataclasses import replace

    base = qb.ERRORS_CONTEMPORARY_MEDIAN
    rates = {k: min(v * scale, 0.5) for k, v in base.items()}
    nm = qb.synthetic_noise_model(**rates, two_qubit_gate="cz")
    noisy, ideal = qb._graph_backends(model.num_qubits, model.edges, model.basis_gates, nm)
    return replace(model, backend=noisy, ideal_backend=ideal, noise_model=nm, error_rates=rates)
