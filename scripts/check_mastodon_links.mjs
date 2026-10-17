// Logged-out render check for Mastodon links (dehype design row 3, condition C25).
// pulse.py lists the live Mastodon ids its outputs would show (history/mastodon-candidates.json). For each id whose cached
// result is due, this reads https://mastodon.social/api/v1/statuses/<id> (its HTTP status is recorded per id; group B3's
// deleted-post recheck counts a 404 there as removed), then loads https://mastodon.social/statuses/<id> in a fresh headless
// browser context with no cookies and no login. The check passes when the page shows the status with non-empty text; it fails
// on a not-found page, a login wall, a redirect off mastodon.social (a post from another server) or an empty app shell after a
// fixed wait. Fail-closed: an id the run does not reach (time cap, rate budget, network error) keeps its old entry, and
// pulse.py links only an id whose latest check passed less than 7 days before its NOW.
//
// Usage: node scripts/check_mastodon_links.mjs [--candidates history/mastodon-candidates.json] [--cache web/checks/mastodon-links.json]
//                                              [--cap-seconds 180] [--fixture <file>]
//   --fixture replays recorded lookups and page snapshots from a JSON file instead of the network (unit tests; no browser).
// The browser is playwright-core 1.59.1 from scripts/checks (npm ci --prefix scripts/checks) running the Chromium headless
// shell that version installs (node scripts/checks/node_modules/playwright-core/cli.js install --only-shell chromium).
// Cache (compact JSON): {"note", "updated_at", "statuses": {"<id>": {"result": "pass"|"fail", "checked_at", "passed_at"
// (the latest passing check, kept through later fails, null if none), "api_status" (HTTP status or null), "reason" (fail only)}}}
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

export const HOST = 'mastodon.social';
const DAY = 864e5;
export const RECHECK_PASS_DAYS = 6;     // a pass is re-checked a day before pulse.py stops trusting it (7 days)
export const RETRY_FAIL_HOURS = 20;     // a failed id is tried again on the next daily run, not on a same-day rerun
export const KEEP_DAYS = 45;            // pulse.py RETAIN_DAYS: an entry no candidate needs is dropped after this
export const RATE_RESERVE = 40;         // stop while this many of the IP's API calls are left (each page load spends several)
const WAIT_MS = 15000, NAV_MS = 20000, API_MS = 10000, WORKERS = 2;
const UA = 'dehype-mastodon-render-check/1.0 (+https://github.com/namastex888/dehype)';
const iso = t => new Date(t).toISOString().replace(/\.\d{3}Z$/, 'Z');

export function due(e, now) {
  if (!e || !e.checked_at) return true;
  const age = now - Date.parse(e.checked_at);
  return e.result === 'pass' ? age >= RECHECK_PASS_DAYS * DAY : age >= RETRY_FAIL_HOURS * 36e5;
}

// never checked first (newest id first), then passes about to expire, then old failures (oldest check first)
export function order(ids, statuses, now) {
  const rank = id => { const e = statuses[id]; return !e ? 0 : e.result === 'pass' ? 1 : 2; };
  return ids.filter(id => /^\d{1,20}$/.test(id) && due(statuses[id], now)).sort((a, b) =>
    rank(a) - rank(b) || (rank(a) === 0 ? (BigInt(b) > BigInt(a) ? 1 : -1) : Date.parse(statuses[a].checked_at) - Date.parse(statuses[b].checked_at)));
}

// snap: {host, path, textLength, notFound, login, error} read from the rendered page (never its text)
export function classify(snap) {
  if (snap.error) return ['fail', `browser error: ${String(snap.error).slice(0, 80)}`];
  if (snap.host !== HOST || snap.path.startsWith('/redirect/')) return ['fail', 'redirects off mastodon.social (a post from another server)'];
  if (snap.login || snap.path.startsWith('/auth/')) return ['fail', 'login wall'];
  if (snap.textLength > 0) return ['pass', null];
  if (snap.notFound) return ['fail', 'not-found page'];
  return ['fail', `empty page after ${WAIT_MS / 1000}s`];
}

export function prune(statuses, ids, now) {
  const keep = new Set(ids);
  for (const [id, e] of Object.entries(statuses)) if (!keep.has(id) && now - Date.parse(e.checked_at) > KEEP_DAYS * DAY) delete statuses[id];
  return statuses;
}

// lookup(id) -> {status, remaining}; render(id) -> snap; clock() -> ms. Mutates and returns statuses with the run's counts.
export async function run({ ids, statuses, capMs, lookup, render, clock }) {
  const start = clock(), queue = order(ids, statuses, start);
  const n = { candidates: ids.length, due: queue.length, pass: 0, fail: 0, unreached: 0, stop: null };
  let remaining = Infinity;
  const work = async () => {
    for (let id; (id = queue.shift()) !== undefined;) {
      if (n.stop || clock() - start >= capMs) { n.stop ||= 'time cap reached'; n.unreached++; continue; }
      if (remaining < RATE_RESERVE) { n.stop = `API rate budget (${remaining} calls left)`; n.unreached++; continue; }
      let api;
      try { api = await lookup(id); } catch { n.unreached++; continue; }               // network error: not reached
      if (Number.isFinite(api.remaining)) remaining = api.remaining;
      if (api.status === 429) { n.stop = 'API rate limit (429)'; n.unreached++; continue; }
      let result = 'fail', reason = `api ${api.status}`;
      if (api.status === 200) {
        let snap;
        try { snap = await render(id); } catch (e) { snap = { error: e.message }; }
        [result, reason] = classify(snap);
      }
      const at = iso(clock()), old = statuses[id] || {};
      statuses[id] = { result, checked_at: at, passed_at: result === 'pass' ? at : old.passed_at ?? null, api_status: api.status, ...(reason && { reason }) };
      n[result]++;
    }
  };
  await Promise.all(Array.from({ length: WORKERS }, work));
  return n;
}

async function browserRender() {
  const require = createRequire(new URL('./checks/package.json', import.meta.url));
  const { chromium } = require('playwright-core');
  const browser = await chromium.launch({ headless: true });
  const render = async id => {
    const ctx = await browser.newContext({ locale: 'en-US', serviceWorkers: 'block' });   // a fresh context: no cookies, no login
    try {
      const page = await ctx.newPage();
      await page.goto(`https://${HOST}/statuses/${id}`, { waitUntil: 'domcontentloaded', timeout: NAV_MS });
      await page.waitForFunction(() => (document.querySelector('.detailed-status .status__content')?.innerText || '').trim()   // the fixed wait
        || document.querySelector('.redirect, #user_email, [class*="column_error"]'), null, { timeout: WAIT_MS }).catch(() => {});
      return await page.evaluate(() => ({
        host: location.host, path: location.pathname,
        textLength: (document.querySelector('.detailed-status .status__content')?.innerText || '').trim().length,
        notFound: !!document.querySelector('[class*="empty_state"], [class*="column_error"]'),
        login: !!document.querySelector('#user_email'),
      }));
    } finally { await ctx.close(); }
  };
  return { render, close: () => browser.close() };
}

async function apiLookup(id) {
  const r = await fetch(`https://${HOST}/api/v1/statuses/${id}`, { headers: { 'User-Agent': UA, Accept: 'application/json' }, redirect: 'manual', signal: AbortSignal.timeout(API_MS) });
  await r.arrayBuffer().catch(() => {});
  return { status: r.status, remaining: Number(r.headers.get('x-ratelimit-remaining') ?? NaN) };
}

const readJson = (f, dflt) => { try { return JSON.parse(readFileSync(f, 'utf8')); } catch { return dflt; } };

async function main(argv) {
  const arg = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };
  const candFile = arg('--candidates', 'history/mastodon-candidates.json'), cacheFile = arg('--cache', 'web/checks/mastodon-links.json');
  const capMs = Number(arg('--cap-seconds', '180')) * 1000, fixture = arg('--fixture');
  const ids = (readJson(candFile, {}).ids || []).map(String);
  const statuses = readJson(cacheFile, {}).statuses || {};
  let lookup, render, clock = Date.now, close = async () => {};
  if (fixture) {                                                  // recorded lookups and snapshots; a fake clock
    const F = JSON.parse(readFileSync(fixture, 'utf8'));
    let t = Date.parse(F.now);
    clock = () => t;
    lookup = async id => { const l = F.lookups[id]; if (!l) throw new Error('unreachable'); return l; };
    render = async id => { t += F.ms_per_check || 0; return F.pages[id]; };
  } else if (ids.some(id => due(statuses[id], Date.now()))) {
    ({ render, close } = await browserRender());
    lookup = apiLookup;
  }
  const t0 = clock();
  const n = await run({ ids, statuses, capMs, lookup, render, clock });
  await close();
  prune(statuses, ids, clock());
  const sorted = Object.fromEntries(Object.entries(statuses).sort(([a], [b]) => (BigInt(a) < BigInt(b) ? -1 : 1)));
  mkdirSync(dirname(cacheFile), { recursive: true });
  writeFileSync(cacheFile, JSON.stringify({
    note: 'Bot-written: logged-out render check of https://mastodon.social/statuses/<id> per Mastodon post (scripts/check_mastodon_links.mjs). '
      + 'A post links there only while its latest check passed less than 7 days before pulse.json generated_at; api_status is the HTTP status of /api/v1/statuses/<id>.',
    updated_at: iso(clock()), statuses: sorted }));
  const fresh = ids.filter(id => statuses[id]?.result === 'pass' && clock() - Date.parse(statuses[id].passed_at) < 7 * DAY).length;
  console.log(`mastodon render check: ${n.candidates} candidates, ${n.due} due, ${n.pass} pass, ${n.fail} fail, ${n.unreached} not reached`
    + ` (time cap ${capMs / 1000}s${n.stop ? `; stopped: ${n.stop}` : ''}); ${fresh} candidates hold a fresh pass; ${Math.round((clock() - t0) / 1000)}s`);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) await main(process.argv.slice(2));
