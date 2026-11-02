#!/usr/bin/env python3
"""Step 03 - GOES-16 GLM LCFA systematic time sample, Jan 2018 - Dec 2023.

DESIGN LOCK Section 4.4: full-cadence LCFA (180 files/hour) is infeasible for
72 months, so the lightning metric uses a fixed systematic sample: the first
20-second file of every hour (start time HH:00:00), 24 files/day, identical
for every month and both comparison groups, so rate ratios are invariant to
the sampling fraction. Flash counts (total, and inside the CONUS domain box
25-50 N, 125-66 W, from flash_lat/flash_lon) are recorded per file after
download; raw netCDF files are archived under data/raw/glm/ for audit.

Implementation notes (v3): each (day, hour) task lists S3 with the FULL
start-time token as prefix, so listings return one or two keys (small
responses; an earlier day-paginated design failed through this network's
proxy). Downloads use per-thread requests.Session keep-alive connections.
Flash counting is serial in the main thread (netCDF4/HDF5 is not
thread-safe). Checkpointing: results/glm_fetch/<YYYY-MM>.json; files already
on disk are never re-fetched. Months below the 90% completeness rule are
retried in up to two repair passes. A month is VALID at >= 90% retrieved.

Source: AWS Open Data bucket noaa-goes16 (anonymous S3 listing + GET).
"""
import calendar
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import netCDF4 as nc
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "glm"
STATUS = ROOT / "results" / "glm_fetch"
BUCKET = "https://noaa-goes16.s3.amazonaws.com"
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = 25.0, 50.0, -125.0, -66.0
WORKERS = 12
MONTHS = [(y, m) for y in range(2018, 2024) for m in range(1, 13)]
_local = threading.local()


def session() -> requests.Session:
    if not hasattr(_local, "s"):
        _local.s = requests.Session()
    return _local.s


def list_token(year: int, doy: int, hour: int, token: str) -> list[str]:
    prefix = (f"GLM-L2-LCFA/{year}/{doy:03d}/{hour:02d}/"
              f"OR_GLM-L2-LCFA_G16_s{token}")
    url = f"{BUCKET}/?list-type=2&prefix={prefix}&max-keys=10"
    xml = session().get(url, timeout=60).text
    return re.findall(r"<Key>([^<]+)</Key>", xml)


def fetch_one(task: tuple[date, int]) -> dict:
    day, hour = task
    year, doy = day.year, day.timetuple().tm_yday
    token = f"{year}{doy:03d}{hour:02d}0000"
    rec = {"day": day.isoformat(), "hour": hour, "token": token}
    last_err = None
    for attempt in range(4):
        try:
            keys = list_token(year, doy, hour, token)
            cand = sorted(k for k in keys if f"s{token}" in k)
            if not cand:
                rec["status"] = "missing_in_listing"
                return rec
            key = cand[-1]
            rec["key"] = key
            dest = RAW / f"{day.year}" / f"{day.month:02d}" / Path(key).name
            rec["path"] = str(dest.relative_to(ROOT))
            if dest.exists() and dest.stat().st_size > 0:
                rec["status"] = "already archived"
            else:
                resp = session().get(f"{BUCKET}/{key}", timeout=120)
                resp.raise_for_status()
                dest.parent.mkdir(parents=True, exist_ok=True)
                tmp = dest.with_suffix(".part")
                tmp.write_bytes(resp.content)
                tmp.rename(dest)
                rec["status"] = "downloaded"
            rec["bytes"] = dest.stat().st_size
            return rec
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
            time.sleep(2 * (attempt + 1))
    rec["status"] = "failed"
    rec["error"] = last_err
    return rec


def process_month(y: int, m: int) -> bool:
    tag = f"{y}-{m:02d}"
    status_path = STATUS / f"{tag}.json"
    ndays = calendar.monthrange(y, m)[1]
    # DESIGN_LOCK Amendment 2 (2026-10-26): thinned frame, days 1 mod 3
    tasks = [(date(y, m, d), h) for d in range(1, ndays + 1)
             if (d - 1) % 3 == 0 for h in range(24)]
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        records = list(ex.map(fetch_one, tasks))
    records.sort(key=lambda r: (r["day"], r["hour"]))
    for rec in records:  # serial counting: netCDF4 is not thread-safe
        if "path" not in rec:
            continue
        try:
            ds = nc.Dataset(ROOT / rec["path"])
            lat = ds.variables["flash_lat"][:]
            lon = ds.variables["flash_lon"][:]
            ds.close()
        except Exception as exc:  # noqa: BLE001 - file vanished or corrupt:
            rec["status"] = f"count_failed: {exc}"  # month falls below the
            continue                                # gate and is repaired later
        rec["n_flash_total"] = int(len(lat))
        rec["n_flash_box"] = int(
            ((lat >= LAT_MIN) & (lat <= LAT_MAX)
             & (lon >= LON_MIN) & (lon <= LON_MAX)).sum())
    got = [r for r in records if r.get("n_flash_box") is not None]
    frac = len(got) / len(tasks)
    out = {"month": tag, "expected_files": len(tasks),
           "retrieved_files": len(got), "fraction": frac,
           "valid": frac >= 0.90, "records": records}
    status_path.write_text(json.dumps(out))
    print(f"{tag}: {len(got)}/{len(tasks)} files ({frac:.3f}) "
          f"valid={out['valid']}", flush=True)
    return out["valid"]


def month_valid(y: int, m: int) -> bool:
    p = STATUS / f"{y}-{m:02d}.json"
    return p.exists() and json.loads(p.read_text()).get("valid", False)


def main() -> int:
    import fcntl
    lock = open(ROOT / "results" / ".glm_fetch.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another GLM fetch instance is running; exiting")
        return 0
    STATUS.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    todo = [(y, m) for (y, m) in MONTHS
            if (not only or f"{y}-{m:02d}" == only) and not month_valid(y, m)]
    for (y, m) in todo:
        process_month(y, m)
    for repair in range(2):  # repair passes for months still below 90%
        bad = [(y, m) for (y, m) in MONTHS
               if (not only or f"{y}-{m:02d}" == only)
               and not month_valid(y, m)]
        if not bad:
            break
        print(f"repair pass {repair + 1}: {len(bad)} months", flush=True)
        for (y, m) in bad:
            process_month(y, m)
    bad = [(y, m) for (y, m) in MONTHS if not month_valid(y, m)]
    print(f"months valid: {len(MONTHS) - len(bad)}/{len(MONTHS)}; "
          f"invalid: {[f'{y}-{m:02d}' for (y, m) in bad]}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
