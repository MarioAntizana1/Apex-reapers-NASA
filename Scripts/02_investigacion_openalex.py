import csv
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(__file__).resolve().parent / "queries_openalex.json"
OUT_DIR = ROOT / "Evidencias" / "datos" / "openalex"
CSV_PATH = ROOT / "Evidencias" / "datos" / "openalex_resultados.csv"
MD_PATH = ROOT / "Evidencias" / "datos" / "openalex_resumen.md"
API = "https://api.openalex.org/works"
SELECT = ",".join([
    "id",
    "doi",
    "title",
    "publication_year",
    "cited_by_count",
    "type",
    "authorships",
    "primary_location",
    "open_access",
])


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text[:90]


def authors(work: dict, limit: int = 4) -> str:
    names = []
    for item in work.get("authorships") or []:
        name = (item.get("author") or {}).get("display_name")
        if name:
            names.append(name)
        if len(names) >= limit:
            break
    return "; ".join(names)


def source_name(work: dict) -> str:
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    return source.get("display_name") or location.get("landing_page_url") or ""


def fetch(query: str, per_page: int, mailto: str) -> dict:
    params = {
        "search": query,
        "per-page": per_page,
        "select": SELECT,
        "mailto": mailto,
        "sort": "relevance_score:desc",
    }
    last_error = None
    for attempt in range(4):
        try:
            response = requests.get(API, params=params, timeout=60)
            if response.status_code == 429:
                time.sleep(2 + attempt * 2)
                continue
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            time.sleep(1 + attempt)
    raise RuntimeError(f"No se pudo consultar OpenAlex: {last_error}")


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    mailto = config.get("mailto", "1010034@utp.edu.pe")
    per_page = int(config.get("per_page", 6))
    queries = config.get("queries", [])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    summary = [
        "# Resultados de la revisión exploratoria en OpenAlex",
        "",
        f"Consulta ejecutada: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Correo de contacto (polite pool): {mailto}",
        f"Resultados por consulta: {per_page}",
        "",
        "Los resultados son candidatos bibliográficos para revisión; no equivalen a una revisión sistemática completa.",
        "",
    ]

    for index, item in enumerate(queries, start=1):
        category = item.get("category", "Sin categoría")
        query = item["query"]
        print(f"[{index}/{len(queries)}] {category}: {query}")
        payload = fetch(query, per_page, mailto)
        results = payload.get("results", [])
        raw_path = OUT_DIR / f"{index:02d}_{slug(query)}.json"
        raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        summary.append(f"## {category}: {query}")
        summary.append("")
        if not results:
            summary.append("Sin resultados.")
            summary.append("")
            continue
        for work in results:
            title = (work.get("title") or "Sin título").strip()
            year = work.get("publication_year") or ""
            doi = work.get("doi") or ""
            citations = work.get("cited_by_count", 0)
            oa = "Sí" if (work.get("open_access") or {}).get("is_oa") else "No"
            venue = source_name(work)
            rows.append({
                "categoria": category,
                "consulta": query,
                "titulo": title,
                "anio": year,
                "doi": doi,
                "citas": citations,
                "acceso_abierto": oa,
                "tipo": work.get("type", ""),
                "fuente": venue,
                "autores": authors(work),
                "openalex_url": work.get("id", ""),
                "doi_url": f"https://doi.org/{doi.replace('https://doi.org/', '')}" if doi else "",
            })
            summary.append(f"- ({year}) {title}. {venue}. Citas: {citations}. Acceso abierto: {oa}. {doi}")
        summary.append("")
        time.sleep(0.25)

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)

    summary.append("## Archivos generados")
    summary.append("")
    summary.append(f"- CSV consolidado: `{CSV_PATH.relative_to(ROOT)}`")
    summary.append(f"- Respuestas crudas: `{OUT_DIR.relative_to(ROOT)}`")
    summary.append("")
    MD_PATH.write_text("\n".join(summary), encoding="utf-8")
    print(f"OK: {len(rows)} registros")
    print(f"CSV: {CSV_PATH}")
    print(f"Resumen: {MD_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
