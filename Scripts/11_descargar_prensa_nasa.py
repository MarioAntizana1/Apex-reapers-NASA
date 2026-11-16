"""Descarga la coleccion de imagenes de prensa de NASA sobre Jezero.

Fuente: NASA Image and Video Library (https://images.nasa.gov/), API publica
https://images-api.nasa.gov/search?q=Jezero&media_type=image

Incluye vistas orbitales, mapas, graficos de elevacion, imagenes del rover,
conceptos artisticos y figuras de misiones. Se guarda el original cuando pesa
menos de 25 MB; si no, la version grande. Los creditos y la fecha se conservan
en el catalogo.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Evidencias" / "datos" / "jezero"
DEST = OUT / "prensa"
SEARCH = "https://images-api.nasa.gov/search"
UA = "AresAtlas/1.0 (NASA Space Apps 2026; evidencia cientifica)"
TIMEOUT = (20, 120)
MAX_BYTES = 25 * 1024 * 1024


def slug(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text[:70] or "imagen"


def search(session: requests.Session) -> list[dict]:
    items = []
    for page in (1, 2, 3):
        response = session.get(SEARCH, params={"q": "Jezero", "media_type": "image", "page_size": 100, "page": page},
                               timeout=TIMEOUT, headers={"User-Agent": UA})
        response.raise_for_status()
        collection = response.json().get("collection", {})
        batch = collection.get("items", [])
        print(f"[page] {page}: {len(batch)} resultados (total {collection.get('metadata', {}).get('total_hits')})")
        if not batch:
            break
        items.extend(batch)
    unique = {}
    for item in items:
        data = (item.get("data") or [{}])[0]
        nasa_id = data.get("nasa_id")
        if nasa_id:
            unique[nasa_id] = item
    return list(unique.values())


def best_asset(session: requests.Session, item: dict) -> tuple[str, str]:
    nasa_id = item["data"][0]["nasa_id"]
    response = session.get(f"https://images-api.nasa.gov/asset/{nasa_id}", timeout=TIMEOUT,
                           headers={"User-Agent": UA})
    response.raise_for_status()
    assets = [entry.get("href", "") for entry in response.json().get("collection", {}).get("items", [])]
    jpgs = [url for url in assets if url.lower().endswith((".jpg", ".jpeg"))]
    orig = [url for url in jpgs if "~orig" in url]
    large = [url for url in jpgs if "~large" in url]
    medium = [url for url in jpgs if "~medium" in url]
    for candidate in (*orig, *large, *medium, *jpgs):
        try:
            head = session.head(candidate, timeout=TIMEOUT, allow_redirects=True, headers={"User-Agent": UA})
            size = int(head.headers.get("content-length", "0") or 0)
            if size and size <= MAX_BYTES:
                return candidate, ""
        except Exception:  # noqa: BLE001
            continue
    if orig:
        return orig[0], "orig_mayor_25mb"
    if large:
        return large[0], "sin_orig"
    return (jpgs[0] if jpgs else ""), "solo_jpg"


def download(session: requests.Session, item: dict) -> dict:
    data = item["data"][0]
    nasa_id = data.get("nasa_id", "sin_id")
    title = data.get("title", "")
    dest = DEST / f"{nasa_id}_{slug(title)}.jpg"
    if dest.exists() and dest.stat().st_size > 5_000:
        return {**data, "archivo": str(dest.relative_to(ROOT)), "bytes": dest.stat().st_size,
                "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(), "estado": "ok", "url_imagen": ""}
    try:
        url, note = best_asset(session, item)
        if not url:
            return {**data, "archivo": "", "bytes": 0, "sha256": "", "estado": "error",
                    "detalle": "sin asset jpg", "url_imagen": ""}
        response = session.get(url, timeout=TIMEOUT, headers={"User-Agent": UA})
        response.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(response.content)
        print(f"[ok] {nasa_id:<12} {len(response.content):>10,} B  {title[:70]}")
        return {**data, "archivo": str(dest.relative_to(ROOT)), "bytes": len(response.content),
                "sha256": hashlib.sha256(response.content).hexdigest(), "estado": "ok",
                "url_imagen": url, "detalle": note}
    except Exception as exc:  # noqa: BLE001
        print(f"[err] {nasa_id}: {exc}")
        return {**data, "archivo": "", "bytes": 0, "sha256": "", "estado": "error",
                "detalle": str(exc), "url_imagen": ""}


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    items = search(session)
    print(f"Total unico: {len(items)} imagenes")
    results = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(download, session, item): item for item in items}
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: item.get("nasa_id", ""))

    fields = ["nasa_id", "title", "description", "date_created", "center", "secondary_creator",
              "photographer", "credit", "archivo", "bytes", "sha256", "estado", "url_imagen", "detalle"]
    with (OUT / "catalogo_prensa.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in results:
            writer.writerow({key: item.get(key, "") for key in fields})
    (OUT / "catalogo_prensa.json").write_text(json.dumps({
        "generado": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "fuente": "https://images.nasa.gov/search?q=Jezero",
        "licencia": "NASA; ver creditos por imagen. Uso educativo y cientifico.",
        "total": len(results),
        "correctos": sum(1 for item in results if item.get("estado") == "ok"),
        "imagenes": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for item in results if item.get("estado") == "ok")
    print(f"\n{ok}/{len(results)} imagenes descargadas")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
