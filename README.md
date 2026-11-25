# 阅读15｜文献知识图谱构建 — literature-kg (v0.1.1)

The deliverable is the **Skill** in [`submission/`](submission/) (`SKILL.md`, `scripts/`, `schema/`, `examples/`).
At evaluation time it is installed as `/skills/weekly-skill` and run on the platform's three fixed cases. This
bundle has no official answers and no official case data.

**Problem chosen:** evidence binding + cross-paper alignment. Every node and edge is tied to
`source_id + paragraph_id + verbatim quote` (verified by script), concepts are merged across papers only under
explicit rules (merge basis logged), refused merges and disagreements are recorded, and ≥3 queries return
subgraphs with their quotes and uncertain parts. Exports: JSON, CSV, GraphML, Mermaid, DOT, HTML, SVG/PNG.

## Layout

| Path | Content |
|-|-|
| `submission/` | The Skill (22 text files, ~150 KB): `SKILL.md` (agent workflow, schema, rules), `README.md` (methods, limits), `scripts/` (ingest, build_graph, query_graph, export_graph, run_all, check_result, find_text, kglib), `schema/extraction.schema.json`, `examples/` (runnable synthetic two-paper example) |
| `skills/SKILL.md` | copy of the Skill entry point (ARM `skills` modality) |
| `src/reproduce.py` | reproduces everything below |
| `src/make_case.py` | turns the two CC-BY JATS articles in `data/raw/` into a case shaped like the challenge input |
| `src/run_tests.py` | negative controls, alignment vs naive baseline, incremental update, failure handling |
| `data/case1_agent_work/` | extraction files the agent (Claude) wrote while following SKILL.md on that case |
| `execution/` | `run.log` and `results/` (case output incl. result.json, graph files, PNG previews, query results; test report; metrics) |
| `characterization.json`, `trace/trace.jsonl`, `arm_manifest.json` | ARM v1.1 files |

## Reproduce

```bash
python src/reproduce.py      # Python >= 3.9; matplotlib optional (PNG previews). ~15 s.
```

## Results (local, see `execution/results/metrics.json`)

| Check | Skill | Note |
|-|-|-|
| Negative controls (fabricated/misplaced quotes, unknown type/predicate, reversed domain, wrong number, hedged quote) | 7/7 entities, 9/9 relations decided as designed | |
| Cross-paper alignment on a designed set (PSO homonym, same-label samples, same personal name, case/plural variants, GO vs rGO) | precision 1.0, recall 1.0 | naive "same name or any shared alias" merge: 0.5 / 0.75, 3 false merges |
| Incremental update (paper A, then A+B with `--previous`) | 57/57 node IDs, 64/64 edge IDs kept; 10 concepts extended | |
| Failure handling (empty input, missing secondary text, XML-only fallback, empty queries, broken extraction file, determinism) | 6/6 | result.json always written with honest status |
| Real two-paper case (graphene-oxide adsorbents, 73 + 110 paragraphs) | 99 nodes, 114 edges, 10 cross-paper concepts, 5 conflict records, 0 rejected, 210 quotes re-verified, 9/10 queries with results (the 10th correctly returns `no_result`: paper B did not run XPS) | extraction written by Claude, not by the platform's DeepSeek agent |

These test the scripts' mechanisms. How much the Skill helps the platform's agent is measured by the
platform's own baseline-vs-Skill runs; nothing here claims that number.

## Known limits

Extraction recall depends on the agent and is not measured; synonyms with different words merge only through a
declared alias or an override with a reason; table/figure-only values are listed as not reported; approximate quote
matches are accepted but marked. Details in `submission/README.md`.

## License

Code: MIT ([LICENSE](LICENSE)). Test articles: CC BY 4.0, see [`data/ATTRIBUTION.md`](data/ATTRIBUTION.md).
