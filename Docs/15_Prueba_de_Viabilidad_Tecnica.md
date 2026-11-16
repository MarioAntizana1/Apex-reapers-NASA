# 15. Data-access feasibility evidence

This records research acquisition and processing results from the initial dossier. It is **not** application acceptance, a new rerun or navigation validation.

## Recorded Mars Trek snapshot

| Check | Recorded result |
|---|---|
| Service directory | 76 ArcGIS services |
| Configuration/catalog acquisition | Six JSON resources |
| Jezero vectors | Eight GeoJSON collections |
| Basemap/hillshade exports | 2048 × 2048 PNG images |
| Regional DEM export | 1024 × 1024 TIFF |
| Traverse geometry | Approximately 46.3 km accumulated Perseverance trace |
| Regional slope statistics | Median 0.81°, p95 2.83° |

Evidence: `Evidencias/datos/mars_trek/`, particularly `auditoria.json`, `manifiesto_mars_trek.csv` and `estadisticas_jezero.json`. Sources: [S14].

Recorded feature counts: traverse 332, waypoints 7, landing ellipse 1, human-exploration ROIs 2, exploration buffer 1, mineral detection 1, global geology 2 and Mars 2020 sites 2.

The regional elevation export covered approximately 77.2°E–77.9°E and 18.1°N–18.8°N, with recorded minimum −2716 m, maximum −1570 m and mean −2399.9 m. Its output pixel spacing was resampled and does not add detail beyond the source.

**Interpretation limit:** low regional slopes cannot establish obstacle-free terrain. MOLA is too coarse for human-scale hazards [S34, S49]. The measured rover trace is not our planned astronaut route.

## Recorded MEDA sample

Sol 1740 was acquired from PDS [S16]. Main files contain roughly 81,000 rows each, depending on product. The initial processing reported:

| Variable | Minimum | Maximum | Mean |
|---|---:|---:|---:|
| Pressure (Pa) | 651.98 | 696.95 | 671.70 |
| ATS temperature (K) | 193.06 | 258.62 | 220.52 |
| ATS temperature (°C) | −80.09 | −14.53 | −52.63 |
| Humidity A (%) | −0.01 | 19.56 | 4.13 |
| TIRS downward (W/m²) | 26.05 | 49.23 | 35.99 |
| TIRS upward (W/m²) | 81.53 | 343.74 | 160.87 |
| Solar zenith angle (°) | 29.05 | 171.87 | 97.13 |

These are historical script outputs, not newly quality-controlled environmental conclusions. Negative humidity values require calibration/flag interpretation. The sample is neither live weather nor evidence of available water.

## Reproduction and limitations

Use scripts 04–07 as described in [Scripts/README.md](../Scripts/README.md), restore omitted originals and inspect their labels before interpreting statistics. The evidence figure is a research output; it is not a certified map.

This work establishes that relevant data can be accessed and processed. It does not establish validated route safety, suit modeling, human-scale hazard resolution, brief export, offline behavior or the complete proposed MVP.
