"""Offline logic tests (no Qiskit). Run:  python tests/test_logic.py   (or pytest)."""
import ast, math, os, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bellgeo import analysis, geometry
from bellgeo.circuits import build_circuit, SCHEMES
from bellgeo.minisim import MiniCircuit, simulate, sample_counts

mk = lambda nq, nc: MiniCircuit(nq, nc)

def run(scheme, n_int=0, e1=0.0, e2=0.0, ro=0.0, shots=None, seed=0, n_boot=0):
    counts, info = {}, None
    for s in analysis.SETTINGS:
        qc, info = build_circuit(scheme, s, mk, n_int)
        p = simulate(qc, e1, e2, ro)
        counts[s] = p if shots is None else sample_counts(p, shots, seed + len(counts))
    return analysis.evaluate(counts, info, n_boot=n_boot), counts

def test_ideal_all_schemes():
    for scheme in SCHEMES:
        for n_int in ([1, 2, 3] if scheme == "mbr" else [0]):
            r, _ = run(scheme, n_int)
            assert abs(r["F"] - 1) < 1e-9, (scheme, n_int, r["F"])
            assert abs(r["accept"] - 1) < 1e-9, (scheme, r["accept"])

def test_classical_mixture_is_half():
    u = {"00": 2500, "01": 2500, "10": 2500, "11": 2500}
    c = {"ZZ": {"00": 5000, "11": 5000}, "XX": u, "YY": u}
    r = analysis.evaluate(c, {}, n_boot=0)
    assert abs(r["F"] - 0.5) < 1e-12 and not r["verified"]

def test_plain_one_noisy_cx_gives_F_equals_1_minus_e():
    for e in (0.01, 0.05, 0.2):
        r, _ = run("plain", e2=e)
        assert abs(r["F"] - (1 - e)) < 1e-9, (e, r["F"])

def test_checks_raise_conditional_fidelity_and_lower_acceptance():
    raw, _ = run("plain", e2=0.05)
    zz, _ = run("zz", e2=0.05)
    zzxx, _ = run("zzxx", e2=0.05)
    assert zz["accept"] < 1 and zzxx["accept"] < zz["accept"]
    print("   plain F=%.4f | zz F=%.4f acc=%.4f | zzxx F=%.4f acc=%.4f" % (
        raw["F"], zz["F"], zz["accept"], zzxx["F"], zzxx["accept"]))

def test_mbr_pauli_frame_needed():
    r, c = run("mbr", 2)
    info = {"data_bits": (0, 1), "flag_bits": (), "frame_bits": ()}
    nofr = analysis.evaluate(c, info, n_boot=0)
    assert nofr["F"] < 0.6 and abs(r["F"] - 1) < 1e-9

def test_mbr_gate_count():
    for n_int in (1, 2, 3):
        qc, _ = build_circuit("mbr", "ZZ", mk, n_int)
        assert qc.num_two_qubit() == n_int + 1

def test_sigma_calibration_against_sampling():
    p = {s: simulate(build_circuit("plain", s, mk)[0], 0.0, 0.06, 0.01) for s in analysis.SETTINGS}
    info = build_circuit("plain", "ZZ", mk)[1]
    fs, sg = [], []
    for k in range(200):
        cts = {s: sample_counts(p[s], 10_000, 1000 * k + i) for i, s in enumerate(analysis.SETTINGS)}
        r = analysis.evaluate(cts, info, n_boot=0)
        fs.append(r["F"]); sg.append(r["sigma_F"])
    cal = analysis.calibration_summary(fs, sg)
    print("   sigma calibration ratio:", round(cal["ratio"], 3))
    assert 0.85 < cal["ratio"] < 1.15, cal

def test_bootstrap_matches_analytic_sigma():
    r, _ = run("zz", e2=0.04, ro=0.01, shots=10_000, seed=3, n_boot=2000)
    ratio = r["F_boot_std"] / r["sigma_F"]
    print("   bootstrap/analytic sigma:", round(ratio, 3))
    assert 0.8 < ratio < 1.2

def _hyperbolic_patch():
    src = open(os.path.join(ROOT, "qff_basic_benchmark.py")).read()
    keep = [n for n in ast.parse(src).body if (isinstance(n, ast.FunctionDef) and n.name in
            ("_poincare_vertex_radius", "_reflect_across_geodesic", "hyperbolic_patch"))
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "_MERGE_TOL")]
    ns = {"math": math, "np": np}
    exec(compile(ast.Module(keep, []), "x", "exec"), ns)
    return ns["hyperbolic_patch"](7, 3)

def test_geometry_on_real_hyperbolic_patch():
    n, edges, pos, faces = _hyperbolic_patch()
    assert n == 35 and len(edges) == 42
    m = geometry.graph_metrics(edges, n, (0, 3))
    print("   hyperbolic metrics:", {k: m[k] for k in ("port_distance", "ring_through_ports", "girth", "n_shortest_paths", "qubits_within_4_of_both_ports")})
    assert m["port_distance"] == 3 and m["ring_through_ports"] == 7 and m["girth"] == 7

def test_geometry_2016_tree():
    m = geometry.graph_metrics([(0, 1), (1, 2), (1, 3), (3, 4)], 5, (0, 4))
    assert m["port_distance"] == 3 and m["girth"] is None and m["ring_through_ports"] is None

if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for f in fns:
        f(); print("PASS", f.__name__)
    print(f"\nall {len(fns)} tests passed")
