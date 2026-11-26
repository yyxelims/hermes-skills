# Official Chinese Government Leadership-Page Verification

## Evidence standard

- Search engines and AI-search result snippets are discovery aids only.
- Evidence must come from the body of an official district-government or department page.
- Prefer pages titled `领导介绍`, `领导信息`, or `领导班子`; an official dated article may corroborate a name/title but should be labeled as corroboration rather than substituted silently.
- Do not use Baike, media, appointment reports, or third-party directories to fill a missing current leader.

## Batch checklist

For each district × department cell, record:

1. Department's official name, including post-reform variants (`政务服务管理局`, `政务服务和数据管理局`, `政务和数据局`, etc.).
2. Direct official URL.
3. Names and exact titles literally shown in the page body.
4. Whether the page is a current leadership page or only an institution/function page.
5. Explicit status: `已找到`, `官网领导页未找到`, or `页面正文未显示姓名`.
6. Any corroborating official article URL, kept separate from the leadership-page URL.

Use a fixed matrix (district rows × department columns) so no requested cell disappears from the final report. A missing page is a result and should be reported explicitly, not inferred from neighboring districts or historical appointment notices.

## Browser extraction

If the accessibility snapshot omits dynamic content, open the direct official page in the browser and inspect `document.body.innerText` with the browser console. Confirm the page footer/breadcrumb identifies the government site. Preserve the exact URL and the relevant body text before drafting.

## Compact output schema

```text
### District
- Department — official URL
  Name: title; Name: title
  Status: 已找到 / 官网领导页未找到 / 页面正文未显示姓名
  Corroboration (optional): official article URL
```

## Pitfalls

- A page listing departmental responsibilities is not a leadership page.
- A search snippet can contain names from stale indexing; never cite it as page正文.
- “原党组书记、原局长” and historical appointment pages are not current leaders.
- Agency renaming during reforms can produce duplicate-looking pages; verify the page date, current department name, and whether the listed office still exists.
- HTTP, legacy subdomains, and mobile/print URLs may still be official; validate the government-site footer and domain before accepting them.
