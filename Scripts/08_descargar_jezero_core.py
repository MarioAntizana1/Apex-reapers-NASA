"""Descarga los productos centrales de topografia e imagen orbital de Jezero.

Fuentes: USGS Astrogeology (PDS Cartography and Imaging Science Node),
NASA/JPL Mars 2020, Arizona State University (THEMIS) y ESA (HRSC).

Uso:
    python Scripts/08_descargar_jezero_core.py [--solo ID ...]

El script reanuda descargas, calcula SHA-256 y escribe:
    Evidencias/datos/jezero/manifiesto_core.csv
    Evidencias/datos/jezero/catalogo_core.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Evidencias" / "datos" / "jezero"
TIMEOUT = (30, 300)
CHUNK = 1 << 20
UA = "AresAtlas/1.0 (NASA Space Apps 2026; evidencia cientifica)"

# id, grupo, subgrupo, destino, url, mision, instrumento, descripcion,
# resolucion, fecha_dato, crs, licencia, limitaciones
ASSETS = [
    dict(
        id="ctx_dem_20m_jezero",
        grupo="topografia",
        subgrupo="dem",
        destino="topografia/M20_JezeroCrater_CTXDEM_20m.tif",
        url="https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/M20_JezeroCrater_CTXDEM_20m.tif",
        mision="Mars 2020 / MRO",
        instrumento="CTX (Context Camera)",
        descripcion="MDE/MDT de todo el crater Jezero a 20 m/px, mosaico de pares estereo CTX, localizado verticalmente a MOLA.",
        resolucion="20 m/px",
        fecha_dato="2021-10-14",
        crs="Equirectangular, Mars 2000, planetocentrico, R=3396190 m",
        licencia="NASA/USGS; citar Mangold et al. (2021), DOI 10.1126/science.abl4051",
        limitaciones="Pendientes locales suavizadas a 20 m; no resuelve rocas ni escalones de menos de ~40 m. No usar para navegacion.",
        bytes=90345300,
    ),
    dict(
        id="ctx_ortho_5m_jezero",
        grupo="orbital",
        subgrupo="ctx",
        destino="orbital/M20_JezeroCrater_CTXortho_mosaic_5m.tif",
        url="https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/M20_JezeroCrater_CTXortho_mosaic_5m.tif",
        mision="Mars 2020 / MRO",
        instrumento="CTX (Context Camera)",
        descripcion="Ortomosaico visible de todo el crater Jezero a 5 m/px, ajustado al MDE CTX de 20 m.",
        resolucion="5 m/px",
        fecha_dato="2021-10-14",
        crs="Equirectangular, Mars 2000, planetocentrico",
        licencia="NASA/USGS; citar Mangold et al. (2021), DOI 10.1126/science.abl4051",
        limitaciones="Imagen de contexto, no de detalle; algunas costuras y zonas sin cobertura estereo.",
        bytes=359599280,
    ),
    dict(
        id="hirise_dem_1m_landing",
        grupo="topografia",
        subgrupo="dem",
        destino="topografia/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif",
        url="https://planetarymaps.usgs.gov/mosaic/mars2020_trn/HiRISE/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif",
        mision="MRO",
        instrumento="HiRISE",
        descripcion="MDE HiRISE a 1 m/px de la zona de aterrizaje de Perseverance (7 modelos estereo), base de la mision TRN.",
        resolucion="1 m/px",
        fecha_dato="2020-07-24",
        crs="Equirectangular, Mars 2000, planetocentrico, R=3396190 m",
        licencia="Dominio publico NASA/USGS; citar Fergason et al. (2020), DOI 10.5066/P9REJ9JN",
        limitaciones="Cubre ~20x20 km, no todo el crater. Puede tener costuras y errores en bordes de sombra.",
        bytes=1839545409,
    ),
    dict(
        id="hirise_ortho_25cm_landing",
        grupo="orbital",
        subgrupo="hirise",
        destino="orbital/hirise_ortho_25cm_jezero_soc007.tif",
        url="https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/JEZ_hirise_soc_007_orthoMosaic_25cm_Ortho_blend120.tif",
        mision="MRO",
        instrumento="HiRISE",
        descripcion="Ortomosaico HiRISE a 25 cm/px de la zona de aterrizaje, derivado del MDE HiRISE de 1 m.",
        resolucion="0.25 m/px",
        fecha_dato="2020-07-24",
        crs="Equirectangular, Mars 2000, planetocentrico",
        licencia="Dominio publico NASA/USGS; citar Fergason et al. (2020)",
        limitaciones="Cubre solo la zona de aterrizaje; producto enorme (3.4 GB), no apto para carga directa en web.",
        bytes=3408854746,
    ),
    dict(
        id="ctx_dem_20m_trn",
        grupo="topografia",
        subgrupo="dem",
        destino="topografia/JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif",
        url="https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif",
        mision="Mars 2020 / MRO",
        instrumento="CTX (Context Camera)",
        descripcion="MDE CTX de la elipse de aterrizaje (producto LVS de TRN), 20 m/px, controlado con MOLA.",
        resolucion="20 m/px",
        fecha_dato="2020-07-24",
        crs="Equirectangular, Mars 2000, planetocentrico",
        licencia="Dominio publico NASA/USGS; citar Fergason et al. (2020), DOI 10.5066/P906QQT8",
        limitaciones="Solo cubre la zona de aterrizaje; precision horizontal ~9.6 m.",
        bytes=9662387,
    ),
    dict(
        id="ctx_ortho_6m_trn",
        grupo="orbital",
        subgrupo="ctx",
        destino="orbital/JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0.tif",
        url="https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0.tif",
        mision="Mars 2020 / MRO",
        instrumento="CTX (Context Camera)",
        descripcion="Ortomosaico CTX de la zona de aterrizaje (LVS), 6 m/px.",
        resolucion="6 m/px",
        fecha_dato="2020-07-24",
        crs="Equirectangular, Mars 2000, planetocentrico",
        licencia="Dominio publico NASA/USGS; citar Fergason et al. (2020), DOI 10.5066/P906QQT8",
        limitaciones="Solo zona de aterrizaje; imagen pancromatica.",
        bytes=36269402,
    ),
    dict(
        id="hirise_dem_cr_north",
        grupo="topografia",
        subgrupo="dem_hirise_individual",
        destino="topografia/hirise_individual/DTM_Jezero_CR_NORTH_1m.tif",
        url="https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/DTM_MOLAtopography_DeltaGeoid_Jezero_CR_NORTH_Edited_affine_1m_Eqc_latTs0_lon0.tif",
        mision="MRO",
        instrumento="HiRISE",
        descripcion="MDE HiRISE individual del modelo estereo Jezero_CR (norte), 1 m/px.",
        resolucion="1 m/px",
        fecha_dato="2020-07-24",
        crs="Equirectangular, Mars 2000, planetocentrico",
        licencia="Dominio publico NASA/USGS; citar Fergason et al. (2020)",
        limitaciones="Modelo individual; usar el mosaico para analisis continuo.",
        bytes=72020271,
    ),
    dict(
        id="hirise_dem_cr_south",
        grupo="topografia",
        subgrupo="dem_hirise_individual",
        destino="topografia/hirise_individual/DTM_Jezero_CR_SOUTH_1m.tif",
        url="https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/DTM_MOLAtopography_DeltaGeoid_Jezero_CR_SOUTH_Edited_affine_1m_Eqc_latTs0_lon0.tif",
        mision="MRO",
        instrumento="HiRISE",
        descripcion="MDE HiRISE individual del modelo estereo Jezero_CR (sur), 1 m/px.",
        resolucion="1 m/px",
        fecha_dato="2020-07-24",
        crs="Equirectangular, Mars 2000, planetocentrico",
        licencia="Dominio publico NASA/USGS; citar Fergason et al. (2020)",
        limitaciones="Modelo individual; usar el mosaico para analisis continuo.",
        bytes=77432148,
    ),
    dict(
        id="hirise_dem_c",
        grupo="topografia",
        subgrupo="dem_hirise_individual",
        destino="topografia/hirise_individual/DTM_Jezero_C_1m.tif",
        url="https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/DTM_MOLAtopography_DeltaGeoid_Jezero_C_Edited_affine_1m_Eqc_latTs0_lon0.tif",
        mision="MRO",
        instrumento="HiRISE",
        descripcion="MDE HiRISE individual del modelo estereo Jezero_C (centro), 1 m/px.",
        resolucion="1 m/px",
        fecha_dato="2020-07-24",
        crs="Equirectangular, Mars 2000, planetocentrico",
        licencia="Dominio publico NASA/USGS; citar Fergason et al. (2020)",
        limitaciones="Modelo individual; usar el mosaico para analisis continuo.",
        bytes=125020023,
    ),
    dict(
        id="hirise_dem_dl",
        grupo="topografia",
        subgrupo="dem_hirise_individual",
        destino="topografia/hirise_individual/DTM_Jezero_DL_1m.tif",
        url="https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/DTM_MOLAtopography_DeltaGeoid_Jezero_DL_Edited_affine_1m_Eqc_latTs0_lon0.tif",
        mision="MRO",
        instrumento="HiRISE",
        descripcion="MDE HiRISE individual del modelo estereo Jezero_DL (delta), 1 m/px.",
        resolucion="1 m/px",
        fecha_dato="2020-07-24",
        crs="Equirectangular, Mars 2000, planetocentrico",
        licencia="Dominio publico NASA/USGS; citar Fergason et al. (2020)",
        limitaciones="Modelo individual; usar el mosaico para analisis continuo.",
        bytes=114658582,
    ),
    dict(
        id="hirise_dem_e",
        grupo="topografia",
        subgrupo="dem_hirise_individual",
        destino="topografia/hirise_individual/DTM_Jezero_E_1m.tif",
        url="https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/DTM_MOLAtopography_DeltaGeoid_Jezero_E_Edited_affine_1m_Eqc_latTs0_lon0.tif",
        mision="MRO",
        instrumento="HiRISE",
        descripcion="MDE HiRISE individual del modelo estereo Jezero_E (este), 1 m/px.",
        resolucion="1 m/px",
        fecha_dato="2020-07-24",
        crs="Equirectangular, Mars 2000, planetocentrico",
        licencia="Dominio publico NASA/USGS; citar Fergason et al. (2020)",
        limitaciones="Modelo individual; usar el mosaico para analisis continuo.",
        bytes=132409896,
    ),
    dict(
        id="hirise_dem_n",
        grupo="topografia",
        subgrupo="dem_hirise_individual",
        destino="topografia/hirise_individual/DTM_Jezero_N_1m.tif",
        url="https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/DTM_MOLAtopography_DeltaGeoid_Jezero_N_Edited_affine_1m_Eqc_latTs0_lon0.tif",
        mision="MRO",
        instrumento="HiRISE",
        descripcion="MDE HiRISE individual del modelo estereo Jezero_N (norte), 1 m/px.",
        resolucion="1 m/px",
        fecha_dato="2020-07-24",
        crs="Equirectangular, Mars 2000, planetocentrico",
        licencia="Dominio publico NASA/USGS; citar Fergason et al. (2020)",
        limitaciones="Modelo individual; usar el mosaico para analisis continuo.",
        bytes=105619366,
    ),
    dict(
        id="hirise_dem_w",
        grupo="topografia",
        subgrupo="dem_hirise_individual",
        destino="topografia/hirise_individual/DTM_Jezero_W_1m.tif",
        url="https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/DTM_MOLAtopography_DeltaGeoid_Jezero_W_Edited_affine_1m_Eqc_latTs0_lon0.tif",
        mision="MRO",
        instrumento="HiRISE",
        descripcion="MDE HiRISE individual del modelo estereo Jezero_W (oeste), 1 m/px.",
        resolucion="1 m/px",
        fecha_dato="2020-07-24",
        crs="Equirectangular, Mars 2000, planetocentrico",
        licencia="Dominio publico NASA/USGS; citar Fergason et al. (2020)",
        limitaciones="Modelo individual; usar el mosaico para analisis continuo.",
        bytes=129734394,
    ),
    dict(
        id="themis_day_ir_tile",
        grupo="orbital",
        subgrupo="themis",
        destino="orbital/themis_day_ir_N00_060.png",
        url="https://mars.asu.edu/data/thm_dir/large/thm_dir_N00_060.png",
        mision="Mars Odyssey",
        instrumento="THEMIS (banda IR diurna, 12.57 um)",
        descripcion="Mosaico THEMIS IR diurno, tesela 0-30 N / 60-90 E; incluye Jezero. Se recorta a la region en el procesado.",
        resolucion="~231 m/px (256 ppd)",
        fecha_dato="2006-11-16 (v2.0)",
        crs="Simple cilindrica, -180..180 E, planetocentrico",
        licencia="Dominio publico NASA/ASU; citar Christensen et al.",
        limitaciones="Resolucion gruesa; mezcla temperatura de superficie y pendiente; no es un mapa de temperatura absoluta.",
        bytes=40196864,
    ),
    dict(
        id="hrsc_jezero_color",
        grupo="orbital",
        subgrupo="hrsc",
        destino="orbital/hrsc_jezero_color.png",
        url="https://media.esa.int/legacy/web/images/esa_multimedia/images/2021/02/jezero_crater_and_surrounds/23161973-1-eng-GB/Jezero_crater_and_surrounds.png",
        mision="Mars Express (ESA)",
        instrumento="HRSC",
        descripcion="Mosaico en color HRSC de Jezero y alrededores, combinando canales RGB y nadir de alta resolucion.",
        resolucion="~12.5-25 m/px segun zona",
        fecha_dato="2021-02",
        crs="No georreferenciado en el PNG publico; usar como imagen de contexto, no como capa medida.",
        licencia="ESA/Mars Express (DLR/FU Berlin); uso educativo con atribucion",
        limitaciones="Producto de comunicacion, no un GeoTIFF cientifico; puede tener realce de color y costuras.",
        bytes=90299728,
    ),
    dict(
        id="hrsc_jezero_annotated",
        grupo="orbital",
        subgrupo="hrsc",
        destino="orbital/hrsc_jezero_annotated.png",
        url="https://media.esa.int/legacy/web/images/esa_multimedia/images/2021/02/jezero_crater_and_surrounds_annotated/23161692-1-eng-GB/Jezero_crater_and_surrounds_annotated.png",
        mision="Mars Express (ESA)",
        instrumento="HRSC",
        descripcion="Version anotada del mosaico HRSC de Jezero (toponimos y rasgos).",
        resolucion="~12.5-25 m/px",
        fecha_dato="2021-02",
        crs="No georreferenciado",
        licencia="ESA/Mars Express (DLR/FU Berlin); uso educativo con atribucion",
        limitaciones="Rotulos sobreimpresos; no usar para medicion.",
        bytes=92263856,
    ),
    dict(
        id="ctx_dem_20m_label",
        grupo="metadatos",
        subgrupo="pds4",
        destino="metadatos/M20_JezeroCrater_CTXDEM_20m.xml",
        url="https://astrogeology.usgs.gov/ckan/dataset/f8ef46b8-d512-4c46-b825-fe9633c38e1c/resource/5691ea08-1db4-4018-a341-e415e716add7/download/m20_jezerocrater_ctxdem_20m.xml",
        mision="Mars 2020 / MRO",
        instrumento="CTX",
        descripcion="Etiqueta PDS4 del MDE CTX de 20 m.",
        resolucion="",
        fecha_dato="2021-10-14",
        crs="Mars 2000",
        licencia="Dominio publico",
        limitaciones="",
        bytes=None,
    ),
    dict(
        id="ctx_ortho_5m_label",
        grupo="metadatos",
        subgrupo="pds4",
        destino="metadatos/M20_JezeroCrater_CTXortho_5m.xml",
        url="https://astrogeology.usgs.gov/ckan/dataset/f8ef46b8-d512-4c46-b825-fe9633c38e1c/resource/d139f28f-9976-40b1-aa55-49b78cebf055/download/m20_jezerocrater_ctxortho_mosaic_5m.xml",
        mision="Mars 2020 / MRO",
        instrumento="CTX",
        descripcion="Etiqueta PDS4 del ortomosaico CTX de 5 m.",
        resolucion="",
        fecha_dato="2021-10-14",
        crs="Mars 2000",
        licencia="Dominio publico",
        limitaciones="",
        bytes=None,
    ),
    dict(
        id="hirise_dem_1m_label",
        grupo="metadatos",
        subgrupo="pds3",
        destino="metadatos/JEZ_hirise_soc_006_DTM_1m.lbl",
        url="https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.lbl",
        mision="MRO",
        instrumento="HiRISE",
        descripcion="Etiqueta ISIS/PDS del MDE HiRISE de 1 m.",
        resolucion="",
        fecha_dato="2020-07-24",
        crs="Mars 2000",
        licencia="Dominio publico",
        limitaciones="",
        bytes=None,
    ),
    dict(
        id="ctx_dem_20m_browse",
        grupo="metadatos",
        subgrupo="browse",
        destino="topografia/M20_JezeroCrater_CTXDEM_20m_browse.jpg",
        url="https://astrogeology.usgs.gov/ckan/dataset/f8ef46b8-d512-4c46-b825-fe9633c38e1c/resource/563e70c1-78d3-4595-b97a-f840c67aa3a3/download/m20_jezerocrater_ctxdem_mosaic_20m.jpg",
        mision="Mars 2020 / MRO",
        instrumento="CTX",
        descripcion="Imagen de vista previa del MDE CTX de 20 m.",
        resolucion="1024 px",
        fecha_dato="2021-10-14",
        crs="Vista previa",
        licencia="Dominio publico",
        limitaciones="Solo referencia visual.",
        bytes=None,
    ),
    dict(
        id="hirise_dem_1m_browse",
        grupo="metadatos",
        subgrupo="browse",
        destino="topografia/JEZ_hirise_DTM_1m_browse.jpg",
        url="https://astrogeology.usgs.gov/ckan/dataset/381ba037-d8a9-4cea-86be-374e4951afe3/resource/3fe8c4ce-af1d-4d55-8e25-e6e1e69867ff/download/jez_hirise_soc_006_dtm_molatopography_deltageoid_1m_eqc_latts0_lon0_blend40_1024.jpg",
        mision="MRO",
        instrumento="HiRISE",
        descripcion="Vista previa del MDE HiRISE de 1 m.",
        resolucion="1024 px",
        fecha_dato="2020-07-24",
        crs="Vista previa",
        licencia="Dominio publico",
        limitaciones="Solo referencia visual.",
        bytes=None,
    ),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def download(asset: dict, session: requests.Session) -> dict:
    dest = OUT / asset["destino"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    expected = asset.get("bytes")
    if dest.exists() and dest.stat().st_size > 0 and (not expected or dest.stat().st_size == expected):
        print(f"[skip] {asset['id']} ({dest.stat().st_size:,} B)", flush=True)
        return {**asset, "estado": "ok", "bytes_reales": dest.stat().st_size, "sha256": sha256(dest), "reanudado": False}

    part = dest.with_suffix(dest.suffix + ".part")
    last_error = None
    for attempt in range(1, 7):
        existing = part.stat().st_size if part.exists() else 0
        headers = {"User-Agent": UA}
        if existing:
            headers["Range"] = f"bytes={existing}-"
        print(f"[get ] {asset['id']} intento {attempt} -> {dest.name} ({existing:,} B ya descargados)", flush=True)
        started = time.time()
        try:
            with requests.get(asset["url"], headers=headers, stream=True, timeout=(30, 120), allow_redirects=True) as response:
                if response.status_code == 416:
                    part.replace(dest)
                    return {**asset, "estado": "ok", "bytes_reales": dest.stat().st_size, "sha256": sha256(dest), "reanudado": True}
                response.raise_for_status()
                mode = "ab" if existing and response.status_code == 206 else "wb"
                if mode == "wb":
                    existing = 0
                with part.open(mode) as handle:
                    for chunk in response.iter_content(CHUNK):
                        if chunk:
                            handle.write(chunk)
            part.replace(dest)
            elapsed = max(time.time() - started, 0.001)
            size = dest.stat().st_size
            print(f"[ok  ] {asset['id']} {size:,} B en {elapsed:.1f}s ({size/elapsed/1e6:.2f} MB/s)", flush=True)
            return {
                **asset,
                "estado": "ok",
                "bytes_reales": size,
                "sha256": sha256(dest),
                "reanudado": bool(existing),
                "segundos": round(elapsed, 2),
            }
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"[warn] {asset['id']} intento {attempt}: {exc}", flush=True)
            time.sleep(min(2 ** attempt, 20))
    raise RuntimeError(f"No se pudo descargar {asset['id']}: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", nargs="*", default=None, help="IDs concretos a descargar")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    selected = [a for a in ASSETS if not args.solo or a["id"] in args.solo]
    session = requests.Session()
    results = []
    for asset in selected:
        try:
            results.append(download(asset, session))
        except Exception as exc:  # noqa: BLE001
            print(f"[err ] {asset['id']}: {exc}")
            results.append({**asset, "estado": "error", "detalle": str(exc)})

    fields = [
        "id", "grupo", "subgrupo", "destino", "url", "estado", "bytes", "bytes_reales",
        "sha256", "mision", "instrumento", "descripcion", "resolucion", "fecha_dato",
        "crs", "licencia", "limitaciones", "detalle",
    ]
    with (OUT / "manifiesto_core.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow({key: row.get(key, "") for key in fields})
    (OUT / "catalogo_core.json").write_text(
        json.dumps({"generado": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "activos": results},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    ok = sum(1 for r in results if r.get("estado") == "ok")
    print(f"\n{ok}/{len(results)} descargas correctas")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
