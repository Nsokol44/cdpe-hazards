#!/usr/bin/env python3
"""Step 09b - Build the cover letter DOCX from cover_letter.md.

Same standing format rules as the manuscript: Times New Roman, all text
black, metadata creator "Nicholas J. Sokol".
"""
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "manuscript" / "cover_letter.md"
OUT = ROOT / "manuscript" / "cover_letter.docx"


def main() -> int:
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    for block in SRC.read_text(encoding="utf-8").split("\n\n"):
        text = " ".join(block.split())
        if text:
            doc.add_paragraph(text)
    for par in doc.paragraphs:
        for run in par.runs:
            run.font.name = "Times New Roman"
            run.font.color.rgb = RGBColor(0, 0, 0)
    for style in doc.styles:
        try:
            style.font.name = "Times New Roman"
            style.font.color.rgb = RGBColor(0, 0, 0)
        except Exception:  # noqa: BLE001
            pass
    cp = doc.core_properties
    cp.author = "Nicholas J. Sokol"
    cp.last_modified_by = "Nicholas J. Sokol"
    cp.title = "Cover letter: CDPE hazards manuscript, Advances in Atmospheric Sciences"
    cp.comments = ""
    doc.save(OUT)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
