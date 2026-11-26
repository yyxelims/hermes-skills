#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静态审计 .pptx 版式：文字溢出 / 出界 / 图片重叠。

无需 LibreOffice、无需视觉模型。每次 build 后跑，全绿再交付。

用法:
    python3 audit_layout.py deck.pptx

估算口径：CJK 字宽 ≈ 1.0 × 字号(pt)，拉丁/数字 ≈ 0.55 × 字号(pt)；
行高 = 字号 × line_spacing × 1.02，再加 space_before / space_after。
框内可用宽度 = shape 宽 - 22pt（左右内边距），可用高 = shape 高 - 8pt。
ratio > 1.0 即判为溢出。经验上这套估算和 PowerPoint 实际折行足够接近。
"""
import sys
import unicodedata

from pptx import Presentation
from pptx.util import Emu


def char_w(ch, size):
    return size * (1.0 if unicodedata.east_asian_width(ch) in ("W", "F") else 0.55)


def audit(path):
    prs = Presentation(path)
    SW, SH = Emu(prs.slide_width).inches, Emu(prs.slide_height).inches
    over, oob, overlap = [], [], []

    for si, slide in enumerate(prs.slides, 1):
        pics = []
        for sh in slide.shapes:
            L, T, W, H = [Emu(v).inches for v in (sh.left, sh.top, sh.width, sh.height)]
            if L < -0.02 or T < -0.02 or L + W > SW + 0.02 or T + H > SH + 0.02:
                oob.append((si, str(sh.shape_type), round(L, 2), round(T, 2),
                            round(W, 2), round(H, 2)))
            if sh.shape_type == 13:  # PICTURE
                pics.append((L, T, W, H))
            if not sh.has_text_frame:
                continue
            tf = sh.text_frame
            if not tf.text.strip():
                continue
            bw = Emu(sh.width).pt - 22
            bh = Emu(sh.height).pt - 8
            if bw <= 0 or bh <= 0:
                continue
            need = 0.0
            for p in tf.paragraphs:
                txt = "".join(r.text for r in p.runs)
                if not txt:
                    continue
                size = max((r.font.size.pt for r in p.runs if r.font.size), default=12.0)
                ls = p.line_spacing or 1.2
                sb = p.space_before.pt if p.space_before else 0
                sa = p.space_after.pt if p.space_after else 0
                tw = sum(char_w(c, size) for c in txt)
                lines = max(1, -(-int(tw * 100) // int(bw * 100)))
                need += lines * size * ls * 1.02 + sb + sa
            if need / bh > 1.0:
                over.append((si, round(need / bh, 2), round(bh, 1), round(need, 1),
                             tf.text.replace("\n", " / ")[:60]))

        for i in range(len(pics)):
            for j in range(i + 1, len(pics)):
                x1, y1, w1, h1 = pics[i]
                x2, y2, w2, h2 = pics[j]
                ox = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                oy = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                if ox > 0.05 and oy > 0.05:
                    overlap.append((si, round(ox, 2), round(oy, 2)))

    n_pic = sum(1 for s in prs.slides for sh in s.shapes if sh.shape_type == 13)
    print(f"slides: {len(prs.slides._sldIdLst)}   图片数: {n_pic}")
    print("\n[文字溢出]" + ("  无" if not over else ""))
    for o in sorted(over, key=lambda x: -x[1]):
        print("  p%-3s ratio=%-5s box=%-6s need=%-6s | %s" % o)
    print("\n[出界]" + ("  无" if not oob else ""))
    for o in oob:
        print("  p%s %s at %s,%s %sx%s" % o)
    print("\n[图片重叠]" + ("  无" if not overlap else f"  {overlap}"))
    return 0 if not (over or oob or overlap) else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(audit(sys.argv[1]))
