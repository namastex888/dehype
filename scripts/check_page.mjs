// Static page gate: the inline script parses, the data files parse, every field the page reads exists, and the public
// files keep the public-data rules (no person handle; Reddit, X, LinkedIn, YouTube, Telegram counts only; Mastodon counts only
// unless linked by its handle-free mastodon.social/statuses link with a fresh passing render check; no unlisted X figure).
// briefing.json keeps the same rules plus its own: proposals with no label word, "not fetched" for an unfetched source, previews only.
// verdicts.json and corrections.json (owner-reviewed) keep them too, and every verdict row resolves and carries its fields.
// No post that removals.json (owner-reviewed) or checks/dossier-gone.json (bot-written) names by URL hash is still published.
// Node standard library only. Usage: node scripts/check_page.mjs [webDir]
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { createHash } from 'node:crypto';

const web = process.argv[2] || 'web';
const fail = [];
const need = (cond, msg) => { if (!cond) fail.push(msg); };
const warn = [];

// Public-data rules (design group A; pulse.py and hype_build.py apply them, this gate fails what they miss): no person handle,
// Reddit, X, LinkedIn, YouTube and Telegram as counts only, Mastodon as a count unless its post record links to
// https://mastodon.social/statuses/<id> with a render check in checks/mastodon-links.json that passed less than 7 days before
// pulse.json's generated_at (not the clock: a refresh outage never fails links already committed), no unlisted X figure.
const COUNT_ONLY = new Set(['Reddit', 'X', 'LinkedIn', 'YouTube', 'Telegram', 'Discord', 'Mastodon']);
const NAMED = new Set(['Newsletter', 'Official', 'arXiv', 'GitHub']);          // newsletter, feed, lab or paper and repo names stay
const POST_BODY = ['title', 'author', 'url', 'link', 'score', 'comments', 'who'], HYPE_BODY = ['au', 't', 'url', 'likes', 'score', 'cm', 'rp', 'views'];
const NET_URL = [['Reddit', 'reddit\\.com|redd\\.it'], ['X', 'x\\.com|twitter\\.com|t\\.co|nitter\\.net|fxtwitter\\.com|vxtwitter\\.com'], ['LinkedIn', 'linkedin\\.com|lnkd\\.in'],
  ['YouTube', 'youtube\\.com|youtu\\.be|youtube-nocookie\\.com'], ['Telegram', 't\\.me|telegram\\.me']]
  .map(([n, h]) => [n, new RegExp(`^https?://(?:[\\w-]+\\.)*(?:${h})(?=[/:?#]|$)`, 'i')]);
const ACCOUNT_URL = /^https?:\/\/(?!(?:[\w-]+\.)*npmjs\.(?:org|com)\/)[^\s?#]*\/@|bsky\.app\/profile\/[^/\s]+\/post\/|\/users\/[^/\s]+\/statuses\/|did:(?:plc|web):/i;
const STATUS_URL = /^https:\/\/mastodon\.social\/statuses\/(\d{1,20})$/, LINK_MS = 7 * 864e5;
let MC = {}, genAt = NaN;                                        // the render-check cache; pulse.json generated_at (ms)
try { MC = JSON.parse(readFileSync(join(web, 'checks', 'mastodon-links.json'), 'utf8')).statuses || {}; }
catch (e) { if (e.code !== 'ENOENT') fail.push(`checks/mastodon-links.json unreadable: ${e.message}`); }
const MASTO_RULE = 'Mastodon link without a render check passed less than 7 days before pulse.json generated_at';
// the same rule pulse.py load_links applies at its NOW: the latest check passed, 0 to 7 days before generated_at
function mastoLink(id) {                                         // null when the link may stand, else why not
  const e = MC[id];
  if (!e) return 'no check in checks/mastodon-links.json';
  if (!e.passed_at) return 'its check never passed';
  if (e.result !== 'pass' || e.passed_at !== e.checked_at) return 'its latest check failed';
  const age = genAt - Date.parse(e.passed_at);
  if (age < 0) return 'its pass is later than generated_at';
  return age < LINK_MS ? null : 'its last pass is 7 days or more before generated_at';
}
const STATUS_ANY = /mastodon\.social\/(?:redirect\/)?statuses\//i;           // any other spelling of a status link is never published
const X_PROFILE = /^https?:\/\/(?:www\.)?(?:x|twitter)\.com\/\w+\/?$/i;
const HANDLE = /(?<![A-Za-z0-9_/.@])@[A-Za-z0-9_][A-Za-z0-9_.-]*(?![A-Za-z0-9_/-])/;
const X_WORD = /(?<![A-Za-z0-9_-])X(?![A-Za-z0-9_-])/;
const X_TERMS = /x\.com|twitter|tweet|repost|retweet|x_search|syndication|\b(?:likes|replies|views|reposts|followers|impressions|bookmarks)\b/i;
const urlNet = u => (NET_URL.find(([, rx]) => rx.test(u)) || [])[0] || (ACCOUNT_URL.test(u) ? 'account' : null);
const cite = n => ({ X: 'an X post', account: 'a post whose link names its account' })[n] || `a ${n} post`;
const RULE = { account: 'account-naming URL (a person handle)' };
for (const n of ['Reddit', 'X', 'LinkedIn', 'YouTube', 'Telegram']) RULE[n] = `${n} link (${n} is counts only${n === 'X' ? '; only links.x_handle may link the project\'s own account' : ''})`;
const sentences = t => (t || '').split(/(?<=[.!?])\s+/).filter(Boolean);
const xFigure = s => /[0-9]/.test(s) && (X_WORD.test(s) || X_TERMS.test(s));
const sha = s => createHash('sha256').update(s, 'utf8').digest('hex');
function walk(o, path, fn) {
  if (Array.isArray(o)) o.forEach((v, i) => walk(v, `${path}[${i}]`, fn));
  else if (o && typeof o === 'object') { fn(o, path); for (const [k, v] of Object.entries(o)) walk(v, path ? `${path}.${k}` : k, fn); }
  else if (typeof o === 'string') fn(o, path);
}
const found = {};                                                // one finding per file and rule: count and the first places
const finding = (file, rule, at) => { const f = found[`${file}: ${rule}`] ||= []; f.push(at); };
function publicRules(file, D) {
  walk(D, '', (v, at) => {
    if (typeof v === 'string') {
      if (/\.links\.x_handle$/.test(at) && X_PROFILE.test(v)) return;
      for (const u of v.match(/https?:\/\/[^\s"'<>]+/g) || []) {
        const n = urlNet(u), m = STATUS_URL.exec(u), why = m && mastoLink(m[1]);
        if (n) finding(file, RULE[n], at);
        if (why) finding(file, `${MASTO_RULE} (${why})`, at);
        if (!m && STATUS_ANY.test(u)) finding(file, 'Mastodon status link not in the form https://mastodon.social/statuses/<id>', at);
      }
      const bare = v.replace(/https?:\/\/\S+/g, ' ');                // a link written without its scheme
      if (/(^|[^\w.])reddit\.com\//i.test(bare)) finding(file, RULE.Reddit, at);
      if (/(^|[^\w.])(x|twitter)\.com\//i.test(bare)) finding(file, RULE.X, at);
      if (!/\.aliases\[\d+\]$/.test(at) && HANDLE.test(bare)) finding(file, 'person handle (@name)', at);
      if (/\bt3_[a-z0-9]{4,}\b/.test(v)) finding(file, 'Reddit id (t3_)', at);
      return;
    }
    const net = typeof v.net === 'string' ? v.net : typeof v.pl === 'string' ? v.pl : null;
    if (!net) return;
    const body = 'pl' in v ? HYPE_BODY : POST_BODY, who = 'pl' in v ? 'au' : 'author';
    // a Mastodon post record shown with its handle-free link (its check is the string rule above); any other is a count
    const linked = net === 'Mastodon' && who === 'author' && STATUS_URL.test(v.url || '');
    if (COUNT_ONLY.has(net) && !linked) for (const k of body) { if (v[k] != null && v[k] !== '') finding(file, `count-only ${net} record carries ${k}`, at); }
    else if (v[who] && (who === 'au' || v.source === 'dossier' || !NAMED.has(net))) finding(file, `person handle: ${net} ${who}`, at);
    if (linked && v.who) finding(file, 'person handle: Mastodon who', at);
  });
}
function hypeRules(H) {
  const list = f => { try { return JSON.parse(readFileSync(join(web, 'i18n', f), 'utf8')); } catch (e) { fail.push(`i18n/${f} unreadable: ${e.message}`); return {}; } };
  const S = list('dossier-sources.json'), X = list('dossier-x-figures.json');
  const byOk = new Set([...(S.keep || []), ...(S.network || []).map(e => e.by)]);
  need(X.placeholder && X.placeholder.en && X.placeholder.pt, 'i18n/dossier-x-figures.json lacks the en and pt placeholder');
  const listed = new Map();
  for (const e of X.hits || []) {
    need(['strip', 'keep'].includes(e.disposition) && e.reason && e.field && /^[0-9a-f]{64}$/.test(e.sha256 || ''), `i18n/dossier-x-figures.json entry ${e.slug}/${e.field} incomplete`);
    listed.set(`${e.slug}|${e.field}|${e.sha256}`, e.disposition);
  }
  for (const [slug, it] of Object.entries(H.items || {})) {
    for (const k of ['account', 'followers', 'cand_account']) if (it.viral?.[k] != null) finding('hype.json', `viral.${k} publishes an account`, `items.${slug}.viral.${k}`);
    (it.skeptic || []).forEach((s, i) => { if (s.by && !byOk.has(s.by)) finding('hype.json', 'skeptic[].by name not in i18n/dossier-sources.json', `items.${slug}.skeptic[${i}].by`); });
    for (const [k, rows] of [['traction', it.traction], ['evidence_in.usage', it.evidence_in?.usage], ['discovery.metrics', it.discovery?.metrics]])
      (rows || []).forEach((r, i) => {
        const n = urlNet(r.url || '') || [...COUNT_ONLY].find(n => r.url === cite(n));
        if (COUNT_ONLY.has(n) && typeof r.value === 'number') finding('hype.json', 'figure from a count-only post is shown', `items.${slug}.${k}[${i}].value`);
      });
  }
  for (const [slug, f, t] of prose(H)) for (const s of sentences(typeof t === 'string' ? t : '')) {
    if (!xFigure(s)) continue;
    const d = listed.get(`${slug}|${f}|${sha(s)}`);
    if (d !== 'keep') finding('hype.json', d === 'strip' ? 'X-figure sentence listed strip is still shown' : 'unlisted X-figure sentence (list it in i18n/dossier-x-figures.json)',
      `${slug ? `items.${slug}.` : ''}${f}`);
  }
}
function* prose(H) {                                             // the prose fields hype_build.prose_fields walks, in its order
  for (const k of ['ranking_interpretation', 'gap_note']) yield [null, k, H[k]];
  for (const k of ['coverage', 'coverage_short']) for (const [i, v] of (H[k] || []).entries()) yield [null, `${k}[${i}]`, v];
  for (const [slug, it] of Object.entries(H.items || {})) {
    for (const k of ['summary', 'status', 'first_seen_meaning', 'peak_reason', 'category']) yield [slug, k, it[k]];
    yield [slug, 'viral.reason', it.viral?.reason];
    for (const k of ['assessment', 'limitations']) yield [slug, `coord.${k}`, it.coord?.[k]];
    for (const [i, e] of (it.coord?.evidence || []).entries()) yield [slug, `coord.evidence[${i}].t`, e.t];
    for (const [i, s] of (it.traction || []).entries()) yield [slug, `traction[${i}].notes`, s.notes];
    for (const [i, s] of (it.skeptic || []).entries()) { yield [slug, `skeptic[${i}].claim`, s.claim]; yield [slug, `skeptic[${i}].by`, s.by]; }
    for (const k of Object.keys(it.notes || {}).sort()) yield [slug, `notes.${k}`, it.notes[k]];
    if (it.qual_gap) yield [slug, 'qual_gap.text', it.qual_gap.text];
  }
}

const html = readFileSync(join(web, 'index.html'), 'utf8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
need(scripts.length === 1, `expected one inline script, found ${scripts.length}`);
for (const s of scripts) {
  try { new Function(s); } catch (e) { fail.push(`inline script does not parse: ${e.message}`); }
}
need(!/\/blob\/main\//.test(html), 'page links to /blob/main/ (default branch is dev)');

const D = JSON.parse(readFileSync(join(web, 'data.json'), 'utf8'));
for (const k of ['generated_at', 'generated_local', 'sources', 'scoring_version', 'windows', 'views', 'tracked', 'papers', 'repos', 'priors'])
  need(k in D, `data.json missing ${k}`);
for (const tab of ['papers', 'repos']) {
  need(D[tab] && D[tab].items && Object.keys(D[tab].items).length > 0, `data.json ${tab}.items empty`);
  for (const w of D.windows || []) {
    const v = D[tab]?.[w]?.all;
    need(v && Array.isArray(v.rows), `data.json ${tab}.${w}.all.rows missing`);
    for (const r of (v?.rows || [])) {
      if (!D[tab].items[r.id]) { fail.push(`data.json ${tab}.${w} row ${r.id} has no item`); break; }
    }
  }
}

const H = JSON.parse(readFileSync(join(web, 'hype.json'), 'utf8'));
for (const k of ['items', 'views', 'windows', 'n_projects', 'weights', 'gap_min_coverage', 'coverage'])
  need(k in H, `hype.json missing ${k}`);
for (const [w, meta] of Object.entries(H.windows || {})) {
  if (!meta.enabled) continue;
  for (const r of H[w]?.all?.rows || []) {
    const it = H.items[r.id];
    if (!it || !it.discovery || !it.win || !it.links || !it.coord) { fail.push(`hype.json ${w} row ${r.id} item incomplete`); break; }
  }
}

// Semantic index (optional file pair): sizes agree and every id still exists in the data it was built from.
let semNote = 'no semantic index';
try {
  const ix = JSON.parse(readFileSync(join(web, 'search-index.json'), 'utf8'));
  const bin = readFileSync(join(web, 'search-vectors.bin'));
  need(/^[0-9a-f]{40}$/.test(ix.revision || ''), 'search index has no pinned model revision');
  need(bin.length === ix.rows * ix.dim, `search-vectors.bin is ${bin.length} bytes, expected ${ix.rows * ix.dim}`);
  const items = { papers: D.papers.items, repos: D.repos.items, hype: H.items };
  for (const [t, v] of Object.entries(ix.tabs)) {
    const missing = v.ids.filter(id => !items[t]?.[id]);
    if (missing.length) warn.push(`search index ${t} has ${missing.length} ids not in the data (stale index; rebuild with scripts/embed)`);
  }
  if (ix.data_generated_at !== D.generated_at) warn.push(`search index built from data ${ix.data_generated_at}, page data is ${D.generated_at}; new items fall back to keyword matching`);
  semNote = `semantic index ${ix.rows} vectors`;
} catch (e) {
  if (e.code !== 'ENOENT' || /search-vectors/.test(e.path || '')) fail.push(`semantic index unreadable: ${e.message}`);
}

// Pulse topic map (optional): ids unique, edges point at nodes, every node carries its windows and evidence posts.
let pulseNote = 'no pulse map', live = new Set();                 // live: the day's story ids (verdict rows below)
try {
  const P = JSON.parse(readFileSync(join(web, 'pulse.json'), 'utf8'));
  const ids = new Set(P.nodes.map(n => n.id));
  need(ids.size === P.nodes.length, 'pulse.json has duplicate node ids');
  for (const n of P.nodes) {
    need(P.windows.every(w => n.w?.[w] && Number.isFinite(n.w[w].weight)), `pulse node ${n.id} lacks window metrics`);
    // a node seen only on count-only networks, or only through posts the deleted-post recheck did not reach (B3), has its evidence
    // in the counts, never as a shown post: every post it publishes (its spread) is then a count
    const counted = r => r && typeof r === 'object' && POST_BODY.every(k => r[k] == null);
    need(Array.isArray(n.samples) && (n.samples.length > 0 || Object.keys(n.w?.['30d']?.nets || {}).every(k => COUNT_ONLY.has(k))
      || (Array.isArray(n.spread) && n.spread.length > 0 && n.spread.every(counted))),
      `pulse node ${n.id} has no evidence posts`);
  }
  for (const e of P.edges) need(ids.has(e.a) && ids.has(e.b), `pulse edge ${e.a}-${e.b} points at a missing node`);
  need(P.sources && Object.keys(P.sources).length > 0, 'pulse.json has no source status');
  // signal + live project counts: required once pulse.py writes them (method names the signal); older files only warn
  if (/signal/.test(P.method || '')) {
    for (const n of P.nodes) need(P.windows.every(w => Number.isFinite(n.w[w].signal) && n.w[w].signal_parts && Number.isFinite(n.w[w].reach)),
      `pulse node ${n.id} lacks signal / reach`);
    need(P.projects && typeof P.projects === 'object', 'pulse.json has no projects map');
    for (const id of Object.keys(H.items || {}))
      need(['7d', '30d'].every(w => Number.isFinite(P.projects?.[id]?.[w]?.voices)), `pulse.json projects lacks hype id ${id}`);
  } else warn.push('pulse.json predates the signal field (no signal / projects); the next pulse.py run adds them');
  // v3: who/where, common reach percentile, organic-vs-orchestrated signals, newsletter citations (required once method names reach_pct)
  if (/reach_pct/.test(P.method || '')) {
    const LABELS = ['too few posts', 'no coordination signal', 'some coordination signals', 'strong coordination signals'];
    for (const n of P.nodes) {
      need(P.windows.every(w => n.w[w].where && (n.w[w].reach_pct === null || Number.isFinite(n.w[w].reach_pct)) && n.with?.[w]),
        `pulse node ${n.id} lacks where / reach_pct / with`);
      const o = n.organic;
      need(o && LABELS.includes(o.label) && Number.isFinite(o.posts) && o.readings && Array.isArray(o.flags), `pulse node ${n.id} lacks organic signals`);
      for (const k of ['burst', 'dupe', 'single_topic', 'link_push'])
        need(o && (o[k] === null || (o[k] >= 0 && o[k] <= 1)), `pulse node ${n.id} organic.${k} out of range`);
    }
    need(P.windows.every(w => Array.isArray(P.citations?.[w]?.domains)), 'pulse.json citations missing a window');
  } else warn.push('pulse.json predates reach_pct / organic signals; the next pulse.py run adds them');
  // privacy: cited X handles are a ranking of (often pseudonymous) accounts; they stay in history/citations.json, never on the site
  need(!/"x_handles"/.test(readFileSync(join(web, 'pulse.json'), 'utf8')), 'pulse.json publishes x_handles (keep them in history/citations.json)');
  genAt = Date.parse(P.generated_at);
  live = new Set((P.stories || []).map(s => s.id));
  const links = new Set((readFileSync(join(web, 'pulse.json'), 'utf8').match(/https:\/\/mastodon\.social\/statuses\/\d+/g) || []));
  pulseNote = `pulse ${P.nodes.length} topics${P.projects ? `, ${Object.keys(P.projects).length} projects` : ''}, ${links.size} Mastodon links`;
  publicRules('pulse.json', P);
} catch (e) { if (e.code !== 'ENOENT') fail.push(`pulse.json unreadable: ${e.message}`); }
publicRules('hype.json', H);
hypeRules(H);

// Daily briefing (design rows 6, 8, 9; C7, C9, C13, C36): the public-data rules above, every pipeline record a proposal with no
// label word, a count from a source not fully fetched reads "not fetched" (never 0 or false), at most ten Top 10 rows, at most four
// gauges with the council names, every one a preview (none shipped), no trend or arrow before 14 ledger days, Risk and Jobs placeholders.
// Self-contained on purpose: the Top 10 recompute against pulse.json runs in tests/test_pulse.py.
const PREVIEW = 'preview, not yet reproducible', NOT_FETCHED = 'not fetched', NO_SOURCE = 'no qualified source', TREND_DAYS = 14;
const LABEL_WORDS = new Set(['REAL', 'OVERHYPED', 'FALSE', 'PUSHED', 'UNVERIFIED']);
const GAUGE_NAMES = new Set(['Releases / research output by area', 'Hype vs substance', 'Daily movers']);
const NET_ADAPTERS = { HN: ['Hacker News (Algolia)'], Lobsters: ['Lobsters (ai tag)'], Mastodon: ['Mastodon (mastodon.social tags)'],
  Reddit: ['Reddit (arctic-shift archive)', 'Reddit (official API)'], Bluesky: ['Bluesky (app password)'], Newsletter: ['Newsletters (RSS)'],
  Official: ['Official feeds (RSS)'] };
const TREND_KEY = /^(trend|trends|arrow|arrows|delta|day_over_day)$/;
function ledgerCount() {                                         // web/ledger/index.json from group E1 on; 0 without it
  try { const L = JSON.parse(readFileSync(join(web, 'ledger', 'index.json'), 'utf8')); const e = Array.isArray(L) ? L : L?.entries; return Array.isArray(e) ? e.length : 0; }
  catch (e) { if (e.code !== 'ENOENT') fail.push(`ledger/index.json unreadable: ${e.message}`); return 0; }
}
function briefingRules(B) {
  const F = 'briefing.json', st = {};
  for (const [net, ads] of Object.entries(NET_ADAPTERS)) {
    const s = ads.map(a => B.sources?.[a]?.status);
    st[net] = s.includes('ok') ? 'ok' : s.includes('partial') ? 'partial' : NOT_FETCHED;
  }
  // a reading from one source: a positive count or true, 0 or false only when that source was fully fetched, else "not fetched"
  const fetched = (v, net, at, bool = false) => {
    if (v === NOT_FETCHED || (bool ? v === true : Number.isInteger(v) && v > 0)) return;
    if ((bool ? v === false : v === 0) && st[net] === 'ok') return;
    finding(F, (v === 0 || v === false) ? `${net} not fully fetched but a count reads ${v} (must read "not fetched")` : `${net} reading is not a count, ${bool ? 'true, false' : '0'} or "not fetched"`, at);
  };
  need(Number.isFinite(Date.parse(B.generated_at)), 'briefing.json generated_at missing');
  need(/ BRT$/.test(B.window?.end_brt || '') && B.window?.end === B.generated_at, 'briefing.json window end is not generated_at printed in BRT');
  need(B.method?.version && /^[0-9a-f]{16}$/.test(B.method?.config_hash || ''), 'briefing.json method lacks its version or config hash');
  const recs = Array.isArray(B.records) ? B.records : [], ids = new Set(recs.map(r => r.id));
  need(Array.isArray(B.records) && ids.size === recs.length, 'briefing.json records missing or ids not unique');
  recs.forEach((r, i) => {
    const at = `records[${i}]`;
    if (r.state !== 'proposed') finding(F, 'pipeline record state is not "proposed"', `${at}.state`);
    for (const k of ['label', 'verdict']) if (k in r) finding(F, `pipeline record carries a ${k} field`, `${at}.${k}`);
    // a label word anywhere in a value, as an upper-case word ("REAL", "REAL (proposed)"); headlines and titles are what was posted
    walk(r, at, (v, p) => {
      if (typeof v !== 'string' || /\.(headline|title)$/.test(p)) return;
      for (const w of v.split(/[^A-Z]+/)) if (LABEL_WORDS.has(w)) finding(F, `pipeline record carries a label word (${w})`, p);
    });
    need(/^s:[0-9a-f]{12}$/.test(r.id || '') && r.method_version === B.method?.version && r.config_hash === B.method?.config_hash,
      `briefing record ${r.id} lacks its stable id, method version or config hash`);
    need(r.seen === 'new today' || /^first seen \d{4}-\d{2}-\d{2}$/.test(r.seen || ''), `briefing record ${r.id} lacks "new today" or its first-seen date`);
    const c = r.computed || {}, sub = r.substance || {};
    for (const [net, v] of Object.entries(c.networks || {})) fetched(v, net, `${at}.computed.networks.${net}`);
    fetched(c.newsletters, 'Newsletter', `${at}.computed.newsletters`);
    fetched(c.hn_points, 'HN', `${at}.computed.hn_points`);
    fetched(c.official, 'Official', `${at}.computed.official`, true);
    fetched(sub.official, 'Official', `${at}.substance.official`, true);
    need(Array.isArray(sub.repos) && Array.isArray(sub.papers) && r.related_in_topic?.reading === 'related in topic',
      `briefing record ${r.id} lacks its own-link substance or the "related in topic" reading`);
  });
  const top = Array.isArray(B.top10) ? B.top10 : [];
  need(Array.isArray(B.top10) && top.length <= 10, 'briefing.json top10 missing or longer than 10');
  top.forEach((t, i) => need(t.rank === i + 1 && ids.has(t.id) && (t.seen === 'new today' || /^first seen \d{4}-\d{2}-\d{2}$/.test(t.seen || '')),
    `briefing top10 row ${i + 1} lacks its rank, record or "new today" / first-seen date`));
  const ledger = ledgerCount(), days = Number.isInteger(B.ledger_days) ? B.ledger_days : NaN;
  need(days >= 0, 'briefing.json ledger_days missing');
  if (days > ledger) finding(F, `ledger_days ${days} exceeds the ${ledger} days in ledger/index.json`, 'ledger_days');
  const gauges = Array.isArray(B.gauges) ? B.gauges : [];
  need(Array.isArray(B.gauges) && gauges.length <= 4, 'briefing.json gauges missing or more than four');
  for (const k of Object.keys(B)) if (/score/i.test(k)) finding(F, 'combined score', k);
  gauges.forEach((g, i) => {
    const at = `gauges[${i}]`;
    if (!GAUGE_NAMES.has(g.name)) finding(F, 'gauge not named by the council (no combined score)', `${at}.name`);
    if (g.shipped || /shipped/i.test(g.status || '')) finding(F, 'gauge marked shipped (no gauge ships in S1)', `${at}.status`);
    else if (g.status !== PREVIEW) finding(F, `gauge status is not "${PREVIEW}"`, `${at}.status`);
    if (!g.coverage || typeof g.coverage !== 'object') finding(F, 'gauge without coverage', `${at}.coverage`);
    if (g.value === null && !/^insufficient data: /.test(g.reason || '')) finding(F, 'null gauge without an "insufficient data" reason', `${at}.reason`);
    if (Math.min(days, ledger) < TREND_DAYS)
      walk(g, at, (v, p) => { if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) if (TREND_KEY.test(k) && x != null) finding(F, `trend or arrow before ${TREND_DAYS} ledger days`, `${p}.${k}`); });
    if (g.id === 'hype_vs_substance') (g.value?.stories || []).forEach((row, j) => {
      const h = row.hype || {}, s = row.substance || {}, rp = `${at}.value.stories[${j}]`;
      for (const [net, v] of Object.entries(h.networks || {})) fetched(v, net, `${rp}.hype.networks.${net}`);
      fetched(h.newsletters, 'Newsletter', `${rp}.hype.newsletters`); fetched(h.hn_points, 'HN', `${rp}.hype.hn_points`);
      fetched(s.official, 'Official', `${rp}.substance.official`, true);
    });
  });
  const panel = id => (B.panels || []).find(p => p.id === id);
  need(panel('jobs')?.reading === NO_SOURCE, 'briefing.json Jobs panel does not read "no qualified source"');
  need(panel('risk') && Array.isArray(panel('risk').events) && (panel('risk').events.length > 0 || panel('risk').reading === NO_SOURCE) && !('dial' in panel('risk')),
    'briefing.json Risk panel is not a dated event log reading "no qualified source" (no dial)');
  return `briefing ${recs.length} records, Top 10 of ${top.length}, ${gauges.length} gauges, ${days} ledger days`;
}
let briefNote = 'no briefing';
try {
  const B = JSON.parse(readFileSync(join(web, 'briefing.json'), 'utf8'));
  publicRules('briefing.json', B);
  briefNote = briefingRules(B);
} catch (e) { fail.push(`briefing.json unreadable: ${e.message}`); }

// Verdict file (design row 7; C2, C10, C11, C30, C32): owner-reviewed rows, never in a bot commit (scripts/check_owner_files.py in ci.yml).
// A row's s: id resolves through story-aliases.json to the story that took its posts (before a live story of the same id: B1 note), else to
// a story in the day's pulse.json, else to an id a ledger/ids/YYYY-MM-DD.json archive file records as published. An upgraded row (REAL,
// OVERHYPED, FALSE, PUSHED) carries its named claim (the document, for PUSHED), a primary source URL that is never an X, LinkedIn or YouTube
// post, a reason in en and pt, the confirming commit and the confirmed date; a FALSE row links the right-of-reply and corrections path.
const VERDICT_KEYS = new Set(['id', 'label', 'claim', 'document', 'source', 'reason', 'commit', 'confirmed', 'reply']);
const UPGRADED = new Set(['REAL', 'OVERHYPED', 'FALSE', 'PUSHED']), CLAIMED = new Set(['REAL', 'OVERHYPED', 'FALSE']);
const NO_SOURCE_NET = new Set(['X', 'LinkedIn', 'YouTube']), REPLY_PATH = 'POLICY.md#reply';
const SID = /^s:[0-9a-f]{12}$/, COMMIT = /^[0-9a-f]{7,40}$/;
const DAY = { test: s => /^\d{4}-\d{2}-\d{2}$/.test(s) && Number.isFinite(Date.parse(`${s}T00:00:00Z`)) && new Date(`${s}T00:00:00Z`).toISOString().slice(0, 10) === s };   // a real calendar date
const CORRECTION_KEYS = new Set(['id', 'date', 'kind', 'about', 'text', 'link']);
const text = v => typeof v === 'string' && v.trim() !== '';
function readJSON(f, missing) {                                  // null when absent (with the missing message, if one is given) or unreadable
  try { return JSON.parse(readFileSync(join(web, f), 'utf8')); }
  catch (e) { if (e.code !== 'ENOENT') fail.push(`${f} unreadable: ${e.message}`); else if (missing) fail.push(missing); return null; }
}
function archive() {                                             // ledger/ids/YYYY-MM-DD.json (written by group E1): {"date", "ids": [...]}
  const ids = new Set(); let files = [];
  try { files = readdirSync(join(web, 'ledger', 'ids')).filter(f => f.endsWith('.json')).sort(); }
  catch (e) { if (e.code !== 'ENOENT') fail.push(`ledger/ids unreadable: ${e.message}`); }
  for (const f of files) {
    const A = readJSON(`ledger/ids/${f}`);
    if (A && DAY.test(A.date || '') && `${A.date}.json` === f && Array.isArray(A.ids) && A.ids.every(x => SID.test(x))) A.ids.forEach(x => ids.add(x));
    else if (A) fail.push(`ledger/ids/${f} is not {"date": "<its file name date>", "ids": ["s:<12 hex>", ...]}`);
  }
  return { ids, days: files.length };
}
function aliasMap() {                                            // story-aliases.json (pulse.py, bot-written): {"aliases": {old: {to, since}}}
  const A = readJSON('story-aliases.json'), out = {};
  if (A === null) return out;
  if (!A.aliases || typeof A.aliases !== 'object' || Array.isArray(A.aliases)) { fail.push('story-aliases.json lacks its aliases map'); return out; }
  for (const [k, e] of Object.entries(A.aliases)) {
    if (SID.test(k) && SID.test(e?.to || '') && e.to !== k && DAY.test(e.since || '')) out[k] = e.to;
    else finding('story-aliases.json', 'alias is not "s:<id>": {"to": "s:<another id>", "since": "YYYY-MM-DD"}', `aliases.${k}`);
  }
  return out;
}
function verdictRules(V, C) {
  const F = 'verdicts.json', alias = aliasMap(), ar = archive(), how = { live: 0, alias: 0, archive: 0 };
  for (const [f, lang] of [['POLICY.md', 'en'], ['POLICY.pt.md', 'pt']]) {
    let md = '';
    try { md = readFileSync(join(web, f), 'utf8'); } catch (e) { fail.push(`${f} missing: the ${lang} right-of-reply and corrections policy is published before the first FALSE row`); continue; }
    for (const a of ['reply', 'corrections', 'removals']) need(md.includes(`<a id="${a}"></a>`), `${f} lacks its <a id="${a}"></a> section`);
  }
  function resolve(id) {                                         // 'alias' | 'live' | 'archive' | null
    const seen = [id];
    while (alias[seen.at(-1)] && !seen.includes(alias[seen.at(-1)])) seen.push(alias[seen.at(-1)]);
    if (alias[seen.at(-1)]) finding('story-aliases.json', 'alias cycle', `aliases.${id}`);
    if (seen.length > 1 && live.has(seen.at(-1))) return 'alias';
    if (live.has(id)) return 'live';
    return seen.some(x => ar.ids.has(x)) ? 'archive' : null;
  }
  const rows = Array.isArray(V?.rows) ? V.rows : [];
  if (V) need(Array.isArray(V.rows), 'verdicts.json lacks its rows list');
  const claims = new Set();
  rows.forEach((r, i) => {
    const at = `rows[${i}]`;
    if (!r || typeof r !== 'object' || Array.isArray(r)) return finding(F, 'verdict row is not an object', at);
    for (const k of Object.keys(r)) if (!VERDICT_KEYS.has(k)) finding(F, `verdict row carries a field outside the verdict shape (${k}); a label is on a claim or story, never on a person or account`, `${at}.${k}`);
    if (!SID.test(r.id || '')) finding(F, 'verdict row id is not a story id ("s:" and 12 hex)', `${at}.id`);
    else { const h = resolve(r.id); if (h) how[h]++; else finding(F, 'orphaned s: id: resolves to no story in pulse.json, no id in a ledger/ids/ archive file and no story-aliases.json alias', `${at}.id`); }
    const key = JSON.stringify([r.id, r.claim ?? null, r.document ?? null]);
    if (claims.has(key)) finding(F, 'two verdict rows on one story and the same claim or document (one row per claim: change the row by a pull request and log the change in corrections.json)', at);
    claims.add(key);
    if (!LABEL_WORDS.has(r.label)) return finding(F, 'verdict row label is not REAL, OVERHYPED, FALSE, PUSHED or UNVERIFIED', `${at}.label`);
    if (r.source != null && NO_SOURCE_NET.has(urlNet(String(r.source)))) finding(F, 'verdict row primary source is an X, LinkedIn or YouTube post (a claim with only an X source stays UNVERIFIED and names the account and date with no link)', `${at}.source`);
    if (!UPGRADED.has(r.label)) return;
    if (CLAIMED.has(r.label) && !text(r.claim)) finding(F, `${r.label} verdict row lacks its named claim`, `${at}.claim`);
    if (r.label === 'PUSHED' && !text(r.document)) finding(F, 'PUSHED verdict row lacks its document (a public document showing an undisclosed paid or material connection)', `${at}.document`);
    if (!/^https?:\/\/[^\s]+$/.test(r.source || '')) finding(F, 'upgraded verdict row lacks its primary source URL', `${at}.source`);
    for (const lang of ['en', 'pt']) if (!text(r.reason?.[lang])) finding(F, `upgraded verdict row lacks its reason in ${lang}`, `${at}.reason.${lang}`);
    if (!COMMIT.test(r.commit || '')) finding(F, 'upgraded verdict row lacks its confirming commit (7 to 40 hex)', `${at}.commit`);
    if (!DAY.test(r.confirmed || '')) finding(F, 'upgraded verdict row lacks its confirmed date (YYYY-MM-DD)', `${at}.confirmed`);
    if (r.label === 'FALSE' && r.reply !== REPLY_PATH) finding(F, `FALSE verdict row does not link the right-of-reply and corrections path (${REPLY_PATH})`, `${at}.reply`);
  });
  // corrections.json: entries c:1, c:2, ... in order (appended, never edited over: scripts/check_owner_files.py compares the base commit)
  const E = Array.isArray(C?.entries) ? C.entries : [];
  if (C) need(Array.isArray(C.entries), 'corrections.json lacks its entries list');
  E.forEach((e, i) => {
    const at = `entries[${i}]`;
    if (!e || typeof e !== 'object' || Array.isArray(e)) return finding('corrections.json', 'correction entry is not an object', at);
    for (const k of Object.keys(e)) if (!CORRECTION_KEYS.has(k)) finding('corrections.json', `correction entry carries a field outside the entry shape (${k})`, `${at}.${k}`);
    if (e.id !== `c:${i + 1}`) finding('corrections.json', 'correction entry id is not its place in the log (c:1, c:2, ...)', `${at}.id`);
    if (!DAY.test(e.date || '') || !['correction', 'reply'].includes(e.kind)) finding('corrections.json', 'correction entry lacks its date or kind (correction or reply)', at);
    if (e.about != null && !SID.test(e.about)) finding('corrections.json', 'correction entry about is not a story id', `${at}.about`);
    // our correction is written in both languages; a reply is the replying party's own words, in the language they sent
    if (e.kind === 'reply' ? !(text(e.text?.en) || text(e.text?.pt)) : !(text(e.text?.en) && text(e.text?.pt))) finding('corrections.json', 'correction entry lacks its text (a correction in en and pt, a reply in the language sent)', `${at}.text`);
    if (e.link != null && !/^https?:\/\/[^\s]+$/.test(e.link)) finding('corrections.json', 'correction entry link is not a URL', `${at}.link`);
  });
  return `verdicts ${rows.length} rows (${how.live} live, ${how.alias} by alias, ${how.archive} by archive; ${Object.keys(alias).length} aliases, ${ar.days} archive days), ${E.length} corrections`;
}
let verdictNote = 'no verdicts';
{
  const V = readJSON('verdicts.json', 'verdicts.json missing (owner-reviewed; {"rows": []} when it holds no row)');
  const C = readJSON('corrections.json', 'corrections.json missing (owner-reviewed, append-only; {"entries": []} when it holds no entry)');
  if (V) publicRules('verdicts.json', V);
  if (C) publicRules('corrections.json', C);
  verdictNote = verdictRules(V, C);
}

// Removal requests and deleted posts (design row 7, C34): removals.json (owner-reviewed) and checks/dossier-gone.json (bot-written,
// append-only) name posts by the SHA256 of the post URL as stored (hashes, not the URLs); hype.json holds no URL either list names
// (the removal pull request scrubs it); pulse.json and briefing.json hold no URL that dossier-gone.json lists, nor one that a
// removals.json entry dated before their generated_at day (UTC) names: they drop a requested post at the next daily rebuild.
const HEX64 = /^[0-9a-f]{64}$/;
function hashList(f, key, dateKey, missing) {                    // {sha256: date} of the well-formed entries
  const R = readJSON(f, missing), out = new Map();
  if (R === null) return out;
  publicRules(f, R);
  if (!Array.isArray(R[key])) { fail.push(`${f} lacks its ${key} list`); return out; }
  const shape = `{"sha256": "<64 hex>", "${dateKey}": "YYYY-MM-DD"}`;
  R[key].forEach((e, i) => {
    const ok = e && typeof e === 'object' && !Array.isArray(e) && HEX64.test(e.sha256 || '') && DAY.test(e[dateKey] || '')
      && Object.keys(e).every(k => k === 'sha256' || k === dateKey);
    if (ok) out.set(e.sha256, e[dateKey]); else finding(f, `entry is not ${shape}`, `${key}[${i}]`);
  });
  return out;
}
let removalNote = 'no removals';
{
  const R = hashList('removals.json', 'entries', 'date', 'removals.json missing (owner-reviewed; {"entries": []} when it holds no request)');
  const G = hashList('checks/dossier-gone.json', 'gone', 'found');
  let pending = 0;
  for (const f of ['hype.json', 'pulse.json', 'briefing.json']) {
    const X = f === 'hype.json' ? H : readJSON(f);
    if (!X) continue;
    const day = f === 'hype.json' ? null : String(X.generated_at || '').slice(0, 10);
    const why = u => {
      const h = sha(u), d = R.get(h);
      if (d !== undefined && (day === null || d < day)) return 'post named by removals.json is still published';
      if (d !== undefined) pending++;
      return G.has(h) ? 'post whose URL hash checks/dossier-gone.json lists is still published' : null;
    };
    walk(X, '', (v, at) => { const w = typeof v === 'string' && /^https?:\/\//.test(v) && why(v); if (w) finding(f, w, at); });
  }
  removalNote = `removals: ${R.size} requests, ${G.size} dossier posts found gone, none published` + (pending ? ` (${pending} places in pulse.json or briefing.json await the next daily rebuild)` : '');
}

for (const [rule, at] of Object.entries(found)) fail.push(`${rule} at ${at.length} place${at.length > 1 ? 's' : ''}, e.g. ${at.slice(0, 3).join(', ')}`);
for (const w of warn) console.warn('warning: ' + w);
if (fail.length) { console.error('page check FAILED\n- ' + fail.join('\n- ')); process.exit(1); }
console.log(`page check ok: script parses; ${Object.keys(D.papers.items).length} papers, ${Object.keys(D.repos.items).length} repos, ${Object.keys(H.items).length} hype projects; ${semNote}; ${pulseNote}; ${briefNote}; ${verdictNote}; ${removalNote}`);
