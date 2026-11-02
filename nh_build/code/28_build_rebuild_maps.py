#!/usr/bin/env python3
"""Workstream D (2026-11-02) - publication-grade map figures for the
SPEIbase analysis (Jan 1980 - Dec 2023; baseline SPEI-1, thr 1.5,
r 4.0 deg; 46 CDPE months).

Figure 1 (fig_map_geography_speibase): rebuild of the Natural Hazards
package's Figure 1 design on the as-of-record report series --
(a) tornado + severe-hail (>= 1.00 in) reports per 1-degree cell;
(b) share of each cell's reports falling in the 46 baseline CDPE
months, cells with >= 25 reports, BrBG centred on the proportional
expectation 46/528 = 8.71%. Report counts follow the frozen Step-04
rules (domain box 25-50 N, 125-66 W; county-centroid fallback via the
Census gazetteer) over the win2023 tree's Storm Events files and are
asserted against its Step-04 series totals (54,607 tornadoes;
229,650 hail >= 1 in; 379,430 hail overall).

Figure 2 (fig_map_poles_speibase): pole geography of the 46 baseline
months from the Workstream B run (poles_by_scenario.csv). Counts of
CDPE months whose dry (a) / wet (b) pole fell in each 1-degree cell,
one shared colour scale (cividis) and one shared legend for both
panels, pole locations overlaid as points. Basemap: full North
America land context from Natural Earth 10 m admin-1
(data/natural_earth/ne_10m_admin_1_states_provinces.shp) -- country
outlines and coastlines from the dissolved Canada / Mexico / United
States polygons, state and province lines subtle -- because many
poles sit over Canada and northern Mexico.

Both figures: exactly 6.0 in wide, 300-dpi PNG + vector PDF,
colourblind-safe palettes, no raw variable names. Figure 1 uses state
outlines from the hazards project's us_states_simplified.geojson.
"""
import gzip
import io
import json
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm, TwoSlopeNorm

PKG = Path(__file__).resolve().parents[1]
FIN = PKG.parent
RUN = PKG / "results" / "run_armA_speibase_rebuild_2026-11-02"
B_DIR = RUN / "B_speibase_full"
W23 = FIN / "cdpe-hazards-nclimgrid" / "win2023"
STATES = (FIN / "cdpe-hazards-natural-hazards" / "code"
          / "us_states_simplified.geojson")
NE_ADMIN1 = (PKG / "data" / "natural_earth"
             / "ne_10m_admin_1_states_provinces.shp")
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = 25.0, 50.0, -125.0, -66.0
USECOLS = ["BEGIN_YEARMONTH", "EVENT_TYPE", "TOR_F_SCALE", "MAGNITUDE",
           "BEGIN_LAT", "BEGIN_LON", "STATE_FIPS", "CZ_FIPS"]
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
    "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "axes.linewidth": 0.6,
})

STATES_GEO = json.loads(STATES.read_text())


def draw_states(ax):
    for feat in STATES_GEO["features"]:
        geom = feat["geometry"]
        if geom["type"] == "Polygon":
            polys = [geom["coordinates"]]
        elif geom["type"] == "MultiPolygon":
            polys = geom["coordinates"]
        else:
            continue
        for poly in polys:
            for ring in poly:
                xs = [c[0] for c in ring]
                ys = [c[1] for c in ring]
                ax.plot(xs, ys, color="0.25", lw=0.35, zorder=3,
                        solid_joinstyle="round")


def style_ax(ax, ylabel=False):
    draw_states(ax)
    ax.set_xlim(-125, -66)
    ax.set_ylim(24, 50)
    ax.set_aspect(1 / np.cos(np.radians(37)))
    ax.set_xlabel("Longitude (degrees)")
    if ylabel:
        ax.set_ylabel("Latitude (degrees)")
    else:
        ax.set_yticklabels([])


_NA_BASEMAP = None


def na_basemap():
    """Natural Earth 10 m admin-1 units for Canada, Mexico and the
    United States, clipped to just beyond the pole-figure frame, plus
    the dissolved country polygons (coastlines / national borders)."""
    global _NA_BASEMAP
    if _NA_BASEMAP is None:
        import geopandas as gpd
        from shapely.geometry import box
        units = gpd.read_file(NE_ADMIN1, bbox=(-126.0, 23.0, -65.0, 51.5))
        units = units[units["admin"].isin(
            ["Canada", "Mexico", "United States of America"])]
        units = units.clip(box(-126.5, 23.2, -64.5, 51.8))
        countries = units.dissolve(by="admin")
        _NA_BASEMAP = (units, countries)
    return _NA_BASEMAP


def draw_na_land(ax):
    units, countries = na_basemap()
    countries.plot(ax=ax, facecolor="#f4f4f0", edgecolor="none",
                   zorder=1)
    units.boundary.plot(ax=ax, color="0.60", linewidth=0.28, zorder=3)
    countries.boundary.plot(ax=ax, color="0.28", linewidth=0.55,
                            zorder=3)


def style_ax_poles(ax, ylabel=False):
    draw_na_land(ax)
    ax.set_xlim(-125.6, -65.4)
    ax.set_ylim(23.9, 50.9)
    ax.set_aspect(1 / np.cos(np.radians(37)))
    ax.set_xlabel("Longitude (degrees)")
    if ylabel:
        ax.set_ylabel("Latitude (degrees)")
    else:
        ax.set_ylabel("")
        ax.set_yticklabels([])


def load_centroids():
    zpath = W23 / "data" / "raw" / "reference" / "gaz_counties_national.zip"
    with zipfile.ZipFile(zpath) as z:
        name = [n for n in z.namelist() if n.endswith(".txt")][0]
        with z.open(name) as f:
            df = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8"),
                             sep="\t", dtype={"GEOID": str})
    df.columns = [c.strip() for c in df.columns]
    return {int(g): (float(la), float(lo)) for g, la, lo in
            zip(df["GEOID"], df["INTPTLAT"], df["INTPTLONG"])}


def baseline_month_set():
    ser = pd.read_csv(B_DIR / "cdpe_monthly_series.csv", parse_dates=["date"])
    col = "SPEI-1|thr=1.5|r=4.0"
    months = {d.strftime("%Y-%m") for d, v in zip(ser["date"], ser[col])
              if int(v) == 1}
    assert len(months) == 46, len(months)
    return months


def report_grids():
    centroids = load_centroids()
    cdpe = baseline_month_set()
    series = pd.read_csv(W23 / "results" / "hazard_series_storm.csv")
    exp = (int(series["tornado_all"].sum()), int(series["hail_ge1in"].sum()),
           int(series["hail_all"].sum()))
    assert exp == (54607, 229650, 379430), exp
    files = sorted((W23 / "data" / "raw" / "storm_events").glob(
        "StormEvents_details-*.csv.gz"))
    assert len(files) == 44, len(files)
    recs = []
    n_tor = n_hail_ge = n_hail_all = 0
    for path in files:
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
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
            if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
                continue
            if r.EVENT_TYPE == "Tornado":
                n_tor += 1
                recs.append((lat, lon, key))
            else:
                n_hail_all += 1
                if pd.notna(r.MAGNITUDE) and float(r.MAGNITUDE) >= 1.0:
                    n_hail_ge += 1
                    recs.append((lat, lon, key))
    assert (n_tor, n_hail_ge, n_hail_all) == exp, (n_tor, n_hail_ge, n_hail_all)
    print(f"report totals asserted vs Step 04: tornado {n_tor}, "
          f"hail>=1in {n_hail_ge}, hail all {n_hail_all}")
    pts = pd.DataFrame(recs, columns=["lat", "lon", "month"])
    pts["clat"] = np.floor(pts["lat"]).astype(int)
    pts["clon"] = np.floor(pts["lon"]).astype(int)
    pts["cdpe"] = pts["month"].isin(cdpe)
    tot = pts.groupby(["clat", "clon"]).size().rename("total")
    inc = pts[pts["cdpe"]].groupby(["clat", "clon"]).size().rename("incdpe")
    grid = pd.concat([tot, inc], axis=1).fillna(0).reset_index()
    grid["share"] = 100.0 * grid["incdpe"] / grid["total"]
    lats = np.arange(24, 51)
    lons = np.arange(-125, -65)
    A = np.full((len(lats) - 1, len(lons) - 1), np.nan)
    Bm = np.full_like(A, np.nan)
    for r in grid.itertuples(index=False):
        i, j = r.clat - 24, r.clon + 125
        if 0 <= i < A.shape[0] and 0 <= j < A.shape[1]:
            A[i, j] = r.total
            if r.total >= 25:
                Bm[i, j] = r.share
    return lats, lons, A, Bm


def fig_report_geography():
    lats, lons, A, Bm = report_grids()
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 3.2),
                             constrained_layout=True)
    m0 = axes[0].pcolormesh(lons, lats, np.ma.masked_invalid(A),
                            cmap="viridis",
                            norm=LogNorm(vmin=1, vmax=np.nanmax(A)),
                            shading="auto", zorder=2)
    axes[0].set_title("(a) Reports per 1-degree cell")
    cb0 = fig.colorbar(m0, ax=axes[0], shrink=0.95, pad=0.015)
    cb0.set_label("Reports per cell")
    cb0.ax.tick_params(labelsize=7.5)
    share_max = np.nanpercentile(Bm, 99)
    norm = TwoSlopeNorm(vmin=0.0, vcenter=100.0 * 46 / 528,
                        vmax=max(share_max, 12.0))
    m1 = axes[1].pcolormesh(lons, lats, np.ma.masked_invalid(Bm),
                            cmap="BrBG", norm=norm, shading="auto", zorder=2)
    axes[1].set_title("(b) Share in CDPE months (%)")
    cb1 = fig.colorbar(m1, ax=axes[1], shrink=0.95, pad=0.015)
    cb1.set_label("Percent of the cell's reports")
    cb1.ax.tick_params(labelsize=7.5)
    style_ax(axes[0], ylabel=True)
    style_ax(axes[1])
    fig.suptitle("Tornado and severe-hail reports, Jan 1980–Dec 2023,\n"
                 "and their share in the 46 baseline CDPE months",
                 fontsize=9.5)
    for ext in ("png", "pdf"):
        fig.savefig(RUN / f"fig_map_geography_speibase.{ext}", dpi=300)
    plt.close(fig)
    print("wrote fig_map_geography_speibase.png/.pdf | "
          f"cells {(~np.isnan(A)).sum()}, share cells {(~np.isnan(Bm)).sum()}, "
          f"median share {np.nanmedian(Bm):.1f}%")


def fig_pole_geography():
    poles = pd.read_csv(B_DIR / "poles_by_scenario.csv", parse_dates=["date"])
    base = poles[(poles["index"] == "SPEI-1") & (poles["threshold"] == 1.5)
                 & (poles["radius_deg"] == 4.0) & (poles["is_cdpe"] == 1)]
    assert len(base) == 46, len(base)
    lat_e = np.arange(24, 51, 1.0)
    lon_e = np.arange(-125, -65, 1.0)

    def counts(la, lo):
        H, _, _ = np.histogram2d(la, lo, bins=[lat_e, lon_e])
        return np.ma.masked_where(H == 0, H)

    Hd = counts(base["dry_lat"].values, base["dry_lon"].values)
    Hw = counts(base["wet_lat"].values, base["wet_lon"].values)
    vmax = int(max(Hd.max(), Hw.max()))
    print(f"pole cells used: dry {(Hd > 0).sum()}, wet {(Hw > 0).sum()}, "
          f"vmax {vmax}")
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 3.0),
                             constrained_layout=True)
    m = None
    for ax, H, la, lo, title in (
            (axes[0], Hd, base["dry_lat"], base["dry_lon"], "(a) Dry pole"),
            (axes[1], Hw, base["wet_lat"], base["wet_lon"], "(b) Wet pole")):
        m = ax.pcolormesh(lon_e, lat_e, H, cmap="cividis", vmin=1,
                          vmax=vmax, shading="auto", zorder=2)
        ax.scatter(lo, la, s=11, facecolor="white", edgecolor="0.1",
                   linewidths=0.45, zorder=5)
        ax.set_title(title)
        style_ax_poles(ax, ylabel=(ax is axes[0]))
    cb = fig.colorbar(m, ax=axes, shrink=0.95, pad=0.015)
    cb.set_label("CDPE months with pole in cell")
    cb.ax.tick_params(labelsize=7.5)
    cb.set_ticks(range(1, vmax + 1))
    fig.suptitle("Dry- and wet-pole locations in the 46 baseline CDPE "
                 "months, Jan 1980–Dec 2023", fontsize=9.5)
    for ext in ("png", "pdf"):
        fig.savefig(RUN / f"fig_map_poles_speibase.{ext}", dpi=300)
    plt.close(fig)
    print("wrote fig_map_poles_speibase.png/.pdf")


if __name__ == "__main__":
    fig_report_geography()
    fig_pole_geography()
