# LLM 摘要生成 — 完整处理规范（v4）

## 模型配置

- 模型：`deepseek-chat`
- 温度：0.2
- max_tokens：**4000**（容纳 12 篇 × ~400 字摘要）
- 批次大小：**12 篇/批**（39 批处理 468 篇，~6-8 分钟）

## 成本估算

deepseek-chat 定价 ¥1/百万 input + ¥2/百万 output。
468 篇有正文，12 篇/批 = 39 批，每批 ~8000 input chars。
总 input ~35 万 tokens，总 output ~10 万 tokens。
**一次全量 ≈ ¥0.5-0.6**。

## Prompt 模板（v4，已验证可靠 — 98.5% 覆盖率）

**⚠️ 严禁给 LLM "不相关"选项** — 否则它会误杀 58% 的文章。
相关性过滤用关键词黑名单在 build_final.py 处理，不在 LLM 层做。

```
你是一位金融监管政策分析师。请为以下每篇文章生成摘要。

对每篇文章，严格按以下格式输出（不要用markdown，不要加粗，不要判断是否相关）：

第N篇
标题：完整标题原文
日期：YYYY-MM-DD
摘要：核心要点（200-400字中文，包含具体政策内容/数据/人物/机构）
时间节点：关键日期或时限（无则写"无"）

--- 第0篇 ---
标题:{title}
正文:{body}

--- 第1篇 ---
标题:{title}
正文:{body}
...
```

## 解析逻辑（v4，鲁棒解析）

```python
# 分块：容忍空格和可选冒号
blocks = re.split(r'第\s*(\d+)\s*篇\s*[：:]?\s*', resp)

def parse_one(text):
    result = {}
    # 容错检测"不相关"（安全网，虽然 prompt 已不要求）
    if re.search(r'不(?:相关|属于|涉及)', text[:50]):
        result['irrelevant'] = True
        return result
    
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
        
        # ⚠️ 用 re.search 而非 re.match — 容忍 **标题：**、- 标题：等前缀
        m = re.search(r'标题[：:]\s*(.+)', line)
        if m and not result.get('title'):
            t = m.group(1).strip()
            t = re.sub(r'\*\*', '', t)  # 去粗体标记
            if len(t) > 3: result['title'] = t
        
        m = re.search(r'日期[：:]\s*(.+)', line)
        if m and not result.get('date'):
            dm = re.search(r'(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})', m.group(1))
            if dm:
                d = dm.group(1).replace('/', '-').replace('.', '-')
                parts = d.split('-')
                if len(parts) == 3:
                    result['date'] = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
        
        m = re.search(r'摘要[：:]\s*(.+)', line)
        if m and not result.get('summary'):
            s = m.group(1).strip()
            s = re.sub(r'\*\*', '', s)
            if len(s) > 20: result['summary'] = s[:400]
        
        m = re.search(r'时间节点[：:]\s*(.+)', line)
        if m and not result.get('keydates'):
            kd = m.group(1).strip()
            if kd not in ('无','无特定','无明确时间节点','暂无','—','-'):
                result['keydates'] = kd[:200]
    
    # 回退：无结构化字段但文本较长 → 全文字段当摘要
    if not result and len(text) > 30:
        if not re.search(r'(error|错误|失败|抱歉|无法)', text, re.IGNORECASE):
            result['summary'] = text[:400]
    
    return result
```

## 断点续传机制

```python
# 从输出文件读取（非输入文件），检测已有摘要的跳过
out_path = os.path.join(DATA, 'detail_pages_llm_v2.json')
input_path = os.path.join(DATA, 'detail_pages_v2.json')

if os.path.exists(out_path):
    with open(out_path) as f:
        details = json.load(f)
    existing = sum(1 for d in details if d.get('llm_summary','') and len(d['llm_summary'])>20)
    if existing > 0:
        print(f"从已有输出恢复: {existing}篇已有摘要")
    else:
        with open(input_path) as f:
            details = json.load(f)
else:
    with open(input_path) as f:
        details = json.load(f)

# 每 10 批增量保存
if batch_num > 0 and batch_num % 10 == 0:
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(details, f, ensure_ascii=False, indent=1)
```

## 失败模式历史

### ❌ v1: `[J]` 格式（0/526 篇有摘要）
LLM 完全忽略 `[J] 标题:xxx | 日期:xxx` 格式。

### ❌ v2: 状态机解析（0/526 篇有摘要）
`current_j` 状态机完全不匹配 LLM 实际输出。

### ⚠️ v3: 自然语言 + 过滤（130/526 篇有摘要，58% 误杀）
LLM 遵守 `第N篇：相关/不相关` 标记，但把 58% 文章标为不相关（误杀）。

### ✅ v4: 纯摘要 + 鲁棒解析（461/468，98.5% 覆盖率）
去掉"不相关"选项，`re.search` 容忍 markdown 前缀，断点续传防超时。

## 实际运行指标（2026-08-06 终态）\n\n| 指标 | 值 |\n|------|----|\n| 输入文章 | 724 篇（468 有正文 → 630 优化后） |\n| LLM 摘要 | **628 篇**（99.7%，630篇正文中仅2篇无摘要） |\n| 无摘要 | 2 篇（极端短正文页面） |\n| 过滤为不相关 | 0（prompt 不提供此选项） |\n| JS 正文垃圾 | 0（scrape_details.py is_js_body 检测 + Playwright 兜底后清零） |\n| 日期提取 | 456 篇（从 LLM 输出中） |\n| API 批次 | ~53 批（12 篇/批，含增量） |\n| 耗时 | ~6-8 分钟（全量）/ ~1-2 分钟（增量） |\n| 成本 | ~¥0.5-0.8 |\n\n## 注意事项\n\n1. **不要在 prompt 里给 LLM \"不相关\"选项** — DeepSeek 会把 58% 的正常金融文章误判为不相关。\n2. **断点续传是关键** — 468 篇 × 12篇/批 = 39 批需要 ~8 分钟，容易超时。每 10 批增量保存 + 从已有输出恢复。\n3. **正文必须先清理 JS 垃圾** — scrape_details.py 的 `is_js_body()` 检测 safe.gov.cn 的 JS 挑战页，清空 body 后再跑 LLM，否则 LLM 会给 JS 代码生成荒谬摘要。\n4. **摘要 400 字够用** — `[:400]` 截断 + `max_tokens=4000`。（LLM 返回的摘要实际上限是 400 字，prompt 写 200-400 字）
