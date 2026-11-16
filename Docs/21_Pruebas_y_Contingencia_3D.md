# 21. 3D testing and contingency

**Status:** proposed acceptance and fallback plan. Measured results require a recorded environment and execution; none are implied by listing these cases.

## Minimum checks

| Area | Cases | Acceptance |
|---|---|---|
| Data | Control points, CRS, units, vertical reference, coverage and no-data | Differences explained within a product-appropriate tolerance |
| Science | Mineral/POI claims and uncertainty | Source-backed; no interpretation beyond evidence |
| Routes | Flat terrain, barrier, blocked endpoint, same endpoint, outside/unreachable destination | Consistent graph result or explicit rejection; no invented traversable connection |
| Conversions | Known coordinates and round trip | Correct units and agreed numerical tolerance |
| 2D/3D correspondence | Base, stops, direction and height reference | Same intended locations; representations clearly distinguished |
| Camera | Slopes, edges, missing terrain, reset and exit | Recoverable controls; unsupported coverage handled visibly |
| Route display | Relief, light and surface overlap | Visible route/markers without unexplained displacement |
| Usability | New user opens layers, creates stops, enters/exits 3D | Task outcome and misunderstandings recorded |
| Accessibility | Keyboard, focus, contrast and pointer-lock exit | No focus trap; information not color-only |
| Performance | Initial load, scene entry, movement and decoration | Measured on a defined device, not guessed |
| Graphics failures | No WebGL or terrain-load error | Explain failure and preserve 2D |
| Integration | Open → layers → plan → 3D → 2D | Shared selection preserved without blocking errors |

## Performance assumptions

The original 3D plan used **30 sustained FPS** as a provisional target, not a measured result. Record CPU/GPU/RAM, operating system, browser, viewport, asset version and scenario before comparing measurements.

Terrain size, detail, load time and asset-weight budgets need measurement. Do not infer runtime performance from a successful build.

## Handoff/fallback levels

| Level | Deliverable | Responsibility |
|---|---|---|
| A — intended | Free local exploration, terrain and clear route/stop context | Proposed 3D owner with Mario integrating |
| B — handoff | Minimal viewer without additional effects/decoration | Mario with assistance and existing design/assets |
| C — scope reduction | Orbital or guided view if free movement threatens delivery | Team decision with visible limitation |
| D — base delivery | 2D map and available terrain/profile context; mark 3D pending | Team preserves core workflow |

Trigger a fallback when ownership/availability or the first integration milestone is missed. Do not block map/data/science work waiting indefinitely for 3D.

## Definition of done

Supported coverage is explicit, controls recover, source/assumptions are visible, failures do not destroy the 2D flow and test results are recorded. Decorative polish is optional. The existing demonstration remains illustrative, not a validated EVA simulator.
