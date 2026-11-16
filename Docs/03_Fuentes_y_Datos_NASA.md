# 03. Data sources and acquisition contracts

**Rule:** a dataset does not become an application layer simply because it is downloadable. Retain its mission/instrument, product ID, variable, resolution, date, CRS/body model, coverage, usage terms, processing and limitations.

## Integrated and acquired products

| Product / original source | Mission / instrument | Role | Limitation |
|---|---|---|---|
| [CTX science-investigation collection](https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/) [S37] | MRO / CTX | 5 m/px regional orthomosaic and 20 m/px DEM; reduced imagery, slopes and hillshade | Not the separate TRN CTX release [S77]; resolution is not accuracy |
| [HiRISE TRN DTM release](https://doi.org/10.5066/P9REJ9JN) [S78] | MRO / HiRISE | Individual CR North 1 m DTM for local 3D | Partial coverage, stereo artifacts; CR quality issues documented by USGS |
| [HiRISE image release](https://doi.org/10.5066/P9QJDP48) [S79] | MRO / HiRISE | ESP_036618_1985 NORTH, 25 cm/px; local tiles and texture | Pixel spacing is not positional accuracy; orthorectification uses the stereo model |
| [Mars Trek](https://trek.nasa.gov/mars/) [S14] | Multiple missions / GIS products | Traverse, waypoints, landing ellipse, exploration ROIs, mineral/geological context and regional rasters | Coarse/simplified context is not local hazard certification |
| [MEDA PDS bundle](https://pds-atmospheres.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda/) [S16] | Mars 2020 / MEDA | Archived research sample, sol 1740 | Not real time; not yet an implemented conditions panel |
| [SIM 3464](https://doi.org/10.3133/sim3464) [S36] | USGS geological mapping | Jezero and Nili Planum reference | A preview is not a georeferenced raster layer |
| [Mars 2020 raw images](https://mars.nasa.gov/mars2020/multimedia/raw-images/) [S75] | Perseverance cameras | Selected visual context and instrument/sol metadata | Raw image coordinates cannot be inferred from a screenshot |
| [PIA24765 panorama](https://science.nasa.gov/resource/perseverances-office-on-mars/) [S80] | Perseverance / Mastcam-Z | Cropped/mirrored 3D sky illustration | Sol 155, 2021-07-28; not a view from the simulated site |

## Other research candidates — not all integrated

| Mission / tool | Instrument or product | Research use | Sources |
|---|---|---|---|
| Mars Global Surveyor | MOLA | Regional topography; not walking-scale obstacles | [S14, S71] |
| MRO | CRISM | Hydrated minerals and compositional context | [S47, S61] |
| MRO | MARCI, MCS, SHARAD | Atmospheric context and subsurface research | [S61] |
| Mars Odyssey | THEMIS, GRS/HEND | Thermal context and coarse hydrogen-related research | [S48, S62] |
| Mars Express | HRSC, OMEGA, MARSIS | Regional imagery, mineralogy and subsurface context | [S66] |
| ExoMars TGO | CaSSIS, ACS/NOMAD | Color imagery and atmospheric research | [S67] |
| MAVEN | Atmospheric/plasma instruments | Upper-atmosphere and space-environment context | [S65] |
| Mars 2020 | Mastcam-Z, SuperCam, PIXL/SHERLOC, RIMFAX | Visual, chemical and subsurface science | [S60] |
| Curiosity | REMS, RAD, DAN | Gale environmental/radiation context; not local Jezero measurements | [S41–S43, S64] |
| InSight, Phoenix, Viking, MER | Mission-specific observations | Broader Mars context | [S63, S68–S70] |
| Mars Climate Database | Model climatology | Seasonal/model context, not live observations | [S44, S57] |
| OpenPlanetaryMap, JMARS | Mapping tools | Benchmark and possible analysis tools | [S55–S56] |

Instrument resolution depends on the actual product and mode. Do not substitute an instrument's best nominal resolution for a dataset's metadata.

## Mars Trek endpoints

Base: `https://trek.nasa.gov/mars/`.

| Resource | Path relative to base |
|---|---|
| Configuration | `jpl/config/config.json` |
| Basemaps | `jpl/config/basemapList.json` |
| Static layers | `jpl/config/staticLayers.json` |
| Service directory | `trekarcgis/rest/services?f=pjson` |
| Traverse | `trekarcgis/rest/services/Perseverance_Traverse_Path/MapServer/0` |
| Waypoints | `trekarcgis/rest/services/mars2020_waypoints/MapServer/0` |
| Landing ellipse | `trekarcgis/rest/services/perseverance_landing_ellipse/MapServer/0` |
| Human exploration ROI | `trekarcgis/rest/services/EZMars/MapServer/3` |
| Hydrous minerals | `trekarcgis/rest/services/Hydrous_Mineral_Detections_OMEGA_CRISM_clon0/MapServer/0` |
| Global geology | `trekarcgis/rest/services/SIM3292_Global_Geology/MapServer/0` |
| Regional elevation | `trekarcgis/rest/services/mola128_mola64_merge_90Nto90S_SimpleC_clon0/ImageServer` |

The initial audit recorded 76 services and eight downloaded Jezero vector collections. Counts describe that snapshot, not a current service guarantee. Requests, status and outputs are recorded in `Evidencias/datos/mars_trek/`.

## PDS environmental sample

Use [Mars 2020 archive](https://pds-geosciences.wustl.edu/missions/mars2020/) [S15] and the MEDA bundle [S16]. The selected sol 1740 sample contains:

| Product token | Variable |
|---|---|
| `DER_PS` | Pressure |
| `CAL_ATS` | Air-temperature channels |
| `CAL_RHS` | Relative humidity |
| `CAL_RDS` | Radiation/dust sensor channels |
| `DER_TIRS` | Thermal infrared measurements |
| `DER_ANCILLARY` | Position/orientation and solar geometry |

Check labels, flags, units, no-data and channel definitions before computing statistics. Do not reinterpret humidity as available water or every RDS channel as a direct dust-concentration measurement.

## Resource audit decisions

| Resource | Decision |
|---|---|
| Mars Trek [S14] | Appropriate research source for Mars context, subject to product checks |
| USGS Mars mapping hub [S73] | Reference cards and source discovery; verify actual geospatial files |
| Curiosity's proposed Mount Sharp path [S74] | Visual analogy in **Gale**, not Jezero data |
| NASA Worldview [S76] | Earth-observation viewer; not a Mars layer source |
| Mars 2020 raw images [S75] | Visual context, not automatically georeferenced map content |

## Data workflow

```text
Original archive → selective download → completeness + labels
  → CRS/units/coverage/rights inspection
  → documented derivatives → app catalog → alignment/science review
```

Follow [Scripts/README.md](../Scripts/README.md). Keep originals unchanged and partial files out of validated evidence. Use the data card in [13](13_Checklist_y_Plantillas.md). Actual application metadata lives in `app/public/layers.json`.

## Known gaps

- No validated human-scale obstacle inventory or suit-performance model.
- No implemented relay ephemerides or localized radiation model.
- Archived conditions do not constitute a live weather API.
- Spectral detections do not establish abundance or accessible resources.
- Different products can use different datums, latitude conventions and vertical references.
- Independent alignment, scientific interpretation and rights review remain necessary.

Source catalogs and manifests are published; raw originals are omitted under the [evidence policy](../Evidencias/README.md). Consult product-specific terms rather than assuming all NASA-associated material has identical rights.
