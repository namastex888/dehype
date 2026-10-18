// Feed adapter plugin (design row 15; C1, C17, C43): RSS 2.0 and JSON Feed 1.1, in English and Portuguese, one item per Top 10 story of
// the day's briefing.json, in rank order. Both languages carry the same item ids and the same headlines (as posted, with their lang tag;
// never translated); our own text (verdict state, readings, labels) comes from i18n/strings.json in the feed's language. Each item
// carries the story's stable id, its verdict state ("proposed by the pipeline, not reviewed" until an owner row in verdicts.json,
// resolved through story-aliases.json, confirms a label) and its source links. A count-only network (Reddit, X, LinkedIn, YouTube,
// Telegram, Discord, and Mastodon: a feed reader keeps an item after a later render check fails or the post is deleted) is never
// linked, only counted; no author or handle is written. Every date comes from briefing.json generated_at, so the same inputs give the same bytes. Node standard library only;
// scripts/dehype/compose.mjs loads it as a Cordis plugin (apply) and writes what it emits. A stale briefing (compose.mjs, after a failed Pulse
// step; C5) has no Top 10: each feed then reads "stale since" its date with the reason, in its description and in one item dated by the
// failed run (id stale:<date>), and carries the stale object in _dehype; no story of the earlier briefing is carried over.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

export const SITE = 'https://namastex888.github.io/dehype/';
export const FEEDS = { en: { code: 'en', q: '', xml: 'feed.xml', json: 'feed.json' }, pt: { code: 'pt-BR', q: '?lang=pt', xml: 'feed.pt.xml', json: 'feed.pt.json' } };
const COUNT_ONLY = new Set(['Reddit', 'X', 'LinkedIn', 'YouTube', 'Telegram', 'Discord', 'Mastodon']);
const COUNT_ONLY_URL = /^https?:\/\/(?:[\w-]+\.)*(?:reddit\.com|redd\.it|x\.com|twitter\.com|t\.co|linkedin\.com|lnkd\.in|youtube\.com|youtu\.be|t\.me|telegram\.me|discord\.com|discord\.gg|mastodon\.social)(?:[/:?#]|$)/i;
const LABELS = { REAL: 'label.real', OVERHYPED: 'label.overhyped', FALSE: 'label.false', PUSHED: 'label.pushed', UNVERIFIED: 'label.unverified' };
const STATUS = { ok: 'status.ok', partial: 'status.partial', failed: 'status.failed', 'not connected': 'status.not_connected', unknown: 'status.unknown', 'not fetched': 'reading.not_fetched' };

const json = (web, f, empty) => { try { return JSON.parse(readFileSync(join(web, f), 'utf8')); } catch (e) { if (empty !== undefined && e.code === 'ENOENT') return empty; throw e; } };
export function readInputs(web) {                               // the committed files the feeds are built from
  return { briefing: json(web, 'briefing.json'), pulse: json(web, 'pulse.json'), verdicts: json(web, 'verdicts.json', { rows: [] }),
    aliases: json(web, 'story-aliases.json', { aliases: {} }), strings: json(web, 'i18n/strings.json').strings };
}

function verdictsById(V, A) {                                     // web/dehype.js verdicts(): an alias row follows its story
  const M = A?.aliases || {}, to = id => { const seen = [id]; while (M[seen.at(-1)]?.to && !seen.includes(M[seen.at(-1)].to)) seen.push(M[seen.at(-1)].to); return seen.at(-1); };
  const m = new Map();
  for (const r of V?.rows || []) { m.set(to(r.id), r); if (!m.has(r.id)) m.set(r.id, r); }
  return m;
}
const http = u => typeof u === 'string' && /^https?:\/\//.test(u);
const allowed = (u, net) => http(u) && !COUNT_ONLY_URL.test(u) && !COUNT_ONLY.has(net);
const xml = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' })[c]);

export function build({ briefing: B, pulse: P, verdicts: V, aliases: A, strings: S }) {
  const at = B.generated_at, when = new Date(at);
  if (!Number.isFinite(when.getTime())) throw new Error('briefing.json generated_at is not a date');
  const recs = new Map((B.records || []).map(r => [r.id, r])), stories = new Map((P.stories || []).map(s => [s.id, s])), ver = verdictsById(V, A);
  const rows = (B.top10 || []).map(x => recs.get(x.id)).filter(Boolean);
  const out = {};
  for (const [lang, L] of Object.entries(FEEDS)) {
    const t = (k, v = {}) => { const e = S[k]; if (!e || typeof e.en !== 'string') throw new Error(`i18n/strings.json lacks ${k}`); return (e[lang] || e.en).replace(/\{(\w+)\}/g, (m, x) => x in v ? String(v[x]) : m); };
    const byEn = new Map(Object.entries(S).filter(([, e]) => typeof e.en === 'string').map(([k, e]) => [e.en, k]));
    const tr = v => { if (typeof v !== 'string') return v; const k = byEn.get(v) || STATUS[v]; if (k) return t(k); const m = /^first seen (\d{4}-\d{2}-\d{2})$/.exec(v); return m ? t('seen.first_seen', { date: m[1] }) : v; };
    const nm = n => { const k = byEn.get(n); return k && k.startsWith('name.') ? t(k) : n; };
    const rd = v => v === true ? t('ui.yes') : v === false ? t('ui.no') : v == null ? '—' : typeof v === 'number' ? String(v) : tr(v);
    const page = (p, id) => `${SITE}${p}.html${L.q}${id ? '#' + id : ''}`;
    const items = rows.map(r => {
      const s = stories.get(r.id) || {}, c = r.computed || {}, sub = r.substance || {}, v = ver.get(r.id);
      const verdict = v && LABELS[v.label]
        ? { state: 'confirmed', label: v.label, text: t(LABELS[v.label]), confirmed: v.confirmed || null, source: http(v.source) ? v.source : null, reason: v.reason?.[lang] || null }
        : { state: 'proposed', label: null, text: t('state.proposed') };
      const story = [s.link, s.url].find(u => allowed(u, 'story')) || null;
      const links = [], seen = new Set(), add = o => { if (o.url && !seen.has(o.url)) { seen.add(o.url); links.push(o); } };
      if (story) add({ net: 'story', url: story });
      for (const p of s.posts || []) if (p.title && allowed(p.url, p.net)) add({ net: p.net, url: p.url, title: p.title, lang: p.lang || 'und' });
      for (const p of s.path || []) if (['Official', 'Newsletter'].includes(p.net) && allowed(p.url, p.net)) add({ net: p.net, url: p.url, ...(p.who ? { who: p.who } : {}) });
      for (const u of [...(sub.repos || []), ...(sub.papers || [])]) if (allowed(u, 'own')) add({ net: 'own', url: u });
      const counted = Object.entries(s.nets || {}).filter(([n, k]) => COUNT_ONLY.has(n) && k > 0)
        .map(([n, k]) => t(k === 1 ? 'ui.counted.one' : 'ui.counted', { net: nm(n), n: k }));
      const st = Object.entries(r.sources || {}), ok = st.filter(([, x]) => x === 'ok').length;
      const nets = Object.entries(c.networks || {}).filter(([, x]) => x !== 0).map(([n, x]) => `${nm(n)} ${rd(x)}`).join(' · ') || '—';
      const lines = [`${tr(r.seen)} · ${t(r.kind === 'news' ? 'kind.news' : 'kind.chatter')}${r.release ? ' · ' + r.release : ''}`,
        `${t('ui.verdict')}: ${verdict.text}${verdict.reason ? ' · ' + verdict.reason : ''}${verdict.confirmed ? ' · ' + t('ui.confirmed', { date: verdict.confirmed }) : ''}`,
        `${t('ui.voices')}: ${rd(c.voices)} · ${t('ui.networks')}: ${nets}`,
        `${t('ui.newsletters')}: ${rd(c.newsletters)} · ${t('ui.lab_post')}: ${rd(c.official)} · ${t('ui.hn_points')}: ${rd(c.hn_points)}`,
        [t('ui.sources_ok', { n: ok, total: st.length }), ...st.filter(([, x]) => x !== 'ok').map(([n, x]) => `${nm(n)} ${tr(x)}`)].join(' · ')];
      const own = links.filter(o => o.net === 'story' || o.net === 'own'), posts = links.filter(o => !own.includes(o));
      const name = o => o.title ?? o.who ?? o.url, groups = [[t('ui.posts'), posts, counted], [t('substance.from'), own, []]].filter(([, l, x]) => l.length || x.length);
      const text = [...lines, ...groups.flatMap(([h, l, x]) => ['', `${h}:`, ...l.map(o => `- ${o.net === 'story' || o.net === 'own' ? o.url : `${nm(o.net)}: ${name(o)} ${o.url}`}`), ...x.map(y => `- ${y}`)]),
        '', `${t('ui.evidence')}: ${page('stories', r.id)}`].join('\n');
      const html = lines.map(l => `<p>${xml(l)}</p>`).join('') + groups.map(([h, l, x]) => `<p>${xml(h)}:</p><ul>${l.map(o => `<li>${o.net === 'story' || o.net === 'own' ? '' : xml(nm(o.net)) + ': '}`
        + `<a href="${xml(o.url)}"${o.lang ? ` lang="${xml(o.lang)}"` : ''}>${xml(name(o))}</a></li>`).join('')}${x.map(y => `<li>${xml(y)}</li>`).join('')}</ul>`).join('')
        + `<p><a href="${xml(page('stories', r.id))}">${xml(t('ui.evidence'))}</a></p>`;
      const readings = { seen: r.seen, kind: r.kind, voices: c.voices ?? null, networks: c.networks || {}, newsletters: c.newsletters ?? null, official: c.official ?? null, hn_points: c.hn_points ?? null, sources: r.sources || {} };
      return { r, url: page('stories', r.id), story, verdict, links, readings, text, html };
    });
    const title = `dehype · ${t('index.title')}`, home = page('index'), about = page('method'), S0 = B.stale?.since ? B.stale : null;
    const note = S0 && { id: `stale:${S0.since}`, when: new Date(S0.at), title: t('stale.failed', { date: S0.since, reason: tr(S0.reason) }), text: t('stale.failed.note', { date: S0.since }) };
    const scope = note ? `${note.title}. ${note.text}` : t('index.scope'), built = note ? note.when : when;
    out[L.xml] = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
<title>${xml(title)}</title>
<link>${xml(home)}</link>
<description>${xml(scope)}</description>
<language>${L.code}</language>
<lastBuildDate>${built.toUTCString()}</lastBuildDate>
<docs>https://www.rssboard.org/rss-specification</docs>
<atom:link href="${SITE}${L.xml}" rel="self" type="application/rss+xml"/>
${items.map(i => `<item>
<title>${xml(i.r.headline)}</title>
<link>${xml(i.url)}</link>
<guid isPermaLink="false">${xml(i.r.id)}</guid>
<pubDate>${when.toUTCString()}</pubDate>
<category domain="${xml(about)}">${xml(i.verdict.text)}</category>
<dc:language>${xml(i.r.lang || 'und')}</dc:language>
<description>${xml(i.html)}</description>
</item>
`).join('')}${note ? `<item>
<title>${xml(note.title)}</title>
<link>${xml(home)}</link>
<guid isPermaLink="false">${xml(note.id)}</guid>
<pubDate>${note.when.toUTCString()}</pubDate>
<description>${xml(note.text)}</description>
</item>
` : ''}</channel>
</rss>
`;
    out[L.json] = JSON.stringify({ version: 'https://jsonfeed.org/version/1.1', title, home_page_url: home, feed_url: `${SITE}${L.json}`, description: scope, language: L.code,
      _dehype: { about, generated_at: at, window_end: B.window?.end_brt || null, items: 'briefing.json top10, in rank order', ...(S0 ? { stale: S0 } : {}) },
      items: items.map(i => ({ id: i.r.id, url: i.url, ...(i.story ? { external_url: i.story } : {}), title: i.r.headline, language: i.r.lang || 'und', content_text: i.text, date_published: at,
        _dehype: { about, id: i.r.id, verdict: i.verdict, sources: i.links, readings: i.readings } })).concat(note
        ? [{ id: note.id, url: home, title: note.title, language: L.code, content_text: note.text, date_published: S0.at }] : []) });
  }
  return out;
}

export const name = 'dehype-feed';
export function apply(ctx, { inputs, emit }) {                  // one-shot: build, emit through a fiber effect, keep no state after it
  ctx.effect(() => { for (const [f, text] of Object.entries(build(inputs))) emit(f, text); }, 'dehype-feed: the four feeds');
}
export default { name, apply };
