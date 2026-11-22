#!/usr/bin/env python3
"""Find paragraphs containing a phrase or regex, to copy exact quotes.

    python find_text.py --work /app/work [--source paper-B] "pseudo-second-order"
    python find_text.py --work /app/work --pid p-0059 --source paper-A      # print one paragraph
Prints  source_id | paragraph_id | section | match in context (case-insensitive; dashes/quotes normalised).
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kglib import read_jsonl, norm_text  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="/app/work")
    ap.add_argument("--source")
    ap.add_argument("--pid")
    ap.add_argument("--context", type=int, default=160)
    ap.add_argument("pattern", nargs="?")
    a = ap.parse_args()
    paras = read_jsonl(os.path.join(a.work, "corpus", "paragraphs.jsonl"))
    n = 0
    for p in paras:
        if a.source and p["source_id"] != a.source:
            continue
        if a.pid:
            if p["paragraph_id"] == a.pid:
                print(f"{p['source_id']} | {p['paragraph_id']} | {p['section']}\n{p['text']}")
                n += 1
            continue
        t = p["text"]
        try:
            rx = re.compile(a.pattern, re.I)
        except re.error:
            rx = re.compile(re.escape(a.pattern), re.I)
        m = rx.search(t) or rx.search(norm_text(t))
        if m:
            src = t if rx.search(t) else norm_text(t)
            lo, hi = max(0, m.start() - a.context), min(len(src), m.end() + a.context)
            print(f"{p['source_id']} | {p['paragraph_id']} | {p['section'][:50]} | ...{src[lo:hi]}...")
            n += 1
    if not n:
        print("no match")
    return 0 if n else 1


if __name__ == "__main__":
    sys.exit(main())
