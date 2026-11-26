# 并发详情页抓取模式

## 背景

列表页抓取只能拿到标题+日期+URL，Excel 需要的"核心内容摘要"和"关键时间节点"必须从详情页正文提取。776 篇文章逐一抓取耗时太长，需要并发。

## 方案：ThreadPoolExecutor(3 workers)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=3) as pool:
    futures = {pool.submit(process_one, art, i, total): i for i, art in enumerate(tasks)}
    for f in as_completed(futures):
        results.append(f.result())
```

## 性能

- 776 篇文章，3 并发，47 秒完成（16.5 篇/秒）
- 526/776 (68%) 成功获取正文
- 116 篇提取到关键时间节点

## 正文提取策略

```python
def extract_from_html(html):
    # 1. 标题：<h1> 优先，<title> 备选
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    # 2. 正文：<article>/<main>/class=content 等优先
    # 3. 日期：(\d{4}年\d{1,2}月\d{1,2}日) regex
    # 4. 文号：从标题+正文前500字提取
```

## 覆盖率限制

~32% 的页面拿不到正文，原因：
- 部分 URL 不可达（政府网站临时不可用）
- 页面结构不匹配（无标准 article/content div）
- nfra.gov.cn 的 Angular SPA 页面用 urllib GET 返回空壳

这些文章回退到模板摘要（gen_summary）。
