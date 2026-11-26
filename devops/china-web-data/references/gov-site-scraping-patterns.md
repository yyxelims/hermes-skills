# Chinese Government Site Scraping Patterns

> 基于2026-08-03对26个中国政府网站的全量抓取测试总结。

## 已验证可抓取的政府网站（urllib + BS4/regex）

| 网站 | 编码 | 方法 | 提取率 |
|------|------|------|:---:|
| pbc.gov.cn (人行) | **GBK** | BS4 | 高 |
| beijing.gov.cn (首都之窗) | UTF-8 | BS4 | 高 |
| samr.gov.cn (市场监管总局) | UTF-8 | BS4 | 高 |
| safe.gov.cn (外汇局) | UTF-8 | BS4 | 高 |
| cca.org.cn (中消协) | UTF-8 | BS4 | 高 |
| jrj.beijing.gov.cn (北京金融局) | UTF-8 | regex | 中 |
| beijing.pbc.gov.cn (人行北京分行) | UTF-8 | regex | 中 |

## 需要Browser/Playwright的站点

| 网站 | 原因 | 实测结果 |
|------|------|---------|
| nfra.gov.cn (金融监管总局) | Angular SPA，子页面302→404 | ✅ Browser实测通过。**首页即含全部最新内容**：政策法规6-7篇(+日期)、公告6篇(+日期)、监管动态8篇(+日期)、5位总局领导(丁向群局长+4副局长)。通过首页导航点击获取。文章详情URL: `/cn/view/pages/ItemDetail.html?docId={docId}` |
| nucc.com (网联) | 543B JS壳，Vue SPA | ✅ Browser实测通过。新闻中心3个Tab (公司新闻/媒体报道/行业动态)，每页3篇×7页≈21篇。文章含日期(MM/DD)和标题，转自人行重大政策。 |
| xzxk.pbc.gov.cn (人行行政许可) | JSF应用 | ✅ Browser实测通过首页。公开可见**11类行政审批事项**：人民币图样使用、黄金进出口、债券市场备案、银行结算账户许可、**非银行支付机构行政许可**(⭐)、**银行卡清算机构准入**(⭐)、个人征信机构审批等。每项含服务指南+线上办理入口。许可证详情和公示需登录。 |
| unionpay.com.cn (银联) | SSL证书CN不匹配 | ❌ Browser也失败: `ERR_CERT_COMMON_NAME_INVALID`。证书的 Common Name 与实际域名不匹配，无法建立HTTPS连接。 |
| gsxt.gov.cn (企业信用) | Cloudflare 521 | ❌ 需突破CF防护 |
| creditchina.gov.cn (信用中国) | WAF 412 | ❌ 需突破WAF |

## 编码处理模板

```python
import urllib.request

body = resp.read()
for enc in ['utf-8', 'gbk', 'gb2312']:
    try:
        html = body.decode(enc)
        break
    except:
        continue
else:
    html = body.decode('utf-8', errors='ignore')
```

## macOS SSL fix（必须）

```python
import ssl
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
```

## 政府网站文章提取的可靠正则

```python
# 标准政府文章格式: <a href="tYYYYMMDD_数字.html">标题</a>
articles = re.findall(
    r'<a[^>]*href=["\']([^"\']*(?:t?\d{6,10}[_/]\d+)[^"\']*\.html?[^"\']*)["\'][^>]*>\s*([\u4e00-\u9fa5][^<]{5,120})</a>',
    html
)
```

## 核心工作原则

### 数据交付原则
- **用户输入"抓数据" = 必须交付原文内容/逐条列表**。Excel 不能只有统计数字或摘要。
- ✅ 正确：每篇文章放日期+标题+**正文内容**（非仅URL）
- ❌ 错误："共抓取XX条，详见某文件..." 或只放链接列表
- **内容优先于 URL**：用户要的是正文内容，不是链接列表。

### 一次到位工作流
- 写好完整脚本 → 直接运行 → 交付结果。不接受逐步试错、不接受长篇解释后再改。

## pbc.gov.cn 详情页反爬

- **列表页可正常抓取**：提取标题+日期+URL 无问题
- **详情页有重定向循环**：urllib 返回 `HTTP Error 302: infinite loop`
- **正文通常为附件**：pbc.gov.cn 公告正文多为 `.xls`/`.doc` 附件链接，非 HTML 文章
- **如必须抓正文**：必须用 Browser，且大部分公告只有标题+附件，没有内联正文

## 网站改名/域名变更记录

- "北京市地方金融监督管理局" → "中共北京市委金融委员会办公室"（jrj.beijing.gov.cn）
- "网联清算有限公司" 域名 nhunionpay.com → nucc.com
- **对策**: 每个URL先用 HTTP HEAD/GET 验证，失败的不要假设路径正确

## 日期提取策略

1. **优先从URL中提取日期**（如 `t20260708_4752133.html` → `2026-07-08`）
2. 其次从页面文本中用 regex `\d{4}[-/]\d{2}[-/]\d{2}` 提取
3. 避免用页面元素定位日期（不同网站差异太大）

## 领导名单提取模板

```json
{"leaders": [{"name": "潘功胜", "position": "行长", "url": "..."}]}
```

## 数据提取模板

### 政策/公告列表 → 提取字段
```json
{"articles": [{"title": "...", "date": "2026-07-08", "url": "..."}]}
```

### Excel汇报格式（3个Sheet）
1. **抓取结果汇总**: 序号/来源/用途/URL/HTTP状态/方法/数据类型/提取字段/可定时抓取/备注
2. **数据详情**: 每个核心数据源的具体提取内容
3. **抓取方法总结**: 3种方法的适用站点、优缺点、代码示例

## 快速决策树

```
URL可访问（200）?
├─ 返回内容 > 5KB HTML? → urllib + BS4 ✅
│  └─ BeautifulSoup未安装? → urllib + regex ✅
├─ 返回内容 < 2KB（JS壳）? → Browser/Playwright ⚠️
└─ 返回404/403/521?
   ├─ 尝试加Referer头和完整浏览器UA
   ├─ 尝试 http → https 或反之
   ├─ 尝试从首页导航找到新URL
   └─ 仍失败 → 标记为"需人工确认"
```

## Advanced Patterns (2026-08-06)

### Detail Page Concurrent Scraping

When titles on list pages are CSS-truncated (ending with "..."), visit each detail page to get the full title and body text:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=3) as pool:
    futures = {pool.submit(process_one, art, i, total): i for i, art in enumerate(tasks)}
    for f in as_completed(futures):
        results.append(f.result())
```

Typical throughput: ~16 articles/second for 700+ articles.

### Title Recovery from Body Text

Government websites often truncate `<title>` and `<h1>` tags (e.g., "中国人民银行召开2026年下半年工作..."). The full title usually appears in the body's first paragraph:

```python
if title.endswith('...') or title.endswith('…'):
    prefix = title.rstrip('...').rstrip('…')
    if prefix and len(prefix) > 5 and body:
        idx = body.find(prefix)
        if idx >= 0:
            chunk = body[idx:idx+200]
            for end_char in ['。', '！', '？', '\n']:
                ei = chunk.find(end_char, len(prefix))
                if ei > len(prefix):
                    title = chunk[:ei+1].strip()
                    break
```

### URL Fuzzy Matching Across List/Detail Pages

**Critical bug**: the same article can have DIFFERENT URLs in list page vs detail page contexts. Example:
- List page URL: `https://www.pbc.gov.cn/zhifujiesuansi/index.html/goutongjiaoliu/113456/113469/2026080209562668921/index.html`
- Detail page URL: `https://www.pbc.gov.cn/goutongjiaoliu/113456/113469/2026080209562668921/index.html`

The `zhifujiesuansi/index.html/` prefix is injected by the list page. **Always index detail data by article ID** (last numeric path segment), not by full URL:

```python
detail_by_id = {}
for d in detail_data:
    url = d.get('url', '')
    parts = url.rstrip('/').split('/')
    aid = parts[-2] if parts[-1] in ('index.html','index.htm') else parts[-1]
    detail_by_id[aid] = d
```

### pbc.gov.cn 支付结算司 URL Malformation

All detail pages under `pbc.gov.cn/zhifujiesuansi` have broken URLs with a doubled path prefix (`/zhifujiesuansi/index.html/zhifujiesuansi/...`). These detail pages return **404 or timeout** — body text and full titles are unrecoverable from the detail pages. The only available data is the list page title (usually CSS-truncated at ~22 chars). **These articles are accepted as-is with truncated titles.**

### nucc 网联 Tab Scraping Fix

The original regex-based article extraction fails on nucc.com. Use `document.body.innerText` with this pattern:

```python
body = clean_text(await page.evaluate('() => document.body.innerText'))
articles = re.findall(
    r'(\d{1,2})\s+(\d{4}\.\d{2})\s+(.+?)(?=\s*\d{1,2}\s+\d{4}\.\d{2}|\s*(?:1\s*\n|下一页|$))',
    body, re.DOTALL
)
```

### Impact Grading Rules for Regulatory Monitoring

| Level | Leaders | Articles |
|:--:|------|------|
| 🔴 Red | P0 agency (金监总局/人行/外汇局/北京金融局) + 副局长↑ | Formal regulation (办法/规定/管理条例) AND core rule (信用卡息费/收单费率/消金准入) |
| 🟠 Orange | P1 agency (市场监管总局/商务局/发改委/市监局) + 副局长↑ | 征求意见稿 / 行政处罚 / 促消费政策 / 规范性文件 with 信用卡/支付/消金 keywords |
| 🔵 Blue | Others | Others |

### Excel Generation: Follow the Spec EXACTLY

User will reject simplified Excel outputs. The specification must be followed field-by-field:

**Sheet 1**: 20 fields (序号, 信息分类, 发布日期, 涉及单位, 涉及人员, 职务变动, 行政级别, 分管业务领域, 对应卡部业务条线, 对口内部团队, 影响等级, 核心影响摘要, 建议跟进动作, 责任人, 原文链接, 信息来源栏目, 首次抓取时间, 最近更新时间, 跟进状态, 备注)

**Sheet 2**: 16 fields (序号, 资讯类型, 发布日期, 发布单位, 文件文号, 文件标题, 核心业务标签, 核心内容摘要, 关键时间节点, 影响等级, 对我行业务影响, 责任团队, 原文链接, 抓取时间, 跟进状态, 备注)

**Summary generation**: Use body text (first 180 chars) with type prefix like `【规范性文件】` or `【会议】`. Never copy the title as the summary. Auto-detect article type from title keywords.

- 旧 URL 格式 ItemList.html?itemId=XXX **全部返回302→404**
- 新站使用 Angular，首页 `https://www.nfra.gov.cn` 即包含：
  - 政策法规（6-7篇最新，含日期）
  - 公告通知（6篇最新，含日期）
  - 监管动态（8篇最新，含日期）
  - 领导信息（机构概况→总局领导：丁向群、肖远企、丛林、付万军、杨国瑞）
- 文章详情URL格式：`/cn/view/pages/ItemDetail.html?docId={docId}&itemId={itemId}`
- 旧版API模式（CDN缓存）：`{origin}/cn/static/data/{Path}[params].json` — **已变动，不可用**

### nfra.gov.cn ItemId 速查（2026-08实测）

| ItemId | 分类 | 说明 |
|--------|------|------|
| 928 | 政策法规 | 现行规章+规范性文件 |
| 925 | 公告通知 | 行政许可/处罚/人事任免 |
| 917/915 | 新闻资讯 | 总局动态+派出机构动态 |
| 916 | 政策解读 | 答记者问+图解政策 |
| 918 | 总局领导 | **已失效** → 从首页机构概况进入 |

### nfra.gov.cn 文章正文抓取（Browser方式）

```python
# 通过Browser逐篇抓取全文：
# 1. browser_navigate 到 ItemDetail.html?docId=XXXXXX&itemId=XXX
# 2. 等待 Angular 渲染完成
# 3. browser_console 执行 document.body.innerText 提取全文
# 4. 从"发布时间"开始，到"版权与免责声明"结束，提取正文
```
