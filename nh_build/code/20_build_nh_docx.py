#!/usr/bin/env python3
"""Step 20 - Build the Natural Hazards manuscript DOCX from manuscript_nh.md.

Adapted from the AAS builder (step 09). Differences are format-only:
- Citations and the reference list are rendered in Springer author-year
  style from references_nh.bib (byte-identical copy of the verified
  references_aas.bib): "(Author Year)", groups ordered per the journal's
  alphabetization rules, list entries as "Surname Initials (Year) Title.
  JournalAbbr Volume:Pages. https://doi.org/...".
- The "Statements and Declarations" section held at the end of the .md is
  emitted after the generated References, per the journal's guidelines.
- Body font 10-pt Times New Roman, continuous line numbering, automatic
  page numbering in the footer.
Standing rules enforced as in step 09: all text black (theme attributes
stripped), metadata creator "Nicholas J. Sokol", failure on any em dash
or any prose semicolon outside citation groups.
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

PKG = Path(__file__).resolve().parents[1]
MS = PKG / "manuscript_nh.md"
BIB = PKG / "references_nh.bib"
OUT = PKG / "manuscript_nh.docx"
FIGDIR = PKG / "figures"

# ISSN List of Title Word Abbreviations forms (journal as named in the bib).
JOURNAL_ABBR = {
    "Advances in Atmospheric Sciences": "Adv Atmos Sci",
    "Annual Review of Earth and Planetary Sciences":
        "Annu Rev Earth Planet Sci",
    "Annals of Statistics": "Ann Stat",
    "Atmospheric Research": "Atmos Res",
    "Bulletin of the American Meteorological Society":
        "Bull Am Meteorol Soc",
    "Earth and Space Science": "Earth Space Sci",
    "E-Journal of Severe Storms Meteorology":
        "Electron J Sev Storms Meteorol",
    "Geographical Review": "Geogr Rev",
    "Geophysical Research Letters": "Geophys Res Lett",
    "International Journal of Climatology": "Int J Climatol",
    "Journal of Applied Meteorology and Climatology":
        "J Appl Meteorol Climatol",
    "Journal of Climate": "J Clim",
    "Journal of Geophysical Research": "J Geophys Res",
    "Nature": "Nature",
    "Nature Geoscience": "Nat Geosci",
    "Nature Reviews Earth & Environment": "Nat Rev Earth Environ",
    "Nature Water": "Nat Water",
    "New Phytologist": "New Phytol",
    "npj Natural Hazards": "npj Nat Hazards",
    "Quarterly Journal of the Royal Meteorological Society":
        "Q J R Meteorol Soc",
    "Science Advances": "Sci Adv",
    "Scientific Data": "Sci Data",
    "Stochastic Hydrology and Hydraulics": "Stoch Hydrol Hydraul",
    "Water": "Water",
    "Water Resources Research": "Water Resour Res",
    "Weather and Climate Extremes": "Weather Clim Extremes",
    "Weather and Forecasting": "Weather Forecast",
}


def parse_bib(text):
    entries = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", text, re.S):
        body = m.group(3)
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*\{", body):
            depth, j = 1, fm.end()
            while j < len(body) and depth:
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                j += 1
            fields[fm.group(1)] = body[fm.end():j - 1]
        entries[m.group(2).strip()] = {
            "entrytype": m.group(1),
            **{k: v.replace("&amp;", "&").strip()
               for k, v in fields.items()}}
    return entries


def _split_authors(raw: str) -> list[str]:
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
    """[(family, given)] with a trailing ('others', '') marker preserved."""
    out = []
    for p in _split_authors(fields.get("author", "")):
        if p == "others":
            out.append(("others", ""))
        elif p.startswith("{") and p.endswith("}"):
            out.append((p[1:-1].strip(), ""))
        elif "," in p:
            fam, given = p.split(",", 1)
            out.append((fam.strip(), given.strip()))
        else:
            toks = p.split()
            out.append((toks[-1], " ".join(toks[:-1])))
    return out


def real_authors(fields):
    return [a for a in authors_of(fields) if a[0] != "others"]


def has_others(fields):
    return any(a[0] == "others" for a in authors_of(fields))


def initials_springer(given):
    out = []
    for tok in re.split(r"[\s]+", given):
        if not tok:
            continue
        subs = tok.replace(".", "").split("-")
        out.append("-".join(s[0].upper() for s in subs if s))
    return "".join(out)


def year_of(fields):
    return fields.get("year", "") or "n.d."


# Springer disambiguates works by the same author in the same year with
# letter suffixes (2026a, 2026b). Populated in main() before rendering.
YEAR_LABELS = {}


def year_label(key, fields):
    return YEAR_LABELS.get(key) or year_of(fields)


def compute_year_labels(bib, cited):
    groups = {}
    for k in cited:
        groups.setdefault((who_text(bib[k]), year_of(bib[k])), []).append(k)
    labels = {}
    for (who, yr), keys in groups.items():
        if len(keys) > 1:
            keys.sort(key=lambda k: ref_sort_key(k, bib))
            for i, k in enumerate(keys):
                labels[k] = f"{yr}{'abcdefghijklmnopqrstuvwxyz'[i]}"
    return labels


def year_sort(fields):
    y = year_of(fields)
    m = re.match(r"n\.d\.(a|b)?", y)
    if m:
        return (0, m.group(1) or "")
    digits = re.sub(r"\D", "", y)
    return (int(digits) if digits else 9999, "")


def ref_sort_key(key, bib):
    """Springer alphabetization: first author; then single-author works,
    two-author works (by coauthor), multi-author works; chronological
    within each class."""
    f = bib[key]
    auth = real_authors(f)
    fam1 = auth[0][0].lower() if auth else key
    ini1 = initials_springer(auth[0][1]).lower() if auth else ""
    if has_others(f) or len(auth) > 2:
        cls, fam2 = 2, ""
    elif len(auth) == 2:
        cls, fam2 = 1, auth[1][0].lower()
    else:
        cls, fam2 = 0, ""
    return (fam1, ini1, cls, fam2, year_sort(f), f.get("title", "").lower())


def who_text(fields):
    auth = real_authors(fields)
    if has_others(fields) or len(auth) > 2:
        return f"{auth[0][0]} et al."
    if len(auth) == 2:
        return f"{auth[0][0]} and {auth[1][0]}"
    return auth[0][0]


def cite_parenthetical(keys, bib):
    rendered = [(ref_sort_key(k, bib),
                 f"{who_text(bib[k])} {year_label(k, bib[k])}")
                for k in keys]
    rendered.sort(key=lambda r: r[0])
    return "(" + "; ".join(r[1] for r in rendered) + ")"


def cite_narrative(key, bib):
    return f"{who_text(bib[key])} ({year_label(key, bib[key])})"


def author_list_springer(fields):
    names = []
    for fam, given in real_authors(fields):
        ini = initials_springer(given)
        names.append(f"{fam} {ini}" if ini else fam)
    if has_others(fields):
        return (names[0] + " et al") if names else "et al"
    return ", ".join(names)


def reference_entry(key, f):
    year = year_label(key, f)
    head = f"{author_list_springer(f)} ({year}) {f.get('title', '')}."
    doi = f.get("doi", "")
    doi_tail = f" https://doi.org/{doi}" if doi else ""
    journal = f.get("journal", "")
    if journal:
        journal = JOURNAL_ABBR.get(journal, journal)
        vol = f.get("volume", "")
        pages = f.get("pages", "").replace("--", "–")
        tail = f" {journal}"
        if vol and pages:
            tail += f" {vol}:{pages}."
        elif vol:
            tail += f" {vol}."
        else:
            tail += "."
        return head + tail + doi_tail
    if f.get("entrytype") == "inproceedings":
        pages = f.get("pages", "").replace("--", "–")
        tail = f" In: {f.get('booktitle', '')}"
        if pages:
            tail += f", pp {pages}"
        return head + tail + "."
    if f.get("entrytype") == "techreport":
        tail = (f" {f.get('institution', '')} Irrigation and Drainage Paper "
                f"{f.get('number', '')}.")
        if f.get("url"):
            tail += f" {f['url']}"
        return head + tail
    if f.get("entrytype") == "book":
        return head + f" {f.get('publisher', '')}." + doi_tail
    extra = f.get("howpublished", "") or f.get("publisher", "")
    note = f.get("note", "")
    # Polish round (author-directed, 2026-11-01): when the trailing
    # field is itself a URL (Adams 2017, howpublished = the GitHub
    # address), Springer style leaves no period after it.
    if extra.startswith("http"):
        tail = f" {extra}"
    elif extra:
        tail = f" {extra}."
    else:
        tail = ""
    if note:
        tail += f" {note}."
    return head + tail + doi_tail


def _set_cell_border(cell, edge, val, sz):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = tcPr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tcPr.append(borders)
    el = borders.find(qn(f"w:{edge}"))
    if el is None:
        el = OxmlElement(f"w:{edge}")
        borders.append(el)
    el.set(qn("w:val"), val)
    el.set(qn("w:sz"), str(sz))
    el.set(qn("w:space"), "0")
    el.set(qn("w:color"), "000000")


def style_booktabs(table):
    """Booktabs styling (review fix round, 2026-11-01): a heavy top rule,
    a light rule under the header row, a heavy bottom rule, no other
    borders, and rows that cannot split, so the table stays on one page.
    Applied to Tables 1 and 2 only, per the review brief."""
    rows = table.rows
    for ri, row in enumerate(rows):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
        for cell in row.cells:
            for edge in ("top", "left", "bottom", "right",
                         "insideH", "insideV"):
                _set_cell_border(cell, edge, "none", 0)
            for par in cell.paragraphs:
                par.paragraph_format.keep_together = True
                if ri < len(rows) - 1:
                    par.paragraph_format.keep_with_next = True
    for cell in rows[0].cells:
        _set_cell_border(cell, "top", "single", 12)
        _set_cell_border(cell, "bottom", "single", 6)
    for cell in rows[-1].cells:
        _set_cell_border(cell, "bottom", "single", 12)


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
    cited_keys = set()
    for group in re.findall(r"\[@([^\]]+)\]", raw):
        cited_keys.update(k.strip().lstrip("@") for k in group.split(";"))
    cited_keys.update(re.findall(r"(?<![\w@])@(\w+)", raw))
    YEAR_LABELS.update(compute_year_labels(bib, cited_keys))
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

    # Split off the Statements and Declarations block (rendered last).
    sd_start = lines.index("# Statements and Declarations")
    body_lines, sd_lines = lines[:sd_start], lines[sd_start:]

    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(10)
    for style_name, size in (("Heading 1", 12), ("Heading 2", 11),
                             ("Heading 3", 10)):
        st = doc.styles[style_name]
        st.font.name = "Times New Roman"
        st.font.size = Pt(size)
        st.font.bold = True

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

    para_buf = []

    def flush(target_doc=doc):
        nonlocal para_buf
        if para_buf:
            text = " ".join(s.strip() for s in para_buf).strip()
            if text:
                add_runs(target_doc.add_paragraph(), text, bib)
            para_buf = []

    def render(line_list):
        nonlocal para_buf
        j = 0
        while j < len(line_list):
            line, s = line_list[j], line_list[j].strip()
            fig = re.match(r"\[FIGURE:\s*(\S+)\]\s*(.*)", s)
            if fig:
                flush()
                img = FIGDIR / f"{fig.group(1)}.png"
                doc.add_picture(str(img))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                if fig.group(2):
                    add_runs(doc.add_paragraph(), fig.group(2), bib)
                j += 1
                continue
            if s.startswith("|") and j + 1 < len(line_list) and \
                    re.match(r"^\|[\s:|-]+\|$", line_list[j + 1].strip()):
                flush()
                rows = []
                while j < len(line_list) and \
                        line_list[j].strip().startswith("|"):
                    cells = [c.strip() for c in
                             line_list[j].strip().strip("|").split("|")]
                    rows.append(cells)
                    j += 1
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
            j += 1
        flush()

    # body_lines still contains the YAML block lines; render from the
    # first content line after it (same offset logic as step 09).
    j0 = 0
    if body_lines[0].strip() == "---":
        j0 = 1
        while body_lines[j0].strip() != "---":
            j0 += 1
        j0 += 1
    render(body_lines[j0:])

    # Tables 1 and 2 (the first two tables in document order) get the
    # booktabs treatment; Table 3 keeps the grid style, per the brief.
    for tbl in list(doc.tables)[:2]:
        style_booktabs(tbl)

    # Polish round (author-directed, 2026-11-01): Table 2 layout only,
    # no content change. The first column widens so entries such as
    # "SPEI-1, theta = 1.5, r = 4 degrees" stay on one line, and the
    # paragraph after the table gains space before it so the last row
    # no longer touches the following text. Widths sum to the 6.0 in
    # text measure (Letter, 1.25 in side margins).
    from docx.shared import Inches
    from docx.text.paragraph import Paragraph as _Paragraph
    _t2 = doc.tables[1]
    _widths = [Inches(2.80), Inches(1.25), Inches(0.95), Inches(1.00)]
    _t2.autofit = False
    _layout = OxmlElement("w:tblLayout")
    _layout.set(qn("w:type"), "fixed")
    _t2._tbl.tblPr.append(_layout)
    for _row in _t2.rows:
        for _ci, _cell in enumerate(_row.cells):
            _cell.width = _widths[_ci]
    for _ci, _col in enumerate(_t2.columns):
        _col.width = _widths[_ci]
    _next = _t2._tbl.getnext()
    if _next is not None and _next.tag == qn("w:p"):
        _Paragraph(_next, doc).paragraph_format.space_before = Pt(6)

    cited = set()
    for group in re.findall(r"\[@([^\]]+)\]", raw):
        cited.update(k.strip().lstrip("@") for k in group.split(";"))
    cited.update(re.findall(r"(?<![\w@])@(\w+)", raw))
    doc.add_heading("References", level=1)
    for key in sorted(cited, key=lambda k: ref_sort_key(k, bib)):
        add_runs(doc.add_paragraph(), reference_entry(key, bib[key]), bib)

    render(sd_lines)

    # Continuous line numbering + automatic page numbering (footer).
    section = doc.sections[0]
    sectPr = section._sectPr
    ln = OxmlElement("w:lnNumType")
    ln.set(qn("w:countBy"), "1")
    ln.set(qn("w:start"), "0")
    ln.set(qn("w:restart"), "continuous")
    pg_mar = sectPr.find(qn("w:pgMar"))
    pg_mar.addnext(ln)
    footer_par = section.footer.paragraphs[0]
    footer_par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer_par.add_run()
    fld_begin = OxmlElement("w:fldChar"); fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar"); fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin); run._r.append(instr); run._r.append(fld_end)

    def clean_paragraph(par):
        for run in par.runs:
            run.font.name = "Times New Roman"
            run.font.color.rgb = RGBColor(0, 0, 0)
            rpr = run._element.get_or_add_rPr()
            el = rpr.find(qn("w:color"))
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
    for par in section.footer.paragraphs:
        clean_paragraph(par)
    for style in doc.styles:
        try:
            style.font.name = "Times New Roman"
            style.font.color.rgb = RGBColor(0, 0, 0)
        except Exception:  # noqa: BLE001
            pass

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
