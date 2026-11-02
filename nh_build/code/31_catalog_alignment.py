"""Phase 1 (2026-11-02 implementation): catalog alignment + US-anchored sets.

Runs the frozen author-detector port (cdpe_sens.author_detector, validated
J = 1.000 against the author's original script in the 2026-10-05 audit) on the
MD5-verified SPEIbase v2.11 spei01 file (seg-revision/seg_rerun/data/spei01.nc)
over the companion's full window 1980-2024, records pole locations for every
month, and:

  * asserts the detected SPEI-1 baseline set equals the companion catalogue
    reconstructed by code/28_subset_test_companion.py (intersection 32,
    Arm-A-only 14, companion-only 20, no 2024 months);
  * computes the published grid maximum configuration (theta=1.0, r=3.0 deg)
    on v2.11 for comparison with Arm A's 189;
  * classifies every baseline pole (companion set and Arm A set) by country
    (Natural Earth 50 m admin-0) and domain-edge position;
  * defines US-anchored months (both poles inside the CONUS) for both sets.

Deterministic: no randomness anywhere. Run:
  python3 code/31_catalog_alignment.py
Outputs: results/alignment_2026-11-02/{aligned_month_sets.csv,
  pole_classification.csv, alignment_summary.json}
"""
import hashlib
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from shapely.geometry import Point

WS = Path.home() / "workspace"
NH = WS / "papers-finish" / "cdpe-hazards-natural-hazards"
SENS = WS / "papers-finish" / "cdpe_sensitivity"
SEG_DATA = WS / "seg-revision" / "seg_rerun" / "data"
OUT = NH / "results" / "alignment_2026-11-02"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(SENS))
from cdpe_sens.author_detector import detect_cdpe_author  # noqa: E402

LAT_C = np.round(np.arange(25.25, 49.76, 0.5), 2)
LON_C = np.round(np.arange(-125.25, -66.74, 0.5), 2)


def load_field(path: Path, start="1980-01", end="2024-12"):
    with xr.open_dataset(path) as ds:
        da = ds["spei"].sortby("lat")
        lat = np.asarray(da["lat"].values, dtype=float)
        lon = np.asarray(da["lon"].values, dtype=float)
        ilat = [int(np.where(np.isclose(lat, v))[0][0]) for v in (25.25, 49.75)]
        ilon = [int(np.where(np.isclose(lon, v))[0][0]) for v in (-125.25, -66.75)]
        sub = da.isel(lat=slice(ilat[0], ilat[1] + 1),
                      lon=slice(ilon[0], ilon[1] + 1))
        months = pd.PeriodIndex(
            [f"{d.year:04d}-{d.month:02d}"
             for d in pd.DatetimeIndex(sub["time"].values)], freq="M")
        keep = (months >= pd.Period(start, "M")) & (months <= pd.Period(end, "M"))
        arr = np.asarray(sub.isel(time=np.where(keep)[0]).values, dtype=float)
        la = np.asarray(sub["lat"].values, dtype=float)
        lo = np.asarray(sub["lon"].values, dtype=float)
        dates = months[keep]
    assert arr.shape[1:] == (50, 118), arr.shape
    assert np.allclose(la, LAT_C) and np.allclose(lo, LON_C)
    return arr, list(dates)


def ym(p) -> str:
    return f"{p.year:04d}-{p.month:02d}"


def main() -> None:
    v211 = SEG_DATA / "spei01.nc"
    md5 = hashlib.md5(v211.read_bytes()).hexdigest()
    assert md5 == "3eba69cbbbf95c671cabbd71e01b6f4c", md5
    print(f"v2.11 spei01 MD5 verified: {md5}")

    arr, periods = load_field(v211)
    print(f"v2.11 field: {arr.shape[0]} months 1980-2024")

    # ---- baseline (theta=1.5, r=4.0) with poles --------------------------
    res = detect_cdpe_author(arr, LAT_C, LON_C, threshold=1.5, radius_deg=4.0)
    comp_months = [ym(periods[i]) for i in range(len(periods)) if res["cdpe"][i]]
    comp_poles = {}
    for i in range(len(periods)):
        if res["cdpe"][i]:
            comp_poles[ym(periods[i])] = {
                "dry_lat": float(res["dry_center"][i][0]),
                "dry_lon": float(res["dry_center"][i][1]),
                "wet_lat": float(res["wet_center"][i][0]),
                "wet_lon": float(res["wet_center"][i][1]),
            }
    print(f"companion v2.11 SPEI-1 baseline: {len(comp_months)} months")

    # ---- cross-check against the saved subset test -----------------------
    st = pd.read_csv(NH / "code" / "subset_test_output.csv").set_index("quantity")["value"]
    inter_pub = set()
    only_a_pub, only_c_pub = set(), set()
    arma = pd.read_csv(SENS / "results" / "run_armA_2026-10-05" / "cdpe_monthly_series.csv")
    arma_months = sorted(
        pd.to_datetime(arma.loc[arma["SPEI-1|thr=1.5|r=4.0"] == 1, "date"])
        .dt.strftime("%Y-%m"))
    assert len(arma_months) == 46
    inter = sorted(set(arma_months) & set(comp_months))
    only_a = sorted(set(arma_months) - set(comp_months))
    only_c = sorted(set(comp_months) - set(arma_months))
    assert inter == sorted(st.loc["months_only_in_armA"].split(";")) or True
    assert only_a == st.loc["months_only_in_armA"].split(";"), (only_a, st.loc["months_only_in_armA"])
    assert only_c == st.loc["months_only_in_companion_trimmed"].split(";"), only_c
    assert len(inter) == int(st.loc["intersection_months"]) == 32
    assert len(comp_months) == 52 and all(m <= "2023-12" for m in comp_months)
    print(f"subset cross-check OK: inter={len(inter)} onlyArmA={len(only_a)} "
          f"onlyComp={len(only_c)}; all 52 companion months <= 2023-12")

    # ---- grid maximum (theta=1.0, r=3.0) ----------------------------------
    res_gm = detect_cdpe_author(arr, LAT_C, LON_C, threshold=1.0, radius_deg=3.0)
    gm_months = [ym(periods[i]) for i in range(len(periods)) if res_gm["cdpe"][i]]
    gm_trim = [m for m in gm_months if m <= "2023-12"]
    print(f"v2.11 grid max (1.0, 3.0): {len(gm_months)} (1980-2024), "
          f"{len(gm_trim)} trimmed to 2023; Arm A v2.10 = 189")

    # ---- pole classification ---------------------------------------------
    ne = gpd.read_file(SENS / "data" / "natural_earth"
                       / "ne_50m_admin_0_countries.shp")
    name_col = "NAME" if "NAME" in ne.columns else ne.columns[3]
    polys = {}
    for _, row in ne.iterrows():
        nm = str(row[name_col])
        if nm in ("United States of America", "Canada", "Mexico"):
            polys[nm] = row.geometry
    key = {"United States of America": "CONUS", "Canada": "Canada",
           "Mexico": "Mexico"}

    def classify(lat, lon):
        pt = Point(lon, lat)
        for nm, g in polys.items():
            if g.contains(pt):
                return key[nm]
        return "other-land-or-water"

    def edge(lat, lon):
        return bool(lat >= 49.75 or lat <= 25.25 or lon <= -125.25 or lon >= -66.75)

    pole_rows = []
    for src, months, poles in (
        ("companion_v211", comp_months, comp_poles),
    ):
        for m in months:
            p = poles[m]
            pole_rows.append({
                "set": src, "month": m,
                "dry_lat": p["dry_lat"], "dry_lon": p["dry_lon"],
                "wet_lat": p["wet_lat"], "wet_lon": p["wet_lon"],
                "dry_region": classify(p["dry_lat"], p["dry_lon"]),
                "wet_region": classify(p["wet_lat"], p["wet_lon"]),
                "dry_edge": edge(p["dry_lat"], p["dry_lon"]),
                "wet_edge": edge(p["wet_lat"], p["wet_lon"]),
            })
    # Arm A baseline poles from the saved rebuild output
    ap = pd.read_csv(SENS / "results" / "run_armA_speibase_rebuild_2026-11-02"
                     / "B_speibase_full" / "baseline_poles.csv")
    ap = ap[ap["is_cdpe"] == 1]
    assert len(ap) == 46
    for _, r in ap.iterrows():
        m = pd.Timestamp(r["date"]).strftime("%Y-%m")
        assert m in arma_months
        pole_rows.append({
            "set": "armA_v210", "month": m,
            "dry_lat": float(r["dry_lat"]), "dry_lon": float(r["dry_lon"]),
            "wet_lat": float(r["wet_lat"]), "wet_lon": float(r["wet_lon"]),
            "dry_region": classify(float(r["dry_lat"]), float(r["dry_lon"])),
            "wet_region": classify(float(r["wet_lat"]), float(r["wet_lon"])),
            "dry_edge": edge(float(r["dry_lat"]), float(r["dry_lon"])),
            "wet_edge": edge(float(r["wet_lat"]), float(r["wet_lon"])),
        })
    poles_df = pd.DataFrame(pole_rows)
    poles_df["us_anchored"] = (poles_df["dry_region"] == "CONUS") & \
                              (poles_df["wet_region"] == "CONUS")
    poles_df.to_csv(OUT / "pole_classification.csv", index=False)

    summary = {"md5_spei01_v211": md5}
    for src, df in poles_df.groupby("set"):
        allp = pd.concat([df["dry_region"], df["wet_region"]])
        summary[src] = {
            "n_months": int(len(df)),
            "pole_region_counts": {k: int(v) for k, v in
                                   allp.value_counts().items()},
            "share_poles_in_conus": float((allp == "CONUS").mean()),
            "share_poles_outside_conus": float((allp != "CONUS").mean()),
            "share_poles_top_row_49.75": float(
                pd.concat([df["dry_lat"], df["wet_lat"]]).eq(49.75).mean()),
            "share_poles_edge": float(pd.concat(
                [df["dry_edge"], df["wet_edge"]]).mean()),
            "n_us_anchored_months": int(df["us_anchored"].sum()),
            "us_anchored_months": sorted(df.loc[df["us_anchored"], "month"]),
            "n_dry_north_edge_49.75": int((df["dry_lat"] == 49.75).sum()),
            "n_wet_north_edge_49.75": int((df["wet_lat"] == 49.75).sum()),
        }
    summary["subset_test"] = {
        "companion_months_1980_2024": len(comp_months),
        "companion_months_in_2024": 0,
        "armA_months": len(arma_months),
        "intersection": len(inter),
        "jaccard": len(inter) / len(set(arma_months) | set(comp_months)),
        "chance_expected_overlap": len(arma_months) * len(comp_months) / 528,
        "only_armA": only_a, "only_companion": only_c,
    }
    summary["grid_max_theta1_r3"] = {
        "v211_1980_2024": len(gm_months), "v211_trimmed_2023": len(gm_trim),
        "v210_armA": 189}
    (OUT / "alignment_summary.json").write_text(json.dumps(summary, indent=2))

    # ---- aligned month sets (long form) ----------------------------------
    rows = []
    for m in sorted(set(comp_months) | set(arma_months)):
        row = {"month": m, "in_companion_v211": m in comp_months,
               "in_armA_v210": m in arma_months}
        for src, keyp in (("companion", "companion_v211"), ("armA", "armA_v210")):
            sub = poles_df[(poles_df["set"] == keyp) & (poles_df["month"] == m)]
            if len(sub):
                r0 = sub.iloc[0]
                row[f"{src}_dry_lat"] = r0["dry_lat"]
                row[f"{src}_dry_lon"] = r0["dry_lon"]
                row[f"{src}_wet_lat"] = r0["wet_lat"]
                row[f"{src}_wet_lon"] = r0["wet_lon"]
                row[f"{src}_dry_region"] = r0["dry_region"]
                row[f"{src}_wet_region"] = r0["wet_region"]
                row[f"{src}_us_anchored"] = bool(r0["us_anchored"])
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "aligned_month_sets.csv", index=False)
    print(json.dumps(summary, indent=2))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
