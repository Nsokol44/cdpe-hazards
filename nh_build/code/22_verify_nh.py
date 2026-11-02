#!/usr/bin/env python3
"""Step 22 - Verification suite for the Natural Hazards package.

1. Citation closure (step 08 logic) on manuscript_nh.md / references_nh.bib,
   plus: 37 reference entries rendered in manuscript_nh.docx and the DOI
   set in the rendered list equals the DOI set in the bib.
2. Number trace (step 11 logic) on manuscript_nh.md against the results
   corpus of the parent package: expects 0 unmatched literals.
3. Numeric-token identity: full numeric-token multiset of the NH source
   .md equals that of the AAS source .md (citations and YAML stripped),
   and the rendered-text numeric multiset of manuscript_nh.docx equals
   that of the delivered AAS manuscript (manuscript_aas_formatted.docx).
4. Word counts (abstract, keywords, main text, totals).
5. Em dash and prose-semicolon scans on both final DOCXs.
6. DOCX hygiene: no 'python-docx' string, no themeColor attributes,
   every w:color is 000000, creator metadata, blank dc:description,
   line numbering present, 7 embedded figures MD5-matched to figures/.

Rebuild 2026-11-02: expectations updated for the lightning-arm removal
and the pole-map insertion (Figure 2), as itemised at each check.
"""
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

from docx import Document

PKG = Path(__file__).resolve().parents[1]
# The NH package was a subfolder of the AAS package when this suite was
# written (SRC_PKG = PKG.parent). Since the 2026-11-01 move it is a
# sibling folder, so the source package is named explicitly.
SRC_PKG = PKG.parent / "cdpe-hazards-aas"
NO_DOI_OK = {"sokol_cdpe", "sokol_seg", "ncei_storm_events", "noaa_glm",
             "mckee1993", "allen1998", "adams2017"}
failures = []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL"), name, detail)
    if not ok:
        failures.append(name)


def numbers_in(text):
    raw = re.findall(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+", text)
    return [n.replace(",", "") for n in raw]


def docx_text(path):
    d = Document(path)
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            for cell in row.cells:
                parts.extend(p.text for p in cell.paragraphs)
    return "\n".join(parts), d


# ---- 1. citation closure -------------------------------------------------
ms = (PKG / "manuscript_nh.md").read_text(encoding="utf-8")
bib_text = (PKG / "references_nh.bib").read_text(encoding="utf-8")
bib = {}
for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", bib_text, re.S):
    body = m.group(3)
    fields = dict(re.findall(r"(\w+)\s*=\s*\{(.*?)\}", body, re.S))
    bib[m.group(2).strip()] = fields
cited = set()
for group in re.findall(r"\[@([^\]]+)\]", ms):
    cited.update(k.strip().lstrip("@") for k in group.split(";"))
cited.update(re.findall(r"(?<![\w@])@(\w+)", ms))
check("closure cited==bib", cited == set(bib),
      f"cited {len(cited)}, bib {len(bib)}, "
      f"missing {sorted(cited - set(bib))}, uncited {sorted(set(bib) - cited)}")
no_doi = [k for k, f in bib.items()
          if not f.get("doi", "").strip() and k not in NO_DOI_OK]
check("closure DOIs present or allowlisted", not no_doi, str(no_doi))

nh_text, nh_doc = docx_text(PKG / "manuscript_nh.docx")
paras = [p.text for p in nh_doc.paragraphs]
ri = paras.index("References")
sdi = paras.index("Statements and Declarations")
ref_paras = [t for t in paras[ri + 1:sdi] if t.strip()]
# Rebuild 2026-11-02: 37 entries (the three GLM-only references left
# with the lightning arm).
check("rendered reference entries == 37", len(ref_paras) == 37,
      f"found {len(ref_paras)}")
bib_dois = {f["doi"].strip() for f in bib.values() if f.get("doi")}
rendered_dois = set(re.findall(r"https://doi\.org/(\S+)", nh_text))
check("rendered DOI set == bib DOI set", rendered_dois == bib_dois,
      f"bib {len(bib_dois)}, rendered {len(rendered_dois)}, "
      f"diff {sorted(bib_dois ^ rendered_dois)}")

# ---- 2. number trace (step 11 logic, NH source) --------------------------
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "step11", SRC_PKG / "code" / "11_verify_numbers.py")
step11 = importlib.util.module_from_spec(spec)
step11.__name__ = "step11"
import types
step11_main = None
src11 = (SRC_PKG / "code" / "11_verify_numbers.py").read_text()
src11 = src11.replace('MS = ROOT / "manuscript" / "manuscript_aas.md"',
                      'MS = ROOT / "manuscript" / "manuscript_aas.md"')
# Reimplement inline against the NH md to avoid touching the source pkg:
allowed = set()
summary = json.loads((SRC_PKG / "results" / "rate_ratios_summary.json")
                     .read_text())


def round_variants(v):
    out = set()
    for nd in (0, 1, 2, 3):
        out.add(f"{v:.{nd}f}")
    out.add(str(int(round(v))))
    if 0 < v < 1:
        for nd in (0, 1):
            out.add(f"{v * 100:.{nd}f}")
        out.add(str(int(round(v * 100))))
    return out


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
    walk(json.loads((SRC_PKG / "results" / name).read_text()))
import pandas as pd
storm = pd.read_csv(SRC_PKG / "results" / "hazard_series_storm.csv")
hw = pd.read_csv(SRC_PKG / "results" / "hazard_series_heatwave.csv")
monthly = pd.read_csv(SRC_PKG / "results" / "monthly_series_all.csv")
for col in storm.columns[1:]:
    allowed.update(round_variants(float(storm[col].sum())))
    allowed.update(round_variants(float(storm[col].mean())))
allowed.update(round_variants(float(hw["heatwave_days_per_cell"].mean())))
# Rebuild 2026-11-02: the GLM (lightning) arm was dropped from the
# paper; monthly_series_all.csv no longer carries a glm_flash_box
# column, so the sampled-flash aggregate leaves the allowed corpus.
# The Figure 2 caption's pole-map counts join instead (dry poles 43
# cells, wet poles 42, at most 3 months per cell;
# SPEIBASE_REBUILD_REPORT.md, run_armA_speibase_rebuild_2026-11-02).
for v in (43.0, 42.0, 3.0):
    allowed.update(round_variants(v))
base = (SRC_PKG.parent / "cdpe_sensitivity" / "manuscript"
        / "manuscript.md").read_text(encoding="utf-8")
allowed.update(numbers_in(base))
allowed.update({str(n) for n in
                (3, 4, 5, 6, 10, 12, 24, 36, 44, 46, 52, 90, 95, 99, 100,
                 528, 720, 756, 2000, 2018, 2023, 1980, 1995, 1996, 2010,
                 2014, 50, 25, 66, 125, 2, 1, 0)})
# Rebuild 2026-11-02: two structural literals join the traced text
# with the figure renumbering and the Section 3.2 figure pointer:
# "7" (Figure 7, the monthly-series figure's new number) and "1.00"
# (the 1.00-inch severe-hail criterion, now inside a traced sentence;
# no corpus value formats to exactly 1.00 in the no-lightning run).
allowed.update({"7", "1.00"})
sections, capture = [], False
for line in ms.splitlines():
    if line.startswith("## Abstract") or re.match(r"# [345]\.", line):
        capture = True
    elif line.startswith("# ") and not re.match(r"# [345]\.", line):
        capture = False
    if capture:
        sections.append(line)
trace_text = re.sub(r"\[@[^\]]+\]", "", "\n".join(sections))
found = numbers_in(trace_text)
unmatched = sorted({n for n in found if n not in allowed},
                   key=lambda x: float(x))
(PKG / "nh_number_trace.txt").write_text(
    "checked=%d unmatched=%s\n" % (len(found), unmatched))
aas_ms = (SRC_PKG / "manuscript" / "manuscript_aas.md").read_text(
    encoding="utf-8")
aas_sections, aas_capture = [], False
for line in aas_ms.splitlines():
    if line.startswith("## Abstract") or re.match(r"# [345]\.", line):
        aas_capture = True
    elif line.startswith("# ") and not re.match(r"# [345]\.", line):
        aas_capture = False
    if aas_capture:
        aas_sections.append(line)
aas_found = numbers_in(re.sub(r"\[@[^\]]+\]", "",
                                "\n".join(aas_sections)))
# Fix round 2026-11-01: Section 3.1 was shortened at the reviewer's
# direction and the comparison detail moved to Supplementary
# Information S1. Five literals leave the traced sections with that
# detail (the Jaccard 1.000 code check, the companion SPI-1 count 66,
# the 22 months at the documented specification, and the catalog
# Jaccard values 0.063 and 0.054; 66 and 22 remain in Table 2), and
# one literal joins with the supplement pointer (the "1" of "S1").
# Every remaining literal must still trace to the results corpus.
# Rebuild 2026-11-02: the lightning literals left both packages'
# traced sections symmetrically, and the pole-map caption and pointer
# joined both, so the removed set is unchanged. The added set is now
# {"1": 1}: the "S1" token stands alone, because the AAS manuscript
# gained its own Section 3.2 "(Figure 1)" pointer in this rebuild
# (balancing NH's), and the 2026-11-01 Figure 6 asymmetry ("6" x2) is
# gone now that both manuscripts run to Figure 7.
_removed = Counter(aas_found) - Counter(found)
_added = Counter(found) - Counter(aas_found)
check("number trace: 0 unmatched; delta is the directed S3.1 move",
      not unmatched
      and _removed == {"1.000": 1, "66": 1, "22": 1, "0.063": 1,
                       "0.054": 1}
      and _added == {"1": 1},
      f"NH checked {len(found)}, AAS checked {len(aas_found)}, "
      f"unmatched {unmatched}, removed {dict(_removed)}, "
      f"added {dict(_added)}")

# ---- 3. numeric-token identity -------------------------------------------
def md_numbers(path):
    t = Path(path).read_text(encoding="utf-8")
    t = re.sub(r"^---\n.*?\n---\n", "", t, flags=re.S)
    t = re.sub(r"\[@[^\]]+\]", "", t)
    t = re.sub(r"(?<![\w@])@\w+", "", t)
    return Counter(numbers_in(t))


a_md = md_numbers(SRC_PKG / "manuscript" / "manuscript_aas.md")
n_md = md_numbers(PKG / "manuscript_nh.md")
# Rebuild 2026-11-02: the only-AAS set is still the Section 3.1 move.
# The only-NH set is now just the "S1" pointer token: the report-
# geography caption tokens that the 2026-11-01 map insertion added to
# NH alone (1980, 2023, 25, 1.00, 46 x2, 8.7, 528 and the figure
# renumbering tokens) now appear in both manuscripts and cancel, as
# do the new pole-map caption tokens, which both manuscripts carry.
check("numeric tokens: NH md vs AAS md (mod directed S3.1 move)",
      (a_md - n_md) == Counter({"1.000": 1, "66": 1, "22": 1,
                                "0.063": 1, "0.054": 1})
      and (n_md - a_md) == Counter({"1": 1}),
      f"only-AAS {dict((a_md - n_md))}, only-NH {dict((n_md - a_md))}")

aas_text, _ = docx_text(SRC_PKG / "manuscript" / "manuscript_aas_formatted.docx")
a_doc = Counter(numbers_in(aas_text))
n_doc = Counter(numbers_in(nh_text))
# Deliberate, bib-faithful rendering differences (the AAS builder dropped
# these fields): book DOI for Saltelli 2008 (10.1002, 9780470725184),
# FAO series number for Allen 1998 (56), and proceedings title/pages for
# McKee 1993 (8, 179, 184).
EXPLAINED = Counter({"10.1002": 1, "9780470725184": 1, "56": 1, "8": 1,
                     "179": 1, "184": 1})
# Fix round 2026-11-01 additions, each tied to a directed change:
# only-NH gains the Sokol year labels (five "2026" in text citations,
# two in the reference list, less the one in the dropped SEG note) and
# the FAO URL tokens (4, 0490 twice, 00). Only-AAS gains the five
# Section 3.1 literals moved to the supplement, the dropped SEG
# manuscript number (0019), and the Adams note's calibration years
# (1981, 2010). The "1" tokens cancel: "S1" joins in Section 3.1 while
# the "1" of "SPI-1" leaves with the Adams note.
EXPLAINED_NH = EXPLAINED + Counter({"2026": 6, "4": 1, "0490": 2,
                                    "00": 1})
# Rebuild 2026-11-02: the 2026-11-01 map-figure token block is gone
# from EXPLAINED_NH, because the AAS manuscript now carries the same
# two map figures with identical caption numbers, so those tokens
# cancel between the two DOCXs. The three GLM-only references left
# both reference lists symmetrically and add no delta.
EXPLAINED_AAS = Counter({"1.000": 1, "66": 1, "22": 1, "0.063": 1,
                         "0.054": 1, "0019": 1, "1981": 1, "2010": 1})
diff_aas = a_doc - n_doc
diff_nh = n_doc - a_doc
check("numeric tokens: NH docx vs AAS docx (mod explained)",
      diff_aas == EXPLAINED_AAS and diff_nh == EXPLAINED_NH,
      f"only-AAS {dict(diff_aas)}, only-NH {dict(diff_nh)}")

# ---- 4. word counts -------------------------------------------------------
abs_m = re.search(r"## Abstract\s*\n(.*?)\n\n", ms, re.S)
abs_words = len(abs_m.group(1).split())
# Rebuild 2026-11-02: 188 words after the lightning clauses left the
# abstract (inside the journal's 150 to 250 word band).
check("abstract == 188 words", abs_words == 188, f"counted {abs_words}")
kw = re.search(r"\*\*Keywords:\*\*\s*(.+)", ms).group(1)
check("keywords == 6", len([k for k in kw.split(",") if k.strip()]) == 6)
pre_ref = paras[:ri]
front = 4  # title, author, affiliation, corresponding-author paragraphs
main_words = sum(len(t.split()) for t in pre_ref[front:])
for t in nh_doc.tables:
    for row in t.rows:
        for cell in row.cells:
            main_words += sum(len(p.text.split()) for p in cell.paragraphs)
total_words = sum(len(t.split()) for t in paras) + sum(
    len(p.text.split()) for t in nh_doc.tables for row in t.rows
    for cell in row.cells for p in cell.paragraphs)
print(f"INFO main text (body through Acknowledgments, incl. captions and "
      f"tables): {main_words} words; total DOCX: {total_words} words")

# ---- 5. em dash / semicolon scans -----------------------------------------
check("no em dash in NH manuscript", "—" not in nh_text)
stripped = re.sub(r"\([^()]*?(?:\d{4}|n\.d\.)[^()]*?\)", "", nh_text)
check("semicolons only inside citations (manuscript)", ";" not in stripped,
      f"residual {stripped.count(';')}")
cl_text, _ = docx_text(PKG / "cover_letter_nh.docx")
check("no em dash in NH cover letter", "—" not in cl_text)
check("no semicolons in NH cover letter", ";" not in cl_text)

# ---- 6. DOCX hygiene --------------------------------------------------------
for name in ("manuscript_nh.docx", "cover_letter_nh.docx",
             "supplementary_information_nh.docx"):
    z = zipfile.ZipFile(PKG / name)
    names = z.namelist()
    blob = b"\n".join(z.read(n) for n in names if n.endswith(".xml"))
    check(f"{name}: no 'python-docx' string", b"python-docx" not in blob)

    content_parts = [n for n in names if n == "word/document.xml"
                     or re.match(r"word/(header|footer)\d*\.xml$", n)]
    cblob = b"\n".join(z.read(n) for n in content_parts)
    check(f"{name}: no themeColor in content parts",
          b"themeColor" not in cblob)
    colors = set(re.findall(rb'w:color w:val="([0-9A-Fa-f]{6})"', cblob))
    check(f"{name}: all content colors black", colors <= {b"000000"},
          f"found {colors}")
    # The python-docx template style library (styles.xml,
    # stylesWithEffects.xml) carries latent theme definitions that never
    # reach rendered text. The delivered AAS package carries exactly the
    # same residue; assert parity with it rather than rewriting styles.
    aas_z = zipfile.ZipFile(
        SRC_PKG / "manuscript" / "manuscript_aas_formatted.docx")
    for part in ("word/styles.xml", "word/stylesWithEffects.xml"):
        same = z.read(part).count(b"themeColor") == \
            aas_z.read(part).count(b"themeColor")
        check(f"{name}: template parity with AAS file in {part}", same)
    core = z.read("docProps/core.xml").decode("utf-8")
    check(f"{name}: creator is the author",
          "<dc:creator>Nicholas J. Sokol</dc:creator>" in core)
    desc = re.search(r"<dc:description>(.*?)</dc:description>", core, re.S)
    check(f"{name}: dc:description blank",
          desc is None or desc.group(1).strip() == "")
    if name.startswith("manuscript"):
        doc_xml = z.read("word/document.xml").decode("utf-8")
        check("manuscript: line numbering present",
              "w:lnNumType" in doc_xml)
        media = [n for n in names if n.startswith("word/media/")]
        fig_md5 = {hashlib.md5((PKG / "figures" / f).read_bytes()).hexdigest()
                   for f in ("fig_s1_count_heatmaps.png", "fig_s2_variance.png",
                             "fig_h1_forest.png", "fig_h2_envelope.png",
                             "fig_h3_series.png", "fig_map_geography.png",
                             "fig_map_poles.png")}
        emb_md5 = {hashlib.md5(z.read(n)).hexdigest() for n in media}
        # Rebuild 2026-11-02: 7 figures (the pole map joined).
        check("manuscript: 7 figures embedded, MD5-matched to sources",
              len(media) == 7 and emb_md5 == fig_md5,
              f"media {len(media)}")
        cap_re = re.compile(r"^(Table|Figure) \d+\.")
        keeps = sum(1 for p in nh_doc.paragraphs
                    if cap_re.match(p.text.strip())
                    and p.paragraph_format.keep_with_next)
        # Rebuild 2026-11-02: 10 captions (3 tables + 7 figures); the
        # builder sets keep_with_next on captions in the raw build.
        check("manuscript: 10 captions carry keep_with_next", keeps == 10,
              f"found {keeps}")

print()
print("RESULT:", "ALL PASS" if not failures else f"FAILURES: {failures}")
sys.exit(1 if failures else 0)
