import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tifffile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Evidencias" / "datos" / "mars_trek"
GEO = DATA / "geojson"
OUT = ROOT / "Evidencias" / "capturas"
OUT.mkdir(parents=True, exist_ok=True)

BBOX = (77.2, 18.1, 77.9, 18.8)
WIDTH = 2048
HEIGHT = 2048
R_MARS = 3396190.0


def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def lonlat_to_px(lon, lat):
    lon_min, lat_min, lon_max, lat_max = BBOX
    x = (lon - lon_min) / (lon_max - lon_min) * WIDTH
    y = (lat_max - lat) / (lat_max - lat_min) * HEIGHT
    return x, y


def haversine(lon1, lat1, lon2, lat2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_MARS * math.asin(min(1, math.sqrt(a)))


def iter_coords(geometry):
    kind = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if kind == "LineString":
        yield coords
    elif kind == "MultiLineString":
        for line in coords:
            yield line
    elif kind == "Polygon":
        for ring in coords:
            yield ring
    elif kind == "MultiPolygon":
        for polygon in coords:
            for ring in polygon:
                yield ring


def draw_geometry(draw, geometry, fill=None, outline=None, width=3):
    for ring in iter_coords(geometry):
        points = [lonlat_to_px(lon, lat) for lon, lat, *_ in ring]
        if len(points) < 2:
            continue
        if fill and len(points) >= 3:
            draw.polygon(points, fill=fill)
        if outline:
            draw.line(points, fill=outline, width=width, joint="curve")


def load_json(name):
    return json.loads((GEO / name).read_text(encoding="utf-8"))


def dem_sample(dem, lon, lat):
    lon_min, lat_min, lon_max, lat_max = BBOX
    height, width = dem.shape
    x = int((lon - lon_min) / (lon_max - lon_min) * (width - 1))
    y = int((lat_max - lat) / (lat_max - lat_min) * (height - 1))
    x = max(0, min(width - 1, x))
    y = max(0, min(height - 1, y))
    return float(dem[y, x])


def main():
    dem = tifffile.imread(DATA / "jezero_mola_dem.tif").astype(np.float32)
    base = Image.open(DATA / "jezero_viking_base.png").convert("RGB").resize((WIDTH, HEIGHT), Image.LANCZOS)
    shade = Image.open(DATA / "jezero_mola_shade.png").convert("L").resize((WIDTH, HEIGHT), Image.LANCZOS)

    dem_resized = np.asarray(Image.fromarray(dem).resize((WIDTH, HEIGHT), Image.BILINEAR), dtype=np.float32)
    gy, gx = np.gradient(dem_resized)
    slope = np.degrees(np.arctan(np.hypot(gx, gy) / 20.0))
    slope = np.clip(slope, 0, 90)
    shade_arr = np.asarray(shade, dtype=np.float32) / 255.0
    base_arr = np.asarray(base, dtype=np.float32) / 255.0
    relief = 0.55 + 0.75 * shade_arr
    composed = np.clip(base_arr * relief[..., None], 0, 1)
    composed = (composed * 255).astype(np.uint8)
    image = Image.fromarray(composed)
    draw = ImageDraw.Draw(image, "RGBA")

    ez = load_json("ez_roi_jezero.geojson")
    for feature in ez.get("features", []):
        draw_geometry(draw, feature["geometry"], fill=(255, 140, 0, 45), outline=(255, 170, 40, 230), width=4)
        ring = next(iter_coords(feature["geometry"]))
        if ring:
            lons = [p[0] for p in ring]
            lats = [p[1] for p in ring]
            cx, cy = lonlat_to_px(sum(lons) / len(lons), sum(lats) / len(lats))
            label = feature["properties"].get("name", "ROI")
            draw.text((cx - 30, cy - 10), f"ROI {label}", font=font(30, True), fill=(255, 220, 160, 255), stroke_width=2, stroke_fill=(0, 0, 0, 220))

    ellipse = load_json("landing_ellipse.geojson")
    for feature in ellipse.get("features", []):
        draw_geometry(draw, feature["geometry"], fill=(255, 235, 0, 45), outline=(255, 235, 0, 240), width=4)

    traverse = load_json("perseverance_traverse.geojson")
    route_length = 0.0
    route_points = []
    for feature in traverse.get("features", []):
        for ring in iter_coords(feature["geometry"]):
            for lon, lat, *_ in ring:
                route_points.append((lon, lat))
            points = [lonlat_to_px(lon, lat) for lon, lat, *_ in ring]
            if len(points) >= 2:
                draw.line(points, fill=(0, 235, 255, 255), width=5, joint="curve")
    for first, second in zip(route_points, route_points[1:]):
        distance = haversine(first[0], first[1], second[0], second[1])
        if distance < 2000:
            route_length += distance

    sampled = []
    cumulative = 0.0
    target = 0.0
    step = 250.0
    for first, second in zip(route_points, route_points[1:]):
        segment = haversine(first[0], first[1], second[0], second[1])
        if segment <= 0 or segment > 2000:
            continue
        while target <= cumulative + segment:
            fraction = (target - cumulative) / segment
            lon = first[0] + (second[0] - first[0]) * fraction
            lat = first[1] + (second[1] - first[1]) * fraction
            sampled.append((lon, lat, dem_sample(dem, lon, lat)))
            target += step
        cumulative += segment

    slopes = []
    for first, second in zip(sampled, sampled[1:]):
        distance = haversine(first[0], first[1], second[0], second[1])
        if distance > 50:
            slopes.append(math.degrees(math.atan(abs(second[2] - first[2]) / distance)))
    if slopes:
        max_slope = float(np.percentile(slopes, 95))
        median_slope = float(np.percentile(slopes, 50))
    else:
        max_slope = 0.0
        median_slope = 0.0

    waypoints = load_json("mars2020_waypoints.geojson")
    for feature in waypoints.get("features", []):
        lon, lat, *_ = feature["geometry"]["coordinates"]
        x, y = lonlat_to_px(lon, lat)
        draw.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=2)
        name = feature["properties"].get("name", "")
        if name and name != "Jezero Crater":
            draw.text((x + 13, y - 32), name, font=font(26, True), fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 220))

    minerals = load_json("hydrous_minerals.geojson")
    for feature in minerals.get("features", []):
        lon, lat, *_ = feature["geometry"]["coordinates"]
        x, y = lonlat_to_px(lon, lat)
        draw.ellipse([x - 10, y - 10, x + 10, y + 10], fill=(255, 0, 110, 255), outline=(255, 255, 255, 255), width=2)

    lon_min, lat_min, lon_max, lat_max = BBOX
    m_per_px = (haversine(lon_min, (lat_min + lat_max) / 2, lon_max, (lat_min + lat_max) / 2) + haversine(lon_min, lat_min, lon_min, lat_max)) / 2 / WIDTH
    scale_km = 5
    scale_px = int(scale_km * 1000 / m_per_px)
    sx, sy = 60, HEIGHT - 90
    draw.rectangle([sx, sy, sx + scale_px, sy + 14], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=2)
    draw.text((sx, sy - 40), f"{scale_km} km", font=font(30, True), fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 220))
    draw.line([sx + scale_px - 4, sy + 7, sx + scale_px - 4, sy - 16], fill=(255, 255, 255, 255), width=3)
    draw.text((sx + scale_px - 10, sy - 50), "N", font=font(34, True), fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 220))

    panel = [40, 40, 940, 360]
    draw.rounded_rectangle(panel, radius=18, fill=(10, 12, 18, 205), outline=(255, 255, 255, 90), width=2)
    draw.text((70, 65), "JEZERO CRATER", font=font(54, True), fill=(255, 255, 255, 255))
    draw.text((70, 130), "Evidencia de datos para un mapa de exploración humana", font=font(28), fill=(230, 230, 230, 255))
    draw.text((70, 185), "Base: NASA Mars Trek / Viking MDIM 2.1 + MOLA", font=font(24), fill=(200, 200, 200, 255))
    draw.text((70, 220), "Travesía: Perseverance (332 segmentos)  |  ROI: Mars HLS 2015", font=font(24), fill=(200, 200, 200, 255))
    draw.text((70, 255), f"Elevación: {np.nanmin(dem):.0f} a {np.nanmax(dem):.0f} m  |  Pendiente MOLA p95: {max_slope:.1f}°", font=font(24), fill=(200, 200, 200, 255))
    draw.text((70, 290), f"Longitud estimada de la travesía: {route_length/1000:.1f} km", font=font(24), fill=(200, 200, 200, 255))
    draw.text((70, 325), "No usar para navegación real. Datos de resolución mixta; ver Docs/03.", font=font(22, True), fill=(255, 180, 120, 255))

    legend = [WIDTH - 430, 40, WIDTH - 40, 330]
    draw.rounded_rectangle(legend, radius=18, fill=(10, 12, 18, 205), outline=(255, 255, 255, 90), width=2)
    items = [
        ((0, 235, 255, 255), "Travesía Perseverance"),
        ((255, 235, 0, 255), "Elipse de aterrizaje"),
        ((255, 170, 40, 255), "ROI de exploración humana"),
        ((255, 0, 110, 255), "Mineral hidratado (CRISM)"),
        ((255, 255, 255, 255), "Waypoint / destino científico"),
    ]
    for index, (color, label) in enumerate(items):
        y = 80 + index * 48
        draw.rectangle([WIDTH - 400, y, WIDTH - 370, y + 24], fill=color, outline=(0, 0, 0, 200))
        draw.text((WIDTH - 352, y - 3), label, font=font(24), fill=(255, 255, 255, 255))

    out_path = OUT / "jezero_evidencia_datos.png"
    image.save(out_path, optimize=True)
    stats = {
        "bbox": BBOX,
        "dem_min_m": round(float(np.nanmin(dem)), 1),
        "dem_max_m": round(float(np.nanmax(dem)), 1),
        "dem_mean_m": round(float(np.nanmean(dem)), 1),
        "pendiente_regional_p95_deg": round(max_slope, 2),
        "pendiente_regional_mediana_deg": round(median_slope, 2),
        "longitud_travesia_km": round(route_length / 1000, 2),
        "metros_por_pixel_aprox": round(m_per_px, 2),
        "imagen": str(out_path.relative_to(ROOT)),
        "fuente": "NASA Mars Trek (Viking MDIM 2.1, MOLA, Perseverance traverse, EZMars) y NASA PDS/USGS",
    }
    (DATA / "estadisticas_jezero.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
