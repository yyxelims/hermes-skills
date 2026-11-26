# -*- coding: utf-8 -*-
"""逐字稿/汇报稿/讲话稿 → docx 生成模板。

用法：把 PAGES 填成 (页面标题, [正文段落...]) 列表，改 OUT 路径，然后 `python3 本脚本.py`。
（注意：跑 .py 脚本文件不触发审批；`python -c` 和 heredoc 内联执行会触发审批。）

排版约定（用户偏好）：
- 大标题黑体 20pt 居中；页面标题黑体 14pt 深蓝 #2F5597
- 正文宋体 12pt，首行缩进 2 字符（Pt(24)），1.5 倍行距
- 每页末尾红色加粗右对齐的【翻页】标记
- PPT 里是占位符的内容，段落前缀「⚠️ 待补充：」

从 PPTX 提取内容写逐字稿时：以 read_file 提取的物理页序为准，
不要信 PPT 的页脚页码——调过页序后页脚页码常常是错的（本次就遇到 3/4/5/6/7/8 全错位）。
技术点用科普语言/比喻讲给非技术领导听，别堆专业词汇。
"""
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUT = "逐字稿.docx"

# (页面标题, [正文段落...])
PAGES = [
    ("第1页 · 封面", ["各位领导、各位同事，大家好！", "我是……。下面开始我的汇报。"]),
]


def set_font(run, size=12, bold=False, east="宋体", latin="Times New Roman", color=None):
    run.font.name = latin
    run.font.size = Pt(size)
    run.font.bold = bold
    rpr = run._element.get_or_add_rPr()
    rpr.get_or_add_rFonts().set(qn("w:eastAsia"), east)
    if color is not None:
        run.font.color.rgb = RGBColor(*color)


doc = Document()
normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(12)
normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "宋体")

for heading, paras in PAGES:
    hp = doc.add_paragraph()
    hp.paragraph_format.space_before = Pt(12)
    hp.paragraph_format.space_after = Pt(4)
    set_font(hp.add_run(heading), size=14, bold=True, east="黑体", color=(0x2F, 0x55, 0x97))

    for text in paras:
        bp = doc.add_paragraph()
        bp.paragraph_format.first_line_indent = Pt(24)
        bp.paragraph_format.line_spacing = 1.5
        bp.paragraph_format.space_after = Pt(2)
        set_font(bp.add_run(text), size=12)

    fp = doc.add_paragraph()
    fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    fp.paragraph_format.space_before = Pt(2)
    fp.paragraph_format.space_after = Pt(4)
    set_font(fp.add_run("【翻页】"), size=11, bold=True, east="黑体", color=(0xC0, 0x00, 0x00))

doc.save(OUT)
print("SAVED:", OUT)
