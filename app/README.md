# Apex-Mars — application procedures

**Team:** Apex-Reapers. **Earlier working name:** Ares Atlas.

React + TypeScript + Vite + OpenLayers + proj4, with an experimental Three.js terrain view. This is an educational/research prototype, **not a navigation, life-support or validated EVA system**.

See the [project summary](../README.md), [documentation](../Docs/README.md) and [AI disclosure](../Docs/25_Workflows_Tools_AI_and_Impact.md#generative-ai-disclosure).

This guide records the current development workspace. The documentation publication does not include pending application-code changes; a fresh clone or the public demo can have fewer features. The recorded tests/build below were run on that local workspace, not a clean checkout of the documentation commit.

## Run, test and build

Use a Node.js version supported by Vite 7; Node.js 22.12+ is a suitable baseline. From `app/`:

```bash
npm ci
npm run dev
```

Open the URL printed by Vite.

```bash
npm test
npm run build
npx playwright install chromium --only-shell
npm run test:e2e
```

The Playwright configuration uses `http://127.0.0.1:5173`, starts Vite if needed and may reuse an existing server outside CI. Confirm that a reused server belongs to this app before interpreting results.

`dist/` is static build output. No backend, login or API key is required. WebGL is needed for 3D. Large-bundle warnings are performance concerns, not scientific-validation failures.

## Deployment

The repository's source branch is `master`, not `main`. A separate `gh-pages` branch exists for the public demo. Publishing source/documentation to `master` does not prove that the deployed site changed.

Vite currently uses `base: './'`. For another hosting layout, verify the base path, image/worker URLs, direct page load and application behavior before publication. Do not overwrite the deployment branch merely to publish documentation.

## Implemented interaction and limitations

- Inspect layers and their source cards; toggle visibility and opacity.
- Choose a hypothetical base and science stops.
- Review nearest-neighbour stop ordering, return-to-base distance and illustrative resource estimates.
- Inspect a separate worker-based experimental terrain route.
- Explore 3D within complete local terrain coverage; the base/stops come from 2D.

The interface is primarily Spanish. Brief export, validated science/return alternatives, environmental-data UI, water/radiation/communications models, bilingual UI and offline support remain incomplete.

### Planning calculations

`src/mission.ts` orders stops with a nearest-neighbour heuristic, adds return to base and uses straight-line horizontal distances. It is not globally optimal or terrain-aware.

Current **ASSUMPTIONS**:

| Parameter | Value |
|---|---|
| Walking speed | 2 km/h |
| Walking energy | 300 kcal/h |
| Science-stop energy | 200 kcal/h |
| Walking oxygen | 0.8 L/min |
| Science-stop oxygen | 0.5 L/min |
| Walking CO₂ | 0.65 L/min |
| Science-stop CO₂ | 0.4 L/min |
| Oxygen reserve factor | 1.3 |

User-configured limits do not represent validated suit performance. CO₂ is treated as configured processing capacity, not as evidence of an actual scrubber design.

The experimental A* route does **not** replace these straight-line resource calculations. Its image-derived slope indices and assumed 2,000 m relief are not measured slope/elevation. See [routing integration](INTEGRACION_RUTAS.md).

### 3D demonstration

The scene uses partial CR North HiRISE terrain: complete 256 m chunks at 8 m overview spacing, with local 1 m height detail and 25 cm imagery where available. Incomplete chunks are excluded. Heights encoded at 0.1 m intervals are not accurate to 0.1 m by virtue of that encoding.

The base must lie within supported complete terrain. Stops outside it are warned about. The direction arrow and distance are straight-line horizontal guidance to the next stop, not safe routing or the A* path length.

The astronaut, rocket and randomly placed decorative rocks are illustrative. Movement, jumps and trails are not validated EVA dynamics or an observed obstacle inventory.

Resource meters reset to configured limits whenever the scene opens and track movement independently from the 2D mission. Defaults: 0.8 L O₂/min, 0.65 L CO₂/min and 300 kcal/h walking, multiplied by 2 while sprinting; each jump adds 4 walking-equivalent seconds. Rates are editable. Movement remains possible at zero: no safety decision is implied.

## Add or update scientific image layers

1. Obtain the original product and inspect source, rights, CRS/body model, units, date, resolution and coverage.
2. Preserve the original outside the runtime asset directory.
3. Reproject actual georeferenced data into the shared app CRS **before** calculating bounds.
4. Export a browser-friendly PNG/JPEG/WebP under `public/maps/`.
5. Add complete metadata to `public/layers.json`; later entries render above earlier entries.
6. Check alignment independently and expose uncertainty/coverage limits.

```json
{
  "layers": [
    {
      "id": "example-only",
      "name": "Replace with reviewed layer name",
      "url": "maps/replace-with-real-image.png",
      "extent": [-100, -100, 100, 100],
      "source": "https://science.nasa.gov/",
      "description": "Replace with reviewed description",
      "mission": "Replace with actual mission",
      "instrument": "Replace with actual instrument",
      "resolution": "Replace with product resolution",
      "date": "Replace with observation/product date",
      "license": "Replace with verified usage terms",
      "limitations": "Replace with coverage, uncertainty and processing limits"
    }
  ]
}
```

**Schema example only:** the bounds are arbitrary test values and the NASA URL is not provenance for a real image. Do not activate this entry without replacing every value.

The catalog checks complete fields, unique IDs, finite extents, local relative image URLs and HTTPS provenance links. It does not verify scientific accuracy, licensing or georeferencing. Image-load failures are displayed rather than replaced with fictitious data.

## Shared coordinates

`MARS:JEZERO` is the local spherical equirectangular projection defined in `src/MapView.tsx`: metres, east-positive longitude, spherical latitude, radius 3,396,190 m, longitude origin 77.45°, latitude origin/standard parallel 18.45°.

```text
+proj=eqc +lat_ts=18.45 +lat_0=18.45 +lon_0=77.45 +R=3396190 +units=m +no_defs
```

**ASSUMPTION:** these are the app's cartographic parameters, not proof that every NASA/USGS product uses the same CRS. Inspect original body model, latitude convention and vertical reference, then transform the data.

`extent` means `[xmin, ymin, xmax, ymax]` in local projected metres, not longitude/latitude.

## Data preparation and attribution

| Asset | Original source and caution |
|---|---|
| Regional CTX images/topography | [USGS science-investigation collection](https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/); [Mangold et al., 2021](https://doi.org/10.1126/science.abl4051) |
| Local DTM | [USGS HiRISE TRN release](https://doi.org/10.5066/P9REJ9JN); preserve the documented CR stereo-model quality warning |
| Local HiRISE tiles | [USGS orthomosaic release](https://doi.org/10.5066/P9QJDP48); MRO/HiRISE ESP_036618_1985 NORTH; acquisition recorded as 2014-05-19, 25 cm/px; NASA/JPL-Caltech/UArizona |
| Context overlay | [NASA/JPL Mars Trek](https://trek.nasa.gov/mars/); simplified contextual information |
| Sky illustration | [PIA24765](https://science.nasa.gov/resource/perseverances-office-on-mars/), Mastcam-Z, sol 155, 2021-07-28; NASA/JPL-Caltech/ASU/MSSS; cropped/mirrored and not a view from this simulated site |

Sky source: `Evidencias/datos/jezero/prensa/PIA24765-Figure1-web.jpg`; recorded SHA-256 `e0a3b178d6be908c0308fbe2b5f136aed210bfde0610c406724eb1e2c0c077b1`.

The local HiRISE tile square is 10 km wide, centered on X −13823, Y 8996 m. Detail appears below 8 m/pixel within coverage. Missing areas are transparent; imagery does not guarantee terrain coverage at every selected base.

Generate data with scripts 12–16 only after following [Scripts/README.md](../Scripts/README.md). Scripts 14–16 require fresh output directories and will refuse to overwrite packaged assets. Regenerate in a separate workspace rather than deleting originals.

Review product-specific terms. Custom icon/model authorship and rights are not fully inventoried; do not infer NASA provenance or unrestricted reuse from their presence.

## Source layout

| Path | Responsibility |
|---|---|
| `src/App.tsx` | UI, base/stops, resource settings and shared state |
| `src/MapView.tsx` | Map, projection and image lifecycle |
| `src/layers.ts` | Image-catalog contract |
| `src/mission.ts`, `simulation.ts` | Illustrative planning/movement calculations |
| `src/routing/` | Worker-based experimental planner and tests |
| `src/Terrain3D.tsx`, `terrain.ts`, `hirise.ts` | Scene, coverage and local detail |
| `public/layers.json` | Current layer metadata |
| `scripts/` | Experimental image-derived routing-grid preparation |
| `tests/` | Browser scenarios and controlled fixtures |

## Publication checks recorded on 2026-11-15

`npm test`: **7 files / 50 tests passed**. `npm run build`: **passed**, with a warning about JavaScript chunks above 500 kB. Browser-suite results are recorded separately when executed. These are software checks, not independent data/science validation or proof of the deployed version.
