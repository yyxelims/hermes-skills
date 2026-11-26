# magpie vs CC Switch（核对于 2026-11-11）

两个仓库的 README + GitHub API 元数据都读过，以下数字与结论均有出处，不是推测。

## 元数据

| | CC Switch | magpie |
|---|---|---|
| 仓库 | `farion1231/cc-switch` | `yetone/magpie` |
| 官网 | ccswitch.io | usemagpie.ai |
| 语言/框架 | Rust + Tauri 2 | Go（菜单栏 / 窗口 / TUI / Web / CLI 多形态） |
| 创建 | 2025-08-04 | 2026-09-23（约 7 周涨到 33.9k★） |
| Stars / Forks | 153k / 10.1k | 33.9k / 3.0k |
| Open issues | 963 | 3685 |
| 版本 | v4.x | **v0.1.3678**（release 号即构建号，日更） |
| License | — | MIT |
| 外部 PR | 接受 | **不接受**（仅 maintainer 可提，只能去 Discord 反馈） |

## 架构差别（这是所有功能差异的根）

- **CC Switch**：默认 Direct —— 原子改写 `~/.claude/settings.json`、Codex TOML、Gemini 配置等，**只换 endpoint/key/model**，注释、顺序、自己加的 hooks/plugins/MCP 原样保留；请求直连上游。Routing / Aggregation 是**后加的可选**模式（v4）。
- **magpie**：网关 `127.0.0.1:3425` 是**必经之路**，说 OpenAI Chat / OpenAI Responses / Anthropic Messages / Gemini 四种协议并互相翻译（流式、tool call、reasoning 都算）。所以它才能做脱敏、中间件、计量、跨协议 —— 代价是单点。

## magpie 的独有能力

1. 订阅池化：同一订阅加多个账号，额度耗尽自动接力，agent 看不到报错；Claude 是驱动本地 `claude` 二进制 + MCP 桥接工具（不是纯 HTTP 转发）。
2. 路由组：`group/xxx`，模式 `smart`（额度即将重置的先用）/ `order` / `rotate` / `usage` / `pace`；组可嵌套；会话在缓存有价值时粘在回答它的账号上。
3. 意图路由：小模型读每轮，测试派强模型、闲聊派便宜模型。
4. 隐私脱敏（默认关）：请求出本机前把 key/token/邮箱/卡号身份证换成 `{{API_KEY_k3v9x2mq}}`，回复（含流式与 tool args）再换回；同一值占位符稳定，prompt cache 不失效；只在内存不落盘；可选 1.6GB 本地模型抓姓名/地址/密码；可 Mask/Warn/Block 三档。
5. 网关中间件：JS `onRequest/onEvent/onResponse`，配套 `param-override`、`model-map`、`system-prompt`、`word-guard`、`think-tags`（对标 New API 同名 JSON）。
6. 给所有 agent 补工具：统一 web search（Tavily/Brave/Exa/SearXNG/豆包/元宝…多 key 轮换）、图片、视频，走 MCP。
7. 运维面：LAN 共享（每客户端一把带日/周/月限额的 key）、Docker 跑 NAS、remote magpie、WebDAV/S3/GitHub 加密备份、OTLP 导出。

## CC Switch 的独有能力

1. 12 个工具（Claude Code / Claude Desktop / Codex / Gemini CLI / Grok Build / OpenCode / OpenClaw / Hermes / Pi / MiniMax Code / Kimi Code / Oh My Pi），switch 与 coexist 两种写配置方式。
2. 统一 MCP / Skills / Prompts / Projects 面板（skills.sh 一键装、按工具同步、软链或复制）。
3. 会话阅读视图：把各工具 session log 解析成「每轮摘要 + 改了哪些文件 + 哪步失败标红」，一键复制 resume 命令。
4. 配额看板：官方订阅 5h/周/月窗口、Coding Plan、账号余额，直接印在 provider 卡和托盘上。
5. `ccswitch://` Deep Link 一键导入 provider/MCP/prompt；90+ provider 预设。
6. 首次启动自动把现有配置导入为 `default` provider，不丢配置。

## 判断结论（对「Hermes + GLM/DeepSeek + Claude Code 切 key」这类用户）

- 只要切 key、换模型、顺带看配额和会话 → **CC Switch 足够且更稳**（直连模式下没有中间层可挂）。
- 想要多订阅账号额度接力、或让 Codex/Gemini/Hermes 吃到 Claude / ChatGPT 订阅 → **magpie**，但只在这些工具上开，别整体替换。
- 两者可共存，迁移方向是 magpie 一键导入 CC Switch 的 provider（反向无）。

## 回答用户时容易漏的两点

- magpie 的支持列表里**有 Hermes Agent**（CC Switch 也能管 Hermes 的 MEMORY.md/USER.md）—— 用户自己在用 Hermes，这条直接影响结论。
- magpie README 自己声明「不接受 PR」，且默认打开匿名遥测 —— 属于选型风险项，要在回答里点出来，别只讲功能。
