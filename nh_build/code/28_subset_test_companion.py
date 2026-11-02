"""Subset test demanded by the 2026-11-02 external review (REVIEW_TRIAGE_2026-11-02, item A).

Question: is the hazards paper's Arm A SPEI-1 shortfall (46 months, 1980-2023,
SPEIbase v2.10) against the companion study's published catalogue (52 months,
1980-2024, SPEIbase v2.11) a window artifact? I.e., if the companion's months
are trimmed to Dec 2023, do the 46 form a subset?

Method: the companion's published month list does not survive on disk as a
file (workspace-wide find for the Study-1 outputs cdpe_event_dates.csv /
spi_vs_spei_events.csv / events_only_spei.csv returns nothing, 2026-11-02).
We therefore regenerate the published catalogue with the companion's own
frozen detector (seg-revision/seg_rerun/Sokol_Study1_CDPE_Identification.py,
imported, unmodified) on the MD5-verified SPEIbase v2.11 spei01 file in
seg_rerun/data/ (MD5 3eba69cbbbf95c671cabbd71e01b6f4c). The regeneration is
accepted as the published catalogue only if it returns exactly 52 events
over 1980-2024 (the companion manuscript's printed count), which also
re-validates the detector port used for the SEG paper.

Deterministic: pure set arithmetic on fixed inputs; no randomness.
Run: python3 code/28_subset_test_companion.py
Outputs: code/subset_test_output.csv (this script's directory).
"""
import hashlib
import sys
from pathlib import Path

import pandas as pd

WS = Path.home() / "workspace"
SEG_RERUN = WS / "seg-revision" / "seg_rerun"
SPEI01_V211 = SEG_RERUN / "data" / "spei01.nc"
ARM_A_SERIES = (
    WS / "papers-finish" / "cdpe_sensitivity" / "results"
    / "run_armA_2026-10-05" / "cdpe_monthly_series.csv"
)
OUT_CSV = Path(__file__).with_name("subset_test_output.csv")
EXPECTED_MD5 = "3eba69cbbbf95c671cabbd71e01b6f4c"
EXPECTED_PUBLISHED_N = 52  # companion manuscript S3.1: "Fifty-two CDPEs ... 1980-2024"


def ym(ts) -> str:
    return pd.Timestamp(ts).strftime("%Y-%m")


def main() -> None:
    md5 = hashlib.md5(SPEI01_V211.read_bytes()).hexdigest()
    assert md5 == EXPECTED_MD5, f"v2.11 spei01 MD5 mismatch: {md5}"

    sys.path.insert(0, str(SEG_RERUN))
    import Sokol_Study1_CDPE_Identification as s1  # companion's frozen detector

    spei = s1.load_spei(str(SPEI01_V211))
    # Mirror the companion script's own main flow: restrict to its declared
    # study period (module constants STUDY_START/STUDY_END = 1980-2024);
    # the raw file spans 1901-2024 and identify_cdpes iterates all times.
    spei = spei.sel(time=slice(s1.STUDY_START, s1.STUDY_END))
    events = s1.identify_cdpes(spei)  # defaults: theta=1.5, r=4.0, f=0.5, q=0.10
    companion_all = sorted(ym(t) for t in events)
    print(f"Regenerated companion catalogue 1980-2024: {len(companion_all)} months")
    assert len(companion_all) == EXPECTED_PUBLISHED_N, (
        f"regeneration returned {len(companion_all)}, not the published "
        f"{EXPECTED_PUBLISHED_N}; subset test not valid on this basis"
    )

    companion_2024 = [m for m in companion_all if m >= "2024-01"]
    companion_trim = [m for m in companion_all if m <= "2023-12"]

    series = pd.read_csv(ARM_A_SERIES)
    # Arm A series timestamps are mid-month (e.g. 1980-05-16); normalise both
    # sides to calendar months before comparing.
    arm_a = sorted(
        pd.to_datetime(
            series.loc[series["SPEI-1|thr=1.5|r=4.0"] == 1, "date"]
        ).dt.strftime("%Y-%m")
    )
    print(f"Arm A baseline SPEI-1 (v2.10, 1980-2023): {len(arm_a)} months")

    inter = sorted(set(arm_a) & set(companion_trim))
    only_arm_a = sorted(set(arm_a) - set(companion_trim))
    only_companion = sorted(set(companion_trim) - set(arm_a))
    gap_headline = EXPECTED_PUBLISHED_N - len(arm_a)  # 6

    rows = [
        ("companion_published_months_1980_2024", len(companion_all)),
        ("companion_months_in_2024", len(companion_2024)),
        ("companion_months_trimmed_to_2023", len(companion_trim)),
        ("armA_baseline_months_1980_2023", len(arm_a)),
        ("intersection_months", len(inter)),
        ("armA_subset_of_companion_trimmed", set(arm_a) <= set(companion_trim)),
        ("months_only_in_armA", ";".join(only_arm_a)),
        ("months_only_in_companion_trimmed", ";".join(only_companion)),
        ("months_companion_2024", ";".join(companion_2024)),
        ("headline_gap_spei1", gap_headline),
        ("gap_explained_by_window_alone", len(companion_2024)),
        ("share_of_gap_explained_by_window", len(companion_2024) / gap_headline),
    ]
    pd.DataFrame(rows, columns=["quantity", "value"]).to_csv(OUT_CSV, index=False)
    for k, v in rows:
        print(f"{k}: {v}")
    print(f"Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
