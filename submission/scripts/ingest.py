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
END_PUNCT = tuple('.!?:;。！？；)"\'”]')
HEAD_RE = re.compile(r"^(?:(?:\d{1,2}(?:\.\d{1,2})*\.?|[IVX]{1,4}\.)\s+)?(abstract|introduction|background|related work|materials?(?: and methods)?|methods?|methodology|experimental(?: section| procedures)?|results?(?: and discussion)?|discussion|conclusions?|summary|acknowledge?ments?|funding|data availability|supplementary(?: material)?|references|bibliography|摘要|引言|方法|结果|讨论|结论|参考文献)\b", re.I)
REF_HEAD_RE = re.compile(r"^(?:\d+\.?\s+)?(references|bibliography|literature cited|参考文献)\s*$", re.I)


def dehyphen(t):
    """'adsorp-\\ntion' -> 'adsorption' (line-break hyphenation only); collapse whitespace."""
    t = t.replace("­\n", "").replace("­", "")
    t = re.sub(r"([a-z]{2,})-\s*\n\s*([a-z]{2,})", r"\1\2", t)
    return re.sub(r"\s+", " ", t).strip()


def reflow_lines(block):
    """Split a hard-wrapped or one-line-per-paragraph text into paragraphs."""
    lines = [ln.rstrip() for ln in block.split("\n") if ln.strip()]
    if not lines:
        return []
    avg = sum(len(ln) for ln in lines) / len(lines)
    if avg > 160:  # one paragraph per line
        return [ln.strip() for ln in lines]
    paras, cur = [], []
    for i, ln in enumerate(lines):
        cur.append(ln)
        nxt = lines[i + 1].lstrip() if i + 1 < len(lines) else ""
        short = len(ln.strip()) < 0.85 * avg
        if not nxt or (ln.rstrip().endswith((".", "!", "?", "。", "！", "？")) and nxt[:1].isupper()) or (short and ln.rstrip().endswith(END_PUNCT) and nxt[:1].isupper()):
            paras.append("\n".join(cur))
            cur = []
    return paras


def text_paragraphs(path, src):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        raw = f.read().replace("\r\n", "\n")
    out, sec = [], ""
    blocks = re.split(r"\n\s*\n", raw)
    if len(blocks) <= 3 and raw.count("\n") > 20:  # plain .txt without blank lines between paragraphs
        blocks = reflow_lines(raw)
    for i, block in enumerate(blocks):
        b = block.strip()
        m = re.match(r"^#+\s+(.*)", b)
        if m and "\n" not in b:
            sec = m.group(1).strip()
            continue
        if len(b) < 80 and "\n" not in b and not b.endswith((".", "。")) and HEAD_RE.match(b):
            sec = b
            continue
        mid = re.match(r"^\[([A-Za-z0-9_.:-]+)\]\s*(.*)", b, re.S)
        if len(b) < 15:
            continue
        out.append({"source_id": src, "paragraph_id": mid.group(1) if mid else f"selfmade-md{i:03d}",
                    "section": sec, "text": dehyphen((mid.group(2) if mid else b).strip()),
                    "origin": os.path.basename(path), "id_field": "inline" if mid else "generated"})
    return out


# ------------------------------------------------------------------ PDF ---
def _column_order(blocks, width):
    """Reading order for 1- or 2-column pages. blocks: (x0, y0, x1, y1, text)."""
    mid = width / 2.0
    left = lambda b: b[2] <= mid + 0.03 * width  # noqa: E731
    right = lambda b: b[0] >= mid - 0.03 * width  # noqa: E731
    two_col = sum(1 for b in blocks if left(b)) >= 2 and sum(1 for b in blocks if right(b)) >= 2
    if not two_col:
        return sorted(blocks, key=lambda b: (round(b[1]), b[0]))
    out, seg = [], []
    for b in sorted(blocks, key=lambda b: (b[1], b[0])):
        if not left(b) and not right(b):  # full-width block (title, wide caption) closes the band above it
            out += sorted(seg, key=lambda b: (right(b), b[1]))
            out.append(b)
            seg = []
        else:
            seg.append(b)
    return out + sorted(seg, key=lambda b: (right(b), b[1]))


def _pdf_pages_pymupdf(path):
    try:
        import pymupdf as fitz  # PyMuPDF >= 1.24
    except ImportError:
        import fitz  # PyMuPDF
    doc = fitz.open(path)
    if doc.needs_pass:
        raise PermissionError("PDF is encrypted")
    pages = []
    for page in doc:
        bl = [tuple(b[:5]) for b in page.get_text("blocks") if (len(b) < 7 or b[6] == 0) and b[4].strip()]
        pages.append({"blocks": _column_order(bl, page.rect.width), "images": len(page.get_images(full=False))})
    return pages, "pymupdf"


def _pdf_pages_pdftotext(path):
    """poppler pdftotext -bbox-layout: blocks with coordinates -> same column-aware ordering as PyMuPDF."""
    import shutil
    import subprocess
    exe = shutil.which("pdftotext")
    if not exe:
        raise RuntimeError("pdftotext not available")
    p = subprocess.run([exe, "-q", "-enc", "UTF-8", "-bbox-layout", path, "-"], capture_output=True, timeout=180)
    if p.returncode != 0:
        msg = p.stderr.decode("utf-8", "replace")
        if re.search(r"Incorrect password", msg, re.I):
            raise PermissionError("PDF is encrypted")
        raise RuntimeError(msg[:200] or "pdftotext failed")
    root = ET.fromstring(p.stdout.decode("utf-8", "replace"))
    pages = []
    for pg in root.iter():
        if strip_ns(pg.tag) != "page":
            continue
        blocks = []
        for bl in pg.iter():
            if strip_ns(bl.tag) != "block":
                continue
            lines = [" ".join((w.text or "") for w in ln if strip_ns(w.tag) == "word") for ln in bl if strip_ns(ln.tag) == "line"]
            txt = "\n".join(x for x in lines if x.strip())
            if txt.strip():
                blocks.append((float(bl.get("xMin", 0)), float(bl.get("yMin", 0)), float(bl.get("xMax", 0)), float(bl.get("yMax", 0)), txt))
        pages.append({"blocks": _column_order(blocks, float(pg.get("width") or 600)), "images": None})
    return pages, "pdftotext"


def _pdf_pages_pypdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader  # type: ignore
    r = PdfReader(path)
    if r.is_encrypted:
        raise PermissionError("PDF is encrypted")
    pages = []
    for pg in r.pages:
        t = pg.extract_text() or ""
        pages.append({"blocks": [(0, i, 0, i, bk) for i, bk in enumerate(reflow_lines(t))], "images": None})
    return pages, "pypdf"


def pdf_paragraphs(path, src):
    """Text-layer PDF -> paragraphs with REAL page numbers: id 'p<page>-para<n>' (n = reading order on that page).
    Tries PyMuPDF (column-aware block order), then pdftotext, then pypdf. Returns (paragraphs, error, info).
    No OCR: pages without a text layer are listed, never guessed."""
    pages, tool, errs = None, None, []
    for fn in (_pdf_pages_pymupdf, _pdf_pages_pdftotext, _pdf_pages_pypdf):
        try:
            pg_try, tool_try = fn(path)
        except PermissionError as e:
            return [], str(e), {"extractor": None, "tried": errs}
        except Exception as e:  # noqa: BLE001
            errs.append(f"{fn.__name__[11:]}: {type(e).__name__}: {str(e)[:120]}")
            continue
        if any(len(b[4].strip()) >= 8 for pg in pg_try for b in pg["blocks"]):
            pages, tool = pg_try, tool_try
            break
        errs.append(f"{tool_try}: no text layer")
        pages = pages or pg_try
    info = {"extractor": tool, "pages_total": len(pages or []), "pages_without_text": [], "tried": errs}
    if not pages or not tool:
        if pages:
            info["pages_without_text"] = list(range(1, len(pages) + 1))
        return [], "PDF has no usable text layer (scanned/image-only?); OCR is not performed" if pages else "PDF cannot be parsed (" + "; ".join(errs) + ")", info
    # running headers / footers: same short line (digits masked) at top/bottom of >= 40% of pages
    edge = Counter()
    for pg in pages:
        texts = [re.sub(r"\d+", "#", re.sub(r"\s+", " ", b[4]).strip()) for b in pg["blocks"]]
        for t in set(texts[:2] + texts[-2:]):
            if len(t) < 120:
                edge[t] += 1
    rep = {t for t, k in edge.items() if len(pages) >= 3 and k >= max(2, 0.4 * len(pages))}
    out, sec, in_refs, dropped = [], "", False, 0
    for pno, pg in enumerate(pages, 1):
        if sum(len(b[4].strip()) for b in pg["blocks"]) < 20:
            info["pages_without_text"].append(pno)
            continue
        k = 0
        for b in pg["blocks"]:
            t = dehyphen(b[4])
            if not t or re.sub(r"\d+", "#", t) in rep or re.fullmatch(r"(page\s*)?\d{1,4}(\s*(of|/)\s*\d{1,4})?", t, re.I):
                continue
            if REF_HEAD_RE.match(t):
                in_refs, sec = True, t
                continue
            if len(t) < 90 and not t.endswith((".", "。")) and HEAD_RE.match(t):
                sec, in_refs = t, False
                continue
            if in_refs:
                if re.match(r"^(?:appendix|supplementary)\b", t, re.I):
                    in_refs, sec = False, t
                else:
                    dropped += 1
                    continue
            # paragraph split by a column or page break: join when the previous block is unfinished
            if out and not out[-1]["text"].endswith(END_PUNCT) and t[:1].islower():
                out[-1]["text"] += " " + t
                if pno != out[-1]["page"] and pno not in out[-1].setdefault("continues_on_pages", []):
                    out[-1]["continues_on_pages"].append(pno)
                continue
            if len(t) < 12 and not re.search(r"\d", t):
                continue
            k += 1
            out.append({"source_id": src, "paragraph_id": f"p{pno}-para{k}", "section": sec or f"PDF page {pno}", "page": pno,
                        "text": t, "origin": os.path.basename(path), "id_field": "pdf_text_layer", "extractor": tool})
    info["reference_blocks_skipped"] = dropped
    if not out:
        return [], "PDF has no usable text layer (scanned/image-only?); OCR is not performed", info
    return out, None, info


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
    a = ap.parse_known_args()[0]
    root, files = find_files(a.input)
    cdir = os.path.join(a.work, "corpus")
    os.makedirs(cdir, exist_ok=True)
    warnings, seen, degraded = [], [], []
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
    sources = []
    if manifest_path:
        try:
            sources = parse_manifest(read_json(manifest_path))
        except Exception as e:  # noqa: BLE001
            report = {"status": "failed", "input_root": root, "case_id": case.get("case_id") or case.get("id"),
                      "files": seen, "sources": [], "paragraphs_total": 0, "duplicate_text_conflicts": [],
                      "warnings": [f"invalid manifest {os.path.basename(manifest_path)}: {type(e).__name__}: {e}"],
                      "partial_reasons": [f"invalid manifest: {e}"]}
            write_json(os.path.join(cdir, "ingest_report.json"), report)
            print(f"ingest: status=failed invalid manifest: {e}")
            return 2
    if not manifest_path:
        warnings.append("no corpus manifest found; sources derived from file names")

    mat_roles = {}
    for m in (case.get("materials") or []):
        if isinstance(m, dict):
            mp = m.get("path") or m.get("file") or m.get("name")
            mr = str(m.get("role") or "").lower().strip()
            if mp and mr:
                mat_roles[os.path.basename(str(mp)).lower()] = mr

    def doi_slug(x):
        return re.sub(r"[^a-z0-9]+", "", str(x or "").lower())

    def src_for_file(fname):
        b = os.path.basename(fname)
        low = b.lower()
        explicit_role = mat_roles.get(low)
        if explicit_role in ("supplement", "supplementary", "appendix", "glossary"):
            return "__supplement__"
        for s in sources:
            if b in s["files"]:
                return s["source_id"]
        stem = doi_slug(b.rsplit(".", 1)[0])
        for s in sources:  # e.g. '10.1371_journal.pone.0123.pdf' or 'paper-B.pdf'
            if (s.get("doi") and len(doi_slug(s["doi"])) > 6 and doi_slug(s["doi"]) in stem) or (stem and stem == doi_slug(s["source_id"])):
                return s["source_id"]
        if not explicit_role and re.search(r"(supplement|glossary|appendix)", low) and not re.search(r"(primary|secondary)", low):
            return "__supplement__"
        if sources:
            want_role = explicit_role or ("secondary" if "secondary" in low else ("primary" if "primary" in low else None))
            if want_role:
                hit = next((s["source_id"] for s in sources if str(s.get("role") or "").lower() == want_role), None)
                if hit:
                    return hit
                if want_role == "secondary" and len(sources) >= 2:
                    return sources[1]["source_id"]
                if want_role == "primary":
                    return sources[0]["source_id"]
            return None
        if explicit_role in ("primary", "secondary"):
            return explicit_role
        for role in ("primary", "secondary"):
            if role in low:
                return role
        return None

    paras, xml_by_src, pdf_by_src, role_alias = [], defaultdict(list), defaultdict(list), {}
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
            elif ext in ("md", "txt") and b.lower() not in ("task.md", "readme.md") and not re.match(r"(license|licence|attribution|notice)", b, re.I):
                ps = text_paragraphs(f, src)
                rec["location_kind"] = "text_block"
                rec["paragraphs"], rec["role"] = len(ps), "text_fallback"
                for p in ps:
                    p["role"] = "text_fallback"
                paras += ps
            elif ext == "pdf":
                ps, err, info = pdf_paragraphs(f, src)
                if err:
                    warnings.append(f"{b}: {err}")
                    degraded.append(f"{b}: {err}")
                if info.get("pages_without_text"):
                    degraded.append(f"{b}: pages without text layer {info['pages_without_text'][:30]}")
                    warnings.append(f"{b}: {len(info['pages_without_text'])}/{info['pages_total']} page(s) without text layer "
                                    f"(scanned/image-only, not OCRed): pages {info['pages_without_text'][:30]}")
                rec.update({"paragraphs": len(ps), "role": "pdf", "location_kind": "pdf_text_layer", "pdf": info})
                for p in ps:
                    p["role"] = "pdf"
                pdf_by_src[src].extend(ps)
        except Exception as e:  # noqa: BLE001
            warnings.append(f"{b}: unreadable ({type(e).__name__}: {e})")
            rec["error"] = str(e)

    # standalone papers (PDF / .md / .txt) whose source is unknown: one source per file (stem), never one 'UNKNOWN' blob
    if not sources:
        for p in paras + [q for ps in pdf_by_src.values() for q in ps]:
            if p["source_id"] is None and p.get("role") in ("pdf", "text_fallback"):
                p["source_id"] = re.sub(r"[^A-Za-z0-9._-]+", "_", p["origin"].rsplit(".", 1)[0])[:60]
        for key in [k for k in pdf_by_src if k is None]:
            for q in pdf_by_src.pop(key):
                pdf_by_src[q["source_id"]].append(q)
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
            have.add(src)
            warnings.append(f"source {src}: paragraphs taken from publisher XML ({len(ps)})")
    # unmapped PDF files when a manifest exists: give them to manifest sources that still have no text (file order)
    if sources and pdf_by_src.get(None):
        empty = [x["source_id"] for x in sources if x["source_id"] not in have]
        by_file = defaultdict(list)
        for q in pdf_by_src.pop(None):
            by_file[q["origin"]].append(q)
        for fn, qs in sorted(by_file.items()):
            tgt = empty.pop(0) if empty else None
            warnings.append(f"{fn}: not named in manifest; " + (f"assigned to source {tgt} (first manifest source still without text) - verify" if tgt else "no source left; paragraphs kept as UNKNOWN"))
            for q in qs:
                q["source_id"] = tgt
            pdf_by_src[tgt].extend(qs)
    # PDF text layer: used for sources without JSON/text/XML paragraphs (otherwise a second copy of the same paper)
    for src, ps in pdf_by_src.items():
        src = canon(src)
        for p in ps:
            p["source_id"] = src
        if src in have and src is not None:
            warnings.append(f"source {src}: PDF text layer ({len(ps)} blocks) not used, organiser paragraphs exist; kept in pdf_paragraphs.jsonl")
        else:
            paras += ps
            have.add(src)
            if ps:
                warnings.append(f"source {src}: paragraphs taken from the PDF text layer ({len(ps)}); ids p<page>-para<n> = real PDF page + reading-order block, generated by ingest")
    write_jsonl(os.path.join(cdir, "pdf_paragraphs.jsonl"), [p for ps in pdf_by_src.values() for p in ps])
    write_jsonl(os.path.join(cdir, "xml_paragraphs.jsonl"), [p for ps in xml_by_src.values() for p in ps])

    if not sources:
        sids = sorted({str(p["source_id"]) for p in paras if p["source_id"] is not None})
        prim = next((k for k, v in mat_roles.items() if v == "primary"), None)
        prim_sid = role_alias.get("primary", "primary")
        sids.sort(key=lambda x: (x == "__supplement__", x != prim_sid, x != role_alias.get("secondary", "secondary"), x))
        for i, sid in enumerate(sids):
            rec = {"source_id": sid, "doi": None, "title": None, "authors": [], "license": None, "sha256": None, "files": [], "manifest_record": None}
            if sid == "__supplement__":
                rec["role"] = "supplement"
            elif i == 0 and (case.get("doi") or case.get("title")):
                rec.update({"doi": case.get("doi"), "title": case.get("title"), "authors": case.get("authors") or [],
                            "metadata_note": "taken from case.json root, which describes the primary paper only"})
            sources.append(rec)
    orphan = [p for p in paras if p["source_id"] in (None, "None")]
    if orphan:
        warnings.append(f"{len(orphan)} paragraphs without identifiable source; assigned to 'UNKNOWN'")
        for p in orphan:
            p["source_id"] = "UNKNOWN"

    status = "ok" if paras and not degraded and not any("no paragraphs" in w for w in warnings) else ("partial" if paras else "failed")
    if status == "failed":
        report = {"status": "failed", "input_root": root, "case_id": case.get("case_id") or case.get("id"),
                  "files": seen, "sources": [], "paragraphs_total": 0,
                  "duplicate_text_conflicts": conflicts, "warnings": warnings,
                  "partial_reasons": degraded + [w for w in warnings if "no paragraphs" in w],
                  "location_note": "no paragraphs extracted; existing corpus files (if any) were preserved"}
        write_json(os.path.join(cdir, "ingest_report.json"), report)
        print(f"ingest: status=failed sources={len(sources)} paragraphs=0 warnings={len(warnings)}")
        for w in warnings:
            print("  WARN", w)
        return 2
    by_src = defaultdict(list)
    for p in paras:
        by_src[p["source_id"]].append(p)
    report_sources = []
    for s in sources:
        ps = by_src.get(s["source_id"], [])
        s["paragraph_count"] = len(ps)
        s["location_kind"] = sorted({str(p.get("id_field")) for p in ps})
        pages = sorted({p["page"] for p in ps if p.get("page")})
        if pages:
            s["pdf_pages_with_text"] = [pages[0], pages[-1]]
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
    status = "ok" if paras and not degraded and not any("no paragraphs" in w for w in warnings) else ("partial" if paras else "failed")
    cid = case["case_id"] if ("case_id" in case and case["case_id"] is not None) else case.get("id")
    report = {"status": status, "input_root": root, "case_id": cid,
              "files": seen, "sources": report_sources, "paragraphs_total": len(paras),
              "duplicate_text_conflicts": conflicts, "warnings": warnings,
              "partial_reasons": degraded + [w for w in warnings if "no paragraphs" in w],
              "location_note": "pdf_text_layer ids p<page>-para<n>: real PDF page + reading-order block made by ingest; organiser ids (JATS/JSON) are not pages"}
    write_json(os.path.join(cdir, "ingest_report.json"), report)
    print(f"ingest: status={status} sources={len(sources)} paragraphs={len(paras)} warnings={len(warnings)}")
    for s in report_sources:
        print(f"  {s['source_id']}: {s['paragraph_count']} paragraphs  doi={s['doi']}  ids={s['location_kind']}  -> {cdir}/{s.get('corpus_file', s['source_id'] + '.txt')}")
    for w in warnings:
        print("  WARN", w)
    return 0 if status != "failed" else 2


if __name__ == "__main__":
    sys.exit(main())
