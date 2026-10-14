## Core 3x3 grid (cases 1-9)

| Case | Model | Condition | F ± σ_F | F−2σ>0.5 | Accept | Discarded | Depth | 2q gates | SWAPs | Phys. qubits | Data on ports? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2016 | ideal | 1.0000 ± 0.0000 | yes | 1.000 | 0 | 6 | 7 | 2 | 4 [0, 1, 3, 4] | no |
| 2 | 2016 | noisy | 0.8433 ± 0.0026 | yes | 1.000 | 0 | 6 | 7 | 2 | 4 [0, 1, 3, 4] | no |
| 3 | 2016 | noisy+zzxx | 0.8349 ± 0.0030 | yes | 0.807 | 5,803 | 14 | 14 | 4 | 5 [0, 1, 2, 3, 4] | no |
| 4 | contemporary | ideal | 1.0000 ± 0.0000 | yes | 1.000 | 0 | 13 | 7 | 2 | 4 [126, 127, 128, 129] | no |
| 5 | contemporary | noisy | 0.9472 ± 0.0016 | yes | 1.000 | 0 | 13 | 7 | 2 | 4 [126, 127, 128, 129] | no |
| 6 | contemporary | noisy+zzxx | 0.9585 ± 0.0015 | yes | 0.944 | 1,668 | 35 | 14 | 4 | 5 [126, 127, 128, 129, 137] | no |
| 7 | hyperbolic | ideal | 1.0000 ± 0.0000 | yes | 1.000 | 0 | 13 | 7 | 2 | 4 [0, 1, 2, 3] | no |
| 8 | hyperbolic | noisy | 0.9549 ± 0.0015 | yes | 1.000 | 0 | 13 | 7 | 2 | 4 [0, 1, 2, 3] | no |
| 9 | hyperbolic | noisy+zzxx | 0.9665 ± 0.0013 | yes | 0.932 | 2,033 | 35 | 14 | 4 | 5 [0, 1, 2, 3, 7] | no |

### All schemes, native noise (each model's own gate set + noise)

| Model | Scheme | F ± σ_F | bootstrap 95% CI | Accept | 2q | SWAPs | Depth | Phys. qubits | ΔF vs plain (z) |
|---|---|---|---|---|---|---|---|---|---|
| 2016 | plain (SWAP-routed) | 0.8433 ± 0.0026 | [0.8381, 0.8488] | 1.000 | 7 | 2 | 6 | 4 | – |
| 2016 | ZZ check | 0.8663 ± 0.0026 | [0.8612, 0.8713] | 0.904 | 10 | 3 | 12 | 4 | +0.0231 (z=+6.2) |
| 2016 | XX check | 0.8221 ± 0.0030 | [0.8161, 0.8275] | 0.893 | 12 | 3 | 13 | 4 | -0.0212 (z=-5.3) |
| 2016 | ZZ+XX check | 0.8349 ± 0.0030 | [0.8294, 0.8408] | 0.807 | 14 | 4 | 14 | 5 | -0.0084 (z=-2.1) |
| 2016 | measurement-based routing | 0.7954 ± 0.0030 | [0.7895, 0.8014] | 1.000 | 3 | 0 | 6 | 4 | -0.0479 (z=-12.1) |
| contemporary | plain (SWAP-routed) | 0.9472 ± 0.0016 | [0.9440, 0.9503] | 1.000 | 7 | 2 | 13 | 4 | – |
| contemporary | ZZ check | 0.9762 ± 0.0011 | [0.9740, 0.9782] | 0.955 | 10 | 3 | 23 | 4 | +0.0290 (z=+14.9) |
| contemporary | XX check | 0.9734 ± 0.0012 | [0.9711, 0.9757] | 0.952 | 12 | 4 | 34 | 5 | +0.0263 (z=+13.3) |
| contemporary | ZZ+XX check | 0.9585 ± 0.0015 | [0.9557, 0.9614] | 0.944 | 14 | 4 | 35 | 5 | +0.0114 (z=+5.3) |
| contemporary | measurement-based routing | 0.9398 ± 0.0017 | [0.9363, 0.9431] | 1.000 | 3 | 0 | 16 | 4 | -0.0074 (z=-3.2) |
| hyperbolic | plain (SWAP-routed) | 0.9549 ± 0.0015 | [0.9520, 0.9577] | 1.000 | 7 | 2 | 13 | 4 | – |
| hyperbolic | ZZ check | 0.9612 ± 0.0014 | [0.9585, 0.9638] | 0.963 | 10 | 3 | 23 | 4 | +0.0063 (z=+3.1) |
| hyperbolic | XX check | 0.9494 ± 0.0016 | [0.9463, 0.9526] | 0.966 | 12 | 3 | 30 | 4 | -0.0055 (z=-2.5) |
| hyperbolic | ZZ+XX check | 0.9665 ± 0.0013 | [0.9641, 0.9689] | 0.932 | 14 | 4 | 35 | 5 | +0.0116 (z=+5.9) |
| hyperbolic | measurement-based routing | 0.9475 ± 0.0016 | [0.9446, 0.9507] | 1.000 | 3 | 0 | 16 | 4 | -0.0074 (z=-3.4) |


### All schemes, common noise (graph is the only difference)

| Model | Scheme | F ± σ_F | bootstrap 95% CI | Accept | 2q | SWAPs | Depth | Phys. qubits | ΔF vs plain (z) |
|---|---|---|---|---|---|---|---|---|---|
| 2016 | plain (SWAP-routed) | 0.9549 ± 0.0015 | [0.9520, 0.9577] | 1.000 | 7 | 2 | 13 | 4 | – |
| 2016 | ZZ check | 0.9612 ± 0.0014 | [0.9585, 0.9638] | 0.963 | 10 | 3 | 23 | 4 | +0.0063 (z=+3.1) |
| 2016 | XX check | 0.9494 ± 0.0016 | [0.9463, 0.9526] | 0.966 | 12 | 3 | 30 | 4 | -0.0055 (z=-2.5) |
| 2016 | ZZ+XX check | 0.9664 ± 0.0013 | [0.9637, 0.9690] | 0.932 | 14 | 4 | 35 | 5 | +0.0115 (z=+5.8) |
| 2016 | measurement-based routing | 0.9475 ± 0.0016 | [0.9446, 0.9507] | 1.000 | 3 | 0 | 16 | 4 | -0.0074 (z=-3.4) |
| contemporary | plain (SWAP-routed) | 0.9549 ± 0.0015 | [0.9520, 0.9577] | 1.000 | 7 | 2 | 13 | 4 | – |
| contemporary | ZZ check | 0.9612 ± 0.0014 | [0.9585, 0.9638] | 0.963 | 10 | 3 | 23 | 4 | +0.0063 (z=+3.1) |
| contemporary | XX check | 0.9494 ± 0.0016 | [0.9463, 0.9526] | 0.966 | 12 | 3 | 30 | 4 | -0.0055 (z=-2.5) |
| contemporary | ZZ+XX check | 0.9665 ± 0.0013 | [0.9641, 0.9689] | 0.932 | 14 | 4 | 35 | 5 | +0.0116 (z=+5.9) |
| contemporary | measurement-based routing | 0.9475 ± 0.0016 | [0.9446, 0.9507] | 1.000 | 3 | 0 | 16 | 4 | -0.0074 (z=-3.4) |
| hyperbolic | plain (SWAP-routed) | 0.9549 ± 0.0015 | [0.9520, 0.9577] | 1.000 | 7 | 2 | 13 | 4 | – |
| hyperbolic | ZZ check | 0.9612 ± 0.0014 | [0.9585, 0.9638] | 0.963 | 10 | 3 | 23 | 4 | +0.0063 (z=+3.1) |
| hyperbolic | XX check | 0.9494 ± 0.0016 | [0.9463, 0.9526] | 0.966 | 12 | 3 | 30 | 4 | -0.0055 (z=-2.5) |
| hyperbolic | ZZ+XX check | 0.9665 ± 0.0013 | [0.9641, 0.9689] | 0.932 | 14 | 4 | 35 | 5 | +0.0116 (z=+5.9) |
| hyperbolic | measurement-based routing | 0.9475 ± 0.0016 | [0.9446, 0.9507] | 1.000 | 3 | 0 | 16 | 4 | -0.0074 (z=-3.4) |


### Geometry metrics

| Metric | 2016 | contemporary | hyperbolic |
|---|---|---|---|
| qubits | 5 | 156 | 35 |
| couplers | 4 | 176 | 42 |
| avg_degree | 1.60 | 2.26 | 2.40 |
| max_degree | 3 | 3 | 3 |
| port_distance | 3 | 3 | 3 |
| n_shortest_paths | 1 | 1 | 1 |
| ring_through_ports | None | 12 | 7 |
| girth | None | 12 | 7 |
| qubits_within_4_of_both_ports | 3 | 7 | 19 |
| port_degrees | (1, 1) | (2, 3) | (3, 3) |


### Uncertainty calibration

| Model | Scheme | seeds | mean F | empirical std | mean quoted σ_F | ratio |
|---|---|---|---|---|---|---|
| 2016 | mbr | 10 | 0.7995 | 0.0025 | 0.0029 | 0.86 |
| 2016 | plain | 10 | 0.8470 | 0.0032 | 0.0026 | 1.20 |
| 2016 | zzxx | 10 | 0.8372 | 0.0041 | 0.0030 | 1.38 |
| contemporary | mbr | 10 | 0.9424 | 0.0012 | 0.0017 | 0.71 |
| contemporary | plain | 10 | 0.9489 | 0.0017 | 0.0016 | 1.09 |
| contemporary | zzxx | 10 | 0.9621 | 0.0013 | 0.0014 | 0.95 |
| hyperbolic | mbr | 10 | 0.9495 | 0.0013 | 0.0016 | 0.83 |
| hyperbolic | plain | 10 | 0.9568 | 0.0014 | 0.0014 | 1.00 |
| hyperbolic | zzxx | 10 | 0.9676 | 0.0013 | 0.0013 | 1.01 |


### Transpiler optimization level (plain Bell, 2q gates / depth)

| Model | opt 0: 2q / depth | opt 1: 2q / depth | opt 2: 2q / depth | opt 3: 2q / depth |
|---|---|---|---|---|
| 2016 | 7 / 6 | 7 / 6 | 7 / 6 | 7 / 6 |
| contemporary | 7 / 14 | 7 / 14 | 7 / 13 | 7 / 13 |
| hyperbolic | 7 / 14 | 7 / 14 | 7 / 13 | 7 / 13 |


## Machine-written findings

**native noise**
- 2016: unprotected F = 0.8433 ± 0.0026 with 7 two-qubit gates (2 SWAPs); data end on the ports: False.
  - ZZ check improves the baseline: ΔF = +0.0231 (z = +6.2), 10 2q gates, 4 qubits, keeping 90.4% of shots (2,866 discarded), yield 0.663 vs 0.687.
  - XX check worsens the baseline: ΔF = -0.0212 (z = -5.3), 12 2q gates, 4 qubits, keeping 89.3% of shots (3,195 discarded), yield 0.576 vs 0.687.
  - ZZ+XX check worsens the baseline: ΔF = -0.0084 (z = -2.1), 14 2q gates, 5 qubits, keeping 80.7% of shots (5,803 discarded), yield 0.540 vs 0.687.
  - measurement-based routing worsens the baseline: ΔF = -0.0479 (z = -12.1), 3 2q gates, 4 qubits.
- contemporary: unprotected F = 0.9472 ± 0.0016 with 7 two-qubit gates (2 SWAPs); data end on the ports: False.
  - ZZ check improves the baseline: ΔF = +0.0290 (z = +14.9), 10 2q gates, 4 qubits, keeping 95.5% of shots (1,345 discarded), yield 0.910 vs 0.894.
  - XX check improves the baseline: ΔF = +0.0263 (z = +13.3), 12 2q gates, 5 qubits, keeping 95.2% of shots (1,436 discarded), yield 0.902 vs 0.894.
  - ZZ+XX check improves the baseline: ΔF = +0.0114 (z = +5.3), 14 2q gates, 5 qubits, keeping 94.4% of shots (1,668 discarded), yield 0.866 vs 0.894.
  - measurement-based routing worsens the baseline: ΔF = -0.0074 (z = -3.2), 3 2q gates, 4 qubits.
- hyperbolic: unprotected F = 0.9549 ± 0.0015 with 7 two-qubit gates (2 SWAPs); data end on the ports: False.
  - ZZ check improves the baseline: ΔF = +0.0063 (z = +3.1), 10 2q gates, 4 qubits, keeping 96.3% of shots (1,123 discarded), yield 0.888 vs 0.910.
  - XX check worsens the baseline: ΔF = -0.0055 (z = -2.5), 12 2q gates, 4 qubits, keeping 96.6% of shots (1,011 discarded), yield 0.869 vs 0.910.
  - ZZ+XX check improves the baseline: ΔF = +0.0116 (z = +5.9), 14 2q gates, 5 qubits, keeping 93.2% of shots (2,033 discarded), yield 0.870 vs 0.910.
  - measurement-based routing worsens the baseline: ΔF = -0.0074 (z = -3.4), 3 2q gates, 4 qubits.
**common noise (graph only)**
- 2016: unprotected F = 0.9549 ± 0.0015 with 7 two-qubit gates (2 SWAPs); data end on the ports: False.
  - ZZ check improves the baseline: ΔF = +0.0063 (z = +3.1), 10 2q gates, 4 qubits, keeping 96.3% of shots (1,123 discarded), yield 0.888 vs 0.910.
  - XX check worsens the baseline: ΔF = -0.0055 (z = -2.5), 12 2q gates, 4 qubits, keeping 96.6% of shots (1,011 discarded), yield 0.869 vs 0.910.
  - ZZ+XX check improves the baseline: ΔF = +0.0115 (z = +5.8), 14 2q gates, 5 qubits, keeping 93.2% of shots (2,041 discarded), yield 0.869 vs 0.910.
  - measurement-based routing worsens the baseline: ΔF = -0.0074 (z = -3.4), 3 2q gates, 4 qubits.
- contemporary: unprotected F = 0.9549 ± 0.0015 with 7 two-qubit gates (2 SWAPs); data end on the ports: False.
  - ZZ check improves the baseline: ΔF = +0.0063 (z = +3.1), 10 2q gates, 4 qubits, keeping 96.3% of shots (1,123 discarded), yield 0.888 vs 0.910.
  - XX check worsens the baseline: ΔF = -0.0055 (z = -2.5), 12 2q gates, 4 qubits, keeping 96.6% of shots (1,011 discarded), yield 0.869 vs 0.910.
  - ZZ+XX check improves the baseline: ΔF = +0.0116 (z = +5.9), 14 2q gates, 5 qubits, keeping 93.2% of shots (2,033 discarded), yield 0.870 vs 0.910.
  - measurement-based routing worsens the baseline: ΔF = -0.0074 (z = -3.4), 3 2q gates, 4 qubits.
- hyperbolic: unprotected F = 0.9549 ± 0.0015 with 7 two-qubit gates (2 SWAPs); data end on the ports: False.
  - ZZ check improves the baseline: ΔF = +0.0063 (z = +3.1), 10 2q gates, 4 qubits, keeping 96.3% of shots (1,123 discarded), yield 0.888 vs 0.910.
  - XX check worsens the baseline: ΔF = -0.0055 (z = -2.5), 12 2q gates, 4 qubits, keeping 96.6% of shots (1,011 discarded), yield 0.869 vs 0.910.
  - ZZ+XX check improves the baseline: ΔF = +0.0116 (z = +5.9), 14 2q gates, 5 qubits, keeping 93.2% of shots (2,033 discarded), yield 0.870 vs 0.910.
  - measurement-based routing worsens the baseline: ΔF = -0.0074 (z = -3.4), 3 2q gates, 4 qubits.
