# 并行审计：子代理 Context 模板

此模板在 2026-06-25 审计（103 skill, 3 组并行）中实战验证——3 个子代理全部一次性完成且输出有效 JSON。直接复制此模板，替换 skill 列表即可。

## 模板结构

每个子代理的 context 必须包含以下 6 个部分：

1. **Skill 列表**：精确的名称列表（逗号分隔）
2. **评分标准**：5 维度评分细则（1-5 分完整描述），子代理无父代理记忆，必须内嵌
3. **principles 编号映射表**：14 条原则的中文名称
4. **JSON 输出格式**：含正常评分和 SKILL NOT FOUND 两种 fallback
5. **路径解析规则**：bare name → category prefix → search_files → mark ghost 的四级 fallback
6. **已知问题**：本组内的已知幽灵 skill、ambiguous 名称、超大文件等

## 完整模板

```
你是工程控制论审计子代理。对以下 N 个Skill逐一评分，输出JSON数组到文件。

## 要审计的Skill列表（共 N 个）
skill-a, skill-b, skill-c, ...

## 评分标准（5维度，每维1-5分）

**1. 闭环完整性（closure，映射原则1、6）**：
- 5分：完整「执行→验证→修正→再执行」循环，含自动化验证
- 4分：有验证但依赖人工触发
- 3分：线性工作流，缺少验证环
- 2分：纯CRUD/工具手册，无验证
- 1分：无任何反馈机制

**2. 稳定性（stability，映射原则4）**：
- 5分：容错、fallback、错误恢复、边界条件处理
- 4分：Troubleshooting指南+已知pitfalls
- 3分：基本错误处理说明
- 2分：仅提及可能需要检查
- 1分：无稳定性考虑

**3. 可观测性（observability，映射原则5、13）**：
- 5分：结构化metrics、实时监控、多维度状态检查
- 4分：JSON输出、状态检查命令、错误码
- 3分：文本输出可被下游解析
- 2分：依赖人工目视检查
- 1分：无可观测反馈信号

**4. 最优化（optimization，映射原则7）**：
- 5分：自动优化策略（参数搜索、调度优化、自适应）
- 4分：多策略选择指南+优化建议
- 3分：基本性能/效率建议
- 2分：仅提供可行方案
- 1分：无优化考虑

**5. 跨域性（cross_domain，映射原则10）**：
- 5分：方法论完全领域无关
- 4分：核心方法论可迁移，实现绑定领域
- 3分：部分方法论可泛化
- 2分：高度特化于单一工具/平台
- 1分：完全不可迁移

## principles 数组
记录该skill **体现**（而非缺失）的核心原则编号：
1=实践-理论-实践循环, 2=特殊→一般, 3=数学建模, 4=稳定性优先, 5=能控能观对偶, 6=反馈闭环, 7=最优化, 8=协调解耦, 9=分析→综合, 10=跨域统一, 11=技术科学定位, 12=大系统观, 13=信息-控制融合, 14=理论实践不可偏废

## issues 字段
简短说明关键缺陷和改进建议（中文，≤150字）。若无明显缺陷写"无"。

## 输出格式
每个skill一个JSON对象：
{"name": "skill-name", "category": "category", "closure": 4, "closure_note": "...", "stability": 3, "stability_note": "...", "observability": 3, "observability_note": "...", "optimization": 2, "optimization_note": "...", "cross_domain": 3, "cross_domain_note": "...", "principles": [1, 6], "issues": "..."}

**若skill读取失败（skill_view返回error或not found）**：
{"name": "skill-name", "category": "unknown", "closure": 0, "closure_note": "SKILL NOT FOUND", "stability": 0, "stability_note": "SKILL NOT FOUND", "observability": 0, "observability_note": "SKILL NOT FOUND", "optimization": 0, "optimization_note": "SKILL NOT FOUND", "cross_domain": 0, "cross_domain_note": "SKILL NOT FOUND", "principles": [], "issues": "SKILL NOT FOUND — available_skills列表中存在但磁盘无对应文件"}

**重要**：JSON 的 `name` 字段必须使用不含 category 前缀的裸名称。即使上方列表中为消歧义使用了 `creative/comfyui` 格式，JSON 中应写 `"name": "comfyui"`。

## 路径解析规则
1. 先用 bare name 调用 skill_view(name)（如 skill_view('baidu-ai-search')）
2. 若返回"Ambiguous skill name"，用完整分类路径（如 'apple/apple-notes'）
3. 若返回"not found"，用 search_files(target='files', pattern='*skill-name*', path='~/.hermes/skills/') 查找，再用 read_file() 读取
4. 若search_files也找不到，则标记为 SKILL NOT FOUND

## 已知问题
- <列出本组已知幽灵skill>
- <列出本组已知ambiguous名称及正确路径>
- <列出本组超大skill文件>
- 每个skill先调用 skill_view(name) 加载内容，阅读后评分
- 审计偏见提醒：方法论类skill天然高分是正常的，工具手册类低分也是正常的
- 评分时基于skill的实际文档内容，不要臆测

## ⚠️ DO NOT DRIFT — 严格遵守分配的 Skill 列表

**这是最大的审计失败模式**（2026-07-02 审计：3组中2组扫描了错误的skill）。子代理必须**精确**审计上方"要审计的Skill列表"中列出的skill，不得多、不得少、不得替换。

**防止漂移的硬性规则**：
1. **开始前先计数**：确认列表中 skill 数量（如 N=37 个），在第一条 log 中打印 "Starting audit of N skills"
2. **逐个处理**：按列表顺序依次 `skill_view(name)`。每处理完一个，计数 `processed += 1`
3. **禁止范围外加载**：如果 `skill_view()` 返回其他不相关 skill 的内容，忽略它——只审计列表中指定的 skill
4. **输出前自检**：`write_file` 前打印 `"Processed X/Y skills, writing JSON..."`。若 X ≠ Y，报告差异
5. **只输出分配的 skill**：JSON 数组中只能包含列表中指定的 skill。即使无意中读到了其他 skill，也不得将其加入输出
6. **幽灵skill也要输出**：列表中标记为幽灵的 skill 仍需在 JSON 中出现（closure=0），不能跳过

**常见漂移模式及预防**：
- **模式1 — 批量skill_view时读到上下文外的skill**：并发调用 `skill_view()` 时某个响应可能来自其他类别的skill。**预防**：响应返回后核对 name 字段是否在分配列表中，不在则丢弃。
- **模式2 — 处理完部分skill后忘记剩余**：session 中断或超时后只写了部分条目到 JSON。**预防**：每完成 10 个 skill 就写一个 checkpoint JSON，最后再合并。
- **模式3 — 子代理"发挥主动性"**：子代理可能认为某些skill"看起来应该属于本组"而主动添加。**预防**：在 context 中强调"你分配的名单是唯一的权威来源，不要自行判断归属"。

## 输出文件
将所有 N 个skill的JSON对象组成数组，用 write_file 写入：
~/.hermes/skills/reports/cybernetics_groupX.json
确保JSON格式正确（valid JSON array）。
```

## 设计原则

1. **自包含**：子代理无父代理上下文，评分标准必须完整内嵌
2. **双输出格式**：正常评分 + SKILL NOT FOUND 两种 fallback，避免子代理因读取失败而丢弃整个条目
3. **四级 fallback**：bare name → category prefix → search_files → ghost，最大化可评分 skill 数量
4. **审计偏见提醒**：防止子代理因方法论/工具类差异而产生评分偏差
5. **已知问题预填**：提前告知本组的幽灵 skill 和路径歧义，减少子代理试错

## 已知陷阱

### 陷阱：子代理复用 category 前缀到 JSON name 字段

当 skill 列表中包含 category 前缀（如 `creative/comfyui`、`apple/apple-notes`，用于消歧义或辅助子代理路径解析）时，子代理可能将带前缀的名称直接写入 JSON 的 `name` 字段，导致合并验证时名称不匹配（预期 `comfyui`，实际 `creative/comfyui`）。

**预防方案**：
1. **模板中明确要求**：在"输出格式"后追加："`name` 字段必须使用**不含 category 前缀的裸名称**。即使上方技能列表使用了 `creative/comfyui` 格式，JSON 中应写 `\"name\": \"comfyui\"`。"
2. **父代理验证后规范化**：合并前用脚本剥离前缀（`name.split('/', 1)[-1]`），参见 parallel-large-scale-audit.md 第 3.5 步。
3. **统一策略**：若所有子代理使用统一 bare-name 列表，则此陷阱不会触发。仅当某个组必须使用前缀（如 Group 1 的 creative/apple 消歧义）时才需关注。

2026-07-14 审计中 Group 1 触发此陷阱——父代理用 `_fix_group1_names.py` 剥离前缀后通过验证。
