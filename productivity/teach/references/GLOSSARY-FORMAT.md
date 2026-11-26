# Glossary Format

A glossary lives in `./reference/glossary.html`. It is the canonical definition of all domain terms used across lessons. Once created, every lesson must use the glossary's definitions consistently.

## Format

A self-contained HTML file, beautiful and printable:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Glossary — {Topic}</title>
<style>
  body { font-family: system-ui; max-width: 800px; margin: 40px auto; padding: 0 20px; }
  dt { font-weight: 700; margin-top: 16px; color: #1a1a2e; }
  dd { margin-left: 20px; color: #555; margin-bottom: 8px; }
</style>
</head>
<body>
<h1>Glossary — {Topic}</h1>
<dl>
  <dt>Term 1</dt>
  <dd>Definition. Keep it clear and concise. One paragraph max.</dd>
  <dt>Term 2</dt>
  <dd>Definition.</dd>
</dl>
</body>
</html>
```

## Rules

- **One definition per term.** If a term has multiple meanings, pick the one relevant to this mission.
- **Add terms as they appear in lessons.** Don't pre-populate a huge glossary upfront — let it grow organically.
- **Use the glossary in every lesson.** Link back to it. If a lesson uses a term not in the glossary, add it.
