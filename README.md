# Apex-Mars

**Explore Jezero Crater, plan a Marswalk, and understand the assumptions behind every decision.**

Apex-Mars is an educational Mars exploration prototype developed by **Apex-Reapers** for the **NASA Space Apps Challenge 2026 — Interplanetary Survival Guide: Martian Map**. Earlier research uses the working name **Ares Atlas**.

The project connects orbital imagery, topography and scientific context in a browser-based map. Its longer-term goal is to help people ask three questions: **Where could we go? What could we learn? How would we return?**

> **Research and education only.** This is not certified navigation, a validated EVA simulator, a weather forecasting service or a life-support system. A route or green indicator does not establish that a real traverse is safe.

**Team:** Mario Manuel Antizana Ponce de León, Mauricio, Mauricio Sebastián Reátegui, Alessandro, Nicole and Valeria Rosado.

**[Public demo](https://marioantizana1.github.io/Apex-reapers-NASA/)** · **[Documentation](Docs/README.md)** · **[Bibliography](Docs/11_Bibliografia.md)** · **[Workflows, tools and AI disclosure](Docs/25_Workflows_Tools_AI_and_Impact.md)**

The public demo is deployed separately; its features may lag behind the source in this repository.

**Publication scope:** this update publishes documentation, research scripts and source metadata. Descriptions of newer prototype features reflect the local development workspace; its pending application-code changes are not included in this documentation commit. The checked-in application and public demo may therefore expose a smaller feature set.

## Project summary and status

| Area | Current prototype | Important limitation |
|---|---|---|
| 2D exploration | OpenLayers map; orbital imagery, elevation, hillshade, slopes and a contextual traverse overlay; layer visibility, opacity and provenance | Scientific alignment and interpretation still require independent review |
| Mission planning | Hypothetical base, science stops, nearest-neighbour stop ordering and return-to-base estimates | Stop ordering is not globally optimal; the original resource estimates use straight-line segments |
| Terrain routing | Experimental worker-based A* planner, configurable criteria and route display | The routing grid contains assumed terrain indices and height scaling, not validated slope/elevation measurements |
| 3D exploration | Three.js terrain demonstration using a partial HiRISE DTM, local detail, selected base/stops and movement controls | Partial coverage; decorative objects and movement are illustrative |
| Resource display | Configurable oxygen, CO₂ processing-capacity and calorie assumptions | 3D movement meters are independent of the planned 2D mission and reset on entry |
| Research | Source catalog, bibliography, evidence manifests, acquisition and processing scripts | Archived observations are not live conditions; raw data is downloaded separately |

**Planned, not complete:** exportable mission brief, validated science-versus-return route comparison, water/radiation/communications analysis, environmental-data UI, offline/PWA support and bilingual UI. The current application interface is primarily Spanish; the public documentation is English.

See the [solution proposal](Docs/06_Propuesta_Solucion.md) and [traceability matrix](Docs/17_Matriz_de_Trazabilidad.md). A planning document is not evidence that a feature has shipped.

## Why this project could matter

These are **potential benefits**, not measured operational outcomes:

- **Education:** make planetary mapping, mission constraints and Mars science easier to explore.
- **Scientific literacy:** distinguish observations, derived maps and assumptions; show sources and uncertainty alongside the visualization.
- **Planning research:** demonstrate trade-offs between distance, science stops, terrain criteria and return requirements.
- **Reproducibility:** connect each derived asset to its source page, metadata and processing procedure.
- **Collaboration:** give developers, science reviewers and designers a shared map and data contract.

No reduction in astronaut risk, resource consumption or mission cost has been demonstrated. Operational use would require validated data, suit models, human-factors research and expert review. Background: EVA planning literature [S27–S33], terrain planning [S72] and planetary mapping guidance [S50–S51] in the bibliography.

## Tools and architecture

| Purpose | Tools used in the repository |
|---|---|
| Application | React 19, TypeScript, Vite, npm |
| Planetary map and coordinates | OpenLayers, proj4, a documented local Mars projection |
| 3D demonstration | Three.js, local STL models, derived terrain chunks and image tiles |
| Data acquisition and processing | Python, requests, NumPy, rasterio, Pillow, tifffile, pypdf and truststore, depending on the script |
| Testing | Vitest, Playwright, TypeScript build checks and Python integrity checks |
| Collaboration and publication | Git, GitHub and a static GitHub Pages demo |
| AI-assisted work | OpenCode and generative-AI assistance; see disclosure below |

QGIS/GDAL, Zotero, Figma/Penpot and Blender/Krita/GIMP appear in the **proposed team workflow**. Their presence in a plan is not proof that every tool was actually used. React Three Fiber was considered; the current implementation uses Three.js directly.

```text
Official source pages / archives
        → acquire originals + metadata
        → inspect CRS, coverage, dates and usage terms
        → derive web images, terrain and catalogs
        → app/public/ → React + OpenLayers / Three.js
        → tests + scientific review → demonstration + documentation
```

The browser application is static: it needs no backend, login or API key. Acquisition scripts contact external archives; normal map rendering uses packaged assets.

## Run and test

Use a Node.js version supported by Vite 7 (Node.js 22.12+ is a suitable baseline), npm and a modern browser. WebGL is needed for 3D.

```bash
cd app
npm ci
npm run dev
```

Open the local URL printed by Vite.

```bash
# From app/
npm test
npm run build
npx playwright install chromium --only-shell
npm run test:e2e
```

`npm run build` writes `app/dist/`. For a subdirectory deployment, preserve the configured base path or supply the correct Vite `--base` value. See [application procedures](app/README.md).

## Data sources and bibliography

The following links identify **where the data and scientific context came from**, not just general NASA homepages:

| Source / original page | What we use or investigate | Status / caveat |
|---|---|---|
| [NASA/JPL Mars Trek](https://trek.nasa.gov/mars/) and [service catalog](https://trek.nasa.gov/mars/trekarcgis/rest/services?f=pjson) [S14] | Perseverance traverse, waypoints, landing ellipse, exploration ROIs, mineral/geological context and regional MOLA products | Research acquisition and derived contextual overlay; coarse data does not resolve walking hazards |
| [USGS CTX science-investigation products](https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/) and [Mangold et al., 2021](https://doi.org/10.1126/science.abl4051) [S37] | Jezero 5 m/px CTX orthomosaic and 20 m/px DEM; derived color, slope and hillshade images | These regional science products are not the separate CTX TRN product [S77] |
| [USGS HiRISE TRN DTM](https://doi.org/10.5066/P9REJ9JN) [S78] | Individual CR North 1 m DTM and related terrain products | Partial local 3D coverage; USGS documents quality issues with the CR stereo model |
| [USGS HiRISE orthomosaic](https://doi.org/10.5066/P9QJDP48) [S79] | ESP_036618_1985 NORTH imagery at 25 cm/px; derived local tiles/textures | Pixel spacing is not positional accuracy; the same stereo-model caveat applies |
| [PDS Mars 2020 archive](https://pds-geosciences.wustl.edu/missions/mars2020/) [S15] and [PDS MEDA bundle](https://pds-atmospheres.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda/) [S16] | Environmental research sample, sol 1740 | Archived measurements; not a live weather feed or an implemented environmental UI |
| [USGS geologic map SIM 3464](https://doi.org/10.3133/sim3464) [S36] and [Mars mapping hub](https://astrogeology-usgs.hub.arcgis.com/pages/interactive-maps-mars) [S73] | Jezero/Nili Planum geological reference | Citation/context; a preview image is not a georeferenced scientific layer |
| [Mars 2020 raw images](https://mars.nasa.gov/mars2020/multimedia/raw-images/) [S75] | Selected surface-image research and instrument/sol metadata | Visual context, not automatically a map |
| [Perseverance's “Office” on Mars, PIA24765](https://science.nasa.gov/resource/perseverances-office-on-mars/) [S80] | Cropped and mirrored sky illustration in the 3D demo | Mastcam-Z panorama, sol 155, 2021-07-28; NASA/JPL-Caltech/ASU/MSSS; not a view from the simulated location |
| [NASA Technical Reports Server](https://ntrs.nasa.gov/) and [OpenAlex](https://openalex.org/) [S81–S82] | Technical reports and literature discovery | Research references, not terrain measurements |

Key reading: [BASALT EVA planning](https://doi.org/10.1089/ast.2018.1850) [S27], [geospatial/temporal EVA needs](https://doi.org/10.1089/ast.2018.1838) [S28], [Jezero geological mapping](https://doi.org/10.1007/s11214-020-00739-x) [S35], [MEDA instrument](https://doi.org/10.1007/s11214-021-00816-9) [S40] and [USGS planetary mapping protocol](https://doi.org/10.3133/tm11b13) [S50].

The [full bibliography](Docs/11_Bibliografia.md) preserves the source IDs used throughout the dossier. The [data catalog](Docs/03_Fuentes_y_Datos_NASA.md) describes additional research candidates; not every researched mission or instrument is integrated into the app.

### Reproduce the data workflow

Run acquisition and processing commands from the repository root. Python 3.11+ is recommended:

```bash
python -m pip install requests numpy rasterio pillow tifffile pypdf truststore
python Scripts/00_verificar_entorno.py
python Scripts/04_auditar_mars_trek.py
python Scripts/05_descargar_datos_meda.py
python Scripts/08_descargar_jezero_core.py --solo ctx_dem_20m_jezero ctx_ortho_5m_jezero hirise_dem_cr_north
```

Downloads can be large. Review the [script-by-script procedure](Scripts/README.md) before running processing or generating tiles. The original data, incomplete `.part` files, downloaded papers and private conversation history are **not** distributed in Git. Source catalogs, metadata and manifests are retained; reduced application assets are separate from the raw research archive.

The existing evidence manifest describes a **local collection**, not a promise that every listed file is present in a clone. `python Scripts/07_verificar_evidencias.py --check` will report intentionally omitted files until the corresponding data has been restored. See [evidence policy](Evidencias/README.md).

## Generative AI disclosure

**We used generative AI during the project.** AI assistance supported research organization, brainstorming, explanations, code drafting and debugging, test preparation, documentation and English-language editing. OpenCode is the coding-agent environment used for the documented work; this publication session uses OpenAI GPT-6.1 Sol. A complete model/version history for earlier sessions has not been verified.

AI output is **not** a scientific source, a terrain measurement or evidence of validation. Team members remain responsible for reviewing code, checking citations and licenses, interpreting data and approving published claims. Review and external scientific validation are not represented as complete merely because AI assisted the work.

The resource models, decorative 3D objects and terrain-routing assumptions must not be mistaken for NASA-validated operational data. The authorship/license history of custom icons and models still requires confirmation; we do not claim that every asset was AI-generated or team-authored without evidence.

See the [detailed AI disclosure and usage log](Docs/25_Workflows_Tools_AI_and_Impact.md#generative-ai-disclosure).

## Repository guide

```text
README.md        Project overview, benefits, sources and disclosure
Docs/            English research, design, validation and project procedures
Scripts/         Research acquisition, processing and integrity tools
Evidencias/      Evidence policy, source metadata and manifests
app/             Application, automated tests and reduced runtime assets
```

Document filenames retain their original Spanish identifiers to preserve existing links. Public prose is English; original source metadata and the application UI may retain their source language.

## Credits, limitations and next steps

Credit belongs to the original data producers and the works cited in the bibliography, including NASA, JPL-Caltech, USGS, UArizona, ASU, MSSS and ESA/DLR/FU Berlin where applicable. **Public access is not a blanket license:** review the terms of each product and retain its required attribution. NASA or Space Apps participation does not imply NASA endorsement.

The documented project schedule identifies the event as 2026-11-14–2026-11-15, with pre-event work limited to research/planning and application development beginning during the event. These are project records, not a new independent certification of event rules or dates; consult the [official challenge](https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/) and [participant FAQ](https://www.spaceappschallenge.org/resources/participant-faqs/) for authoritative requirements [S01–S03].

Next priorities: independently review geospatial alignment and data/asset rights, replace assumed routing inputs with validated terrain measurements, implement the exportable brief, and evaluate usability before making stronger impact claims.
