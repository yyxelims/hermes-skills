# 移动支付网正文提取 — newsbody div + 导航噪音剥离

## 问题

移动支付网 `policy.html` 列表页是 JS 动态加载，urllib 返回 0 篇文章。
详情页 `/news/YYYYMM/HHMMSS.html` urllib 可用，但正文被导航菜单文本污染。

## 列表页 URL 提取

必须用 Browser 渲染后提取：
```javascript
Array.from(document.querySelectorAll('a'))
  .filter(a => a.href && a.href.includes('/news/') && !a.href.includes('page='))
  .map(a => a.href)
```

## 详情页正文提取

### 容器定位
正文在 `<div class="newsbody">` 内：
```python
m = re.search(r'<div class="newsbody"[^>]*>(.*?)</div>\s*<div class="newsbody_bottom"', html, re.DOTALL)
```

### 导航噪音剥离
剥离 HTML 标签后，以下关键词的独立行必须删除：
```python
nav_kw = ['资讯', '焦点', '业界', '视角', '创新', '评测', '企业', '投融资',
          '政策', '国际', '调研', '专栏', '活动', '数据库', '牌照查询', '资料查询',
          '财报查询', '金松奖', '会员登录', '会员注册', '投稿', '支付数据查询',
          '交通支付查询', '申报', '最新文章', '监管', '跨境支付', '数字货币',
          '开放银行', '金融科技', '安全', '招标', '招聘', '交通']
```

### Hex Entity 清理
```python
body = re.sub(r'&#x[0-9a-f]+;', '', body)  # &#xe78b; 等
```

### 标题清理
```python
title = title.replace('-移动支付网', '').replace('_移动支付网', '')
```

## 日期提取
URL 格式 `/news/202608/10103540.html` → `2026-08-10`

## 完整脚本
`scrape_payment_sources.py` — clean_body(html, source='mpaypass')
