# CSS/JS 正文污染全链路清洗

## 问题
政府网站（pbc.gov.cn、beijing.gov.cn 等）常返回 CSS/JS 代码而非文章内容。LLM 基于这些代码生成假摘要（"本文为页面框架..."、"主要展示网站导航和样式代码"）。

## 三道防线

### 第一道：clean_body 预处理（scrape_details.py）

```python
def clean_body(text):
    if not text: return ''
    # CSS 注释块
    text = re.sub(r'/\*.*?\*/', '', text)
    # CSS 规则块
    text = re.sub(r'\{[^}]*\}', '', text)
    # 速度标记
    text = re.sub(r'var\s+_speedMark\s*=\s*new\s+Date\(\);?', '', text)
    # 逐行过滤 CSS 选择器
    if re.match(r'^[.#@]?\w[\w-]*\s*\{', line): continue
    if re.match(r'^[a-z-]+\s*:\s*[^;]+;?\s*$', line): continue
```

### 第二道：clean 函数（scrape_leaders_full.py）

领导简历也有 CSS 污染，同样需要过滤:
```python
def clean(s):
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', str(s or ''))
    s = re.sub(r'\{[^}]*\}', '', s)
    s = re.sub(r'/\*.*?\*/', '', s)
    s = re.sub(r'\.\w+\s*\{[^}]*\}', '', s)
    s = re.sub(r'#[a-zA-Z][\w-]*\s*\{[^}]*\}', '', s)
    return s.strip()
```

### 第三道：摘要安全网（build_final.py）

检测 12 个关键词，命中即替换为标题兜底:
```python
BAD_SUMMARY_KW = [
    '导航CSS', '样式代码', 'RSS订阅', '栏目设置',
    '导航结构', '页面框架', '网站头部导航', '常见问题、更新日志',
    '本文为', '页面包含网站', '页面日期显示脚本', '导航和页面框架'
]
if any(kw in summary for kw in BAD_SUMMARY_KW):
    summary = f'【{site}】{title[:180]} (正文未成功抓取)'
```

## 常见 CSS 污染模式

| 模式 | 示例 | 来源 |
|------|------|------|
| CSS 注释 | `/*导航css*/` | pbc.gov.cn |
| CSS 规则 | `body{margin:0;padding:0;}` | pbc.gov.cn |
| JS 变量 | `var _speedMark = new Date();` | pbc.gov.cn 列表页 |
| CSS 选择器残留 | `body a .header #logo .logo1` | pbc.gov.cn 领导页 |
| JS 混淆代码 | `function u(o,s){...}0x...` | safe.gov.cn JS 挑战页 |
| 导航文本 | `访问人民银行主站 机构简介 公告信息...` | 人行北京分行 |

## 假摘要特征

LLM 看到 CSS/导航页面时生成的典型摘要:
- "本文为...页面框架"
- "主要内容为网站导航和页面框架信息"
- "页面包含网站头部导航、常见问题、更新日志、RSS订阅等栏目设置"
- "该页面为...栏目，页面包含数据展示框和交互选择功能，但正文内容未提供具体数据"
