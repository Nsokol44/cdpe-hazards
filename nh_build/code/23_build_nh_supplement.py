#!/usr/bin/env python3
"""Step 23 - Build the Natural Hazards supplementary information DOCX
from supplementary_information_nh.md.

Created in the 2026-11-01 review fix round: Section 3.1 of the main
text was shortened and the full companion-study count comparison moved
here (Supplementary Information S1). Built the same way as the
manuscript (step 20): 10-pt Times New Roman, continuous line
numbering, automatic page numbering in the footer, all text black,
metadata creator "Nicholas J. Sokol". Fails on any em dash or
semicolon in the source.
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

    for block in "\n".join(lines[i:]).split("\n\n"):
        text = " ".join(block.split())
        if text:
            doc.add_paragraph(text)

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
