"""cdpe_sens: sensitivity and uncertainty analysis for concurrent
drought-pluvial event (CDPE) detection.

The package separates four concerns so each can be audited on its own:

    spei         - PET, accumulation, and standardization (SPEI/SPI)
    events       - CDPE detection (pluggable; replace with your published algorithm)
    sensitivity  - full-factorial scenario runs, variance decomposition,
                   one-at-a-time agreement, bootstrap sampling uncertainty
    io           - NetCDF loading, unit conversion, common-grid regridding

``synthetic`` exists ONLY for unit tests. Nothing generated from it may be
reported as a result (see ``scripts/run_analysis.py`` for the guard).
"""

__version__ = "0.1.0"

from .spei import thornthwaite_pet, accumulate, compute_spei  # noqa: F401
from .events import detect_cdpe, event_table  # noqa: F401
from .author_detector import (  # noqa: F401
    classify_month_author,
    detect_cdpe_author,
    make_author_detector,
)
from .sensitivity import (  # noqa: F401
    run_sensitivity,
    variance_decomposition,
    oat_agreement,
    bootstrap_rate_ci,
    annual_counts,
    interannual_correlation,
)
