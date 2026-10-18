// "Stale since" in the browser (design row 18, C37; Decision 15): web/dehype.js's staleSince, run from its stale:start ... stale:end block
// (dehype.js itself needs a page). A briefing belongs to the America/Sao_Paulo date of its generated_at and reads "stale since" that date
// once 06:00 America/Sao_Paulo of the next date has passed, whatever the hour it was made. Run: node --test tests/dehype_stale.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const js = readFileSync(new URL('../web/dehype.js', import.meta.url), 'utf8');
const block = js.match(/\/\/ stale:start[^\n]*\n([\s\S]*?)\/\/ stale:end/)?.[1];
assert.ok(block, 'web/dehype.js lacks its stale:start ... stale:end block');
const staleSince = new Function('DAY', 'esc', 't', `${block}; return staleSince;`)(864e5, String, String);
const at = s => Date.parse(s);

// SC-19's six cases (WISH.md Group E1), today 2026-10-17; BRT is UTC-3 (no daylight saving since 2019)
const SIX = [
  ['generated 05:25 BRT today, viewed 07:00 BRT today: no marker', '2026-10-17T08:25:00Z', '2026-10-17T10:00:00Z', null],
  ['generated 05:25 BRT the previous day, viewed 05:50 BRT today: no marker', '2026-10-16T08:25:00Z', '2026-10-17T08:50:00Z', null],
  ['the same previous-day briefing viewed 07:00 BRT today: stale since its date', '2026-10-16T08:25:00Z', '2026-10-17T10:00:00Z', '2026-10-16'],
  ['generated 14:00 BRT the previous day, viewed 05:50 BRT today: no marker', '2026-10-16T17:00:00Z', '2026-10-17T08:50:00Z', null],
  ['the same 14:00 briefing viewed 07:00 BRT today: stale since its date', '2026-10-16T17:00:00Z', '2026-10-17T10:00:00Z', '2026-10-16'],
  ['generated 05:25 BRT two days earlier, viewed 05:50 BRT today: stale since its date', '2026-10-15T08:25:00Z', '2026-10-17T08:50:00Z', '2026-10-15'],
];
// edges: the 06:00 boundary, a late-evening run that is already the next UTC day, an unreadable generated_at
const EDGES = [
  ['on time, viewed at 05:59:59 BRT the next day', '2026-10-17T08:25:00Z', '2026-10-18T08:59:59Z', null],
  ['on time, viewed at 06:00 BRT the next day', '2026-10-17T08:25:00Z', '2026-10-18T09:00:00Z', '2026-10-17'],
  ['made 23:30 BRT (02:30Z the next UTC day): belongs to its BRT date', '2026-10-17T02:30:00Z', '2026-10-17T09:00:00Z', '2026-10-16'],
  ['generated_at missing or unreadable reads no date', 'not a date', '2026-10-17T12:00:00Z', null],
];
for (const [name, gen, now, want] of [...SIX, ...EDGES]) test(name, () => assert.equal(staleSince(gen, at(now)), want));
