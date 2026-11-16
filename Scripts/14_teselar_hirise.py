"""Genera teselas HiRISE locales para el área de la base, sin modificar el original."""
from pathlib import Path
import math

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "Evidencias/datos/jezero/orbital/ESP_036618_1985_NORTH_25cm.tif"
DEST = ROOT / "app/public/maps/hirise-north"
CRS = "+proj=eqc +lat_ts=18.45 +lat_0=18.45 +lon_0=77.45 +R=3396190 +units=m +no_defs"
X, Y, LENGTH, SIZE = -18823, 13996, 10000, 512
RESOLUTIONS = [8, 4, 2, 1, 0.5, 0.25]


def main():
    DEST.mkdir(parents=True, exist_ok=False)
    with rasterio.open(SOURCE) as src:
        for z, resolution in enumerate(RESOLUTIONS):
            pixels = math.ceil(LENGTH / resolution)
            count = math.ceil(pixels / SIZE)
            with WarpedVRT(src, crs=CRS, transform=from_origin(X, Y, resolution, resolution),
                           width=count * SIZE, height=count * SIZE, nodata=0,
                           resampling=Resampling.bilinear) as vrt:
                for row in range(count):
                    for col in range(count):
                        data = vrt.read(1, window=Window(col * SIZE, row * SIZE, SIZE, SIZE))
                        rgba = np.empty((SIZE, SIZE, 2), dtype=np.uint8)
                        rgba[:, :, 0] = data
                        rgba[:, :, 1] = np.where(data == 0, 0, 255)
                        path = DEST / str(z) / str(col) / f"{row}.png"
                        path.parent.mkdir(parents=True, exist_ok=True)
                        Image.fromarray(rgba, "LA").save(path, optimize=True)
                    print(f"nivel {z}: fila {row + 1}/{count}", flush=True)
    print("Teselas terminadas", flush=True)


if __name__ == "__main__":
    main()
