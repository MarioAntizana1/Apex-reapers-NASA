import csv
import json
import statistics
import sys
from pathlib import Path

import requests

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Evidencias" / "datos" / "meda"
BASE = "https://pds-atmospheres.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda"
SOL = "1740"
DER = f"{BASE}/data_derived_env/sol_1740_1859/sol_1740"
CAL = f"{BASE}/data_calibrated_env/sol_1740_1859/sol_1740"
FILES = {
    "WE__1740___________DER_PS__________________P01.CSV": f"{DER}/WE__1740___________DER_PS__________________P01.CSV",
    "WE__1740___________DER_TIRS________________P01.CSV": f"{DER}/WE__1740___________DER_TIRS________________P01.CSV",
    "WE__1740___________DER_ANCILLARY___________P01.CSV": f"{DER}/WE__1740___________DER_ANCILLARY___________P01.CSV",
    "WE__1740___________CAL_ATS_________________P01.CSV": f"{CAL}/WE__1740___________CAL_ATS_________________P01.CSV",
    "WE__1740___________CAL_RHS_________________P01.CSV": f"{CAL}/WE__1740___________CAL_RHS_________________P01.CSV",
    "WE__1740___________CAL_RDS_________________P01.CSV": f"{CAL}/WE__1740___________CAL_RDS_________________P01.CSV",
}
STATS = [
    ("presion_pa", "WE__1740___________DER_PS__________________P01.CSV", "PRESSURE"),
    ("temperatura_ats_k", "WE__1740___________CAL_ATS_________________P01.CSV", "ATS_LOCAL_TEMP1"),
    ("humedad_a_pct", "WE__1740___________CAL_RHS_________________P01.CSV", "HUMICAP_A_HUMIDITY"),
    ("tirs_down_w_m2", "WE__1740___________DER_TIRS________________P01.CSV", "DOWNWARD_LW_IRRADIANCE"),
    ("tirs_up_w_m2", "WE__1740___________DER_TIRS________________P01.CSV", "UPWARD_LW_IRRADIANCE"),
    ("zenit_solar_deg", "WE__1740___________DER_ANCILLARY___________P01.CSV", "SOLAR_ZENITHAL_ANGLE"),
]


def download(name, url):
    target = OUT / name
    if target.exists() and target.stat().st_size > 0:
        print(f"SKIP {name} ({target.stat().st_size} B)")
        return target
    with requests.get(url, timeout=240, stream=True) as response:
        response.raise_for_status()
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    print(f"OK   {name} ({target.stat().st_size} B)")
    return target


def column_stats(path, column):
    values = []
    with path.open(encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            raw = row.get(column, "")
            try:
                values.append(float(raw))
            except Exception:
                continue
    if not values:
        return None
    return {
        "n": len(values),
        "min": round(min(values), 3),
        "max": round(max(values), 3),
        "mean": round(statistics.fmean(values), 3),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        download(name, url)

    stats = {
        "sol": SOL,
        "fuente": BASE,
        "archivos": sorted(path.name for path in OUT.glob("*.CSV")),
        "variables": {},
    }
    for label, name, column in STATS:
        path = OUT / name
        if path.exists():
            result = column_stats(path, column)
            if result:
                stats["variables"][label] = result
                print(f"{label:20s} {result}")

    path = OUT / "estadisticas_meda.json"
    path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
