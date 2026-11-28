#!/usr/bin/env python3
"""Lightweight incremental extractor helper (stdlib only).

Allows the agent to pass compact entity/relation JSON with `paragraph_id` and
a short `anchor` (e.g. first ~6 words of the target sentence). This script
expands each anchor into a verbatim quote from `work/corpus/<safe_source_id>.txt`
and appends/merges into `work/extract/<file>.json`.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from kglib import norm_text, read_json, write_json  # noqa: E402


def _load_corpus_paragraphs(work_dir, source_id):
    """Load {paragraph_id: text} for a given source_id from work/corpus/."""
    cdir = os.path.join(work_dir, "corpus")
    paras = {}
    safe_id = source_id.replace("/", "_")
    candidates = [
        os.path.join(cdir, f"{safe_id}.txt"),
        os.path.join(cdir, f"{source_id}.txt"),
    ]
    report = read_json(os.path.join(cdir, "ingest_report.json"), {}) or {}
    for s in report.get("sources", []):
        if s.get("source_id") == source_id and s.get("corpus_file"):
            candidates.insert(0, os.path.join(work_dir, s["corpus_file"]))
            candidates.insert(0, os.path.join(cdir, os.path.basename(s["corpus_file"])))
    target = next((p for p in candidates if os.path.exists(p)), None)
    if not target:
        return paras
    with open(target, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.match(r"^\[([^\]]+)\]\s*(?:\([^)]*\)\s*)?(.*)$", line.rstrip("\r\n"))
            if m:
                paras[m.group(1).strip()] = m.group(2).strip()
    return paras


def expand_anchor(anchor, para_text, max_len=260):
    """Find anchor in para_text and return a verbatim 12-260 char quote."""
    if not anchor or not para_text:
        return anchor or ""
    idx = para_text.find(anchor)
    if idx == -1:
        # Case-insensitive / whitespace-normalized search
        words = [re.escape(w) for w in anchor.strip().split() if w]
        if words:
            pat = re.compile(r"\s+".join(words), re.I)
            m = pat.search(para_text)
            if m:
                idx = m.start()
    if idx == -1:
        # Fallback: match first 4 words
        words = [re.escape(w) for w in anchor.strip().split()[:4] if w]
        if len(words) >= 2:
            m = re.compile(r"\s+".join(words), re.I).search(para_text)
            if m:
                idx = m.start()
    if idx == -1:
        return anchor
    # Expand to sentence boundary or max_len
    end = min(len(para_text), idx + max_len)
    # Try to end at a sentence punctuation if within [idx+30, end]
    sub = para_text[idx:end]
    sent_m = re.search(r"[.!?。；;](?:\s|$)", sub[30:])
    if sent_m:
        end = idx + 30 + sent_m.start() + 1
    quote = para_text[idx:end].strip()
    if len(quote) < 12 and len(para_text) >= 12:
        quote = para_text[max(0, idx):min(len(para_text), idx + 120)].strip()
    return quote


def _expand_item_quotes(item, paras):
    pid = item.get("paragraph_id", "")
    anchor = item.pop("anchor", None) or item.pop("quote_anchor", None)
    if anchor and (not item.get("quote") or len(item.get("quote", "")) < len(anchor) + 5):
        ptext = paras.get(pid, "")
        item["quote"] = expand_anchor(anchor, ptext) if ptext else anchor
    return item


def main():
    ap = argparse.ArgumentParser(description="Append compact entities/relations with anchor-expanded verbatim quotes.")
    ap.add_argument("--work", default="/app/work", help="Work directory")
    ap.add_argument("--source", required=True, help="source_id")
    ap.add_argument("--out", help="Output extract json path (default: <work>/extract/<safe_source_id>.json)")
    ap.add_argument("--data", help="JSON string or @path/to/chunk.json (reads stdin if omitted)")
    a = ap.parse_known_args()[0]

    if a.data:
        if a.data.startswith("@"):
            with open(a.data[1:], "r", encoding="utf-8-sig") as f:
                payload = json.load(f)
        else:
            payload = json.loads(a.data)
    else:
        payload = json.load(sys.stdin)

    safe_id = a.source.replace("/", "_")
    out_path = a.out or os.path.join(a.work, "extract", f"{safe_id}.json")
    existing = read_json(out_path, None) or {"source_id": a.source, "entities": [], "relations": [], "not_reported": []}

    paras = _load_corpus_paragraphs(a.work, a.source)

    new_entities = payload.get("entities", [])
    for ent in new_entities:
        for m in ent.get("mentions", []):
            _expand_item_quotes(m, paras)
    existing.setdefault("entities", []).extend(new_entities)

    new_rels = payload.get("relations", [])
    for rel in new_rels:
        _expand_item_quotes(rel, paras)
    existing.setdefault("relations", []).extend(new_rels)

    new_nr = payload.get("not_reported", [])
    existing.setdefault("not_reported", []).extend(new_nr)

    write_json(out_path, existing)
    print(f"kg_add: +{len(new_entities)} entities, +{len(new_rels)} relations -> {out_path} (total: {len(existing['entities'])}E, {len(existing['relations'])}R)")


if __name__ == "__main__":
    main()
