# Minimal example (synthetic data — not a real paper, not an official case)

Input: `examples/mini/input/` — two made-up "papers" S1 and S2 of three paragraphs each, a manifest and a case.json.
They are built so that the alignment rules are visible:

| In S1 | In S2 | Expected decision |
|-|-|-|
| particle swarm optimization (**PSO**) | pseudo-second-order (**PSO**) model | not merged — `abbreviation_homonym` |
| Composite C1 (from graphene oxide + chitosan) | Composite C1 (iron-doped carbon) | not merged — `same_label_different_object` |
| J. Smith | J. Smith | not merged — `possible_same_person` |
| X-ray diffraction (XRD) | X-Ray Diffraction (XRD) | merged (case-insensitive full name) |
| Graphene Oxide | graphene oxide (GO) | merged; S2's reduced graphene oxide stays separate (`similar_name_review`) |
| Langmuir isotherm | Langmuir isotherms | merged (plural) |

The agent-written extraction files are in `examples/mini/work/extract/` and the queries in `examples/mini/work/queries.json`.

## Run

```bash
K=submission/scripts            # or /skills/weekly-skill/scripts
python $K/ingest.py  --input submission/examples/mini/input --work /tmp/mini/work
cp -r submission/examples/mini/work/* /tmp/mini/work/
python $K/run_all.py --input submission/examples/mini/input --work /tmp/mini/work --out /tmp/mini/out
python $K/query_graph.py --graph /tmp/mini/work/graph/graph.json find PSO
```

## Example output (abridged, from a local run; your hashes/timestamps differ)

```
build_graph: {'nodes': 18, 'edges': 10, 'shared_concepts': 4, 'rejected': 0, 'conflicts': 4, 'needs_review_edges': 1}
  q1: ok  nodes=5 edges=4
  q2: ok  nodes=2 edges=0
  q3: ok  nodes=8 edges=7
check_result: ok=True checked=26 hard=0 warnings=[]
run_all: status=success nodes=18 edges=10 queries_ok=6 problems=[] check_exit=0
```

`/tmp/mini/out/queries.md`, query q2 (“Is 'PSO' the same method in both papers?”):

| node | type | papers | evidence |
|-|-|-|-|
| particle swarm optimization (PSO) | Method | S1 | S1:a1 “particle swarm optimization (PSO)” |
| pseudo-second-order model (PSO) | Method | S2 | S2:b1 “Kinetics were fitted with the pseudo-second-order (PSO) model” |

Related alignment records: `abbreviation_homonym: pso — same abbreviation expands to different full names in different papers (not_merged)`

Query q1 keeps the two papers' capacities apart (120 mg/g at 25 °C in S1, 45 mg/g in S2, temperature not stated —
listed under `not_reported`), each with its own paragraph and quote.

`result.json` (abridged):

```json
{"case_id": "mini-example", "status": "success",
 "sources": [{"source_id": "S1", "doi": "10.0000/example.1"}, {"source_id": "S2", "doi": "10.0000/example.2"}],
 "edges": [{"id": "R:…", "source": "S1:Sample:composite-c1", "predicate": "HAS_RESULT", "target": "S1:Measurement:c1-capacity-120-mg-g-methylene-blue-25-c",
            "source_id": "S1", "conditions": {"adsorbate": "methylene blue", "T": "25 °C"}, "strength": "direct",
            "evidence": [{"source_id": "S1", "paragraph_id": "a3", "quote": "Composite C1 reached 120 mg/g for methylene blue at 25 °C.", "match": "exact"}]}],
 "alignment": {"merges": [{"scope": "cross_paper", "merged": ["X-Ray Diffraction", "X-ray diffraction"], "basis": "equal normalised full name 'xraydiffraction'"}],
               "not_merged": [{"kind": "possible_same_person", "names": ["J. Smith"]}, {"kind": "same_label_different_object", "names": ["Composite C1"]},
                              {"kind": "abbreviation_homonym", "abbreviation": "pso"}, {"kind": "similar_name_review", "names": ["Graphene Oxide", "reduced graphene oxide"]}]}}
```
