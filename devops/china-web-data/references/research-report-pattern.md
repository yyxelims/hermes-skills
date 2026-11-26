# Research Report Pattern

## Workflow

When asked to research a topic and produce a summary report:

1. **Search phase** (parallel where possible):
   - Chinese sources: `python3 universal_search.py "关键词" -e baidu --headless --no-random`
   - English sources: `python3 universal_search.py "keywords" -e baidu --headless --no-random` (or bing with proxy)
   - Academic papers: `curl -s "https://export.arxiv.org/api/query?..."` using arxiv skill

2. **Compilation phase**:
   - Group findings by theme/methodology
   - Identify the top 3-5 most mathematically/numerically significant results
   - Draft highlights in a "亮点总结" section

3. **Output**: HTML with light theme, Noto Sans SC font, clean card-based layout

## HTML Template Key Elements

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap">
  <style>
    body { font-family: 'Noto Sans SC', sans-serif; background: #f8f9fa; color: #2c3e50; }
    .header { background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460); color: white; padding: 60px 0 40px; text-align: center; }
    .container { max-width: 960px; margin: 0 auto; padding: 30px 20px; }
    .section { background: white; border-radius: 12px; padding: 30px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
    .paper { padding: 16px 0; border-bottom: 1px solid #f0f0f0; }
    .highlight-box { background: linear-gradient(135deg, #fef9e7, #fdebd0); border-left: 4px solid #f39c12; padding: 16px 20px; border-radius: 0 8px 8px 0; }
  </style>
</head>
```

## Design Rules

- **Light theme only** (#f8f9fa background, white cards)
- **Noto Sans SC** for Chinese text
- **Card-based layout** with rounded corners (12px) and subtle shadows
- **Dark gradient header** for visual impact
- **Color-coded tags** for paper categories (math=green, theory=blue, optimization=orange, geometry=red, spectral=purple, information=cyan)
- **Highlight boxes** with yellow left border for key takeaways
- **ArXiv IDs** in monospace pill badges
- Footer with data sources and date range

## File Naming

Pattern: `{topic}_report_{YYYY}W{WW}.html` or `{topic}_summary_{YYYYMMDD}.html`

## Post-Generation

Always run `open /path/to/report.html` to display in the user's browser.
