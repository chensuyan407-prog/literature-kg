#!/usr/bin/env python3
"""Step 5: export the graph in editable formats plus rendered previews.

    python export_graph.py --graph work/graph/graph.json --out /app/output/graph [--queries work/graph/queries/query_results.json]

Writes graph.json (copy), nodes.csv, edges.csv, evidence.csv, graph.graphml, graph.mmd (Mermaid),
graph.dot, graph.svg + graph.png (overview: one column per paper, shared concepts in the middle),
graph.html (self-contained, searchable tables + SVG), and queries/<id>.svg|.png per query subgraph.
PNG needs matplotlib; without it, SVG/HTML are still written and the PNG is reported as skipped.
"""
import argparse
import csv
import html
import json
import os
import shutil
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kglib import read_json, write_json  # noqa: E402

COLORS = {"Paper": "#444444", "Researcher": "#8c6d31", "Material": "#1f77b4", "Sample": "#17becf", "Method": "#2ca02c", "Model": "#98df8a",
          "Task": "#9467bd", "Metric": "#e377c2", "Measurement": "#ff7f0e", "Conclusion": "#d62728", "Dataset": "#bcbd22",
          "Instrument": "#7f7f7f", "Condition": "#c49c94", "Mechanism": "#8c564b"}
TYPE_ORDER = list(COLORS)


def layout(nodes, sources, width_col=330, row_h=26):
    cols = [s["source_id"] for s in sources]
    if len(cols) >= 2:
        order = [cols[0], "__shared__"] + cols[1:]
    else:
        order = cols + ["__shared__"]
    buckets = defaultdict(list)
    for n in nodes:
        if n["type"] == "Researcher" and n.get("attribution") == ["metadata"]:
            continue  # authors are listed in tables, not drawn (keeps overview legible)
        col = "__shared__" if len(n["sources"]) > 1 else n["sources"][0]
        buckets[col].append(n)
    pos, height = {}, 0
    for ci, col in enumerate(order):
        y = 60
        for n in sorted(buckets[col], key=lambda n: (TYPE_ORDER.index(n["type"]) if n["type"] in TYPE_ORDER else 99, n["label"].lower())):
            pos[n["id"]] = (40 + ci * width_col, y)
            y += row_h
        height = max(height, y)
    return pos, order, max(height + 60, 220), 40 + len(order) * width_col


def esc(s):
    return html.escape(str(s), quote=True)


def svg(graph, node_ids=None, edge_ids=None, title=""):
    nodes = [n for n in graph["nodes"] if node_ids is None or n["id"] in node_ids]
    edges = [e for e in graph["edges"] if (edge_ids is None or e["id"] in edge_ids)]
    pos, order, H, W = layout(nodes, graph["sources"])
    edges = [e for e in edges if e["source"] in pos and e["target"] in pos]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif" font-size="11">',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>', f'<text x="20" y="20" font-size="14" font-weight="bold">{esc(title)}</text>']
    for ci, col in enumerate(order):
        lab = "concepts in >=2 papers (one node, per-paper edges)" if col == "__shared__" else f"paper {col}"
        out.append(f'<text x="{40 + ci * 330}" y="44" font-size="12" font-weight="bold" fill="#333">{esc(lab)}</text>')
    for e in edges:
        (x1, y1), (x2, y2) = pos[e["source"]], pos[e["target"]]
        col = "#999" if e["strength"] == "direct" else "#d62728"
        dash = "" if e["strength"] == "direct" else ' stroke-dasharray="4,3"'
        if x1 == x2:
            mx = x1 + 150 + min(abs(y2 - y1) / 4, 120)
            d = f"M{x1 + 6},{y1} Q{mx},{(y1 + y2) / 2} {x2 + 6},{y2}"
        else:
            d = f"M{x1 + 6},{y1} L{x2 - 6},{y2}"
        out.append(f'<path d="{d}" stroke="{col}" stroke-width="0.8" fill="none" opacity="0.55"{dash}><title>{esc(e["predicate"])} [{esc(e["source_id"])} {esc(e["evidence"][0]["paragraph_id"])}] {esc(e["evidence"][0]["quote"][:200])}</title></path>')
    for n in nodes:
        if n["id"] not in pos:
            continue
        x, y = pos[n["id"]]
        c = COLORS.get(n["type"], "#000")
        lab = n["label"] if len(n["label"]) <= 42 else n["label"][:40] + "…"
        out.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{c}"><title>{esc(n["id"])}</title></circle>'
                   f'<text x="{x + 10}" y="{y + 4}">{esc(lab)} <tspan fill="#888" font-size="9">{esc(n["type"])}</tspan></text>')
    for i, (t, c) in enumerate(COLORS.items()):
        lx, ly = 40 + (i % 7) * 120, H - 38 + (i // 7) * 18
        out.append(f'<circle cx="{lx}" cy="{ly}" r="5" fill="{c}"/><text x="{lx + 8}" y="{ly + 4}" font-size="10">{t}</text>')
    out.append("</svg>")
    return "\n".join(out), (pos, nodes, edges, W, H, order)


def png(path, lay, title):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:  # noqa: BLE001
        return f"skipped: matplotlib unavailable ({e})"
    pos, nodes, edges, W, H, order = lay
    fig = plt.figure(figsize=(W / 80, H / 80), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    ax.text(20, 20, title, fontsize=11, weight="bold", va="center")
    for ci, col in enumerate(order):
        ax.text(40 + ci * 330, 44, "concepts in >=2 papers (one node, per-paper edges)" if col == "__shared__" else f"paper {col}", fontsize=9.5, weight="bold", va="center")
    for e in edges:
        (x1, y1), (x2, y2) = pos[e["source"]], pos[e["target"]]
        ax.plot([x1, x2 if x1 != x2 else x2 + 40, x2] if x1 == x2 else [x1, x2], [y1, (y1 + y2) / 2, y2] if x1 == x2 else [y1, y2],
                color="#999" if e["strength"] == "direct" else "#d62728", lw=0.6, alpha=0.5, ls="-" if e["strength"] == "direct" else "--")
    for n in nodes:
        if n["id"] in pos:
            x, y = pos[n["id"]]
            ax.scatter([x], [y], s=28, color=COLORS.get(n["type"], "#000"), zorder=3)
            lab = n["label"] if len(n["label"]) <= 42 else n["label"][:40] + "…"
            ax.text(x + 9, y, f"{lab}  [{n['type']}]", fontsize=7.5, va="center")
    for i, (t, c) in enumerate(COLORS.items()):
        lx, ly = 40 + (i % 7) * 120, H - 38 + (i // 7) * 18
        ax.scatter([lx], [ly], s=20, color=c)
        ax.text(lx + 8, ly, t, fontsize=7, va="center")
    fig.savefig(path)
    plt.close(fig)
    return "ok"


def graphml(graph):
    keys = [("label", "node"), ("type", "node"), ("scope", "node"), ("sources", "node"), ("aliases", "node"), ("evidence", "node"),
            ("predicate", "edge"), ("source_id", "edge"), ("strength", "edge"), ("conditions", "edge"), ("paragraph_id", "edge"), ("quote", "edge")]
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">']
    for k, f in keys:
        out.append(f'<key id="{f[0]}_{k}" for="{f}" attr.name="{k}" attr.type="string"/>')
    out.append('<graph id="G" edgedefault="directed">')
    for n in graph["nodes"]:
        ev = "; ".join(f"{x['source_id']}:{x['paragraph_id']}" for x in n["evidence"][:6])
        vals = {"label": n["label"], "type": n["type"], "scope": n["scope"], "sources": ",".join(n["sources"]), "aliases": "|".join(n["aliases"]), "evidence": ev}
        out.append(f'<node id="{esc(n["id"])}">' + "".join(f'<data key="n_{k}">{esc(v)}</data>' for k, v in vals.items()) + "</node>")
    for e in graph["edges"]:
        ev = e["evidence"][0]
        vals = {"predicate": e["predicate"], "source_id": e["source_id"], "strength": e["strength"], "conditions": json.dumps(e.get("conditions", {}), ensure_ascii=False),
                "paragraph_id": ev["paragraph_id"], "quote": ev["quote"]}
        out.append(f'<edge id="{esc(e["id"])}" source="{esc(e["source"])}" target="{esc(e["target"])}">' + "".join(f'<data key="e_{k}">{esc(v)}</data>' for k, v in vals.items()) + "</edge>")
    out += ["</graph>", "</graphml>"]
    return "\n".join(out)


def mermaid(graph):
    ids = {n["id"]: f"n{i}" for i, n in enumerate(graph["nodes"])}
    out = ["graph LR"]
    for n in graph["nodes"]:
        if n["type"] == "Researcher" and n.get("attribution") == ["metadata"]:
            continue
        lab = n["label"].replace('"', "'")[:50]
        out.append(f'  {ids[n["id"]]}["{lab} ({n["type"]})"]')
    for e in graph["edges"]:
        if e["predicate"] == "AUTHOR_OF":
            continue
        arrow = "-->" if e["strength"] == "direct" else "-.->"
        out.append(f'  {ids[e["source"]]} {arrow}|{e["predicate"]} {e["source_id"]}| {ids[e["target"]]}')
    return "\n".join(out)


def dot(graph):
    out = ["digraph KG {", "  rankdir=LR; node [shape=box,fontsize=10];"]
    for n in graph["nodes"]:
        out.append(f'  "{n["id"]}" [label="{n["label"][:50]}\\n[{n["type"]}]" color="{COLORS.get(n["type"], "#000")}"];')
    for e in graph["edges"]:
        out.append(f'  "{e["source"]}" -> "{e["target"]}" [label="{e["predicate"]} {e["source_id"]}:{e["evidence"][0]["paragraph_id"]}"{" style=dashed" if e["strength"] != "direct" else ""}];')
    out.append("}")
    return "\n".join(out)


def html_page(graph, svg_text, queries):
    nodes_rows = "".join(f"<tr><td>{esc(n['id'])}</td><td>{esc(n['type'])}</td><td>{esc(n['label'])}</td><td>{esc(', '.join(n['aliases']))}</td><td>{esc(', '.join(n['sources']))}</td>"
                         f"<td>{esc(' | '.join(x['source_id'] + ':' + x['paragraph_id'] + ' “' + x['quote'][:120] + '”' for x in n['evidence'][:2]))}</td></tr>" for n in graph["nodes"])
    lab = {n["id"]: n["label"] for n in graph["nodes"]}
    edge_rows = "".join(f"<tr><td>{esc(lab[e['source']])}</td><td>{esc(e['predicate'])}</td><td>{esc(lab[e['target']])}</td><td>{esc(e['source_id'])}</td><td>{esc(e['evidence'][0]['paragraph_id'])}</td>"
                        f"<td>{esc(e['strength'])}{' ⚠' if e.get('needs_review') else ''}</td><td>{esc(json.dumps(e.get('conditions', {}), ensure_ascii=False))}</td><td>“{esc(e['evidence'][0]['quote'][:220])}”</td></tr>" for e in graph["edges"])
    conf = "".join(f"<li><b>{esc(c['kind'])}</b> {esc(c.get('names') or c.get('abbreviation') or c.get('key'))}: {esc(c.get('reason', ''))}</li>" for c in graph["conflicts"])
    merges = "".join(f"<li>{esc(m['scope'])}: {esc(' = '.join(m['merged']))} — {esc(m['basis'])}</li>" for m in graph["merge_log"])
    qs = "".join(f"<li><b>{esc(q.get('id'))}</b> {esc(q.get('question'))} → {esc(q['status'])} ({len(q['edges'])} edges)</li>" for q in (queries or []))
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Literature knowledge graph</title>
<style>body{{font-family:Arial,sans-serif;margin:16px;color:#222;background:#fff}}table{{border-collapse:collapse;font-size:12px;width:100%}}td,th{{border:1px solid #ddd;padding:3px;vertical-align:top}}
input{{width:300px;padding:4px}}.wrap{{overflow:auto;border:1px solid #eee;max-height:700px}}</style></head><body>
<h1>Literature knowledge graph</h1><p>{len(graph['nodes'])} nodes, {len(graph['edges'])} edges, sources: {esc(', '.join(s['source_id'] + ' (' + str(s.get('doi')) + ')' for s in graph['sources']))}.
Locations are organiser paragraph IDs, not PDF pages.</p>
<p><input id="f" placeholder="filter rows…" oninput="for(const r of document.querySelectorAll('tbody tr'))r.style.display=r.textContent.toLowerCase().includes(this.value.toLowerCase())?'':'none'"></p>
<h2>Queries</h2><ul>{qs}</ul><h2>Merges</h2><ul>{merges}</ul><h2>Not merged / conflicts</h2><ul>{conf}</ul>
<h2>Overview</h2><div class="wrap">{svg_text}</div>
<h2>Edges</h2><table><thead><tr><th>subject</th><th>predicate</th><th>object</th><th>paper</th><th>¶</th><th>strength</th><th>conditions</th><th>quote</th></tr></thead><tbody>{edge_rows}</tbody></table>
<h2>Nodes</h2><table><thead><tr><th>id</th><th>type</th><th>label</th><th>aliases</th><th>papers</th><th>evidence</th></tr></thead><tbody>{nodes_rows}</tbody></table>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--queries")
    a = ap.parse_args()
    g = read_json(a.graph)
    os.makedirs(a.out, exist_ok=True)
    report = {}
    if os.path.abspath(a.graph) != os.path.abspath(os.path.join(a.out, "graph.json")):
        shutil.copy(a.graph, os.path.join(a.out, "graph.json"))
    lab = {n["id"]: n["label"] for n in g["nodes"]}
    with open(os.path.join(a.out, "nodes.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "type", "label", "aliases", "scope", "sources", "first_paragraph", "first_quote"])
        for n in g["nodes"]:
            w.writerow([n["id"], n["type"], n["label"], "|".join(n["aliases"]), n["scope"], ",".join(n["sources"]), n["evidence"][0]["paragraph_id"], n["evidence"][0]["quote"]])
    with open(os.path.join(a.out, "edges.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "subject_id", "subject", "predicate", "object_id", "object", "source_id", "paragraph_id", "quote", "strength", "attribution", "conditions", "needs_review"])
        for e in g["edges"]:
            ev = e["evidence"][0]
            w.writerow([e["id"], e["source"], lab[e["source"]], e["predicate"], e["target"], lab[e["target"]], e["source_id"], ev["paragraph_id"], ev["quote"],
                        e["strength"], e["attribution"], json.dumps(e.get("conditions", {}), ensure_ascii=False), e.get("needs_review", False)])
    with open(os.path.join(a.out, "evidence.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["item_kind", "item_id", "source_id", "paragraph_id", "match", "quote"])
        for n in g["nodes"]:
            for ev in n["evidence"]:
                w.writerow(["node", n["id"], ev["source_id"], ev["paragraph_id"], ev.get("match"), ev["quote"]])
        for e in g["edges"]:
            for ev in e["evidence"]:
                w.writerow(["edge", e["id"], ev["source_id"], ev["paragraph_id"], ev.get("match"), ev["quote"]])
    for name, txt in (("graph.graphml", graphml(g)), ("graph.mmd", mermaid(g)), ("graph.dot", dot(g))):
        with open(os.path.join(a.out, name), "w", encoding="utf-8") as f:
            f.write(txt)
    s, lay = svg(g, title=f"Knowledge graph: {len(g['nodes'])} nodes, {len(g['edges'])} edges (dashed red = hedged/indirect/cited)")
    with open(os.path.join(a.out, "graph.svg"), "w", encoding="utf-8") as f:
        f.write(s)
    report["graph.png"] = png(os.path.join(a.out, "graph.png"), lay, "Knowledge graph overview")
    queries = read_json(a.queries, []) if a.queries else []
    if queries:
        qd = os.path.join(a.out, "queries")
        os.makedirs(qd, exist_ok=True)
        for q in queries:
            if not q.get("edges") and not q.get("nodes"):
                continue
            nid = {n["id"] for n in q["nodes"]} | {e["subject_id"] for e in q["edges"]} | {e["object_id"] for e in q["edges"]}
            qs, ql = svg(g, nid, {e["id"] for e in q["edges"]}, title=f"{q.get('id')}: {q.get('question', '')[:110]}")
            with open(os.path.join(qd, f"{q.get('id')}.svg"), "w", encoding="utf-8") as f:
                f.write(qs)
            report[f"queries/{q.get('id')}.png"] = png(os.path.join(qd, f"{q.get('id')}.png"), ql, f"{q.get('id')}: {q.get('question', '')[:110]}")
    with open(os.path.join(a.out, "graph.html"), "w", encoding="utf-8") as f:
        f.write(html_page(g, s, queries))
    write_json(os.path.join(a.out, "export_report.json"), report)
    print("export:", a.out, report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
