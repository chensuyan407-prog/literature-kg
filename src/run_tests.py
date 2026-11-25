"""Mechanism tests for the literature-kg Skill scripts.

python tests/run_tests.py [--case testdata/case1] [--out tests/results]

T1 negative controls: fabricated / misplaced evidence and schema violations must be rejected.
T2 alignment on a designed two-paper corpus with gold merge decisions; compared with a naive
   baseline (merge on equal lower-cased name or any shared alias string, type-agnostic).
T3 incremental update: graph for paper A, then A+B with --previous; ids must be kept.
T4 failure handling: missing material, manifest source without text, empty queries, determinism.
T5 the real two-paper case (if present): counts, self-check.
Writes OUT/test_report.json and OUT/test_report.md.
"""
import argparse
import hashlib
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "submission", "scripts")
sys.path.insert(0, S)
from kglib import name_key  # noqa: E402


def run(script, *args):
    p = subprocess.run([sys.executable, "-X", "utf8", os.path.join(S, script)] + list(args), capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout + p.stderr


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def jdump(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(o, f, ensure_ascii=False, indent=1)


# ------------------------------------------------------------------ T1 ---
def t1_negative(case_dir, tmp):
    work = os.path.join(tmp, "t1", "work")
    shutil.copytree(os.path.join(case_dir, "work", "corpus"), os.path.join(work, "corpus"))
    good = {"key": "MGO", "name": "MGO composite", "type": "Sample", "mentions": [{"paragraph_id": "p-0007", "quote": "The MGO composite was synthesized via a modified chemical coprecipitation route."}]}
    ents = [good,
            {"key": "LA", "name": "lactic acid", "type": "Material", "mentions": [{"paragraph_id": "p-0006", "quote": "lactic acid (monocarboxylic)"}]},
            {"key": "fake1", "name": "chitosan", "type": "Material", "mentions": [{"paragraph_id": "p-0006", "quote": "chitosan was used as a co-adsorbent"}]},
            {"key": "fake2", "name": "succinic acid", "type": "Material", "mentions": [{"paragraph_id": "p-9999", "quote": "succinic acid (dicarboxylic)"}]},
            {"key": "fake3", "name": "humic acid", "type": "Material", "mentions": [{"paragraph_id": "p-0002", "quote": "Humic acids (HA) are natural high-molecular-weight organic compounds"}]},
            {"key": "fake4", "name": "thing", "type": "Gizmo", "mentions": [{"paragraph_id": "p-0006", "quote": "lactic acid (monocarboxylic)"}]},
            {"key": "m1", "name": "qmax 334.45 mg/g", "type": "Measurement", "attributes": {"value": "334.45"}, "mentions": [{"paragraph_id": "p-0055", "quote": "The maximum adsorption capacity of MGO for lactic acid (334.45 mg/g)"}]},
            {"key": "Hb", "name": "hydrogen bonding", "type": "Mechanism", "mentions": [{"paragraph_id": "p-0065", "quote": "which may facilitate supplementary hydrogen bonding interactions"}]},
            {"key": "m_bad", "name": "qmax 434.45 mg/g", "type": "Measurement", "attributes": {"value": "434.45"}, "mentions": [{"paragraph_id": "p-0055", "quote": "The maximum adsorption capacity of MGO for lactic acid (334.45 mg/g)"}]}]
    rels = [
        {"subject": "MGO", "predicate": "TESTED_ON", "object": "LA", "paragraph_id": "p-0010", "quote": "All adsorption experiments for lactic, succinic, and citric acids were conducted", "strength": "direct", "_expect": "accept"},
        {"subject": "MGO", "predicate": "HAS_RESULT", "object": "m1", "paragraph_id": "p-0055", "quote": "The maximum adsorption capacity of MGO for lactic acid (334.45 mg/g)", "strength": "direct", "_expect": "accept"},
        {"subject": "MGO", "predicate": "TESTED_ON", "object": "LA", "paragraph_id": "p-0010", "quote": "MGO selectively adsorbs lactic acid over all other acids", "strength": "direct", "_expect": "reject"},
        {"subject": "MGO", "predicate": "TESTED_ON", "object": "LA", "paragraph_id": "p-0040", "quote": "All adsorption experiments for lactic, succinic, and citric acids were conducted", "strength": "direct", "_expect": "reject"},
        {"subject": "MGO", "predicate": "ADSORBS_STRONGLY", "object": "LA", "paragraph_id": "p-0010", "quote": "All adsorption experiments for lactic, succinic, and citric acids were conducted", "strength": "direct", "_expect": "reject"},
        {"subject": "LA", "predicate": "HAS_RESULT", "object": "MGO", "paragraph_id": "p-0010", "quote": "All adsorption experiments for lactic, succinic, and citric acids were conducted", "strength": "direct", "_expect": "reject"},
        {"subject": "MGO", "predicate": "TESTED_ON", "object": "chitosan", "paragraph_id": "p-0010", "quote": "All adsorption experiments for lactic, succinic, and citric acids were conducted", "strength": "direct", "_expect": "reject"},
        {"subject": "MGO", "predicate": "HAS_RESULT", "object": "m_bad", "paragraph_id": "p-0055", "quote": "The maximum adsorption capacity of MGO for lactic acid (334.45 mg/g)", "strength": "direct", "_expect": "flag"},
        {"subject": "m1", "predicate": "ATTRIBUTED_TO", "object": "Hb", "paragraph_id": "p-0065", "quote": "may be associated with its smaller molecular size and the presence of an additional hydroxyl group", "strength": "direct", "_expect": "hedged"},
    ]
    jdump(os.path.join(work, "extract", "paper-A.json"), {"source_id": "paper-A", "entities": ents, "relations": [{k: v for k, v in r.items() if k != "_expect"} for r in rels]})
    rc, out = run("build_graph.py", "--work", work)
    g = jload(os.path.join(work, "graph", "graph.json"))
    rej_names = {r.get("name") for r in g["rejected"] if r["kind"] == "entity"} | {(r.get("item") or {}).get("name") for r in g["rejected"] if r["kind"] == "entity"}
    ent_expect = {"chitosan": "reject", "succinic acid": "reject", "humic acid": "reject", "thing": "reject", "MGO composite": "accept", "lactic acid": "accept", "qmax 334.45 mg/g": "accept"}
    ent_res = {n: ("reject" if n in rej_names else "accept") for n in ent_expect}
    rows = []
    for r in rels:
        quote = r["quote"]
        lab = {n["id"]: n["label"] for n in g["nodes"]}
        obj_name = next((x["name"] for x in ents if x["key"] == r["object"]), r["object"])
        hit = [e for e in g["edges"] if e["predicate"] == r["predicate"] and lab[e["target"]] == obj_name
               and any(ev["quote"] == quote and ev["paragraph_id"] == r["paragraph_id"] for ev in e["evidence"])]
        if not hit:
            got = "reject"
        elif r["_expect"] == "flag":
            got = "flag" if hit[0].get("needs_review") else "accept"
        elif r["_expect"] == "hedged":
            got = "hedged" if hit[0]["strength"] == "hedged" else "accept"
        else:
            got = "accept"
        rows.append({"case": f"{r['predicate']} {r['subject']}->{r['object']} @{r['paragraph_id']}", "expected": r["_expect"], "got": got})
    ok_e = sum(ent_res[n] == ent_expect[n] for n in ent_expect)
    ok_r = sum(x["expected"] == x["got"] for x in rows)
    return {"entities": {"expected": ent_expect, "got": ent_res, "correct": ok_e, "total": len(ent_expect)},
            "relations": {"rows": rows, "correct": ok_r, "total": len(rows)},
            "pass": ok_e == len(ent_expect) and ok_r == len(rows)}


# ------------------------------------------------------------------ T2 ---
ALIGN_A = [
    ("a1", "Abstract", "We tune adsorbent synthesis with particle swarm optimization (PSO) and characterise samples by X-ray diffraction (XRD). Graphene Oxide sheets were purchased."),
    ("a2", "Methods", "Composite C1 was prepared from graphene oxide and chitosan. Equilibrium data followed the Langmuir isotherm. J. Smith performed the measurements."),
    ("a3", "Results", "Composite C1 reached 120 mg/g. Reduced graphene oxide was not tested."),
]
ALIGN_B = [
    ("b1", "Abstract", "Kinetics were fitted with the pseudo-second-order (PSO) model; the GO used here was graphene oxide from a supplier. X-Ray Diffraction (XRD) confirmed the phase."),
    ("b2", "Methods", "Composite C1 denotes our iron-doped carbon. Isotherms were described by Langmuir isotherms. J. Smith analysed the data."),
    ("b3", "Results", "Composite C1 adsorbed 45 mg/g. We compare with reduced graphene oxide (rGO)."),
]
ALIGN_ENTS = {
    "S1": [("PSO1", "particle swarm optimization", "Method", ["PSO"], "a1"), ("XRD1", "X-ray diffraction", "Method", ["XRD"], "a1"),
           ("GO1", "Graphene Oxide", "Material", [], "a1"), ("C1a", "Composite C1", "Sample", [], "a2"), ("L1", "Langmuir isotherm", "Method", [], "a2"),
           ("JS1", "J. Smith", "Researcher", [], "a2"), ("RGO1", "reduced graphene oxide", "Material", [], "a3")],
    "S2": [("PSO2", "pseudo-second-order", "Method", ["PSO"], "b1"), ("XRD2", "X-Ray Diffraction", "Method", ["XRD"], "b1"),
           ("GO2", "graphene oxide", "Material", ["GO"], "b1"), ("C1b", "Composite C1", "Sample", [], "b2"), ("L2", "Langmuir isotherms", "Method", [], "b2"),
           ("JS2", "J. Smith", "Researcher", [], "b2"), ("RGO2", "reduced graphene oxide", "Material", ["rGO"], "b3")],
}
GOLD_SAME = {frozenset(p) for p in [("XRD1", "XRD2"), ("GO1", "GO2"), ("L1", "L2"), ("RGO1", "RGO2")]}
# not same: PSO1/PSO2 (abbreviation homonym), C1a/C1b (same label, different samples), JS1/JS2 (no identity evidence), GO*/RGO* (different material)


def naive_merge(ents):
    """Baseline: same lower-cased name or any shared alias string -> same node (type-agnostic)."""
    parent = {e[0]: e[0] for e in ents}

    def f(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for a, b in itertools.combinations(ents, 2):
        na = {a[1].lower()} | {x.lower() for x in a[3]}
        nb = {b[1].lower()} | {x.lower() for x in b[3]}
        if na & nb:
            parent[f(a[0])] = f(b[0])
    return {e[0]: f(e[0]) for e in ents}


def pair_scores(groups, ents, gold):
    pairs = [frozenset((a[0], b[0])) for a, b in itertools.combinations(ents, 2) if a[0][-1] != b[0][-1] or True]
    cross = [p for p in pairs if len({x[-1] for x in p}) == 2 or True]
    pred = {p for p in cross if len({groups[x] for x in p}) == 1}
    tp = len(pred & gold)
    fp = sorted("+".join(sorted(p)) for p in pred - gold)
    fn = sorted("+".join(sorted(p)) for p in gold - pred)
    prec = tp / len(pred) if pred else 1.0
    rec = tp / len(gold) if gold else 1.0
    return {"precision": round(prec, 3), "recall": round(rec, 3), "false_merges": fp, "missed_merges": fn}


def t2_alignment(tmp):
    base = os.path.join(tmp, "t2")
    inp = os.path.join(base, "input")
    os.makedirs(inp, exist_ok=True)
    jdump(os.path.join(inp, "corpus-manifest.json"), {"sources": [{"source_id": "S1", "doi": "10.0000/s1", "title": "Synthetic paper 1", "authors": ["A. One"], "file": "primary-material.json"},
                                                                 {"source_id": "S2", "doi": "10.0000/s2", "title": "Synthetic paper 2", "authors": ["B. Two"], "file": "secondary-material.json"}]})
    jdump(os.path.join(inp, "primary-material.json"), {"paragraphs": [{"paragraph_id": i, "section": s, "text": t} for i, s, t in ALIGN_A]})
    jdump(os.path.join(inp, "secondary-material.json"), {"paragraphs": [{"paragraph_id": i, "section": s, "text": t} for i, s, t in ALIGN_B]})
    jdump(os.path.join(inp, "case.json"), {"case_id": "synthetic-alignment", "output_contract": {"case_id": "", "graph": "", "queries": "", "alignment": ""}})
    work = os.path.join(base, "work")
    run("ingest.py", "--input", inp, "--work", work)
    texts = {i: t for i, _, t in ALIGN_A + ALIGN_B}
    allents = []
    for src, ents in ALIGN_ENTS.items():
        out = []
        for key, name, typ, al, pid in ents:
            t = texts[pid]
            q = next(x for x in [name] + al if x.lower() in t.lower())
            start = t.lower().index(q.lower())
            quote = t[max(0, start - 20): start + len(q) + 20]
            out.append({"key": key, "name": name, "type": typ, "aliases": al, "mentions": [{"paragraph_id": pid, "quote": quote}]})
            allents.append((key, name, typ, al, pid))
        jdump(os.path.join(work, "extract", f"{src}.json"), {"source_id": src, "entities": out, "relations": []})
    rc, out = run("build_graph.py", "--work", work)
    g = jload(os.path.join(work, "graph", "graph.json"))
    # map our keys -> node ids by matching name+source
    groups = {}
    for key, name, typ, al, pid in allents:
        src = "S1" if pid.startswith("a") else "S2"
        n = next(n for n in g["nodes"] if src in n["sources"] and n["type"] == typ and name_key(name) in {name_key(x) for x in [n["label"]] + n["aliases"]})
        groups[key] = n["id"]
    ours = pair_scores(groups, allents, GOLD_SAME)
    naive = pair_scores(naive_merge(allents), allents, GOLD_SAME)
    kinds = sorted({c["kind"] for c in g["conflicts"]})
    return {"skill": ours, "naive_baseline": naive, "conflict_kinds_recorded": kinds,
            "conflicts": [{k: c.get(k) for k in ("kind", "names", "abbreviation", "expansions", "decision")} for c in g["conflicts"]],
            "pass": ours["precision"] == 1.0 and ours["recall"] == 1.0}


# ------------------------------------------------------------------ T3 ---
def t3_incremental(case_dir, tmp):
    base = os.path.join(tmp, "t3")
    w1 = os.path.join(base, "w1")
    shutil.copytree(os.path.join(case_dir, "work", "corpus"), os.path.join(w1, "corpus"))
    os.makedirs(os.path.join(w1, "extract"))
    shutil.copy(os.path.join(case_dir, "work", "extract", "paper-A.json"), os.path.join(w1, "extract"))
    run("build_graph.py", "--work", w1)
    g1 = jload(os.path.join(w1, "graph", "graph.json"))
    w2 = os.path.join(base, "w2")
    shutil.copytree(os.path.join(case_dir, "work", "corpus"), os.path.join(w2, "corpus"))
    shutil.copytree(os.path.join(case_dir, "work", "extract"), os.path.join(w2, "extract"))
    run("build_graph.py", "--work", w2, "--previous", os.path.join(w1, "graph", "graph.json"))
    g2 = jload(os.path.join(w2, "graph", "graph.json"))
    ids1 = {n["id"]: n["label"] for n in g1["nodes"] if "paper-B" not in n["sources"]}
    ids2 = {n["id"]: n for n in g2["nodes"]}
    kept = [i for i in ids1 if i in ids2]
    e1 = {e["id"] for e in g1["edges"]}
    e2 = {e["id"] for e in g2["edges"]}
    actions = {}
    for c in g2["change_log"]:
        actions[c["action"]] = actions.get(c["action"], 0) + 1
    ext = [c["name"] for c in g2["change_log"] if c["action"] == "node_extended"]
    return {"v1_nodes": len(g1["nodes"]), "v2_nodes": len(g2["nodes"]), "v1_ids_kept": f"{len(kept)}/{len(ids1)}",
            "v1_edges_kept": f"{len(e1 & e2)}/{len(e1)}", "change_log_actions": actions, "nodes_extended_with_paper_B": ext,
            "pass": len(kept) == len(ids1) and e1 <= e2 and bool(ext)}


# ------------------------------------------------------------------ T4 ---
def strip_volatile(g):
    g = dict(g)
    g.pop("previous_graph", None)
    return json.dumps(g, sort_keys=True, ensure_ascii=False)


def t4_failures(case_dir, tmp):
    res = {}
    # (a) empty input folder
    inp = os.path.join(tmp, "t4a", "input")
    os.makedirs(inp)
    jdump(os.path.join(inp, "case.json"), {"case_id": "empty", "output_contract": {"graph": ""}})
    rc1, o1 = run("ingest.py", "--input", inp, "--work", os.path.join(tmp, "t4a", "work"))
    rc2, o2 = run("run_all.py", "--input", inp, "--work", os.path.join(tmp, "t4a", "work"), "--out", os.path.join(tmp, "t4a", "out"))
    r = jload(os.path.join(tmp, "t4a", "out", "result.json"))
    res["empty_input"] = {"ingest_exit": rc1, "result_status": r["status"], "status_detail": r["status_detail"], "pass": rc1 != 0 and r["status"] == "failed"}
    # (b) manifest lists a paper whose text is missing
    inp = os.path.join(tmp, "t4b", "input")
    shutil.copytree(os.path.join(case_dir, "input"), inp)
    os.remove(os.path.join(inp, "secondary-material.json"))
    m = jload(os.path.join(inp, "material.json"))
    m["paragraphs"] = [p for p in m["paragraphs"] if p["source_id"] != "paper-B"]
    jdump(os.path.join(inp, "material.json"), m)
    os.remove(os.path.join(inp, "secondary-publisher.xml"))
    rc, o = run("ingest.py", "--input", inp, "--work", os.path.join(tmp, "t4b", "work"))
    rep = jload(os.path.join(tmp, "t4b", "work", "corpus", "ingest_report.json"))
    res["missing_secondary_text"] = {"ingest_status": rep["status"], "warnings": rep["warnings"], "pass": rep["status"] == "partial"}
    # (c) XML-only fallback for the secondary paper
    inp = os.path.join(tmp, "t4c", "input")
    shutil.copytree(os.path.join(case_dir, "input"), inp)
    os.remove(os.path.join(inp, "secondary-material.json"))
    m = jload(os.path.join(inp, "material.json"))
    m["paragraphs"] = [p for p in m["paragraphs"] if p["source_id"] != "paper-B"]
    jdump(os.path.join(inp, "material.json"), m)
    rc, o = run("ingest.py", "--input", inp, "--work", os.path.join(tmp, "t4c", "work"))
    rep = jload(os.path.join(tmp, "t4c", "work", "corpus", "ingest_report.json"))
    b = next(s for s in rep["sources"] if s["source_id"] == "paper-B")
    res["xml_fallback"] = {"paper_B_paragraphs": b["paragraph_count"], "location_kind": b["location_kind"], "warnings": rep["warnings"], "pass": b["paragraph_count"] > 50}
    # (d) queries with no result
    g = os.path.join(case_dir, "work", "graph", "graph.json")
    rc1, o1 = run("query_graph.py", "--graph", g, "find", "unobtainium")
    rc2, o2 = run("query_graph.py", "--graph", g, "path", "lactic acid", "phenol", "--source", "paper-A")
    res["empty_queries"] = {"find_exit": rc1, "find_status": json.loads(o1)["status"], "find_reason": json.loads(o1).get("reason"),
                            "path_status": json.loads(o2)["status"], "path_reason": json.loads(o2).get("reason"),
                            "pass": json.loads(o1)["status"] == "no_result" and json.loads(o2)["status"] == "no_result"}
    # (e) determinism: build twice
    w = os.path.join(tmp, "t4e")
    shutil.copytree(os.path.join(case_dir, "work", "corpus"), os.path.join(w, "corpus"))
    shutil.copytree(os.path.join(case_dir, "work", "extract"), os.path.join(w, "extract"))
    run("build_graph.py", "--work", w)
    h1 = hashlib.sha256(strip_volatile(jload(os.path.join(w, "graph", "graph.json"))).encode()).hexdigest()
    run("build_graph.py", "--work", w)
    h2 = hashlib.sha256(strip_volatile(jload(os.path.join(w, "graph", "graph.json"))).encode()).hexdigest()
    res["deterministic_rebuild"] = {"sha256_run1": h1[:16], "sha256_run2": h2[:16], "pass": h1 == h2}
    # (f) broken extraction JSON
    with open(os.path.join(w, "extract", "paper-B.json"), "w", encoding="utf-8") as f:
        f.write("{not json")
    rc, o = run("build_graph.py", "--work", w)
    gg = jload(os.path.join(w, "graph", "graph.json"))
    res["broken_extraction_file"] = {"exit": rc, "warnings": gg["warnings"], "pass": rc == 0 and any("invalid JSON" in x for x in gg["warnings"])}
    # (g) DOI source_id sanitization + JSON Schema / deliverables contract
    t4g_inp = os.path.join(tmp, "t4g", "input")
    t4g_work = os.path.join(tmp, "t4g", "work")
    t4g_out = os.path.join(tmp, "t4g", "output")
    os.makedirs(t4g_inp, exist_ok=True)
    jdump(os.path.join(t4g_inp, "case.json"), {
        "schema": {
            "properties": {
                "summary": {"type": "string"},
                "count": {"type": "integer"},
                "uncertainty": {"type": "string"},
            },
            "required": ["summary", "count", "uncertainty"],
        },
        "deliverables": ["summary_graph.md"],
        "queries": [],
    })
    jdump(os.path.join(t4g_inp, "material.json"), {
        "sources": [{"source_id": "10.1038/s41586"}],
        "paragraphs": [{"source_id": "10.1038/s41586", "paragraph_id": "p1", "text": "Lactic acid inhibits E. coli."}],
    })
    rc_i, _ = run("ingest.py", "--input", t4g_inp, "--work", t4g_work)
    rep_g = jload(os.path.join(t4g_work, "corpus", "ingest_report.json"))
    corpus_file = rep_g["sources"][0].get("corpus_file")
    os.makedirs(os.path.join(t4g_work, "extract"), exist_ok=True)
    jdump(os.path.join(t4g_work, "extract", "10.1038_s41586.json"), {
        "source_id": "10.1038/s41586",
        "entities": [{"name": "lactic acid", "type": "compound"}],
        "relations": [],
    })
    rc_r, _ = run("run_all.py", "--input", t4g_inp, "--work", t4g_work, "--out", t4g_out)
    res_g = jload(os.path.join(t4g_out, "result.json"))
    res["doi_and_schema_contract"] = {
        "ingest_exit": rc_i,
        "corpus_file": corpus_file,
        "run_exit": rc_r,
        "has_summary": isinstance(res_g.get("summary"), str),
        "count_is_int": isinstance(res_g.get("count"), int) and not isinstance(res_g.get("count"), bool),
        "has_deliverable": os.path.exists(os.path.join(t4g_out, "summary_graph.md")),
        "pass": (rc_i == 0 and corpus_file == "10.1038_s41586.txt"
                 and os.path.exists(os.path.join(t4g_work, "corpus", "10.1038_s41586.txt"))
                 and rc_r == 0 and isinstance(res_g.get("summary"), str)
                 and isinstance(res_g.get("count"), int) and not isinstance(res_g.get("count"), bool)
                 and "uncertainty" in res_g and os.path.exists(os.path.join(t4g_out, "summary_graph.md"))),
    }
    res["pass"] = all(v["pass"] for v in res.values() if isinstance(v, dict))
    return res


# ------------------------------------------------------------------ T5 ---
def t5_case(case_dir):
    r = jload(os.path.join(case_dir, "output", "result.json"))
    chk = jload(os.path.join(case_dir, "output", "check_report.json"))
    ev = [ev for e in r["edges"] for ev in e["evidence"] if ev.get("match") != "metadata"]
    return {"status": r["status"], "stats": r["stats"], "queries": {q["id"]: q["status"] for q in r["queries"]},
            "edge_evidence_match": {m: sum(1 for x in ev if x["match"] == m) for m in ("exact", "normalized", "approx")},
            "check": {k: chk[k] for k in ("ok", "evidence_items_checked")}, "pass": chk["ok"] and r["status"] in ("success", "partial")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default=os.path.join(ROOT, "testdata", "case1"))
    ap.add_argument("--out", default=os.path.join(ROOT, "tests", "results"))
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="kgtest_")
    rep = {}
    have_case = os.path.exists(os.path.join(a.case, "work", "extract"))
    if have_case:
        rep["T1_negative_controls"] = t1_negative(a.case, tmp)
    rep["T2_alignment"] = t2_alignment(tmp)
    if have_case:
        rep["T3_incremental"] = t3_incremental(a.case, tmp)
        rep["T4_failures"] = t4_failures(a.case, tmp)
        rep["T5_real_case"] = t5_case(a.case)
    os.makedirs(a.out, exist_ok=True)
    jdump(os.path.join(a.out, "test_report.json"), rep)
    lines = ["# Test report", ""]
    for k, v in rep.items():
        lines.append(f"## {k}: {'PASS' if v.get('pass') else 'FAIL'}\n\n```json\n{json.dumps(v, ensure_ascii=False, indent=1)[:6000]}\n```\n")
    with open(os.path.join(a.out, "test_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    for k, v in rep.items():
        print(f"{k}: {'PASS' if v.get('pass') else 'FAIL'}")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0 if all(v.get("pass") for v in rep.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
