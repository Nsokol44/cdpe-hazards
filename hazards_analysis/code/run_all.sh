#!/usr/bin/env bash
# One-command rerun of the CDPE hazards paper pipeline.
# Acquisition steps skip files already in the raw archive (never fetch twice).
set -euo pipefail
cd "$(dirname "$0")"
python3 00_fetch_cdpe_monthsets.py
python3 01_fetch_storm_events.py
python3 02_fetch_gridmet.py
python3 03_fetch_glm.py
python3 04_build_storm_series.py
python3 05_build_heatwave_series.py
python3 06_rate_ratios.py
python3 07_figures.py
python3 07b_regen_fig_s2.py
python3 10_fact_sheet.py
python3 08_citation_closure.py
python3 11_verify_numbers.py
python3 12_build_manifest.py
python3 09_build_docx.py
python3 09b_build_cover_letter.py
echo "pipeline complete"
