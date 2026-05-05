from html import escape
from pathlib import Path
from typing import Iterable, Optional, Union

from data_parser.utils.path_utils import ensure_parent_dir, to_path


PathLike = Union[str, Path]


def _get_value(point, names, index=None, default=None):
    if isinstance(point, dict):
        for name in names:
            if name in point:
                return point[name]
        return default

    if index is not None:
        try:
            return point[index]
        except IndexError:
            return default

    return default


def _point_to_lat_lon_alt(point):
    lat = _get_value(point, ["lat", "latitude"], 0)
    lon = _get_value(point, ["lon", "lng", "longitude"], 1)
    alt = _get_value(point, ["alt", "altitude", "height"], 2, 0.0)

    if lat is None or lon is None:
        raise ValueError(f"KML point must have latitude and longitude: {point}")

    return float(lat), float(lon), float(alt or 0.0)


def export_kml(
    points: Iterable,
    output_path: PathLike,
    name: str = "GNSS Path",
    include_points: bool = False,
) -> Path:
    """
    GNSS 좌표를 KML로 저장.

    지원 입력:
        [{"lat": 36.1, "lon": 127.1, "alt": 10.0}, ...]
        [(36.1, 127.1, 10.0), ...]
        [(36.1, 127.1), ...]
    """
    path = to_path(output_path)
    ensure_parent_dir(path)

    points = list(points)

    if not points:
        raise ValueError("No points to export as KML")

    coordinates = []

    for point in points:
        lat, lon, alt = _point_to_lat_lon_alt(point)
        coordinates.append(f"{lon},{lat},{alt}")

    coord_text = "\n".join(coordinates)
    safe_name = escape(name)

    point_placemarks = ""

    if include_points:
        items = []

        for idx, point in enumerate(points):
            lat, lon, alt = _point_to_lat_lon_alt(point)
            items.append(
                f"""
        <Placemark>
            <name>Point {idx}</name>
            <Point>
                <coordinates>{lon},{lat},{alt}</coordinates>
            </Point>
        </Placemark>
"""
            )

        point_placemarks = "\n".join(items)

    kml_text = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>{safe_name}</name>

        <Placemark>
            <name>{safe_name}</name>
            <LineString>
                <tessellate>1</tessellate>
                <altitudeMode>absolute</altitudeMode>
                <coordinates>
{coord_text}
                </coordinates>
            </LineString>
        </Placemark>
{point_placemarks}
    </Document>
</kml>
"""

    path.write_text(kml_text, encoding="utf-8")
    return path