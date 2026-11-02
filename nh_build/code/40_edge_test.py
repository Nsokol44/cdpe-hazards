#!/usr/bin/env python3
"""Fix Round 2, item 6 - northern-edge artifact test (Paper 1 robustness
and Paper 2 prerequisite).

Question: 20 dry poles of the aligned 52-month catalog sit at or north
of 47.75 N, many on the top row of the domain (49.75 N). Is the
northern-edge pile-up a domain-edge artifact (the detector's driest
cell is forced onto the boundary when the true minimum lies outside
the box) or real geography (dry poles genuinely cluster near the
Canadian border)?

Test: re-run the frozen Study-1-lineage detector (cdpe_sens
author_detector, the same port validated J = 1.000 against the author's
original script) for the baseline definition (SPEI-1, theta = 1.5,
r = 4.0 degrees, f = 0.5, q = 0.10) on SPEIbase v2.11 with the domain
box expanded north by 3 degrees (to 53.0 N) and by 5 degrees (to
55.0 N). Longitude bounds, southern bound, and every other parameter
are unchanged. Because the global SPEIbase field is in hand (MD5
3eba69cbbbf95c671cabbd71e01b6f4c, verified before use), the expanded
runs are the same detector on more of the same field.

Per expansion, for each of the 20 baseline dry poles at or north of
47.75 N (their baseline months), classify the expanded-run dry pole
for that month (months that cease to qualify get a 'lost' class):
  * same_place: expanded dry-pole latitude within 0.5 deg of the
    baseline latitude (either direction);
  * moved_north: more than 0.5 deg north of the baseline latitude but
    below the new top row;
  * moved_to_new_edge: at or north of (expanded top row - 0.25 deg);
  * moved_south: more than 0.5 deg south of the baseline latitude;
  * lost: month no longer qualifies as a CDPE month in the expanded run.
Also report the expanded-run baseline month counts and their overlap
(Jaccard + intersection) with the 52, the month lists gained/lost, and
the latitudinal distribution of the expanded dry poles.

This is a robustness NOTE, not a redefinition: the catalog of record
stays the 52. If the pile-up is an artifact, the manuscript gains a
limitations paragraph (drafted in the note) at the author's call.

Outputs: results/fixround2_2026-11-02/edge_test_poles.csv (per month,
per expansion), edge_test_summary.json, EDGE_TEST_NOTE.md.

Deterministic. Deps: numpy, pandas, xarray.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

WS = Path.home() / "workspace"
NH = WS / "papers-finish" / "cdpe-hazards-natural-hazards"
SENS = WS / "papers-finish" / "cdpe_sensitivity"
SEG_DATA = WS / "seg-revision" / "seg_rerun" / "data"
OUT = NH / "results" / "fixround2_2026-11-02"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(SENS))
from cdpe_sens.author_detector import detect_cdpe_author  # noqa: E402


def load_field(lat_lo, lat_hi, start="1980-01", end="2023-12"):
    path = SEG_DATA / "spei01.nc"
    md5 = hashlib.md5(path.read_bytes()).hexdigest()
    assert md5 == "3eba69cbbbf95c671cabbd71e01b6f4c", md5
    with xr.open_dataset(path) as ds:
        da = ds["spei"].sortby("lat")
        lat = np.asarray(da["lat"].values, dtype=float)
        lon = np.asarray(da["lon"].values, dtype=float)
        ilat = [int(np.where(np.isclose(lat, v))[0][0])
                for v in (lat_lo, lat_hi)]
        ilon = [int(np.where(np.isclose(lon, v))[0][0])
                for v in (-125.25, -66.75)]
        sub = da.isel(lat=slice(ilat[0], ilat[1] + 1),
                      lon=slice(ilon[0], ilon[1] + 1))
        months = pd.PeriodIndex(
            [f"{d.year:04d}-{d.month:02d}"
             for d in pd.DatetimeIndex(sub["time"].values)], freq="M")
        keep = (months >= pd.Period(start, "M")) & \
               (months <= pd.Period(end, "M"))
        arr = np.asarray(sub.isel(time=np.where(keep)[0]).values,
                         dtype=float)
        la = np.asarray(sub["lat"].values, dtype=float)
        lo = np.asarray(sub["lon"].values, dtype=float)
        dates = months[keep]
    return arr, la, lo, [f"{p.year:04d}-{p.month:02d}" for p in dates]


def main() -> int:
    poles = pd.read_csv(
        NH / "results" / "alignment_2026-11-02" / "pole_classification.csv")
    comp = poles[poles["set"] == "companion_v211"].copy()
    assert len(comp) == 52
    base = {r.month: r for r in comp.itertuples()}
    north = comp[comp["dry_lat"] >= 47.75]
    print(f"baseline dry poles at or north of 47.75 N: {len(north)}")
    assert len(north) == 20, len(north)

    # sanity: re-run the baseline box first and require the 52 back
    arr, la, lo, months = load_field(25.25, 49.75)
    res = detect_cdpe_author(arr, la, lo, threshold=1.5, radius_deg=4.0)
    base_months = [months[i] for i in range(len(months)) if res["cdpe"][i]]
    assert base_months == sorted(comp["month"]), (
        len(base_months), set(base_months) ^ set(comp["month"]))
    print("baseline box reproduces the 52 exactly")

    rows, summary = [], {}
    for label, top in (("plus3", 52.75), ("plus5", 54.75)):
        arr, la, lo, months = load_field(25.25, top)
        res = detect_cdpe_author(arr, la, lo, threshold=1.5,
                                 radius_deg=4.0)
        exp_months = [months[i] for i in range(len(months))
                      if res["cdpe"][i]]
        exp_poles = {months[i]: (float(res["dry_center"][i][0]),
                                 float(res["dry_center"][i][1]),
                                 float(res["wet_center"][i][0]),
                                 float(res["wet_center"][i][1]))
                     for i in range(len(months)) if res["cdpe"][i]}
        inter = sorted(set(exp_months) & set(comp["month"]))
        jac = len(inter) / len(set(exp_months) | set(comp["month"]))
        gained = sorted(set(exp_months) - set(comp["month"]))
        lost = sorted(set(comp["month"]) - set(exp_months))
        print(f"{label}: {len(exp_months)} months, overlap {len(inter)}, "
              f"Jaccard {jac:.3f}, gained {len(gained)}, lost {len(lost)}")
        classes = {}
        for r in north.itertuples():
            if r.month not in exp_poles:
                cls = "lost"
                new_lat = np.nan
            else:
                new_lat = exp_poles[r.month][0]
                if new_lat >= top - 0.25:
                    cls = "moved_to_new_edge"
                elif new_lat < r.dry_lat - 0.5:
                    cls = "moved_south"
                elif new_lat > r.dry_lat + 0.5:
                    cls = "moved_north"
                else:
                    cls = "same_place"
            classes[cls] = classes.get(cls, 0) + 1
            rows.append({"month": r.month, "expansion": label,
                         "baseline_dry_lat": r.dry_lat,
                         "baseline_dry_lon": r.dry_lon,
                         "expanded_dry_lat": new_lat,
                         "expanded_dry_lon": (exp_poles[r.month][1]
                                              if r.month in exp_poles
                                              else np.nan),
                         "class": cls,
                         "still_cdpe": r.month in exp_poles})
        lat_dist = pd.Series([exp_poles[m][0] for m in exp_months])
        summary[label] = {
            "n_months": len(exp_months), "overlap_with_52": len(inter),
            "jaccard": round(float(jac), 3),
            "months_gained": gained, "months_lost": lost,
            "north_dry_pole_classes": classes,
            "expanded_dry_lat_median": float(lat_dist.median()),
            "expanded_dry_lat_p90": float(lat_dist.quantile(0.9)),
            "expanded_dry_poles_at_new_top_row": int(
                (lat_dist >= top - 0.25).sum()),
        }
    pd.DataFrame(rows).to_csv(OUT / "edge_test_poles.csv", index=False)
    (OUT / "edge_test_summary.json").write_text(json.dumps(summary,
                                                            indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
