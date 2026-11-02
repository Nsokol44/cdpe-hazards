#!/usr/bin/env python3
"""Step 23 - Build the Natural Hazards supplementary information DOCX
from supplementary_information_nh.md.

Created in the 2026-11-01 review fix round and extended in the Phase 5
rewrite (2026-11-02) to render the markdown structure the rewritten
supplement uses: YAML front matter (title, author, affiliation),
level-1 and level-2 headings, markdown tables (booktabs styling),
and bold or italic inline runs. Built the same way as the manuscript
(step 20): 10-pt Times New Roman, continuous line numbering, automatic
page numbering in the footer, all text black, metadata creator
"Nicholas J. Sokol". Fails on any em dash or semicolon in the source.
"""
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

PKG = Path(__file__).resolve().parents[1]
MS = PKG / "supplementary_information_nh.md"
OUT = PKG / "supplementary_information_nh.docx"

INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*)")


def add_runs(par, text):
    for tok in INLINE.split(text):
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            r = par.add_run(tok[2:-2])
            r.bold = True
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            r = par.add_run(tok[1:-1])
            r.italic = True
        else:
            par.add_run(tok)


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


def main() -> int:
    raw = MS.read_text(encoding="utf-8")
    assert "—" not in raw, "em dash present"
    assert ";" not in raw, "semicolon present"
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
    normal.font.size = Pt(10)
    for style_name, size in (("Heading 1", 12), ("Heading 2", 11),
                             ("Heading 3", 10)):
        st = doc.styles[style_name]
        st.font.name = "Times New Roman"
        st.font.size = Pt(size)
        st.font.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(meta["title"])
    r.bold = True
    r.font.size = Pt(13)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(meta["author"])
    r.bold = True
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(meta["affiliation"])

    para_buf = []

    def flush():
        nonlocal para_buf
        if para_buf:
            text = " ".join(s.strip() for s in para_buf).strip()
            if text:
                add_runs(doc.add_paragraph(), text)
            para_buf = []

    j = i
    while j < len(lines):
        line, s = lines[j], lines[j].strip()
        if s.startswith("|") and j + 1 < len(lines) and \
                re.match(r"^\|[\s:|-]+\|$", lines[j + 1].strip()):
            flush()
            rows = []
            while j < len(lines) and lines[j].strip().startswith("|"):
                cells = [c.strip() for c in
                         lines[j].strip().strip("|").split("|")]
                rows.append(cells)
                j += 1
            rows = [rows[0]] + rows[2:]
            table = doc.add_table(rows=len(rows), cols=len(rows[0]))
            table.style = "Table Grid"
            for ri, row in enumerate(rows):
                for ci, cell in enumerate(row):
                    par = table.cell(ri, ci).paragraphs[0]
                    add_runs(par, cell)
                    if ri == 0:
                        for run in par.runs:
                            run.bold = True
            style_booktabs(table)
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
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)

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
