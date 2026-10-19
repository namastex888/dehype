# Publishing plan

How dehype goes public, what we say about it, and what we do not claim yet. Rewritten 2026-10-18; it replaces the 2026-10-16 plan (which had Cloudflare as primary host and MIT / CC BY 4.0). Owner of the plan: the delivery agent, by delegation from the repository owner. Mechanics: [ARCHITECTURE.md](ARCHITECTURE.md); sequencing: [ROADMAP.md](ROADMAP.md); method and rules: [METHODOLOGY.md](../METHODOLOGY.md), [POLICY.md](../web/POLICY.md).

Every figure below is quoted from a committed file or the live JSON, with its date. If a number is not here, we don't have it.

## 1. Hosting (final)

**GitHub Pages only**: https://namastex888.github.io/dehype/ (ROADMAP decision D2).

- Why: it is free, it was already deploying, and there is no server to run or secret to hold. `deploy.yml` is a single job.
- Vercel: rejected by the owner (its free plan's non-commercial clause and bandwidth cap).
- Cloudflare Pages: dropped by the owner (D2). The job and its secrets were removed in commit `3751100` (PR #44, 2026-10-18). There is no second host and no custom domain.
- Revisit only if traffic or a feature needs a server (D2 "revisit when").

**Licence**, from commit `4b3c830` (2026-10-18), which replaced the MIT `LICENSE`:

- Code: AGPL-3.0-or-later.
- Data (`web/*.json`, the four feeds, `web/ledger/`, the dated Release assets): CC BY-SA 4.0. This covers only our selection, arrangement and computed fields. Third-party titles, names and links keep their owners' terms.
- Earlier commits, including the 2.0 release of 2026-10-07, stay MIT (code) and CC BY 4.0 (data). Full text: [METHODOLOGY.md#licence](../METHODOLOGY.md#licence).

## 2. How it updates itself

`.github/workflows/refresh.yml`, cron `45 7 * * *` = 04:45 BRT (São Paulo is UTC-3 all year). The target is a live briefing by 06:00. That has not been observed yet: the new cron landed on 2026-10-18, so one scheduled run is on record (2026-10-18 13:18 UTC). The cron gets re-fitted after 7-10 scheduled runs.

```
 04:45 BRT  cron ─► refresh.yml (GitHub Actions)
   │
   ├─ restore pipeline state (Actions cache: history/, cache/)
   ├─ collect      run.py (arXiv, HF papers, HN, GitHub) + pulse.py (HN, Lobsters, Mastodon,
   │               Reddit via arctic-shift archive, Bluesky, newsletters, official feeds, BLS,
   │               HN hiring, Wikipedia views, the Hugging Face Hub check of release names)
   ├─ recheck      pulse.py looks up every showable stored post by id; deleted/removed ones
   │               leave (180 s cap, fail-closed: unreached posts show as counts only)
   ├─ clean        Mastodon logged-out render check; drop removals.json / dossier-gone posts
   │               from hype.json; no handles, count-only networks stay counts
   ├─ stories      pulse.py: topics, stories (events), What's new, briefing.json
   ├─ publish set  gauges + panels in briefing.json; compose.mjs (Cordis 4.0.4) writes
   │               feed.xml, feed.json, feed.pt.xml, feed.pt.json; search index
   ├─ ledger       manifest.py: day's input manifest (with the stored indicator and Hub inputs),
   │               web/ledger/<date>.json, story-id archive
   ├─ timestamp    ots.mjs: OpenTimestamps proof of the manifest SHA256 (committed pending)
   ├─ release      manifest on draft Release ledger-<date>, downloaded back, hash must match
   ├─ Gate         python -m unittest discover tests && node scripts/check_page.mjs
   ├─ commit       bot-written files only, replayed onto dev (no secret in this step)
   ├─ push         PUSH_TOKEN in this step only; git alone
   └─ Release      published on the pushed commit (never replaced)
        │
        ├─► deploy.yml ─► GitHub Pages
        ├─► attest job: Sigstore attestation of the manifest
        └─► verify-attestation job: gh attestation verify on that manifest
```

The diagram shows the logical order. In the workflow, `pulse.py` does the recheck, the handle-free build and the stories in one step, then rebuilds with `--relink` after the Mastodon render check.

If Pulse fails, the site keeps yesterday's briefing, labelled "stale since <date>" with the reason. No value carries over, and that day gets no manifest, ledger entry or Release. Any PR runs `ci.yml`, which never fetches and never deploys.

**The record as of 2026-10-18** (live `web/ledger/index.json`): 1 ledger day (`2026-10-18`), Release `ledger-2026-10-18`, manifest SHA256 `def3063d…6ed6`. The OpenTimestamps proof is still **pending**; "anchored" is written only by a later day's entry. The S1 clock needs 14 such days and the owner's confirm (wish dehype-s1, SC-26).

## 3. Launch plan

| Phase | Who | Starts when | Done when |
|---|---|---|---|
| L0 Owner test | the owner, reading it every morning | now (first ledger day 2026-10-18) | 14 entries in `web/ledger/index.json`, verdict confirms in git, the owner's final confirm (S1 pass) |
| L1 AI builders | 10-20 people who build with AI daily, invited one by one; feeds first | after about 7 ledger days, the readiness list (section 5) is green and the Portuguese text is reviewed | 5 written replies on what they read, what was wrong, what they would drop |
| L2 Wider audience | public posts | S1 passed (14 days + owner confirm) | posts out; issues triaged within 48 h |
| L3 Weekly | readers of L1-L2 | after L2 | "What moved this week" from the 7-day Stories view, 4 weeks in a row |

**Channels**

| Channel | Phase | Format |
|---|---|---|
| RSS / JSON Feed | L1 | `feed.xml`, `feed.json`, `feed.pt.xml`, `feed.pt.json` at the site root (RSS 2.0, JSON Feed 1.1). This is the main way to read it. |
| Hacker News | L2 | Show HN: "dehype: a daily AI briefing where every story shows its evidence and the record is verifiable". Link the site plus `audit.html`, and post the method in the first comment. |
| Mastodon / Bluesky | L1-L2 | the owner's own accounts: one post per day with that day's top story and its evidence state, plus a link. No thread of claims. |
| AI newsletters | L2 | a short pitch email: one paragraph, `og.png`, the feed URL, an offer of the weekly post |

The link preview is `web/og.png` (Open Graph tags in `web/index.html`). X and LinkedIn are not channels for now: we don't collect from them, and our policy never accepts them as a primary source.

**Do not claim yet**

- Don't use a "doom meter" or any "how doomed are we" dial. The Risk panel is a dated event log with no dial, and it currently reads "no qualified source" with 0 events (briefing.json, 2026-10-18). What a risk reading would even mean is an open S3 question (O12).
- Don't call dehype "the standard for the state of AI", or anything like it, before 14 ledger days and qualified S3 indicators (Risk, Jobs). Jobs also reads "no qualified source". The BLS and HN-hiring figures shown under it are context, not a forecast, and none of them attributes a change to AI.
- No gauge is "shipped". All 3 gauges read "preview, not yet reproducible" until the S5 recompute verifier passes.
- Don't say "we fact-checked N stories". `web/verdicts.json` has 0 owner rows (2026-10-18), so every story's evidence record is "proposed".
- Sampled counts are not platform totals. Missing data means unknown, not low. Scores and gaps are leads for investigation, not measures of capability, adoption, revenue or truth.

## 4. Talk track

**1-minute pitch.** Every morning dehype says what happened in AI in the last 24 hours. It's one page of the top 10 stories, in English and Portuguese, and each story shows its evidence: how many people posted it, on which networks, and whether a primary source confirms it. It shows no handles, deleted posts leave the next day, and a verdict needs a primary source and gives the subject a right of reply. Each day's inputs go on a dated GitHub Release with a Sigstore attestation and an OpenTimestamps proof, so anyone can check the record wasn't rewritten. Code is AGPL, data is CC BY-SA. It is still in its 14-day test, so the gauges are previews. Read it through the feed.

**5-minute talk**

1. (0:00-0:40) The problem. AI news is a stream of claims, and a lot of them are topics wearing an event's clothes. dehype reports events, not topics: "Claude is discussed" is not news, a release is.
2. (0:40-1:40) Demo the Briefing (`index.html`). Show the top 10 and open one story: its posts by network, counts-only rows, and an evidence state that reads "proposed" because no owner has confirmed it.
3. (1:40-2:30) Rules on the page: no handles, deleted posts leave, and when a story is mostly complaints it's listed under Complaints, not as news. Show the Stories page and Sources (`status.html`), where every source has its status.
4. (2:30-3:30) Audit (`audit.html`). Ledger entry, Release, attestation, timestamp proof. Run `gh attestation verify` live.
5. (3:30-4:20) What it is not yet: gauges are previews, Risk and Jobs read "no qualified source", there's no X data, and the sample is small and English-heavy. Say so on stage.
6. (4:20-5:00) Ask: subscribe to the feed, send corrections and replies (POLICY.md), and propose sources through issues.

**Talking points, each with its check**

| # | Claim | How anyone verifies it |
|---|---|---|
| 1 | No person handles in public data. Reddit, X, LinkedIn, YouTube, Telegram and Discord are counts only. | the "X route and public data" section of METHODOLOGY.md; `node scripts/check_page.mjs` fails the build on any of them |
| 2 | Deleted posts leave on the next daily run | refresh.yml recheck step; POLICY.md "Removal requests and deleted posts" (HN, Mastodon, Bluesky and Reddit are looked up by id) |
| 3 | A verdict needs a primary source, never an X, LinkedIn or YouTube post. FALSE is set only by the owner, by hand. | POLICY.md "Verdicts" |
| 4 | Right of reply: free, within 60 days (Lei 13.188/2015), published within 7 days of receipt | POLICY.md "Right of reply" |
| 5 | The daily record can be checked independently | `gh attestation verify manifest-2026-10-18.json.gz --repo namastex888/dehype` exited 0 on 2026-10-18 |
| 6 | Each manifest is timestamped on Bitcoin | `ots verify -f manifest-<date>.json.gz <date>.ots` against your own node (the 2026-10-18 proof is still pending) |
| 7 | Open licence: AGPL-3.0-or-later code, CC BY-SA 4.0 data | `LICENSE`; commit `4b3c830` |
| 8 | Sources are public and listed with their status | live briefing.json, 2026-10-18: HN 2,739, Reddit archive 6,160, Mastodon 1,359, Bluesky 796, Lobsters 100, newsletters 241 (partial: 3 feeds unreachable), official feeds 173 posts fetched |
| 9 | Stable ids: a story id is a hash of its source, so the data can move to another store without duplicates | METHODOLOGY.md "Data identity (stable ids)" |
| 10 | It runs with no server and no paid API: GitHub Actions plus Pages, and search by meaning runs in the browser | ROADMAP D2-D4 |

**Hard questions, honest answers**

- *Do you have X data?* Not live. The X counts in the Hype research dossier come from a 2026-10-07 research pass, and whether that used X's published interfaces, or whether a paid call was made, is not on record. We show no X post text or link. Live X waits on the owner funding the official API (status.html: "held").
- *Reddit has no free API. How do you read it?* Through the arctic-shift public archive, a third party with no uptime guarantee, and only as counts. We've asked for official API access under Reddit's Responsible Builder Policy (pending).
- *Isn't this a small, English-heavy sample?* Yes. Sources are sampled feeds, not totals. Hacker News supplies the paper mentions and most of the Hype research dossier (405 sampled posts, content cutoff 2026-10-07), and it over-represents developer tools and English. HN, Lobsters, Reddit, arXiv and GitHub publish no language, so their titles read `und`. METHODOLOGY.md "Known biases" lists the rest.
- *Can I trust the gauges?* Not yet as measurements. All 3 read "preview, not yet reproducible" until the S5 verifier can rebuild them from the Release inputs.
- *Who decides verdicts?* For now, the owner alone, by pull request. There are 0 rows so far. A wider verdict policy is S2, and governance (G1) comes later.
- *Does the timestamp prove a story is true?* No. It proves the day's inputs existed by that block's time. The refresh's own check trusts blockstream.info for the block header; `ots verify` against your own Bitcoin node removes that trust.
- *Could a compromised dependency push to the site?* The push token sits in a step that runs only git. The job token and `$GITHUB_ENV` are not fully isolated; ARCHITECTURE.md section 2 says so, and the full fix is a separate push job (future work).

## 5. Pre-launch checklist

The live state is on [Sources & roadmap](https://namastex888.github.io/dehype/status.html).

Owner actions still open:

- [ ] **GitHub token**: replace the read-only `TRENDING_GH_TOKEN` secret. Repo star data is degraded until then. Without it the job token allows about 1,000 API requests an hour; with it, 5,000 (ARCHITECTURE.md section 2).
- [ ] **Portuguese review**: a native read of every `pt` string (`web/i18n/strings.json`, `sources-plan.json`, METHODOLOGY.pt.md, POLICY.pt.md) and of the pt feeds.
- [ ] **Protect `dev`**: a ruleset that requires a PR and the `ci` check for people, with the refresh bot's push as the only bypass (ARCHITECTURE.md section 2).
- [ ] **Vendoring decision**: transformers.js stays on jsDelivr for now. Vendoring it would add 13.9 MB to the site and about 4.2 MB to git, and GitHub push protection flags a pattern in the bundle. The owner decides whether to allow-list it or pick another bundle.
- [ ] Retire the old refresher outside the repo that pushes to `main` (ARCHITECTURE.md section 2).

Before L1:

- [ ] At least 7 consecutive ledger days, each Gate green. Compare scheduled deploy times against 06:00.
- [ ] The first proof shows "anchored" on the audit page.
- [ ] The nav at 390 px does not scroll sideways, checked on a real phone.
- [ ] Every post draft has been checked against "Do not claim yet" (section 3).
- [ ] Someone other than the author reads three briefings cold and reports what confused them.

Before L2: S1 has passed (14 ledger days + the owner's confirm), all of the above is done, and this file has been re-read against the live JSON on launch day.
