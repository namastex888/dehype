# Signals plan: people, audience and how gossip spreads

Status 2026-10-16: **design, partly built.** Pulse already records, per topic, the first post on every network we collect ("How it spread" in the node drawer). This plan extends that into a people graph and a diffusion trace that ends at the daily newsletter the owner reads. Items marked **owner decision** need an answer before code.

## The picture

```
   curated people (people.json)            networks we read                     end point
 ┌──────────────────────────────┐   ┌──────────────────────────────────┐   ┌────────────────────┐
 │ researchers · lab staff ·    │   │ X (needs API)  Bluesky  Mastodon │   │ daily newsletter   │
 │ builders · journalists ·     │──►│ Reddit  HN  Lobsters  GitHub     │──►│ (owner's inbox or  │
 │ insiders/leakers · investors │   │ arXiv/HF                          │   │  public archive)   │
 └──────────────┬───────────────┘   └───────────────┬──────────────────┘   └─────────┬──────────┘
                │ audience (followers, where free)   │ posts with time + author       │ items with date + links
                ▼                                    ▼                                ▼
        ┌───────────────────────────────────────────────────────────────────────────────────┐
        │ pulse.py: topic match → per topic cascade                                         │
        │   origin (earliest post we saw) → amplifiers (curated, high-audience reposts)     │
        │   → network crossings (HN→Reddit→Mastodon…) → newsletter mention (reached digest) │
        │   latency between steps; who started it; who made it spread                       │
        └───────────────────────────────────────────────────────────────────────────────────┘
                                                     ▼
        Pulse map: node size by voices (today) or by audience reached (new toggle)
        node drawer: cascade timeline + people involved · People tab: who starts what
```

## Pieces

| Piece | What | Data access | Status |
|---|---|---|---|
| Spread trace | first post per network per topic, latency between them | existing feeds | **built** (Pulse drawer) |
| `people.json` | curated list: name, handles per network, role, why they matter; public accounts only, reviewed by PR | committed file | next |
| Audience | follower counts per handle, refreshed weekly | Bluesky, Mastodon, GitHub, Reddit: free public APIs · X: API only | next (free networks) |
| Audience view | toggle on the map: size by audience reached (sum of followers of distinct authors, labelled "potential reach, not views") | from the two rows above | next |
| People graph | who mentions / replies to / quotes whom among curated people | Bluesky + Mastodon free; X needs API | after `people.json` |
| Cascade detection | per topic: origin → curated amplifiers → network crossings → newsletter; flag "starting to spread" when a topic crosses its second network or a curated high-audience account picks it up | all of the above | after people graph |
| Newsletter source | items from AI newsletters as the "reached the digest" end point | 12 public RSS feeds in `newsletters.json` (Rundown, Neuron, AINews/Latent Space, TLDR AI, Decoder, Techmeme, AlphaSignal, Zvi, Simon Willison, Import AI, Interconnects, Agent Uptime; AI Minds has no public feed and Claw's Newsletter returns 404) | **built**; email-only newsletters (Superhuman AI, Turing Post, AI Breakfast, Axios AI+) need the dedicated inbox in decision 2 |
| Newsletter citations | the domains and X handles each newsletter item links to, so the digests can be reverse-engineered | links read from the item HTML before stripping; `pulse.json` `citations` (top 50 per window, with the newsletters citing each and the topics of those items) | **built**; the handle list is a candidate follow list for decision 1 (X List), reviewed by the owner before anyone is added |
| Official source | lab and vendor announcements as the origin of a launch | `official_feeds.json` (verified RSS/Atom; Anthropic through a community mirror) | **built** |
| X | the network where most AI gossip starts | see decision 1 | owner decision |

## Owner decisions

**1. X access.** Following people with your account does not give a pipeline access to their posts; X only allows automated reading through its API.

| Option | Terms | Cost | Recommendation |
|---|---|---|---|
| A. Official X API: your developer account reads a private X List of the curated people | compliant; bearer token as a secret in one workflow step | paid tier; check the current price on developer.x.com before deciding | **recommended if X matters enough to fund** |
| B. Your logged-in account driven by a local script (cookies / browser automation) | violates X's terms; account-ban risk; cannot run in public CI | free | not for this pipeline |
| C. No X collection: curate the X List for your own reading; we follow the same people on Bluesky/Mastodon where they cross-post | compliant | free | default until A is funded |

**2. Newsletter.** Which newsletter is it?
- If it has a **public web archive or RSS** (many AI dailies do), we read that: no private data, runs in CI today.
- If it exists only in your inbox: forward it to a dedicated mailbox and read it with the Gmail API (OAuth refresh token as a secret). We publish only derived facts (newsletter name, date, topics matched, public links it cites), never the email text.

**3. Who is on the list.** Start from ~50 public accounts the owner already follows for AI news; each entry states why (role) so the list stays reviewable. Private individuals are not added.

## Honesty rules for this layer

- "Origin" means the earliest post in our sampled feeds, never proof of who started it.
- Audience is follower count at collection time, labelled "potential reach", never views or impressions.
- A cascade shows that people discussed a name in that order; it does not verify the claim (a rumour node stays a rumour).
- Raw private data (inbox, X API payloads under its terms) is not published; only aggregates and public links.

## Tools considered (2026-10-16)

Reviewed read-only; none is adopted as code. The pipeline stays standard-library Python, unattended and terms-compliant.

| Repository | Licence | How it gets data | Verdict |
|---|---|---|---|
| mvanhorn/last30days-skill | MIT | HN Algolia, arctic-shift Reddit archive, Bluesky app password; paid routes for X | **approach adopted** for Reddit (arctic-shift) with attribution; fine as an interactive skill |
| Panniantong/Agent-Reach | MIT | logged-in cookies for Reddit and X | rejected: cookie scraping, takes over research prompts |
| msitarzewski/agency-agents | MIT | none (persona prompts) | rejected for the pipeline |
| sansan0/TrendRadar | GPL-3.0 | third-party newsnow server (relays cookie-scraped Weibo/Douyin) | rejected as code (GPL into MIT, goodwill server); ideas only |
| davidteather/TikTok-Api | MIT | headless browser, user cookies, stealth scripts, residential proxies | rejected |
| facebookresearch/Kats | MIT | none (statistics library; pins old numpy/pandas) | borrow the method only: a stdlib CUSUM / robust z-score change-point test, after enough daily history (council dissent: about 8 weeks) |
| ericciarla/trendFinder | MIT | paid X API, Firecrawl, OpenAI | rejected (paid keys; LLM "why it's rising" only if the owner funds a capped model) |
| ScrapeCreators/social-media-research-skills | MIT (skill text) | paid ScrapeCreators API, credits per call | not in the pipeline; at most an opt-in interactive skill (council dissent: none) |
| ZJU-REAL/Easel | Apache-2.0 | logged-in browser publishing, cookie extraction, volunteer hot-list APIs | rejected |

Council record: five lenses, decision proceed-with-conditions; consensus "adopt none as code"; dissent opposes installing any skill and calls both borrowed ideas premature.
