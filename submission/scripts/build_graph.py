#!/usr/bin/env python3
"""Step 3: turn per-paper extraction files into one evidence-bound graph.

    python build_graph.py --work /app/work [--previous OLD/graph.json]

Reads   work/corpus/{paragraphs.jsonl,sources.json}
        work/extract/<source_id>.json          (written by the agent, schema in SKILL.md)
        work/extract/alignment_overrides.json  (optional: forced merge / split with reason)
Writes  work/graph/graph.json                  nodes, edges, merge_log, conflicts, rejected, change_log
Checks  every mention / relation quote against the cited paragraph (exact > normalized > approx),
        entity name present in its evidence paragraph, predicate vocabulary + domain/range,
        numbers of a Measurement present in its quote, hedging / citation cues vs declared strength.
Alignment: within a paper, entities sharing a name/alias key are one node. Across papers only
        CONCEPT types (Material, Method, Task, Metric, Instrument, Researcher) may merge, and only
        on an equal full-name key (abbreviation alone is never enough). Instance types (Sample,
        Measurement, Conclusion, Dataset, Model, Condition, Paper) never merge across papers.
"""
import argparse
import glob
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kglib import (CONCEPT_TYPES, ENTITY_TYPES, PREDICATES, STRENGTHS, HEDGE_RE, CITE_RE, VERSION,  # noqa: E402
                   read_json, read_jsonl, write_json, quote_match, name_key, is_abbrev, slug, short_hash,
                   jaccard, numbers_in, norm_text, squash, mentioned, distinct_jaccard, DESCRIPTIVE_TYPES)

TYPE_ALIASES = {"researcher": "Researcher", "author": "Researcher", "person": "Researcher", "material": "Material",
                "chemical": "Material", "compound": "Material", "adsorbate": "Material", "adsorbent": "Material",
                "sample": "Sample", "composite": "Sample", "specimen": "Sample", "method": "Method",
                "technique": "Method", "model": "Model", "algorithm": "Method", "task": "Task", "application": "Task",
                "metric": "Metric", "property": "Metric", "quantity": "Metric", "result": "Measurement",
                "measurement": "Measurement", "value": "Measurement", "finding": "Conclusion", "conclusion": "Conclusion",
                "claim": "Conclusion", "dataset": "Dataset", "instrument": "Instrument", "equipment": "Instrument",
                "condition": "Condition", "paper": "Paper", "mechanism": "Mechanism", "interaction": "Mechanism"}


class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def norm_type(t):
    if t in ENTITY_TYPES:
        return t
    return TYPE_ALIASES.get(str(t or "").strip().lower())


def check_quote(src, pid, quote, para_index, xml_index):
    """Verify one evidence item. Returns dict with status and the paragraph text used."""
    p = para_index.get((src, pid))
    if p is None:
        # tolerate id given without prefix differences ("p12" vs "p-0012") only via exact lookup -> fail loudly
        return {"status": "paragraph_not_found", "score": 0.0}
    st, sc = quote_match(quote, p["text"])
    out = {"status": st, "score": sc, "section": p.get("section", "")}
    if xml_index:
        xs = xml_index.get(src)
        if xs:
            out["publisher_xml_check"] = "found" if squash(quote) and squash(quote) in xs else "not_found_in_xml"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="/app/work")
    ap.add_argument("--previous", help="graph.json from an earlier run: keep its node ids (incremental update)")
    ap.add_argument("--min-quote", type=int, default=12)
    a = ap.parse_args()
    cdir, edir, gdir = (os.path.join(a.work, d) for d in ("corpus", "extract", "graph"))
    paras = read_jsonl(os.path.join(cdir, "paragraphs.jsonl"))
    sources = read_json(os.path.join(cdir, "sources.json"), [])
    if not paras:
        print("build_graph: no paragraphs (run ingest.py first)")
        return 2
    para_index = {(p["source_id"], p["paragraph_id"]): p for p in paras}
    pid_sets = defaultdict(set)
    for p in paras:
        pid_sets[p["source_id"]].add(p["paragraph_id"])
    xml_index = defaultdict(str)
    for p in read_jsonl(os.path.join(cdir, "xml_paragraphs.jsonl")):
        if p.get("source_id"):
            xml_index[p["source_id"]] += squash(p["text"])
    src_ids = [s["source_id"] for s in sources]

    rejected, warnings, flags = [], [], []
    ents = {}       # local uid -> entity record (one per extraction entry)
    key_of = {}     # (source, local key/name) -> uid
    ex_files = sorted(f for f in glob.glob(os.path.join(edir, "*.json")) if not os.path.basename(f).startswith("alignment"))
    extractions = {}
    for f in ex_files:
        try:
            ex = read_json(f)
        except Exception as e:  # noqa: BLE001
            warnings.append(f"{os.path.basename(f)}: invalid JSON ({e}); file skipped")
            continue
        if not isinstance(ex, dict):
            warnings.append(f"{os.path.basename(f)}: top level must be an object; file skipped")
            continue
        src = ex.get("source_id") or os.path.basename(f).split(".")[0]
        if src not in src_ids:
            warnings.append(f"{os.path.basename(f)}: source_id '{src}' not in corpus sources {src_ids}; skipped")
            continue
        if src in extractions:  # several part files per paper (paper-A.json, paper-A.part2.json, ...)
            for k in ("entities", "relations", "not_reported"):
                extractions[src].setdefault(k, []).extend(ex.get(k) or [])
        else:
            extractions[src] = {k: list(ex.get(k) or []) for k in ("entities", "relations", "not_reported")}
    missing = [s for s in src_ids if s not in extractions and pid_sets.get(s)]
    for s in missing:
        warnings.append(f"no extraction file for source {s} (graph is partial for this paper)")

    # ------------------------------------------------------------ entities ---
    for src, ex in extractions.items():
        for i, e in enumerate(ex.get("entities", [])):
            uid = f"{src}#e{i}"
            name = (e.get("name") or "").strip()
            typ = norm_type(e.get("type"))
            if not name or not typ:
                rejected.append({"kind": "entity", "source_id": src, "item": e, "reason": "missing name or unknown type"})
                continue
            ev_ok, evs = [], []
            for m in e.get("mentions") or e.get("evidence") or []:
                pid, q = str(m.get("paragraph_id") or m.get("pid") or ""), m.get("quote") or ""
                chk = check_quote(src, pid, q, para_index, xml_index)
                ev = {"source_id": src, "paragraph_id": pid, "quote": q, "match": chk["status"], "match_score": chk["score"],
                      "section": chk.get("section", "")}
                if "publisher_xml_check" in chk:
                    ev["publisher_xml_check"] = chk["publisher_xml_check"]
                if len(q) < a.min_quote and chk["status"] != "paragraph_not_found":
                    ev["match"] = "quote_too_short" if chk["status"] == "absent" else chk["status"]
                text = para_index.get((src, pid), {}).get("text", "")
                names = [name] + list(e.get("aliases") or [])
                ev["name_in_paragraph"] = typ in DESCRIPTIVE_TYPES or mentioned(names, text)
                evs.append(ev)
                if ev["match"] in ("exact", "normalized", "approx"):
                    ev_ok.append(ev)
            if not ev_ok:
                rejected.append({"kind": "entity", "source_id": src, "name": name, "type": typ, "evidence": evs,
                                 "reason": "no mention quote found in the cited paragraph"})
                continue
            if not any(ev["name_in_paragraph"] for ev in ev_ok):
                flags.append({"kind": "entity", "source_id": src, "name": name, "flag": "name_not_in_evidence_paragraph",
                              "detail": "neither name nor alias occurs in the cited paragraphs; check it is not an inferred concept"})
            ents[uid] = {"uid": uid, "source_id": src, "key": str(e.get("key") or name), "name": name, "type": typ,
                         "aliases": sorted({x.strip() for x in (e.get("aliases") or []) if x and x.strip() and x.strip() != name}),
                         "attributes": e.get("attributes") or {}, "attribution": e.get("attribution", "author"),
                         "definition": e.get("definition"), "evidence": ev_ok,
                         "rejected_evidence": [ev for ev in evs if ev not in ev_ok]}
            key_of[(src, str(e.get("key") or name))] = uid
            key_of.setdefault((src, name), uid)
            for al in e.get("aliases") or []:
                key_of.setdefault((src, al), uid)

    # Paper nodes + authors from manifest (metadata evidence, not paragraph evidence)
    for s in sources:
        uid = f"{s['source_id']}#paper"
        ents[uid] = {"uid": uid, "source_id": s["source_id"], "key": "paper", "name": s.get("title") or s["source_id"], "type": "Paper",
                     "aliases": [x for x in [s.get("doi")] if x], "attributes": {"doi": s.get("doi"), "license": s.get("license"), "sha256": s.get("sha256")},
                     "attribution": "metadata", "evidence": [{"source_id": s["source_id"], "paragraph_id": "corpus-manifest", "quote": f"doi={s.get('doi')}", "match": "metadata"}]}
        key_of[(s["source_id"], "paper")] = uid
        for j, au in enumerate(s.get("authors") or []):
            auid = f"{s['source_id']}#au{j}"
            ents[auid] = {"uid": auid, "source_id": s["source_id"], "key": au, "name": au, "type": "Researcher", "aliases": [], "attributes": {"author_position": j + 1},
                          "attribution": "metadata", "evidence": [{"source_id": s["source_id"], "paragraph_id": "corpus-manifest", "quote": au, "match": "metadata"}]}

    # ------------------------------------------------------------ alignment ---
    uf, merge_log, conflicts = UF(), [], []
    # within-paper: shared name/alias key + compatible type
    by_key = defaultdict(list)
    for uid, e in ents.items():
        for n in [e["name"]] + e["aliases"]:
            by_key[(e["source_id"], name_key(n))].append(uid)
    for (src, k), uids in by_key.items():
        uids = sorted(set(uids))
        for u in uids[1:]:
            a0, b0 = ents[uids[0]], ents[u]
            if a0["type"] != b0["type"]:
                conflicts.append({"kind": "same_name_different_type", "scope": "within_paper", "source_id": src, "key": k,
                                  "items": [(a0["name"], a0["type"]), (b0["name"], b0["type"])], "decision": "kept_separate"})
                continue
            if uf.find(uids[0]) != uf.find(u):
                uf.union(uids[0], u)
                merge_log.append({"scope": "within_paper", "source_id": src, "merged": [a0["name"], b0["name"]], "type": a0["type"],
                                  "basis": f"shared name/alias key '{k}' in the same paper"})
    # abbreviation expansions per paper: alias that is an abbreviation -> full names
    abbr_exp = defaultdict(lambda: defaultdict(set))
    for uid, e in ents.items():
        for al in [e["name"]] + e["aliases"]:
            if is_abbrev(al):
                for full in [e["name"]] + e["aliases"]:
                    if not is_abbrev(full):
                        abbr_exp[name_key(al)][e["source_id"]].add(name_key(full))
    overrides = read_json(os.path.join(edir, "alignment_overrides.json"), {}) or {}
    forced_split = {frozenset(map(str, p[:2])) for p in overrides.get("split", [])}
    # cross-paper: concept types only, equal full-name key
    full_keys = defaultdict(list)
    for uid, e in ents.items():
        for n in [e["name"]] + e["aliases"]:
            if not is_abbrev(n) and len(name_key(n)) >= 3:
                full_keys[(e["type"], name_key(n))].append(uid)
    for (typ, k), uids in sorted(full_keys.items()):
        srcs = {ents[u]["source_id"] for u in uids}
        if len(srcs) < 2:
            continue
        names = sorted({ents[u]["name"] for u in uids})
        if typ not in CONCEPT_TYPES:
            conflicts.append({"kind": "same_label_different_object", "scope": "cross_paper", "type": typ, "key": k, "names": names,
                              "sources": sorted(srcs), "decision": "not_merged",
                              "reason": f"{typ} is paper-specific (sample / result / dataset instance); equal labels do not make the same object"})
            continue
        if typ == "Researcher":
            conflicts.append({"kind": "possible_same_person", "scope": "cross_paper", "key": k, "names": names, "sources": sorted(srcs),
                              "decision": "not_merged", "reason": "equal personal name only; no ORCID/affiliation evidence in the material"})
            continue
        roots = sorted({uf.find(u) for u in uids})
        for r in roots[1:]:
            pair = frozenset([ents[roots[0]]["name"], ents[r]["name"]])
            if pair in forced_split:
                continue
            defs = [ents[u].get("definition") for u in uids if ents[u].get("definition")]
            uf.union(roots[0], r)
            merge_log.append({"scope": "cross_paper", "type": typ, "merged": names, "sources": sorted(srcs), "basis": f"equal normalised full name '{k}'",
                              "note": "shared concept node only; each paper's conditions, samples and values stay on paper-scoped nodes/edges",
                              "definitions": defs[:4]})
    # abbreviation homonyms across papers
    for ab, per in abbr_exp.items():
        if len(per) < 2:
            continue
        sets = list(per.values())
        if any(x & y for i, x in enumerate(sets) for y in sets[i + 1:]):
            continue  # same expansion in at least two papers: consistent, merge handled by full name
        conflicts.append({"kind": "abbreviation_homonym", "scope": "cross_paper", "abbreviation": ab,
                          "expansions": {s: sorted(v) for s, v in per.items()}, "decision": "not_merged",
                          "reason": "same abbreviation expands to different full names in different papers"})
    # agent-declared cross-paper conflicts (e.g. opposite interpretations): every quote must verify
    for c in overrides.get("conflicts", []):
        evs = []
        for it in c.get("evidence", []):
            src, pid, q = it.get("source_id"), str(it.get("paragraph_id")), it.get("quote", "")
            chk = check_quote(src, pid, q, para_index, xml_index)
            evs.append({"source_id": src, "paragraph_id": pid, "quote": q, "match": chk["status"]})
        ok = len(evs) >= 2 and all(e["match"] in ("exact", "normalized", "approx") for e in evs)
        (conflicts if ok else rejected).append({"kind": c.get("kind", "interpretation_conflict"), "scope": "cross_paper" if len({e["source_id"] for e in evs}) > 1 else "within_paper",
                                                 "names": c.get("about"), "evidence": evs, "decision": "both_kept_not_resolved",
                                                 "reason": c.get("reason", "") if ok else "declared conflict rejected: needs >=2 verified quotes"})
    # near-duplicate names across papers (candidates for human review, never auto-merged)
    concept = [u for u, e in ents.items() if e["type"] in CONCEPT_TYPES and e["attribution"] != "metadata"]
    seen_pairs = set()
    for i, u in enumerate(concept):
        for v in concept[i + 1:]:
            eu, ev = ents[u], ents[v]
            if eu["source_id"] == ev["source_id"] or eu["type"] != ev["type"] or eu["type"] == "Researcher" or uf.find(u) == uf.find(v):
                continue
            pair = frozenset([name_key(eu["name"]), name_key(ev["name"])])
            j = distinct_jaccard(eu["name"], ev["name"])
            if j > 0.5 and pair not in seen_pairs:
                seen_pairs.add(pair)
                conflicts.append({"kind": "similar_name_review", "scope": "cross_paper", "type": eu["type"], "names": [eu["name"], ev["name"]],
                                  "sources": [eu["source_id"], ev["source_id"]], "token_jaccard": round(j, 2), "decision": "not_merged",
                                  "reason": "similar but not equal names; may be broader/narrower or different objects (e.g. GO vs reduced GO)"})
    for m in overrides.get("merge", []):
        a_name, b_name, why = (list(m) + ["", "", ""])[:3]
        ua = [u for u, e in ents.items() if e["name"] == a_name or a_name in e["aliases"]]
        ub = [u for u, e in ents.items() if e["name"] == b_name or b_name in e["aliases"]]
        if ua and ub and ents[ua[0]]["type"] == ents[ub[0]]["type"] and (ents[ua[0]]["type"] in CONCEPT_TYPES or ents[ua[0]]["source_id"] == ents[ub[0]]["source_id"]):
            uf.union(ua[0], ub[0])
            merge_log.append({"scope": "override", "merged": [a_name, b_name], "basis": why or "agent override (no reason given)"})
        else:
            warnings.append(f"override merge {a_name!r}+{b_name!r} refused (not found, type differs, or cross-paper instance)")

    # ---------------------------------------------------------- node build ---
    groups = defaultdict(list)
    for uid in ents:
        groups[uf.find(uid)].append(uid)
    prev = read_json(a.previous, {}) if a.previous else {}
    prev_by_key, prev_sources = {}, {n["id"]: n.get("sources", []) for n in (prev or {}).get("nodes", [])}
    for n in (prev or {}).get("nodes", []):
        for k in n.get("match_keys", []):
            prev_by_key[k] = n["id"]
    nodes, node_of, change_log, used_ids = [], {}, [], set()
    for root, uids in sorted(groups.items()):
        members = [ents[u] for u in sorted(uids)]
        typ = members[0]["type"]
        srcs = sorted({m["source_id"] for m in members})
        best = max(members, key=lambda m: (len(m["evidence"]), not is_abbrev(m["name"]), len(m["name"])))
        name = best["name"]
        if typ == "Paper":
            nid = f"{srcs[0]}:Paper"
        elif typ in CONCEPT_TYPES and (len(srcs) > 1 or typ != "Researcher"):
            nid = f"C:{typ}:{slug(name_key(name) and name)}"
        else:
            nid = f"{srcs[0]}:{typ}:{slug(name)}"
        mkeys = sorted({f"{typ}|{('*' if nid.startswith('C:') else m['source_id'])}|{name_key(n)}" for m in members for n in [m['name']] + m['aliases']})
        prev_id = next((prev_by_key[k] for k in mkeys if k in prev_by_key), None)
        if prev_id:
            nid = prev_id
            old_src = prev_sources.get(prev_id, [])
            if set(srcs) - set(old_src):
                change_log.append({"action": "node_extended", "id": nid, "name": name, "new_sources": sorted(set(srcs) - set(old_src)),
                                   "basis": "matched previous node by name/alias key; id kept"})
        elif prev:
            change_log.append({"action": "node_added", "id": nid, "name": name})
        base, k = nid, 2
        while nid in used_ids:
            nid = f"{base}~{k}"
            k += 1
        used_ids.add(nid)
        aliases = sorted({n for m in members for n in [m["name"]] + m["aliases"]} - {name})
        node = {"id": nid, "type": typ, "label": name, "aliases": aliases, "scope": "concept" if nid.startswith("C:") else "paper", "cross_paper": len(srcs) > 1,
                "sources": srcs, "attribution": sorted({m["attribution"] for m in members}),
                "attributes": {m["source_id"]: m["attributes"] for m in members if m["attributes"]},
                "definitions": {m["source_id"]: m["definition"] for m in members if m.get("definition")},
                "evidence": [ev for m in members for ev in m["evidence"]][:12], "match_keys": mkeys}
        nodes.append(node)
        for u in uids:
            node_of[u] = nid
    if prev:
        kept = {n["id"] for n in prev.get("nodes", [])}
        for nid in kept - used_ids:
            change_log.append({"action": "node_missing_in_rebuild", "id": nid, "note": "present in previous graph, not rebuilt; kept in previous file, check extraction"})

    # --------------------------------------------------------------- edges ---
    edges = {}
    for s in sources:
        for j, au in enumerate(s.get("authors") or []):
            pid = node_of.get(f"{s['source_id']}#au{j}")
            eid = "R:" + short_hash(pid, "AUTHOR_OF", s["source_id"])
            edges[eid] = {"id": eid, "source": pid, "predicate": "AUTHOR_OF", "target": f"{s['source_id']}:Paper", "source_id": s["source_id"],
                          "strength": "direct", "attribution": "metadata", "conditions": {}, "polarity": "positive",
                          "evidence": [{"source_id": s["source_id"], "paragraph_id": "corpus-manifest", "quote": au, "match": "metadata"}], "flags": []}
    for src, ex in extractions.items():
        for i, r in enumerate(ex.get("relations", [])):
            subj, pred, obj = str(r.get("subject", "")), str(r.get("predicate", "")).upper(), str(r.get("object", ""))
            us, uo = key_of.get((src, subj)), key_of.get((src, obj))
            base = {"kind": "relation", "source_id": src, "item": r}
            if subj == "paper":
                us = f"{src}#paper"
            if not us or not uo or us not in node_of or uo not in node_of:
                rejected.append({**base, "reason": f"subject/object key not found among accepted entities of {src} ({subj!r} -> {obj!r})"})
                continue
            if pred not in PREDICATES:
                rejected.append({**base, "reason": f"predicate {pred!r} not in vocabulary {sorted(PREDICATES)}"})
                continue
            dom, rng, _ = PREDICATES[pred]
            ts, to = ents[us]["type"], ents[uo]["type"]
            if ts not in dom or to not in rng:
                rejected.append({**base, "reason": f"{pred} does not allow {ts} -> {to} (domain {sorted(dom)}, range {sorted(rng)})"})
                continue
            evs, ok = [], []
            items = r.get("evidence") or [{"paragraph_id": r.get("paragraph_id") or r.get("pid"), "quote": r.get("quote")}]
            for it in items:
                pid, q = str(it.get("paragraph_id") or it.get("pid") or ""), it.get("quote") or ""
                chk = check_quote(src, pid, q, para_index, xml_index)
                ev = {"source_id": src, "paragraph_id": pid, "quote": q, "match": chk["status"], "match_score": chk["score"], "section": chk.get("section", "")}
                if "publisher_xml_check" in chk:
                    ev["publisher_xml_check"] = chk["publisher_xml_check"]
                if len(q) < a.min_quote and chk["status"] == "absent":
                    ev["match"] = "quote_too_short"
                evs.append(ev)
                if ev["match"] in ("exact", "normalized", "approx"):
                    ok.append(ev)
            if not ok:
                rejected.append({**base, "evidence": evs, "reason": "relation quote not found in the cited paragraph"})
                continue
            eflags = []
            strength = r.get("strength", "direct")
            if strength not in STRENGTHS:
                eflags.append(f"unknown strength {strength!r} -> 'indirect'")
                strength = "indirect"
            qtxt = " ".join(ev["quote"] for ev in ok)
            if HEDGE_RE.search(qtxt) and strength == "direct":
                eflags.append("hedging cue in quote but strength=direct -> downgraded to hedged")
                strength = "hedged"
            if CITE_RE.search(qtxt) and r.get("attribution", "author") == "author":
                eflags.append("citation cue in quote; check the claim is the authors' own, not a cited one")
            ptext = " ".join(para_index[(src, ev["paragraph_id"])]["text"] for ev in ok)
            for side, u in (("subject", us), ("object", uo)):
                e = ents[u]
                if e["type"] in DESCRIPTIVE_TYPES:
                    continue
                if not mentioned([e["name"]] + e["aliases"], ptext):
                    eflags.append(f"{side} '{e['name']}' not named in the evidence paragraph (pronoun/inference?) -> needs_review")
            for u in (us, uo):
                if ents[u]["type"] == "Measurement":
                    val = str(ents[u]["attributes"].get("value", ""))
                    miss = [n for n in numbers_in(val) if n not in numbers_in(" ".join(ev["quote"] for ev in ents[u]["evidence"]) + " " + qtxt)]
                    if miss:
                        eflags.append(f"value number(s) {miss} of '{ents[u]['name']}' not in any quote")
            ns, no = node_of[us], node_of[uo]
            cond = r.get("conditions") or {}
            eid = "R:" + short_hash(ns, pred, no, src, sorted(cond.items()) if isinstance(cond, dict) else cond)
            if eid in edges:
                edges[eid]["evidence"] += ok
                continue
            edges[eid] = {"id": eid, "source": ns, "predicate": pred, "target": no, "source_id": src, "strength": strength,
                          "attribution": r.get("attribution", "author"), "polarity": r.get("polarity", "positive"),
                          "conditions": cond, "note": r.get("note"), "evidence": ok, "flags": eflags,
                          "needs_review": any("needs_review" in f or "not in any quote" in f for f in eflags)}
    # contradictions: same subject/predicate/object, opposite polarity
    by_triple = defaultdict(list)
    for e in edges.values():
        by_triple[(e["source"], e["predicate"], e["target"])].append(e)
    for t, es in by_triple.items():
        if len({e["polarity"] for e in es}) > 1:
            conflicts.append({"kind": "polarity_conflict", "triple": t, "edges": [e["id"] for e in es],
                              "sources": sorted({e["source_id"] for e in es}), "decision": "both_kept",
                              "reason": "papers/paragraphs disagree; not resolved into one conclusion"})
    if prev:
        old = {e["id"] for e in prev.get("edges", [])}
        change_log += [{"action": "edge_added", "id": k} for k in edges if k not in old]
    not_reported = {src: ex.get("not_reported", []) for src, ex in extractions.items() if ex.get("not_reported")}
    graph = {"schema": "literature-kg/0.1", "tool_version": VERSION, "sources": [{k: v for k, v in s.items() if k != "manifest_record"} for s in sources],
             "nodes": nodes, "edges": list(edges.values()), "merge_log": merge_log, "conflicts": conflicts,
             "flags": flags + [{"kind": "edge", "id": e["id"], "flags": e["flags"]} for e in edges.values() if e["flags"]],
             "rejected": rejected, "not_reported": not_reported, "warnings": warnings, "change_log": change_log,
             "previous_graph": a.previous}
    stats = {"nodes": len(nodes), "edges": len(edges), "shared_concepts": sum(1 for n in nodes if n["cross_paper"]),
             "nodes_by_source": {s: sum(1 for n in nodes if s in n["sources"]) for s in src_ids},
             "edges_by_source": {s: sum(1 for e in edges.values() if e["source_id"] == s) for s in src_ids},
             "rejected": len(rejected), "conflicts": len(conflicts), "needs_review_edges": sum(1 for e in edges.values() if e.get("needs_review"))}
    graph["stats"] = stats
    write_json(os.path.join(gdir, "graph.json"), graph)
    print("build_graph:", stats)
    for w in warnings:
        print("  WARN", w)
    for r in rejected[:25]:
        print("  REJECTED", r["kind"], r.get("name") or r.get("item", {}).get("subject", ""), "->", r["reason"][:150])
    if len(rejected) > 25:
        print(f"  ... {len(rejected) - 25} more rejected (see graph.json 'rejected')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
