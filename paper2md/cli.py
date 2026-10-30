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
    parser.add_argument(
        "targets",
        nargs="+",
        help="Path to one or more PDF files, or directories containing PDF files."
    )
    parser.add_argument(
        "-o", "--output",
        help="Optional output .md path (valid only when converting a single PDF).",
        default=None
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="DPI for extracted figures (default: 200)."
    )
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="Disable LaTeX formula OCR (keep formulas as images)."
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Force re-conversion even if document was already converted (ignore status.json)."
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively scan subdirectories for PDF files."
    )

    args = parser.parse_args()

    collected_pdfs = []
    for t_str in args.targets:
        t_path = Path(t_str).resolve()
        if not t_path.exists():
            print(f"[Paper2MD] Warning: Path does not exist: {t_path}")
            continue
        if t_path.is_file():
            if t_path.suffix.lower() == ".pdf":
                collected_pdfs.append(t_path)
            else:
                print(f"[Paper2MD] Skipping non-PDF file: {t_path.name}")
        elif t_path.is_dir():
            if args.recursive:
                found = list(t_path.rglob("*.pdf")) + list(t_path.rglob("*.PDF"))
            else:
                found = list(t_path.glob("*.pdf")) + list(t_path.glob("*.PDF"))
            found_sorted = sorted(list({p.resolve() for p in found}), key=lambda p: p.name.lower())
            collected_pdfs.extend(found_sorted)

    # Deduplicate while preserving order
    pdf_files = []
    seen = set()
    for p in collected_pdfs:
        if p not in seen:
            seen.add(p)
            pdf_files.append(p)

    if not pdf_files:
        print("[Paper2MD] No PDF files found to process.")
        sys.exit(0)

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

    total = len(pdf_files)
    if total > 1:
        print(f"\n[Paper2MD] Starting batch processing for {total} document(s)...")

    success_count = 0
    skipped_count = 0
    failed_count = 0

    for idx, pdf in enumerate(pdf_files, 1):
        prefix = f"[{idx}/{total}] " if total > 1 else ""
        try:
            out = convert_pdf_to_md(
                str(pdf),
                output_md_path=args.output if total == 1 else None,
                dpi=args.dpi,
                enable_formula_ocr=not args.no_ocr,
                ocr_model=ocr_model,
                force=args.force,
                return_details=True,
            )
            if isinstance(out, dict) and out.get("status") == "skipped":
                skipped_count += 1
            else:
                success_count += 1
        except Exception as e:
            failed_count += 1
            print(f"  [Error] {prefix}Failed to convert {pdf.name}: {e}")

    if total > 1:
        print("\n" + "=" * 55)
        print("[Paper2MD Batch Summary]")
        print(f"  Total documents : {total}")
        print(f"  Converted       : {success_count}")
        print(f"  Skipped (cached): {skipped_count}")
        print(f"  Failed          : {failed_count}")
        print("=" * 55)


if __name__ == "__main__":
    main()
