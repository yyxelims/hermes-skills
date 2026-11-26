# AIHOT 旧接口停服事件（2026-10-31）+ v1 迁移对照

## 现象

- 个人网站 `***/daily.html` 打开正常、归档按钮都在，但内容停在 2026-10-31。
- cron job `ab48b69d8335`（AI日报每日上传OSS，`40 8 * * *`，no_agent）每天照跑，`last_status: error`，无告警送达。
- 手动跑 `~/.hermes/scripts/aihot_daily_upload.sh` → `urllib.error.HTTPError: 404 Not Found`，traceback 里带 `http_error_302`（先跟着 301 跳转，再吃 404）。

## 真实原因

`https://aihot.virxact.com/api/public/*` 于 **2026-10-31 15:59:59Z（北京时间 10-31 23:59）停止服务**：

```
HTTP/2 301
location: https://aihot.news/api/public/daily
```

跟到新域名后返回 404，**响应体自己给出了替代方案**（这一步最省时间）：

```json
{"code":"not_found",
 "detail":"/api/public/daily 已于 2026 年 10 月 31 日（北京时间）停止服务；请改用 https://aihot.news/api/v1/dailies/latest",
 "replacement":"https://aihot.news/api/v1/dailies/latest",
 "notice":{"type":"legacy_sunset","sunset":"2026-10-31T15:59:59Z",
           "url":"https://aihot.news/agent?tab=api#legacy-api-migration"}}
```

## 端点新旧对照

| 旧（已停用） | 新 |
|---|---|
| `/api/public/daily` | `/api/v1/dailies/latest` |
| `/api/public/daily/{date}` | `/api/v1/dailies/{date}` |
| `/api/public/dailies?take=N` | `/api/v1/dailies?limit=N`（1–180） |
| `/api/public/items?mode=selected` | 人读走 `/api/v1/agent/latest`；结构化走 `/api/v1/items` |

规范：`https://aihot.news/openapi-v1.json`（`AIHOT Public API 2.0.0`）。另有 `/api/v1/agent/*`（latest / search / hot / daily / weekly / monthly / *-resets），直接返回**整理好的中文 Markdown**，末尾带「回答提示」，适合给人读；请求时 UA 用 `aihot-skill/2.0.0 (+https://aihot.news/aihot-skill/)`。官方 Skill v2.0.0：`https://aihot.news/aihot-skill/SKILL.md`。

## 三处静默破坏

1. **包装层**：日报包在 `{"schemaVersion":1,"report":{...}}`，不取 `report` 就全部字段为 `None`。
2. **字段嵌套化**：`sourceName` → `source.name`，`sourceUrl` → `links.original`（另有 `links.aihot`）。
3. **字段消失**：日报正文 item **不再有 `publishedAt`**（只有 `flashes` 有）。前端原本就是 `it.publishedAt ? fmt(it.publishedAt) : ''`，所以空时间不报错 —— 这也是它没被早期发现的原因之一。

`report` 顶层键：`date` / `generatedAt` / `windowStart` / `windowEnd` / `links` / `attribution` / `lead` / `sections` / `flashes` / `highlights`。

## 落地改法（`~/Documents/工作/个人网站/pipeline/aihot_daily_pipeline.py`）

- `API = "https://aihot.news"`
- 新增 `fetch_report(path)`：`return d.get("report") or d`
- 新增 `_src(it)` / `_url(it)`：兼容 dict 与字符串两种形状
- 三个调用点换路径：`/api/v1/dailies/latest`、`/api/v1/dailies/{date}`、`/api/v1/dailies?limit=N`
- 备份保留为 `aihot_daily_pipeline.py.bak-20261111`

同步迁移的副本：`~/.hermes/skills/research/aihot/scripts/ai_daily.py`、`references/html-generator.md`、`references/multi-day-combined.md`（旧 `take=` 一并改 `limit=`）。

## 验收数字（2026-11-11）

- `--backfill 14` 回填 12 天（11-01…11-10、10-30、10-29；10-31 已在索引，自动跳过）
- 归档天数 60 → **72**；`index.json.latest = 2026-11-11`
- 当天：12 条 / 5 个版块 / 10 条快讯
- 浏览器实开 `***/daily.html` 渲染正常；点归档 `11/10` 得到 12 条、首条为「Anthropic 发布 Claude Fable 5.2 与 Claude Mythos 5.2」
