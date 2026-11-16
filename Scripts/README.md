# Research and data procedures

These Python tools acquire, inspect and transform research data. They are separate from the browser application. Preserve original scientific products; distribute reduced derivatives separately.

## Environment

Run from the repository root with Python 3.11+, internet access and sufficient storage. The full acquisition can require **many gigabytes**, not merely the size of the Git clone.

```bash
python -m pip install requests pypdf pillow numpy rasterio tifffile truststore
python Scripts/00_verificar_entorno.py
```

Dependencies vary by script; this is a combined installation command, not a fully pinned environment. GDAL-backed rasterio installation may need platform-specific packages. Review the script's constants and output paths before executing it.

## Acquisition and research workflow

| Script | Purpose | Main output |
|---|---|---|
| `00_verificar_entorno.py` | Check environment, packages, disk and endpoints | Console report |
| `01_obtener_reto_spaceapps.py` | Fetch challenge, home and FAQ records [S01–S03] | `Evidencias/web/` |
| `02_investigacion_openalex.py` | Literature discovery using `queries_openalex.json` [S82] | OpenAlex JSON and consolidated CSV/Markdown |
| `03_investigacion_ntrs.py` | Technical-report search and open PDF acquisition [S81] | NTRS records and local papers |
| `04_auditar_mars_trek.py` | Inspect services and acquire Jezero layers [S14] | `Evidencias/datos/mars_trek/` |
| `05_descargar_datos_meda.py` | Acquire sol 1740 MEDA sample and statistics [S16] | `Evidencias/datos/meda/` |
| `06_generar_evidencia_visual.py` | Generate research map and regional DEM/traverse statistics | Evidence image and statistics |
| `07_verificar_evidencias.py` | Generate or check SHA-256 inventory | `Evidencias/manifiesto.csv` |
| `08_auditar_recursos_nasa.py` | Inspect challenge resources, including USGS mapping hub and raw images | `Evidencias/datos/recursos_nasa_2026/` |
| `08_descargar_jezero_core.py` | Acquire CTX/HiRISE products, source labels and context imagery | Jezero core catalog and manifest |
| `09_descargar_hirise_browse.py` | Collect HiRISE browse images | Browse catalog and local images |
| `10_descargar_perseverance.py` | Collect selected rover surface images | Surface-image catalog |
| `11_descargar_prensa_nasa.py` | Acquire selected outreach images | Press-image catalog |

The two `08_` scripts are independent tools, not alternative versions of the same program. Source IDs resolve in the [bibliography](../Docs/11_Bibliografia.md).

### Minimal research example

```bash
python Scripts/04_auditar_mars_trek.py
python Scripts/05_descargar_datos_meda.py
python Scripts/06_generar_evidencia_visual.py
```

Review acquisition status, product labels and missing values before using the results. A successful HTTP response or a local hash is not proof of scientific suitability.

### Selective core downloads

```bash
python Scripts/08_descargar_jezero_core.py --solo ctx_dem_20m_jezero ctx_ortho_5m_jezero hirise_dem_cr_north
```

The identifiers and original URLs are defined in the script's `ASSETS` list. Running without `--solo` requests the broader collection, including very large products. Some downloads support resumption through `.part` files; incomplete files are not accepted scientific evidence.

**Separate prerequisite for script 14:** obtain `ESP_036618_1985_NORTH_25cm.tif` from the [USGS orthomosaic release](https://doi.org/10.5066/P9QJDP48) and place it at `Evidencias/datos/jezero/orbital/`. That individual orthophoto is not one of the core downloader's selected products above.

## Processing and application assets

| Script | Input / operation | Output |
|---|---|---|
| `12_procesar_topografia.py` | CTX DEM; slope, hillshade, contours and profiles | Jezero topographic derivatives |
| `13_procesar_orbital_y_mapas.py` | Orbital products and contextual vectors | Reduced map images/catalog for the app |
| `14_teselar_hirise.py` | Individual 25 cm HiRISE orthophoto; local reprojection and image tiling | `app/public/maps/hirise-north/` |
| `15_preparar_relieve_3d.py` | Individual CR North 1 m DTM; resample to complete 256 m chunks at 8 m spacing | `app/public/terrain-3d/` |
| `16_relieve_3d_detalle.py` | Same DTM, restricted to existing chunks; 1 m detail, 0.1 m quantization | `app/public/terrain-3d-detail/` |

Run processing only after inspecting inputs:

```bash
python Scripts/12_procesar_topografia.py
python Scripts/13_procesar_orbital_y_mapas.py
```

Scripts 14–16 require their destination directories **not to exist** and deliberately refuse to overwrite them. A normal clone may already include generated runtime assets: do not rerun these scripts over them or delete them blindly. For regeneration, use a separate checkout/output workspace and preserve existing results.

```bash
# Only in a workspace where the corresponding output directories do not exist:
python Scripts/14_teselar_hirise.py
python Scripts/15_preparar_relieve_3d.py
python Scripts/16_relieve_3d_detalle.py
```

Both the data projection and the application projection must be checked; see [application coordinates](../app/README.md#shared-coordinates). Spatial resolution, interpolation and numeric quantization are not claims of measurement accuracy.

The routing-grid generator in `app/scripts/` belongs to a separate experimental workflow: it uses image-derived indices and assumed relief. Do not confuse that grid with the scientific HiRISE terrain chunks.

## Integrity and provenance

```bash
python Scripts/07_verificar_evidencias.py --check
python Scripts/test_jezero_integridad.py
```

The first command checks the existing local inventory. Without `--check`, script 07 writes a new inventory: preserve the old one if you need historical comparison. Downloaded data omitted from Git will appear missing in a fresh clone; this is expected, not a successful complete validation.

Retain URL, access date, mission/instrument, product identifier, units, CRS/body model, resolution, license, coverage, processing steps and limitations. Use the [data-card template](../Docs/13_Checklist_y_Plantillas.md).

## Troubleshooting

- **HTTP failures:** official archives can change paths, rate-limit or become unavailable. Record the failure and inspect the source page; do not substitute an unrelated product.
- **TLS errors:** `truststore` can use the platform trust store where supported. Do not disable certificate verification.
- **PowerShell blocks npm:** use `npm.cmd` or a command prompt rather than changing system policy indiscriminately.
- **Insufficient disk:** selectively acquire products or use another storage location after reviewing script paths. Do not delete originals to hide an incomplete workflow.
- **Existing output directory:** scripts 14–16 protect previous results; regenerate in a separate workspace.

## Boundaries

These procedures do not validate a suit, certify a route, establish live weather, complete scientific review, or submit a Space Apps project. Their outputs need human review. Some comments, identifiers and source metadata retain Spanish; the public operating instructions are English.
