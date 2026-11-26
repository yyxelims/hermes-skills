#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CJK 排版自查：估算每个文本框需要的高度 vs 形状高度，ratio>1.0 即溢出。

用法：
    env -u PYTHONPATH python3 check_pptx_overflow.py /path/to/deck.pptx

原理（无需 LibreOffice / 渲染器 / vision）：
    CJK 字宽 ≈ 字号pt × 1.0，拉丁 ≈ 字号 × 0.55
    每段行数 = ceil(总字宽 / (框宽pt - 22))          # 22pt ≈ 左右内边距
    需要高度 = Σ(行数 × 字号 × line_spacing + space_before + space_after)

注意：高度小于一行行高的小文本框（页码等）会误报，给它们 ≥0.4" 高度即可。
"""
import sys
import unicodedata
from pptx import Presentation
from pptx.util import Emu

PATH = sys.argv[1] if len(sys.argv) > 1 else None
if not PATH:
    sys.exit("usage: check_pptx_overflow.py <deck.pptx>")


def char_w(ch, size):
    return size * (1.0 if unicodedata.east_asian_width(ch) in ("W", "F") else 0.55)


prs = Presentation(PATH)
problems = []
for si, slide in enumerate(prs.slides, 1):
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        tf = sh.text_frame
        if not tf.text.strip():
            continue
        box_w = Emu(sh.width).pt - 22
        box_h = Emu(sh.height).pt - 8
        if box_w <= 0:
            continue
        need = 0.0
        for p in tf.paragraphs:
            txt = "".join(r.text for r in p.runs)
            if not txt:
                continue
            size = max((r.font.size.pt for r in p.runs if r.font.size), default=12.5)
            ls = p.line_spacing or 1.2
            sb = p.space_before.pt if p.space_before else 0
            sa = p.space_after.pt if p.space_after else 0
            tw = sum(char_w(c, size) for c in txt)
            lines = max(1, int(tw / box_w) + (1 if tw % box_w else 0))
            need += lines * size * ls * 1.02 + sb + sa
        ratio = need / box_h if box_h > 0 else 9
        if ratio > 1.0:
            problems.append((si, sh.name, round(ratio, 2), round(box_h, 1),
                             round(need, 1), tf.text.replace("\n", " / ")[:70]))

print("slides:", len(prs.slides._sldIdLst))
if not problems:
    print("OK: 没有检测到文字溢出")
else:
    for p in sorted(problems, key=lambda x: -x[2]):
        print("溢出 p%-3s %-22s ratio=%-5s box=%-6s need=%-6s | %s" % p)
    sys.exit(1)
