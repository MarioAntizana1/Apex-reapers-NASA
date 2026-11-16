# 12. Research log and decisions

Historical records below are translated and consolidated. Counts reflect recorded snapshots, not a new acquisition or independent audit.

## Activity log

| Date | Activity | Recorded evidence |
|---|---|---|
| 2026-10-24 | Challenge, Mars science and technical-report research | Original dossier, source catalog and local papers |
| 2026-10-24 | OpenAlex exploratory search | 40 queries; 235 candidate records |
| 2026-10-24 | NTRS search | Consolidated report records and local open PDFs |
| 2026-10-24 | Mars Trek audit | 76 services; 17/18 requested resources recorded; Jezero vectors/rasters |
| 2026-10-24 | MEDA sample acquisition | Six product categories, sol 1740 |
| 2026-10-24 | Research figure and regional DEM/traverse statistics | Local evidence figure and statistics |
| 2026-10-25 | Team redistribution | Historical five-person plan |
| 2026-11-02 | Six-person roster update | Mauricio Sebastián Reátegui and Valeria Rosado added; earlier roster superseded |
| 2026-11-14 | Challenge-resource audit and Jezero CTX acquisition/processing | `Evidencias/datos/recursos_nasa_2026/`, Jezero catalog and derivatives |
| 2026-11-14 | Initial map implementation scope approved | `app/`, initial interface document |
| 2026-11-15 | English public documentation/distribution scope approved | [Publication plan](24_Publication_Plan.md), README and AI disclosure |

## Research queries and findings

Search categories included human exploration, EVA/walkback, terrain, GIS, Jezero, atmosphere, resources, science, communications, habitability and planetary protection. Search configurations and results remain the reproducible record.

Key findings: primary Mars data is available; MOLA does not resolve walking hazards; archived MEDA is not live weather; science-driven EVA planning and latency need explicit treatment; and public Jezero viewers already exist [S14, S16–S17, S27–S34, S49, S72].

## Architecture decision record register

| ADR | Date | Decision and reason | Status / consequence |
|---|---|---|---|
| ADR-001 | 2026-10-24 | Focus on Jezero: rich observations and exploration-zone precedent [S17] | Accepted case study; no landing-site certification |
| ADR-002 | 2026-10-24 | Focus on one short illustrative EVA, not a multi-sol campaign | Planning scope; four-hour scenario is an assumption |
| ADR-003 | 2026-10-24 | React/TypeScript/Vite with OpenLayers/proj4 | Implemented stack; planetary CRS needs explicit handling |
| ADR-004 | 2026-10-24 | Use locally prepared static assets without a required backend | No claim of live data or completed offline support |
| ADR-005 | 2026-10-24 | Expose configurable EVA assumptions | No validated suit model |
| ADR-006 | 2026-10-24 | Restrict pre-event work to research/planning under the team's reading of guidance [S03] | Historical timing policy; official rules govern |
| ADR-007 | 2026-10-24 | Plan bilingual UI, internal Spanish documents and English submission | Public-document language updated by ADR-012; bilingual UI still pending |
| ADR-008 | 2026-10-24 | Explicit Mars equirectangular coordinates rather than Earth WGS84 | Actual local projection documented in app guide; source transformations need review |
| ADR-009 | 2026-10-25 | Redistribute responsibilities for a five-person roster | Superseded by ADR-010 |
| ADR-010 | 2026-11-02 | Restore six-person roster and redistribute QA, research, PM and visual work | Latest roster; confirm individual assignments |
| ADR-011 | 2026-11-14 | Deliver a 2D shell before inventing or assuming terrain assets | Historical first delivery; later code includes experimental 3D/routing |
| ADR-012 | 2026-11-15 | Publish English reference documentation, reproducible procedures and AI disclosure; omit raw archive/private history | Owner-approved publication policy; preserve source IDs and stable filenames |

ADR-012 alternatives: upload the entire roughly 8 GB archive, or publish source catalogs/manifests and download procedures. The latter was approved to avoid bulk, incomplete-download and privacy/redistribution risks.

The latest source uses a local spherical projection; the earlier general “Mars 2000” wording must not be interpreted as proof that all assets share identical coordinates.

## Open questions and risks

| Question / risk | Next action |
|---|---|
| Actual submission/event requirements | Verify current official guidance and deadline |
| Local terrain alignment and quality | Independent control-point/metadata review |
| Suit, radiation and communication assumptions | Seek qualified expert review |
| Science scoring and POI interpretation | Source-backed criteria; no unsourced certainty |
| Visual-asset authorship and rights | Complete per-asset provenance |
| Contributor availability and handoffs | Confirm current responsibilities |
| Prototype versus deployed version | Verify both separately |
| AI-use inventory | Preserve known use; acknowledge missing historical model metadata |

No completed external scientific validation or official submission is inferred from this log.

## Evidence and change control

Use the [scripts guide](../Scripts/README.md), [evidence policy](../Evidencias/README.md), [validation plan](09_Plan_de_Validacion.md) and [traceability matrix](17_Matriz_de_Trazabilidad.md). For future decisions record context, alternatives, reason, consequence, owner/date and status; do not overwrite historical outcomes with aspirations.
