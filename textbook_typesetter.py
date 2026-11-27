#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
textbook_typesetter.py - 统编高中语文教科书出版级排版工具 (Typst 架构主驱动程序)
================================================================================
全面基于专业排版引擎 Typst 构建，1:1 像素级复刻教育部统编高中语文教科书印刷标准。
================================================================================
"""

import os
import sys
import re
import argparse
import subprocess
import yaml
from typing import Dict, Any, List, Tuple

from cjk_layout_engine import (
    format_cjk_paragraph_to_lines,
    run_paging_engine,
    id_to_rope_or_sym,
    split_page_footnotes_balanced,
    CIRCLE_SYMBOLS,
    PAGE_HEIGHT,
    TOP_MARGIN,
    BODY_LINE_HEIGHT,
    HEADER_HEIGHT,
    SAFETY_GAP,
    SEP_LINE_HEIGHT,
    LINE_TO_FN_GAP,
    FN_LINE_HEIGHT
)


def _parse_fn_key_to_id(key: Any) -> int:
    """将词典键（整数、数字字符串、带圈序号、[n]）统一转换为整数 ID"""
    if isinstance(key, int):
        return key
    s = str(key).strip()
    if s.isdigit():
        return int(s)
    if s in CIRCLE_SYMBOLS:
        return CIRCLE_SYMBOLS.index(s) + 1
    m = re.match(r'^\[(\d+)\]$', s)
    if m:
        return int(m.group(1))
    return 1


def _format_fn_dict_entry(val: Any) -> str:
    """将词典值转换为标准注释文本（若为 {词条: 释义} 映射则自动添加 〔〕）"""
    if isinstance(val, dict) and len(val) > 0:
        term, desc = next(iter(val.items()))
        term_str = str(term).strip()
        desc_str = str(desc).strip()
        if term_str.startswith('〔') and term_str.endswith('〕'):
            return f"{term_str}{desc_str}"
        return f"〔{term_str}〕{desc_str}"
    if isinstance(val, (list, tuple)) and len(val) >= 2:
        term_str = str(val[0]).strip()
        desc_str = str(val[1]).strip()
        if term_str.startswith('〔') and term_str.endswith('〕'):
            return f"{term_str}{desc_str}"
        return f"〔{term_str}〕{desc_str}"
    return str(val).strip()


def parse_markdown_lesson(md_path: str) -> Tuple[Dict[str, Any], str, Dict[int, Tuple[str, str]], str]:
    """
    解析课文 Markdown 文件，提取 Frontmatter、正文、字词出处注释、学习提示
    支持灵活的标题格式（如 ## 正文 / ### 【课文正文】 / 省略正文标题）
    注释支持 YAML/Python 词典格式，自动为 {词条: 释义} 添加 〔〕
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    meta = {}
    content = raw_text
    if raw_text.lstrip().startswith('---'):
        parts = re.split(r'^---\s*$', raw_text.lstrip(), maxsplit=2, flags=re.MULTILINE)
        if len(parts) >= 3 and parts[0].strip() == '':
            meta = yaml.safe_load(parts[1]) or {}
            content = parts[2].strip()

    # 剥离 HTML 注释
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

    # 按章节标题灵活切分（不再强绑定 ### 【...】 固定写法）
    sections = {'body': [], 'footnotes': [], 'hint': []}
    current_sec = 'body'

    re_body_hdr = re.compile(r'^#{1,6}\s*【?(?:课文)?正文】?\s*$')
    re_fn_hdr = re.compile(r'^#{1,6}\s*【?(?:课文字词与出处|课文字词|字词与出处|字词|出处)?注释】?\s*$')
    re_hint_hdr = re.compile(r'^#{1,6}\s*【?学习提示】?\s*$')

    for line in content.splitlines():
        stripped = line.strip()
        if re_body_hdr.match(stripped):
            current_sec = 'body'
            continue
        if re_fn_hdr.match(stripped):
            current_sec = 'footnotes'
            continue
        if re_hint_hdr.match(stripped):
            current_sec = 'hint'
            continue
        sections[current_sec].append(line)

    def _clean_hr(lines_list: List[str]) -> str:
        text = '\n'.join(lines_list).strip()
        text = re.sub(r'^\s*---\s*$', '', text, flags=re.MULTILINE).strip()
        return text

    body_text = _clean_hr(sections['body'])
    hint_text = _clean_hr(sections['hint'])
    fn_raw = _clean_hr(sections['footnotes'])

    # 提取注释（优先支持 Frontmatter footnotes 或 注释区词典格式，兼容旧版逐行格式）
    fn_dict: Dict[int, Tuple[str, str]] = {}

    raw_fn_mapping = None
    if isinstance(meta.get('footnotes'), dict):
        raw_fn_mapping = meta['footnotes']
    elif fn_raw:
        # 剥离可选的 ```yaml / ```python / ``` 代码块围栏
        fn_clean = re.sub(r'^```[a-zA-Z]*\s*\n', '', fn_raw.strip())
        fn_clean = re.sub(r'\n```\s*$', '', fn_clean).strip()
        try:
            loaded = yaml.safe_load(fn_clean)
            if isinstance(loaded, dict):
                raw_fn_mapping = loaded
        except Exception:
            raw_fn_mapping = None

    if raw_fn_mapping is not None:
        for k, v in raw_fn_mapping.items():
            fid = _parse_fn_key_to_id(k)
            sym = CIRCLE_SYMBOLS[fid - 1] if 1 <= fid <= len(CIRCLE_SYMBOLS) else f"[{fid}]"
            txt = _format_fn_dict_entry(v)
            fn_dict[fid] = (sym, txt)
    elif fn_raw:
        # 向后兼容旧版逐行注释格式
        for line in fn_raw.splitlines():
            line = line.strip()
            if not line:
                continue
            m = re.match(r'^([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚㉛㉜㉝㉞㉟㊱㊲㊳㊴㊵㊶㊷㊸㊹㊺㊻㊼㊽㊾㊿]|\[\d+\])\s*(.*)', line)
            if m:
                sym, txt = m.group(1), m.group(2)
                fid = _parse_fn_key_to_id(sym)
                fn_dict[fid] = (sym, txt)

    return meta, body_text, fn_dict, hint_text


def convert_line_to_typst_markup(line_str: str, local_fn_map: Dict[int, int] = None) -> str:
    """
    将包含 ①②③ 或 [51] 的文字转换为 Typst 的 #fn-mark(...) 宏
    若提供 local_fn_map，则将原始全局注释 ID 转换为当页从 1 开始的局部编号
    """
    out = []
    i = 0
    while i < len(line_str):
        ch = line_str[i]
        if ch in CIRCLE_SYMBOLS:
            orig_fid = CIRCLE_SYMBOLS.index(ch) + 1
            fid = local_fn_map.get(orig_fid, orig_fid) if local_fn_map else orig_fid
            out.append(f"#fn-mark({fid})")
            i += 1
            continue
        m = re.match(r'\[(\d+)\]', line_str[i:])
        if m:
            orig_fid = int(m.group(1))
            fid = local_fn_map.get(orig_fid, orig_fid) if local_fn_map else orig_fid
            out.append(f"#fn-mark({fid})")
            i += len(m.group(0))
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def generate_typst_code(
    meta: Dict[str, Any],
    pages: List[Dict[str, Any]],
    fn_dict: Dict[int, Tuple[str, str]],
    hint_text: str,
    start_page: int = None,
    book_title: str = None,
    unit: str = None
) -> str:
    """
    根据分页与几何数据生成出版级 Typst 排版源码
    """
    # 优先使用显式传入的参数，其次读取 Markdown Frontmatter，最后采用缺省值
    unit = unit if unit is not None else meta.get('unit', '')
    book_title = book_title if book_title is not None else meta.get('book_title', '必修上册')
    start_page = int(start_page if start_page is not None else meta.get('start_page', 1))
    title = meta.get('title', '')
    author = meta.get('author', '')
    lesson_num = meta.get('lesson_num', None)
    subtitle = meta.get('subtitle', None)

    lines_out = [
        '#import "textbook.typ": *',
        '',
        f'#show: textbook-doc.with(',
        f'  unit: "{unit}",',
        f'  book-title: "{book_title}",',
        f'  start-page: {start_page},',
        f')',
        ''
    ]

    for p_idx, page in enumerate(pages):
        page_num = page["page_num"]
        real_page = start_page + page_num - 1
        is_odd = (real_page % 2 == 1)
        is_first_page = (p_idx == 0)

        if not is_first_page:
            lines_out.append('#pagebreak()')
            lines_out.append('')

        # 建立当页注释的局部重新编号映射（统编教科书出版规范：每页严格从序号 1 / ① 开始）
        fn_ids = page.get("fn_ids", [])
        local_fn_map = {orig_fid: (l_idx + 1) for l_idx, orig_fid in enumerate(fn_ids)}

        # 首页渲染标题区
        if is_first_page:
            num_param = f'num: {lesson_num},' if lesson_num else ''
            sub_param = f'subtitle: "{subtitle}",' if subtitle else ''
            author_param = f'author: "{author}",' if author else ''
            title_fn_local = local_fn_map.get(1, 1)
            lines_out.append(f'#lesson-header(')
            if num_param: lines_out.append(f'  {num_param}')
            lines_out.append(f'  title: "{title}",')
            lines_out.append(f'  title-fn: {title_fn_local},')
            if sub_param: lines_out.append(f'  {sub_param}')
            if author_param: lines_out.append(f'  {author_param}')
            lines_out.append(f'  is-odd: {str(is_odd).lower()}')
            lines_out.append(')')
            lines_out.append('')

        # 渲染正文行（角标转换为当页局部序号）
        for line_str, indent, is_last in page["lines"]:
            markup = convert_line_to_typst_markup(line_str, local_fn_map=local_fn_map)
            indent_str = f'indent: {indent}pt, ' if indent > 0.0 else ''
            last_str = 'is-last: true' if is_last else ''
            args_list = [a for a in [indent_str.strip(', '), last_str] if a]
            args = (", ".join(args_list))
            if args:
                lines_out.append(f'#bl({args})[{markup}]')
            else:
                lines_out.append(f'#bl()[{markup}]')

        # 渲染当页双栏页底注释（方案一：绝对等分平衡，左栏与右栏物理行绑定）
        if fn_ids:
            fn_entries = []
            for orig_fid in fn_ids:
                if orig_fid in fn_dict:
                    sym, txt = fn_dict[orig_fid]
                    local_id = local_fn_map[orig_fid]
                    rope_sym = id_to_rope_or_sym(local_id)
                    fn_entries.append((rope_sym, txt))

            left_lines, right_lines, max_cols = split_page_footnotes_balanced(fn_entries)
            fn_block_h = max_cols * FN_LINE_HEIGHT
            FN_BOTTOM_ANCHOR = 780.0
            fn_top_y = FN_BOTTOM_ANCHOR - fn_block_h
            sep_y = fn_top_y - LINE_TO_FN_GAP
            sep_dy = sep_y - TOP_MARGIN

            lines_out.append('')
            lines_out.append(f'// 第 {page_num} 页页底双栏注释 (方案一：绝对等分平衡，左栏 {len(left_lines)} 行, 右栏 {len(right_lines)} 行)')
            lines_out.append(f'#place(top + left, dx: 0pt, dy: {sep_dy:.1f}pt)[')
            lines_out.append(f'  #footnote-section((')
            for l in left_lines:
                sym_prop = f'sym: text(font: font-rope)[#"{l["rope_sym"]}"], ' if (l["is_first"] and (l["rope_sym"].startswith("@") or l["rope_sym"].startswith("#"))) else (f'sym: text(font: font-rope)[{l["rope_sym"]}], ' if l["is_first"] else '')
                first_prop = 'is-first: true, ' if l["is_first"] else ''
                last_prop = 'is-last: true, ' if l["is_entry_last"] else ''
                lines_out.append(f'    fn-line({sym_prop}{first_prop}{last_prop}body: fn-content[{l["content"]}]),')
            lines_out.append(f'  ), (')
            for l in right_lines:
                sym_prop = f'sym: text(font: font-rope)[#"{l["rope_sym"]}"], ' if (l["is_first"] and (l["rope_sym"].startswith("@") or l["rope_sym"].startswith("#"))) else (f'sym: text(font: font-rope)[{l["rope_sym"]}], ' if l["is_first"] else '')
                first_prop = 'is-first: true, ' if l["is_first"] else ''
                last_prop = 'is-last: true, ' if l["is_entry_last"] else ''
                lines_out.append(f'    fn-line({sym_prop}{first_prop}{last_prop}body: fn-content[{l["content"]}]),')
            lines_out.append(f'  ), is-odd: {str(is_odd).lower()})')
            lines_out.append(']')

        # 渲染学习提示
        if page.get("has_hint") and hint_text:
            lines_out.append('')
            lines_out.append(f'#hint-section(is-odd: {str(is_odd).lower()})[')
            for hp in hint_text.split('\n\n'):
                hp = hp.strip()
                if hp:
                    lines_out.append(hp)
                    lines_out.append('')
            lines_out.append(']')

    return '\n'.join(lines_out)


def find_typst_executable() -> str:
    """寻找工作区或系统环境中的 typst 可执行文件"""
    local_typst = os.path.join(os.path.dirname(__file__), "typst", "typst.exe")
    if os.path.exists(local_typst):
        return local_typst
    local_typst_unix = os.path.join(os.path.dirname(__file__), "typst", "typst")
    if os.path.exists(local_typst_unix):
        return local_typst_unix
    # 查找 PATH
    import shutil
    p = shutil.which("typst")
    if p:
        return p
    return "typst"


def export_pdf_preview(pdf_path: str, output_dir: str = None, dpi: int = 150):
    """使用 pymupdf 导出高保真预览 PNG 图片"""
    try:
        import fitz
    except ImportError:
        print("[!] 警告: 未安装 pymupdf，跳过预览图导出")
        return

    if output_dir is None:
        output_dir = os.path.dirname(pdf_path) or "."

    doc = fitz.open(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi)
        img_name = f"{base_name}_preview_p{i+1}.png"
        img_path = os.path.join(output_dir, img_name)
        pix.save(img_path)
        print(f"[+] 导出高清页面预览: {img_path}")


def typeset_markdown_file(
    md_path: str,
    output_pdf: str,
    font_path: str = "./fonts",
    preview: bool = False,
    start_page: int = None,
    book_title: str = None,
    unit: str = None
) -> bool:
    """对单个 Markdown 文件执行全套排版、代码生成与 Typst 编译"""
    if not os.path.exists(md_path):
        print(f"[-] 错误: 输入文件不存在 {md_path}")
        return False

    print(f"[*] 正在解析课文文件: {md_path} ...")
    meta, body_text, fn_dict, hint_text = parse_markdown_lesson(md_path)

    # 1. 对正文段落进行 31 字网格分行
    paras = [p.strip() for p in body_text.split('\n\n') if p.strip()]
    all_lines = []
    for p in paras:
        clean_p = "".join(l.strip() for l in p.splitlines() if l.strip())
        is_hang = clean_p.startswith("《") or clean_p.startswith("“")
        lines = format_cjk_paragraph_to_lines(clean_p, is_hanging=is_hang)
        all_lines.extend(lines)

    # 2. 运行原子捆绑单调贪心分页引擎
    has_hint = bool(hint_text.strip())
    pages = run_paging_engine(all_lines, fn_dict, title_fn_id=1, has_hint=has_hint)

    print(f"[+] 分页规划完成: 共 {len(pages)} 页")
    for p in pages:
        print(f"    - 第 {p['page_num']} 页: {len(p['lines'])} 行正文, {len(p['fn_ids'])} 条注释" + (", 含【学习提示】" if p['has_hint'] else ""))

    # 3. 生成 Typst 源码
    typ_content = generate_typst_code(
        meta=meta,
        pages=pages,
        fn_dict=fn_dict,
        hint_text=hint_text,
        start_page=start_page,
        book_title=book_title,
        unit=unit
    )
    base_name = os.path.splitext(os.path.basename(md_path))[0]
    out_dir = os.path.dirname(output_pdf) or "."
    typ_path = os.path.join(out_dir, f"{base_name}_generated.typ")
    with open(typ_path, "w", encoding="utf-8") as f:
        f.write(typ_content)
    print(f"[+] 生成出版级 Typst 源码: {typ_path}")

    # 4. 调用 typst compile
    typst_bin = find_typst_executable()
    cmd = [typst_bin, "compile", "--font-path", font_path, typ_path, output_pdf]
    print(f"[*] 正在调用 Typst 编译器: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        print(f"[-] Typst 编译失败:\n{res.stderr}")
        return False

    print(f"🎉 成功生成出版级教材 PDF: {output_pdf}")

    # 5. 若请求 preview，导出图片
    if preview:
        export_pdf_preview(output_pdf, out_dir)

    return True


def main():
    parser = argparse.ArgumentParser(description="统编高中语文教科书出版级排版工具 (Typst 驱动引擎)")
    parser.add_argument("input", help="输入的 Markdown 课文文件路径")
    parser.add_argument("-o", "--output", help="输出的出版级 PDF 文件路径")
    parser.add_argument("-p", "--start-page", type=int, default=None, help="起始页码 (如 51, 62；未输入则读取课文 frontmatter，缺省为 1)")
    parser.add_argument("-b", "--book-title", default=None, help="页脚书册名称 (如 '必修上册'；未输入则读取 frontmatter，缺省为 '必修上册')")
    parser.add_argument("-u", "--unit", default=None, help="页脚单元名称 (如 '第二单元'；未输入则读取 frontmatter，缺省为空)")
    parser.add_argument("--font-path", default="./fonts", help="正版字库所在目录 (默认 ./fonts)")
    parser.add_argument("--preview", action="store_true", help="是否通过 pymupdf 导出高保真预览 PNG")

    args = parser.parse_args()

    out_pdf = args.output
    if not out_pdf:
        base = os.path.splitext(os.path.basename(args.input))[0]
        out_pdf = f"output_{base}.pdf"

    success = typeset_markdown_file(
        md_path=args.input,
        output_pdf=out_pdf,
        font_path=args.font_path,
        preview=args.preview,
        start_page=args.start_page,
        book_title=args.book_title,
        unit=args.unit
    )
    sys.exit(0 if success else 1)

    out_pdf = args.output
    if not out_pdf:
        base = os.path.splitext(os.path.basename(args.input))[0]
        out_pdf = f"output_{base}.pdf"

    success = typeset_markdown_file(
        md_path=args.input,
        output_pdf=out_pdf,
        font_path=args.font_path,
        preview=args.preview
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


