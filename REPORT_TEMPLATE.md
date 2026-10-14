# Report skeleton (fill from results/tables.md and results/dashboard.html)

1. **Problem and setup.** Bell pair between two ports, three models, 10,000 shots, seeds (`seed_t`, `seed_s`, opt level).
2. **Method.** F = (1+XX−YY+ZZ)/4; σ_F formula; verified if F−2σ>0.5; bootstrap CI; post-selection rule applied identically in XX/YY/ZZ.
3. **Core grid.** Paste the core table (cases 1-9) and the core figure.
4. **Routing.** SWAPs and 2q gates per model; note `data_on_ports`; transpiler-level table.
5. **Protection.** ZZ / XX / ZZ+XX: ΔF with z-score, acceptance, discarded shots, yield. State plainly whether the checks pay for their own gates.
6. **Measurement-based routing.** Gate count vs SWAP routing, fidelity, the cost of reading out intermediates (readout error enters through the frame).
7. **Connectivity vs gate set vs noise.** Native-noise table vs graph-only table. Geometry metrics.
8. **Noise sweep.** Crossover points.
9. **Recommendation (Task 7).** One design choice, tied to the numbers; candidates: native mid-circuit measurement with classical frame tracking, or ancilla-friendly ports. State limits (finite patches, simulated noise, one port pair).
10. **Reproducibility.** Commands, versions, seeds, uncertainty-calibration table.
