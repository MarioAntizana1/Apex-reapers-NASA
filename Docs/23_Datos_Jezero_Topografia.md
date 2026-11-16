# 23. Jezero imagery and topography

**Edition:** 2026-11-15. The collection is partial, not exhaustive. Original large downloads remain outside Git; `.part` files are incomplete regardless of their apparent size.

## Products and provenance

| Product | Mission / instrument | Native spacing / role | Original reference | Limitations |
|---|---|---|---|---|
| Regional CTX DEM | MRO / CTX | 20 m/px, regional elevation | [USGS science-investigation collection](https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/), [S37] | Seams, smoothing and stereo artifacts; not walking-hazard certification |
| Regional CTX orthomosaic | MRO / CTX | 5 m/px, regional imagery | Same collection, [S37] | Reduced for web; illumination differences/seams |
| Individual CR North DTM | MRO / HiRISE | 1 m/px, local 3D terrain | https://doi.org/10.5066/P9REJ9JN [S78] | Partial coverage and documented CR stereo-model quality issues |
| ESP_036618_1985 NORTH orthophoto | MRO / HiRISE | 25 cm/px, local tiles/texture | https://doi.org/10.5066/P9QJDP48 [S79] | Source acquisition recorded as 2014-05-19; model/orthorectification caveats; pixel size ≠ accuracy |
| Surface-image sample | Mars 2020 / multiple cameras | Visual context by camera/sol | Raw-image catalog [S75] | Selected sample, not a full archive or map layer |
| HiRISE browse images | MRO / HiRISE | Preview/discovery | Mission/archive context [S61] | Not substitutes for scientific originals |

The regional CTX science products are **not** the CTX TRN DTM identified by DOI `10.5066/P906QQT8` [S77]. Similarly, the partial individual HiRISE model used locally is not proof that the whole HiRISE mosaic finished downloading.

## Local originals and derivatives

- CTX originals: `Evidencias/datos/jezero/topografia/M20_JezeroCrater_CTXDEM_20m.tif` and `orbital/M20_JezeroCrater_CTXortho_mosaic_5m.tif`.
- HiRISE terrain: `topografia/hirise_individual/DTM_Jezero_CR_NORTH_1m.tif`.
- HiRISE orthophoto: `orbital/ESP_036618_1985_NORTH_25cm.tif`.
- PDS labels and source catalogs: Jezero `metadatos/`, `catalogo_core.json` and acquisition manifests.
- Application copies: `app/public/maps/`, `terrain-3d/`, `terrain-3d-detail/`.

Scripts 12–13 derive CTX slope/hillshade, images and profiles. Script 14 makes local HiRISE tiles; 15–16 derive 8 m overview chunks and 1 m detail. Stored 0.1 m height quantization is not an accuracy claim.

Hillshade is synthetic illumination; elevation color is a visualization. Decorative rocks are not measured obstacles. Image-derived routing indices and assumed relief are a **different model** from these scientific terrain products.

## Coordinates, quality and rights

Original product labels document cartographic references; the app's local spherical projection is described in [app/README.md](../app/README.md#shared-coordinates). Check actual transforms and extents independently; do not assume all equirectangular products share an origin or vertical datum.

Keep originals unchanged. Inspect coverage/no-data, quality warnings and product-specific usage terms. A local checksum supports integrity comparisons, not authenticity without an independent reference.

See [script procedures](../Scripts/README.md), [data catalog](03_Fuentes_y_Datos_NASA.md) and [validation plan](09_Plan_de_Validacion.md). Independent scientific/geospatial sign-off is not claimed.
