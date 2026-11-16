# Evidence, provenance and distribution policy

This folder records the research collection behind Apex-Mars. Source identifiers refer to the [bibliography](../Docs/11_Bibliografia.md). Initial research records date from 2026-10-24–2026-10-25; subsequent collection includes event-period Jezero products.

## What Git includes

- Source catalogs, download manifests, audit results and selected structured metadata.
- SHA-256 inventory and historical verification results.
- This explanation of omitted files and reproduction procedures.

## What stays outside Git

Raw GeoTIFFs, full-resolution images, downloaded PDFs/text extracts, cached web pages, MEDA observation CSVs, incomplete `.part` downloads and private conversation history remain local. The research collection is approximately 8 GB in the publication workspace. Nothing is deleted from local storage by this policy.

Reduced **runtime** assets under `app/public/` are separate application deliverables; their presence does not mean raw products are included.

## Collection layout

| Local path | Contents / source |
|---|---|
| `web/` | Challenge/FAQ snapshots [S01–S03]; omitted HTML can be fetched again |
| `papers/` | NASA reports and literature; downloaded documents are not redistributed |
| `datos/mars_trek/` | Service audit, vector catalog and regional raster research [S14] |
| `datos/meda/` | Sol 1740 archived environmental sample [S16] |
| `datos/openalex/`, `datos/ntrs/` | Literature-search responses [S81–S82] |
| `datos/recursos_nasa_2026/` | Challenge-resource audit and USGS map references |
| `datos/jezero/` | Core source catalog, acquisition manifests, labels and local originals/derivatives |
| `capturas/` | Locally generated research figures |
| `manifiesto.csv` | Historical SHA-256 inventory, sizes and modification dates |
| `verificacion.json` | Historical verification snapshot; not a new release certificate |

Some catalog fields and titles preserve the original research language. They are source records, not untranslated public procedures.

## Original data pages

- [NASA/JPL Mars Trek](https://trek.nasa.gov/mars/) [S14].
- [PDS MEDA archive](https://pds-atmospheres.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda/) [S16].
- [USGS CTX science-investigation products](https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/) [S37].
- [USGS HiRISE DTM release](https://doi.org/10.5066/P9REJ9JN) [S78].
- [USGS HiRISE image release](https://doi.org/10.5066/P9QJDP48) [S79].
- [NASA raw rover images](https://mars.nasa.gov/mars2020/multimedia/raw-images/) [S75].
- [NASA Technical Reports Server](https://ntrs.nasa.gov/) [S81].

Exact file URLs and product identifiers are retained in the acquisition scripts and catalogs. See [data sources](../Docs/03_Fuentes_y_Datos_NASA.md) for further references and caveats.

## Restore and verify

Follow [Scripts/README.md](../Scripts/README.md) to download only the collection you need, inspect labels and reproduce derivatives. Do not treat browse images as georeferenced products.

```bash
python Scripts/07_verificar_evidencias.py --check
```

**Expected fresh-clone behavior:** this reports missing raw files listed in the local inventory, because those files are intentionally excluded. Restore the relevant files before interpreting the check as a collection-integrity result.

Do not regenerate the manifest merely to conceal missing or changed files. A local SHA-256 value supports later byte-for-byte comparison; without an independent trusted reference, it does not establish authenticity or scientific correctness.

## Interpretation limits

- MOLA is regional context, not a walking-hazard model.
- Resampled pixels do not create new terrain detail.
- MEDA sol 1740 is an archived sample, not present-day conditions.
- Mineral detections do not establish accessible water, reserves or life.
- Derived slopes and color-based routing indices are not safety certification.
- Observation times, coverage, calibration flags, no-data and original usage terms must accompany reuse.

Credit each product's creators and preserve its usage conditions. Open access does not grant unrestricted rights to every image or publication.
