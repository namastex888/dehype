# dehype policy: verdicts, right of reply, corrections and removals

Portuguese: [POLICY.pt.md](POLICY.pt.md). This page is published before the first FALSE verdict and is checked on every build.

## Verdicts

dehype labels claims, stories, topics and projects, never people or accounts. There are five labels:

- **REAL**: a primary source confirms the named claim.
- **OVERHYPED**: a primary source shows the claim is true in part, or smaller than it was presented.
- **FALSE**: a cited primary source contradicts the named claim.
- **PUSHED**: a public document (a filing, a sponsor tag, an admission) shows an undisclosed paid or material connection behind the story.
- **UNVERIFIED**: not yet checked against a primary source.

Every story starts as "proposed by the pipeline, not reviewed". The pipeline writes an evidence record with the state "proposed" and no label word; it never proposes a label. Only the owner changes a label, by a pull request to `web/verdicts.json`, and the merge is the confirm. The daily refresh never writes that file: it stages a fixed list of bot-written files that leaves it out, and before it pushes its commit it runs the owner-file check (`scripts/check_owner_files.py`), so a refresh commit that touched it is never pushed. CI and the deploy run the same check on every other change. There is one row per claim: two rows on one story with the same claim or document are rejected, and a changed verdict changes its row.

A row whose label is REAL, OVERHYPED, FALSE or PUSHED carries:

- the named claim (for PUSHED, the document);
- a primary source URL, which is never an X, LinkedIn or YouTube post. A claim whose only source is an X post stays UNVERIFIED; its reason may name the official account and the date, with no link;
- a reason in English and in Portuguese;
- the confirming commit and the date it was confirmed. The confirming commit is the one that sets the label; a commit cannot name itself, so the row cites it in a follow-up commit of the same pull request.

FALSE is set only by the owner, by hand, on a named claim, with a cited primary source that contradicts it. PUSHED needs the public document cited on the row; coordination signals are shown as "coordination signals" and never as a label. Every FALSE row links the right of reply and corrections below (`POLICY.md#reply`).

A row names a story by its id (`s:` and 12 hex). A story's id can move when an earlier post arrives; the refresh then writes the move to `web/story-aliases.json` (old id to new id), and the row follows it. Each day's published story ids are to be kept in a story-id archive (`web/ledger/ids/YYYY-MM-DD.json`, written once the daily ledger is in place), so that a confirmed row stays valid after its story leaves the 7-day story window. CI fails a row whose id resolves to none of these. Until that archive is in place, no upgraded row (REAL, OVERHYPED, FALSE or PUSHED) is added, because a row whose story leaves the 7-day window would have nothing to resolve to.

<a id="reply"></a>
## Right of reply

Anyone a story or verdict concerns (a company, a project, the author of a claim) may reply, free of charge. dehype honours the right of reply or rectification of Lei 13.188/2015 (Brazil), exercised within 60 days of the publication.

How to reply: send the text of the reply with the story id (`s:...`) or a link to the story, by email to felipe@namastex.ai, or as an issue at https://github.com/namastex888/dehype/issues (issues are public).

What happens: the reply is added to the corrections log as a `reply` entry, in the language it was sent, linked to the story it answers, and is to be shown wherever that story's verdict is shown. A valid reply is published within 7 days of receipt. If the reply shows that a verdict is wrong, the verdict is corrected as below.

<a id="corrections"></a>
## Corrections

The corrections log is `web/corrections.json`. It is appended to, never edited over: CI compares the file with the base commit of every change and fails a change that edits or removes an existing entry. A correction to an earlier entry is a new entry.

Each entry has an id (`c:1`, `c:2`, ... in order), a date, a kind (`correction` or `reply`), the story it is about (`s:...`, when it concerns one), its text (a correction in English and Portuguese; a reply in the language it was sent) and an optional link.

When a verdict changes, the row in `web/verdicts.json` is changed by a pull request and a correction entry says what changed and why. The earlier state stays in the public git history. To report an error, use the same email or issue as a reply.

<a id="removals"></a>
## Removal requests and deleted posts

How to ask for removal: send the address (URL) of the post, by email to felipe@namastex.ai. An issue at https://github.com/namastex888/dehype/issues also works, but issues are public, so an issue would itself point at the post. Anyone may ask about a post they wrote or that concerns them.

What happens: the owner records an accepted request in `web/removals.json` by a pull request. That file is owner-reviewed: the daily refresh never writes it, and the owner-file check (`scripts/check_owner_files.py`) refuses a refresh commit that touches it. An entry holds only the SHA256 of the post's address and the date the request was accepted, so the file publishes no address, id or text of the post.

What the daily rebuild drops: on the next daily rebuild, a post that `web/removals.json` names, or that its source reports deleted or removed, leaves the pages, `pulse.json`, `briefing.json`, the feeds and the history database the pipeline keeps. A post of the research dossier also leaves `web/hype.json` and the Hype page, and no later run brings it back.

The deleted-post recheck: the collectors are searches and timelines that never report a deletion, so each daily refresh looks up by id every stored post the day's outputs could show: Hacker News through its Firebase item endpoint (`deleted` or `dead`), Mastodon through mastodon.social `/api/v1/statuses/<id>` (a 404, also when the Mastodon render check records it), Bluesky through `app.bsky.feed.getPosts` (a post missing from the answer) and Reddit records through the arctic-shift archive by id (`[deleted]` or `[removed]`; Reddit is shown as counts only, so such a record leaves the counts). It also looks up every research-dossier post that keeps a source id (today its Hacker News posts). A dossier post found gone is recorded in `web/checks/dossier-gone.json`, written by the refresh, appended to and never edited, which holds only the SHA256 of each such post's address; the refresh then removes the post from `web/hype.json` (deletion-only). The recheck runs under a time cap of 180 seconds and fails closed: a post it could not reach that day is shown only as a count, never with its text or link, until a later run reaches it.

The hash: the SHA256, in lowercase hex, of the post's address exactly as the source gives it: `https://news.ycombinator.com/item?id=<id>` for Hacker News; for Mastodon the post's own address or `https://mastodon.social/statuses/<id>`; `https://bsky.app/profile/<account>/post/<id>` for Bluesky; the `https://www.reddit.com/r/...` permalink for Reddit. It can be computed with `printf '%s' '<address>' | shasum -a 256`.

X, LinkedIn, YouTube and Telegram posts in the research dossier keep no address, text or author: nothing of such a post is shown, so there is nothing to recheck or to name.

Limits: committed git history and the anchored manifests cannot be edited. A post published before its removal stays in the earlier commits of this public repository and in any manifest already anchored, as the Reddit record hash does; the removal applies from the next daily rebuild on.

<a id="file-shapes"></a>
## File shapes

`web/verdicts.json` (owner-reviewed):

```json
{"rows": [
  {"id": "s:0123456789ab", "label": "FALSE", "claim": "the claim as made, named",
   "source": "https://example.org/primary-source", "reason": {"en": "...", "pt": "..."},
   "commit": "1a2b3c4", "confirmed": "2026-10-08", "reply": "POLICY.md#reply"}
]}
```

PUSHED rows carry `document` (the public document, named) in place of `claim`; UNVERIFIED rows need only `id` and `label`.

`web/corrections.json` (owner-reviewed, append-only):

```json
{"entries": [
  {"id": "c:1", "date": "2026-10-20", "kind": "correction", "about": "s:0123456789ab",
   "text": {"en": "...", "pt": "..."}, "link": "https://example.org/source"}
]}
```

`web/removals.json` (owner-reviewed; one entry per accepted request):

```json
{"entries": [
  {"sha256": "<SHA256 of the post's address, 64 lowercase hex>", "date": "2026-10-20"}
]}
```

`web/checks/dossier-gone.json` (written by the refresh, append-only; one entry per dossier post found gone):

```json
{"note": "...", "gone": [{"sha256": "<SHA256 of the post's address as stored in web/hype.json>", "found": "2026-10-20"}]}
```
