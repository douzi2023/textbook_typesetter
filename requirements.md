# 统编高中语文教科书排版引擎 - 依赖与字体配置指南 (Requirements)

为了完全重现教育部统编高中语文教科书（人教版）像素级出版标准，本项目高度依赖特定的**高保真中文字库**、**Typst 排版编译器**以及 **Python 环境**。

> [!WARNING]
> **字体版权合规声明**：
> 因商业字库版权保护，本公开仓库**未打包附带任何商用中文字体文件与 Typst 预编译可执行文件**。
> 若在缺失上述字体或编译器的环境下直接运行，Typst 的回退字体机制（Font Fallback）将导致：
> 1. 汉字字形与字距发生偏移，严格的 31 字字格网格无法对齐；
> 2. 注释中的汉语拼音注音声调字母（如 *pén*, *chāng*, *gǔ*）丢失或显示为方块豆腐块；
> 3. 带圈注释序号（1~99）无法正确定位与渲染；
> 4. 正文与页底双栏注释的高度与间距计算出现偏差。
>
> **因此，在正式排版前，请务必根据下文指南补齐字库与运行依赖。**

---

## 一、所需字库清单 (Fonts Configuration)

请在项目根目录下创建 `fonts` 文件夹（即 `./fonts/`），并将以下 8 种字体文件重命名并放入该目录中：

| 推荐文件名 | 字体家族名称 (Typst PostScript Name) | 官方书册对应用途 | 字体说明与获取建议 |
| :--- | :--- | :--- | :--- |
| `FZSSK.TTF` | `FZShuSong-Z01` | **正文汉字、注释正文、页脚文本** | 方正书宋_GBK，统编教材核心正文字体，定义 31 字/行版心物理网格。 |
| `FZZHUNYSK.TTF` | `FZYaSong-M-GBK` | **课文大标题、副标题、序号大字** | 方正准雅宋_GBK，人教版标题专文字体。 |
| `FZFSK.TTF` | `FZFangSong-Z02` | **课文作者署名** | 方正仿宋_GBK，正文下方居中作者姓名排版。 |
| `FZKTK.TTF` | `FZKai-Z03` | **【学习提示】正文** | 方正楷体_GBK，课文末尾三段式学习任务正文。 |
| `FZLTZHK.TTF` | `FZLanTingHei-DB-GBK` | **【学习提示】徽标小标题** | 方正兰亭中黑_GBK，提示部分徽标右侧“学习提示”四字。 |
| `FZZDXJW.TTF` | `FZZhongDengXian-Z07S` | **奇偶页页脚页码数字** | 方正中等线简体（或系统等线体），页脚阿拉伯数字。 |
| `rope.ttf` | `RBNQWV+RopeSequenceNumberST-R` | **带圈注释序号 (1~99)** | 人教版教材专用带圈序号字库，支持正文右上角标与注释首序号。 |
| `neu-xt.ttf` | `NEU-XT` | **注释专用汉语拼音** | 教材专用拼音字库，内置完整汉语拼音声调符号。 |

> [!NOTE]
> - **注释数字**：注释中的出版年份、生卒年等连续阿拉伯数字在模板中自动绑定西文字体 `Times New Roman`（Windows / macOS / Linux 操作系统普遍自带，无需放入 `./fonts/`）。
> - **字体路径自定义**：若您的字库保存在其他目录，可通过命令行参数 `--font-path <路径>` 进行指定。

---

## 二、Typst 排版编译器依赖 (Typst Compiler)

本项目采用现代出版级排版引擎 [Typst](https://typst.app/) 进行高精度矢量排版与 PDF 渲染。

- **推荐版本**：Typst v0.13.0 ~ v0.15.1+

### 安装与部署方式（二选一）：

#### 方式 A：放置在项目根目录（推荐，开箱即用）
1. 从 [Typst 官方 GitHub Releases](https://github.com/typst/typst/releases) 下载适用于您操作系统的最新发行版压缩包（如 Windows 选择 `typst-x86_64-pc-windows-msvc.zip`）。
2. 解压后，将 `typst.exe`（Linux/macOS 为 `typst`）放置在项目根目录的 `typst` 文件夹下：
   ```
   textbook_typesetter/
   └── typst/
       └── typst.exe  (或 typst)
   ```
   主程序会自动优先探测该路径并调用。

#### 方式 B：全局系统环境变量（System PATH）
通过官方包管理器安装并将其加入系统 `PATH` 环境变量中：
- **Windows (Winget)**:
  ```powershell
  winget install --id Typst.Typst
  ```
- **macOS (Homebrew)**:
  ```bash
  brew install typst
  ```
- **Rust (Cargo)**:
  ```bash
  cargo install --locked typst-cli
  ```
安装后可在终端执行 `typst --version` 验证是否成功。

---

## 三、Python 环境依赖 (Python Environment)

本项目要求 **Python 3.8 及以上版本**。

### 1. 核心运行依赖
执行以下命令安装运行主排版程序所需的依赖库：

```bash
pip install pymupdf Pillow numpy
```

- **`pymupdf` (fitz)**：用于解析 PDF、计算实际渲染元素物理坐标，以及在开启 `--preview` 时导出高精度页面预览图。
- **`Pillow` (PIL)**：处理图像、画布与徽标尺寸适配。
- **`numpy`**：矩阵数值计算与版心坐标校准。

### 2. 自动化审查比对工具依赖（可选）
若需要使用 `image_diff_inspector.py` 进行像素级 SSIM / PSNR 机械审查比对，需额外安装：

```bash
pip install scikit-image opencv-python
```

---

## 四、部署就绪验证 (Quick Check)

当字库文件放入 `./fonts/` 且 Typst 配置就绪后，可通过以下命令测试排版流程是否通畅：

```bash
# 执行测试课文排版并输出高清预览图
python textbook_typesetter.py gongjiang_article.md --preview
```

执行成功后，终端将输出：
```
[*] 正在解析课文文件: gongjiang_article.md ...
[+] 分页规划完成: 共 2 页
    - 第 1 页: 24 行正文, 3 条注释
    - 第 2 页: 10 行正文, 0 条注释, 含【学习提示】
[+] 生成出版级 Typst 源码: .\gongjiang_article_generated.typ
[*] 正在调用 Typst 编译器: ...
🎉 成功生成出版级教材 PDF: output_gongjiang_article.pdf
[+] 导出高清页面预览: .\output_gongjiang_article_preview_p1.png
[+] 导出高清页面预览: .\output_gongjiang_article_preview_p2.png
```
可在生成的预览图片中直观核验字体、版心与双栏注释是否符合规范。
