---
name: regulatory-monitoring-workflows
description: Use for Chinese regulatory monitoring and leader research.
tags: [regulatory, policy, leadership, scraping, chinese-web, evidence]
---

# Regulatory Monitoring Workflows

Use this class skill for projects that monitor Chinese regulators, bank leadership, leadership work portfolios, and credit-card/consumer-finance/payment regulation.

## Consolidated class notes

This umbrella absorbs `policy-tracking`, `dynamic-policy-data-pipelines`, and `leader-portfolio-research`. Use the workflow below as the class-level contract; retain their provider/site-specific date extraction, body-cleaning, Playwright, and script details in the linked references rather than creating separate skills. The former policy-tracking rule that LLM relevance filtering was unreliable is superseded by the explicit strict-relevance gate here: validate the current policy scope and test the classifier on representative false positives before production.

## Core workflow

1. Identify authoritative first-party sources and their current entry pages.
2. Refresh every available source before building a report.
3. Normalize all successful JSON shapes into one article pool.
4. Fetch and clean full detail-page bodies; discard empty, CSS/JS, or clearly incomplete bodies.
5. Deduplicate mechanically by canonical URL, normalized title, and body fingerprint.
6. Use the LLM only for strict business relevance classification.
7. Generate summaries only for retained articles, from the full body.
8. Build the Excel deliverable and run structural/content validation.

The LLM must not be used to paper over missing source data, infer facts from names, or summarize articles that will later be discarded.

## Leadership portfolio evidence

For each leader, search the leader's own institution first using combinations of:

- `姓名 + 分管处室`
- `姓名 + 分管工作`
- `姓名 + 负责工作`
- `姓名 + 联系处室`
- `姓名 + 领导活动/讲话/调研`

Priority page types: official leader profile, institutional functions, internal departments, authority/responsibility lists, formal division-of-work documents, and official activity pages explicitly naming departments or responsibilities.

Evidence grades:

- **A** — first-party page explicitly says the leader is responsible for a business; suitable for current responsibility.
- **B** — first-party page explicitly names supervised departments and the work area can be read from the body; suitable for “historical portfolio and main work.”
- **C** — multiple first-party activities consistently show a work focus; label only as “publicly documented work focus.”
- **D** — media inference, one-off attendance, or name mention; never write into the portfolio field.

Always store the source URL and publication year. Historical evidence must not be presented as current formal responsibility. If there is no authoritative evidence, leave the field blank.

## Strict business relevance

Keep an article only when the article itself directly concerns credit cards, consumer finance/personal consumer lending, payment/acquiring, card clearing, or directly applicable consumer protection, credit reporting, AML/anti-fraud, or digital-RMB payment regulation.

Exclude incidental bank-name mentions, ordinary macro/monetary policy, generic cross-border finance, ordinary bank AI, generic bank operations, product promotions, and articles that explicitly say a rule does not apply to credit cards without changing credit-card rules.

BANK is a priority service object, not the only bank. Collect other relevant banks under the same relevance standard.

## Freshness and failure gates

A dynamic run must check both file freshness and content count. A non-zero process exit, missing source, empty output, or stale core source stops workbook generation. Never let a recent timestamp on an empty file count as success. For unstable external sites, do not promise a stabilization date; mark the source partial/non-core, retry boundedly, log status, and allow automatic re-entry when it recovers.

## Source integration pitfalls

- Do not claim a source is covered merely because its scraper ran; verify that its records enter the unified candidate pool.
- Flatten list, nested-list, and dictionary-with-tabs JSON structures before normalization.
- Browser/list records without a usable detail body are not article candidates until their detail pages are fetched.
- Avoid hard-coded dated filenames; select the newest valid output dynamically.
- When a source's old section URL is a stale archive, use the current homepage/topic block and document the change.

## Beijing district-department leadership coverage

“16区区级领导已覆盖” is not the same claim as “16区各委办局领导已覆盖.” The first covers district-level party/government rosters; the second requires opening each district’s official “机构信息/政府部门” directory and each target bureau’s own “领导介绍” page. Keep the two layers in separate datasets and report the covered districts/departments explicitly. A user-named bureau (for example, 某城区文化和旅游局) must be verified first from its official page and reported with names, titles, and the official URL before generalizing coverage.

For the Beijing district-department expansion, prioritize 文旅、商务、市场监管、发展改革、政务和数据、金融工作/金融管理 departments. Do not infer bureau leaders from district leaders, news attendance, or a district homepage. The bureau roster should include the current head and deputy heads shown on the bureau’s own page; preserve兼任/挂职/执法大队长 wording exactly. If a district site only exposes a department directory or a stale page, record that gap rather than claiming full coverage.


When the business focus is Beijing, include all 16 district governments rather than only municipal-level agencies. Use the Beijing municipal government hub `https://www.beijing.gov.cn/gongkai/zfxxgk/fdzdgknr/sjbmqzf/` to discover each district's official leader page; the page provides district-specific URLs and avoids guessing a shared `/ldjs/` path. District leader pages are structurally inconsistent and often separate 区委/区政府/区人大/区政协 tabs. For target work, extract at least 区委 and 区政府 leaders, and verify the district chief from the district government's own page plus recent official appointment/election notices. Do not treat a stale committee-only page as a complete district leadership list.

For Fengtai, the committee page `https://www.bjft.gov.cn/xxfb/ldxx/` does not by itself contain the district government roster. Follow the 区政府领导 tab `https://www.bjft.gov.cn/xxfb/ldxx/qzfld/`. The official 2025 notices confirm 张艳林 was appointed代理区长 on 2025-03-26 and elected区长 on 2025-07-18/19; this is the required pattern for detecting a newly elected district chief.

For district policy/news coverage, separate formal policy notices from actionable consumption-scene dynamics. The latter include consumption festivals, commercial districts, ticket-economy, cultural-tourism consumption, coupons, and payment-service arrangements. Keep them in a separate scene/dynamics sheet; do not force non-regulatory scene stories into the regulatory-news table. Fetch full正文 and generate a body-based summary for the scene sheet.

## Business-facing HTML delivery

When converting the workbook to a single interactive HTML, preserve the business conclusions but hide technical/source columns: do not display source names, original links, or raw-body columns by default; keep long summaries and evidence expandable inline. Rewrite the business summary as factual `当前情况 / 业务判断 / 事实依据`, not instructional language such as “先看/再看/如何使用”. Remove empty or meaningless fields (for example, an all-empty importance level) instead of displaying them. Version deliverables rather than overwriting a prior reviewed workbook (v1, v2, v3...). Validate actual sheet counts, row counts, visible headers, summary text, and expand controls in a browser.

## Deliverable and communication

Keep user-facing updates short and concrete: report actual counts, file path, and validation result. Do not replace execution with a long plan. Business Excel should expose conclusions, evidence, full source text, and business impact—not internal LLM, scraping, cache, or script terminology. When the user asks for brevity, answer with the result first and omit process narration.

## References

- `references/beijing-district-department-leadership.md` — verified district-department directory flow and Fengtai Culture & Tourism Bureau roster.
- `references/leader-portfolio-and-unified-pipeline.md` — evidence grading, official-page discovery, unified source-pool design, and freshness gates.
