# 第1组 Skill 审计 (2026-08-05)

## 审计范围

36个skill，覆盖7个类别：

| 类别 | 数量 | 特点 |
|------|:----:|------|
| apple | 5 | macOS工具手册，closure普遍低 (2-3) |
| autonomous-ai-agents | 4 | agent编排，综合得分高 (3-5) |
| creative | 19 | 方法论丰富，跨度最大 (2-5) |
| baidu-ai-search | 1 | 中文搜索，含限流自保护 |
| browser-automation-tools | 1 | Selenium实战，pitfall密集 |
| byted-supabase | 1 | 安全规范严格，平台特化 |
| dogfood | 1 | QA方法论，5-phase流程 |
| hatch-pet | 1 | 极完备QA体系，格式高度特化 |
| neat-freak | 1 | 知识管理典范，跨域满分 |
| poe-api | 1 | API集成，batch verified models |
| yuanbao | 1 | 精简群组交互，平台特化 |

## 审计方法

### 加载策略

1. 批量并行skill_view（每批8个），减少往返次数
2. 每个skill提取标准元数据：name, description, tags, version, linked_files, prerequisites, pitfalls
3. 读完全部36个后再统一评分，避免顺序效应

### 评分维度（5维 × 1-5分）

| 维度 | 对应控制论原则 | 评分问题 |
|------|:-----------:|----------|
| **closure** (闭环反馈) | 原则1 | 是否有"执行→验证→调整"的闭环？验证是自动还是人工？ |
| **stability** (稳定鲁棒) | 原则4 | 是否有pitfalls/troubleshooting？错误恢复路径？fallback机制？ |
| **observability** (可观测性) | 原则5 | 输出是否可结构化解析？有无进度监控？错误是否可追踪？ |
| **optimization** (反馈优化) | 原则6,7 | 是否提供效率/成本/质量的优化指导？决策树？best practices？ |
| **cross_domain** (跨域可迁移) | 原则14 | 方法论的通用性如何？脱离具体工具/平台后还剩多少价值？ |

### 特殊规则

- 纯视觉输出skill的observability不因为"视觉艺术本质"给1分——必须看是否有验证机制（如pixel-art的`ffprobe`+`Image.getcolors()`）
- macOS工具手册类skill的跨域分自然低（2分），不是缺陷——是类别特征
- NOT FOUND的ghost skill所有维度给0分，不参与平均计算

## 关键发现

### 高分skill共性

1. **comfyui** (25/25): health_check→check_deps→auto_fix三级诊断+修复，hardware_check路由local vs cloud
2. **hermes-agent** (24/25): doctor/config check/migrate/status多维诊断，20+provider+profiles+credential pools
3. **neat-freak** (24/25): 三类知识/三种受众分离，尺寸体检+变更影响矩阵+自检清单
4. **claude-code** (22/25): 15条pitfalls+两种output模式+tmux监控+cost optimization
5. **touchdesigner-mcp** (23/25): CRITICAL RULES防猜测，empirical recipes，get_errors/get_perf/get_screenshot

### 低分skill特征

- **apple-notes** (10/25): 纯CLI命令手册，无验证、无fallback、无结构化输出
- **imessage** (11/25): 同上
- **yuanbao** (12/25): 极度精简，缺少错误处理和验证反馈

### 幽灵skill发现

- `ideation`: available_skills列表中存在但磁盘无文件，需要从索引中移除或创建实际文件

### 编码/路径问题

- `pixel-art`: 存在两个同名skill (`creative/pixel-art/SKILL.md` vs `baoyu-infographic/references/styles/pixel-art.md`)，需用完整路径`creative/pixel-art`加载。建议重命名后者避免歧义。

## 方法论 vs 工具手册

| 类型 | 典型skill | 闭环节 | 稳定性 | 可观测性 | 优化 | 跨域 |
|------|----------|:------:|:------:|:--------:|:----:|:----:|
| 方法论 | humanizer, neat-freak, claude-design | 4-5 | 4-5 | 3-4 | 5 | 4-5 |
| 工具手册 | apple-notes, imessage | 2 | 2-3 | 2 | 2 | 2 |
| agent编排 | claude-code, codex | 3-4 | 4-5 | 3-4 | 3-5 | 3-4 |
| 生成管线 | comfyui, baoyu-comic, p5js | 4-5 | 4-5 | 4-5 | 5 | 3-4 |

**结论**: 方法论型skill天然适合控制论框架，但这不是得分偏倚——方法论文本就应该在所有维度上更强。工具手册型skill的低分是类别特征，不是质量问题。
