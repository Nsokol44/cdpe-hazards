"""SPEI/SPI computation, fully vectorized over (time, lat, lon).

Water balance D = P - PET is accumulated over ``timescale`` months, then
standardized separately for each calendar month and grid cell against a
calibration period. Methodological choices that matter for CDPE detection
are exposed as arguments so they can be treated as factors:

* ``timescale``   accumulation window (months)
* ``cal_period``  (first_year, last_year) used to fit the reference distribution
* ``dist``        'loglogistic' (3-parameter, PWM fit; Vicente-Serrano et al. 2010)
                  or 'empirical' (Gringorten plotting position, nonparametric)
* ``pet``         None gives an SPI-like precipitation-only index
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import gamma as gamma_fn
from scipy.stats import norm

EPS = 1e-6
MIN_CAL_N = 20  # minimum calibration values per (calendar month, cell)


def thornthwaite_pet(tmean, lat, dates):
    """Thornthwaite (1948) monthly PET in mm/month.

    Parameters
    ----------
    tmean : (T, Y, X) monthly mean air temperature in deg C
    lat   : (Y,) latitude in degrees (regular grid)
    dates : pandas.DatetimeIndex of length T (month starts)
    """
    tmean = np.asarray(tmean, dtype=float)
    months = dates.month.values
    clim = np.stack([np.nanmean(tmean[months == m], axis=0) for m in range(1, 13)])
    heat = np.nansum((np.clip(clim, 0, None) / 5.0) ** 1.514, axis=0)  # (Y, X)
    with np.errstate(divide="ignore", invalid="ignore"):
        a = 6.75e-7 * heat**3 - 7.71e-5 * heat**2 + 1.792e-2 * heat + 0.49239
        t = tmean
        pet_unadj = 16.0 * (10.0 * np.clip(t, 0, None) / heat[None]) ** a[None]
        hot = -415.85 + 32.24 * t - 0.43 * t**2
        pet_unadj = np.where(t >= 26.5, hot, pet_unadj)
        pet_unadj = np.where(t <= 0, 0.0, pet_unadj)
        pet_unadj = np.where(heat[None] <= 0, 0.0, pet_unadj)

    # day-length and month-length correction (FAO-56 day-length formula)
    mid = pd.DatetimeIndex(dates) + pd.Timedelta(days=14)
    doy = mid.dayofyear.values.astype(float)
    delta = 0.409 * np.sin(2 * np.pi * doy / 365.0 - 1.39)  # (T,)
    phi = np.deg2rad(np.asarray(lat, dtype=float))  # (Y,)
    x = -np.tan(phi)[None, :] * np.tan(delta)[:, None]  # (T, Y)
    ws = np.arccos(np.clip(x, -1, 1))
    daylen = 24.0 / np.pi * ws  # hours
    corr = (daylen / 12.0)[:, :, None] * (dates.days_in_month.values / 30.0)[:, None, None]
    return pet_unadj * corr


def accumulate(x, k):
    """Trailing k-month sum along axis 0. First k-1 steps are NaN."""
    x = np.asarray(x, dtype=float)
    if k == 1:
        return x.copy()
    out = np.full_like(x, np.nan)
    T = x.shape[0]
    acc = np.zeros_like(x[k - 1:])
    for j in range(k):
        acc = acc + x[k - 1 - j: T - j]
    out[k - 1:] = acc
    return out


def _loglogistic_cdf(x_eval, x_cal_sorted, n_valid):
    """Fit a 3-parameter log-logistic by probability-weighted moments on
    sorted calibration values (NaNs last) and evaluate the CDF at x_eval.
    Returns (F, ok) where ok marks cells with a valid fit (beta > 1, alpha > 0)."""
    Nc = x_cal_sorted.shape[0]
    i = np.arange(1, Nc + 1, dtype=float)[:, None, None]
    n = n_valid[None].astype(float)
    valid = i <= n
    with np.errstate(divide="ignore", invalid="ignore"):
        Fi = (i - 0.35) / n
        xs = np.where(valid, x_cal_sorted, 0.0)
        w0 = (xs * valid).sum(0) / n[0]
        w1 = (xs * (1 - Fi) * valid).sum(0) / n[0]
        w2 = (xs * (1 - Fi) ** 2 * valid).sum(0) / n[0]
        beta = (2 * w1 - w0) / (6 * w1 - w0 - 6 * w2)
        g1 = gamma_fn(1 + 1 / beta)
        g2 = gamma_fn(1 - 1 / beta)
        alpha = (w0 - 2 * w1) * beta / (g1 * g2)
        gam = w0 - alpha * g1 * g2
        ok = (np.isfinite(beta) & np.isfinite(alpha) & np.isfinite(gam)
              & (beta > 1) & (alpha > 0))
        d = x_eval - gam[None]
        F = 1.0 / (1.0 + (alpha[None] / d) ** beta[None])
        F = np.where(d <= 0, 0.0, F)
    return F, ok


def _empirical_cdf(x_eval, x_cal_sorted, n_valid, max_elems=20_000_000):
    """Gringorten plotting-position ECDF, chunked over rows to cap memory."""
    Nm, Y, X = x_eval.shape
    Nc = x_cal_sorted.shape[0]
    out = np.full(x_eval.shape, np.nan)
    rows = max(1, int(max_elems // max(1, Nm * Nc * X)))
    for y0 in range(0, Y, rows):
        y1 = min(Y, y0 + rows)
        cal = x_cal_sorted[:, y0:y1]
        xe = x_eval[:, y0:y1]
        cnt = (cal[None] <= xe[:, None]).sum(axis=1).astype(float)
        n = n_valid[None, y0:y1].astype(float)
        r = np.clip(cnt, 1, n)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[:, y0:y1] = (r - 0.44) / (n + 0.12)
    return out


def _standardize(x_eval, x_cal, dist):
    """Standardize x_eval (Nm,Y,X) against x_cal (Nc,Y,X).
    Returns (z, fallback_fraction)."""
    cal_sorted = np.sort(x_cal, axis=0)  # NaNs sort last
    n_valid = np.isfinite(x_cal).sum(axis=0)
    enough = n_valid >= MIN_CAL_N
    F_emp = _empirical_cdf(x_eval, cal_sorted, n_valid)
    fb = 0.0
    if dist == "empirical":
        F = F_emp
    elif dist == "loglogistic":
        F_ll, ok = _loglogistic_cdf(x_eval, cal_sorted, n_valid)
        use = ok & enough
        F = np.where(use[None], F_ll, F_emp)
        denom = max(1, int(enough.sum()))
        fb = float((enough & ~ok).sum()) / denom
    else:
        raise ValueError(f"unknown dist {dist!r}")
    F = np.where(enough[None] & np.isfinite(x_eval), F, np.nan)
    z = norm.ppf(np.clip(F, EPS, 1 - EPS))
    return z, fb


def compute_spei(precip, pet, dates, timescale, cal_period=None,
                 dist="loglogistic", return_diagnostics=False):
    """Standardized (P - PET) index, shape (T, Y, X).

    ``pet=None`` yields a precipitation-only (SPI-like) index using the same
    distribution machinery, so SPEI-vs-SPI differences isolate the evaporative
    demand term rather than the fitting method.
    """
    precip = np.asarray(precip, dtype=float)
    D = precip - np.asarray(pet, dtype=float) if pet is not None else precip
    A = accumulate(D, timescale)
    months = dates.month.values
    years = dates.year.values
    if cal_period is None:
        cal_t = np.ones(len(dates), dtype=bool)
    else:
        cal_t = (years >= cal_period[0]) & (years <= cal_period[1])
    out = np.full_like(A, np.nan)
    fb_list = []
    for m in range(1, 13):
        idx = np.where(months == m)[0]
        cidx = idx[cal_t[idx]]
        if len(cidx) < MIN_CAL_N:
            continue
        z, fb = _standardize(A[idx], A[cidx], dist)
        out[idx] = z
        fb_list.append(fb)
    if return_diagnostics:
        return out, {"loglogistic_fallback_fraction":
                     float(np.mean(fb_list)) if fb_list else float("nan")}
    return out
