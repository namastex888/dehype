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

const CASES = [
  ['on time (05:25 BRT), viewed the same day', '2026-10-17T08:25:00Z', '2026-10-17T20:00:00Z', null],
  ['on time, viewed at 05:59:59 BRT the next day', '2026-10-17T08:25:00Z', '2026-10-18T08:59:59Z', null],
  ['on time, viewed at 06:00 BRT the next day', '2026-10-17T08:25:00Z', '2026-10-18T09:00:00Z', '2026-10-17'],
  ['made 23:30 BRT (02:30Z the next UTC day): belongs to its BRT date', '2026-10-17T02:30:00Z', '2026-10-17T09:00:00Z', '2026-10-16'],
  ['two days old, no run committed or deployed', '2026-10-15T08:25:00Z', '2026-10-17T12:00:00Z', '2026-10-15'],
  ['generated_at missing or unreadable reads no date', 'not a date', '2026-10-17T12:00:00Z', null],
];
for (const [name, gen, now, want] of CASES) test(name, () => assert.equal(staleSince(gen, at(now)), want));

test('off schedule: a manual run at 14:00 BRT reads fresh until 06:00 the next day, then stale', () => {
  assert.equal(staleSince('2026-10-17T17:00:00Z', at('2026-10-18T08:59:00Z')), null);
  assert.equal(staleSince('2026-10-17T17:00:00Z', at('2026-10-18T09:00:00Z')), '2026-10-17');
});
