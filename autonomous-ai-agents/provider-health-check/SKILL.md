---
name: provider-health-check
author: Hermes Agent
license: MIT
description: "检测Hermes各provider/模型哪些可用。Use when 问模型挂没挂、切默认模型前批量验证。"
version: 1.1.0
metadata:
  hermes:
    tags: [hermes, setup, providers, debugging]
    related_skills: [hermes-agent]
---

# Provider/模型健康检查

## When to Use（何时用）
- 用户问"哪些模型能用 / 哪些挂了"
- 切换 `model.default` 前批量验证候选模型
- 新接入 provider 后的冒烟测试

## 快速用法

```bash
python3 <skill_dir>/scripts/check_providers.py
```

逐个 provider/model 发最小 chat 请求（max_tokens=32，内容 "hi"），输出 ✅/❌ 表格与错误详情。新增 provider 在脚本顶部 `PROVIDERS` 表加一行即可。

## 已验证的坑（2026-08-28 全端点实测）

1. **opencode.ai（Zen / Console Go）有 Cloudflare UA 指纹拦截**：python urllib 默认 UA 一律 403 (error 1010)。探针必须用 `curl + 浏览器 UA + --http2`。带浏览器 UA 后 models/chat 全通。
2. **poe (api.poe.com/v1)**：`max_tokens` 必须 ≥16，否则 400 "integer below minimum value"。脚本统一用 32。
3. **火山方舟 ark**：AgentPlan 订阅过期 → 该账号全部模型 400 "does not have a valid AgentPlan subscription"。这是账号订阅问题，不是模型挂了；续订后自然恢复。
4. **/v1/models 列表 ≠ 可用**：列表里残留已下线模型（如 grok-4.6、muse-spark），请求报 401/403/400。必须逐个发真实 chat 请求才算数。
5. **500 Internal server error**：重试 3 次 + 换 stream/max_tokens 仍 500 = 服务端故障，标记挂了等修复即可（当时 gpt-5.6-luna、minimax-m2.7 如此）。
6. ark 的 key 不在 hermes 密钥文件，在 config.yaml 的 `providers.volcengine-agent-plan.api_key`，脚本用正则提取。

## 判定标准
- ✅ = 2xx 且 choices 非空
- ❌ = 4xx/5xx，附错误前 80 字符
- 脚本是 2026-08-28 会话逐端点验证过的探针逻辑整合版；跑一次即可得到实时状态，不要凭历史结论下判断。
