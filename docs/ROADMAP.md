# Roadmap: current sequencing

Owner of sequencing since 2026-10-16: the delivery agent, by delegation from the repository owner. The original 20-issue plan ([WISH](../.genie/wishes/open-intelligence-observatory/WISH.md), tracking [#1](https://github.com/namastex888/trending-research/issues/1)) stays the scope of record; nothing is dropped or declared done here. What changes is the order: **the dehype briefing on several static pages is the public surface that comes first** (the daily AI reality briefing, design [open-ai-reality-media](../.genie/brainstorms/open-ai-reality-media/DESIGN.md), delivered as wish [dehype-s1](../.genie/wishes/dehype-s1/WISH.md)), because every later layer (investigation, assistant, community) needs readers and a live surface to land on. Architecture map: [ARCHITECTURE.md](ARCHITECTURE.md).

## Decisions

| # | Decision | Why | Revisit when |
|---|---|---|---|
| D1 | Ship the public tracker before the remaining M1 investigation work | it already has real data and daily refreshes; it was only missing a usable UI and hosting | — |
| D2 | Host on GitHub Pages only, deployed by GitHub Actions (`deploy.yml`, one job) | free static hosting with no account beyond GitHub and no secret to hold; the owner dropped the second host, so its job is gone | traffic or features need a server |
| D3 | Refresh in GitHub Actions; pipeline state in the Actions cache, the record in git: the daily ledger on Pages and each day's input manifest on a dated GitHub Release | the old refresher lived outside the repo; a dated Release keeps the inputs durable at no cost | history must outlive cache eviction for trends: rebuild it from the dated Release manifests and the committed story-id archive, not from object storage |
| D4 | "AI search" = local question parser + semantic ranking with a small open embedding model, vectors built at refresh time, query embedded in the browser Workers AI is out with Cloudflare (D2): search by meaning runs in the browser, and an answer layer would need its own decision. | zero cost, no server, query stays private; the parser keeps filters exact | an LLM answer layer (summaries, Q&A over evidence) is wanted: Workers AI behind a Pages Function, with a spend cap |
| D5 | Several static pages (briefing, stories, output, Hype, method, audit) sharing one `dehype.css` and one `dehype.js`, no build; the frontend adapter writes data and string tables, never HTML | the briefing, method and audit views each need their own page and URL; still no bundler (R1-4 reopened the one-file rule) | a page needs server-side state |
| D6 | DSH assistant (#4 → #10) and read model (#7) stay in scope but behind P1–P4 | both need owner credentials, spend caps and two independent reviews that are not available today | owner supplies the prerequisites |

## Next deliveries

| Step | Delivery | Builds on | Status |
|---|---|---|---|
| P1 | Console UI: charts, filters, smart + semantic search, detail drawer | layer 0 | live |
| P1b | **Pulse**: default topic map from sampled HN, Reddit (arctic-shift), Mastodon, Lobsters, tracker and dossier posts; rising topics; evidence posts per node | P2 | this change |
| P2 | Hosting + daily self-update + CI gate | P1 | live on GitHub Pages |
| P2b | More voices: Bluesky (app password), YouTube Data API (free key), official Reddit API if approved; X only via a paid, terms-compliant route (official API or xAI search) if the owner funds it | P1b | planned |
| P2c | **People and diffusion**: curated `people.json`, audience from free APIs, audience-weighted map, people graph, gossip cascade from origin to the owner's daily newsletter ([SIGNALS_PLAN.md](SIGNALS_PLAN.md)); spread trace per topic already built | P1b | owner decisions: X access, newsletter source |
| P3 | Richer search corpus: embed abstracts (the pipeline stores titles only today) and README excerpts; optional LLM answer card over the top results via Workers AI with a hard daily cap Workers AI is out with Cloudflare (D2); the answer card would need another no-server route. | P2 | planned |
| P4 | Durable history: the daily ledger on Pages (`web/ledger/`, with its story-id archive and timestamp proofs) plus each day's input manifest on a dated GitHub Release, so the record survives cache eviction without object storage | P2 | the ledger and Releases land with dehype S1 (groups E1, E2); weekly-snapshot trimming of `data.json` stays planned |
| P5 | Trend-over-time charts per item (needs ≥ 14 daily snapshots from P2/P4) | P4 | planned |
| P6 | Link the frontier-economics investigation explorer (`web/prototypes/`, #8's chosen direction) from the console | #6, #8 | planned |
| P7 | Continue #7 → #9 → #12 (read model, relationship lens/inspector, first published investigation) | owner prerequisites | blocked |
| P8 | #4 → #10 assistant, #13–#21 per milestone order | P7 | blocked / not started |

## How the roadmap issues map onto the steps

- **#14 (automated adapters with health)**: P2 gives a scheduled run with per-source status on the page; the remaining criteria (quota back-off, preserved last-good evidence, budget) stay open.
- **#21 (CI gates)**: P2 adds a real CI pipeline; its acceptance (broken-provenance and network-replay failures caught, deployed behavior verified) stays open.
- **#13 (offline replay)**: `run.py --rescore` exists; CI runs fixtures only. Not accepted.
- None of these are marked accepted by this change.

## Later pillars (design rows OUT of S1; each is its own wish)

S1, the daily briefing, is wish [dehype-s1](../.genie/wishes/dehype-s1/WISH.md). The rest of the design's G-sized scope waits on S1 passing (14 dated briefings and the owner's confirm). Each pillar's open question is asked when that pillar is designed (R3-1); none is dropped, and the owner can pull any forward.

| Pillar | Delivery | Deferred question | Status |
|---|---|---|---|
| S2 | Verdict policy beyond the S1 rows and their policy text | designed once S1 has passed | planned |
| S3 | Risk and jobs sources: the risk event log and the jobs panel, placeholders in S1 until a qualified, licensed source exists | O12: what "how doomed are we" means for the risk log; O6: which external indicators come first (only BLS qualifies, for general labour context) | planned |
| S4 | Awareness map | A10: which stated proxy the map uses | planned |
| S5 | Audit trail: the recompute verifier R2-4 names, reading each dated Release's input manifest plus a numbers-only gauge-input asset (each story's computed fields and the per-area output counts the gauges were built from); until it is green no gauge reads "shipped" | O30: how the verifier checks the voice-based gauge components, since the manifest carries no handles and Reddit only as hashes | planned |
| S6 | Channels beyond the feed and the AI-builders audience path | O4b: how "becoming popular against bubble leaders" is framed | planned |
| G1 | Governance: the open-suggestions channel, personhood with bridging ratings, the DAO | O16: the phase-1 open-suggestions channel and what triggers phase 2 | planned |

## Superseded statements

Two older documents are kept as written on their dates; where they disagree with this roadmap, this roadmap holds.

- [PUBLISHING.md](PUBLISHING.md) (launch plan, 2026-10-16): its Cloudflare lines (the Cloudflare URL, "Cloudflare becomes the primary", step L2) are superseded by D2, GitHub Pages only. Its "Code (MIT), data snapshots (CC BY 4.0)" reads, from the licence change forward, code AGPL-3.0 and data CC BY-SA 4.0 for our selection, arrangement and computed fields; earlier releases keep MIT and CC BY 4.0.
- [SIGNALS_PLAN.md](SIGNALS_PLAN.md), the TrendRadar row: "GPL into MIT" no longer applies, because this code is now AGPL-3.0 and GPL-3.0 code can be combined with it (section 13 of both licences); the verdict stands for its other reason, the goodwill server that relays cookie-scraped data.
