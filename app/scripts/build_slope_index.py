"""Genera la malla de costo de pendiente que usa el planificador de rutas.

Entrada:  public/maps/jezero_ctx_dem_20m_slope.jpg  (capa "ctx-dem-slope" del catálogo)
Salidas:  public/terrain/slope_index_60m.png   -> índice 0-255 por celda (escala de grises)
          public/terrain/slope_index.json      -> metadatos, extensión y supuestos

SUPUESTOS (revisar antes de usar en ciencia o navegación):
- La imagen de pendientes es una rampa de color continua verde -> amarillo -> naranja
  -> rojo (-> violeta en los casos más extremos). No incluye leyenda numérica en
  grados, así que el índice es RELATIVO: 0 = liso, 255 = el valor más alto de la
  rampa. No se afirma que equivalga a grados reales.
- El tono (H) es robusto al sombreado del relieve y a la compresión JPEG; por eso el
  índice se deriva del tono y no del brillo.
- La rejilla se agrega a ~60 m por celda con promedio por área, que es la resolución
  con la que el planificador A* puede trabajar en el navegador.
- Las celdas fuera de la imagen no existen: la rejilla cubre exactamente la extensión
  declarada en layers.json para esta capa.

Regenerar:  python scripts/build_slope_index.py
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
APP = HERE.parent
PUBLIC = APP / "public"
SLOPE_IMAGE = PUBLIC / "maps" / "jezero_ctx_dem_20m_slope.jpg"
OUT_DIR = PUBLIC / "terrain"

# Extensión declarada por la capa ctx-dem-slope en public/layers.json: [xmin, ymin, xmax, ymax].
EXTENT = (-25446.7, -51538.2, 63681.8, 49801.8)
TARGET_CELL_METRES = 60.0

# Puntos de control tono(°) -> índice(0-1). Interpolación lineal entre ellos.
RAMP = [
    (0.0, 0.97),
    (15.0, 0.88),
    (35.0, 0.66),
    (55.0, 0.42),
    (75.0, 0.18),
    (95.0, 0.04),
    (110.0, 0.00),
    (180.0, 0.00),
    (200.0, 0.55),
    (260.0, 1.00),
    (300.0, 1.00),
]


def severity_from_hue(hue_deg: float) -> float:
    if hue_deg <= RAMP[0][0]:
        return RAMP[0][1]
    for (h0, v0), (h1, v1) in zip(RAMP, RAMP[1:]):
        if h0 <= hue_deg <= h1:
            t = (hue_deg - h0) / (h1 - h0)
            return v0 + t * (v1 - v0)
    return 0.0


def quantize(value: int) -> int:
    return (value // 8) * 8


def build_lut() -> list[int]:
    # Canal H de Pillow: 0-255 donde 255 equivale a 360°.
    lut = []
    for i in range(256):
        hue = i * 360.0 / 255.0
        lut.append(int(round(severity_from_hue(hue) * 255)))
    return lut


def main() -> None:
    if not SLOPE_IMAGE.exists():
        raise SystemExit(f"No se encontró la capa de pendientes: {SLOPE_IMAGE}")

    xmin, ymin, xmax, ymax = EXTENT
    width_m, height_m = xmax - xmin, ymax - ymin
    cols = max(1, int(round(width_m / TARGET_CELL_METRES)))
    rows = max(1, int(round(height_m / TARGET_CELL_METRES)))
    res_x, res_y = width_m / cols, height_m / rows

    source = Image.open(SLOPE_IMAGE).convert("HSV")
    if source.size != (3602, 4096):
        print(f"aviso: se esperaba 3602x4096, la imagen es {source.size[0]}x{source.size[1]}")

    hue = source.split()[0]
    severity = hue.point(build_lut())  # reasigna tono -> índice, a resolución nativa
    grid = severity.resize((cols, rows), Image.Resampling.BOX)  # promedio por área -> 60 m
    # Cuantizar a 32 niveles: el índice es una estimación relativa y así el PNG
    # comprime mucho mejor (2 MB -> ~0,3 MB) sin cambiar el comportamiento del A*.
    grid = grid.point(quantize)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUT_DIR / "slope_index_60m.png"
    grid.save(png_path, optimize=True)

    meta = {
        "id": "slope-index-60m",
        "name": "Malla de costo · índice de pendiente CTX",
        "sourceLayer": "ctx-dem-slope",
        "sourceImage": "maps/jezero_ctx_dem_20m_slope.jpg",
        "grid": "terrain/slope_index_60m.png",
        "units": "relative-index-0-255",
        "extent": [xmin, ymin, xmax, ymax],
        "width": cols,
        "height": rows,
        "resolution": {"x": round(res_x, 4), "y": round(res_y, 4)},
        "ramp": [{"hue": h, "index": round(v, 3)} for h, v in RAMP],
        "origin": "top-left",
        "noData": None,
        "generated": "2026-11-15",
        "notes": [
            "Índice relativo 0-255 derivado del tono de la capa de pendientes; no son grados validados.",
            "El índice no incorpora elevación, rugosidad ni obstáculos: es solo pendiente estimada.",
            "Rejilla agregada por área desde 20 m a ~60 m para que el cálculo quepa en el navegador.",
            "No sustituye un MDE con unidades verticales verificadas. No apto para navegación real.",
        ],
    }
    (OUT_DIR / "slope_index.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    values = list(grid.getdata())
    print(f"rejilla {cols}x{rows} celdas, resolución {res_x:.3f}x{res_y:.3f} m")
    print(f"índice min={min(values)} max={max(values)} media={sum(values)/len(values):.1f}")
    print(f"png {png_path.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
