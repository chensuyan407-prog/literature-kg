---
name: literature-kg
description: Build an evidence-bound knowledge graph from one or more scientific papers (JATS/JSON paragraphs, XML, Markdown or PDF), with every node and edge tied to source_id + paragraph_id + verbatim quote, cross-paper alias alignment that records merge basis and refused merges, conflict records, executed graph queries, and exported graph files (JSON, CSV, GraphML, Mermaid, DOT, HTML, SVG/PNG). Use for 文献知识图谱构建 / entity-relation extraction / evidence binding / graph query / incremental update tasks.
---

# literature-kg — 文献知识图谱构建 (evidence-bound)

You read the papers and extract entities, relations, cross-paper decisions, and queries. The scripts
flatten inputs into paragraphs with organiser IDs, verify every quote against its cited paragraph,
enforce the relation schema, align aliases under fixed rules, run queries, export, and self-check.
Nothing enters the graph without a verbatim quote found in the cited paragraph.

## 1. Main Pipeline Command (auto-detects `python3` and `/skills/weekly-skill`)

```bash
PY=$(command -v python3 || command -v python)
for d in /skills/weekly-skill /app/submission /app/skills /app/skills/* "${SKILL_DIR:-}" "$(pwd)"; do
  [ -f "$d/scripts/run_all.py" ] && K="$d/scripts" && break
done
W=/app/work O=/app/output

# Step A: Ingest inputs -> read /input/task.md, /input/case.json, and $W/corpus/<safe_source_id>.txt
"$PY" "$K/ingest.py" --input /input --work "$W"

# Step B: After writing $W/extract/<source_id>.json and $W/queries.json, run full pipeline:
"$PY" "$K/run_all.py" --input /input --work "$W" --out "$O"
# Incremental update: add --previous <old>/graph/graph.json to preserve node IDs and log change_log.
# Quote lookup helper: "$PY" "$K/find_text.py" --work "$W" --source <source_id> "<phrase>"
```

## 2. Workflow (≤ 64 requests / 900 s; save partial result early)

1. **Ingest**: Run Step A. Check `$W/corpus/ingest_report.json` (`sources[].corpus_file`, `location_kind`,
   `warnings`). Organiser JSON/JATS IDs (`p-0012`) are **not PDF pages**. PDF text layers give
   `p<page>-para<n>` (real pages); `.md`/`.txt` give `selfmade-mdNNN`. Root DOI/title/authors in
   `case.json` belong to the **primary** paper only.
2. **Extract**: Read each `$W/corpus/<safe_source_id>.txt` (`[paragraph_id] (section) text`). Write
   `$W/extract/<source_id>.json` (replace `/` in DOIs with `_` in filename; split long papers as
   `.part2.json`). Target ≈15–40 entities and ≈15–40 relations per paper. Write primary paper first
   and run Step B once for an early honest partial result.
3. **Cross-paper & Conflicts** (optional `$W/extract/alignment_overrides.json`):
   `{"merge": [["A","B","reason"]], "split": [["A","B","reason"]], "conflicts": [{"kind":"interpretation_conflict","about":[...],"reason":"...","evidence":[{"source_id","paragraph_id","quote"},...]}]}`.
   Never write an edge whose subject and object come from different papers.
4. **Queries** (`$W/queries.json`, ≥ 3 real questions from `task.md`):
   ops: `find NAME` · `neighbors NAME` · `path A B` · `type TYPE` · `predicate P1,P2` · `shared` · `uncertain` · `evidence ID`.
   (`shared`, `type Measurement`, `uncertain` are also added automatically).
5. **Run & Fix**: Run Step B. Fix `REJECTED` items using `find_text.py` (max 2 rounds; leave remaining
   rejected items honestly listed in `result.json`). Optional: `$W/contract_fill.json` for non-graph
   `output_contract` fields; `$W/notes.json` (`{"uncertainty":[...],"not_reported":[...]}`).

## 3. Minimal Positive Example (`$W/extract/paper-A.json`)

```json
{"source_id": "paper-A",
 "entities": [
  {"key": "MGO", "name": "magnetically modified graphene oxide composite", "type": "Sample", "aliases": ["MGO"],
   "mentions": [{"paragraph_id": "p-0001", "quote": "using a magnetically modified graphene oxide (MGO) composite"}]},
  {"key": "qmax", "name": "qmax for lactic acid", "type": "Measurement", "attributes": {"value": "334.45", "unit": "mg/g"},
   "mentions": [{"paragraph_id": "p-0055", "quote": "The maximum adsorption capacity of MGO for lactic acid (334.45 mg/g)"}]}],
 "relations": [
  {"subject": "MGO", "predicate": "HAS_RESULT", "object": "qmax", "conditions": {"T": "25 °C"},
   "paragraph_id": "p-0055", "quote": "The maximum adsorption capacity of MGO for lactic acid (334.45 mg/g)", "strength": "direct"}],
 "not_reported": [{"item": "BET surface area", "note": "not measured (p-0104)"}]}
```

## 4. 图谱构建与取证 Checklist (Core Constraints)

- **Verbatim Evidence**: Every node/edge needs `source_id` + `paragraph_id` + contiguous `quote` (12–300 chars,
  copied verbatim; keep linearised formulas like `R 2`, `m2/g`). Never invent PDF page numbers.
- **Entity Types**:
  - Concept (cross-paper mergeable on equal normalised **full name**): `Material, Method, Task, Metric, Instrument, Mechanism, Researcher`.
  - Instance (paper-scoped, never merged across papers): `Sample, Measurement, Conclusion, Dataset, Model, Condition, Paper`.
  - Authors come from manifest automatically (`Researcher -AUTHOR_OF-> Paper`). Only extract entities named in the paper.
- **Predicates (type-enforced)**: `STUDIES`, `USES`, `PREPARED_FROM`, `INSTANCE_OF`, `CHARACTERIZED_BY`,
  `TESTED_ON`, `HAS_RESULT`, `MEASURED_BY`, `UNDER_CONDITION`, `FITS`, `OUTPERFORMS`, `COMPARED_WITH`,
  `SUPPORTS`, `CONTRADICTS`, `ATTRIBUTED_TO`, `INVOLVES`, `CONCLUDES`, `PART_OF`, `APPLIED_TO`.
  Co-occurrence ≠ relation; preserve direction (`A OUTPERFORMS B`) and `conditions`.
- **Strength & Attribution**: `strength` ∈ `direct | indirect | hedged | cited`; `attribution` ∈ `author | cited`.
  Uncertain/hedged candidate relations are **retained with uncertainty flags**, never silently dropped.
- **Cross-paper Alignment**: Abbreviation alone never merges; generic words (`model`, `sample`) never merge
  (`generic_term_not_merged`); same metric in two papers keeps per-paper values (`cross_paper_values_not_combined`).
  Record `abbreviation_homonym`, `same_label_different_object`, `similar_name_review`, and `conflicts`.
- **Outputs & Failure Handling**: `result.json` aligns `case_id`, `status` (`success|partial|failed`),
  `output_contract` fields, inline `evidence`, `queries`, `alignment`, `conflicts`, `rejected`, `not_reported`,
  `uncertainty`. If `ingest` is `partial` (missing text, scanned/encrypted PDF), never fabricate content;
  mark `status: partial` and explain in `notes.json`.
