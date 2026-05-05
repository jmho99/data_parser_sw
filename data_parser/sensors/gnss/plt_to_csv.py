"""Convert GeoLife PLT files to NavSatFix-like CSV."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from data_parser.sensors.gnss.gnss_config import FIX_CSV_FIELDNAMES


def geolife_plt_to_fix_csv(
    input_plt: str | Path,
    output_csv: str | Path,
    frame_id: str = "geolife",
    skip_header_lines: int = 6,
) -> Path:
    """Convert GeoLife .plt format to the common GNSS fix CSV schema."""
    input_plt = Path(input_plt)
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    with input_plt.open("r", errors="ignore") as f:
        lines = f.readlines()

    for line in lines[skip_header_lines:]:
        parts = line.strip().split(",")
        if len(parts) < 7:
            continue

        try:
            lat = float(parts[0])
            lon = float(parts[1])
            alt_ft = float(parts[3])
            date_str = parts[5]
            time_str = parts[6]
            alt_m = alt_ft * 0.3048

            dt = datetime.strptime(
                f"{date_str} {time_str}",
                "%Y-%m-%d %H:%M:%S",
            ).replace(tzinfo=timezone.utc)
            timestamp = dt.timestamp()
        except ValueError:
            continue

        rows.append({
            "bag_time": timestamp,
            "header_time": timestamp,
            "frame_id": frame_id,
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

    with output_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIX_CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[DONE] Saved {len(rows)} points to {output_csv}")
    return output_csv


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Convert GeoLife PLT to GNSS fix CSV.")
    parser.add_argument("input_plt")
    parser.add_argument("output_csv")
    parser.add_argument("--frame-id", default="geolife")
    parser.add_argument("--skip-header-lines", type=int, default=6)
    args = parser.parse_args()

    geolife_plt_to_fix_csv(
        input_plt=args.input_plt,
        output_csv=args.output_csv,
        frame_id=args.frame_id,
        skip_header_lines=args.skip_header_lines,
    )


if __name__ == "__main__":
    main()
