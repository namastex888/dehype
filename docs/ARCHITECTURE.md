# Architecture

Plain map of what exists, what runs where, and how the roadmap attaches to it. Updated 2026-10-16.

Legend used below: `[LIVE]` runs today · `[NEW]` added by the console/hosting change · `[PLANNED]` designed, not built · `[BLOCKED]` waiting on an owner decision or credential.

## 1. Data flow, end to end

```
 ┌──────────────────────── PUBLIC SOURCES (free, no paid keys) ─────────────────────────┐
 │  arXiv API · Hugging Face papers · GitHub REST + search · Hacker News (Algolia)       │
 └──────────────────────────────────────────┬───────────────────────────────────────────┘
                                            │  once a day, 06:17 São Paulo
                                            ▼
 ┌──────────────── .github/workflows/refresh.yml  (GitHub Actions, free)  [NEW] ────────┐
 │                                                                                      │
 │   Actions cache ──restore──►  history/trending.db   (our own snapshots: stars,       │
 │   (pipeline state)            cache/                 upvotes, ranks per run)         │
 │                                     │                                                │
 │                                     ▼                                                │
 │   run.py  [LIVE] ── fetch ──► features ──► scoring.py (pure functions, method v3.0,  │
 │                                            weights in scoring_config.json)           │
 │                                     │                                                │
 │                                     ▼                                                │
 │                     web/data.json   papers + repos, 7 windows × 7 paradigms          │
 │                                     │                                                │
 │   scripts/embed/embed.mjs ──► web/search-index.json + search-vectors.bin             │
 │      (one 384-d vector per paper/repo/project, MiniLM-L6 q8, pinned HF commit)       │
 │   gate: unit tests + scripts/check_page.mjs ──► commit "data: daily refresh" to dev  │
 │   state ──save──► Actions cache (+ 30-day artifact backup of history/)               │
 └─────────────────────────────────────┬────────────────────────────────────────────────┘
                                       │ calls deploy.yml (pushes made by the job token
                                       │ do not trigger workflows, so refresh calls it)
                                       ▼
 ┌──────────────── .github/workflows/deploy.yml  [NEW] ───────────────────────────────────┐
 │   cp METHODOLOGY.md web/ → check_page → job 1: GitHub Pages (always)                   │
 │                                        job 2: Cloudflare Pages (when 2 secrets exist)  │
 └─────────────────────────────────────┬────────────────────────────────────────────────┘
                                       ▼
 ┌──── GitHub Pages [LIVE] namastex888.github.io/trending-research · Cloudflare [needs account] ┐
 │   index.html · data.json (3.9 MB) · hype.json · search index · METHODOLOGY.md · og.png     │
 └─────────────────────────────────────┬──────────────────────────────────────────────────────┘
                                       ▼
 ┌──────────────── Browser: web/index.html  (one static file, no build)  [NEW] ─────────┐
 │  search ─► 1. parser: tab, window, paradigm, "stars > 1k", "from meta", "new",       │
 │               "rising", "attention ahead" become filters                             │
 │           2. leftover words ─► semantic: same embedding model runs in the browser    │
 │               (transformers.js, same pinned weights, ~28 MB once), dot product,      │
 │               keeps the closest items; keyword fallback if the model cannot load    │
 │           ─► KPI tiles · paradigm mix · scatter · leaders · table                    │
 │  (no server, no paid API, the query never leaves the browser)                        │
 │  row click ─► detail drawer (score anatomy, flags, sources, HYPE research card)      │
 │  Method tab renders METHODOLOGY.md, the single source for every formula              │
 └──────────────────────────────────────────────────────────────────────────────────────┘

 Off the automatic path (manual, private input):
   hype/hype_research.json (social research dossier, not committed: raw post excerpts)
        └─► hype_build.py ─► web/hype.json      refreshed only when a research pass runs
```

What each piece guarantees:

| Piece | Guarantee | Where it is enforced |
|---|---|---|
| `run.py` | every value comes from a named public source; failure is recorded per source, never filled in | `note()` → `data.json.sources`, shown in the header's source-health popover |
| `scoring.py` | unknown stays `null`; coverage is completeness, not confidence; thin evidence shrinks toward the prior | unit tests, `eval.py`, METHODOLOGY.md |
| `check_page.mjs` | the page script parses; the top-level data fields and per-row item references it relies on exist; the search vectors match the index (stale index = warning) | `ci.yml`, `refresh.yml`, `deploy.yml` |
| `index.html` | `—` for unknown, gap labels only when both coverages ≥ 50%, sampled counts called samples, star-growth source and span shown per row | carried over from the previous page and checked by an independent review |

## 2. How it updates itself

```
 06:17 BRT daily ─► refresh.yml ─► run.py (~20–40 min) ─► data.json ─► commit to dev ─► deploy.yml ─► Pages
 any push to dev touching web/** or METHODOLOGY.md ─────────────────────────────────► deploy.yml ─► Pages
 any PR ─► ci.yml (tests, fixture eval, scoring smoke, page check)   — never deploys, never fetches
```

Momentum needs earlier snapshots. They live in `history/trending.db`, which is kept between runs in the Actions cache. The first automated run starts a new history: every entry shows as new, and snapshot-based star growth needs a second daily run (repositories created inside the window and GitHub stargazer timestamps can still give values on day one); 7-day momentum becomes snapshot-measured after a week. If the cache is ever evicted (7 days without a run), the same reset happens and the page says so. Nothing is back-filled or invented.

GitHub limits: with only the job token the GitHub API allows about 1,000 requests per hour, so some activity lookups may be partial (recorded as `partial` in sources). Adding a read-only fine-grained token as the `TRENDING_GH_TOKEN` secret raises that to 5,000.

**Repository size.** Each refresh commits a ~4 MB `data.json` (plus a 0.7 MB vector file). Git stores them compressed, but history still grows by roughly 0.5–1 MB a day. ROADMAP step P4 moves daily snapshots to object storage (R2) and keeps only weekly snapshots in git.

**Retire the old refresher.** Until 2026-10-16 the daily data commits came from a job outside this repository that pushes to `main`. The default branch is now `dev`, and git does not redirect pushes to a renamed branch, so that job would create a new `main` that nothing deploys. Disable it; `refresh.yml` replaces it.

## 3. Publishing

Decision: **GitHub Pages now, Cloudflare Pages as primary once its secrets exist**, both deployed by the same `deploy.yml`. GitHub Pages needs no extra account, so the site is public today; Cloudflare adds a custom domain, no commercial clause and Workers AI. Launch plan and talking points: [PUBLISHING.md](PUBLISHING.md).

| | Cloudflare Pages (free) | Vercel Hobby |
|---|---|---|
| Static bandwidth | static asset requests free and unlimited | 100 GB fast data transfer / month cap |
| Use terms | no non-commercial clause | personal, non-commercial use only |
| File limit | 25 MiB per asset, 20,000 files | fine for this site |
| Builds | 500 deploys / month (we use ~31) | — |
| Next step it unlocks | Workers AI + Pages Functions for semantic search on the same account | Vercel functions |

The project may later carry sponsorship or a commercial owner, and a data site is read by crawlers and newsletters in bursts; Cloudflare has no commercial clause and no static bandwidth meter. Sources: [Pages limits](https://developers.cloudflare.com/pages/platform/limits/), [Pages Functions pricing](https://developers.cloudflare.com/pages/functions/pricing/), [Vercel fair use](https://vercel.com/docs/limits/fair-use-guidelines), [Vercel Hobby](https://vercel.com/docs/plans/hobby).

One-time setup (owner):

1. Cloudflare dashboard → My Profile → API Tokens → create a token with **Account · Cloudflare Pages · Edit**.
2. GitHub → Settings → Secrets and variables → Actions: add `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`. Optional: variable `CF_PAGES_PROJECT` (default `trend-observatory`), secret `TRENDING_GH_TOKEN`.
3. Actions → deploy → Run workflow. The first run creates the Pages project with production branch `dev`; the site is then at `https://trend-observatory.pages.dev` (or your custom domain).

Zero-secret alternative: Cloudflare dashboard → Workers & Pages → Create → Pages → connect this GitHub repository, production branch `dev`, build command empty, output directory `web`. Leave the two secrets unset: `deploy.yml` then skips itself, and Cloudflare deploys on every push to `dev`, including the refresh commit.

## 4. The roadmap on top of this

The tracker above is layer 0. The observatory roadmap ([WISH](../.genie/wishes/open-intelligence-observatory/WISH.md), issues #2–#21) builds an evidence system on top of it:

```
 LAYER                        WHAT IT ADDS                                   ISSUES              STATE
 ───────────────────────────────────────────────────────────────────────────────────────────────────────
 5  community & governance    sourced corrections, branching, gap → issue    #17 #18 #20         not started
 4  release & regression      editorial publish, change review, CI gates     #12 #16 #21         CI started here
 3  reader surfaces           visual direction, relationship lens/timeline/  #8 #9 #10           #8 accepted;
                              inspector, assistant on the investigation                          #9 #10 blocked
 2  evidence store            Brain persistence, source revisions,           #5 #7               #5 accepted;
                              investigation read model                                           #7 blocked
 1  sources & semantics       claim/evidence contracts, economics panel,     #2 #3 #11 #13 #14   #2 #3 #11
                              scoring semantics, replay, adapters, stance,   #15 #19             accepted
                              new lenses
 0  public tracker            papers / repos / hype ranking + console        —                   LIVE, this change
 ───────────────────────────────────────────────────────────────────────────────────────────────────────
 Milestones: M0 contracts (#2–#5) · M1 first public investigation (#6–#12) · M2 reliable collection
             (#13–#16, #21) · M3 community (#17, #18) · M4 broader lenses + roadmap automation (#19, #20)
```

How the pieces relate:

```
   sources ──► evidence contracts (#2) ──► Brain store (#5) ──► read model (#7) ──► lens / inspector (#9)
      │                                                             │                      │
      └─► scoring semantics (#11) ──► tracker scores (layer 0)      └─► assistant (#4 → #10, DeepSeek
                                                                         Harness, cites the same IDs)
   flagship investigation: frontier-AI economics (#6) ──► visual direction chosen (#8) ──► publish (#12)
```

- **Brain** is the evidence database (claims, spans, source revisions). **DSH** (DeepSeek Harness) is the planned assistant runtime that answers with citations into the same evidence IDs. **Cordis** is DSH's plugin framework. The investigation explorer prototypes live in `web/prototypes/` and are not linked from the main page yet.
- #4 and #7 are blocked on owner-level prerequisites (credentials, spend caps, two independent reviews); see the 2026-10-16 checkpoint under `.genie/wishes/open-intelligence-observatory/checkpoints/`.

Current sequencing is in [ROADMAP.md](ROADMAP.md).
