# Sports Match Odds — When Polymarket Has No Markets

Polymarket rarely covers individual sports match outcomes (esp. non-US sports).
Use this fallback when the user asks for match-level betting data.

## Primary Source: OddsPortal (oddsportal.com)

OddsPortal aggregates 1X2 odds from dozens of bookmakers. It requires JS rendering.

### Extraction Recipe (browser_console)

Navigate to the sport/league page, then run in `browser_console`:

```js
let matches = [];
document.querySelectorAll('a').forEach(a => {
    let text = a.textContent.trim();
    if (text.includes('–') || text.includes('-')) {
        let parent = a.closest('div[class*="flex"], div[class*="event"], div[class*="match"]');
        if (!parent) parent = a.parentElement?.parentElement;
        let fullText = parent ? parent.textContent.trim() : '';
        matches.push({match: text, context: fullText.substring(0, 200)});
    }
});
JSON.stringify(matches, null, 2);
```

The `context` field will contain three decimal numbers: Home win odds, Draw odds, Away win odds.
Example output: `"00:00Spain–Cape Verde1.1113.5031.00"` → 1.11 / 13.50 / 31.00.

### Odds → Implied Probability

```
raw_prob = [1/odds_1, 1/odds_X, 1/odds_2]
overround = sum(raw_prob)
true_prob = [p / overround for p in raw_prob]  # normalise to 1.0
```

### Score Prediction Heuristic

1. Use implied win probability as prior
2. Cross-reference FIFA rankings (Wikipedia: `FIFA Men's World Ranking`)
3. Map strength gap to typical scorelines from historical World Cup data:
   - 85%+ favourite → most common: 3-0, 4-0, 2-0
   - 60-70% favourite → most common: 2-0, 2-1, 1-0
   - ~50% (coin flip) → most common: 1-0, 1-1, 0-0
4. Assign confidence as win_prob × historical_score_frequency
   - Typical ceiling for exact score prediction: 20-30%

## Alternative Sources

| Source | Access | Notes |
|--------|--------|-------|
| OddsPortal | Browser (JS) | Best coverage, free tier shows avg odds |
| Flashscore | Browser | Live scores + some odds |
| Sofascore | Browser | Good for in-play data |
| Bet365 / Betfair | Browser | Requires geo/IP; heavy JS |
| Wikipedia | curl (API) | FIFA rankings, group schedules, historical results |

## 2026 World Cup Specifics

- Group stage: June 11–27, 2026. 48 teams, 12 groups (A–L), top 2 + 8 best 3rd advance
- Wikipedia pages: `2026_FIFA_World_Cup`, `2026_FIFA_World_Cup_Group_[A-L]`
- FIFA rankings API: `parse&page=FIFA_Men%27s_World_Ranking` on en.wikipedia.org/w/api.php
- The rankings table in Wikipedia raw text is hard to parse; prefer the group-specific pages
  which include FIFA rank numbers in the team info rows
