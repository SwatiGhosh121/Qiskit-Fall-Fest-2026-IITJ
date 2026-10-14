"""Offline smoke test of plots/report/dashboard using fake rows built from the mini simulator."""
import os, sys, types, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
# stub qiskit-dependent modules so bellgeo.plots/report import without Qiskit
from bellgeo import analysis, plots, report, geometry
from bellgeo.circuits import build_circuit
from bellgeo.minisim import MiniCircuit, simulate, sample_counts
mk = lambda nq, nc: MiniCircuit(nq, nc)
NL = {"2016": 0.016, "contemporary": 0.0039, "hyperbolic": 0.0039}
def mkrow(study, model, scheme, mode, e2, **extra):
    n_int = 2 if scheme == "mbr" else 0
    cts, info = {}, None
    for i, s in enumerate(analysis.SETTINGS):
        qc, info = build_circuit(scheme, s, mk, n_int)
        cts[s] = sample_counts(simulate(qc, 0, 0 if mode == "ideal" else e2, 0.01 if mode != "ideal" else 0), 10000, i)
    r = analysis.evaluate(cts, info, n_boot=100)
    r.update(study=study, model=model, scheme=scheme, mode=mode, depth=10, n2q=5, swaps=2,
             n_phys=4, phys_qubits=[0, 1], data_on_ports=False, layout=[0, 1], opt=2, seed_t=1, **extra)
    return r
rows = []
for model in plots.MODELS:
    for scheme in ("plain", "zz", "xx", "zzxx", "mbr"):
        for mode in ("ideal", "noisy"):
            rows.append(mkrow("native", model, scheme, mode, NL[model]))
            rows.append(mkrow("graph_only", model, scheme, mode, 0.0039))
        for sc in (0.5, 1, 2):
            rows.append(mkrow("noise_sweep", model, scheme, "noisy", 0.0039 * sc, scale=sc))
        for k in range(4):
            rows.append(mkrow("seed_validation", model, scheme, "noisy", NL[model], seed_index=k))
    for l in range(4):
        rows.append({"study": "opt_levels", "model": model, "opt": l, "n2q": 7 - l % 2, "depth": 20})
core = []
for i, model in enumerate(plots.MODELS):
    for j, (mode, scheme) in enumerate((("ideal", "plain"), ("noisy", "plain"), ("noisy", "zzxx"))):
        r = [x for x in rows if x["study"] == "native" and x["model"] == model and x["scheme"] == scheme and x["mode"] == mode][0]
        core.append(dict(r, case=3 * i + j + 1, label=f"{mode}+{scheme}"))
# fake models/plans for fig_geometry
class M: pass
class P: pass
models, plans = {}, {}
edges = {"2016": [(0,1),(1,2),(1,3),(3,4)], "contemporary": [(i,i+1) for i in range(12)], "hyperbolic": [(i,(i+1)%7) for i in range(7)]}
for name, e in edges.items():
    m = M(); m.edges = e; m.num_qubits = max(max(x) for x in e) + 1
    m.ports = (0, 4) if name == "2016" else (0, 3); m.positions = None
    models[name] = m
    p = P(); p.placement_table = [{"ancilla": q, "esp": 0.9 - 0.01 * q} for q in range(1, m.num_qubits) if q not in m.ports]
    plans[(name, "zz")] = p
geo = {n: geometry.graph_metrics(models[n].edges, models[n].num_qubits, models[n].ports) for n in models}
figs = [plots.fig_geometry(models, plans, geo), plots.fig_core(core), plots.fig_cost(rows),
        plots.fig_tradeoff(rows), plots.fig_graph_only(rows), plots.fig_sweep(rows),
        plots.fig_calibration(rows), plots.fig_opt(rows)]
md = (report.table_core(core) + report.table_ablation(rows, "native", "native") + report.table_geometry(geo)
      + report.table_calibration(rows) + report.table_opt(rows) + report.auto_findings(rows, "zzxx"))
os.makedirs("/tmp/dash", exist_ok=True)
report.dashboard("/tmp/dash/d.html", [("a", "fig", figs[1]), ("t", "md", md)])
figs[1].savefig("/tmp/dash/core.png", dpi=80); figs[5].savefig("/tmp/dash/sweep.png", dpi=80)
print(md[-1800:]); print("OFFLINE REPORT SMOKE TEST OK", os.path.getsize("/tmp/dash/d.html"))
