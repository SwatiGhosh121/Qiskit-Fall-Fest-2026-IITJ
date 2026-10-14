"""Markdown tables, machine-written findings and a self-contained HTML dashboard."""

from __future__ import annotations

import base64
import html
import io
import math

import numpy as np

from . import analysis
from .plots import MODEL_LABEL, MODELS, SCHEME_LABEL


def _sel(rows, **kw):
    return [r for r in rows if all(r.get(k) == v for k, v in kw.items())]


def _f(r):
    return f"{r['F']:.4f} ± {r['sigma_F']:.4f}"


def table_core(core):
    h = ("| Case | Model | Condition | F ± σ_F | F−2σ>0.5 | Accept | Discarded | Depth | 2q gates | "
         "SWAPs | Phys. qubits | Data on ports? |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in core:
        h += (f"| {r['case']} | {r['model']} | {r['label']} | {_f(r)} | {'yes' if r['verified'] else 'NO'} | "
              f"{r['accept']:.3f} | {r['n_discarded']:,} | {r['depth']} | {r['n2q']} | {r['swaps']} | "
              f"{r['n_phys']} {r['phys_qubits']} | {'yes' if r['data_on_ports'] else 'no'} |\n")
    return h


def table_ablation(rows, study, title):
    h = (f"### {title}\n\n| Model | Scheme | F ± σ_F | bootstrap 95% CI | Accept | 2q | SWAPs | Depth | "
         "Phys. qubits | ΔF vs plain (z) |\n|---|---|---|---|---|---|---|---|---|---|\n")
    for m in MODELS:
        base = _sel(rows, study=study, model=m, scheme="plain", mode="noisy")[0]
        for s in ("plain", "zz", "xx", "zzxx", "mbr"):
            r = _sel(rows, study=study, model=m, scheme=s, mode="noisy")[0]
            if s == "plain":
                d = "–"
            else:
                c = analysis.compare(base, r)
                d = f"{c['delta_F']:+.4f} (z={c['z']:+.1f})"
            h += (f"| {m} | {SCHEME_LABEL.get(s, s)} | {_f(r)} | [{r['F_lo']:.4f}, {r['F_hi']:.4f}] | "
                  f"{r['accept']:.3f} | {r['n2q']} | {r['swaps']} | {r['depth']} | {r['n_phys']} | {d} |\n")
    return h + "\n"


def table_geometry(geo):
    keys = ["qubits", "couplers", "avg_degree", "max_degree", "port_distance", "n_shortest_paths",
            "ring_through_ports", "girth", "qubits_within_4_of_both_ports", "port_degrees"]
    h = "| Metric | " + " | ".join(MODELS) + " |\n|---|" + "---|" * len(MODELS) + "\n"
    for k in keys:
        vals = []
        for m in MODELS:
            v = geo[m][k]
            vals.append(f"{v:.2f}" if isinstance(v, float) else str(v))
        h += f"| {k} | " + " | ".join(vals) + " |\n"
    return h + "\n"


def table_calibration(rows):
    sv = _sel(rows, study="seed_validation")
    if not sv:
        return ""
    h = ("| Model | Scheme | seeds | mean F | empirical std | mean quoted σ_F | ratio |\n"
         "|---|---|---|---|---|---|---|\n")
    for m, s in sorted({(r["model"], r["scheme"]) for r in sv}):
        rr = _sel(sv, model=m, scheme=s)
        c = analysis.calibration_summary([r["F"] for r in rr], [r["sigma_F"] for r in rr])
        h += (f"| {m} | {s} | {c['n']} | {c['F_mean']:.4f} | {c['F_std_empirical']:.4f} | "
              f"{c['sigma_analytic_mean']:.4f} | {c['ratio']:.2f} |\n")
    return h + "\n"


def table_opt(rows):
    oo = _sel(rows, study="opt_levels")
    if not oo:
        return ""
    h = "| Model | " + " | ".join(f"opt {l}: 2q / depth" for l in range(4)) + " |\n|---|---|---|---|---|\n"
    for m in MODELS:
        cells = []
        for l in range(4):
            r = _sel(oo, model=m, opt=l)[0]
            cells.append(f"{r['n2q']} / {r['depth']}")
        h += f"| {m} | " + " | ".join(cells) + " |\n"
    return h + "\n"


def auto_findings(rows, headline):
    """Facts computed from the numbers (no interpretation beyond the sign and the z-score)."""
    out = []
    for study, tag in (("native", "native noise"), ("graph_only", "common noise (graph only)")):
        out.append(f"**{tag}**")
        for m in MODELS:
            base = _sel(rows, study=study, model=m, scheme="plain", mode="noisy")[0]
            out.append(f"- {m}: unprotected F = {_f(base)} with {base['n2q']} two-qubit gates "
                       f"({base['swaps']} SWAPs); data end on the ports: {base['data_on_ports']}.")
            for s in ("zz", "xx", "zzxx", "mbr"):
                r = _sel(rows, study=study, model=m, scheme=s, mode="noisy")[0]
                c = analysis.compare(base, r)
                verdict = ("improves" if c["z"] > 2 else "worsens" if c["z"] < -2 else
                           "is statistically indistinguishable from")
                extra = ""
                if s != "mbr":
                    extra = (f", keeping {100 * r['accept']:.1f}% of shots "
                             f"({r['n_discarded']:,} discarded), yield {r['yield']:.3f} vs {base['yield']:.3f}")
                out.append(f"  - {SCHEME_LABEL[s]} {verdict} the baseline: ΔF = {c['delta_F']:+.4f} "
                           f"(z = {c['z']:+.1f}), {r['n2q']} 2q gates, {r['n_phys']} qubits{extra}.")
    return "\n".join(out)


def _b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    return base64.b64encode(buf.getvalue()).decode()


def _md_to_html(md):
    """Very small markdown-table/bullet renderer (enough for our own output)."""
    lines, out, i = md.split("\n"), [], 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|"):
            tbl = []
            while i < len(lines) and lines[i].startswith("|"):
                tbl.append(lines[i])
                i += 1
            cells = [[c.strip() for c in t.strip("|").split("|")] for t in tbl if "---" not in t]
            out.append("<table>")
            for k, row in enumerate(cells):
                tag = "th" if k == 0 else "td"
                out.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in row) + "</tr>")
            out.append("</table>")
            continue
        if ln.startswith("###"):
            out.append(f"<h3>{html.escape(ln.strip('# '))}</h3>")
        elif ln.strip().startswith("- "):
            ind = (len(ln) - len(ln.lstrip())) // 2
            out.append(f"<div class='li' style='margin-left:{18 * ind}px'>• {html.escape(ln.strip()[2:])}</div>")
        elif ln.strip():
            out.append(f"<p>{html.escape(ln).replace('**', '')}</p>")
        i += 1
    return "\n".join(out)


def dashboard(path, sections):
    """sections: list of (title, kind, payload) with kind in {'md', 'fig'}."""
    body = []
    for title, kind, payload in sections:
        body.append(f"<h2>{html.escape(title)}</h2>")
        if kind == "fig":
            body.append(f"<img src='data:image/png;base64,{_b64(payload)}'/>")
        else:
            body.append(_md_to_html(payload))
    css = ("body{font-family:system-ui,Segoe UI,Arial;max-width:1150px;margin:24px auto;padding:0 16px;"
           "color:#111;line-height:1.45}h1{color:#4c1d95}h2{border-bottom:2px solid #ddd;padding-bottom:4px;"
           "margin-top:34px}table{border-collapse:collapse;font-size:12.5px;margin:10px 0;width:100%}"
           "th,td{border:1px solid #ccc;padding:4px 7px;text-align:left}th{background:#f3f4f6}"
           "img{max-width:100%}.li{font-size:14px}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"<html><head><meta charset='utf-8'><title>Geometry-aware Bell benchmark</title>"
                 f"<style>{css}</style></head><body><h1>Geometry-aware Bell benchmark: results dashboard</h1>"
                 + "\n".join(body) + "</body></html>")
