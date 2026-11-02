#!/usr/bin/env bash
# Phase 3 one-command rerun (2026-11-02). Deps: numpy, pandas, scipy,
# statsmodels (pip install statsmodels). Deterministic: seeds are fixed
# inside each script (20261026 frozen ratio bootstrap; 20261102 GLM /
# median / pole-relative bootstraps). Runtime ~25 min (GLM year-block
# bootstraps and the StormEvents cell rebuild dominate).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 code/32_prepare_inputs.py
python3 code/33_ratio_arms.py
python3 code/34_glm_models.py
python3 code/35_pole_relative.py
python3 code/36_misc_stats.py
python3 code/37_build_phase3_report.py
echo "Phase 3 rerun complete: results/phase3_2026-11-02/PHASE3_RESULTS.md"
