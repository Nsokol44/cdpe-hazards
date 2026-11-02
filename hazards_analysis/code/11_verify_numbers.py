#!/usr/bin/env python3
"""Step 11 - Number trace for gate G3.

Extracts every numeric literal from the hazards-arm sections of the filled
manuscript (abstract results sentence region excluded: the whole abstract,
Sections 3.2-3.4, 4, 5) and checks each against the allowed value corpus:
rate_ratios_summary.json, the build logs, the monthly series aggregates,
and the fact sheet, at the printed precisions. Sensitivity-arm numbers are
checked against the base manuscript, whose results are the version of
record for that arm. Prints a trace report; unmatched numbers must be
explained in the compliance note.
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"


def numbers_in(text: str) -> list[str]:
    raw = re.findall(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+", text)
    return [n.replace(",", "") for n in raw]


def round_variants(v: float) -> set[str]:
    out = set()
    for nd in (0, 1, 2, 3):
        out.add(f"{v:.{nd}f}")
    out.add(str(int(round(v))))
    if 0 < v < 1:  # percent forms as printed in prose (0.87 -> "87")
        for nd in (0, 1):
            out.add(f"{v * 100:.{nd}f}")
        out.add(str(int(round(v * 100))))
    return out


def main() -> int:
    allowed = set()
    summary = json.loads((RES / "rate_ratios_summary.json").read_text())

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, (int, float)):
            allowed.update(round_variants(float(o)))

    walk(summary)
    for name in ("storm_build_log.json", "heatwave_build_log.json"):
        walk(json.loads((RES / name).read_text()))
    storm = pd.read_csv(RES / "hazard_series_storm.csv")
    hw = pd.read_csv(RES / "hazard_series_heatwave.csv")
    monthly = pd.read_csv(RES / "monthly_series_all.csv")
    for col in storm.columns[1:]:
        allowed.update(round_variants(float(storm[col].sum())))
        allowed.update(round_variants(float(storm[col].mean())))
    allowed.update(round_variants(float(hw["heatwave_days_per_cell"].mean())))
    # Rebuild 2026-11-02: the GLM (lightning) arm was dropped from the
    # paper; monthly_series_all.csv no longer carries a glm_flash_box
    # column, so the sampled-flash aggregate leaves the allowed corpus.
    # The same rebuild's Figure 2 caption reports the pole-map build
    # (SPEIBASE_REBUILD_REPORT.md, run_armA_speibase_rebuild_2026-11-02):
    # dry poles occupy 43 cells, wet poles 42, at most 3 months per cell.
    for v in (43.0, 42.0, 3.0):
        allowed.update(round_variants(v))
    base = (ROOT.parent / "cdpe_sensitivity" / "manuscript"
            / "manuscript.md").read_text(encoding="utf-8")
    allowed.update(numbers_in(base))
    # structural constants of the design
    allowed.update({str(n) for n in
                    (3, 4, 5, 6, 10, 12, 24, 36, 44, 46, 52, 90, 95, 99, 100,
                     528, 720, 756, 2000, 2018, 2023, 1980, 1995, 1996, 2010,
                     2014, 50, 25, 66, 125, 2, 1, 0)})

    ms = (ROOT / "manuscript" / "manuscript_aas.md").read_text(encoding="utf-8")
    sections = []
    capture = False
    for line in ms.splitlines():
        if line.startswith("## Abstract") or re.match(r"# [345]\.", line):
            capture = True
        elif line.startswith("# ") and not re.match(r"# [345]\.", line):
            capture = False
        if capture:
            sections.append(line)
    text = "\n".join(sections)
    text = re.sub(r"\[@[^\]]+\]", "", text)
    found = numbers_in(text)
    unmatched = sorted({n for n in found if n not in allowed},
                       key=lambda x: float(x))
    print(f"numeric literals checked: {len(found)}; "
          f"unique unmatched: {len(unmatched)}")
    for n in unmatched:
        print("UNMATCHED:", n)
    (RES / "number_trace.txt").write_text(
        "checked=%d unmatched=%s\n" % (len(found), unmatched))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
