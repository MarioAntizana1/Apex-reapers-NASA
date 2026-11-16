"""Deriva alturas a 1 m para los fragmentos 3D existentes; conserva el DTM original."""
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "Evidencias/datos/jezero/topografia/hirise_individual/DTM_Jezero_CR_NORTH_1m.tif"
MANIFEST = ROOT / "app/public/terrain-3d/manifest.json"
DEST = ROOT / "app/public/terrain-3d-detail"
CRS = "+proj=eqc +lat_ts=18.45 +lat_0=18.45 +lon_0=77.45 +R=3396190 +units=m +no_defs"


def main():
    manifest = json.loads(MANIFEST.read_text())
    DEST.mkdir(parents=True, exist_ok=False)
    available = []
    with rasterio.open(SOURCE) as source:
        for col, row in manifest["chunks"]:
            transform = from_origin(manifest["west"] + col * 256 - 0.5,
                                    manifest["north"] - row * 256 + 0.5, 1, 1)
            with WarpedVRT(source, crs=CRS, transform=transform, width=257, height=257,
                           nodata=-32768, resampling=Resampling.bilinear) as vrt:
                data = vrt.read(1, masked=True)
            if np.ma.getmaskarray(data).any() or not np.isfinite(data).all():
                continue
            scaled = np.rint(data * 10)
            if scaled.min() < -32767 or scaled.max() > 32767:
                raise ValueError(f"Altura fuera de rango en {col}_{row}")
            (DEST / f"{col}_{row}.bin").write_bytes(scaled.astype("<i2").tobytes())
            available.append([col, row])
    (DEST / "manifest.json").write_text(json.dumps({"chunks": available}, separators=(",", ":")))
    print(f"Fragmentos de 1 m: {len(available)} de {len(manifest['chunks'])}")


if __name__ == "__main__":
    main()
