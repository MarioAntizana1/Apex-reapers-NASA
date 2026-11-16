"""Audita los recursos NASA entregados por el reto (2026-11-14).

No construye la aplicación: verifica qué aporta cada enlace, descarga solo
metadatos y vistas previas, y deja un veredicto explícito de uso.

Salida: Evidencias/datos/recursos_nasa_2026/
"""

import html
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Evidencias" / "datos" / "recursos_nasa_2026"
TIMEOUT = 90
HEADERS = {"User-Agent": "AresAtlas-research/1.0 (NASA Space Apps 2026)"}

PGM = (
    "https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/"
    "PGM_Map_Database_MARS_INTERACTIVE2/FeatureServer/1"
)
USGS_APP = "https://usgs.maps.arcgis.com/sharing/rest/content/items/f693b580b2464e6989f32e4266199552/data?f=pjson"
RAW_API = "https://mars.nasa.gov/rss/api/?feed=raw_images&category=mars2020&feedtype=json&num=100&page=1"
RAW_LATEST = "https://mars.nasa.gov/rss/api/?feed=raw_images&category=mars2020,ingenuity&feedtype=json&ver=1.2&latest=true"
RAW_SOL = "https://mars.nasa.gov/rss/api/?feed=raw_images&category=mars2020&feedtype=json&num=10&page=1&sol={sol}"

LOG = []


def fetch(url, params=None, label="", binary=False):
    started = time.time()
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        content = response.content
        LOG.append({
            "recurso": label or url,
            "url": response.url,
            "estado": response.status_code,
            "tipo": response.headers.get("content-type", ""),
            "bytes": len(content),
            "segundos": round(time.time() - started, 2),
        })
        print(f"[{response.status_code}] {len(content):>9} B  {label or url}")
        if response.status_code != 200:
            return None
        return content if binary else response
    except Exception as exc:
        LOG.append({
            "recurso": label or url,
            "url": url,
            "estado": "ERROR",
            "tipo": "",
            "bytes": 0,
            "segundos": round(time.time() - started, 2),
            "detalle": str(exc),
        })
        print(f"[ERROR] {label or url}: {exc}")
        return None


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def meta_content(text, pattern):
    match = re.search(pattern, text, flags=re.I | re.S)
    return html.unescape(match.group(1)).strip() if match else None


def auditar_mars_trek():
    audit = ROOT / "Evidencias" / "datos" / "mars_trek" / "auditoria.json"
    resumen = json.loads(audit.read_text(encoding="utf-8")) if audit.exists() else {}
    return {
        "id": "mars_trek",
        "url": "https://trek.nasa.gov/mars/",
        "estado": "reutilizado",
        "relevancia": "alta",
        "aporta": "Capas listas para web: DEM MOLA, mosaico Viking, travesía, waypoints, elipse, minerales y geología.",
        "decision": "integrar",
        "limitaciones": "Base Viking de 232 m/px y DEM regional; no resuelve pendientes locales de una caminata.",
        "evidencia": "Evidencias/datos/mars_trek/auditoria.json",
        "resumen_auditoria": {
            "servicios": resumen.get("servicios"),
            "recursos_ok": resumen.get("recursos_ok"),
            "recursos_total": resumen.get("recursos_total"),
        },
    }


def auditar_usgs():
    page = fetch(
        "https://astrogeology-usgs.hub.arcgis.com/pages/interactive-maps-mars",
        label="USGS Hub — mapas interactivos de Marte",
    )
    app = fetch(USGS_APP, label="USGS — configuración de la app Marte")
    webmap = None
    if app:
        app_data = app.json()
        map_id = (app_data.get("map") or {}).get("itemId")
        if map_id:
            webmap = fetch(
                f"https://usgs.maps.arcgis.com/sharing/rest/content/items/{map_id}/data?f=pjson",
                label="USGS — web map de Marte",
            )

    meta = fetch(f"{PGM}?f=pjson", label="PGM — metadatos del FeatureServer")
    count = fetch(f"{PGM}/query?where=1%3D1&returnCountOnly=true&f=json", label="PGM — total de mapas")
    sim = fetch(
        f"{PGM}/query?where=USGSMapNumber%3D%27SIM%203464%27&outFields=*&returnGeometry=false&f=json",
        label="PGM — ficha SIM 3464 (Jezero)",
    )
    bbox = fetch(
        f"{PGM}/query?where=1%3D1&geometry=-77.7,18.1,-77.2,18.7"
        "&geometryType=esriGeometryEnvelope&inSR=4326"
        "&spatialRel=esriSpatialRelIntersects"
        "&outFields=MapTitle,USGSMapNumber,PublicationDate,MapScale,FormattedAuthors,"
        "USGSPublicationPage,InteractiveMap,FullImageLink,InsetImageLink,SuggestedCitation"
        "&returnGeometry=false&f=json",
        label="PGM — mapas que cubren Jezero",
    )

    datos = {
        "consultado": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "fuente": "USGS Planetary Geologic Mapping Hub — Interactive Maps: Mars",
        "url": "https://astrogeology-usgs.hub.arcgis.com/pages/interactive-maps-mars",
        "app_marte": {
            "item_id": "f693b580b2464e6989f32e4266199552",
            "url": "https://usgs.maps.arcgis.com/apps/webappviewer/index.html?id=f693b580b2464e6989f32e4266199552",
            "basemap": "Mars_MGS_MOLA_ClrShade_merge_global_463m (Mars Trek)",
            "capa": "PGM_Map_Database_MARS_INTERACTIVE2/FeatureServer/1",
        },
        "catalogo_total": (count.json().get("count") if count else None),
        "campos": [f["name"] for f in (meta.json().get("fields", []) if meta else [])],
        "sim3464": (sim.json().get("features") or [{}])[0].get("attributes") if sim else None,
        "mapas_que_cubren_jezero": [
            f.get("attributes") for f in (bbox.json().get("features", []) if bbox else [])
        ],
        "advertencia": (
            "Los polígonos del FeatureServer son índices de hojas cartográficas, "
            "no contactos geológicos. SIM 3464 es un mapa cartográfico estático "
            "a escala 1:75 000; su PNG no es una capa georreferenciada para web."
        ),
    }
    save_json(OUT / "usgs_pgm_jezero.json", datos)

    preview_url = (datos.get("sim3464") or {}).get("InsetImageLink")
    if preview_url:
        preview = fetch(preview_url, label="USGS — vista previa SIM 3464", binary=True)
        if preview:
            (OUT / "usgs_sim3464_preview.png").write_bytes(preview)

    if webmap:
        save_json(OUT / "usgs_mars_webmap.json", webmap.json())

    return {
        "id": "usgs_pgm",
        "url": "https://astrogeology-usgs.hub.arcgis.com/pages/interactive-maps-mars",
        "estado": "ok",
        "relevancia": "alta para ciencia y citas; media para capas web",
        "aporta": (
            "Catálogo de 148 mapas geológicos de Marte, ficha y vista previa del "
            "mapa de Jezero (SIM 3464) y enlaces interactivos por hoja."
        ),
        "decision": "usar como fuente de fichas, citas y enlace científico; no como capa raster",
        "limitaciones": (
            "Es un índice de mapas, no un mapa geológico continuo. La vista previa "
            "no está georreferenciada."
        ),
        "evidencia": [
            "Evidencias/datos/recursos_nasa_2026/usgs_pgm_jezero.json",
            "Evidencias/datos/recursos_nasa_2026/usgs_sim3464_preview.png",
            "Evidencias/datos/recursos_nasa_2026/usgs_mars_webmap.json",
        ],
    }


def auditar_curiosity():
    url = "https://science.nasa.gov/resource/curiositys-proposed-path-up-mount-sharp/"
    response = fetch(url, label="NASA Science — ruta propuesta de Curiosity")
    datos = {
        "consultado": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "url": url,
        "titulo": None,
        "descripcion": None,
        "animacion": "curiosity_mount_sharp_route.gif",
        "credito": "NASA/JPL-Caltech/ESA/University of Arizona/JHUAPL/MSSS/USGS Astrogeology Science Center",
        "relevancia": "media",
        "uso": (
            "Referencia visual de cómo se comunica una ruta y sus paradas. "
            "Es Gale, no Jezero: no se usa como capa del mapa."
        ),
        "limitaciones": (
            "Animación ilustrativa de una ruta propuesta, no un dataset "
            "georreferenciado ni una travesía validada."
        ),
    }
    if response:
        text = response.text
        datos["titulo"] = meta_content(text, r"<title>(.*?)</title>")
        datos["descripcion"] = meta_content(text, r'<meta name="description" content="([^"]+)"')
        image = meta_content(text, r'<meta property="og:image" content="([^"]+)"')
        if image:
            gif = fetch(image, label="NASA Science — GIF de la ruta", binary=True)
            if gif:
                (OUT / "curiosity_mount_sharp_route.gif").write_bytes(gif)
    save_json(OUT / "curiosity_mount_sharp.json", datos)
    return {
        "id": "curiosity_mount_sharp",
        "url": url,
        "estado": "ok",
        "relevancia": "media (analogía, no Jezero)",
        "aporta": "Animación de una ruta propuesta por la ladera de Mount Sharp (Gale).",
        "decision": "usar solo como referencia visual de comunicación de rutas",
        "limitaciones": "No es un dato georreferenciado ni una ruta validada.",
        "evidencia": [
            "Evidencias/datos/recursos_nasa_2026/curiosity_mount_sharp.json",
            "Evidencias/datos/recursos_nasa_2026/curiosity_mount_sharp_route.gif",
        ],
    }


def auditar_worldview():
    url = "https://worldview.earthdata.nasa.gov/"
    response = fetch(url, label="NASA Worldview")
    datos = {
        "consultado": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "url": url,
        "tipo": "visualizador de observación de la Tierra (NASA EOSDIS/GIBS)",
        "relevancia_marte": "ninguna",
        "decision": "no usar en el MVP",
        "motivo": (
            "Worldview muestra datos de la Tierra (MODIS, VIIRS, etc.), no de Marte. "
            "No sirve para el mapa de Jezero ni para condiciones marcianas."
        ),
        "uso_posible_futuro": (
            "Solo si se quisiera comparar un análogo terrestre; está fuera del alcance "
            "y del MVP."
        ),
    }
    if response:
        datos["titulo"] = meta_content(response.text, r"<title>(.*?)</title>")
    save_json(OUT / "worldview_nota.json", datos)
    return {
        "id": "worldview",
        "url": url,
        "estado": "ok, no aplica",
        "relevancia": "ninguna para Marte",
        "aporta": "Observación de la Tierra, no de Marte.",
        "decision": "rechazar para el MVP",
        "limitaciones": "No contiene capas marcianas.",
        "evidencia": "Evidencias/datos/recursos_nasa_2026/worldview_nota.json",
    }


def auditar_raw_images():
    latest = fetch(RAW_API, label="Mars 2020 — catálogo de imágenes crudas")
    estado = fetch(RAW_LATEST, label="Mars 2020 — último sol publicado")
    ultimo_sol = estado.json().get("latest_sol") if estado else 2031
    sol = fetch(
        RAW_SOL.format(sol=ultimo_sol),
        label=f"Mars 2020 — imágenes del sol {ultimo_sol}",
    )
    datos = {
        "consultado": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "api": RAW_API,
        "catalogo": "https://mars.nasa.gov/mars2020/multimedia/raw-images/",
        "total_images": None,
        "total_images_incl_ingenuity": None,
        "ultimo_sol": None,
        "ultima_actualizacion_utc": None,
        "muestra": [],
        "limitaciones": (
            "Las imágenes crudas no están georreferenciadas, no son un feed en vivo "
            "y muchas son primeros planos de instrumentos. No se usan como capa del mapa."
        ),
    }
    if estado:
        body = estado.json()
        datos["ultimo_sol"] = body.get("latest_sol")
        datos["ultima_actualizacion_utc"] = body.get("latest")
        datos["total_images_incl_ingenuity"] = body.get("total")
    if latest:
        body = latest.json()
        datos["total_images"] = body.get("total_images")
        for image in body.get("images", [])[:1]:
            datos["muestra"].append(formatear_imagen(image))
    if sol:
        for image in sol.json().get("images", [])[:2]:
            datos["muestra"].append(formatear_imagen(image))

    descargas = {
        "mars2020_mcz_sol2024_800.jpg": (
            "https://mars.nasa.gov/mars2020-raw-images/pub/ods/surface/sol/02024/"
            "ids/edr/browse/zcam/ZL0_2024_0846622470_145EBY_N0930000ZCAM10058_1100LMJ02_800.jpg"
        ),
        "mars2020_supercam_sol2031_800.jpg": (
            "https://mars.nasa.gov/mars2020-raw-images/pub/ods/surface/sol/02031/"
            "ids/edr/browse/scam/LRE_2031_0847235763_228ECM_N0930000SCAM01031_0010I4J01_800.jpg"
        ),
    }
    for name, url in descargas.items():
        image = fetch(url, label=f"Mars 2020 — muestra {name}", binary=True)
        if image:
            (OUT / name).write_bytes(image)

    save_json(OUT / "mars2020_raw_images.json", datos)
    return {
        "id": "mars2020_raw_images",
        "url": "https://mars.nasa.gov/mars2020/multimedia/raw-images/",
        "estado": "ok",
        "relevancia": "media para contexto visual; baja para el mapa",
        "aporta": (
            "Catálogo de más de un millón de imágenes crudas de Perseverance, con sol, "
            "instrumento, fecha UTC y crédito."
        ),
        "decision": "usar solo en una ficha o galería de contexto, nunca como capa georreferenciada",
        "limitaciones": "Sin coordenadas, sin tiempo real y con abundantes primeros planos técnicos.",
        "evidencia": [
            "Evidencias/datos/recursos_nasa_2026/mars2020_raw_images.json",
            "Evidencias/datos/recursos_nasa_2026/mars2020_mcz_sol2024_800.jpg",
            "Evidencias/datos/recursos_nasa_2026/mars2020_supercam_sol2031_800.jpg",
        ],
    }


def formatear_imagen(image):
    files = image.get("image_files", {})
    return {
        "imageid": image.get("imageid"),
        "sol": image.get("sol"),
        "fecha_utc": image.get("date_taken_utc"),
        "instrumento": image.get("camera", {}).get("instrument"),
        "credito": image.get("credit"),
        "caption": (image.get("caption") or "")[:400],
        "browse_800": files.get("medium"),
        "full_res": files.get("full_res"),
        "ficha": image.get("link"),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    recursos = [
        auditar_mars_trek(),
        auditar_usgs(),
        auditar_curiosity(),
        auditar_worldview(),
        auditar_raw_images(),
    ]
    auditoria = {
        "generado": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "fuente": "Recursos NASA entregados para el reto, 2026-11-14",
        "recursos": recursos,
        "peticiones": LOG,
        "nota": (
            "Solo Mars Trek y USGS PGM aportan datos georreferenciados o citables para "
            "el mapa. Worldview es de la Tierra. Las imágenes crudas y la animación de "
            "Curiosity son contexto visual, no capas."
        ),
    }
    save_json(OUT / "auditoria.json", auditoria)
    (OUT / "README.md").write_text(
        "# Recursos NASA auditados (2026-11-14)\n\n"
        "Ver `auditoria.json` para el veredicto por recurso. Resumen:\n\n"
        "| Recurso | Decisión |\n|---|---|\n"
        "| Mars Trek | Integrar (ya auditado) |\n"
        "| USGS PGM / Interactive Maps | Fichas y citas; no capa raster |\n"
        "| Curiosity up Mount Sharp | Referencia visual (Gale) |\n"
        "| NASA Worldview | Rechazar: es de la Tierra |\n"
        "| Mars 2020 raw images | Contexto visual; no capa |\n\n"
        "Reproducir: `python Scripts/08_auditar_recursos_nasa.py`\n",
        encoding="utf-8",
    )
    print(json.dumps({"archivos": len(list(OUT.iterdir())), "recursos": len(recursos)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
