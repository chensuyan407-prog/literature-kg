---
name: literature-kg
description: Build an evidence-bound knowledge graph from one or more scientific papers (JATS/JSON paragraphs, XML, Markdown or PDF), with every node and edge tied to source_id + paragraph_id + verbatim quote, cross-paper alias alignment that records merge basis and refused merges, conflict records, executed graph queries, and exported graph files (JSON, CSV, GraphML, Mermaid, DOT, HTML, SVG/PNG). Use for 文献知识图谱构建 / entity-relation extraction / evidence binding / graph query / incremental update tasks.
---

# literature-kg — 文献知识图谱构建 (evidence-bound)

You read the papers and extract entities, relations, cross-paper decisions, and queries. The scripts
flatten inputs into paragraphs with organiser IDs, verify every quote against its cited paragraph,
enforce the relation schema, align aliases under fixed rules, run queries, export, and self-check.
Nothing enters the graph without a verbatim quote found in the cited paragraph.

## 1. Main Pipeline Commands (cross-shell single-line `python`)

Use `python` (or `python3` if `python` is absent) with the skill scripts directory (`/skills/weekly-skill/scripts`, `/app/submission/scripts`, or `submission/scripts`):

- **Step A (Ingest)**:
  `python /skills/weekly-skill/scripts/ingest.py --input /input --work /app/work`
- **Step B (Incremental chunked extract via `kg_add.py`, recommended to save tokens)**:
  `python /skills/weekly-skill/scripts/kg_add.py --work /app/work --source <source_id> --data @/app/work/chunk.json`
- **Step C (Full pipeline: build + query + export + check)**:
  `python /skills/weekly-skill/scripts/run_all.py --input /input --work /app/work --out /app/output`
- **Incremental update**: add `--previous <old>/graph/graph.json` to `run_all.py`.
- **Quote lookup helper**:
  `python /skills/weekly-skill/scripts/find_text.py --work /app/work --source <source_id> "<phrase>"`

## 2. Workflow & Chunking Rules (CRITICAL: keep every reply < 6k tokens)

1. **Ingest**: Run Step A. Check `/app/work/corpus/ingest_report.json` (`sources[].corpus_file`, `location_kind`, `warnings`). Organiser JSON/JATS IDs (`p-0012`) are **not PDF pages**. PDF text layers give `p<page>-para<n>` (real pages); `.md`/`.txt` give `selfmade-mdNNN`. Root DOI/title/authors in `case.json` belong to the **primary** paper only.
2. **Chunked Extract (MANDATORY: `<=12` entities + `<=12` relations per call, `<6k` tokens per reply)**:
   - Read `/app/work/corpus/<safe_source_id>.txt` (`[paragraph_id] (section) text`).
   - **Never** output a huge JSON file in one turn. Write small chunks (`<=12` entities + `<=12` relations) using `kg_add.py` (pass `paragraph_id` + `anchor` = first ~6 words of the sentence; `kg_add.py` expands `anchor` into a verbatim `quote` from `work/corpus/`).
   - For large papers (>30 entities/relations), split into `.part1.json`, `.part2.json`, etc. via `--out /app/work/extract/<safe_source_id>.part2.json`.
   - Write primary paper first and run Step C once for an early honest partial result.
3. **Cross-paper & Conflicts** (optional `/app/work/extract/alignment_overrides.json`):
   `{"merge": [["A","B","reason"]], "split": [["A","B","reason"]], "conflicts": [{"kind":"interpretation_conflict","about":[...],"reason":"...","evidence":[{"source_id","paragraph_id","quote"},...]}]}`.
   Never write an edge whose subject and object come from different papers.
4. **Queries** (`/app/work/queries.json`, `>= 3` real questions from `task.md`):
   ops: `find NAME` · `neighbors NAME` · `path A B` · `type TYPE` · `predicate P1,P2` · `shared` · `uncertain` · `evidence ID`.
   (`shared`, `type Measurement`, `uncertain` are also added automatically).
5. **Run & Fix**: Run Step C. Fix `REJECTED` items using `find_text.py` (max 2 rounds; leave remaining rejected items honestly listed in `result.json`). Optional: `/app/work/contract_fill.json` for non-graph `output_contract` fields; `/app/work/notes.json` (`{"uncertainty":[...],"not_reported":[...]}`).

## 3. Extract Schema & Minimal Example

### Entity & Relation Fields
- **Entity**: `key` (short id), `name` (full name), `type` (see below), `aliases` (list), `attributes` (dict, e.g. `{"value": "334.45", "unit": "mg/g"}`), `mentions` (`[{"paragraph_id": "...", "anchor": "first 6 words..."}]` or `"quote": "verbatim 12-300 chars"`).
- **Relation**: `subject` (key/name), `predicate` (see table), `object` (key/name), `paragraph_id`, `anchor` (or `quote`), `conditions` (dict, optional), `strength` (`direct|indirect|hedged|cited`), `attribution` (`author|cited`).

```json
{"source_id": "paper-A",
 "entities": [
  {"key": "MGO", "name": "magnetically modified graphene oxide composite", "type": "Sample", "aliases": ["MGO"],
   "mentions": [{"paragraph_id": "p-0001", "anchor": "using a magnetically modified graphene oxide"}]},
  {"key": "qmax", "name": "qmax for lactic acid", "type": "Measurement", "attributes": {"value": "334.45", "unit": "mg/g"},
   "mentions": [{"paragraph_id": "p-0055", "anchor": "The maximum adsorption capacity of MGO"}]}],
 "relations": [
  {"subject": "MGO", "predicate": "HAS_RESULT", "object": "qmax", "conditions": {"T": "25 °C"},
   "paragraph_id": "p-0055", "anchor": "The maximum adsorption capacity of MGO", "strength": "direct"}],
 "not_reported": [{"item": "BET surface area", "note": "not measured (p-0104)"}]}
```

## 4. Entity Types & Predicate Constraints (Self-Contained Reference)

- **Concept Types** (cross-paper mergeable on equal normalised **full name**): `Material, Method, Task, Metric, Instrument, Mechanism, Researcher`.
- **Instance Types** (paper-scoped, never merged across papers): `Sample, Measurement, Conclusion, Dataset, Model, Condition, Paper`.
- Authors come from manifest automatically (`Researcher -AUTHOR_OF-> Paper`). Only extract entities named in the paper.

| Predicate | Allowed Subject Types | Allowed Object Types | Meaning |
| :--- | :--- | :--- | :--- |
| `AUTHOR_OF` | `Researcher` | `Paper` | researcher wrote paper |
| `STUDIES` | `Paper, Method, Sample, Model` | `Task, Material` | addresses task / studies material |
| `USES` | `Paper, Method, Sample, Model, Task, Measurement` | `Method, Material, Dataset, Instrument, Model, Metric` | uses method/material/dataset/instrument |
| `PREPARED_FROM` | `Sample, Material` | `Material, Sample` | made from / modified with |
| `INSTANCE_OF` | `Sample, Model, Dataset` | `Material, Method, Dataset` | paper-specific instance of concept |
| `CHARACTERIZED_BY` | `Sample, Material, Model` | `Method, Instrument` | characterised / analysed with |
| `HAS_RESULT` | `Sample, Material, Method, Model, Paper` | `Measurement` | reported value / observation |
| `MEASURED_BY` | `Measurement` | `Metric, Method, Instrument` | quantity / method of value |
| `UNDER_CONDITION` | `Measurement, Conclusion, Sample` | `Condition` | holds under this condition |
| `FITS` | `Method, Model` | `Measurement, Sample` | model describes the data |
| `OUTPERFORMS` | `ANY - {Researcher, Paper}` | `ANY - {Researcher, Paper}` | subject better than object |
| `COMPARED_WITH` | `ANY - {Researcher}` | `ANY - {Researcher}` | explicit comparison without winner |
| `SUPPORTS` | `Measurement, Conclusion, Method, Sample` | `Conclusion` | evidence supports claim |
| `CONTRADICTS` | `Measurement, Conclusion` | `Conclusion, Measurement` | evidence contradicts claim |
| `CONCLUDES` | `Paper` | `Conclusion` | paper states this conclusion |
| `PART_OF` | `ANY` | `ANY` | component / sub-step of |
| `TESTED_ON` | `Sample, Material, Method, Model` | `Material, Sample, Dataset, Task` | tested with target/dataset/task |
| `ATTRIBUTED_TO` | `Measurement, Conclusion, Sample` | `Mechanism, Conclusion, Material, Metric` | explained by mechanism / cause |
| `INVOLVES` | `Sample, Material, Method, Conclusion` | `Mechanism` | process involves mechanism |
| `APPLIED_TO` | `Method, Material, Sample, Model` | `Task, Material, Sample, Dataset` | applied to target / task |

### Common `REJECTED` Reasons
- `quote_not_found` / `quote_absent`: `quote` not found verbatim in `paragraph_id` (use `kg_add.py` with `anchor` or `find_text.py`).
- `bad_predicate` / `type_mismatch`: subject or object entity type violates the predicate table above.
- `missing_entity`: `subject` or `object` key/name not declared in `entities`.
- `cross_paper_edge`: subject and object belong to different `source_id`s (forbidden).
- `entity_not_mentioned`: quote does not mention the subject/object name or alias.

## 5. Outputs & Failure Handling

- `result.json` aligns `case_id`, `status` (`success|partial|failed`), `status_reason`, `output_contract` fields, inline `graph.nodes` / `graph.edges`, `queries`, `alignment`, `conflicts`, `rejected`, `not_reported`, `uncertainty`.
- If `ingest` is `partial` (missing text, scanned/encrypted PDF), never fabricate content; mark `status: partial` and explain in `notes.json`.
