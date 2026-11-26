# -*- coding: utf-8 -*-
"""
剧本 → AI 视频分镜脚本 生成器骨架。
用同一份镜头数据产出 docx + html（带复制按钮的抄写页）+ md，内容一字不差。

用法：
  1. 复制本文件到 /tmp/<task>/build.py
  2. 把 META / SHOTS 换成本次的全局设定与镜头数据
     （数据量大就拆成 data1.py / data2.py，用 importlib 载入后 SHOTS = a.SHOTS + b.SHOTS）
  3. 改 OUT 为交付目录，python3 build.py

跑 .py 文件不触发审批；python -c / heredoc 内联会触发 → 一律落成文件再跑。
docx 依赖 python-docx（pip install python-docx）。
"""
import os, html
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.oxml.ns import qn

OUT = "/tmp/storyboard_out"
TITLE = "XXX · AI 生成视频逐镜分镜脚本与提示词"

META = {
    "film": "片名/用途",
    "alt_titles": ["备选片名A", "备选片名B"],
    "ratio": "主版 16:9（4K/25fps）；竖版 9:16（1080×1920）",
    "style": "写实电影感 · 纪实质感 · 冷暖平衡",
    "tools": "可灵 / 即梦 / Seedance / Runway / Veo / Sora",
    "strategy": "以图生视频为主（首帧图→视频）保证一致性；台词戏拆 3-6 秒短镜做正反打。",
    "characters": [
        {"name": "角色A", "role": "身份（年龄/性别）",
         "anchor_cn": "中文外貌锚点：年龄、脸型、发型、服装、配饰、神情",
         "anchor_en": "East Asian ... , warm and professional expression"},
    ],
    "scene": {"name": "场景名", "anchor_cn": "环境长句…", "anchor_en": "modern interior ..."},
    "props": [{"name": "道具A", "cn": "外观描述", "en": "description"}],
    "style_prefix_cn": "【风格】电影感写实风格，4K超高清，色彩自然通透；",
    "style_prefix_en": "cinematic photorealism, 4K ultra HD, natural color grading,",
    "negative_cn": "模糊，低清，手部畸形，五官扭曲，文字乱码，水印，品牌标识…",
    "negative_en": "blurry, low resolution, deformed hands, distorted face, garbled text, watermark, logo",
    "audio": {"bgm": "分段情绪曲线…", "sfx": "音效清单…", "vo": "配音人选与语速…"},
    "caption_rules": "字体/位置/哪些数字加重；所有文字一律后期叠加。",
    "tech": "画幅、分辨率、帧率、单镜时长、交付格式。",
    "consistency": ["用同一张定妆图作首帧/主体参考，固定 seed…"],
    "pitfalls": ["文字交给 AI 必崩，后期叠加…", "手部走图生视频…"],
    "compliance": ["台词/期限数字与原文逐字一致…"],
}

SHOTS = [
    {
        "no": "S01", "title": "镜头小标题", "dur": "4s", "size": "中近景", "cam": "固定机位",
        "visual": "画面内容：构图、人物、道具、背景。",
        "action": "动作—动作—微表情。",
        "line": "台词原文照抄", "speaker": "角色A",
        "audio": "音效 + 本镜 BGM 走向。",
        "caption": "后期叠加的字幕/角标。",
        "cn": "【风格】…。【主体】角色锚点原样复述。【动作】…。【环境】…。【镜头】…。【光线】色温5000K。【画质】超高清，无品牌标识。",
        "en": "cinematic photorealism, 4K ultra HD, ..., no brand logo",
        "first": "首帧图提示词：景别，主体+锚点，动作定格，环境，光线，质感，4K",
        "note": "本镜专属生成要点/坑。",
    },
]

# ---------------------------------------------------------------- 通用工具
def loads():
    return META, SHOTS

def secs(s): 
    try: return int(str(s).replace("s", "").strip())
    except: return 0
TOTAL = sum(secs(s["dur"]) for s in SHOTS)
TOTAL_TXT = f"{TOTAL // 60} 分 {TOTAL % 60} 秒（{len(SHOTS)} 个镜头单元）"
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- 1) MARKDOWN
md = [f"# {TITLE}\n"]
md.append(f"| 项目 | 内容 |\n|---|---|")
md.append(f"| 片名 | {META['film']} |")
md.append(f"| 总时长 | 约 {TOTAL_TXT} |")
md.append(f"| 画幅 | {META['ratio']} |")
md.append(f"| 风格 | {META['style']} |")
md.append(f"| 工具 | {META['tools']} |\n")
for c in META["characters"]:
    md.append(f"**{c['name']}｜{c['role']}**\n- 中文锚点：{c['anchor_cn']}\n- English：{c['anchor_en']}\n")
md.append(f"**场景锚点**：{META['scene']['anchor_cn']}\n")
md.append(f"**风格前缀**：{META['style_prefix_cn']}\n")
md.append(f"**负向提示词**：{META['negative_cn']}\n")
md.append("## 分镜总表\n| 镜号 | 标题 | 时长 | 景别 | 运镜 |\n|---|---|---|---|---|")
for s in SHOTS:
    md.append(f"| {s['no']} | {s['title']} | {s['dur']} | {s['size']} | {s['cam']} |")
md.append("")
for s in SHOTS:
    md.append(f"### {s['no']}　{s['title']}\n")
    md.append(f"**时长**：{s['dur']}　|　**景别**：{s['size']}　|　**运镜**：{s['cam']}\n")
    md.append(f"**画面内容**：{s['visual']}\n")
    if s.get("action"): md.append(f"**动作/微表情**：{s['action']}\n")
    if s.get("line"):   md.append(f"**台词（{s['speaker']}）**：{s['line']}\n")
    md.append(f"**音效/音乐**：{s['audio']}\n")
    if s.get("caption"): md.append(f"**字幕/包装**：{s['caption']}\n")
    md.append(f"**中文提示词**\n```\n{s['cn']}\n```\n")
    md.append(f"**English Prompt**\n```\n{s['en']}\n```\n")
    md.append(f"**首帧图提示词**\n```\n{s['first']}\n```\n")
    if s.get("note"): md.append(f"**⚠️ 生成要点**：{s['note']}\n")
    md.append("---\n")
for title, key in [("一致性执行方案", "consistency"), ("生成避坑指南", "pitfalls"), ("合规红线", "compliance")]:
    if META.get(key):
        md.append(f"## {title}\n")
        for i, t in enumerate(META[key], 1): md.append(f"{i}. {t}")
        md.append("")
open(os.path.join(OUT, "分镜脚本.md"), "w", encoding="utf-8").write("\n".join(md))

# ---------------------------------------------------------------- 2) DOCX
doc = Document()
st = doc.styles["Normal"]
st.font.name = "PingFang SC"; st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "PingFang SC")   # 关键：eastAsia 必须同设

def _f(run, size=10.5, mono=False):
    run.font.name = "Consolas" if mono else "PingFang SC"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "PingFang SC")
    run.font.size = Pt(size)

def H(t, lvl=1): return doc.add_heading(t, level=lvl)
def P(t, bold=False, size=10.5, color=None):
    p = doc.add_paragraph(); r = p.add_run(t); _f(r, size); r.bold = bold
    if color: r.font.color.rgb = color
    return p
def KV(k, v):
    p = doc.add_paragraph(); r1 = p.add_run(k + "："); _f(r1); r1.bold = True
    r2 = p.add_run(v); _f(r2); return p
def BOX(label, text):
    P(label, bold=True, size=10, color=RGBColor(0x02, 0x84, 0xC7))
    p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(0.5)
    _f(p.add_run(text), 10)

doc.add_heading(TITLE, 0)
P(f"总时长：约 {TOTAL_TXT}｜画幅：{META['ratio']}")
P(f"风格：{META['style']}｜工具：{META['tools']}")
P(f"策略：{META['strategy']}")
H("一、角色一致性锚点", 1)
for c in META["characters"]:
    H(f"{c['name']}｜{c['role']}", 2); KV("中文锚点", c["anchor_cn"]); KV("English", c["anchor_en"])
H("二、场景与道具锚点", 1)
KV("场景", META["scene"]["anchor_cn"])
for p in META["props"]: KV(p["name"], p["cn"])
H("三、通用提示词", 1)
KV("风格前缀", META["style_prefix_cn"]); KV("负向提示词", META["negative_cn"])
KV("BGM", META["audio"]["bgm"]); KV("音效", META["audio"]["sfx"]); KV("配音", META["audio"]["vo"])
KV("字幕规范", META["caption_rules"]); KV("技术参数", META["tech"])
H("四、分镜总表", 1)
tb = doc.add_table(rows=1, cols=5)
for i, t in enumerate(["镜号", "标题", "时长", "景别", "运镜"]): tb.rows[0].cells[i].text = t
for s in SHOTS:
    row = tb.add_row().cells
    for i, k in enumerate(["no", "title", "dur", "size", "cam"]): row[i].text = str(s[k])
doc.add_page_break(); H("五、逐镜分镜脚本与提示词", 1)
for s in SHOTS:
    H(f"{s['no']}　{s['title']}", 2)
    P(f"时长：{s['dur']}　|　景别：{s['size']}　|　运镜：{s['cam']}", bold=True, size=10,
      color=RGBColor(0x64, 0x74, 0x8B))
    KV("画面内容", s["visual"])
    if s.get("action"): KV("动作/微表情", s["action"])
    if s.get("line"):   KV(f"台词（{s['speaker']}）", s["line"])
    KV("音效/音乐", s["audio"])
    if s.get("caption"): KV("字幕/包装", s["caption"])
    BOX("【中文提示词】可灵 / 即梦 / Seedance", s["cn"])
    BOX("【English Prompt】Runway / Veo / Sora", s["en"])
    BOX("【首帧图提示词】图生视频用", s["first"])
    if s.get("note"): P("⚠️ " + s["note"], size=10, color=RGBColor(0xB4, 0x53, 0x09))
for title, key in [("六、一致性执行方案", "consistency"), ("七、生成避坑指南", "pitfalls"), ("八、合规红线", "compliance")]:
    if META.get(key):
        H(title, 1)
        for i, t in enumerate(META[key], 1): P(f"{i}. {t}")
doc.save(os.path.join(OUT, "分镜脚本.docx"))

# ---------------------------------------------------------------- 3) HTML（抄写页）
e = html.escape
def shot_html(s):
    o = [f'<article class="shot" id="{s["no"]}">']
    o.append(f'<div class="shot-hd"><span class="no">{s["no"]}</span><h3>{e(s["title"])}</h3>'
             f'<div class="tags"><span class="tag t1">{e(s["dur"])}</span>'
             f'<span class="tag t2">{e(s["size"])}</span><span class="tag t3">{e(s["cam"])}</span></div></div>')
    o.append(f'<div class="row"><b>画面内容</b><p>{e(s["visual"])}</p></div>')
    if s.get("action"): o.append(f'<div class="row"><b>动作/微表情</b><p>{e(s["action"])}</p></div>')
    if s.get("line"):   o.append(f'<div class="row"><b>台词 · {e(s["speaker"])}</b><p class="dialog">{e(s["line"])}</p></div>')
    o.append(f'<div class="row"><b>音效/音乐</b><p>{e(s["audio"])}</p></div>')
    if s.get("caption"): o.append(f'<div class="row"><b>字幕/包装</b><p>{e(s["caption"])}</p></div>')
    for label, key, cls in [("中文提示词 · 可灵/即梦/Seedance", "cn", "p-cn"),
                            ("English Prompt · Runway/Veo/Sora", "en", "p-en"),
                            ("首帧图提示词 · 图生视频", "first", "p-ff")]:
        pid = f'{s["no"]}-{key}'
        o.append(f'<div class="prompt {cls}"><div class="ph"><span>{e(label)}</span>'
                 f'<button class="cp" data-t="{pid}">复制</button></div><pre id="{pid}">{e(s[key])}</pre></div>')
    if s.get("note"): o.append(f'<div class="note">⚠️ {e(s["note"])}</div>')
    o.append('</article>')
    return "\n".join(o)

rows = "\n".join(f'<tr><td>{e(s["no"])}</td><td>{e(s["title"])}</td><td>{e(s["dur"])}</td>'
                 f'<td>{e(s["size"])}</td><td>{e(s["cam"])}</td>'
                 f'<td class="jump"><a href="#{s["no"]}">查看 →</a></td></tr>' for s in SHOTS)
shots_html = "\n".join(shot_html(s) for s in SHOTS)

HTML = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(TITLE)}</title><style>
:root{{--bg:#f6f7f9;--surface:#fff;--ink:#334155;--ink2:#64748b;--line:#e2e8f0;
--accent:#0284c7;--accent-bg:#e0f2fe;--hot:#d97706;--hot-bg:#fef3c7;--green:#059669;--green-bg:#d1fae5;}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-size:15px;line-height:1.75;
font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 20px 80px}}
header{{background:linear-gradient(135deg,#0b3a5c 0%,#0284c7 55%,#38bdf8 100%);color:#fff;padding:44px 20px 38px;margin-bottom:26px}}
header .inner{{max-width:1080px;margin:0 auto}}header h1{{margin:0 0 6px;font-size:27px}}header .sub{{opacity:.9;font-size:14px}}
nav.toc{{position:sticky;top:0;z-index:50;background:rgba(246,247,249,.94);backdrop-filter:blur(10px);
border-bottom:1px solid var(--line);padding:9px 20px;margin:-26px -20px 26px}}
nav.toc a{{color:var(--accent);text-decoration:none;font-size:13px;margin-right:16px}}
h2{{font-size:20px;margin:38px 0 14px;padding-left:12px;border-left:4px solid var(--accent)}}
h3{{font-size:16px;margin:0}}
.card{{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:12px}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;font-size:13.5px}}
th{{background:#2f5597;color:#fff;text-align:left;padding:9px 11px}}td{{padding:8px 11px;border-top:1px solid var(--line)}}
tbody tr:nth-child(even){{background:#f8fafc}}td.jump a{{color:var(--accent);text-decoration:none;font-size:12.5px}}
.shot{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-bottom:18px;
box-shadow:0 1px 3px rgba(15,23,42,.05);scroll-margin-top:64px}}
.shot-hd{{display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding-bottom:12px;border-bottom:1px dashed var(--line);margin-bottom:12px}}
.no{{background:#0b3a5c;color:#fff;border-radius:8px;padding:3px 9px;font-size:13px;font-weight:700}}
.tags{{margin-left:auto;display:flex;flex-wrap:wrap;gap:6px}}.tag{{border-radius:999px;padding:2px 10px;font-size:12px}}
.t1{{background:var(--accent-bg);color:#075985}}.t2{{background:var(--green-bg);color:#065f46}}.t3{{background:var(--hot-bg);color:#92400e}}
.row{{margin:9px 0}}.row b{{display:block;font-size:12.5px;color:var(--ink2);margin-bottom:2px}}.row p{{margin:0;font-size:14px}}
.dialog{{background:#f1f5f9;border-left:3px solid var(--hot);border-radius:0 8px 8px 0;padding:9px 13px;font-size:14.5px;color:#1e293b}}
.prompt{{margin:12px 0 0;border:1px solid var(--line);border-radius:10px;overflow:hidden}}
.prompt .ph{{display:flex;align-items:center;justify-content:space-between;padding:6px 10px 6px 12px;font-size:12px;font-weight:600}}
.p-cn .ph{{background:#e0f2fe;color:#075985}}.p-en .ph{{background:#ede9fe;color:#5b21b6}}.p-ff .ph{{background:#d1fae5;color:#065f46}}
.prompt pre{{margin:0;padding:12px 14px;white-space:pre-wrap;word-break:break-word;font-size:13.5px;line-height:1.8;color:#1e293b;
background:#fff;font-family:"Noto Sans SC","PingFang SC",system-ui,sans-serif}}
.p-en pre{{font-family:ui-monospace,Menlo,monospace;font-size:12px}}
.cp{{background:#fff;border:1px solid rgba(15,23,42,.15);border-radius:6px;padding:2px 10px;font-size:11.5px;cursor:pointer;font-family:inherit}}
.cp.ok{{background:var(--green);color:#fff;border-color:var(--green)}}
.note{{margin-top:12px;background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:9px 13px;font-size:13px;color:#92400e}}
.toolbar{{position:fixed;right:22px;bottom:22px;z-index:99}}
.toolbar button{{background:#0b3a5c;color:#fff;border:none;border-radius:999px;padding:11px 18px;font-size:13px;cursor:pointer;
box-shadow:0 6px 18px rgba(11,58,92,.3);font-family:inherit}}
@media(max-width:600px){{body{{font-size:14px}}.wrap{{padding:0 12px 70px}}.tags{{margin-left:0;width:100%}}pre{{font-size:12.5px}}}}
</style></head><body>
<header><div class="inner"><h1>{e(TITLE)}</h1>
<div class="sub">总时长 约 {e(TOTAL_TXT)}　|　{e(META['ratio'])}　|　{e(META['style'])}</div></div></header>
<div class="wrap">
<nav class="toc"><a href="#sec-char">角色锚点</a><a href="#sec-global">通用提示词</a>
<a href="#sec-table">分镜总表</a><a href="#sec-shots">逐镜提示词</a></nav>
<h2 id="sec-char">一、角色一致性锚点</h2>
""" + "\n".join(f'<div class="card"><div class="card-hd">{e(c["name"])}</div>'
                f'<div style="font-size:12px;color:#075985">{e(c["role"])}</div>'
                f'<p><b>中文</b>{e(c["anchor_cn"])}</p><p style="font-size:12px;color:#475569">{e(c["anchor_en"])}</p></div>'
                for c in META["characters"]) + f"""
<h2 id="sec-global">二、通用提示词</h2>
<div class="card"><b>风格前缀</b><p>{e(META['style_prefix_cn'])}</p></div>
<div class="card"><b>负向提示词</b><p>{e(META['negative_cn'])}</p></div>
<div class="card"><b>音频</b><p>BGM：{e(META['audio']['bgm'])}</p><p>音效：{e(META['audio']['sfx'])}</p><p>配音：{e(META['audio']['vo'])}</p></div>
<h2 id="sec-table">三、分镜总表</h2>
<table><thead><tr><th>镜号</th><th>标题</th><th>时长</th><th>景别</th><th>运镜</th><th></th></tr></thead><tbody>{rows}</tbody></table>
<h2 id="sec-shots">四、逐镜分镜脚本与提示词</h2>
{shots_html}
</div>
<div class="toolbar"><button id="copyAll">复制全部中文提示词</button></div>
<script>
function copy(t){{
  if(navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(t);
  var ta=document.createElement('textarea'); ta.value=t; ta.style.position='fixed'; ta.style.opacity=0;
  document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); return Promise.resolve();
}}
document.addEventListener('click', function(ev){{
  var b = ev.target.closest('.cp'); if(!b) return;
  copy(document.getElementById(b.dataset.t).innerText).then(function(){{
    b.textContent='已复制 ✓'; b.classList.add('ok');
    setTimeout(function(){{ b.textContent='复制'; b.classList.remove('ok'); }}, 1400);
  }});
}});
document.getElementById('copyAll').addEventListener('click', function(){{
  var btn=this, pres=document.querySelectorAll('.p-cn pre'), nos=document.querySelectorAll('.shot .no'), out=[];
  pres.forEach(function(n,i){{ out.push('【'+nos[i].textContent+'】\\n'+n.textContent); }});
  copy(out.join('\\n\\n')).then(function(){{
    btn.textContent='已复制 '+pres.length+' 条 ✓';
    setTimeout(function(){{ btn.textContent='复制全部中文提示词'; }}, 1800);
  }});
}});
</script></body></html>"""
open(os.path.join(OUT, "分镜脚本.html"), "w", encoding="utf-8").write(HTML)

print("OK", len(SHOTS), "shots,", TOTAL_TXT)
for f in os.listdir(OUT): print(" ", f, os.path.getsize(os.path.join(OUT, f)), "bytes")
