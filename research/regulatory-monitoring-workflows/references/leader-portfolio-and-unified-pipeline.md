# Evidence notes and implementation recipe

## Official-page patterns found

- Beijing Financial Management Bureau: activity pages titled “分管处室” can name both the leader and supervised offices. Example: Wang Ying's 2023 page names 银行保险处、金融发展协调处、行政审批处、发展中心. Li Jingxiang pages name historical supervised offices and a rural-finance work item. These are B-grade historical evidence unless a current division document confirms them.
- PBC: the official institutional-functions page is useful for mapping departments to domains (monetary policy, credit policy, macroprudential, financial stability, payments, credit reporting, AML), but does not by itself prove which deputy governor owns which department.
- SAFE: official leader/activity pages establish the leader's institutional role and recurring work focus (foreign exchange, cross-border investment/financing, international cooperation), but recurring public work is not the same as a formal internal portfolio.

## Search recipe

For each current leader, search the institution's own domain with:

- `姓名 分管处室`
- `姓名 分管工作`
- `姓名 负责工作`
- `姓名 联系处室`
- `姓名 领导活动`
- `姓名 调研`

Fetch the detail page and extract the exact sentence naming the office or responsibility. Save URL, publication date, evidence grade, and validity (`historical`, `current`, `unknown`). Leave unknown fields empty.

## Unified source pool recipe

Load the newest valid output from every successful collector, flatten list/dict/nested-tab JSON, normalize title/body/date/url/site, then deduplicate by canonical URL, normalized title, and body hash. Only records with a usable full body proceed to relevance classification. A scraper's successful exit code is not sufficient: require fresh mtime and positive content count. If a source is empty or stale, mark it partial/non-core and do not use its old output as a new run.

## User-facing style

Give the actual count, result path, and validation status first. Keep updates short; do not narrate long plans or repeat implementation detail unless asked.
