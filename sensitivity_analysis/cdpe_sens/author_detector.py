"""The author's published CDPE detector (Sokol Study 1), as a pluggable
``cdpe_sens`` detector.

This module is a NumPy port of ``classify_month`` / ``buffer_mask`` /
``find_extreme_cell`` / ``identify_cdpes`` in
``Sokol_Study1_CDPE_Identification.py`` (lines 317-398). It replaces the
generic stand-in in :mod:`cdpe_sens.events` for analyses of the author's
own algorithm. The extracted specification, the factor mapping, and every
adaptation made here are documented in ``AUTHOR_ALGORITHM.md``.

The algorithm, per month, on a standardized-index field (SPEI in the
author's pipeline, which uses the precomputed SPEIbase product):

1. **Value identification.** The dry pole is the grid cell with the
   minimum index value in the domain that month; the wet pole is the
   cell with the maximum. (Ties resolve to the first cell in row-major
   order, matching xarray's ``argmin``/``argmax`` behaviour.)
2. **Zonal extraction.** Around each pole, a circular buffer of radius
   ``radius_deg`` in *degree space* -- Euclidean distance
   ``sqrt((lat-c_lat)^2 + (lon-c_lon)^2) <= radius_deg`` on the cell
   coordinates. This is deliberately NOT a geodesic buffer; it matches
   the author's code.
3. **Sequestration (qualification).** A pole's zone qualifies when, over
   the cells INSIDE its buffer only:
     * the fraction of cells with a missing (NaN) index is
       ``<= max_na_frac`` (author baseline 0.10), AND
     * at least ``majority_frac`` (author baseline 0.5) of the *valid*
       buffer cells satisfy the threshold: ``<= -threshold`` for the dry
       zone, ``>= +threshold`` for the wet zone.
   The author's code implements ``frac >= majority_frac`` (so exactly
   50% qualifies), even though the Study 1 parameter comment and the
   original manuscript wording say ">50%". This port follows the code.
4. A month is a CDPE month iff BOTH zones qualify in the same month.
   Months are classified independently: there is no duration or merging
   rule in the identification step. (The author's pipeline treats each
   qualifying month as one event; its declustering diagnostic is a
   separate robustness check and is NOT part of identification.)

Signature note: :func:`cdpe_sens.sensitivity.run_sensitivity` calls
``detector(spei, drought_thr, pluvial_thr, min_area_frac,
min_cluster_cells)`` positionally. This detector's native parameters are
(threshold, radius, majority fraction, NA fraction) and it needs the
grid coordinates, which the generic call does not pass. Use
:func:`make_author_detector` to bind coordinates and parameters into a
closure with the generic signature. Two generic concepts have NO
counterpart in the author's algorithm and are ignored by that closure
(loudly -- see its docstring): ``min_area_frac`` (his spatial-extent
criterion is the within-buffer majority, not a domain fraction) and
``min_cluster_cells`` (he has no connected-cluster filter).
"""
from __future__ import annotations

import numpy as np

# Author baseline configuration (Study 1, lines 124-128).
AUTHOR_THRESHOLD = 1.5
AUTHOR_RADIUS_DEG = 4.0
AUTHOR_MAJORITY_FRAC = 0.5
AUTHOR_MAX_NA_FRAC = 0.10


def buffer_mask_np(lat, lon, center_lat, center_lon, radius_deg):
    """Boolean (Y, X) mask of cells within ``radius_deg`` of the centre,
    using Euclidean distance in degree space -- a direct port of the
    author's ``buffer_mask`` (Study 1, lines 326-333)."""
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    lon2d, lat2d = np.meshgrid(lon, lat)
    dist = np.sqrt((lat2d - center_lat) ** 2 + (lon2d - center_lon) ** 2)
    return dist <= radius_deg


def _qualifies(vals_in_buffer, want, threshold, majority_frac, max_na_frac):
    """The author's within-buffer qualification test (Study 1, lines
    356-379). ``vals_in_buffer`` is the 1-D array of field values at the
    buffer cells (NaNs included). Returns (qualifies, frac_beyond,
    na_frac); the fractions are NaN when the buffer is empty."""
    n_buffer = vals_in_buffer.size
    if n_buffer == 0:
        return False, float("nan"), float("nan")
    n_na = int(np.isnan(vals_in_buffer).sum())
    na_frac = n_na / n_buffer
    n_valid = n_buffer - n_na
    if n_valid == 0:
        return False, float("nan"), na_frac
    if na_frac > max_na_frac:
        return False, float("nan"), na_frac
    valid = vals_in_buffer[~np.isnan(vals_in_buffer)]
    if want == "dry":
        frac = float((valid <= -threshold).sum()) / n_valid
    else:
        frac = float((valid >= threshold).sum()) / n_valid
    return frac >= majority_frac, frac, na_frac


def classify_month_author(field2d, lat, lon, threshold=AUTHOR_THRESHOLD,
                          radius_deg=AUTHOR_RADIUS_DEG,
                          majority_frac=AUTHOR_MAJORITY_FRAC,
                          max_na_frac=AUTHOR_MAX_NA_FRAC):
    """Classify one monthly index field, mirroring the author's
    ``classify_month`` return values.

    Returns a dict with ``is_event``, the pole centres
    (``dry_center``/``wet_center`` as (lat, lon)), the within-buffer
    qualifying fractions (``dry_frac``/``wet_frac`` -- the share of valid
    buffer cells beyond the threshold; NOT domain area fractions), the
    within-buffer NaN fractions, and ``spei_min``/``spei_max``.

    Documented deviation: for an all-NaN month the author's xarray code
    raises inside ``argmin``; this port returns ``is_event=False`` with
    NaN statistics instead, so batch runs over fields with spin-up or
    fully-missing months do not abort.
    """
    field2d = np.asarray(field2d, dtype=float)
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    if not np.isfinite(field2d).any():
        return {"is_event": False, "dry_center": (float("nan"), float("nan")),
                "wet_center": (float("nan"), float("nan")),
                "dry_frac": float("nan"), "wet_frac": float("nan"),
                "dry_na_frac": float("nan"), "wet_na_frac": float("nan"),
                "spei_min": float("nan"), "spei_max": float("nan")}

    flat = np.where(np.isfinite(field2d), field2d, np.inf)
    iy, ix = np.unravel_index(int(np.argmin(flat)), field2d.shape)
    dry_center = (float(lat[iy]), float(lon[ix]))
    flat = np.where(np.isfinite(field2d), field2d, -np.inf)
    iy, ix = np.unravel_index(int(np.argmax(flat)), field2d.shape)
    wet_center = (float(lat[iy]), float(lon[ix]))

    dry_buf = buffer_mask_np(lat, lon, *dry_center, radius_deg)
    wet_buf = buffer_mask_np(lat, lon, *wet_center, radius_deg)

    dry_ok, dry_frac, dry_na = _qualifies(field2d[dry_buf], "dry",
                                          threshold, majority_frac, max_na_frac)
    wet_ok, wet_frac, wet_na = _qualifies(field2d[wet_buf], "wet",
                                          threshold, majority_frac, max_na_frac)
    return {"is_event": bool(dry_ok and wet_ok),
            "dry_center": dry_center, "wet_center": wet_center,
            "dry_frac": dry_frac, "wet_frac": wet_frac,
            "dry_na_frac": dry_na, "wet_na_frac": wet_na,
            "spei_min": float(np.nanmin(field2d)),
            "spei_max": float(np.nanmax(field2d))}


def detect_cdpe_author(spei, lat, lon, threshold=AUTHOR_THRESHOLD,
                       radius_deg=AUTHOR_RADIUS_DEG,
                       majority_frac=AUTHOR_MAJORITY_FRAC,
                       max_na_frac=AUTHOR_MAX_NA_FRAC):
    """Author detector over a (T, Y, X) index field.

    Returns the standard detector dict plus per-month diagnostics.
    WARNING -- key semantics differ from the generic detector:
    ``drought_frac``/``pluvial_frac`` here are the author's *within-buffer
    qualifying fractions* (share of valid cells in the dry/wet pole's
    buffer beyond the threshold), not fractions of the domain. Do not
    compare them directly with the generic detector's area fractions.
    ``evaluable`` is False only for months with no finite cell at all
    (the author's domain has no spin-up concept: SPEIbase fields are
    complete from the first month).
    """
    spei = np.asarray(spei, dtype=float)
    T = spei.shape[0]
    cdpe = np.zeros(T, dtype=bool)
    evaluable = np.zeros(T, dtype=bool)
    dry_frac = np.full(T, np.nan)
    wet_frac = np.full(T, np.nan)
    dry_center = np.full((T, 2), np.nan)
    wet_center = np.full((T, 2), np.nan)
    spei_min = np.full(T, np.nan)
    spei_max = np.full(T, np.nan)
    for t in range(T):
        r = classify_month_author(spei[t], lat, lon, threshold=threshold,
                                  radius_deg=radius_deg,
                                  majority_frac=majority_frac,
                                  max_na_frac=max_na_frac)
        cdpe[t] = r["is_event"]
        evaluable[t] = np.isfinite(r["spei_min"])
        dry_frac[t] = r["dry_frac"]
        wet_frac[t] = r["wet_frac"]
        dry_center[t] = r["dry_center"]
        wet_center[t] = r["wet_center"]
        spei_min[t] = r["spei_min"]
        spei_max[t] = r["spei_max"]
    return {"cdpe": cdpe, "drought_frac": dry_frac, "pluvial_frac": wet_frac,
            "evaluable": evaluable, "dry_center": dry_center,
            "wet_center": wet_center, "spei_min": spei_min,
            "spei_max": spei_max}


def make_author_detector(lat, lon, radius_deg=AUTHOR_RADIUS_DEG,
                         majority_frac=AUTHOR_MAJORITY_FRAC,
                         max_na_frac=AUTHOR_MAX_NA_FRAC):
    """Bind grid coordinates and author parameters into a detector with
    the generic ``cdpe_sens`` signature, for use as
    ``run_sensitivity(..., detector=make_author_detector(lat, lon))``.

    The returned callable has signature
    ``(spei, drought_thr, pluvial_thr, min_area_frac, min_cluster_cells)``:

    * ``drought_thr`` is used as the author's (symmetric) threshold. The
      author's algorithm applies ONE threshold to both poles, so the
      callable raises ``ValueError`` if ``drought_thr != pluvial_thr``
      rather than silently generalizing the algorithm.
      (``run_sensitivity`` always passes them equal.)
    * ``min_area_frac`` and ``min_cluster_cells`` are IGNORED: neither
      concept exists in the author's algorithm. Varying them in a
      factorial run with this detector produces identical event series,
      and any variance decomposition over those factors will (correctly,
      for this detector) attribute zero share to them.
    """
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)

    def _detector(spei, drought_thr, pluvial_thr, min_area_frac,
                  min_cluster_cells):
        if drought_thr != pluvial_thr:
            raise ValueError(
                "The author's CDPE algorithm uses a single symmetric SPEI "
                f"threshold; got drought_thr={drought_thr} != "
                f"pluvial_thr={pluvial_thr}. Refusing to generalize it "
                "silently.")
        return detect_cdpe_author(spei, lat, lon, threshold=drought_thr,
                                  radius_deg=radius_deg,
                                  majority_frac=majority_frac,
                                  max_na_frac=max_na_frac)

    return _detector
