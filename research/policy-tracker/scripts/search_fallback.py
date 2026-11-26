#!/usr/bin/env python3
"""搜索兜底脚本模板 — 多引擎策略：SearXNG(本地)→百度 AI Search(兜底)
复制到项目脚本/目录使用，按实际环境修改 SEARXNG 地址和 API key 路径。
"""
import json, os, sys, time, re, ssl, urllib.request, urllib.parse

# === 配置区（按实际环境修改） ===
DATA_DIR = '/path/to/政策动态追踪/数据'
INPUT_FILE = os.path.join(DATA_DIR, 'detail_pages_llm_v2.json')
SEARXNG_URL = 'http://localhost:8080'  # SearXNG Docker 地址，无则为空
BAIDU_API_KEY = ''  # 百度 AI Search API key
DAILY_LIMIT = 80

_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE


def searxng_search(query):
    """本地 SearXNG — 百度+搜狗，无限额（但3次后封IP 3600s）"""
    if not SEARXNG_URL:
        return ''
    try:
        q = urllib.parse.quote(query)
        url = f'{SEARXNG_URL}/search?q={q}&format=json&engines=baidu,sogou&language=zh-CN'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urllib.request.urlopen(req, timeout=15, context=_SSL)
        data = json.loads(r.read())
        texts = []
        for item in data.get('results', [])[:5]:
            title = item.get('title', '') or ''
            content = item.get('content', '') or ''
            snippet = f"{title}：{content}"[:300] if content else title[:200]
            if len(snippet) > 20:
                texts.append(snippet)
        return ' | '.join(texts)[:400] if texts else ''
    except Exception:
        return ''


def baidu_search(query):
    """百度 AI Search API — 80次/天"""
    try:
        sys.path.insert(0, '/Users/you/quant-lab')
        from baidu_search import search
        r = search(query)
        texts = []
        if r.get('summary'):
            texts.append(r['summary'])
        for ref in r.get('references', [])[:3]:
            content = ref.get('content', '') or ''
            if len(content) > 30:
                texts.append(content[:300])
        return ' '.join(texts)[:400] if texts else ''
    except Exception:
        return ''


def search_best(query):
    """SearXNG(优先) → 百度(兜底)"""
    result = searxng_search(query)
    if result and len(result) > 50:
        return result, 'searxng'
    result = baidu_search(query)
    if result and len(result) > 50:
        return result, 'baidu'
    return '', 'none'


if __name__ == '__main__':
    with open(INPUT_FILE) as f:
        articles = json.load(f)

    # 检测需要搜索兜底的文章（body<100字/summary含导航关键词）
    todo = []
    for d in articles:
        body = str(d.get('detail_body', '') or '')
        summary = str(d.get('llm_summary', '') or '')
        title = str(d.get('title', '') or '')
        
        needs = False
        if len(body) < 100:
            needs = True
        elif any(kw in summary for kw in ['网站导航', '页面框架', '导航CSS', 'RSS订阅']):
            needs = True
        
        if needs and title and len(title) > 5:
            todo.append(d)

    print(f'需搜索补全: {len(todo)}篇')

    fixed = 0
    baidu_used = 0
    stats = {'searxng': 0, 'baidu': 0, 'none': 0}

    for i, d in enumerate(todo):
        title = d.get('title', '')[:120]
        result, source = search_best(title)
        
        if source == 'baidu':
            baidu_used += 1
            if baidu_used > DAILY_LIMIT:
                print(f'百度额度用完，剩余{len(todo)-i}篇跳过')
                break
        
        stats[source] += 1
        
        if result and len(result) > 50:
            d['llm_summary'] = result
            fixed += 1
            print(f'  [{i+1}/{len(todo)}] ✅ [{source}] {title[:40]}')
        else:
            print(f'  [{i+1}/{len(todo)}] ❌ {title[:40]}')
        
        time.sleep(0.3)

    with open(INPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=1)

    print(f'\n修复: {fixed}/{len(todo)}篇')
    print(f'来源: SearXNG={stats["searxng"]}, 百度={stats["baidu"]}')
