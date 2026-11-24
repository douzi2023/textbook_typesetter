#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cjk_layout_engine.py - 统编高中语文教科书出版级排版核心几何与分页引擎
================================================================================
负责：
1. 31 字字格网格断行（标点挤压、段首悬挂、避头尾禁则）
2. 双栏注释高度平衡折算（单栏 215.6pt，9.0pt 书宋）
3. 原子捆绑单调贪心分页算法（绝对禁止注释跨页顺延，零震荡收敛）
================================================================================
"""

import re
import math
from typing import List, Dict, Tuple, Any

PAGE_HEIGHT = 841.89
TOP_MARGIN = 60.0
BOTTOM_MARGIN = 50.0
# 统编高中语文教科书 A4 版心出版级黄金阈值 (728.0 pt)
USABLE_HEIGHT = 728.0  # 严格对齐 24 行正文+双栏注释容量极限

BODY_LINE_HEIGHT = 21.0       # 正文严格 21.0 pt
HEADER_HEIGHT = 150.9         # 首页课文主标题+序号+作者占位
SAFETY_GAP = 28.2             # 正文末行与注释分割线黄金安全间隙
SEP_LINE_HEIGHT = 0.25        # 分割线粗细
LINE_TO_FN_GAP = 10.1         # 分割线与当页最上方注释文字顶部间距
FN_LINE_HEIGHT = 14.8         # 注释单行行距 14.8 pt
FN_COL_WIDTH = 215.6          # 注释单栏宽度
HINT_TOTAL_HEIGHT = 274.0     # 学习提示（留白41pt + 徽标虚线23pt + 楷体3段约210pt）

CIRCLE_SYMBOLS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚㉛㉜㉝㉞㉟㊱㊲㊳㊴㊵㊶㊷㊸㊹㊺㊻㊼㊽㊾㊿"
NO_LINE_START = set("，。、；：？！’”》）〕…—")
NO_LINE_END = set("‘“《（〔")
DOUBLE_PUNC_PAIRS = {"：“", "。”", "、“", "、”", "，”", "”，", "；“", "？”", "！”", "〔《", "》〕", "》，", "。“"}


def sym_to_id(sym: str) -> int:
    """带圈序号转换为整数 ID"""
    if sym in CIRCLE_SYMBOLS:
        return CIRCLE_SYMBOLS.index(sym) + 1
    m = re.match(r'\[(\d+)\]', sym)
    if m:
        return int(m.group(1))
    return 1


def id_to_rope_or_sym(fn_id: int) -> str:
    """转换为 Rope ASCII 字符 (1~19 -> a~s, 20~23 -> t~w, 24~29 -> @4~@9, 30~39 -> #0~#9)"""
    if 1 <= fn_id <= 19:
        return "abcdefghijklmnopqrs"[fn_id - 1]
    if 20 <= fn_id <= 23:
        return "tuvw"[fn_id - 20]
    if 24 <= fn_id <= 29:
        return f"@{fn_id - 20}"
    if 30 <= fn_id <= 39:
        return f"#{fn_id - 30}"
    if 1 <= fn_id <= len(CIRCLE_SYMBOLS):
        return CIRCLE_SYMBOLS[fn_id - 1]
    return f"[{fn_id}]"


def measure_token_width(tok: str) -> float:
    """测算 token 物理排版宽度 (9pt 书宋基准: 汉字9pt, 西文字母/数字4.5pt)"""
    w = 0.0
    for ch in tok:
        if ord(ch) < 128:
            w += 4.5
        elif '\u00C0' <= ch <= '\u024F' or '\u1E00' <= ch <= '\u1EFF':
            w += 4.5
        else:
            w += 9.0
    return w


def format_footnote_entry_to_lines(rope_sym: str, text: str) -> List[Dict[str, Any]]:
    """
    将单条注释格式化为若干 215.6pt 栏宽的物理排版行
    返回: list of { 'is_first': bool, 'rope_sym': str, 'content': str, 'is_entry_last': bool }
    """
    tokens = []
    i = 0
    while i < len(text):
        m = re.match(r'[A-Za-z0-9\u00C0-\u024F\u1E00-\u1EFF]+', text[i:])
        if m:
            tokens.append(m.group(0))
            i += len(m.group(0))
            continue
        tokens.append(text[i])
        i += 1

    lines = []
    is_first = True
    cur_tokens = []
    cur_w = 0.0
    cap = FN_COL_WIDTH - 13.5  # 首行预留 13.5pt 给带圈序号与间距

    idx = 0
    while idx < len(tokens):
        tok = tokens[idx]
        w = measure_token_width(tok)

        if cur_tokens and len(tok) == 1 and len(cur_tokens[-1]) == 1:
            if (cur_tokens[-1] + tok) in DOUBLE_PUNC_PAIRS:
                w -= 4.5

        if cur_w + w > cap + 0.01:
            if len(tok) == 1 and tok in NO_LINE_START:
                if cur_tokens:
                    pulled = cur_tokens.pop()
                    lines.append({
                        "is_first": is_first,
                        "rope_sym": rope_sym if is_first else "",
                        "content": "".join(cur_tokens),
                        "is_entry_last": False
                    })
                    cur_tokens = [pulled, tok]
                    cur_w = measure_token_width(pulled) + w
                    is_first = False
                    cap = FN_COL_WIDTH
                    idx += 1
                    continue
            elif cur_tokens and len(cur_tokens[-1]) == 1 and cur_tokens[-1] in NO_LINE_END:
                last = cur_tokens.pop()
                lines.append({
                    "is_first": is_first,
                    "rope_sym": rope_sym if is_first else "",
                    "content": "".join(cur_tokens),
                    "is_entry_last": False
                })
                cur_tokens = [last]
                cur_w = measure_token_width(last)
                is_first = False
                cap = FN_COL_WIDTH
                continue
            else:
                lines.append({
                    "is_first": is_first,
                    "rope_sym": rope_sym if is_first else "",
                    "content": "".join(cur_tokens),
                    "is_entry_last": False
                })
                cur_tokens = []
                cur_w = 0.0
                is_first = False
                cap = FN_COL_WIDTH
                continue

        cur_tokens.append(tok)
        cur_w += w
        idx += 1

    if cur_tokens:
        lines.append({
            "is_first": is_first,
            "rope_sym": rope_sym if is_first else "",
            "content": "".join(cur_tokens),
            "is_entry_last": True
        })

    if lines:
        lines[-1]["is_entry_last"] = True

    return lines


def split_page_footnotes_balanced(fn_entries: List[Tuple[str, str]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    """
    将当页的所有注释条目预排切分为物理行，并等分为左栏与右栏两段 (方案一核心算法)
    返回: (left_lines, right_lines, max_column_lines)
    """
    all_lines = []
    for rope_sym, txt in fn_entries:
        entry_lines = format_footnote_entry_to_lines(rope_sym, txt)
        all_lines.extend(entry_lines)

    total_m = len(all_lines)
    left_count = math.ceil(total_m / 2.0)
    left_lines = all_lines[:left_count]
    right_lines = all_lines[left_count:]

    return left_lines, right_lines, left_count


def measure_footnote_lines(txt: str) -> int:
    """根据物理分行器测算单条注释占用的真实行数"""
    return len(format_footnote_entry_to_lines("", txt))


def format_cjk_paragraph_to_lines(text: str, is_hanging: bool = False) -> List[Tuple[str, float, bool]]:
    """
    将中文自然段落按照 31 字字格网格切分为排版行
    返回: list of (line_content_with_tags, indent_pt, is_last)
    """
    tokens = []
    i = 0
    while i < len(text):
        if text[i] in CIRCLE_SYMBOLS:
            tokens.append(('fn', text[i]))
            i += 1
            continue
        m = re.match(r'\[\d+\]', text[i:])
        if m:
            tokens.append(('fn', m.group(0)))
            i += len(m.group(0))
            continue
        tokens.append(('char', text[i]))
        i += 1

    lines = []
    cur_tokens = []
    cur_cells = 0.0
    is_first = True
    first_indent = 18.0 if is_hanging else 24.0
    cap = 31.0 - (1.5 if is_hanging else 2.0)

    idx = 0
    while idx < len(tokens):
        ttype, tval = tokens[idx]
        # 角标在统编教材字格网格中占用 1.0 个标准字格（包含字形与字距），确保行宽严格不超过 372.0pt！
        cost = 1.0

        if ttype == 'char' and cur_tokens:
            prev_t, prev_v = cur_tokens[-1]
            if prev_t == 'char' and (prev_v + tval) in DOUBLE_PUNC_PAIRS:
                cost = 0.5

        if cur_cells + cost > cap + 0.01:
            # 避头尾禁则
            if ttype == 'char' and tval in NO_LINE_START:
                # 遇到行首禁则标点，当前行无法容纳，将行末 1 个字符回退到下一行带出标点
                if cur_tokens:
                    pulled = cur_tokens.pop()
                    lines.append((cur_tokens, first_indent if is_first else 0.0, False))
                    cur_tokens = [pulled, (ttype, tval)]
                    cur_cells = (0.3 if pulled[0] == 'fn' else 1.0) + cost
                    is_first = False
                    cap = 31.0
                    idx += 1
                    continue
            elif cur_tokens and cur_tokens[-1][1] in NO_LINE_END:
                last = cur_tokens.pop()
                lines.append((cur_tokens, first_indent if is_first else 0.0, False))
                cur_tokens = [last]
                cur_cells = 0.3 if last[0] == 'fn' else 1.0
                is_first = False
                cap = 31.0
                continue

            lines.append((cur_tokens, first_indent if is_first else 0.0, False))
            cur_tokens = []
            cur_cells = 0.0
            is_first = False
            cap = 31.0
            continue

        cur_tokens.append((ttype, tval))
        cur_cells += cost
        idx += 1

    if cur_tokens:
        lines.append((cur_tokens, first_indent if is_first else 0.0, True))

    result = []
    for toks, indent, is_last in lines:
        line_str = "".join(t[1] for t in toks)
        result.append((line_str, indent, is_last))
    return result


def extract_line_fn_ids(line_str: str) -> List[int]:
    """提取排版行中包含的注释 ID"""
    ids = []
    for ch in line_str:
        if ch in CIRCLE_SYMBOLS:
            ids.append(sym_to_id(ch))
    for m in re.finditer(r'\[(\d+)\]', line_str):
        ids.append(int(m.group(1)))
    return ids


def run_paging_engine(
    body_lines: List[Tuple[str, float, bool]],
    fn_dict: Dict[int, Tuple[str, str]],
    title_fn_id: int = 1,
    has_hint: bool = True
) -> List[Dict[str, Any]]:
    """
    原子捆绑单调贪心分页算法核心实现
    严格遵守：正文所引注释全部在当页闭环，严禁跨页顺延！
    """
    pages = []
    current_lines = []
    current_fn_ids = []

    line_idx = 0
    page_num = 1

    while line_idx < len(body_lines):
        line_text, indent, is_last = body_lines[line_idx]
        is_first_page = (page_num == 1)
        header_h = HEADER_HEIGHT if is_first_page else 0.0

        # 当前行自带注释
        line_fns = extract_line_fn_ids(line_text)
        if is_first_page and len(current_lines) == 0 and title_fn_id in fn_dict:
            line_fns = [title_fn_id] + [fid for fid in line_fns if fid != title_fn_id]

        cand_lines = current_lines + [(line_text, indent, is_last)]
        cand_fns = list(dict.fromkeys(current_fn_ids + line_fns))

        body_h = len(cand_lines) * BODY_LINE_HEIGHT

        if cand_fns:
            fn_total_lines = sum(measure_footnote_lines(fn_dict[fid][1]) for fid in cand_fns if fid in fn_dict)
            fn_col_lines = math.ceil(fn_total_lines / 2.0)
            fn_block_h = fn_col_lines * FN_LINE_HEIGHT
            # SAFETY_GAP (28.2pt) 是正文底端与注释文字顶端的总安全间隙（分割线居中于其间）
            fn_total_h = SAFETY_GAP + fn_block_h
        else:
            fn_block_h = 0.0
            fn_total_h = 0.0

        total_h = header_h + body_h + fn_total_h

        # 判定当页是否满版
        if total_h <= USABLE_HEIGHT + 0.5:
            current_lines.append((line_text, indent, is_last))
            current_fn_ids = cand_fns
            line_idx += 1
        else:
            # 熔断！当前页锁定截断
            if not current_lines:
                current_lines.append((line_text, indent, is_last))
                current_fn_ids = cand_fns
                line_idx += 1

            # 计算最终该页的注释高度与分割线位置
            fn_h_final = 0.0
            if current_fn_ids:
                fn_t_lines = sum(measure_footnote_lines(fn_dict[fid][1]) for fid in current_fn_ids if fid in fn_dict)
                fn_col_l = math.ceil(fn_t_lines / 2.0)
                fn_h_final = fn_col_l * FN_LINE_HEIGHT

            pages.append({
                "page_num": page_num,
                "lines": current_lines,
                "fn_ids": current_fn_ids,
                "fn_block_h": fn_h_final,
                "has_hint": False
            })

            page_num += 1
            current_lines = []
            current_fn_ids = []

    # 处理最后一页
    if current_lines:
        fn_h_final = 0.0
        if current_fn_ids:
            fn_t_lines = sum(measure_footnote_lines(fn_dict[fid][1]) for fid in current_fn_ids if fid in fn_dict)
            fn_col_l = math.ceil(fn_t_lines / 2.0)
            fn_h_final = fn_col_l * FN_LINE_HEIGHT

        # 判定学习提示是否能装入最后一页
        tail_body_h = len(current_lines) * BODY_LINE_HEIGHT
        tail_fn_h = (SAFETY_GAP + fn_h_final) if current_fn_ids else 0.0
        tail_header_h = HEADER_HEIGHT if page_num == 1 else 0.0

        if has_hint:
            if tail_header_h + tail_body_h + tail_fn_h + HINT_TOTAL_HEIGHT <= USABLE_HEIGHT:
                pages.append({
                    "page_num": page_num,
                    "lines": current_lines,
                    "fn_ids": current_fn_ids,
                    "fn_block_h": fn_h_final,
                    "has_hint": True
                })
            else:
                pages.append({
                    "page_num": page_num,
                    "lines": current_lines,
                    "fn_ids": current_fn_ids,
                    "fn_block_h": fn_h_final,
                    "has_hint": False
                })
                # 提示另起一页
                pages.append({
                    "page_num": page_num + 1,
                    "lines": [],
                    "fn_ids": [],
                    "fn_block_h": 0.0,
                    "has_hint": True
                })
        else:
            pages.append({
                "page_num": page_num,
                "lines": current_lines,
                "fn_ids": current_fn_ids,
                "fn_block_h": fn_h_final,
                "has_hint": False
            })

    return pages

