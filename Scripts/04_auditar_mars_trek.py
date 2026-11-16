import csv
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Evidencias" / "datos" / "mars_trek"
GEO = OUT / "geojson"
BASE = "https://trek.nasa.gov/mars"
TIMEOUT = 120
BBOX = "77.0,17.9,78.1,19.0"

STATIC = {
    "config.json": f"{BASE}/jpl/config/config.json",
    "basemapList.json": f"{BASE}/jpl/config/basemapList.json",
    "staticLayers.json": f"{BASE}/jpl/config/staticLayers.json",
    "autoLayers.json": f"{BASE}/jpl/config/autoLayers.json",
    "facetStructure.json": f"{BASE}/jpl/config/facetStructure.json",
    "services.json": f"{BASE}/trekarcgis/rest/services?f=pjson",
    "raster_list_eq.json": f"{BASE}/tiles/Mars/rasters/eq/list.json",
}

FEATURES = {
    "perseverance_traverse.geojson": ("Perseverance_Traverse_Path/MapServer/0", True),
    "mars2020_waypoints.geojson": ("mars2020_waypoints/MapServer/0", False),
    "landing_ellipse.geojson": ("perseverance_landing_ellipse/MapServer/0", False),
    "ez_roi_jezero.geojson": ("EZMars/MapServer/3", False),
    "ez_buffer_jezero.geojson": ("EZMars/MapServer/4", False),
    "hydrous_minerals.geojson": ("Hydrous_Mineral_Detections_OMEGA_CRISM_clon0/MapServer/0", False),
    "global_geology.geojson": ("SIM3292_Global_Geology/MapServer/0", False),
    "mars2020_sites.geojson": ("mars2020/MapServer/0", False),
}

RASTERS = {
    "jezero_viking_base.png": (
        f"{BASE}/trekarcgis/rest/services/Mars_Viking_MDIM21_ClrMosaic_global_232m/ImageServer/exportImage",
        {"bbox": "77.2,18.1,77.9,18.8", "bboxSR": "4326", "imageSR": "4326", "size": "2048,2048", "format": "png32", "f": "image"},
    ),
    "jezero_mola_shade.png": (
        f"{BASE}/trekarcgis/rest/services/Mars_MOLA_blend200ppx_HRSC_Shade_clon0dd_200mpp_lzw/ImageServer/exportImage",
        {"bbox": "77.2,18.1,77.9,18.8", "bboxSR": "4326", "imageSR": "4326", "size": "2048,2048", "format": "png32", "f": "image"},
    ),
    "jezero_mola_dem.tif": (
        f"{BASE}/trekarcgis/rest/services/mola128_mola64_merge_90Nto90S_SimpleC_clon0/ImageServer/exportImage",
        {"bbox": "77.2,18.1,77.9,18.8", "bboxSR": "4326", "imageSR": "4326", "size": "1024,1024", "format": "tiff", "f": "image"},
    ),
}

MANIFEST = []


def fetch(url, params=None, label="", binary=False):
    started = time.time()
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        content = response.content
        status = response.status_code
        content_type = response.headers.get("content-type", "")
        elapsed = round(time.time() - started, 2)
        MANIFEST.append({
            "recurso": label or url,
            "url": response.url,
            "estado": status,
            "tipo": content_type,
            "bytes": len(content),
            "segundos": elapsed,
        })
        print(f"[{status}] {len(content):>10} B  {elapsed:>6.2f}s  {label or url}")
        return response, content
    except Exception as exc:
        MANIFEST.append({
            "recurso": label or url,
            "url": url,
            "estado": "ERROR",
            "tipo": "",
            "bytes": 0,
            "segundos": round(time.time() - started, 2),
            "detalle": str(exc),
        })
        print(f"[ERROR] {label or url}: {exc}")
        return None, None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    GEO.mkdir(parents=True, exist_ok=True)

    for name, url in STATIC.items():
        response, content = fetch(url, label=name)
        if response is not None and response.status_code == 200:
            (OUT / name).write_bytes(content)

    services = {}
    services_path = OUT / "services.json"
    if services_path.exists():
        services = json.loads(services_path.read_text(encoding="utf-8"))
    service_names = [item.get("name") for item in services.get("services", [])]
    (OUT / "servicios_vectores.txt").write_text("\n".join(service_names), encoding="utf-8")

    for name, (service, simplify) in FEATURES.items():
        params = {
            "where": "1=1",
            "geometry": BBOX,
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
        }
        if simplify:
            params["maxAllowableOffset"] = "0.00005"
        response, content = fetch(f"{BASE}/trekarcgis/rest/services/{service}/query", params=params, label=name)
        if response is not None and response.status_code == 200:
            (GEO / name).write_bytes(content)
            try:
                payload = json.loads(content)
                count = len(payload.get("features", []))
                MANIFEST[-1]["features"] = count
            except Exception:
                pass

    for name, (url, params) in RASTERS.items():
        response, content = fetch(url, params=params, label=name)
        if response is not None and response.status_code == 200:
            (OUT / name).write_bytes(content)

    manifest_path = OUT / "manifiesto_mars_trek.csv"
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["recurso", "url", "estado", "tipo", "bytes", "segundos", "features", "detalle"])
        writer.writeheader()
        for row in MANIFEST:
            writer.writerow({key: row.get(key, "") for key in writer.fieldnames})

    summary = {
        "generado": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "bbox_jezero": BBOX,
        "total_recursos": len(MANIFEST),
        "correctos": sum(1 for row in MANIFEST if row.get("estado") == 200),
        "errores": sum(1 for row in MANIFEST if row.get("estado") != 200),
        "features": {row["recurso"]: row.get("features") for row in MANIFEST if "features" in row},
        "servicios": len(service_names),
    }
    (OUT / "auditoria.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
