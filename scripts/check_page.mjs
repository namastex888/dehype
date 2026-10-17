// Static page gate: the inline script parses, the data files parse, every field the page reads exists, and the public
// files keep the public-data rules (no person handle; Reddit, X, LinkedIn, YouTube, Telegram counts only; Mastodon counts only
// unless linked by its handle-free mastodon.social/statuses link with a fresh passing render check; no unlisted X figure).
// Node standard library only. Usage: node scripts/check_page.mjs [webDir]
import { readFileSync } from 'node:fs';
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
const NET_URL = [['Reddit', 'reddit\\.com|redd\\.it'], ['X', 'x\\.com|twitter\\.com'], ['LinkedIn', 'linkedin\\.com|lnkd\\.in'],
  ['YouTube', 'youtube\\.com|youtu\\.be'], ['Telegram', 't\\.me|telegram\\.me']]
  .map(([n, h]) => [n, new RegExp(`^https?://(?:[\\w-]+\\.)*(?:${h})(?=[/:?#]|$)`, 'i')]);
const ACCOUNT_URL = /^https?:\/\/(?!(?:[\w-]+\.)*npmjs\.(?:org|com)\/)[^\s?#]*\/@|bsky\.app\/profile\/[^/\s]+\/post\/|\/users\/[^/\s]+\/statuses\/|did:(?:plc|web):/i;
const STATUS_URL = /^https:\/\/mastodon\.social\/statuses\/(\d{1,20})$/, LINK_MS = 7 * 864e5;
let MC = {}, genAt = NaN;                                        // the render-check cache; pulse.json generated_at (ms)
try { MC = JSON.parse(readFileSync(join(web, 'checks', 'mastodon-links.json'), 'utf8')).statuses || {}; }
catch (e) { if (e.code !== 'ENOENT') fail.push(`checks/mastodon-links.json unreadable: ${e.message}`); }
const MASTO_RULE = 'Mastodon link without a render check passed less than 7 days before pulse.json generated_at';
function mastoLink(id) {                                         // null when the link may stand, else why not
  const e = MC[id];
  if (!e) return 'no check in checks/mastodon-links.json';
  if (!e.passed_at) return 'its check never passed';
  return genAt - Date.parse(e.passed_at) < LINK_MS ? null : 'its last pass is 7 days or more before generated_at';
}
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
let pulseNote = 'no pulse map';
try {
  const P = JSON.parse(readFileSync(join(web, 'pulse.json'), 'utf8'));
  const ids = new Set(P.nodes.map(n => n.id));
  need(ids.size === P.nodes.length, 'pulse.json has duplicate node ids');
  for (const n of P.nodes) {
    need(P.windows.every(w => n.w?.[w] && Number.isFinite(n.w[w].weight)), `pulse node ${n.id} lacks window metrics`);
    // a node seen only on count-only networks has its evidence in the counts, never as a shown post
    need(Array.isArray(n.samples) && (n.samples.length > 0 || Object.keys(n.w?.['30d']?.nets || {}).every(k => COUNT_ONLY.has(k))),
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
  const links = new Set((readFileSync(join(web, 'pulse.json'), 'utf8').match(/https:\/\/mastodon\.social\/statuses\/\d+/g) || []));
  pulseNote = `pulse ${P.nodes.length} topics${P.projects ? `, ${Object.keys(P.projects).length} projects` : ''}, ${links.size} Mastodon links`;
  publicRules('pulse.json', P);
} catch (e) { if (e.code !== 'ENOENT') fail.push(`pulse.json unreadable: ${e.message}`); }
publicRules('hype.json', H);
hypeRules(H);

for (const [rule, at] of Object.entries(found)) fail.push(`${rule} at ${at.length} place${at.length > 1 ? 's' : ''}, e.g. ${at.slice(0, 3).join(', ')}`);
for (const w of warn) console.warn('warning: ' + w);
if (fail.length) { console.error('page check FAILED\n- ' + fail.join('\n- ')); process.exit(1); }
console.log(`page check ok: script parses; ${Object.keys(D.papers.items).length} papers, ${Object.keys(D.repos.items).length} repos, ${Object.keys(H.items).length} hype projects; ${semNote}; ${pulseNote}`);
