#!/usr/bin/env python3

import sys
import csv
from datetime import datetime, timezone

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 geolife_plt_to_fix_csv.py input.plt output.csv")
        sys.exit(1)

    input_plt = sys.argv[1]
    output_csv = sys.argv[2]

    rows = []

    with open(input_plt, "r", errors="ignore") as f:
        lines = f.readlines()

    # GeoLife .plt는 앞 6줄이 헤더인 경우가 많음
    for line in lines[6:]:
        parts = line.strip().split(",")
        if len(parts) < 7:
            continue

        lat = float(parts[0])
        lon = float(parts[1])
        alt_ft = float(parts[3])
        date_str = parts[5]
        time_str = parts[6]

        alt_m = alt_ft * 0.3048

        dt = datetime.strptime(
            date_str + " " + time_str,
            "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)

        t = dt.timestamp()

        rows.append({
            "bag_time": t,
            "header_time": t,
            "frame_id": "geolife",
            "latitude": lat,
            "longitude": lon,
            "altitude": alt_m,
            "status": 0,
            "service": 1,
            "cov_xx": "",
            "cov_yy": "",
            "cov_zz": "",
            "cov_xy": "",
            "cov_xz": "",
            "cov_yz": "",
            "position_covariance_type": 0,
        })

    fieldnames = [
        "bag_time",
        "header_time",
        "frame_id",
        "latitude",
        "longitude",
        "altitude",
        "status",
        "service",
        "cov_xx",
        "cov_yy",
        "cov_zz",
        "cov_xy",
        "cov_xz",
        "cov_yz",
        "position_covariance_type",
    ]

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} points to {output_csv}")

if __name__ == "__main__":
    main()
