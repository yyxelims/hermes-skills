# Programmatic .docx Content Insertion

## Use Case

When you need to insert large blocks of formatted content at a specific position inside an existing .docx file (e.g., appending sections before a chapter heading, injecting comment responses into a patent disclosure, adding new chapters to a report).

## The `insert_content_before_heading` Pattern

python-docx doesn't have a native "insert paragraph at position N" API. The workaround is to create paragraphs via `doc.add_paragraph()`, which appends to the body, then use lxml to move the new `<w:p>` elements to the desired position.

```python
from docx import Document
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def insert_content_before_heading(doc, heading_text, content_blocks):
    """
    Insert paragraphs before the first heading containing `heading_text`.
    
    content_blocks = [(style_name, text, bold, font_size), ...]
    Style names: 'Heading 1', 'Heading 2', 'Heading 3', 'Body Text', 'Normal'
    """
    # Find target paragraph
    target_element = None
    for p in doc.paragraphs:
        if p.style.name.startswith('Heading') and heading_text in p.text:
            target_element = p._element
            break
    
    if target_element is None:
        return  # Heading not found
    
    parent = target_element.getparent()
    target_pos = list(parent).index(target_element)
    
    # Create paragraphs, then move them before the target
    for style_name, text, bold, size in reversed(content_blocks):
        p = doc.add_paragraph()
        if style_name.startswith('Heading'):
            level = int(style_name[-1])
            p.style = doc.styles[f'Heading {level}']
        else:
            p.style = doc.styles[style_name]
        
        p.clear()
        run = p.add_run(text)
        if bold: run.bold = True
        if size: run.font.size = size
        run.font.name = '宋体'
        
        # Set East Asian font
        rPr = run._r.get_or_add_rPr()
        rFonts = etree.SubElement(rPr, f'{{{W}}}rFonts')
        rFonts.set(f'{{{W}}}eastAsia', '宋体')
        
        # Move before target (reversed order = correct final order)
        parent.insert(target_pos, p._element)
```

## Usage Example

```python
content = []
content.append(('Heading 2', '新章节标题', True, Pt(14)))
content.append(('Body Text', '这是正文段落。', False, Pt(11)))
content.append(('Normal', '这是另一个段落。', False, Pt(11)))

insert_content_before_heading(doc, '双模型协同', content)
doc.save('output.docx')
```

## Pitfalls

1. **Table cells have separate text frames** — if you're modifying text in tables, iterate `shape.table.rows → cell.text_frame.paragraphs`, not just `shape.text_frame`.
2. **Style name lookups are case-sensitive** — use exact names from the original document (check with `p.style.name`).
3. **Font settings on runs require XML manipulation** — `run.font.name = '宋体'` only sets the Latin font. For Chinese documents, also set `<w:rFonts w:eastAsia="宋体"/>` via lxml.
4. **Preserve original font sizes and formatting** when doing find-and-replace on existing text — capture `run.font.size`, `run.font.bold`, `run.font.color.rgb` before clearing and re-adding.
