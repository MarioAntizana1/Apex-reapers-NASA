# 06. Solution proposal and implementation boundaries

**Vision:** turn orbital and rover context into an understandable Marswalk planning discussion: destination, science, constraints and return.

This document contains the **product proposal**, not a claim that the complete MVP has shipped. Current procedures are in [app/README.md](../app/README.md).

## Personas and jobs

| Persona | Main question |
|---|---|
| EVA commander / astronaut, conceptual use | Can this plan fit the constraints and include a return? |
| Mission planner / researcher | How do alternatives change distance, timing and assumptions? |
| Planetary scientist | What supports this location's scientific interpretation? |
| Educator / public user | What can this map teach without hiding uncertainty? |

Real operational deployment is outside the prototype's validated scope.

## Intended modes

- **Explorer:** inspect layers, source cards, science context and uncertainty.
- **Survival:** compare route, timing, resources and return assumptions.
- **Mission Brief:** export a traceable plan, parameters, sources and limitations.
- **Mission/Game and Analyst modes:** optional future concepts, not required for the core delivery.

## Intended user flow

```text
Open Jezero → inspect sources → set hypothetical base
  → add science stops → compare plan and return constraints
  → inspect terrain/conditions → export a brief
```

The implemented flow currently stops short of the complete validated comparison/brief workflow.

## Current prototype

| Implemented component | Boundary |
|---|---|
| 2D map, visibility/opacity and provenance | Actual scientific alignment still needs independent review |
| Base and stops | Hypothetical planning locations, not a known habitat or certified site |
| Nearest-neighbour ordering and return-to-base estimates | Heuristic, not globally optimal; resource estimates use straight-line legs |
| Worker-based A* terrain routing | Image-derived terrain indices and assumed relief; separate from resource estimates |
| Partial HiRISE 3D | Visual demonstration with coverage restrictions; not obstacle-aware navigation |
| Resource displays | Configurable illustrative assumptions; no suit telemetry |

## Proposed MVP — not all complete

- Jezero map with 8–10 well-documented layers.
- Editable route and elevation profile.
- Distinct return-focused and science-focused alternatives with defensible return constraints.
- Distance, time, oxygen, water, energy, dose and communication information.
- Explained risk/turn-around indicators.
- Dated environmental information, showing sol and source.
- Exportable mission brief.
- Source cards and English/Spanish interface.

The current catalog has fewer layers than this target. Water, radiation, communications, environmental UI, offline support, bilingual UI and brief export must not be advertised as delivered.

## Scientific layer concept

Base/context: CTX/HiRISE imagery, regional topography, nomenclature and geology [S14, S35–S37, S78–S79].

Science: traverse, waypoints, exploration ROIs and supported mineral interpretations [S14, S17, S39, S47].

Constraints: validated local slopes, dated environmental observations and defensible resource models. MEDA research data is archived, not live [S16, S40]. RAD measurements at Gale are not local Jezero dosimetry [S42–S43].

A “science score” would be a project-defined heuristic, not objective scientific value; publish criteria and uncertainty before introducing one.

## Resource and return models

Planned calculations would combine route length, speed, slope, science dwell time, consumable rates, reserve and return requirements. Every unvalidated coefficient is an **ASSUMPTION**.

Actual current constants are documented in the application guide. The straight-line estimator, experimental A* route and 3D movement meters are separate calculations. They must not be conflated.

## Architecture and contracts

```text
Python acquisition/processing → metadata + reduced local assets
                                 ↓
React state → OpenLayers map / route worker / Three.js demonstration
                                 ↓
                         UI + provenance + tests
```

Stack: React, TypeScript, Vite, OpenLayers, proj4 and Three.js; static assets, no required application backend. CSS is maintained locally. Vitest and Playwright cover software behavior.

Current `layers.json` is an image catalog validated by `app/src/layers.ts`. Proposed `route.json` and `brief.json` are design concepts, not existing exported formats or APIs.

## Accessibility, offline and security

Provide labelled controls, visible focus, understandable errors and explanations that do not depend on color alone. Preserve the 2D experience if WebGL or terrain loading fails. Avoid terrestrial projections/basemaps for Mars by accident.

Offline/PWA support is a roadmap item, not guaranteed by packaging assets locally. Do not embed secrets or arbitrary remote executable content.

## Scope discipline

Do not prioritize a global immersive globe, live weather, generative chat assistant, multi-site mission logistics or realistic suit physics over a traceable core and brief. Link every feature to [R1–R8](17_Matriz_de_Trazabilidad.md), and distinguish software checks from scientific validation.
