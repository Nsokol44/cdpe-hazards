#!/usr/bin/env python3
"""Step 09 - Build the AAS manuscript DOCX from manuscript_aas.md.

Renders [@key] citations and @key narrative citations in AAS style from
references_aas.bib, generates the reference list in AAS Endnote style,
builds pipe tables and figure blocks, and enforces the standing format
rules: Times New Roman throughout, all text black (theme colours stripped),
metadata creator "Nicholas J. Sokol". Fails if any ⟦token⟧ remains, if an
em dash appears, or if a prose semicolon appears outside citation groups.
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
MS = ROOT / "manuscript" / "manuscript_aas.md"
BIB = ROOT / "manuscript" / "references_aas.bib"
OUT = ROOT / "manuscript" / "manuscript_aas.docx"
FIGDIR = ROOT / "figures"

JOURNAL_ABBR = {
    "Advances in Atmospheric Sciences": "Adv. Atmos. Sci.",
    "Nature Reviews Earth & Environment": "Nat. Rev. Earth Environ.",
    "International Journal of Climatology": "Int. J. Climatol.",
    "Journal of Climate": "J. Climate",
    "Atmospheric Research": "Atmos. Res.",
    "Earth and Space Science": "Earth Space Sci.",
    "Weather and Forecasting": "Wea. Forecasting",
    "Journal of Applied Meteorology and Climatology":
        "J. Appl. Meteor. Climatol.",
    "Nature Geoscience": "Nat. Geosci.",
    "E-Journal of Severe Storms Meteorology":
        "Electron. J. Severe Storms Meteor.",
    "Weather and Climate Extremes": "Wea. Climate Extremes",
    "npj Natural Hazards": "npj Nat. Hazards",
}


def parse_bib(text):
    entries = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", text, re.S):
        body = m.group(3)
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*\{", body):
            # brace-aware value scan: values may contain balanced braces
            depth, j = 1, fm.end()
            while j < len(body) and depth:
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                j += 1
            fields[fm.group(1)] = body[fm.end():j - 1]
        entries[m.group(2).strip()] = {
            k: v.replace("&amp;", "&").strip() for k, v in fields.items()}
    return entries


def _split_authors(raw: str) -> list[str]:
    """Split on ' and ' at brace depth 0 (corporate names may contain it)."""
    parts, depth, cur, i = [], 0, "", 0
    while i < len(raw):
        ch = raw[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        if depth == 0 and raw.startswith(" and ", i):
            parts.append(cur)
            cur, i = "", i + 5
            continue
        cur += ch
        i += 1
    parts.append(cur)
    return [p.strip() for p in parts]


def authors_of(fields):
    raw = fields.get("author", "")
    out = []
    for p in _split_authors(raw):
        if p.startswith("{") and p.endswith("}"):
            out.append((p[1:-1].strip(), ""))  # corporate author
        elif "," in p:
            fam, given = p.split(",", 1)
            out.append((fam.strip(), given.strip()))
        else:
            toks = p.split()
            out.append((toks[-1], " ".join(toks[:-1])))
    return out


def initials(given):
    out = []
    for tok in re.split(r"[\s]+", given):
        if not tok:
            continue
        subs = tok.split("-")
        out.append("-".join(s[0].upper() + "." for s in subs if s))
    return " ".join(out)


def cite_parenthetical(keys, bib):
    rendered = []
    for key in keys:
        f = bib[key]
        auth = authors_of(f)
        year = f.get("year", "n.d.")
        if len(auth) == 1:
            who = auth[0][0]
        elif len(auth) == 2:
            who = f"{auth[0][0]} and {auth[1][0]}"
        else:
            who = f"{auth[0][0]} et al."
        rendered.append((int(re.sub(r"\D", "", year) or 0), f"{who}, {year}"))
    rendered.sort()
    return "(" + "; ".join(r[1] for r in rendered) + ")"


def cite_narrative(key, bib):
    f = bib[key]
    auth = authors_of(f)
    year = f.get("year", "n.d.")
    if len(auth) == 1:
        who = auth[0][0]
    elif len(auth) == 2:
        who = f"{auth[0][0]} and {auth[1][0]}"
    else:
        who = f"{auth[0][0]} et al."
    return f"{who} ({year})"


def reference_entry(key, f):
    auth = authors_of(f)
    names = []
    for fam, given in auth:
        ini = initials(given)
        names.append(f"{fam}, {ini}" if ini else fam)
    if len(names) > 1:
        byline = ", ".join(names[:-1]) + ", and " + names[-1]
    else:
        byline = names[0] if names else ""
    year = f.get("year", "")
    title = f.get("title", "")
    head = f"{byline}, {year}: {title}." if year else f"{byline}: {title}."
    journal = f.get("journal", "")
    if journal:
        journal = JOURNAL_ABBR.get(journal, journal)
        vol = f.get("volume", "")
        pages = f.get("pages", "").replace("--", "–")
        tail = f" {journal}"
        if vol:
            tail += f", **{vol}**"
        if pages:
            tail += f", {pages}"
        tail += "."
        if f.get("doi"):
            tail += f" https://doi.org/{f['doi']}"
        return head + tail
    extra = f.get("howpublished", "") or f.get("publisher", "")
    note = f.get("note", "")
    tail = f" {extra}." if extra else ""
    if note:
        tail += f" {note}."
    return head + tail


INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|\[@[^\]]+\]|(?<![\w@])@\w+)")


def add_runs(par, text, bib):
    for tok in INLINE.split(text):
        if not tok:
            continue
        if tok.startswith("[@"):
            keys = [k.strip().lstrip("@") for k in tok[1:-1].split(";")]
            par.add_run(cite_parenthetical(keys, bib))
        elif tok.startswith("@") and not tok.startswith("@@"):
            par.add_run(cite_narrative(tok[1:], bib))
        elif tok.startswith("**") and tok.endswith("**"):
            r = par.add_run(tok[2:-2]); r.bold = True
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            r = par.add_run(tok[1:-1]); r.italic = True
        else:
            par.add_run(tok)


def main() -> int:
    raw = MS.read_text(encoding="utf-8")
    assert "⟦" not in raw, "unfilled tokens remain"
    assert "—" not in raw, "em dash present"
    prose = re.sub(r"\[@[^\]]+\]", "", raw)
    assert ";" not in prose, "prose semicolon present"
    bib = parse_bib(BIB.read_text(encoding="utf-8"))
    lines = raw.splitlines()
    meta, i = {}, 0
    if lines[0].strip() == "---":
        i = 1
        while lines[i].strip() != "---":
            m = re.match(r'(\w+):\s*"(.*)"', lines[i].strip())
            if m:
                meta[m.group(1)] = m.group(2)
            i += 1
        i += 1

    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(meta["title"]); r.bold = True; r.font.size = Pt(16)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(meta["author"]); r.bold = True
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(meta["affiliation"])
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(f"Corresponding author: {meta['author']}, "
              f"{meta['affiliation']}. E-mail: {meta['email']}. "
              f"ORCID: {meta['orcid']}.")

    cited_order = []
    para_buf = []

    def flush():
        nonlocal para_buf
        if para_buf:
            text = " ".join(s.strip() for s in para_buf).strip()
            if text:
                add_runs(doc.add_paragraph(), text, bib)
            para_buf = []

    while i < len(lines):
        line, s = lines[i], lines[i].strip()
        fig = re.match(r"\[FIGURE:\s*(\S+)\]\s*(.*)", s)
        if fig:
            flush()
            img = FIGDIR / f"{fig.group(1)}.png"
            doc.add_picture(str(img))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            if fig.group(2):
                add_runs(doc.add_paragraph(), fig.group(2), bib)
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and \
                re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            rows = [rows[0]] + rows[2:]
            table = doc.add_table(rows=len(rows), cols=len(rows[0]))
            table.style = "Table Grid"
            for ri, row in enumerate(rows):
                for ci, cell in enumerate(row):
                    par = table.cell(ri, ci).paragraphs[0]
                    add_runs(par, cell, bib)
                    if ri == 0:
                        for run in par.runs:
                            run.bold = True
            continue
        if s.startswith("## "):
            flush()
            doc.add_heading(s[3:], level=2)
        elif s.startswith("# "):
            flush()
            doc.add_heading(s[2:], level=1)
        elif s == "":
            flush()
        else:
            para_buf.append(line)
        i += 1
    flush()

    for key in re.findall(r"\[@([^\]]+)\]", raw):
        cited_order.extend(k.strip().lstrip("@") for k in key.split(";"))
    cited_order.extend(re.findall(r"(?<![\w@])@(\w+)", raw))
    cited = sorted(set(cited_order),
                   key=lambda k: (authors_of(bib[k])[0][0].lower(),
                                  bib[k].get("year", "")))
    doc.add_heading("References", level=1)
    for key in cited:
        add_runs(doc.add_paragraph(), reference_entry(key, bib[key]), bib)

    # Force Times New Roman, black, and strip theme attributes everywhere.
    def clean_paragraph(par):
        for run in par.runs:
            run.font.name = "Times New Roman"
            run.font.color.rgb = RGBColor(0, 0, 0)
            rpr = run._element.get_or_add_rPr()
            for tag in ("w:color",):
                el = rpr.find(qn(tag))
                if el is not None:
                    for attr in ("w:themeColor", "w:themeTint", "w:themeShade"):
                        if el.get(qn(attr)) is not None:
                            del el.attrib[qn(attr)]
            rfonts = rpr.find(qn("w:rFonts"))
            if rfonts is not None:
                for attr in ("w:hAnsiTheme", "w:asciiTheme", "w:csTheme",
                             "w:eastAsiaTheme"):
                    if rfonts.get(qn(attr)) is not None:
                        del rfonts.attrib[qn(attr)]

    for par in doc.paragraphs:
        clean_paragraph(par)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for par in cell.paragraphs:
                    clean_paragraph(par)
    for style in doc.styles:
        try:
            style.font.name = "Times New Roman"
            style.font.color.rgb = RGBColor(0, 0, 0)
        except Exception:  # noqa: BLE001
            pass

    # Keep every caption with its object across page breaks. A caption
    # paragraph never splits internally (keep_together) and never strands
    # at a page foot away from what follows it (keep_with_next). Table
    # captions precede their tables, so this bonds caption to table.
    # Figure captions follow their image paragraph in this build, so the
    # image paragraph also gets keep_with_next to hold it with its
    # caption on the same page.
    caption_re = re.compile(r"^(Table|Figure) \d+\.")
    n_captions = 0
    for par in doc.paragraphs:
        if caption_re.match(par.text.strip()):
            par.paragraph_format.keep_with_next = True
            par.paragraph_format.keep_together = True
            n_captions += 1
        if par._p.xpath(".//w:drawing"):
            par.paragraph_format.keep_with_next = True
    assert n_captions == 8, f"expected 8 captions, found {n_captions}"

    cp = doc.core_properties
    cp.author = "Nicholas J. Sokol"
    cp.last_modified_by = "Nicholas J. Sokol"
    cp.title = meta["title"]
    cp.comments = ""
    doc.save(OUT)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
