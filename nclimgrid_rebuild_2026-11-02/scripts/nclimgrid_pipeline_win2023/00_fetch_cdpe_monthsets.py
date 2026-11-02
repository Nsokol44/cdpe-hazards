#!/usr/bin/env python3
"""Step 00 - Stage the frozen CDPE month sets (inputs to the hazards arm).

Copies the Arm A monthly indicator table from the completed sensitivity study
into data/raw/cdpe_monthsets/ (never re-derived here; the sensitivity study is
the version of record) and downloads the Census county gazetteer used only as
a fallback geolocation for Storm Events records that lack coordinates.

Idempotent: existing archived files are never re-fetched or overwritten.
"""
import hashlib
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SRC = Path.home() / "workspace" / "papers-finish" / "cdpe_sensitivity" / \
    "results" / "run_armA_2026-10-05" / "cdpe_monthly_series.csv"
GAZ_URLS = [
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_counties_national.zip",
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_counties_national.zip",
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    dest_dir = RAW / "cdpe_monthsets"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "cdpe_monthly_series_armA.csv"
    if not dest.exists():
        shutil.copy2(SRC, dest)
        print(f"copied {SRC} -> {dest}")
    print(f"monthsets sha256={sha256(dest)} size={dest.stat().st_size}")

    ref_dir = RAW / "reference"
    ref_dir.mkdir(parents=True, exist_ok=True)
    gaz = ref_dir / "gaz_counties_national.zip"
    if not gaz.exists():
        for url in GAZ_URLS:
            try:
                print(f"fetching {url}")
                urllib.request.urlretrieve(url, gaz)
                break
            except Exception as exc:  # noqa: BLE001
                print(f"  failed: {exc}")
                if gaz.exists():
                    gaz.unlink()
        else:
            print("ERROR: gazetteer download failed from all URLs", file=sys.stderr)
            return 1
    print(f"gazetteer size={gaz.stat().st_size} sha256={sha256(gaz)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
