// Frontend adapter plugin (design row 16; Decision 9): the per-language string and data-field tables the dehype pages load,
// web/i18n/table.en.json and web/i18n/table.pt.json, from the hand-written i18n/strings.json. Each table holds every string entry with
// its "ref" resolved (Decision 10: the X-figure placeholder lives beside its list) and only the text the page needs in that language:
// en alone in the English table, en and pt in the Portuguese one (web/dehype.js tr() maps a data string's English back to its entry),
// plus the data files' "fields" and "methods" maps. Deterministic: the same strings.json gives the same bytes, so the refresh never
// stages the tables. A pull request that changes web/verdicts.json or web/i18n/strings.json runs
// `npm ci --prefix scripts/dehype --ignore-scripts && node scripts/dehype/compose.mjs` and commits the four feeds and the two tables
// (web/POLICY.md; tests/test_feed.py fails it otherwise). Node standard library only.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

export const TABLES = { en: 'i18n/table.en.json', pt: 'i18n/table.pt.json' };
const at = (o, path) => path.split(/\.|\[(\d+)\]/).filter(x => x != null && x !== '').reduce((v, k) => v == null ? v : v[k], o);

export function readInputs(web) {                               // strings.json and the files its refs name
  const I = JSON.parse(readFileSync(join(web, 'i18n', 'strings.json'), 'utf8')), refs = {};
  for (const e of Object.values(I.strings || {})) if (e.ref) { const f = e.ref.split('#')[0]; refs[f] ||= JSON.parse(readFileSync(join(web, 'i18n', f), 'utf8')); }
  return { I, refs };
}

export function build({ I, refs }) {
  const out = {};
  for (const [lang, f] of Object.entries(TABLES)) {
    const strings = {};
    for (const [k, e0] of Object.entries(I.strings || {})) {
      const e = e0.ref ? at(refs[e0.ref.split('#')[0]], e0.ref.split('#')[1]) : e0;
      if (!e || typeof e.en !== 'string' || typeof e.pt !== 'string') throw new Error(`i18n/strings.json ${k} lacks its en or pt text`);
      strings[k] = lang === 'en' ? { en: e.en } : { en: e.en, pt: e.pt };
    }
    out[f] = JSON.stringify({ lang, from: 'i18n/strings.json', written_by: 'scripts/dehype/plugins/frontend.mjs', fields: I.fields || {}, methods: I.methods || {}, strings });
  }
  return out;
}

export const name = 'dehype-frontend';
export function apply(ctx, { inputs, emit }) {
  ctx.effect(() => { for (const [f, text] of Object.entries(build(inputs))) emit(f, text); }, 'dehype-frontend: the page tables');
}
export default { name, apply };
