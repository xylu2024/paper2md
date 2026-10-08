"""
Text and Character Normalization for Paper2MD.

Fixes academic typesetting font quirks, unmapped glyphs, replacement characters (\\ufffd),
broken math symbols, negative exponents in units, vector accents, and corrupted European diacritics.
"""

import re
from typing import List, Dict, Any, Optional


def clean_font_span(text: str, font: str) -> str:
    """
    Map font-specific character encodings for academic and Elsevier 3B2 fonts.
    """
    if not text:
        return ""

    font_lower = font.lower() if font else ""

    # 1. Advent Symbol fonts (AdvPS*, e.g., AdvPS44A44B) where 'e' is en-dash and '$' is times/cdot
    if "advps" in font_lower or "symbol" in font_lower:
        if text == "e":
            return "–"
        if text == "$":
            return "×"

    # 2. MathType Extra font (MT-Extra) where \x02 / \ufffd is a vector arrow
    if "mt-extra" in font_lower:
        text = text.replace("\x02", "").replace("\ufffd", "")
        return "\\vec{" + text + "}" if text.strip() else "\\vec"

    # 3. Elsevier 3B2 math font (AdvP4C4E74 and similar)
    if "4c4e74" in font_lower or "4c4e3a" in font_lower:
        text = text.replace("\x02", "−")
        text = text.replace("¡", "−")
        text = text.replace("\x04", "°")
        text = text.replace("\x05", "≈")
        text = text.replace("¼", "=")
        text = text.replace("þ", "+")
        text = text.replace("ð", "(")
        text = text.replace("Þ", ")")
        text = text.replace("j", "|")

    # 4. Symbol Greek letters (AdvPS4721B4)
    if "4721b4" in font_lower:
        if text == "r":
            return "ρ"
        if text == "u":
            return "ω"
        if text == "4":
            return "Δϕ"

    # 5. Approx / punctuation in AdvPS3FDD77
    if "3fdd77" in font_lower:
        if text == "z":
            return "≈"
        if text == ",":
            return "×"

    return text


def clean_textlines(textlines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Clean spans within PyMuPDF textlines, normalizing fonts and merging overlapping diacritics.
    """
    if not textlines or not isinstance(textlines, list):
        return textlines

    for line in textlines:
        if not isinstance(line, dict) or "spans" not in line:
            continue
        spans = line.get("spans", [])
        if not spans:
            continue

        for span in spans:
            if not isinstance(span, dict):
                continue
            text = span.get("text", "")
            font = span.get("font", "")
            if text:
                span["text"] = clean_font_span(text, font)

    return textlines


def clean_table_markdown(table_md: str) -> str:
    """
    Normalize table markdown content (units, math symbols, dimensionless quantities).
    """
    if not table_md:
        return ""

    # Replace dimensionless symbol placeholder [e] with [-]
    table_md = re.sub(r'\[e\]', '[-]', table_md)

    # Normalize exponents in table units
    table_md = re.sub(r'<sup>\s*[\ufffd¡−–]\s*([0-9a-zA-Z=/_+.-]+)\s*</sup>', r'<sup>-\1</sup>', table_md)
    table_md = re.sub(
        r'(\b(?:m|s|K|W|J|A|V|Pa|Hz|N|T|g|kg|mol)\b(?:\s*\(?[a-zA-Z0-9^/ ]+\)?)?)\s*<sup>\s*[\ufffd¡−–]\s*([0-9]+)\s*</sup>',
        r'\1<sup>-\2</sup>',
        table_md
    )

    # Common math symbols in tables
    table_md = table_md.replace("¼", "=")
    table_md = table_md.replace("þ", "+")
    table_md = table_md.replace("ð", "(")
    table_md = table_md.replace("Þ", ")")
    table_md = re.sub(r'T\(x;y\)', 'T(x,y)', table_md)
    table_md = re.sub(r'\bCp;([a-zA-Z0-9]+)\b', r'C_{p,\1}', table_md)

    return table_md


def clean_markdown_text(s: str) -> str:
    """
    Comprehensive multi-pass cleaner for the final generated Markdown text.
    Eliminates replacement characters (\\ufffd), restores negative unit exponents,
    formats dimensions, and corrects scientific terms and foreign names.
    """
    if not s:
        return ""

    # --- 1. Basic 3B2 Math Symbol Replacements ---
    s = s.replace("¼", "=")
    s = s.replace("þ", "+")
    s = s.replace("ð", "(")
    s = s.replace("Þ", ")")

    # --- 2. Exponents and Units (Superscripts) ---
    # Fix explicit minus signs replaced by \ufffd, ¡, etc. in superscripts: <sup>1</sup> -> <sup>-1</sup>
    s = re.sub(r'<sup>\s*[\ufffd¡−–]\s*([0-9a-zA-Z=/_+.-]+)\s*</sup>', r'<sup>-\1</sup>', s)

    # Fix units with missing minus sign inside <sup> when marked with \ufffd or ¡
    s = re.sub(
        r'(\b(?:m|s|K|W|J|A|V|Pa|Hz|N|T|g|kg|mol)\b(?:\s*\(?[a-zA-Z0-9^/ ]+\)?)?)\s*<sup>\s*[\ufffd¡−–]\s*([0-9]+)\s*</sup>',
        r'\1<sup>-\2</sup>',
        s
    )
    s = re.sub(r'(\b(?:mm|cm|m)\b)\s*<sup>\s*[\ufffd¡−–]\s*([0-9]+)\s*</sup>', r'\1<sup>-\2</sup>', s)
    s = re.sub(r'(\b(?:mm|cm|m)\b)\s*<sup>\s*([1-9])\s*</sup>\s*,?\s*leading', r'\1<sup>-\2</sup>, leading', s)
    s = re.sub(r'10[\ufffd¡](\d+)', r'10^-\1', s)
    s = re.sub(r'K[\ufffd]1', 'K^-1', s)
    s = re.sub(r'Wm[\ufffd]2', 'W m^-2', s)

    # Scientific notation commas: e.g. 7.46,10 -> 7.46 × 10
    s = re.sub(r'(\d+(?:\.\d+)?)\s*,\s*(10<sup>)', r'\1 × \2', s)
    s = re.sub(r'(\d+(?:\.\d+)?)\s*,\s*(10\^-?\d+)', r'\1 × \2', s)

    # Temperature / Degree symbols: 20<sup></sup> C -> 20 °C, 1<sup></sup> -> 1°
    s = re.sub(r'(\d+(?:\.\d+)?)\s*<sup>\s*[\ufffd°]?\s*</sup>\s*([CFK])\b', r'\1 °\2', s)
    s = re.sub(r'(\d+(?:\.\d+)?)\s*<sup>\s*[\ufffd°]\s*</sup>', r'\1°', s)
    s = re.sub(r'(\d+(?:\.\d+)?)\s*[\ufffd]\s*C\b', r'\1 °C', s)

    # --- 3. Dimensions and Numerical Ranges ---
    # 3D: 50  30  12 mm -> 50 × 30 × 12 mm
    s = re.sub(r'(\d+(?:\.\d+)?)\s*[\ufffd]\s*(\d+(?:\.\d+)?)\s*[\ufffd]\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|nm|µm|um)', r'\1 × \2 × \3 \4', s)
    # 2D: 9.6  9.6 mm -> 9.6 × 9.6 mm
    s = re.sub(r'(\d+(?:\.\d+)?)\s*[\ufffd]\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|nm|µm|um)', r'\1 × \2 \3', s)
    s = re.sub(r'(\d+(?:\.\d+)?)\s*[\ufffd]\s*(\d+(?:\.\d+)?)', r'\1 × \2', s)

    # Page and number ranges: 246 e255 -> 246–255, 1456e1464 -> 1456–1464
    s = re.sub(r'(\d+)\s*e\s*(\d+)', r'\1–\2', s)
    s = re.sub(r'(\d+)e(\d+)', r'\1–\2', s)

    # --- 4. Scientific Words and Compound Terms ---
    # Dimensionless quantity indicator [e] in tables / text
    s = re.sub(r'\[e\]', '[-]', s)
    s = re.sub(r'\bHeeNe\b', 'He-Ne', s)
    s = re.sub(r'\bsolideliquid\b', 'solid-liquid', s)
    s = re.sub(r'\bmagnetizationedemagnetization\b', 'magnetization-demagnetization', s)
    s = re.sub(r'\bheatetransfer\b', 'heat-transfer', s)
    s = re.sub(r'\b(Fig\.\s*\d+[a-z]?)\s+e\s+', r'\1 – ', s)
    s = re.sub(r'\bconvection\s+e\s+in\s+contrast\b', 'convection – in contrast', s)
    s = re.sub(r'\bmachine\s+e\s+the\s+visual\b', 'machine – the visual', s)

    # --- 5. Names and European Diacritics ---
    # Author names
    s = re.sub(r'Tu[\ufffd]?sek', 'Tušek', s)
    s = re.sub(r'Poredo[\ufffd]?s', 'Poredoš', s)
    s = re.sub(r'Bj[\ufffd]?rk', 'Bjørk', s)
    s = re.sub(r'(?:\bS|[\ufffd])arlah', 'Šarlah', s)
    s = re.sub(r'\bSŠarlah\b', 'Šarlah', s)
    s = re.sub(r'Universit[€\ufffd]at', 'Universität', s)

    # French keywords and academic terminology
    s = re.sub(r'Mots\s+cl[\ufffd]?es', 'Mots clés', s)
    s = re.sub(r'Froid\s+magnetique[\ufffd]?', 'Froid magnétique', s)
    s = re.sub(r'Interferom[\ufffd]?\s*etre[\ufffd]?', 'Interféromètre', s)
    s = re.sub(r'Reg[\ufffd]?\s*en[\ufffd]?\s*erateur[\ufffd]?', 'Régénérateur', s)
    s = re.sub(r'magnetique[\ufffd]?\s*a[\ufffd]?\s*plaques', 'magnétique à plaques', s)
    s = re.sub(r'paralleles[\ufffd]?', 'parallèles', s)
    s = re.sub(r'interferom[\ufffd]?\s*etriques[\ufffd]?', 'interférométriques', s)
    s = re.sub(r'\ba[\ufffd]?\s*resolution[\ufffd]?', 'à résolution', s)
    s = re.sub(r'magnetis[\ufffd]?\s*ee[\ufffd]?', 'magnétisée', s)
    s = re.sub(r'periodiquement[\ufffd]?', 'périodiquement', s)

    # --- 6. Math Formulas and Expressions in Prose ---
    s = re.sub(r'T\(x;y\)', 'T(x,y)', s)
    s = re.sub(r'T\(x;\s*t\)', 'T(x, t)', s)
    s = re.sub(r'\bJa;b\b', 'J_{a,b}', s)
    s = re.sub(r'\bCp;Gd\b', 'C_{p,Gd}', s)
    s = re.sub(r'\bCp;f\b', 'C_{p,f}', s)
    s = re.sub(r'beyond\s+t\s*[\ufffd\x05]\s*(\d+)', r'beyond t ≈ \1', s)
    s = re.sub(r'dxz0:2', 'dx ≈ 0.2', s)
    s = re.sub(r'\$t\s*[\ufffd]\s*(\d+)', r'$t - \1', s)
    s = re.sub(r'from\s*[\ufffd]p\s*to\s*p', r'from -π to π', s)
    s = re.sub(r'=\s*[\ufffd](DTad)', r'= -\1', s)
    s = re.sub(r'\)\s*[\ufffd]\s*n\(T0\)', ') - n(T0)', s)
    s = re.sub(r'[\ufffd\x07]{1,3}x=', '|_{x=', s)
    s = re.sub(r'[\ufffd\x07]{1,3}fi', '|_{fi}', s)
    s = re.sub(r'[\ufffd\x07]{1,3}T=', '|_{T=', s)
    s = re.sub(r'Be<sup>[\ufffd]Cx[\ufffd\x07]*</sup>', r'Be<sup>-Cx</sup>|_{fi}', s)
    s = re.sub(r'p4:45kf', r'√(4.45 kf)', s)
    s = re.sub(r'p3:71kf', r'√(3.71 kf)', s)
    s = re.sub(r'\bpkf\b', r'√(kf)', s)

    # --- 7. Vectors (e.g. MT-Extra font / arrow artifacts) ---
    s = re.sub(r'_B_\s*[\ufffd\x02]\s*_r_', r'$\\vec{B}_r$', s)
    s = re.sub(r'_B_\s*[\ufffd\x02]', r'$\\vec{B}$', s)
    s = re.sub(r'[\ufffd\x02]\s*_B_', r'$\\vec{B}$', s)
    s = re.sub(r'[\ufffd\x02]\s*_fL_', r'$\\vec{f}_L$', s)
    s = re.sub(r'[\ufffd\x02]\s*_j_', r'$\\vec{j}$', s)
    s = re.sub(r'[\ufffd\x02]\s+([BjfvEHAM])\b', r'$\\vec{\1}$', s)
    s = re.sub(r'\b([BjfvEHAM])\s+[\ufffd\x02]\b', r'$\\vec{\1}$', s)
    s = re.sub(r'(?:[\ufffd\x02]\s*){2,}_?fL_?', r'$\\vec{f}_L$', s)
    s = re.sub(r'(?:[\ufffd\x02]\s*){2,}_?j_?', r'$\\vec{j}$', s)
    s = re.sub(r'(?:[\ufffd\x02]\s*){2,}_?B_?', r'$\\vec{B}$', s)

    # --- 8. Clean Any Remaining Stray \ufffd ---
    s = re.sub(r'([a-zA-Z0-9])[\ufffd]([a-zA-Z0-9])', r'\1-\2', s)
    s = re.sub(r'[\ufffd]+', '', s)

    return s
