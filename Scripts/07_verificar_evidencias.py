import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "Evidencias"
MANIFEST = EVIDENCE / "manifiesto.csv"
REPORT = EVIDENCE / "verificacion.json"
EXCLUDE = {MANIFEST.name, REPORT.name}


def sha256(path, chunk=1024 * 1024):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def collect():
    rows = []
    for path in sorted(EVIDENCE.rglob("*")):
        if not path.is_file():
            continue
        if path.name in EXCLUDE:
            continue
        stat = path.stat()
        rows.append({
            "ruta": str(path.relative_to(ROOT)),
            "bytes": stat.st_size,
            "modificado": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime)),
            "sha256": sha256(path),
        })
    return rows


def write_manifest(rows):
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["ruta", "bytes", "modificado", "sha256"])
        writer.writeheader()
        writer.writerows(rows)


def check(rows):
    if not MANIFEST.exists():
        return {"estado": "sin_manifiesto", "faltantes": [], "cambiados": [], "nuevos": []}
    with MANIFEST.open(encoding="utf-8-sig", newline="") as handle:
        previous = {row["ruta"]: row for row in csv.DictReader(handle)}
    current = {row["ruta"]: row for row in rows}
    faltantes = sorted(set(previous) - set(current))
    nuevos = sorted(set(current) - set(previous))
    cambiados = sorted(
        path for path in set(previous) & set(current)
        if previous[path]["sha256"] != current[path]["sha256"]
    )
    return {"estado": "ok" if not (faltantes or cambiados) else "revisar", "faltantes": faltantes, "cambiados": cambiados, "nuevos": nuevos}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows = collect()
    report = {
        "generado": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "archivos": len(rows),
        "bytes": sum(row["bytes"] for row in rows),
        "check": check(rows) if args.check else None,
    }
    if not args.check:
        write_manifest(rows)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not args.check or report["check"]["estado"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
