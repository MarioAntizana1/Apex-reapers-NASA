# 25. Workflows, tools, generative AI and potential impact

**Project:** Apex-Mars · **Team:** Apex-Reapers · **Edition:** 2026-11-15.

This is the public operating guide and transparency statement. See [current scope](06_Propuesta_Solucion.md), [validation](09_Plan_de_Validacion.md) and [bibliography](11_Bibliografia.md).

## End-to-end workflow

```text
Challenge requirements
  → literature and original data pages
  → acquisition + source metadata
  → geospatial inspection + usage-term review
  → derived web assets
  → 2D map / experimental route / 3D demonstration
  → software tests + separate scientific review
  → documentation, demonstration and submission
```

### 1. Research and source selection

1. Read the challenge and current participant guidance [S01–S03].
2. Discover literature with OpenAlex and NASA NTRS; prefer primary sources [S81–S82].
3. Record why a source supports a specific requirement, not just that it mentions Mars.
4. Separate original observations, interpretations, climatology and project assumptions.
5. Add a stable `[Sxx]` bibliography entry before using a scientific claim.

The existing review is exploratory, not a systematic review or expert certification. Search inputs are in `Scripts/queries_openalex.json` and `Scripts/queries_ntrs.json`.

### 2. Data acquisition and validation

1. Select a product from Mars Trek, PDS, USGS or another identified primary archive.
2. Preserve the original URL, product ID, observation/acquisition date and required attribution.
3. Inspect the actual metadata: body model, latitude/longitude convention, CRS, units, resolution, coverage, vertical reference and no-data.
4. Check download completeness and record a checksum.
5. Evaluate fitness for the intended scale. A context map is not a local hazard survey.

Use [script procedures](../Scripts/README.md), [source catalog](03_Fuentes_y_Datos_NASA.md) and the [data-card template](13_Checklist_y_Plantillas.md).

### 3. Processing and map integration

1. Keep originals unchanged.
2. Derive reduced images, terrain chunks and metadata in a documented processing step.
3. Transform real data into the app's local Mars projection; do not assign arbitrary map bounds to a screenshot.
4. Add complete metadata to `app/public/layers.json`.
5. Check alignment at control points and show partial coverage or uncertainty visibly.
6. Keep the experimental image-derived routing grid separate from measured terrain.

Native resolution, resampled spacing, storage quantization and accuracy are four different properties. The HiRISE CR model has documented quality caveats [S78–S79].

### 4. Development and review

Git and GitHub provide source history and integration. The working process is small, reviewable changes with explicit acceptance criteria:

```text
Task + owner + acceptance criterion
  → inspect connected code/data
  → implement or integrate
  → automated checks
  → human review
  → documented limitations
  → commit / publication
```

Keep credentials, conversation exports, caches and raw multi-gigabyte downloads out of commits. Preserve other contributors' work; do not reset or overwrite it to simplify publication.

### 5. Testing and release

From `app/`, run `npm test`, `npm run build` and `npm run test:e2e` after installing the Playwright browser. Inspect the public deployment separately: a source push is not proof that GitHub Pages was updated.

Software checks cover contracts, algorithms and UI behavior. Separate review must check the actual scientific dataset, coordinate alignment, interpretation, licenses and suitability. See test IDs D01–D08, C01–C09, U01–U08, T01–T10 and P01–P05 in the [validation plan](09_Plan_de_Validacion.md).

Before publishing, check sources, missing assets, disclosure, links and whether each advertised feature really exists. Record unavailable evidence rather than declaring the entire MVP complete.

## User workflow

1. Open the 2D Jezero map.
2. Inspect layer sources, dates and limits; adjust visibility/opacity.
3. Place a **hypothetical** base and add science stops.
4. Review straight-line mission estimates and the separately labelled experimental terrain route.
5. Open 3D only within supported terrain coverage; explore the illustrative scene.
6. Return to the map to revise the plan.

The 3D direction indicator points toward a stop in a straight line. It is not obstacle avoidance. The illustrative resource meters do not block movement at zero and are not a suit-status feed.

An exportable brief and validated science/return alternatives remain planned. Do not include them in a demo script as if already available.

## Tool inventory: confirmed versus proposed

| Tool | Role | Evidence/status |
|---|---|---|
| React, TypeScript, Vite, npm | UI, typing, development and build | `app/package.json`, application source |
| OpenLayers, proj4 | Map and planetary coordinate handling | Dependencies and map implementation |
| Three.js | Experimental 3D scene | `app/src/Terrain3D.tsx`; no React Three Fiber dependency |
| Python, requests | Research acquisition and service audits | `Scripts/` |
| NumPy, rasterio, Pillow, tifffile | Raster processing and terrain/image derivatives | Imports in processing tools |
| pypdf, truststore | Report text extraction and platform certificate support | Research tools |
| Vitest, Playwright | Unit and browser tests | Test scripts and suites |
| Git, GitHub, GitHub Pages | Version control, collaboration and static demonstration | Repository and public demo link |
| OpenCode, generative-AI assistance | Coding, troubleshooting and documentation support | This publication workflow and project working material |
| QGIS / GDAL | Proposed GIS inspection workflow | Team plan; individual usage not independently audited |
| Zotero | Proposed citation-management tool | Team plan; actual usage not established |
| Figma or Penpot | Proposed design workflow | Team plan; tool choice not confirmed |
| Blender, Krita or GIMP | Proposed visual-asset workflow | Team plan; per-asset production history not confirmed |
| Service Worker / PWA | Intended offline support | Roadmap, not implemented functionality |

## Generative AI disclosure

**Generative AI was used as an assistant during this project.** It supported research organization, brainstorming, technical explanations, code drafting and debugging, test preparation, documentation and English editing/translation.

OpenCode is an agent environment, not a scientific data source. The model identified for this publication session is **OpenAI GPT-6.1 Sol**. We do not have a verified complete list of providers, model versions, prompts or dates for all earlier assistance, and do not invent one.

### Public usage record

| Activity | AI contribution | Required human responsibility / remaining limit |
|---|---|---|
| Research organization | Suggested search directions, summaries and document structure | Verify primary sources and do not cite AI as scientific authority |
| Product and workflow planning | Helped articulate scope, roles and trade-offs | Team decides priorities and checks event guidance |
| Development support | Assisted with code, debugging and explanations | Review implementation and run tests; assistance does not certify correctness |
| Validation preparation | Suggested test cases and checks | Distinguish proposed tests from executed results and scientific validation |
| Documentation publication, 2026-11-15 | English reference edition, source organization, procedures and disclosure | Project owner approved publication scope; scientific/rights review remains open |
| Visual assets | Complete per-asset AI/authorship history is not established | Confirm author, source, transformations and rights before claiming ownership or unrestricted reuse |

### Boundaries and safeguards

- AI is not an onboard autonomous mission controller or an implemented conversational assistant in the app.
- NASA/USGS measurements come from the cited archives, not from a language model.
- Generated explanations and code can contain errors. Passing software tests does not validate the scientific model.
- Do not enter secrets or private participant data into public logs or publish private conversation exports.
- Humans remain accountable for final decisions, interpretation, citation, code review and submission.
- Decorative models/icons and illustrative resource rates are not observations of Mars or validated suit performance.

For future entries, use the [AI-use record template](13_Checklist_y_Plantillas.md#ai-use-record) and note the tool/model if known, task, affected artifacts, review performed and remaining uncertainty.

## Potential benefits and how to evaluate them

These are proposed outcomes, not measured results:

| Audience | Potential benefit | Suggested evaluation |
|---|---|---|
| Students and educators | Understand Mars terrain and mission trade-offs | Before/after comprehension questions and source-identification tasks |
| Public science users | Explore orbital and rover context with less jargon | Task completion, misunderstanding reports and accessibility review |
| Planning researchers | Compare route assumptions in an inspectable prototype | Benchmark against validated terrain, established methods and expert review |
| Planetary-science communicators | Connect a geological claim to its source and uncertainty | Review sample data cards and check for unsupported claims |
| Development/data teams | Reuse documented acquisition and integration procedures | Fresh-workspace reproduction and checksum comparison |

The motivating literature discusses science-driven EVA planning [S27–S33], terrain-aware trade-offs [S72] and responsible planetary mapping [S50–S51]. It does **not** prove this prototype improves real mission safety.

## Risks and next steps

1. Replace assumed routing indices/height scaling with independently validated measurements.
2. Review geospatial alignment, partial coverage, vertical datum and CR-model artifacts.
3. Verify third-party asset rights and complete the visual-asset inventory.
4. Implement a traceable mission brief before adding nonessential modes.
5. Test usability with new users and record findings, not just aspirations.
6. Add validated environmental, communications or resource models only with evidence and clear dates.
7. Update public claims after actual tests and deployments, not merely after editing a roadmap.
