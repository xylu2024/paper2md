# Paper2MD 📄➡️📝

> **High-Fidelity Academic PDF to Markdown Converter** with intelligent layout parsing, figure extraction, and local LaTeX formula OCR.
> 针对学术论文（双栏排版、复杂图表、数学公式）优化的 Markdown 转换工具。

---

## 🌟 Why Paper2MD? (为什么选择 Paper2MD)

现有的许多 PDF 转 Markdown 工具在处理学术期刊（如 Nature, Science, IEEE, ACS, Elsevier 等）时往往存在严重缺陷：
- **微软官方 MarkItDown**：底层仅使用基础启发式规则，会将双栏排版误判为数千字符的**巨型表格表头**，英文单词粘连，无法离线提取插图，公式全部损坏。
- **纯文本/基础 PyMuPDF**：虽然版面流较好，但论文中的**数学公式会被切片成数十张破碎的小图片**，无法作为文本渲染，污染插图目录。
- **大模型方案 (Nougat / MinerU)**：虽然效果好，但动辄需要数十 GB 显存与繁重的 CUDA 依赖环境，普通办公或轻薄本难以快速本地运行。

**Paper2MD** 提供了一个**极速、轻量、高保真**的解决方案：
1. **智能版面解构**：基于 PyMuPDF 布局分析引擎，完美还原双栏阅读流，消除伪表格与文本粘连。
2. **公式转写与自动清理**：内置轻量级 ONNX 数学公式识别模型（**RapidLaTeXOCR**），单公式 0.3 秒识别，自动将公式转换为可直接渲染的 `$$ ... $$` KaTeX/MathJax 语法，并**自动清理公式碎图**。
3. **高清图表提取**：仅提取正文中的真实科学图表与机理图，保存在规范命名的插图文件夹中，并在 Markdown 中自动建立相对路径引用。

---

## 📊 Feature Comparison (效果对比)

| 特性 | Microsoft MarkItDown | PyMuPDF4LLM 原生 | **Paper2MD (本项目)** |
| :--- | :--- | :--- | :--- |
| **双栏排版还原** | ❌ 错乱为几十列空表格 | ✅ 自然段落与小节 | ✅ **自然段落与小节** |
| **文字粘连 (Word Gluing)** | ❌ 严重粘字 | ✅ 正常单词间距 | ✅ **正常单词间距** |
| **学术插图提取** | ❌ 离线为 0 张 (需云端 API) | ⚠️ 混杂公式与插图 | ✅ **提取真实高清图表 (200+ DPI)** |
| **数学公式处理** | ❌ 乱码或丢失 | ⚠️ 导出为 PNG 图片切片 | ✅ **直接识别为 LaTeX `$$...$$` 语法** |
| **Obsidian/渲染器兼容** | ❌ 无法阅读 | ⚠️ 满屏公式小碎图 | ✅ **公式开箱即完美渲染** |
| **运行开销** | 极轻 (但质量差) | 极轻 (~2s) | **极轻 (~5-10s, 无需大显存)** |

---

## 📦 Installation (安装教程)

Paper2MD 支持在 **Windows**、**Arch Linux / EndeavourOS**、**Ubuntu / Debian** 以及 **macOS** 上一键部署。

### 方式一：推荐通过 `pipx` 安装（全平台通用，无需折腾虚拟环境）

`pipx` 可以将 Python 命令行工具自动隔离安装并直接注册到系统的全局环境变量中，在 **Arch / EndeavourOS（避免 PEP 668 报错）** 和 **Windows** 上最推荐：

#### 1. 安装 pipx
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
*(运行 `pipx ensurepath` 后请重启终端使环境变量生效)*

#### 2. 一键安装 Paper2MD
```bash
pipx install git+https://github.com/<your-username>/paper2md.git
```
安装完成后，在终端直接输入 `paper2md` 即可全局运行！

---

### 方式二：标准 `pip` 安装

如果你更习惯在已有的虚拟环境或全局 Python 环境中安装：

```bash
# 直接从 GitHub 仓库安装
pip install git+https://github.com/<your-username>/paper2md.git

# 或者克隆本仓库到本地后安装（开发模式）
git clone https://github.com/<your-username>/paper2md.git
cd paper2md
pip install -e .
```

> **Arch Linux / EndeavourOS 用户提示**：  
> 若直接在系统 Python 下使用 `pip install` 提示 `externally-managed-environment`，建议先创建虚拟环境：  
> `python -m venv ~/.local/share/paper2md-env`  
> `source ~/.local/share/paper2md-env/bin/activate`  
> 然后再执行 `pip install .` 即可。

---

## 🚀 Usage (使用说明)

### 1. 命令行调用 (CLI)

```bash
# 转换单篇学术文献（自动在同目录下生成 .md 文件与 _figures 文件夹）
paper2md "path/to/paper.pdf"

# 批量转换当前目录下的所有 PDF 文件
paper2md .

# 批量转换指定目录下的所有 PDF 文件
paper2md "D:/Literature/My_Papers"

# 自定义插图导出分辨率（默认 200 DPI，高清论文建议 300）
paper2md "paper.pdf" --dpi 300

# 纯文字/图表提取模式（跳过公式 OCR 加快速度）
paper2md "paper.pdf" --no-ocr
```

### 2. Python 模块调用 (Python API)

你也可以在自己的脚本或爬虫/文献管理工作流中直接调用：

```python
from paper2md import convert_pdf_to_md

# 转换论文并返回生成的 markdown 路径
md_path = convert_pdf_to_md(
    pdf_path="path/to/paper.pdf",
    output_md_path="output.md",      # 可选，默认同名
    dpi=200,                         # 图片分辨率
    enable_formula_ocr=True          # 是否开启公式转 LaTeX
)

print(f"Conversion complete: {md_path}")
```

---

## 📐 转换效果展示 (Formula Example)

被识别转换后的公式将以标准数学块呈现，Obsidian、Typora、VS Code 或 GitHub Markdown 会自动将其渲染为矢量排版：

```markdown
The reaction rate follows Fick’s first law:

$$
J = -D \frac{\partial c}{\partial z} \tag{12}
$$

The Stokes-Einstein equation is applied to estimate diffusion:

$$
D = \frac{k_{\mathrm{B}} T}{6\pi \eta R} \tag{14}
$$
```

---

## 🛠️ 依赖说明 (Dependencies)

* [PyMuPDF](https://github.com/pymupdf/PyMuPDF) & [PyMuPDF4LLM](https://github.com/pymupdf/pymupdf4llm): 核心排版解构与图文提取。
* [RapidLaTeXOCR](https://github.com/RapidAI/RapidLaTeXOCR): 极速离线数学公式识别引擎（基于 ONNXRuntime）。
* `opencv-python-headless`: 图像预处理后端（无 GUI 依赖，适配无头服务器与各类 Linux 发行版）。

---

## 📄 License

本项目基于 [MIT License](LICENSE) 开源。欢迎 Star、Fork 与提 Issue！
