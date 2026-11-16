# 20. Team objectives, deliverables and tools

**Historical proposal date:** 2026-11-14. Individual availability and acceptance were not fully confirmed. These are proposed assignments, not proof of every person's completed contribution or actual tool use.

| Person | Objective and deliverable | Proposed tools | Acceptance criterion |
|---|---|---|---|
| Mario | Integrate app, routes, shared state, tests and publication | Editor, Node.js, Git, React, TypeScript, Vite, OpenLayers, proj4, Vitest, Playwright | A coherent supported flow; explain route criteria and limits |
| Mauricio | Prepare aligned imagery/elevation and documented layers | QGIS, GDAL if needed, catalog table | Usable reduced files with CRS, units, bounds, resolution, no-data, source and rights |
| Alessandro | Review mineralogy, geological explanations and science POIs | QGIS, Zotero or Markdown/reference table | Claims and confidence match cited evidence; detection is not overinterpreted |
| Nicole | UX, visual direction, transitions, error/empty states and accessibility | Figma or Penpot, choice unconfirmed | A new user can follow the core flow without constant coaching |
| Valeria | Lightweight visual assets, provenance and usability findings | Blender, Krita/GIMP and browser | Assets have scale/orientation/rights records; reproducible usability issues logged |
| Mauricio Sebastián | Proposed local 3D viewer and route correspondence | Editor, Three.js, browser profiling; React Three Fiber was only considered | Supported terrain exploration, recoverable controls and shared base/stops |

Nicole/Valeria emphasis could be exchanged by preference. Earlier roles emphasized Mauricio Sebastián's QA/data validation; confirm the actual handoff rather than treating conflicting plans as completed staffing.

## Detailed delivery rules

- **Data:** configure Mars explicitly; do not accept terrestrial distance/projection defaults without review.
- **Science:** each POI/claim has a source, interpretation boundary and review status.
- **Design:** cozy visual direction must not hide critical scientific information or rely only on color.
- **Assets:** decorative rocks are not measured obstacles; confirm license or authorship.
- **3D:** first load terrain and shared markers, then movement/route visibility, then optional decoration.
- **Integration:** do not require realistic physics, inventory or individually colliding rocks for the initial flow.

## Sequence

1. Agree on selected area, data and coordinate/height/route contracts.
2. Integrate a small map and terrain sample.
3. Share base/stops and distinguish each route representation.
4. Test loading, limits, controls, sources and fallback.
5. Polish only after critical issues are resolved.

Use Git/GitHub for reviewable changes, bounded tasks and acceptance criteria. Keep large raw working files outside ordinary Git commits. If the 3D owner cannot deliver the first milestone, apply [21 — Contingency](21_Pruebas_y_Contingencia_3D.md).

The [confirmed-versus-proposed inventory](25_Workflows_Tools_AI_and_Impact.md#tool-inventory-confirmed-versus-proposed) avoids presenting suggested tools as verified usage.
