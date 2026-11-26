# Free Chinese E-Book Download Sources

When Baidu AI Search finds a resource name but links to paywalled sites (book118, docin, renrendoc, taodocs — all require VIP or virtual coins), use these sources for the actual free download.

## GitHub

Search for Chinese classical texts in PDF/ebook form.

### API discovery
```bash
curl -s 'https://api.github.com/search/repositories?q=<keyword>+pdf&per_page=5'
```

### Example: 道德经
- Repo: `tt24h/daodejing` — four-version parallel comparison PDF (王弼本, 帛书本, 郭简本, 汉简本)
- Release assets at `https://api.github.com/repos/<owner>/<repo>/releases`
- Download URL pattern: `https://github.com/<owner>/<repo>/releases/download/<tag>/<filename>.pdf`

### Tips
- Use English keywords (`daodejing`, `tao te ching`) — GitHub search is English-biased
- Check releases tab, not just repo contents — PDFs are typically in releases
- Chinese keyword search works but may return fewer results due to encoding

## Internet Archive (archive.org)

Best source for annotated/translated Chinese classics. Many users upload original scans, annotated editions, and translations.

### Search
```bash
# Find items by title
curl -s 'https://archive.org/advancedsearch.php?q=title:(<chinese_keyword>)+AND+mediatype:(texts)&fl[]=identifier,title,year&rows=10&output=json'
```

### Get file list
```bash
curl -s 'https://archive.org/metadata/<identifier>' | python3 -c "
import sys, json
d = json.load(sys.stdin)
for f in d.get('files', []):
    name = f.get('name', '')
    fmt = f.get('format', '')
    if 'pdf' in name.lower() or 'PDF' in fmt:
        print(name)
"
```

### Download
```bash
curl -L -o <output.pdf> 'https://archive.org/download/<identifier>/<filename>'
```

### Example: 道德经原文译文注释
- Identifier: `daodejing_202605`
- File: `老子道德经：原文译文注释 v0.1.0.pdf` (1 MB)
- Contains: original text + modern Chinese translation + commentary per chapter

### Tips
- Search with Chinese characters in title field
- Filter `mediatype:(texts)` for PDF/ebook content
- Use full Chinese filenames in download URL — URL-encode if needed (spaces, colons)
- archive.org bandwidth can be slow on large files

## When All Else Fails

- **ctext.org** (Chinese Text Project): web-based, no PDF, but authoritative source texts. `curl -sL 'https://ctext.org/dao-de-jing/zh'` for HTML.
- **guoxuedashi.com** (国学大师): web-based classical texts with annotations.
- **Baidu Wangpan** (百度网盘): some Baidu search results include pan.baidu.com links with extraction codes — check the result content field for codes.
