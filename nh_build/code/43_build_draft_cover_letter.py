#!/usr/bin/env python3
"""Fix Round 2, item 1 (fallback) - build the DRAFT replacement cover
letter DOCX from cover_letter_nh_DRAFT_2026-11-02.md.

The author's own replacement letter could not be found in
~/workspace/user/files, the NH Drive folder, or the project folder on
2026-11-02, so this draft was written from the rebuilt manuscript's
claims only. It is NOT the letter of record and is not filed to Drive:
the filed cover_letter_nh.docx stays in place until the author
supplies or approves a letter. Same format rules as code/21: Times
New Roman, all text black, creator metadata. Fails on any em dash or
semicolon in the source.
"""
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor

PKG = Path(__file__).resolve().parents[1]
SRC = PKG / "cover_letter_nh_DRAFT_2026-11-02.md"
OUT = PKG / "cover_letter_nh_DRAFT_2026-11-02.docx"


def main() -> int:
    raw = SRC.read_text(encoding="utf-8")
    assert "—" not in raw, "em dash present"
    assert ";" not in raw, "semicolon present"
    for stale in ("756", "46 CDPE months", "fitting distribution "
                  "dominate", "70 percent"):
        assert stale not in raw, f"stale claim present: {stale}"
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
    cp.title = ("DRAFT cover letter: CDPE hazards manuscript, "
                "Natural Hazards")
    cp.comments = ""
    doc.save(OUT)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
