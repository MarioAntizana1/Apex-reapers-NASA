# 19. Shared 2D and 3D design

## Intent

Provide one coherent exploration workflow: the map establishes location and context; a supported local terrain view makes relief easier to explore. Both should use the same base and stops, without claiming that 3D visualization proves route safety.

## Technology choices

- React/TypeScript/Vite for application state and build.
- OpenLayers/proj4 for the map and explicit planetary projection.
- Three.js directly for the implemented scene. React Three Fiber was considered, not adopted as a dependency.
- Static local assets for predictable delivery; no application backend required.

Alternatives considered in earlier planning included simpler image-only mapping or globe-oriented tools. The focused Jezero case favors explicit local coordinates and a small terrain area.

## Shared data contract

| Item | Required agreement |
|---|---|
| Coordinates | Local projected metres; named Mars body model/projection; no implicit Earth WGS84 |
| Heights | Units, vertical reference, no-data and any scaling |
| Extent | Actual coverage and handling outside it |
| Base/stops | Shared state with a hypothetical-location label |
| Route | Same endpoints/order; distinguish straight segments, A* path and 3D direction indicator |
| Scientific metadata | Product/source, observation date, resolution, terms and limits |
| Assets | Format, scale, orientation, origin and authorship/rights |

The actual projection definition is in [app/README.md](../app/README.md#shared-coordinates). Compatibility with every original product must be checked rather than assumed.

## Current limits

The scene requires the selected base to lie in a complete local terrain chunk and warns about stops beyond coverage. Its direction indicator is a straight-line guide to the next stop, not obstacle-aware navigation. Decorative rocks, astronaut and rocket are illustrative.

The experimental routing grid is separate from HiRISE geometry and contains assumptions. Resource estimates remain independent of terrain-route length.

## Interaction and performance

Use clear controls, visible loading/error/no-data states, a recoverable camera and a reliable exit back to 2D. Load high-resolution detail locally rather than treating the entire region as full detail. Benchmark a defined device before advertising performance.

Decoration and advanced effects follow core correctness. If WebGL or terrain fails, preserve the 2D workflow. See [21 — Tests and contingency](21_Pruebas_y_Contingencia_3D.md).
