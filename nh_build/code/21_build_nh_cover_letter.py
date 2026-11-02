#!/usr/bin/env python3
"""Step 21 - Build the Natural Hazards cover letter DOCX from
cover_letter_nh.md. Same standing rules as step 09b: Times New Roman,
all text black, metadata creator "Nicholas J. Sokol". Fails on any em
dash or semicolon in the letter source."""
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor

PKG = Path(__file__).resolve().parents[1]
SRC = PKG / "cover_letter_nh.md"
OUT = PKG / "cover_letter_nh.docx"


def main() -> int:
    raw = SRC.read_text(encoding="utf-8")
    assert "—" not in raw, "em dash present"
    assert ";" not in raw, "semicolon present"
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    for block in raw.split("\n\n"):
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
    cp.title = ("Cover letter: CDPE hazards manuscript, Natural Hazards")
    cp.comments = ""
    doc.save(OUT)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
