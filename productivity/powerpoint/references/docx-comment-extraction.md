# Extracting Word Comments (.docx)

When reviewing patent documents or manuscripts with track-changes comments,
use lxml + zipfile to extract comments without needing Word.

```python
import zipfile
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

with zipfile.ZipFile('document.docx', 'r') as z:
    comments_xml = z.read('word/comments.xml')
    root = etree.fromstring(comments_xml)

    for comment in root.findall(f'{{{W}}}comment'):
        cid = comment.get(f'{{{W}}}id')
        author = comment.get(f'{{{W}}}author')
        date = comment.get(f'{{{W}}}date', '')[:10]
        texts = []
        for p in comment.findall(f'{{{W}}}p'):
            for r in p.findall(f'{{{W}}}r'):
                for t in r.findall(f'{{{W}}}t'):
                    if t.text:
                        texts.append(t.text)
        full_text = ''.join(texts)
        print(f'批注 {cid} | {author} | {date}')
        print(f'  {full_text}')
        print()
```

The `python-docx` library does NOT expose comments through its public API.
Must use the raw XML + zipfile approach.

To also find which paragraph each comment is attached to, parse
`word/document.xml` and look for `<w:commentReference w:id="N"/>` elements.

## Checking if Comments Exist

```python
with zipfile.ZipFile('document.docx', 'r') as z:
    comment_files = [f for f in z.namelist() if 'comment' in f.lower()]
    if comment_files:
        print(f"Found: {comment_files}")
    else:
        print("No comments in this document")
```
