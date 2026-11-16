"""Genera mapas orbitales, superposiciones y laminas de evidencia para Jezero.

Entradas:
  orbital/M20_JezeroCrater_CTXortho_mosaic_5m.tif
  orbital/hirise_ortho_25cm_jezero_soc007.tif
  orbital/themis_day_ir_N00_060.png
  orbital/hrsc_jezero_color.png
  derivados/topografia/jezero_ctx_dem_20m_*.jpg
  Evidencias/datos/mars_trek/geojson/*.geojson

Salidas:
  derivados/orbital/*.jpg
  derivados/mapas/*.png
  app/public/maps/*.jpg, *.png
"""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine
from PIL import Image, ImageDraw, ImageFont
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Evidencias" / "datos" / "jezero"
OUT = DATA / "derivados"
ORB = OUT / "orbital"
MAPS = OUT / "mapas"
APPMAPS = ROOT / "app" / "public" / "maps"
GEO = ROOT / "Evidencias" / "datos" / "mars_trek" / "geojson"
for path in (ORB, MAPS, APPMAPS):
    path.mkdir(parents=True, exist_ok=True)

R_MARS = 3396190.0
LON0, LAT0, LAT_TS = 77.45, 18.45, 18.45
GEO_MARS = "+proj=longlat +R=3396190 +no_defs"

CTX_DEM = DATA / "topografia" / "M20_JezeroCrater_CTXDEM_20m.tif"
HIRISE_DEM = DATA / "topografia" / "JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif"
CTX_ORTHO = DATA / "orbital" / "M20_JezeroCrater_CTXortho_mosaic_5m.tif"
HIRISE_ORTHO = DATA / "orbital" / "hirise_ortho_25cm_jezero_soc007.tif"
THEMIS = DATA / "orbital" / "themis_day_ir_N00_060.png"
HRSC = DATA / "orbital" / "hrsc_jezero_color.png"
HRSC_ANNOT = DATA / "orbital" / "hrsc_jezero_annotated.png"


def font(size: int, bold: bool = False):
    for name in (("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
                 else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def app_xy(lon: float, lat: float) -> tuple[float, float]:
    x = R_MARS * math.radians(lon - LON0) * math.cos(math.radians(LAT_TS))
    y = R_MARS * math.radians(lat - LAT0)
    return x, y


def app_bounds(lonlat: tuple[float, float, float, float]) -> list[float]:
    lon_min, lat_min, lon_max, lat_max = lonlat
    xs, ys = zip(*(app_xy(lon, lat) for lon, lat in
                   [(lon_min, lat_min), (lon_min, lat_max), (lon_max, lat_min), (lon_max, lat_max)]))
    return [round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1)]


def raster_bounds(ds) -> tuple[float, float, float, float]:
    b = transform_bounds(ds.crs, GEO_MARS, *ds.bounds, densify_pts=21)
    return (min(b[0], b[2]), min(b[1], b[3]), max(b[0], b[2]), max(b[1], b[3]))


def read_downsampled(path: Path, max_side: int = 4096) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    with rasterio.open(path) as ds:
        scale = max(ds.width, ds.height) / max_side
        width = max(1, int(round(ds.width / scale)))
        height = max(1, int(round(ds.height / scale)))
        data = ds.read(1, out_shape=(height, width), resampling=Resampling.average)
        bounds = raster_bounds(ds)
    return data, bounds


def stretch(data: np.ndarray, low: float = 1.0, high: float = 99.0, gamma: float = 1.0) -> np.ndarray:
    valid = data[data > 0]
    if valid.size == 0:
        valid = data.ravel()
    lo, hi = np.percentile(valid, [low, high])
    out = np.clip((data.astype(np.float32) - lo) / max(hi - lo, 1e-6), 0, 1)
    if gamma != 1.0:
        out = out ** gamma
    return (out * 255).astype(np.uint8)


def tint(rgb: np.ndarray, color: tuple[float, float, float]) -> np.ndarray:
    return np.clip(rgb[..., None].astype(np.float32) * np.array(color), 0, 255).astype(np.uint8)


def save(image: Image.Image, path: Path, quality: int = 86) -> None:
    if path.suffix.lower() in (".jpg", ".jpeg"):
        image.convert("RGB").save(path, quality=quality, optimize=True)
    else:
        image.save(path, optimize=True)
    print(f"[img] {path.relative_to(ROOT)} {image.size} {path.stat().st_size/1e6:.2f} MB")


def lonlat_to_px(lon, lat, bounds, width, height):
    lon_min, lat_min, lon_max, lat_max = bounds
    x = (lon - lon_min) / (lon_max - lon_min) * width
    y = (lat_max - lat) / (lat_max - lat_min) * height
    return x, y


def iter_lines(geometry):
    kind = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if kind == "LineString":
        yield from [coords]
    elif kind == "MultiLineString":
        yield from coords
    elif kind == "Polygon":
        yield from coords
    elif kind == "MultiPolygon":
        for polygon in coords:
            yield from polygon


def load_geojson(name):
    path = GEO / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"features": []}


def draw_overlay(image: Image.Image, bounds, width, height, include_geology: bool = True) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    ellipse = load_geojson("landing_ellipse.geojson")
    for feature in ellipse.get("features", []):
        for ring in iter_lines(feature.get("geometry", {})):
            points = [lonlat_to_px(lon, lat, bounds, width, height) for lon, lat, *_ in ring]
            if len(points) > 2:
                draw.polygon(points, fill=(255, 220, 0, 28))
                draw.line(points + [points[0]], fill=(255, 220, 0, 230), width=4)

    if include_geology:
        geology = load_geojson("global_geology.geojson")
        for feature in geology.get("features", []):
            for ring in iter_lines(feature.get("geometry", {})):
                points = [lonlat_to_px(lon, lat, bounds, width, height) for lon, lat, *_ in ring]
                if len(points) > 2:
                    draw.line(points + [points[0]], fill=(210, 220, 235, 90), width=1)

    roi = load_geojson("ez_roi_jezero.geojson")
    for feature in roi.get("features", []):
        for ring in iter_lines(feature.get("geometry", {})):
            points = [lonlat_to_px(lon, lat, bounds, width, height) for lon, lat, *_ in ring]
            if len(points) > 2:
                draw.polygon(points, fill=(255, 140, 0, 14))
                draw.line(points + [points[0]], fill=(255, 155, 30, 200), width=2)

    traverse = load_geojson("perseverance_traverse.geojson")
    for feature in traverse.get("features", []):
        for ring in iter_lines(feature.get("geometry", {})):
            points = [lonlat_to_px(lon, lat, bounds, width, height) for lon, lat, *_ in ring]
            if len(points) > 1:
                draw.line(points, fill=(0, 240, 255, 245), width=max(2, width // 1400), joint="curve")

    minerals = load_geojson("hydrous_minerals.geojson")
    for feature in minerals.get("features", []):
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])
        if geometry.get("type") == "Point" and len(coords) >= 2:
            x, y = lonlat_to_px(coords[0], coords[1], bounds, width, height)
            r = max(4, width // 900)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 0, 110, 255), outline=(255, 255, 255, 230), width=2)

    waypoints = load_geojson("mars2020_waypoints.geojson")
    for feature in waypoints.get("features", []):
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])
        if not coords:
            continue
        lon, lat = coords[0], coords[1]
        x, y = lonlat_to_px(lon, lat, bounds, width, height)
        r = max(4, width // 800)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=2)
        name = feature.get("properties", {}).get("name", "")
        if name and name.lower() not in ("jezero crater", "jezero"):
            draw.text((x + r + 4, y - r - 18), str(name), font=font(max(14, width // 150), True),
                      fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 230))


def add_frame(image: Image.Image, title: str, subtitle: str, legend: list[tuple[tuple[int, int, int], str]],
              bounds, footer: str) -> Image.Image:
    width, height = image.size
    draw = ImageDraw.Draw(image, "RGBA")
    panel = [28, 28, min(width - 28, 1080), 250]
    draw.rounded_rectangle(panel, radius=16, fill=(8, 12, 18, 215), outline=(255, 255, 255, 70), width=2)
    draw.text((52, 48), title, font=font(42, True), fill=(255, 255, 255, 255))
    draw.text((52, 104), subtitle, font=font(20), fill=(220, 228, 238, 255))
    draw.text((52, 140), footer, font=font(16), fill=(170, 185, 200, 255))
    # Escala grafica (10 km).
    lon_min, lat_min, lon_max, lat_max = bounds
    mid_lat = (lat_min + lat_max) / 2
    m_per_px = (R_MARS * math.radians(lon_max - lon_min) * math.cos(math.radians(mid_lat))) / width
    scale_km = 10
    scale_px = int(scale_km * 1000 / m_per_px)
    sx, sy = 52, height - 70
    draw.rectangle([sx, sy, sx + scale_px, sy + 12], fill=(255, 255, 255, 235), outline=(0, 0, 0, 255), width=2)
    draw.text((sx, sy - 30), f"{scale_km} km", font=font(18, True), fill=(255, 255, 255, 255),
              stroke_width=2, stroke_fill=(0, 0, 0, 230))
    draw.text((width - 60, 40), "N", font=font(32, True), fill=(255, 255, 255, 255),
              stroke_width=2, stroke_fill=(0, 0, 0, 230))
    draw.line([(width - 46, 78), (width - 46, 118)], fill=(255, 255, 255, 255), width=3)
    # Leyenda.
    box_h = 32 * len(legend) + 22
    box = [width - 430, height - box_h - 30, width - 30, height - 30]
    draw.rounded_rectangle(box, radius=14, fill=(8, 12, 18, 215), outline=(255, 255, 255, 70), width=2)
    for index, (color, label) in enumerate(legend):
        y = box[1] + 16 + index * 32
        draw.rectangle([box[0] + 16, y, box[0] + 42, y + 18], fill=color + (255,), outline=(0, 0, 0, 200))
        draw.text((box[0] + 52, y - 2), label, font=font(16), fill=(240, 244, 248, 255))
    return image


def process_ctx_ortho() -> None:
    if not CTX_ORTHO.exists():
        print("[skip] CTX ortho")
        return
    data, bounds = read_downsampled(CTX_ORTHO, 4096)
    gray = stretch(data, 1.0, 99.0, 1.0)
    rgb = tint(gray, (1.0, 0.98, 0.95))
    save(Image.fromarray(rgb), ORB / "jezero_ctx_5m_gray.jpg", 86)
    save(Image.fromarray(rgb), APPMAPS / "jezero_ctx_5m.jpg", 84)
    (ORB / "jezero_ctx_5m_extent.json").write_text(json.dumps({
        "bbox_lonlat": bounds, "extent_app_m": app_bounds(bounds),
        "width": int(rgb.shape[1]), "height": int(rgb.shape[0]),
    }, indent=2), encoding="utf-8")


def process_hirise_ortho() -> None:
    if not HIRISE_ORTHO.exists():
        print("[skip] HiRISE ortho")
        return
    data, bounds = read_downsampled(HIRISE_ORTHO, 4096)
    gray = stretch(data, 1.5, 99.0, 1.0)
    rgb = tint(gray, (1.0, 0.98, 0.96))
    save(Image.fromarray(rgb), ORB / "jezero_hirise_25cm_gray.jpg", 88)
    save(Image.fromarray(rgb), APPMAPS / "jezero_hirise_25cm.jpg", 84)
    (ORB / "jezero_hirise_extent.json").write_text(json.dumps({
        "bbox_lonlat": bounds, "extent_app_m": app_bounds(bounds),
        "width": int(rgb.shape[1]), "height": int(rgb.shape[0]),
    }, indent=2), encoding="utf-8")


def process_themis() -> None:
    if not THEMIS.exists():
        print("[skip] THEMIS")
        return
    image = Image.open(THEMIS).convert("L")
    width, height = image.size
    # La tesela ASU thm_dir_N00_060 cubre 0-30 N, 60-90 E.
    lon_min, lon_max, lat_min, lat_max = 60.0, 90.0, 0.0, 30.0
    crop = (76.95, 17.55, 78.60, 19.32)
    x0 = int((crop[0] - lon_min) / (lon_max - lon_min) * width)
    x1 = int((crop[2] - lon_min) / (lon_max - lon_min) * width)
    y0 = int((lat_max - crop[3]) / (lat_max - lat_min) * height)
    y1 = int((lat_max - crop[1]) / (lat_max - lat_min) * height)
    data = np.asarray(image.crop((x0, y0, x1, y1)), dtype=np.float32)
    valid = data[data > 0]
    lo, hi = np.percentile(valid, [2, 98])
    t = np.clip((data - lo) / max(hi - lo, 1e-6), 0, 1)
    palette = np.array([
        [0.00, 10, 8, 20], [0.18, 35, 20, 70], [0.38, 95, 35, 95],
        [0.58, 180, 65, 70], [0.78, 240, 140, 45], [1.00, 255, 245, 200],
    ], dtype=np.float32)
    rgb = np.zeros(t.shape + (3,), dtype=np.float32)
    for i in range(len(palette) - 1):
        t0, r0, g0, b0 = palette[i]
        t1, r1, g1, b1 = palette[i + 1]
        mask = (t >= t0) & (t <= t1)
        local = (t[mask] - t0) / max(t1 - t0, 1e-6)
        rgb[mask, 0] = r0 + (r1 - r0) * local
        rgb[mask, 1] = g0 + (g1 - g0) * local
        rgb[mask, 2] = b0 + (b1 - b0) * local
    rgb[data <= 0] = 0
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb).resize((2048, int(2048 * rgb.shape[0] / rgb.shape[1])), Image.LANCZOS)
    save(img, ORB / "jezero_themis_ir_dia.jpg", 86)
    save(img, APPMAPS / "jezero_themis_ir.jpg", 84)
    (ORB / "jezero_themis_extent.json").write_text(json.dumps({
        "bbox_lonlat": crop, "extent_app_m": app_bounds(crop),
        "width": img.size[0], "height": img.size[1],
    }, indent=2), encoding="utf-8")


def process_hrsc() -> None:
    for path, name in ((HRSC, "jezero_hrsc_color.jpg"), (HRSC_ANNOT, "jezero_hrsc_annotated.jpg")):
        if not path.exists():
            print(f"[skip] {path.name}")
            continue
        image = Image.open(path).convert("RGB")
        image.thumbnail((4096, 4096), Image.LANCZOS)
        save(image, ORB / name, 88)


def build_overview() -> None:
    if not CTX_ORTHO.exists() or not CTX_DEM.exists():
        print("[skip] overview")
        return
    data, bounds = read_downsampled(CTX_ORTHO, 4096)
    gray = stretch(data, 1.0, 99.0, 1.0)
    base = Image.fromarray(tint(gray, (1.0, 0.97, 0.92))).convert("RGB")

    dem, _ = read_downsampled(CTX_DEM, 4096)
    dem = dem.astype(np.float32)
    dem[dem < -1e30] = np.nan
    fill = np.where(np.isfinite(dem), dem, np.nanmedian(dem))
    gy, gx = np.gradient(fill)
    az, alt = math.radians(315), math.radians(45)
    lx, ly, lz = math.sin(az) * math.cos(alt), math.cos(az) * math.cos(alt), math.sin(alt)
    shade = (-gx * lx + gy * ly + lz) / np.sqrt(gx * gx + gy * gy + 1.0)
    shade = np.clip(shade, 0, 1)
    shade = np.asarray(Image.fromarray((shade * 255).astype(np.uint8)).resize(base.size, Image.LANCZOS), dtype=np.float32) / 255.0
    arr = np.asarray(base, dtype=np.float32) * (0.55 + 0.65 * shade[..., None])
    image = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    draw_overlay(image, bounds, *base.size)
    legend = [
        ((0, 240, 255), "Travesia Perseverance"),
        ((255, 220, 0), "Elipse de aterrizaje"),
        ((255, 140, 0), "ROI de exploracion humana"),
        ((255, 0, 110), "Mineral hidratado (CRISM/OMEGA)"),
        ((255, 255, 255), "Waypoint / destino cientifico"),
    ]
    image = add_frame(image, "JEZERO CRATER", "Mapa topografico y de contexto | CTX 5 m + MDE 20 m",
                      legend, bounds, "NASA/JPL/USGS | Mars 2020, MRO CTX | Ares Atlas 2026")
    save(image, MAPS / "jezero_mapa_topografico.png", 90)
    save(image, APPMAPS / "jezero_overview.jpg", 86)


def build_hirise_map() -> None:
    if not HIRISE_ORTHO.exists() or not HIRISE_DEM.exists():
        print("[skip] HiRISE map")
        return
    data, bounds = read_downsampled(HIRISE_ORTHO, 4096)
    gray = stretch(data, 1.5, 99.0, 1.0)
    base = Image.fromarray(tint(gray, (1.0, 0.98, 0.96))).convert("RGB")
    dem, _ = read_downsampled(HIRISE_DEM, 4096)
    dem = dem.astype(np.float32)
    dem[dem < -1e30] = np.nan
    fill = np.where(np.isfinite(dem), dem, np.nanmedian(dem))
    gy, gx = np.gradient(fill)
    az, alt = math.radians(315), math.radians(45)
    lx, ly, lz = math.sin(az) * math.cos(alt), math.cos(az) * math.cos(alt), math.sin(alt)
    shade = (-gx * lx + gy * ly + lz) / np.sqrt(gx * gx + gy * gy + 1.0)
    shade = np.clip(shade, 0, 1)
    shade = np.asarray(Image.fromarray((shade * 255).astype(np.uint8)).resize(base.size, Image.LANCZOS), dtype=np.float32) / 255.0
    arr = np.asarray(base, dtype=np.float32) * (0.5 + 0.7 * shade[..., None])
    image = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    draw_overlay(image, bounds, *base.size, include_geology=False)
    legend = [((0, 240, 255), "Travesia Perseverance"), ((255, 220, 0), "Elipse de aterrizaje")]
    image = add_frame(image, "ZONA DE ATERRIZAJE", "HiRISE 25 cm + MDE HiRISE 1 m | octocoptero de contexto",
                      legend, bounds, "NASA/JPL/USGS | Mars 2020 TRN | Ares Atlas 2026")
    save(image, MAPS / "jezero_hirise_mapa.png", 90)
    save(image, APPMAPS / "jezero_hirise_map.jpg", 86)


def build_overlay_layers() -> None:
    if not CTX_ORTHO.exists():
        return
    with rasterio.open(CTX_ORTHO) as ds:
        bounds = raster_bounds(ds)
        width = int(round(ds.width / max(ds.width, ds.height) * 4096))
        height = int(round(ds.height / max(ds.width, ds.height) * 4096))
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_overlay(overlay, bounds, width, height, include_geology=True)
    overlay.save(APPMAPS / "jezero_overlay_travesia.png", optimize=True)
    print(f"[img] app/public/maps/jezero_overlay_travesia.png {overlay.size} {(APPMAPS / 'jezero_overlay_travesia.png').stat().st_size/1e6:.2f} MB")
    (ORB / "jezero_overlay_extent.json").write_text(json.dumps({
        "bbox_lonlat": bounds, "extent_app_m": app_bounds(bounds), "width": width, "height": height,
    }, indent=2), encoding="utf-8")


def build_contact_sheets() -> None:
    # Contacto de las 261 imagenes HiRISE.
    catalog = DATA / "catalogo_hirise_browse.json"
    if catalog.exists():
        items = json.loads(catalog.read_text(encoding="utf-8")).get("imagenes", [])
        thumbs = []
        for item in items:
            path = ROOT / item.get("archivo", "")
            if path.exists():
                image = Image.open(path).convert("RGB")
                image.thumbnail((220, 160), Image.LANCZOS)
                thumbs.append((image, item["id"]))
        cols = 9
        cell_w, cell_h = 240, 205
        rows = math.ceil(len(thumbs) / cols)
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (10, 13, 18))
        draw = ImageDraw.Draw(sheet)
        for index, (image, image_id) in enumerate(thumbs):
            x = (index % cols) * cell_w + 10
            y = (index // cols) * cell_h + 10
            sheet.paste(image, (x, y))
            draw.text((x, y + 168), image_id, font=font(14), fill=(210, 220, 230))
        sheet.save(MAPS / "contacto_hirise_jezero.jpg", quality=82, optimize=True)
        print(f"[img] contacto_hirise_jezero.jpg {sheet.size} {(MAPS / 'contacto_hirise_jezero.jpg').stat().st_size/1e6:.2f} MB")

    # Contacto por instrumento de Perseverance.
    catalog = DATA / "catalogo_superficie.json"
    if catalog.exists():
        items = json.loads(catalog.read_text(encoding="utf-8")).get("imagenes", [])
        by_instrument: dict[str, list[dict]] = {}
        for item in items:
            by_instrument.setdefault(item.get("instrumento", "?"), []).append(item)
        selected = []
        for instrument, group in sorted(by_instrument.items()):
            for item in group[:3]:
                selected.append((instrument, item))
        cols = 6
        cell_w, cell_h = 300, 250
        rows = math.ceil(len(selected) / cols)
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (10, 13, 18))
        draw = ImageDraw.Draw(sheet)
        for index, (instrument, item) in enumerate(selected):
            path = ROOT / item.get("archivo", "")
            if not path.exists():
                continue
            image = Image.open(path).convert("RGB")
            image.thumbnail((280, 190), Image.LANCZOS)
            x = (index % cols) * cell_w + 10
            y = (index // cols) * cell_h + 10
            sheet.paste(image, (x, y))
            draw.text((x, y + 196), f"Sol {item.get('sol')} | {instrument}", font=font(14), fill=(210, 220, 230))
        sheet.save(MAPS / "contacto_perseverance_instrumentos.jpg", quality=82, optimize=True)
        print(f"[img] contacto_perseverance_instrumentos.jpg {sheet.size} {(MAPS / 'contacto_perseverance_instrumentos.jpg').stat().st_size/1e6:.2f} MB")


def publish_dem_layers() -> None:
    for name in ("jezero_ctx_dem_20m_color.jpg", "jezero_ctx_dem_20m_hillshade.jpg",
                 "jezero_ctx_dem_20m_slope.jpg", "jezero_hirise_dem_2m_color.jpg",
                 "jezero_hirise_dem_2m_hillshade.jpg", "jezero_hirise_dem_2m_slope.jpg"):
        source = OUT / "topografia" / name
        if source.exists():
            shutil.copy2(source, APPMAPS / name)
            print(f"[copy] app/public/maps/{name} {source.stat().st_size/1e6:.2f} MB")


def read_extent(path: Path) -> list[float] | None:
    if not path.exists():
        return None
    try:
        extent = json.loads(path.read_text(encoding="utf-8")).get("extent_app_m")
    except (OSError, ValueError):
        return None
    if not isinstance(extent, list) or len(extent) != 4:
        return None
    return [float(value) for value in extent]


def build_layers_catalog() -> None:
    specs = [
        dict(
            id="ctx-ortho-5m",
            name="Jezero · ortomosaico CTX",
            image="jezero_ctx_5m.jpg",
            extent=ORB / "jezero_ctx_5m_extent.json",
            source="https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/",
            description="Ortomosaico visible del cráter Jezero y su región, base cartográfica para comparar capas.",
            mission="Mars 2020 / MRO",
            instrument="CTX (Context Camera)",
            resolution="5 m/px nativo; 4096 px para web",
            date="2021-10-14",
            license="Dominio público NASA/USGS (Mangold et al., 2021; DOI 10.1126/science.abl4051)",
            limitations="Mosaico de contexto, no de detalle; costuras y zonas con distinta iluminación.",
        ),
        dict(
            id="hirise-ortho-25cm",
            name="Zona de aterrizaje · HiRISE",
            image="jezero_hirise_25cm.jpg",
            extent=ORB / "jezero_hirise_extent.json",
            source="https://planetarymaps.usgs.gov/mosaic/mars2020_trn/HiRISE/",
            description="Ortomosaico HiRISE de la zona de aterrizaje de Perseverance, derivado del MDE de 1 m.",
            mission="MRO",
            instrument="HiRISE",
            resolution="0.25 m/px nativo; ~5 m/px en la vista web",
            date="2020-07-24",
            license="Dominio público NASA/USGS (Fergason et al., 2020; DOI 10.5066/P9REJ9JN)",
            limitations="Solo cubre la zona de aterrizaje; no es un mapa de todo el cráter.",
        ),
        dict(
            id="themis-ir-diurno",
            name="Jezero · THEMIS IR diurno",
            image="jezero_themis_ir.jpg",
            extent=ORB / "jezero_themis_extent.json",
            source="https://mars.asu.edu/data/thm_dir/",
            description="Mosaico térmico infrarrojo diurno (THEMIS) recortado a la región de Jezero.",
            mission="Mars Odyssey",
            instrument="THEMIS (IR diurno, 12.57 µm)",
            resolution="~231 m/px",
            date="2006-11-16",
            license="Dominio público NASA/ASU",
            limitations="Resolución gruesa; mezcla temperatura y pendiente; no es temperatura absoluta.",
        ),
        dict(
            id="ctx-dem-color",
            name="Topografía · MDE CTX 20 m",
            image="jezero_ctx_dem_20m_color.jpg",
            extent=OUT / "topografia" / "jezero_ctx_dem_20m_extent.json",
            source="https://doi.org/10.1126/science.abl4051",
            description="Modelo digital de elevación del cráter y su región, coloreado por altura y sombreado.",
            mission="Mars 2020 / MRO",
            instrument="CTX (fotogrametría estéreo)",
            resolution="20 m/px",
            date="2021-10-14",
            license="Dominio público NASA/USGS (Mangold et al., 2021)",
            limitations="Pendientes suavizadas a 20 m; no resuelve rocas ni escalones menores de ~40 m.",
        ),
        dict(
            id="ctx-dem-hillshade",
            name="Relieve · sombreado CTX",
            image="jezero_ctx_dem_20m_hillshade.jpg",
            extent=OUT / "topografia" / "jezero_ctx_dem_20m_extent.json",
            source="https://doi.org/10.1126/science.abl4051",
            description="Sombreado del relieve calculado con luz desde el noroeste (315°, 45°).",
            mission="Mars 2020 / MRO",
            instrument="CTX (fotogrametría estéreo)",
            resolution="20 m/px",
            date="2021-10-14",
            license="Dominio público NASA/USGS (Mangold et al., 2021)",
            limitations="Iluminación sintética; no es una imagen real y exagera el relieve.",
        ),
        dict(
            id="ctx-dem-slope",
            name="Pendientes · MDE CTX",
            image="jezero_ctx_dem_20m_slope.jpg",
            extent=OUT / "topografia" / "jezero_ctx_dem_20m_extent.json",
            source="https://doi.org/10.1126/science.abl4051",
            description="Pendiente del terreno en grados, calculada a partir del MDE CTX de 20 m.",
            mission="Mars 2020 / MRO",
            instrument="CTX (fotogrametría estéreo)",
            resolution="20 m/px",
            date="2021-10-14",
            license="Dominio público NASA/USGS (Mangold et al., 2021)",
            limitations="Pendiente media por píxel; no apta para navegación ni para estabilidad local.",
        ),
        dict(
            id="hirise-dem-color",
            name="Topografía · MDE HiRISE 2 m",
            image="jezero_hirise_dem_2m_color.jpg",
            extent=OUT / "topografia" / "jezero_hirise_dem_2m_extent.json",
            source="https://doi.org/10.5066/P9REJ9JN",
            description="MDE HiRISE de la zona de aterrizaje, remuestreado a 2 m y coloreado por altura.",
            mission="MRO",
            instrument="HiRISE",
            resolution="1 m/px nativo; 2 m/px derivado",
            date="2020-07-24",
            license="Dominio público NASA/USGS (Fergason et al., 2020)",
            limitations="Cubre ~20×20 km; costuras y errores en bordes de sombra.",
        ),
        dict(
            id="overlay-travesia",
            name="Superposición · travesía y geología",
            image="jezero_overlay_travesia.png",
            extent=ORB / "jezero_overlay_extent.json",
            source="https://trek.nasa.gov/mars/",
            description="Capa transparente con travesía, elipse de aterrizaje, ROI, minerales hidratados y contactos geológicos.",
            mission="Mars 2020 / Mars Trek",
            instrument="Vectores GIS (NASA/JPL/ASU)",
            resolution="vector",
            date="2026-11-14",
            license="NASA/JPL/ASU Mars Trek; uso educativo con atribución",
            limitations="Trazados aproximados y simplificados; no sustituyen datos oficiales.",
        ),
    ]
    layers = []
    for original in specs:
        spec = dict(original)
        extent_path = spec.pop("extent")
        image = spec.pop("image")
        extent = read_extent(extent_path)
        if extent is None or not (APPMAPS / image).exists():
            print(f"[skip] capa {spec['id']} sin extensión o imagen")
            continue
        layers.append({**spec, "url": f"maps/{image}", "extent": extent})
    (ROOT / "app" / "public" / "layers.json").write_text(
        json.dumps({"layers": layers}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[json] app/public/layers.json {len(layers)} capas")


def main() -> int:
    process_ctx_ortho()
    process_hirise_ortho()
    process_themis()
    process_hrsc()
    build_overview()
    build_hirise_map()
    build_overlay_layers()
    build_contact_sheets()
    publish_dem_layers()
    build_layers_catalog()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
