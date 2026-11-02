#!/usr/bin/env python3
"""Segmented parallel downloader with per-segment range resume
(same pattern as the hazards pipeline's frozen fetchers): carve any
legacy single-stream partial into segments, loop each segment with
range resume until byte-exact, assemble, verify total size and the
HDF5 magic bytes."""
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SEGMENTS = 6


def seg_bounds(total, i):
    chunk = (total + SEGMENTS - 1) // SEGMENTS
    return i * chunk, min(total, (i + 1) * chunk) - 1


def fetch(url: str, dest: Path) -> int:
    out = subprocess.run(["curl", "-sSI", "-L", "--connect-timeout", "30",
                          url], capture_output=True, text=True, timeout=120)
    total = None
    for line in out.stdout.splitlines():
        if line.lower().startswith("content-length:"):
            total = int(line.split(":")[1].strip())
    assert total, f"no content-length for {url}"
    if dest.exists() and dest.stat().st_size == total:
        print(f"{dest.name}: already complete ({total})", flush=True)
        return total
    segdir = dest.parent / ".segs" / dest.name
    segdir.mkdir(parents=True, exist_ok=True)
    legacy = dest
    if legacy.exists() and not any(segdir.iterdir()):
        data = legacy.read_bytes()
        for j in range(SEGMENTS):
            s, e = seg_bounds(total, j)
            if data[s:e + 1]:
                (segdir / f"seg{j}").write_bytes(data[s:e + 1])
        legacy.unlink()

    def fetch_seg(i):
        start, end = seg_bounds(total, i)
        want = end - start + 1
        seg = segdir / f"seg{i}"
        for _ in range(200):
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
        raise RuntimeError(f"segment incomplete: {dest.name} seg{i}")

    with ThreadPoolExecutor(max_workers=SEGMENTS) as ex:
        list(ex.map(fetch_seg, range(SEGMENTS)))
    tmp = dest.with_suffix(dest.suffix + ".assembled")
    with open(tmp, "wb") as fh:
        for j in range(SEGMENTS):
            fh.write((segdir / f"seg{j}").read_bytes())
    assert tmp.stat().st_size == total, (tmp.stat().st_size, total)
    magic = tmp.open("rb").read(4)
    assert magic == b"\x89HDF", f"bad magic: {magic!r}"
    tmp.rename(dest)
    for j in range(SEGMENTS):
        (segdir / f"seg{j}").unlink()
    segdir.rmdir()
    print(f"{dest.name}: complete ({total} bytes)", flush=True)
    return total


if __name__ == "__main__":
    base = "https://www.ncei.noaa.gov/pub/data/nidis/indices/nclimgrid-monthly"
    here = Path(__file__).parent
    import sys
    pairs = [tuple(a.split("-")) for a in sys.argv[1:]] or [("gamma", "01"), ("pearson", "01")]
    for variant, ts in pairs:
        fetch(f"{base}/spei-{variant}/nclimgrid-spei-{variant}-{ts}.nc",
              here / f"nclimgrid-spei-{variant}-{ts}.nc")
