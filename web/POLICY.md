# dehype policy: verdicts, right of reply and corrections

Portuguese: [POLICY.pt.md](POLICY.pt.md). This page is published before the first FALSE verdict and is checked on every build.

## Verdicts

dehype labels claims, stories, topics and projects, never people or accounts. There are five labels:

- **REAL**: a primary source confirms the named claim.
- **OVERHYPED**: a primary source shows the claim is true in part, or smaller than it was presented.
- **FALSE**: a cited primary source contradicts the named claim.
- **PUSHED**: a public document (a filing, a sponsor tag, an admission) shows an undisclosed paid or material connection behind the story.
- **UNVERIFIED**: not yet checked against a primary source.

Every story starts as "proposed by the pipeline, not reviewed". The pipeline writes an evidence record with the state "proposed" and no label word; it never proposes a label. Only the owner changes a label, by a pull request to `web/verdicts.json`, and the merge is the confirm. The daily refresh bot never writes that file, and CI rejects a bot commit that touches it.

A row whose label is REAL, OVERHYPED, FALSE or PUSHED carries:

- the named claim (for PUSHED, the document);
- a primary source URL, which is never an X, LinkedIn or YouTube post. A claim whose only source is an X post stays UNVERIFIED; its reason may name the official account and the date, with no link;
- a reason in English and in Portuguese;
- the confirming commit and the date it was confirmed.

FALSE is set only by the owner, by hand, on a named claim, with a cited primary source that contradicts it. PUSHED needs the public document cited on the row; coordination signals are shown as "coordination signals" and never as a label. Every FALSE row links the right of reply and corrections below (`POLICY.md#reply`).

A row names a story by its id (`s:` and 12 hex). A story's id can move when an earlier post arrives; the refresh then writes the move to `web/story-aliases.json` (old id to new id), and the row follows it. Each day's published story ids are to be kept in a story-id archive (`web/ledger/ids/YYYY-MM-DD.json`, written once the daily ledger is in place), so that a confirmed row stays valid after its story leaves the 7-day story window. CI fails a row whose id resolves to none of these.

<a id="reply"></a>
## Right of reply

Anyone a story or verdict concerns (a company, a project, the author of a claim) may reply, free of charge. In Brazil this is the right of reply or rectification of Lei 13.188/2015, exercised within 60 days of the publication.

How to reply: send the text of the reply with the story id (`s:...`) or a link to the story, by email to felipe@namastex.ai, or as an issue at https://github.com/namastex888/dehype/issues (issues are public).

What happens: the reply is added to the corrections log as a `reply` entry, in the language it was sent, linked to the story it answers, and is to be shown wherever that story's verdict is shown. A reply is published within 7 days of receipt. If the reply shows that a verdict is wrong, the verdict is corrected as below.

<a id="corrections"></a>
## Corrections

The corrections log is `web/corrections.json`. It is appended to, never edited over: CI compares the file with the base commit of every change and fails a change that edits or removes an existing entry. A correction to an earlier entry is a new entry.

Each entry has an id (`c:1`, `c:2`, ... in order), a date, a kind (`correction` or `reply`), the story it is about (`s:...`, when it concerns one), its text (a correction in English and Portuguese; a reply in the language it was sent) and an optional link.

When a verdict changes, the row in `web/verdicts.json` is changed by a pull request and a correction entry says what changed and why. The earlier state stays in the public git history. To report an error, use the same email or issue as a reply.

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
