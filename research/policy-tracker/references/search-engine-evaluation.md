# 搜索引擎 API 方案评估（2026-08-07）

## 结论

从 Hermes 沙箱环境，**仅百度 AI Search API 可靠可用**。所有网页抓取类搜索引擎均被反爬拦截。

## 实测方案

| 方案 | 中文效果 | 费用 | 限制 | 状态 |
|------|:--:|------|------|:--:|
| **百度 AI Search API** | ✅ 最佳 | 免费 | 80次/天 | ✅ 生产 |
| SearXNG（Docker本地） | ✅ | 免费 | ≤3次/小时封IP | ⚠️ ad-hoc |
| Claw Search | ✅ | 免费 | 100次/分钟 | ⚠️ 2026-08-07 502 |
| DuckDuckGo API | ❌ | 免费 | 无中文索引 | ❌ |
| Bing/Baidu/Sogou/Google网页 | ❌ | — | CAPTCHA/反爬/IP封禁 | ❌ |
| Brave Search API | ⚠️ | 免费 2000次/月 | 需注册Key | 未测 |
| 火山引擎 Web Search | ⚠️ | 未知 | 需注册+Key | 未测 |

## SearXNG 部署笔记

```bash
docker pull docker.m.daocloud.io/searxng/searxng:latest  # Docker Hub被墙，用DaoCloud镜像
docker run -d --name searxng -p 8080:8080 searxng/searxng
```

配置 `settings.yml`:
```yaml
search:
  formats: [html, json]
server:
  limiter: false
```

限制：百度+搜狗 3次查询后封IP 3600秒（CAPTCHA suspended_time=3600），其他引擎全部ConnectTimeout。
macOS 不支持 `--network host`，用 `-p 8080:8080`。

## Claw Search API

- 端点：`GET https://www.claw-search.com/api/search?q=关键词`
- 免费，无Key，100次/分钟，国内服务器
- 返回：`{web: {results: [{title, url, description}]}}`
- 状态：2026-08-07 502 Bad Gateway（服务暂时不可用）
