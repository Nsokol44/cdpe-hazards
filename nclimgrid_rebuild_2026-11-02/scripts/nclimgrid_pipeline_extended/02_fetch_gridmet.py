#!/usr/bin/env python3
"""Step 02 - Download gridMET daily maximum temperature yearly files, 1980-2023.

Source: University of Idaho gridMET via https://www.northwestknowledge.net/
metdata/data/tmmx_<year>.nc (about 140-147 MB per year, 6.5 GB total).
The server drops long transfers, so each file is fetched as 6 byte-range
segments downloaded concurrently (12 workers across years/segments); each
segment loops with range-resume until its byte count is exact, then the
segments are concatenated and the total verified against Content-Length.
A legacy single-stream .part file, if present, is carved into segments and
reused. Files already archived are never re-fetched.
"""
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "gridmet"
BASE = "https://www.northwestknowledge.net/metdata/data/"
YEARS = range(1980, 2027)  # EXTENDED run: +2024-2026
SEGMENTS = 6
WORKERS = 12


def content_length(url: str) -> int:
    for attempt in range(8):
        try:
            out = subprocess.run(
                ["curl", "-sSI", "-L", "--connect-timeout", "30", url],
                capture_output=True, text=True, timeout=120).stdout
            for line in out.splitlines():
                if line.lower().startswith("content-length:"):
                    return int(line.split(":")[1].strip())
            raise IOError("no Content-Length header")
        except Exception as exc:  # noqa: BLE001
            print(f"  HEAD attempt {attempt + 1} failed: {exc}", flush=True)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"HEAD failed: {url}")


def seg_bounds(total: int, i: int) -> tuple[int, int]:
    chunk = (total + SEGMENTS - 1) // SEGMENTS
    return i * chunk, min(total, (i + 1) * chunk) - 1  # inclusive end


def fetch_segment(args) -> tuple[int, int]:
    year, i, url, total = args
    start, end = seg_bounds(total, i)
    want = end - start + 1
    seg = OUT / ".segments" / f"{year}" / f"seg{i}"
    seg.parent.mkdir(parents=True, exist_ok=True)
    legacy = OUT / f"tmmx_{year}.nc.part"
    if i == 0 and legacy.exists() and not seg.exists():
        # carve the legacy single-stream partial into segment files once
        data = legacy.read_bytes()
        for j in range(SEGMENTS):
            s2, e2 = seg_bounds(total, j)
            piece = data[s2:e2 + 1]
            if piece:
                (seg.parent / f"seg{j}").write_bytes(piece)
        legacy.unlink()
    tmp = seg.with_suffix(".resp")
    for _ in range(400):
        have = seg.stat().st_size if seg.exists() else 0
        if have == want:
            return year, i
        if have > want:
            seg.unlink()
            have = 0
        out = subprocess.run(
            ["curl", "-sS", "-L", "--connect-timeout", "30",
             "-r", f"{start + have}-{end}", "-o", str(tmp),
             "-w", "%{http_code}", url],
            capture_output=True, text=True, check=False, timeout=900)
        code = out.stdout.strip()[-3:]
        body = tmp.read_bytes() if tmp.exists() else b""
        piece = b""
        if code == "206":
            piece = body[:want - have]
        elif code == "200":
            # server ignored the range: body is the whole file, so slice
            # out exactly the bytes this segment still needs
            piece = body[start + have:end + 1]
        if piece:
            with open(seg, "ab") as fh:
                fh.write(piece)
        if tmp.exists():
            tmp.unlink()
        time.sleep(1)
    raise RuntimeError(f"segment incomplete: year {year} seg {i}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    log = {}
    tasks = []
    totals = {}
    for y in YEARS:
        name = f"tmmx_{y}.nc"
        dest = OUT / name
        if dest.exists() and dest.stat().st_size > 1_000_000:
            log[name] = {"url": BASE + name, "bytes": dest.stat().st_size,
                         "status": "already archived"}
            continue
        totals[y] = content_length(BASE + name)
        tasks.extend((y, i, BASE + name, totals[y]) for i in range(SEGMENTS))
    print(f"{len(tasks)} segments to fetch", flush=True)
    if tasks:
        # tolerate individual segment failures: retry them in later passes
        pending = list(tasks)
        for p in range(6):
            if not pending:
                break
            failed = []
            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                futs = {ex.submit(fetch_segment, t): t for t in pending}
                for fut in futs:
                    try:
                        fut.result()
                    except Exception as exc:  # noqa: BLE001
                        print(f"  pass {p + 1}: {exc}", flush=True)
                        failed.append(futs[fut])
            pending = failed
        if pending:
            raise RuntimeError(f"{len(pending)} segments still incomplete")
    for y, total in totals.items():
        name = f"tmmx_{y}.nc"
        dest = OUT / name
        segdir = OUT / ".segments" / f"{y}"
        tmp = OUT / f"{name}.assembled"
        with open(tmp, "wb") as out:
            for i in range(SEGMENTS):
                out.write((segdir / f"seg{i}").read_bytes())
        assert tmp.stat().st_size == total, \
            f"{name}: assembled {tmp.stat().st_size} != {total}"
        tmp.rename(dest)
        for i in range(SEGMENTS):
            (segdir / f"seg{i}").unlink()
        segdir.rmdir()
        log[name] = {"url": BASE + name, "bytes": total, "status": "downloaded"}
        print(f"  {name}: {total} bytes (downloaded)", flush=True)
    (OUT / "fetch_log.json").write_text(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
