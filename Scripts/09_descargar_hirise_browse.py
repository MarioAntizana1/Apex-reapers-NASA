"""Cataloga y descarga las imagenes HiRISE que mencionan Jezero.

Fuente: University of Arizona, HiRISE (NASA/JPL/UA).
Busqueda: https://uahirise.org/results.php?keyword=Jezero (261 resultados, 11 paginas).

Descarga la vista detalle JPEG de cada observacion y escribe:
    Evidencias/datos/jezero/orbital/hirise_browse/*.jpg
    Evidencias/datos/jezero/catalogo_hirise_browse.csv
    Evidencias/datos/jezero/catalogo_hirise_browse.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Evidencias" / "datos" / "jezero"
DEST = OUT / "orbital" / "hirise_browse"
BASE = "https://uahirise.org"
UA = "AresAtlas/1.0 (NASA Space Apps 2026; evidencia cientifica)"
TIMEOUT = (20, 90)
PATTERN = re.compile(
    r"<a href='(?P<id>(?:ESP|PSP|DTEEC)_\d{6}_\d{4})'>"
    r"<img src='(?P<thumb>https://static\.uahirise\.org/images/(?P<year>\d{4})/thumb/[^']+)'"
    r"[^>]*alt='(?P<title>[^']*)'[^>]*>.*?"
    r"Lat:\s*(?P<lat>-?[\d.]+)&deg;\s*Long:\s*(?P<lon>-?[\d.]+)&deg;",
    re.S,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def collect(session: requests.Session) -> list[dict]:
    records: dict[str, dict] = {}
    for page in range(1, 20):
        url = f"{BASE}/results.php?keyword=Jezero&page={page}"
        response = session.get(url, timeout=TIMEOUT, headers={"User-Agent": UA})
        if response.status_code != 200:
            print(f"[warn] pagina {page}: HTTP {response.status_code}")
            continue
        found = 0
        for match in PATTERN.finditer(response.text):
            item = match.groupdict()
            if item["id"] in records:
                continue
            year = item["year"]
            records[item["id"]] = {
                "id": item["id"],
                "titulo": item["title"].strip(),
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
                "year": year,
                "thumb_url": item["thumb"],
                "detail_url": f"https://static.uahirise.org/images/{year}/details/{item['id']}.jpg",
                "pagina": page,
                "url_ficha": f"{BASE}/{item['id']}",
            }
            found += 1
        print(f"[page] {page}: {found} nuevas, {len(records)} acumuladas")
        if found == 0:
            break
    return sorted(records.values(), key=lambda item: item["id"])


def download(item: dict, session: requests.Session) -> dict:
    dest = DEST / f"{item['id']}.jpg"
    if dest.exists() and dest.stat().st_size > 10_000:
        return {**item, "archivo": str(dest.relative_to(ROOT)), "bytes": dest.stat().st_size,
                "sha256": sha256(dest), "estado": "ok", "variante": "detail" if "detail" in item.get("_used", "") else "cache"}
    for variant, url in (("detail", item["detail_url"]), ("thumb", item["thumb_url"])):
        try:
            response = session.get(url, timeout=TIMEOUT, headers={"User-Agent": UA})
            if response.status_code == 200 and len(response.content) > 8_000:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(response.content)
                print(f"[ok] {item['id']} {len(response.content):,} B ({variant})")
                return {**item, "archivo": str(dest.relative_to(ROOT)), "bytes": len(response.content),
                        "sha256": hashlib.sha256(response.content).hexdigest(), "estado": "ok",
                        "variante": variant, "_used": variant}
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] {item['id']} {variant}: {exc}")
    print(f"[err] {item['id']} sin imagen")
    return {**item, "archivo": "", "bytes": 0, "sha256": "", "estado": "error", "variante": ""}


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    records = collect(session)
    print(f"Total catalogo: {len(records)} imagenes HiRISE")
    results = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(download, item, session): item for item in records}
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: item["id"])

    fields = ["id", "titulo", "lat", "lon", "year", "pagina", "variante", "archivo", "bytes", "sha256", "estado", "detail_url", "thumb_url", "url_ficha"]
    with (OUT / "catalogo_hirise_browse.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow({key: row.get(key, "") for key in fields})
    (OUT / "catalogo_hirise_browse.json").write_text(json.dumps({
        "generado": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "fuente": "https://uahirise.org/results.php?keyword=Jezero",
        "licencia": "NASA/JPL/University of Arizona; uso educativo y cientifico con atribucion",
        "total": len(results),
        "correctos": sum(1 for item in results if item.get("estado") == "ok"),
        "imagenes": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for item in results if item.get("estado") == "ok")
    print(f"\n{ok}/{len(results)} imagenes descargadas")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
