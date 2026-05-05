"""Convert GNSS fix CSV to KML, and optionally ROS2 bag directly to KML."""

from __future__ import annotations

import csv
import math
import tempfile
from html import escape
from pathlib import Path


def safe_float(value, default=math.nan):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def is_fix_csv(path: str | Path) -> bool:
    """Return True when a CSV has the columns needed for KML trajectory output."""
    path = Path(path)
    try:
        with path.open("r", newline="") as f:
            reader = csv.DictReader(f)
            fields = set(reader.fieldnames or [])
    except OSError:
        return False

    return {"latitude", "longitude"}.issubset(fields)


def fix_csv_to_kml(
    input_csv: str | Path,
    output_kml: str | Path,
    min_status: int = 0,
    max_cov_xy: float | None = None,
    point_step: int = 50,
) -> Path:
    """Convert a NavSatFix-like CSV file to a KML trajectory."""
    input_csv = Path(input_csv)
    output_kml = Path(output_kml)
    output_kml.parent.mkdir(parents=True, exist_ok=True)

    coords = []
    placemarks = []

    with input_csv.open("r", newline="") as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader):
            lat = safe_float(row.get("latitude"))
            lon = safe_float(row.get("longitude"))
            alt = safe_float(row.get("altitude"), 0.0)

            if math.isnan(lat) or math.isnan(lon):
                continue

            if abs(lat) > 90.0 or abs(lon) > 180.0:
                continue

            status = safe_int(row.get("status"), -999)
            if status < min_status:
                continue

            cov_xx = safe_float(row.get("cov_xx"))
            cov_yy = safe_float(row.get("cov_yy"))

            if max_cov_xy is not None:
                if not math.isnan(cov_xx) and cov_xx > max_cov_xy:
                    continue
                if not math.isnan(cov_yy) and cov_yy > max_cov_xy:
                    continue

            coords.append(f"{lon:.9f},{lat:.9f},{alt:.3f}")

            if point_step > 0 and idx % point_step == 0:
                time_text = (
                    row.get("header_time")
                    or row.get("bag_time")
                    or row.get("ros_receive_time")
                    or ""
                )

                desc = "\n".join([
                    f"lat: {lat}",
                    f"lon: {lon}",
                    f"alt: {alt}",
                    f"status: {status}",
                    f"cov_xx: {cov_xx}",
                    f"cov_yy: {cov_yy}",
                ])

                placemarks.append(f"""
    <Placemark>
      <name>{escape(str(time_text))}</name>
      <description>{escape(desc)}</description>
      <Point>
        <coordinates>{lon:.9f},{lat:.9f},{alt:.3f}</coordinates>
      </Point>
    </Placemark>
""")

    if not coords:
        raise RuntimeError("No valid GPS points found.")

    coord_text = "\n".join(coords)
    placemark_text = "\n".join(placemarks)

    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>GNSS Trajectory</name>

    <Style id="trackStyle">
      <LineStyle>
        <color>ff0000ff</color>
        <width>4</width>
      </LineStyle>
    </Style>

    <Style id="pointStyle">
      <IconStyle>
        <scale>0.6</scale>
      </IconStyle>
    </Style>

    <Placemark>
      <name>GNSS Trajectory</name>
      <styleUrl>#trackStyle</styleUrl>
      <LineString>
        <tessellate>1</tessellate>
        <altitudeMode>clampToGround</altitudeMode>
        <coordinates>
{coord_text}
        </coordinates>
      </LineString>
    </Placemark>

{placemark_text}

  </Document>
</kml>
"""

    with output_kml.open("w") as f:
        f.write(kml)

    print(f"[DONE] Saved KML: {output_kml}")
    print(f"[INFO] Valid points: {len(coords)}")
    return output_kml


def bag_to_kml(
    bag_path: str | Path,
    output_kml: str | Path,
    topics: list[str] | None = None,
    min_status: int = 0,
    max_cov_xy: float | None = None,
    point_step: int = 50,
) -> Path:
    """Extract the first NavSatFix-like CSV from a bag and convert it to KML."""
    from data_parser.sensors.gnss.bag_to_csv import extract_rosbag_to_csv

    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_paths = extract_rosbag_to_csv(
            bag_path=bag_path,
            output_dir=tmp_dir,
            topics=topics,
        )
        fix_csv_paths = [p for p in csv_paths if is_fix_csv(p)]
        if not fix_csv_paths:
            raise RuntimeError("No NavSatFix CSV was created from the bag.")

        return fix_csv_to_kml(
            input_csv=fix_csv_paths[0],
            output_kml=output_kml,
            min_status=min_status,
            max_cov_xy=max_cov_xy,
            point_step=point_step,
        )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Convert GNSS fix CSV to KML.")
    parser.add_argument("input_csv")
    parser.add_argument("output_kml")
    parser.add_argument("--min-status", type=int, default=0)
    parser.add_argument("--max-cov-xy", type=float, default=None)
    parser.add_argument("--point-step", type=int, default=50)
    args = parser.parse_args()

    fix_csv_to_kml(
        input_csv=args.input_csv,
        output_kml=args.output_kml,
        min_status=args.min_status,
        max_cov_xy=args.max_cov_xy,
        point_step=args.point_step,
    )


if __name__ == "__main__":
    main()
