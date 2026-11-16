import csv
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(__file__).resolve().parent / "queries_ntrs.json"
OUT = ROOT / "Evidencias" / "datos" / "ntrs"
PAPERS = ROOT / "Evidencias" / "papers" / "ntrs_auto"
CSV_PATH = ROOT / "Evidencias" / "datos" / "ntrs_resultados.csv"
MD_PATH = ROOT / "Evidencias" / "datos" / "ntrs_resumen.md"
API = "https://ntrs.nasa.gov/api/citations/search"


def slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()[:80]


def search(query, size):
    response = requests.post(API, json={"q": query, "page": {"size": size}}, timeout=90)
    response.raise_for_status()
    return response.json()


def pdf_link(item):
    for download in item.get("downloads", []) or []:
        link = (download.get("links") or {}).get("pdf")
        if link:
            return "https://ntrs.nasa.gov" + link
    return ""


def download_pdf(item, max_mb):
    link = pdf_link(item)
    if not link:
        return None
    target = PAPERS / f"ntrs_{item.get('id')}.pdf"
    if target.exists():
        return target
    response = requests.get(link, timeout=180)
    if response.status_code != 200:
        return None
    if not response.headers.get("content-type", "").startswith("application/pdf"):
        return None
    if len(response.content) > max_mb * 1024 * 1024:
        return None
    target.write_bytes(response.content)
    return target


def main():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    size = int(config.get("page_size", 8))
    download = bool(config.get("download_pdfs", True))
    max_mb = float(config.get("max_pdf_mb", 12))
    queries = config.get("queries", [])
    OUT.mkdir(parents=True, exist_ok=True)
    PAPERS.mkdir(parents=True, exist_ok=True)

    rows = []
    summary = [
        "# Resultados de la búsqueda en NASA NTRS",
        "",
        f"Consulta ejecutada: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Resultados por consulta: {size}",
        "",
    ]
    downloads_done = 0

    for index, item in enumerate(queries, start=1):
        category = item.get("category", "Sin categoría")
        query = item["query"]
        print(f"[{index}/{len(queries)}] {category}: {query}")
        try:
            payload = search(query, size)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            continue
        results = payload.get("results", [])
        raw_path = OUT / f"{index:02d}_{slug(query)}.json"
        raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        summary.append(f"## {category}: {query}")
        summary.append("")
        if not results:
            summary.append("Sin resultados.")
            summary.append("")
            continue
        for result in results:
            date = ""
            publications = result.get("publications") or []
            if publications:
                date = (publications[0].get("publicationDate") or "")[:10]
            abstract = re.sub(r"<[^>]+>", " ", result.get("abstract") or "")
            abstract = re.sub(r"\s+", " ", abstract).strip()
            link = pdf_link(result)
            rows.append({
                "categoria": category,
                "consulta": query,
                "id": result.get("id", ""),
                "titulo": result.get("title", ""),
                "fecha": date,
                "tipo": result.get("stiType", ""),
                "resumen": abstract[:1200],
                "pdf": link,
            })
            summary.append(f"- [{date}] {result.get('title', '')} (NTRS {result.get('id', '')})")
            if download and link and downloads_done < 12:
                downloaded = download_pdf(result, max_mb)
                if downloaded:
                    downloads_done += 1
                    summary.append(f"  - PDF: `{downloaded.relative_to(ROOT)}`")
        summary.append("")
        time.sleep(0.2)

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)

    summary.append("## Archivos generados")
    summary.append("")
    summary.append(f"- CSV: `{CSV_PATH.relative_to(ROOT)}`")
    summary.append(f"- Respuestas crudas: `{OUT.relative_to(ROOT)}`")
    summary.append(f"- PDFs: `{PAPERS.relative_to(ROOT)}`")
    summary.append(f"- PDFs descargados en esta ejecución: {downloads_done}")
    MD_PATH.write_text("\n".join(summary), encoding="utf-8")
    print(f"OK: {len(rows)} registros; {downloads_done} PDFs")
    print(f"CSV: {CSV_PATH}")
    print(f"Resumen: {MD_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
