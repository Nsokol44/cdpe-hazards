"""Port-vs-release check (companion diagnostic to code/28_subset_test_companion.py).

The subset test (28) shows the hazards Arm A SPEI-1 catalogue (46 months,
SPEIbase v2.10) and the companion's published catalogue trimmed to the same
window (52 months, SPEIbase v2.11) agree on only 32 months. Two candidate
causes remain: (i) the input fields differ (release v2.10 vs v2.11), or
(ii) the Arm A detector port differs from the companion's original detector.

This script separates them: it runs the Arm A port
(cdpe_sens.author_detector.detect_cdpe_author, defaults theta=1.5, r=4.0,
f=0.5, q=0.10) on the SAME v2.11 spei01 field that the original detector
just used to regenerate the published 52, over the Arm A window
1980-01..2023-12. If the port returns exactly the companion's trimmed 52,
the port is faithful and the SPEI-1 gap is wholly an input-field (release)
difference. Deterministic; no randomness.

Run: python3 code/29_port_vs_release_check.py
Output: code/port_vs_release_output.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

WS = Path.home() / "workspace"
SEG_RERUN = WS / "seg-revision" / "seg_rerun"
SPEI01_V211 = SEG_RERUN / "data" / "spei01.nc"
SENS = WS / "papers-finish" / "cdpe_sensitivity"
ARM_A_SERIES = SENS / "results" / "run_armA_2026-10-05" / "cdpe_monthly_series.csv"
OUT_CSV = Path(__file__).with_name("port_vs_release_output.csv")


def main() -> None:
    sys.path.insert(0, str(SEG_RERUN))
    sys.path.insert(0, str(SENS))
    import Sokol_Study1_CDPE_Identification as s1
    from cdpe_sens.author_detector import detect_cdpe_author

    spei_full = s1.load_spei(str(SPEI01_V211))

    # Reference: original detector, Arm A window (trim of the published 52).
    spei_trim = spei_full.sel(time=slice("1980-01-01", "2023-12-31"))
    orig_events = s1.identify_cdpes(spei_trim)
    companion_trim = sorted(pd.Timestamp(t).strftime("%Y-%m") for t in orig_events)

    # Port on the identical field and window.
    lat = spei_trim["lat"].values
    lon = spei_trim["lon"].values
    months = [pd.Timestamp(t).strftime("%Y-%m") for t in spei_trim.time.values]
    res = detect_cdpe_author(np.asarray(spei_trim.values, dtype=float), lat, lon)
    port_months = sorted(m for m, c in zip(months, res["cdpe"]) if c)

    series = pd.read_csv(ARM_A_SERIES)
    arm_a = sorted(
        pd.to_datetime(
            series.loc[series["SPEI-1|thr=1.5|r=4.0"] == 1, "date"]
        ).dt.strftime("%Y-%m")
    )

    rows = [
        ("companion_trimmed_original_detector", len(companion_trim)),
        ("armA_port_on_v211_same_window", len(port_months)),
        ("port_equals_companion_trimmed", port_months == companion_trim),
        ("port_intersection_with_armA_v210", len(set(port_months) & set(arm_a))),
        ("port_only_vs_companion", ";".join(sorted(set(port_months) - set(companion_trim)))),
        ("companion_only_vs_port", ";".join(sorted(set(companion_trim) - set(port_months)))),
    ]
    pd.DataFrame(rows, columns=["quantity", "value"]).to_csv(OUT_CSV, index=False)
    for k, v in rows:
        print(f"{k}: {v}")
    print(f"Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
