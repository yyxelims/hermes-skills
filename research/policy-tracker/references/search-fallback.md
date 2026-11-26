# search_fallback.py — 多搜索引擎补全

## 位置
`政策动态追踪/脚本/search_fallback.py`

## 在流水线中的位置
```
⑧ llm_filter_summarize.py  →  ⑧.5 search_fallback.py  →  ⑨ build_final.py
```

## 功能
对正文缺失 / LLM 生成假摘要的文章，调用多搜索引擎自动查找替代来源，注入摘要。

## 搜索引擎策略
```
Claw Search（免费无限）→ 百度 AI Search（兜底 80次/天）
```
自动降级：Claw 返回空或失败 → 切换百度。

## 检测条件（满足任一触发搜索）
1. `len(body) < 100` — 正文缺失
2. `'正文未成功抓取' in summary` — 安全网已标记
3. LLM 摘要含以下任一关键词 — 假摘要：
   `网站导航`, `页面框架`, `栏目设置`, `导航结构`, `样式代码`, `RSS订阅`,
   `页面日期显示脚本`, `页面为.*栏目`, `主要内容为网站`
4. `'当前位置' in body and '首页' in body and len(body) < 300` — 导航页面

## 排除（不搜索）
- safe.gov.cn 导航页：URL 含 `zcxmzh`, `hwmywhgl`, `grjcxmwhgl`, `fwmywhgl`, `zbxmzh`, `kjzjtz`, `kjzqtz`
- 裸目录首页：URL 以 `/index.html` 结尾但前面不含日期 ID 模式 `/\\d{6,}/index\\.html$`

## 配额管理
- Claw Search：100次/分钟，免费无限制，作为主引擎
- 百度 AI Search：80次/天，超限自动停止
- 已修复的摘要随增量保存写入，未处理的次日继续（断点续传）

## 依赖
- Claw Search API：无需额外依赖（urllib + ssl）
- `baidu_search.py`（`/Users/you/quant-lab/baidu_search.py`）+ 百度千帆 API Key
