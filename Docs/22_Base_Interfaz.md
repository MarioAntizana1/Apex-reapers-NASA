# 22. Initial interface delivery

**Historical approval:** 2026-11-14, short design approved in conversation. **Identity:** Apex-Reapers / Apex-Mars; Ares Atlas is the earlier working name.

This describes the **first delivery**, not the latest complete application. Later source includes mission interaction, experimental routing and 3D.

## Intent and scope

Create a 2D shell ready to receive NASA resources: map, layer controls and source information, without fabricating scientific data. Keep application code in `app/`, separate from research scripts.

## Approaches

- **Selected:** React/TypeScript/Vite and OpenLayers first. Integrate real imagery before terrain.
- **Deferred initially:** simultaneous 2D/3D, because elevation, coverage and shared coordinates needed checking.

## Approved initial design

Header with identity/site/view selector; layer sidebar; map zoom/pan/reset; selected-layer metadata, visibility and opacity. Show an explicit empty state without assets. At this initial stage, 3D was disabled with an explanation.

Implementation choices: local CSS, JSON image catalog with shared projected extents and structural validation, local files under `app/public/`. An ungeoreferenced image must not become a measured map by assigning arbitrary bounds.

Initial scope excluded routes, EVA calculations, brief, upload UI, unsupported POIs and terrain. This initial exclusion is not a statement that every later feature remains absent.

## Acceptance plan

1. Configure app and tests.
2. Check catalog fields, duplicate IDs, coordinate bounds and URL rules.
3. Implement map/controls, source cards and empty/error states.
4. Verify tests, TypeScript/Vite build and browser interaction.

Initial evidence supports partial R1/R2/R3/R7 only. Structural checks and synthetic UI fixtures do not establish scientific validity or completion of D01–D08.
