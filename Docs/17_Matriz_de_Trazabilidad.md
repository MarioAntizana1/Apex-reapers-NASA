# 17. Requirements traceability

The chain is **requirement → source/data → function → check → evidence**. Requirement IDs are project interpretations of the challenge [S01] and historical evaluation guidance [S04], not an independent official acceptance decision.

## Requirements and current evidence

| ID | Requirement | Data / source | Function and checks | Current status |
|---|---|---|---|---|
| R1 | Integrated layered view | CTX/HiRISE, Mars Trek [S14, S37, S78–S79] | Map/catalog; D01–D08, U01 | Partial implementation; independent alignment review pending |
| R2 | Multiple NASA mission datasets | Source catalog [S14–S16, S40–S43, S47] | Provenance cards; D01–D08 | Catalog/research exists; not every candidate mission is integrated |
| R3 | Surface location or route | Jezero, traverse and terrain [S14, S36–S37] | Base/stops, experimental routing; U02, D02, D05 | Prototype implemented; no operational suitability claim |
| R4 | Support Marswalk planning | Terrain/planning literature [S27–S33, S72] | Mission estimates; U03/U06/U08, C09, T04 | Illustrative partial model; brief and full constraints pending |
| R5 | Help reason about execution/return | Relay, radiation and environmental context [S09, S16, S42–S43] | Return concepts and risk explanations; U03/U05/U07, T04 | Return-to-base estimates exist; validated turn-around, comm/radiation models pending |
| R6 | Connect scientific opportunities | Geology, mineralogy and ROIs [S35–S39, S47] | Context overlay/stops; U04/U08, C01–C08 | Partial context; expert-reviewed POIs/science scoring pending |
| R7 | Scientific validity and feasibility | Original archives and mapping guidance [S50] | Metadata, assumptions, tests; D01–D08, C01–C09, T01–T10 | Software evidence exists; independent scientific/rights review incomplete |
| R8 | Explain problem and solution | Public docs and presentation plan | README, pitch, references, disclosure; P01–P05 | English documentation prepared; actual submission/presentation acceptance not claimed |

## Software artifacts

| Artifact | What it supports | What it does not establish |
|---|---|---|
| `app/src/layers.test.ts` | Layer-contract validation | Scientific accuracy or licensing |
| `app/src/mission.test.ts`, `simulation.test.ts` | Illustrative calculation behavior | Suit performance or health/safety |
| `app/src/terrain.test.ts`, `hirise.test.ts` | Coverage/asset-coordinate helper behavior | Independent geospatial alignment |
| `app/src/routing/*.test.ts` | Experimental graph/terrain behavior | Accuracy of assumed input terrain |
| `app/tests/interface.spec.ts` | UI scenarios with controlled fixtures | Real-data scientific validation |
| `app/tests/routing-regression.spec.ts` | Stale-response and route regression scenarios | Operational route certification |

Run tests before recording current results. Their presence alone is not a passing execution.

## Research evidence

- Source/product catalog: `Docs/03_Fuentes_y_Datos_NASA.md` and `app/public/layers.json`.
- Acquisition metadata: `Evidencias/datos/mars_trek/`, `datos/jezero/`.
- Literature records: `Evidencias/datos/openalex_resultados.csv`, `ntrs_resultados.csv`.
- MEDA sample: local original collection, restored separately [S16].
- Integrity scope: `Evidencias/manifiesto.csv` and [evidence policy](../Evidencias/README.md).
- Bibliography and methods: [11](11_Bibliografia.md), [05](05_Metodologia.md).

## Open gaps

Validated local hazard/slope inputs, independent coordinate checks, suit/consumable validation, relay ephemerides, local radiation modeling, science review, user studies, brief export and deployment verification remain separate work.

**Rule:** no orphan feature enters the core scope; no requirement is marked complete without appropriate evidence. Documentation publication updates visibility and traceability, not scientific completion.
