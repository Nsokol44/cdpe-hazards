"""SYNTHETIC DATA - FOR UNIT TESTS AND SMOKE TESTS ONLY.

Everything produced here is random. It exists so the code can be checked for
correctness (shapes, monotonicity, identities). No number computed from it
may appear in a manuscript. Datasets are flagged ``is_synthetic=True`` and
``scripts/run_analysis.py`` refuses to run on them unless explicitly told to,
and then stamps every output directory as non-publishable.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter

from .io import MonthlyDataset


def make_synthetic_dataset(name="synthetic", seed=0, start_year=1980, n_years=40,
                           ny=24, nx=30, lat0=30.0, dlat=1.0, lon0=-100.0, dlon=1.0,
                           smooth=2.5, noise_scale=0.5):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(f"{start_year}-01-01", periods=12 * n_years, freq="MS")
    T = len(dates)
    lat = lat0 + dlat * np.arange(ny)
    lon = lon0 + dlon * np.arange(nx)
    month = dates.month.values

    def field():
        f = rng.standard_normal((T, ny, nx))
        f = gaussian_filter(f, sigma=(0, smooth, smooth))
        return f / f.std()

    season_t = 12 + 14 * np.sin(2 * np.pi * (month - 4) / 12.0)
    tmean = season_t[:, None, None] - 0.35 * (lat[None, :, None] - lat0) + 1.0 * field()
    season_p = 80 + 30 * np.sin(2 * np.pi * (month - 2) / 12.0)
    precip = season_p[:, None, None] * np.exp(noise_scale * field())
    return MonthlyDataset(name, precip, tmean, lat, lon, dates, is_synthetic=True)
