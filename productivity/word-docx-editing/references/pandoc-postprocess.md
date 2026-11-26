# Pandoc LaTeX → DOCX Post-Processing Recipe

## Pre-Conversion: Fix LaTeX

Pandoc cannot handle `\begin{align}...\end{align}` with `\notag`. Before conversion:

```python
# Replace align blocks with separate equation environments
old = r'''\begin{align}
h_k &= \bar{A}_k \cdot h_{k-1} + \bar{B}_k \cdot e_k \label{eq:mamba} \\
y_k &= C_k \cdot h_k \notag
\end{align}'''
new = r'''\begin{equation}
h_k = \bar{A}_k \cdot h_{k-1} + \bar{B}_k \cdot e_k \label{eq:mamba}
\end{equation}
\begin{equation}
y_k = C_k \cdot h_k
\end{equation}'''
```

## Post-Conversion Fixes (in order)

### 0. CRITICAL: Collect all targets before any inserts
```python
# PHASE 1: Find everything
formula_els = [el for el in body.iter(f'{{{W}}}p') if el.findall(f'.//{{{M}}}oMathPara')]
table_els = body.findall(f'.//{{{W}}}tbl')
image_els = [el for el in body.iter(f'{{{W}}}p') if el.findall(f'.//{{{W}}}drawing')]

# PHASE 2: Insert (never iterate doc.paragraphs after raw XML inserts)
for el in formula_els: parent.insert(pos, make_right_para(f'({num})'))
for tbl_el in table_els: parent.insert(pos, make_caption(f'表{i+1}：...'))
for img_el in image_els: parent.insert(pos, make_caption(f'图{i+1}：...'))

# PHASE 3: Save and re-open before any python-docx iteration
doc.save(path); doc = Document(path)
```

### 1. Remove longtable "续" rows
Pandoc converts `\endhead` as regular table rows:
```python
for table in doc.tables:
    tbl = table._tbl
    rows_to_remove = []
    for i, row_el in enumerate(tbl.findall(f'{{{W}}}tr')):
        first_cell = row_el.find(f'.//{{{W}}}t')
        if first_cell is not None and first_cell.text and '续' in first_cell.text:
            rows_to_remove.append(row_el)
    for row_el in rows_to_remove:
        tbl.remove(row_el)
```

### 2. Replace `\ref` references (TWO-PASS)
```python
# Pass 1: Replace [eq:xxx] references
eq_map = {
    '[eq:mamba]': '式1', '[eq:zoh_a]': '式1a', '[eq:zoh_b]': '式1b',
    '[eq:zu]': '式2', '[eq:forward]': '式3', '[eq:reverse]': '式4',
    '[eq:loss]': '式5', '[eq:score]': '式6', '[eq:deviation]': '式7',
}
for p in doc.paragraphs:
    for old, new in eq_map.items():
        if old in p.text:
            for r in p.runs:
                r.text = r.text.replace(old, new)

# Pass 2: Clean nested "式(式N)" → "式N"
nested_fixes = {
    '式(式1)': '式1', '式(式1a)': '式1a', '式(式1b)': '式1b',
    '式(式4)': '式4', '式(式6)': '式6', '式(式7)': '式7',
}
for p in doc.paragraphs:
    for old, new in nested_fixes.items():
        if old in p.text:
            for r in p.runs:
                r.text = r.text.replace(old, new)
```

### 3. Convert plain-text math to OMML
Pandoc sometimes converts inline math to unicode instead of OMML. Rebuild affected paragraphs:
```python
def math_run(text):
    om = etree.Element(f'{{{M}}}oMath')
    r = etree.SubElement(om, f'{{{M}}}r')
    t = etree.SubElement(r, f'{{{M}}}t'); t.text = text
    wr = etree.Element(f'{{{W}}}r'); wr.append(om)
    return wr

def text_run(text):
    wr = etree.Element(f'{{{W}}}r')
    rPr = etree.SubElement(wr, f'{{{W}}}rPr')
    rf = etree.SubElement(rPr, f'{{{W}}}rFonts')
    rf.set(f'{{{W}}}ascii', 'Times New Roman')
    rf.set(f'{{{W}}}eastAsia', '宋体')
    t = etree.SubElement(wr, f'{{{W}}}t'); t.text = text
    return wr

def rebuild_para(p_element, runs):
    for old_r in p_element.findall(f'{{{W}}}r'):
        p_element.remove(old_r)
    for r in runs:
        p_element.append(r)

# Usage: replace "x_T~N(0,I)" with OMML
rebuild_para(p_element, [
    text_run('从纯噪声 '),
    math_run('x_T \\sim \\mathcal{N}(0, I)'),
    text_run(' 出发，执行DDIM 50步逆向去噪...'),
])
```

### 4. Add equation numbers to display formulas
Formula text is in `m:t` (math namespace), NOT `w:t`:
```python
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'

for p_el in body.iter(f'{{{W}}}p'):
    if p_el.findall(f'.//{{{M}}}oMathPara'):
        texts = [t.text or '' for t in p_el.iter(f'{{{M}}}t')]
        full = ''.join(texts)
        # Classify formula by content
        if 'h_k' in full and 'bar' in full: num = '1'
        elif 'z_u' in full and 'W_p' in full: num = '2'
        # ... etc
        if num:
            r_el = etree.SubElement(p_el, f'{{{W}}}r')
            t = etree.SubElement(r_el, f'{{{W}}}t')
            t.text = f'  ({num})'
```

### 5. Format "以张小明为例" structured data as bullets
```python
def make_bullet_para(text):
    p_el = etree.Element(f'{{{W}}}p')
    pPr = etree.SubElement(p_el, f'{{{W}}}pPr')
    pStyle = etree.SubElement(pPr, f'{{{W}}}pStyle')
    pStyle.set(f'{{{W}}}val', 'ListBullet')
    # ... add run with text
    return p_el

# For field-by-field data (like preprocessing steps)
fields = full_text.split('；')
for field in fields:
    if field.strip():
        parent.insert(pos, make_bullet_para(field.strip() + '；'))
# Remove original semicolon paragraph
parent.remove(original_el)
```

### 6. Fix image sizes
```python
for d in p._element.findall(f'.//{{{W}}}drawing'):
    for ext in d.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}ext'):
        ext.set('cx', str(int(5.0 * 914400)))  # 5 inches wide
```

### 7. Apply consistent formatting
- Font: Times New Roman 12pt + 宋体 (body), 黑体 (headings)
- No italics: remove `<w:i/>` from all non-math runs
- Paragraph indent: first_line_indent = Pt(24) (~2 Chinese chars)
- Tables: centered, dark header, zebra rows
- Captions: centered, "表N：..." / "图N：..."
