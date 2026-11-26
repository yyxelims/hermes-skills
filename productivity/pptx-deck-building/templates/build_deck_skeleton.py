#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中文汇报 PPT 骨架：复制本文件 → 只改底部内容区 → 跑 check_pptx_overflow.py。

版式：封面 / 目录 / 章节分隔页 / 卡片内容页（1 或 2 列，可加权重）+ 数字卡条。
正文行首标记：^强调  ~次要  !待补充
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

OUT = "/tmp/deck-v1.pptx"

NAVY = RGBColor(0x1F, 0x38, 0x64); BLUE = RGBColor(0x2F, 0x55, 0x97)
ACCENT = RGBColor(0x17, 0x69, 0xAA); INK = RGBColor(0x33, 0x44, 0x5C)
MUTED = RGBColor(0x71, 0x80, 0x96); HOLD = RGBColor(0x9A, 0xA5, 0xB1)
CARD = RGBColor(0xF7, 0xFA, 0xFD); LINE = RGBColor(0xE3, 0xEA, 0xF3)
LTBLUE = RGBColor(0xE8, 0xF2, 0xFB); WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "微软雅黑"

W, H = Inches(13.333), Inches(7.5)
ML, CW = Inches(0.62), Inches(12.09)
TOP, BOT = Inches(1.52), Inches(6.88)

prs = Presentation(); prs.slide_width, prs.slide_height = W, H
BLANK = prs.slide_layouts[6]
page_no = [0]


def set_font(run, size=12.5, bold=False, color=INK, italic=False):
    f = run.font
    f.size, f.bold, f.italic, f.name = Pt(size), bold, italic, FONT
    f.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs"):          # 三个都要设，否则中文回退
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {}); rPr.append(el)
        el.set("typeface", FONT)


def textbox(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.1)
    tf.margin_top = tf.margin_bottom = Inches(0.04)
    return tb, tf


def para(tf, text, size=12.5, bold=False, color=INK, first=False,
         space_before=4, space_after=2, align=PP_ALIGN.LEFT, line=1.3, italic=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment, p.line_spacing = align, line
    p.space_before, p.space_after = Pt(space_before), Pt(space_after)
    r = p.add_run(); r.text = text
    set_font(r, size, bold, color, italic)
    return p


def rect(slide, x, y, w, h, fill=CARD, line=LINE, rounded=True, radius=0.035):
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, x, y, w, h)
    shp.shadow.inherit = False                        # 关默认阴影
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line; shp.line.width = Pt(0.75)
    if rounded:
        try:
            shp.adjustments[0] = radius
        except Exception:
            pass
    shp.text_frame.word_wrap = True
    return shp


def new_slide(count_page=True):
    s = prs.slides.add_slide(BLANK); page_no[0] += 1
    if count_page:
        _, tf = textbox(s, Inches(12.1), Inches(6.94), Inches(0.9), Inches(0.42))
        para(tf, f"{page_no[0]}", 10, False, HOLD, first=True, align=PP_ALIGN.RIGHT)
    return s


def header(slide, title, kicker=None):
    rect(slide, ML, Inches(0.46), Inches(0.075), Inches(0.42), fill=ACCENT, line=None, rounded=False)
    _, tf = textbox(slide, ML + Inches(0.18), Inches(0.4), Inches(11.6), Inches(0.55))
    para(tf, title, 25, True, NAVY, first=True, space_before=0, space_after=0, line=1.0)
    if kicker:
        _, tf2 = textbox(slide, ML + Inches(0.2), Inches(0.98), Inches(11.6), Inches(0.34))
        para(tf2, kicker, 12, False, MUTED, first=True, space_before=0, space_after=0, line=1.0)
    rect(slide, ML, Inches(1.36), CW, Emu(9525), fill=LINE, line=None, rounded=False)


def _draw_card(slide, x, y, w, h, head, lines, body_size, head_size):
    rect(slide, x, y, w, h)
    _, tf = textbox(slide, x + Inches(0.1), y + Inches(0.12), w - Inches(0.28), h - Inches(0.2))
    first = True
    if head:
        para(tf, head, head_size, True, NAVY, first=True, space_before=0, space_after=4, line=1.05)
        first = False
    for ln in lines:
        color, size, bold, italic, txt = INK, body_size, False, False, ln
        if txt.startswith("!"):
            txt, color, italic = txt[1:], HOLD, True
        elif txt.startswith("^"):
            txt, color, bold = txt[1:], ACCENT, True
        elif txt.startswith("~"):
            txt, color, size = txt[1:], MUTED, body_size - 0.5
        para(tf, txt, size, bold, color, first=first,
             space_before=1.5, space_after=1.5, line=1.22, italic=italic)
        first = False


def cards(slide, blocks, cols=1, top=TOP, bottom=BOT, gap=0.16,
          body_size=12.5, head_size=14.5, weights=None):
    """blocks: [(heading|None, [line,...]), ...]；weights 仅单列生效，按内容量分配卡高。"""
    n = len(blocks)
    if cols == 1:
        avail = (bottom - top) - Inches(gap) * (n - 1)
        ws = weights or [1] * n
        tot = float(sum(ws)); y = top
        for i, (head, lines) in enumerate(blocks):
            ch = int(avail * ws[i] / tot)
            _draw_card(slide, ML, y, CW, ch, head, lines, body_size, head_size)
            y = y + ch + Inches(gap)
    else:
        rows = (n + cols - 1) // cols
        cwid = (CW - Inches(gap) * (cols - 1)) / cols
        ch = ((bottom - top) - Inches(gap) * (rows - 1)) / rows
        for i, (head, lines) in enumerate(blocks):
            r, c = divmod(i, cols)
            _draw_card(slide, ML + (cwid + Inches(gap)) * c, top + (ch + Inches(gap)) * r,
                       cwid, ch, head, lines, body_size, head_size)


def stat_bar(slide, stats, top=TOP, h=0.95):
    """stats: [("847","人 · 领导档案覆盖"), ...] 建议 4 个"""
    sw = (CW - Inches(0.14) * (len(stats) - 1)) / len(stats)
    for i, (n, lab) in enumerate(stats):
        x = ML + (sw + Inches(0.14)) * i
        rect(slide, x, top, sw, Inches(h), fill=LTBLUE, line=RGBColor(0xD3, 0xE4, 0xF4))
        _, tf = textbox(slide, x + Inches(0.12), top + Inches(0.06), sw - Inches(0.24), Inches(h - 0.1))
        para(tf, n, 24, True, ACCENT, first=True, space_before=0, space_after=0, line=1.0)
        para(tf, lab, 11, False, MUTED, space_before=1, line=1.0)


def divider(num, title, sub):
    s = new_slide()
    rect(s, Inches(0), Inches(0), Inches(4.6), H, fill=NAVY, line=None, rounded=False)
    rect(s, Inches(4.6), Inches(0), Inches(0.05), H, fill=ACCENT, line=None, rounded=False)
    _, tf = textbox(s, Inches(1.0), Inches(2.6), Inches(3.2), Inches(1.6))
    para(tf, num, 72, True, RGBColor(0x3E, 0x6B, 0x9E), first=True, space_before=0, line=1.0)
    _, tf = textbox(s, Inches(5.3), Inches(2.75), Inches(7.4), Inches(1.8))
    para(tf, title, 34, True, NAVY, first=True, space_before=0, line=1.1)
    rect(s, Inches(5.32), Inches(3.75), Inches(1.1), Inches(0.045), fill=ACCENT, line=None, rounded=False)
    _, tf = textbox(s, Inches(5.3), Inches(4.0), Inches(7.4), Inches(0.9))
    para(tf, sub, 14, False, MUTED, first=True, space_before=0, line=1.35)
    return s


def cover(title, sub, who, teacher, org, date):
    s = new_slide(count_page=False); page_no[0] = 0
    rect(s, Inches(0), Inches(0), W, Inches(2.55), fill=NAVY, line=None, rounded=False)
    rect(s, Inches(0), Inches(2.55), W, Inches(0.05), fill=ACCENT, line=None, rounded=False)
    _, tf = textbox(s, Inches(1.0), Inches(0.85), Inches(11), Inches(1.4))
    para(tf, title, 40, True, WHITE, first=True, space_before=0, line=1.05)
    para(tf, sub, 15, False, RGBColor(0xC7, 0xDA, 0xEE), space_before=10, line=1.0)
    _, tf = textbox(s, Inches(1.0), Inches(3.4), Inches(7), Inches(1.6))
    para(tf, who, 20, True, NAVY, first=True, space_before=0, line=1.2)
    para(tf, teacher, 15, False, INK, space_before=8, line=1.2)
    para(tf, org, 14, False, MUTED, space_before=8, line=1.2)
    rect(s, Inches(1.0), Inches(5.35), Inches(1.2), Inches(0.045), fill=ACCENT, line=None, rounded=False)
    _, tf = textbox(s, Inches(1.0), Inches(5.6), Inches(8), Inches(0.4))
    para(tf, date, 13, False, MUTED, first=True, space_before=0, line=1.0)
    return s


def thanks(lines):
    s = new_slide(count_page=False)
    rect(s, Inches(0), Inches(0), W, H, fill=NAVY, line=None, rounded=False)
    rect(s, Inches(0), Inches(3.42), W, Inches(0.05), fill=ACCENT, line=None, rounded=False)
    _, tf = textbox(s, Inches(0), Inches(2.35), W, Inches(1.0))
    para(tf, "感 谢 聆 听", 44, True, WHITE, first=True, space_before=0, line=1.0, align=PP_ALIGN.CENTER)
    _, tf = textbox(s, Inches(0), Inches(3.7), W, Inches(1.4))
    for i, t in enumerate(lines):
        para(tf, t, 15, False, RGBColor(0xC7, 0xDA, 0xEE), first=(i == 0),
             space_before=0 if i == 0 else 4, line=1.5, align=PP_ALIGN.CENTER)
    return s


# ======================= 以下只改内容 =======================
cover("XXXX 年度工作汇报", "回顾 · 重点 · 展望",
      "汇 报 人 ：某某", "指导老师：某某", "某单位 · 某部门", "2026 年")

s = new_slide(); header(s, "重点工作示例页", "副标题：一句话说清这页在讲什么")
stat_bar(s, [("847", "人 · 覆盖"), ("724", "条 · 跟踪"), ("12", "家 · 机构"), ("16", "区 · 全覆盖")])
cards(s, [
    ("覆盖范围", ["第一条要点", "^关键数字放这里", "~次要说明"]),
    ("处理流程", ["抓取 → 去重 → 判断 → 摘要 → 交付", "!待补充内容用感叹号开头"]),
], cols=2, top=TOP + Inches(1.12), gap=0.14, body_size=11.5, head_size=13.5)

divider("01", "章节标题", "这一章要讲的三件事")
thanks(["感谢指导老师的悉心指导", "感谢领导与同事的支持"])

prs.save(OUT)
print("saved:", OUT, "slides:", len(prs.slides._sldIdLst))
