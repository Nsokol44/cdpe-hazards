#!/usr/bin/env python3
"""Step 04 - Monthly tornado and hail series from Storm Events, 1980-2023.

DESIGN LOCK Section 4.1-4.2. Domain filter: event begin coordinates inside
25-50 N, 125-66 W; records missing coordinates fall back to the county
centroid (Census gazetteer) and are counted only if the centroid is in the
box. Every disposition is logged. Output: results/hazard_series_storm.csv
with all 528 months (zero-filled) and results/storm_build_log.json.
"""
import gzip
import io
import json
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = 25.0, 50.0, -125.0, -66.0
USECOLS = ["BEGIN_YEARMONTH", "EVENT_TYPE", "TOR_F_SCALE", "MAGNITUDE",
           "BEGIN_LAT", "BEGIN_LON", "STATE_FIPS", "CZ_FIPS"]


def load_centroids() -> dict[int, tuple[float, float]]:
    zpath = RAW / "reference" / "gaz_counties_national.zip"
    with zipfile.ZipFile(zpath) as z:
        name = [n for n in z.namelist() if n.endswith(".txt")][0]
        with z.open(name) as f:
            df = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8"),
                             sep="\t", dtype={"GEOID": str})
    df.columns = [c.strip() for c in df.columns]
    out = {}
    for geoid, la, lo in zip(df["GEOID"], df["INTPTLAT"], df["INTPTLONG"]):
        out[int(geoid)] = (float(la), float(lo))
    return out


def main() -> int:
    centroids = load_centroids()
    files = sorted((RAW / "storm_events").glob("StormEvents_details-*.csv.gz"))
    assert len(files) == 47, f"expected 47 yearly files, found {len(files)}"  # EXTENDED run: 1980-2026
    log = {"n_with_coords": 0, "n_via_centroid": 0, "n_no_location": 0,
           "n_outside_box": 0}
    rows = []
    months = pd.period_range("1980-01", "2026-07", freq="M")  # EXTENDED run: through the binding endpoint 2026-07 (Storm Events)
    totals = {str(m): dict(tornado_all=0, tornado_ef1plus=0,
                           tornado_ef2plus=0, hail_all=0, hail_ge1in=0)
              for m in months}
    ef1 = {"F1", "F2", "F3", "F4", "F5", "EF1", "EF2", "EF3", "EF4", "EF5"}
    ef2 = {"F2", "F3", "F4", "F5", "EF2", "EF3", "EF4", "EF5"}
    for path in files:
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
            df = pd.read_csv(fh, usecols=USECOLS, low_memory=False)
        df = df[df["EVENT_TYPE"].isin(["Tornado", "Hail"])]
        for r in df.itertuples(index=False):
            ym = str(int(r.BEGIN_YEARMONTH))
            key = f"{ym[:4]}-{ym[4:6]}"
            if key not in totals:
                continue
            lat, lon = r.BEGIN_LAT, r.BEGIN_LON
            if pd.notna(lat) and pd.notna(lon):
                log["n_with_coords"] += 1
            else:
                fips = None
                if pd.notna(r.STATE_FIPS) and pd.notna(r.CZ_FIPS):
                    fips = int(r.STATE_FIPS) * 1000 + int(r.CZ_FIPS)
                if fips in centroids:
                    lat, lon = centroids[fips]
                    log["n_via_centroid"] += 1
                else:
                    log["n_no_location"] += 1
                    continue
            if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
                log["n_outside_box"] += 1
                continue
            t = totals[key]
            if r.EVENT_TYPE == "Tornado":
                t["tornado_all"] += 1
                scale = str(r.TOR_F_SCALE).strip().upper()
                if scale in ef1:
                    t["tornado_ef1plus"] += 1
                if scale in ef2:
                    t["tornado_ef2plus"] += 1
            else:
                t["hail_all"] += 1
                if pd.notna(r.MAGNITUDE) and float(r.MAGNITUDE) >= 1.0:
                    t["hail_ge1in"] += 1
    out = pd.DataFrame([{"month": k, **v} for k, v in totals.items()])
    out.to_csv(ROOT / "results" / "hazard_series_storm.csv", index=False)
    (ROOT / "results" / "storm_build_log.json").write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    print(out.head(3).to_string())
    print("months:", len(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
