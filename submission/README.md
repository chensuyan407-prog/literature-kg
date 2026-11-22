# literature-kg v0.1.0 — methods, limits, maintenance

Skill for the Bohrium challenge “阅读15｜文献知识图谱构建” (`product-arena-10-760d1a0b`).
Entry point for agents: [`SKILL.md`](SKILL.md). Runnable example: [`examples/minimal_example.md`](examples/minimal_example.md).

## Chosen problem

**Evidence binding + cross-paper alignment** for a small corpus (typically two papers): turn the papers into
one graph in which every node and edge can be traced to `source_id + paragraph_id + verbatim quote`, where the
same concept in two papers becomes one node *only* when the rule allows it, and where refused merges and
disagreements are recorded instead of being silently resolved. Queries run on that graph and return the
supporting quotes and the uncertain parts.

## Division of labour

| Step | Who | Why |
|-|-|-|
| Find entities, relations, conditions, hedging | agent (LLM) | needs reading comprehension |
| Paragraph flattening, source registry | `ingest.py` | material schema is not fixed; IDs must be the organiser's |
| Quote verification, schema/type constraints, number check, hedge/citation cues | `build_graph.py` | must be exact and repeatable |
| Alias alignment, homonym / same-label / similar-name records, stable IDs, incremental change log | `build_graph.py` | deterministic rules, auditable `merge_log` |
| Queries with subgraph + evidence + uncertainty | `query_graph.py` | same answer every run |
| Exports and previews | `export_graph.py` | JSON, CSV, GraphML, Mermaid, DOT, HTML, SVG, PNG |
| Result assembly, contract mapping, independent re-check | `run_all.py`, `check_result.py` | result.json always written |

## Key methods

- **Material discovery** (`ingest.py`): any JSON object with a text field (`text|content|body|paragraph|…`) and an
  ID field (`paragraph_id|para_id|pid|id|…`) is a paragraph; the source is taken from the object or its ancestors,
  else from the manifest file mapping, else from `primary`/`secondary` in the file name. Per-paper files win over the
  summary index (`material.json`); text differences between them are reported. Publisher XML `<p>` elements are used
  only when a paper has no JSON text (otherwise kept to cross-check quotes: `publisher_xml_check`). Markdown/PDF are
  fallbacks with clearly generated IDs (`selfmade-mdNNN`, `pdfpageN-bM`).
- **Quote verification**: exact → normalised (NFKC, unified dashes/quotes, case, whitespace) → squashed
  (letters/digits only, tolerates linearised sub/superscripts like `R 2`/`R2`) → approximate (≥90 % of tokens and a
  contiguous run of ≥6 tokens). Anything else is rejected with the reason. `check_result.py` repeats the check on
  the final result.json independently of the builder.
- **Grounding flags**: an entity whose name/alias does not occur in its evidence paragraph (≥60 % of distinctive word
  stems) is flagged; an edge whose subject/object is not named in the evidence paragraph gets `needs_review`;
  Measurement values whose digits are not in any quote are flagged; hedging words downgrade `direct` → `hedged`;
  citation cues (`[12]`, `et al.`, `has been reported`) are flagged when attribution is `author`.
- **Alignment rules**: within a paper, shared normalised name/alias + same type. Across papers, only concept types
  (Material, Method, Task, Metric, Instrument, Mechanism) merge, only on an equal normalised full name — never on an
  abbreviation alone. Instance types (Sample, Measurement, Conclusion, Dataset, Model, Condition, Paper) never merge
  across papers. Researchers never auto-merge across papers (name equality is not identity). Records:
  `abbreviation_homonym`, `same_label_different_object`, `possible_same_person`, `similar_name_review`
  (distinctive-token Jaccard > 0.5), `same_name_different_type`, agent-declared conflicts with ≥2 verified quotes.
- **No cross-paper synthesis**: edges are always paper-scoped (`source_id`), so a shared concept node connects two
  papers' statements without combining their conditions, samples or values. Path queries that cross papers say so.
- **Stable IDs**: concept `C:<Type>:<slug>`, instance `<source_id>:<Type>:<slug>`, edges `R:<hash(subject, predicate,
  object, source, conditions)>`. With `--previous`, node IDs are looked up by name/alias keys and kept.

## Tested (see repository `tests/`)

| Test | Result |
|-|-|
| Negative controls (fabricated quote, wrong paragraph, other paper's text, unknown type/predicate, reversed domain, unknown key, wrong number, hedged quote) | 7/7 entity and 9/9 relation decisions as expected |
| Designed alignment set (PSO homonym, same-label samples, same personal name, case/plural variants, GO vs rGO) | skill precision 1.0 / recall 1.0; naive name-or-alias merge 0.5 / 0.75 (3 false merges, 1 missed) |
| Incremental: paper A, then A+B with `--previous` | 57/57 node IDs and 64/64 edge IDs kept; 10 nodes extended with paper B |
| Failure handling | empty input → `failed` result.json; missing secondary text → `partial`; XML-only fallback; empty queries → `no_result` with reason; broken extraction JSON skipped with warning; rebuild byte-identical |
| Real pair (two CC-BY 4.0 papers on graphene-oxide adsorbents, extraction written by hand following SKILL.md) | 99 nodes, 114 edges, 10 cross-paper concepts, 0 rejected, 210 evidence items re-verified |

These are mechanism tests on local data. They do not measure how a given LLM agent performs with the Skill; the
platform's own baseline-vs-Skill runs do that.

## Limits

- Extraction quality depends on the agent; the scripts verify evidence and structure, not whether the agent missed
  an entity. Recall is not measured automatically.
- Table and figure contents are not in paragraph material; values only in tables are listed as `not_reported`.
- Alias matching is lexical. Synonyms with different words (e.g. "magnetite" vs "Fe3O4" when not declared as alias)
  are not merged unless the agent lists the alias or adds a `merge` override with a reason.
- Approximate quote matching can accept a quote with a changed small word; such evidence has `match: approx`
  and is listed as uncertain.
- The overview figure is a column layout (paper A | shared | paper B), readable up to ~150 nodes per column.

## Maintenance

Version 0.1.0 (2026-11-22). Python ≥ 3.9 standard library; optional matplotlib ≥ 3.5 (PNG) and PyMuPDF ≥ 1.23
(PDF input). Changes to the relation vocabulary go in `scripts/kglib.py` (`PREDICATES`, type sets) and must be
mirrored in `SKILL.md` and `schema/extraction.schema.json`. License: MIT.
