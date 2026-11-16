import importlib
import platform
import shutil
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DIRS = ["Docs", "Evidencias", "Scripts", "Evidencias/datos", "Evidencias/papers", "Evidencias/web", "Evidencias/capturas"]
PACKAGES = ["requests", "pypdf", "PIL", "numpy", "tifffile"]
ENDPOINTS = [
    "https://trek.nasa.gov/mars/jpl/config/config.json",
    "https://pds-atmospheres.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda/readme.txt",
    "https://api.openalex.org/works?per-page=1",
    "https://api.spaceappschallenge.org/graphql",
]


def check_packages():
    results = {}
    for name in PACKAGES:
        try:
            module = importlib.import_module(name)
            results[name] = getattr(module, "__version__", "ok")
        except Exception as exc:
            results[name] = f"FALTA ({exc.__class__.__name__})"
    return results


def check_dirs():
    return {path: (ROOT / path).exists() for path in REQUIRED_DIRS}


def check_disk():
    total, used, free = shutil.disk_usage(ROOT)
    return {
        "total_gb": round(total / 1024**3, 2),
        "used_gb": round(used / 1024**3, 2),
        "free_gb": round(free / 1024**3, 2),
    }


def check_endpoints():
    results = {}
    for url in ENDPOINTS:
        try:
            response = requests.get(url, timeout=20, headers={"User-Agent": "AresAtlas/0.1"})
            if url.endswith('/graphql') and response.status_code == 400:
                results[url] = '400 (esperado)'
            else:
                results[url] = response.status_code
        except Exception as exc:
            results[url] = f"ERROR: {exc.__class__.__name__}"
    return results


def main():
    print("=" * 72)
    print("VERIFICACIÓN DE ENTORNO — Ares Atlas / NASA Space Apps 2026")
    print("=" * 72)
    print(f"Python: {sys.version.split()[0]}")
    print(f"Plataforma: {platform.platform()}")
    print(f"Raíz: {ROOT}")
    print()

    dirs = check_dirs()
    print("Carpetas:")
    for path, exists in dirs.items():
        print(f"  {'OK ' if exists else 'FALTA'} {path}")
    print()

    packages = check_packages()
    print("Paquetes:")
    for name, version in packages.items():
        print(f"  {name:10s} {version}")
    print()

    disk = check_disk()
    print("Disco:")
    for key, value in disk.items():
        print(f"  {key:9s} {value} GB")
    print()

    endpoints = check_endpoints()
    print("Endpoints:")
    for url, status in endpoints.items():
        print(f"  {status!s:12s} {url}")
    print()

    core_ok = all(dirs.values()) and disk["free_gb"] > 0.5 and all((isinstance(v, int) and v < 500) or v == '400 (esperado)' for v in endpoints.values())
    print("RESULTADO:", "OK" if core_ok else "REVISAR")
    return 0 if core_ok else 1


if __name__ == "__main__":
    sys.exit(main())
