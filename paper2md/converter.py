"""
Core conversion logic for Paper2MD:
- Extracts reading flow and handles two-column academic layouts via PyMuPDF4LLM
- Extracts high-resolution figures into a structured folder
- Uses RapidLaTeXOCR to convert math equations into KaTeX/LaTeX ($$ ... $$)
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

try:
    from rapid_latex_ocr import LaTeXOCR
    _OCR_AVAILABLE = True
except ImportError:
    _OCR_AVAILABLE = False


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

    # 1. Detect equation tag at the end (e.g. \qquad (12) or \quad(1))
    tag_m = re.search(r'(?:\\qquad|\\quad|\s)+\(([0-9]+[a-z]?)\)\s*$', s)
    tag = ""
    if tag_m:
        tag = f" \\tag{{{tag_m.group(1)}}}"
        s = s[:tag_m.start()].strip()

    # 2. Strip unnecessary \begin{array}{...} wrapping if single row
    array_m = re.match(r'^\\begin\{array\}\{[^}]+\}\s*\{\{?(.*?)\}?\}\s*\\end\{array\}$', s, re.DOTALL)
    if array_m:
        inner = array_m.group(1).strip()
        inner = re.sub(r'(\\qquad|\\quad)+\s*$', '', inner).strip()
        s = inner

    # 3. Clean trailing formatting spacing
    s = re.sub(r'(\\qquad|\\quad)+\s*$', '', s).strip()

    return (s + tag).strip()


def convert_pdf_to_md(
    pdf_path: str,
    output_md_path: Optional[str] = None,
    dpi: int = 200,
    enable_formula_ocr: bool = True,
    ocr_model: Optional["LaTeXOCR"] = None,
) -> str:
    """
    Convert a single PDF paper to Markdown with figures and LaTeX formulas.
    
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
                        md_output += picture_text_to_md(
                            box.textlines,
                            ignore_code=page.full_ocred,
                            clip=clip,
                        )
                    continue

                # Tables
                if btype == "table":
                    if box.table.get("html"):
                        md_output += box.table["html"] + "\n\n"
                    else:
                        table_text = box.table["markdown"]
                        if page.full_ocred:
                            table_text = table_text.replace("`", "")
                        md_output += table_text + "\n\n"
                    continue

                if not hasattr(box, "textlines"):
                    continue

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

        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(md_output)

        print(f"  [Success] Done! Formulas converted: {formulas_count}, Figures preserved: {figures_count}")
        return str(output_md_path)

    finally:
        os.chdir(orig_cwd)
