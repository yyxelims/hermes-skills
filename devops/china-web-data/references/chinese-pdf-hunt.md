# Chinese Academic PDF Hunting Guide

## Problem

Chinese document sharing sites (book118, doc88, docin, taodocs) frequently purge user-uploaded academic PDFs due to copyright claims. Web scraping (universal_search.py) returns 0 results for queries containing "PDF", "下载", or "免费" because Chinese search engines filter these terms.

## Two-Step Workflow

### Step 1: Find sources via Baidu AI Search

The Baidu AI Search API bypasses content filters that block web scraping:

```bash
python3 /Users/you/quant-lab/baidu_search.py "书名 作者 PDF 下载"
```

This returns AI-summarized results with source URLs that web scraping would miss entirely.

### Step 2: Check GitHub for the actual PDF

When Chinese doc sites have purged the content, search GitHub:

```
https://github.com/search?q="Book Title" Author+Name&type=repositories
```

GitHub repos are a reliable fallback because:
- They're less targeted by Chinese copyright enforcement
- Many users mirror academic PDFs in repos named after the book
- PDFs in repos can be downloaded directly via raw.githubusercontent.com

### Step 3: Download

```bash
curl -L -o "output.pdf" "https://raw.githubusercontent.com/USER/REPO/main/file.pdf"
```

Verify with:
```bash
file output.pdf
python3 -c "import fitz; d=fitz.open('output.pdf'); print(f'{d.page_count} pages'); d.close()"
```

## Known Repositories

| Book | GitHub Repo | Pages | Size |
|------|------------|-------|------|
| 钱学森《工程控制论》第三版 | Tri985211/engineering_cybernetics | 1067 | 9.9MB |

## When Doc Sites ARE Available

Sometimes doc88 or book118 still have the PDF. Check Baidu AI Search results for these domains:
- `doc88.com` — requires points to download (usually 1000+)
- `book118.com` — VIP required, often purged
- `docin.com` — similar restrictions
- `taodocs.com` — sometimes accessible

For Internet Archive: use advanced search API first to check availability:
```bash
curl -s "https://archive.org/advancedsearch.php?q=title:(TITLE)+AND+creator:(AUTHOR)&fl[]=identifier,title,creator,year,format&output=json&rows=10"
```
Then check if the PDF is downloadable (some are DRM-protected with "printdisabled" tag).

## Anti-Patterns

- **Do NOT** spend more than 2 attempts scraping Chinese doc sites — they purge fast
- **Do NOT** try to bypass doc88/book118 paywalls — they require real accounts
- **Do NOT** use Playwright to interact with doc sharing sites — the PDFs are server-side and require payment
- **Go straight to GitHub** after the first doc site returns "文档已下架"
