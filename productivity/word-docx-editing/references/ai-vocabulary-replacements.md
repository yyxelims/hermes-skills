# AI Vocabulary Replacements (Chinese → Natural)

Quick-reference dictionary for de-AI-ifying Chinese business/technical documents.
Apply these replacements during the rewrite phase of the de-AI pipeline.

## High-Priority (must replace — these are dead giveaways)

| AI Term | Natural Alternatives |
|---------|---------------------|
| 依托 | 利用 / 基于 / 通过 / 借助 |
| 适配 | 适用 / 匹配 / 适合 / 兼容 |
| 全流程 | 端到端 / 贯穿始终 / 从…到… / 整个 |
| 赋能 | 删除 / 提升能力 / 赋予 |
| 助力 | 帮助 / 支持 / 推动 / 促进 |
| 夯实 | 巩固 / 加强 / 打牢 |
| 盘活 | 激活 / 重新利用 / 让…发挥价值 |
| 深耕 | 扎根 / 专注 / 在…持续投入 |
| 闭环 | 完整链路 / 端到端 / 形成循环 |

## Medium-Priority (replace most occurrences)

| AI Term | Natural Alternatives |
|---------|---------------------|
| 支撑 | 支持 / 保障 / 作为基础 |
| 一体化 | 整合 / 统一 / 合并 |
| 体系 | 框架 / 系统 / 机制 / 制度 |
| 架构 | 结构 / 设计 / 组织方式 |
| 引擎 | 模块 / 组件 / 核心 (keep if product name) |
| 维度 | 角度 / 方面 / 层面 |
| 颗粒度 | 细节 / 精细程度 / 粒度 |
| 对齐 | 一致 / 匹配 / 协调 |
| 抓手 | 切入点 / 突破口 / 手段 |
| 痛点 | 问题 / 困难 / 瓶颈 |

## Low-Priority (replace if overused)

| AI Term | Natural Alternatives |
|---------|---------------------|
| 显著 | 明显 / 较大 / 看得出 |
| 有效 | 管用 / 起了作用 |
| 关键 | 重要 / 核心 / 决定性 |
| 优化 | 改进 / 调整 / 提升 |
| 落地 | 实施 / 应用 / 真正用起来 / 推进 |
| 打通 | 连接 / 串联 / 整合 |
| 矩阵 | 组合 / 阵列 / 体系 |

## Patterns to Break

| AI Pattern | Fix |
|-----------|-----|
| 一是…二是…三是…四是… | 第一…第二…另外…还有 |
| 风险点：…应对措施：… (repeated 5x) | Vary structure per risk item |
| 依托…实现…助力…提升 | Break into separate sentences |
| [长句50+字无断句] | Split into 2-3 shorter sentences |
| 无具体数据/案例 | Add scenario examples ("比如一家企业…") |

## Quick Script

To count AI terms in a text file:
```bash
grep -o -E '依托|适配|全流程|赋能|助力|夯实|盘活|深耕|闭环|支撑|一体化|体系|架构|引擎|维度' file.txt | sort | uniq -c | sort -rn
```
