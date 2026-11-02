"""Loading monthly reanalysis fields, unit conversion, and common-grid regridding.

Regridding note: precipitation is interpolated linearly (not conservatively).
For coarse-to-fine or similar-resolution grids this is a defensible
simplification, but it should be stated as a limitation, and a conservative
remap (e.g. xESMF) is a reasonable robustness check.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.interpolate import LinearNDInterpolator


@dataclass
class MonthlyDataset:
    name: str
    precip: np.ndarray        # (T, Y, X) mm/month
    tmean: np.ndarray         # (T, Y, X) deg C
    lat: np.ndarray           # (Y,) regular grid
    lon: np.ndarray           # (X,) regular grid
    dates: pd.DatetimeIndex   # month starts
    is_synthetic: bool = False


def month_starts(time_values):
    return pd.DatetimeIndex(time_values).to_period("M").to_timestamp()


def to_mm_per_month(x, dates, units):
    """Convert a precipitation field to mm/month.

    units: 'mm/month' | 'mm/day' | 'kg m-2 s-1' | 'm/day'
    (ERA5 monthly means of daily totals are typically 'm/day'.)
    """
    dim = dates.days_in_month.values.astype(float)[:, None, None]
    if units == "mm/month":
        return x
    if units == "mm/day":
        return x * dim
    if units == "kg m-2 s-1":
        return x * 86400.0 * dim
    if units == "m/day":
        return x * 1000.0 * dim
    raise ValueError(f"unsupported precipitation units {units!r}")


def to_celsius(x, units):
    if units in ("degC", "C"):
        return x
    if units == "K":
        return x - 273.15
    raise ValueError(f"unsupported temperature units {units!r}")


def open_monthly_field(path, var, lat_name="lat", lon_name="lon", time_name="time"):
    """Read one variable. Returns (values (T,Y,X), lat, lon, dates); lat/lon may be 1-D or 2-D."""
    import xarray as xr
    ds = xr.open_dataset(path)
    da = ds[var]
    lat = ds[lat_name].values
    lon = ds[lon_name].values
    dates = month_starts(ds[time_name].values)
    return np.asarray(da.values, dtype=float), lat, lon, dates


def _lon_to_180(lon):
    return ((np.asarray(lon) + 180.0) % 360.0) - 180.0


def regrid(values, src_lat, src_lon, tgt_lat, tgt_lon):
    """Linear interpolation from a regular OR curvilinear source grid onto a
    regular target grid (tgt_lat (Y,), tgt_lon (X,)). One Delaunay
    triangulation is built and reused for every time step."""
    src_lat = np.asarray(src_lat)
    src_lon = _lon_to_180(src_lon)
    if src_lat.ndim == 1:
        src_lon, src_lat = np.meshgrid(src_lon, src_lat)
    T = values.shape[0]
    pts = np.column_stack([src_lon.ravel(), src_lat.ravel()])
    vals = values.reshape(T, -1).T            # (npts, T)
    interp = LinearNDInterpolator(pts, vals, fill_value=np.nan)
    gx, gy = np.meshgrid(_lon_to_180(tgt_lon), tgt_lat)
    out = interp(np.column_stack([gx.ravel(), gy.ravel()]))   # (ny*nx, T)
    return out.T.reshape(T, len(tgt_lat), len(tgt_lon))


def restrict_period(ds, start, end):
    keep = (ds.dates >= pd.Timestamp(start)) & (ds.dates <= pd.Timestamp(end))
    return MonthlyDataset(ds.name, ds.precip[keep], ds.tmean[keep], ds.lat, ds.lon,
                          ds.dates[keep], ds.is_synthetic)


def common_period(datasets):
    start = max(d.dates.min() for d in datasets)
    end = min(d.dates.max() for d in datasets)
    if start >= end:
        raise ValueError("datasets have no overlapping period")
    return start, end
