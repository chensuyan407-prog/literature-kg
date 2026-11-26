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
import json
import os
import re
import shutil
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
    r"(uncertain|limitation|unknown|undecid)": "uncertainty", r"(verification_notes|review_notes|notes)": "uncertainty",
    r"(source|provenance|corpus|paper)": "sources", r"(evidence|citation)": "evidence_index", r"(status|state)": "status",
    r"(change|increment|update)": "change_log", r"(not_reported|missing|unreported)": "not_reported",
    r"(export|file|artifact)": "artifacts", r"(stat|summary|count)": "stats",
}


def contract_schema(contract):
    """Normalize flat dict, JSON Schema (properties/required), deliverables, or list contract into {field: spec}."""
    if isinstance(contract, list):
        out = {}
        for c in contract:
            nm = c if isinstance(c, str) else (c.get("name") or c.get("field") if isinstance(c, dict) else None)
            if nm:
                out[nm] = c if isinstance(c, dict) else None
        return out
    if not isinstance(contract, dict):
        return {}
    src = contract.get("deliverables") if isinstance(contract.get("deliverables"), dict) and len(contract) == 1 else contract
    if "properties" in src or ("required" in src and isinstance(src.get("required"), list)):
        fields = {}
        if isinstance(src.get("properties"), dict):
            fields.update(src["properties"])
        if isinstance(src.get("required"), list):
            for nm in src["required"]:
                if isinstance(nm, str) and nm not in fields:
                    fields[nm] = None
        if isinstance(src.get("deliverables"), dict):
            for nm, spec in src["deliverables"].items():
                if isinstance(nm, str) and nm not in fields:
                    fields[nm] = spec
        return fields
    return src


def _want_type(spec):
    if isinstance(spec, dict) and isinstance(spec.get("type"), str):
        spec = spec["type"]
    s = json.dumps(spec, ensure_ascii=False).lower() if not isinstance(spec, str) else spec.lower()
    if isinstance(spec, list) or re.search(r"\blist\b|array|\[\]|列表|数组", s):
        return "list"
    if isinstance(spec, dict) or re.search(r"\bobject\b|\bdict\b|\bmap\b|对象|字典", s):
        return "object"
    if re.search(r"\bstring\b|\bstr\b|\btext\b|字符串|文本", s):
        return "string"
    if re.search(r"\binteger\b|\bint\b|整数", s):
        return "integer"
    if re.search(r"number|float|数值|数字", s):
        return "number"
    if re.search(r"bool", s):
        return "boolean"
    return None


def _coerce_val(val, want):
    if want is None or val is None:
        return val
    if want == "string":
        if isinstance(val, str):
            return val
        if isinstance(val, list) and all(isinstance(x, str) for x in val):
            return "\n".join(val)
        return json.dumps(val, ensure_ascii=False)
    if want == "integer":
        if isinstance(val, bool):
            return int(val)
        if isinstance(val, (int, float)):
            return int(val)
        if isinstance(val, dict):
            return int(val.get("nodes") if isinstance(val.get("nodes"), (int, float)) else (val.get("total") if isinstance(val.get("total"), (int, float)) else len(val)))
        return len(val) if isinstance(val, (list, str)) else 0
    if want == "number":
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            return val
        if isinstance(val, dict):
            return float(val.get("nodes") if isinstance(val.get("nodes"), (int, float)) else len(val))
        return float(len(val)) if isinstance(val, (list, str)) else 0.0
    if want == "boolean":
        return bool(val)
    if want == "list":
        if isinstance(val, list):
            return val
        if isinstance(val, dict):
            lists = [x for v in val.values() if isinstance(v, list) for x in v]
            return lists if lists else [{"key": k, "value": v} for k, v in val.items()]
        return [val]
    if want == "object":
        if isinstance(val, dict):
            return val
        return {"items": val} if isinstance(val, list) else {"value": val}
    return val


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
    g = (read_json(gpath, {}) or {}) if rc_b == 0 else {}
    queries = (read_json(os.path.join(qdir, "query_results.json"), []) or []) if (rc_b == 0 and rc_q == 0) else []
    qmd = os.path.join(qdir, "query_results.md")
    if queries and os.path.exists(qmd):
        import shutil
        shutil.copy(qmd, os.path.join(a.out, "queries.md"))
    ing = read_json(os.path.join(a.work, "corpus", "ingest_report.json"), {}) or {}
    case_path = os.path.join(a.input, "case.json") if os.path.isdir(a.input) else a.input
    raw_case = read_json(case_path, {})
    case = raw_case if isinstance(raw_case, dict) else {}
    try:
        notes = read_json(os.path.join(a.work, "notes.json"), {}) or {}
    except Exception as e:  # noqa: BLE001
        notes = {"uncertainty": [f"invalid notes.json ignored: {e}"]}
    try:
        fill = read_json(os.path.join(a.work, "contract_fill.json"), {}) or {}
    except Exception as e:  # noqa: BLE001
        fill = {}
        notes.setdefault("uncertainty", []).append(f"invalid contract_fill.json ignored: {e}")

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
    problems += [f"input: {r}" for r in ing.get("partial_reasons", [])]
    status = "failed" if rc_b != 0 or not g.get("nodes") else ("partial" if problems or ing.get("status") != "ok" else "success")
    uncertainty = list(notes.get("uncertainty", []))
    uncertainty += [f"{c['kind']}: {c.get('names') or c.get('abbreviation') or c.get('key')} — {c.get('reason', '')}" for c in g.get("conflicts", [])]
    uncertainty += [f"edge {e['id']} ({e['source_id']}): {'; '.join(e['flags'])}" for e in g.get("edges", []) if e.get("flags")]
    kinds = {k for s in ing.get("sources", []) for k in (s.get("location_kind") or [])}
    if kinds - {"pdf_text_layer"}:
        uncertainty.append("Locations with organiser paragraph IDs (JATS/JSON) or generated block IDs are not PDF page numbers.")
    if "pdf_text_layer" in kinds:
        uncertainty.append("PDF locations p<page>-para<n>: real PDF page + reading-order block from the text layer (no OCR); tables/figures/equations may be incomplete.")
    uncertainty.append("Inline formulas / sub- and superscripts are linearised in the material; values were matched as written.")
    evidence_index = [{"item": e["id"], "kind": "edge", "source_id": ev["source_id"], "paragraph_id": ev["paragraph_id"], "quote": ev["quote"], "match": ev.get("match")}
                      for e in g.get("edges", []) for ev in e["evidence"][:1]]
    cid = case["case_id"] if ("case_id" in case and case["case_id"] is not None) else (case["id"] if ("id" in case and case["id"] is not None) else (ing.get("case_id") if ing.get("case_id") is not None else os.path.basename(os.path.abspath(a.input))))
    result = {
        "case_id": cid,
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
    contract = case.get("output_contract") or case.get("output_fields") or case.get("schema") or case.get("deliverables") or {}
    schema = contract_schema(contract)
    req_fields = set(contract.get("required", [])) if isinstance(contract, dict) and isinstance(contract.get("required"), list) else set()
    CORE_FIELDS = {"case_id", "status", "nodes", "edges", "sources", "queries"}
    mapping = {}
    for k, spec in schema.items():
        if not k:
            continue
        want = _want_type(spec)
        if k in result and result[k] is not None:
            if k not in CORE_FIELDS:
                result[k] = _coerce_val(result[k], want)
            mapping[k] = k
            continue
        if k in fill and k not in CORE_FIELDS:
            result[k] = _coerce_val(fill[k], want)
            mapping[k] = "contract_fill.json"
            continue
        hit = next((f for pat, f in SYN.items() if re.search(pat, k.lower())), None)
        if hit and hit in result:
            result[k] = _coerce_val(result[hit], want)
            mapping[k] = hit
        else:
            result[k] = None
            mapping[k] = None
            result["uncertainty"].append(f"output_contract field '{k}' could not be filled from the graph; left null (fill via work/contract_fill.json)")
            if k in req_fields:
                problems.append(f"required output_contract field '{k}' is null")
    for k, v in fill.items():
        if k not in CORE_FIELDS:
            result.setdefault(k, _coerce_val(v, _want_type(schema.get(k))) if k in schema else v)
    delivs = case.get("deliverables")
    if isinstance(delivs, list):
        for d in delivs:
            nm = d if isinstance(d, str) else (d.get("path") or d.get("name") if isinstance(d, dict) else None)
            if nm and nm.endswith(".md") and ".." not in nm:
                out_md = os.path.join(a.out, os.path.basename(nm))
                if not os.path.exists(out_md):
                    if os.path.exists(qmd):
                        shutil.copy(qmd, out_md)
                    else:
                        with open(out_md, "w", encoding="utf-8") as mf:
                            mf.write(f"# Literature KG Summary ({result['case_id']})\n\nStatus: {status}\nNodes: {len(result['nodes'])}, Edges: {len(result['edges'])}\n")
    result["artifacts"] = sorted(os.path.relpath(os.path.join(r, f), a.out).replace("\\", "/") for r, _, fs in os.walk(a.out) for f in fs if f != "result.json")
    result["output_contract_mapping"] = mapping
    write_json(os.path.join(a.out, "result.json"), result)
    rc_c = step([os.path.join(HERE, "check_result.py"), "--result", os.path.join(a.out, "result.json"), "--work", a.work], [])
    if rc_c != 0:
        problems.append(f"check_result hard check failed (exit {rc_c})")
        status = "failed"
        result["status"] = status
        result["status_detail"] = problems
        write_json(os.path.join(a.out, "result.json"), result)
    elif problems and result["status"] == "success":
        status = "partial"
        result["status"] = status
        result["status_detail"] = problems
        write_json(os.path.join(a.out, "result.json"), result)
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
