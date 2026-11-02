#!/usr/bin/env python3
"""Step 01 - Download NOAA/NCEI Storm Events yearly details files, 1980-2023.

Source directory: https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/
File names carry a creation-date suffix (cYYYYMMDD) that changes when NCEI
republishes; the directory listing is parsed once and, for each year, the file
with the latest creation suffix is chosen. The resolved URL for every file is
recorded in fetch_log.json next to this script's outputs and in the data
manifest. Idempotent: files already archived are never re-fetched.
"""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path


SEGMENTS = 4


def _seg_bounds(total: int, i: int) -> tuple[int, int]:
    chunk = (total + SEGMENTS - 1) // SEGMENTS
    return i * chunk, min(total, (i + 1) * chunk) - 1


def robust_download(url: str, dest: Path) -> int:
    """Segmented parallel download with per-segment range resume.

    The NCEI server closes connections after roughly 10-17 s, so transfer
    volume per connection is capped; four parallel byte-range segments,
    each looping with range resume until byte-exact, are several times
    faster than a single stream (measured 2026-10-26). A legacy
    single-stream .part file is carved into segments and reused. The
    assembled file is verified with gzip -t before entering the archive.
    """
    import subprocess
    from concurrent.futures import ThreadPoolExecutor
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as resp:
        expected = int(resp.headers["Content-Length"])
    segdir = dest.parent / ".segs" / dest.name
    segdir.mkdir(parents=True, exist_ok=True)
    legacy = dest.with_suffix(dest.suffix + ".part")
    if legacy.exists() and not any(segdir.iterdir()):
        data = legacy.read_bytes()
        for j in range(SEGMENTS):
            s2, e2 = _seg_bounds(expected, j)
            if data[s2:e2 + 1]:
                (segdir / f"seg{j}").write_bytes(data[s2:e2 + 1])
        legacy.unlink()

    def fetch_seg(i: int) -> None:
        start, end = _seg_bounds(expected, i)
        want = end - start + 1
        seg = segdir / f"seg{i}"
        for _ in range(80):
            have = seg.stat().st_size if seg.exists() else 0
            if have == want:
                return
            if have > want:
                seg.unlink()
                have = 0
            with open(seg, "ab") as fh:
                subprocess.run(["curl", "-sS", "-L", "--connect-timeout",
                                "30", "-r", f"{start + have}-{end}", url],
                               stdout=fh, check=False, timeout=900)
            time.sleep(1)
        raise RuntimeError(f"segment incomplete: {url} seg{i}")

    with ThreadPoolExecutor(max_workers=SEGMENTS) as ex:
        list(ex.map(fetch_seg, range(SEGMENTS)))
    tmp = dest.with_suffix(dest.suffix + ".assembled")
    with open(tmp, "wb") as out:
        for j in range(SEGMENTS):
            out.write((segdir / f"seg{j}").read_bytes())
    assert tmp.stat().st_size == expected
    chk = subprocess.run(["gzip", "-t", str(tmp)])
    if chk.returncode != 0:
        tmp.unlink()
        raise RuntimeError(f"gzip integrity check failed: {url}")
    tmp.rename(dest)
    for j in range(SEGMENTS):
        (segdir / f"seg{j}").unlink()
    segdir.rmdir()
    return expected

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "storm_events"
BASE = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
YEARS = range(1980, 2027)  # EXTENDED run: +2024-2026 (latest vintage per year, as the frozen step resolves)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(BASE, timeout=120) as resp:
        listing = resp.read().decode("utf-8", "replace")
    found = {}
    for year, cdate in re.findall(
            r"StormEvents_details-ftp_v1\.0_d(\d{4})_c(\d+)\.csv\.gz", listing):
        y = int(year)
        if y in YEARS and (y not in found or cdate > found[y]):
            found[y] = cdate
    missing = [y for y in YEARS if y not in found]
    if missing:
        print(f"ERROR: no details file listed for years {missing}", file=sys.stderr)
        return 1
    log = {}
    for y in YEARS:
        name = f"StormEvents_details-ftp_v1.0_d{y}_c{found[y]}.csv.gz"
        dest = OUT / name
        url = BASE + name
        if dest.exists() and dest.stat().st_size > 0:
            status = "already archived"
        else:
            print(f"fetching {name}", flush=True)
            try:
                robust_download(url, dest)
                status = "downloaded"
            except RuntimeError:
                # NCEI throttles hard; record and continue with other years.
                # A later rerun retries only the missing years.
                status = "FAILED (rerun to retry)"
                log[name] = {"url": url, "bytes": 0, "status": status}
                print(f"  {name}: FAILED", flush=True)
                continue
        log[name] = {"url": url, "bytes": dest.stat().st_size, "status": status}
        print(f"  {name}: {log[name]['bytes']} bytes ({status})")
        time.sleep(2)  # brief pacing between files
    (OUT / "fetch_log.json").write_text(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
