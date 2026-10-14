# Geometry-aware Bell verification: QFF 2026 Basic Track

Uses the organizers' `qff_basic_benchmark.py` **unchanged** (3 models, ports, noise, 10,000 shots).

## Run it

```bash
pip install -r requirements.txt          # qiskit-ibm-runtime must be 0.50.0
python tests/test_logic.py               # 10 offline logic tests (no Qiskit needed), ~10 s
python run_all.py --quick                # smoke run
python run_all.py                        # full run -> results/
```
Then open **`results/dashboard.html`** in a browser. It shows every figure and table plus
machine-written findings. `results/tables.md` has the same tables for pasting into the report;
`results/results.json|csv` hold all raw numbers; `results/circuits/` has compiled circuit drawings;
`results/figures/graph_*.png` are the required graph drawings with ports highlighted.

## What is in the project

| Part | What it does |
|---|---|
| Core grid (cases 1-9) | Bell pair on the ports, ideal / noisy / noisy + protection, F from XX, YY, ZZ, `F-2σ>0.5` test, bootstrap CI, acceptance, discarded shots, depth, 2q gates, SWAPs, physical qubits |
| Protection (Builder level) | ZZ check, XX check, ZZ+XX double check. Ancilla sites are searched over the port neighbourhood and ranked by estimated success probability from the model's own error rates |
| **Measurement-based routing (MBR)** | Replaces 2 SWAPs + CNOT (7 two-qubit gates) by a 3-CNOT chain along a shortest path. Intermediates are measured in X; their parity is a Pauli-frame correction applied in post-processing (no feed-forward needed). The Bell pair ends exactly on the ports |
| Graph-only study (Task 6) | Same three graphs with `noise="common"` (same gate set and noise) |
| Noise sweep | Common noise x0.25 ... x4: where do checks or MBR start to pay off? |
| Uncertainty calibration | Repeats runs over independent seeds: is the quoted σ_F the real scatter? |
| Geometry metrics | Port distance, shortest-path count, ring through the ports, girth, room for ancillas |
| Validity checks | Every compiled circuit is checked against the coupling graph and gate set; ideal runs must give F = 1 exactly |

## Honest notes

* MBR is a published technique (Bäumer et al., *Efficient long-range entanglement using dynamic
  circuits*, PRX Quantum 2024; also IBM's long-range-entanglement tutorial). Our contribution is
  applying it with classical Pauli-frame post-processing to this geometry comparison and measuring
  where it pays off. Keep it clearly separate from the nine core cases (the rules allow this).
* With the standard SWAP routing, the transpiler leaves one Bell qubit on a neighbour of a port,
  not on the port itself (`data_on_ports` column). MBR does not have this issue.
* The headline protection (`--headline`, default `zzxx`) is fixed before looking at results. All
  other schemes are reported too, whether they win or lose.
* `bellgeo/minisim.py` is a NumPy simulator used only for the offline tests. It is not used for any
  reported number.
