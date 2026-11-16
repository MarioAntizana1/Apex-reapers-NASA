# Apex-Mars

**Explore Jezero Crater, one layer at a time.**

Apex-Mars is an educational exploration and planning prototype by **Apex-Reapers** for NASA Space Apps 2026. It connects orbital imagery, topography, scientific context and explicit planning assumptions.

**[Public demo](https://marioantizana1.github.io/Apex-reapers-NASA/)** · **[Full project README](../README.md)** · **[English documentation](../Docs/README.md)** · **[Bibliography](../Docs/11_Bibliografia.md)**

## Prototype and potential benefits

Explore a layered 2D map, inspect provenance, place a hypothetical base and science stops, review illustrative resource estimates and experiment with terrain routing and partial 3D exploration. Deployment may lag behind repository source.

Potential benefits include accessible Mars education, clearer scientific provenance, reproducible data workflows and discussion of planning trade-offs. These are proposed benefits, not measured mission-safety or cost improvements.

**Not navigation, life support or a validated EVA simulator.** Routing inputs and resource rates include assumptions; coverage and scientific/rights review are incomplete. Brief export, full environmental analysis and other roadmap items are not all implemented.

## Tools and workflow

React, TypeScript, Vite, OpenLayers, proj4 and Three.js; Python data tools; Vitest and Playwright; Git/GitHub and static hosting.

```text
Original archives → acquisition and metadata → inspected derivatives
  → map / experimental route / 3D → tests and review → documentation
```

See [procedures](../Scripts/README.md) and [detailed workflows/tools](../Docs/25_Workflows_Tools_AI_and_Impact.md).

## Original data pages

- [NASA/JPL Mars Trek](https://trek.nasa.gov/mars/).
- [USGS CTX science-investigation products](https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/).
- [USGS HiRISE DTM](https://doi.org/10.5066/P9REJ9JN) and [orthomosaic](https://doi.org/10.5066/P9QJDP48).
- [NASA PDS MEDA archive](https://pds-atmospheres.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda/) — research sample, not live conditions.
- [USGS Jezero geological map](https://doi.org/10.3133/sim3464).
- [NASA PIA24765 panorama](https://science.nasa.gov/resource/perseverances-office-on-mars/) — credited, cropped/mirrored illustrative sky.

Full citations, distinctions between integrated/research-only data and product-specific cautions are in the [root README](../README.md) and [bibliography](../Docs/11_Bibliografia.md). Raw large data is omitted; catalogs, manifests and reproduction procedures are provided.

## Generative AI disclosure

We used generative AI for research organization, planning, explanations, code/debugging/test assistance and documentation/English editing. AI is not a scientific source. Humans remain responsible for review, citation, interpretation and publication; complete historical model and visual-asset provenance is not established.

Read the [detailed disclosure](../Docs/25_Workflows_Tools_AI_and_Impact.md#generative-ai-disclosure).

## Run locally

```bash
cd app
npm ci
npm run dev
```

See [app/README.md](../app/README.md) for prerequisites, testing, coordinates, resource assumptions and deployment procedures.
