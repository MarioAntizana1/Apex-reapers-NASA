# Apex-Mars — documentation

**Team:** Apex-Reapers. **Application:** Apex-Mars (provisional name); earlier research used **Ares Atlas**.

**English reference edition:** 2026-11-15. Stable Spanish filenames and source IDs are retained so existing links continue to work. Earlier planning has been edited and consolidated in English; it is not a claim that all proposed work was completed.

Start with the [project README](../README.md), [executive summary](00_Resumen_Ejecutivo.md), [source catalog](03_Fuentes_y_Datos_NASA.md) and [workflows/AI disclosure](25_Workflows_Tools_AI_and_Impact.md).

## Document map

| Document | Purpose |
|---|---|
| [00 — Executive summary](00_Resumen_Ejecutivo.md) | Problem, proposal, current status and potential value |
| [01 — Challenge and participation](01_Reto_y_Convocatoria.md) | Official links, recorded schedule and compliance |
| [02 — Mars and Jezero research](02_Investigacion_Marte.md) | Scientific background and interpretation limits |
| [03 — NASA and other data sources](03_Fuentes_y_Datos_NASA.md) | Original pages, missions, products and acquisition contracts |
| [04 — Related work and benchmark](04_Estado_del_Arte_y_Benchmark.md) | Prior tools, literature and differentiation |
| [05 — Methodology](05_Metodologia.md) | Research, development, review and quality gates |
| [06 — Solution proposal](06_Propuesta_Solucion.md) | Personas, architecture, scope and roadmap versus implemented prototype |
| [07 — Project plan](07_Plan_Proyecto.md) | Work packages, event plan, risks and contingencies |
| [08 — Team and roles](08_Equipo_y_Roles.md) | Responsibilities, review and collaboration |
| [09 — Validation plan](09_Plan_de_Validacion.md) | Data, science, usability, software and presentation tests |
| [10 — Pitch and communication](10_Plan_de_Pitch_y_Comunicacion.md) | English narrative, demo, submission and disclosure |
| [11 — Bibliography](11_Bibliografia.md) | Source IDs, primary links, DOIs and research limitations |
| [12 — Research and decisions](12_Registro_de_Investigacion.md) | Historical activity, ADRs and unresolved questions |
| [13 — Checklists and templates](13_Checklist_y_Plantillas.md) | Data cards, tests, ADRs, AI log and release checklists |
| [14 — Glossary](14_Glosario.md) | Scientific and technical vocabulary |
| [15 — Data-access feasibility](15_Prueba_de_Viabilidad_Tecnica.md) | Recorded research results, not operational validation |
| [16 — Learning plan](16_Plan_de_Aprendizaje_y_Reto_Personal.md) | Skills, team learning and retrospective |
| [17 — Traceability matrix](17_Matriz_de_Trazabilidad.md) | Requirement → source → function → test → evidence |
| [18 — Game and analyst concepts](18_Modo_Juego_y_Simulacion.md) | Optional modes and scientific boundaries |
| [19 — 2D/3D design](19_Planteamiento_Web_2D_3D.md) | Shared data contracts and design trade-offs |
| [20 — Team objectives and tools](20_Objetivos_y_Herramientas_Equipo.md) | Proposed responsibilities and deliverables |
| [21 — 3D testing and contingency](21_Pruebas_y_Contingencia_3D.md) | Coverage, interaction, performance and fallback |
| [22 — Initial interface scope](22_Base_Interfaz.md) | Historical first delivery and acceptance criteria |
| [23 — Jezero imagery and topography](23_Datos_Jezero_Topografia.md) | Actual products, derivatives and quality caveats |
| [24 — Publication plan](24_Publication_Plan.md) | Approved English documentation and Git distribution policy |
| [25 — Workflows, tools, AI and impact](25_Workflows_Tools_AI_and_Impact.md) | End-to-end procedures and transparency statement |

## Operating procedures

- [Run, build, test and integrate layers](../app/README.md).
- [Acquire data and regenerate derivatives](../Scripts/README.md).
- [Understand omitted raw data and integrity manifests](../Evidencias/README.md).
- [Experimental routing integration and limitations](../app/INTEGRACION_RUTAS.md).

## Reading status correctly

The initial dossier recorded pre-event research in October 2026. Later records cover application development during the event. Descriptions of the full MVP, bilingual UI, offline support, brief export or expert review are **targets unless implementation and evidence are explicitly identified**.

The prototype contains a map, planning assumptions, experimental routing and a limited 3D demonstration. It does not establish that the full challenge or operational safety requirements are satisfied.

## Conventions

- `[Sxx]` refers to the bibliography; the same IDs survive translation.
- Dates use ISO 8601; retain original observation dates and sols.
- Use SI units where applicable; identify non-SI display units explicitly.
- `ASSUMPTION` means a value or model is not independently validated. Existing UI/source records may say `SUPUESTO`.
- Each layer needs mission/instrument, variable, resolution, date, CRS, coverage, source, usage terms, processing and limitations.
- Record decisions as `ADR-xxx`; never confuse a historical decision with a completed validation.
- Passing software tests is not scientific certification.

**Safety boundary:** research and education only; not navigation, life support or a validated EVA simulator.
