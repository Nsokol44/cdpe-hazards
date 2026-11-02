#!/usr/bin/env python3
"""Step 12 - Data manifest: every raw file archived for this paper.

Writes data/DATA_MANIFEST.md (dataset-level summary with per-file name,
size, SHA-256, source URL, access date) and data/raw/glm_manifest.csv
(one row per GLM file; 50k+ rows do not belong in a Markdown table).
Access date for all downloads in this build: 2026-10-26.
"""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DATE = "2026-10-26"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    lines = ["# DATA MANIFEST - CDPE hazards paper (AAS)", "",
             f"Access date for all downloads: {DATE}.", ""]
    # Storm Events
    slog = json.loads((RAW / "storm_events" / "fetch_log.json").read_text())
    lines += ["## NOAA/NCEI Storm Events (yearly details files)", "",
              "| file | bytes | sha256 | source URL |",
              "|---|---|---|---|"]
    for name, rec in sorted(slog.items()):
        p = RAW / "storm_events" / name
        if p.exists():
            lines.append(f"| {name} | {p.stat().st_size} | {sha256(p)} | "
                         f"{rec['url']} |")
    # gridMET
    glog = json.loads((RAW / "gridmet" / "fetch_log.json").read_text())
    lines += ["", "## gridMET daily maximum temperature (yearly files)", "",
              "| file | bytes | sha256 | source URL |",
              "|---|---|---|---|"]
    for name, rec in sorted(glog.items()):
        p = RAW / "gridmet" / name
        if p.exists():
            lines.append(f"| {name} | {p.stat().st_size} | {sha256(p)} | "
                         f"{rec['url']} |")
    # staged inputs and reference
    lines += ["", "## Staged inputs and reference data", ""]
    ms = RAW / "cdpe_monthsets" / "cdpe_monthly_series_armA.csv"
    lines.append(f"- cdpe_monthly_series_armA.csv: copied unchanged from the "
                 f"sensitivity study (results/run_armA_2026-10-05/"
                 f"cdpe_monthly_series.csv of Sokol, unpublished CDPE "
                 f"sensitivity study). bytes={ms.stat().st_size} "
                 f"sha256={sha256(ms)}")
    gaz = RAW / "reference" / "gaz_counties_national.zip"
    lines.append(f"- gaz_counties_national.zip: US Census Bureau county "
                 f"gazetteer (2023), bytes={gaz.stat().st_size} "
                 f"sha256={sha256(gaz)}, source "
                 f"https://www2.census.gov/geo/docs/maps-data/data/"
                 f"gazetteer/2023_Gazetteer/2023_Gaz_counties_national.zip")
    # GLM per-file CSV manifest
    rows = []
    total_bytes = 0
    for jf in sorted((ROOT / "results" / "glm_fetch").glob("*.json")):
        d = json.loads(jf.read_text())
        for r in d["records"]:
            if "key" not in r or "path" not in r:
                continue
            p = ROOT / r["path"]
            if p.exists():
                rows.append({"file": str(p.relative_to(RAW)),
                             "bytes": p.stat().st_size,
                             "sha256": sha256(p),
                             "url": "https://noaa-goes16.s3.amazonaws.com/"
                                    + r["key"],
                             "n_flash_box": r.get("n_flash_box")})
                total_bytes += p.stat().st_size
    with open(RAW / "glm_manifest.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "bytes", "sha256", "url",
                                           "n_flash_box"])
        w.writeheader()
        w.writerows(rows)
    lines += ["", "## GOES-16 GLM LCFA (systematic hourly sample)", "",
              f"{len(rows)} files, {total_bytes} bytes total. Per-file name, "
              f"size, SHA-256, and source URL: data/raw/glm_manifest.csv. "
              f"Sampling rule: first 20-second file of every hour, January "
              f"2018 to December 2023 (DESIGN LOCK Section 4.4 and "
              f"Amendment 1)."]
    (ROOT / "data" / "DATA_MANIFEST.md").write_text("\n".join(lines) + "\n")
    print(f"manifest written; GLM rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
