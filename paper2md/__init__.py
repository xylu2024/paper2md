"""
Paper2MD: High-fidelity academic PDF to Markdown converter with LaTeX formula OCR and figure extraction.
"""

from .version import __version__
from .converter import convert_pdf_to_md

__all__ = ["convert_pdf_to_md", "__version__"]
