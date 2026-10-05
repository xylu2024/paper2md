# Paper2MD 📄➡️📝

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey)](https://github.com/xylu2024/paper2md)
[![Powered by PyMuPDF](https://img.shields.io/badge/layout-PyMuPDF4LLM-green)](https://github.com/pymupdf/pymupdf4llm)
[![OCR: RapidLaTeXOCR](https://img.shields.io/badge/OCR-RapidLaTeXOCR-orange)](https://github.com/RapidAI/RapidLaTeXOCR)

> **High-Fidelity Academic PDF to Markdown Converter**  
> Engineered specifically for complex scientific literature (dual-column layouts, vector schematics, high-resolution plots, and dense mathematical formulas).

---

## 💡 Motivation: Why Paper2MD?

Converting complex scientific papers (e.g., from *Nature Portfolio*, *ACS*, *Science*, *IEEE*, *Elsevier*) into Markdown for note-taking in **Obsidian**, LLM knowledge indexing (RAG), or web viewing is notoriously difficult:

- **Microsoft MarkItDown**: Relies on basic heuristic rules. On dual-column academic PDFs, it misinterprets columns and margins as a **monstrous 20-column empty table header**, glues words together (`determinethecompletereaction...`), completely drops figures in offline mode, and scrambles formulas into ASCII gibberish.
- **Raw PyMuPDF / Text Extractors**: While resolving reading flows, they slice mathematical equations into dozens of tiny PNG images that clutter your image folder and cannot be rendered natively as text.
- **Heavy Multimodal Models (e.g., Nougat / MinerU)**: While accurate, they require tens of gigabytes of GPU VRAM, heavy CUDA toolchains, and minutes per paper, making them impractical for lightweight laptops or quick batch workflows.

**Paper2MD** bridges this gap:
1. **Two-Column Flow Restoration**: Powered by PyMuPDF layout analysis, eliminating column splitting and word gluing.
2. **Local LaTeX Formula Recognition**: Automatically detects equation bounding boxes, passes them to a lightweight local ONNX model (**RapidLaTeXOCR**, ~0.3 s per equation), and outputs native KaTeX/MathJax `$$ ... $$` code with `\tag{}` equation numbers.
3. **Clean Figure Management**: Extracts only authentic scientific figures and diagrams at high resolution (200+ DPI), while **automatically purging temporary equation snippet images** to keep your folder tidy.
4. **Blazingly Fast & Lightweight**: Converts a 10-page dense article in 5–10 seconds on a standard CPU.

---

## 🔬 Head-to-Head Comparison: MarkItDown vs. Paper2MD

### 1. Dual-Column Layout & Headings
*Tested on ACS JPCC (Bidmon et al., 2026)*

* **Microsoft MarkItDown Output**:
  ```markdown
  | | pubs.acs.org/JPCC | | | | | | | | | | | | | | | Article |
  | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
  | | Determination | | | | of the | Kinetic | | Rate | Law | of | Rare-Earth | | | Solvent | | |
  | | Extraction | | Using | | Interferometry: | | | | The | Case | of | Samarium(III) | | | | |
  | .selcitra dehsilbup erahs yletamitigel ot woh no snoitpo rof senilediuggnirahs/gro.sca.sbup//:sptth eeS | ABSTRACT: | The | growing | | demand | for rare-earths, | | which are | | | | | | | | |
  ```
  *(Result: Inexplicably converted into a huge broken table where body text only occupies the table header, and watermark text is reversed).*

* **Paper2MD Output**:
  ```markdown
  # Determination of the Kinetic Rate Law of Rare-Earth Solvent Extraction Using Interferometry: The Case of Samarium(III)

  **Alexander Bidmon, Kilian Ortmann, Yuheng He, Kerstin Eckert, and Zhe Lei\***

  *Cite This: J. Phys. Chem. C 2026, 130, 1148−1157*

  ### ABSTRACT
  The growing demand for rare-earths, which are processed by using costly and environmentally unfriendly solvent extraction methods, requires a better understanding of the underlying reaction kinetics...
  ```
  *(Result: Clean hierarchy, clear headers, and natural reading flow).*

---

### 2. Typography & Word Gluing (Ligature Handling)

* **Microsoft MarkItDown**:
  ```text
  determinethecompletereactionratelawofaliquid−liquidsolvent
  ```
* **Paper2MD**:
  ```text
  determine the complete reaction rate law of a liquid−liquid solvent
  ```

---

### 3. Mathematical Formulas

* **Microsoft MarkItDown**:
  ```text
  J=-D dc/dz (12) (dropped or mangled into surrounding table cells)
  ```
* **Paper2MD (Automatically converted to standard KaTeX)**:
  ```markdown
  The Sm(III) reaction rate at the interface is correlated by Fick’s first law:

  $$
  J = -D \frac{\partial c}{\partial z} \tag{12}
  $$

  The mass transfer follows Fick’s second law:

  $$
  \frac{\partial c}{\partial t} = D \frac{\partial^{2}c}{\partial z^{2}} \tag{13}
  $$

  The Stokes−Einstein−Sutherland equation estimates the diffusion coefficient:

  $$
  D = \frac{k_{\mathrm{B}} T}{6\pi \eta R} \tag{14}
  $$
  ```

---

### 4. Summary Matrix

| Feature | Microsoft MarkItDown | PyMuPDF4LLM (Raw) | **Paper2MD** |
| :--- | :--- | :--- | :--- |
| **Dual-Column Layout** | ❌ Broken into giant empty tables | ✅ Natural reading flow | ✅ **Natural reading flow** |
| **Word Spacing / Ligatures** | ❌ Severe word gluing | ✅ Normal spaces | ✅ **Normal spaces** |
| **Figure Extraction** | ❌ 0 figures offline (needs Azure API) | ⚠️ Mixed formulas & figures | ✅ **Authentic figures only (200+ DPI)** |
| **Mathematical Formulas** | ❌ Lost or corrupted | ⚠️ Exported as small PNG snippets | ✅ **OCR-converted to LaTeX `$$...$$`** |
| **Obsidian / Typora Native Math**| ❌ Cannot render | ⚠️ Cluttered with PNG links | ✅ **100% native vector rendering** |
| **Footnotes & References** | ❌ Scrambled | ✅ Superscript (`<sup>1</sup>`) | ✅ **Superscript (`<sup>1</sup>`)** |
| **Hardware Overhead** | Lightweight (poor output) | Lightweight (~2s) | **Lightweight (~5-10s, runs on any CPU)** |

---

## 📦 Installation

Paper2MD supports **Windows**, **Linux (Arch Linux / EndeavourOS, Ubuntu / Debian)**, and **macOS**.

### Option A: Install via `pipx` (Recommended for all platforms)

[`pipx`](https://pypa.github.io/pipx/) isolates the package and automatically exposes the `paper2md` command globally without polluting your system Python environment. This is especially ideal for **Arch Linux / EndeavourOS** (avoids PEP 668 `externally-managed-environment` errors):

#### 1. Install pipx (if not already installed)
* **Arch Linux / EndeavourOS**:
  ```bash
  sudo pacman -S python-pipx
  pipx ensurepath
  ```
* **Ubuntu / Debian**:
  ```bash
  sudo apt update && sudo apt install pipx
  pipx ensurepath
  ```
* **macOS (Homebrew)**:
  ```bash
  brew install pipx
  pipx ensurepath
  ```
* **Windows**:
  ```powershell
  pip install pipx
  pipx ensurepath
  ```
*(Restart your terminal after running `pipx ensurepath`)*

#### 2. Install Paper2MD globally
```bash
pipx install git+https://github.com/xylu2024/paper2md.git
```
`paper2md` is now globally available in any terminal!

---

### Option B: Standard `pip` Installation

You can install Paper2MD directly into your active Python virtual environment:

```bash
# Direct install from GitHub
pip install git+https://github.com/xylu2024/paper2md.git

# Or clone and install in editable mode for development
git clone https://github.com/xylu2024/paper2md.git
cd paper2md
pip install -e .
```

> **Arch Linux / EndeavourOS Tip**:  
> If running `pip install` on system Python throws `error: externally-managed-environment`, create a dedicated venv first:  
> `python -m venv ~/.local/share/paper2md-env && source ~/.local/share/paper2md-env/bin/activate`

---

## 🚀 CLI Usage

### Basic Commands

```bash
# 1. Convert a single paper (creates paper.md and a clean figures folder)
paper2md "path/to/paper.pdf"

# 2. Batch convert all PDF papers in the current directory
paper2md .

# 3. Batch convert all PDF papers in a target directory
paper2md "D:/PhD/Literature"

# 4. Custom figure DPI resolution (default: 200, use 300 for high-res publication figures)
paper2md "paper.pdf" --dpi 300

# 5. Fast mode: Skip formula OCR (keeps equations as images)
paper2md "paper.pdf" --no-ocr
```

---

## 🐍 Python API Usage

You can seamlessly integrate Paper2MD into your own research scripts or document ingestion pipelines:

```python
from paper2md import convert_pdf_to_md

# Convert PDF and get path of resulting markdown file
output_path = convert_pdf_to_md(
    pdf_path="path/to/article.pdf",
    output_md_path="output.md",      # Optional: defaults to same name
    dpi=200,                         # Optional: figure resolution
    enable_formula_ocr=True          # Optional: whether to run LaTeX OCR
)

print(f"Successfully converted to: {output_path}")
```

---

## 📂 Output Folder Structure

When processing `Bidmon_2026.pdf`, Paper2MD generates:

```text
Literature/
├── Bidmon_2026.pdf
├── Bidmon_2026.md                    <-- Clean Markdown with LaTeX equations
└── Bidmon_2026_figures/              <-- Only genuine figures & charts
    ├── Bidmon_2026.pdf-0004-03.png   <-- Figure 1
    ├── Bidmon_2026.pdf-0005-05.png   <-- Figure 2
    └── ...
```
*(All temporary formula image slices are automatically deleted after OCR recognition to ensure zero folder pollution).*

---

## 🛠️ Core Dependencies

- **[PyMuPDF](https://github.com/pymupdf/PyMuPDF)** & **[PyMuPDF4LLM](https://github.com/pymupdf/pymupdf4llm)**: State-of-the-art document layout parser and reading-flow deconstruction.
- **[RapidLaTeXOCR](https://github.com/RapidAI/RapidLaTeXOCR)**: Lightweight, high-accuracy offline LaTeX equation OCR based on ONNXRuntime.
- **`opencv-python-headless`**: Fast image preprocessing backend without desktop GUI dependencies, fully compatible with headless Linux environments.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## ✍️ Authors & Institutional Affiliation

**Dipl.-Ing. Xueyong Lu** (he/him)  
Doctoral Researcher / Research Associate  
Department: Fluid Dynamics of Resource Technology Processes  
Institute of Fluid Dynamics  
Helmholtz-Zentrum Dresden - Rossendorf (HZDR)  
