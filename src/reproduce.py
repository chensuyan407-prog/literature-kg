"""Reproduce every result in this bundle (about 10-20 s on a laptop).

python src/reproduce.py
1. builds the local two-paper case from data/raw (two CC-BY 4.0 JATS articles) -> execution/results/case1/input
2. runs the Skill's ingest.py on it
3. adds the extraction files written by the agent (Claude, following submission/SKILL.md) from data/case1_agent_work
4. runs run_all.py (build graph, queries, exports, result.json, self-check)
5. runs src/run_tests.py (negative controls, alignment vs naive baseline, incremental update, failure handling)
6. writes execution/run.log, execution/results/metrics.json, trace/trace.jsonl, characterization.json, arm_manifest.json
"""
import datetime
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(ROOT, "submission", "scripts")
RES = os.path.join(ROOT, "execution", "results")
LOG = os.path.join(ROOT, "execution", "run.log")
TRACE = os.path.join(ROOT, "trace", "trace.jsonl")
_order = [0]


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def log(msg):
    print(msg)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{now()}] {msg}\n")


def step(**kw):
    _order[0] += 1
    kw.update(timestamp=now(), step_order=_order[0])
    with open(TRACE, "a", encoding="utf-8") as f:
        f.write(json.dumps(kw, ensure_ascii=False) + "\n")


def tool(script, *args):
    cid = f"c{_order[0] + 1}"
    step(step_type="tool_call", tool_name="python", tool_call_id=cid, tool_args={"script": os.path.relpath(script, ROOT).replace("\\", "/"), "args": [os.path.relpath(a, ROOT).replace("\\", "/") if os.path.exists(a) else a for a in args]})
    t = time.time()
    p = subprocess.run([sys.executable, "-X", "utf8", script] + list(args), capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout + p.stderr).strip()
    step(step_type="tool_result", tool_call_id=cid, tool_output=out[-1500:], duration_s=round(time.time() - t, 3))
    log(f"$ python {os.path.relpath(script, ROOT)} {' '.join(os.path.relpath(a, ROOT) if os.path.exists(a) else a for a in args)}  (exit {p.returncode})\n{out}")
    return p.returncode


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    t0 = time.time()
    ran_at = now()
    for p in (LOG, TRACE):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if os.path.exists(p):
            os.remove(p)
    if os.path.exists(RES):
        shutil.rmtree(RES)
    os.makedirs(RES)
    log(f"python {platform.python_version()} on {platform.system()}")
    step(step_type="thought", title="Plan", body="Build the two-paper case from the CC-BY JATS files, run the Skill end to end with the agent-written extraction, then run the mechanism tests (negative controls, alignment vs naive baseline, incremental IDs, failure handling) and record metrics.")
    case = os.path.join(RES, "case1")
    tool(os.path.join(ROOT, "src", "make_case.py"), os.path.join(ROOT, "data", "raw"), os.path.join(case, "input"))
    tool(os.path.join(K, "ingest.py"), "--input", os.path.join(case, "input"), "--work", os.path.join(case, "work"))
    shutil.copytree(os.path.join(ROOT, "data", "case1_agent_work"), os.path.join(case, "work"), dirs_exist_ok=True)
    step(step_type="thought", title="Agent extraction", body="Extraction files (paper-A.json, paper-B.json, alignment_overrides.json, queries.json) were written by the agent after reading work/corpus/*.txt, following SKILL.md; they are copied, not regenerated.")
    rc = tool(os.path.join(K, "run_all.py"), "--input", os.path.join(case, "input"), "--work", os.path.join(case, "work"), "--out", os.path.join(case, "output"))
    rct = tool(os.path.join(ROOT, "src", "run_tests.py"), "--case", case, "--out", os.path.join(RES, "tests"))
    rep = json.load(open(os.path.join(RES, "tests", "test_report.json"), encoding="utf-8"))
    res = json.load(open(os.path.join(case, "output", "result.json"), encoding="utf-8"))
    chk = json.load(open(os.path.join(case, "output", "check_report.json"), encoding="utf-8"))
    t1, t2, t3, t4 = rep["T1_negative_controls"], rep["T2_alignment"], rep["T3_incremental"], rep["T4_failures"]
    ev = [e for x in res["edges"] for e in x["evidence"] if e.get("match") != "metadata"] + [e for x in res["nodes"] for e in x["evidence"] if e.get("match") != "metadata"]
    m = {
        "negative_controls_entity_accuracy": t1["entities"]["correct"] / t1["entities"]["total"],
        "negative_controls_relation_accuracy": t1["relations"]["correct"] / t1["relations"]["total"],
        "alignment_precision_skill": t2["skill"]["precision"], "alignment_recall_skill": t2["skill"]["recall"],
        "alignment_precision_naive": t2["naive_baseline"]["precision"], "alignment_recall_naive": t2["naive_baseline"]["recall"],
        "alignment_false_merges_naive": t2["naive_baseline"]["false_merges"],
        "incremental_node_id_retention": eval(t3["v1_ids_kept"]), "incremental_edge_id_retention": eval(t3["v1_edges_kept"]),
        "failure_handling_checks_passed": sum(1 for k, v in t4.items() if isinstance(v, dict) and v["pass"]),
        "failure_handling_checks_total": sum(1 for k, v in t4.items() if isinstance(v, dict)),
        "deterministic_rebuild": t4["deterministic_rebuild"]["pass"],
        "case1_status": res["status"], "case1_nodes": res["stats"]["nodes"], "case1_edges": res["stats"]["edges"],
        "case1_cross_paper_concepts": res["stats"]["shared_concepts"], "case1_rejected_items": res["stats"]["rejected"],
        "case1_needs_review_edges": res["stats"]["needs_review_edges"], "case1_conflict_records": res["stats"]["conflicts"],
        "case1_queries_ok": sum(1 for q in res["queries"] if q["status"] == "ok"), "case1_queries_total": len(res["queries"]),
        "case1_evidence_items_reverified": chk["evidence_items_checked"], "case1_check_ok": chk["ok"],
        "case1_evidence_exact_or_normalized_fraction": round(sum(1 for e in ev if e["match"] in ("exact", "normalized")) / max(1, len(ev)), 4),
        "run_all_exit": rc, "tests_exit": rct,
    }
    json.dump(m, open(os.path.join(RES, "metrics.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log("metrics: " + json.dumps(m, ensure_ascii=False))
    step(step_type="observation", title="Metrics", body=json.dumps(m, ensure_ascii=False))
    write_characterization(m, t2)
    wall = round(time.time() - t0, 2)
    write_manifest(ran_at, wall, 0 if rc == 0 and rct == 0 else 1)
    step(step_type="final", title="Done", body=f"wall {wall}s; run_all exit {rc}; tests exit {rct}")
    return 0 if rc == 0 and rct == 0 else 1


def dev(target, metric, actual, ref, explanation, tol, artifact="metrics"):
    score = max(0.0, 1 - abs(actual - ref) / tol) if tol else float(actual == ref)
    return {"target": target, "metric": metric, "actual_value": actual, "reference_value": ref, "score": round(score, 4),
            "explanation": explanation, "evidence_artifact": artifact, "tolerance": tol}


def write_characterization(m, t2):
    d = [
        dev("negative controls: entity accept/reject decisions", "absolute_error", m["negative_controls_entity_accuracy"], 1.0,
            "7 designed entities: fabricated quote, wrong paragraph id, other paper's text, unknown type must be rejected; 3 valid accepted", 0.5),
        dev("negative controls: relation decisions", "absolute_error", m["negative_controls_relation_accuracy"], 1.0,
            "9 designed relations: fabricated quote, wrong paragraph, unknown predicate, reversed domain, unknown key rejected; wrong number flagged; hedged quote downgraded", 0.5),
        dev("cross-paper alignment precision (designed set)", "absolute_error", m["alignment_precision_skill"], 1.0,
            f"naive baseline (equal name or any shared alias string) precision = {m['alignment_precision_naive']}, false merges {m['alignment_false_merges_naive']}", 0.5),
        dev("cross-paper alignment recall (designed set)", "absolute_error", m["alignment_recall_skill"], 1.0,
            f"naive baseline recall = {m['alignment_recall_naive']} (misses plural variant)", 0.5),
        dev("incremental update: node id retention", "absolute_error", m["incremental_node_id_retention"], 1.0, "graph(A) then graph(A+B) with --previous", 0.5),
        dev("incremental update: edge id retention", "absolute_error", m["incremental_edge_id_retention"], 1.0, "graph(A) then graph(A+B) with --previous", 0.5),
        dev("failure handling checks", "absolute_error", m["failure_handling_checks_passed"], m["failure_handling_checks_total"],
            "empty input, missing secondary text, XML-only fallback, empty queries, determinism, broken extraction JSON", 3),
        dev("real two-paper case: evidence re-verified by independent checker", "absolute_error", 1.0 if m["case1_check_ok"] else 0.0, 1.0,
            f"{m['case1_evidence_items_reverified']} evidence items re-checked against paragraphs; exact/normalized fraction {m['case1_evidence_exact_or_normalized_fraction']}", 0.5, "case1_result"),
        dev("real two-paper case: queries with results", "absolute_error", m["case1_queries_ok"], m["case1_queries_total"] - 1,
            "q7 (XPS in paper B) is expected to return no_result: the paper states XPS was not performed", 3, "case1_queries"),
    ]
    c = {"deviations_from_paper": d,
         "envelope": [{"param": "papers_per_graph", "min": 1, "max": 2, "tested": True},
                      {"param": "paragraphs_per_paper", "min": 3, "max": 129, "tested": True},
                      {"param": "input_formats", "min": 1, "max": 3, "tested": True, "unit": "JSON (two schemas), JATS XML fallback, no-manifest"},
                      {"param": "papers_per_graph", "min": 3, "max": 10, "tested": False},
                      {"param": "PDF-only input", "min": 1, "max": 1, "tested": False}],
         "failure_modes": [
             {"condition": "entity named only by pronoun or implied ('the composite')", "symptom": "edge kept with needs_review flag; not rejected", "evidence_artifact": "case1_result"},
             {"condition": "synonyms with different words not declared as alias (e.g. magnetite vs Fe3O4 across papers)", "symptom": "two nodes; merge only via agent override with reason", "evidence_artifact": "metrics"},
             {"condition": "values only in tables/figures (not in paragraph text)", "symptom": "not in graph; listed under not_reported", "evidence_artifact": "case1_result"},
             {"condition": "approximate quote (>=90% tokens, 6-token anchor)", "symptom": "accepted with match=approx and listed as uncertain", "evidence_artifact": "metrics"},
             {"condition": "extraction recall", "symptom": "not measured: scripts verify what the agent extracted, not what it missed", "evidence_artifact": "metrics"}],
         "sensitivity": [],
         "notes": "Mechanism tests on local data. The real case uses two CC-BY 4.0 articles (ACS Omega 2026, doi 10.1021/acsomega.6c05759; Materials 2026, doi 10.3390/ma19163371) shaped like the challenge input; extraction files were written by the agent (Claude) following SKILL.md, so case numbers show what the pipeline does with one agent's extraction, not a DeepSeek baseline-vs-Skill comparison (the platform runs that). reference_value is the designed ground truth."}
    json.dump(c, open(os.path.join(ROOT, "characterization.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log("wrote characterization.json")


def write_manifest(ran_at, wall, exit_code):
    arts = [("metrics", "execution/results/metrics.json", "metric", "json"),
            ("test_report", "execution/results/tests/test_report.json", "data", "json"),
            ("case1_result", "execution/results/case1/output/result.json", "data", "json"),
            ("case1_graph", "execution/results/case1/output/graph/graph.json", "data", "json"),
            ("case1_graphml", "execution/results/case1/output/graph/graph.graphml", "data", "other"),
            ("case1_edges_csv", "execution/results/case1/output/graph/edges.csv", "table", "csv"),
            ("case1_queries", "execution/results/case1/output/queries.md", "data", "other"),
            ("case1_overview_png", "execution/results/case1/output/graph/graph.png", "figure", "png"),
            ("case1_query_shared_png", "execution/results/case1/output/graph/queries/q_shared.png", "figure", "png"),
            ("case1_html", "execution/results/case1/output/graph/graph.html", "data", "other")]
    man = {"arm_version": "1.1",
           "paper": {"title": "阅读15｜文献知识图谱构建 — literature-kg Skill", "challenge_id": "product-arena-10-760d1a0b"},
           "entrypoint": "src/reproduce.py",
           "environment": {"dependencies": "requirements.txt", "python_version": ">=3.9", "gpu_required": False,
                           "extra_packages": ["matplotlib>=3.5 (optional, PNG previews)", "PyMuPDF>=1.23 (optional, PDF input)"]},
           "execution": {"log_path": "execution/run.log", "exit_code": exit_code, "ran_at": ran_at, "wall_time_s": wall, "ran_by": "agent",
                         "artifacts": [{"id": i, "path": p, "type": t, "format": f, "checksum_sha256": sha(os.path.join(ROOT, p))} for i, p, t, f in arts if os.path.exists(os.path.join(ROOT, p))]},
           "expected_outputs": [{"name": d["target"], "type": "metric", "produced_by": [d["evidence_artifact"]], "comparison_method": "numeric_tolerance"}
                                for d in json.load(open(os.path.join(ROOT, "characterization.json"), encoding="utf-8"))["deviations_from_paper"]],
           "characterization": {"path": "characterization.json"},
           "trace": "trace/trace.jsonl",
           "skills_used": [{"skill_id": "literature-kg", "version": "0.1.0"}],
           "provenance": {"created_by": "agent", "toolchain": f"Claude Code + Python {platform.python_version()}"},
           "handoff": {"status": "partial",
                       "next_suggestion": "Run the Skill with the platform's DeepSeek harness on the fixed cases; measure extraction recall against a hand-labelled set; add 3+ paper corpora.",
                       "modality_notes": {"skills": "Skill lives in submission/ (SKILL.md + scripts + schema + examples); copy of SKILL.md in skills/SKILL.md"}}}
    json.dump(man, open(os.path.join(ROOT, "arm_manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log("wrote arm_manifest.json")


if __name__ == "__main__":
    sys.exit(main())
