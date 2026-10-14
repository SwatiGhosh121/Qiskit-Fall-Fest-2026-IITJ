#!/usr/bin/env python
"""Run the whole project: core 3x3 grid + all extra studies + figures + dashboard.

    python run_all.py                 # full run (a few minutes)
    python run_all.py --quick         # fast smoke run (fewer seeds / sweep points)
    python run_all.py --headline zz   # choose which protection fills cases 3, 6, 9

Outputs go to ./results : results.json, results.csv, tables.md, dashboard.html (open it in a
browser), figures/*.png, circuits/*.png.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import warnings

import numpy as np

import qff_basic_benchmark as qb
from bellgeo import plots, report, runner, studies
from bellgeo.studies import Log


def parse():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--outdir", default="results")
    p.add_argument("--seed-t", type=int, default=1, help="transpiler seed (reported)")
    p.add_argument("--seed-s", type=int, default=1, help="simulator seed (reported)")
    p.add_argument("--opt-level", type=int, default=2, help="transpiler optimization level")
    p.add_argument("--headline", default="zzxx", choices=["zz", "xx", "zzxx"],
                   help="protection used for cases 3, 6, 9 (fixed in advance, see README)")
    p.add_argument("--seeds", type=int, default=10, help="seeds for the uncertainty calibration")
    p.add_argument("--n-boot", type=int, default=1000)
    p.add_argument("--quick", action="store_true")
    p.add_argument("--skip-sweep", action="store_true")
    p.add_argument("--force", action="store_true", help="continue even if a self-check fails")
    return p.parse_args()


def jsonable(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (set, tuple)):
        return list(o)
    return str(o)


def main():
    a = parse()
    log = Log()
    if a.quick:
        a.seeds, a.n_boot = 4, 300
    scales = [0.5, 1, 2] if a.quick else [0.25, 0.5, 1, 2, 4]
    cfg = {"shots": qb.SHOTS, "seed_t": a.seed_t, "seed_s": a.seed_s, "opt": a.opt_level,
           "n_boot": a.n_boot}
    os.makedirs(os.path.join(a.outdir, "figures"), exist_ok=True)
    os.makedirs(os.path.join(a.outdir, "circuits"), exist_ok=True)
    log(f"config: {cfg}  headline={a.headline}  qiskit-ibm-runtime pinned={qb.PINNED_QISKIT_IBM_RUNTIME}")

    # ---------------- 1. native-noise matrix: the nine core cases + ablation -------------
    rows, plans, models = studies.run_matrix("native", studies.ALL_SCHEMES, cfg, "native", log)
    bad = studies.selfcheck(rows)
    if bad:
        print("\nSELF-CHECK FAILED:\n  " + "\n  ".join(bad), file=sys.stderr)
        if not a.force:
            sys.exit(1)
    log("self-check passed: ideal F = 1 and acceptance = 1 for every scheme; all circuits valid")
    core = studies.core_table(rows, a.headline)

    # ---------------- 2. graph-only comparison (common gate set + noise) -----------------
    rows_c, plans_c, models_c = studies.run_matrix("common", studies.ALL_SCHEMES, cfg, "graph_only", log)
    rows += rows_c
    bad = studies.selfcheck(rows_c)
    if bad and not a.force:
        print("\nSELF-CHECK FAILED (common):\n  " + "\n  ".join(bad), file=sys.stderr)
        sys.exit(1)

    # ---------------- 3. noise sweep -----------------------------------------------------
    if not a.skip_sweep:
        rows += studies.noise_sweep(models_c, plans_c, scales, ["plain", "zz", "zzxx", "mbr"], cfg, log)

    # ---------------- 4. uncertainty calibration over seeds ------------------------------
    rows += studies.seed_validation(models, plans, ["plain", a.headline, "mbr"], a.seeds, cfg, log)

    # ---------------- 5. transpiler level sensitivity + geometry metrics -----------------
    rows += studies.opt_level_study(models, log)
    geo = studies.geometry_table(models)

    # ---------------- 6. figures ---------------------------------------------------------
    log("drawing figures ...")
    fig_dir = os.path.join(a.outdir, "figures")
    for name, m in models.items():  # required deliverable: graphs with the ports highlighted
        try:
            qb.draw_model(m).savefig(os.path.join(fig_dir, f"graph_{name}.png"), dpi=150, bbox_inches="tight")
        except Exception as exc:  # pragma: no cover
            log(f"  draw_model({name}) failed: {exc}")
    figs = {
        "geometry": plots.fig_geometry(models, plans, geo),
        "core": plots.fig_core(core),
        "cost": plots.fig_cost(rows),
        "tradeoff": plots.fig_tradeoff(rows, "native"),
        "graph_only": plots.fig_graph_only(rows),
        "calibration": plots.fig_calibration(rows),
        "opt": plots.fig_opt(rows),
    }
    if not a.skip_sweep:
        figs["sweep"] = plots.fig_sweep(rows)
    for k, f in figs.items():
        f.savefig(os.path.join(fig_dir, f"{k}.png"), dpi=150, bbox_inches="tight")

    for name in studies.MODELS:  # compiled circuits of the headline protection and of MBR
        for scheme in (a.headline, "mbr", "plain"):
            try:
                plans[(name, scheme)].compiled["ZZ"].draw(
                    "mpl", idle_wires=False, filename=os.path.join(a.outdir, "circuits", f"{name}_{scheme}.png"))
            except Exception as exc:  # pragma: no cover
                log(f"  circuit drawing {name}/{scheme} skipped: {exc}")

    # ---------------- 7. tables, dashboard, raw data --------------------------------------
    tables = "\n".join([
        "## Core 3x3 grid (cases 1-9)\n", report.table_core(core),
        report.table_ablation(rows, "native", "All schemes, native noise (each model's own gate set + noise)"),
        report.table_ablation(rows, "graph_only", "All schemes, common noise (graph is the only difference)"),
        "### Geometry metrics\n", report.table_geometry(geo),
        "### Uncertainty calibration\n", report.table_calibration(rows),
        "### Transpiler optimization level (plain Bell, 2q gates / depth)\n", report.table_opt(rows),
    ])
    findings = report.auto_findings(rows, a.headline)
    with open(os.path.join(a.outdir, "tables.md"), "w", encoding="utf-8") as fh:
        fh.write(tables + "\n## Machine-written findings\n\n" + findings + "\n")
    with open(os.path.join(a.outdir, "results.json"), "w") as fh:
        json.dump({"config": cfg, "headline": a.headline, "core": core, "rows": rows, "geometry": geo},
                  fh, indent=1, default=jsonable)
    cols = ["study", "model", "noise_variant", "scheme", "mode", "scale", "seed_index", "F", "sigma_F",
            "verified", "XX", "YY", "ZZ", "accept", "n_discarded", "depth", "n2q", "swaps", "n_phys",
            "data_on_ports", "esp", "F_lo", "F_hi", "seed_t", "seed_sim"]
    with open(os.path.join(a.outdir, "results.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    sections = [("Machine-written findings", "md", findings),
                ("Core 3x3 grid", "fig", figs["core"]), ("Core table", "md", report.table_core(core)),
                ("Geometry of the three graphs", "fig", figs["geometry"]),
                ("Geometry metrics", "md", report.table_geometry(geo)),
                ("Circuit cost", "fig", figs["cost"]),
                ("Protection trade-off (native noise)", "fig", figs["tradeoff"]),
                ("All schemes, native noise", "md", report.table_ablation(rows, "native", "native")),
                ("Graph-only comparison", "fig", figs["graph_only"]),
                ("All schemes, common noise", "md", report.table_ablation(rows, "graph_only", "graph only"))]
    if not a.skip_sweep:
        sections.append(("Noise sensitivity", "fig", figs["sweep"]))
    sections += [("Uncertainty calibration", "fig", figs["calibration"]),
                 ("Uncertainty calibration table", "md", report.table_calibration(rows)),
                 ("Transpiler optimization level", "fig", figs["opt"])]
    report.dashboard(os.path.join(a.outdir, "dashboard.html"), sections)

    log(f"DONE. Open {os.path.join(a.outdir, 'dashboard.html')} in a browser.")
    print("\n" + findings)


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    main()
