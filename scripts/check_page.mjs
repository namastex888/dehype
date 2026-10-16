// Static page gate: the inline script parses, the data files parse, and every field the page reads exists.
// Node standard library only. Usage: node scripts/check_page.mjs [webDir]
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const web = process.argv[2] || 'web';
const fail = [];
const need = (cond, msg) => { if (!cond) fail.push(msg); };
const warn = [];

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
  need(bin.length === ix.rows * ix.dim, `search-vectors.bin is ${bin.length} bytes, expected ${ix.rows * ix.dim}`);
  const items = { papers: D.papers.items, repos: D.repos.items, hype: H.items };
  for (const [t, v] of Object.entries(ix.tabs)) {
    const missing = v.ids.filter(id => !items[t]?.[id]);
    if (missing.length) warn.push(`search index ${t} has ${missing.length} ids not in the data (stale index; rebuild with scripts/embed)`);
  }
  if (ix.data_generated_at !== D.generated_at) warn.push(`search index built from data ${ix.data_generated_at}, page data is ${D.generated_at}; new items fall back to keyword matching`);
  semNote = `semantic index ${ix.rows} vectors`;
} catch (e) { if (e.code !== 'ENOENT') fail.push(`semantic index unreadable: ${e.message}`); }

for (const w of warn) console.warn('warning: ' + w);
if (fail.length) { console.error('page check FAILED\n- ' + fail.join('\n- ')); process.exit(1); }
console.log(`page check ok: script parses; ${Object.keys(D.papers.items).length} papers, ${Object.keys(D.repos.items).length} repos, ${Object.keys(H.items).length} hype projects; ${semNote}`);
