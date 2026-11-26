# LLM 两步判断 + 双缓存模式

## 问题

将"判断相关性"和"分类业务线"合并到一个 LLM prompt 会导致判断过松（81% 判为相关，实际只有 21%）。

## 两步走方案

```python
# Step 1: 严格判断相关性（prompt含明确的包含/排除清单）
prompt = """判断以下文章是否与信用卡/支付/消金/银行监管/征信/反洗钱直接相关。
仅回答"[N] 相关"或"[N] 不相关"。
注意：银行间市场业务/外汇管理/支付清算/征信管理/反洗钱/消费金融 都属于相关。
排除：纯汇率牌价/逆回购MLF操作公告/领导人讲话(无实质内容)/体育/食品安全。"""

# Step 2: 仅对相关的文章分类
relevant_only = [a for a in articles if rel_map[a.title]]
CATS = '信用卡发卡|收单支付|消保合规|消费分期|数字人民币|跨境支付|反洗钱|银行监管'
prompt = f"""对以下金融监管相关文章分类，每篇回答: "[N] {CATS}"（选一个最匹配的）"""
```

## 关键教训

- **"严格"前缀**：会导致过度收紧（18% 判为相关）
- **"判断...注意：XX属于相关"**：正确平衡（36% 判为相关）
- 排除词要精确——`外汇牌价`会误杀外汇管理政策，应为`纯汇率牌价`

## Python tuple 布尔陷阱

```python
# ❌ BUG: (False, '') 仍是 truthy
sum(1 for v in results.values() if v)  # 423，但实际只有 95

# ✅ 正确
sum(1 for v in results.values() if v[0])  # 95
```

## SHA256 缓存模式

```python
import hashlib

CACHE_FILE = 'relevance_cache.json'
try:
    cache = json.load(open(CACHE_FILE))
except:
    cache = {}

def cache_key(title):
    return hashlib.sha256(title.encode()).hexdigest()[:12]

# 读取: 先查缓存
ck = cache_key(title)
if ck in cache:
    is_rel = cache[ck]  # 直接返回
else:
    # 未命中: 送LLM
    result = ask_llm(title)
    cache[ck] = result
    json.dump(cache, open(CACHE_FILE, 'w'))  # 持久化
```

## 去重后索引重建

```python
# ❌ BUG: 去重移除行后，check_items 索引失效
row_data = [rd for i, rd in enumerate(row_data) if i not in dup_indices]
check_items[idx][6] = ...  # IndexError!

# ✅ 正确: 重建 old→new 映射
old_to_new = {}
new_idx = 0
for old_idx in range(len(row_data)):
    if old_idx not in dup_indices:
        old_to_new[old_idx] = new_idx
        new_idx += 1
new_check = [(old_to_new[old_idx], s, t, site) 
             for old_idx, s, t, site in check_items 
             if old_idx in old_to_new]
check_items = new_check
```

## 二次审查找回误判

```python
# Phase 3.1: 对第一轮判为"不相关"的文章，用不同 prompt 二次审查
prompt = """以下文章在第一轮被判定为"不相关"。请严格复查：
是否涉及信用卡/收单/支付清算/消费金融/消保/征信/反洗钱/数字人民币/银行监管处罚？
对每篇只回答"[N] 错杀"或"[N] 正确"，不要解释。"""

# 只把"错杀"的加回 Sheet2，其余丢弃（不保留 Sheet5 垃圾回收站）
```

## JS渲染页面抓取模式

移动支付网等 JS 动态加载的列表页，urllib 拿不到文章 URL：

1. Browser 渲染页面 → `browser_console` 提取所有 `/news/YYYYMM/HHMMSS.html` 链接
2. 保存 URL 列表到 JSON
3. urllib 逐篇抓取正文（详情页通常是静态 HTML）
