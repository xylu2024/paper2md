"""
Command-line interface (CLI) for Paper2MD.
"""

import sys
import argparse
from pathlib import Path

from .converter import convert_pdf_to_md, _OCR_AVAILABLE

try:
    from rapid_latex_ocr import LaTeXOCR
except ImportError:
    LaTeXOCR = None


def main():
    parser = argparse.ArgumentParser(
        prog="paper2md",
        description="Paper2MD: High-fidelity academic PDF to Markdown converter with LaTeX formula OCR and figure extraction."
    )
    parser.add_argument("target", help="Path to a PDF file or a directory containing PDFs.")
    parser.add_argument("-o", "--output", help="Optional output .md path (for single file).", default=None)
    parser.add_argument("--dpi", type=int, default=200, help="DPI for extracted figures (default: 200).")
    parser.add_argument("--no-ocr", action="store_true", help="Disable LaTeX formula OCR (keep formulas as images).")

    args = parser.parse_args()
    target_path = Path(args.target).resolve()

    if not target_path.exists():
        print(f"Error: Target path does not exist: {target_path}")
        sys.exit(1)

    ocr_model = None
    if not args.no_ocr:
        if _OCR_AVAILABLE and LaTeXOCR is not None:
            print("[Paper2MD] Loading LaTeX OCR model...")
            try:
                ocr_model = LaTeXOCR()
            except Exception as e:
                print(f"[Paper2MD] Warning: Could not initialize LaTeX OCR ({e}). Formulas will be kept as images.")
        else:
            print("[Paper2MD] Note: LaTeX OCR dependencies not installed. Formulas will be kept as images.")
            print("           To enable LaTeX formula OCR, run: pip install rapid_latex_ocr requests")

    if target_path.is_file() and target_path.suffix.lower() == ".pdf":
        convert_pdf_to_md(
            str(target_path),
            output_md_path=args.output,
            dpi=args.dpi,
            enable_formula_ocr=not args.no_ocr,
            ocr_model=ocr_model,
        )
    elif target_path.is_dir():
        pdf_files = list(target_path.glob("*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in {target_path}")
            return
        print(f"Found {len(pdf_files)} PDF files in {target_path}")
        for pdf in pdf_files:
            try:
                convert_pdf_to_md(
                    str(pdf),
                    dpi=args.dpi,
                    enable_formula_ocr=not args.no_ocr,
                    ocr_model=ocr_model,
                )
            except Exception as e:
                print(f"[Error] Failed to convert {pdf.name}: {e}")
    else:
        print(f"Target is not a PDF file or valid directory: {target_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
