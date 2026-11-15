# Apex-Mars — application shell

Team: **Apex-Reapers**. Apex-Mars is the provisional application name;
earlier research documents use the working name Ares Atlas.

React + TypeScript + Vite + OpenLayers. This first delivery is a 2D shell;
resources are configured in `public/layers.json`. The 3D button is intentionally
disabled. This is not the complete hackathon MVP.

## Run

From `app/`:

```bash
npm ci
npm run dev
```

Open the local address printed by Vite.

```bash
npm test
npx playwright install chromium --only-shell
npm run test:e2e
npm run build
```

`dist/` is the static deployment output. No backend or API key is needed.

## Add NASA images

1. Download and check the source, usage terms, coverage and CRS.
2. Place browser-friendly PNG/JPEG/WebP images in `public/maps/`.
3. Reproject them to the shared CRS described below **before** configuring
   their bounds. The viewer does not infer georeferencing or convert an
   arbitrary screenshot into a map.
4. Add their metadata to `public/layers.json`. Array order is rendering order:
   later images appear above earlier images.

```json
{
  "layers": [
    {
      "id": "orbital",
      "name": "Nombre de la capa",
      "url": "maps/imagen.png",
      "extent": [-100, -100, 100, 100],
      "source": "https://science.nasa.gov/",
      "description": "Descripción revisada por el equipo.",
      "mission": "Completar con la misión",
      "instrument": "Completar con el instrumento",
      "resolution": "Completar",
      "date": "Completar",
      "license": "Completar con las condiciones verificadas",
      "limitations": "Completar con cobertura, incertidumbre y limitaciones"
    }
  ]
}
```

**This is a schema example, not a scientific layer.** The bounds are arbitrary
test values and the source URL is not the source of an actual image.
Replace all values with verified metadata; do not activate this example.

The catalog validates complete fields, unique identifiers, finite bounds,
relative local image URLs, and HTTPS provenance links. This structural check
does **not** verify scientific accuracy, licensing or actual georeferencing.
Image load failures appear next to the layer.

## Route planner — shortest path over terrain

`src/routing/` adds planning on top of the 2D map: the user places waypoints and
an A\* search returns the cheapest traverse across the CTX slope grid instead of
the straight line.

- `scripts/build_slope_index.py` converts `public/maps/jezero_ctx_dem_20m_slope.jpg`
  into `public/terrain/slope_index_60m.png` (one byte per ~60 m cell) plus
  `public/terrain/slope_index.json` (extent, resolution, assumptions). Run it
  from `app/` with `python scripts/build_slope_index.py`.
- `src/routing/terrain.ts` loads and decodes that grid in the browser.
- `src/routing/planner.ts` is the planner: A\* over 8 neighbours without cutting
  diagonal corners, cell cost `1 + penalty · (index/255)²`, cells above the
  tolerance are impassable, Douglas–Peucker plus Chaikin smooth the trace.
- `src/routing/worker.ts` runs the search in a Web Worker and
  `useRoutePlanner.ts` owns the state and debounces slider changes, so the map
  stays responsive.
- 0 in the index is smooth terrain, 255 the strongest tone of the source ramp.
  **Relative values, not validated degrees**: the source layer has no numeric
  legend and there is no vertical datum.

Panel figures (distance, detour, max index, cost per metre, cells explored) come
from the same grid, so they match the drawn line — they are not a rover traverse
simulation: no rocks, energy model, communications or slope-limit validation.
Unit tests live in `src/routing/*.test.ts`, browser tests in `tests/route.spec.ts`.

## Shared coordinates — initial assumption

`MARS:JEZERO` in `src/MapView.tsx` is a local spherical equirectangular
projection, with metres, east-positive longitude, spherical latitude,
radius 3,396,190 m, longitude origin 77.45°, latitude origin and standard
parallel 18.45°. Its PROJ definition is:

```text
+proj=eqc +lat_ts=18.45 +lat_0=18.45 +lon_0=77.45 +R=3396190 +units=m +no_defs
```

**SUPUESTO:** these are initial cartographic parameters, not a claim that
all NASA resources use this CRS. Verify the original body model and latitude
convention and transform the actual assets before integrating them.
`extent` is `[xmin, ymin, xmax, ymax]` in this projected CRS, not longitude
and latitude. The empty viewer has no validated geographic coverage.

For 3D, a DEM with documented vertical units, reference, coverage and NoData
handling is still needed. A color image or slope map does not replace it.

## Layout

- `src/App.tsx`: layer controls, route panel and metadata.
- `src/MapView.tsx`: OpenLayers map, image lifecycle and route drawing.
- `src/layers.ts`: catalog contract and validation.
- `src/routing/`: terrain grid, A\* planner, worker and React hook.
- `scripts/build_slope_index.py`: builds `public/terrain/` from the slope layer.
- `public/layers.json`: resource catalog, populated by the data pipeline.
- `tests/`: browser tests using synthetic resources only.

Limits: Spanish UI only for this delivery; scientific POIs, EVA, brief, offline
cache and 3D are not implemented. No external font, terrestrial basemap or
runtime image service is required.
