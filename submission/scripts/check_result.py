#!/usr/bin/env python3
"""Self-check of /app/output/result.json against the corpus (independent of build_graph).

    python check_result.py --result /app/output/result.json --work /app/work

Re-verifies every node/edge quote in its cited paragraph, checks each item names a real
source_id, that the root (primary) DOI is not attached to the secondary paper, that >=3 queries
ran, and that all output_contract fields exist. Exit 1 if any hard check fails.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kglib import read_json, read_jsonl, write_json, quote_match  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True)
    ap.add_argument("--work", default="/app/work")
    a = ap.parse_args()
    r = read_json(a.result)
    paras = {(p["source_id"], p["paragraph_id"]): p["text"] for p in read_jsonl(os.path.join(a.work, "corpus", "paragraphs.jsonl"))}
    srcs = {s["source_id"]: s for s in r.get("sources", [])}
    hard, soft = [], []
    n_checked = 0
    for kind in ("nodes", "edges"):
        for it in r.get(kind, []):
            evs = it.get("evidence") or []
            if not evs:
                hard.append(f"{kind[:-1]} {it.get('id')} has no evidence")
            for ev in evs:
                if ev.get("match") == "metadata":
                    if ev.get("source_id") not in srcs:
                        hard.append(f"{it.get('id')}: unknown metadata source_id {ev.get('source_id')}")
                    continue
                n_checked += 1
                if ev.get("source_id") not in srcs:
                    hard.append(f"{it.get('id')}: unknown source_id {ev.get('source_id')}")
                    continue
                t = paras.get((ev["source_id"], ev["paragraph_id"]))
                if t is None:
                    hard.append(f"{it.get('id')}: paragraph {ev['source_id']}:{ev['paragraph_id']} not in corpus")
                else:
                    qm = quote_match(ev.get("quote", ""), t)[0]
                    if qm == "absent":
                        hard.append(f"{it.get('id')}: quote not found in {ev['source_id']}:{ev['paragraph_id']}")
                    elif qm == "approx":
                        soft.append(f"{it.get('id')}: approx quote match in {ev['source_id']}:{ev['paragraph_id']} (needs review)")
            if kind == "edges" and it.get("source_id") not in srcs:
                hard.append(f"edge {it.get('id')} source_id {it.get('source_id')} unknown")
    dois = [s.get("doi") for s in srcs.values()]
    if len(dois) >= 2 and dois[0] and dois[0] == dois[1]:
        hard.append("primary DOI copied onto the secondary source")
    qok = [q for q in r.get("queries", []) if q.get("status") == "ok"]
    if len(qok) < 3:
        soft.append(f"only {len(qok)} queries with results")
    for q in qok:
        for e in q.get("edges", []):
            if not e.get("evidence"):
                hard.append(f"query {q.get('id')} edge {e.get('id')} lacks evidence")
    miss = [k for k, v in (r.get("output_contract_mapping") or {}).items() if v is None]
    if miss:
        soft.append(f"contract fields left null: {miss}")
    if not r.get("case_id"):
        hard.append("case_id missing")
    rep = {"ok": not hard, "evidence_items_checked": n_checked, "hard_failures": hard[:200], "warnings": soft}
    write_json(os.path.join(os.path.dirname(a.result), "check_report.json"), rep)
    print(f"check_result: ok={rep['ok']} checked={n_checked} hard={len(hard)} warnings={soft}")
    for h in hard[:15]:
        print("  FAIL", h)
    return 0 if not hard else 1


if __name__ == "__main__":
    sys.exit(main())
