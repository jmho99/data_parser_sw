#!/usr/bin/env python3

import csv
import argparse
import math
from html import escape


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("output_kml")
    parser.add_argument("--min-status", type=int, default=0)
    parser.add_argument("--max-cov-xy", type=float, default=None)
    parser.add_argument("--point-step", type=int, default=50)
    args = parser.parse_args()

    coords = []
    placemarks = []

    with open(args.input_csv, "r", newline="") as f:
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

            # NavSatFix 기준:
            # -1: NO_FIX
            #  0: FIX
            #  1: SBAS_FIX
            #  2: GBAS_FIX
            if status < args.min_status:
                continue

            cov_xx = safe_float(row.get("cov_xx"))
            cov_yy = safe_float(row.get("cov_yy"))

            if args.max_cov_xy is not None:
                if not math.isnan(cov_xx) and cov_xx > args.max_cov_xy:
                    continue
                if not math.isnan(cov_yy) and cov_yy > args.max_cov_xy:
                    continue

            coords.append(f"{lon:.9f},{lat:.9f},{alt:.3f}")

            if args.point_step > 0 and idx % args.point_step == 0:
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
    <name>ROS2 GPS Trajectory</name>

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
      <name>GPS Trajectory</name>
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

    with open(args.output_kml, "w") as f:
        f.write(kml)

    print(f"[DONE] Saved KML: {args.output_kml}")
    print(f"[INFO] Valid points: {len(coords)}")


if __name__ == "__main__":
    main()
