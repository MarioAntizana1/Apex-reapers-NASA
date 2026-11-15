"""Genera las mallas de terreno que usa el planificador de rutas.

Entradas (capas del catálogo public/layers.json):
  public/maps/jezero_ctx_dem_20m_slope.jpg      capa "ctx-dem-slope"
  public/maps/jezero_ctx_dem_20m_color.jpg      capa "ctx-dem-20m-color"

Salidas:
  public/terrain/slope_index_60m.png  -> índice de pendiente 0-255 por celda
  public/terrain/elevation_60m.png    -> índice de altura relativa 0-255 por celda
  public/terrain/terrain.json         -> metadatos, extensión, calibración y supuestos

QUÉ REPRESENTA CADA MALLA
- Pendiente: el "piso" del terreno. Una ladera empinada encarece el paso y las crestas
  extremas se marcan como intransitables.
- Altura: el relieve de gran escala. Sirve para cobrar el ASCENSO acumulado, que es lo
  que hace que el planificador prefiera rodear una montaña en vez de subirla.

SUPUESTOS (revisar antes de usar en ciencia o navegación):
- La capa de pendientes es una rampa de color continua verde -> amarillo -> naranja
  -> rojo (-> violeta en los casos más extremos), sin leyenda numérica en grados. El
  índice es RELATIVO: 0 = liso, 255 = el valor más alto de la rampa.
- El tono (H) es robusto al sombreado del relieve y a la compresión JPEG; por eso el
  índice de pendiente se deriva del tono y no del brillo.
- La capa "MDE en color" es una rampa hipsométrica: el tono va de cian/azul (cota baja)
  a ámbar/rojo (cota alta). La altura se decodifica del TONO a resolución nativa y sólo
  después se promedia a 60 m; promediar el RGB antes de decodificar arrastra el gris de
  las zonas sin saturación hacia valores intermedios falsos.
- El tono no separa albedo de altura en las celdas muy desaturadas (blanco, hielo) ni en
  las muy oscuras; esas celdas se descartan y se rellenan con la vecindad.
- El relieve se suaviza con un desenfoque gaussiano de ~240 m: interesa el relieve de
  gran escala (borde del cráter, montes, delta), no el moteado de 20 m.
- La escala vertical es un SUPUESTO declarado: el desnivel total de la ventana se toma
  como 2000 m. De ahí sale metresPerIndex. No es una cota sobre el elipsoide.
- Las celdas fuera de la imagen no existen: la rejilla cubre exactamente la extensión
  declarada en layers.json para esta capa.

Regenerar:  python scripts/build_terrain_grids.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
APP = HERE.parent
PUBLIC = APP / "public"
MAPS = PUBLIC / "maps"
OUT_DIR = PUBLIC / "terrain"

SLOPE_IMAGE = MAPS / "jezero_ctx_dem_20m_slope.jpg"
COLOR_IMAGE = MAPS / "jezero_ctx_dem_20m_color.jpg"

# Extensión declarada por la capa ctx-dem-slope en public/layers.json: [xmin, ymin, xmax, ymax].
EXTENT = (-25446.7, -51538.2, 63681.8, 49801.8)
TARGET_CELL_METRES = 60.0

# Puntos de control tono(°) -> índice(0-1) de la rampa de PENDIENTES. Interpolación lineal.
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

# Rampa hipsométrica de la capa "MDE en color": tono alto (cian/azul) = cota baja.
ELEV_LOW_HUE = 215.0
ELEV_HIGH_HUE = 35.0
# Por debajo de esta saturación el tono no es fiable (albedo, hielo, sombra profunda).
ELEV_MIN_SATURATION = 0.15
# Suavizado del relieve, en celdas de 60 m: 4 celdas ≈ 240 m.
ELEV_SMOOTH_CELLS = 4.0
# Desnivel total supuesto de la ventana, en metros (supuesto, no medido).
RELIEF_METRES_ASSUMED = 2000.0


def severity_from_hue(hue_deg: float) -> float:
    if hue_deg <= RAMP[0][0]:
        return RAMP[0][1]
    for (h0, v0), (h1, v1) in zip(RAMP, RAMP[1:]):
        if h0 <= hue_deg <= h1:
            t = (hue_deg - h0) / (h1 - h0)
            return v0 + t * (v1 - v0)
    return 0.0


def quantize_slope(value: int) -> int:
    # 32 niveles: el índice de pendiente es una estimación gruesa y así el PNG pesa ~0,3 MB.
    return (value // 8) * 8


def quantize_elevation(value: int) -> int:
    # Más fino que la pendiente: si se cuantiza a 8, cada celda vecina salta un escalón y el
    # ascenso acumulado se llena de escalones falsos de 17 m.
    return (value // 2) * 2


def build_lut() -> list[int]:
    # Canal H de Pillow: 0-255 donde 255 equivale a 360°.
    lut = []
    for i in range(256):
        hue = i * 360.0 / 255.0
        lut.append(int(round(severity_from_hue(hue) * 255)))
    return lut


def hue_and_saturation(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """HSV calculado a mano en float32: hace falta el tono con precisión, no el de Pillow."""
    rgb = rgb.astype(np.float32) / 255.0
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    delta = np.maximum(mx - mn, 1e-6)
    hue = np.zeros_like(mx)
    m = mx == r
    hue[m] = ((g[m] - b[m]) / delta[m]) % 6
    m = (mx == g) & ~(mx == r)
    hue[m] = ((b[m] - r[m]) / delta[m]) + 2
    m = (mx == b) & ~(mx == r) & ~(mx == g)
    hue[m] = ((r[m] - g[m]) / delta[m]) + 4
    hue = (hue * 60.0) % 360.0
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    return hue, sat


def build_elevation(cols: int, rows: int) -> Image.Image:
    """Índice de altura relativa 0-255 decodificado del tono de la rampa hipsométrica."""
    if not COLOR_IMAGE.exists():
        raise SystemExit(f"Falta la capa hipsométrica: {COLOR_IMAGE.name}")

    rgb = np.asarray(Image.open(COLOR_IMAGE).convert("RGB"))
    height_px, width_px = rgb.shape[:2]
    hue, sat = hue_and_saturation(rgb)
    del rgb

    span = ELEV_LOW_HUE - ELEV_HIGH_HUE
    index = np.clip((ELEV_LOW_HUE - hue) / span, 0.0, 1.0) * 255.0
    del hue
    valid = sat >= ELEV_MIN_SATURATION
    del sat

    # Acumular por celda de 60 m el índice YA decodificado (no el RGB).
    ys = (np.arange(height_px) * rows // height_px).clip(0, rows - 1)
    xs = (np.arange(width_px) * cols // width_px).clip(0, cols - 1)
    acc = np.zeros((rows, cols), dtype=np.float64)
    cnt = np.zeros((rows, cols), dtype=np.float64)
    np.add.at(acc, (ys[:, None], xs[None, :]), np.where(valid, index, 0.0).astype(np.float64))
    np.add.at(cnt, (ys[:, None], xs[None, :]), valid.astype(np.float64))
    del index, valid

    def blur(array: np.ndarray, radius: float) -> np.ndarray:
        im = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8))
        return np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32)

    # Relleno en dos etapas: primero una convolución normalizada muy amplia (~1,8 km) para
    # que las manchas sin saturación (albedo blanco, sombras) tomen la cota de su entorno,
    # y después el desenfoque de relieve normal. Con un solo paso, el interior de una mancha
    # grande cae al valor global y aparece como un pozo falso de cientos de metros.
    cells = np.where(cnt > 0, acc / np.maximum(cnt, 1), 0.0).astype(np.float32)
    weights = (cnt > 0).astype(np.float32)
    fallback = float(np.median(cells[cnt > 0])) if (cnt > 0).any() else 0.0
    wide = 30.0
    num = blur(cells * weights, wide)
    den = blur(weights * 255.0, wide) / 255.0
    wide_fill = np.where(den > 1e-4, num / np.maximum(den, 1e-4), fallback)
    filled = np.where(cnt > 0, cells, wide_fill)
    relief = blur(filled, ELEV_SMOOTH_CELLS)
    del cells, weights, num, den, wide_fill, filled, acc, cnt

    lo, hi = np.percentile(relief, [0.01, 99.99])
    span_index = max(float(hi - lo), 1e-3)
    stretched = np.clip((relief - lo) / span_index * 255.0, 0.0, 255.0)
    return Image.fromarray(stretched.astype(np.uint8))


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
    slope_grid = severity.resize((cols, rows), Image.Resampling.BOX)  # promedio por área -> 60 m
    # Cuantizar a 32 niveles: el índice es una estimación relativa y así el PNG
    # comprime mucho mejor (2 MB -> ~0,3 MB) sin cambiar el comportamiento del A*.
    slope_grid = slope_grid.point(quantize_slope)

    elevation_grid = build_elevation(cols, rows).point(quantize_elevation)

    metres_per_index = RELIEF_METRES_ASSUMED / 255.0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slope_png = OUT_DIR / "slope_index_60m.png"
    elevation_png = OUT_DIR / "elevation_60m.png"
    slope_grid.save(slope_png, optimize=True)
    elevation_grid.save(elevation_png, optimize=True)

    meta = {
        "id": "terrain-60m",
        "name": "Mallas de terreno · pendiente y altura relativa (CTX)",
        "extent": [xmin, ymin, xmax, ymax],
        "width": cols,
        "height": rows,
        "resolution": {"x": round(res_x, 4), "y": round(res_y, 4)},
        "origin": "top-left",
        "noData": None,
        "generated": "2026-11-15",
        "slope": {
            "grid": "terrain/slope_index_60m.png",
            "sourceLayer": "ctx-dem-slope",
            "sourceImage": "maps/jezero_ctx_dem_20m_slope.jpg",
            "units": "relative-index-0-255",
            "ramp": [{"hue": h, "index": round(v, 3)} for h, v in RAMP],
            "notes": [
                "Índice relativo 0-255 derivado del tono de la capa de pendientes; no son grados validados.",
                "Rejilla agregada por área desde 20 m a ~60 m para que el cálculo quepa en el navegador.",
            ],
        },
        "elevation": {
            "grid": "terrain/elevation_60m.png",
            "sourceLayer": "ctx-dem-20m-color",
            "sourceImage": "maps/jezero_ctx_dem_20m_color.jpg",
            "units": "relative-height-index-0-255",
            "metresPerIndex": round(metres_per_index, 4),
            "reliefMetres": RELIEF_METRES_ASSUMED,
            "smoothCells": ELEV_SMOOTH_CELLS,
            "ramp": {
                "lowHue": ELEV_LOW_HUE,
                "highHue": ELEV_HIGH_HUE,
                "minSaturation": ELEV_MIN_SATURATION,
            },
            "calibration": {
                "assumption": "el desnivel total de la ventana se toma como 2000 m",
                "reliefMetres": RELIEF_METRES_ASSUMED,
            },
            "notes": [
                "Índice de altura relativa decodificado del tono de la rampa hipsométrica a resolución nativa.",
                "Relieve suavizado ~240 m: interesa el relieve de gran escala, no el moteado de 20 m.",
                "El desnivel en metros es aproximado: sale de un desnivel total supuesto, no de una cota del MDE.",
                "0 = cota más baja de la ventana, 255 = cota más alta; no es altura sobre el elipsoide.",
            ],
        },
        "notes": [
            "Ambas mallas comparten extensión, tamaño y origen: la celda (fila, columna) es la misma en las dos.",
            "No sustituyen un MDE con unidades verticales verificadas. No apto para navegación real.",
        ],
    }
    (OUT_DIR / "terrain.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def summarize(grid: Image.Image) -> str:
        hist = grid.histogram()
        total = max(sum(hist), 1)
        mean = sum(v * c for v, c in enumerate(hist)) / total
        lowest = next(i for i, c in enumerate(hist) if c)
        highest = max(i for i, c in enumerate(hist) if c)
        return f"min={lowest} max={highest} media={mean:.1f}"

    print(f"rejilla {cols}x{rows} celdas, resolución {res_x:.3f}x{res_y:.3f} m")
    print(f"pendiente  {summarize(slope_grid)}")
    print(f"altura     {summarize(elevation_grid)}")
    print(f"escala vertical: 1 índice = {metres_per_index:.2f} m -> desnivel supuesto "
          f"{RELIEF_METRES_ASSUMED:.0f} m")
    print(f"png pendiente {slope_png.stat().st_size/1024:.0f} KB · "
          f"png altura {elevation_png.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
