# -*- coding: utf-8 -*-
"""
Script xóa phần số thứ tự chương/mục bị lặp cứng trong chuỗi văn bản của
các tiêu đề Heading 1, Heading 2, Heading 3 (do Word đã cấu hình Multilevel List
tự động đánh số `CHƯƠNG %1:`, `%1.%2`, `%1.%2.%3`), đồng thời làm sạch luôn
bản lưu đệm trong Mục lục (Table of Contents SDT) của file `Internship_Report - Copy.docx`.
"""

from __future__ import annotations

import re
from pathlib import Path
import docx
from docx.oxml.ns import qn


ROOT_DIR = Path(__file__).resolve().parent.parent
TARGET_FILES = [
    ROOT_DIR / "Internship_Report - Copy.docx",
    ROOT_DIR / "Internship_Report - Completed.docx",
]

PAT_H1 = re.compile(r"^\s*CHƯƠNG\s+\d+\s*[\.\:\-]?\s*", re.IGNORECASE)
PAT_H23 = re.compile(r"^\s*\d+(?:\.\d+)+\.?\s*")


def update_paragraph_runs_in_place(p: docx.text.paragraph.Paragraph, new_text: str) -> None:
    """Cập nhật nội dung văn bản của đoạn văn mà vẫn giữ nguyên bookmark (_Toc...) và định dạng Run."""
    runs = p.runs
    if not runs:
        p.add_run(new_text)
        return
    runs[0].text = new_text
    for r in runs[1:]:
        r.text = ""


def clean_toc_sdt(doc: docx.Document) -> int:
    """Làm sạch phần tiền tố bị lặp trong các dòng mục lục (TOC SDT) được Word lưu đệm."""
    cleaned_toc_entries = 0
    sdts = doc._body._body.findall(f".//{qn('w:sdt')}")
    for sdt in sdts:
        for p_el in sdt.findall(f".//{qn('w:p')}"):
            # Kiểm tra các thẻ <w:t> bên trong hyperlink của dòng TOC
            t_elems = p_el.findall(f".//{qn('w:t')}")
            for t_el in t_elems:
                txt = t_el.text or ""
                if not txt.strip():
                    continue
                # Không xóa thẻ <w:t> đầu tiên vốn là nhãn số tự động của Word (ví dụ 'CHƯƠNG 1:', '1.1', '1.2.1')
                # Chỉ xóa khi chuỗi chứa cả tiền tố số lẫn tên tiêu đề (dài hơn nhãn số đơn thuần)
                new_txt = PAT_H1.sub("", txt)
                if new_txt == txt:
                    new_txt = PAT_H23.sub("", txt)
                if new_txt != txt and new_txt.strip():
                    t_el.text = new_txt.strip()
                    cleaned_toc_entries += 1
    return cleaned_toc_entries


def clean_document_headings(docx_path: Path) -> None:
    if not docx_path.exists():
        return
    doc = docx.Document(str(docx_path))
    count_h1 = 0
    count_h2 = 0
    count_h3 = 0

    for p in doc.paragraphs:
        style_name = p.style.name
        raw_text = p.text
        if not raw_text or not raw_text.strip():
            continue

        if style_name == "Heading 1":
            cleaned = PAT_H1.sub("", raw_text).strip()
            if cleaned != raw_text.strip():
                update_paragraph_runs_in_place(p, cleaned)
                count_h1 += 1
        elif style_name == "Heading 2":
            cleaned = PAT_H23.sub("", raw_text).strip()
            if cleaned != raw_text.strip():
                update_paragraph_runs_in_place(p, cleaned)
                count_h2 += 1
        elif style_name == "Heading 3":
            cleaned = PAT_H23.sub("", raw_text).strip()
            if cleaned != raw_text.strip():
                update_paragraph_runs_in_place(p, cleaned)
                count_h3 += 1

    toc_cleaned = clean_toc_sdt(doc)
    doc.save(str(docx_path))
    print(
        f"[{docx_path.name}] Đã xóa tiền tố số thừa: "
        f"Heading 1 = {count_h1}, Heading 2 = {count_h2}, Heading 3 = {count_h3}, "
        f"Dòng mục lục (TOC cache) = {toc_cleaned}."
    )


def main() -> None:
    for path in TARGET_FILES:
        clean_document_headings(path)


if __name__ == "__main__":
    main()
