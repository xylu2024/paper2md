"""
Core conversion logic for Paper2MD:
- Extracts reading flow and handles two-column academic layouts via PyMuPDF4LLM
- Extracts high-resolution figures into a structured folder
- Uses RapidLaTeXOCR to convert math equations into KaTeX/LaTeX ($$ ... $$)
- Applies comprehensive character and font healing to eliminate \ufffd and symbol corruptions
"""

import os
import re
from pathlib import Path
from typing import Optional

import pymupdf
from pymupdf4llm.helpers import document_layout
from pymupdf4llm.helpers.document_layout import (
    title_to_md,
    section_hdr_to_md,
    list_item_to_md,
    footnote_to_md,
    text_to_md,
    picture_text_to_md,
    create_list_item_levels,
    GRAPHICS_TEXT,
)

from .cleaner import clean_textlines, clean_table_markdown, clean_markdown_text

try:
    from rapid_latex_ocr import LaTeXOCR
    _OCR_AVAILABLE = True
    _OCR_ERROR = None
except Exception as e:
    _OCR_AVAILABLE = False
    _OCR_ERROR = str(e)


def get_clean_fig_dir(pdf_file: Path) -> str:
    """Generate a clean, space-free folder name for extracted figures."""
    m = re.match(r'^([a-zA-Z0-9]+)', pdf_file.stem)
    base = m.group(1) if m else "doc"
    year_m = re.search(r'\b(19\d\d|20\d\d)\b', pdf_file.stem)
    if year_m:
        return f"{base}_{year_m.group(1)}_figures"
    return f"{base}_figures"


def clean_latex(latex_str: str) -> str:
    """Normalize and clean raw LaTeX OCR output for KaTeX/MathJax rendering."""
    s = latex_str.strip()
    if not s:
        return ""

    # 1. Clean long trails of spaces / tildes / quads / semicolons
    s = re.sub(r'(?:\\qquad|\\quad|\\;|\\,|\\!|~|\s)+$', '', s)

    # 2. Detect equation tag at the end (e.g. \qquad (12) or \quad(1) or (A.1) or (\mathrm{~A.4)})
    tag = ""
    tag_m = re.search(r'(?:\\qquad|\\quad|\\;|~|\s)+\((.*?)\)?\}?\s*$', s)
    if tag_m:
        raw = re.sub(r'\\[a-zA-Z]+|\{|\}|~|\s', '', tag_m.group(1))
        m = re.search(r'([A-Za-z0-9]+(?:\.[0-9A-Za-z]+)?|[0-9]+[a-zA-Z]?)', raw)
        if m:
            clean_num = m.group(1)
            clean_num = re.sub(r'([A-Za-z])\.[lI]', r'\1.1', clean_num)
            clean_num = re.sub(r'^[dD]\.', 'A.', clean_num)
            if clean_num.lower() not in ['phi', 'varepsilon', 'omega', 'alpha', 'beta'] and len(clean_num) <= 6:
                tag = f" \\tag{{{clean_num}}}"
                s = s[:tag_m.start()].strip()

    # 3. Strip unnecessary \begin{array}{...} wrapping if single row
    array_m = re.match(r'^\\begin\{array\}\{[^}]+\}\s*\{\{?(.*?)\}?\}\s*\\end\{array\}$', s, re.DOTALL)
    if array_m:
        inner = array_m.group(1).strip()
        inner = re.sub(r'(?:\\qquad|\\quad|\\;|~|\s)+$', '', inner).strip()
        s = inner

    # 4. Clean bold font notation: \bf{\bf x} -> \mathbf{x}
    s = re.sub(r'\\bf\{\\bf\s+([^}]+)\}', r'\\mathbf{\1}', s)
    s = re.sub(r'\\bf\{([^}]+)\}', r'\\mathbf{\1}', s)
    s = re.sub(r'{\\bf\s+([a-zA-Z0-9]+)\}', r'\\mathbf{\1}', s)

    # 5. Clean trailing unclosed or erroneous vertical bars e.g. 2\pi| -> 2\pi l
    s = re.sub(r'2\\pi\|\s*$', r'2\\pi l', s)
    s = re.sub(r'2\\pi\|\s*\}', r'2\\pi l}', s)

    # 6. Clean trailing formatting spacing
    s = re.sub(r'(?:\\qquad|\\quad|\\;|\\,|\\!|~|\s)+$', '', s).strip()

    # 7. Strip trailing periods before tag
    if s.endswith('.') and tag:
        s = s[:-1].strip()

    return (s + tag).strip()


def convert_pdf_to_md(
    pdf_path: str,
    output_md_path: Optional[str] = None,
    dpi: int = 200,
    enable_formula_ocr: bool = True,
    ocr_model: Optional["LaTeXOCR"] = None,
) -> str:
    """
    Convert a single PDF paper to Markdown with figures, LaTeX formulas, and cleaned symbols.
    
    Args:
        pdf_path: Path to the input PDF file.
        output_md_path: Optional path for the output markdown file. Defaults to same name as PDF.
        dpi: Resolution for extracted figures (default: 200).
        enable_formula_ocr: Whether to run OCR on formulas to convert them into LaTeX.
        ocr_model: Optional pre-loaded LaTeXOCR instance.

    Returns:
        The path of the generated markdown file.
    """
    pdf_file = Path(pdf_path).resolve()
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_file}")

    if output_md_path is None:
        output_md_path = pdf_file.with_suffix(".md")
    else:
        output_md_path = Path(output_md_path).resolve()

    fig_dir_name = get_clean_fig_dir(pdf_file)
    fig_dir = pdf_file.parent / fig_dir_name
    fig_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[Paper2MD] Processing: {pdf_file.name}")
    print(f"  -> Output: {output_md_path.name}")
    print(f"  -> Figures: {fig_dir_name}/")

    orig_cwd = Path.cwd()
    os.chdir(pdf_file.parent)

    try:
        if enable_formula_ocr and not _OCR_AVAILABLE:
            print(f"  -> [Info] Local LaTeX OCR unavailable ({_OCR_ERROR}). Formulas will be kept as images.")
            print("     To enable LaTeX formula OCR, run: pip install rapid_latex_ocr requests")

        if enable_formula_ocr and _OCR_AVAILABLE and ocr_model is None:
            print("  -> Initializing local LaTeX OCR engine...")
            ocr_model = LaTeXOCR()

        print("  -> Analyzing layout & extracting elements...")
        parsed_doc = document_layout.parse_document(
            str(pdf_file.name),
            image_dpi=dpi,
            image_format="png",
            image_path=fig_dir_name,
            write_images=True,
            force_text=True,
        )

        md_output = ""
        formulas_count = 0
        figures_count = 0

        for page in parsed_doc.pages:
            list_item_levels = create_list_item_levels(page.boxes)

            for i, box in enumerate(page.boxes):
                btype = box.boxclass
                clip = pymupdf.IRect(box.x0, box.y0, box.x1, box.y1)

                # Skip header/footer
                if btype in ("page-header", "page-footer"):
                    continue

                # Mathematical Formulas
                if btype == "formula":
                    raw_latex = ""
                    if enable_formula_ocr and ocr_model and box.image:
                        img_path = Path(box.image)
                        if img_path.exists():
                            try:
                                with open(img_path, "rb") as f:
                                    img_bytes = f.read()
                                res, _ = ocr_model(img_bytes)
                                raw_latex = clean_latex(res)
                            except Exception as e:
                                print(f"    [Warn] Formula OCR error on {img_path.name}: {e}")
                            finally:
                                # Remove temporary formula snippet file so figures folder stays tidy
                                try:
                                    img_path.unlink(missing_ok=True)
                                except Exception:
                                    pass

                    if raw_latex:
                        formulas_count += 1
                        md_output += f"\n$$\n{raw_latex}\n$$\n\n"
                    elif box.image and Path(box.image).exists():
                        md_output += GRAPHICS_TEXT % box.image + "\n\n"
                    continue

                # Pictures / Figures
                if btype == "picture":
                    if isinstance(box.image, str):
                        figures_count += 1
                        md_output += GRAPHICS_TEXT % box.image + "\n\n"
                    if box.textlines:
                        clean_textlines(box.textlines)
                        md_output += picture_text_to_md(
                            box.textlines,
                            ignore_code=page.full_ocred,
                            clip=clip,
                        )
                    continue

                # Tables
                if btype == "table":
                    if box.table.get("html"):
                        table_html = clean_table_markdown(box.table["html"])
                        md_output += table_html + "\n\n"
                    else:
                        table_text = box.table["markdown"]
                        if page.full_ocred:
                            table_text = table_text.replace("`", "")
                        table_text = clean_table_markdown(table_text)
                        md_output += table_text + "\n\n"
                    continue

                if not hasattr(box, "textlines") or not box.textlines:
                    continue

                # Clean spans in textlines before converting to markdown
                clean_textlines(box.textlines)

                # Headings & Text
                if btype == "title":
                    md_output += title_to_md(box.header_level, box.textlines)
                elif btype == "section-header":
                    md_output += section_hdr_to_md(box.header_level, box.textlines)
                elif btype == "list-item":
                    md_output += list_item_to_md(box.textlines, list_item_levels[i])
                elif btype == "footnote":
                    md_output += footnote_to_md(box.textlines)
                else:
                    md_output += text_to_md(box.textlines, ignore_code=page.full_ocred)

        # Comprehensive post-processing to clean mathematical symbols, exponents,
        # units, names, and any remaining replacement characters (\ufffd)
        md_output = clean_markdown_text(md_output)

        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(md_output)

        print(f"  [Success] Done! Formulas converted: {formulas_count}, Figures preserved: {figures_count}")
        return str(output_md_path)

    finally:
        os.chdir(orig_cwd)
