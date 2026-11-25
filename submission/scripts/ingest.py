#!/usr/bin/env python3
"""Step 1: read the case folder, register sources, flatten every paragraph.

    python ingest.py --input /input --work /app/work

Writes  work/corpus/sources.json        one record per independent paper (manifest metadata)
        work/corpus/paragraphs.jsonl    {source_id, paragraph_id, section, text, origin}
        work/corpus/<source_id>.txt     reading dump: "[paragraph_id] (section) text"
        work/corpus/candidates.json     abbreviation definitions + frequent terms per source (hints only)
        work/corpus/ingest_report.json  files seen, counts, warnings (status ok|partial|failed)
The JSON schema of the material files is not assumed: any object holding a text
field and an id field is taken as a paragraph; the source is inherited from the
object, its ancestors, the manifest file mapping or the file name (primary/secondary).
"""
import argparse
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kglib import read_json, write_json, write_jsonl, sha256_file, norm_text  # noqa: E402

TEXT_KEYS = ["text", "content", "body", "paragraph", "para_text", "plain_text", "value", "p", "sentence"]
ID_KEYS = ["paragraph_id", "para_id", "pid", "paragraphId", "jats_id", "p_id", "block_id", "id", "anchor"]
SRC_KEYS = ["source_id", "sourceId", "paper_id", "doc_id", "document_id", "article_id", "source"]
SEC_KEYS = ["section", "section_title", "sec_title", "heading", "section_path", "sec", "title_path"]


def find_files(inp):
    root = inp if os.path.isdir(inp) else os.path.dirname(os.path.abspath(inp))
    files = []
    for pat in ("*", "*/*", "*/*/*"):
        files += [f for f in glob.glob(os.path.join(root, pat)) if os.path.isfile(f)]
    return root, sorted(set(files))


def first(d, keys):
    for k in keys:
        if k in d and d[k] not in (None, "", [], {}):
            return k, d[k]
    return None, None


# --------------------------------------------------------------- manifest ---
def parse_manifest(obj):
    """Return list of source dicts from a corpus manifest of unknown shape."""
    found = []

    def walk(x):
        if isinstance(x, dict):
            keys = set(x)
            if keys & {"doi", "DOI"} or (keys & set(SRC_KEYS) and keys & {"title", "authors", "license", "sha256", "file", "path"}):
                found.append(x)
                return
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(obj)
    sources = []
    for i, d in enumerate(found):
        _, sid = first(d, SRC_KEYS + ["id"])
        authors = d.get("authors") or d.get("author") or []
        if isinstance(authors, str):
            authors = [a.strip() for a in re.split(r";|\band\b|,(?=\s*[A-Z][a-z]+\s)", authors) if a.strip()]
        authors = [a if isinstance(a, str) else " ".join(str(a.get(k, "")) for k in ("given", "given_names", "first", "surname", "family", "last", "name") if a.get(k)).strip() for a in authors]
        files = []
        for k, v in d.items():
            if isinstance(v, str) and re.search(r"\.(json|xml|md|txt|pdf)$", v, re.I):
                files.append(os.path.basename(v))
            if isinstance(v, dict):
                files += [os.path.basename(s) for s in v.values() if isinstance(s, str) and re.search(r"\.(json|xml|md|txt|pdf)$", s, re.I)]
        sources.append({
            "source_id": str(sid) if sid else f"S{i + 1}",
            "doi": d.get("doi") or d.get("DOI"),
            "title": d.get("title"),
            "authors": [a for a in authors if a],
            "license": d.get("license") or d.get("licence"),
            "sha256": d.get("sha256") or d.get("source_sha256") or d.get("hash") or d.get("checksum"),
            "role": d.get("role") or d.get("kind"),
            "files": files,
            "manifest_record": d,
        })
    return sources


# ------------------------------------------------------- JSON paragraphs ---
def json_paragraphs(obj, default_src, fname):
    out = []

    def walk(x, src, sec, path):
        if isinstance(x, dict):
            _, s = first(x, SRC_KEYS)
            if isinstance(s, (str, int)):
                src = str(s)
            k_sec, v_sec = first(x, SEC_KEYS)
            if isinstance(v_sec, list):
                v_sec = " > ".join(map(str, v_sec))
            tk, tv = first(x, TEXT_KEYS)
            ik, iv = first(x, ID_KEYS)
            if isinstance(tv, str) and len(tv.strip()) >= 15 and isinstance(iv, (str, int)) and tk not in ("title",):
                out.append({"source_id": src, "paragraph_id": str(iv), "section": str(v_sec or sec or ""),
                            "text": tv.strip(), "origin": f"{fname}:{path}", "id_field": ik})
                return
            if isinstance(v_sec, str) and k_sec:
                sec = v_sec
            elif isinstance(x.get("title"), str) and len(x["title"]) < 200 and any(isinstance(v, list) for v in x.values()):
                sec = x["title"]
            for k, v in x.items():
                walk(v, src, sec, f"{path}.{k}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, src, sec, f"{path}[{i}]")

    walk(obj, default_src, "", "$")
    return out


# -------------------------------------------------------- XML paragraphs ---
def strip_ns(tag):
    return tag.split("}", 1)[-1] if isinstance(tag, str) else ""


def xml_paragraphs(path, src):
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        return [], f"xml parse error: {e}"
    out = []
    parent = {c: p for p in tree.iter() for c in p}
    n = 0
    for el in tree.iter():
        if strip_ns(el.tag) != "p":
            continue
        anc, secs, in_back = el, [], False
        while anc in parent:
            anc = parent[anc]
            t = strip_ns(anc.tag)
            if t in ("ref-list", "fn-group", "license", "permissions", "author-notes"):
                in_back = True
            if t in ("sec", "abstract", "app", "ack"):
                title = next((c for c in anc if strip_ns(c.tag) == "title"), None)
                secs.append("".join(title.itertext()).strip() if title is not None else t)
        if in_back:
            continue
        text = re.sub(r"\s+", " ", "".join(el.itertext())).strip()
        if len(text) < 15:
            continue
        n += 1
        pid = el.get("id") or f"xml-p{n:03d}"
        out.append({"source_id": src, "paragraph_id": pid, "section": " > ".join(reversed(secs)),
                    "text": text, "origin": f"{os.path.basename(path)}", "id_field": "id" if el.get("id") else "generated"})
    return out, None


def xml_meta(path):
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return {}
    meta = {}
    for el in root.iter():
        t = strip_ns(el.tag)
        if t == "article-id" and el.get("pub-id-type") == "doi" and "doi" not in meta:
            meta["doi"] = (el.text or "").strip()
        if t == "article-title" and "title" not in meta:
            meta["title"] = re.sub(r"\s+", " ", "".join(el.itertext())).strip()
    return meta


# -------------------------------------------------------- text fallbacks ---
def text_paragraphs(path, src):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    out, sec = [], ""
    for i, block in enumerate(re.split(r"\n\s*\n", raw)):
        b = block.strip()
        m = re.match(r"^#+\s+(.*)", b)
        if m and "\n" not in b:
            sec = m.group(1).strip()
            continue
        mid = re.match(r"^\[([A-Za-z0-9_.:-]+)\]\s*(.*)", b, re.S)
        if len(b) < 15:
            continue
        out.append({"source_id": src, "paragraph_id": mid.group(1) if mid else f"selfmade-md{i:03d}",
                    "section": sec, "text": (mid.group(2) if mid else b).strip(),
                    "origin": os.path.basename(path), "id_field": "inline" if mid else "generated"})
    return out


def pdf_paragraphs(path, src):
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return [], "PyMuPDF not installed; PDF not parsed"
    try:
        doc = fitz.open(path)
    except Exception as e:  # noqa: BLE001
        return [], f"PDF cannot be opened: {e}"
    if doc.needs_pass:
        return [], "PDF is encrypted"
    out = []
    for pno, page in enumerate(doc, 1):
        for bno, b in enumerate(page.get_text("blocks")):
            t = re.sub(r"\s+", " ", b[4]).strip()
            if len(t) >= 30:
                out.append({"source_id": src, "paragraph_id": f"pdfpage{pno}-b{bno}", "section": f"PDF page {pno}",
                            "text": t, "origin": os.path.basename(path), "id_field": "pdf_page_block"})
    if not out:
        return [], "PDF has no text layer (scanned?); OCR needed"
    return out, None


# ------------------------------------------------------------ candidates ---
ABBR_RE = re.compile(r"((?:[A-Za-z0-9Ͱ-Ͽ][\wͰ-Ͽ'-]*\s+){0,7}[A-Za-z0-9Ͱ-Ͽ][\wͰ-Ͽ'-]*)\s*\(([A-Z][A-Za-z0-9Ͱ-Ͽ+@/-]{1,11})s?\)")


def abbreviation_defs(text):
    """'magnetically modified graphene oxide (MGO)' -> ('MGO', 'magnetically modified graphene oxide')."""
    res = []
    for m in ABBR_RE.finditer(text):
        words, ab = m.group(1).split(), m.group(2)
        letters = [c.lower() for c in ab if c.isalpha()]
        if not letters:
            continue
        # shortest suffix of words whose initials cover the abbreviation letters in order
        best = None
        for k in range(1, len(words) + 1):
            cand = words[-k:]
            initials = "".join(w[0].lower() for w in cand if w[0].isalnum())
            joined = "".join(cand).lower()
            it = iter(joined)
            if initials and initials[0] == letters[0] and all(c in it for c in letters):
                best = " ".join(cand)
                if len(initials) >= len(letters) - 1:
                    break
        if best:
            res.append((ab, best.strip(" ,;")))
    return res


STOP = set("the a an of and or in on at to for with by from as is are was were be this that these those its their our we it which using used use than then also into via between within based after before under over".split())


def frequent_terms(paras, top=40):
    c = Counter()
    for p in paras:
        words = re.findall(r"[A-Za-z][A-Za-z0-9Ͱ-Ͽ-]+", p["text"])
        for n in (2, 3):
            for i in range(len(words) - n + 1):
                g = words[i:i + n]
                if g[0].lower() in STOP or g[-1].lower() in STOP:
                    continue
                c[" ".join(w.lower() for w in g)] += 1
    return [t for t, k in c.most_common(top * 2) if k >= 3][:top]


# ------------------------------------------------------------------ main ---
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/input")
    ap.add_argument("--work", default="/app/work")
    a = ap.parse_args()
    root, files = find_files(a.input)
    cdir = os.path.join(a.work, "corpus")
    os.makedirs(cdir, exist_ok=True)
    warnings, seen = [], []
    case = {}
    case_path = os.path.join(root, "case.json") if os.path.isdir(a.input) else a.input
    if os.path.exists(case_path):
        try:
            case = read_json(case_path) or {}
        except Exception as e:  # noqa: BLE001
            warnings.append(f"case.json unreadable: {e}")
    else:
        warnings.append("case.json not found")

    manifest_path = next((f for f in files if re.search(r"manifest", os.path.basename(f), re.I) and f.endswith(".json")), None)
    sources = parse_manifest(read_json(manifest_path)) if manifest_path else []
    if not manifest_path:
        warnings.append("no corpus manifest found; sources derived from file names")

    def src_for_file(fname):
        b = os.path.basename(fname)
        for s in sources:
            if b in s["files"]:
                return s["source_id"]
        low = b.lower()
        if sources:
            if "secondary" in low and len(sources) >= 2:
                return sources[1]["source_id"]
            if "primary" in low:
                return sources[0]["source_id"]
            return None
        for role in ("primary", "secondary"):
            if role in low:
                return role
        return None

    paras, xml_by_src, role_alias = [], defaultdict(list), {}
    for f in files:
        b = os.path.basename(f)
        ext = b.rsplit(".", 1)[-1].lower() if "." in b else ""
        if f == manifest_path or os.path.abspath(f) == os.path.abspath(case_path):
            continue
        rec = {"file": os.path.relpath(f, root), "bytes": os.path.getsize(f), "sha256": sha256_file(f)}
        seen.append(rec)
        src = src_for_file(f)
        try:
            if ext == "json":
                ps = json_paragraphs(read_json(f), src, b)
                rec["paragraphs"] = len(ps)
                rec["role"] = "summary_index" if (len({p["source_id"] for p in ps}) > 1 or re.fullmatch(r"material\.json", b)) else "source_text"
                own = {p["source_id"] for p in ps}
                if rec["role"] == "source_text" and src and len(own) == 1 and None not in own and src not in own:
                    role_alias[src] = own.pop()  # e.g. file role 'secondary' == in-file source_id 'paper-B'

                for p in ps:
                    p["role"] = rec["role"]
                paras += ps
            elif ext == "xml":
                if src is None and sources:
                    meta = xml_meta(f)
                    src = next((s["source_id"] for s in sources if s.get("doi") and meta.get("doi") and s["doi"].lower() in meta["doi"].lower()), None)
                ps, err = xml_paragraphs(f, src)
                if err:
                    warnings.append(f"{b}: {err}")
                rec["paragraphs"] = len(ps)
                rec["role"] = "publisher_xml"
                xml_by_src[src].extend(ps)
            elif ext in ("md", "txt") and b.lower() not in ("task.md", "readme.md"):
                ps = text_paragraphs(f, src)
                rec["paragraphs"], rec["role"] = len(ps), "text_fallback"
                for p in ps:
                    p["role"] = "text_fallback"
                paras += ps
            elif ext == "pdf":
                ps, err = pdf_paragraphs(f, src)
                if err:
                    warnings.append(f"{b}: {err}")
                rec["paragraphs"], rec["role"] = len(ps), "pdf"
                for p in ps:
                    p["role"] = "pdf"
                paras += ps
        except Exception as e:  # noqa: BLE001
            warnings.append(f"{b}: unreadable ({type(e).__name__}: {e})")
            rec["error"] = str(e)

    # Map unknown/alias source labels onto manifest ids (doi, doi URL, role word, 1-based index)
    ids = {s["source_id"] for s in sources}

    def canon(sid):
        sid = role_alias.get(sid, sid)
        if sid is None or sid in ids:
            return sid
        low = str(sid).lower().strip()
        for pre in ("https://doi.org/", "http://doi.org/", "doi:", "https://dx.doi.org/"):
            if low.startswith(pre):
                low = low[len(pre):]
        for i, s in enumerate(sources):
            if (s.get("doi") and low == str(s["doi"]).lower()) or low == str(s.get("role") or "").lower()                or (low in ("primary", "main", "original", "paper1", "1") and i == 0)                or (low in ("secondary", "new", "added", "paper2", "2") and i == 1):
                return s["source_id"]
        return sid
    for p in paras:
        p["source_id"] = canon(p["source_id"])
    # summary-index paragraphs without a source: recover it from per-paper files with the same text
    by_text = {}
    for p in paras:
        if p.get("role") != "summary_index" and p["source_id"] is not None:
            by_text[(p["paragraph_id"], norm_text(p["text"])[:200])] = p["source_id"]
    unresolved = 0
    for p in paras:
        if p["source_id"] is None and p.get("role") == "summary_index":
            hit = by_text.get((p["paragraph_id"], norm_text(p["text"])[:200]))
            if hit:
                p["source_id"] = hit
            elif by_text:
                p["_drop"] = True
                unresolved += 1
    if unresolved:
        warnings.append(f"{unresolved} summary-index paragraphs had no source and no twin in per-paper files; not used")
    paras = [p for p in paras if not p.get("_drop")]
    # Deduplicate: prefer per-source files over the summary index; record text conflicts
    best, conflicts = {}, []
    order = {"source_text": 0, "pdf": 1, "text_fallback": 2, "summary_index": 3}
    for p in sorted(paras, key=lambda p: order.get(p.get("role"), 9)):
        k = (p["source_id"], p["paragraph_id"])
        if k in best:
            if norm_text(best[k]["text"]) != norm_text(p["text"]):
                conflicts.append({"source_id": k[0], "paragraph_id": k[1], "kept": best[k]["origin"], "other": p["origin"]})
            best[k].setdefault("also_in", []).append(p["origin"])
            continue
        best[k] = p
    paras = list(best.values())
    # XML used as fallback for sources without JSON/text paragraphs, otherwise kept for cross-checks
    have = {p["source_id"] for p in paras}
    for src, ps in xml_by_src.items():
        src = canon(src)
        for p in ps:
            p["source_id"] = src
        if src not in have:
            paras += ps
            warnings.append(f"source {src}: paragraphs taken from publisher XML ({len(ps)})")
    write_jsonl(os.path.join(cdir, "xml_paragraphs.jsonl"), [p for ps in xml_by_src.values() for p in ps])

    if not sources:
        sids = sorted({str(p["source_id"]) for p in paras if p["source_id"] is not None})
        prim = role_alias.get("primary", "primary")
        sids.sort(key=lambda x: (x != prim, x != role_alias.get("secondary", "secondary"), x))
        for i, sid in enumerate(sids):
            rec = {"source_id": sid, "doi": None, "title": None, "authors": [], "license": None, "sha256": None, "files": [], "manifest_record": None}
            if i == 0 and (case.get("doi") or case.get("title")):
                rec.update({"doi": case.get("doi"), "title": case.get("title"), "authors": case.get("authors") or [],
                            "metadata_note": "taken from case.json root, which describes the primary paper only"})
            sources.append(rec)
    orphan = [p for p in paras if p["source_id"] in (None, "None")]
    if orphan:
        warnings.append(f"{len(orphan)} paragraphs without identifiable source; assigned to 'UNKNOWN'")
        for p in orphan:
            p["source_id"] = "UNKNOWN"

    by_src = defaultdict(list)
    for p in paras:
        by_src[p["source_id"]].append(p)
    report_sources = []
    for s in sources:
        ps = by_src.get(s["source_id"], [])
        s["paragraph_count"] = len(ps)
        s["location_kind"] = sorted({p.get("id_field") for p in ps})
        if not ps:
            warnings.append(f"source {s['source_id']} listed in manifest but no paragraphs found (material missing?)")
        safe_sid = re.sub(r'[\\/:*?"<>|]+', "_", str(s["source_id"]))
        s["corpus_file"] = f"{safe_sid}.txt"
        report_sources.append({k: s[k] for k in ("source_id", "doi", "paragraph_count", "location_kind", "corpus_file")})
        with open(os.path.join(cdir, s["corpus_file"]), "w", encoding="utf-8") as f:
            f.write(f"# {s['source_id']} | doi={s.get('doi')} | {s.get('title')}\n# authors: {'; '.join(s.get('authors') or [])}\n\n")
            for p in ps:
                f.write(f"[{p['paragraph_id']}] ({p['section'][:60]}) {p['text']}\n\n")
    cands = {}
    for sid, ps in by_src.items():
        abbr = defaultdict(lambda: {"expansions": Counter(), "paragraphs": []})
        for p in ps:
            for ab, exp in abbreviation_defs(p["text"]):
                abbr[ab]["expansions"][exp] += 1
                abbr[ab]["paragraphs"].append(p["paragraph_id"])
        cands[sid] = {"abbreviations": {k: {"expansions": dict(v["expansions"]), "paragraphs": v["paragraphs"][:5]} for k, v in abbr.items()},
                      "frequent_terms": frequent_terms(ps)}
    write_json(os.path.join(cdir, "candidates.json"), {"note": "heuristic hints, not graph content; verify in text", "sources": cands})
    write_jsonl(os.path.join(cdir, "paragraphs.jsonl"), paras)
    write_json(os.path.join(cdir, "sources.json"), sources)
    status = "ok" if paras and not any("no paragraphs" in w for w in warnings) else ("partial" if paras else "failed")
    report = {"status": status, "input_root": root, "case_id": case.get("case_id") or case.get("id"),
              "files": seen, "sources": report_sources, "paragraphs_total": len(paras),
              "duplicate_text_conflicts": conflicts, "warnings": warnings}
    write_json(os.path.join(cdir, "ingest_report.json"), report)
    print(f"ingest: status={status} sources={len(sources)} paragraphs={len(paras)} warnings={len(warnings)}")
    for s in report_sources:
        print(f"  {s['source_id']}: {s['paragraph_count']} paragraphs  doi={s['doi']}  ids={s['location_kind']}  -> {cdir}/{s.get('corpus_file', s['source_id'] + '.txt')}")
    for w in warnings:
        print("  WARN", w)
    return 0 if status != "failed" else 2


if __name__ == "__main__":
    sys.exit(main())
