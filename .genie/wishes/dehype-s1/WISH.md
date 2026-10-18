# Wish: dehype S1, the daily AI reality briefing

| Field | Value |
|-------|-------|
| **Status** | APPROVED |
| **Slug** | `dehype-s1` |
| **Date** | 2026-10-17 |
| **Author** | Planning agent for the owner (namastex888); implementation delegated |
| **Appetite** | large, twelve sequential execution groups (design groups A-F, split to fit the admission band) |
| **Branch** | `wish/dehype-s1` |
| **Repos touched** | `namastex888/trending-research` |
| **Design** | [DESIGN.md](../../brainstorms/open-ai-reality-media/DESIGN.md) |

## Summary

Deliver S1 of the reviewed design (verdict SHIP, preflight passed 2026-10-17): turn the five-tab console into dehype, a daily briefing that says what happened in the last 24h, what each story's evidence is and who has confirmed what, in English and Portuguese, on a record anyone can verify. The design's six groups A-F are delivered in dependency order as twelve groups (A1, A2, B1, B2, B3, C1, C2, C3, D, E1, E2, F) so that each fits the admission band; group A1 lands first and is useful alone. S1 succeeds only when the owner has used it daily for 14 days, evidenced from the record (design Decision 8).

## Scope

### IN

The design's Scope IN rows 1-22 (DESIGN.md lines 24-47), each assigned to exactly one plan group except where a row is split and the split is named:

- Rows 1, 2, 4, 5 (design group A: handles, Reddit counts, X/LinkedIn/YouTube/Telegram counts, X figures in prose) -> **Group A1**.
- Row 3 (design group A: Mastodon render check) -> **Group A2**; until A2 lands, every Mastodon post shows as a count (the fail-closed form of row 3).
- Rows 6, 8 and the data half of row 9 (design group B: evidence records, Top 10, gauge values) -> **Group B1**.
- Row 7, first half (verdict file, story-id resolution and alias file, corrections log, right of reply and corrections policy) -> **Group B2**.
- Row 7, second half (removal requests, deleted-post recheck by id, dossier-gone list, `hype_build.py --scrub` removals) -> **Group B3**.
- Rows 12 and 14 (design group C: two-language strings, `lang` tags, method sources and X-route disclosure) -> **Group C1**.
- Row 10 (shell, all-stories, output and Hype pages), the Hype-page wordings of row 11, and row 13 (Portuguese dossier file) -> **Group C2**.
- Row 10 (briefing first screen, method and audit pages), the display half of row 9 (gauge header in `web/index.html`), and the fold of row 11 -> **Group C3**.
- Rows 15 and 16 (design group D: feeds and the one-shot Cordis composition) -> **Group D**.
- Row 17, the Sigstore half of row 18, and the "stale since" half of row 18 (design group E) -> **Group E1**.
- The OpenTimestamps half of row 18 -> **Group E2**.
- Rows 19, 20, 21 and 22 (design group F: staging set, ready time, records, licence) -> **Group F**.

### OUT

- Everything in the design's Scope OUT (DESIGN.md lines 51-68), unchanged: S2 verdict policy beyond the S1 rows, S3 risk and jobs sources, S4 awareness map, S6 channels, G1 governance, trend lines and "shipped" gauges before 14 ledger days, the S5 recompute verifier, a combined State of AI score, pipeline-proposed labels and any model or paid route for them, PUSHED from coordination signals, translated headlines, WISH #4 acceptance and DSH/Brain/tenant work, the Mission control look on the observatory explorer, Reddit and X/LinkedIn/YouTube/Telegram text, links or figures, rewriting public git history, putting the dossier into the daily refresh, and paid chains, storage, analytics or any server.
- Editing `.genie/brainstorms/open-ai-reality-media/DESIGN.md` (its review stamp covers its bytes).
- The roadmap entries' content for S2-S6 and G1 beyond what row 21 records; each is its own later wish.
- Committing the brainstorm directory inside an execution group: it is 3,365 lines (DRAFT.md 3,178), over the band on its own, so it is committed with this WISH.md in the planning commit, and Group F only verifies it is on `origin/dev` (row 21).

## Decisions

Plan-level choices made where the design does not fix the answer (each is also listed for the operator in the planning report):

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Design groups A, B, C and E are split (A1/A2, B1/B2/B3, C1/C2/C3, E1/E2); D and F stay whole | Estimated sizes: A about 24 files (fixtures included) sits at the 25-file hard maximum with no margin; B's row 7 alone lists 16 files plus about 12 fixtures (over 25); C's five new pages, CSS, JS, an index rewrite and a translated `METHODOLOGY.pt.md` (about 430 lines, plus its `web/` copy) exceed 2,000 insertions; E's `opentimestamps` 0.4.9 lockfile measures 875 lines on its own (scratchpad `npm install --package-lock-only`, 88 packages), which with the manifest, attestation job, audit page and stale-since logic approaches the 2,000-insertion maximum |
| 2 | Every group runs sequentially; each group's `depends-on` names the group before it as well as its real producer | `scripts/check_page.mjs`, `pulse.py`, `web/i18n/strings.json`, `.github/workflows/refresh.yml` and `ci.yml` are shared by most groups, so no two groups have disjoint file ownership |
| 3 | A1 shows every Mastodon post as a count; A2 adds the render check and the link | Fail-closed is the design's own fallback (row 3, Risk 8), so A1 is complete and buildable alone without a browser dependency |
| 4 | The display half of row 9 (`web/index.html` gauge header) moves from design group B to Group C3 | C3 rewrites `web/index.html` as the briefing first screen; rendering the header in the old console first would be thrown away and would make B and C co-own one file |
| 5 | Within design group C, languages (C1) land before pages (C2, C3), and the console is flipped to dehype in one group (C3) | The pages read `web/i18n/strings.json`, so it must exist first; building the new pages beside the console (C2) and folding every console URL and anchor at once (C3) avoids an interim build in which today's anchors break |
| 6 | Row 13 lands whole in C2 with the Hype page; the Hype-page wordings of row 11 land in C2, the fold check of row 11 in C3 | Row 13's checks need the page that renders the notice |
| 7 | Each group that creates a bot-written output adds it to `refresh.yml`'s `git add` line in the same group (A2 `web/checks/mastodon-links.json`; B1 `web/briefing.json`; B2 `web/story-aliases.json`; B3 `web/checks/dossier-gone.json` and `web/hype.json`; D the four feeds; E1 the ledger and story-id archive; E2 `web/ledger/ots/`); Group F (row 19) fixes the final set and adds its CI check | Row 7 already requires the refresh to stage the scrubbed `web/hype.json` before row 21's inherited fix would; a bot-written cache that is not committed is not a cache; B1 stages `web/briefing.json` so the C3 first screen never reads a frozen briefing between C3 and D |
| 8 | C1 edits only the GitHub Pages job's sync step in `deploy.yml`; Group F drops the Cloudflare job (row 21) | Keeps the design's row assignment; row 12 names "the one sync step left once row 21 drops the Cloudflare job". Until F, the Cloudflare mirror (dropped by the owner) lacks `METHODOLOGY.pt.md` |
| 9 | The frontend plugin's per-language output paths are fixed by Group D, and D points `web/dehype.js` at them; C2 and C3 read `web/i18n/strings.json`, `web/briefing.json`, `web/pulse.json`, `web/hype.json` and `web/data.json` directly | The Approach says "a frontend plugin writes the per-language data and string tables" and the pages read them, but no row names those files, and the pages (C) land before the plugin (D) |
| 10 | The two-language X-figure placeholder strings (row 5) are defined by A1 next to its list in `web/i18n/dossier-x-figures.json`; C1 references them from `web/i18n/strings.json` | Row 5 needs a "fixed two-language placeholder" before `strings.json` (row 12, C1) exists |
| 11 | The Decision 13 measurement is taken in A1 and recorded in this WISH.md under Group A1; C1 writes the same figure into `METHODOLOGY.md` and `METHODOLOGY.pt.md` | The measurement deadline (before about 2026-11-06, artifact expiry 2026-11-15 19:14 UTC) falls before C1 can be reached; the Portuguese method source is created in C1 |
| 12 | The "shared" Mastodon `/api/v1/statuses/<id>` lookup (rows 3 and 7) is shared as one endpoint and one recorded result: A2's check records the HTTP status per id in `web/checks/mastodon-links.json`, and B3's recheck counts a 404 there, or from its own call to the same endpoint, as removed | A2's check is Node (`scripts/check_mastodon_links.mjs`) and B3's recheck is in `pulse.py` (Python); the design does not say which side calls the other |
| 13 | B2 fixes the JSON shape of `web/ledger/ids/YYYY-MM-DD.json` (read side, with a fixture); E1 writes files in that shape | The verdict check (row 7, B2) reads the archive before the writer (row 17, E1) exists |
| 14 | Negative fixtures run inside the unittest suite. Each negative fixture is an overlay: the test copies the committed `web/` tree to a temporary directory, writes only the fixture's files over it, runs `node scripts/check_page.mjs <temp dir>`, and asserts exit 1 and the specific finding message for that rule in the output, never exit 1 alone; a positive fixture asserts exit 0 on its overlay | The design names the fixtures but not how they are run; `check_page.mjs` hard-reads `index.html`, `data.json`, `hype.json`, `search-index.json`, `search-vectors.bin` and `pulse.json` (lines 11-65 at 2bc0ace), so a fixture directory without them would fail for the wrong reason |
| 15 | The `dehype.js` six-case stale-since test runs as `node --test tests/dehype_stale.test.mjs` (file name chosen by this plan) and E1 adds that command to `ci.yml`'s test job | The design names "a `dehype.js` fixture test with six cases" but no file or runner |
| 16 | `scripts/dehype/compose.mjs` runs with no arguments from the repository root, reads `web/` and writes its outputs into `web/` | The design fixes the step ("one Node step after `pulse.py`") but not its command line; validation needs a fixed command |
| 17 | `LICENSE` carries the AGPL-3.0 text; the CC BY-SA 4.0 data statement (its scope and the earlier MIT and CC BY 4.0 releases) lives in `README.md`, `CITATION.cff` and the two `METHODOLOGY` files; no separate data-licence file is added | Row 22 lists only `LICENSE`, `README.md`, `CITATION.cff`, `METHODOLOGY.md`, `METHODOLOGY.pt.md` |
| 18 | The brainstorm directory is committed with this WISH.md in the planning commit, not by Group F | It is 3,365 lines; Group F verifies it is on `origin/dev` (row 21) |
| 19 | Admission counts hand-written lines only: regenerated data files (`web/pulse.json`, `web/briefing.json`, `web/hype.json`, `web/data.json`, `web/story-aliases.json`, `web/feed*.xml`, `web/ledger/**`, `web/checks/*.json`, `web/search-index.json`, `web/search-vectors.bin`) and npm lockfiles (`scripts/checks/package-lock.json`, `scripts/dehype/package-lock.json`) are excluded from the 2,000-insertion count and listed separately in each group's PR with their line counts; they still count toward the 25-file maximum. Hand-written, owner-reviewed files (`web/verdicts.json`, `web/removals.json`, `web/corrections.json` and the other staging-set files) always count. Generated `web/*.json` files stay compact on one line, as `web/pulse.json` and `web/hype.json` are at 2bc0ace (0 newlines) | The design says nothing on how admission counts generated files; machine output and lockfiles are not reviewable insertions, and the measured lockfiles (875, 53 and 28 lines) would otherwise dominate E2 and A2 |
| 20 | Data rebuild rule: a group that changes `pulse.py` restores the latest successful refresh's `history-<run_id>` artifact (uploaded by `refresh.yml`'s "Back up history" step) into `history/` inside its worktree (gitignored, never committed), runs `python3 pulse.py --offline`, and commits the regenerated `web/pulse.json` (and, from B1 on, `web/briefing.json`). The command is the rebuild block in each such group's Validation (A1, A2, B1, B2, B3, C1) | `ci.yml` runs `check_page.mjs` on the committed `web/`; `pulse.py` reads the gitignored `history/signals.sqlite`, and `--scrub` covers only `web/hype.json`. At 2bc0ace the committed `pulse.json` holds 1,791 `"author"`, 1,023 `reddit.com` and 255 `/@` matches (review finding), so a rule change in `pulse.py` that is not followed by a rebuild leaves CI failing on stale data. Under `--offline` the B3 recheck makes no calls, so every recheckable post shows as a count (fail-closed) |
| 21 | Discord is counts only alongside Reddit, X, LinkedIn, YouTube and Telegram (A1, `COUNT_ONLY` in `pulse.py` and `scripts/check_page.mjs`) | Stricter than the design, which names Discord only in C28's poster list; the dossier holds no Discord post today, so this binds nothing yet and fails closed if a research pass adds one |

## Simplicity Case

- **Simplest complete design:** the design's own (DESIGN.md line 86): extend the existing pipeline and page guard, add one composition step and static pages, and keep every record in git, Pages or a dated Release. No new service, database or account. The plan adds no mechanism beyond the design's rows; it only splits rows across groups.
- **Added machinery:** exactly the design's list (DESIGN.md lines 87-95): the Cordis step; the Mastodon render check and its cache; the X-figure detector and disposition lists; the SHA256-keyed Portuguese dossier file; manifest, attestation and timestamp; the alias file and story-id archive; `removals.json`; the deleted-post recheck by id; the OpenTimestamps upgrade loop; the corrections base-commit comparison; `hype_build.py --scrub`; `web/checks/dossier-gone.json`; the separate attestation job. The plan adds one test runner invocation (`node --test`, Decision 15) because the design requires a JavaScript fixture test.
- **Deferred until measured:** re-fitting the cron after 7-10 scheduled runs; language detection for `lang` (source metadata or `und` unless untagged headlines prove common); automated dossier refresh until the research pass has a committed input (DESIGN.md line 96).
- **Complexity removed:** no server, login, analytics or tenant model; no translation model; no pipeline label proposals; no trend maths before 14 days; no hashed-handle scheme; no Reddit pointers in an anchored file (DESIGN.md line 97). No parallel writers, so no merge coordination between groups.

## Dependencies

**depends-on:** none
**blocks:** none

## Success Criteria

The design's 26 Success Criteria (DESIGN.md lines 149-174) are numbered SC-1 to SC-26 in order. Each is copied verbatim into the group that proves it; a criterion proved across several groups is copied into each with a scope note.

- [ ] SC-1 no person handle in a public file (DESIGN.md line 149): A1 for `pulse.json`, `hype.json` and the leak fixtures; C2/C3 on the pages; D on the feeds.
- [ ] SC-2 committed `web/hype.json` clean without a research pass, and the Decision 13 measurement (line 150): A1 (scrub, tests, measurement), C1 (figure on the method page).
- [ ] SC-3 Reddit counts only (line 151): A1; pages C2/C3; feeds D.
- [ ] SC-4 manifest holds no Reddit field but the hash (line 152): E1.
- [ ] SC-5 Mastodon link only with a passing check (line 153): A2; manifest URL part E1.
- [ ] SC-6 no X, LinkedIn, YouTube or Telegram post URL or content (line 154): A1; pages C2/C3; feeds D.
- [ ] SC-7 X-figure detector hits listed (line 155): A1.
- [ ] SC-8 every string has `en` and `pt`, headlines carry `lang` (line 156): C1.
- [ ] SC-9 `dossier.pt.json` form and fallback (line 157): C2.
- [ ] SC-10 evidence records `state: proposed`, "not fetched" (line 158): B1; feed part D.
- [ ] SC-11 verdict rows resolve and carry their fields (line 159): B2.
- [ ] SC-12 corrections appended, never edited (line 160): B2.
- [ ] SC-13 removal requests and deleted posts leave every output (line 161): B3; feed part D; Hype page part C2.
- [ ] SC-14 Top 10 ids and order equal a recompute (line 162): B1.
- [ ] SC-15 gauge header at most four gauges, previews, no trend before 14 days (line 163): B1 (data), C3 (display).
- [ ] SC-16 feeds validate as RSS 2.0 and JSON Feed 1.1 in both languages (line 164): D.
- [ ] SC-17 Cordis step exactly 4.0.4, MIT notice, no server (line 165): D.
- [ ] SC-18 ledger hash equals Release asset, attestation, OpenTimestamps proof (line 166): E1 (ledger, Release, attestation), E2 (proof, upgrade, anchored).
- [ ] SC-19 "stale since" on failure and in the browser (line 167): E1.
- [ ] SC-20 every console URL and anchor resolves (line 168): C3 (Hype wordings C2).
- [ ] SC-21 X-route disclosure and licence text on the method page (line 169): C1 (disclosure), F (licence text).
- [ ] SC-22 staging set (line 170): F.
- [ ] SC-23 live on Pages by 06:00 America/Sao_Paulo (line 171): F, evidence collected during the clock (QA).
- [ ] SC-24 `docs/ROADMAP.md` records (line 172): F.
- [ ] SC-25 no gauge reads "shipped" (line 173): B1.
- [ ] SC-26 S1 as a whole (line 174), verbatim: S1 as a whole succeeds: 14 dated Daily briefings published on Pages from the first scheduled run whose deploy passes S1's per-deploy checks, the owner's verdict confirms and overrides in git across those days, and the owner's final confirm. The per-deploy checks that start the clock are the ones a single run proves: `python -m unittest discover tests`, `node scripts/check_page.mjs` on the built site, `tests.test_feed` on the four feeds, the manifest check in `scripts/manifest.py`, `gh attestation verify` on the day's manifest, and a ledger hash equal to the Release asset's (a proof reading "pending" passes). The 06:00 deploy times, the anchored-on-N+1 proof and the merged `docs/ROADMAP.md` diff are evidence collected during the clock, not conditions for starting it. **Proof:** the 14 entries in `web/ledger/index.json`, the first of them from a run whose log shows each per-deploy check passing, `git log -- web/verdicts.json` over those dates, and the owner's confirm recorded in the wish.

## Execution Strategy

Every group is sequential (Decision 2). **Trust boundary:** groups A1, A2, B1, B2, B3, C1, D, E1, E2 and F touch `.github/workflows/*` or licence files (`LICENSE`, `CITATION.cff`) and need the plan route (reviewed plan, then `work`), not quick `/wish`. Only C2 and C3 touch no trust-boundary path; if a worker on C2 or C3 finds it must edit a workflow, that group moves to the plan route before the edit.

### Wave 1 (sequential)

| Group | Agent | Complexity | Model | Description |
|-------|-------|------------|-------|-------------|
| A1 | engineer | High: rewrites public data shapes in `pulse.py` and `hype_build.py`, scrubs the committed `web/hype.json`, grows `check_page.mjs` into the public-file gate; time-boxed measurement (before about 2026-11-06) | inherit | Public-data rules: handles, Reddit counts, X/LinkedIn/YouTube/Telegram counts, X figures, `--scrub` (rows 1, 2, 4, 5). TRUST-BOUNDARY: `ci.yml` |
| A2 | engineer | Medium: first browser dependency (`playwright-core` 1.59.1), per-post fail-closed check, time cap in the refresh | inherit | Mastodon render check and handle-free links (row 3). TRUST-BOUNDARY: `refresh.yml`, `ci.yml` |
| B1 | engineer | Medium: new `web/briefing.json` contract every later group reads | inherit | Evidence records, Top 10 cut, gauge values (rows 6, 8, data half of 9); stages `web/briefing.json` in the refresh (Decision 7). TRUST-BOUNDARY: `refresh.yml` |
| B2 | engineer | High: verdict file contract, legal exposure (FALSE, PUSHED), append-only corrections check against the base commit | inherit | Verdicts, aliases, corrections, reply policy (row 7, first half). TRUST-BOUNDARY: `ci.yml`, `refresh.yml` |
| B3 | engineer | High: deletes rows from the history DB, rewrites `web/hype.json` in the refresh, four network lookups under a time cap | inherit | Removals and deleted-post recheck (row 7, second half). TRUST-BOUNDARY: `refresh.yml` |
| C1 | engineer | Medium: Portuguese method source, sync step and path filter | inherit | Two languages, `lang` tags, method sources, X-route disclosure (rows 12, 14). TRUST-BOUNDARY: `deploy.yml` (and `ci.yml` if a step is added) |
| C2 | engineer | Medium: new shell and three pages beside the console; insertion estimate nearest the band | inherit | dehype shell, all stories, output, Hype page, Portuguese dossier file (rows 10, 11 Hype wordings, 13). No trust-boundary path |
| C3 | engineer | Medium: flips `web/index.html` to the briefing and folds every console URL and anchor at once | inherit | Briefing first screen with gauge header, method and audit pages, the fold (rows 9 display, 10, 11). No trust-boundary path |
| D | engineer | High: new pinned dependency tree (`@deepseek-ai/cordis@4.0.4`), licence-closure audit, Node step in the refresh | inherit | Four feeds and the one-shot Cordis composition (rows 15, 16). TRUST-BOUNDARY: `refresh.yml` |
| E1 | engineer | High: new attestation job with `id-token: write`, dated Releases, manifest privacy rules | inherit | Ledger, manifest, story-id archive, Sigstore attestation, stale since (row 17, row 18 parts). TRUST-BOUNDARY: `refresh.yml`, `ci.yml` |
| E2 | engineer | Medium: unmaintained pinned client (`opentimestamps` 0.4.9, 875-line lockfile), upgrade loop that must never edit earlier entries | inherit | OpenTimestamps proof, upgrade and anchored/pending (row 18, proof half). TRUST-BOUNDARY: `refresh.yml` |
| F | engineer | Medium: workflow schedule, staging set, Cloudflare job removal, licence change | inherit | Staging set, ready time, records, licence (rows 19-22). TRUST-BOUNDARY: `refresh.yml`, `deploy.yml`, `ci.yml`, `LICENSE`, `CITATION.cff` |

**Global constraints:**
- No invented numbers; no paid actions without approval; plain ASCII explanations (DRAFT.md line 825, owner's earlier decisions).
- **Numbers are never invented.** Missing data shows as — and reduces evidence coverage when applicable. (`README.md` line 69)
- A7: No paid source, API or chain fee without explicit approval (DRAFT.md line 930).
- Paid chains or storage (EAS gas, IPFS or Arweave fees, Cloudflare R2), analytics, and any server (Source: R1-3, R2-3, R5-1). (Design Scope OUT, kept out)
- Person handles leave the public data and pages, including handles inside URLs and in free-text dossier fields; official, newsletter, outlet, paper and article names stay (Design Decision 13).
- Reddit appears on the pages, in `pulse.json` and in the feeds as counts only, with the fixed headline fallback (Design Decision 17).
- Reddit text, permalinks or ids anywhere public, and in the anchored manifest anything but the record hash (Source: R6-2, R5-2). (Design Scope OUT, kept out)
- X, LinkedIn and YouTube are counts only in both files, links included; the project's own X profile link stays; Telegram takes the same rule, flagged (Design Decision 21).
- X, LinkedIn, YouTube or Telegram text, links or figures, and X posts as verdict primary sources; loosening either gets its own question (Source: R8-3). (Design Scope OUT, kept out)
- A verdict row's primary source is never an X, LinkedIn or YouTube post; a claim with only an X source stays UNVERIFIED and may name the official account and date, with no link. Flagged: R8-3 did not name the verdict file (Design Decision 22).
- Labels are REAL, OVERHYPED, FALSE, PUSHED and UNVERIFIED, on claims, stories, topics or projects, never on people or accounts. UNVERIFIED means "not yet checked against a primary source" (Design Decision 3).
- A pipeline-proposed REAL, OVERHYPED, FALSE or PUSHED, and any model or paid hosted route for proposing verdicts (Source: R4-1, R4-2). (Design Scope OUT, kept out)
- The pipeline writes an evidence record with the state "proposed" and no label word. The owner upgrades a row by PR, and the merge is the confirm (Design Decision 5).
- Translated headlines or post titles, and any translation model; dossier prose Portuguese reviews do not gate S1 or the 14-day clock (Source: R8-1). (Design Scope OUT, kept out)
- Rewriting public git history: the 10 `pulse.json` and 12 `hype.json` commits that carry handles, Reddit titles and X excerpts stay, and the rules apply from the change forward; a rewrite gets its own question (Source: R6-2, R3-3). (Design Scope OUT, kept out)
- the browser is `playwright-core` pinned exactly to 1.59.1 with its lockfile, running the Chromium build that version installs (Design row 3).
- pinned exactly to `@deepseek-ai/cordis@4.0.4` with its MIT notice; licence closure of the installed tree audited; only the qualified component API; no server, socket, profile, credential, home directory, DSH launcher, WISH Run, task, worker or dispatch; no claim of WISH #4 acceptance (Design row 16).
- the JavaScript client `opentimestamps` pinned exactly to 0.4.9 (Design row 18).
- Paths are named against `origin/dev` at 2bc0ace, the product the owner judged. (Design Scope); the wish still works in a worktree cut from `origin/dev`.
- Never push to main or master; `gh pr create --base dev`. (host rules, `~/.claude/CLAUDE.md`)
- Never `git stash`, `git checkout <branch>`, or `git reset` in the shared workspace; use a worktree. (host rules, `~/.claude/CLAUDE.md`)
- `timeout` does not exist; use `gtimeout` (coreutils) or `curl -m`. (host rules, `~/.claude/CLAUDE.md`)

Describe each group's coupling and risk in **Complexity**. In **Model**, inherit the active model unless user instructions or an evidenced capacity need justify another supported runtime configuration. Use portable role names; keep actual model/effort settings in the runtime. Order groups by dependencies and give parallel writers disjoint files or isolated worktrees.

## Execution Groups

The aggregate gate every group runs is the repository's `ci.yml` test job, run locally: `python3 -m unittest discover -s tests`, the two `eval.py` fixture commands, and `node scripts/check_page.mjs`. A group's own checks are added to it, never substituted for it.

Groups that change `pulse.py` (A1, A2, B1, B2, B3, C1) follow the data rebuild rule (Decision 20): their Validation restores the latest successful refresh's `history-<run_id>` artifact into the gitignored `history/`, runs `python3 pulse.py --offline` before `check_page.mjs`, and the worker commits the regenerated `web/pulse.json` (and `web/briefing.json` from B1 on). A1 restores the latest artifact for its committed rebuild after taking the Decision 13 measurement on `history-38948143514`.

### Group A1: Public-data rules (handles, Reddit, X/LinkedIn/YouTube/Telegram, X figures, scrub)

**Goal:** No person handle, Reddit text or id, or X, LinkedIn, YouTube or Telegram content or figure reaches `web/pulse.json` or `web/hype.json`, and `scripts/check_page.mjs` fails CI on any of them; useful alone and first.

**Deliverables:**
1. Design row 1: conversation-network `author` values, account-naming post URLs (a `/@` segment, `x.com/…/status/`, `twitter.com/…/status/`, `bsky.app/profile/…/post/`, DIDs included), `viral.cand_account`, `viral.account`, `viral.followers` leave every public file; `@handle` posters in `skeptic[].by` become `X user`-style network labels through the new disposition list `web/i18n/dossier-sources.json`; outlet, newsletter, official feed, paper and article authors stay; `links.x_handle` and `aliases[]` are exempt by field (C6, C22, C28).
2. Design row 2: Reddit counts only in `pulse.json` and `hype.json` (no title, permalink, `t3_` id or username); headline fallback: earliest non-Reddit post title, else the topic label, else "Reddit discussion, title not shown"; dossier citations to `reddit.com` keep their claim and read "a Reddit post" (C20).
3. Design row 4: the `pulse.py` dossier copy (lines 311-318, inside `internal_posts()`) writes count-only records for X, LinkedIn, YouTube and Telegram, with no `title`, `author`, `url`, `score`, `comments` or URL-built `id`, each keeping its hype item id so `PROJECT_TOPIC` places it; status links leave `posts[]`, the citation fields and `viral.cand_post` ("an X post" in their place); X-sourced `traction[]` rows read "figure from an X post, not shown"; synthetic fixture `tests/fixtures/dossier_scrub.json` (new) and its test (C23, C26, C29, C35).
4. Design row 5: the X-figure sentence detector (numeral plus an X or engagement term) over every prose field; each hit listed `strip` or `keep` with a reason in `web/i18n/dossier-x-figures.json` (new); `strip` sentences render as a fixed two-language placeholder (Decision 10); an unlisted hit fails CI (C27).
5. Approach: `hype_build.py --scrub web/hype.json`, idempotent, applying the group-A rules to the committed output; run once and the result committed; the full research-pass build uses the same rule code.
6. Approach (reviewer MEDIUM-1): `ci.yml`'s search-index job copies the whole tree, `cp -R web "$RUNNER_TEMP/"` in place of `mkdir -p "$RUNNER_TEMP/web" && cp web/*.json web/index.html "$RUNNER_TEMP/web/"`.
7. Leak fixtures in `tests/fixtures/public_leaks/` (new), one per rule (handle, account-naming URL, Reddit, X, LinkedIn, YouTube, Telegram, unlisted X-figure hit), each an overlay on a copy of `web/` whose test asserts the rule's own finding message (Decision 14).
8. Interim Mastodon rule: every Mastodon post shows as a count until Group A2 (Decision 3).
9. Decision 13 one-time measurement: download the `history-38948143514` artifact (run 38948143514, which committed `102f289`) into `history/` inside the A1 worktree (gitignored, never committed; it holds handles and Reddit text), run `python3 pulse.py --offline` on it before and after the scrub on the same day, and record node voices, weight and signal before and after below. Deadline: before about 2026-11-06, and in any case before the artifact expires on 2026-11-15 at 19:14 UTC.

Measurement record (filled by the A1 worker at execution, then copied into the method page by Group C1): retaken 2026-10-17 after the review repair (dossier posts already stored count once) on the `history-38948143514` artifact store (`signals.sqlite` of run 38948143514), `python3 pulse.py --offline` run twice eight seconds apart (`generated_at` 13:29:40Z and 13:29:48Z UTC): before = `pulse.py` and `web/hype.json` as at `origin/dev` a85b23e (the 2bc0ace data); after = the A1 `pulse.py` with the scrubbed `web/hype.json`. Topic nodes compared: 157 on both maps of 160 (`p:sora`, `v:glm-5.2`, `v:qwen-3` left the 160 cut; `p:dspy`, `p:llama-4`, `p:wan` joined). 30-day network post totals: HN 625 before, 579 after (46 dossier HN posts in the window duplicate stored live HN posts and now count once, as the stored post); X 55 dossier records, Reddit 6,240 and Mastodon 1,192 unchanged.
- 30-day node voices: 6,141 before, 6,130 after (-11, -0.2%); changed on 29 nodes, 16 down (at most -4) and 13 up (+1 each). All 13 rises are `PROJECT_TOPIC` placements of count-only X records on a project node that text matching had given no X post (`p:browser-use`, `p:claude-app`, `p:deepseek-harness`, `p:deepseek-v4-1-flash`, `p:glm-5-3`, `p:goose`, `p:hermes-agent-nous-research`, `p:langgraph`, `p:manus`, `p:opencode`, `p:pi`, `p:reflection-beam`, `p:suno`).
- 30-day weight: 19,183.0 before, 18,518.0 after (-665.0, -3.5%), on the same 29 nodes; the largest drop is `claude` (-363.5), which loses the X network it held only through text-matched dossier posts.
- 30-day signal (0-100): changed on 133 of 157 nodes, 95 down and 38 up, by 1.7 points on average (largest -11.7, largest +10.7); the sum fell 0.35%; the 30-day top 10 by signal keeps nine of its ten topics (`anthropic` leaves, `claude-haiku` enters).
- 7-day voices and weight: unchanged (every dossier post is older than 7 days); 7-day signal moved on 54 nodes by at most 0.5 points, from the changed node set.
- Figure for the method page (C1, both languages): "On the 2026-10-16 data, removing handles and X, LinkedIn, YouTube and Telegram content from the research dossier changed 30-day topic voices by -0.2% (29 of 157 topics; 13 project topics gained one voice when their X posts were placed on them), weight by -3.5% and signal by 1.7 points on average on 133 topics; 7-day voices and weight did not change. The effect ends when the dossier's posts, dated up to 2026-10-07, leave the 30-day window (about 2026-11-06)."

**Interfaces:**
- Consumes: `origin/dev` at 2bc0ace: `pulse.py` (`NOW`, `RETAIN_DAYS`, `PROJECT_TOPIC`, `internal_posts()`, `build()`, `main()`, `--offline`), `hype_build.py` (`build()`, `project()`, `--no-history`), `scripts/check_page.mjs [webDir]`.
- Produces: `python3 hype_build.py --scrub <path>`: rewrites the file in place, a second run changes no byte; Group B3 extends it with the two removal lists. The count-only dossier record: the fields above removed, the hype item id kept. `scripts/check_page.mjs [webDir]` stays the single public-file gate and exits 1 on any finding. `web/i18n/dossier-sources.json` and `web/i18n/dossier-x-figures.json` exist; their JSON schemas are not fixed by the design, A1 fixes them (the X-figure list must carry, per hit, the sentence, `strip` or `keep` and a reason, plus the two placeholder strings `en` and `pt`). New `pulse.py` and `hype_build.py` function names are not fixed by the design.

**Acceptance Criteria:**
- [ ] SC-1 (this group: `web/pulse.json`, `web/hype.json` and the leak fixtures; the pages are checked again in C2/C3 and the feeds in D): No person handle reaches a public file: no conversation-network `author`, no account-naming post URL (`/@`, `x.com/…/status/`, `twitter.com/…/status/`, `bsky.app/profile/…/post/`, DIDs), no `@handle` or undispositioned name in `skeptic[].by`, `viral.*` or `coord.evidence[]`, in either language (C6, C22, C28). **Proof:** `node scripts/check_page.mjs` exits 0 on the built `web/` and exits 1 on each leak fixture in `tests/fixtures/public_leaks/` (new).
- [ ] SC-2 (A1 half: the scrub, the idempotent rerun, the count and placement test, the synthetic-fixture test, and the measurement recorded in this WISH.md; the method-page half, the figure stated in both languages, is C1): The committed `web/hype.json` is clean without a research pass: `hype_build.py --scrub` applied to today's `origin/dev` file removes every handle, X, LinkedIn, YouTube, Telegram and Reddit link and X figure the round-7 and round-9 reads counted, keeps the 82 items and their counts, and a second run changes no byte. **Proof:** `python hype_build.py --scrub web/hype.json` followed by `node scripts/check_page.mjs` exits 0, a rerun leaves `git diff --stat web/hype.json` empty, and a test in `tests/test_pulse.py` compares the item and per-network post counts before and after, checks that each count-only dossier record lands on its `PROJECT_TOPIC` node; on the committed synthetic fixture `tests/fixtures/dossier_scrub.json` (new) the same test checks the direction and mechanics of the change in node voices, weight and signal (count-only records placed by `PROJECT_TOPIC`, HN dossier voices merged once their authors are gone, node voices not rising except through `PROJECT_TOPIC` placements of count-only records, which can add one voice per network to a project node that text matching missed: 13 nodes, +1 each, in the measurement below; a dossier post already stored counts once); and the one-time measurement on the `history-38948143514` artifact, taken before about 2026-11-06 and in any case before the artifact expires on 2026-11-15, is recorded in the wish with the figure the method page states in both languages (C35).
- [ ] SC-3 (this group: `pulse.json`, `hype.json` and the fallback; pages in C2/C3, feeds in D): Reddit is counts only: no `reddit.com` URL, `t3_` id, or title or author on a Reddit record in `pulse.json`, `hype.json`, the pages or the four feeds, and the headline fallback follows its fixed order (C20). **Proof:** `node scripts/check_page.mjs` on the built site plus the Reddit fixtures, and `python -m unittest tests.test_pulse` covering the three fallback cases.
- [ ] SC-6 (this group: both files and the fixtures; pages in C2/C3, feeds in D): No `x.com` or `twitter.com` URL except `links.x_handle`, no LinkedIn or YouTube post URL, no Telegram post URL, and no `title`, `author`, `url`, `score` or `comments` on a count-only record, in either file, the pages or the feeds (C23, C26, C29). **Proof:** `node scripts/check_page.mjs` exits 0 on the built site and 1 on the X, LinkedIn, YouTube and Telegram fixtures.
- [ ] SC-7: Every X-figure detector hit is listed in `web/i18n/dossier-x-figures.json`, and each `strip` sentence renders as the fixed placeholder in both languages (C27). **Proof:** the CI detector step exits 1 on a fixture with an unlisted hit, and the built `web/hype.json` holds none of the 14 sentences round 9 found.

**Validation:**
```bash
set -e
python3 -m unittest discover -s tests
python3 eval.py --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json
python3 eval.py --issue11-smoke --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json --compare-v2
T="$(mktemp -d)"; cp web/hype.json "$T/once.json"; python3 hype_build.py --scrub web/hype.json; cmp web/hype.json "$T/once.json"
RUN="$(gh run list --workflow refresh.yml --branch dev --status success --limit 1 --json databaseId --jq '.[0].databaseId')"
rm -rf history && gh run download "$RUN" -n "history-$RUN" -D history
python3 pulse.py --offline
node scripts/check_page.mjs
```

**depends-on:** none

---

### Group A2: Mastodon render check and handle-free links

**Goal:** A Mastodon post links to `https://mastodon.social/statuses/<id>` only after a per-post, fail-closed, logged-out render check passed within 7 days of the checked `pulse.json`'s `generated_at`; every other Mastodon post stays a count.

**Deliverables:**
1. Design row 3: `scripts/check_mastodon_links.mjs` (new), the logged-out headless-browser check using mastodon.social's own status id; `scripts/checks/package.json` (new: `playwright-core` 1.59.1 exact) and `scripts/checks/package-lock.json` (new; measured 28 lines); the bot-written cache `web/checks/mastodon-links.json` (new); `pulse.py` emits the link only for an id with a passing check less than 7 days before `pulse.json`'s `generated_at` (not the CI clock) (C25, C34).
2. `refresh.yml`: the check step with a time cap inside the 15-minute margin, its pass and fail counts and its time cap in the run log, and `web/checks/mastodon-links.json` added to the `git add` line (Decision 7).
3. `scripts/check_page.mjs`: fails a fixture page with an unchecked id and passes a fixture whose check is 6 days older than its `pulse.json`'s `generated_at` though more than 7 days older than the clock.
4. The `/api/v1/statuses/<id>` lookup result is recorded per id for Group B3's recheck (Decision 12).

**Interfaces:**
- Consumes: A1's count-only Mastodon rule and `scripts/check_page.mjs`.
- Produces: `web/checks/mastodon-links.json`: per status id at least the check result, the check time and the `/api/v1/statuses/<id>` HTTP status; the exact shape and the CLI of `scripts/check_mastodon_links.mjs` are not fixed by the design, A2 fixes them. `scripts/checks/` is the npm tree Group E2 extends with `opentimestamps`.

**Acceptance Criteria:**
- [ ] SC-5 (this group: the link rule, the cache and the fixtures; the manifest's handle-free Mastodon URL is proved in E1; the run-log part is collected on the first refresh after merge, see QA): A Mastodon link appears only for an id with a passing check in `web/checks/mastodon-links.json` made less than 7 days before the `generated_at` of the `pulse.json` being checked (not the time CI runs), every other Mastodon post shows as a count, and the manifest carries the handle-free URL for every Mastodon record (C25). **Proof:** `node scripts/check_page.mjs` fails a fixture page with an unchecked id and passes a fixture whose check is 6 days older than its `pulse.json`'s `generated_at` though more than 7 days older than the clock, and the refresh run log shows the check's pass and fail counts and its time cap.

**Validation:**
```bash
set -e
python3 -m unittest discover -s tests
python3 eval.py --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json
python3 eval.py --issue11-smoke --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json --compare-v2
RUN="$(gh run list --workflow refresh.yml --branch dev --status success --limit 1 --json databaseId --jq '.[0].databaseId')"
rm -rf history && gh run download "$RUN" -n "history-$RUN" -D history
python3 pulse.py --offline
node scripts/check_page.mjs
npm ci --prefix scripts/checks --ignore-scripts --no-audit --no-fund
npm ls playwright-core --prefix scripts/checks | grep -q 'playwright-core@1.59.1'
```

**depends-on:** A1

---

### Group B1: Evidence records, Top 10 and gauge values

**Goal:** `pulse.py` writes `web/briefing.json` beside `pulse.json` with one evidence record per briefing story, the Top 10 cut under the published rule, and the gauge header values, all checked by the unittest suite and `check_page.mjs`.

**Deliverables:**
1. Design row 6: one evidence record per briefing story: stable id, the computed fields it was built from, source status, method version and config hash, `state: proposed`, no label word; an unfetched source reads "not fetched", never `false` or 0; substance counts only from the story's own links or a confirmed row; topic samples read "related in topic" (C7, C8, C9).
2. Design row 8: Top 10: covered news stories with a post in the last 24h, stories first seen in that window first by heat, then the rest by heat, ties by newest post then stable id; the window ends at `pulse.py`'s `NOW`, printed in BRT; each row says "new today" or its first-seen date; every other story one click away with the same evidence (C13, C19).
3. Design row 9, data half: the gauge values with the council names ("Releases / research output by area", "Hype vs substance" per story with its components, "Daily movers", a dated sourced "Risk" event log with no dial, a "Jobs" panel reading "no qualified source"), up to four gauges with coverage and "preview, not yet reproducible", no trend or arrow before 14 ledger days, no gauge "shipped", no combined score (C36). The `web/index.html` display moves to C3 (Decision 4).
4. `refresh.yml`: `web/briefing.json` added to the `git add` line, so the daily refresh commits it from B1 on (Decision 7).
5. Tests in `tests/test_pulse.py`: offline-rebuild fixture, the Top 10 recompute on the day's files and a reordered fixture; `check_page.mjs` fixtures for a REAL-carrying pipeline record, a trend with 13 ledger days and a gauge marked shipped.

**Interfaces:**
- Consumes: A1's cleaned `pulse.py` story and post shapes and the Reddit headline fallback.
- Produces: `web/briefing.json` (new). Fixed by the design: `generated_at`, per-record `state: "proposed"`, the literal readings "not fetched", "related in topic", "new today", "preview, not yet reproducible", "no qualified source", and the gauge names above. Not fixed by the design: every other key name and the nesting; B1 fixes them and later groups (B2, B3, C3, D, E1) consume them as landed.

**Acceptance Criteria:**
- [ ] SC-10 (this group: the evidence records and gauge values in `briefing.json`; the four feed files are checked in D): Each briefing story has one evidence record with `state: proposed`, no label word, "not fetched" for an unfetched source, and substance only from the story's own links or a confirmed row; the Hype vs substance gauge values in `briefing.json` and the feed items read "not fetched" for that source too, never `false` or 0 (C7, C8, C9). **Proof:** `python -m unittest tests.test_pulse` with an offline-rebuild fixture, checked in the evidence records, the gauge values and the four feed files, and a pipeline record carrying REAL that the check rejects.
- [ ] SC-14: The briefing's ten ids and their order equal a recompute from the day's `pulse.json` under the published rule, and each row shows "new today" or its first-seen date (C13, C19). **Proof:** the CI recompute step in `tests/test_pulse.py` passes on the day's files and fails on a reordered fixture.
- [ ] SC-15 (this group: the `briefing.json` data and its fixture; the header display is C3): The gauge header shows at most four gauges with coverage and "preview, not yet reproducible", the risk log and jobs panel as placeholders, no combined score, and no trend or arrow while the ledger holds fewer than 14 days. **Proof:** `node scripts/check_page.mjs` fails a fixture `briefing.json` that carries a trend with 13 ledger days.
- [ ] SC-25: No gauge reads "shipped" in S1: every gauge carries "preview, not yet reproducible", because R2-4's ship rule (14 ledger days, a green recompute verifier and the owner's confirm) needs the S5 verifier. **Proof:** `node scripts/check_page.mjs` fails a fixture `briefing.json` with a gauge marked shipped.

**Validation:**
```bash
set -e
python3 -m unittest discover -s tests
python3 eval.py --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json
python3 eval.py --issue11-smoke --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json --compare-v2
RUN="$(gh run list --workflow refresh.yml --branch dev --status success --limit 1 --json databaseId --jq '.[0].databaseId')"
rm -rf history && gh run download "$RUN" -n "history-$RUN" -D history
python3 pulse.py --offline
node scripts/check_page.mjs
python3 -m unittest tests.test_pulse
```

**depends-on:** A2 (serialized on shared files), A1

---

### Group B2: Verdict file, story-id resolution, corrections and reply policy

**Goal:** The owner-reviewed verdict file exists in git with its CI rules: every row resolves to a story, an archived id or an alias, every upgraded row carries its claim, source, two-language reason and confirming commit, and corrections are append-only against the base commit.

**Deliverables:**
1. Design row 7, verdict part: `web/verdicts.json` (new): labels REAL, OVERHYPED, FALSE, PUSHED, UNVERIFIED; an upgraded row carries the named claim (or the document, for PUSHED), a primary source URL that is never an X, LinkedIn or YouTube post, a reason in both languages and the confirming commit; FALSE rows link the right-of-reply and corrections path (C10, C30).
2. Design row 7, resolution part: a row's `s:` id resolves to a story in the day's `pulse.json`, to an id in a `web/ledger/ids/` archive file, or through `web/story-aliases.json` (new, bot-written), which `pulse.py` writes each run by comparing the day's stories with the previous `pulse.json` (a story whose posts carry over under a new id maps old id to new), kept apart from the owner-reviewed rows; `refresh.yml` stages it (Decision 7) (C2, C32).
3. Design row 7, corrections part: `web/corrections.json` (new), appended never edited over; a `ci.yml` check compares it with the base commit and fails an edited or removed entry (C11, C40).
4. Design row 7, policy part: `web/POLICY.md` and `web/POLICY.pt.md` (new) with right of reply (Lei 13.188/2015, 60 days, Risk 5) and corrections; published before the first FALSE row. The removal and deleted-post section is Group B3.
5. Fixtures: one per missing verdict field, an orphaned `s:` id, and a row confirmed 9 days before a `pulse.json` that no longer holds its story but whose id is in that day's archive file (with a fixture `web/ledger/ids/YYYY-MM-DD.json`, Decision 13); the alias test in `tests/test_pulse.py`; the corrections edit, remove and append fixture commits, run in a scratch git repository by the unittest suite (Decision 14).

**Interfaces:**
- Consumes: B1's `web/briefing.json` story ids and `pulse.json` stories.
- B2 note: no upgraded verdict row (REAL, OVERHYPED, FALSE, PUSHED) is added to `web/verdicts.json` before E1 lands the `web/ledger/ids/` archive: until then a row whose story leaves the 7-day window resolves to nothing and fails `check_page.mjs` in the refresh Gate, which blocks that day's data commit (stated in `web/POLICY.md` and `web/POLICY.pt.md`).
- B1 note: alias resolution must prefer the post-carry-over alias (old id to the new id that took its posts) over a live id that still exists but whose posts moved; B1 ids are unique per day, and when two stories name one release the earliest editorial post keeps the `release:` key (STORY_METHOD).
- Produces: `web/verdicts.json` row fields named above (exact key names not fixed by the design beyond the `s:` id prefix); `web/story-aliases.json` (old id to new id); `web/corrections.json`; the read shape of `web/ledger/ids/YYYY-MM-DD.json`, fixed here and written by E1 (Decision 13); whether the corrections check is an inline `ci.yml` step or a script is not fixed by the design.

**Acceptance Criteria:**
- [ ] SC-11: Every verdict row resolves to a story in the day's `pulse.json`, to an id in a `web/ledger/ids/` archive file, or through `web/story-aliases.json`; every upgraded row carries its claim or document, a primary source that is not an X, LinkedIn or YouTube post, a reason in both languages and the confirming commit; every FALSE row links the reply and corrections path (C2, C10, C11, C30). **Proof:** `node scripts/check_page.mjs` exits 1 on one fixture per missing field and on an orphaned `s:` id, and exits 0 on a fixture row confirmed 9 days before a `pulse.json` that no longer holds its story but whose id is in that day's archive file; a `tests/test_pulse.py` case gives `pulse.py` a previous `pulse.json` whose story gains an earlier post and checks that the alias file maps the old id to the new one.
- [ ] SC-12: A reply or correction is appended, never edited over (C11). **Proof:** the `ci.yml` check exits 1 on a fixture commit that edits an existing `web/corrections.json` entry and on one that removes an entry, comparing with the base commit, and exits 0 on one that appends.

**Validation:**
```bash
set -e
python3 -m unittest discover -s tests
python3 eval.py --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json
python3 eval.py --issue11-smoke --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json --compare-v2
RUN="$(gh run list --workflow refresh.yml --branch dev --status success --limit 1 --json databaseId --jq '.[0].databaseId')"
rm -rf history && gh run download "$RUN" -n "history-$RUN" -D history
python3 pulse.py --offline
node scripts/check_page.mjs
python3 -m unittest tests.test_pulse
```

**depends-on:** B1

---

### Group B3: Removal requests and the deleted-post recheck

**Goal:** A stored or dossier post that its source reports gone, or that `web/removals.json` names, leaves every built output, the history DB and the committed `web/hype.json` on the next daily rebuild, and a post the recheck could not reach shows only as a count.

**Deliverables:**
1. Design row 7, removal part: `web/removals.json` (new, owner-reviewed) applied by the build; the removal-request and deleted-post section in `web/POLICY.md` and `web/POLICY.pt.md` (how a person asks, what the daily rebuild drops, that X, LinkedIn, YouTube and Telegram dossier records keep nothing to recheck, and that committed git history and the anchored manifests cannot be edited) (C34).
2. Design row 7, recheck part: after `pulse.py` builds its lists and before the composition and manifest steps, recheck by id every stored post the day's outputs would show: HN through the Firebase item endpoint (`deleted` or `dead`), Mastodon through mastodon.social `/api/v1/statuses/<id>` (a 404 counts as removed; shared with A2, Decision 12), Bluesky through `app.bsky.feed.getPosts` (a missing URI counts as removed), Reddit records through arctic-shift by id (`[deleted]` or `[removed]`); a post found gone is deleted from `history/signals.sqlite`; time cap inside C12's 15-minute margin, fail-closed; checked, removed and unreached counts and the cap in the run log.
3. Design row 7, dossier part: the recheck also covers every dossier post that keeps a source id (today the 268 HN posts); `internal_posts()` drops, before `build()`, every dossier post that `web/removals.json` names or whose URL's SHA256 is in `web/checks/dossier-gone.json` (new, bot-written, append-only, hashes only), to which `pulse.py` adds each dossier post the recheck finds gone.
4. `hype_build.py --scrub web/hype.json` also removes from each item's `posts` every post either list names (deletion-only); the full research-pass build applies both lists; `refresh.yml` runs the scrub after the recheck and stages `web/hype.json` and `web/checks/dossier-gone.json` (Decision 7).
5. `scripts/check_page.mjs`: fails a build missing a policy key in either language, and a built `web/hype.json` that holds a post `web/removals.json` names or whose URL hash `web/checks/dossier-gone.json` lists.
6. The `tests/test_pulse.py` cases SC-13 names (removal-listed post; HN, Mastodon, Bluesky stubs with a timeout case; three HN dossier posts with `dead`, removal-listed and timeout), asserting `pulse.json` and `briefing.json`; the four-feed assertion is added by Group D.

**Interfaces:**
- Consumes: A1's `hype_build.py --scrub`, A2's recorded Mastodon lookup, B1's `web/briefing.json`, B2's `web/POLICY.md` and `web/POLICY.pt.md`.
- B2 note: `web/POLICY.md` and `web/POLICY.pt.md` carry the sections `<a id="reply"></a>` and `<a id="corrections"></a>` that `check_page.mjs` requires; the removal section is added beside them. `scripts/check_owner_files.py` (`OWNER_FILES`) is where `web/removals.json` joins the no-bot-commit rule.
- Produces: `web/removals.json` and `web/checks/dossier-gone.json` (shapes not fixed by the design; the hash input, the URL string as stored, is fixed by B3 and stated in the policy); the recheck's place in `pulse.py`'s `main()` between the lists and the output writes; the time-cap value is not fixed by the design.

**Acceptance Criteria:**
- [ ] SC-13 (this group: the policy, `pulse.json`, `briefing.json`, the history DB, `web/hype.json` and the fixtures; the four feeds are asserted in D, the Hype page in C2; the run-log part is collected on the first refresh after merge): `web/POLICY.md` and `web/POLICY.pt.md` carry the removal-request and deleted-post section (how to ask, what the daily rebuild drops, and that git history and the anchored manifests cannot be edited), and a stored post that the by-id recheck finds deleted or removed, or that `web/removals.json` names, leaves the built pages, `pulse.json`, `briefing.json` and the four feeds, and a post found gone leaves the history DB; a dossier post found gone or removal-listed also leaves `web/hype.json` and the Hype page, and no later run reloads it; a post the recheck could not reach shows as a count (C34). **Proof:** `node scripts/check_page.mjs` fails a build missing a policy key in either language; a `tests/test_pulse.py` fixture with one removal-listed post checks that it reaches no built output; and a `tests/test_pulse.py` case loads stored HN, Mastodon and Bluesky posts into a scratch history DB, stubs the recheck to return `deleted` for the HN item, a 404 for the Mastodon status and a missing URI for the Bluesky post, and checks that each leaves every output and its DB row, while a fourth post whose recheck times out appears only as a count; a further `tests/test_pulse.py` case runs `pulse.py` on a fixture `web/hype.json` holding three HN dossier posts, stubs the recheck to return `dead` for the first, names the second in a fixture `web/removals.json` and times out on the third, and checks that the first two leave `pulse.json`, `briefing.json` and the four feeds, that `hype_build.py --scrub` then removes them and only them from the fixture `web/hype.json` with the third kept, that the first's URL hash is in `web/checks/dossier-gone.json`, and that a second `pulse.py` run on the rewritten file reloads neither; `node scripts/check_page.mjs` fails a built `web/hype.json` that holds a post `web/removals.json` names or whose URL hash `web/checks/dossier-gone.json` lists; the refresh run log shows the recheck's checked, removed and unreached counts and its time cap.

**Validation:**
```bash
set -e
python3 -m unittest discover -s tests
python3 eval.py --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json
python3 eval.py --issue11-smoke --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json --compare-v2
T="$(mktemp -d)"; cp web/hype.json "$T/once.json"; python3 hype_build.py --scrub web/hype.json; cmp web/hype.json "$T/once.json"
RUN="$(gh run list --workflow refresh.yml --branch dev --status success --limit 1 --json databaseId --jq '.[0].databaseId')"
rm -rf history && gh run download "$RUN" -n "history-$RUN" -D history
python3 pulse.py --offline
node scripts/check_page.mjs
```

**depends-on:** B2, A2

---

### Group C1: Two languages, `lang` tags and the method sources

**Goal:** Every string of our own text has an `en` and a `pt` entry, every headline carries `lang`, and the method text (with the X-route disclosure and the Decision 13 figure) has English and Portuguese root sources copied into `web/` by `run.py` and the Pages job.

**Deliverables:**
1. Design row 12: `web/i18n/strings.json` (new) with `en` and `pt` for every string of our own text known so far (later groups add theirs); headlines and post titles stay as posted with a `lang` tag from source metadata, else `und`, written by `pulse.py`; no build step writes a translated headline (C17, C33).
2. Design row 12, method sources: repository-root `METHODOLOGY.md` and new `METHODOLOGY.pt.md`; `run.py` and the GitHub Pages job's sync step in `deploy.yml` copy both into `web/`; `deploy.yml`'s push path filter lists both; the disclosure and licence checks run on the copied files (Decision 8: the Cloudflare job is dropped by F).
3. Design row 14: the method text discloses the X route in both languages: the X counts and the attention scores built from X posts come from the 2026-10-07 research pass, whose notes name "x_search" reports and "X syndication" readbacks; whether those are X's published interfaces, and whether a paid call was made, is not on record; counts read "posts in our sample", never reach; written in the root files, not the `web/` copies (C31). The Hype header's disclosure key is in `strings.json`, rendered by C2.
4. Decision 13's measured figure from Group A1, stated in both method files.
5. `check_page.mjs` fixtures: a missing `pt` key, a translated headline, a method copy lacking the disclosure key.

**Interfaces:**
- Consumes: A1's measurement record (this WISH.md, Group A1) and placeholder strings (Decision 10).
- Produces: `web/i18n/strings.json` (schema not fixed by the design; C1 fixes it: one entry per key with non-empty `en` and `pt`); the `lang` field on every headline and post title; `METHODOLOGY.pt.md`, `web/METHODOLOGY.md`, `web/METHODOLOGY.pt.md`. `web/dehype.js` (also listed on row 12) is created by C2.

**Acceptance Criteria:**
- [ ] SC-2, C1 half: `METHODOLOGY.md` and `METHODOLOGY.pt.md` (and their `web/` copies) state the Decision 13 figure recorded under Group A1, measured on the `history-38948143514` artifact's store, in both languages.
- [ ] SC-8: Every string of our own text has a non-empty `en` and `pt` entry, every headline carries `lang`, and no build step writes a translated headline (C17). **Proof:** `node scripts/check_page.mjs` fails a fixture with a missing `pt` key and one with a translated headline.
- [ ] SC-21 (this group: the X-route disclosure, the sync step and the path filter; the licence text is added by Group F; the refresh-run byte-equality part is collected after merge): The method page and the Hype header disclose the X route in both languages, and counts read "posts in our sample" (C31), and the licence text is on the method page in both languages. **Proof:** `node scripts/check_page.mjs`, run after the sync step copies the root `METHODOLOGY.md` and `METHODOLOGY.pt.md` into `web/`, fails a build whose method page lacks the disclosure key or the licence text in either language; a refresh run leaves both `web/` copies byte-equal to their root sources; and `deploy.yml`'s push path filter lists `METHODOLOGY.pt.md`.

**Validation:**
```bash
set -e
python3 -m unittest discover -s tests
python3 eval.py --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json
python3 eval.py --issue11-smoke --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json --compare-v2
RUN="$(gh run list --workflow refresh.yml --branch dev --status success --limit 1 --json databaseId --jq '.[0].databaseId')"
rm -rf history && gh run download "$RUN" -n "history-$RUN" -D history
python3 pulse.py --offline
node scripts/check_page.mjs
cmp METHODOLOGY.md web/METHODOLOGY.md
cmp METHODOLOGY.pt.md web/METHODOLOGY.pt.md
grep -q 'METHODOLOGY.pt.md' .github/workflows/deploy.yml
```

**depends-on:** B3 (serialized on shared files), A1

---

### Group C2: dehype shell, all-stories, output and Hype pages

**Goal:** The dehype shell (`web/dehype.css`, `web/dehype.js`) and three static pages (all stories, output by area, Hype project page) exist beside the console in the Mission control look, in both languages, with the Hype page's fixed wordings and the reviewed-Portuguese dossier fallback.

**Deliverables:**
1. Design row 10, part: `web/dehype.css` (new), `web/dehype.js` (new), `web/stories.html` (new, all stories with the same evidence display as the briefing), `web/output.html` (new, the output-by-area drill-down for Papers and Repos), `web/hype.html` (new); the observatory explorer keeps its own shell.
2. Design row 11, Hype-page part: each page names the data file it reads; the Hype page heads every view with "research dossier, content cut" and the `content_cutoff` date, "not in the daily refresh"; the gap class shows as Hype vs substance components with "heuristic only, not validation" and never fills the verdict slot; skeptic entries read "sampled criticism, not checked against a primary source"; the Hype header shows the X-route disclosure key from C1 (C21).
3. Design row 13: `web/i18n/dossier.pt.json` (new, may be empty) keyed by slug, field path and the SHA256 of the English text, each entry with `reviewed_in` (the merged PR); a hash mismatch falls back to English under the fixed Portuguese notice; `hype_build.py` provides the field paths and hashes; `check_page.mjs` validates only the form of the entries that exist and passes an empty file (C24).
4. `check_page.mjs` grows from a one-page check (it asserts exactly one inline script in `web/index.html` today) to cover each new page and the handle, Reddit and X rules on them.

**Interfaces:**
- Consumes: C1's `web/i18n/strings.json` and `lang` tags; B1's `web/briefing.json`; B3's scrubbed `web/hype.json`; `web/data.json` and `web/pulse.json` as today.
- Produces: `web/dehype.js` with the language switch and the data loaders (function names not fixed by the design); the pages read the source files directly until D points the loader at the frontend plugin's tables (Decision 9); `web/i18n/dossier.pt.json` entry form: slug, field path, SHA256 of the English text, `reviewed_in`.

**Acceptance Criteria:**
- [ ] SC-9: A Portuguese page shows dossier prose only from a `dossier.pt.json` entry whose hash matches the current English and that has `reviewed_in`, else the English under the notice, and no S1 check requires a reviewed Portuguese entry: `check_page.mjs` validates only the form of the entries that exist (`reviewed_in` and the hash match) (C24). **Proof:** `node scripts/check_page.mjs` fails a fixture entry without `reviewed_in` and a page with neither notice nor match, and exits 0 with an empty `dossier.pt.json`; `grep -n 'dossier.pt.json'` over the S1 acceptance steps finds only the C24 form check.
- [ ] SC-13, Hype page part only: a dossier post found gone or removal-listed is absent from the built Hype page (asserted with the B3 fixtures).
- [ ] SC-1, SC-3 and SC-6 hold on the three new pages: `node scripts/check_page.mjs` exits 0 on the built `web/` including them.

**Validation:**
```bash
set -e
python3 -m unittest discover -s tests
python3 eval.py --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json
python3 eval.py --issue11-smoke --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json --compare-v2
node scripts/check_page.mjs
```

**depends-on:** C1, B3

---

> C1 note for C2/C3: the method pages carry `<a id="<english-slug>"></a>` lines before each pt heading; md2html must use them as the next heading id and skip auto-slugs for the pt file. The English `method` paragraphs in pulse.json/briefing.json must not render on pt pages; link the pt method anchor from strings.json `methods` instead. Data strings are rendered English: reuse check_page.mjs `ours` to map them back to keys.

### Group C3: Briefing first screen, method and audit pages, and the fold

**Goal:** `web/index.html` becomes the dehype briefing with the gauge header, the method and audit pages exist, and every console URL and tab anchor in use today resolves to its dehype page, with search kept.

**Deliverables:**
1. Design row 10, part: `web/index.html` rewritten as the briefing first screen (Top 10 with evidence records and "new today" or first-seen date), `web/method.html` (new, reading the `web/` copies of the two method files), `web/audit.html` (new shell; E1 and E2 fill the ledger, hashes and anchored/pending states).
2. Design row 9, display half: the gauge header in `web/index.html` showing B1's values: at most four gauges with coverage and "preview, not yet reproducible", the risk log and jobs panel as placeholders, no combined score, no trend or arrow before 14 ledger days (Decision 4).
3. Design row 11, fold: every console URL and tab anchor in use today resolves to its dehype page (Pulse to the briefing and all stories, Papers and Repos to the output drill-down, Hype to the Hype page, Method to the method page, Decision 18 of the design); the in-browser search stays and keeps its row count on screen; `tests/fixtures/console_anchors.json` (new) lists today's anchors and wordings, and `check_page.mjs` checks the built site against it (C21).

**Interfaces:**
- Consumes: C2's `web/dehype.css`, `web/dehype.js`, the three pages and the anchor targets; B1's `web/briefing.json` gauge and Top 10 keys; C1's method copies.
- Produces: `web/audit.html` with the slots E1 and E2 fill (slot names not fixed by the design); `tests/fixtures/console_anchors.json`.

**Acceptance Criteria:**
- [ ] SC-20: Every console URL and tab anchor in use today resolves to its dehype page; each page names its data file; the Hype page header shows the `content_cutoff` date; the gap class and skeptic entries carry their fixed wording; search shows its row count (C21). **Proof:** `node scripts/check_page.mjs` checks the built site against a committed list of today's anchors and wordings, `tests/fixtures/console_anchors.json` (new).
- [ ] SC-15 (this group: the header display of B1's values): The gauge header shows at most four gauges with coverage and "preview, not yet reproducible", the risk log and jobs panel as placeholders, no combined score, and no trend or arrow while the ledger holds fewer than 14 days. **Proof:** `node scripts/check_page.mjs` fails a fixture `briefing.json` that carries a trend with 13 ledger days.
- [ ] SC-1, SC-3 and SC-6 hold on the rewritten `web/index.html` and the two new pages: `node scripts/check_page.mjs` exits 0 on the built `web/`.

**Validation:**
```bash
set -e
python3 -m unittest discover -s tests
python3 eval.py --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json
python3 eval.py --issue11-smoke --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json --compare-v2
node scripts/check_page.mjs
node --test tests/dehype_stale.test.mjs
```

**depends-on:** C2

---

### Group D: Feeds and the one-shot Cordis composition

**Goal:** One Node step after `pulse.py`, pinned to `@deepseek-ai/cordis@4.0.4` and using only the qualified component API, writes RSS 2.0 and JSON Feed 1.1 feeds in English and Portuguese and the frontend's per-language tables, with no server and no WISH Run.

**Deliverables:**
1. Design row 15: `web/feed.xml`, `web/feed.json`, `web/feed.pt.xml`, `web/feed.pt.json` (new), written by `scripts/dehype/plugins/feed.mjs` (new): same item ids and headlines in both languages; each item carries the stable id, the verdict state ("proposed by the pipeline, not reviewed" or the confirmed label) and the source links (C1, C17, C43); `tests/test_feed.py` (new).
2. Design row 16: `scripts/dehype/compose.mjs` (new) creates a context, loads the feed and frontend adapter plugins, writes data and string tables and disposes; `scripts/dehype/plugins/frontend.mjs` (new); `scripts/dehype/package.json` and `scripts/dehype/package-lock.json` (new; measured 53 lines, 3 packages); `scripts/dehype/NOTICE` (new, the MIT text); the licence-closure audit of the installed tree committed beside it (file name not fixed by the design) (C14, C18).
3. `refresh.yml`: the Node step after `pulse.py` with a time cap, its duration in the run log, and the four feeds added to the `git add` line (`web/briefing.json` is already staged by B1, Decision 7).
4. `web/dehype.js` points its loader at the frontend plugin's tables (Decision 9).
5. Feed parts of earlier criteria: the evidence-record readings (SC-10) and the removal cases (SC-13) asserted on the four feed files; SC-1, SC-3, SC-6 on the feeds through `check_page.mjs`.

**Interfaces:**
- Consumes: B1's `web/briefing.json`, B2's `web/verdicts.json`, C1's `web/i18n/strings.json`; the Cordis qualified component API as documented in `docs/integrations/cordis.md` (the plan does not restate its signatures).
- Produces: `node scripts/dehype/compose.mjs` (no arguments, run from the repository root, Decision 16); the four feed files with the RSS and JSON Feed fields SC-16 names, including the `_dehype` extension object; the frontend tables' paths, fixed by D (not fixed by the design). E1 adds the failed-Pulse "stale since" handling to `compose.mjs`.

**Acceptance Criteria:**
- [ ] SC-16: The RSS file validates as RSS 2.0 and the JSON file as JSON Feed 1.1 in both languages, with the same item ids and headlines, each item carrying its stable id, verdict state and source links (C1, C17). **Proof:** `python -m unittest tests.test_feed` (new) on the four built feed files, asserting for RSS 2.0 a root `rss` with `version="2.0"`, one `channel` with `title`, `link`, `description` and `language` (`en` or `pt-BR`), and on each `item` a `title`, a `link`, a `guid` with `isPermaLink="false"` holding the stable id, a `pubDate` that parses as RFC 822, a `category` holding the verdict state and the source links in `description`; and for JSON Feed 1.1 a top-level `version` equal to `https://jsonfeed.org/version/1.1`, a `title`, a `language` and an `items` array, each item with a string `id` equal to the stable id, a `url`, `content_text`, a `date_published` that parses as RFC 3339, and the verdict state and source links in an `_dehype` extension object; the English and Portuguese files of each format hold the same ids in the same order with the same headlines.
- [ ] SC-17 (the run-log duration is collected on the first refresh after merge): The Cordis step resolves exactly `@deepseek-ai/cordis@4.0.4`, ships the MIT notice, opens no server or socket, creates no WISH Run or dispatch, and fits its time cap (C14, C18). **Proof:** `npm ls @deepseek-ai/cordis --prefix scripts/dehype` prints 4.0.4, `scripts/dehype/NOTICE` holds the MIT text, the licence-closure audit is committed beside it, and the refresh run log shows the step's duration.
- [ ] SC-10, feed part: the four feed files read "not fetched" for an unfetched source, never `false` or 0, on the offline-rebuild fixture.
- [ ] SC-13, feed part: the posts removed in B3's fixtures reach none of the four feed files.

**Validation:**
```bash
set -e
npm ci --prefix scripts/dehype --ignore-scripts --no-audit --no-fund
npm ls @deepseek-ai/cordis --prefix scripts/dehype | grep -q '@deepseek-ai/cordis@4.0.4'
grep -q 'MIT' scripts/dehype/NOTICE
node scripts/dehype/compose.mjs
python3 -m unittest discover -s tests
python3 -m unittest tests.test_feed
python3 eval.py --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json
python3 eval.py --issue11-smoke --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json --compare-v2
node scripts/check_page.mjs
```

**depends-on:** C3, B2

---

### Group E1: Ledger, manifest, story-id archive, attestation and stale since

**Goal:** Each refresh writes a daily ledger on Pages, a handle-free input manifest on a dated GitHub Release whose SHA256 the ledger records, a never-edited story-id archive, and a Sigstore attestation from a least-privilege job; and the briefing, gauges and feed read "stale since" when a run fails or is late.

**Deliverables:**
1. Design row 17: `scripts/manifest.py` (new) writes the manifest (post ids and handle-free URLs, Mastodon records as `mastodon.social/statuses/<id>`, each Reddit record only as the SHA256 of its canonical stored JSON plus the network name) and its check; `web/ledger/index.json` (new); `web/ledger/ids/YYYY-MM-DD.json` (new, one per day, in B2's shape, Decision 13); the dated Release asset; `refresh.yml` steps after the composition, staging the ledger and archive (C3, C15, C16, C25, C32).
2. Design row 18, attestation part: a Sigstore attestation of the manifest that `gh attestation verify` accepts, made in its own job (`needs: refresh`, permissions `id-token: write` and `attestations: write` only, the manifest passed in as an artifact) so no attestation token sits beside `npm ci` and pip code (C42).
3. Design row 18, stale-since part: when the Pulse step fails, the briefing, gauges and feed read "stale since" the date with the reason and carry no value over (in `scripts/dehype/compose.mjs`); `web/dehype.js` reads the briefing as belonging to the America/Sao_Paulo calendar date of its `generated_at` and shows "stale since" that date once 06:00 America/Sao_Paulo of the next date has passed (C5, C12, C37).
4. `web/audit.html` shows the ledger hash and the Release asset hash side by side.
5. Tests: the manifest check's Reddit fixture and a SHA256 recompute from canonical JSON (unittest); the failed-Pulse composition test; the six-case `dehype.js` test as `tests/dehype_stale.test.mjs`, run by `node --test` and added to `ci.yml`'s test job (Decision 15).

**Interfaces:**
- Consumes: B3's post-recheck lists (the manifest omits posts found gone), D's `compose.mjs`, B2's archive shape, C3's `web/audit.html`.
- B2 note: the story-id archive read shape (Decision 13) is `web/ledger/ids/YYYY-MM-DD.json` = `{"date": "YYYY-MM-DD", "ids": ["s:<12 hex>", ...]}` E1 names the file by the America/Sao_Paulo date of the briefing's `generated_at`; B2 requires only that `date` equals the file name's date, ignores extra keys (the fixture also writes `generated_at`), unions `ids` over every file in the directory, and fails a file in another shape. Example: `tests/fixtures/verdicts/archive/ledger/ids/2026-10-08.json`.
- B1 note: `pulse.py` (`ledger_days`) and `check_page.mjs` (`ledgerCount`) count ledger days from `web/ledger/index.json` read as a JSON list of day entries or as `{"entries": [...]}`; any other shape counts as 0 days, which holds trends.
- Produces: `web/ledger/index.json` entries (one per day; carries the ledger SHA256; E2 adds the proof date and block height); `scripts/manifest.py`'s CLI is not fixed by the design, E1 fixes it; the attestation action is not named by the design (pin it by commit SHA like the existing actions).

**Acceptance Criteria:**
- [ ] SC-4: The manifest holds no `reddit.com`, no `t3_` id and no Reddit field other than the hash and the network name, and an outsider who holds the archived record recomputes its hash (C15, C16). **Proof:** the manifest check in `scripts/manifest.py` (new) fails its Reddit fixture, and a test recomputes one record's SHA256 from canonical JSON.
- [ ] SC-5, manifest part: the manifest carries the handle-free `mastodon.social/statuses/<id>` URL for every Mastodon record.
- [ ] SC-18 (this group: the ledger hash equal to the Release asset's, the attestation job's permissions, the audit page's matching hashes; `gh attestation verify` on a day's manifest is collected on the first refresh after merge; the OpenTimestamps part is E2): The day's ledger SHA256 equals the Release asset's, the manifest has an attestation and an OpenTimestamps proof, and a proof not yet upgraded reads "pending" (C3, C4). **Proof:** the attestation is made in a job whose permissions are only `id-token: write` and `attestations: write`, and `gh attestation verify` on the day's manifest exits 0; the pinned `opentimestamps` client's `upgrade` then `verify --ignore-bitcoin-node`, through the Esplora explorer, accept the proof against a Bitcoin block; the audit page shows the matching hashes; and the day N-1 proof, pending when published, reads "anchored" with its block height in the ledger entry of day N+1, with `web/ledger/ots/` holding the upgraded file and no earlier ledger entry changed.
- [ ] SC-19: When the Pulse step fails, the briefing, gauges and feed read "stale since" the date with the reason, and no value is carried over; and when no run has committed or deployed, the browser reads a briefing as belonging to the America/Sao_Paulo calendar date of its `generated_at`, whatever the hour it was made (a late scheduled run or a manual `workflow_dispatch` included), and shows "stale since" followed by that date once 06:00 America/Sao_Paulo of the next date has passed, so a briefing from an earlier date never reads fresh after that day's 06:00 deadline (C5, C12, C37; R10-1, its reviewer HIGH-2). **Proof:** a test that runs the composition on a failed-Pulse fixture and checks the three outputs, and a `dehype.js` fixture test with six cases: a briefing generated at 05:25 BRT today, viewed at 07:00 BRT today, shows no marker; a briefing generated at 05:25 BRT the previous day, viewed at 05:50 BRT today, shows no marker; the same previous-day briefing viewed at 07:00 BRT today finds "stale since" with its date; a briefing generated at 14:00 BRT the previous day, viewed at 05:50 BRT today, shows no marker; the same 14:00 briefing viewed at 07:00 BRT today finds "stale since" with its date; and a briefing generated at 05:25 BRT two days earlier, viewed at 05:50 BRT today, finds "stale since" with its date.

**Validation:**
```bash
set -e
python3 -m unittest discover -s tests
node --test tests/dehype_stale.test.mjs
python3 eval.py --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json
python3 eval.py --issue11-smoke --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json --compare-v2
node scripts/check_page.mjs
```

- E1 known gap (deferred to the owner): the audit page's "equal" mark compares the Release asset SHA256 that the refresh runner recorded after downloading the asset back (`scripts/manifest.py release`), not a hash the browser reads from GitHub; a browser check against the GitHub Releases API would add an external fetch to `web/dehype.js` (one loader, named files only) and is left for the owner to decide.

- E1 wiring note (from the E2 review): E1's workflow wiring (`e1-workflow.proposed.diff`) must never be applied without E2's. From E2 on, `check_page.mjs` fails a ledger entry without its OpenTimestamps proof, so E1's manifest step alone would make the refresh Gate fail before "Commit snapshot" and stop every data commit, the briefing included. The two land as one combined workflow change.

**depends-on:** D, B3, C3

---

### Group E2: OpenTimestamps proof, upgrade loop and anchored state

**Goal:** Each day's manifest gets an OpenTimestamps proof from the pinned `opentimestamps` 0.4.9 client, committed pending; later refreshes upgrade pending proofs in place and record the block in their own ledger entry, so the audit page reads "anchored" only once a ledger entry records the block.

**Deliverables:**
1. Design row 18, proof part: `opentimestamps` pinned exactly to 0.4.9 added to `scripts/checks/package.json` and `scripts/checks/package-lock.json` (measured: 875 lines, 88 packages with `playwright-core` 888 lines); the licence-closure audit of the `scripts/checks/` tree (LGPL-3.0 client; file name not fixed by the design) (C4, C38).
2. `web/ledger/ots/YYYY-MM-DD.ots` (new) committed pending when published; each later refresh runs `upgrade` on every proof still pending, commits the upgraded file in place, and records the date and Bitcoin block height in that run's own ledger entry, never editing earlier entries; the `refresh` job (not the attestation job, which keeps only `id-token: write` and `attestations: write` and runs no `npm ci`, C42) runs `verify --ignore-bitcoin-node` against the public Esplora explorer at `https://blockstream.info/api` in a step named "OpenTimestamps upgrade and verify", after the manifest step; `refresh.yml` stages `web/ledger/ots/` (Decision 7).
3. `web/audit.html` reads "anchored" for a date only once a ledger entry records its block, else "pending".
4. `METHODOLOGY.md` and `METHODOLOGY.pt.md` (and their `web/` copies) name the route, the explorer it trusts, and that anyone with a node can run `ots verify`.

**Interfaces:**
- Consumes: E1's manifest, `web/ledger/index.json` entries and `web/audit.html`; A2's `scripts/checks/` npm tree.
- Produces: the ledger-entry fields for proof date and block height (key names not fixed by the design); the exact client invocation follows the 0.4.9 package's own interface (not restated by the design beyond `upgrade` and `verify --ignore-bitcoin-node`).

**Acceptance Criteria:**
- [ ] SC-18 (this group: the proof, the upgrade loop and the pending/anchored reading; the day N-1 proof reading "anchored" in day N+1's entry is collected during the clock, see QA): The day's ledger SHA256 equals the Release asset's, the manifest has an attestation and an OpenTimestamps proof, and a proof not yet upgraded reads "pending" (C3, C4). **Proof:** the attestation is made in a job whose permissions are only `id-token: write` and `attestations: write`, and `gh attestation verify` on the day's manifest exits 0; the pinned `opentimestamps` client's `upgrade` then `verify --ignore-bitcoin-node`, through the Esplora explorer, accept the proof against a Bitcoin block; the audit page shows the matching hashes; and the day N-1 proof, pending when published, reads "anchored" with its block height in the ledger entry of day N+1, with `web/ledger/ots/` holding the upgraded file and no earlier ledger entry changed.

**Validation:**
```bash
set -e
npm ci --prefix scripts/checks --ignore-scripts --no-audit --no-fund
npm ls opentimestamps --prefix scripts/checks | grep -q 'opentimestamps@0.4.9'
npm ls playwright-core --prefix scripts/checks | grep -q 'playwright-core@1.59.1'
python3 -m unittest discover -s tests
node --test tests/dehype_stale.test.mjs
python3 eval.py --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json
python3 eval.py --issue11-smoke --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json --compare-v2
node scripts/check_page.mjs
cmp METHODOLOGY.md web/METHODOLOGY.md
cmp METHODOLOGY.pt.md web/METHODOLOGY.pt.md
```

- E2 risk note: `npm audit` on `scripts/checks` (2026-10-18) flags 11 packages, all through `opentimestamps` 0.4.9: `request` (SSRF) and `form-data` critical; `qs`, `tough-cookie`, `uuid`, `bn.js` moderate; `elliptic` low. No fix exists but a downgrade, so the pin stands; the scoping (runner only, allow-listed calendars and explorer, per-call deadlines, no cookies, no secret in the steps) is recorded in `scripts/checks/licence-closure.json` and in the risk table.

**depends-on:** E1

---

### Group F: Staging set, ready time, records and licence

**Goal:** The bot's staging set is exactly the bot-written files and is checked in CI, the refresh is scheduled to be live by 06:00 America/Sao_Paulo, the roadmap and README record S1, and the code and data licences change from this change forward.

**Deliverables:**
1. Design row 19: the verdict file, `dossier.pt.json`, `dossier-x-figures.json`, the `skeptic[].by` disposition list and `removals.json` enter only by a merged PR and are never in the bot's staging set; `mastodon-links.json`, `story-aliases.json`, `dossier-gone.json`, the scrubbed `web/hype.json`, the day's `briefing.json`, feeds, ledger, story-id archive and upgraded proofs under `web/ledger/ots/` are; `check_page.mjs` checks the `git add` line of `refresh.yml` in CI (C2, C44).
2. Design row 20: the refresh cron moves from `17 9 * * *` to `45 7 * * *`; the Cordis step, the Mastodon check and the recheck keep their time caps inside the 15-minute margin; the re-fit after 7-10 scheduled runs is recorded in this wish (C12, C34).
3. Design row 21: `docs/ROADMAP.md` amends D5 to "several static pages", D2 to GitHub Pages only, D3's revisit text and P4 to the ledger on Pages plus inputs on dated Releases (no R2), line 3 to name the dehype briefing on several static pages as the first public surface, and adds S2-S6 and G1 with their deferred questions (O12, O6, O4b, O16, A10, and O30 for S5), S5 naming the recompute verifier and its inputs; the dehype name in `README.md`; the inherited fixes: `web/hype.json` in the refresh commit set (already staged by B3; confirmed here), relative fetch paths in `web/prototypes/explorer.js`, and the Cloudflare job dropped from `deploy.yml`; the brainstorm directory confirmed on `origin/dev` (Decision 18) (C41, C45).
4. Design row 22: code AGPL-3.0, data CC BY-SA 4.0 covering our selection, arrangement and computed fields only, from the change forward; earlier releases keep MIT and CC BY 4.0; `LICENSE`, `README.md`, `CITATION.cff`, and the licence text in `METHODOLOGY.md` and `METHODOLOGY.pt.md` (and their `web/` copies) (Decision 17); the Cordis MIT notice kept.

**Interfaces:**
- Consumes: every bot-written path landed by A2, B2, B3, D, E1, E2; C1's method sources.
- Produces: the final `git add` line of `.github/workflows/refresh.yml` and its `check_page.mjs` check; none consumed by a later group.

**Acceptance Criteria:**
- [ ] SC-22: The verdict file and the four owner-reviewed lists (`dossier.pt.json`, `dossier-x-figures.json`, the `skeptic[].by` disposition list, `removals.json`) are never in the bot's staging set, and `mastodon-links.json`, `story-aliases.json`, `dossier-gone.json`, `web/hype.json`, the story-id archive and `web/ledger/ots/` are. **Proof:** the `git add` line of `.github/workflows/refresh.yml`, checked by `node scripts/check_page.mjs` in CI.
- [ ] SC-24: `docs/ROADMAP.md` records D5 as "several static pages", D2 as GitHub Pages only, D3's revisit text and P4 as the ledger on Pages plus inputs on dated Releases (no R2), line 3 with the dehype briefing on several static pages as the first public surface, and lists S2-S6 and G1 with their deferred questions (O12, O6, O4b, O16, A10, and O30 for S5), S5 naming the recompute verifier and its inputs. **Proof:** the merged diff of `docs/ROADMAP.md`, whose D2, D3 and P4 lines name neither Cloudflare nor R2 object storage.
- [ ] SC-21, licence part: `node scripts/check_page.mjs` fails a build whose method page lacks the licence text in either language.
- [ ] SC-23 (evidence collected during the clock, see QA): The day's briefing, gauges and feed are live on Pages by 06:00 America/Sao_Paulo on scheduled runs, with the window end printed in BRT (C12). **Proof:** the Pages deploy times of the first 7-10 scheduled runs, recorded with the cron re-fit in the wish.

**Validation:**
```bash
set -e
python3 -m unittest discover -s tests
node --test tests/dehype_stale.test.mjs
python3 eval.py --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json
python3 eval.py --issue11-smoke --features tests/fixtures/features_a.json tests/fixtures/features_b.json --hype tests/fixtures/hype_small.json --compare-v2
node scripts/check_page.mjs
grep -q "cron: '45 7 \* \* \*'" .github/workflows/refresh.yml
if grep -qi 'cloudflare' .github/workflows/deploy.yml; then echo 'cloudflare job still present' >&2; exit 1; fi
grep -q 'GNU AFFERO GENERAL PUBLIC LICENSE' LICENSE
cmp METHODOLOGY.md web/METHODOLOGY.md
cmp METHODOLOGY.pt.md web/METHODOLOGY.pt.md
git cat-file -e origin/dev:.genie/brainstorms/open-ai-reality-media/DRAFT.md
```

> C3 notes for F (from the C3 review): (1) before public launch, vendor transformers.js 4.2.0 and its onnxruntime wasm files into `web/vendor/` with integrity hashes, so the search by meaning (`web/dehype.js` `TF_URL`, today pinned on jsDelivr and loaded only after the reader selects it) no longer pulls code from a CDN; (2) the refresh cron (06:17 BRT today) runs after the 06:00 BRT deadline that `dehype.js` staleSince applies (C37), so the briefing reads "stale since" each morning until F moves the cron ahead of 06:00; (3) `web/og.png` is still the old observatory art (the `og:image` URL already points at the dehype Pages site).

F record (filled by the F worker, 2026-10-17):
- Workflow change, not applied (owner approval pending): `.genie/wishes/dehype-s1/f-workflow.proposed.diff`, applied after `e-workflow.combined.proposed.diff` (`patch -p1` from the repository root, both in order; `actionlint` passes on the result). It moves the cron to `45 7 * * *` (04:45 BRT), drops the Cloudflare job (its `env`, header and the refresh's `secrets: inherit`, which only that job used), splits "Commit snapshot" into a no-secret commit, replay and recheck step and a push step that holds `PUSH_TOKEN` and runs git alone (hooks, credential helper and fsmonitor off; an earlier step that ran third-party code can still write `$GITHUB_ENV` or `$GITHUB_PATH`, which this step inherits, and only a separate push job would close that); it changes nothing in `ci.yml`. The staging-set check needs no new CI step: it runs inside `node scripts/check_page.mjs`, which CI, the refresh Gate and the deploy already run.
- Staging set (SC-22): `check_page.mjs` reads every `git add` and `git commit` in `refresh.yml`: each staged path must be bot-written (an owner-reviewed file, a flag, glob or directory fails), and each output of a step the workflow runs must be staged, so `web/ledger` is required once `scripts/manifest.py daily` is wired. On the workflow with both diffs applied the staged set is exactly the SC-22 list (14 paths over 2 `git add` lines). `tests/test_pulse.py`'s two workflow-shape tests now hold before and after the diffs (a second `git add` line may only re-stage the recomposed feeds; every deploy job runs the owner-file check before the page check).
- Vendored search code (C3 note 1): **deferred**: GitHub push protection flags a pattern ("Mistral AI API Key") in the minified `@huggingface/transformers` 4.2.0 browser bundle; the orchestrator will not bypass secret scanning, so vendoring needs an owner decision (for example an allow-listed false positive, or another bundle). Until then `web/dehype.js` keeps loading the exact-pinned transformers.js 4.2.0 from jsDelivr after a click, now with `device: 'wasm'`, and `check_page.mjs` keeps its single pinned `import(TF_URL)` rule and narrow jsDelivr exception. Measured for the deferred change: the plain `ort-wasm-simd-threaded` pair works in Chrome with every host but the site and Hugging Face blocked; vendoring would add 13,879,203 bytes to the site and 4,173,190 bytes as git objects. No commit on this branch contains the bundle.
- Licence (row 22): `LICENSE` is the GNU AGPL-3.0 text verbatim (SHA-256 0d96a4ff...abcb0); `CITATION.cff` names `AGPL-3.0-only` and `CC-BY-SA-4.0` and drops `version: 2.0` (the last MIT release); the effective point is "the commit that replaced the MIT `LICENSE`", so every earlier commit and the 2.0 release keep MIT and CC BY 4.0.
- Deferred to the workflow approval: the cron and Cloudflare greps of the Validation (they pass on the scratch tree with both diffs applied), SC-23 (deploy times of the first 7-10 scheduled runs and the cron re-fit, recorded here once collected), and the "stale since" banner each morning, which stays until the cron moves.
- Owner setting, not a workflow edit (B2 residual): protect `dev` with a ruleset requiring a pull request and the `ci` check for people, the refresh's bot push the only bypass; the refresh's own deploy has no `before` commit and checks only the bot's commit, so without it a direct push the deploy refused would be published by the next refresh (`docs/ARCHITECTURE.md` section 2).

- Review repair (2026-10-18, code FIX-FIRST, proposal SHIP): the staging rule now reads shell words with their quotes removed (a word with `$`, a backtick or a backslash fails) and matches `git [-C dir|-c k=v|--opt] add|stage` and the same forms of `git commit` (no `-a`, `--all`, `--include`, `--only` or pathspec, after `--` included); each bypass the review named passes the 892a95b gate and fails this one. `og.png` rows read "proposed · not reviewed" over coverage bars, with the five labels only as a small legend. The push-token text (here, `docs/ARCHITECTURE.md` and the proposal's header) names what the split does not isolate: `github.token` as the fallback `GH_TOKEN` of "Fetch and score" and in the `gh release` steps, and `$GITHUB_ENV`, `$GITHUB_PATH` and `.git/config` (`include.path`, `url.*.insteadOf`) written by an earlier step; the full fix, a separate push job fed a git bundle, is future work. `dehype.js` passes `device: 'wasm'`. Vendoring was then dropped from F (see above); this branch is one squashed commit. To stay within 25 files the `docs/PUBLISHING.md` and `docs/SIGNALS_PLAN.md` corrections are folded into a "Superseded statements" section of `docs/ROADMAP.md` (linked from the README's launch-plan link); editing those two files in place is a two-file follow-up. Licence: AGPL-3.0-only, flagged to the owner by the coordinator.

**depends-on:** E2

---

## QA Criteria

_What must be verified on dev after merge. The QA agent tests each criterion._

- [ ] Functional: after each group merges, the next scheduled or manual refresh on `dev` passes and `node scripts/check_page.mjs` exits 0 on the deployed `web/` tree.
- [ ] Functional (A2, B3, D): the refresh run log shows the Mastodon check's pass and fail counts and time cap, the recheck's checked, removed and unreached counts and time cap, and the Cordis step's duration (SC-5, SC-13, SC-17).
- [ ] Integration (E1): `gh attestation verify` on the day's manifest exits 0, and the day's ledger SHA256 equals the Release asset's (SC-18).
- [ ] Integration (E2): the day N-1 proof, pending when published, reads "anchored" with its block height in the ledger entry of day N+1, with `web/ledger/ots/` holding the upgraded file and no earlier ledger entry changed (SC-18).
- [ ] Integration (C1, F): a refresh run leaves `web/METHODOLOGY.md` and `web/METHODOLOGY.pt.md` byte-equal to their root sources (SC-21).
- [ ] Integration (F): the Pages deploy times of the first 7-10 scheduled runs and the cron re-fit are recorded in this wish (SC-23).
- [ ] Integration (F): the merged diff of `docs/ROADMAP.md`, whose D2, D3 and P4 lines name neither Cloudflare nor R2 object storage (SC-24).
- [ ] S1 clock (SC-26): the 14 entries in `web/ledger/index.json`, the first from a run whose log shows each per-deploy check passing; `git log -- web/verdicts.json` over those dates; the owner's final confirm recorded in this wish.
- [ ] Regression: `web/data.json`, the Papers and Repos data and the observatory explorer (`web/prototypes/`) keep working; every console URL and tab anchor in use today still resolves (SC-20); the semantic search index still builds in `ci.yml`'s search-index job.

---

## Assumptions / Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| The Decision 13 measurement deadline is missed: dossier posts leave `pulse.py`'s 30-day window by about 2026-11-06, and the `history-38948143514` artifact expires 2026-11-15 19:14 UTC | High | A1 is first and carries the measurement as a deliverable; the artifact is downloaded into the gitignored `history/` of the A1 worktree and never committed; if A1 slips, the operator takes the measurement alone before the date and A1 records it |
| Insertion estimates are judgement, not measurement (C2 nearest the band, about 1,800) | Medium | Admission re-estimates each group; a group over 25 files or 2,000 insertions becomes a sibling group (for C2, `web/hype.html` plus row 13 move to their own group) |
| Admission may not accept Decision 19's exclusion of regenerated data files and lockfiles (E2's lockfile is 875 lines) | Medium | Each PR lists the excluded files with their line counts; even counted, E2 holds little else and stays under 2,000 |
| Design Risks 1-13 (DESIGN.md lines 133-145): UNVERIFIED-heavy days, public history keeps old handles, Mastodon ids resolve to authors, the X collection route, FALSE/PUSHED legal exposure, missing 06:00, Cordis receipts and licences, render-check flakes, moving story ids, offline `official` false, the fold's size, Reddit/Telegram terms, the unmaintained `opentimestamps` client | per design | Mitigations as written in the design; legal exposure (Risk 5, High) is held by B2 publishing the reply and corrections path before any FALSE row |
| (E2) The pinned `opentimestamps` 0.4.9 tree carries npm advisories: `request` SSRF and `form-data` critical, `qs`, `tough-cookie`, `uuid`, `bn.js` moderate, `elliptic` low; npm offers no fix but a downgrade | Medium | Runs only on the runner in two time-capped refresh steps with no secret or token in their environment; contacts only the default aggregators, whitelisted calendars and `https://blockstream.info/api`, each call under a 45 s deadline and the upgrade loop under a 150 s budget; no multipart body, cookie jar or caller-buffer uuid is used, and the bitcore/bn.js/elliptic code is reached only by the client's printable tree, never called; recorded in `scripts/checks/licence-closure.json`; a replacement no-fee client under A7 if one is needed (design Risk 13) |
| Most groups share `check_page.mjs`, `pulse.py`, `strings.json` and the workflows | Medium | Strictly sequential execution (Decision 2); each worker branches from the previous group's merge on `dev` |
| The rebuild data can be stale: the only successful refresh artifact is still run 38948143514 (2026-10-16) and `pulse.py` uses wall-clock `NOW`, so a rebuild days later can leave the 24h window thin in the committed `pulse.json` | Low | The next scheduled refresh replaces it; each group's PR states the artifact run id it rebuilt from |
| `web/index.html` stays the console until C3; a long gap between C2 and C3 leaves new pages unlinked | Low | C2's pages are reachable by URL; C3 follows directly |
| The Cloudflare mirror lacks `METHODOLOGY.pt.md` between C1 and F | Low | The owner dropped Cloudflare; F removes the job (Decision 8) |
| Trust-boundary edits (workflows, `LICENSE`, `CITATION.cff`) in ten of twelve groups | Medium | Plan route for those groups; each workflow edit reviewed as such; actions pinned by commit SHA as in today's workflows |

---

## Review Results

_The read-only reviewer returns evidence; the invoking orchestrator appends a timestamped block here after plan, execution, and PR reviews._

### Plan review 1 — 2026-10-17T12:12:15Z — FIX-FIRST
Reviewer: Claude (claude-opus-5-5), independent read-only plan reviewer subagent. Reviewed sha256 3f04506b…421bc8 at HEAD 2bc0ace. Ran unittest (74 tests), check_page.mjs, both eval.py commands: exit 0. Findings: HIGH pulse.json rebuild path missing; MEDIUM interim stale briefing; MEDIUM fixtures could pass for the wrong reason; MEDIUM group count; MEDIUM non-design global rule; LOW SC-2 overclaim; LOW undecided verify step. Repo-wide `genie wish lint` exit 1 on three pre-existing open-intelligence-observatory snapshot files, judged unrelated; this wish lints clean alone.

### Plan review 2 — 2026-10-17T12:19:14Z — APPROVED
Same reviewer, sha256 d948aeb6…fb35. All seven findings resolved; rebuild rule dry-run on a scratch copy (artifact 38948143514 → `pulse.py --offline` exit 0 → `check_page.mjs` exit 0). Two LOW notes (Decision 19 glob too broad; stale rebuild data) applied by the orchestrator after approval as wording-only edits: generated files listed by name, owner-reviewed files always counted, one risk row added.

---

## Files to Create/Modify

```
# A1
pulse.py
web/index.html                         (review repair: a story with no URL shows its headline as text, no empty posts button)
hype_build.py
web/pulse.json
web/hype.json
scripts/check_page.mjs
web/i18n/dossier-sources.json          (new)
web/i18n/dossier-x-figures.json        (new)
.github/workflows/ci.yml
tests/test_pulse.py
tests/fixtures/dossier_scrub.json      (new)
tests/fixtures/public_leaks/           (new, one fixture per rule)
.genie/wishes/dehype-s1/WISH.md        (measurement record)

# A2
scripts/check_mastodon_links.mjs       (new)
scripts/checks/package.json            (new)
scripts/checks/package-lock.json       (new)
web/checks/mastodon-links.json         (new, bot-written)
pulse.py, web/pulse.json, scripts/check_page.mjs, tests/test_pulse.py
.github/workflows/refresh.yml
.github/workflows/ci.yml

# B1
pulse.py, web/pulse.json, tests/test_pulse.py, scripts/check_page.mjs
web/briefing.json                      (new, bot-written from B1 on)
.github/workflows/refresh.yml
tests/fixtures/                        (offline-rebuild, reordered Top 10, briefing trend and shipped fixtures)

# B2
web/verdicts.json                      (new, owner-reviewed)
web/story-aliases.json                 (new, bot-written)
web/corrections.json                   (new)
web/POLICY.md                          (new)
web/POLICY.pt.md                       (new)
pulse.py, scripts/check_page.mjs, tests/test_pulse.py
tests/fixtures/                        (verdict-row fixtures, archive fixture web/ledger/ids/YYYY-MM-DD.json)
.github/workflows/ci.yml
.github/workflows/refresh.yml

# B3
web/removals.json                      (new, owner-reviewed)
web/checks/dossier-gone.json           (new, bot-written)
pulse.py, hype_build.py, web/hype.json, web/pulse.json, web/briefing.json
web/POLICY.md, web/POLICY.pt.md
scripts/check_page.mjs, tests/test_pulse.py, tests/fixtures/
history/signals.sqlite                 (Actions cache, not in the checkout)
.github/workflows/refresh.yml

# C1
web/i18n/strings.json                  (new)
pulse.py, web/pulse.json, run.py
METHODOLOGY.md
METHODOLOGY.pt.md                      (new)
web/METHODOLOGY.md
web/METHODOLOGY.pt.md                  (new, copy)
scripts/check_page.mjs, tests/fixtures/
.github/workflows/deploy.yml

# C2
web/dehype.css                         (new)
web/dehype.js                          (new)
web/stories.html                       (new)
web/output.html                        (new)
web/hype.html                          (new)
web/i18n/dossier.pt.json               (new)
web/i18n/strings.json, hype_build.py, scripts/check_page.mjs, tests/fixtures/

# C3
web/index.html
web/method.html                        (new)
web/audit.html                         (new)
web/dehype.js, web/dehype.css, web/i18n/strings.json, scripts/check_page.mjs
tests/fixtures/console_anchors.json    (new)

# D
scripts/dehype/compose.mjs             (new)
scripts/dehype/plugins/feed.mjs        (new)
scripts/dehype/plugins/frontend.mjs    (new)
scripts/dehype/package.json            (new)
scripts/dehype/package-lock.json       (new)
scripts/dehype/NOTICE                  (new)
scripts/dehype/<licence-closure audit> (new, name not fixed by the design)
web/feed.xml, web/feed.json, web/feed.pt.xml, web/feed.pt.json   (new)
tests/test_feed.py                     (new)
tests/test_pulse.py, web/dehype.js, scripts/check_page.mjs
<frontend plugin tables>               (new, paths fixed by D)
.github/workflows/refresh.yml

# E1
scripts/manifest.py                    (new)
web/ledger/index.json                  (new)
web/ledger/ids/YYYY-MM-DD.json         (new, one per day, bot-written)
scripts/dehype/compose.mjs, web/dehype.js, web/audit.html
tests/dehype_stale.test.mjs            (new)
tests/ (manifest tests and Reddit fixture)
.github/workflows/refresh.yml
.github/workflows/ci.yml

# E2
scripts/checks/package.json, scripts/checks/package-lock.json
scripts/checks/<licence-closure audit> (new, name not fixed by the design)
web/ledger/ots/YYYY-MM-DD.ots          (new, bot-written)
scripts/manifest.py, web/ledger/index.json, web/audit.html
METHODOLOGY.md, METHODOLOGY.pt.md, web/METHODOLOGY.md, web/METHODOLOGY.pt.md
.github/workflows/refresh.yml

# F
.github/workflows/refresh.yml
.github/workflows/deploy.yml
.github/workflows/ci.yml
scripts/check_page.mjs, tests/fixtures/
docs/ROADMAP.md
README.md
web/prototypes/explorer.js
LICENSE
CITATION.cff
METHODOLOGY.md, METHODOLOGY.pt.md, web/METHODOLOGY.md, web/METHODOLOGY.pt.md
```
