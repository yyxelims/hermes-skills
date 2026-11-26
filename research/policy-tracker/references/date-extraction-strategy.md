# 日期提取完整策略 (v7 最终版)

## 优先级链

```
LLM提取 (llm_date)
  → 详情页字段 (detail_date)
  → URL 提取 (3种格式)
  → 正文提取 (正文前500字)
  → 标题提取 (YYYY年M月)
  → 标题字典匹配 (find_date)
  → 列表页日期 (date字段)
  → 放弃 (标记为无日期)
```

## URL 日期提取 (3种格式, 按优先级)

```python
# 1. 移动支付网: /news/YYYYMM/HHMMSS.html (含完整日期)
url_m = re.search(r'/(\d{4})(\d{2})/(\d{2})\d{6}\.html', url)

# 2. 政府网站: /YYYY/MM/DD/ 或 /YYYY-MM-DD/
url_m2 = re.search(r'/(\d{4})[-/](\d{1,2})[-/](\d{1,2})/', url)

# 3. 北京政务网: /tYYYYMMDD_XXXX.html (URL含日期戳)
url_m3 = re.search(r'/t(\d{4})(\d{2})(\d{2})_', url)
```

## 正文日期提取

```python
# 优先: "发布日期/发布时间/印发日期/成文日期:" 后面跟日期
body_m = re.search(r'(?:发布|印发|成文|日期|时间)[：:]\s*(\d{4}[-/\.年]\d{1,2}[-/\.月]\d{1,2})[日号]?', body[:500])

# 回退: 正文前300字中第一个 YYYY-MM-DD 格式
body_m = re.search(r'(\d{4}-\d{2}-\d{2})', body[:300])

# 格式标准化
d_str = d_str.replace('年','-').replace('月','-').replace('日','').replace('.','-').replace('/','-')
```

## 标题日期提取

```python
# "2026年5月北京市金融统计数据" → 2026-05-01
tm = re.search(r'(\d{4})年(\d{1,2})月', title)
if tm:
    date = f'{tm.group(1)}-{tm.group(2).zfill(2)}-01'
```

## 结果

日期覆盖率: 77% → 86% (URL提取+正文提取+标题提取三层增强)

剩余无日期的为:
- 人行知识手册页面 (本质无发布日期)
- 北京政务网部分政策法规 (详情页不含日期)
- PBC 部分新闻公告 (页面无日期字段, URL无日期格式)
