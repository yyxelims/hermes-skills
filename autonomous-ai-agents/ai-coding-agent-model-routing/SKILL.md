---
name: ai-coding-agent-model-routing
description: Use when 给 AI 编码 agent 换模型/配网关（CC Switch、magpie）。
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [claude-code, codex, gemini-cli, provider-routing, gateway, tool-selection]
    related_skills: [hermes-agent, provider-health-check, glm-zhipu, deepseek-harness]
---

# 给 coding agent 接模型：切换器与网关工具

Claude Code / Codex / Gemini CLI / Hermes 这类 agent 各自把模型、base URL、key 写在自己格式的文件里。给它们换 provider、换模型、换账号的工具，用户问「这玩意儿有啥用」「和 X 什么区别」「要不要装」时用本 skill。

## When to Use（何时用）

- 用户贴一个同类项目的 GitHub 链接问「有啥用 / 和 ccswitch 有什么区别」
- 用户想把某家订阅（Claude / ChatGPT / Copilot / Gemini / Grok）接到另一个 agent 里
- 用户在多个 provider、多个账号之间来回切，想省手工改配置的功夫

## 先分类：两类工具，别混成一个东西

| | 配置切换器 | 本地网关 |
|---|---|---|
| 代表 | CC Switch（Direct 模式） | magpie、New API、LiteLLM |
| 原理 | 原子改写 agent 自己的配置文件，请求**直连**上游 | 所有 agent 指向 `127.0.0.1:port`，由网关转发 |
| 能做 | 换 key/endpoint/model、统一管 MCP/Skill/Prompt、读会话日志、看配额 | 以上全部 + 协议互转、失败转移、多账号池、脱敏、计量、限流、中间件 |
| 代价 | 拿不到请求体，做不了转换/脱敏/计量 | **单点**：网关挂了所有 agent 一起挂；必须常驻 |
| 什么时候选它 | 用户只想「切 key」 | 用户要「额度池 / 跨协议 / 统一计量」 |

回答这类问题先判断用户要的是**切换**还是要**网关**。只按 README 功能清单横向对比，会把两种东西混成一个，结论必然含糊。

## 主流工具一句话

- **CC Switch**（`farion1231/cc-switch`，Rust + Tauri，153k★，v4.x）：12 个工具；Direct / Routing / Aggregation 三模式；MCP、Skills、Prompts、Sessions、Projects 管理最全；配额看板细；`ccswitch://` Deep Link；WebDAV/S3 同步。成熟度最高，中文社区验证充分。
- **magpie**（`yetone/magpie`，Go，33.9k★，v0.1.x）：本地网关 `127.0.0.1:3425`；100+ agent；多账号额度池 + `smart/order/rotate/usage/pace` 五种路由策略 + 意图路由；隐私脱敏、网关中间件、LAN 共享带限额、Docker、远程/同步。功能最深，成熟度最浅。
- 通用网关（New API / LiteLLM / one-api）：多租户、按 key 计费、模型映射，适合自建服务端。magpie 的中间件设计明显对标 New API（`model_mapping`、`param_override` 同名同 JSON）。

细节对比、版本号、以及「这个用户该选哪个」的结论见 `references/magpie-vs-cc-switch.md`。

## 坑

1. **网关是单点**。推荐 magpie 之前先问一句：它崩了你能否接受所有 CLI 一起停。
2. **0.1.x + 每天几十个 release + 数千 open issue** = 不当生产依赖。重要工作留一条直连的路。
3. **订阅池化有 ToS 风险**。把 Claude/ChatGPT/Gemini 订阅接进第三方 agent，可能违反厂商条款 —— 两个工具的 README 自己都写了这句，转述时别当成无害功能。
4. **默认值要翻**：magpie 默认每天上报匿名使用统计（`DO_NOT_TRACK=1` 关），隐私脱敏默认**关**。
5. **迁移成本低**：magpie 能一键导入 CC Switch 的 provider，所以「先 CC Switch，不够再 magpie」是可行路线，不必二选一。
6. **两者都管 Hermes**（CC Switch 用 coexist 模式，还能编 MEMORY.md / USER.md），提建议时别漏掉用户实际在用的工具。

## 快速核实一个新同类仓库

不要只看 star 数。三步拿硬事实（先落文件再读，`curl | python3 -c` 会触发审批）：

```bash
curl -sL https://raw.githubusercontent.com/<owner>/<repo>/main/README.md -o /tmp/r.md
grep -n "^## \|^### " /tmp/r.md     # 先摸目录，跳过赞助商长条再精读
curl -sL https://api.github.com/repos/<owner>/<repo> -o /tmp/m.json
```

从 `m.json` 读 `stargazers_count`、`created_at`、`pushed_at`、`license`、`language`、`open_issues_count`、`homepage`：`created_at` + star 数 → 涨速；`open_issues_count` → 维护压力；`pushed_at` → 是否还活跃。这三项比 README 的自我描述可信得多。

## 输出格式

结论先行：一句话讲本质区别（「CC Switch 是配置切换器，magpie 是本地网关」），再给对比表，最后落到「你的场景用哪个 + 不建议用什么」。**不要**按 README 的功能顺序复述一遍 —— 用户要的是取舍，不是说明书。
