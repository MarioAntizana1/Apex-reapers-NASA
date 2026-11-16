"""Prepara fragmentos del DTM HiRISE para la demo 3D, sin alterar el original."""
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "Evidencias/datos/jezero/topografia/hirise_individual/DTM_Jezero_CR_NORTH_1m.tif"
DEST = ROOT / "app/public/terrain-3d"
CRS = "+proj=eqc +lat_ts=18.45 +lat_0=18.45 +lon_0=77.45 +R=3396190 +units=m +no_defs"
WEST, NORTH = -18823, 13996
STEP, CELLS, COUNT = 8, 32, 40


def main():
    DEST.mkdir(parents=True, exist_ok=False)
    size = COUNT * CELLS + 1
    with rasterio.open(SOURCE) as source:
        with WarpedVRT(source, crs=CRS, transform=from_origin(WEST - STEP / 2, NORTH + STEP / 2, STEP, STEP),
                       width=size, height=size, nodata=-32768, resampling=Resampling.bilinear) as vrt:
            height = vrt.read(1, masked=True)
    chunks = []
    for row in range(COUNT):
        for col in range(COUNT):
            data = height[row * CELLS:row * CELLS + CELLS + 1, col * CELLS:col * CELLS + CELLS + 1]
            if np.ma.getmaskarray(data).any() or not np.isfinite(data).all():
                continue
            (DEST / f"{col}_{row}.json").write_text(json.dumps(np.round(data, 2).tolist(), separators=(",", ":")))
            chunks.append([col, row])
    if not chunks:
        raise RuntimeError("No se encontraron fragmentos HiRISE completos")
    start = min(chunks, key=lambda c: math.hypot(c[0] * 256 + 128 - 5000, c[1] * 256 + 128 - 5000))
    (DEST / "manifest.json").write_text(json.dumps({"chunks": chunks, "start": start, "west": WEST, "north": NORTH,
                                                    "step": STEP, "cells": CELLS}, separators=(",", ":")))
    print(f"{len(chunks)} fragmentos; inicio {start}")


if __name__ == "__main__":
    main()
