"""Deriva productos topograficos y mapas listos para web a partir de los datos de Jezero.

Entradas (Evidencias/datos/jezero):
  topografia/M20_JezeroCrater_CTXDEM_20m.tif
  topografia/JEZ_hirise_soc_006_DTM_..._1m_...tif
  orbital/M20_JezeroCrater_CTXortho_mosaic_5m.tif
  orbital/hirise_ortho_25cm_jezero_soc007.tif
  orbital/themis_day_ir_N00_060.png
  orbital/hirise_browse/*.jpg

Salidas (Evidencias/datos/jezero/derivados):
  topografia/*.tif, *.jpg, *.png, *.geojson, *.csv
  perfiles/*
  estadisticas_topografia.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine
from PIL import Image, ImageDraw, ImageFont
from rasterio.enums import Resampling
from rasterio.warp import transform as warp_transform
from rasterio.warp import transform_bounds
from skimage.measure import approximate_polygon, find_contours

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Evidencias" / "datos" / "jezero"
OUT = DATA / "derivados"
TOPO = OUT / "topografia"
PERFILES = OUT / "perfiles"
TOPO.mkdir(parents=True, exist_ok=True)
PERFILES.mkdir(parents=True, exist_ok=True)

R_MARS = 3396190.0
LON0 = 77.45
LAT0 = 18.45
LAT_TS = 18.45
GEO_MARS = "+proj=longlat +R=3396190 +no_defs"

CTX_DEM = DATA / "topografia" / "M20_JezeroCrater_CTXDEM_20m.tif"
HIRISE_DEM = DATA / "topografia" / "JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif"
CTX_ORTHO = DATA / "orbital" / "M20_JezeroCrater_CTXortho_mosaic_5m.tif"
HIRISE_ORTHO = DATA / "orbital" / "hirise_ortho_25cm_jezero_soc007.tif"
THEMIS = DATA / "orbital" / "themis_day_ir_N00_060.png"
GEOJSON = ROOT / "Evidencias" / "datos" / "mars_trek" / "geojson"


def font(size: int, bold: bool = False):
    for name in (("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def app_xy(lon: float, lat: float) -> tuple[float, float]:
    x = R_MARS * math.radians(lon - LON0) * math.cos(math.radians(LAT_TS))
    y = R_MARS * math.radians(lat - LAT0)
    return x, y


def lonlat_to_app_bounds(bounds: tuple[float, float, float, float]) -> list[float]:
    lon_min, lat_min, lon_max, lat_max = bounds
    corners = [(lon_min, lat_min), (lon_min, lat_max), (lon_max, lat_min), (lon_max, lat_max)]
    xs, ys = zip(*(app_xy(lon, lat) for lon, lat in corners))
    return [round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1)]


def lonlat_bounds(ds: rasterio.DatasetReader) -> tuple[float, float, float, float]:
    b = transform_bounds(ds.crs, GEO_MARS, *ds.bounds, densify_pts=21)
    return (min(b[0], b[2]), min(b[1], b[3]), max(b[0], b[2]), max(b[1], b[3]))


def read_grid(path: Path, downsample: int = 1) -> tuple[np.ndarray, Affine, object, tuple[float, float, float, float]]:
    with rasterio.open(path) as ds:
        width = max(1, ds.width // downsample)
        height = max(1, ds.height // downsample)
        data = ds.read(1, out_shape=(height, width), resampling=Resampling.average).astype(np.float32)
        transform = ds.transform * Affine.scale(ds.width / width, ds.height / height)
        crs = ds.crs
        bounds = lonlat_bounds(ds)
        nodata = ds.nodata
    if nodata is not None:
        data[data == np.float32(nodata)] = np.nan
    data[data < -1e30] = np.nan
    data[np.abs(data) > 1e8] = np.nan
    return data, transform, crs, bounds


def grid_metrics(dem: np.ndarray, transform: Affine) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    dx = abs(transform.a)
    dy = abs(transform.e)
    filled = np.where(np.isfinite(dem), dem, np.nanmedian(dem))
    grad_row, grad_col = np.gradient(filled, dy, dx)
    dzdx = grad_col
    dzdy = -grad_row
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
    slope[~np.isfinite(dem)] = np.nan
    # Normal de la superficie y luz desde 315 grados (NO), 45 grados de altitud.
    az = math.radians(315.0)
    alt = math.radians(45.0)
    lx = math.sin(az) * math.cos(alt)
    ly = math.cos(az) * math.cos(alt)
    lz = math.sin(alt)
    denom = np.sqrt(dzdx * dzdx + dzdy * dzdy + 1.0)
    shade = (-dzdx * lx - dzdy * ly + lz) / denom
    shade = np.clip(shade, 0.0, 1.0)
    shade[~np.isfinite(dem)] = np.nan
    return slope, shade, np.hypot(dzdx, dzdy)


def clamp_percentiles(dem: np.ndarray) -> tuple[float, float]:
    valid = dem[np.isfinite(dem)]
    return float(np.percentile(valid, 0.5)), float(np.percentile(valid, 99.5))


def dem_palette(t: np.ndarray) -> np.ndarray:
    stops = np.array([
        [0.00, 8, 18, 30],
        [0.12, 15, 45, 65],
        [0.28, 34, 92, 92],
        [0.45, 96, 132, 92],
        [0.62, 168, 158, 105],
        [0.78, 210, 192, 150],
        [0.90, 235, 225, 200],
        [1.00, 255, 255, 255],
    ], dtype=np.float32)
    out = np.zeros(t.shape + (3,), dtype=np.float32)
    for index in range(len(stops) - 1):
        t0, r0, g0, b0 = stops[index]
        t1, r1, g1, b1 = stops[index + 1]
        mask = (t >= t0) & (t <= t1)
        local = (t[mask] - t0) / max(t1 - t0, 1e-6)
        out[mask, 0] = r0 + (r1 - r0) * local
        out[mask, 1] = g0 + (g1 - g0) * local
        out[mask, 2] = b0 + (b1 - b0) * local
    return np.clip(out, 0, 255).astype(np.uint8)


def slope_palette(slope: np.ndarray) -> np.ndarray:
    stops = np.array([
        [0.0, 34, 139, 94],
        [2.0, 120, 190, 90],
        [5.0, 245, 215, 80],
        [10.0, 245, 150, 50],
        [15.0, 225, 70, 45],
        [20.0, 160, 30, 60],
        [30.0, 230, 230, 230],
    ], dtype=np.float32)
    out = np.zeros(slope.shape + (3,), dtype=np.float32)
    for index in range(len(stops) - 1):
        t0, r0, g0, b0 = stops[index]
        t1, r1, g1, b1 = stops[index + 1]
        mask = (slope >= t0) & (slope <= t1)
        local = (slope[mask] - t0) / max(t1 - t0, 1e-6)
        out[mask, 0] = r0 + (r1 - r0) * local
        out[mask, 1] = g0 + (g1 - g0) * local
        out[mask, 2] = b0 + (b1 - b0) * local
    return np.clip(out, 0, 255).astype(np.uint8)


def stretch_gray(array: np.ndarray, low: float = 2.0, high: float = 98.0) -> np.ndarray:
    valid = array[np.isfinite(array)]
    lo, hi = np.percentile(valid, [low, high])
    out = np.clip((array - lo) / max(hi - lo, 1e-6), 0, 1)
    return (out * 255).astype(np.uint8)


def save_jpeg(rgb: np.ndarray, path: Path, quality: int = 86, max_side: int | None = None) -> None:
    image = Image.fromarray(rgb)
    if max_side and max(image.size) > max_side:
        image.thumbnail((max_side, max_side), Image.LANCZOS)
    image.save(path, quality=quality, optimize=True)
    print(f"[img] {path.relative_to(ROOT)} {image.size} {path.stat().st_size/1e6:.2f} MB")


def save_png(rgb: np.ndarray, path: Path, max_side: int | None = None) -> None:
    image = Image.fromarray(rgb)
    if max_side and max(image.size) > max_side:
        image.thumbnail((max_side, max_side), Image.LANCZOS)
    image.save(path, optimize=True)
    print(f"[img] {path.relative_to(ROOT)} {image.size} {path.stat().st_size/1e6:.2f} MB")


def save_extent(name: str, bounds: tuple[float, float, float, float], width: int, height: int,
                extra: dict | None = None) -> None:
    payload = {
        "capa": name,
        "bbox_lonlat": [round(v, 6) for v in bounds],
        "extent_app_m": lonlat_to_app_bounds(bounds),
        "width": int(width),
        "height": int(height),
    }
    if extra:
        payload.update(extra)
    (TOPO / f"{name}_extent.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def save_geotiff(array: np.ndarray, path: Path, transform: Affine, crs, dtype: str = "float32") -> None:
    profile = {
        "driver": "GTiff", "height": array.shape[0], "width": array.shape[1], "count": 1,
        "dtype": dtype, "crs": crs, "transform": transform, "compress": "deflate",
        "predictor": 2 if dtype.startswith("float") else 1, "nodata": np.nan if dtype.startswith("float") else 0,
    }
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(array.astype(dtype), 1)
    print(f"[tif] {path.relative_to(ROOT)} {array.shape} {path.stat().st_size/1e6:.2f} MB")


def colorized(dem: np.ndarray, shade: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
    t = np.clip((dem - vmin) / max(vmax - vmin, 1e-6), 0, 1)
    t[~np.isfinite(dem)] = 0
    rgb = dem_palette(t)
    relief = 0.45 + 0.55 * np.nan_to_num(shade, nan=0.5)
    rgb = np.clip(rgb.astype(np.float32) * relief[..., None], 0, 255).astype(np.uint8)
    rgb[~np.isfinite(dem)] = 0
    return rgb


def contour_geojson(dem: np.ndarray, transform: Affine, crs, levels: np.ndarray,
                    simplify: float = 1.2, min_points: int = 8) -> dict:
    features = []
    filled = np.where(np.isfinite(dem), dem, np.nanmedian(dem))
    rows, cols = filled.shape
    for level in levels:
        for contour in find_contours(filled, float(level)):
            if len(contour) < min_points:
                continue
            simplified = approximate_polygon(contour, tolerance=simplify)
            if len(simplified) < 4:
                continue
            xs = [float(transform.c + (col + 0.5) * transform.a) for row, col in simplified]
            ys = [float(transform.f + (row + 0.5) * transform.e) for row, col in simplified]
            lons, lats = warp_transform(crs, GEO_MARS, xs, ys)
            coords = [[round(float(lon), 6), round(float(lat), 6)] for lon, lat in zip(lons, lats)]
            features.append({
                "type": "Feature",
                "properties": {"elev_m": round(float(level), 1)},
                "geometry": {"type": "LineString", "coordinates": coords},
            })
    return {"type": "FeatureCollection", "name": "contornos", "features": features}


def stats_summary(dem: np.ndarray, slope: np.ndarray, transform: Affine, label: str,
                  bounds: tuple[float, float, float, float], source: str) -> dict:
    valid_dem = dem[np.isfinite(dem)]
    valid_slope = slope[np.isfinite(slope)]
    cell_x, cell_y = abs(transform.a), abs(transform.e)
    area_km2 = float(len(valid_dem) * cell_x * cell_y / 1e6)
    return {
        "capa": label,
        "fuente": source,
        "resolucion_m": [round(cell_x, 3), round(cell_y, 3)],
        "tamano_px": [int(dem.shape[1]), int(dem.shape[0])],
        "bbox_lonlat": [round(v, 5) for v in bounds],
        "extent_app_m": lonlat_to_app_bounds(bounds),
        "area_km2": round(area_km2, 1),
        "elevacion_m": {
            "min": round(float(np.min(valid_dem)), 1),
            "max": round(float(np.max(valid_dem)), 1),
            "media": round(float(np.mean(valid_dem)), 1),
            "mediana": round(float(np.median(valid_dem)), 1),
            "p01": round(float(np.percentile(valid_dem, 1)), 1),
            "p05": round(float(np.percentile(valid_dem, 5)), 1),
            "p95": round(float(np.percentile(valid_dem, 95)), 1),
            "p99": round(float(np.percentile(valid_dem, 99)), 1),
            "desviacion": round(float(np.std(valid_dem)), 1),
        },
        "pendiente_deg": {
            "media": round(float(np.mean(valid_slope)), 2),
            "mediana": round(float(np.median(valid_slope)), 2),
            "p90": round(float(np.percentile(valid_slope, 90)), 2),
            "p95": round(float(np.percentile(valid_slope, 95)), 2),
            "p99": round(float(np.percentile(valid_slope, 99)), 2),
            "max": round(float(np.max(valid_slope)), 2),
            "fraccion_mayor_15": round(float(np.mean(valid_slope > 15)), 4),
            "fraccion_mayor_20": round(float(np.mean(valid_slope > 20)), 4),
            "fraccion_mayor_25": round(float(np.mean(valid_slope > 25)), 4),
        },
    }


def hypsometric_curve(dem: np.ndarray, path: Path) -> None:
    valid = dem[np.isfinite(dem)]
    low, high = float(np.min(valid)), float(np.max(valid))
    edges = np.linspace(low, high, 101)
    counts, _ = np.histogram(valid, bins=edges)
    total = counts.sum()
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["elevacion_m", "area_km2", "fraccion_area", "fraccion_area_por_encima"])
        cell_area_km2 = (abs(20.0) * abs(20.0)) / 1e6
        cumulative = 0
        rows = []
        for index in range(len(counts)):
            area = counts[index] * cell_area_km2
            rows.append((edges[index], area, counts[index] / total))
        for elev, area, fraction in rows:
            above = sum(row[1] for row in rows if row[0] >= elev)
            writer.writerow([round(float(elev), 2), round(float(area), 4), round(float(fraction), 6), round(float(above), 4)])
    print(f"[csv] {path.relative_to(ROOT)}")


def sample_dem_lonlat(dem: np.ndarray, transform: Affine, crs, lon: float, lat: float) -> float:
    xs, ys = warp_transform(GEO_MARS, crs, [lon], [lat])
    col = (xs[0] - transform.c) / transform.a - 0.5
    row = (ys[0] - transform.f) / transform.e - 0.5
    if not (0 <= row < dem.shape[0] - 1 and 0 <= col < dem.shape[1] - 1):
        return float("nan")
    r0, c0 = int(math.floor(row)), int(math.floor(col))
    fr, fc = row - r0, col - c0
    values = np.array([[dem[r0, c0], dem[r0, c0 + 1]], [dem[r0 + 1, c0], dem[r0 + 1, c0 + 1]]])
    if not np.all(np.isfinite(values)):
        return float("nan")
    return float((values[0, 0] * (1 - fr) * (1 - fc) + values[0, 1] * (1 - fr) * fc +
                  values[1, 0] * fr * (1 - fc) + values[1, 1] * fr * fc))


def haversine(lon1, lat1, lon2, lat2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_MARS * math.asin(min(1.0, math.sqrt(a)))


def densify_line(points: list[tuple[float, float]], step_m: float = 100.0) -> list[tuple[float, float, float]]:
    out = []
    distance = 0.0
    out.append((points[0][0], points[0][1], 0.0))
    for (lon1, lat1), (lon2, lat2) in zip(points, points[1:]):
        segment = haversine(lon1, lat1, lon2, lat2)
        if segment < 1:
            continue
        n = max(1, int(segment // step_m))
        for k in range(1, n + 1):
            t = k / n
            out.append((lon1 + (lon2 - lon1) * t, lat1 + (lat2 - lat1) * t, distance + segment * t))
        distance += segment
    return out


def profile(dem: np.ndarray, transform: Affine, crs, points: list[tuple[float, float]],
            name: str, step_m: float = 100.0) -> list[dict]:
    dense = densify_line(points, step_m)
    rows = []
    previous = None
    for lon, lat, distance in dense:
        elev = sample_dem_lonlat(dem, transform, crs, lon, lat)
        slope = ""
        if previous and previous[2] is not None and math.isfinite(elev) and math.isfinite(previous[2]) and distance > previous[1]:
            slope = round(math.degrees(math.atan(abs(elev - previous[2]) / (distance - previous[1]))), 2)
        rows.append({"perfil": name, "distancia_m": round(distance, 1), "lon": round(lon, 6),
                     "lat": round(lat, 6), "elevacion_m": round(elev, 1) if math.isfinite(elev) else "",
                     "pendiente_media_deg": slope})
        previous = (lon, distance, elev)
    return rows


def draw_profile(rows: list[dict], title: str, path: Path, width: int = 1800, height: int = 620) -> None:
    image = Image.new("RGB", (width, height), (12, 16, 24))
    draw = ImageDraw.Draw(image)
    values = [row["elevacion_m"] for row in rows if row["elevacion_m"] != ""]
    distances = [row["distancia_m"] for row in rows if row["elevacion_m"] != ""]
    if not values:
        return
    margin_l, margin_r, margin_t, margin_b = 90, 40, 80, 70
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b
    vmin, vmax = min(values), max(values)
    dmax = max(distances)
    pad = max((vmax - vmin) * 0.08, 10)
    vmin -= pad
    vmax += pad
    for i in range(6):
        y = margin_t + plot_h * i / 5
        draw.line([(margin_l, y), (width - margin_r, y)], fill=(40, 50, 64), width=1)
        draw.text((12, y - 10), f"{vmax - (vmax - vmin) * i / 5:.0f} m", font=font(18), fill=(160, 175, 192))
    for i in range(6):
        x = margin_l + plot_w * i / 5
        draw.line([(x, margin_t), (x, height - margin_b)], fill=(30, 38, 50), width=1)
        draw.text((x - 20, height - margin_b + 12), f"{dmax * i / 5 / 1000:.1f} km", font=font(18), fill=(160, 175, 192))
    points = []
    for row in rows:
        if row["elevacion_m"] == "":
            continue
        x = margin_l + plot_w * row["distancia_m"] / max(dmax, 1)
        y = margin_t + plot_h * (1 - (row["elevacion_m"] - vmin) / max(vmax - vmin, 1))
        points.append((x, y))
    if len(points) > 1:
        draw.line(points, fill=(80, 220, 255), width=4, joint="curve")
        polygon = points + [(points[-1][0], height - margin_b), (points[0][0], height - margin_b)]
        draw.polygon(polygon, fill=(18, 60, 80))
        draw.line(points, fill=(80, 220, 255), width=4, joint="curve")
    draw.text((margin_l, 22), title, font=font(30, True), fill=(255, 255, 255))
    draw.text((margin_l, 58), "Perfil topografico derivado del MDE; no usar para navegacion real",
              font=font(17), fill=(160, 175, 192))
    draw.text((width - margin_r - 120, height - 30), "Ares Atlas / NASA", font=font(15), fill=(120, 135, 150))
    image.save(path, optimize=True)
    print(f"[img] {path.relative_to(ROOT)} {image.size} {path.stat().st_size/1e6:.2f} MB")


def process_dem(name: str, path: Path, downsample: int, vmin_clip: float, vmax_clip: float,
                contour_interval: float, source: str, contours: bool = True) -> dict:
    dem, transform, crs, bounds = read_grid(path, downsample)
    slope, shade, _ = grid_metrics(dem, transform)
    stats = stats_summary(dem, slope, transform, name, bounds, source)

    vmin, vmax = clamp_percentiles(dem)
    vmin = max(vmin, vmin_clip)
    vmax = min(vmax, vmax_clip)
    rgb_color = colorized(dem, shade, vmin, vmax)
    save_jpeg(rgb_color, TOPO / f"{name}_color.jpg", quality=86, max_side=4096)

    shade_rgb = np.repeat((np.nan_to_num(shade, nan=0.0) * 255).astype(np.uint8)[..., None], 3, axis=2)
    save_jpeg(shade_rgb, TOPO / f"{name}_hillshade.jpg", quality=88, max_side=4096)

    slope_rgb = slope_palette(slope)
    slope_rgb[~np.isfinite(slope)] = 0
    save_jpeg(slope_rgb, TOPO / f"{name}_slope.jpg", quality=90, max_side=4096)
    stale_png = TOPO / f"{name}_slope.png"
    if stale_png.exists():
        stale_png.unlink()

    save_geotiff(dem.astype(np.float32), TOPO / f"{name}_dem.tif", transform, crs, "float32")
    save_geotiff(slope.astype(np.float32), TOPO / f"{name}_slope.tif", transform, crs, "float32")
    save_geotiff(shade.astype(np.float32), TOPO / f"{name}_hillshade.tif", transform, crs, "float32")
    save_extent(name, bounds, dem.shape[1], dem.shape[0], {
        "resolucion_m": [round(abs(transform.a), 3), round(abs(transform.e), 3)],
        "fuente": source,
    })

    # Heightmap 16-bit para un futuro modo 3D.
    valid = dem[np.isfinite(dem)]
    lo, hi = float(np.nanpercentile(valid, 0.5)), float(np.nanpercentile(valid, 99.5))
    heightmap = np.clip((dem - lo) / max(hi - lo, 1e-6), 0, 1)
    heightmap[~np.isfinite(dem)] = 0
    heightmap = (heightmap * 65535).astype(np.uint16)
    if max(heightmap.shape) > 2048:
        image = Image.fromarray(heightmap, mode="I;16")
        image.thumbnail((2048, 2048), Image.LANCZOS)
        heightmap = np.asarray(image, dtype=np.uint16)
    Image.fromarray(heightmap, mode="I;16").save(TOPO / f"{name}_heightmap_16bit.png")
    (TOPO / f"{name}_heightmap_16bit.json").write_text(json.dumps({
        "archivo": f"{name}_heightmap_16bit.png", "elev_min_m": lo, "elev_max_m": hi,
        "unidad": "16 bits lineal entre elev_min_m y elev_max_m", "nodata": 0,
        "extent_app_m": lonlat_to_app_bounds(bounds), "bbox_lonlat": bounds,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # Contornos: se calculan sobre una version reducida para mantener el GeoJSON manejable.
    if contours:
        max_side = max(dem.shape)
        step = max(1, max_side // 2200)
        dem_c = dem[::step, ::step]
        transform_c = transform * Affine.scale(step, step)
        levels = np.arange(math.ceil(float(np.nanmin(dem_c)) / contour_interval) * contour_interval,
                           float(np.nanmax(dem_c)) + contour_interval, contour_interval)
        geojson = contour_geojson(dem_c, transform_c, crs, levels, simplify=1.0)
        (TOPO / f"{name}_contornos_{int(contour_interval)}m.geojson").write_text(
            json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
        print(f"[geo] {name}_contornos_{int(contour_interval)}m.geojson {len(geojson['features'])} rasgos")
    return stats


def process_ctx() -> dict | None:
    if not CTX_DEM.exists():
        print("[skip] falta el MDE CTX")
        return None
    print("\n== Topografia CTX 20 m ==")
    stats = process_dem("jezero_ctx_dem_20m", CTX_DEM, 1, -3600, -400, 100.0,
                        "USGS/Mars 2020 Science Investigation CTX DEM 20 m")
    hypsometric_curve(read_grid(CTX_DEM, 1)[0], TOPO / "jezero_ctx_dem_20m_curva_hipsometrica.csv")
    return stats


def process_hirise() -> dict | None:
    if not HIRISE_DEM.exists():
        print("[skip] falta el MDE HiRISE")
        return None
    print("\n== Topografia HiRISE 1 m (zona de aterrizaje) ==")
    # 2 m para conservar detalle sin cargar 460 M de pixeles en RAM.
    stats = process_dem("jezero_hirise_dem_2m", HIRISE_DEM, 2, -2800, -1600, 10.0,
                        "USGS Mars 2020 TRN HiRISE DTM 1 m (remuestreado a 2 m)",
                        contours=False)
    return stats


def load_traverse() -> list[tuple[float, float]]:
    path = GEOJSON / "perseverance_traverse.geojson"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    segments = []
    for feature in data.get("features", []):
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])
        if geometry.get("type") == "LineString":
            segments.append([(float(p[0]), float(p[1])) for p in coords])
        elif geometry.get("type") == "MultiLineString":
            segments.extend([[(float(p[0]), float(p[1])) for p in line] for line in coords])
    # Une los segmentos contiguos y descarta saltos grandes.
    points = []
    for segment in segments:
        if points and haversine(points[-1][0], points[-1][1], segment[0][0], segment[0][1]) > 2500:
            break
        points.extend(segment)
    return points


def process_profiles(ctx_dem: np.ndarray | None = None, ctx_transform: Affine | None = None,
                     ctx_crs=None) -> dict:
    if ctx_dem is None:
        ctx_dem, ctx_transform, ctx_crs, _ = read_grid(CTX_DEM, 1)
    rows = []
    traverse = load_traverse()
    if traverse:
        rows.extend(profile(ctx_dem, ctx_transform, ctx_crs, traverse, "travesia_perseverance", 100.0))
        draw_profile([r for r in rows if r["perfil"] == "travesia_perseverance"],
                     "Perfil de elevacion - travesia de Perseverance en Jezero",
                     PERFILES / "perfil_travesia_perseverance.png")
    transects = {
        "transecta_oeste_este": [(77.00, 18.45), (78.58, 18.45)],
        "transecta_norte_sur": [(77.45, 17.58), (77.45, 19.29)],
        "transecta_delta": [(77.55, 18.42), (77.78, 18.58)],
    }
    all_rows = list(rows)
    for name, points in transects.items():
        all_rows.extend(profile(ctx_dem, ctx_transform, ctx_crs, points, name, 200.0))
    with (PERFILES / "perfiles_transectas.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["perfil", "distancia_m", "lon", "lat", "elevacion_m", "pendiente_media_deg"])
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"[csv] perfiles_transectas.csv {len(all_rows)} puntos")
    # Grafico multiple.
    panels = []
    for name in transects:
        rows_t = [r for r in all_rows if r["perfil"] == name]
        panels.append((name, rows_t))
    draw_multi_profile(panels, PERFILES / "perfiles_transectas.png")
    return {"puntos_travesia": len([r for r in rows if r["perfil"] == "travesia_perseverance"]),
            "longitud_travesia_m": max([r["distancia_m"] for r in rows if r["perfil"] == "travesia_perseverance"], default=0)}


def draw_multi_profile(panels: list[tuple[str, list[dict]]], path: Path, width: int = 1800, height: int = 1100) -> None:
    image = Image.new("RGB", (width, height), (12, 16, 24))
    draw = ImageDraw.Draw(image)
    draw.text((60, 22), "Transectas topograficas de Jezero", font=font(30, True), fill=(255, 255, 255))
    draw.text((60, 58), "MDE CTX 20 m/px; escala vertical exagerada para lectura", font=font(17), fill=(160, 175, 192))
    panel_h = (height - 110) // max(len(panels), 1)
    for index, (name, rows) in enumerate(panels):
        top = 100 + index * panel_h
        margin_l, margin_r = 90, 40
        plot_w = width - margin_l - margin_r
        plot_h = panel_h - 50
        values = [r["elevacion_m"] for r in rows if r["elevacion_m"] != ""]
        distances = [r["distancia_m"] for r in rows if r["elevacion_m"] != ""]
        if not values:
            continue
        vmin, vmax = min(values), max(values)
        pad = max((vmax - vmin) * 0.1, 10)
        vmin -= pad
        vmax += pad
        dmax = max(distances, default=1)
        draw.text((margin_l, top), name.replace("_", " ").title(), font=font(20, True), fill=(220, 230, 240))
        points = []
        for row in rows:
            if row["elevacion_m"] == "":
                continue
            x = margin_l + plot_w * row["distancia_m"] / max(dmax, 1)
            y = top + 30 + plot_h * (1 - (row["elevacion_m"] - vmin) / max(vmax - vmin, 1))
            points.append((x, y))
        if len(points) > 1:
            draw.line(points, fill=(80, 220, 255), width=3, joint="curve")
        draw.text((margin_l - 80, top + 30), f"{vmax:.0f}", font=font(14), fill=(160, 175, 192))
        draw.text((margin_l - 80, top + 30 + plot_h - 14), f"{vmin:.0f}", font=font(14), fill=(160, 175, 192))
        draw.text((width - margin_r - 90, top + 30 + plot_h - 14), f"{dmax/1000:.0f} km", font=font(14), fill=(160, 175, 192))
    image.save(path, optimize=True)
    print(f"[img] {path.relative_to(ROOT)} {image.size} {path.stat().st_size/1e6:.2f} MB")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paso", choices=["ctx", "hirise", "perfiles", "todo"], default="todo")
    args = parser.parse_args()
    results = {}
    if args.paso in ("ctx", "todo"):
        ctx = process_ctx()
        if ctx:
            results["ctx_20m"] = ctx
    if args.paso in ("hirise", "todo"):
        hirise = process_hirise()
        if hirise:
            results["hirise_2m"] = hirise
    if args.paso in ("perfiles", "todo") and CTX_DEM.exists():
        results["perfiles"] = process_profiles()
    (OUT / "estadisticas_topografia.json").write_text(json.dumps({
        "generado": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "radio_marte_m": R_MARS,
        "crs_app": "+proj=eqc +lat_ts=18.45 +lat_0=18.45 +lon_0=77.45 +R=3396190 +units=m +no_defs",
        "resultados": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
