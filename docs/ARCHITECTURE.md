# Architecture

Plain map of what exists, what runs where, and how the roadmap attaches to it. Updated 2026-10-17 for dehype S1 (wish [dehype-s1](../.genie/wishes/dehype-s1/WISH.md)): several static pages, GitHub Pages only, the ledger on Pages and the inputs on dated Releases, no Cloudflare and no object storage.

Legend used below: `[LIVE]` runs today · `[S1]` added by dehype S1 · `[PENDING]` written, waiting on the owner's approval of a workflow change · `[PLANNED]` designed, not built.

## 1. Data flow, end to end

```
 ┌──────────────────────── PUBLIC SOURCES (free, no paid keys) ─────────────────────────┐
 │  arXiv · Hugging Face papers · GitHub · Hacker News · Reddit (arctic-shift, counts)  │
 │  Mastodon · Lobsters · newsletters and official feeds (RSS) · [Bluesky*]             │
 └──────────────────────────────────────────┬───────────────────────────────────────────┘
                                            │  once a day, 04:45 São Paulo [PENDING]
                                            ▼  (06:17 until the workflow change lands)
 ┌──────────────── .github/workflows/refresh.yml  (GitHub Actions, free) ───────────────┐
 │   Actions cache ──restore──►  history/ (trending.db, signals.sqlite)  cache/         │
 │   run.py ──► scoring.py ──► web/data.json            (papers + repos)        [LIVE]  │
 │   pulse.py ──► web/pulse.json, web/briefing.json, web/story-aliases.json             │
 │      (deleted-post recheck, removals.json applied; Reddit, X, LinkedIn, YouTube,     │
 │       Telegram as counts only; no person handle)                              [S1]   │
 │   check_mastodon_links.mjs ──► web/checks/mastodon-links.json (render check)  [S1]   │
 │   hype_build.py --scrub ──► web/hype.json (deletion only)                     [S1]   │
 │   compose.mjs (Cordis 4.0.4) ──► web/feed{,.pt}.{xml,json}                    [S1]   │
 │   embed.mjs ──► web/search-index.json + search-vectors.bin (MiniLM-L6 q8)     [LIVE] │
 │   manifest.py + ots.mjs ──► web/ledger/ (index, day files, story-id archive,         │
 │      OpenTimestamps proofs); manifest ──► dated Release ledger-YYYY-MM-DD  [PENDING] │
 │   gate: unit tests + scripts/check_page.mjs                                          │
 │   commit (no secret; only the bot-written files) ──► push to dev (token, git only)   │
 └─────────────────────────────────────┬────────────────────────────────────────────────┘
                                       │ calls deploy.yml (pushes made by the job token
                                       │ do not trigger workflows, so refresh calls it)
                                       ▼          attest job: Sigstore attestation of
 ┌──────────── .github/workflows/deploy.yml ───────┐  the manifest (id-token only) [PENDING]
 │  owner-file check → copy both METHODOLOGY files │
 │  → check_page → GitHub Pages (the only host)    │
 └─────────────────────────────────────┬───────────┘
                                       ▼
 ┌──── GitHub Pages [LIVE] namastex888.github.io/dehype ────────────────────────────────┐
 │  index.html (briefing) · stories · output · hype · method · audit (en and pt)        │
 │  dehype.css · dehype.js · i18n/ tables · data files · feeds · ledger/                │
 └─────────────────────────────────────┬────────────────────────────────────────────────┘
                                       ▼
 ┌──────────────── Browser: static pages, no build, no server ──────────────────────────┐
 │  briefing: at most four gauges (previews, with coverage) and the Top 10 stories      │
 │  search by meaning, only after a click: transformers.js 4.2.0 (exact pin) and its    │
 │     onnxruntime wasm from jsDelivr, the model (23.7 MB) from Hugging Face at the     │
 │     index's revision; the query never leaves the browser; word match as fallback    │
 │  "stale since": a briefing older than 06:00 São Paulo of the next day says so        │
 └──────────────────────────────────────────────────────────────────────────────────────┘

 Off the automatic path (manual, private input):
   hype/hype_research.json (social research dossier, not committed: raw post excerpts)
        └─► hype_build.py ─► web/hype.json      refreshed only when a research pass runs
```

What each piece guarantees:

| Piece | Guarantee | Where it is enforced |
|---|---|---|
| `run.py` | every value comes from a named public source; failure is recorded per source, never filled in | `note()` → `data.json.sources` |
| `scoring.py` | unknown stays `null`; coverage is completeness, not confidence; thin evidence shrinks toward the prior | unit tests, `eval.py`, METHODOLOGY.md |
| `pulse.py` | no person handle; counts-only networks; evidence records `state: proposed`, no label word; Top 10 recomputable | unit tests, `check_page.mjs` |
| `check_page.mjs` | the pages and data keep the public-data rules; both method sources carry the licence; the one imported script is the exact-pinned transformers.js; the refresh stages exactly the bot-written files and never an owner-reviewed one | `ci.yml`, `refresh.yml`, `deploy.yml` |
| `check_owner_files.py` | `verdicts.json`, `corrections.json` and `removals.json` change only by a person's merged PR; corrections are appended, never edited | `ci.yml`, `refresh.yml`, `deploy.yml` |

\* Bluesky needs an app password secret (`BSKY_HANDLE`, `BSKY_APP_PASSWORD`). The official Reddit API is optional (`REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`); without it Reddit comes from the arctic-shift public archive. X is not collected: there is no free route that stays within X's terms.

## 2. How it updates itself

```
 04:45 BRT daily ─► refresh.yml (~20–40 min) ─► commit + push to dev ─► deploy.yml ─► Pages by 06:00
 any push to dev touching web/**, METHODOLOGY.md or METHODOLOGY.pt.md ───────────► deploy.yml ─► Pages
 any PR ─► ci.yml (tests, fixture eval, scoring smoke, owner files, page check) — never deploys, never fetches
```

The schedule is `45 7 * * *` (São Paulo is UTC-3 all year), re-fitted after 7-10 scheduled runs from their Pages deploy times; until the pending workflow change (`.genie/wishes/dehype-s1/f-workflow.proposed.diff`, applied after `e-workflow.combined.proposed.diff`) lands, the cron is still `17 9 * * *` (06:17 BRT), so each morning's briefing reads "stale since" until the run finishes.

The refresh's push is split in two (C42, pending): the data commit is made, replayed onto `dev` over the public URL and checked in a step that holds no secret, and `PUSH_TOKEN` is only in the next step, which runs git (with hooks, credential helpers and fsmonitor turned off) and no npm, node or Python code. That keeps the push token out of the steps that run dependency code; it does not isolate the job token. `github.token` is still the fallback `GH_TOKEN` of "Fetch and score" (`run.py`) when `TRENDING_GH_TOKEN` is unset, and the `gh release` steps hold it too. An earlier step that ran third-party code can also write `$GITHUB_ENV` or `$GITHUB_PATH`, or a `.git/config` entry (an `include.path`, or a `url.<base>.insteadOf` that redirects the push), which the push step inherits; the `-c` overrides cover only the keys they name. The full fix, future work, is a separate push job on a fresh runner that receives the data commit as a git bundle artifact and holds the only write token.

Momentum needs earlier snapshots. They live in `history/trending.db`, which is kept between runs in the Actions cache. If the cache is ever evicted (7 days without a run), history starts again and the page says so. Nothing is back-filled or invented.

GitHub limits: with only the job token the GitHub API allows about 1,000 requests per hour, so some activity lookups may be partial (recorded as `partial` in sources). Adding a read-only fine-grained token as the `TRENDING_GH_TOKEN` secret raises that to 5,000.

**Repository size.** Each refresh commits a ~4 MB `data.json` (plus a 0.7 MB vector file and the smaller briefing, Pulse, feed and ledger files). Git stores them compressed, but history still grows by roughly 0.5–1 MB a day. The durable record is the ledger on Pages plus each day's input manifest on a dated GitHub Release (ROADMAP P4); there is no object storage. Vendoring the search code (transformers.js and its onnxruntime wasm, 13.9 MB on the site, about 4.2 MB in git) is deferred: GitHub push protection flags a pattern in the minified bundle; needs an owner decision.

**Protect `dev` (owner setting).** The deploy refuses a push in which a bot commit touches an owner-reviewed file or a corrections entry is edited or removed, but the refresh's own deploy (a `workflow_call`, with no `before` commit) checks only the bot's data commit. A direct push the deploy refused would therefore be published by the next refresh. A branch ruleset on `dev` that requires a pull request and the `ci` check for people, with the refresh's bot push as the only bypass, closes that path.

**Retire the old refresher.** Until 2026-10-16 the daily data commits came from a job outside this repository that pushes to `main`. The default branch is now `dev`, so that job would create a new `main` that nothing deploys. Disable it; `refresh.yml` replaces it.

## 3. Publishing

Decision (ROADMAP D2): **GitHub Pages only**, deployed by the one job in `deploy.yml`. It needs no account beyond GitHub and no secret; the Cloudflare job and its secrets are gone. The site is `https://namastex888.github.io/dehype/`. Feeds: `feed.xml`, `feed.json`, `feed.pt.xml`, `feed.pt.json` at the site root.

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
 0  public surface            dehype briefing + papers / repos / hype         —                   LIVE (S1)
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
