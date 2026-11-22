---
name: literature-kg
description: Build an evidence-bound knowledge graph from one or more scientific papers (JATS/JSON paragraphs, XML, Markdown or PDF), with every node and edge tied to source_id + paragraph_id + verbatim quote, cross-paper alias alignment that records merge basis and refused merges, conflict records, executed graph queries, and exported graph files (JSON, CSV, GraphML, Mermaid, DOT, HTML, SVG/PNG). Use for 文献知识图谱构建 / entity-relation extraction / evidence binding / graph query / incremental update tasks.
---

# literature-kg — 文献知识图谱构建 (evidence-bound)

You (the agent) read the papers and decide what the entities and relations are. The scripts do
everything that must be exact: flatten the material into paragraphs with their organiser IDs,
verify every quote against the cited paragraph, enforce the relation schema, align aliases
within and across papers under fixed rules, keep stable IDs, run queries, export, and self-check.
Nothing enters the graph without a quote that is found in the cited paragraph.

Scripts are in `scripts/` next to this file (installed: `/skills/weekly-skill/scripts`). Python ≥3.9,
standard library only; matplotlib optional (PNG previews), PyMuPDF optional (PDF input).
Below, `K=/skills/weekly-skill/scripts`, `W=/app/work`, `O=/app/output`.

## Workflow (≈10–20 tool calls; save a partial result early)

1. **Ingest** — `python $K/ingest.py --input /input --work $W`
   Prints sources (manifest DOI/authors/license/hash), paragraph counts and warnings. Also read
   `/input/task.md` and `/input/case.json` (note `case_id` and `output_contract`).
   Paper text for reading: `$W/corpus/<source_id>.txt`, one line per paragraph: `[paragraph_id] (section) text`.
   Hints (abbreviation definitions, frequent terms): `$W/corpus/candidates.json`.
   The root DOI/title/authors of case.json belong to the FIRST (primary) paper only.
2. **Read each paper** (read the .txt in chunks if long). Focus on what the task asks.
3. **Write one extraction file per paper**: `$W/extract/<source_id>.json` (schema below). If it is
   long, split into `<source_id>.part2.json` etc. (same `source_id`; keys may refer across parts).
   Write the primary paper first, then immediately run step 6 once → an honest partial result exists.
4. **Cross-paper decisions** (optional file `$W/extract/alignment_overrides.json`):
   `{"merge": [["name in A", "name in B", "reason"]], "split": [["name", "name", "reason"]],
     "conflicts": [{"kind": "interpretation_conflict", "about": [...], "reason": "...",
                    "evidence": [{"source_id","paragraph_id","quote"}, {...}]}]}`
   Use `conflicts` when two papers (or two paragraphs of one paper) disagree; each needs ≥2 verified quotes.
   Never write an edge whose subject comes from one paper and object from another.
5. **Queries** — `$W/queries.json`: at least 3 real questions from task.md, e.g.
   `[{"id":"q1","question":"...","op":"predicate","args":["HAS_RESULT,TESTED_ON"]},
     {"id":"q2","question":"...","op":"neighbors","args":["<name or alias>"],"depth":2,"predicate":null,"source":null},
     {"id":"q3","question":"...","op":"path","args":["<A>","<B>"]}]`
   ops: `find NAME` · `neighbors NAME` · `path A B` · `type TYPE` · `predicate P1,P2` · `shared` · `uncertain` · `evidence ID`.
   `shared`, `type Measurement` and `uncertain` are added automatically. A query with no result is
   reported as `no_result` with the reason — keep it, it is a valid answer ("not reported").
6. **Build + query + export + result** — `python $K/run_all.py --input /input --work $W --out $O`
   It prints `REJECTED ...` lines (quote not found, unknown key, predicate/type violation) and
   `needs_review` flags. Fix rejected items (use `python $K/find_text.py --work $W --source S "phrase"`
   to copy the exact sentence) and rerun. Two fix rounds are enough; leave the rest rejected — they
   are listed in result.json, which is honest.
7. Optional: `$W/contract_fill.json` = values for output_contract fields that are not graph data
   (e.g. a textual answer); `$W/notes.json` = `{"uncertainty": [...], "not_reported": [...]}`. Rerun step 6.
8. Final message: status, counts, where the files are, the queries' answers in 3–6 lines, open issues.

Incremental update (new paper later): ingest again with the new material, add its extraction file,
then `run_all.py ... --previous <old>/graph/graph.json` → old node IDs are kept; `change_log` lists
`node_added`, `node_extended` (existing concept gets a new paper), `edge_added`, `node_missing_in_rebuild`.

## Extraction file schema (`$W/extract/<source_id>.json`)

```json
{"source_id": "<exactly as printed by ingest>",
 "entities": [
  {"key": "MGO", "name": "magnetically modified graphene oxide composite", "type": "Sample",
   "aliases": ["MGO", "MGO composite"], "attributes": {}, "definition": null, "attribution": "author",
   "mentions": [{"paragraph_id": "p-0001", "quote": "using a magnetically modified graphene oxide (MGO) composite"}]}],
 "relations": [
  {"subject": "MGO", "predicate": "HAS_RESULT", "object": "m_qmax_LA",
   "conditions": {"adsorbate": "lactic acid", "T": "25 °C"},
   "paragraph_id": "p-0055", "quote": "The maximum adsorption capacity of MGO for lactic acid (334.45 mg/g)",
   "strength": "direct", "attribution": "author", "polarity": "positive", "note": null}],
 "not_reported": [{"item": "BET surface area of the composite", "note": "not measured (p-0104)"}]}
```

- `key`: your local handle; relations refer to keys (names/aliases also work). Use `"paper"` as
  subject for the paper itself (STUDIES / CONCLUDES).
- `quote`: copied **verbatim** from that paragraph line (12–300 characters, one contiguous span; do
  not join sentences, do not fix typos or formula linearisation like `R 2`, `m2/g`, `10–6`).
  Several evidence items: `"evidence": [{"paragraph_id","quote"}, ...]` instead of paragraph_id/quote.
- `paragraph_id` is the organiser's ID printed in brackets; it is not a PDF page — never call it a page.
- Only entities that are **named in the paper**. Do not add textbook concepts the paper does not mention.
- Measurements: one node per reported value (or small set of values reported together) with
  `attributes: {"value": "334.45", "unit": "mg/g"}`; the value digits must appear in a quote. Put
  experimental conditions in `conditions` or a `Condition` node — never drop them.
- `strength`: `direct` (stated as a result by the authors), `indirect` (inferred from the paragraph,
  e.g. implied subject), `hedged` (may/suggest/likely/probably), `cited` (claim of other work).
  `attribution`: `author` or `cited` (statement supported by a reference like [12] or "X et al. reported").
  The builder downgrades `direct` → `hedged` when the quote contains hedging words and flags citation cues.

**Entity types** — concept (may be shared across papers): `Material, Method, Task, Metric, Instrument,
Mechanism, Researcher`; instance (always paper-scoped): `Sample, Measurement, Conclusion, Dataset,
Model, Condition, Paper`. A specific synthesised sample / trained model / dataset split / reported value
is an instance even if its label equals one in the other paper. Authors come from the manifest
automatically (`Researcher -AUTHOR_OF-> Paper`); do not re-extract them.

**Predicates** (subject → object types are enforced; violations are rejected):
`STUDIES` (Paper/Method/Sample/Model→Task/Material) · `USES` (…→Method/Material/Dataset/Instrument/Model/Metric) ·
`PREPARED_FROM` (Sample/Material→Material/Sample) · `INSTANCE_OF` (Sample/Model/Dataset→Material/Method/Dataset) ·
`CHARACTERIZED_BY` (Sample/Material/Model→Method/Instrument) · `TESTED_ON` (Sample/Material/Method/Model→Material/Sample/Dataset/Task) ·
`HAS_RESULT` (Sample/Material/Method/Model/Paper→Measurement) · `MEASURED_BY` (Measurement→Metric/Method/Instrument) ·
`UNDER_CONDITION` (Measurement/Conclusion/Sample→Condition) · `FITS` (Method/Model→Measurement/Sample) ·
`OUTPERFORMS` / `COMPARED_WITH` (same-kind objects; put the criterion and range in `conditions`) ·
`SUPPORTS` / `CONTRADICTS` (Measurement/Conclusion/Method/Sample→Conclusion) · `ATTRIBUTED_TO` (Measurement/Conclusion/Sample→Mechanism/Conclusion/Material/Metric) ·
`INVOLVES` (Sample/Material/Method/Conclusion→Mechanism) · `CONCLUDES` (Paper→Conclusion) · `PART_OF` · `APPLIED_TO`.
Co-occurrence in a paragraph is not a relation. Direction matters: "A outperforms B" → `A OUTPERFORMS B`.

## Alignment rules (applied by build_graph.py, recorded in `merge_log` / `conflicts`)

- Within a paper: entities sharing a normalised name/alias (case, hyphen, space, plural, Greek-letter
  insensitive) and the same type become one node.
- Across papers: only concept types merge, only on an equal normalised **full name** (abbreviation
  alone never merges). The merged node keeps per-paper evidence; edges stay per paper, so conditions,
  samples and values are never combined into one conclusion.
- Recorded, not merged: `abbreviation_homonym` (same abbreviation, different expansions),
  `same_label_different_object` (instances with equal labels), `possible_same_person`,
  `similar_name_review` (e.g. graphene oxide vs reduced graphene oxide), `same_name_different_type`,
  plus your declared `conflicts`.

## Outputs (`/app/output`)

`result.json` — `case_id`, `status` (success | partial | failed) + `status_detail`, `sources`, `nodes`, `edges`
(each with evidence: source_id, paragraph_id, quote, match), `queries` (results with evidence and
uncertain items), `alignment` (merges, not_merged, rules), `conflicts`, `rejected`, `not_reported`,
`uncertainty`, `evidence_index`, `change_log`, `artifacts`, `run`, and every `output_contract` field
(mapped from the graph, or from contract_fill.json; unmapped fields are null and listed in uncertainty).
`graph/` — graph.json, nodes.csv, edges.csv, evidence.csv, graph.graphml, graph.mmd, graph.dot, graph.html,
graph.svg/png, `queries/<id>.svg|png`. `queries.md` — readable query results. `check_report.json` — independent re-check.

## Failure handling

| Situation | What happens / what to do |
|-|-|
| case.json / manifest missing | ingest warns; sources are derived from files; state it in notes.json |
| a manifest paper has no text | ingest status `partial`; result status `partial`; do not invent its content |
| only publisher XML / Markdown / PDF | XML `<p>` (ids or generated `xml-pNNN`), Markdown blocks (`selfmade-mdNNN`), PDF blocks (`pdfpageN-bM`, real page numbers) are used; generated IDs are labelled as such |
| encrypted / scanned PDF | ingest warning; report the paper as unreadable, no OCR guesses |
| quote not found | item rejected with reason; fix the quote or leave it rejected |
| same name, different object | keep separate; add a `conflicts` entry if it matters for the task |
| papers disagree | both edges kept, `conflicts` entry with both quotes; never pick a winner unless a paper does |
| query finds nothing | `no_result` + reason in result.json; say "not reported in the material" |
| script crash | result.json is still written by run_all.py with status `failed`/`partial` and the step logs |

Never: cite page numbers that do not exist, merge two papers' samples/values, copy the primary DOI to the
secondary paper, present table values that are not in the paragraph text, or claim success when status is partial.
