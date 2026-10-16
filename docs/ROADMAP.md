# Roadmap: current sequencing

Owner of sequencing since 2026-10-16: the delivery agent, by delegation from the repository owner. The original 20-issue plan ([WISH](../.genie/wishes/open-intelligence-observatory/WISH.md), tracking [#1](https://github.com/namastex888/trending-research/issues/1)) stays the scope of record; nothing is dropped or declared done here. What changes is the order: **a public, self-updating, good-looking tracker comes first**, because every later layer (investigation, assistant, community) needs readers and a live surface to land on. Architecture map: [ARCHITECTURE.md](ARCHITECTURE.md).

## Decisions

| # | Decision | Why | Revisit when |
|---|---|---|---|
| D1 | Ship the public tracker before the remaining M1 investigation work | it already has real data and daily refreshes; it was only missing a usable UI and hosting | — |
| D2 | Host on Cloudflare Pages, deployed by GitHub Actions | free static bandwidth, no non-commercial clause, Workers AI on the same account for search ([details](ARCHITECTURE.md#3-publishing)) | traffic or features need a server |
| D3 | Refresh in GitHub Actions; state in the Actions cache | the old refresher lived outside the repo and pushed to a branch that no longer exists | history needs to outlive cache eviction → move `history/` to object storage (R2) |
| D4 | "AI search" = local question parser + semantic ranking with a small open embedding model, vectors built at refresh time, query embedded in the browser | zero cost, no server, query stays private; the parser keeps filters exact | an LLM answer layer (summaries, Q&A over evidence) is wanted: Workers AI behind a Pages Function, with a spend cap |
| D5 | Keep `web/index.html` one static file, no build | contributor rule; nothing in the UI needs a bundler yet | a second page type (investigation explorer) goes live |
| D6 | DSH assistant (#4 → #10) and read model (#7) stay in scope but behind P1–P4 | both need owner credentials, spend caps and two independent reviews that are not available today | owner supplies the prerequisites |

## Next deliveries

| Step | Delivery | Builds on | Status |
|---|---|---|---|
| P1 | Console UI: charts, filters, smart + semantic search, detail drawer | layer 0 | this change |
| P2 | Hosting + daily self-update + CI gate | P1 | this change; needs Cloudflare secrets |
| P3 | Richer search corpus: embed abstracts (the pipeline stores titles only today) and README excerpts; optional LLM answer card over the top results via Workers AI with a hard daily cap | P2 | planned |
| P4 | Durable history: copy `history/` to R2 after each run so momentum survives cache eviction; publish daily `data.json` to R2 and commit only weekly snapshots to git to cap repository growth | P2 | planned |
| P5 | Trend-over-time charts per item (needs ≥ 14 daily snapshots from P2/P4) | P4 | planned |
| P6 | Link the frontier-economics investigation explorer (`web/prototypes/`, #8's chosen direction) from the console | #6, #8 | planned |
| P7 | Continue #7 → #9 → #12 (read model, relationship lens/inspector, first published investigation) | owner prerequisites | blocked |
| P8 | #4 → #10 assistant, #13–#21 per milestone order | P7 | blocked / not started |

## How the roadmap issues map onto the steps

- **#14 (automated adapters with health)**: P2 gives a scheduled run with per-source status on the page; the remaining criteria (quota back-off, preserved last-good evidence, budget) stay open.
- **#21 (CI gates)**: P2 adds a real CI pipeline; its acceptance (broken-provenance and network-replay failures caught, deployed behavior verified) stays open.
- **#13 (offline replay)**: `run.py --rescore` exists; CI runs fixtures only. Not accepted.
- None of these are marked accepted by this change.
