#!/usr/bin/env python3
"""Build cybernetics audit HTML report from group JSON files.

Reads cybernetics_group{1,2,3}.json from the reports directory,
computes statistics, and generates a styled HTML report + merged JSON.

Usage:
    python3 scripts/audit-report-builder.py

Output:
    ~/.hermes/skills/reports/cybernetics_audit_YYYYMMDD.html
    ~/.hermes/plans/cybernetics-audit-YYYY-MM-DD.json
"""
import json, os
from collections import Counter
from datetime import date

home = os.path.expanduser("~")
report_dir = os.path.join(home, ".hermes", "skills", "reports")
plans_dir = os.path.join(home, ".hermes", "plans")
today = date.today()
date_str = today.strftime("%Y%m%d")
iso_date = today.isoformat()

# ── Read all 3 group files ──
all_data = []
for g in ["group1", "group2", "group3"]:
    path = os.path.join(report_dir, f"cybernetics_{g}.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    all_data.extend(data)
    print(f"{g}: {len(data)} items")

print(f"Total: {len(all_data)} skills")

# ── Dimensions ──
DIMS = ["closure","stability","observability","optimization","cross_domain"]
DIM_LABEL = {
    "closure": "闭环完整性", "stability": "稳定性",
    "observability": "可观测性", "optimization": "最优化",
    "cross_domain": "跨域性"
}
DIM_COL = {
    "closure": "#4A90D9", "stability": "#7B1FA2",
    "observability": "#00897B", "optimization": "#E64A19",
    "cross_domain": "#4527A0"
}
PNAMES = {
    1: "实践-理论-实践循环", 2: "特殊→一般", 3: "数学建模",
    4: "稳定性优先", 5: "能控能观对偶", 6: "反馈闭环",
    7: "最优化", 8: "协调解耦", 9: "分析→综合",
    10: "跨域统一", 11: "技术科学定位", 12: "大系统观",
    13: "信息-控制融合", 14: "理论实践不可偏废"
}

# ── Statistics ──
avgs = {}
for dm in DIMS:
    vals = [d[dm] for d in all_data if d[dm] > 0]
    avgs[dm] = round(sum(vals)/len(vals), 2) if vals else 0

cat_count = Counter(d["category"] for d in all_data)
cat_scores = {}
for d in all_data:
    c = d["category"]
    cat_scores.setdefault(c, {dm: [] for dm in DIMS})
    for dm in DIMS:
        if d[dm] > 0:
            cat_scores[c][dm].append(d[dm])
cat_avg = {}
for c, sc in cat_scores.items():
    cat_avg[c] = {}
    for dm in DIMS:
        v = sc[dm]
        cat_avg[c][dm] = round(sum(v)/len(v), 2) if v else 0

pcount = Counter()
for d in all_data:
    for p in d.get("principles", []):
        pcount[p] += 1

for d in all_data:
    d["_total"] = sum(d[dm] for dm in DIMS)
scored = sorted([d for d in all_data if d["_total"] > 0],
                key=lambda x: x["_total"], reverse=True)
top10 = scored[:10]
bot10 = scored[-10:][::-1]
nf = [d for d in all_data if d["closure"] == 0]
overall_avg = round(sum(avgs.values())/5, 2)

# ── Save merged JSON ──
merged_path = os.path.join(plans_dir, f"cybernetics-audit-{iso_date}.json")
os.makedirs(plans_dir, exist_ok=True)
with open(merged_path, "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)
print(f"Merged JSON: {merged_path}")

# ── HTML helpers ──
def hbar(val, mx=5, c="#4A90D9"):
    return f'<div class="bar-bg"><div class="bar-fill" style="width:{val/mx*100}%;background:{c}"></div><span class="bar-label">{val}</span></div>'

def hcolor(s):
    if s >= 4.5: return "#2E7D32"
    if s >= 3.5: return "#558B2F"
    if s >= 2.5: return "#F9A825"
    if s >= 1.5: return "#EF6C00"
    return "#C62828"

esc = lambda s: str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

# ── Build HTML ──
H = []

H.append(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>工程控制论 Skill 审计报告 — {iso_date}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Noto Sans SC',-apple-system,BlinkMacSystemFont,sans-serif;background:#F5F5F0;color:#333;line-height:1.6;padding:20px}}
.container{{max-width:1400px;margin:0 auto}}
.header{{background:#fff;border-radius:12px;padding:40px;margin-bottom:24px;box-shadow:0 1px 3px rgba(0,0,0,.08);border-left:6px solid #1565C0}}
.header h1{{font-size:32px;font-weight:900;color:#1565C0;margin-bottom:8px}}
.header .subtitle{{font-size:16px;color:#666}}
.meta-strip{{display:flex;gap:24px;margin-top:16px;flex-wrap:wrap}}
.meta-item{{background:#E3F2FD;padding:8px 16px;border-radius:20px;font-size:14px;font-weight:500;color:#1565C0}}
.meta-item.warn{{background:#FFF3E0;color:#E65100}}
.card{{background:#fff;border-radius:12px;padding:28px;margin-bottom:24px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.card h2{{font-size:22px;font-weight:700;color:#333;margin-bottom:20px;padding-bottom:12px;border-bottom:2px solid #E8E8E0}}
.card h3{{font-size:17px;font-weight:600;color:#555;margin:16px 0 12px}}
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}
@media(max-width:900px){{.grid-2{{grid-template-columns:1fr}}}}
.bar-bg{{background:#EEE;border-radius:4px;height:22px;position:relative;overflow:hidden;min-width:60px}}
.bar-fill{{height:100%;border-radius:4px}}
.bar-label{{position:absolute;left:8px;top:1px;font-size:12px;font-weight:600;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.3)}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th{{background:#F0F0E8;padding:10px 12px;text-align:left;font-weight:600;color:#555;border-bottom:2px solid #DDD;position:sticky;top:0;white-space:nowrap}}
td{{padding:8px 12px;border-bottom:1px solid #EEE;vertical-align:middle}}
tr:hover{{background:#FAFAF5}}
.table-wrap{{max-height:600px;overflow-y:auto;border:1px solid #EEE;border-radius:8px}}
.table-wrap.big{{max-height:800px}}
.skill-cards{{display:flex;flex-wrap:wrap;gap:8px}}
.skill-card{{display:flex;align-items:center;gap:8px;padding:8px 14px;border-radius:8px;font-size:13px;background:#F5F5F0}}
.skill-card.top{{border-left:4px solid #2E7D32}}
.skill-card.bottom{{border-left:4px solid #C62828}}
.skill-card .rank{{font-weight:900;font-size:16px;color:#999;min-width:28px}}
.skill-card .skill-name{{font-weight:600;color:#333}}
.skill-card .skill-cat{{color:#888;font-size:11px}}
.skill-card .skill-score{{margin-left:auto;font-weight:700;font-size:16px}}
.issues-list{{list-style:none;padding:0}}
.issues-list li{{padding:10px 16px;margin-bottom:8px;background:#FFF8E1;border-left:4px solid #FF8F00;border-radius:4px;font-size:14px}}
.wbox{{background:#FFF3E0;border-left:4px solid #E65100;padding:16px 20px;border-radius:8px;margin-bottom:12px;font-size:14px}}
.wbox strong{{color:#E65100}}
.gbox{{background:#E8F5E9;border-left:4px solid #2E7D32;padding:16px 20px;border-radius:8px;margin-bottom:12px;font-size:14px}}
.footer{{text-align:center;color:#999;font-size:13px;padding:30px}}
.footer strong{{color:#666}}
</style>
</head>
<body>
<div class="container">
""")

# Header
H.append('<div class="header">')
H.append('<h1>\U0001F4CA 工程控制论 Skill 审计报告</h1>')
H.append('<div class="subtitle">基于钱学森、宋健《工程控制论》第三版 14 条核心原则</div>')
H.append('<div class="meta-strip">')
H.append(f'<span class="meta-item">\U0001F4C5 {iso_date}</span>')
H.append(f'<span class="meta-item">\U0001F4E6 {len(all_data)} 个 Skill</span>')
H.append(f'<span class="meta-item">\U0001F4C2 {len(cat_count)} 个类别</span>')
H.append('<span class="meta-item">\u2705 5 维度评估</span>')
if nf:
    H.append(f'<span class="meta-item warn">\u26A0\uFE0F {len(nf)} 个幽灵 Skill</span>')
H.append('</div></div>')

# Overview + Distribution
H.append('<div class="grid-2">')
H.append('<div class="card"><h2>\U0001F4C8 整体评分概览</h2><table>')
H.append('<tr><th>维度</th><th style="width:70%">平均分</th></tr>')
for dm in DIMS:
    H.append(f'<tr><td style="font-weight:600">{DIM_LABEL[dm]}</td><td>{hbar(avgs[dm], c=DIM_COL[dm])}</td></tr>')
H.append('</table>')
H.append(f'<div style="margin-top:12px;font-size:14px;color:#666"><strong>总体平均：{overall_avg} / 5</strong></div>')
H.append('</div>')

H.append('<div class="card"><h2>\U0001F3AF 维度分数分布</h2><table>')
H.append('<tr><th>维度</th><th>1分</th><th>2分</th><th>3分</th><th>4分</th><th>5分</th></tr>')
for dm in DIMS:
    dist = Counter()
    for sk in scored:
        dist[sk[dm]] += 1
    cells = "".join(f"<td>{dist.get(s, 0)}</td>" for s in range(1, 6))
    H.append(f"<tr><td>{DIM_LABEL[dm]}</td>{cells}</tr>")
H.append('</table></div></div>')

# Principles
most_covered = pcount.most_common(3) if pcount else []
least_covered = sorted(pcount.items(), key=lambda x: x[1])[:3]
top_p_str = "、".join(f"P{p}={PNAMES[p]}" for p, _ in most_covered)
bot_p_str = "、".join(f"P{p}={PNAMES[p]}" for p, _ in least_covered)
H.append('<div class="card"><h2>\\U0001F9EC 14条核心原则覆盖度</h2>')
H.append(f'<p style="font-size:14px;color:#666;margin-bottom:16px">最常体现：<strong>{top_p_str}</strong>；最少体现：<strong>{bot_p_str}</strong>。</p>')
H.append('<table>')
mp_val = max(pcount.values()) if pcount else 1
for p in range(1, 15):
    cnt = pcount.get(p, 0)
    H.append(f'<tr><td style="white-space:nowrap">P{p}: {PNAMES[p]}</td><td style="width:100%">{hbar(cnt, mx=mp_val, c="#4A90D9")}</td></tr>')
H.append('</table></div>')

# Top/Bottom
def scards(lst, cls):
    r = '<div class="skill-cards">'
    for i, sk in enumerate(lst):
        rank = f"#{i+1}" if cls == "top" else f"#{len(scored)-i}"
        r += f'<div class="skill-card {cls}"><span class="rank">{rank}</span><span class="skill-name">{sk["name"]}</span><span class="skill-cat">{sk["category"]}</span><span class="skill-score">{sk["_total"]}</span></div>'
    r += '</div>'
    return r

H.append('<div class="grid-2">')
H.append('<div class="card"><h2>\U0001F3C6 Top 10 评分最高</h2>' + scards(top10, 'top') + '</div>')
H.append('<div class="card"><h2>\u26A0\uFE0F Bottom 10 评分最低</h2>' + scards(bot10, 'bottom') + '</div>')
H.append('</div>')

# Not Found
if nf:
    H.append('<div class="card"><h2>\U0001F47B 幽灵 Skill（SKILL NOT FOUND）</h2>')
    H.append('<div class="wbox">以下 skill 存在于 available_skills 列表但磁盘无对应 SKILL.md 文件。</div>')
    H.append('<ul class="issues-list">')
    for x in nf:
        H.append(f'<li><strong>{x["name"]}</strong> ({x["category"]}) — available_skills 列表中存在但磁盘无对应文件</li>')
    H.append('</ul></div>')

# Category table
H.append('<div class="card"><h2>\U0001F4C2 按类别评分</h2><div class="table-wrap"><table>')
header = '<tr><th>类别</th><th>数量</th><th>总分</th>' + "".join(f"<th>{DIM_LABEL[dm]}</th>" for dm in DIMS) + '</tr>'
H.append(header)
for c, cnt in sorted(cat_count.items()):
    av = cat_avg[c]
    t = round(sum(av.values())/5, 2)
    row = f'<tr><td>{c}</td><td>{cnt}</td><td style="font-weight:bold;color:{hcolor(t)}">{t}</td>'
    for dm in DIMS:
        row += f'<td>{hbar(av[dm], c=DIM_COL[dm])}</td>'
    row += '</tr>'
    H.append(row)
H.append('</table></div></div>')

# All skills detail
H.append('<div class="card"><h2>\U0001F4CB 全部 Skill 评分明细</h2><div class="table-wrap big"><table>')
header = '<tr><th>Skill</th><th>类别</th><th>总分</th>' + "".join(f"<th>{DIM_LABEL[dm]}</th>" for dm in DIMS) + '<th>体现原则</th><th>缺陷/建议</th></tr>'
H.append(header)
for sk in scored:
    t = sk["_total"]
    row = f'<tr><td>{sk["name"]}</td><td>{sk["category"]}</td><td style="font-weight:bold;color:{hcolor(t/5)}">{t}</td>'
    for dm in DIMS:
        row += f'<td>{hbar(sk[dm], c=DIM_COL[dm])}</td>'
    prs = ",".join(f"P{p}" for p in sk.get("principles", [])) or "\u2014"
    iss = esc(sk.get("issues", "\u65E0")[:80])
    for dm in DIMS:
        note_key = f"{dm}_note"
        if note_key not in sk:
            sk[note_key] = "SKILL NOT FOUND" if sk[dm] == 0 else ""
    iss_s = 'color:#888' if iss == "\u65E0" else 'color:#C62828'
    row += f'<td style="font-size:11px">{prs}</td><td style="font-size:11px;{iss_s}">{iss}</td></tr>'
    H.append(row)
H.append('</table></div></div>')

# Build findings from data (data-driven, not hardcoded)
cat_total = {c: round(sum(av.values())/5, 2) for c, av in cat_avg.items()}
strong_cats = sorted(cat_total.items(), key=lambda x: x[1], reverse=True)
strong_cats_top = strong_cats[:3]
weak_cats_candidates = [(c, s) for c, s in cat_total.items() if s < 3.0]
if not weak_cats_candidates:
    weak_cats_candidates = sorted(cat_total.items(), key=lambda x: x[1])[:3]
worst_dim = min(avgs.items(), key=lambda x: x[1])
least_covered_p = sorted(pcount.items(), key=lambda x: x[1])[:3]
low_closure = [d for d in all_data if d["closure"] <= 2 and d["closure"] > 0]
low_stability = [d for d in all_data if d["stability"] <= 2 and d["stability"] > 0]

# Findings
H.append('<div class="card"><h2>\\U0001F50D 系统性发现与改进建议</h2>')

H.append('<h3>1. 整体健康度</h3>')
H.append(f'<p style="font-size:14px;color:#666;margin-bottom:12px">5 维度总平均 <strong>{overall_avg}/5</strong>。最大短板：<strong>{DIM_LABEL[worst_dim[0]]}（{avgs[worst_dim[0]]}）</strong>。</p>')

H.append('<h3>2. 强项类别</h3>')
for c, s in strong_cats_top:
    weaknesses = [dm for dm in DIMS if cat_avg[c][dm] < 3.0]
    weak_str = f"，弱项：{', '.join(DIM_LABEL[w] for w in weaknesses)}" if weaknesses else ""
    H.append(f'<div class="gbox"><strong>{c}（均分 {s}）</strong>：包含多个评分较高的 skill{weak_str}。</div>')

H.append('<h3>3. 弱项类别</h3>')
for c, s in weak_cats_candidates:
    H.append(f'<div class="wbox"><strong>{c}（均分 {s}）</strong>：多为纯工具手册模式，缺乏反馈闭环。建议增加\\u201c操作\\u2192确认\\u201d闭环和错误恢复。</div>')

H.append('<h3>4. 被忽视的原则</h3>')
H.append('<ul class="issues-list">')
for p, cnt in least_covered_p:
    H.append(f'<li><strong>P{p} {PNAMES[p]}（{cnt} skills）</strong>：极少数 skill 体现该原则。</li>')
H.append('</ul>')

H.append('<h3>5. 共性改进方向</h3>')
H.append('<ul class="issues-list">')
pct_low = round(len(low_closure)/len(scored)*100) if scored else 0
H.append(f'<li><strong>增加验证闭环</strong>：{len(low_closure)} 个 skill（{pct_low}%）闭环完整性\\u22642，缺少\\u201c执行后验证\\u201d步骤。</li>')
H.append('<li><strong>提升可观测性</strong>：工具类 skill 应输出结构化结果（JSON），而非纯文本。</li>')
H.append(f'<li><strong>增加错误恢复</strong>：{len(low_stability)} 个 skill 稳定性\\u22642，pitfalls 偏重列举而缺少恢复方案。</li>')
H.append('<li><strong>跨 skill 集成</strong>：当前 skill 间几乎无协调设计，缺乏大系统观视角。</li>')
if nf:
    H.append(f'<li><strong>清理幽灵 skill</strong>：{len(nf)} 个 skill 存在于 catalog 但无文件，建议从 available_skills 列表清除。</li>')
H.append('</ul>')
H.append('</div>')

# Footer
H.append(f'<div class="footer"><p>工程控制论 Skill 审计报告 | {iso_date}</p>')
H.append('<p>基于 <strong>钱学森、宋健《工程控制论》第三版</strong> 14 条核心原则</p></div>')
H.append('</div></body></html>')

html = "\n".join(H)
html_path = os.path.join(report_dir, f"cybernetics_audit_{date_str}.html")
os.makedirs(report_dir, exist_ok=True)
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"HTML: {html_path} ({len(html)} chars)")
print("DONE")
