#!/usr/bin/env python3
"""Standalone AI HOT daily report generator. Usage: python ai_daily.py [YYYY-MM-DD] [--open]. Zero dependencies beyond stdlib."""
import json, os, ssl, sys, urllib.request
from datetime import datetime, timezone, timedelta

API_BASE = "https://aihot.news/api/v1"
OUTPUT_DIR = os.path.expanduser("~/Documents/本地/ai探索/AI日报")
BEIJING_TZ = timezone(timedelta(hours=8))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/YOUR_SERVER_IP Safari/537.36"
CAT_MAP = {"模型发布/更新":("cat-model","模型"),"产品发布/更新":("cat-product","产品"),"行业动态":("cat-industry","行业"),"论文研究":("cat-paper","论文"),"技巧与观点":("cat-tip","观点")}

def fetch_daily(date=None):
    url = f"{API_BASE}/dailies/{date}" if date else f"{API_BASE}/dailies/latest"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        d = json.loads(resp.read())
    return d.get("report") or d


def _src(it):
    s = it.get("source")
    if isinstance(s, dict):
        return (s.get("name") or "").strip()
    return (s or it.get("sourceName") or "").strip()


def _url(it):
    ln = it.get("links") or {}
    if isinstance(ln, dict):
        return ln.get("original") or ln.get("aihot") or "#"
    return it.get("sourceUrl") or it.get("url") or "#"

def smart_truncate(text, soft_limit=150):
    if not text or len(text) <= soft_limit: return text
    candidates = []
    for sep in ["。","！","？","；"]:
        idx = text.rfind(sep, 0, soft_limit + 60)
        if idx >= soft_limit - 40: candidates.append(idx)
    if candidates: return text[:max(candidates)+1] + "…"
    comma = text.rfind("，", 0, soft_limit)
    if comma >= soft_limit - 40: return text[:comma] + "…"
    return text[:soft_limit] + "…"

def build_html(daily):
    date_str = daily["date"]
    num = 1
    sections_html = ""
    for sec in daily.get("sections", []):
        if not sec.get("items"): continue
        css, tag = CAT_MAP.get(sec["label"], ("cat-industry","行业"))
        items = ""
        for item in sec["items"]:
            t = item.get("title",""); u = _url(item); s = _src(item)
            summary = smart_truncate(item.get("summary") or "")
            items += f"""\n      <div class="item">
        <div class="item-header"><span class="item-num">{num}</span><span class="item-title"><a href="{u}" target="_blank">{t}</a></span><span class="category-tag {css}">{tag}</span></div>
        <div class="item-meta"><span class="source">{s}</span></div>
        <div class="item-summary">{summary}</div></div>"""
            num += 1
        sections_html += f"""\n  <div class="section"><div class="section-title">{sec["label"]} · {len(sec["items"])} 条</div>{items}\n  </div>"""
    lead_html = ""
    if daily.get("lead"):
        l = daily["lead"]
        lead_html = f"""<div class="flash-section" style="margin-bottom:20px"><div style="font-size:14px;color:var(--text-secondary);line-height:1.8"><strong>📰 主编点评：</strong>{l.get("title","")}<br>{l.get("leadParagraph","")}</div></div>"""
    flash_html = ""
    if daily.get("flashes"):
        items = "".join(f'<div class="flash-item">· <a href="{_url(f)}" target="_blank">{f["title"]}</a> — {_src(f)}</div>' for f in daily["flashes"])
        flash_html = f"""<div class="flash-section"><div class="section-title">⚡ 快讯 · {len(daily["flashes"])} 条</div>{items}</div>"""
    total = num - 1
    now_str = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M")
    # CSS truncated for brevity — see SKILL.md template for full responsive CSS
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>AI HOT 日报 · {date_str}</title>
<style>@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
:root{{--bg:#fff;--text:#1a1a2e;--text2:#555;--accent:#ff2442;--border:#e8e8e8;--card:#f8f9fb;--tm:#eff6ff;--tp:#f0fdf4;--ti:#fefce8;--tpp:#f5f3ff;--tt:#fff7ed}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Noto Sans SC',-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg);color:var(--text);line-height:1.8;max-width:900px;margin:0 auto;padding:32px 24px 60px}}
.header{{text-align:center;padding:32px 0 24px;border-bottom:2px solid var(--accent);margin-bottom:32px}}
.header .badge{{display:inline-block;background:var(--accent);color:#fff;font-size:12px;padding:3px 14px;border-radius:20px;margin-bottom:10px;letter-spacing:1px}}
.header h1{{font-size:26px;font-weight:700}}.header .meta{{font-size:13px;color:var(--text2);margin-top:6px}}
.section{{margin:32px 0}}.section-title{{font-size:18px;font-weight:700;padding-left:12px;border-left:4px solid var(--accent);margin-bottom:16px}}
.item{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:18px 20px;margin-bottom:14px}}
.item:hover{{box-shadow:0 2px 12px rgba(0,0,0,.06)}}
.item-header{{display:flex;align-items:baseline;gap:10px;margin-bottom:8px}}
.item-num{{font-size:13px;font-weight:700;color:var(--accent);min-width:28px;text-align:right}}
.item-title{{font-size:15px;font-weight:600;color:var(--text);line-height:1.5}}
.item-title a{{color:inherit;text-decoration:none}}.item-title a:hover{{text-decoration:underline;color:var(--accent)}}
.item-meta{{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-bottom:6px;font-size:12px;color:var(--text2);padding-left:38px}}
.item-summary{{font-size:13px;color:var(--text2);line-height:1.7;padding-left:38px;margin-top:4px}}
.category-tag{{display:inline-block;font-size:11px;padding:1px 8px;border-radius:10px;font-weight:500;margin-left:6px}}
.cat-model{{background:var(--tm);color:#2563eb}}.cat-product{{background:var(--tp);color:#059669}}
.cat-industry{{background:var(--ti);color:#a16207}}.cat-paper{{background:var(--tpp);color:#7c3aed}}.cat-tip{{background:var(--tt);color:#c2410c}}
.flash-section{{background:linear-gradient(135deg,#fff1f2,#fce4e6);border:1px solid #fecdd3;border-radius:10px;padding:18px 22px;margin:28px 0}}
.flash-section .section-title{{border-left-color:#fb7185;font-size:16px}}
.flash-item{{padding:4px 0;font-size:13px;color:var(--text2)}}.flash-item a{{color:var(--accent)}}
.footer{{margin-top:48px;padding-top:20px;border-top:1px solid var(--border);font-size:12px;color:#bbb;text-align:center}}
.stats-bar{{text-align:center;font-size:13px;color:var(--text2);padding:8px 0;margin-bottom:8px}}
@media(max-width:768px){{body{{padding:20px 14px 40px}}.header{{padding:20px 0 16px;margin-bottom:20px}}.header h1{{font-size:20px}}.header .meta{{font-size:12px}}.section{{margin:20px 0}}.section-title{{font-size:15px}}.item{{padding:14px 14px;margin-bottom:10px}}.item-header{{flex-wrap:wrap;gap:6px}}.item-num{{font-size:12px;min-width:22px}}.item-title{{font-size:14px}}.item-meta{{padding-left:28px;font-size:11px}}.item-summary{{padding-left:28px;font-size:12px}}.category-tag{{font-size:10px;padding:1px 6px}}.flash-section{{padding:14px 14px}}.flash-item{{font-size:12px}}.stats-bar{{font-size:12px}}.footer{{font-size:11px}}}}
@media(max-width:400px){{body{{padding:14px 10px 30px}}.header h1{{font-size:18px}}.section-title{{font-size:14px}}.item{{padding:10px 10px}}.item-title{{font-size:13px}}.item-meta{{padding-left:22px}}.item-summary{{padding-left:22px}}}}
</style></head><body>
<div class="header"><div class="badge">AI 行业资讯</div><h1>AI HOT 日报 · {date_str}</h1><div class="meta">UTC {daily["windowStart"][:10]} ~ {daily["windowEnd"][:10]} · 北京时间每天 08:00 更新 · 共 {total} 条</div></div>
<div class="stats-bar">共 {total} 条，按版块分类</div>
{lead_html}{sections_html}{flash_html}
<div class="footer">数据来源：AIHOT (aihot.news) · 生成时间：{now_str}（北京时间）</div>
</body></html>"""

def main():
    date_arg = None; open_browser = False
    for a in sys.argv[1:]:
        if a == "--open": open_browser = True
        elif a.startswith("20"): date_arg = a
        else: print(f"用法: python3 {sys.argv[0]} [YYYY-MM-DD] [--open]"); sys.exit(1)
    try: daily = fetch_daily(date_arg)
    except urllib.error.HTTPError as e:
        if e.code == 404: print(f"错误：{date_arg or '今天'} 的日报尚未生成"); sys.exit(1)
        raise
    except Exception as e: print(f"网络错误：{e}"); sys.exit(1)
    date_str = daily["date"]; html = build_html(daily)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outpath = os.path.join(OUTPUT_DIR, f"AI日报_{date_str}.html")
    with open(outpath,"w",encoding="utf-8") as f: f.write(html)
    total = sum(len(s.get("items",[])) for s in daily.get("sections",[]))
    print(f"✅ AI 日报已生成\n   日期: {date_str}  |  共 {total} 条  |  {len(daily.get('sections',[]))} 个版块\n   文件: {outpath}")
    if open_browser: import webbrowser; webbrowser.open(f"file://{outpath}")

if __name__ == "__main__": main()
