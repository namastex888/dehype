# Publishing plan

How the observatory goes public, what we say about it, and what we never claim. Owner of the plan: the delivery agent (2026-10-16). Hosting mechanics are in [ARCHITECTURE.md](ARCHITECTURE.md#3-publishing).

## Where it lives

```
 today            GitHub Pages     https://namastex888.github.io/trending-research/   (no extra account)
 when secrets set Cloudflare Pages https://trend-observatory.pages.dev  (+ custom domain, e.g. observatory.<yours>)
 both are fed by the same deploy.yml run; the daily refresh redeploys both
```

GitHub Pages is the zero-setup launch host. Cloudflare becomes the primary once the two secrets exist (no commercial clause, unmetered static bandwidth, Workers AI for later answer features). Keep both running; point the custom domain at Cloudflare.

## Launch sequence

| Step | When | What | Done when |
|---|---|---|---|
| L0 | day 0 | Site live on GitHub Pages, daily refresh green once | `refresh` run succeeds and the page shows the new run date |
| L1 | day 0–1 | Soft launch: share with 5–10 people who read AI papers daily; ask for the three queries they tried and what was wrong | 5 replies collected in a GitHub discussion |
| L2 | day 3+ | Cloudflare + custom domain; README badge with the live link | `deploy` shows both jobs green |
| L3 | day 7+ (a week of snapshots, so 7-day momentum is measured, not a rate proxy) | Public launch posts (below) | posts out; issues triaged within 48 h |
| L4 | weekly | "What moved this week" post generated from the 7d view: top movers, new entries, attention-ahead projects, each with its caveat | 4 consecutive weeks |

## Talking points

**One line:** an open, daily-refreshed observatory of AI papers, repos and hyped projects that shows which signals are actually observed, and says "unknown" instead of inventing a number.

**What makes it different**

1. *Evidence coverage on every score.* Each rank carries how much of its evidence was actually observed. Thin evidence pulls the score toward a neutral prior instead of letting one viral post win.
2. *Attention vs discovery.* For hyped projects we plot sampled attention against independent proxies (code activity, paper upvotes, discussion). Above the diagonal = talked about more than evidenced. It is a lead to investigate, not a verdict.
3. *Stars are not activity.* Repos rank on issues, PRs, commits and contributors moving with star growth; star spikes without activity are capped and flagged.
4. *Ask it in plain English.* "agent repos over 1k stars this month", "robots learning from human videos". Filters are exact; the rest is matched by meaning by a small open model running in your browser. No server, no paid API, your query never leaves the page.
5. *Everything is public.* Code (MIT), data snapshots (CC BY 4.0), the full method rendered on the site, and a pull-request process for changing any weight with before/after numbers.

**Demo script (60 seconds)**

1. Papers, 7d → point at the scatter: high score with low coverage sits lower than you'd expect; that is the shrinkage.
2. Search `robots learning from human videos` → semantic matches highlight in the chart.
3. Hype, overall → the attention-vs-discovery quadrant; open a project above the diagonal; show the skeptic signals and the "sampled, not platform-wide" labels.
4. Method tab → every formula and weight, one click from any score.

## Never claim

- Rankings measure capability, adoption, revenue or truth. They are discovery proxies.
- Sampled post counts are platform totals.
- Missing data means low value. Unknown stays unknown.
- The HYPE gap proves hype. It compares percentiles from different proxy cohorts.
- The roadmap items (#4–#21) are shipped. Only the tracker is live; see [ROADMAP.md](ROADMAP.md).

## Channels and drafts

| Channel | Format | Draft |
|---|---|---|
| Hacker News | Show HN | "Show HN: An AI research tracker that says 'unknown' instead of inventing numbers" + 3-line description, link, method link |
| X / Bluesky | thread, 4 posts | hook (attention-vs-discovery chart image) → coverage idea → search demo GIF → link + method |
| LinkedIn | single post | why stars-only rankings mislead; one chart; link |
| r/MachineLearning | [P] project post | method-first: shrinkage, coverage, cohort semantics; ask for critique of weights |
| Newsletters (AI-focused) | short pitch email | one paragraph + og image + "what moved this week" offer |

The preview image for links is `web/og.png` (Open Graph tags are in `web/index.html`).

## Readiness checklist before L3

- [ ] `refresh` has run green 7 days in a row (snapshot momentum measured)
- [ ] Source health shows ≥ 8/10 ok on launch day
- [ ] Mobile check on a real phone (390 px layout passes in headless)
- [ ] `docs/PUBLISHING.md` "Never claim" list re-read against every post draft
- [ ] Someone other than the author tries five queries cold and reports what confused them
