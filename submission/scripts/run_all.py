#!/usr/bin/env python3
"""Steps 3-6 in one call: build graph -> run queries -> export -> result.json -> self-check.

    python run_all.py --input /input --work /app/work --out /app/output [--previous OLD/graph.json]

Needs work/corpus/* (ingest.py) and work/extract/<source_id>.json (agent). Optional:
work/queries.json (query spec, see query_graph.py), work/contract_fill.json (values for
output_contract fields that cannot be filled from the graph), work/notes.json
({"uncertainty": [...], "not_reported": [...]}).
Always writes /app/output/result.json, even when an earlier step fails (status partial/failed).
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kglib import read_json, write_json, VERSION  # noqa: E402


def step(cmd, log):
    t = time.time()
    p = subprocess.run([sys.executable, "-X", "utf8"] + cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log.append({"cmd": " ".join(os.path.basename(c) if i == 0 else c for i, c in enumerate(cmd)), "exit": p.returncode,
                "seconds": round(time.time() - t, 2), "stdout_tail": p.stdout[-3000:], "stderr_tail": p.stderr[-2000:]})
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr[-2000:])
    return p.returncode


SYN = {  # contract key pattern -> our field
    r"^(graph|knowledge_graph|kg)$": "graph", r"node": "nodes", r"(edge|relation|triple)": "edges", r"(entit)": "nodes",
    r"(quer)": "queries", r"(align|merge|dedup|canonical|alias)": "alignment", r"(conflict|non_merge|not_merged|distinct)": "conflicts",
    r"(uncertain|limitation|unknown|undecid)": "uncertainty", r"(source|provenance|corpus|paper)": "sources",
    r"(evidence|citation)": "evidence_index", r"(status|state)": "status", r"(change|increment|update)": "change_log",
    r"(not_reported|missing|unreported)": "not_reported", r"(export|file|artifact)": "artifacts", r"(stat|summary|count)": "stats",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/input")
    ap.add_argument("--work", default="/app/work")
    ap.add_argument("--out", default="/app/output")
    ap.add_argument("--previous")
    a = ap.parse_args()
    t0 = time.time()
    log = []
    os.makedirs(a.out, exist_ok=True)
    gpath = os.path.join(a.work, "graph", "graph.json")
    rc_b = step([os.path.join(HERE, "build_graph.py"), "--work", a.work] + (["--previous", a.previous] if a.previous else []), log)
    qdir = os.path.join(a.work, "graph", "queries")
    spec = os.path.join(a.work, "queries.json")
    rc_q = step([os.path.join(HERE, "query_graph.py"), "--graph", gpath, "--out", qdir] + (["--spec", spec] if os.path.exists(spec) else []), log) if rc_b == 0 else 9
    rc_e = step([os.path.join(HERE, "export_graph.py"), "--graph", gpath, "--out", os.path.join(a.out, "graph"),
                 "--queries", os.path.join(qdir, "query_results.json")], log) if rc_b == 0 else 9
    g = read_json(gpath, {}) or {}
    queries = read_json(os.path.join(qdir, "query_results.json"), []) or []
    if queries:
        import shutil
        shutil.copy(os.path.join(qdir, "query_results.md"), os.path.join(a.out, "queries.md"))
    ing = read_json(os.path.join(a.work, "corpus", "ingest_report.json"), {}) or {}
    case_path = os.path.join(a.input, "case.json") if os.path.isdir(a.input) else a.input
    case = read_json(case_path, {}) or {}
    notes = read_json(os.path.join(a.work, "notes.json"), {}) or {}
    fill = read_json(os.path.join(a.work, "contract_fill.json"), {}) or {}

    srcs = g.get("sources", [])
    extracted = {e["source_id"] for e in g.get("edges", []) if e["predicate"] != "AUTHOR_OF"}
    problems = []
    if rc_b != 0:
        problems.append("build_graph failed")
    for s in srcs:
        if s.get("paragraph_count") and s["source_id"] not in extracted:
            problems.append(f"no evidence-bound relation for source {s['source_id']}")
    ok_q = [q for q in queries if q["status"] == "ok"]
    if len(ok_q) < 3:
        problems.append(f"only {len(ok_q)} queries returned results (need >=3)")
    status = "failed" if rc_b != 0 or not g.get("nodes") else ("partial" if problems or ing.get("status") != "ok" else "success")
    uncertainty = list(notes.get("uncertainty", []))
    uncertainty += [f"{c['kind']}: {c.get('names') or c.get('abbreviation') or c.get('key')} — {c.get('reason', '')}" for c in g.get("conflicts", [])]
    uncertainty += [f"edge {e['id']} ({e['source_id']}): {'; '.join(e['flags'])}" for e in g.get("edges", []) if e.get("flags")]
    uncertainty += ["Locations are organiser paragraph IDs (JATS), not PDF page numbers.",
                    "Inline formulas / sub- and superscripts are linearised in the material; values were matched as written."]
    evidence_index = [{"item": e["id"], "kind": "edge", "source_id": ev["source_id"], "paragraph_id": ev["paragraph_id"], "quote": ev["quote"], "match": ev.get("match")}
                      for e in g.get("edges", []) for ev in e["evidence"][:1]]
    result = {
        "case_id": case.get("case_id") or case.get("id") or ing.get("case_id") or os.path.basename(os.path.abspath(a.input)),
        "status": status,
        "status_detail": problems or ["all steps completed"],
        "skill": {"name": "literature-kg", "version": VERSION},
        "inputs": {"files": ing.get("files", []), "ingest_status": ing.get("status"), "ingest_warnings": ing.get("warnings", [])},
        "sources": [{k: s.get(k) for k in ("source_id", "doi", "title", "authors", "license", "sha256", "role", "paragraph_count")} for s in srcs],
        "graph": {"file": "graph/graph.json", "formats": ["graph/graph.json", "graph/nodes.csv", "graph/edges.csv", "graph/evidence.csv", "graph/graph.graphml",
                                                         "graph/graph.mmd", "graph/graph.dot", "graph/graph.html", "graph/graph.svg", "graph/graph.png"],
                  "stats": g.get("stats", {})},
        "nodes": [{k: n.get(k) for k in ("id", "type", "label", "aliases", "scope", "sources", "attributes", "definitions")} |
                  {"evidence": [{k: ev.get(k) for k in ("source_id", "paragraph_id", "quote", "match")} for ev in n.get("evidence", [])[:3]]} for n in g.get("nodes", [])],
        "edges": [{k: e.get(k) for k in ("id", "source", "predicate", "target", "source_id", "conditions", "strength", "attribution", "polarity", "needs_review", "flags", "note")} |
                  {"evidence": [{k: ev.get(k) for k in ("source_id", "paragraph_id", "quote", "match")} for ev in e.get("evidence", [])[:3]]} for e in g.get("edges", [])],
        "queries": [{k: q.get(k) for k in ("id", "question", "op", "args", "predicate", "source", "status", "reason", "notes", "edges", "uncertain", "related_conflicts", "per_concept", "not_merged")} |
                    {"nodes": [n["id"] for n in q.get("nodes", [])]} for q in queries],
        "alignment": {"merges": g.get("merge_log", []), "not_merged": [c for c in g.get("conflicts", []) if c.get("decision") == "not_merged"],
                      "rules": "within paper: shared name/alias key; across papers: only concept types with equal full-name key; instances (samples, measurements, conclusions, datasets, models, conditions) never merged across papers; abbreviation alone never merges"},
        "conflicts": g.get("conflicts", []),
        "rejected": g.get("rejected", []),
        "not_reported": {**(g.get("not_reported") or {}), **({"agent_notes": notes["not_reported"]} if notes.get("not_reported") else {})},
        "uncertainty": uncertainty,
        "evidence_index": evidence_index,
        "change_log": g.get("change_log", []) + [{"action": "build", "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "previous_graph": a.previous}],
        "artifacts": sorted(os.path.relpath(os.path.join(r, f), a.out).replace("\\", "/") for r, _, fs in os.walk(a.out) for f in fs if f != "result.json"),
        "stats": g.get("stats", {}),
        "run": {"steps": [{k: v for k, v in s.items() if k != "stdout_tail"} for s in log], "seconds": round(time.time() - t0, 2)},
    }
    contract = case.get("output_contract") or case.get("output_fields") or {}
    keys = list(contract) if isinstance(contract, dict) else [c if isinstance(c, str) else c.get("name") for c in contract if c]
    mapping = {}
    for k in keys:
        if not k or k in result:
            mapping[k] = k
            continue
        if k in fill:
            result[k] = fill[k]
            mapping[k] = "contract_fill.json"
            continue
        hit = next((f for pat, f in SYN.items() if re.search(pat, k.lower())), None)
        if hit and hit in result:
            result[k] = result[hit]
            mapping[k] = hit
        else:
            result[k] = None
            mapping[k] = None
            result["uncertainty"].append(f"output_contract field '{k}' could not be filled from the graph; left null (fill via work/contract_fill.json)")
    for k, v in fill.items():
        result.setdefault(k, v)
    result["output_contract_mapping"] = mapping
    write_json(os.path.join(a.out, "result.json"), result)
    rc_c = step([os.path.join(HERE, "check_result.py"), "--result", os.path.join(a.out, "result.json"), "--work", a.work], [])
    print(f"run_all: status={status} nodes={len(result['nodes'])} edges={len(result['edges'])} queries_ok={len(ok_q)} problems={problems} check_exit={rc_c}")
    return 0 if status != "failed" else 2


def safe_main():
    try:
        return main()
    except Exception as e:  # noqa: BLE001  - always leave a result.json behind
        import traceback
        ap = argparse.ArgumentParser()
        ap.add_argument("--input", default="/input")
        ap.add_argument("--work", default="/app/work")
        ap.add_argument("--out", default="/app/output")
        ap.add_argument("--previous")
        a = ap.parse_known_args()[0]
        case = {}
        try:
            case = read_json(os.path.join(a.input, "case.json"), {}) or {}
        except Exception:  # noqa: BLE001
            pass
        write_json(os.path.join(a.out, "result.json"), {"case_id": case.get("case_id"), "status": "failed",
                   "status_detail": [f"run_all crashed: {type(e).__name__}: {e}"], "traceback": traceback.format_exc()[-4000:],
                   "manual_takeover": f"inspect {a.work}/graph/graph.json and {a.work}/extract/*.json; rerun scripts individually"})
        print("run_all: CRASH", e)
        return 3


if __name__ == "__main__":
    sys.exit(safe_main())
