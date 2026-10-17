# DRAFT: open-ai-reality-media

Round 10 (2026-10-17). Twenty-five decisions are settled (R1-1..R1-4, R2-1..R2-4,
R3-1..R3-4, R4-1..R4-3, R5-1..R5-3, R6-1..R6-3, R8-1..R8-3, R9-1, see ## Settled), plus
owner picks given outside the harness (X1-X17). R4-3 is reopened by R5-1, and R5-3 by
R8-1. The owner's round-10 request repeats the round-1 text word for word. Its run note
says the main checkout was stale at e939123 when round 9 ran check-design, and that it is
now fast-forwarded to `origin/dev`. The lead checked: `HEAD` and `origin/dev` are both
2bc0ace, so `.github/workflows/refresh.yml` exists at the repository root.

What happened after round 9 crystallized:
- DESIGN.md was written, and check-design passed. The independent design review returned
  FIX-FIRST (content SHA-256 f7f0f293...bf8d3c2). It met 14 of its 17 criteria. Three were
  not met: C5 (every DRAFT condition maps to a check), C7 (the verdict model holds across
  the 14 days) and C14 (the files and line references are accurate). The review's C1-C17
  are its own criteria, not this DRAFT's design conditions C1-C31. The ledger's review
  record lists those criteria ids next to the findings, and the DRAFT's numbering
  continues at C32. It made 15 findings
  (HIGH-1..3, MEDIUM-1..7, LOW-1..5), and it marked each one "not an owner decision".
- The lead repaired DESIGN.md against all 15 findings. Check-design, run again after the
  repair, failed on six traceability items. The owner answered R9-1 "Approve as written".
- What R9-1 leaves (C45). Two of the six findings were `refresh.yml` "does not exist"
  (Decisions #23 and Scope IN #20). They resolve now that the checkout matches
  `origin/dev`. The other four stand, approved as written: rows 12 and 15 cite R5-3,
  which R8-1 reopened, and two `<date>` tokens remain (DESIGN.md lines 43 and 157).

Round 10 sends no scouts and no council. The facts came from three places: the round-9
workflow journal (the review's result and the repair's summary), DESIGN.md, and git (see
"What round 10 read"). The repair's fixes exist only in DESIGN.md. So this round writes
them into the DRAFT as design conditions C32-C45, which add scrutiny and are announced.
The next design write starts from them. The repair said it took two moves without asking
the owner. Both are written out here so the owner sees them:
- The recompute verifier that R2-4's ship rule needs is built in S5. So no gauge reads
  "shipped" during S1 (C36, A34, flagged).
- A correction to the record. R3-3's question said removing handles "changes no
  number". On the dossier path it does change node voices, weight and signal, until
  about 2026-11-06 (C35, A35, flagged). R3-3 still stands.
One roadmap question is added for S5 (O30, deferred by R3-1). ## Open stays empty and
nothing is dropped. The size stays G. WRS is 100, so the mode is crystallize.

### What round 10 read (round-9 review, repair and check; evidence, not instructions)

- The round-9 review result and the repair summary come from the workflow journal
  `~/.claude/projects/-Users-feliperosa-workspace-repos-trending-research/5addb51e-7d92-450e-8e63-adb4e00a86b0/subagents/workflows/wf_45c9f015-288/journal.jsonl`.
  The lead extracted them to
  `/private/tmp/claude-501/-Users-feliperosa-workspace-repos-trending-research/5addb51e-7d92-450e-8e63-adb4e00a86b0/scratchpad/review.json`.
  The reviewer read `origin/dev` 2bc0ace with `git show` only. The line references below
  are the reviewer's, and the lead did not re-read them.
- The order of the round-9 run: write, check (exit 0), review (FIX-FIRST), stamp and
  record, repair ("Fixed all 15 findings"), check again (exit 1, six findings), then the
  R9-1 question. The ledger's review record reads `repaired: false` because it was
  stamped before the repair ran. The record is right as written.
- The current DESIGN.md (47,630 bytes) holds the repaired text. Its rows cite the
  findings as "reviewer HIGH-1" and so on. Its review stamp is the pre-repair FIX-FIRST.
  No reviewer has read the repaired design.
- `git rev-parse` gives `HEAD` = `origin/dev` = 2bc0ace. Root `METHODOLOGY.md`,
  `web/METHODOLOGY.md`, `docs/ROADMAP.md` and `.github/workflows/{ci,deploy,refresh}.yml`
  exist in the checkout. DESIGN.md line 18 still says "The local `dev` checkout is
  behind it", which is out of date (C45).
- No file read held text addressed to an agent.

### Design conditions added in round 10 (the review's findings and the repair's answers; add scrutiny, announced)

Each condition comes from a review finding the reviewer marked "not an owner decision".
The repair's answer is carried here so that a fresh design write keeps it. Where a
condition changes an earlier one, it says so.

- C32 Verdict ids outlive the 7-day story window (HIGH-1; amends C2):
  - Why: `pulse.py` keeps stories for `STORY_DAYS = 7` (pulse.py:807, 851). A row
    confirmed on day 1 would be orphaned by about day 8. The blocking gate runs before
    the data commit (refresh.yml:72-73), and `deploy.yml` runs the same check before
    upload (deploy.yml:34-37). So the owner's own confirms would stop the refresh during
    the 14 days.
  - Each run commits a story-id archive, `web/ledger/ids/YYYY-MM-DD.json`. It lists
    every story id that day's `pulse.json` and `briefing.json` published, and it is
    never edited afterwards.
  - `pulse.py` writes a bot-staged alias file, `web/story-aliases.json`. It compares the
    day's stories with the previous `pulse.json`: a story whose posts carry over under a
    new id maps the old id to the new one. The file stays apart from the owner-reviewed
    rows.
  - A row's `s:` id passes when it resolves to the day's `pulse.json`, to the archive, or
    through the alias file. CI fails it otherwise.
  - Fixture: a row confirmed 8 or more days earlier still passes.
- C33 Where the method text lives (HIGH-2; applies to C17, C31 and X13):
  - Why: `web/METHODOLOGY.md` is a copy. `run.py` (lines 1118-1119) and `deploy.yml`
    (lines 36 and 69) overwrite it from the root `METHODOLOGY.md` on every run, and the
    two files hash the same today.
  - The sources are the root `METHODOLOGY.md` and a new root `METHODOLOGY.pt.md`.
  - `run.py` and both `deploy.yml` sync steps copy the two files into `web/`, and
    `deploy.yml`'s push path filter (line 8) lists both.
  - The C31 disclosure check and the licence check run on the copied files.
- C34 Removal requests and deleted posts (HIGH-3). This restores the round-3 condition "a
  documented takedown path that also honours deleted posts" (under round-3 scout 3, Source
  terms). The round-9 design dropped it without notice.
  - `web/POLICY.md` and `web/POLICY.pt.md` say how a person asks for removal.
  - A post whose source reports it deleted or removed on any fetch leaves the pages,
    `pulse.json`, `briefing.json` and the feeds on the next daily rebuild. So does a
    post that a removal request names. The deletion signals are HN `deleted` or `dead`,
    Reddit `[deleted]` or `[removed]`, and a Mastodon or Bluesky not-found.
  - Requests are recorded in an owner-reviewed list, `web/removals.json`, which the build
    applies.
  - The policy states a limit, as the Reddit hash rationale does: committed git history
    and the anchored manifests cannot be edited.
  - Checks: CI checks the policy keys in both languages, and a fixture shows a deleted
    post leaving the built pages.
- C35 What the scrub changes in the counts (MEDIUM-1; corrects the record, see A35):
  - Why: `pulse.py` reads the public `hype.json` and counts dossier `(net, author)`
    pairs as node voices (pulse.py:311-318, 547-549), and voices feed weight
    (pulse.py:596). After the scrub, X, LinkedIn and YouTube dossier posts have no
    `url`, so `pulse.py` skips them (line 314). HN dossier posts lose `au`, so their
    voices merge.
  - So node voices, weight and signal in `pulse.json` change until the 2026-10-07
    dossier posts leave the 30-day window (pulse.py:477), about 2026-11-06.
  - The wish measures the change on the 2026-10-16 snapshot, before and after the scrub,
    and the method page states it in both languages.
  - Count-only dossier records are placed on a topic node by `PROJECT_TOPIC`, not by
    text matching, because they have no text left.
  - `tests/test_pulse.py` covers both behaviours in its scrub test.
- C36 Gauge "shipped" and the recompute verifier (MEDIUM-2; see A34 and O30):
  - Why: R2-4's ship rule needs "a green recompute verifier", and no S1 row built one. The
    design also never said what the verifier would recompute from.
  - The verifier is built in S5, the audit trail. Its roadmap entry names its inputs:
    the dated Release's manifest plus a numbers-only gauge-input asset (each story's
    computed fields and the per-area output counts the gauges were built from).
  - In S1, every gauge carries "preview, not yet reproducible", and no gauge reads
    "shipped". CI fails a fixture `briefing.json` that marks a gauge shipped.
  - Trends still follow R2-4 as recorded: no trend line or arrow before 14 ledger days.
- C37 Stale shown in the browser (MEDIUM-3; extends C5 and C12):
  - Why: a dropped or late schedule, or a failed gate, Cordis or commit step, commits
    nothing (refresh.yml:72-92). The site would then show yesterday's briefing with no
    stale marker.
  - `dehype.js` compares the briefing's `generated_at` with the current time. A briefing
    older than the last 06:00 America/Sao_Paulo deadline reads "stale since" and its
    date, even when no run committed or deployed.
  - Fixture: a briefing dated the previous day, viewed after 06:00, reads stale.
- C38 OpenTimestamps upgrade and verify route (MEDIUM-4, LOW-4; extends C4):
  - The day's proof is committed as `web/ledger/ots/YYYY-MM-DD.ots` while still pending.
  - Each later refresh upgrades every proof there that is still pending, and commits the
    upgraded file in place. The date and Bitcoin block height go into that run's own
    ledger entry, so earlier entries are never edited.
  - The audit page reads "anchored" for a date only once a ledger entry records its
    block. Until then it reads "pending".
  - A proof from day N-1 reading anchored on day N+1 is evidence collected during the
    clock. It is not a condition for starting it (C39).
  - Verify route: the repair names the JavaScript client `opentimestamps`, pinned exactly
    to 0.4.9. The repair says its `verify` falls back to public block explorers when no
    Bitcoin node is reachable, while the Python client needs a local Bitcoin Core node.
    No round-10 read confirms this. The design write confirms it from the package
    before naming the route. Otherwise it names another no-fee route (A7).
  - The method page names the route, says that it trusts the explorers, and says anyone
    with a node can run `ots verify`.
- C39 What starts R3-2's clock (MEDIUM-5; makes the R5-1 reading of the clock start exact):
  - The clock starts on the first scheduled run whose log shows each per-deploy check
    passing:
    - `python -m unittest discover tests`;
    - `node scripts/check_page.mjs` on the built site;
    - `tests.test_feed` on the four feeds;
    - the manifest check in `scripts/manifest.py`;
    - `gh attestation verify` on the day's manifest;
    - a ledger hash equal to the Release asset's (a proof reading "pending" passes).
  - Some criteria need several runs or a merge: the 06:00 deploy times over 7-10 runs, the
    anchored-on-N+1 proof, and the merged `docs/ROADMAP.md` diff. They are evidence
    collected during the clock.
- C40 Append-only corrections and "not fetched" everywhere (MEDIUM-6; C11, C7):
  - CI compares `web/corrections.json` with the base commit, and fails when an existing
    entry is edited or removed.
  - The C7 fixture also covers the gauge values in `briefing.json` and the feed items,
    not only the evidence records.
- C41 Roadmap records (MEDIUM-7; with O11 and R1-4). `docs/ROADMAP.md` gets more than the
  D5 amendment:
  - D2 becomes GitHub Pages only, with the Cloudflare job dropped.
  - D3's revisit text and P4 become the ledger on Pages plus inputs on dated Releases,
    with no R2 object storage (R2-3).
  - Line 3 names the dehype briefing on several static pages as the public surface that
    comes first.
  - The reviewer's lines are docs/ROADMAP.md:3, 10, 11, 13 and 26. The proof is the merged
    diff, in which D2, D3 and P4 name neither Cloudflare nor R2.
- C42 Attestation in its own job (LOW-1; with C4):
  - The Sigstore attestation runs in a separate job (`needs: refresh`). It has only
    `id-token: write` and `attestations: write`, and gets the manifest as an artifact.
  - So no attestation token sits beside `npm ci` and pip code. The refresh job keeps
    `contents: write` (refresh.yml:11-12).
- C43 Pins and feed assertions (LOW-2, LOW-3; with C25 and C1):
  - The render check's browser is `playwright-core`, pinned exactly to 1.59.1 with a
    lockfile under `scripts/checks/`, running the Chromium build that version installs.
  - `tests/test_feed.py` names each required element it asserts:
    - RSS 2.0: channel `title`, `link` and `description`, and per item a `title` or
      `description` plus a `guid`;
    - JSON Feed 1.1: `version` (the 1.1 URL), `title`, `items`, and per item `id` plus
      `content_html` or `content_text`;
    - in both: the stable id, the verdict state and the source links (C1).
- C44 Staging set, amended (HIGH-1, HIGH-3; amends the round-9 staging set):
  - `web/removals.json` is owner-reviewed. It enters only by a merged PR and is never in
    the bot's staging set.
  - The bot does stage `web/story-aliases.json`, `web/ledger/ids/` and the upgraded
    proofs under `web/ledger/ots/`.
  - The `git add` line of `refresh.yml` is checked by `scripts/check_page.mjs` in CI.
- C45 Records and traceability (LOW-5 and R9-1):
  - The brainstorm directory `.genie/brainstorms/open-ai-reality-media/` is committed
    with the design, so the DRAFT it cites exists on `origin/dev`.
  - Outside picks are cited by X id.
  - Rows that rest on the two-language rule cite R8-1, the current answer, as
    check-design requires. Their prose says that R5-3 holds as R8-1 narrowed it.
  - Paths and strings carry no placeholder token: a dated file is spelled
    `YYYY-MM-DD`, and the stale text is written as "stale since" followed by the date.
  - The local-checkout sentence is updated: the checkout matches `origin/dev` since
    round 10.
  - These are fixes of form, and they change no decision. If the design write leaves the
    four findings as they are, R9-1 has already approved them as written.

Round 9 header, kept for the record (2026-10-17). Twenty-four decisions are settled (R1-1..R1-4, R2-1..R2-4,
R3-1..R3-4, R4-1..R4-3, R5-1..R5-3, R6-1..R6-3, R8-1..R8-3, see ## Settled), plus owner
picks given outside the harness (X1-X17). R4-3 is reopened by R5-1, and R5-3 by R8-1. The
owner's round-9 request repeats the round-1 text word for word, so this round works from
the three round-8 answers, all of them the recommended options:
- R8-1 "English first, PT later" (reopens R5-3): dossier prose ships in English under a
  Portuguese notice, and each dossier gains Portuguese once the owner has reviewed it.
- R8-2 "Handle-free link, else count": Mastodon posts link to
  `mastodon.social/statuses/<id>` once a logged-out browser check shows the post, and
  show as a count otherwise.
- R8-3 "Counts only, no X text": X, LinkedIn and YouTube appear in `hype.json` and
  `pulse.json` as counts only.
Round 9 sends no scouts and no council. The lead read `origin/dev` (2bc0ace) `web/hype.json`
and `pulse.py` directly to write the conditions these answers need (under "What round 9
read in the repository"). The read found that R8-3 and R3-3 reach further into
`hype.json` than the round-7 counts showed: 195 more X links in citation and "viral"
fields, 81 candidate-account fields, and 22 `skeptic[].by` values with an `@handle`. It
also corrects the record: the dossier's own notes name part of the X route ("x_search"
reports, "X syndication" readbacks). Every one of these falls under a settled answer read
as written. Eight design conditions are added and announced (C24-C31), and C17 is amended
by C24 to follow R8-1. ## Open is now empty. The closed-question records and O11 move to
their own headings, unchanged (announced). Nothing is dropped, and the size stays G. WRS
100: the design can be written from Settled answers alone, so the mode is crystallize.

Round 8 header, kept for the record (2026-10-16). Nothing new was settled since round 7: the ledger refused the
round-7 batch, so ## Asked is empty and no O27-O29 answer exists. The refusal was on
O27's form. A reopen question must quote the Settled answer verbatim in quotation marks,
then → and the new text. R5-3's recorded answer is "Our text, headlines original
(Recommended)", and the round-7 text quoted it without "(Recommended)". The owner's
round-8 request repeats the round-1 text word for word, and its round note asks to re-ask
O27, O28 and O29 from the facts already here. So round 8 sends no scouts and no council.
It re-asks the same three decisions with the same options and facts, and fixes only the
form:
- O27 reopens R5-3 and quotes "Our text, headlines original (Recommended)" → the new
  text, once for each reopen option. The text after each → matches that option's label.
- O28 and O29 are not reopens. Handles stay removed in every option (R3-3), so they
  carry no reopens field.
Nothing is dropped, no condition is added, the size stays G, and the WRS stays 95.

Round 7 header, kept for the record (2026-10-16). Twenty-one decisions are settled (R1-1..R1-4, R2-1..R2-4,
R3-1..R3-4, R4-1..R4-3, R5-1..R5-3, R6-1..R6-3, see ## Settled), plus owner picks given
outside the harness (X1-X17). R4-3 is reopened by R5-1. The owner's round-7 request
repeats the round-1 text word for word, so this round works from the three round-6
answers, all of them the recommended options:
- R6-1 "New today first": the Top 10 takes stories first seen in the last 24h, ranked by
  heat, then fills from the rest by heat.
- R6-2 "Counts only, no text": no Reddit title, permalink or username on any public page
  or in `pulse.json`. Reddit shows up as a count only.
- R6-3 "Fold into dehype": the five-tab console becomes dehype pages in the Mission
  control look, in English and Portuguese.
The lead read `origin/dev` (2bc0ace) directly for what the fold reaches (under "What
round 7 read in the repository"). The fold brings three things no settled answer covers:
- About 17,700 words of our own dossier prose. R5-3 was asked with about 3,000 words of
  page text plus a 6,760-word method page.
- Post links that carry the author's handle inside the URL (Mastodon, X), which R3-3's
  handle removal did not address.
- 125 X posts (text excerpts, likes, views, handles) in the Hype dossier. The
  repository records X access as "BLOCKED: paid_access_unapproved", and how the dossier
  read those posts is not on record.
Round 7 sent one read-only worker scout: X's terms for post text, counts and links, and
which networks offer a post link without a handle. It reported (findings under "What
round 7's scout found"), and the lead made three more reads of `origin/dev` after it. The
round-7 batch, written after the report, asks three owner decisions:
- O27, a reopen of R5-3: what Portuguese covers for the dossier prose.
- O28: how Mastodon post links appear when their URL carries the author.
- O29: what X content (and the dossier's LinkedIn and YouTube posts) appears on the
  public files.
Five design conditions are added and announced (C19-C23). The roadmap list deferred by
R3-1 moves out of ## Open to its own heading, unchanged (announced). Nothing is dropped,
and the size stays G.
Correction to the pre-report header: the X posts reach `pulse.json` today, not only the
Hype page. `pulse.py` reads every dossier post from `web/hype.json` (pulse.py:311-318), and
29 X entries with excerpts and like counts sit in the topic nodes. So O29 covers both files.

Round 6 header, kept for the record: eighteen decisions were settled (R1-1..R1-4, R2-1..R2-4,
R3-1..R3-4, R4-1..R4-3, R5-1..R5-3, see ## Settled), plus owner picks given outside the
harness (X1-X17). R4-3 is reopened by R5-1. The owner's round-6 request repeats the
round-1 text word for word, so this round works from the three round-5 answers, all of
them the recommended options:
- R5-1 "Qualified Cordis API now" replaces R4-3 "Cordis now, S1 waits". The S1 delivery
  gate is gone, and R3-2's 14-day clock can start.
- R5-2 "Hash per record only": no Reddit identifier, permalink, title or handle enters the
  public input manifest.
- R5-3 "Our text, headlines original": our own text ships in English and Portuguese, and
  headlines stay in the language they were posted in.
Round 6 sends no scouts and no council. Three direct reads of `origin/dev` (2bc0ace, the
`pulse.json` of 2026-10-16T21:56Z) gave the facts this round needed (under "What round 6
read in the repository"). One of them overturns a round-5 default: under the heat rule,
none of the Top 10 stories was first seen in the last 24h. The round-6 batch asks three
owner decisions: the Top 10 ranking rule (O24, now with a different recommendation),
Reddit titles on the public pages (O25, the item R5-2 left flagged), and what happens to
today's five-tab console (O26). Three design conditions are added and announced (C16-C18).
Nothing is dropped, and the size stays G.

Round 5 header, kept for the record: fifteen decisions were settled (R1-1..R1-4, R2-1..R2-4, R3-1..R3-4,
R4-1..R4-3, see ## Settled), plus owner picks given outside the harness (X1-X17). The
owner's round-5 request repeats the round-1 text word for word and adds three outside
picks, recorded below as X15 (English + Portuguese from day one), X16 (briefing ready daily
at 06:00 BRT) and X17 (Top 10 stories, the rest one click away). So this round works from
the three round-4 answers and X15-X17. R4-1 and R4-2 took the recommended options. R4-3
did not: the owner picked "Cordis now, S1 waits", so the first release is gated on an item
the repository's own record calls BLOCKED, with no date on record. Round 5 sent four
read-only scouts and no council; all four reported (findings under "What round 5's scouts
found"). The round-5 batch, written after the reports, asks three owner decisions: what S1
does under the Cordis gate, as a reopen of R4-3 (O22); how Reddit appears in the public
input manifest (O21); and what Portuguese covers (O23). The Top 10 ranking rule (O24)
waits under Open with a design default. Nothing is dropped and the size stays G. Correction
to the pre-report header: no scope item was added for X15. X15 is carried as an outside
pick, with C12-C13 and O23, and the Scope ratchet is unchanged this round.

Round 4 header, kept for the record: twelve decisions were settled (R1-1..R1-4, R2-1..R2-4, R3-1..R3-4,
see ## Settled). The owner also gave picks outside the round harness (X1-X14 below); they
are owner input, not lead assumptions, but the ledger does not hold them. The owner's
round-4 request repeats the round-1 request word for word; nothing new was said, so this
round works only from the four round-3 answers. R3-1 put S1 in testable detail and the
rest on a roadmap, so the Open list is now split: what blocks a testable S1 stays under
Open, and the roadmap pillars' questions move to a labelled "Roadmap decisions, deferred
by R3-1" list (announced below; nothing is dropped, and the owner still sees all of it).
Round 4 sent three read-only scouts and no council; all three reported (findings under
"What round 4's scouts found"). The round-4 batch, written after the reports, asks three
owner decisions: how the pipeline proposes a verdict (O20), the false-claim label (O17),
and Cordis timing for the feed adapter (O15). The scouts closed two fact gaps (the
production Pulse run is live; tests do not assert on `author`) and mastodon.social. Reddit
is not closed: its terms read against open redistribution, and the two documents that
decide whether ids and permalinks may be published as pointers (Public Content Policy,
Developer Documentation) are still unread. It stays under Open as O21, a fact read first,
asked once those are read. Two design conditions were added and announced (C7, C8).

Round 3 header, kept for the record: round 3 sent four read-only scouts and asked O18,
O8, O13 and O14; the owner answered all four (R3-1..R3-4).

### What round 8's answers mean for the design (read from the recorded question and label)

The ledger holds each question's text and the picked label only, so these readings rest on
the question text, the label, and the option text the DRAFT recorded under O27-O29.

- R8-1 "English first, PT later" (reopens R5-3). R5-3 still holds for everything else:
  page chrome, gauge names, labels, the method page, policy pages, feed item chrome and
  the owner's verdict reasons are in English and Portuguese, and headlines stay as posted.
  The dossier prose is the exception (the ten prose fields counted in round 7, 17,667
  words). On the Portuguese Hype page each dossier's prose shows in English under a
  Portuguese notice, until the owner has reviewed that dossier's Portuguese draft. The
  agent drafts, and the owner's merge of the draft's PR is the review (X7). S1's checks
  and R3-2's 14-day clock do not wait on any dossier review. A new research pass that
  changes a dossier's English prose sends that dossier back to English under the notice,
  until its new draft is reviewed (C24).
- R8-2 "Handle-free link, else count". A Mastodon post in our public files links to
  `mastodon.social/statuses/<id>`, where `<id>` is mastodon.social's own status id. The
  fetcher already holds that id (pulse.py:115) for posts from all 31 servers, and the
  design carries it into `pulse.json`. The origin server's `@user` URL is never
  published. A post links only after a logged-out check in a real browser has shown it.
  A post the check has failed on, or not yet run on, shows as a count. The post text,
  network and date show beside the link, as they do today. The dated manifest carries the
  handle-free URL for every Mastodon record, because it passes C22 whatever the render
  check finds: the check decides what the page shows, not what the manifest points at.
  The option's trade-off stands as stated: the id resolves to the author through
  Mastodon's public API, as HN item ids do today (C25).
- R8-3 "Counts only, no X text". In `hype.json` and `pulse.json`, an X post shows only as
  a count: how many X posts our sample holds for a project, or how many X entries a topic
  node's spread holds. No excerpt, handle, link, likes, replies or views appear. The
  question said the answer also covers LinkedIn (6 dossier posts) and YouTube (4), and
  that under an option with links a LinkedIn or YouTube post keeps a link where its URL
  names no account. "Counts only" has no links, so LinkedIn and YouTube are counts only
  too. "No link" covers every X status link in the two files, not only `posts[]`: the
  citation and "viral" fields read this round hold 195 more (C26). The claim a citation
  supports stays, citing "an X post", with no link. This is the reading R6-2 already set
  for Reddit citations. The project's own X profile link (`links.x_handle`, A26) stays,
  as the question said. The sentences in our prose that quote an X figure are listed and
  follow the same rule (C27). The trade-off the owner accepted stands: the counts and the
  attention scores built from these posts keep a collection route the record holds only in
  part, and the method page says so (C31).

### Design conditions added in round 9 (add scrutiny, announced)

- C24 Dossier prose in Portuguese (R8-1; amends C17, whose "every string has an `en` and
  a `pt` entry" no longer holds for dossier prose):
  - C17 still fails a missing or empty `pt` key for all our other text.
  - Reviewed Portuguese dossier prose lives in a committed file,
    `web/i18n/dossier.pt.json`, because `hype.json` is rebuilt from a gitignored input.
    Each entry is keyed by item slug, field path and the SHA256 of the English text it
    translates, and it carries `reviewed_in`, the number of the merged PR that brought it.
  - The build shows a Portuguese entry only when its hash matches the current English
    text. Otherwise it shows the English under a fixed Portuguese notice ("Texto do
    dossiê em inglês; a versão em português aguarda revisão"), whose wording is our text
    under C17.
  - CI fails a `dossier.pt.json` entry without `reviewed_in`, and fails a Portuguese page
    that shows dossier prose with no notice and no matching entry.
  - No S1 acceptance check and no step of R3-2's clock reads `dossier.pt.json`.
- C25 Mastodon links (R8-2):
  - `pulse.json` carries mastodon.social's status id per Mastodon record and the URL
    `https://mastodon.social/statuses/<id>`. No origin-server URL is published. C22 still
    fails any `/@` path segment.
  - The render check is per post. It loads the URL in a headless browser with no
    cookies and no login. It passes when the rendered page shows a status whose text is
    not empty, and it fails on a not-found page, a login wall, or an empty app shell after
    a fixed wait. The browser is a free CI dependency (A7 holds).
  - Results are cached in a committed file, `web/checks/mastodon-links.json` (id, check
    time, pass or fail). A passed post is checked again after 7 days while it is still
    shown.
  - The check is fail-closed. It runs with a time cap inside C12's 15-minute margin, and
    a post it did not reach shows as a count. CI fails a Mastodon link on a page or in a
    feed whose id has no passing check younger than 7 days.
  - The manifest carries the handle-free URL for every Mastodon record (R2-3, A17).
- C26 X, LinkedIn and YouTube counts only, both files (R8-3, with C22 and C23):
  - `pulse.py` (the dossier copy at lines 311-318) copies an X, LinkedIn or YouTube
    dossier post as a count-only record: its network and its project or node. It carries
    no `title`, `author`, `url`, `score` or `comments`, and no `id` built from the URL
    (today the post id is the URL itself, pulse.py:317).
  - In `hype.json`, `posts[]` keeps per network only the count for these three networks.
    Every X, LinkedIn or YouTube status link leaves the citation fields
    (`summary_urls`, `status_urls`, `first_seen_url`, `skeptic[].url`, `traction[].url`,
    `coord.evidence[].url`) and `viral.cand_post`. The claim each one supports stays, with
    "an X post" (or LinkedIn, or YouTube) in place of the link.
  - A `traction[]` row whose source is an X post (5 rows in 4 items) keeps its type,
    unit, `ver` and date. Its value reads "figure from an X post, not shown".
  - CI fails any `x.com` or `twitter.com` URL in either file, the pages or the feeds,
    except a profile URL in `links.x_handle`. It fails a `linkedin.com` or `youtube.com`
    post URL the same way. The fail is by field and pattern, in both languages.
- C27 X figures in our prose (R8-3, "listed and follow the same rule"):
  - A detector runs over every prose field of `hype.json`, sentence by sentence. A
    sentence is a hit when it holds a numeral and either an X term (`X`, `x.com`,
    `twitter`, `tweet`, `repost`, `retweet`, `x_search`, `syndication`) or an engagement
    term (`likes`, `replies`, `views`, `reposts`, `followers`, `impressions`,
    `bookmarks`).
  - Every hit must appear in a committed list, `web/i18n/dossier-x-figures.json`, keyed
    by slug, field path and the sentence's SHA256, with the disposition `strip` or `keep`
    and a one-line reason. `keep` is for a sentence whose figure is not from X (for
    example GitHub stars or HN points).
  - The build replaces each `strip` sentence with a fixed placeholder in both languages
    ("An X figure is not shown here: X appears as counts only. See the method page.").
  - CI fails an unlisted hit. A new research pass therefore lists its hits in the same PR
    that refreshes `hype.json`.
  - Round 9's run of a narrower form of this detector (X term plus numeral) found 14
    sentences in 13 items (`notes.momentum` 9, `status` 3, `skeptic[].claim` 1,
    `skeptic[].by` 1). The full detector also matches engagement terms with no X word,
    such as "1,692 API-observed likes and 66 replies".
- C28 Handles in dossier fields beyond `posts[].au` (R3-3, extends C6 and C22):
  - `viral.cand_account` (81 set, 66 of them `@handles`) and `viral.account` leave the
    public file. `viral.cand_platform` stays as a network name. `viral.followers` leaves:
    it is profile information, which the X Developer Agreement counts as X Content (A29).
  - `skeptic[].by` (105 values, 22 with an `@handle`): outlet and publication names and
    the authors of a published article, paper or report stay, as R3-3 keeps paper
    authors and newsletter names. A poster on a conversation network (X, LinkedIn,
    Reddit, HN, Mastodon, Bluesky, YouTube, Telegram, Discord) becomes "<network> user",
    for example "X user, sampled post". The source note after the semicolon stays.
  - CI fails any `@handle` pattern, and any name a disposition list does not mark as an
    outlet or author, in `skeptic[].by`, `viral.*` or `coord.evidence[]`. `aliases[]` is
    exempt by field: its three `@` values are the projects' own names (A32).
- C29 Telegram (1 dossier post, 2 `viral.cand_post` values; terms not read): counts only,
  as R8-3 sets for X, LinkedIn and YouTube. This is the stricter default for a network
  whose terms nobody has read. A `t.me/<name>/<id>` URL names a channel, which C22 cannot
  tell apart from a person. If the owner wants Telegram text or links, it gets its own
  question.
- C30 Verdict-row sources and X (R8-3, C10, C22): the primary source URL a REAL,
  OVERHYPED, FALSE or PUSHED row must carry (C10) is never an X, LinkedIn or YouTube post
  URL. That covers the handle-free `x.com/i/web/status/<id>` form, which C22's pattern
  does not catch. The verdict file is shown on the pages and in the feeds (C1), so a
  status link there would publish what R8-3 keeps out of the two data files. A claim
  whose only primary source is an X post stays UNVERIFIED. Its reason may name an
  official account and a date, with no link, because official names stay under R3-3.
  Flagged: R8-3 did not name the verdict file. No briefing story carries an X post today
  (X is not collected), so this binds rarely. If the owner wants official X posts as
  linkable primary sources, it gets its own question.
- C31 Method-page disclosure of the X route (R8-3's accepted trade-off): the method page
  and the Hype page's header (C21) say, in both languages, that the X counts and the
  attention scores built from X posts come from the research pass of 2026-10-07. They say
  that the dossier's own notes name "x_search" reports and "X syndication" readbacks, and
  that whether those are X's published interfaces, and whether any paid call was made, is
  not on record. No X figure is shown, and the count is given as "posts in our sample",
  never as reach.
- Staging set for the round-9 files (with C2): `web/i18n/dossier.pt.json` (C24),
  `web/i18n/dossier-x-figures.json` (C27) and the `skeptic[].by` disposition list (C28)
  are owner-reviewed and enter only by a merged PR. Like the verdict file, none of them
  is ever in the bot's staging set in `refresh.yml`, so the daily commit cannot overwrite
  a `reviewed_in` marker or a disposition. `web/checks/mastodon-links.json` (C25) is the
  opposite: the bot writes it, so it is in the staging set. Amended in round 10 by C44:
  `web/removals.json` joins the owner-reviewed set, and `web/story-aliases.json`, the
  story-id archive and the upgraded proofs under `web/ledger/ots/` join the bot's set.

### What round 6's answers mean for the design (read from the recorded question and label)

The ledger holds each question's text and the picked label only, so these readings rest on
the question text and the label, and on the option text the DRAFT recorded under O24-O26.

- R6-1 "New today first": the Top 10 is cut from covered "news" stories with a post in the
  last 24h (A23). First come the stories first seen in that window, ranked by heat
  (pulse.py:970). Then the rest, by heat, up to 10. Ties break by newest post, then by
  stable id. "First seen" is the earliest post in our sample (A11), and the window ends at
  `pulse.py`'s `NOW` (C12). On the 2026-10-16 snapshot all ten are new. On the days before
  it, 5-7 stories a day were first seen, so 3-5 slots would be heat fill. The rule and its
  tie break are published on the method page (C13, C19).
- R6-2 "Counts only, no text": on every public page, in `pulse.json` and in both feed
  formats, Reddit appears only as a count of posts in a story's spread. No Reddit title,
  permalink or username appears. A story whose headline is a Reddit title takes the title
  of its earliest non-Reddit post, or else its topic label (C20). The rule covers story
  post lists (245 Reddit titles) and topic-node samples and spread (710 Reddit entries,
  round 7 count), not only headlines. Under the fold it also covers the Hype page: 23
  dossier citation URLs in 11 items point at `reddit.com` and leave as permalinks. The
  claim each one supports stays, citing "a Reddit post", with no link. Readers cannot
  click through to Reddit. It applies from the change forward (A25).
- R6-3 "Fold into dehype": each console tab becomes a dehype page in the Mission control
  look:
  - Pulse becomes the briefing and the "all stories" page.
  - Papers and Repos become the drill-down of "Releases / research output by area".
  - Hype becomes a project page with the briefing's state display.
  - Method becomes the method page.
  - The in-browser search stays.
  This is the largest S1, and the owner picked it knowing that. Two facts read this round
  change the option's trade-off text:
  - "Until it joins the refresh" has no path today. `hype_build.py` runs only when
    `hype/hype_research.json` exists. That file is gitignored ("not committed, because it
    holds raw post excerpts", CONTRIBUTING.md:54). It is "refreshed only when a research
    pass runs" (ARCHITECTURE.md:63). Adding `hype.json` to the refresh commit set (O11)
    changes nothing on CI. The Hype page therefore rests on a manual research pass, and
    it says so (C21).
  - The fold also brings in the dossier prose, X content and links with handles (O27-O29).
  R3-2's 14-day clock starts on the first scheduled run whose deploy passes S1's
  acceptance checks (R5-1 reading). With the fold, those checks cover every folded page.

### Design conditions added in round 7 (add scrutiny, announced)

- C19 Top 10 rule (R6-1): the method page publishes the rule, the tie break and the
  window end. A CI check recomputes the Top 10 from the day's `pulse.json` and fails if
  the briefing's ten ids or their order differ. Each briefing row shows "new today" or
  "first seen <date>", so the heat fill is visible as such.
- C20 Reddit counts only (R6-2): CI fails if a post, sample, spread or citation record in
  any public file (`pulse.json`, `hype.json`, the pages, both feed formats, both
  languages) holds a `reddit.com` URL or a `t3_` id. It also fails on a title or author
  field on a record whose network is Reddit. The method page and the `sources[]` entry may
  still name Reddit and arctic-shift as a source. The headline fallback order is fixed:
  1. the title of the earliest non-Reddit post, shown as posted with its `lang` (C17);
  2. else the topic label;
  3. else "Reddit discussion, title not shown" in our own text, in both languages.
  Reddit stays in the spread as a count with its network name. The method page states the
  rule and its reason. The manifest is already covered (C16).
- C21 Fold (R6-3):
  - Every console URL and tab anchor in use today keeps resolving to its dehype page.
  - Each folded page names the data file it reads.
  - The Hype page heads every view with "research dossier, content cut <date>, not in
    the daily refresh". It reads the date from `hype.json` `content_cutoff`
    (2026-10-07T03:43Z today).
  - The attention / discovery gap class (`attention_ahead`, `evidence_ahead`, `similar`,
    `insufficient`; 2, 6, 10 and 64 of 82 projects overall) is shown as "Hype vs
    substance" components, with the existing wording "heuristic only, not validation".
    It never fills the verdict slot or uses a label word, because the pipeline proposes
    no label (R4-1, C9).
  - The skeptic entries (sampled user criticism of named projects, written by the
    research pass) read "sampled criticism, not checked against a primary source".
  - The semantic search keeps its row count on screen.
- C22 Handles inside URLs (added after the round-7 report; R3-3, holds in every O28 and
  O29 option): C6 also fails on any post URL in a public file whose path names a person
  account. The files are `pulse.json`, `hype.json`, the pages, both feed formats, the
  manifest (R2-3) and both languages. The patterns: a path segment starting with `@`
  (Mastodon and other fediverse servers), `x.com/<name>/status/` or
  `twitter.com/<name>/status/`, and `bsky.app/profile/<handle or DID>/post/`. A Bluesky DID
  counts as a handle, because it is an account identifier that resolves to the handle
  through the public API (round-7 scout). Profile links of a project's own account
  (`links.x_handle`, A26) are exempt by field, not by pattern. Reason: C6 as planned
  checks only `author` values, and 225 Mastodon and 153 X URLs would pass it while naming
  the author.
- C23 Dossier records in the daily file (added after the round-7 lead read): every rule
  for a network covers the records `pulse.py` copies from `hype.json` (`source:
  "dossier"`, pulse.py:311-318), not only the records its own fetchers read. For a
  network shown as counts only, the check also fails on `score` and `comments`, the
  fields that carry likes and replies, as well as on `title`, `author` and `url`.

### What round 5's answers mean for the design (read from the recorded question and label)

The ledger holds each question's text and the picked label only, so these readings rest on
the question text and the label.

- R5-1 "Qualified Cordis API now" (reopens R4-3): S1's feed and frontend adapters are
  composed with the qualified component API of `@deepseek-ai/cordis@4.0.4` (C14), run as
  a one-shot build in GitHub Actions, with no server and git as the store (C18). "S1
  waits" no longer applies. S1 does not wait on WISH #4's acceptance, Brain #5 or tenant
  principals. It does not claim any of them either. The question text said the lead's
  zero-server reading is "a reading, not a statement on record". The owner picked it
  knowing that, so the design states that the reading is the owner's choice. R3-2's
  14-day clock starts on the first scheduled run whose deploy passes S1's acceptance
  checks. A21 is answered.
- R5-2 "Hash per record only": in the daily input manifest (R2-3), a Reddit record is
  represented by one SHA256 and nothing else. The round-5 option text gave the reason:
  short sequential base36 ids are enumerable, so a hash of the id alone would publish
  the id in effect. The hash is therefore taken over the canonical bytes of the stored
  record (C16). C15 is met for the manifest. The question said it "covers the manifest
  only", and the public pages are asked separately (O25).
- R5-3 "Our text, headlines original": page chrome, gauge names, labels, the method page,
  policy pages (right of reply, corrections), feed item chrome and the owner's verdict
  reasons are written in English and Portuguese. The agent drafts the Portuguese and the
  owner reviews it. Story headlines and post titles are shown as posted, tagged with
  their language, and never machine-translated (C17). The `opus-mt-en-ROMANCE` route is
  not used in S1. A20 is answered.

### Design conditions added in round 6 (add scrutiny, announced)

- C16 Reddit in the manifest (R5-2): each Reddit record in the dated Release manifest is
  `sha256` of the record's canonical JSON as stored on the runner (keys sorted, UTF-8,
  every field as fetched from arctic-shift). The manifest carries no Reddit post id, no
  `reddit.com` URL, no title and no username. A CI check fails the manifest if it holds
  the string `reddit.com`, a `t3_` id, or any field other than the hash and the network
  name for a Reddit record. An outsider who holds the same archived record can recompute
  the hash, and nobody can reach Reddit from the manifest alone.
- C17 Two languages (R5-3): every string of our own text has an `en` and a `pt` entry,
  and CI fails a missing or empty key. Each upgraded verdict row (C10) carries its reason
  in both languages, and the PR that upgrades the row also carries the Portuguese
  reason. Headlines and post titles carry a `lang` field with the language of the source
  post, and CI fails any build step that writes a translated headline. Each feed format
  (C1) ships in English and in Portuguese, with the same item ids and the same headlines.
- C18 One-shot Cordis (R5-1, with C14): the S1 Cordis composition runs as one Node step
  in refresh.yml after `pulse.py`. It starts with `new Context()`, loads the adapter
  plugins, writes files and disposes. It creates no server, socket, profile, credential or
  home directory, and it uses no DSH launcher. All state it reads or writes is in
  git-committed files or the day's Release. The step creates no WISH Run, task, worker
  or dispatch, which keeps the observatory WISH's 2026-10-16 strict hold intact, and no
  S1 page or file claims WISH #4 acceptance. The step's run time is unmeasured. It must
  fit inside C12's 15-minute margin, and C12's cron is re-fitted if it does not.

### What round 4's answers mean for the design (read from the recorded question and label)

The ledger holds each question's text and the picked label only, so these readings rest on
the question text and the label.

- R4-1 "Evidence record, you upgrade": the pipeline writes, per Daily briefing story, an
  evidence record from fields it computes today (official post present, press or
  newsletter cover, spread, complaint share, node coordination readings, source status per
  C7) and the proposed state UNVERIFIED. It never proposes REAL, OVERHYPED, FALSE or
  PUSHED. The owner upgrades a row by PR (optionally drafted with the agent session) with
  a named claim, a cited primary source and a reason; the merge is the confirm (X6, X7).
  No paid model is involved (A7 holds). Dissent carried from scout 2: most rows stay
  UNVERIFIED on most days, so R3-2's 14-day test rests on the owner's effort.
- R4-2 "Add FALSE, you set it": the label set becomes REAL / OVERHYPED / FALSE / PUSHED /
  UNVERIFIED. This amends X10 ("4 labels") as the question quoted. FALSE is set only by the
  owner, by hand, on a named claim with a cited primary source that contradicts it; the
  pipeline never proposes it. UNVERIFIED means "not yet checked against a primary source"
  (A18, stated in the question text, now confirmed). The scope item keeps its spelling.
  The right-of-reply path (Lei 13.188/2015, 60 days) and the corrections log are policy
  text the design writes (A4).
- R4-3 "Cordis now, S1 waits": S1's feed and frontend adapters are Cordis-composed, not
  plain build-time modules (A12 is answered against the lead's assumption). The question
  covered "S1's feed and frontend adapters"; the picked label says "S1 waits"; the round-4
  O15 gloss said "S1's feed waits". The lead reads the label as written: the first release
  waits until cordis.md's "composition/persistence/tenancy BLOCKED" clears, and R3-2's
  14-day clock cannot start before then. The lead does not narrow this to "only the feed
  waits" on its own. Round-5 scout 0 found the wait unbounded: no date is on record (by
  design), and clearing needs named human owners, two independent approvals and upstream
  rc1 changes. The record is silent on a one-shot static build. The round-5 batch therefore
  asks O22 as a reopen of R4-3, with "keep it" as one of its options.

### Design conditions added in round 5 (add scrutiny, announced)

- C9 Evidence record (R4-1): each Daily briefing story has one evidence record carrying
  the story's stable id, the fields it was built from, the source status per C7, the
  method version and its config hash, and `state: proposed` with no label word. CI fails
  if a pipeline-written record carries REAL, OVERHYPED, FALSE or PUSHED.
- C10 Upgraded rows (R4-1, R4-2, R2-2): a row whose label is REAL, OVERHYPED, FALSE or
  PUSHED must carry the named claim (FALSE, REAL, OVERHYPED) or the document (PUSHED), a
  primary source URL, a reason and the confirming commit; CI fails a row missing any of
  them. The labelled subject is a claim, story, topic or project, never a person or
  account.
- C11 FALSE exposure (R4-2): every FALSE row links the published right-of-reply and
  corrections path; a reply or correction is appended, never edited over.
- C12 Ready time (X16): the day's Daily briefing, gauges and feed are live on Pages by
  06:00 America/Sao_Paulo. Today refresh.yml runs at `17 9 * * *` ("06:17
  America/Sao_Paulo"), which starts after the deadline. Measured this round (scout 2, n=2,
  both manual runs): run plus deploy takes 36m30s and 43m05s, and `run.py` is about 97% of
  it. The Pages deploy adds under 1 min. The schedule moves to `45 7 * * *` (04:45 BRT),
  which is the agent's sequencing (memory). The arithmetic: 09:00 UTC minus 45 min (the
  observed maximum rounded up, standing in for a p95), minus 15 min of assumed scheduler
  delay, minus 15 min of margin. The expected live time is about 05:29 BRT. The cron is
  re-fitted after 7-10 scheduled runs, because no scheduled run has ever fired. The
  "last 24h" window ends at `pulse.py`'s `NOW` (taken when the Pulse step starts, about
  38 min into the run, so about 05:25 BRT). The briefing prints that window end in BRT.
  When the run misses 06:00, C5 applies ("stale since <date>" with the reason). The
  OpenTimestamps proof may still read "pending" at 06:00 (C4 already allows it).
- C13 Briefing size (X17): the briefing shows at most 10 stories, ranked by a published
  rule; every other story of the day is reachable in one click from the briefing, with the
  same evidence record and state display. `stories()` returns its list grouped by kind and
  not sorted by heat overall (scout 2), so the ranking is applied explicitly where the
  Top 10 is cut. The rule and its tie break are published. The default rule is in O24.

Added after the round-5 reports (add scrutiny, announced). Scout numbers follow the report
order (scout 0 Cordis, 1 Reddit, 2 ready time, 3 Portuguese). The dispatch list numbers
the same four scouts 1-4.

- C14 Cordis pin and notice (applies whenever any S1 code uses Cordis): the dependency is
  pinned exactly to `@deepseek-ai/cordis@4.0.4`, the qualified version. 4.0.5 was
  published 2026-10-16, and the record says a changed version "invalidates affected prior
  runtime receipts". The MIT copyright and permission notice ships with the AGPL code. The
  licence closure of the installed tree is audited before release, because the record says
  "dependency licence closure not audited". Only the qualified component API is used:
  plugin, inject, effect, fiber await/dispose/restart/update, isolate and extend. No state
  is held in plugin heap across runs.
- C15 Nothing un-deletable from Reddit: until O21 is answered, no Reddit post id,
  permalink or text enters an artifact whose bytes are anchored for good (the dated
  Release manifest, its Sigstore attestation, its OpenTimestamps proof). Reddit's terms
  require deleting removed content "as soon as possible" (Developer Terms §3.3), and an
  anchored file cannot be edited without breaking C3 and C4.

### What round 3's answers mean for the design (read from the recorded question and label)

The ledger holds each question's text and the picked label only, not the option
descriptions, so these readings rest on the question text and the label alone.

- R3-1 "S1 testable, rest roadmap": the design specifies S1 (the dehype identity, the
  Daily briefing in the Mission control look, the gauge header, the RSS / JSON feed, the
  verdict file in git, the audit floor) with acceptance checks a reviewer can run. S2-S6
  and G1 appear as a sequenced roadmap with their open questions named, not as specs. A14
  is answered.
- R3-2 "Your daily use, 14 days": S1 as a whole has succeeded when the owner (the only
  user, X2) has used it daily for 14 days. It sits beside R2-4's per-gauge rule (14 ledger
  days, a green recompute verifier, the owner's confirm). The design writer makes it
  checkable from the record: 14 dated Daily briefings published on Pages, the owner's
  verdict confirms and overrides in git as the trace of use, and the owner's final confirm.
  How "used" is evidenced beyond the git trace is design detail; it must not need
  analytics or a server (X7, X14).
- R3-3 "Remove person handles": conversation-network handles (HN, Reddit, Mastodon,
  Bluesky) leave `pulse.json`, `hype.json` and the page bylines. Newsletter and official
  feed names, paper authors and repo owners stay (the question text). Removal touches the
  writers at pulse.py:605, 607, 971 and hype_build.py:120 (round-3 scout 1) and more of
  the page than three render sites: `web/index.html` reads `author` in 33 places, some of
  which are feed names and paper authors that stay (round-4 scout 0). No test or gate
  asserts on `author`, and no count changes. The daily input manifest (R2-3) follows the same
  rule: post ids and URLs as pointers, no handles (A17). Design condition (adds scrutiny,
  announced): a CI check fails if a conversation-network `author` value reaches a public
  file.
- R3-4 "dehype pages only": the Mission control look (X5) styles the dehype pages. The
  observatory explorer keeps the #8 shell ("the existing tracker's system font, blue
  controls and neutral borders"). No WISH issue changes; O14 is closed.

### Design conditions added in round 4 (add scrutiny, announced)

These are acceptance checks the design writer turns into commands; none changes an owner
answer.

- C1 Feed: the RSS file validates as RSS 2.0 and the JSON file as JSON Feed 1.1; each item
  carries the story's stable id, its verdict state ("proposed by the pipeline, not
  reviewed" or the confirmed label) and the source links.
- C2 Verdict file: CI fails on any `s:` id that resolves neither to a story in the day's
  `pulse.json` nor through the alias table (round-2 repo check); the verdict file is never
  in the bot's staging set (round-2 refresh.yml check). Amended in round 10 by C32: an id
  also resolves through the per-day story-id archive, and the alias file is bot-written.
- C3 Ledger and store: the SHA256 written in the day's ledger on Pages equals the SHA256
  of that day's Release asset, and both appear in the manifest.
- C4 Audit floor: the day's manifest has a Sigstore attestation that `gh attestation
  verify` accepts and an OpenTimestamps proof that `ots upgrade` completes and `ots
  verify` accepts against a Bitcoin block (R1-3); a pending proof reads "pending", never "anchored".
- C5 Fail loudly: when the Pulse step fails (it runs with `continue-on-error: true`), the
  briefing, gauges and feed for that day read "stale since <date>" with the reason, and
  no value is carried over silently (council "fail loudly").
- C6 Handles: the R3-3 check above. It extends the privacy guard `scripts/check_page.mjs`
  already runs (`pulse.json` must not contain `x_handles`, round-4 scout 0).
- C7 Unfetched is not false (added after the round-4 reports): when
  `sources['Official feeds (RSS)']` (or any source) reads "unknown" or "not connected",
  every story's evidence record, the Hype vs substance gauge and the feed read "not
  fetched" for that source, never `false` or 0. When it reads "partial", they name the
  feeds that were reached, keep `official` true where it is true, and read "not fetched"
  for the rest. Reason: the committed `pulse.json` is an offline rebuild with
  `official` false on all 79 stories, and a rule keyed on it would lean every story
  toward "no primary source" (round-4 scouts 0 and 2).
- C8 Substance is the story's own (added after the round-4 reports): a repo, paper or
  official post counts as substance for a story only when the story's own posts link to
  it or a confirmed verdict row cites it. Topic-node tracker samples reached through
  `tags` are shown as "related in topic", never as the story's substance. Reason: node
  samples for broad tags are generic top repos (round-4 scout 0), and `stories()` keeps
  only live and official posts, so no repo or paper link reaches a story today (round-4
  scout 2). This sharpens R2-1 ("spread vs official post, repo, paper") without changing it.

### What round 2's answers mean for the design (read from the option texts)

- R2-1 "Council names, keep 'Hype'": the gauge header uses the council's names, and the
  per-story gauge is called "Hype vs substance" (the option text). So: "Releases /
  research output by area" (output volume, not capability), "Hype vs substance" per
  story (spread vs official post, repo, paper, components shown), "Jobs" as a panel that
  says "no qualified source" until a licensed source qualifies, "Risk" as a dated,
  sourced event log with no dial, "Daily movers" for ups and downs, and no combined State
  of AI score. The option's own trade-off binds: "hype" is acceptable only because every
  story shows the components behind it.
- R2-2 "Document proof only": PUSHED appears only when a public document shows an
  undisclosed paid or material connection (filing, sponsor tag, admission), cited on the
  row. Coordination signals are shown separately as "coordination signals", never as a
  label. PUSHED labels a story, topic or project, never a person or account.
- R2-3 "Ledger on Pages + Releases": a small daily gauge and verdict ledger committed
  under web/ and served by Pages at stable URLs; the full compressed input manifest on a
  dated GitHub Release, its SHA256 in the ledger and in the Bitcoin-anchored manifest.
- R2-4 "Up to 4, trends held": the Daily briefing plus up to four gauges, today's values
  with coverage and a "preview, not yet reproducible" label; no trend line or
  day-over-day arrow until 14 ledger days. A gauge counts as shipped after 14 ledger
  days, a green recompute verifier and the owner's confirm. This is the first testable
  ship rule in the record.

Repository note: the local checkout (`dev` at e939123) is behind `origin/dev`, now at
2bc0ace (PR #29, "Briefing: complaints are not news", the pain classifier). The product
the owner judged is `origin/dev`. Every round reads it with `git show origin/dev:<path>`,
never with a checkout or reset in this shared workspace.

## What the owner said (round 1 request, their words, by pillar)

1. View: "data improved, but the view didnt ... lets redesign the thing as a whole".
2. Identity: "brainstorm on what we are becoming"; "omnichannel AI reality digested to
   human"; "create new media, the future for proofing AI".
3. Audience path: "start off the techinical bottom of it, and as we expand the venture,
   start aiming larger audiences, by targeting bubble leaders, becoming popular against
   them".
4. Reality questions: "how much did we realy advance in which area? how doomed are we?
   hows jobs? how many up and down everyday".
5. Curated feed with verdicts: "whats real, whats fake, whats overhyped, whats financed
   to look hyped ... no bullshit, no FOMO".
6. Awareness map: "map how many humans effectively know about AI, how much.. free
   information".
7. Trust: "it has to be open source, and fully auditable. we will do the blockchain for
   that."

### Earlier owner decisions that constrain this (not part of this request)

- No invented numbers; no paid actions without approval; plain ASCII explanations
  (task context; README "Numbers are never invented").
- GitHub Pages is enough; Cloudflare dropped (memory roadmap-ownership-and-hosting,
  2026-10-16 evening). The same memory says the agent owns sequencing since 2026-10-16.
- Stable ids and URLs must stay deterministic so knowledge can migrate to Brain later
  (same memory; METHODOLOGY "Data identity (stable ids)").
- Topic-level rankings (Claude, agents, Robotics) were judged useless; the owner wants
  the immediate unknowns, judged relevant on sight (same memory).
- Still-open owner decisions from docs/SIGNALS_PLAN.md (origin/dev): X access (paid
  route or none; cookie scraping rejected) and which newsletter or inbox to use.
- Approved records this redesign can collide with: docs/ROADMAP.md D1-D6 (D5 now
  reopened by R1-4 to "several static pages") and the open-intelligence-observatory WISH
  (20 issues, scope of record, IN_PROGRESS). Its #8 visual-direction choice lives in
  web/prototypes/, and it binds Cordis as the composition layer (WISH line 150).

## Owner input given outside the round (2026-10-16, verbatim or exact picks)

These answer earlier Open points. The design writer treats them as owner decisions;
they are not in the ledger because they were not asked through it.

| # | Topic | Owner input | Answers |
|---|---|---|---|
| X1 | Governance direction | "agreed, trust first then decentralize ... i do intend to be decentralized"; "make it a dao"; "I DONT WANT POWER, I WANT HUMANS TO BE FREE AND HAPPY" | identity |
| X2 | Users | "im gonna be the only initial user until the second human comes, do roadmap and do what is needed" | O8 (partly) |
| X3 | Voting direction (discussed) | more people and profiles to follow as sources; fair votes resistant to bots, no social-score power class; 1 human = 1 vote via personhood, no global score; bridging consensus on claims (Community Notes style); scoped, decaying track records; forkability. Phases: (1) observatory + open suggestions, (2) personhood + bridging ratings, (3) DAO | O10 (long term) |
| X4 | First screen | "Daily briefing": 10-15 events from the last 24h, each with a verdict and where it spread | O1 |
| X5 | Look | "Mission control": dark sci-fi HUD, few big numbers, thin glowing lines, calm spatial map; preview showed a STATE OF AI header with PROGRESS / HYPE / JOBS over verdict rows | O1 |
| X6 | Verdicts while sole user | "Data + you": pipeline proposes, owner confirms or overrides, overrides logged publicly with reason | O10 |
| X7 | Override mechanism | "Git commit": verdicts in a reviewed repo file; edits via PR or chat; zero servers | O10 |
| X8 | Delivery | "RSS / JSON feed", plus "think modularly cordis plugins etc, we will extend channels, indefinidely, there will be different frontends for differnt datastreams and audiences, this is just the first one" | O7 |
| X9 | Gauges | Progress by area, Hype temperature, Jobs signal, Risk/doom meter; "/council new gauges, think artificial intelligence analysis, theyre standard for that, i want us to become standard for state of ai" | O6 (partly) |
| X10 | Story labels | "4 labels": REAL / OVERHYPED / PUSHED / UNVERIFIED | O4 detail |
| X11 | Second audience | "AI builders" | A2 / O4b (partly) |
| X12 | Public name | "dehype" | identity |
| X13 | Licence | "Code AGPL, data CC BY-SA" | auditability |
| X14 | Hosting | GitHub Pages only ("im ok with gh pages if all the data is there and working"); Brain knowledge migration later; data links must stay deterministic | O9 (partly) |
| X15 | Language | "English + Portuguese" from day one | new; what it covers is O23 |
| X16 | Ready time | briefing ready daily at "06:00 BRT" | new; C12 |
| X17 | Briefing size | "Top 10" stories, the rest one click away | narrows X4; C13 |

The gauges council (X9) ran outside the harness: 5 lenses, all answered, decision
proceed-with-conditions. Report:
/private/tmp/claude-501/-Users-feliperosa-workspace-repos-trending-research/5addb51e-7d92-450e-8e63-adb4e00a86b0/scratchpad/council-gauges.md
(Synthesis section). The ledger's ## Councils shows none because it was not convened
through the harness. The owner ruled on its renames in R2-1 (council names, keep
"Hype").

### Where the outside picks touch settled or approved records

- X10 vs R1-2 ("Claim labels, sourced"): REAL, OVERHYPED and UNVERIFIED rate claims.
  PUSHED rates how a story spread, which is not a claim, and it carries the exposure
  scout 3 documented. Its proof bar is settled by R2-2: document proof only.
- X10 vs the scope item "real, fake, overhyped, financed to look hyped": the four labels
  had no FAKE. The scope item stays spelled as it is. R4-2 added FALSE, set by the owner
  only, so X10 now reads five labels (O17 closed).
- X17 vs X4: X4 said "10-15 events"; X17, the later owner pick, says "Top 10" with the
  rest one click away. X17 controls; no question needed (C13).
- X16 vs refresh.yml: the daily run is scheduled at 06:17 BRT, after the 06:00 deadline.
  Moving the schedule is sequencing the agent owns (memory). It was measured in round 5,
  and the new time is `45 7 * * *` (C12).
- X15 vs the pipeline and A17: the pipeline is standard-library Python with no model
  (round-4 scout 0), and story headlines are third-party post titles. The page chrome,
  gauge names, labels, method pages and the owner's verdict reasons can be written in
  both languages by hand. Headlines cannot be, without a translation route, and a
  translated title is a derivative of third-party text that A17 says our licence does not
  cover. What "Portuguese from day one" covers is an owner decision (O23), asked in the
  round-5 batch. A Portuguese edition also makes the Brazilian audience explicit, which
  raises the weight of the FALSE and PUSHED exposure scout 3 documented (Código Penal
  arts. 138-141; Lei 13.188/2015).
- R4-3 vs X7 and X14 (zero servers): cordis.md describes Cordis as a runtime plugin and
  lifetime container and states no server requirement (round-3 scout 2), but the WISH's
  DSH assistant (#4, #10) needs a session host. Round-5 scout 0: Cordis itself runs in one
  process with no server, and the repository's real-package probe was a one-shot Node
  command. The gate's wording targets a running DSH application, and the record says
  nothing about static builds. What S1 does about it is O22.
- X9 vs the council: the council's conditions rename or hold all four gauges. The owner
  was asked with old and new quoted and picked the council names, keeping "Hype" (R2-1).
- X8 "cordis plugins": the repo's own record (docs/integrations/cordis.md on origin/dev)
  says Cordis `@deepseek-ai/cordis@4.0.4` is "Contract-qualified; application
  composition/persistence/tenancy BLOCKED". It describes Cordis as a runtime plugin and
  lifetime container; it states no server requirement (round-3 scout 2), but the WISH's
  DSH assistant (#4, #10) needs a session host. X7 and X14 say zero servers. The lead read
  it as an architecture style, not a mandate to adopt Cordis now (A12, O15); the owner
  answered the other way in R4-3 ("Cordis now, S1 waits"), so Cordis adoption is now part
  of S1.
- X13 vs Cordis: Cordis 4.0.4 is MIT (npm metadata, and the upstream LICENSE at
  4878cdab). MIT code can be combined into AGPL code if its notice is kept (round-5 scout
  0, inferred from two FSF entries). The full transitive licence closure was not audited
  (C14).
- X13 changes MIT code and CC BY 4.0 data to AGPL and CC BY-SA. What was already
  published stays under the old licence. Inputs under CC BY 4.0 or CC0 can be combined
  into CC BY-SA output (A13).
- The council asked for gauges to stay inside one web/index.html "unless the owner
  explicitly reopens D5". R1-4 reopened D5, so that condition is met.

## What I assume (not said by the owner)

| # | Assumption | Load-bearing? | Becomes |
|---|---|---|---|
| A1 | "Redesign as a whole" means product identity and information architecture, not only a restyle | was yes | answered by R1-1, X4, X5, X12 |
| A2 | Technical audience first; bubble-leader reach later | was yes | answered by R1-1 and X11 (AI builders second) |
| A3 | "Blockchain" means "anyone can verify what we published and when" | was yes | answered by R1-3 (no-fee stack, Bitcoin anchor) |
| A4 | Verdict labels need a published labeling policy with thresholds, reply and correction | yes | R1-2 settles the claim side, R2-2 the PUSHED bar (document proof); policy text is design work |
| A5 | Doom, jobs and awareness are answered from named external sources with stated coverage, never our own estimates | yes | R2-1 sets the form (risk event log, jobs "no qualified source"); sources in O6, meaning in O12 (round 3 scout 4) |
| A6 | "Omnichannel" means outlets out (digest to many channels) more than channels in | was yes | answered by X8 (feed first, plugins later); X3 also wants more sources in |
| A7 | No paid source, API or chain fee without explicit approval | no (standing rule) | stays assumed |
| A8 | Existing pipelines (pulse.py, run.py, hype_build.py) and their stable ids are the data floor | no | stays assumed |
| A9 | "Becoming popular against them" means public, sourced rebuttal of claims, not personal attacks | yes | O4b, next round |
| A10 | No source measures what humans know about AI; S4 needs a stated proxy or our own instrument | yes | question when S4 is designed |
| A11 | The repo's honesty rules bind every new surface ("origin" = earliest post in our sample, coverage = completeness not truth, coordination output = signals not proof) | no | stays assumed |
| A12 | "cordis plugins" names a modular style; v1 channel and frontend adapters are build-time modules run in GitHub Actions, with no runtime server, and Cordis adoption waits on the observatory WISH | was yes | answered against the assumption by R4-3 ("Cordis now, S1 waits"); what that gate means in practice is O22 |
| A13 | The licence change applies from the change date forward; earlier releases keep MIT / CC BY 4.0 | no (licence mechanics) | stays assumed |
| A14 | This brainstorm's design covers S1 (identity, information architecture, the daily briefing on today's data, gauge slots, feed output, audit floor) in testable detail, and S2-S6 plus the governance phases X3 as a sequenced roadmap, not as testable specs | was yes | answered by R3-1 ("S1 testable, rest roadmap") |
| A15 | R2-4's "fields already in pulse.json" means fields the pipeline already computes today (output by area lives in `data.json`, not `pulse.json`) | no | confirmed by round-3 scout 1 (`data.json` views[].candidates, tracked, sources) |
| A16 | Under R2-4 the jobs "no qualified source" panel and the risk event log are honest placeholders, not gauges that need 14 days; which slots fill the "up to 4" is design detail | no: R2-1 named five slots, R2-4 allows four gauges, and the two placeholders are not gauges, so nothing is dropped | stays assumed; scout 1 found three slots with real values today and no field at all for risk or jobs |
| A17 | The CC BY-SA data licence (X13) covers our selection, arrangement and computed fields; it does not relicense third-party post text, titles or handles. Only arXiv metadata (CC0) carries a grant to redistribute | yes, for the input manifest | round-4 scout 1 agrees: mastodon.social grants third parties nothing, and Reddit's licence is display-only and not sublicensable ("owned by Users and not by Reddit"); Reddit pointers wait on O21 |
| A18 | UNVERIFIED means "not yet checked against a primary source", never "checked and unsupported"; a claim checked and contradicted takes the label O17 picks | yes, for exposure (scout 2 dissent) | stated inside the O17 question text and confirmed by R4-2; policy wording is A4 design work |
| A19 | "06:00 BRT" means America/Sao_Paulo wall-clock time, and "ready" means the briefing, gauges and feed are live on Pages (not only committed) | no: timezone and publish point, checkable | stays assumed; C12 |
| A20 | What "English + Portuguese from day one" covers (chrome only, plus owner-written text, plus translated headlines) | yes: it sets translation cost, a possible model (A7) and third-party-text exposure (A17) | answered by R5-3 (our text in both languages, headlines as posted); was asked as O23 in round 5 |
| A21 | R4-3's "S1 waits" gates the whole first release, not only the feed | yes: it sets when R3-2's clock starts | answered by R5-1, which reopened R4-3 to "Qualified Cordis API now"; the gate no longer holds S1 |
| A22 | America/Sao_Paulo is fixed UTC-3 with no daylight saving, so `45 7 * * *` UTC is 04:45 BRT all year | no: checkable, and it only shifts the cron | stays assumed. It comes from the workflow comment and general knowledge; scout 2 did not verify it |
| A23 | The Top 10 is cut from the "news" kind only (covered stories). Chatter and complaint stories stay one click away, as the page groups them today | no: it follows the page's current grouping (index.html:859) | stays assumed; O24 asks the ranking rule |
| A24 | Under R5-1 the pages stay static files that read data; Cordis adapters emit data and string tables, not HTML | no: either form passes the same checks | stays assumed (round 6) |
| A25 | Handle and Reddit changes apply forward; the 10 public `pulse.json` and 12 `hype.json` commits are not rewritten | no for S1; a rewrite would be its own question | stays assumed (round 6; hype.json count added round 7), flagged |
| A26 | A project's own X account (`links.x_handle`, 43 items, for example `x.com/claudeai`) is an official account, not a person handle, so it stays under R3-3's "official feed names ... stay" | no: 43 organisation links, checkable, and R3-3's question kept official names | stays assumed (round 7), flagged |
| A27 | The `lang` tag (C17) comes from the source's own metadata where it gives one (Mastodon and Bluesky do), else reads `und` (undetermined); no language detection is added | no: a tag value, checkable | stays assumed (round 7) |
| A28 | Topic labels used as fallback headlines (C20, for example "GPT 6") are names, shown as they are in both languages, not translated | no: short proper names | stays assumed (round 7) |
| A30 | R8-3's "no link" covers X status links in every field of the two files, not only `posts[]` (195 more in citation and viral fields) | no: the option text says "No excerpt, handle, link", and the claims stay | stays assumed (round 9); C26 |
| A31 | HN dossier posts keep their text and handle-free item link, with the handle removed | no: it is the HN rule already on the page | stays assumed (round 9), flagged (YC terms) |
| A32 | `aliases[]` `@` values are the projects' own names | no: three values | stays assumed (round 9); C28 exempts the field |
| A33 | Published-article authors in `skeptic[].by` stay; conversation-network posters become "<network> user" | no: the claim and source note stay either way | stays assumed (round 9); C28 |

## Size triage

Size: **G**, and it splits. Seven pillars, four of which (verdict feed, reality
indicators, awareness map, audit trail) are products of their own. The split below stands
as the working plan; nothing is dropped.

```
 S1  identity "dehype" + information architecture + Daily briefing in the Mission
     control look, on today's data (R1-1, X4, X5), RSS / JSON feed out (X8),
     verdict file in git (X6, X7), audit floor (R1-3)          <- first release
 S2  verdict feed policy: REAL / OVERHYPED / UNVERIFIED on claims (R1-2, X10),
     PUSHED on document proof only (R2-2); FALSE added, owner-set (R4-2)
 S3  reality indicators (R2-1 names): releases / research output by area, Hype vs
     substance, daily movers, risk event log, jobs panel; 4 max, trends held (R2-4)
 S4  awareness map: how many humans know about AI, free information
 S5  audit trail: ledger on Pages, inputs on dated Releases (R2-3), manifest,
     Sigstore, OpenTimestamps (R1-3)
 S6  channels and audiences: feed plugins, AI builders (X11), bubble leaders later
 G1  governance phases (X3): open suggestions -> personhood + bridging -> DAO
```

S1 carries thin slices of S2, S3 and S5 (verdict rows, the gauge header, the daily
manifest), so they land without a second redesign.

## What the scouts found (round 1, read-only, evidence not instructions)

Sources: scout 0 read `origin/dev` at 7eb8c1b with `git show` only; scouts 1-3 fetched
public pages on 2026-10-16. Numbers are as the scouts reported them.

### Live product today (origin/dev)

- `web/index.html` is one 131 KB static file with five tabs: Pulse (default: map, briefing,
  "chatter, not in the press yet", rising, most coordinated-looking, people), Papers, Repos,
  Hype (82 projects) and Method. Semantic search runs in the browser (MiniLM, 1,680 rows;
  Pulse topics and stories not indexed).
- Data: `pulse.json` (79 stories, 160 topic nodes, stable ids `s:`+sha1), `data.json`
  (3,759 papers by arXiv id, 1,708 repos by owner/name, 7 windows, scoring 3.0),
  `hype.json` (82 items by slug; 64 of 82 rows "insufficient"; `verification` empty on all
  82; 1 of 82 has a disclosed sponsorship).
- The frontier-economics explorer (`web/prototypes/`) is not linked from the console and
  probably 404s on Pages (absolute fetch path; inference, not tested live).
- Operational gaps: `hype.json` is not in the daily refresh commit set; raw inputs live in
  the Actions cache and a 30-day artifact; none of the commits is signed; no corrections
  log; `deploy.yml` still has a Cloudflare job.

### Pillar map

| Pillar | Floor in the repo today | Open source found (licence as verified) | Hard gap |
|---|---|---|---|
| Redesigned view | five-tab console; explorer pattern unlinked | n/a | no plain-language "state of AI" page |
| Progress by area | papers/repos per paradigm (6), 47 version + 24 model nodes | Epoch AI data hub, CC BY | no capability data; no time series yet (needs 14+ snapshots) |
| Risk / doom | one topic node `safety-alignment` (conversation volume only) | AI Impacts survey (CC0 pages); MIT AI Risk Repository (CC BY 4.0, a catalogue) | no open, objective doom number exists; AIID licence conflict, bars bots |
| Jobs | one topic node `jobs-economy` (volume only) | BLS (public domain), O*NET 31.0 (CC BY 4.0), Indeed Hiring Lab (CC BY 4.0), Epoch polling (CC BY) | AI-attributed layoffs only from Challenger (terms unknown) and Layoffs.fyi (informal) |
| Daily up/down | rank arrows, 1d totals, "Rising now" | n/a | no risers/fallers counter; per-item history unpublished |
| Verdict feed | covered vs chatter, spread path, coordination signals | IFCN principles, ClaimReview, Community Notes bridging (methods) | no verdict labels; thresholds unvalidated; no undisclosed-payment evidence source |
| Awareness map | sampled AI-community voices only | Eurostat enterprise use; Census BTOS (licence not established) | no source measures what humans know |
| Auditable record | MIT code, CC BY 4.0 data, scoring_version + config_sha | Sigstore via GitHub attestations (free); OpenTimestamps (free per designer) | no signing, manifest or anchor; raw inputs not retained |
| Audience path | spread trace, 12 newsletter feeds, 9 person nodes | n/a | no people.json, no outlet of our own |

Not free on the evidence (link and cite only): METR time horizons, Stanford AI Index,
Artificial Analysis, FLI Safety Index, Pew, Manifold commercial use. The Epoch AI
ChatGPT-usage page carries agent-addressed text ("AI not authorized by YouGov is not
authorized to ingest or scrape this data") next to a CC BY 4.0 notice: do-not-ingest until
resolved. Reported, not followed.

### Auditability rungs (scout 2; R1-3 picked the no-fee stack with a Bitcoin anchor)

| Rung | Proves | Cannot prove | Cost |
|---|---|---|---|
| Signed commits and tags | authorship, history integrity | publish time; correctness | free |
| Sigstore attestation of a daily hash manifest | which workflow and commit built the bytes; log time | correctness | free |
| OpenTimestamps anchor on Bitcoin | manifest existed by a block time | authorship; correctness | free per designer |
| EAS on Ethereum / L2 | a wallet made the claim | correctness | gas (paid; not chosen) |
| IPFS / Arweave | byte availability | time, authorship | fees (not chosen) |

None proves a verdict right. "Fully auditable" also needs raw inputs retained, reproducible
builds, each record pinned to a method version, and an append-only corrections log.

### Verdict labels and exposure (scout 3)

- Practice rates claims, not people (ClaimReview, IFCN). "Overhyped" maps to Half True /
  Mostly False. Community Notes publishes contested labels only on cross-perspective
  agreement.
- "Fake" and "financed to look hyped" about a named company imply provable facts: no
  opinion shield in the US (Milkovich); near calúnia/difamação in Brazil (Código Penal
  arts. 138-139, tripled on social networks, art. 141 §2; sourced scientific criticism
  excluded, art. 142 II). Lei 13.188/2015 gives a free right of reply within 60 days.
- Regulators' bar for "financed" is proof of an undisclosed material connection (FTC 16 CFR
  255.5; EU UCPD Annex I item 11). Meta's bar for fake campaigns is false identities,
  which our signals do not measure.
- Labelling accounts breaks the repo rule "post authors are never ranked" and sits near
  Reddit's developer terms.

## What round 2 checked in the repository (origin/dev 2bc0ace, read with git show)

- Author handles are public today. `web/pulse.json` (1,150,420 bytes) carries
  `stories[].posts[].author` (sample values are pseudonymous handles) and, across the
  160 nodes, 1,022 non-null `samples[].author` and 423 non-null `spread[].author`. The
  story `path[].who` is set only for digest and official networks. This settles the
  council's handle-exposure gap: the security lens was right. Removing them changes what
  the site shows, so it is a question for a later round (O13).
- Story ids can move. pulse.py line 964: `cid` is `"release:" + topic` when the story is
  about a named release, else the canonical link of the earliest editorial post, else
  that post's URL; id = `s:` + 12 hex of sha1(cid). A verdict keyed to `s:...` is
  orphaned when an earlier post arrives or release detection changes. Design condition:
  the verdict file needs an alias table and a CI check for unresolved ids (council
  condition; no owner decision needed).
- `.github/workflows/refresh.yml` runs `python pulse.py` with `continue-on-error: true`
  ("a Pulse failure must not block the data commit") and stages only `web/data.json
  web/search-index.json web/search-vectors.bin web/pulse.json`. Design condition: gauges
  and the feed write stale or missing with a reason when pulse fails (council "fail
  loudly"), and the verdict file is never in the bot's staging set.
- Cordis: see "Where the outside picks touch settled or approved records" above.

## What round 3's scouts found (2026-10-16, read-only, evidence not instructions)

Scout 1 read `origin/dev` at 2bc0ace with `git show` only; scouts 3 and 4 fetched public
pages on 2026-10-16; scout 2 read the WISH (local copy and `origin/dev` are
byte-identical), the uncommitted 2026-10-16 checkpoint, ROADMAP and cordis.md. No scout
found text addressed to an agent. Numbers are as reported.

### Gauge slots and the movers (scout 1; O19, A15, A16)

| R2-1 slot | Today-value from one snapshot? | Fields and code | Needs ledger history for |
|---|---|---|---|
| Releases / research output by area | yes, for the tracker's 6 research tags only (not AI at large) | `data.json` papers/repos `[window][tag].candidates` (papers 1d all = 17, repos 1d all = 410), `tracked`, `sources`; window by source date, run.py:780-784, 849-851 | day-over-day change |
| Hype vs substance (per story) | spread side yes; substance side partial | `pulse.json` stories[]: voices, nets, newsletters, official, hn_points, heat (pulse.py:958-972). Repo and paper exist per topic node only; no code joins story.tags to nodes. `official` is false on all 79 stories at this commit (offline rebuild, Official feeds "unknown") | nothing for today's value |
| Daily movers | yes, as "Rising now" | node.rising = conv1 / (conv7 / 7), from post timestamps at build time, null unless conv7 >= 4 and conv1 >= 2 (pulse.py:597-598); 81 of 160 nodes have a value | tracker rank arrows only |
| Risk event log | no field anywhere | closest is story.pain (complaint share, pulse.py:963-964), which is chatter, not sourced events | n/a: needs a new sourced input |
| Jobs panel | no field anywhere | no jobs or labour source is fetched | n/a: placeholder |

- Tracker rank arrows (`rows[].mv`, `prev`) diff against the previous run's ranks in
  `history/trending.db` (run.py:676-688, scoring.py:622-650). That DB lives in the
  Actions cache, not in git. The "1d" arrow is run-to-run, not 24h: `data.json` run_id 2,
  previous_run 2026-10-16T14:31 BRT, same day. Under R2-4 these arrows are "held".
- "Rising now" and the 1d/7d/30d totals count posts by their own timestamps; the stored
  posts (45-day retention, also in the cache) only widen the sample. So Daily movers shows
  today's value under R2-4. O19 is closed as design detail. Caveat: fetch depth is uneven
  (Mastodon 4 pages per tag, arctic-shift 10 x 100 per subreddit), so the ratio is
  relative to our sample.
- The committed `pulse.json` was an offline rebuild (Official "unknown", Newsletters
  partial, Reddit official and Bluesky not connected). Design condition: the gauge header
  reads `sources[]` status as its coverage figure.
- `hype.json` is a hand-refreshed static dossier (content cutoff 2026-10-07, built only
  where the private `hype/hype_research.json` exists, movement "reset").

### Author handles (scout 1 and scout 3; O13)

- Voices, spread counts, emerging phrases and coordination signals are computed in
  pulse.py from the private sqlite on the runner; the page reads only precomputed
  integers. Removing handles from public JSON changes no count, rank or signal.
- Public handles today are entries, not people: `samples[].author` 1,022 entries / 641
  unique, `spread[].author` 423 / 255, `stories[].posts[].author` 346 / 265, `hype.json`
  `posts[].au` 405 / 347. Shown at index.html:703, 736, 813, 981.
- Must stay whatever O13 decides: feed names in `author` for the Newsletter and Official
  networks (index.html:785-786, 807, 819, `newsletter_names`), paper authors and repo
  owners in `data.json` (search "from X").
- Published lists are capped (8 samples per topic, 10 posts per story, one spread entry
  per network), so voice counts are not recountable from the public JSON today, and
  salted hashes in those lists would not make them recountable.
- Cost of removal: three render sites plus the writers at pulse.py:605, 607, 971 and
  hype_build.py:120. Not checked: whether tests or `scripts/check_page.mjs` assert on them.
- Handles are personal data: GitHub's Acceptable Use Policies ask for prompt response to
  "removal requests"; Bluesky says "complete deletion across the network may not always
  be possible". No fetched source grants a right to republish them.

### Source terms and Release limits (scout 3; O9, R2-3)

- GitHub Releases: "Up to 1000 release assets", each file "under 2 GiB", "no limit on the
  total size of a release, nor bandwidth usage" (about-releases). The large-files page
  ties the per-file limit to the Git LFS plan limit instead; a few-MB manifest is far
  below both. Pages sites "no larger than 1 GB", soft 100 GB/month bandwidth. R2-3's store
  fits.
- arXiv metadata is CC0: ids, URLs and titles may be republished.
- Y Combinator's Terms of Use bar scraping and data mining "except as expressly
  authorized"; whether that reaches the Algolia HN API is not stated, and no licence to
  third parties is granted.
- arctic-shift states no licence or terms; it runs its own removal-request form.
  Bluesky: users keep ownership, no relicensing grant. GitHub ToS do not restrict lawful
  use of public repositories.
- Not established (fetches blocked or empty): Reddit Data API and Developer Terms,
  mastodon.social server terms, Lobsters, Hugging Face, each newsletter's terms.
- Design condition (adds scrutiny, announced): the daily input manifest carries post ids
  and URLs as pointers; titles and person handles follow O13 and A17; a documented
  takedown path that also honours deleted posts.

### Risk and jobs sources (scout 4; O6, O12)

| Source | Result | Why |
|---|---|---|
| BLS | PASS on all six points | public domain, API and bulk files, series ids, monthly; general labour data, not AI-attributed |
| AI Incident Database | PARTIAL | CC BY-SA on listed collections except the report `text` field; "not allowed to sell or commercially exploit"; "bots and spiders, are prohibited"; weekly snapshots; GraphQL needs login |
| AIAAIC | UNVERIFIED | CC BY-SA 4.0 only per the OECD catalogue; own pages unreadable |
| OECD AI Incidents Monitor | FAIL | "All rights reserved", no bulk or API |
| MIT AI Risk Repository | FAIL for events | CC BY 4.0, but a taxonomy with no event dates |
| AI Impacts | PARTIAL | CC0 research pages; surveys irregular, last Oct 2023 |
| O*NET 31.0 | PARTIAL | CC BY 4.0 with prescribed attribution; a taxonomy, not an AI measure |
| Indeed Hiring Lab | PARTIAL | CC BY 4.0 CSVs, weekly; no AI dataset found |
| Challenger, Gray & Christmas | FAIL | AI-attributed cut counts (120,136 so far in 2026, about 21%) but no terms and no download |
| Layoffs.fyi | FAIL | "free to use with attribution" only; no export |
| Anthropic Economic Index (extra) | PARTIAL | "CC-BY" text vs "mit" metadata tag; a usage measure, not jobs lost |

So no doom meaning (frontier risk, deployment incidents, economic disruption) has an
AI-specific fully qualified source; only BLS passes, for general labour context. The
jobs panel stays "no qualified source" for AI-specific claims (R2-1). O12 would pick a
meaning for a log that has no automated source either way, so it waits.

### Observatory WISH (scout 2; O14, O15)

- None of the 20 issues (#2-#21) is superseded by S1-S6 or G1. Six are locally accepted
  (#2, #3, #5, #6, #8, #11), fourteen are not; all milestone exits HOLD; #4 BLOCKED; #7
  sixth-cycle reviews pending.
- Collisions sit in five places, each only if the design acts on it:
  1. #8 / #9 look: #8 selected "Guided questions first" (Felipe, 2026-10-09T20:33Z;
     readiness/group-7-felipe-direct-user-selection.json). Its design doc says the shared
     shell uses "the existing tracker's system font, blue controls and neutral borders"
     and "Differences are traversal and disclosure structure, not palettes". X5 collides
     only if it restyles the explorer. Asked this round (O14).
  2. Cordis: WISH:150 "Cordis owns application component lifetimes; use supported pinned
     DSH launcher/SDK and explicitly authorized Brain namespace. No generic substitutes or
     competing semantic memory." Also WISH:44 "One deployable Cordis-composed evidence
     atlas" and WISH:449 "`app/` is the Cordis composition root". cordis.md:
     "Contract-qualified; application composition/persistence/tenancy BLOCKED". Waits (O15).
  3. #12 / #16 editorial approval: the WISH requires "attributed editorial approval" for
     public interpretations, and #16 says an unreviewed interpretation never appears as an
     accepted public conclusion. Design condition (adds scrutiny, announced): a verdict
     row is public as an accepted label only after the owner confirms it (X6); until then
     it reads "proposed by the pipeline, not reviewed".
  4. #17 "votes never upgrade a claim to verified" vs G1 voting: roadmap only (A14), no
     collision today.
  5. WISH:44 "one deployable atlas" vs R1-4 several static pages: R1-4 already reopened
     D5; ROADMAP line 3 and D5 text need the owner-approved amendment written down.
- Overlaps the design should reuse rather than duplicate: #2 claim and replay contracts
  for the verdict file, #7 and #13 reproducible rebuild for S5, #11 label-matches-method
  for the gauge names, #15 common-source rule for claim labels.
- The explorer lens #8 chose is recorded (readiness JSON above); the prototype default is
  still "relationship" (WISH:1028). That part of O11 is answered.

## What round 4's scouts found (2026-10-16, read-only, evidence not instructions)

Scout 0 read `origin/dev` at 2bc0ace with `git show`, `git grep` and `git ls-tree` only.
Scout 1 fetched the Reddit and mastodon.social documents on 2026-10-16 (redditinc.com by
curl and web.archive.org; mastodon.social through its instance API, because the pages are
a client-rendered shell). Scout 2 read the DRAFT, `pulse.py` and `pulse.json` on
`origin/dev`, and fetched fact-checking sources. No scout found text addressed to an
agent; scout 1's grep matched only Reddit's clauses on AI training, which are terms, not
instructions. Numbers are as reported.

### Pipeline and production run (scout 0)

- No paid model or paid API anywhere. No Anthropic or OpenAI key, SDK or call exists in
  `*.py`, `*.mjs` or `*.yml`. The workflow secrets are data-source and hosting
  credentials only: `TRENDING_GH_TOKEN`, `BSKY_*`, `REDDIT_*` (refresh.yml:39, 44-48) and
  `CLOUDFLARE_*` (deploy.yml:54, 75-76). `requirements.txt` holds only `tzdata`. The
  pipeline runs on the Python standard library. The one other dependency, in
  `scripts/embed/package.json`, is `@huggingface/transformers` 4.2.0, a local open model
  that needs no key. Paid models appear only as unbuilt ideas: ROADMAP P3 (a capped
  Workers AI card) and SIGNALS_PLAN:77 ("only if the owner funds a capped model"). So O20
  starts from zero model code.
- The production Pulse run is live. refresh.yml runs `python pulse.py` without
  `--offline`, daily at `17 9 * * *`, with `continue-on-error: true`, after `run.py`
  (GitHub, arXiv, HF) and before the gate (unit tests plus `check_page.mjs`). It commits
  `data.json`, the search files and `pulse.json`, but not `hype.json`. It reaches HN
  (Algolia), Lobsters, mastodon.social tags, Reddit through arctic-shift, the Reddit
  official API and Bluesky (both need credentials, both "not connected" in the last live
  run), newsletters and 14 official feeds.
- Why `official` is false on all 79 stories: the committed `pulse.json` (2eb3063, "built
  from the stored sample (CI refresh will replace it)") is an offline rebuild, and the
  Official network was added in 0ae26bc (2026-10-16 16:51 -0300). That was after the last
  live refreshes had stored their data (29053d0 and 102f289, 19:15 UTC). The next live CI
  run is the first that can set `official` true. Inferred from commit order: no Actions
  log was read, and no live fetch of the 14 feeds is on record. The Anthropic feed comes
  through a community mirror.
- No test or gate asserts on an `author` field. Removing person handles (R3-3) breaks no
  test. The work is in `web/index.html` (33 `author` reads, among them 703 `p.au`, 786 the
  official or mirror tag, 819 newsletter names, 438-455 and 671 paper authors) and in
  the writers.
- No RSS, Atom or JSON Feed output exists. The feed (X8, C1) starts from zero. The only
  feed code parses input (pulse.py:205-228, run.py:256, tests/test_pulse.py:162-176).
- Story fields on `origin/dev`, all 20 present on all 79 stories: id, label, covered,
  kind (news 60, chatter 19, pain 0), pain, headline, url, link, first, last, voices,
  nets, newsletters, official, hn_points, key, path, tags, heat, posts. None holds a
  verdict, a sponsorship flag or a repo or paper link. `hype.json` (82 items, static,
  cutoff 2026-10-07) has the nearest proposer inputs: `traction[].ver`
  (platform_observation 85, vendor_claim 50, independent_report 8), `coord` ("not
  assessed" 81, disclosed sponsorship 1), `links.repo` 40, `links.paper` 16, `skeptic[]`
  on 73. These are project items, not briefing stories.
- Story-to-topic join. Every story tag is a node id. Through tags, 59 of 79 stories reach
  at least one tracker GitHub sample and 5 reach an arXiv sample (scout 0). 64 of 79
  stories have a tag that resolves to a node (scout 2). The two counts measure different
  things. Scout 0 judged precision likely low for broad tags, whose samples are generic
  top repos (C8).

### Verdict proposer options (scout 2; O20)

- Stories carry no claim text, only a `headline`: the title of one post, picked by a
  ranking (pulse.py:940-971). No code chooses which claim a label rates. `pain` is a
  complaint-keyword share, and pulse.py's own method text calls heat "a heuristic for
  ordering attention, not a measure of truth or importance". No field can tell whether a
  claim is true.

| Design | Can tell | Cannot tell | Cost | Touches |
|---|---|---|---|---|
| (a) Rules over computed fields, UNVERIFIED by default | official post present, press or newsletter cover, spread, complaint share, node coordination readings; deterministic and versioned | truth of a claim, which claim, whether a repo or paper backs it, any PUSHED document | zero | X6 literal; R2-1; R1-3 method version |
| (b) Owner's agent session drafts labels in a PR, merge = confirm | reads linked sources, drafts REAL / OVERHYPED with a citation, can find a PUSHED document | not unattended, not reproducible; errors are fluent and need the owner to catch them | no new pipeline fee; whether an existing subscription counts under A7 is the owner's call | X7 "edits via PR or chat"; strains X6's "pipeline proposes"; C2 (a PR writes the file) |
| (c) Model call in Actions under a secret | the same as (b), daily and unattended | the same errors, unattended | paid API, needs explicit approval (A7); GitHub Models was "fully retired" on 2026-07-30 (GitHub docs), so no free route was found | A7; C2 (the proposals must go to a separate file, never the verdict file) |
| (d) No proposal, owner labels from scratch | every label is a human judgement | nothing until the owner acts | zero | contradicts X6; fits WISH #12/#16 |

- Practice: machines find, match and prioritise claims, and humans give the verdicts.
  Full Fact (fullfact.org/ai): "Human experts aren't going anywhere anytime soon". Reuters
  Institute (Graves): automated systems verify only "a narrow range of simple factual
  claims", and fact-checking "will require human supervision for the foreseeable future".
  IFCN asks for a public method, sources a reader can check, a corrections policy and one
  standard. Google ClaimReview asks for a claim "clearly attribute[d] ... to a distinct
  origin" and a traceable source, and Google is "phasing out support for ClaimReview
  markup in Google Search". Each row therefore needs a named claim, a cited source and a
  published method. Design (a) can supply only the method.
- Scout 2 recommends a split. The pipeline writes design (a)'s evidence record and the
  proposed state UNVERIFIED, and it never proposes REAL, OVERHYPED or PUSHED. The owner,
  optionally helped by the agent session (b), upgrades a row by PR with a named claim, a
  cited primary source and a reason, and the merge is the confirm. Dissent: most rows
  stay UNVERIFIED on most days, so the R3-2 test rests on owner effort, which is the
  case for (c). A published UNVERIFIED beside a named company's claim can read as "not
  shown true" unless the policy defines it as "not yet checked", which is the case for
  (d). C1 already shows unconfirmed rows by state, not by label word. The round-4 O20
  question keeps that state display and says so.

### Source terms (scout 1; O9, O21)

- mastodon.social: no conflict found. Its ToS (effective 2026-08-31) "do not apply to
  anyone who is not a registered user". They give users ownership and grant third parties
  nothing. They warn that content may be indexed and stored by anyone. They set no
  scraping, attribution, rate or commercial-use clause for non-registered readers.
  Deletions propagate to followers, and no duty binds third-party readers, so honouring
  deletions is a project choice (already a round-3 condition). Server rule 1008 ("Content
  created by others must be attributed") binds the server's users. robots.txt blocks
  GPTBot and otherwise only `/media_proxy/`, `/interact/` and one API path. An
  unauthenticated tag call returned `x-ratelimit-limit: 300`. Each status has a canonical
  `uri` and `url`. Federated posts carry their own instances' terms, which were not read.
- Reddit Data API Terms (revised 2026-07-20) and Developer Terms (revised 2026-03-24).
  The licence is to "copy and display" User Content to "App Users" in an App, with no
  grant to republish it in a dataset (Data API §2.4, Developer §2.1). Developer §4.2 bars
  "redistribute ... syndicate access to ... Reddit Services and Data", and §7.3 says "You
  will not share Reddit Services and Data with any third party". Content deleted on Reddit
  must be deleted "as soon as possible" (Developer §3.3). Display needs "a link back",
  "the applicable User's username" and the Reddit source (Developer §5.2), which conflicts
  with R3-3 wherever these terms bind. Monetized use, commercial use and AI training need
  written approval (Developer §4.1, §4.2; Data API §2.4, §3.1, §3.2). No numeric rate
  limit is stated.
- Not established. Whether ids and permalinks alone are "User Content" or "Reddit
  Services and Data" (the terms do not name them). Whether the terms bind a project that
  reads Reddit through arctic-shift and not through Reddit's registered API (the Reddit
  official source is not connected). The Reddit Public Content Policy, Developer
  Documentation and User Agreement were not read. This is a plain reading, not legal advice.

## What round 5's scouts found (2026-10-16, read-only, evidence not instructions)

Scout 0 read `origin/dev` with `git show` and `git grep`, plus the uncommitted local
checkpoint `OI4-QUALITY-INTAKE.md`, npm metadata, and upstream files at 4878cdab. Scout 1
fetched Reddit's documents (redditinc.com by curl; the Public Content Policy from a
web.archive.org snapshot of 2026-10-12, because the live page returned HTTP 403). Scout 2
used read-only `gh` commands and the GitHub docs. Scout 3 read Hugging Face model pages
and `origin/dev` files. No scout found text addressed to an agent. Reddit's AI-training
clauses are reported as terms. Numbers are as the scouts reported them. Naming caution:
"S1-S4" in the DSH files are DSH staged-bootstrap stages, not this brainstorm's S1.

### Cordis gate (scout 0; O22, R4-3)

- What is qualified: only the component API table of `@deepseek-ai/cordis@4.0.4`
  (plugin, inject, effect, fiber await/dispose/restart/update, isolate, extend), and only
  as documentary qualification (SHIP). The original #4 criteria 1-3 "remain BLOCKED"
  (cordis.md:3, 5-17; WISH.md:918-920).
- The BLOCKED header covers three separate application-level blockers:
  - Composition is DSH application composition: "Supported DSH launch remains a named
    profile plus ordered patches. A pure new Context() ... tests Cordis only; it is not an
    alternative Harness entrypoint". There is "no accepted observatory plugin entrypoint"
    (cordis.md:23, 27). A second gate is separate: the rc1 launcher force-exits on every
    path, so whole-native disposal completion is unobserved (cordis.md:41).
  - Persistence: evidence must live in a "separately authorized durable evidence
    authority", and "Plugin heap is not durable storage". This waits on Brain #5, which
    is itself BLOCKED on namespace, owner, principals and grants (cordis.md:11, 31;
    WISH.md:922).
  - Tenancy: `isolate()` is service-resolution scope only. Clearing needs independent
    principals and "an all-transport server-enforced principal boundary" (cordis.md:16-17;
    dsh.md:86-111).
- The formal clearing receipt is `receipts.json` turning non-null. Today every
  `live_acceptance` and `prerequisites_missing` field is null, and so are both
  independent reviews (receipts.json:133-174).
- Who can clear it, split three ways:
  - In the repository: #4's qualification work.
  - Upstream: the rc1 launcher's force-exit and its one-operator Web authentication. The
    diagnostic failed with ABI_LOAD_FAILED, cause unknown.
  - Human authority: B1-B9 "still require the named human/custody/spend/platform owners,
    two independent full-plan approvals and fresh formal admission before any #4 code".
  No date exists, by design: the WISH keeps dates and assignees unset. As of 2026-10-16
  the owner's hold is "keep the strict hold; no Run, task, worker, dispatch or release was
  created" (WISH.md:28, 54, 147, 286; OI4-QUALITY-INTAKE.md:10-26, local).
- Upstream moved. `@deepseek-ai/cordis` 4.0.5 is `latest` (published 2026-10-16), and
  the 4.0.4 pin dates from 2026-09-22. A new version clears nothing; it invalidates
  receipts and adds requalification work (cordis.md:3, 49).
- Static builds: cordis.md and dsh.md never mention Pages, static output or Actions.
  - Evidence for a build-time reading: Cordis runs in one process. The upstream
    quick start is `new Context()` -> plugin -> emit -> dispose. The repository's probe
    was a one-shot Node command that "creates no home, profile, credential, socket,
    service or file", and it exited 0 (cordis.md:35; receipts.json:111-124).
  - Evidence for a running-app reading: "Settled component is not complete Web
    application readiness" (cordis.md:12). The WISH designs "One deployable
    Cordis-composed evidence atlas", and its #10 assistant needs `dsh --profile web`
    (WISH.md:44, 449).
  - Whether git-committed files can serve as the "durable evidence authority" is not on
    record.
- This brainstorm's S1 is not one of the WISH's groups. The record neither allows nor
  forbids a Cordis-composed S1. The only Cordis composition ever run was throwaway
  qualification code. The WISH's own groups (#7, #9, #10) may not dispatch "until
  prerequisite acceptance is verified" (WISH.md:38, 159, 180).
- Licence: Cordis 4.0.4 is MIT, and its direct dependencies are MIT. Combining it into
  AGPL code is compatible if the notice is kept. That conclusion is an inference from two
  FSF entries, not one sentence on the FSF page. The transitive closure was not audited
  (C14).

### Reddit terms (scout 1; O21)

- Revisions read:
  - Public Content Policy: "Updated October 06, 2026", read from the archive snapshot.
  - Developer Terms: last revised 2026-03-24.
  - User Agreement: last revised 2026-05-26.
  - Data API Terms: last revised 2026-07-20.
  - Not retrieved (HTTP 403 or an empty shell): the Developer Documentation and the Data
    API Wiki. Developer §5.4 and Data API §4.2 incorporate them by reference. The
    attribution format and the numeric rate limits live there.
- No document names post ids, permalinks or pointers, and none grants a right to
  republish in a dataset. The grant is display-only: Developer §2.1 and Data API §2.4
  ("non-transferable, non-sublicensable, and revocable"). Developer §4.2 bars
  "redistribute ... or syndicate". Correction to round 4: the clause "You will not share
  Reddit Services and Data with any third party" is in §7.2, not §7.3.
- Deletion: content removed on Reddit must be deleted "as soon as possible", with no hours
  or days stated (Developer §3.3). Data API §3.2 says "immediately delete any data not
  required". §7.3 and §8.2 require deletion when data is no longer needed or the app
  stops. A permanent dated Release cuts against these rules wherever they bind. A
  Bitcoin-anchored manifest cannot be edited later (C3, C4), so C15 holds until O21 is
  answered.
- Username: attribution must "cite the applicable User's username" when User Content is
  displayed "in your App" (Developer §5.2). A pointer-only record that displays no content
  is not shown to trigger this; that is a reading, not a clause.
- Archive route: the User Agreement §7 reaches anyone who accesses the Services. It bars
  collection "except as permitted" (robots.txt crawl), and scraping without written
  consent. The Public Content Policy warns against "data brokers". No document mentions
  archives such as arctic-shift. Whether downstream use of a copy collected by someone
  else is covered is not established.
- Research: Reddit permits "non-commercial uses, such as learning and community". It
  describes access it grants researchers itself, and that is not a licence for anyone to
  republish. Whether this project counts as "monetized" (Developer §4.1) is not
  established.
- Scout 1's reading of the O21 options:
  - Pointers with deletions honoured is the shape the deletion clauses expect. It still
    meets the redistribute and share bars if they bind, and permanence cuts against
    retention.
  - A hash per record publishes no Reddit identifier, and no clause addresses hashes.
  - Leaving Reddit out raises no term question.
  These are plain readings, not legal advice.

### Ready time and ranking (scout 2; C12, C13, O24)

- Only two refresh runs exist in the whole Actions history. Both were manual
  (`workflow_dispatch`) and both succeeded: 36m30s and 43m05s, deploy included. Step
  times in the latest run:
  - `run.py`: 37m39s.
  - `pulse.py`: 4m26s.
  - embed: 14s.
  - gate: 1s.
  - commit: 2s.
  The Pages deploy was live about 24s after the commit. No scheduled run has ever fired.
  The earlier "data: daily refresh" commits (2026-10-08..16, about 07:23-07:35 BRT) were
  made locally by the owner's account, so the scheduler delay is unmeasured.
- Cloudflare: the cloudflare job's deploy steps are skipped because
  `CLOUDFLARE_API_TOKEN` is not set, so Pages is the only live target (O11).
- GitHub's docs: scheduled runs can be delayed at high load, especially at the top of the
  hour, and some queued jobs may be dropped. No numeric bound is given. A public repository
  disables its schedule after 60 days without activity. The default branch is `dev`, which
  is valid for schedules.
- The 24h window ends at build time. `pulse.py` takes `NOW` once at import
  (pulse.py:23-25). The page filters on `generated_at` (index.html:856-858).
- Qualifying stories in one snapshot (`pulse.json` of 2026-10-16T21:56Z, 79 stories): 51
  covered "news" stories have a post in the last 24h, enough for a Top 10. Stories first
  seen in that 24h number 33 (32 news). Earlier days had 5-7 first-seen stories each
  (10-11..10-15). A
  "new today" rule could therefore fall under 10 on a quiet day. That is one snapshot, not
  a series.
- Ranking today: heat = (2·log2(1+voices) + non-newsletter, non-official networks +
  1.5·newsletters + 1 if a lab or vendor posted + log10(1+HN points)) · 0.5^(hours since newest post / 48) (pulse.py:970). The
  stored list is grouped by kind, not sorted by heat overall. The page shows the first 15
  news stories. No tie rule exists (pulse.py:845, 973-975; index.html:857-859).

### Portuguese route (scout 3; O23)

- A free route exists inside the existing dependency. `Xenova/opus-mt-en-ROMANCE` runs
  through transformers.js with the `>>pt<<` / `>>pt_BR<<` prefix. It is about 113 MB
  quantised, and the upstream Helsinki-NLP model is Apache-2.0. The Xenova conversion
  itself states no licence (null). Not measured: CPU time for about 100 headlines,
  Brazilian Portuguese quality on AI headlines, and pipeline compatibility with 4.2.0.
- The other routes fail:
  - NLLB-200-600M is CC BY-NC 4.0, a non-commercial licence.
  - MADLAD-400-3B is Apache-2.0 but has no ONNX build and is 11.8 GB.
  - `opus-mt-tc-big-en-pt` is CC BY 4.0 but has no ONNX build; converting it is untested.
- Our own text:
  - `web/index.html` is `lang="en"` with no i18n mechanism. It holds about 500-550 UI
    strings, over 3,000 words (a regex count, approximate).
  - `METHODOLOGY.md` has about 6,760 words, the largest hand-translation job.
  - The `method`, `coverage` and `projects_note` strings in `pulse.json`.
- Third-party text:
  - 79 story headlines (about 1,105 words; each is a post title).
  - 346 post titles in stories, 245 of them from Reddit.
  - 1,022 node sample titles, 557 of them from Reddit.
  - 423 spread entries.
  - Newsletter and official feed names stay as proper names.
- Terms on translating titles:
  - None of the fetched terms mentions translation.
  - HN/YC bars "derivative works" without authorisation.
  - Bluesky's licence runs to Bluesky only.
  - The Reddit and mastodon.social readings are taken from the DRAFT.
  - arXiv metadata is CC0, so arXiv titles may be translated.
  - Only our own text and arXiv titles are clearly translatable under A17.

## What round 6 read in the repository (origin/dev 2bc0ace, read with git show)

The lead read `web/pulse.json` (generated 2026-10-16T21:56:31Z, 79 stories) through `git
show origin/dev:web/pulse.json` into the scratchpad and counted with three small Python
scripts. These are numbers from one snapshot, not a series. "First seen" is the earliest
post in our sample (A11), and the sample starts on 2026-10-10.

- Top 10 under the round-5 default (O24). 51 covered "news" stories have a post in the
  last 24h. Ranked by heat, then newest post, then id, none of the Top 10 was first seen
  in the last 24h. Eight of the ten were first seen on 2026-10-10..13, three to six days
  before the snapshot, and the other two on 2026-10-15. The best-ranked story first seen
  in the last 24h is 11th, and 32 such stories exist. Heat decays from a story's newest
  post, not its first (pulse.py:970), so a story that keeps getting posts stays at the
  top for days. So the heat rule shows "what is big this week", and
  the same stories would lead the briefing on several days running.
- Reddit titles on the public page (O25).
  - Story headlines: 28 of 79 are Reddit post titles (the story `url` is a reddit.com
    link). By kind, that is 10 of 60 news stories and 18 of 19 chatter stories.
  - The heat Top 10 above holds 4 Reddit headlines, and all 10 of its stories have
    Reddit in their spread. The new-today Top 10 holds none.
  - Fallback headlines: 10 of the 28 have a non-Reddit post whose title could serve as the
    headline. The other 18 have a topic `label` (for example "GPT 6", "Muse Spark",
    "Flux 3 Klein"). In this snapshot, each of the 28 has one or the other. The label is
    a short topic name, not a sentence.
  - Story post lists: 245 of 346 post titles are Reddit's (round 5 counted the same).
  - Git history: `web/pulse.json` has 10 commits on `origin/dev`, and each carries Reddit
    titles and person handles in the public history.
- The console (O26). The live page is the five-tab console (Pulse, Papers, Repos, Hype,
  Method; round-1 scout 0). The "about 500-550 UI strings" R5-3 was asked about are this
  console's strings (round-5 scout 3 counted `web/index.html`). `hype.json` is a
  hand-refreshed dossier (82 items, content cutoff 2026-10-07, not in the refresh commit
  set, `verification` empty on all 82). Semantic search runs in the browser over papers
  and repos (MiniLM, 1,680 rows).

## What round 7 read in the repository (origin/dev 2bc0ace, read with git show)

The lead saved `web/hype.json`, `web/pulse.json`, `web/index.html` and `hype_build.py`
from `origin/dev` to the scratchpad and counted with small Python scripts. The figures
come from one snapshot, not a series. No page was fetched. No file held text addressed to
an agent.

- Hype input. `hype_build.py` reads `hype/hype_research.json` (line 26), and run.py calls
  it only "when hype/hype_research.json exists" (line 5). `hype/` is in `.gitignore`
  (line 8), and the folder is absent locally. CONTRIBUTING.md:54 says the dossier is "not
  committed, because it holds raw post excerpts". ARCHITECTURE.md:62-63 puts it "Off the
  automatic path (manual, private input) ... refreshed only when a research pass runs".
  `hype.json` reports `research_generated_at` 2026-10-07T04:18Z and `content_cutoff`
  2026-10-07T03:43Z.
- Dossier prose, our own text (82 items). This is text written by the research pass, not
  quoted from posts. The total is 17,667 words:

  | Field | Words |
  |---|---|
  | `summary` | 3,604 |
  | `notes` | 3,464 |
  | `traction[].notes` | 2,679 |
  | `skeptic[].claim` | 2,321 |
  | `status` | 2,097 |
  | `coord.limitations` | 1,410 |
  | `first_seen_meaning` | 820 |
  | `viral.reason` | 576 |
  | `category` | 367 |
  | `peak_reason` | 329 |

  That is about 2.6 times the method page. A new research pass would write new prose.
  The quoted post text (`posts[].t`) is third-party text, 3,328 words.
- Dossier posts. There are 405: HN 268, X 125, LinkedIn 6, YouTube 4, Telegram 1,
  GitHub 1. Each X post carries `au` (handle), `t` (excerpt), likes, replies, views and
  an `x.com/<handle>/status/<id>` URL. 124 of the 125 URLs carry the handle. The notes
  call views "tool-reported, not API-verified". 43 items also carry `links.x_handle`,
  the project's own account (for example `x.com/claudeai`). No dossier post is from
  Reddit, but 23 citation URLs in 11 items point at `reddit.com`: `skeptic[].url` 11,
  `summary_urls` 7, `status_urls` 5.
- X access in the record. SIGNALS_PLAN says "X only allows automated reading through its
  API". It recommends the paid API "if X matters enough to fund", rejects cookie or
  browser automation ("violates X's terms"), and makes "No X collection" the default.
  `docs/sources/economics-panel.md:60` reads "x:preflight ... BLOCKED:
  paid_access_unapproved". How the research pass read its X posts is not on record.
- Handles inside post URLs in `pulse.json`:
  - story posts: Mastodon 42 of 43 (`mastodon.social/@<user>/<id>`);
  - node samples and spread: Mastodon 180 of 195, X 29 of 29;
  - Reddit permalinks (245 story posts, 710 node entries) carry the subreddit, not the
    user, and leave under R6-2;
  - HN, Lobsters, newsletter, GitHub and arXiv links carry no person handle.
  C6's planned check ("a conversation-network `author` value reaches a public file")
  would fail on these URLs unless they change.
- Gap class (Hype tab). index.html:564 heads the tab "Where does attention run ahead of
  evidence?". index.html:637 says "above the diagonal: talked about more than evidenced".
  The class counts per project, deduplicated (an item appears in several tag views):
  - overall (82): insufficient 64, similar 10, attention_ahead 2, evidence_ahead 6;
  - 30d (68): 55, 6, 1, 6;
  - 7d (58): 47, 4, 2, 5.
  index.html:494 already says "heuristic only, not validation".
- History. `web/hype.json` has 12 commits on `origin/dev` (2026-10-07..16), and
  `web/pulse.json` has 10. Both carry handles, and `pulse.json` also carries Reddit
  titles (A25).

Read by the lead after the scout reported (same snapshot, `git show` / `git grep` only):

- Dossier posts in the daily file. `pulse.py` opens `web/hype.json` and adds every
  dossier post to its pool with `source='dossier'`: text as `title`, handle as `author`,
  likes (else score) as `score`, comments or replies as `comments` (pulse.py:311-318).
  In `pulse.json` this puts 29 X entries in topic nodes (16 spread, 13 samples; 12
  distinct posts), each with `title`, `author` and an `x.com/<handle>/status/<id>` URL;
  the 13 samples also carry `score` and `comments`. Six of the excerpts @-mention other
  accounts. 16 HN entries come the same way. No story post is from X. The daily file
  therefore republishes X text and counts today, with or without the fold.
- Mastodon links by server. `pulse.py` reads nine hashtag timelines on mastodon.social
  (pulse.py:101-121) and keeps mastodon.social's own status id for every post, including
  posts that come from other servers (`s['id']`, line 115). The URL it publishes is the
  origin server's, and `pulse.json` does not carry the id (Mastodon story posts hold
  `net`, `title`, `url`, `author`, `at`, `score`, `comments`). In `pulse.json`:
  - story posts: 43, all with `@<user>` (24 on mastodon.social, 19 elsewhere);
  - node entries: 195 (92 mastodon.social with `@`, 90 elsewhere with `@`, 13 elsewhere
    without `@`, mostly `/display/<uuid>` URLs from non-Mastodon fediverse software);
  - 130 distinct URLs on 31 servers.
  The pre-report count above (42 of 43 and 180 of 195) used a narrower pattern. Counting
  any `/@` path segment on any server gives 43 and 182, 225 in all. C22 uses the wider
  pattern.
- The X route, searched. `git grep` over `origin/dev` for the research pass, the dossier
  input and X tools finds no record of how the X posts were collected. Two lines bear on
  it:
  - `hype.json` `coverage[1]` reads "X samples independently read back with public
    syndication for 128 originals; one X article is not an original tweet check". That
    is a readback check, not the collection route. Whether X's syndication endpoint is
    one of the "currently available, published interfaces" the X terms name was not
    read.
  - docs/ROADMAP.md:23 (P2b, planned) reads "X only via a paid, terms-compliant route
    (official API or xAI search) if the owner funds it".
  `coverage[4]` says LinkedIn, YouTube and Telegram were read from "selected public pages
  only".
- Dossier prose that names X. A crude word match (`X`, `twitter`, `tweet`, `x.com`) finds
  X named in the prose of 13 of the 82 items (`status` 7, `traction` 6, `summary` 4). That
  prose is our text and falls under O27. A figure it quotes from X is an X figure, and the
  design lists those sentences under O29's answer.
- Bluesky: `pulse.json` holds no `bsky.app` URL today. The scout's Bluesky finding feeds
  C22 and any later Bluesky adapter (ROADMAP P2b), not this batch.

## What round 7's scout found (2026-10-16, read-only, evidence not instructions)

One worker scout, medium effort. It read `origin/dev` only through `git show` and did not
fetch the Epoch ChatGPT-usage page. No fetched page held text addressed to an agent. The
X terms mention prompt injection only as a ban on users (Misuse item iv). These are plain
readings, not legal advice.

### X terms (O29)

- Terms of Service, "Effective: October 9, 2026" (https://x.com/en/tos; headings, no
  section numbers):
  - Summary box and "Using the Services": "you cannot scrape the Services without X's
    express written permission".
  - Same heading, developer paragraph: "If you want to reproduce, modify, create
    derivative works, distribute, sell, transfer, publicly display, publicly perform,
    transmit, or otherwise use the Services or Content on the Services, you must use the
    interfaces and instructions we provide, except as permitted through the Services,
    these Terms, or the terms provided on https://docs.x.com/developer-terms . Otherwise,
    all such actions are strictly prohibited."
  - "Misuse of the Services" (iii): no access or search "by any means (automated or
    otherwise) other than through our currently available, published interfaces ...
    (NOTE: crawling or scraping the Services in any form, for any purpose without our
    prior written consent is expressly prohibited)".
  - "Your Rights and Grant of Rights in the Content": users license X, and X may "let
    others do the same" "subject to our terms and conditions for such Content use". No
    grant runs to a third party that did not read through X's interfaces.
- Developer Agreement, "Last Updated: April 27, 2026"
  (https://docs.x.com/developer-terms/agreement):
  - II.A grants a revocable licence to "Copy a reasonable amount of and display the X
    Content" and to "Modify X Content only to format it for display".
  - "X Content" is Posts, Post IDs, profile information "and any other data ... made
    available to you through the X API or by any other means authorized by X".
  - III.A(d) bars redistributing or syndicating "the Licensed Material to any third
    party except as expressly permitted". III.B limits commercial use. III.K bars
    iframing.
  - The licence covers only a reader who accepted the Agreement.
- Developer Policy (https://docs.x.com/developer-terms/policy; no section numbers, no
  stated revision date, page metadata dateModified 2026-09-17), "Content redistribution":
  - "If you provide X Content to third parties, including downloadable datasets or via an
    API, you may only distribute Post IDs, Direct Message IDs, and/or User IDs".
  - Caps: 1,500,000 Post IDs per entity per 30 days. Up to 500 public Post or User
    Objects per person per day only "via non-automated means (e.g., download of
    spreadsheets or PDFs)", and the recipients must agree to X's terms.
  - "By building on the X API or accessing X Content, you must comply with ALL X
    policies".
- Display Requirements (https://docs.x.com/developer-terms/display-requirements; no
  stated revision date, metadata 2026-05-20):
  - "The post author's profile picture, @username, and display name must always be
    displayed and link to the user's X profile."
  - "The post text ... may not be altered or modified."
  - The timestamp must link to the permalink, and the action icons must show, or else
    "View on X".
  - Do not "obscure, or alter the post content or identification of the user".
  - So X's one sanctioned display route requires the handle that R3-3 removed.
- Scout's plain reading: no clause read grants a project that did not read through the
  API a right to republish excerpts or engagement counts on a public page. The ToS
  "Otherwise ... strictly prohibited" paragraph and the scraping bans point the other
  way. Even an API licensee may pass only Post IDs to third parties, and a public page is
  third-party redistribution. Likes, replies and views are X Content as data; no clause
  grants them separately. A bare status link or Post ID is the lowest-risk item, but no
  clause addresses it for a reader outside the API.

### LinkedIn and YouTube (O29)

- LinkedIn User Agreement, effective November 3, 2025, §8.2 "Don'ts":
  - no software or crawlers "to scrape or copy the Services, including profiles and other
    data";
  - no copying, use, display or distribution of "any information (including content)
    obtained from the Services ... without the consent of the content owner";
  - no copying or distribution "(except through the available sharing functionality)" of
    others' posts "without their permission".
  - One line: republishing LinkedIn post text or counts needs the owner's consent, and
    scraping is barred, so no.
- YouTube Terms of Service, effective December 15, 2023, "Permissions and Restrictions":
  - viewing is for "personal, non-commercial use", and videos may be shown "through the
    embeddable YouTube player";
  - no reproducing, distributing or displaying Content except "as expressly authorized by
    the Service" or "with prior written permission from YouTube";
  - no automated access except public search engines or with permission;
  - no harvesting of "usernames or faces".
  - One line: the embed player and the separate API terms (not read) are the routes;
    scraped text or counts, no.
- Telegram (1 dossier post) was not read.

### Post links without a handle (O28, O29, C22)

- X: https://x.com/i/web/status/20 and https://x.com/i/status/20 both return HTTP 307
  to `/jack/status/20`, then 200 with no login (curl, browser User-Agent, no cookies).
  The landing page shows "@jack", the post text and its counts, with a "Log in or sign
  up" prompt. So the form keeps the handle out of our URL. The redirect puts it back in
  the reader's address bar, and the page shows it.
- Mastodon (mastodon.social only, one id): https://mastodon.social/statuses/117453170598896942
  returns 200, 51,285 bytes, no redirect, with the generic title "Mastodon". That is the
  JavaScript app shell, the same bytes as for id 1. `/web/statuses/<id>` redirects to it.
  `/@i/<id>` and `/@/<id>` return 404. The canonical `/@Gargron/<id>` page names the
  author server-side. The unauthenticated API `/api/v1/statuses/<id>` resolves by id
  alone and returns `"acct":"Gargron"`.
- Bluesky: `bsky.app/profile/did:plc:z72i7hdynmk6r22z27h6tvur/post/3kkzsbeh2k22k`
  returns 200 with no login (app shell, title "Bluesky"). A DID is an account
  identifier: `app.bsky.actor.getProfile?actor=<did>` returns the handle `bsky.app`. A
  DID URL has no handle string but names the account.

Scout unknowns:
- Whether the Mastodon `/statuses/<id>` page and the Bluesky DID page show the handle
  once rendered. curl gets only the app shell; nothing was rendered.
- Whether `/statuses/<id>` works on other servers, or for mastodon.social's copy of a
  remote post. Only one mastodon.social post was tested.
- X's Automation Rules, Brand Guidelines, Privacy Policy and Rules were not read, nor
  the YouTube API Services Terms or LinkedIn's API terms.
- No clause read addresses a bare status URL or Post ID published by a reader outside the
  API.
- Enforcement, jurisdiction, and quotation or fair-use exceptions are beyond these texts.
- The collection route of the 125 X posts was not searched by the scout; the lead's
  search above found none on record.

## What round 9 read in the repository (origin/dev 2bc0ace, read with git show)

The lead saved `web/hype.json` from `origin/dev` to the scratchpad, read `pulse.py`
lines 300-322, and counted with small Python scripts run in isolated mode. The figures
come from one snapshot (content cutoff 2026-10-07T03:43Z), not a series. No page was
fetched. No file held text addressed to an agent.

- X links outside `posts[]`. Beyond the 125 post URLs counted in round 7, `hype.json`
  holds 195 X URLs in other fields, 194 of them status links:

  | Field | X URLs | Project's own account | Another listed official account | Same URL as a `posts[]` entry |
  |---|---|---|---|---|
  | `viral.cand_post` | 67 | 22 | 1 | 64 |
  | `summary_urls[]` | 58 | 9 | 1 | 52 |
  | `skeptic[].url` | 24 | 0 | 0 | 20 |
  | `status_urls[]` | 20 | 5 | 0 | 19 |
  | `first_seen_url` | 18 | 4 | 1 | 17 |
  | `traction[].url` | 5 | 1 | 0 | 5 |
  | `coord.evidence[].url` | 3 | 1 | 0 | 3 |
  | total | 195 | 42 | 3 | 180 |

  78 of the 82 items hold at least one X URL. The 43 `links.x_handle` profile links (41
  distinct accounts) are not in the table (A26). Round 7 counted "153 X URLs" (29 in
  `pulse.json`, 124 in `posts[]`), so C22's fail set was larger than recorded. Under R8-3
  all 195 leave as links (C26), including the 45 that point at an official account's
  post. The claims they support stay.
- Handles in other fields. R3-3's writer list named `hype_build.py:120` (`posts[].au`)
  only. The read finds more:
  - `viral.cand_account` is set on 81 items, and 66 of the values are `@handles`. The
    candidate platforms are X 67, LinkedIn 5, YouTube 3, Hacker News 2, Telegram 2,
    GitHub 1 and Blog 1. `viral.account` and `viral.followers` are null on all 82 ("Actual
    first viral origin/follower snapshot not established").
  - `skeptic[]` has 105 entries (`claim`, `by`, `d`, `url`). 22 `by` values hold an
    `@handle` (for example "@VadimStrizheus, sampled X post"). Others name an outlet and
    a journalist ("Matthias Bastian, The Decoder"), a researcher's report, or a LinkedIn
    person.
  - `aliases[]` holds three `@` values, the projects' own names.
  C28 covers them.
- X figures in our prose. `notes` is an object (`momentum`, `traction`, `gap`,
  `confidence`). A sentence with an X term and a numeral appears 14 times in 13 items:
  `notes.momentum` 9, `status` 3, `skeptic[].claim` 1, `skeptic[].by` 1. An example is
  "Security demonstration has 1,692 API-observed likes and 66 replies; 180,805 views
  were reported earlier by x_search." `traction[]` has 143 rows (`type`, `value`,
  `unit`, `ver`, `asof`, `url`, `notes`), and 5 of them cite an X post. C27 lists the
  sentences, and C26 handles the five rows.
- The X route, partly on record. The round-7 search of the repository found no record of
  how the X posts were read. The dossier itself names part of it: "x_search" appears 8
  times (for example "x_search reports the official announcement", "@<handle> via
  x_search"), "syndication" 2 times ("original text read through X syndication API";
  `coverage[1]` "read back with public syndication for 128 originals"), and "API-observed
  likes" once. 15 notes say "tool-reported". What "x_search" ran on, and whether it was a
  paid call, is not on record. ROADMAP P2b names "xAI search" as a paid route the owner
  would have to fund. This corrects "route not on record" in rounds 7 and 8 to "route
  named in part, not established". It decides nothing, because R8-3 keeps all X content
  off both files. C31 discloses it.
- The dossier copy in `pulse.py` (lines 311-318). Each dossier post enters the pool with
  the URL as its id and as its link, the text as `title`, the handle as `author`, likes
  (else score) as `score`, and comments (else replies) as `comments`. C26 states what a
  count-only record keeps.

## WRS bar (round 10, no scouts)

```
 Problem   [####################] 20/20  unchanged: identity, audiences, sole-user test, ready time, languages, Top 10, the fold, all answered
 Scope     [####################] 20/20  the review's scope gaps closed as conditions: method source (C33), takedown path restored (C34), verifier in S5 (C36, flagged)
 Decisions [####################] 20/20  25 settled + 17 outside picks; R9-1 approves the residual traceability items; all 15 findings "not an owner decision"
 Risks     [####################] 20/20  verdict ids survive the 7-day window (C32); stale shown with no deploy (C37); attestation token isolated (C42); count change disclosed (C35)
 Criteria  [####################] 20/20  clock start named per deploy (C39); append-only corrections (C40); ots upgrade (C38); feed assertions listed (C43)
 Total     100/100
```

Evidence: the score stays at 100, because no finding needs the owner. The FIX-FIRST
review does not lower it, for three reasons:
- The reviewer marked all 15 findings "not an owner decision". Its three unmet criteria
  (C5, C7, C14) were faults in how the design was written: a condition dropped, the
  verdict file's ids expiring, the wrong method source file. None was a missing owner
  answer.
- Each finding now has a design condition in the DRAFT (C32-C45). So a design written
  from the DRAFT carries the repair, and does not rely on DESIGN.md's repaired text
  alone.
- The only new owner input, R9-1 "Approve as written", covers the six traceability
  findings. Two of them resolve by the fast-forward, and the other four are approved.
Two moves are flagged, not asked:
- The verifier goes to S5 (A34). It follows the round-1 size triage (S1's slice of S5 is
  "the daily manifest") and the round-3 mapping of WISH #7 and #13 (reproducible rebuild)
  to S5. R3-2's success test does not need a shipped gauge.
- The count correction (A35) changes a fact in R3-3's question, not the owner's pick.
Crystallize: no question is asked, and ## Open is empty.

## WRS bar (round 9, no scouts)

```
 Problem   [####################] 20/20  identity, audiences, sole-user test, ready time, languages, Top 10 rule, the console's fate, all answered
 Scope     [####################] 20/20  dossier prose in PT bounded (R8-1, C24); X, LinkedIn, YouTube counts only in both files (R8-3, C26); every field they reach counted
 Decisions [####################] 20/20  24 settled + 17 outside picks; nothing open; every round-9 finding falls under a settled answer read as written
 Risks     [####################] 20/20  X text, links and figures leave both files; handles in viral and skeptic fields found (C28); X route named in part and disclosed (C31)
 Criteria  [####################] 20/20  C24-C31 are checks: PT hash and review marker, per-post render check, X URL and figure lists, handle patterns
 Total     100/100
```

Evidence: +5 against 95.
- Scope +1. R8-1 takes the 17,667 words of dossier prose off S1's path (C24), and R8-3
  sets what X content the fold carries. The round-9 read counts the rest of what R8-3
  reaches (195 X links in other fields, 5 traction rows, 14 prose sentences).
- Decisions +2. O27, O28 and O29 are answered. The round-9 findings each fall under an
  answer already given: R8-3's "no link" covers the citation links, and R3-3 covers the
  handles in `viral` and `skeptic` fields. The verdict-file rule (C30) and Telegram (C29)
  add scrutiny and are flagged for a question if the owner wants them looser.
- Risks +1. The X text and figures leave the daily file and the dossier. The route the
  record called unknown is named in part by the dossier itself, which is now disclosed.
  The risks that remain are stated, not open: the public git history keeps handles,
  Reddit titles and X excerpts (A25, forward-only); a Mastodon id resolves to its author
  through Mastodon's API (the trade-off in R8-2's option); the X counts rest on a route
  that is not established (the trade-off in R8-3's option).
- Criteria +1. Each condition names the file and the CI fail. The Mastodon render check,
  untested once rendered in round 7, is now a per-post, fail-closed check whose fallback
  is the approved count, so S1 is testable whatever it finds.
- Crystallize: no question is asked, and ## Open is empty.

## WRS bar (round 8, no scouts)

```
 Problem   [####################] 20/20  identity, audiences, sole-user test, ready time, languages, Top 10 rule and the console's fate all answered
 Scope     [###################.] 19/20  what the fold reaches is counted; O27 (dossier prose in PT) and O29 (X content in two files) still set its size
 Decisions [##################..] 18/20  21 settled + 17 outside picks; O27 (reopens R5-3, quote fixed), O28, O29 re-asked with the round-7 facts
 Risks     [###################.] 19/20  X, LinkedIn, YouTube terms read; link forms tested; X text and counts already in pulse.json; route not on record
 Criteria  [###################.] 19/20  C22 and C23 hold in every option; O28's handle-free link form untested once rendered
 Total     95/100
```

Evidence: unchanged against 95. No answer landed, because the ledger refused the round-7
batch on O27's form, and no new fact was read. A re-ask with the quote fixed earns no
point. The reasons each dimension is below 20 are the ones under "WRS bar (round 7, after
the scout report)" below. Not crystallize: O27-O29 are owner decisions.

## WRS bar (round 7, after the scout report)

```
 Problem   [####################] 20/20  identity, audiences, sole-user test, ready time, languages, Top 10 rule and the console's fate all answered
 Scope     [###################.] 19/20  what the fold reaches is counted; O27 (dossier prose in PT) and O29 (X content in two files) still set its size
 Decisions [##################..] 18/20  21 settled + 17 outside picks; O27 (reopens R5-3), O28, O29 asked with the facts behind them
 Risks     [###################.] 19/20  X, LinkedIn, YouTube terms read clause by clause; link forms tested; X text and counts already in pulse.json; route not on record
 Criteria  [###################.] 19/20  C22 closes C6's URL gap in every option; C23 brings dossier records under each network's rule; O28's link form untested when rendered
 Total     95/100
```

Evidence: +1 against 94.
- Risks +1. The X terms are now read clause by clause, with revision dates, and LinkedIn's
  and YouTube's in one line each. All three read against republishing text or counts
  from outside their interfaces. The handle-free link forms are tested. The lead's
  follow-up read found that the exposure is not only the fold's: `pulse.json` carries 29
  X entries from the dossier today (C23). The score is not 20 for three reasons:
  - How the X posts were collected is still not on record.
  - Whether the syndication readback counts as a published interface was not read.
  - The X text stays on the daily page until O29 is answered.
- Criteria unchanged in score. C22 makes the handle check cover URLs, and it holds in
  every O28 and O29 option. It is not 20 because whether the Mastodon handle-free page
  renders the post is untested (O28's recommended option names a logged-out link check).
- Scope, Problem and Decisions unchanged: three owner decisions are asked.
- Not crystallize: O27-O29 are owner decisions.

## WRS bar (round 7, before the scout report)

```
 Problem   [####################] 20/20  identity, audiences, sole-user test, ready time, languages, Top 10 rule and the console's fate all answered
 Scope     [###################.] 19/20  fold settled (R6-3); what the fold reaches is counted, but dossier prose in PT (O27) and X content (O29) still set its size
 Decisions [##################..] 18/20  21 settled + 17 outside picks; O27 (reopens R5-3), O28, O29 wait on the scout report
 Risks     [##################..] 18/20  Reddit text off the pages (R6-2, C20); new: X excerpts with an unrecorded route, handles in post URLs, X terms unread
 Criteria  [###################.] 19/20  Top 10 recompute check (C19), Reddit check (C20), fold checks (C21); C6 fails on handle URLs until O28
 Total     94/100
```

Evidence: +1 against 93.
- Problem +1: R6-3 says what "the thing as a whole" covers.
- Criteria unchanged in score but not in content. R6-1 makes the Top 10 checkable (C19).
  O28 opens a gap: C6 as written fails on 42 + 180 Mastodon and 29 + 124 X URLs.
- Scope unchanged. The fold is settled, but it carries about 17,700 words of our own
  prose that R5-3 was never shown, and 125 X posts.
- Risks unchanged. R6-2 closes the Reddit page exposure. The fold opens an equal one: X
  post excerpts and metrics whose collection route is not on record, while the
  repository's own record says X is "BLOCKED: paid_access_unapproved". X's terms are
  unread.
- Decisions unchanged: three owner decisions are open and wait on the scout.
- Not crystallize: O27-O29 are owner decisions.

## WRS bar (round 6, no scouts)

```
 Problem   [###################.] 19/20  identity, audiences, sole-user test, ready time, size, languages; what "the thing as a whole" covers waits on O26
 Scope     [###################.] 19/20  delivery gate gone (R5-1); manifest and languages bounded (R5-2, R5-3); the console's fate (O26) still sets how much S1 rebuilds
 Decisions [##################..] 18/20  18 settled + 17 outside picks; O24, O25, O26 asked with the facts behind them
 Risks     [##################..] 18/20  manifest exposure closed (C16); Reddit titles on the page and in git history found and counted; Reddit developer docs still unread
 Criteria  [###################.] 19/20  R3-2 clock start testable (R5-1); C16-C18 checkable; the Top 10 rule (C13) waits on O24
 Total     93/100
```

Evidence: +3 against 90.
- Scope +2. R5-1 replaces the unbounded gate (no date, human owners, upstream changes)
  with a one-shot build that has a checkable form (C18). R5-2 and R5-3 bound the manifest
  and the language layer. The score is not 20 because O26 decides whether S1 rebuilds
  the whole console or adds new pages beside it.
- Risks +1. C16 removes Reddit identifiers from the only artifact that can never be
  edited. The page exposure is now counted, and so is the git history (10 commits). The
  score is not 20 for three reasons:
  - Reddit titles stay on the page until O25 is answered.
  - The Developer Documentation was never retrieved.
  - Whether the terms bind reads through arctic-shift is not established.
- Criteria unchanged. The clock start and C16-C18 are now checkable, but the ranking rule
  that cuts the Top 10 is open again. The heat default fails the owner's stated wish for
  "the immediate unknowns" on the one snapshot read.
- Problem and Decisions unchanged: three owner decisions are asked.
- Not crystallize: O24, O25 and O26 are owner decisions.

## WRS bar (round 5, after the scout reports)

```
 Problem   [###################.] 19/20  identity, audiences, sole-user test (R3-2), ready time (X16), size (X17), languages (X15)
 Scope     [#################...] 17/20  S1 content bounded; X15 route found and own-vs-third-party text counted; delivery gate unbounded (no date, human owners, upstream) until O22
 Decisions [##################..] 18/20  15 settled + 17 outside picks; O21, O22 (reopen R4-3), O23 asked with the facts behind them; O24 waits with a default
 Risks     [#################...] 17/20  Reddit terms read (dev docs still unread); anchored manifest vs deletion duty found (C15); Cordis MIT; NLLB fails NC; Reddit titles already on the public page
 Criteria  [###################.] 19/20  C12 measured (cron 45 7 * * *, window end stated), C13 ranking found, C14-C15 added; S1 start not testable until O22
 Total     90/100
```

Evidence: +2 against 88.
- Risks +1. The Reddit terms are now read clause by clause, and the conflict between a
  permanent anchored manifest and the deletion duty is found and held by C15. Cordis's
  licence is MIT, and the one free translation model that fails on licence (NLLB, CC
  BY-NC) is ruled out. The score stays below 20 for three reasons:
  - The Developer Documentation was not retrieved.
  - Whether Reddit's terms bind reads through arctic-shift is not established.
  - The public `pulse.json` already carries 245 Reddit post titles in stories and 557 in
    node samples, an exposure wider than the manifest (Open, flagged).
- Criteria +1. C12 now rests on measured run times, a stated cron and a stated window
  end. C13 has the ranking code, and C14-C15 are checkable. It is not 20 because the start
  of R3-2's 14-day clock is not testable while O22 is open.
- Scope unchanged. The Portuguese route and the text split bound X15. Scout 0 showed the
  Cordis wait has no date and no in-repo clearing path, which offsets that gain.
- Decisions unchanged: no answer landed, and three owner decisions are now asked.
- Not crystallize: O21, O22 and O23 are owner decisions.

## WRS bar (round 5, before the scout reports)

```
 Problem   [###################.] 19/20  identity, audiences, sole-user test (R3-2), plus ready time (X16), size (X17), languages (X15)
 Scope     [#################...] 17/20  S1 content bounded, but its delivery is gated on Cordis BLOCKED with no date (R4-3); X15 adds a bilingual layer with no route yet
 Decisions [##################..] 18/20  15 settled + 17 outside picks; O20, O17, O15 answered; O21, O22, O23 wait on this round's facts
 Risks     [################....] 16/20  FALSE exposure, now with a Portuguese edition; Cordis gate unbounded; Reddit pointers still unread; translated third-party titles
 Criteria  [##################..] 18/20  C9-C13 make the evidence record, upgraded rows, FALSE reply path, 06:00 and Top 10 checkable; S1's start date not testable while the gate is open
 Total     88/100
```

Evidence: roughly flat against 87. Decisions +2 and Criteria +2: R4-1 fixes the
proposer (evidence record, UNVERIFIED, owner upgrade by PR) and R4-2 the label set, which
turn into C9-C11; X16 and X17 turn into C12 and C13. Problem +1 for the ready time, size
and language now stated. Scope -2: R4-3 puts S1 behind cordis.md's "composition/
persistence/tenancy BLOCKED" (a gate whose clearing route cordis.md ties to an
unobserved launcher completion receipt, line 41), and X15 adds a layer the pipeline has
no route for. Risks -2 for the same two reasons plus the Brazilian exposure of FALSE.
Not crystallize: three owner decisions (O21-O23) wait on facts this round reads.

## WRS bar (round 4, after the scout reports)

```
 Problem   [##################..] 18/20  identity, name, first screen, audiences, sole-user phase and the S1 success test (R3-2) stated
 Scope     [###################.] 19/20  S1 testable, rest roadmap (R3-1); feed starts from zero, no model code, live CI run confirmed; adapter form waits on O15
 Decisions [################....] 16/20  12 settled + 14 outside picks; O20, O17, O15 asked this round with the facts behind them; O21 (Reddit) waits on one read
 Risks     [##################..] 18/20  proposer mislabel exposure assessed (scout 2); mastodon.social clear; Reddit terms read, ids-as-pointers not established
 Criteria  [################....] 16/20  R3-2 + R2-4 + C1-C8; verdict-row checks wait on O20 and O17
 Total     87/100
```

Evidence: Problem unchanged. Scope +1: scout 0 shows exactly what S1 builds new (the
feed, the verdict file and the evidence record, from zero) and what it reuses (a live
daily Pulse run and a stdlib pipeline), so S1's content is bounded. The adapter form still
waits on O15. Decisions unchanged: no answer landed this round, though O20's options are
now set out with the facts behind them. Risks +1: the proposer exposure named in round 4
is assessed (scout 2: no field can tell a claim's truth, a rule-driven OVERHYPED would
publish an implied factual judgement from attention data, and GitHub Models is retired),
and mastodon.social is clear. Reddit holds the score below 20: its terms read against
open redistribution and require username attribution, and whether bare ids and
permalinks are allowed is not established. Criteria +1 for C7 and C8, each checkable from
`pulse.json` and the evidence record.

## Gap map

```
 identity + first screen + look (R1-1, X4, X5, X12, R3-4)      SETTLED
      |
      +--> information architecture: briefing page + gauge header + method/audit pages
      |      (R1-4 several static pages; D5 / ROADMAP line 3 amendment = design output)
      |      WISH: none of 20 issues superseded; explorer keeps #8 shell (R3-4)
      |      today's five-tab console: folded into dehype (R6-3), C21   SETTLED
      |        Pulse -> briefing + all stories; Papers/Repos -> output-by-area
      |        drill-down; Hype -> project page; Method -> method page; search stays
      |        Hype rests on a manual research pass (gitignored input), stamped
      |        dossier prose in PT, ~17,700 words: English first, PT once
      |          reviewed (R8-1, reopens R5-3), C24                SETTLED
      |        X posts: 125 in hype.json, 29 entries in pulse.json via
      |          pulse.py:311-318 (C23): counts only, LinkedIn and YouTube
      |          too (R8-3), C26                                   SETTLED
      |          + 195 X links in citation and viral fields, 5 traction rows,
      |            14 prose sentences (round 9 read): C26, C27  design condition
      |          route named in part in the dossier (x_search, syndication),
      |            not established; disclosed (C31)       design condition
      |        handles in viral.cand_account (66) and skeptic[].by (22):
      |          R3-3, C28                                 design condition
      |        Telegram (3 values): counts only, C29        design condition
      |
      +--> gauge header: names (R2-1) + launch gate (R2-4)      SETTLED
      |      slots: output by area, Hype vs substance, Daily movers show today
      |      Hype vs substance substance side: story's own links only, node
      |        samples "related in topic" (C8)                  design condition
      |      `official` false = offline rebuild; live CI run fetches it (fact,
      |        round-4 scout 0); unfetched reads "not fetched" (C7)
      |      risk event log, jobs panel: honest placeholders (A16)
      |      no gauge reads "shipped" in S1; recompute verifier in S5
      |        (C36, A34 flagged; O30 deferred)              design condition
      |      coverage figure = sources[] status                 design condition
      |
      +--> verdict rows  <-- REAL/OVERHYPED/UNVERIFIED on claims (R1-2, X10) SETTLED
      |                  <-- PUSHED document proof only (R2-2)              SETTLED
      |                  <-- Data + you, git file (X6, X7), C2 alias check
      |                        + per-day story-id archive, bot-written alias
      |                        file, so rows outlive the 7-day window (C32)
      |                  <-- removal requests and deleted posts (C34),
      |                        append-only corrections check (C40)
      |                  <-- "proposed, not reviewed" until confirmed (WISH #12/#16, C1)
      |                  <-- proposer: evidence record, UNVERIFIED, owner
      |                        upgrades by PR (R4-1), C9, C10              SETTLED
      |                  <-- FALSE added, owner-set only (R4-2), C11        SETTLED
      |                  <-- person handles removed (R3-3), C6 check        SETTLED
      |                        no test asserts on `author`; 33 page reads (scout 0)
      |                        handles inside post URLs: Mastodon 43 + 182,
      |                        X 29 + 124 (+ 195 in hype.json citation and
      |                        viral fields, round 9); C22 extends C6 to URLs
      |                                                            design condition
      |                        Mastodon: handle-free link, else count (R8-2),
      |                          per-post fail-closed render check, C25    SETTLED
      |                        X: no link at all (R8-3), C26               SETTLED
      |                  <-- primary source never an X post URL (C30)
      |                        flagged: R8-3 did not name the verdict file
      |
      +--> briefing: Top 10, rest one click away (X17), C13       designable
      |      ranking: new today first, heat fill, ties newest post then id
      |        (R6-1), C19 recompute check                      SETTLED
      |      ready 06:00 BRT (X16), C12: run+deploy 36-43 min (n=2, manual);
      |        cron -> 45 7 * * * (04:45 BRT), re-fit after 7-10 runs   designed
      |        Cordis step (C18) unmeasured, must fit the 15-min margin
      |      24h window ends at pulse.py NOW (~05:25 BRT), printed   designed
      |
      +--> languages EN + PT from day one (X15)
      |      our text in both, headlines as posted (R5-3), C17   SETTLED
      |      own text ~500 UI strings + 6,760-word method; the fold (R6-3)
      |        rewrites every console string; dossier prose English first,
      |        PT once reviewed, off S1's path (R8-1), C24      SETTLED
      |
      +--> RSS / JSON feed out (X8), C1 validation, EN + PT (C17)  designable
      |      no feed output exists today; built from zero (scout 0)
      |      adapters on the qualified Cordis API now (R5-1)     SETTLED
      |
      +==> S1 DELIVERY GATE                                      CLEARED by R5-1
      |      one-shot Node step in Actions, no server, git as store (C18)
      |      pin 4.0.4, MIT notice, licence closure audited (C14)
      |      no WISH Run or dispatch; no claim of #4 acceptance (C18)
      |      R3-2's 14-day clock starts on the first scheduled run that passes S1
      |
      +--> audit floor (R1-3) + store (R2-3), C3, C4             SETTLED
             manifest = ids + URLs, no handles (A17, R3-3)      design condition
             mastodon.social pointers: no conflict found (scout 1)        CLOSED
             Reddit in the manifest: hash of canonical record bytes only
               (R5-2), C16                                     SETTLED
             Reddit on the public pages and pulse.json: counts only, no
               title, permalink or username (R6-2), C20         SETTLED
             git history: 10 pulse.json + 12 hype.json commits carry
               handles (and Reddit titles); forward-only (A25)  flagged
             ots upgrade home and verify route (C38); attestation in its
               own job (C42)                          design condition
             method source = root METHODOLOGY.md + .pt.md (C33)
             scrub changes dossier-path node counts until ~2026-11-06,
               measured and disclosed (C35, A35)       flagged

 design review, round 9: FIX-FIRST, 15 findings, none an owner decision;
   repaired in DESIGN.md, carried here as C32-C45      design condition
   traceability: refresh.yml resolves (fast-forward); 2 R5-3 cites and
     2 placeholder tokens approved as written (R9-1)   SETTLED

 S1 acceptance as a whole: R3-2 (owner's daily use, 14 days)    SETTLED
   clock starts on the per-deploy checks (C39)        design condition
 roadmap only (R3-1): S2 policy beyond S1 rows, S3 risk/jobs sources (O12, O6),
   S4 awareness (A10), S5 verifier inputs (O30), S6 bubble leaders (O4b),
   G1 governance (O16)

 Walls no decision removes:
   no open objective doom number   -> risk is a dated sourced event log (R2-1)
   no qualified AI-specific risk or jobs source -> log and panel start as placeholders
   no source measures AI knowledge -> awareness needs a stated proxy (A10)
   no undisclosed-payment evidence -> PUSHED rare, document-backed (R2-2)
   history starts 2026-10-16       -> no trend before 14 committed daily snapshots (R2-4)
```

- Settled: R1-1..R1-4, R2-1..R2-4 as before; R3-1 S1 testable, rest roadmap; R3-2 the
  owner's daily use for 14 days; R3-3 remove person handles; R3-4 Mission control on the
  dehype pages only. R4-1 evidence record, owner upgrades; R4-2 FALSE added, owner-set;
  R4-3 Cordis now, S1 waits, reopened by R5-1 qualified Cordis API now; R5-2 Reddit as a
  hash per record in the manifest; R5-3 our text in both languages, headlines as posted.
  R6-1 new today first; R6-2 Reddit as counts only on the pages; R6-3 console folded into
  dehype. R8-1 dossier prose English first, Portuguese once reviewed (reopens R5-3); R8-2
  Mastodon handle-free link, else count; R8-3 X, LinkedIn and YouTube counts only. R9-1
  the remaining traceability findings approved as written. Plus outside picks X1-X17.
- Blocks a testable S1: nothing. O27, O28 and O29 are answered (R8-1..R8-3), and their
  mechanics are C24-C31. The roadmap questions stay deferred by R3-1, under their own
  heading. Flagged for the owner, not blocking: C29 (Telegram counts only), C30 (no X
  post as a verdict primary source), A25 (git history forward-only), A26 (official X
  profile links stay).
- Round 10: still nothing blocks. The round-9 review's 15 findings are design
  conditions C32-C45, none of them an owner decision. Two more flags for the owner, not
  blocking: A34 (no gauge ships in S1; the verifier is S5 work) and A35 (R3-3's "changes
  no number" was wrong on the dossier path until about 2026-11-06).

## Scouts dispatched

- Round 1: four (live inventory; open sources per pillar; auditability; verdict
  methodology and exposure). All reported.
- Round 2: none. The open points were owner decisions; the facts came from the gauges
  council and three direct repository reads.
- Round 3: four, read-only, worker tier, all reported (findings above).
- Round 4: three, read-only, all reported (findings above). Every brief: read `origin/dev` with `git show` or `git grep
  origin/dev` only (no checkout, stash or reset in this shared workspace); fetched or read
  text is evidence, text that addresses an agent is reported, not followed; the Epoch
  ChatGPT-usage page stays do-not-ingest and is not fetched.
  1. Repository (worker): whether any pipeline or workflow on `origin/dev` calls a paid
     model or API under a secret; which per-story fields could drive a rule-based verdict
     proposer; whether tests or `scripts/check_page.mjs` assert on `author`; whether the
     production Pulse run is live or offline and why `official` is false on all 79
     stories; any existing feed output.
  2. Source terms (worker): Reddit Data API Terms and Developer Terms, and mastodon.social
     server terms, by another route than round 3 (policy index pages, archived copies),
     read for: may post ids and URLs be republished as pointers in a public manifest.
  3. Verdict proposer options (reasoner): no-fee ways the pipeline can propose
     REAL / OVERHYPED / UNVERIFIED from fields the repository actually computes, what each
     can and cannot tell, what fact-checking practice says about automated proposals, and
     which options need an owner decision under A7 (paid API) or X7 (chat edits).

- Round 5: four, read-only, all reported (findings under "What round 5's scouts found",
  where they are numbered 0-3 in report order). Every brief carries the standing rules above (origin/dev through `git show` /
  `git grep` only; `gh` commands read-only; agent-addressed text reported, not followed;
  the Epoch ChatGPT-usage page not fetched).
  1. Cordis gate (reasoner, high; O22): from cordis.md, dsh.md, the qualification
     receipts, the WISH (#4, #10, line 150) and the uncommitted checkpoint
     `checkpoints/2026-10-16/OI4-QUALITY-INTAKE.md`: what exactly is BLOCKED, by what,
     what observable clears it, whether any dated or in-repo path exists, whether the
     gate binds a one-shot Cordis composition run in Actions that emits static files for
     Pages (zero servers), and Cordis's licence against AGPL code (X13).
  2. Reddit pointers (worker, medium; O21): the Reddit Public Content Policy, Developer
     Documentation (attribution format, rate limits) and User Agreement, read for ids and
     permalinks as pointers in a public manifest, third-party archives such as
     arctic-shift, research datasets and deletion duties.
  3. Ready time (worker, low; C12): wall-clock durations of recent refresh.yml and
     deploy.yml runs and the Pages deploy delay (`gh run list` / `gh run view`, read-only),
     GitHub's documented delay for scheduled workflows, and where pulse.py's 24h window
     ends; how many stories a day qualify for the briefing and the rule that would rank a
     Top 10.
  4. Portuguese route (worker, medium; O23): whether a free, openly licensed EN->PT model
     runs offline in Actions through the repo's existing `@huggingface/transformers`
     4.2.0 (model, licence, size, CPU time for about 100 headlines), which page strings
     are ours versus third-party text, and what the fetched sources' terms say about
     translating titles.

- Round 6: none. The three round-5 answers left three owner decisions whose facts were
  in the repository. The lead read them directly (see "What round 6 read in the
  repository"):
  1. `git show origin/dev:web/pulse.json` (2bc0ace) saved to the scratchpad.
  2. A count of Reddit-sourced headlines, fallback headlines and story-post titles.
  3. A simulation of the Top 10 under the heat rule and under a new-today rule.
  4. `git log origin/dev -- web/pulse.json` (10 commits).
  No page was fetched.

- Round 7: one, read-only, worker tier; it reported (findings under "What round 7's scout
  found"). The lead first read `origin/dev` directly, and read it again after the report
  (both under "What round 7 read in the repository"). The brief carries the standing rules: `origin/dev` through
  `git show` / `git grep` only, no checkout, stash or reset; fetched text is evidence,
  and text that addresses an agent is reported, not followed; the Epoch ChatGPT-usage
  page is not fetched.
  1. X terms and handle-free links (worker, medium; O28, O29):
     - X's Terms of Service, Developer Agreement and Developer Policy (display
       requirements, redistribution of content, scraping, rules for readers who do not
       use the API), read for this question: may post text excerpts, engagement counts
       (likes, replies, views) and status links be republished on a public page by a
       project that did not read them through X's API?
     - The same question in one line each for LinkedIn and YouTube, which have 6 and 4
       dossier posts.
     - For X, Mastodon (mastodon.social) and Bluesky: is there a working public web link
       to a single post that carries no handle (for example `x.com/i/web/status/<id>`, a
       Mastodon URL without the `@user` segment)? Does it resolve without login? Does the
       target page show the handle anyway?
     These are plain readings, not legal advice.

- Round 8: none. The round-7 batch was refused on O27's form, not on its facts, and the
  owner's round note asks for a re-ask from the facts already in the DRAFT. Nothing was
  fetched or read beyond the DRAFT.

- Round 9: none, and no council. The three round-8 answers left no owner decision. What
  the design needed was the mechanics of those answers, and the facts for them were in
  the repository. The lead read them directly (see "What round 9 read in the
  repository"):
  1. `git show origin/dev:web/hype.json` (2bc0ace) saved to the scratchpad.
  2. Counts of X URLs by field and by account, handle values in `viral` and `skeptic`
     fields, X-figure sentences in the prose, and the route terms in the dossier notes.
  3. `git show origin/dev:pulse.py`, lines 300-322.
  No page was fetched. A per-post Mastodon render check was not run before the design: it
  is part of the approved option and has the approved fallback (C25).

- Round 10: none, and no council. The round-9 review's findings carry their own
  evidence, and the reviewer marked each one "not an owner decision". No fact the design
  needs is missing. The lead read three things directly (see "What round 10 read"): the
  round-9 workflow journal for the review's result and the repair's summary, DESIGN.md
  (the repaired text), and `git rev-parse` for the checkout state. No page was fetched.
  The OpenTimestamps verify route that C38 names is checked by the design write, not by
  a scout.

## Open

None. Closed-question records, O11 and the roadmap questions are under their own
headings below. Round 10 adds no open question. A34 and A35 are flagged under Assumed.

## Closed questions (record, moved out of ## Open in round 9)

Closed in round 9 by the owner's round-8 answers: O27 (R8-1, reopening R5-3), O28
(R8-2), O29 (R8-3).

Closed in round 7 by the owner's round-6 answers: O24 (R6-1), O25 (R6-2), O26 (R6-3).

Round-8 record, kept: these three were asked in the round-8 batch and are answered by
R8-1, R8-2 and R8-3. They were the last items blocking a testable S1. Their facts are under
"What round 7 read in the repository" and "What round 7's scout found". They were first
written for the round-7 batch. The ledger refused that batch: O27 quoted R5-3 as "Our
text, headlines original", without the recorded answer's "(Recommended)". Round 8 asks
the same three with the same options. Only O27's quote changes.

- O27 Dossier prose in Portuguese, asked as a reopen of R5-3 (reopens field R5-3). The
  question quotes R5-3's recorded answer verbatim, "Our text, headlines original
  (Recommended)", then → and the new text, once for each reopen option. The text after
  each → is that option's label: "English first, PT later" and "Dossier prose English
  only". The "Keep R5-3, translate all" option is not a reopen and carries no →. Options:
  - English first, Portuguese later (recommended; reopen). The Portuguese Hype page shows
    each dossier's prose in English under a Portuguese notice. A dossier switches to
    Portuguese once the owner has reviewed its draft. S1's checks and R3-2's clock do not
    wait on the review. Trade-off: the Portuguese edition carries English blocks for a
    while, and every research pass adds more until it is reviewed.
  - Keep R5-3 and translate all 17,667 words before S1 passes. Trade-off: the largest
    review on S1's path, repeated after each research pass. The 2,321 words of sampled
    criticism of named projects also appear in Portuguese, which raises the Brazilian
    exposure R5-3's question named.
  - Dossier prose in English only (reopen), with a Portuguese notice. Page text, labels
    and structured fields are bilingual. Trade-off: Portuguese readers never get the
    prose in Portuguese. It is the least work and keeps the criticism out of the
    Portuguese edition.
  The pre-report option "structured fields only, prose stays in `hype.json`" is not
  offered. It would take the prose off the project page R6-3 approved, so it would ride
  on R6-3. If the owner wants it, it gets its own question quoting R6-3.
- O28 Mastodon post links that carry the author. In every option, no handle appears in
  our files (C22), and that includes the dated manifest. X links are not in this
  question: they follow O29, because all 29 X links in `pulse.json` come from the
  dossier. Options:
  - Handle-free link, else count (recommended). Each post links to
    `mastodon.social/statuses/<id>` with mastodon.social's own id. The fetcher holds that
    id on the runner for posts from all 31 servers (pulse.py:115), but `pulse.json` does
    not publish it today, so carrying it through is design work. The form is used only after a logged-out
    check in a real browser shows the post. A post the check fails on shows as a count.
    Trade-off: the author is one click away on Mastodon's page, and the id resolves to
    the author through Mastodon's public API. This is how HN links already work here.
  - Post text, no link. The post shows its text, network and date, with no link and no
    author. Trade-off: the reader cannot open the post or check the text against it.
  - Counts only, as R6-2 does for Reddit: no text, no link. Trade-off: the 238 Mastodon
    entries lose their text as well, although round 4 found no conflict with
    mastodon.social's server terms.
  Keeping `@user` URLs is not offered. It would change R3-3 and would need its own
  reopen question.
- O29 X content in `hype.json` and `pulse.json`. The answer also covers the dossier's 6
  LinkedIn and 4 YouTube posts, whose terms read the same way, and the question says so.
  Under an option with links, a LinkedIn or YouTube post gets a link only where its URL
  names no account. Handles stay removed in every option. Options:
  - Counts only, no X text (recommended). Each project shows how many X posts our sample
    holds. No excerpt, handle, link, likes, replies or views (C23 checks `score` and
    `comments`). The sentences in our prose that quote an X figure are listed and follow
    the same rule. Trade-off: the count comes from a collection route that is not on
    record, and the reader cannot open any X post.
  - Counts plus status links (`x.com/i/web/status/<id>`), no text or figures. Trade-off:
    the link redirects to the handle URL. The Developer Policy lets only API users pass
    Post IDs to third parties, and no clause addresses a link published by a reader
    outside the API.
  - Excerpts and figures without the handle, with a status link. Trade-off: on the
    scout's reading no clause grants this, and the one sanctioned display route requires
    the @username. This is the highest exposure.
  - X off the public files, counts and the scores built from X posts included, until an
    X route is on record (ROADMAP P2b: paid API or xAI search, if the owner funds it).
    Trade-off: the scores of projects whose attention is mostly on X change when they are
    recomputed without those posts. The other options keep scores built from the same
    unrecorded route.
- Not asked, flagged: the single Telegram dossier post (terms not read) and the 268 HN
  dossier posts follow the rules those networks already have. Disposition in round 9:
  Telegram takes the stricter counts-only rule (C29), and the HN rule is written out as
  A31.

Round-7 pre-report text of O27-O29, kept for the record (the asked versions are above):

- O27 Dossier prose in Portuguese. This is a reopen of R5-3 if any option narrows it.
  The fold (R6-3) puts the Hype dossiers on a dehype page. Their prose is our own text
  written by the research pass: 17,667 words across 82 projects, about 2.6 times the
  method page. Each new research pass writes more. R5-3 ("Our text, headlines original")
  was asked with "about 500 page strings plus a 6,760-word method page", and this text
  was not counted. Under R5-3 as it stands, the agent drafts all of it in Portuguese and
  the owner reviews it before S1 passes, so the 14-day clock waits on that review.
  Options expected:
  - keep R5-3 and translate the dossiers too, with the cost stated;
  - reopen R5-3 so the dossier prose shows in English with a Portuguese notice, each
    dossier gaining Portuguese once the owner has reviewed it;
  - the Hype page shows structured fields only (numbers, sources, dates) in both
    languages, and the prose stays in `hype.json`.
- O28 Post links that carry the author's handle. R3-3 removed handles from the public
  data and pages. Its question counted bylines and did not mention URLs. Today 42 of 43
  Mastodon story-post links and 180 node links carry `@<user>`, 29 X node links and 124
  of 125 X dossier links carry `<handle>`. C6's check would fail on them. Handles stay
  removed in every option, so this is not a reopen of R3-3. Options expected:
  - a handle-free link where the network offers one, else a count;
  - no conversation-network post links at all.
  The scout reports which handle-free forms exist. Keeping links that show the handle
  would change R3-3 and would need its own reopen question.
- O29 X content on the Hype page. The dossier holds 125 X posts with excerpts, likes,
  replies, views and handles. The repository's own record says X is "BLOCKED:
  paid_access_unapproved" and makes "No X collection" the default. How the research pass
  read these posts is not on record. This is the R6-2 shape for X. Options expected:
  - counts and figures only, no X text, the way R6-2 treats Reddit;
  - excerpts without handles, with a handle-free link if one exists (O28);
  - X left off the page until X access is decided (SIGNALS_PLAN decision 1).
  The scout reads X's terms first.

Closed in round 6 by the owner's round-5 answers: O22 (R5-1, reopening R4-3), O21
(R5-2), O23 (R5-3). Their record is further down.

Round-6 record, kept: these three were asked in the round-6 batch and are answered by
R6-1, R6-2 and R6-3 (closed above).

- O24 The Top 10 ranking rule (C13). It was held under "waits, with a design default" in
  round 5. Round 6 read the snapshot, and the default (heat, then newest post, then id)
  put no story first seen in the last 24h into the Top 10. Eight of the ten
  were three to six days old in our sample. The owner's earlier direction (memory) is
  "the immediate unknowns, judged relevant on sight", so the default no longer stands
  without the owner. The options are:
  - New today first, heat fill (recommended). Stories first seen in the last 24h, ranked
    by heat, then the rest by heat up to 10. Ties break by newest post, then by stable
    id. On the snapshot read, all 10 are new. On earlier days, 5-7 stories a day were
    first seen, so 3-5 slots would be heat fill. Trade-off: "first seen" is relative to
    our sample (A11), so a story we picked up late counts as new.
  - Heat only, as the page ranks today. Trade-off: the same multi-day stories lead on
    several days running.
  - Heat with a cap of 3 slots for stories older than 48h. Trade-off: one more published
    number to justify.
- O25 Reddit titles on the public pages and in `pulse.json` (the item R5-2 left flagged).
  28 of 79 headlines are Reddit post titles, 245 of 346 story posts are Reddit's, and 557
  node samples are. The pages are rebuilt daily, so they can drop a deleted post, but the
  committed `pulse.json` stays in public git history. Displaying Reddit content needs the
  username (Developer §5.2), which R3-3 removed, wherever those terms bind. The options:
  - Counts only, no Reddit text (recommended). A Reddit-titled story takes its headline
    from a non-Reddit post (10 of 28) or from its topic label (the other 18; every one of
    the 28 has one or the other in this snapshot). Reddit appears as a count of posts in
    the spread, with no title, permalink or username. This matches R5-2. Trade-off: the
    reader cannot click through to the Reddit thread, and 18 headlines become short topic
    names such as "GPT 6".
  - Titles with a link back, deletions honoured on each rebuild. Trade-off: no username,
    so this meets Developer §5.2 head-on wherever it binds; git history keeps every title.
  - Permalinks only, no titles. Trade-off: a pointer still lands in git history, and a
    bare "Reddit thread" link tells the reader little.
  Adding usernames back is not offered. It would change R3-3 and would need its own
  reopen question.
- O26 What happens to today's five-tab console (Pulse, Papers, Repos, Hype, Method). "Redesign
  the thing as a whole" and X4 (the briefing is the first screen) set the home page, but
  no answer says what becomes of the other tabs. In every option our text is bilingual
  (R5-3), handles are removed (R3-3), and the observatory explorer keeps its #8 shell
  (R3-4). The console is not the explorer. The options:
  - Fold it into the dehype pages (recommended). Pulse becomes the briefing and the "all
    stories" page. Papers and Repos become the drill-down of "Releases / research output
    by area". Hype becomes a project page that shows the same state display as the
    briefing. Method becomes the method page. Search stays. All of them use the Mission
    control look. Trade-off: the largest S1. Every console string is rewritten in both
    languages, and the Hype page rests on a hand-refreshed dossier (cutoff 2026-10-07,
    `verification` empty on all 82) until it joins the refresh.
  - Keep the console as a linked "tracker" page in its current look, with its text made
    bilingual. Trade-off: two looks side by side, and the old view the owner said did not
    improve stays.
  - Retire the console. Trade-off: the in-browser semantic search over papers and repos and
    the Hype dossiers leave the site. Their data files stay in git.

Closed in round 5 by the owner's round-4 answers: O20 (R4-1), O17 (R4-2), O15 (R4-3).

Round-5 record, kept: these three were asked in the round-5 batch, with the facts the
round-5 scouts read, and are answered by R5-1, R5-2 and R5-3 (closed above).

- O22 What S1 does under the Cordis gate. This is a reopen of R4-3: "Cordis now, S1
  waits" -> new. The wait is unbounded (scout 0):
  - No date is on record, by design.
  - Clearing needs #4 work in the repository, upstream rc1 changes, and named human
    owners with two independent approvals.
  - The 2026-10-16 hold is strict.
  The three BLOCKED items are application-level: DSH composition, a durable evidence
  authority and tenant principals. The record says nothing about a one-shot static build.
  The lead reads it this way: a zero-server Actions build that uses only the qualified
  4.0.4 component API, with git as the store and no tenants, does not reach them. That is
  a reading, not a fact on record.
  The options are:
  - Reopen to "qualified Cordis API now" (recommended).
  - Keep R4-3, build the data layer only, and hold the public briefing.
  - Reopen to plain build-time modules, with Cordis later.
  The question also settles a point scout 0 left open: whether R4-3 meant the WISH's
  full #4 tuple or only Cordis component use. The council is not proposed for this,
  because new facts, not more lenses, were what was missing.
- O21 How Reddit appears in the daily public input manifest (R2-3). Reddit is in the
  nets of 40 of 79 stories. The terms name no ids or permalinks. Deletion is due "as soon
  as possible", and a Bitcoin-anchored Release cannot be edited (C15). Whether the terms
  bind reads through arctic-shift is not established, and the Developer Documentation was
  not retrieved. The options are:
  - A hash per record only (recommended). It must hash the record bytes or be salted,
    because short sequential base36 ids are enumerable.
  - Ids and permalinks with deletions honoured.
  - Reddit left out of the manifest.
  Connecting the official Reddit API (secrets exist, not connected) would bind the
  Developer Terms directly, and it would be asked on its own.
- O23 What "English + Portuguese from day one" (X15) covers. The options are:
  - Our own text in both languages, with headlines in their original language
    (recommended).
  - That plus machine-translated headlines through `opus-mt-en-ROMANCE`, labelled as
    machine translation.
  - The page chrome and policy pages in Portuguese from day one, and the method page
    later.
  The free route exists, so A7 is not triggered. No source's terms grant translating
  titles, except arXiv (CC0).

Round-5 text of O24, kept for the record (asked in round 6 with a different
recommendation, above):

- O24 The Top 10 ranking rule (C13). The default is the existing heat score
  (pulse.py:970), over covered "news" stories with a post in the last 24h (A23). Ties
  break by newest post, then by stable id. The alternative is "new today first, then
  heat", which matches the owner's wish for "the immediate unknowns". On ordinary days
  only 5-7 stories are first seen in 24h, so that rule needs a heat fill to reach 10.
  The question is asked if the owner's 14-day use (R3-2) shows the default fails, or in
  the next batch with room.

Round-5 flag, kept for the record (asked in round 6 as O25, above):

- The public `pulse.json` on Pages already carries Reddit post titles: 245 in story post
  lists and 557 in node samples, gathered through arctic-shift. The Reddit display terms
  (link back, username, deletion) and R3-3 meet on that page, not only in the manifest.
  The design states how page titles follow O21's answer. If the answer needs more than
  O21's options cover, it gets its own question.

Closed since round 1: O1 (R1-1, X4, X5), O2 (R1-1; order in the split above), O3
(R1-4), O4 (R1-2, X10, R2-2), O5 (R1-3, R2-3), O7 (X8), O10 for the sole-user phase
(X6, X7). Round 2 settled the gauge names (R2-1) and the launch gate (R2-4). Round 3
closed O19 by fact. Round 4 records the owner's answers to the round-3 batch: O18 (R3-1),
O8 (R3-2), O13 (R3-3), O14 (R3-4).

Closed by fact in round 4: O9 for mastodon.social (no conflict; scout 1), the cost of
R3-3 (no test asserts on `author`; scout 0), and whether the production Pulse run is live
(it is; scout 0).

Round-4 record, kept: these three were asked in the round-4 batch and are answered by
R4-1, R4-2 and R4-3 (closed above).

- O20 How the pipeline proposes a verdict (X6 "pipeline proposes, owner confirms"). It
  fixes the verdict file schema, what an unconfirmed row carries, and whether a paid
  model is involved (A7). Options from scout 2: (a) rules write an evidence record and
  propose UNVERIFIED, and the owner upgrades by PR (recommended); (b) the agent session
  drafts labels; (c) a capped paid model in Actions. Option (d), no proposal, is not
  offered: it would amend X6, and C1 already keeps label words off unconfirmed rows,
  which removes most of what (d) adds. If the owner wants (d), it gets its own question
  quoting X6.
- O17 Whether a claim shown false gets its own label (the scope item says "fake"; X10 has
  no FAKE). The FALSE option quotes X10 old -> new. In every option UNVERIFIED means "not
  yet checked against a primary source" (A18). The scope item keeps its spelling either
  way.
- O15 Whether S1's feed and frontend adapters are build-time modules run in GitHub Actions
  with Cordis adoption waiting on the observatory WISH (A12), or Cordis now. "Cordis now"
  means S1's feed waits until cordis.md's "composition/persistence/tenancy BLOCKED"
  clears.

Round-5 pre-report text of O21, kept for the record (the asked version is above):

- O21 How Reddit appears in the daily public input manifest (R2-3). Reddit is in
  the nets of 40 of 79 stories. The Data API and Developer Terms read against
  redistributing "Reddit Services and Data" and require deleting content removed on
  Reddit. They require the username in attribution, which R3-3 removed. They do not name
  ids or permalinks, and whether they bind reads through arctic-shift is not settled by
  their text. Asking now would ask the owner to weigh a risk the record cannot yet state.
  Next round, one worker reads the Reddit Public Content Policy, the Developer
  Documentation (attribution format, rate limits) and the User Agreement for ids,
  permalinks, third-party archives and research datasets. Expected options then: ids and
  permalinks as pointers with deletions honoured; a hash per Reddit record only (proves
  the inputs existed, but outsiders cannot re-fetch them); or Reddit left out of the
  public manifest. Connecting the official Reddit API (secrets exist, not connected)
  would bind the Developer Terms directly and would be asked on its own.

## Scheduling the agent owns (O11; moved out of ## Open in round 9, unchanged)

Scheduling, not decision (the agent owns sequencing, memory roadmap-ownership-and-hosting):

- O11 Fixes the redesign inherits: add `hype.json` to the refresh commit set (round 7:
  this changes nothing on CI, because the dossier input is gitignored), make the
  explorer fetch paths relative, drop the Cloudflare job from `deploy.yml` (round-5 scout 2:
  its deploy steps are skipped today because `CLOUDFLARE_API_TOKEN` is unset), and move the
  refresh cron to `45 7 * * *` (C12). The D5 and
  ROADMAP line-3 amendment that R1-4 approved is written by the design as an output.

## Roadmap decisions, deferred by R3-1 (moved from Open in round 4; out of ## Open to its own heading in round 7, announced)

R3-1 put S2-S6 and G1 on a roadmap, not in testable specs. These questions belong to those
pillars; the design lists each on its roadmap entry and they are asked when that pillar is
designed. They are not dropped, and the owner can pull any of them forward.

- O12 What "how doomed are we" means for the risk event log (S3). Round-3 scout 4: no
  meaning has an AI-specific qualified source; AIID is nearest for deployment incidents
  but its terms bar bots and commercial use. In S1 the log is an honest placeholder (A16).
- O6 Which external indicators come first (S3). Only BLS qualifies, for general labour
  context; the pick follows O12.
- O4b How "becoming popular against bubble leaders" is framed (S6, A9). With claim labels
  (R1-2), leaders' claims are rated on the same scale as anyone's.
- O16 Phase-1 "open suggestions" channel and what triggers phase 2 (G1, X3, X2).
- A10 Which stated proxy the awareness map uses (S4).
- O30 (added in round 10, announced; MEDIUM-2, C36) How the S5 recompute verifier checks
  the voice-based gauge components. The dated manifest carries no handles (R3-3) and
  carries Reddit only as hashes (R5-2). The published lists are capped (round-3 scout 1).
  So an outsider can recompute the arithmetic from a numbers-only gauge-input asset, but
  not the voice counts themselves. The question is asked when S5 is designed. Until then
  R2-4's ship rule cannot be met for those components, and C36 keeps every gauge in
  preview.

## Assumed

- A7 no paid source, API or chain fee without explicit approval.
- A8 existing pipelines and stable ids are the data floor.
- A11 the repo's honesty rules bind every new surface.
- A13 the licence change applies forward; earlier releases keep MIT / CC BY 4.0.
- A15 R2-4's "fields already in pulse.json" reads as fields the pipeline computes today
  (confirmed by scout 1).
- A16 the jobs panel and the risk event log are honest placeholders; slot composition is
  design detail.
- A17 CC BY-SA covers our selection, arrangement and computed fields, not third-party
  text or handles (round-4 scout 1 agrees for mastodon.social and Reddit).
- A18 UNVERIFIED means "not yet checked against a primary source". This is load-bearing,
  so it is not assumed silently: the O17 question states it in its text.
- A19 "06:00 BRT" is America/Sao_Paulo wall-clock, and "ready" means live on Pages.
- A22 America/Sao_Paulo is fixed UTC-3, so the cron `45 7 * * *` is 04:45 BRT
  (unverified by scout 2; checkable).
- A23 the Top 10 is cut from the covered "news" stories, and chatter and complaints stay
  one click away (O24 holds the ranking rule).
- A24 Under R5-1 the pages stay static HTML and JS files that read data files. The Cordis
  frontend adapters emit data and string tables for each frontend and language, and they
  do not generate HTML. This keeps D5's "no build" part for the pages themselves, and
  R1-4 asked only about "several static pages". Not load-bearing: either form passes the
  same acceptance checks.
- A25 R3-3, R5-2 and O25 apply from the change forward. The 10 committed versions of
  `pulse.json` in public git history keep their Reddit titles and person handles. A
  history rewrite would be destructive to a shared public repository, so it is not done.
  If the owner wants it, it gets its own question.
- A25 covers `web/hype.json` too: 12 commits (2026-10-07..16) carry handles and X
  excerpts (round 7 count). Still forward-only, still flagged.
- A26 a project's own X account (`links.x_handle`) is an official account and stays
  under R3-3. Flagged: O28 and O29 do not change it, and if the owner reads it otherwise
  it gets its own question. Round 7: it still holds after the scout. It is a link to a
  project's profile, not a post, excerpt or count, so the Post-ID rule and the display
  rules do not reach it, and C22 exempts it by field.
- A29 likes, replies and views on X are X Content, as the scout reads the Developer
  Agreement's definition. They are not our computed fields, so A17's CC BY-SA does not
  cover them.
- Not assumed: that `mastodon.social/statuses/<id>` behaves on other servers, or for a
  remote post's copy, as it did for the one post tested. R8-2's option checks it before
  use, per post, and C25 makes that check fail-closed.
- A27 the `lang` tag comes from the source's metadata, else `und`.
- A28 topic labels used as fallback headlines are names and are not translated.
- A30 (round 9) R8-3's "no link" covers every X status link in `hype.json` and
  `pulse.json`, in citation and "viral" fields too, not only `posts[]`. This is the
  option's text ("No excerpt, handle, link"), applied as R6-2 was applied to Reddit
  citations. Not load-bearing beyond what R8-3 settled: the claims stay, and only the
  links go (C26).
- A31 (round 9) the 268 HN dossier posts and the 16 HN dossier entries in `pulse.json`
  follow the HN rule already in force: the handle (`au`, `author`) is removed (R3-3), the
  `news.ycombinator.com/item?id=` link stays because it names no person, and the text
  shows as HN story titles already do on the page. Not load-bearing for S1: it changes
  nothing that the page shows today except the handle. Flagged, because YC's terms bar
  derivative works "except as expressly authorized" (round-3 scout 3). If the owner wants
  HN excerpts treated as counts, it gets its own question.
- A32 (round 9) the three `@` values in `aliases[]` are the projects' own names, as
  `links.x_handle` is the project's own account (A26), so they stay and C28 exempts the
  field. Not load-bearing: three values, checkable by hand.
- A33 (round 9) in `skeptic[].by`, a journalist's or researcher's name on a published
  article or report is an author name that stays, as R3-3 keeps paper authors and
  newsletter names. A poster on a conversation network is not, and becomes "<network>
  user" (C28). Not load-bearing: the claim and its source note stay either way.
- A34 (round 10; MEDIUM-2, C36) the recompute verifier that R2-4's ship rule needs is S5
  work, so no gauge reads "shipped" during S1. The grounds:
  - The round-1 size triage lists S1's slice of S5 as "the daily manifest".
  - Round-3 scout 2 mapped WISH #7 and #13 (reproducible rebuild) to S5.
  - R2-4's question asked what dehype shows before 14 snapshots exist.
  - R3-2's success test is the owner's 14 days of use, not a shipped gauge.
  - The agent owns sequencing (memory).
  It is not load-bearing for S1's checks, because every gauge already carries the
  preview label, and trends still return after 14 ledger days as R2-4 records. It is
  flagged because it means no gauge reaches "shipped" inside S1. If the owner wants a
  gauge able to ship within S1, that gets its own question, and it meets O30 first.
- A35 (round 10; MEDIUM-1, C35) correction to the record. R3-3's question said "The
  counts (voices, spread, coordination signals) are computed on the runner, so removing
  the handles changes no number". That holds for the fetchers' own posts. It does not
  hold for the dossier path: `pulse.py` counts the public `hype.json`'s dossier authors as
  node voices. So the scrub changes node voices, weight and signal until the 2026-10-07
  dossier posts leave the 30-day window, about 2026-11-06. R3-3's pick still stands,
  because every R3-3 option was about handles, not counts. The design measures the
  change and the method page states it. Flagged. The one alternative the reviewer named
  is to time the scrub after those posts age out, which keeps the handles public until
  then. That would delay what R3-3 removed, so it gets its own question if the owner
  wants it.
- A36 (round 10) R9-1 "Approve as written" covers the six traceability findings the
  question listed, and nothing else. Two resolve by the fast-forward. The design write
  may fix the other four (C45) without asking, because a citation to the current answer
  and a date spelled as a pattern change no decision. Not load-bearing.
- A12 was answered against the assumption by R4-3, and R5-1 then set what the gate means
  (qualified API now, one-shot build). A14 was answered by R3-1, and the proposer by R4-1.
  A20 was answered by R5-3 and A21 by R5-1.

## Settled

- **R1-1** (round 2, decision): What should the first release of the redesigned site be? (Every option stays inside the standing rules: no invented numbers, no paid sources.) — owner picked "Reality digest, today's data (Recommended)"
- **R1-2** (round 2, decision): Which verdict labels may the site publish, about what, and on what proof? — owner picked "Claim labels, sourced (Recommended)"
- **R1-3** (round 2, decision): For the first version, what should 'fully auditable, we will do the blockchain for that' mean? — owner picked "No-fee stack, Bitcoin anchor (Recommended)"
- **R1-4** (round 2, decision): Approved roadmap decision D5 says "Keep web/index.html one static file, no build". D5 says to revisit it once a second kind of page goes live, and the investigation explorer is one. The redesign would trigger that. Change D5? — owner picked "Several static pages (Recommended)"
- **R2-1** (round 3, decision): You picked the gauges "Progress by area, Hype temperature, Jobs signal, Risk/doom meter". The gauges council (5 lenses) asks to name each gauge for what our data can actually measure. The change: "Progress by area" -> "Releases / research output by area" (labelled as output volume, not capability); "Hype temperature" -> a per-story "Attention vs substance" gauge (spread vs official post, repo, paper); "Jobs signal" -> a panel that says "no qualified source" until a licensed source passes qualification; "Risk/doom meter" -> a dated, sourced risk event log, no dial. Plus "Daily movers" for ups and downs, and no single combined State of AI score. Which names does the gauge header use? — owner picked "Council names, keep 'Hype'"
- **R2-2** (round 3, decision): Your 4 story labels include PUSHED (financed or orchestrated to look hyped). Settled R1-2 allows only sourced claim labels, and PUSHED is about how a story spread, not a claim. Our coordination signals (bursts, new accounts, near-duplicates) are unvalidated. Per scout 3, saying a named company paid for or orchestrated hype implies a provable fact (no opinion shield in the US; near difamacao in Brazil; FTC/EU bar is proof of an undisclosed paid connection). In every option PUSHED labels a story, topic or project, never a person or account. What proof does PUSHED need? — owner picked "Document proof only (Recommended)"
- **R2-3** (round 3, decision): Trends and 'fully auditable' (R1-3) need each day's raw inputs kept durably. Today they live in an Actions cache that can be evicted and a 30-day artifact, and the old Cloudflare R2 plan was dropped. You said GitHub Pages is fine 'if all the data is there and working', with deterministic links. Where do daily inputs and the daily ledger live? — owner picked "Ledger on Pages + Releases (Recommended)"
- **R2-4** (round 3, decision): History starts 2026-10-16, so no gauge has 14 days of data yet. GitHub Pages is public, so 'only you use it' means a site labelled as preview, not a hidden one. What does dehype show before 14 committed daily snapshots exist? — owner picked "Up to 4, trends held (Recommended)"
- **R3-1** (round 4, decision): Seven pillars are in scope and nothing is dropped. Round 3 found that the first release (S1: the 'dehype' identity, a daily briefing in the Mission control look, the gauge header, the RSS/JSON feed, a verdict file in git, the audit floor) can be built on today's data. Three gauge slots have real values now (output by area, Hype vs substance, Daily movers). Risk and jobs start as honest placeholders. How much should the design written from this brainstorm specify in testable detail (acceptance checks a reviewer can run)? — owner picked "S1 testable, rest roadmap (Recommended)"
- **R3-2** (round 4, decision): You are the only user until a second person arrives (your words: 'im gonna be the only initial user until the second human comes'). R2-4 already says when a single gauge counts as shipped: 14 ledger days, a green recompute verifier, and your confirm. What test says the first release (S1) as a whole has succeeded? — owner picked "Your daily use, 14 days (Recommended)"
- **R3-3** (round 4, decision): Public pulse.json and hype.json name the people who wrote posts on conversation networks (HN, Reddit, Mastodon, Bluesky). That is 641 unique handles in topic samples and 265 in story post lists, shown as bylines in 3 places on the page. The counts (voices, spread, coordination signals) are computed on the runner, so removing the handles changes no number. Because the published lists are capped, the counts cannot be recounted from public data today, with or without hashes. No source's terms grant a right to republish handles. GitHub and Bluesky terms point to honouring removal requests. Newsletter and official feed names, paper authors and repo owners stay in every option. What happens to person handles in the public data and pages? — owner picked "Remove person handles (Recommended)"
- **R3-4** (round 4, decision): Your Mission control look (dark HUD, few big numbers, thin glowing lines) is the look of the dehype pages. The observatory WISH's accepted issue #8 picked 'Guided questions first' for the investigation explorer (your selection, 2026-10-09). Its design record says the explorer's shell uses "the existing tracker's system font, blue controls and neutral borders" and that "Differences are traversal and disclosure structure, not palettes". The explorer (#9) is not built yet. Round 3 found that none of the WISH's 20 issues is superseded by this redesign. This look is the one place where they can collide. How far does Mission control reach? — owner picked "dehype pages only (Recommended)"
- **R4-1** (round 5, decision): How does the pipeline propose a verdict for each Daily briefing story? Your pick X6 says 'pipeline proposes, owner confirms or overrides'. Round 4 found that no story carries claim text or a repo or paper link of its own, that no computed field can tell whether a claim is true, that the repository has no model code at all, and that GitHub Models (the free hosted route) was retired on 2026-07-30. Fact-checkers (Full Fact, Reuters Institute) use machines to find and prioritise claims and humans to give the verdicts. In every option, an unconfirmed row shows 'proposed by the pipeline, not reviewed' and its evidence, with no label word, until you confirm it in git (C1, WISH #12/#16). PUSHED is set only by hand, with the document cited (R2-2). — owner picked "Evidence record, you upgrade (Recommended)"
- **R4-2** (round 5, decision): Does a claim shown false get its own label? Your words were 'whats real, whats fake'. Your pick X10 is "4 labels": REAL / OVERHYPED / PUSHED / UNVERIFIED, with no FAKE or FALSE. OVERHYPED corresponds to fact-checkers' Half True / Mostly False. Calling a named company's claim false states something that has to be provable: in the US there is no opinion defence, and in Brazil it comes close to calúnia/difamação, though sourced scientific criticism is excluded and the company gets a free right of reply within 60 days. In every option, UNVERIFIED means 'not yet checked against a primary source'. The pipeline never proposes a false-claim label, and the scope item 'real, fake, overhyped, financed to look hyped' keeps its spelling. — owner picked "Add FALSE, you set it (Recommended)"
- **R4-3** (round 5, decision): How are S1's feed and frontend adapters built? You asked to 'think modularly cordis plugins etc' (X8). The observatory WISH makes Cordis the composition layer (WISH:150 'Cordis owns application component lifetimes'). The repository's own record says Cordis is 'Contract-qualified; application composition/persistence/tenancy BLOCKED' (docs/integrations/cordis.md). X7 and X14 say zero servers. No feed output exists today, so the S1 feed is built from zero either way. — owner picked "Cordis now, S1 waits" · reopened by R5-1
- **R5-1** (round 6, decision): Your R4-3 answer was "Cordis now, S1 waits". Round 5 read the gate. It has no date, by design. Clearing it needs three things: work in this repository (#4), upstream DeepSeek changes to the rc1 launcher and its one-operator login, and named human owners with two independent approvals. The repository's 2026-10-16 record says "keep the strict hold". All three BLOCKED items concern a running DSH application: DSH app composition, a durable evidence store (Brain #5, itself BLOCKED) and separate tenant principals. The record says nothing about a one-shot build. Cordis itself runs in one process with no server, and the repository's own Cordis probe was a one-shot Node command. Your answer also settles a point the record leaves open: whether "S1 waits" meant the observatory WISH's full #4 acceptance, or only S1's use of Cordis components. The two reopen options would change the answer like this: "Cordis now, S1 waits" -> "Qualified Cordis API now", or "Cordis now, S1 waits" -> "Plain modules now, Cordis later". The "Keep" option leaves R4-3 as it is. The lead's reading that a zero-server build falls outside the gate is a reading, not a statement on record. What should S1 do? — owner picked "Qualified Cordis API now (Recommended)" · reopens R4-3
- **R5-2** (round 6, decision): Reddit appears in the spread of 40 of the 79 stories. It is read through arctic-shift, a third-party archive, not through Reddit's API. Under R2-3, each day's input manifest goes on a dated GitHub Release whose SHA256 is anchored in Bitcoin (C3, C4), so the manifest can never be edited. Round 5 read Reddit's terms, except the developer documentation (blocked, HTTP 403). They name no post ids or permalinks and grant display rights only. They bar redistributing 'Reddit Services and Data' and require deleting removed content 'as soon as possible'. No clause settles whether they bind a project that never uses Reddit's API. This is a plain reading, not legal advice. This question covers the manifest only. Reddit titles already shown on the public page are flagged separately under Open. How do Reddit records appear in the public input manifest? — owner picked "Hash per record only (Recommended)"
- **R5-3** (round 6, decision): You picked "English + Portuguese" from day one (X15). Our own text is about 500 page strings plus a 6,760-word method page. It can be written in Portuguese by hand: the agent drafts, you review. The headlines are other people's post titles, 79 stories in one day's file. A free offline model fits the existing toolchain: opus-mt-en-ROMANCE, Apache-2.0 upstream, about 113 MB. Its converted copy states no licence, and its speed and Brazilian Portuguese quality are untested. Of the source terms read, none grants translating titles except arXiv (CC0), and Hacker News bars derivative works. A Portuguese edition also makes the Brazilian audience explicit, which raises the weight of FALSE and PUSHED labels. What does Portuguese cover in S1? — owner picked "Our text, headlines original (Recommended)" · reopened by R8-1
- **R6-1** (round 7, decision): The Daily briefing shows a Top 10, with the rest one click away (your pick X17). Round 5 planned to rank it by the heat score the page already uses (voices, networks, newsletters, HN points, decaying from a story's newest post). Round 6 tested that on the 2026-10-16 snapshot. Of 51 news stories with a post in the last 24h, the heat Top 10 held no story first seen in the last 24h. Eight of the ten were first seen 3-6 days earlier, and the best new story ranked 11th. Your earlier direction was 'the immediate unknowns, judged relevant on sight'. 'First seen' means the earliest post in our sample, which starts 2026-10-10. This is one snapshot, not a series. How should the Top 10 be ranked? — owner picked "New today first (Recommended)"
- **R6-2** (round 7, decision): Reddit post titles are on today's public page: 28 of the 79 story headlines, 245 of the 346 post titles in story lists, and 557 topic samples. Your R5-2 answer ('Hash per record only') kept Reddit out of the manifest except as hashes, and it covered the manifest only. The pages are rebuilt daily and can drop a deleted post, but each committed pulse.json stays in public git history. Reddit's terms tie displaying its content to showing the username, which you removed (R3-3), wherever those terms bind. Whether they bind a project that reads through the arctic-shift archive is not established. This is a plain reading, not legal advice. Usernames stay removed in every option. How does Reddit appear on the public pages and in pulse.json? — owner picked "Counts only, no text (Recommended)"
- **R6-3** (round 7, decision): Your words: 'the view didnt [improve], lets redesign the thing as a whole'. The Daily briefing becomes the first screen (X4), but no answer yet says what becomes of today's console tabs: Pulse, Papers, Repos, Hype (82 project dossiers, hand-refreshed, last cut 2026-10-07, not in the daily refresh) and Method, plus the in-browser search over papers and repos. In every option our own text is in English and Portuguese (R5-3), person handles are removed (R3-3), and the observatory explorer keeps its own look (R3-4). The console is not the explorer. What happens to the console? — owner picked "Fold into dehype (Recommended)"
- **R8-1** (round 9, decision): Your R6-3 answer folds the console into dehype, so the 82 Hype project dossiers move onto a dehype page. Their prose is our own text, written by the research pass: 17,667 words, about 2.6 times the 6,760-word method page, and each new research pass writes more. When you answered R5-3, the question counted about 500 page strings plus the method page. This prose was not counted. Under R5-3 as it stands, the agent drafts all of it in Portuguese and you review it before S1 passes, so the 14-day clock (R3-2) waits on that review. 2,321 of those words are sampled criticism of named projects, and a Portuguese edition raises the Brazilian exposure that R5-3's question named. In every option, page text, labels and structured fields stay in both languages, and headlines stay as posted. The two reopen options would change your answer like this: "Our text, headlines original (Recommended)" → "English first, PT later", or "Our text, headlines original (Recommended)" → "Dossier prose English only". The 'Keep R5-3' option leaves R5-3 as it is. What does Portuguese cover for the dossier prose? — owner picked "English first, PT later (Recommended)" · reopens R5-3
- **R8-2** (round 9, decision): Your R3-3 answer removed person handles from the public data and pages. Mastodon post links carry the author inside the URL, shaped like mastodon.social/@<user>/<id>. pulse.json has 225 of them: 43 in story posts and 182 in topic entries, across 31 servers. The planned check fails any public post URL whose path names a person account, so these links change in every option, in the dated manifest too. Round 7 tested one handle-free form. mastodon.social/statuses/<id> opens without a login, but only the app shell was fetched, so whether the rendered page shows the post, and its author, is untested, and only one mastodon.social post was tried. Our fetcher already holds mastodon.social's own id for every post, including posts from other servers, but pulse.json does not publish that id today. Mastodon's public API turns that id back into the author. mastodon.social's terms have no clause for readers who are not registered (round 4). X links are asked separately. Keeping @user links is not offered, because it would change R3-3. How do Mastodon posts appear in our public files? — owner picked "Handle-free link, else count (Recommended)"
- **R8-3** (round 9, decision): Folding the console into dehype (R6-3) puts the dossier's 125 X posts on the Hype page, with their text excerpts, likes, replies, views and handle links. pulse.py copies every dossier post into the daily file, so 29 X entries from the same dossier already reach pulse.json today. This question covers both files. The repository's record says X access is 'BLOCKED: paid_access_unapproved' and makes 'No X collection' the default, and how the research pass read these posts is not on record. Round 7 read X's terms (a plain reading, not legal advice). The Terms of Service bar scraping and bar displaying or distributing content outside X's own interfaces. Even an API user may pass only Post IDs to third parties. X's display rules require the @username, which R3-3 removed. No clause covers a bare status link published by someone outside the API, and x.com/i/web/status/<id> redirects to the URL with the handle in it. LinkedIn's terms (6 dossier posts) and YouTube's (4) read the same way, so this answer covers them too. Under an option with links, a LinkedIn or YouTube post gets a link only where its URL names no account. Person handles stay removed in every option, and the link to a project's own official X account stays. What X content appears in hype.json and pulse.json? — owner picked "Counts only, no X text (Recommended)"
- **R9-1** (round 10, decision): The traceability check found 6 blocking finding(s) in DESIGN.md before review: Decisions #23 (line 117): `.github/workflows/refresh.yml` does not exist under /Users/feliperosa/workspace/repos/trending-research; Scope IN #12 (line 37): R5-3 was reopened by R8-1; cite the current answer instead; Scope IN #15 (line 40): R5-3 was reopened by R8-1; cite the current answer instead; Scope IN #20 (line 45): `.github/workflows/refresh.yml` does not exist under /Users/feliperosa/workspace/repos/trending-research; line 43: placeholder <date>; line 157: placeholder <date>. A row whose Source does not resolve needs your answer to cite. How should the next run go on? — owner picked "Approve as written (Recommended)"
- **R10-1** (round 11, review-findings): The design review returned FIX-FIRST after this run's repair (1 of 2 repairs used). Open findings: HIGH-1 (HIGH) The removal and deleted-post path (C34) skips dossier posts, so the design's promise that a deleted or removal-listed post leaves the pages, pulse.json, briefing.json and the feeds on the next daily rebuild does not hold for them. Row 7 defines the mechanism over 'every stored post' and says a post found gone 'is deleted from the history DB, so no later run reloads it'. But pulse.py builds its pool as stored posts plus internal_posts(), and internal_posts() reloads every dossier post from web/hype.json on every run. Neither the recheck nor the DB delete reaches that population. Two concrete cases: the 16 HN dossier entries in pulse.json, and the 268 HN dossier posts the Hype page shows with text under A31. Nothing in CI rewrites hype.json, so removals.json and the recheck never reach the Hype page until a manual research pass. The success-criterion proof only loads stored HN, Mastodon and Bluesky posts into a scratch DB, so it would pass while the claim fails.; HIGH-2 (HIGH) The browser-side stale rule misses a briefing made off schedule. The rule marks a briefing stale only when its generated_at is before the last 06:00 BRT deadline minus 24 hours. Take a briefing generated after 06:00 on day D, by a late scheduled run or a manual workflow_dispatch (the only kind of run this repository has ever had). If the D+1 scheduled run is dropped or fails, that briefing reads fresh all of D+1, until 06:00 on D+2. At D+1 07:00 the threshold is D 06:00, and 14:00 D is later than that. This is the silent carryover that C5 ('fail loudly') forbids, and it contradicts C37's own fixture: 'a briefing dated the previous day, viewed after 06:00, reads stale'. None of the design's three fixture cases covers a previous-day briefing generated after 06:00.. How should the next run go on? — owner picked "Repair again (Recommended)"

## Asked

_No open questions._

## Size

- **G** · raised by lead · round 1

## Scope ratchet

- Redesign the view as a whole around the identity: omnichannel AI reality digested to human · added by lead · round 1
- Real state of AI progress by area (how much did we really advance) · added by lead · round 1
- Risk state (how doomed are we) · added by lead · round 1
- AI and jobs · added by lead · round 1
- Daily ups and downs · added by lead · round 1
- Curated newsfeed with verdicts: real, fake, overhyped, financed to look hyped · added by lead · round 1
- Map of how many humans effectively know about AI and how much free information exists · added by lead · round 1
- Open source and fully auditable publication record (owner proposed blockchain; mechanism open) · added by lead · round 1
- Audience path: technical audience first, then larger audiences via bubble leaders · added by lead · round 1
- Modular output channels: RSS / JSON feed first, then channel and frontend plugins for different datastreams and audiences · added by lead · round 2
- More people and profiles followed as data sources · added by lead · round 2
- Decentralization path with no owner power class: open suggestions, then personhood-based 1 human = 1 vote with bridging ratings, then a DAO · added by lead · round 2
- Bilingual output: English and Portuguese from day one (X15) · added by lead · round 5

## Councils

_None convened._

## Ledger

```ledger
{
  "settled": [
    {
      "id": "R1-1",
      "kind": "decision",
      "question": "What should the first release of the redesigned site be? (Every option stays inside the standing rules: no invented numbers, no paid sources.)",
      "answer": "Reality digest, today's data (Recommended)",
      "value": "slice:digest",
      "provenance": "owner picked \"Reality digest, today's data (Recommended)\"",
      "round": 2
    },
    {
      "id": "R1-2",
      "kind": "decision",
      "question": "Which verdict labels may the site publish, about what, and on what proof?",
      "answer": "Claim labels, sourced (Recommended)",
      "value": "verdict:claims-sourced",
      "provenance": "owner picked \"Claim labels, sourced (Recommended)\"",
      "round": 2
    },
    {
      "id": "R1-3",
      "kind": "decision",
      "question": "For the first version, what should 'fully auditable, we will do the blockchain for that' mean?",
      "answer": "No-fee stack, Bitcoin anchor (Recommended)",
      "value": "audit:free-stack",
      "provenance": "owner picked \"No-fee stack, Bitcoin anchor (Recommended)\"",
      "round": 2
    },
    {
      "id": "R1-4",
      "kind": "decision",
      "question": "Approved roadmap decision D5 says \"Keep web/index.html one static file, no build\". D5 says to revisit it once a second kind of page goes live, and the investigation explorer is one. The redesign would trigger that. Change D5?",
      "answer": "Several static pages (Recommended)",
      "value": "d5:multi-page",
      "provenance": "owner picked \"Several static pages (Recommended)\"",
      "round": 2
    },
    {
      "id": "R2-1",
      "kind": "decision",
      "question": "You picked the gauges \"Progress by area, Hype temperature, Jobs signal, Risk/doom meter\". The gauges council (5 lenses) asks to name each gauge for what our data can actually measure. The change: \"Progress by area\" -> \"Releases / research output by area\" (labelled as output volume, not capability); \"Hype temperature\" -> a per-story \"Attention vs substance\" gauge (spread vs official post, repo, paper); \"Jobs signal\" -> a panel that says \"no qualified source\" until a licensed source passes qualification; \"Risk/doom meter\" -> a dated, sourced risk event log, no dial. Plus \"Daily movers\" for ups and downs, and no single combined State of AI score. Which names does the gauge header use?",
      "answer": "Council names, keep 'Hype'",
      "value": "gauges:council-hype-word",
      "provenance": "owner picked \"Council names, keep 'Hype'\"",
      "round": 3
    },
    {
      "id": "R2-2",
      "kind": "decision",
      "question": "Your 4 story labels include PUSHED (financed or orchestrated to look hyped). Settled R1-2 allows only sourced claim labels, and PUSHED is about how a story spread, not a claim. Our coordination signals (bursts, new accounts, near-duplicates) are unvalidated. Per scout 3, saying a named company paid for or orchestrated hype implies a provable fact (no opinion shield in the US; near difamacao in Brazil; FTC/EU bar is proof of an undisclosed paid connection). In every option PUSHED labels a story, topic or project, never a person or account. What proof does PUSHED need?",
      "answer": "Document proof only (Recommended)",
      "value": "pushed:document",
      "provenance": "owner picked \"Document proof only (Recommended)\"",
      "round": 3
    },
    {
      "id": "R2-3",
      "kind": "decision",
      "question": "Trends and 'fully auditable' (R1-3) need each day's raw inputs kept durably. Today they live in an Actions cache that can be evicted and a 30-day artifact, and the old Cloudflare R2 plan was dropped. You said GitHub Pages is fine 'if all the data is there and working', with deterministic links. Where do daily inputs and the daily ledger live?",
      "answer": "Ledger on Pages + Releases (Recommended)",
      "value": "store:both",
      "provenance": "owner picked \"Ledger on Pages + Releases (Recommended)\"",
      "round": 3
    },
    {
      "id": "R2-4",
      "kind": "decision",
      "question": "History starts 2026-10-16, so no gauge has 14 days of data yet. GitHub Pages is public, so 'only you use it' means a site labelled as preview, not a hidden one. What does dehype show before 14 committed daily snapshots exist?",
      "answer": "Up to 4, trends held (Recommended)",
      "value": "gate:four-held",
      "provenance": "owner picked \"Up to 4, trends held (Recommended)\"",
      "round": 3
    },
    {
      "id": "R3-1",
      "kind": "decision",
      "question": "Seven pillars are in scope and nothing is dropped. Round 3 found that the first release (S1: the 'dehype' identity, a daily briefing in the Mission control look, the gauge header, the RSS/JSON feed, a verdict file in git, the audit floor) can be built on today's data. Three gauge slots have real values now (output by area, Hype vs substance, Daily movers). Risk and jobs start as honest placeholders. How much should the design written from this brainstorm specify in testable detail (acceptance checks a reviewer can run)?",
      "answer": "S1 testable, rest roadmap (Recommended)",
      "value": "s1-testable-roadmap",
      "provenance": "owner picked \"S1 testable, rest roadmap (Recommended)\"",
      "round": 4
    },
    {
      "id": "R3-2",
      "kind": "decision",
      "question": "You are the only user until a second person arrives (your words: 'im gonna be the only initial user until the second human comes'). R2-4 already says when a single gauge counts as shipped: 14 ledger days, a green recompute verifier, and your confirm. What test says the first release (S1) as a whole has succeeded?",
      "answer": "Your daily use, 14 days (Recommended)",
      "value": "owner-14-days",
      "provenance": "owner picked \"Your daily use, 14 days (Recommended)\"",
      "round": 4
    },
    {
      "id": "R3-3",
      "kind": "decision",
      "question": "Public pulse.json and hype.json name the people who wrote posts on conversation networks (HN, Reddit, Mastodon, Bluesky). That is 641 unique handles in topic samples and 265 in story post lists, shown as bylines in 3 places on the page. The counts (voices, spread, coordination signals) are computed on the runner, so removing the handles changes no number. Because the published lists are capped, the counts cannot be recounted from public data today, with or without hashes. No source's terms grant a right to republish handles. GitHub and Bluesky terms point to honouring removal requests. Newsletter and official feed names, paper authors and repo owners stay in every option. What happens to person handles in the public data and pages?",
      "answer": "Remove person handles (Recommended)",
      "value": "remove",
      "provenance": "owner picked \"Remove person handles (Recommended)\"",
      "round": 4
    },
    {
      "id": "R3-4",
      "kind": "decision",
      "question": "Your Mission control look (dark HUD, few big numbers, thin glowing lines) is the look of the dehype pages. The observatory WISH's accepted issue #8 picked 'Guided questions first' for the investigation explorer (your selection, 2026-10-09). Its design record says the explorer's shell uses \"the existing tracker's system font, blue controls and neutral borders\" and that \"Differences are traversal and disclosure structure, not palettes\". The explorer (#9) is not built yet. Round 3 found that none of the WISH's 20 issues is superseded by this redesign. This look is the one place where they can collide. How far does Mission control reach?",
      "answer": "dehype pages only (Recommended)",
      "value": "dehype-only",
      "provenance": "owner picked \"dehype pages only (Recommended)\"",
      "round": 4
    },
    {
      "id": "R4-1",
      "kind": "decision",
      "question": "How does the pipeline propose a verdict for each Daily briefing story? Your pick X6 says 'pipeline proposes, owner confirms or overrides'. Round 4 found that no story carries claim text or a repo or paper link of its own, that no computed field can tell whether a claim is true, that the repository has no model code at all, and that GitHub Models (the free hosted route) was retired on 2026-07-30. Fact-checkers (Full Fact, Reuters Institute) use machines to find and prioritise claims and humans to give the verdicts. In every option, an unconfirmed row shows 'proposed by the pipeline, not reviewed' and its evidence, with no label word, until you confirm it in git (C1, WISH #12/#16). PUSHED is set only by hand, with the document cited (R2-2).",
      "answer": "Evidence record, you upgrade (Recommended)",
      "value": "proposer:evidence-owner-upgrades",
      "provenance": "owner picked \"Evidence record, you upgrade (Recommended)\"",
      "round": 5
    },
    {
      "id": "R4-2",
      "kind": "decision",
      "question": "Does a claim shown false get its own label? Your words were 'whats real, whats fake'. Your pick X10 is \"4 labels\": REAL / OVERHYPED / PUSHED / UNVERIFIED, with no FAKE or FALSE. OVERHYPED corresponds to fact-checkers' Half True / Mostly False. Calling a named company's claim false states something that has to be provable: in the US there is no opinion defence, and in Brazil it comes close to calúnia/difamação, though sourced scientific criticism is excluded and the company gets a free right of reply within 60 days. In every option, UNVERIFIED means 'not yet checked against a primary source'. The pipeline never proposes a false-claim label, and the scope item 'real, fake, overhyped, financed to look hyped' keeps its spelling.",
      "answer": "Add FALSE, you set it (Recommended)",
      "value": "false:add-false",
      "provenance": "owner picked \"Add FALSE, you set it (Recommended)\"",
      "round": 5
    },
    {
      "id": "R4-3",
      "kind": "decision",
      "question": "How are S1's feed and frontend adapters built? You asked to 'think modularly cordis plugins etc' (X8). The observatory WISH makes Cordis the composition layer (WISH:150 'Cordis owns application component lifetimes'). The repository's own record says Cordis is 'Contract-qualified; application composition/persistence/tenancy BLOCKED' (docs/integrations/cordis.md). X7 and X14 say zero servers. No feed output exists today, so the S1 feed is built from zero either way.",
      "answer": "Cordis now, S1 waits",
      "value": "cordis:now",
      "provenance": "owner picked \"Cordis now, S1 waits\"",
      "round": 5,
      "reopenedBy": "R5-1"
    },
    {
      "id": "R5-1",
      "kind": "decision",
      "question": "Your R4-3 answer was \"Cordis now, S1 waits\". Round 5 read the gate. It has no date, by design. Clearing it needs three things: work in this repository (#4), upstream DeepSeek changes to the rc1 launcher and its one-operator login, and named human owners with two independent approvals. The repository's 2026-10-16 record says \"keep the strict hold\". All three BLOCKED items concern a running DSH application: DSH app composition, a durable evidence store (Brain #5, itself BLOCKED) and separate tenant principals. The record says nothing about a one-shot build. Cordis itself runs in one process with no server, and the repository's own Cordis probe was a one-shot Node command. Your answer also settles a point the record leaves open: whether \"S1 waits\" meant the observatory WISH's full #4 acceptance, or only S1's use of Cordis components. The two reopen options would change the answer like this: \"Cordis now, S1 waits\" -> \"Qualified Cordis API now\", or \"Cordis now, S1 waits\" -> \"Plain modules now, Cordis later\". The \"Keep\" option leaves R4-3 as it is. The lead's reading that a zero-server build falls outside the gate is a reading, not a statement on record. What should S1 do?",
      "answer": "Qualified Cordis API now (Recommended)",
      "value": "reopen-qualified-api",
      "provenance": "owner picked \"Qualified Cordis API now (Recommended)\"",
      "round": 6,
      "reopens": "R4-3"
    },
    {
      "id": "R5-2",
      "kind": "decision",
      "question": "Reddit appears in the spread of 40 of the 79 stories. It is read through arctic-shift, a third-party archive, not through Reddit's API. Under R2-3, each day's input manifest goes on a dated GitHub Release whose SHA256 is anchored in Bitcoin (C3, C4), so the manifest can never be edited. Round 5 read Reddit's terms, except the developer documentation (blocked, HTTP 403). They name no post ids or permalinks and grant display rights only. They bar redistributing 'Reddit Services and Data' and require deleting removed content 'as soon as possible'. No clause settles whether they bind a project that never uses Reddit's API. This is a plain reading, not legal advice. This question covers the manifest only. Reddit titles already shown on the public page are flagged separately under Open. How do Reddit records appear in the public input manifest?",
      "answer": "Hash per record only (Recommended)",
      "value": "hash-only",
      "provenance": "owner picked \"Hash per record only (Recommended)\"",
      "round": 6
    },
    {
      "id": "R5-3",
      "kind": "decision",
      "question": "You picked \"English + Portuguese\" from day one (X15). Our own text is about 500 page strings plus a 6,760-word method page. It can be written in Portuguese by hand: the agent drafts, you review. The headlines are other people's post titles, 79 stories in one day's file. A free offline model fits the existing toolchain: opus-mt-en-ROMANCE, Apache-2.0 upstream, about 113 MB. Its converted copy states no licence, and its speed and Brazilian Portuguese quality are untested. Of the source terms read, none grants translating titles except arXiv (CC0), and Hacker News bars derivative works. A Portuguese edition also makes the Brazilian audience explicit, which raises the weight of FALSE and PUSHED labels. What does Portuguese cover in S1?",
      "answer": "Our text, headlines original (Recommended)",
      "value": "own-text",
      "provenance": "owner picked \"Our text, headlines original (Recommended)\"",
      "round": 6,
      "reopenedBy": "R8-1"
    },
    {
      "id": "R6-1",
      "kind": "decision",
      "question": "The Daily briefing shows a Top 10, with the rest one click away (your pick X17). Round 5 planned to rank it by the heat score the page already uses (voices, networks, newsletters, HN points, decaying from a story's newest post). Round 6 tested that on the 2026-10-16 snapshot. Of 51 news stories with a post in the last 24h, the heat Top 10 held no story first seen in the last 24h. Eight of the ten were first seen 3-6 days earlier, and the best new story ranked 11th. Your earlier direction was 'the immediate unknowns, judged relevant on sight'. 'First seen' means the earliest post in our sample, which starts 2026-10-10. This is one snapshot, not a series. How should the Top 10 be ranked?",
      "answer": "New today first (Recommended)",
      "value": "rank:new-first",
      "provenance": "owner picked \"New today first (Recommended)\"",
      "round": 7
    },
    {
      "id": "R6-2",
      "kind": "decision",
      "question": "Reddit post titles are on today's public page: 28 of the 79 story headlines, 245 of the 346 post titles in story lists, and 557 topic samples. Your R5-2 answer ('Hash per record only') kept Reddit out of the manifest except as hashes, and it covered the manifest only. The pages are rebuilt daily and can drop a deleted post, but each committed pulse.json stays in public git history. Reddit's terms tie displaying its content to showing the username, which you removed (R3-3), wherever those terms bind. Whether they bind a project that reads through the arctic-shift archive is not established. This is a plain reading, not legal advice. Usernames stay removed in every option. How does Reddit appear on the public pages and in pulse.json?",
      "answer": "Counts only, no text (Recommended)",
      "value": "reddit-page:counts",
      "provenance": "owner picked \"Counts only, no text (Recommended)\"",
      "round": 7
    },
    {
      "id": "R6-3",
      "kind": "decision",
      "question": "Your words: 'the view didnt [improve], lets redesign the thing as a whole'. The Daily briefing becomes the first screen (X4), but no answer yet says what becomes of today's console tabs: Pulse, Papers, Repos, Hype (82 project dossiers, hand-refreshed, last cut 2026-10-07, not in the daily refresh) and Method, plus the in-browser search over papers and repos. In every option our own text is in English and Portuguese (R5-3), person handles are removed (R3-3), and the observatory explorer keeps its own look (R3-4). The console is not the explorer. What happens to the console?",
      "answer": "Fold into dehype (Recommended)",
      "value": "console:fold",
      "provenance": "owner picked \"Fold into dehype (Recommended)\"",
      "round": 7
    },
    {
      "id": "R8-1",
      "kind": "decision",
      "question": "Your R6-3 answer folds the console into dehype, so the 82 Hype project dossiers move onto a dehype page. Their prose is our own text, written by the research pass: 17,667 words, about 2.6 times the 6,760-word method page, and each new research pass writes more. When you answered R5-3, the question counted about 500 page strings plus the method page. This prose was not counted. Under R5-3 as it stands, the agent drafts all of it in Portuguese and you review it before S1 passes, so the 14-day clock (R3-2) waits on that review. 2,321 of those words are sampled criticism of named projects, and a Portuguese edition raises the Brazilian exposure that R5-3's question named. In every option, page text, labels and structured fields stay in both languages, and headlines stay as posted. The two reopen options would change your answer like this: \"Our text, headlines original (Recommended)\" → \"English first, PT later\", or \"Our text, headlines original (Recommended)\" → \"Dossier prose English only\". The 'Keep R5-3' option leaves R5-3 as it is. What does Portuguese cover for the dossier prose?",
      "answer": "English first, PT later (Recommended)",
      "value": "pt-dossier:english-first",
      "provenance": "owner picked \"English first, PT later (Recommended)\"",
      "round": 9,
      "reopens": "R5-3"
    },
    {
      "id": "R8-2",
      "kind": "decision",
      "question": "Your R3-3 answer removed person handles from the public data and pages. Mastodon post links carry the author inside the URL, shaped like mastodon.social/@<user>/<id>. pulse.json has 225 of them: 43 in story posts and 182 in topic entries, across 31 servers. The planned check fails any public post URL whose path names a person account, so these links change in every option, in the dated manifest too. Round 7 tested one handle-free form. mastodon.social/statuses/<id> opens without a login, but only the app shell was fetched, so whether the rendered page shows the post, and its author, is untested, and only one mastodon.social post was tried. Our fetcher already holds mastodon.social's own id for every post, including posts from other servers, but pulse.json does not publish that id today. Mastodon's public API turns that id back into the author. mastodon.social's terms have no clause for readers who are not registered (round 4). X links are asked separately. Keeping @user links is not offered, because it would change R3-3. How do Mastodon posts appear in our public files?",
      "answer": "Handle-free link, else count (Recommended)",
      "value": "mastodon:handle-free-link",
      "provenance": "owner picked \"Handle-free link, else count (Recommended)\"",
      "round": 9
    },
    {
      "id": "R8-3",
      "kind": "decision",
      "question": "Folding the console into dehype (R6-3) puts the dossier's 125 X posts on the Hype page, with their text excerpts, likes, replies, views and handle links. pulse.py copies every dossier post into the daily file, so 29 X entries from the same dossier already reach pulse.json today. This question covers both files. The repository's record says X access is 'BLOCKED: paid_access_unapproved' and makes 'No X collection' the default, and how the research pass read these posts is not on record. Round 7 read X's terms (a plain reading, not legal advice). The Terms of Service bar scraping and bar displaying or distributing content outside X's own interfaces. Even an API user may pass only Post IDs to third parties. X's display rules require the @username, which R3-3 removed. No clause covers a bare status link published by someone outside the API, and x.com/i/web/status/<id> redirects to the URL with the handle in it. LinkedIn's terms (6 dossier posts) and YouTube's (4) read the same way, so this answer covers them too. Under an option with links, a LinkedIn or YouTube post gets a link only where its URL names no account. Person handles stay removed in every option, and the link to a project's own official X account stays. What X content appears in hype.json and pulse.json?",
      "answer": "Counts only, no X text (Recommended)",
      "value": "x:counts",
      "provenance": "owner picked \"Counts only, no X text (Recommended)\"",
      "round": 9
    },
    {
      "id": "R9-1",
      "kind": "decision",
      "question": "The traceability check found 6 blocking finding(s) in DESIGN.md before review: Decisions #23 (line 117): `.github/workflows/refresh.yml` does not exist under /Users/feliperosa/workspace/repos/trending-research; Scope IN #12 (line 37): R5-3 was reopened by R8-1; cite the current answer instead; Scope IN #15 (line 40): R5-3 was reopened by R8-1; cite the current answer instead; Scope IN #20 (line 45): `.github/workflows/refresh.yml` does not exist under /Users/feliperosa/workspace/repos/trending-research; line 43: placeholder <date>; line 157: placeholder <date>. A row whose Source does not resolve needs your answer to cite. How should the next run go on?",
      "answer": "Approve as written (Recommended)",
      "value": "approve-uncited",
      "provenance": "owner picked \"Approve as written (Recommended)\"",
      "round": 10
    },
    {
      "id": "R10-1",
      "kind": "review-findings",
      "question": "The design review returned FIX-FIRST after this run's repair (1 of 2 repairs used). Open findings: HIGH-1 (HIGH) The removal and deleted-post path (C34) skips dossier posts, so the design's promise that a deleted or removal-listed post leaves the pages, pulse.json, briefing.json and the feeds on the next daily rebuild does not hold for them. Row 7 defines the mechanism over 'every stored post' and says a post found gone 'is deleted from the history DB, so no later run reloads it'. But pulse.py builds its pool as stored posts plus internal_posts(), and internal_posts() reloads every dossier post from web/hype.json on every run. Neither the recheck nor the DB delete reaches that population. Two concrete cases: the 16 HN dossier entries in pulse.json, and the 268 HN dossier posts the Hype page shows with text under A31. Nothing in CI rewrites hype.json, so removals.json and the recheck never reach the Hype page until a manual research pass. The success-criterion proof only loads stored HN, Mastodon and Bluesky posts into a scratch DB, so it would pass while the claim fails.; HIGH-2 (HIGH) The browser-side stale rule misses a briefing made off schedule. The rule marks a briefing stale only when its generated_at is before the last 06:00 BRT deadline minus 24 hours. Take a briefing generated after 06:00 on day D, by a late scheduled run or a manual workflow_dispatch (the only kind of run this repository has ever had). If the D+1 scheduled run is dropped or fails, that briefing reads fresh all of D+1, until 06:00 on D+2. At D+1 07:00 the threshold is D 06:00, and 14:00 D is later than that. This is the silent carryover that C5 ('fail loudly') forbids, and it contradicts C37's own fixture: 'a briefing dated the previous day, viewed after 06:00, reads stale'. None of the design's three fixture cases covers a previous-day briefing generated after 06:00.. How should the next run go on?",
      "answer": "Repair again (Recommended)",
      "value": "repair",
      "provenance": "owner picked \"Repair again (Recommended)\"",
      "round": 11
    }
  ],
  "asked": [],
  "size": [
    {
      "value": "G",
      "by": "lead",
      "round": 1
    }
  ],
  "scopeIn": [
    {
      "item": "Redesign the view as a whole around the identity: omnichannel AI reality digested to human",
      "by": "lead",
      "round": 1
    },
    {
      "item": "Real state of AI progress by area (how much did we really advance)",
      "by": "lead",
      "round": 1
    },
    {
      "item": "Risk state (how doomed are we)",
      "by": "lead",
      "round": 1
    },
    {
      "item": "AI and jobs",
      "by": "lead",
      "round": 1
    },
    {
      "item": "Daily ups and downs",
      "by": "lead",
      "round": 1
    },
    {
      "item": "Curated newsfeed with verdicts: real, fake, overhyped, financed to look hyped",
      "by": "lead",
      "round": 1
    },
    {
      "item": "Map of how many humans effectively know about AI and how much free information exists",
      "by": "lead",
      "round": 1
    },
    {
      "item": "Open source and fully auditable publication record (owner proposed blockchain; mechanism open)",
      "by": "lead",
      "round": 1
    },
    {
      "item": "Audience path: technical audience first, then larger audiences via bubble leaders",
      "by": "lead",
      "round": 1
    },
    {
      "item": "Modular output channels: RSS / JSON feed first, then channel and frontend plugins for different datastreams and audiences",
      "by": "lead",
      "round": 2
    },
    {
      "item": "More people and profiles followed as data sources",
      "by": "lead",
      "round": 2
    },
    {
      "item": "Decentralization path with no owner power class: open suggestions, then personhood-based 1 human = 1 vote with bridging ratings, then a DAO",
      "by": "lead",
      "round": 2
    },
    {
      "item": "Bilingual output: English and Portuguese from day one (X15)",
      "by": "lead",
      "round": 5
    }
  ],
  "councils": [],
  "reviews": [
    {
      "verdict": "FIX-FIRST",
      "digest": "f7f0f2938ae1af61d177eb56b468b8c5d7c7af701a35bbc047410bcbabf8d3c2",
      "round": 9,
      "repaired": false,
      "findings": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "HIGH-1",
        "HIGH-2",
        "HIGH-3",
        "MEDIUM-1",
        "MEDIUM-2",
        "MEDIUM-3",
        "MEDIUM-4",
        "MEDIUM-5",
        "MEDIUM-6",
        "MEDIUM-7",
        "LOW-1",
        "LOW-2",
        "LOW-3",
        "LOW-4",
        "LOW-5"
      ]
    },
    {
      "verdict": "FIX-FIRST",
      "digest": "c04123607c9336343fe27b21c1de02514782582dfef43ff01b21cb85e7f4003c",
      "round": 10,
      "repaired": false,
      "findings": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "C18",
        "C19",
        "HIGH-1",
        "HIGH-2",
        "MEDIUM-1",
        "MEDIUM-2",
        "MEDIUM-3",
        "LOW-1",
        "LOW-2",
        "LOW-3",
        "LOW-4"
      ]
    },
    {
      "verdict": "FIX-FIRST",
      "digest": "18b8d881ba5d65878a5e36a2561536003c878b9072337273e97caeaef32921c6",
      "round": 10,
      "repaired": true,
      "findings": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "HIGH-1",
        "HIGH-2",
        "MEDIUM-1",
        "MEDIUM-2",
        "LOW-1",
        "LOW-2"
      ]
    },
    {
      "verdict": "SHIP",
      "digest": "576aacddb5fd56f6b41ddf0857fa270ae6b2625a3502ba33fe42d93137f61692",
      "round": 11,
      "repaired": true,
      "findings": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
        "C13",
        "C14",
        "C15",
        "C16",
        "C17",
        "MEDIUM-1",
        "MEDIUM-2",
        "MEDIUM-3",
        "MEDIUM-4",
        "LOW-1"
      ]
    }
  ]
}
```
