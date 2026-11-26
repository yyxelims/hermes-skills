# 多搜索引擎与替代数据源

## 搜索引擎实测对比（2026-08-07）

| 方案 | 中文效果 | 费用 | 限制 | 接入方式 |
|------|:--:|------|------|------|
| **Claw Search** | ✅ 中文可用 | **免费** | 100次/分钟 | `claw-search.com/api/search?q=` |
| 百度 AI Search API | ✅ 最佳 | 免费 | 80次/天 | `qianfan.baidubce.com` |
| 火山引擎 Web Search | ⚠️ 需 Key | — | — | Chat Completions tool |
| DuckDuckGo API | ❌ 无中文 | 免费 | — | `api.duckduckgo.com` |
| Baidu 网页 | ❌ CAPTCHA | — | — | 直接抓取 |
| Sogou 网页 | ❌ 反爬 | — | — | 直接抓取 |
| Google 网页 | ❌ IP封禁 | — | — | 直接抓取 |
| Bing 网页 | ❌ 中文结果差 | — | — | 直接抓取 |
| Brave Search API | ⚠️ 需 key | 免费2000次/月 | — | `api.search.brave.com` |

> **策略**：Claw Search（免费无限，100次/分钟）→ 百度 AI Search（兜底，80次/天）。`search_fallback.py` 自动双引擎切换。

## Claw Search

开源免费搜索引擎，国内服务器部署，兼容 Brave Search 格式。

- **网站**：https://www.claw-search.com/
- **端点**：`GET https://www.claw-search.com/api/search?q=keyword`
- **其他端点**：`/api/images?q=`、`/api/news?q=`、`/api/suggest?q=`
- **限额**：免费，100 次/分钟，无需 API Key
- **响应格式**：
```json
{
  "query": "OpenClaw AI",
  "web": {
    "results": [
      {"title": "...", "url": "https://...", "description": "..."}
    ]
  }
}
```
- **状态**：2026-08-07 实测 API 返回 502（服务可能暂时不可用），静默降级到百度。

## 火山引擎 Web Search（字节跳动）

**产品定位**：字节跳动官方搜索能力输出，基于头条/抖音全网内容索引。

- **入口**：火山方舟 → 工具调用 → Web Search（联网内容插件）
- **API 地址**：`https://ark.cn-beijing.volces.com/api/v3`
- **认证**：火山引擎 API Key（控制台获取）
- **调用方式**：作为 Chat Completions 的 tool/plugin，不是独立搜索 REST API
- **优势**：头条号、地方政务新媒体、行业自媒体转载内容收录丰富

```python
from volcenginesdkarkruntime import Ark

client = Ark(
    base_url='https://ark.cn-beijing.volces.com/api/v3',
    api_key=***('ARK_API_KEY'),
)

response = client.chat.completions.create(
    model="doubao-seed-2-1-pro-260628",
    messages=[{"role": "user", "content": "搜索关键词"}],
    tools=[{"type": "web_search"}]
)
```

## 替代数据源（正文抓取失败时使用）

| 文档类型 | 替代URL | 格式 |
|---------|---------|:--:|
| 支付体系运行报告（季度） | `pbc.gov.cn/zhifujiesuansi/128525/128545/128643/` | PDF |
| 支付体系发展报告（年度） | `pbc.gov.cn/zhifujiesuansi/128525/128545/128645/` | PDF |
| 一般政策文件 | `gov.cn` + `baijiahao.baidu.com` 站内搜索 | HTML |
| 人行支付结算司报告 | 百度 AI 搜索 `"支付体系运行总体情况" site:pbc.gov.cn` | PDF 下载链接 |

## search_fallback.py 逻辑

流水线位置：LLM 摘要之后、build_final 之前。

**双引擎策略**：Claw Search（优先，免费无限）→ 百度 AI Search（兜底，80次/天）

**检测条件**（满足任一即触发搜索）：
- body < 100 字
- LLM 摘要含"正文未成功抓取"
- LLM 摘要含导航关键词（"页面框架"/"导航结构"/"RSS订阅"/"栏目设置"等 12 个）
- body 含"当前位置"+"首页"且 < 300 字

**排除条件**（不搜索）：
- safe.gov.cn 导航页（zcxmzh/hwmywhgl/grjcxmwhgl 等路径）
- 裸 `/index.html`（不含日期 ID 模式如 `/20260729.../index.html`）—— ⚠️ 必须用正则 `/\\d{6,}/index\\.html$` 区分文章页和目录首页

**配额管理**：
- Claw：100次/分钟，无日限
- 百度：80次/天，超限自动停止，标记剩余篇数
- 双引擎均失败 → 标记"无搜索结果"，不影响流水线继续
