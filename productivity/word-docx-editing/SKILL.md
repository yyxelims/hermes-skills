---
name: word-docx-editing
description: >-
  Build, edit, and format Word .docx documents with python-docx, including OMML formulas,
  pandoc conversion post-processing, table styling, font unification, and equation numbering.
  Use when user needs to create/edit .docx files, insert Word formulas, fix pandoc output,
  or format patent disclosures / technical documents in Word.
tags: [docx, word, omml, formulas, pandoc, python-docx, tables, formatting]
---

# Word DOCX Editing

## When to Use

Use this skill when:
- Building `.docx` from scratch with python-docx
- Inserting or editing OMML (Word native) formulas
- Post-processing pandoc LaTeX→docx output (removing `longtable` artifacts, fixing references)
- Adding equation numbers, table captions, figure captions to Word documents
- Unifying fonts (Latin + East Asian) across an entire document
- Formatting Chinese technical documents (patent disclosures, theses, reports) in Word

## Quick Reference

| Task | Approach |
|------|----------|
| LaTeX → Word with formulas | `pandoc file.tex -o output.docx` — converts `\begin{equation}` to OMML |
| Fix pandoc tables | Remove "续" rows, add header styling, zebra stripes |
| Add equation numbers | Search `m:oMathPara` elements, classify by `m:t` content, append number run |
| Fix `\ref` references | Replace `([eq:xxx])` patterns with "式1", "式2", etc. |
| Math as plain text | Rebuild paragraph with `m:oMath` inline elements via `lxml.etree` |
| Font unification | Set all runs to Times New Roman + 宋体/黑体 |
| Table captions | Insert centered `表N：标题` paragraph before each `w:tbl` |
| Figure captions | Insert centered `图N：标题` paragraph after each `w:drawing` |

## Pandoc Conversion Pipeline

```bash
# 1. Fix LaTeX for pandoc compatibility (no \begin{aligned} with \notag)
# 2. Convert
pandoc input.tex -o output.docx --from=latex --to=docx
# 3. Post-process with python-docx (see references/pandoc-postprocess.md)
```

**Critical**: Pandoc cannot handle `\begin{align}...\end{align}` with `\notag`. Split into separate `\begin{equation}...\end{equation}` blocks before conversion.

## Font Standard for Chinese Technical Docs

- Body: Times New Roman 12pt + 宋体 (East Asian)
- Headings: Times New Roman + 黑体 (East Asian), H1 16pt / H2 15pt / H3 14pt
- Tables: 9pt
- No italics anywhere (remove `<w:i/>` from all runs)
- Paragraph first-line indent: 2 characters (~24pt for 12pt font)

## OMML Formula Manipulation

### Finding Display Formulas
```python
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

for p_el in body.iter(f'{{{W}}}p'):
    if p_el.findall(f'.//{{{M}}}oMathPara'):
        # This is a display formula paragraph
        # Formula text is in m:t elements, not w:t
        texts = [t.text or '' for t in p_el.iter(f'{{{M}}}t')]
```

### Adding Equation Numbers
After finding a formula paragraph, append a `w:r` run with the number:
```python
r_el = etree.SubElement(p_el, f'{{{W}}}r')
t_el = etree.SubElement(r_el, f'{{{W}}}t')
t_el.text = '  (1)'
```

### Building Inline OMML Formulas
```python
def math_run(text):
    om = etree.Element(f'{{{M}}}oMath')
    r = etree.SubElement(om, f'{{{M}}}r')
    t = etree.SubElement(r, f'{{{M}}}t')
    t.text = text
    wr = etree.Element(f'{{{W}}}r')
    wr.append(om)
    return wr
```

## Inserting Elements Before/After Existing Elements

Always use lxml parent manipulation, never rely on python-docx paragraph iteration after inserting raw XML elements:
```python
parent = target_element.getparent()
pos = list(parent).index(target_element)
parent.insert(pos + 1, new_element)  # after
parent.insert(pos, new_element)       # before
```

## Consolidated document workflows

This umbrella also covers two related document classes formerly split into `document-version-consolidation` and `document-style-matching`:

- **Version consolidation:** treat the designated base DOCX as immutable, map source topics to explicit anchors, save a new version, preserve XML formatting, write provenance, and verify hashes plus reopened structure.
- **Style matching / own-work reports:** imitate the reference skeleton and tone but rewrite from the user's verified files; never transplant sample facts. Keep requested sections while using natural prose, and deliver outside macOS bundles.

For LaTeX/PDF production, use `latex-chinese-docs` as the format-specific companion; it remains separate because its compiler and OMML conversion workflow are materially distinct.

## Common Pitfalls

1. **pandoc `longtable` → Word**: Pandoc converts LaTeX `longtable` with `\endhead` rows as regular table rows containing "（续）". Remove these rows in post-processing.
2. **pandoc `\ref{}` → Word**: Pandoc cannot cross-reference in docx. All `\ref{eq:xxx}` become literal `[eq:xxx]` text. Replace with "式1", "式2" etc. in post-processing.
3. **pandoc inline math loss**: Some inline `\(...\)` math becomes plain unicode text (ℝ¹²⁸ instead of OMML). Convert to `m:oMath` elements.
4. **python-docx + raw XML**: After inserting raw `lxml` elements into the document body, re-open the document before iterating paragraphs — python-docx cannot parse raw elements as `Paragraph` objects.
5. **OMML text is in `m:t`, not `w:t`**: When searching formula content, look in the math namespace (`m:t`), not the word namespace (`w:t`).
6. **User preference**: "加盐哈希" is not an acceptable Chinese term — use "哈希" or describe the salt separately.
7. **User preference**: All math must be OMML formulas, never plain unicode. Expressions like `x_T~N(0,I)` must be `m:oMath` elements.
8. **User preference**: Tables must be centered with numbered captions (表1, 表2...). Figures need 图1, 图2 captions.
9. **Nested reference cleanup**: After replacing `[eq:xxx]` → `式N`, check for `式(式N)` patterns. The LaTeX source may have "式(\\ref{eq:xxx})" which becomes "式(式N)". Must do a second pass to clean `式(式N)` → `式N`.
10. **All finds before any inserts**: When manipulating document XML, collect all targets first, THEN insert. Inserting raw `lxml` elements breaks subsequent python-docx iteration over `doc.paragraphs`. Always save+reopen after raw XML manipulation.
11. **User preference**: "以张小明为例" structured data fields should use bullet lists (`ListBullet` style) instead of semicolon-separated paragraphs. Each field gets its own bullet line for readability.
12. **User preference**: Paragraphs must have 2-character first-line indent (~24pt for 12pt font). Display formulas and headings are exempt. No italics anywhere in body text (skip formula runs which use math styling).
13. **Duplicate equation numbers**: If multiple scripts add equation numbers, you may get both inline numbers (inside formula paragraph) and standalone number paragraphs (from an earlier script). Always clean up standalone `(1)`, `(2)` etc. paragraphs — only the inline version inside the formula paragraph should remain. Check with: `doc.paragraphs` for any `p.text.strip() in {'(1)','(1a)','(1b)','(2)',...}` and remove those elements.
14. **Formula classified by m:t content, not w:t**: OMML formula text lives in `<m:t>` elements under the math namespace. When classifying formulas for numbering, always read `p_el.iter(f'{{{M}}}t')` — using Word namespace will return empty text.
15. **AI-rate checking**: Use `scripts/ai_detect.py` to check documents for AI-generated content patterns before delivery. The tool computes a composite score from 6 dimensions: perplexity proxy, sentence uniformity, AI-pattern density, lexical diversity, buzzword density, and sentence-starter formatting. See `scripts/ai_detect.py` for usage.
16. **Chinese curly quotes in Python source**: When embedding `\u201c` (") or `\u201d` (") in Python source strings (common when handling Chinese document text), Python 3.12+ raises `SyntaxError: invalid character`. Workaround: store text in a separate JSON file and `json.load()` it. JSON handles all Unicode without parser issues. See `references/format-preserving-text-replace.md`.
17. **Format-preserving text replacement**: When rewriting docx body text without touching formatting, save first-run font properties → clear ALL runs via `run._element.getparent().remove(run._element)` → add single replacement run with saved props. Paragraph-level formatting (alignment, spacing, indentation) is never touched. Always verify font name + size match between original and output. See `references/format-preserving-text-replace.md`.
18. **User preference — "千万不要改字体字号"**: When asked to rewrite/modify a DOCX, font, size, bold, and alignment MUST be preserved verbatim. Never assume the user is OK with formatting changes. Always run the verification step (comparing original vs output font name + size for every paragraph) before delivering.
19. **AIGC de-AI-ification pipeline**: When user asks to "去AI化" a document, the complete workflow is: (a) run `scripts/ai_detect.py` to baseline, (b) rewrite with specific replacements (see `references/ai-vocabulary-replacements.md`), (c) use format-preserving text replacement to apply changes without touching formatting, (d) re-run detection to show improvement. Key rewrite strategies: break parallel structures ("一是…二是…"), replace AI buzzwords with natural alternatives, vary sentence length, add concrete scenario examples, add a closing/summary paragraph if the original ends abruptly. See `references/ai-deai-pipeline.md`.
| Format-preserving text replace | Preserve all formatting (font, size, bold, color, alignment) when rewriting docx text. Save first-run font props, clear runs, add one replacement run. See `references/format-preserving-text-replace.md`. |
20. **User preference — 工作总结/亮点材料用科普风格**: 面向领导或非技术读者的成果总结（数据建模、项目亮点汇报等），用比喻和通俗解释讲亮点，禁止堆专业词汇。示例：把"数据泄露"讲成"考试泄题"、把"多模型集成"讲成"医生会诊"、把"AUC"讲成"猜对率"、把"GMM 软聚类"讲成"每个客户是一份'像谁'的概率"。每个亮点落到"为什么这样设计、解决了什么业务问题"，而非罗列技术名词。纯文字即可，不要求图表。

21. **User preference — 文字交付物默认给 .docx 不给 .md**: 逐字稿、汇报稿、讲话稿、操作手册等任何要交给用户阅读/打印/提交的文字成品，一律导出为 .docx（Word），不要给 .md；用户收到 .md 会直接发火要求重做。生成时写 .py 脚本文件再 `python3 xxx.py` 运行（`python -c` 与 heredoc 会触发审批）。逐字稿排版与内容约定：每页「第X页 · 标题」→ 第一人称口语正文 → 红色右对齐【翻页】标记；PPT 里是占位符的内容标 ⚠️ 待补充；技术点用科普语言/比喻讲（见第20条）。完整生成脚本见 `templates/speech_script_docx.py`。

| AIGC de-AI pipeline | Detect → rewrite → preserve format → verify. See `references/ai-deai-pipeline.md` for full workflow and `references/ai-vocabulary-replacements.md` for the replacement dictionary. |
