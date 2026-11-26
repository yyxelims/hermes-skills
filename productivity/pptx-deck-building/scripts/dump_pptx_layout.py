#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""改已有 pptx 前必跑：递归导出每一页每个形状的 名字/类型/坐标/尺寸/填充色/文字。

为什么不用 zipfile+正则抓 <a:t>：那样只能拿到文字，拿不到形状名和坐标，
而改版面必须知道"这个文本框叫什么、在哪、多大、是不是在 group 里"。

用法:
    env -u PYTHONPATH python3 dump_pptx_layout.py deck.pptx            # 全部页
    env -u PYTHONPATH python3 dump_pptx_layout.py deck.pptx 2 3 6      # 只看第 2/3/6 页
    env -u PYTHONPATH python3 dump_pptx_layout.py deck.pptx --images   # 额外把图片页导出到 /tmp/pptx_imgs/

注意：必须写成 .py 文件跑，`python3 -c` 会触发审批。
env -u PYTHONPATH 是因为 Hermes 会把自家 site-packages 塞进 PYTHONPATH 污染 venv。

导出的图片可以用 tesseract 读中文内容：
    tesseract /tmp/pptx_imgs/xxx.png stdout -l chi_sim+eng --psm 11
"""
import io
import os
import sys

from pptx import Presentation
from pptx.util import Emu

PICTURE, GROUP, TABLE_PH = 13, 6, 19


def fill_of(sh):
    """实心填充返回 RRGGBB，其余返回 '-'。用于区分卡片主体和顶部装饰条。"""
    try:
        if sh.fill.type == 1:
            return str(sh.fill.fore_color.rgb)
    except Exception:
        pass
    return "-"


def pos_of(sh):
    try:
        return (f"({Emu(sh.left).inches:.2f},{Emu(sh.top).inches:.2f}) "
                f"{Emu(sh.width).inches:.2f}x{Emu(sh.height).inches:.2f}")
    except Exception:
        return "n/a"


def dump_runs(para):
    """返回 [(text, pt, color, bold, font)] —— 改字体/字号前必须先看清现状。"""
    out = []
    for r in para.runs:
        if not r.text.strip():
            continue
        size = r.font.size.pt if r.font.size else None
        color = None
        try:
            if r.font.color is not None and r.font.color.type is not None:
                color = str(r.font.color.rgb)
        except Exception:
            pass
        out.append((r.text, size, color, r.font.bold, r.font.name))
    return out


def walk(shapes, indent, dump_images, imgdir, depth=0):
    for sh in shapes:
        tag = f"{'  ' * depth}[{sh.shape_type}] {sh.name!r} pos={pos_of(sh)} fill={fill_of(sh)}"
        print(indent + tag)

        if sh.shape_type == GROUP:
            # 子形状的 left/top 是接近 0 的相对值，属正常现象，不是坐标损坏。
            # 要整组挪位置：直接设 group.top / group.left，子形状自动跟随。
            walk(sh.shapes, indent, dump_images, imgdir, depth + 1)
            continue

        if sh.shape_type == PICTURE:
            try:
                img = sh.image
                print(f"{indent}{'  ' * depth}  <PICTURE {img.ext} {img.size} "
                      f"{len(img.blob)}B>  ← 整页图则无可编辑文字，改前先问用户")
                if dump_images:
                    os.makedirs(imgdir, exist_ok=True)
                    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in sh.name)
                    fn = os.path.join(imgdir, f"{safe}.{img.ext}")
                    with open(fn, "wb") as f:
                        f.write(img.blob)
                    print(f"{indent}{'  ' * depth}  saved -> {fn}")
            except Exception as e:
                print(f"{indent}{'  ' * depth}  <PICTURE unreadable: {e}>")

        if sh.has_text_frame:
            for para in sh.text_frame.paragraphs:
                txt = "".join(r.text for r in para.runs)
                if not txt.strip():
                    continue
                print(f"{indent}{'  ' * depth}  P: {txt}")
                runs = dump_runs(para)
                if runs:
                    desc = " | ".join(f"'{t}'[{s}pt/{c}/{b}/{f}]" for t, s, c, b, f in runs)
                    print(f"{indent}{'  ' * depth}     runs: {desc}")

        if getattr(sh, "has_table", False) and sh.has_table:
            tbl = sh.table
            print(f"{indent}{'  ' * depth}  <TABLE {len(tbl.rows)}x{len(tbl.columns)}>")
            for ri, row in enumerate(tbl.rows):
                cells = [c.text.replace("\n", "\\n") for c in row.cells]
                print(f"{indent}{'  ' * depth}   R{ri}: {cells}")


def main():
    args = [a for a in sys.argv[1:]]
    dump_images = "--images" in args
    args = [a for a in args if a != "--images"]
    if not args:
        print(__doc__)
        sys.exit(1)

    path = args[0]
    only = {int(a) for a in args[1:] if a.isdigit()}
    imgdir = "/tmp/pptx_imgs"

    prs = Presentation(path)
    print(f"FILE: {path}")
    print(f"SLIDE SIZE: {Emu(prs.slide_width).inches:.3f} x "
          f"{Emu(prs.slide_height).inches:.3f} inches")
    print(f"NUM SLIDES: {len(prs.slides)}")

    for idx, slide in enumerate(prs.slides, 1):
        if only and idx not in only:
            continue
        print("\n" + "=" * 72)
        print(f"### SLIDE {idx} ###  layout={slide.slide_layout.name}")
        walk(slide.shapes, "  ", dump_images, imgdir)


if __name__ == "__main__":
    main()
