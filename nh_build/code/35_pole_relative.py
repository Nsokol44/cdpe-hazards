#!/usr/bin/env python3
"""Phase 3, Step 35 - pole-relative stratum analysis (tornado, hail >= 1 in).

Per-cell source: the frozen Step-04 counting replicated exactly as in
code/27_build_map_figure.py - StormEvents details files in
cdpe-hazards-aas/data/raw/storm_events (44 files), domain box
25-50 N / 125-66 W, county-centroid fallback (Census gazetteer) for
records without begin coordinates. Totals are asserted against the
frozen totals (54,607 tornadoes; 229,650 hail >= 1 in; 379,430 hail
overall) before any use. The month x 1-degree-cell counts are saved to
results/phase3_2026-11-02/monthly_cell_counts.csv (traceability source
for this analysis; rerunning this script rebuilds and overwrites it).

Design: for each aligned CDPE month m (companion_v211, 52), poles from
pole_classification.csv. Every 1-degree report cell (centre at
floor(lat)+0.5, floor(lon)+0.5) is classified by Euclidean centre
distance in degrees to m's poles: near-dry if dist to dry pole <= 4.0,
near-wet if dist to wet pole <= 4.0, both -> nearer pole wins, else
elsewhere. Reports in m use m's classification. Control reports: the
same calendar month in every non-CDPE year (a month whose calendar
month matches m's and which is not itself a CDPE month), classified by
m's poles. Stratum rate ratio =
  (stratum reports in CDPE months / 52) /
  (stratum reports in control months / n_control_month_instances),
where n_control_month_instances sums, over the 52 CDPE months, the
number of matched control months for each. Bootstrap: resample the 52
CDPE months with replacement (each resampled month carries its own
control set), B = 2000, seed 20261102, percentile CI. Shares: stratum
share of all CDPE-month reports.

Heat waves are skipped by design: the heat-wave field is a gridMET-based
per-cell mean over 3,608 land cells on its own grid (50 x 118), not
report counts on the 1-degree report grid, so pole-distance strata of
report cells are not defined for it.

Deps: numpy, pandas. Deterministic (seed above).
"""
import gzip
import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

PKG = Path(__file__).resolve().parents[1]
SRC = PKG.parent / "cdpe-hazards-aas"
RAW = SRC / "data" / "raw"
OUT = PKG / "results" / "phase3_2026-11-02"
ALIGN = PKG / "results" / "alignment_2026-11-02"
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = 25.0, 50.0, -125.0, -66.0
USECOLS = ["BEGIN_YEARMONTH", "EVENT_TYPE", "TOR_F_SCALE", "MAGNITUDE",
           "BEGIN_LAT", "BEGIN_LON", "STATE_FIPS", "CZ_FIPS"]
B = 2000
SEED = 20261102


def load_centroids():
    zpath = RAW / "reference" / "gaz_counties_national.zip"
    with zipfile.ZipFile(zpath) as z:
        name = [n for n in z.namelist() if n.endswith(".txt")][0]
        with z.open(name) as f:
            df = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8"),
                             sep="\t", dtype={"GEOID": str})
    df.columns = [c.strip() for c in df.columns]
    return {int(g): (float(la), float(lo)) for g, la, lo in
            zip(df["GEOID"], df["INTPTLAT"], df["INTPTLONG"])}


def build_cell_counts():
    centroids = load_centroids()
    files = sorted((RAW / "storm_events").glob("StormEvents_details-*.csv.gz"))
    assert len(files) == 44
    recs = []
    n_tor = n_hail_ge = n_hail_all = 0
    for path in files:
        with gzip.open(path, "rt", encoding="utf-8",
                       errors="replace") as fh:
            df = pd.read_csv(fh, usecols=USECOLS, low_memory=False)
        df = df[df["EVENT_TYPE"].isin(["Tornado", "Hail"])]
        for r in df.itertuples(index=False):
            ym = str(int(r.BEGIN_YEARMONTH))
            key = f"{ym[:4]}-{ym[4:6]}"
            lat, lon = r.BEGIN_LAT, r.BEGIN_LON
            if not (pd.notna(lat) and pd.notna(lon)):
                fips = None
                if pd.notna(r.STATE_FIPS) and pd.notna(r.CZ_FIPS):
                    fips = int(r.STATE_FIPS) * 1000 + int(r.CZ_FIPS)
                if fips in centroids:
                    lat, lon = centroids[fips]
                else:
                    continue
            if not (LAT_MIN <= lat <= LAT_MAX
                    and LON_MIN <= lon <= LON_MAX):
                continue
            if r.EVENT_TYPE == "Tornado":
                n_tor += 1
                recs.append((key, int(np.floor(lat)), int(np.floor(lon)),
                             1, 0))
            else:
                n_hail_all += 1
                if pd.notna(r.MAGNITUDE) and float(r.MAGNITUDE) >= 1.0:
                    n_hail_ge += 1
                    recs.append((key, int(np.floor(lat)),
                                 int(np.floor(lon)), 0, 1))
    assert n_tor == 54607 and n_hail_ge == 229650 \
        and n_hail_all == 379430, (n_tor, n_hail_ge, n_hail_all)
    pts = pd.DataFrame(recs, columns=["month", "clat", "clon",
                                      "tornado", "hail_ge1in"])
    grid = pts.groupby(["month", "clat", "clon"],
                       as_index=False).sum()
    grid.to_csv(OUT / "monthly_cell_counts.csv", index=False)
    print(f"cell counts OK: {n_tor} tornado, {n_hail_ge} hail>=1in, "
          f"{len(grid)} month-cells")
    return grid


def stratum_of(clat, clon, dry, wet):
    d_dry = np.hypot(clat + 0.5 - dry[0], clon + 0.5 - dry[1])
    d_wet = np.hypot(clat + 0.5 - wet[0], clon + 0.5 - wet[1])
    near_d, near_w = d_dry <= 4.0, d_wet <= 4.0
    out = np.full(len(clat), "elsewhere", dtype=object)
    both = near_d & near_w
    out[near_d & ~near_w] = "near_dry"
    out[near_w & ~near_d] = "near_wet"
    out[both & (d_dry <= d_wet)] = "near_dry"
    out[both & (d_dry > d_wet)] = "near_wet"
    return out


def main() -> int:
    grid = build_cell_counts()
    poles = pd.read_csv(ALIGN / "pole_classification.csv")
    pc = poles[poles["set"] == "companion_v211"].copy()
    cdpe_months = sorted(pc["month"])
    assert len(cdpe_months) == 52
    pole_map = {r.month: ((r.dry_lat, r.dry_lon), (r.wet_lat, r.wet_lon))
                for r in pc.itertuples()}
    all_months = sorted(grid["month"].unique())
    # per (cdpe month, stratum, hazard): exposed reports and control
    # reports / control month count
    per_m = {}  # month -> dict stratum -> (tor_e, hail_e, tor_c, hail_c, n_ctrl)
    for m in cdpe_months:
        dry, wet = pole_map[m]
        cal = m[5:7]
        controls = [x for x in all_months
                    if x[5:7] == cal and x not in cdpe_months]
        gm = grid[grid["month"] == m]
        gc = grid[grid["month"].isin(controls)]
        sm = stratum_of(gm["clat"].values, gm["clon"].values, dry, wet)
        sc = stratum_of(gc["clat"].values, gc["clon"].values, dry, wet)
        d = {}
        for s in ("near_dry", "near_wet", "elsewhere"):
            d[s] = (float(gm.loc[sm == s, "tornado"].sum()),
                    float(gm.loc[sm == s, "hail_ge1in"].sum()),
                    float(gc.loc[sc == s, "tornado"].sum()),
                    float(gc.loc[sc == s, "hail_ge1in"].sum()),
                    len(controls))
        per_m[m] = d

    def rr_from(month_list, stratum, haz_idx):
        e = sum(per_m[m][stratum][haz_idx] for m in month_list)
        c = sum(per_m[m][stratum][haz_idx + 2] for m in month_list)
        nc = sum(per_m[m][stratum][4] for m in month_list)
        if c == 0 or nc == 0:
            return np.nan
        return (e / len(month_list)) / (c / nc)

    rng = np.random.default_rng(SEED)
    rows = []
    for haz, haz_idx, hlabel in [("tornado_all", 0, "Tornadoes"),
                                 ("hail_ge1in", 1, "Hail >= 1 in")]:
        tot_e = sum(per_m[m][s][haz_idx] for m in cdpe_months
                    for s in ("near_dry", "near_wet", "elsewhere"))
        for s in ("near_dry", "near_wet", "elsewhere"):
            point = rr_from(cdpe_months, s, haz_idx)
            reps = []
            for _ in range(B):
                sample = list(rng.choice(cdpe_months, size=52,
                                         replace=True))
                reps.append(rr_from(sample, s, haz_idx))
            reps = np.array([r for r in reps if np.isfinite(r)])
            e = sum(per_m[m][s][haz_idx] for m in cdpe_months)
            c = sum(per_m[m][s][haz_idx + 2] for m in cdpe_months)
            nc = sum(per_m[m][s][4] for m in cdpe_months)
            rows.append({
                "hazard": haz, "hazard_label": hlabel, "stratum": s,
                "rr": point,
                "ci_lo": float(np.percentile(reps, 2.5)),
                "ci_hi": float(np.percentile(reps, 97.5)),
                "cdpe_reports": int(e), "control_reports": int(c),
                "n_control_month_instances": int(nc),
                "share_of_cdpe_reports": float(e / tot_e),
                "bootstrap_finite": int(len(reps))})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "pole_relative_results.csv", index=False)
    print(res.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
