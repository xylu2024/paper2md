"""
Paper2MD: High-fidelity academic PDF to Markdown converter with LaTeX formula OCR and figure extraction.
"""

from .converter import convert_pdf_to_md

__version__ = "0.1.1"
__all__ = ["convert_pdf_to_md", "__version__"]
