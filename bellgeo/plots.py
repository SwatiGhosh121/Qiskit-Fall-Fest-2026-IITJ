"""Matplotlib figures. Every function takes result rows (list of dicts) and returns a Figure."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

MODELS = ["2016", "contemporary", "hyperbolic"]
MODEL_LABEL = {"2016": "2016-inspired", "contemporary": "Contemporary (FakeFez)",
               "hyperbolic": "Hyperbolic {7,3}"}
SCHEME_COLOR = {"plain": "#6b7280", "zz": "#2563eb", "xx": "#0891b2", "zzxx": "#7c3aed",
                "mbr": "#16a34a"}
SCHEME_LABEL = {"plain": "plain (SWAP-routed)", "zz": "ZZ check", "xx": "XX check",
                "zzxx": "ZZ+XX check", "mbr": "measurement-based routing"}
PORT_A, PORT_B, QUBIT = "#2ca02c", "#7b3fe4", "#9db4d8"


def _sel(rows, **kw):
    return [r for r in rows if all(r.get(k) == v for k, v in kw.items())]


def fig_geometry(models, plans, geo):
    """Neighbourhood of the ports on each graph, ancilla sites coloured by ESP of the ZZ check."""
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.6))
    for ax, name in zip(axes, MODELS):
        m = models[name]
        plan = plans.get((name, "zz"))
        table = plan.placement_table if plan else []
        esp = {r["ancilla"]: r["esp"] for r in table}
        g = nx.Graph()
        g.add_edges_from(m.edges)
        keep = set(esp) | set(m.ports)
        if name in ("2016", "hyperbolic"):
            keep = set(g.nodes) if name == "2016" else set(g.nodes)
        sub = g.subgraph(keep)
        if m.positions:
            pos = {n: m.positions[n] for n in sub.nodes}
        else:
            pos = nx.kamada_kawai_layout(sub)
        cols = []
        for n in sub.nodes:
            if n == m.ports[0]:
                cols.append(PORT_A)
            elif n == m.ports[1]:
                cols.append(PORT_B)
            elif n in esp:
                cols.append(plt.cm.viridis((esp[n] - min(esp.values())) /
                                           (max(esp.values()) - min(esp.values()) + 1e-12)))
            else:
                cols.append("#e5e7eb")
        nx.draw_networkx_edges(sub, pos, ax=ax, edge_color="#5a6b8c", width=1.3)
        nx.draw_networkx_nodes(sub, pos, ax=ax, node_color=cols, node_size=360,
                               edgecolors="k", linewidths=0.6)
        nx.draw_networkx_labels(sub, pos, ax=ax, font_size=7)
        if table:
            best = table[0]["ancilla"]
            ax.scatter(*pos[best], s=900, facecolors="none", edgecolors="#dc2626", linewidths=2.5)
        gm = geo[name]
        ax.set_title(f"{MODEL_LABEL[name]}\nports {m.ports}, distance {gm['port_distance']}, "
                     f"ring through ports: {gm['ring_through_ports']}, girth: {gm['girth']}",
                     fontsize=10)
        ax.set_aspect("equal" if m.positions else "auto")
        ax.axis("off")
    fig.suptitle("Port neighbourhoods. Green = port A, purple = port B. Colour = estimated success "
                 "of the ZZ-check circuit with the ancilla at that qubit (red ring = chosen)",
                 fontsize=11)
    fig.tight_layout()
    return fig


def fig_core(core):
    fig, ax = plt.subplots(figsize=(10, 5))
    w = 0.26
    labels = ["ideal", "noisy", "noisy + protection"]
    colors = ["#9ca3af", "#ef4444", "#2563eb"]
    for j, lab in enumerate(labels):
        vals = [core[3 * i + j]["F"] for i in range(3)]
        errs = [2 * core[3 * i + j]["sigma_F"] for i in range(3)]
        bars = ax.bar(np.arange(3) + (j - 1) * w, vals, w, yerr=errs, capsize=3,
                      color=colors[j], label=lab)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.012, f"{v:.3f}", ha="center", fontsize=8)
    ax.axhline(0.5, ls="--", c="k", lw=1)
    ax.text(2.45, 0.505, "F = 0.5 (separable bound)", ha="right", fontsize=8)
    ax.set_xticks(range(3))
    ax.set_xticklabels([MODEL_LABEL[m] for m in MODELS])
    ax.set_ylim(0.4, 1.08)
    ax.set_ylabel("Bell fidelity F(Φ⁺)  (error bars: ±2σ)")
    ax.set_title("The 3×3 core grid (cases 1-9)")
    ax.legend(loc="lower left")
    fig.tight_layout()
    return fig


def fig_cost(rows):
    nat = _sel(rows, study="native", mode="noisy")
    schemes = ["plain", "zz", "xx", "zzxx", "mbr"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    w = 0.16
    for k, key, title in ((0, "n2q", "Two-qubit gates after compilation"),
                          (1, "depth", "Circuit depth after compilation")):
        ax = axes[k]
        for j, s in enumerate(schemes):
            vals = [_sel(nat, model=m, scheme=s)[0][key] for m in MODELS]
            bars = ax.bar(np.arange(3) + (j - 2) * w, vals, w, color=SCHEME_COLOR[s],
                          label=SCHEME_LABEL[s])
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v + 0.3, str(v), ha="center", fontsize=7)
        ax.set_xticks(range(3))
        ax.set_xticklabels([MODEL_LABEL[m] for m in MODELS])
        ax.set_title(title)
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    return fig


def fig_tradeoff(rows, study="native"):
    nat = _sel(rows, study=study, mode="noisy")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=False)
    for ax, m in zip(axes, MODELS):
        base = _sel(nat, model=m, scheme="plain")[0]
        ax.axhline(base["F"], c="#6b7280", ls="--", lw=1)
        ax.axhspan(base["F"] - 2 * base["sigma_F"], base["F"] + 2 * base["sigma_F"],
                   color="#6b7280", alpha=0.12)
        for s in ("plain", "zz", "xx", "zzxx", "mbr"):
            r = _sel(nat, model=m, scheme=s)[0]
            ax.errorbar(r["accept"], r["F"], yerr=2 * r["sigma_F"], fmt="o", ms=9,
                        color=SCHEME_COLOR[s], capsize=3, label=SCHEME_LABEL[s])
        ax.set_xlabel("acceptance fraction")
        ax.set_title(MODEL_LABEL[m])
        ax.set_xlim(0.4, 1.03)
    axes[0].set_ylabel("conditional fidelity F  (±2σ)")
    axes[0].legend(fontsize=7, loc="lower left")
    fig.suptitle("Protection trade-off: fidelity gain vs discarded shots (grey band = unprotected ±2σ)")
    fig.tight_layout()
    return fig


def fig_graph_only(rows):
    com = _sel(rows, study="graph_only", mode="noisy")
    fig, ax = plt.subplots(figsize=(11, 4.8))
    schemes = ["plain", "zz", "xx", "zzxx", "mbr"]
    w = 0.16
    for j, s in enumerate(schemes):
        vals = [_sel(com, model=m, scheme=s)[0] for m in MODELS]
        ax.bar(np.arange(3) + (j - 2) * w, [v["F"] for v in vals], w,
               yerr=[2 * v["sigma_F"] for v in vals], capsize=2, color=SCHEME_COLOR[s],
               label=SCHEME_LABEL[s])
    ax.set_xticks(range(3))
    ax.set_xticklabels([MODEL_LABEL[m].split(" (")[0] for m in MODELS])
    ax.set_ylim(0.7, 1.0)
    ax.set_ylabel("Bell fidelity (conditional)")
    ax.set_title("Graph-only comparison: identical gate set and noise (cz, FakeFez medians) on all graphs")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    return fig


def fig_sweep(rows):
    sw = _sel(rows, study="noise_sweep")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True)
    for ax, m in zip(axes, MODELS):
        for s in ("plain", "zz", "zzxx", "mbr"):
            rr = sorted(_sel(sw, model=m, scheme=s), key=lambda r: r["scale"])
            if not rr:
                continue
            x = [r["scale"] for r in rr]
            y = np.array([r["F"] for r in rr])
            e = np.array([2 * r["sigma_F"] for r in rr])
            ax.plot(x, y, "-o", color=SCHEME_COLOR[s], label=SCHEME_LABEL[s])
            ax.fill_between(x, y - e, y + e, color=SCHEME_COLOR[s], alpha=0.15)
        ax.set_xscale("log", base=2)
        ax.set_xlabel("noise scale (× FakeFez median rates)")
        ax.set_title(MODEL_LABEL[m].split(" (")[0])
        ax.axhline(0.5, ls="--", c="k", lw=0.8)
    axes[0].set_ylabel("Bell fidelity")
    axes[0].legend(fontsize=8)
    fig.suptitle("Noise sensitivity (common noise): where does protection / routing pay off?")
    fig.tight_layout()
    return fig


def fig_calibration(rows):
    sv = _sel(rows, study="seed_validation")
    keys = sorted({(r["model"], r["scheme"]) for r in sv})
    ratios, labels = [], []
    for m, s in keys:
        rr = _sel(sv, model=m, scheme=s)
        f = np.array([r["F"] for r in rr])
        sg = np.mean([r["sigma_F"] for r in rr])
        ratios.append(f.std(ddof=1) / sg if sg > 0 else np.nan)
        labels.append(f"{m}\n{s}")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(range(len(keys)), ratios, color="#2563eb")
    ax.axhline(1, c="k", ls="--")
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("empirical std of F / quoted σ_F")
    n = len({r["seed_index"] for r in sv})
    ax.set_title(f"Uncertainty calibration over {n} independent simulator seeds (1 = perfectly calibrated)")
    fig.tight_layout()
    return fig


def fig_opt(rows):
    oo = _sel(rows, study="opt_levels")
    fig, ax = plt.subplots(figsize=(7, 4))
    for m in MODELS:
        rr = sorted(_sel(oo, model=m), key=lambda r: r["opt"])
        ax.plot([r["opt"] for r in rr], [r["n2q"] for r in rr], "-o", label=MODEL_LABEL[m])
    ax.set_xlabel("Qiskit optimization_level")
    ax.set_ylabel("two-qubit gates (plain Bell)")
    ax.set_xticks([0, 1, 2, 3])
    ax.legend()
    fig.tight_layout()
    return fig
