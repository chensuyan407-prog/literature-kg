"""Build a local test case shaped like the challenge description from two CC-BY JATS files.

python tests/make_case.py RAW_DIR OUT_INPUT_DIR
The official case format is not public; this mimics the description (corpus-manifest.json,
material.json summary index, primary-/secondary-material.json, secondary-publisher.xml,
case.json, task.md) with two different JSON shapes and colliding paragraph ids, to test
that ingest does not assume one schema.
"""
import hashlib
import json
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET


def tag(e):
    return e.tag.split("}", 1)[-1]


def article(path):
    root = ET.parse(path).getroot()
    art = next(e for e in root.iter() if tag(e) == "article")
    meta = {"doi": None, "title": None, "authors": []}
    grp_author = False
    for e in art.iter():
        t = tag(e)
        if t == "article-id" and e.get("pub-id-type") == "doi" and not meta["doi"]:
            meta["doi"] = e.text.strip()
        if t == "article-title" and not meta["title"]:
            meta["title"] = re.sub(r"\s+", " ", "".join(e.itertext())).strip()
        if t == "contrib-group" and e.get("content-type") == "author":
            grp_author = True
        if t == "contrib" and (e.get("contrib-type") == "author" or (e.get("contrib-type") is None and grp_author)):
            sn = next((x for x in e.iter() if tag(x) == "surname"), None)
            gn = next((x for x in e.iter() if tag(x) == "given-names"), None)
            if sn is not None:
                meta["authors"].append(((gn.text or "") + " " + (sn.text or "")).strip())
        if t == "back":
            break
    secs = []

    def walk(el, path):
        for c in el:
            t = tag(c)
            if t in ("ref-list", "fn-group", "permissions", "author-notes", "table-wrap", "fig", "license"):
                continue
            if t in ("sec", "abstract"):
                title = next((x for x in c if tag(x) == "title"), None)
                name = re.sub(r"\s+", " ", "".join(title.itertext())).strip() if title is not None else t
                walk(c, path + [name])
            elif t == "p":
                txt = re.sub(r"\s+", " ", "".join(c.itertext())).strip()
                if len(txt) > 20:
                    secs.append((" > ".join(path), txt))
            else:
                walk(c, path)

    front = next(e for e in art if tag(e) == "front")
    body = next(e for e in art if tag(e) == "body")
    for e in front.iter():
        if tag(e) == "abstract":
            walk(e, ["Abstract"])
            break
    walk(body, [])
    return meta, secs


def main(raw, out):
    os.makedirs(out, exist_ok=True)
    a_meta, a_par = article(os.path.join(raw, "PMC13613405.xml"))
    b_meta, b_par = article(os.path.join(raw, "PMC13514153.xml"))
    pa = [{"source_id": "paper-A", "paragraph_id": f"p-{i + 1:04d}", "section": s, "text": t} for i, (s, t) in enumerate(a_par)]
    pb = [{"source_id": "paper-B", "paragraph_id": f"p-{i + 1:04d}", "section": s, "text": t} for i, (s, t) in enumerate(b_par)]
    # primary: nested sections, key "id"; secondary: flat list with "paragraph_id"
    prim = {"doi": a_meta["doi"], "title": a_meta["title"], "sections": []}
    for p in pa:
        if not prim["sections"] or prim["sections"][-1]["title"] != p["section"]:
            prim["sections"].append({"title": p["section"], "paragraphs": []})
        prim["sections"][-1]["paragraphs"].append({"id": p["paragraph_id"], "text": p["text"]})
    sec = {"source_id": "paper-B", "doi": b_meta["doi"], "blocks": [{"paragraph_id": p["paragraph_id"], "section_path": p["section"].split(" > "), "content": p["text"]} for p in pb]}
    files = {"primary-material.json": prim, "secondary-material.json": sec,
             "material.json": {"doi": a_meta["doi"], "title": a_meta["title"], "authors": a_meta["authors"], "paragraphs": pa + pb}}
    for name, obj in files.items():
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
    shutil.copy(os.path.join(raw, "PMC13514153.xml"), os.path.join(out, "secondary-publisher.xml"))
    h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()  # noqa: E731
    manifest = {"corpus": [
        {"source_id": "paper-A", "role": "primary", "doi": a_meta["doi"], "title": a_meta["title"], "authors": a_meta["authors"], "license": "CC-BY-4.0", "source_sha256": h(os.path.join(raw, "PMC13613405.xml")), "file": "primary-material.json"},
        {"source_id": "paper-B", "role": "secondary", "doi": b_meta["doi"], "title": b_meta["title"], "authors": b_meta["authors"], "license": "CC-BY-4.0", "source_sha256": h(os.path.join(raw, "PMC13514153.xml")), "file": "secondary-material.json", "publisher_xml": "secondary-publisher.xml"}]}
    with open(os.path.join(out, "corpus-manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    case = {"case_id": "local-go-adsorption-kg", "doi": a_meta["doi"], "title": a_meta["title"],
            "task": "Build one evidence-bound knowledge graph over both papers; run >=3 queries; record cross-paper merges and non-merges.",
            "materials": list(files) + ["corpus-manifest.json", "secondary-publisher.xml"],
            "output_contract": {"case_id": "string", "status": "success|partial|failed", "graph": "nodes and edges with source_id, paragraph_id, quote",
                                "queries": "at least 3 executed queries with results and evidence", "alignment": "cross-paper merge basis and non-merge conflicts",
                                "uncertainty": "unreported / undecidable items", "sources": "per-paper provenance"}}
    with open(os.path.join(out, "case.json"), "w", encoding="utf-8") as f:
        json.dump(case, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, "task.md"), "w", encoding="utf-8") as f:
        f.write("# Task\n\nBuild a literature knowledge graph over the two papers (graphene-oxide-based adsorbents). "
                "Keep both papers' nodes, relations and sources; every substantive node/edge cites source_id, paragraph_id and a short quote. "
                "Run at least 3 queries, e.g. (1) which adsorbates were studied with which adsorbent and what capacity was reported; "
                "(2) which isotherm/kinetic models fit each paper's data; (3) which concepts appear in both papers and whether they are the same object.\n")
    print("case written to", out, len(pa), len(pb))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
