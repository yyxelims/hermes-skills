# LLM 双缓存层 — 避免重复 API 调用

## 设计

| 缓存文件 | Key | Value 格式 | 使用位置 |
|---------|-----|-----------|---------|
| `数据/relevance_cache.json` | 标题 SHA256 前12位 | `[is_relevant_bool, category_string]` | Phase 2 (相关性+分类) |
| `数据/personnel_cache.json` | 任免正文 SHA256 前12位 | `{names, agency, position, type}` | Phase 0 (任免提取) |

## 工作原理

```python
import hashlib

def cache_key(title):
    return hashlib.sha256(title.encode()).hexdigest()[:12]

# Load cache
try:
    relevance_cache = json.load(open(CACHE_FILE))
except:
    relevance_cache = {}

# Phase 2: Check cache before LLM call
for title in articles:
    ck = cache_key(title)
    cached = relevance_cache.get(ck)
    if isinstance(cached, list) and len(cached) == 2:
        # New format: [is_relevant, category]
        results[title] = (cached[0], cached[1])
    elif isinstance(cached, bool) or cached is not None:
        # Old format: bool only (backward compat)
        results[title] = (cached, '')
    else:
        uncached.append(title)  # Need LLM

# After LLM: persist to cache
relevance_cache[cache_key(title)] = [is_relevant, category]
json.dump(relevance_cache, open(CACHE_FILE, 'w'), ensure_ascii=False)
```

## 性能

- **首次运行**: ~50 次 API（30 相关性 + N 分类 + 15 任免）
- **后续运行**: 0 次 API（全缓存命中），秒级完成
- **增量更新**: 新文章自动追加判断并写入缓存。已有文章不动
- **缓存失效**: 标题或正文变化自动重新判断（仅变化部分调 API）

## 陷阱

1. **旧缓存格式兼容**: 旧缓存是 `bool`，新缓存是 `[bool, str]`。用 `isinstance(cached, list)` 区分
2. **缓存文件位置**: 必须放在 `数据/` 目录（脚本运行目录），不要放脚本目录
3. **清缓存时机**: 修改 LLM prompt 后必须清缓存，否则旧 prompt 的判断结果继续使用
4. **不要缓存整个 body**: 用 title 做 key 就够了。body 太长导致 SHA256 计算慢且 key 不稳定（body 可能在不同抓取中略有变化）
