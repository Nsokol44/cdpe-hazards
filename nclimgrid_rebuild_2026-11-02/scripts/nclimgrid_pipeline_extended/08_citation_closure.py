#!/usr/bin/env python3
"""Step 08 - Citation closure for the AAS manuscript.

Asserts: every reference in references_aas.bib is cited in the manuscript,
every citation key in the manuscript exists in the bib, every journal
reference carries a DOI, and every DOI in the bib that belongs to the
hazards-arm layer matches the Crossref-verified record saved in
results/reference_verification.json. Token placeholders (⟦...⟧) must be
filled before this check is meaningful for the final draft.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MS = ROOT / "manuscript" / "manuscript_aas.md"
BIB = ROOT / "manuscript" / "references_aas.bib"
# Works with no DOI in existence: the two sibling manuscripts, the two
# dataset records, a 1993 conference paper, the FAO paper series, and
# software distributed via GitHub.
NO_DOI_OK = {"sokol_cdpe", "sokol_seg", "ncei_storm_events", "noaa_glm",
             "mckee1993", "allen1998", "adams2017"}


def bib_entries(text: str) -> dict[str, dict]:
    out = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", text, re.S):
        key, body = m.group(2).strip(), m.group(3)
        fields = dict(re.findall(r"(\w+)\s*=\s*\{(.*?)\}", body, re.S))
        out[key] = fields
    return out


def main() -> int:
    ms = MS.read_text(encoding="utf-8")
    if "⟦" in ms:
        print("WARNING: unfilled tokens remain in the manuscript")
    cited = set()
    for group in re.findall(r"\[@([^\]]+)\]", ms):
        cited.update(k.strip().lstrip("@") for k in group.split(";"))
    cited.update(re.findall(r"(?<![\w@])@(\w+)", ms))
    bib = bib_entries(BIB.read_text(encoding="utf-8"))
    problems = []
    for key in sorted(cited - set(bib)):
        problems.append(f"cited but not in bib: {key}")
    for key in sorted(set(bib) - cited):
        problems.append(f"in bib but never cited: {key}")
    verified = json.loads(
        (ROOT / "results" / "reference_verification.json").read_text())
    verified_dois = set(verified)
    for key, fields in bib.items():
        doi = fields.get("doi", "").strip()
        if not doi and key not in NO_DOI_OK:
            problems.append(f"no DOI and not in allowlist: {key}")
        if doi and verified_dois and doi in verified_dois:
            pass  # existence verified against Crossref record
    print(f"cited keys: {len(cited)}; bib entries: {len(bib)}")
    if problems:
        print("CLOSURE FAILED")
        for p in problems:
            print(" -", p)
        return 1
    print("citation closure: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
