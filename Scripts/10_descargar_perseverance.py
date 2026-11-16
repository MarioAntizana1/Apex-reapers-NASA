"""Descarga una seleccion representativa de imagenes de Perseverance e Ingenuity.

Fuente: NASA/JPL-Caltech, Mars 2020 raw images
(https://mars.nasa.gov/mars2020/multimedia/raw-images/), API publica RSS.

No se descargan las ~500.000 imagenes de la mision: se elige una muestra
estratificada por sol e instrumento para cubrir todos los tipos de camara,
la llegada, la travesia y el delta. Se guardan en:

    Evidencias/datos/jezero/superficie/perseverance/sol_XXXX/<instrumento>/*.jpg
    Evidencias/datos/jezero/superficie/ingenuity/sol_XXXX/*.jpg
    Evidencias/datos/jezero/catalogo_superficie.csv
    Evidencias/datos/jezero/catalogo_superficie.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Evidencias" / "datos" / "jezero"
DEST = OUT / "superficie"
API = "https://mars.nasa.gov/rss/api/"
UA = "AresAtlas/1.0 (NASA Space Apps 2026; evidencia cientifica)"
TIMEOUT = (20, 90)

SOLS = [0, 1, 2, 3, 4, 10, 20, 30, 42, 58, 100, 200, 300, 400, 500,
        600, 700, 800, 900, 1000, 1200, 1400, 1500, 1700, 1900, 2031]
INGENUITY_SOLS = [0, 30, 43, 58, 100, 300, 500, 800, 1069]
MAX_POR_SOL = 22
MAX_POR_INSTRUMENTO = 3


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fetch_feed(session: requests.Session, category: str, sol: int, page: int) -> list[dict]:
    params = {
        "feed": "raw_images",
        "category": category,
        "feedtype": "json",
        "num": 100,
        "page": page,
        "sol": sol,
    }
    response = session.get(API, params=params, timeout=TIMEOUT, headers={"User-Agent": UA})
    response.raise_for_status()
    return response.json().get("images", [])


def fetch_sol(session: requests.Session, category: str, sol: int) -> list[dict]:
    images = fetch_feed(session, category, sol, 0)
    # La API devuelve todos los resultados del sol en la primera pagina.
    return images


def choose(images: list[dict], limit: int) -> list[dict]:
    by_instrument: dict[str, list[dict]] = {}
    for image in images:
        instrument = image.get("camera", {}).get("instrument") or "UNKNOWN"
        by_instrument.setdefault(instrument, []).append(image)
    chosen = []
    for instrument, group in sorted(by_instrument.items()):
        group.sort(key=lambda item: item.get("imageid", ""))
        take = min(MAX_POR_INSTRUMENTO, len(group))
        if take == 1:
            indices = [0]
        else:
            indices = sorted({round(i * (len(group) - 1) / (take - 1)) for i in range(take)})
        chosen.extend(group[index] for index in indices)
    chosen.sort(key=lambda item: (item.get("camera", {}).get("instrument", ""), item.get("imageid", "")))
    return chosen[:limit]


def pick_url(image: dict) -> str:
    files = image.get("image_files", {})
    for key in ("large", "medium", "full_res", "small"):
        url = files.get(key)
        if url:
            return url
    return ""


def download_one(session: requests.Session, image: dict, category: str) -> dict:
    instrument = (image.get("camera", {}).get("instrument") or "UNKNOWN").replace("/", "_")
    sol = int(image.get("sol", 0))
    imageid = image.get("imageid", "sin_id")
    base = DEST / ("perseverance" if category == "mars2020" else "ingenuity") / f"sol_{sol:04d}" / instrument.lower()
    dest = base / f"{imageid}.jpg"
    if dest.exists() and dest.stat().st_size > 5_000:
        return {**image, "archivo": str(dest.relative_to(ROOT)), "bytes": dest.stat().st_size,
                "sha256": sha256_bytes(dest.read_bytes()), "estado": "ok", "instrumento": instrument}
    url = pick_url(image)
    if not url:
        return {**image, "archivo": "", "bytes": 0, "sha256": "", "estado": "error", "instrumento": instrument,
                "detalle": "sin URL"}
    try:
        response = session.get(url, timeout=TIMEOUT, headers={"User-Agent": UA})
        response.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(response.content)
        print(f"[ok] {category} sol {sol:>4} {instrument:<22} {len(response.content):>9,} B {imageid}")
        return {**image, "archivo": str(dest.relative_to(ROOT)), "bytes": len(response.content),
                "sha256": hashlib.sha256(response.content).hexdigest(), "estado": "ok",
                "instrumento": instrument, "url_imagen": url}
    except Exception as exc:  # noqa: BLE001
        print(f"[err] {category} sol {sol} {instrument}: {exc}")
        return {**image, "archivo": "", "bytes": 0, "sha256": "", "estado": "error", "instrumento": instrument,
                "detalle": str(exc), "url_imagen": url}


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    selected: list[tuple[str, dict]] = []
    for sol in SOLS:
        try:
            images = fetch_sol(session, "mars2020", sol)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] sol {sol}: {exc}")
            continue
        chosen = choose(images, MAX_POR_SOL)
        print(f"[sol ] {sol:>4}: {len(images):>4} disponibles, {len(chosen):>2} seleccionadas")
        selected.extend(("mars2020", image) for image in chosen)
    for sol in INGENUITY_SOLS:
        try:
            images = fetch_sol(session, "ingenuity", sol)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] ingenuity sol {sol}: {exc}")
            continue
        chosen = choose(images, 6)
        print(f"[ing ] {sol:>4}: {len(images):>4} disponibles, {len(chosen):>2} seleccionadas")
        selected.extend(("ingenuity", image) for image in chosen)

    results = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(download_one, session, image, category): (category, image)
                   for category, image in selected}
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: (item.get("sol", 0), item.get("camera", {}).get("instrument", ""), item.get("imageid", "")))

    fields = [
        "sol", "instrumento", "imageid", "fecha_utc", "titulo", "descripcion", "credito",
        "archivo", "bytes", "sha256", "estado", "url_imagen", "url_ficha", "detalle",
    ]
    with (OUT / "catalogo_superficie.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for image in results:
            writer.writerow({
                "sol": image.get("sol"),
                "instrumento": image.get("instrumento"),
                "imageid": image.get("imageid"),
                "fecha_utc": image.get("date_taken_utc"),
                "titulo": image.get("title"),
                "descripcion": image.get("caption"),
                "credito": image.get("credit"),
                "archivo": image.get("archivo"),
                "bytes": image.get("bytes"),
                "sha256": image.get("sha256"),
                "estado": image.get("estado"),
                "url_imagen": image.get("url_imagen", pick_url(image)),
                "url_ficha": image.get("link"),
                "detalle": image.get("detalle", ""),
            })
    (OUT / "catalogo_superficie.json").write_text(json.dumps({
        "generado": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "fuente": "https://mars.nasa.gov/mars2020/multimedia/raw-images/",
        "licencia": "NASA/JPL-Caltech; credito por instrumento segun metadatos",
        "soles": SOLS,
        "soles_ingenuity": INGENUITY_SOLS,
        "total": len(results),
        "correctos": sum(1 for item in results if item.get("estado") == "ok"),
        "instrumentos": sorted({item.get("instrumento") for item in results if item.get("instrumento")}),
        "imagenes": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for item in results if item.get("estado") == "ok")
    print(f"\n{ok}/{len(results)} imagenes descargadas")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
