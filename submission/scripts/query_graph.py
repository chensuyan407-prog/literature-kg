#!/usr/bin/env python3
"""Step 4: query the graph; every answer carries its subgraph, evidence and uncertain parts.

Single query:
    python query_graph.py --graph work/graph/graph.json find "graphene oxide"
    python query_graph.py --graph G neighbors "MGO" [--predicate HAS_RESULT] [--depth 2] [--source paper-A]
    python query_graph.py --graph G path "humic acid" "phenol"
    python query_graph.py --graph G type Measurement [--source S]
    python query_graph.py --graph G predicate FITS [--source S]
    python query_graph.py --graph G shared            # concepts present in >=2 papers, per-paper edges side by side
    python query_graph.py --graph G uncertain         # hedged / needs_review / conflicts / rejected
    python query_graph.py --graph G evidence R:abc123
Batch (what run_all.py uses):
    python query_graph.py --graph G --spec work/queries.json --out OUTDIR
    spec = [{"id": "q1", "question": "...", "op": "neighbors", "args": ["MGO"], "predicate": "HAS_RESULT", "depth": 1, "source": null}, ...]
An empty result is reported as status "no_result" with the reason (name not found / no edge of that type).
"""
import argparse
import json
import os
import sys
from collections import defaultdict, deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kglib import read_json, write_json, name_key, norm_text  # noqa: E402


class Graph:
    def __init__(self, g):
        self.g = g
        self.nodes = {n["id"]: n for n in g["nodes"]}
        self.edges = {e["id"]: e for e in g["edges"]}
        self.out, self.inc = defaultdict(list), defaultdict(list)
        for e in g["edges"]:
            self.out[e["source"]].append(e)
            self.inc[e["target"]].append(e)

    def resolve(self, name, source=None):
        """Node ids matching a name/alias/id. Exact key match first, then substring."""
        if name in self.nodes:
            return [name], "id"
        k = name_key(name)
        hits = [n["id"] for n in self.nodes.values() if k in {name_key(x) for x in [n["label"]] + n["aliases"]}]
        how = "name_or_alias"
        if not hits:
            nk = norm_text(name)
            hits = [n["id"] for n in self.nodes.values() if any(nk in norm_text(x) for x in [n["label"]] + n["aliases"])]
            how = "substring"
        if source:
            hits = [h for h in hits if source in self.nodes[h]["sources"]]
        return sorted(hits), how

    def sub(self, node_ids, edge_ids):
        ns = [self.brief(self.nodes[i]) for i in sorted(node_ids) if i in self.nodes]
        es = sorted((self.edge_view(self.edges[i]) for i in edge_ids), key=lambda e: (e["source_id"], e["predicate"], e["subject"], e["object"]))
        return ns, es

    @staticmethod
    def brief(n):
        return {"id": n["id"], "type": n["type"], "label": n["label"], "aliases": n["aliases"][:6], "scope": n["scope"], "sources": n["sources"],
                "attributes": n.get("attributes", {}), "evidence": [{k: ev.get(k) for k in ("source_id", "paragraph_id", "quote", "match")} for ev in n["evidence"][:3]]}

    def edge_view(self, e):
        return {"id": e["id"], "subject": self.nodes[e["source"]]["label"], "predicate": e["predicate"], "object": self.nodes[e["target"]]["label"],
                "subject_id": e["source"], "object_id": e["target"], "source_id": e["source_id"], "conditions": e.get("conditions", {}),
                "strength": e["strength"], "attribution": e["attribution"], "polarity": e.get("polarity"), "needs_review": e.get("needs_review", False),
                "flags": e.get("flags", []), "evidence": [{k: ev.get(k) for k in ("source_id", "paragraph_id", "quote", "match")} for ev in e["evidence"][:3]]}


def uncertain_of(G, edge_ids):
    out = []
    for i in edge_ids:
        e = G.edges[i]
        if e["strength"] in ("hedged", "cited", "indirect") or e.get("needs_review") or e["evidence"][0].get("match") == "approx":
            out.append({"edge": i, "why": [x for x in [e["strength"] if e["strength"] != "direct" else None,
                                                       "needs_review" if e.get("needs_review") else None,
                                                       "approximate quote match" if e["evidence"][0].get("match") == "approx" else None] if x] + e.get("flags", [])})
    return out


def run(G, op, args, predicate=None, depth=1, source=None):
    res = {"op": op, "args": args, "predicate": predicate, "depth": depth, "source": source}
    nodes, edges, notes = set(), set(), []
    if op in ("find", "neighbors"):
        hits, how = G.resolve(args[0], source)
        res["resolved"] = {"query": args[0], "matched_by": how, "nodes": hits}
        if not hits:
            return {**res, "status": "no_result", "reason": f"no node named or aliased '{args[0]}'" + (f" in {source}" if source else ""),
                    "nodes": [], "edges": [], "uncertain": []}
        if how == "substring" and len(hits) > 1:
            notes.append(f"'{args[0]}' matched {len(hits)} nodes by substring; results include all of them")
        if len(hits) > 1:
            notes.append(f"'{args[0]}' names {len(hits)} distinct nodes (" + "; ".join(f"{G.nodes[h]['label']} [{G.nodes[h]['type']}, {','.join(G.nodes[h]['sources'])}]" for h in hits)
                         + ") — they were deliberately not merged; read results per paper")
        k = name_key(args[0])
        labels = {name_key(x) for h in hits for x in [G.nodes[h]["label"]] + G.nodes[h]["aliases"]} | {k}
        res["related_conflicts"] = [c for c in G.g.get("conflicts", []) if
                                    labels & {name_key(str(x)) for x in (c.get("names") or []) + [c.get("abbreviation") or "", c.get("key") or ""] if x}]
        nodes |= set(hits)
        if op == "neighbors":
            frontier = deque((h, 0) for h in hits)
            seen = set(hits)
            while frontier:
                nid, d = frontier.popleft()
                if d >= depth:
                    continue
                for e in G.out[nid] + G.inc[nid]:
                    if predicate and e["predicate"] not in predicate.split(","):
                        continue
                    if source and e["source_id"] != source:
                        continue
                    edges.add(e["id"])
                    other = e["target"] if e["source"] == nid else e["source"]
                    nodes.add(other)
                    if other not in seen:
                        seen.add(other)
                        frontier.append((other, d + 1))
            if not edges:
                notes.append("node exists but has no edge" + (f" of type {predicate}" if predicate else "") + (f" in {source}" if source else ""))
    elif op == "path":
        a, _ = G.resolve(args[0], source)
        b, _ = G.resolve(args[1], source)
        res["resolved"] = {"from": a, "to": b}
        if not a or not b:
            return {**res, "status": "no_result", "reason": "endpoint not found: " + ", ".join(x for x, h in ((args[0], a), (args[1], b)) if not h), "nodes": [], "edges": [], "uncertain": []}
        prev, q, goal = {x: None for x in a}, deque(a), set(b)
        found = None
        while q:
            x = q.popleft()
            if x in goal:
                found = x
                break
            for e in G.out[x] + G.inc[x]:
                if source and e["source_id"] != source:
                    continue
                y = e["target"] if e["source"] == x else e["source"]
                if y not in prev:
                    prev[y] = (x, e["id"])
                    q.append(y)
        if not found:
            return {**res, "status": "no_result", "reason": "no connecting path (the papers may not link these objects)", "nodes": [], "edges": [], "uncertain": []}
        x = found
        while x is not None:
            nodes.add(x)
            if prev[x]:
                edges.add(prev[x][1])
                x = prev[x][0]
            else:
                x = None
        notes.append("a path through a shared concept node connects two papers' statements; it is navigation, not a combined finding")
    elif op == "type":
        nodes |= {n["id"] for n in G.nodes.values() if n["type"] == args[0] and (not source or source in n["sources"])}
        for n in list(nodes):
            for e in G.out[n] + G.inc[n]:
                if (not predicate or e["predicate"] in predicate.split(",")) and (not source or e["source_id"] == source):
                    edges.add(e["id"])
                    nodes |= {e["source"], e["target"]}
    elif op == "predicate":
        for e in G.edges.values():
            if e["predicate"] in args[0].split(",") and (not source or e["source_id"] == source):
                edges.add(e["id"])
                nodes |= {e["source"], e["target"]}
    elif op == "shared":
        shared = [n for n in G.nodes.values() if len(n["sources"]) > 1]
        res["per_concept"] = []
        for n in shared:
            per = defaultdict(list)
            for e in G.out[n["id"]] + G.inc[n["id"]]:
                if predicate and e["predicate"] not in predicate.split(","):
                    continue
                per[e["source_id"]].append(G.edge_view(e))
                edges.add(e["id"])
                nodes |= {e["source"], e["target"]}
            nodes.add(n["id"])
            res["per_concept"].append({"concept": n["label"], "id": n["id"], "type": n["type"], "sources": n["sources"],
                                       "edges_by_paper": dict(per), "evidence_by_paper": {s: [ev for ev in n["evidence"] if ev["source_id"] == s][:2] for s in n["sources"]}})
        res["not_merged"] = [c for c in G.g.get("conflicts", []) if c.get("scope") == "cross_paper"]
        notes.append("shared = same general concept term; paper-scoped samples, conditions and values are listed per paper and are not combined")
    elif op == "uncertain":
        edges |= {i for i, e in G.edges.items() if e["strength"] != "direct" or e.get("needs_review") or e.get("flags")}
        for i in edges:
            nodes |= {G.edges[i]["source"], G.edges[i]["target"]}
        res["conflicts"] = G.g.get("conflicts", [])
        res["rejected"] = [{k: r.get(k) for k in ("kind", "source_id", "name", "reason")} | {"item": r.get("item")} for r in G.g.get("rejected", [])]
        res["not_reported"] = G.g.get("not_reported", {})
    elif op == "evidence":
        if args[0] in G.edges:
            edges.add(args[0])
            nodes |= {G.edges[args[0]]["source"], G.edges[args[0]]["target"]}
        elif args[0] in G.nodes:
            nodes.add(args[0])
        else:
            return {**res, "status": "no_result", "reason": f"no node or edge with id {args[0]}", "nodes": [], "edges": [], "uncertain": []}
    else:
        return {**res, "status": "error", "reason": f"unknown op {op}", "nodes": [], "edges": [], "uncertain": []}
    ns, es = G.sub(nodes, edges)
    status = "ok" if (es or (op in ("find", "evidence") and ns) or res.get("per_concept")) else "no_result"
    out = {**res, "status": status, "notes": notes, "nodes": ns, "edges": es, "uncertain": uncertain_of(G, edges)}
    if status == "no_result" and "reason" not in out:
        out["reason"] = notes[0] if notes else "no matching edges"
    return out


def to_md(q, r):
    lines = [f"### {q.get('id', '')}: {q.get('question', '')}", "", f"`{r['op']} {' '.join(map(str, r['args']))}`"
             + (f" predicate={r['predicate']}" if r.get("predicate") else "") + (f" source={r['source']}" if r.get("source") else "")
             + f" → **{r['status']}** ({len(r['nodes'])} nodes, {len(r['edges'])} edges)", ""]
    if r.get("reason"):
        lines.append(f"Reason: {r['reason']}\n")
    for n in r.get("notes", []):
        lines.append(f"> {n}\n")
    if r["edges"]:
        lines += ["| subject | predicate | object | paper | ¶ | strength | conditions | quote |", "|-|-|-|-|-|-|-|-|"]
        for e in r["edges"][:60]:
            ev = e["evidence"][0]
            cond = "; ".join(f"{k}={v}" for k, v in (e["conditions"] or {}).items()) if isinstance(e["conditions"], dict) else str(e["conditions"])
            qt = (ev.get("quote") or "").replace("|", "/")
            lines.append(f"| {e['subject']} | {e['predicate']} | {e['object']} | {e['source_id']} | {ev.get('paragraph_id')} | {e['strength']}{' ⚠' if e['needs_review'] else ''} | {cond} | “{qt[:160]}” |")
    if r.get("op") == "find" and r["nodes"]:
        lines += ["| node | type | papers | evidence |", "|-|-|-|-|"]
        for n in r["nodes"]:
            ev = n["evidence"][0] if n["evidence"] else {}
            lines.append(f"| {n['label']} ({', '.join(n['aliases'][:3])}) | {n['type']} | {', '.join(n['sources'])} | {ev.get('source_id')}:{ev.get('paragraph_id')} “{(ev.get('quote') or '')[:120]}” |")
    if r.get("related_conflicts"):
        lines += ["", "Related alignment records:"] + [f"- {c['kind']}: {c.get('names') or c.get('abbreviation') or c.get('key')} — {c.get('reason', '')} ({c.get('decision', '')})" for c in r["related_conflicts"][:10]]
    if r.get("not_merged"):
        lines += ["", "Not merged across papers:"] + [f"- {c['kind']}: {c.get('names') or c.get('abbreviation')} — {c['reason']}" for c in r["not_merged"][:20]]
    if r.get("uncertain"):
        lines += ["", "Uncertain:"] + [f"- {u['edge']}: {', '.join(u['why'])}" for u in r["uncertain"][:20]]
    return "\n".join(lines) + "\n"


DEFAULT_SPEC = [
    {"id": "q_shared", "question": "Which concepts occur in more than one paper, and what does each paper say about them (kept separate)?", "op": "shared", "args": []},
    {"id": "q_results", "question": "Which reported results (Measurement) exist per paper, with conditions and evidence?", "op": "type", "args": ["Measurement"]},
    {"id": "q_uncertain", "question": "Which relations are hedged, cited, flagged, rejected or in conflict?", "op": "uncertain", "args": []},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True)
    ap.add_argument("--spec")
    ap.add_argument("--out")
    ap.add_argument("--predicate")
    ap.add_argument("--depth", type=int, default=1)
    ap.add_argument("--source")
    ap.add_argument("op", nargs="?")
    ap.add_argument("args", nargs="*")
    a = ap.parse_args()
    G = Graph(read_json(a.graph))
    if a.spec or not a.op:
        spec = read_json(a.spec, None) if a.spec else None
        if not spec:
            spec = DEFAULT_SPEC
        elif isinstance(spec, dict):
            spec = spec.get("queries", [])
        ids = {q.get("id") for q in spec}
        spec = spec + [q for q in DEFAULT_SPEC if q["id"] not in ids]
        out = a.out or os.path.join(os.path.dirname(a.graph), "queries")
        os.makedirs(out, exist_ok=True)
        results, md = [], ["# Executed graph queries\n"]
        for q in spec:
            try:
                r = run(G, q["op"], q.get("args", []), q.get("predicate"), q.get("depth", 1), q.get("source"))
            except Exception as e:  # noqa: BLE001
                r = {"op": q.get("op"), "args": q.get("args"), "status": "error", "reason": f"{type(e).__name__}: {e}", "nodes": [], "edges": [], "uncertain": []}
            r = {"id": q.get("id"), "question": q.get("question"), **r}
            results.append(r)
            md.append(to_md(q, r))
            print(f"  {q.get('id')}: {r['status']}  nodes={len(r['nodes'])} edges={len(r['edges'])}  {r.get('reason', '')}")
        write_json(os.path.join(out, "query_results.json"), results)
        with open(os.path.join(out, "query_results.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(md))
        return 0
    r = run(G, a.op, a.args, a.predicate, a.depth, a.source)
    print(json.dumps(r, ensure_ascii=False, indent=1)[:20000])
    return 0 if r["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
