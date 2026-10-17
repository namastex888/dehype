// dehype shell (design rows 10, 11, 13; D5 amended: static pages, one stylesheet, one script, no build). Each page names the data
// files it reads in <body data-src>; our own text comes from i18n/strings.json in en and pt; headlines and titles stay as posted with
// their lang tag. The data files carry our own text in English: tr() maps such a value back to its strings.json entry with the
// templates scripts/check_page.mjs uses (ours) and renders the page language. English method paragraphs are never shown: pages link
// the method anchors (strings.json methods). Dossier prose shows in Portuguese only from a reviewed i18n/dossier.pt.json entry whose
// SHA256 matches the current English, else in English under the fixed Portuguese notice (C24). Classic script: new Function parses it.
'use strict';
const DH = (() => {
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const REPO = 'https://github.com/namastex888/dehype/blob/dev/';            // method and policy links until group C3 adds method.html
const METHOD = { en: REPO + 'METHODOLOGY.md', pt: REPO + 'METHODOLOGY.pt.md' }, POLICY = { en: REPO + 'POLICY.md', pt: REPO + 'POLICY.pt.md' };
const NAV = [['stories', 'nav.stories'], ['output', 'nav.output'], ['hype', 'nav.hype'], ['index', 'nav.console']];
const COUNT_ONLY = new Set(['Reddit', 'X', 'LinkedIn', 'YouTube', 'Telegram', 'Discord', 'Mastodon']);
const NOT_FETCHED = 'not fetched', DAY = 864e5;
const store = { get: k => { try { return localStorage.getItem(k); } catch { return null; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch { } } };
const page = document.body.dataset.page, files = (document.body.dataset.src || '').split(/\s+/).filter(Boolean);
let I = { strings: {}, fields: {} }, REF = {}, lang = 'en', theme = 'dark', DATA_KEYS = [], render = () => { };
const cache = {};
// ------------------------------------------------------------------ data and strings
function load(f) { return cache[f] ||= fetch(f, { cache: 'no-cache' }).then(r => { if (!r.ok) throw new Error(`${f}: HTTP ${r.status}`); return r.json(); }); }
const opt = (f, empty) => load(f).catch(() => empty);
const entry = k => { const e = I.strings[k]; return e && e.ref ? REF[k] : e; };
function t(k, v = {}) { const e = entry(k), s = e ? (e[lang] || e.en) : k; return s.replace(/\{(\w+)\}/g, (m, x) => x in v ? v[x] : m); }
const RX = {}, TR = new Map();
const rx = k => RX[k] ||= new RegExp('^' + String(entry(k)?.en ?? '\u0000').replace(/[.*+?^$()|[\]\\]/g, '\\$&').replace(/\\?\{(\w+)\\?\}/g, '(?<$1>[\\s\\S]+?)') + '$');
function tr(v, keys = DATA_KEYS, depth = 0) {                     // a data string that is our own text, in the page language
  if (lang === 'en' || typeof v !== 'string') return v;
  const ck = keys.length + '|' + v; if (TR.has(ck)) return TR.get(ck);
  let out = v;
  for (const k of keys) {
    const m = rx(k).exec(v); if (!m) continue;
    const g = { ...m.groups }; if (g.detail != null && depth < 2) g.detail = tr(g.detail, keys.filter(x => x !== k), depth + 1);
    out = t(k, g); break;
  }
  TR.set(ck, out); return out;
}
const loc = () => lang === 'pt' ? 'pt-BR' : 'en-US';
const nf = n => typeof n === 'number' ? n.toLocaleString(loc(), { maximumFractionDigits: 1 }) : n == null ? '—' : esc(tr(n));
const day = s => (s || '').slice(0, 10);
const ago = (iso, now) => { const h = (now - Date.parse(iso)) / 36e5; return !isFinite(h) ? '—' : h < 1 ? t('ui.ago.now') : h < 48 ? t('ui.ago.h', { n: Math.round(h) }) : t('ui.ago.d', { n: Math.round(h / 24) }); };
const href = p => p + '.html' + (lang === 'pt' ? '?lang=pt' : '');
const link = (u, text, l) => /^https?:\/\//.test(u || '') ? `<a href="${esc(u)}" target="_blank" rel="noopener"${l ? ` lang="${esc(l)}"` : ''}>${text}</a>` : text;
const posted = (s, l) => `<span lang="${esc(l || 'und')}">${esc(s)}</span>`;              // as posted, never translated
async function sha(s) { const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)); return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join(''); }
// ------------------------------------------------------------------ shell
function shell() {
  document.documentElement.lang = lang === 'pt' ? 'pt-BR' : 'en';
  document.documentElement.dataset.theme = theme;
  document.title = `dehype · ${t(page + '.title')}`;
  $('#top').innerHTML = `<a class="skip" href="#main">${esc(t('ui.skip'))}</a><div class="wrap"><a class="brand" href="${href('index')}"><i></i>DEHYPE</a>
<nav aria-label="${esc(t('ui.nav'))}">${NAV.map(([p, k]) => `<a href="${href(p)}"${p === page ? ' aria-current="page"' : ''}>${esc(t(k))}</a>`).join('')}</nav>
<div class="tools"><div class="seg" role="group" aria-label="${esc(t('ui.language'))}"><button data-lang="en" lang="en" aria-pressed="${lang === 'en'}">EN</button><button data-lang="pt" lang="pt" aria-pressed="${lang === 'pt'}">PT</button></div>
<button class="btn" id="theme">${esc(t(theme === 'dark' ? 'ui.theme.light' : 'ui.theme.dark'))}</button></div></div>`;
  $$('[data-lang]').forEach(b => b.onclick = () => setLang(b.dataset.lang));
  $('#theme').onclick = () => { theme = theme === 'dark' ? 'light' : 'dark'; store.set('dehype.theme', theme); shell(); redraw(); };
  $$('[data-k]').forEach(el => el.textContent = t(el.dataset.k));
  $('meta[name=description]')?.setAttribute('content', t(page + '.scope'));
  $('#reads').innerHTML = esc(t('ui.reads')) + ' ' + files.map(f => `<code class="mono">${esc(f)}</code>`).join(', ');
  $('#foot').innerHTML = `<div class="wrap"><p>${esc(t('ui.foot.data'))} ${files.map(f => `<a href="${esc(f)}"><code class="mono">${esc(f)}</code></a>`).join(' · ')}</p>
<p><a href="${METHOD[lang]}">${esc(t('ui.method'))}</a> · <a href="${POLICY[lang]}#corrections">${esc(t('ui.corrections'))}</a> · ${esc(t('ui.foot.counts'))}</p></div>`;
}
function setLang(l) {
  lang = l; store.set('dehype.lang', l); TR.clear();
  const u = new URL(location.href); if (l === 'pt') u.searchParams.set('lang', 'pt'); else u.searchParams.delete('lang'); history.replaceState(null, '', u);
  shell(); render();
}
// ------------------------------------------------------------------ figures, cards, tables, tooltip
const tip = document.createElement('div'); tip.className = 'tip'; tip.setAttribute('role', 'tooltip'); document.body.append(tip);
function showTip(x, y, title, rows) {
  tip.replaceChildren();
  if (title) { const h = document.createElement('div'); h.className = 'tt'; h.textContent = title; tip.append(h); }
  for (const [v, l, c] of rows) {
    const r = document.createElement('div'); r.className = 'tv';
    if (c) { const i = document.createElement('i'); i.style.background = `var(${c})`; r.append(i); }
    const b = document.createElement('b'); b.textContent = v; r.append(b, document.createTextNode(' ' + l)); tip.append(r);
  }
  tip.classList.add('on');
  tip.style.left = Math.max(8, Math.min(x + 14, innerWidth - tip.offsetWidth - 8)) + 'px';
  tip.style.top = Math.max(8, Math.min(y + 14, innerHeight - tip.offsetHeight - 8)) + 'px';
}
const hideTip = () => tip.classList.remove('on');
const kpis = list => `<div class="kpis">${list.map(([l, v, s]) => `<div class="kpi"><span class="lbl">${esc(l)}</span><span class="num">${v}</span>${s ? `<small>${s}</small>` : ''}</div>`).join('')}</div>`;
function sources(S) {                                            // coverage: a one-line summary, each source's status behind it (icon + label)
  const cls = { ok: 'ok', partial: 'partial', failed: 'bad', [NOT_FETCHED]: 'nf' }, ico = { ok: '●', partial: '◐', failed: '✕' }, E = Object.entries(S || {}), st = s => typeof s === 'string' ? s : s.status;
  const weak = E.filter(([, s]) => st(s) !== 'ok').map(([n, s]) => `${esc(n)} <span class="mono">${esc(tr(st(s)))}</span>`).join(' · ');
  return `<details class="cov"><summary><span class="lbl">${esc(t('ui.coverage'))}</span> <span class="st ok"><b aria-hidden="true">●</b> ${esc(t('ui.sources_ok', { n: E.filter(([, s]) => st(s) === 'ok').length, total: E.length }))}</span>${weak ? ` · ${weak}` : ''}</summary>
<ul>${E.map(([n, s]) => `<li class="st ${cls[st(s)] || 'nf'}"><b aria-hidden="true">${ico[st(s)] || '○'}</b> ${esc(n)} <span class="mono">${esc(tr(st(s)))}</span>${s.detail ? ` <span class="dim">· ${esc(tr(s.detail))}</span>` : ''}</li>`).join('')}</ul></details>`;
}
function table(o) {
  return `<table class="t">${o.caption ? `<caption>${esc(o.caption)}</caption>` : ''}<thead><tr>${o.cols.map(([l, c]) => `<th scope="col"${c ? ` class="${c}"` : ''}>${esc(l)}</th>`).join('')}</tr></thead>
<tbody>${o.rows.map(r => `<tr${r.attr || ''}>${r.cells.map((c, i) => `<td${o.cols[i][1] ? ` class="${o.cols[i][1]}"` : ''}>${c}</td>`).join('')}</tr>`).join('') || `<tr><td colspan="${o.cols.length}" class="dim">${esc(t('ui.none'))}</td></tr>`}</tbody></table>`;
}
const cards = [];
function card(el, o) {                                           // a chart with its legend and its table-view twin
  const view = el.dataset.view || 'chart';
  el.className = 'card';
  el.innerHTML = `<div class="card-h"><div><h2>${esc(o.title)}</h2>${o.sub ? `<p>${esc(o.sub)}</p>` : ''}</div><div class="seg" role="group" aria-label="${esc(t('ui.view'))}">${['chart', 'table'].map(v => `<button data-v="${v}" aria-pressed="${v === view}">${esc(t({ chart: 'ui.chart', table: 'ui.table' }[v]))}</button>`).join('')}</div></div>
${o.legend ? `<div class="legend">${o.legend.map(([l, c]) => `<span><i style="background:var(${c})"></i>${esc(l)}</span>`).join('')}</div>` : ''}<div class="plot"></div><div class="tw"></div>`;
  const plot = $('.plot', el), tw = $('.tw', el), set = v => { el.dataset.view = v; plot.hidden = v === 'table'; tw.hidden = v !== 'table'; $$('.seg button', el).forEach(b => b.setAttribute('aria-pressed', b.dataset.v === v)); };
  tw.innerHTML = table(o.table); set(view);
  $$('.seg button', el).forEach(b => b.onclick = () => set(b.dataset.v));
  const draw = () => { hideTip(); o.draw(plot, Math.max(280, plot.clientWidth || el.clientWidth - 40)); };
  el._draw = draw; if (!cards.includes(el)) cards.push(el); draw();
}
function redraw() { cards.forEach(c => c.isConnected && c._draw && c._draw()); }
let rz; addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(redraw, 150); });
function ticks(hi, n = 4) { const st0 = (hi || 1) / n, mag = 10 ** Math.floor(Math.log10(st0)), st = [1, 2, 2.5, 5, 10].map(x => x * mag).find(x => x >= st0); const o = []; for (let v = 0; v <= hi + 1e-9; v += st) o.push(+v.toFixed(6)); if (o.at(-1) < hi) o.push(+(o.at(-1) + st).toFixed(6)); return o; }
const bar = (x, y, w, h) => { const r = Math.min(4, w, h / 2); return w <= 0 ? '' : `M${x},${y}h${w - r}a${r},${r} 0 0 1 ${r},${r}v${h - 2 * r}a${r},${r} 0 0 1 ${-r},${r}h${-(w - r)}z`; };
function hover(el, show, pick) {                                 // per-mark tooltip on hover and keyboard focus; Enter picks
  for (const g of $$('.mk', el)) {
    const i = +g.dataset.i, at = e => { const b = g.getBoundingClientRect(); return e && e.clientX != null ? [e.clientX, e.clientY] : [b.right, b.top]; };
    g.addEventListener('pointermove', e => show(i, ...at(e))); g.addEventListener('pointerleave', hideTip);
    g.addEventListener('focus', () => show(i, ...at())); g.addEventListener('blur', hideTip);
    if (pick) { g.addEventListener('click', () => pick(i)); g.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(i); } }); }
  }
}
// Story map: each story a dot at its first post (x) and its voices (y, square-root scale); two series, news and chatter.
function scatter(plot, W, pts, o) {
  const H = W < 520 ? 230 : 290, m = { l: 36, r: 14, t: 12, b: 30 }, iw = W - m.l - m.r, ih = H - m.t - m.b;
  const yt = ticks(Math.max(1, ...pts.map(p => p.y)), 4), ym = yt.at(-1), X = v => m.l + (v - o.x0) / (o.x1 - o.x0) * iw, Y = v => m.t + ih - Math.sqrt(v / ym) * ih;
  const days = []; for (let d = Math.ceil(o.x0 / DAY) * DAY; d <= o.x1; d += DAY) days.push(d);
  const every = Math.ceil(days.length / Math.max(2, Math.floor(iw / 64)));
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(o.label)}">`;
  s += yt.map(v => `<line class="grid" x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}"/><text class="axis" x="${m.l - 6}" y="${Y(v) + 4}" text-anchor="end">${nf(v)}</text>`).join('');
  s += days.map((d, i) => i % every ? '' : `<text class="axis" x="${X(d)}" y="${H - 8}" text-anchor="middle">${new Date(d).toISOString().slice(5, 10)}</text>`).join('');
  s += `<line class="base" x1="${m.l}" x2="${W - m.r}" y1="${m.t + ih}" y2="${m.t + ih}"/>`;
  const order = pts.map((p, i) => i).sort((a, b) => pts[b].s - pts[a].s);
  s += order.map(i => { const p = pts[i]; return `<circle data-i="${i}" cx="${X(p.x).toFixed(1)}" cy="${Y(p.y).toFixed(1)}" r="4.5" style="fill:var(${p.s ? '--s2' : '--s1'});stroke:var(--panel);stroke-width:2"/>`; }).join('');
  s += `<circle class="ring" r="8" cx="0" cy="0" style="fill:none;stroke:var(--ink);stroke-width:1.5;opacity:0"/><rect class="hit" x="${m.l}" y="0" width="${iw}" height="${m.t + ih}" style="fill:transparent"/></svg>`;
  plot.innerHTML = s;
  const svg = $('svg', plot), ring = $('.ring', svg), hit = $('.hit', svg);
  const near = e => { const b = svg.getBoundingClientRect(), k = W / b.width, x = (e.clientX - b.left) * k, y = (e.clientY - b.top) * k; let best = -1, bd = 24 * k; pts.forEach((p, i) => { const d = Math.hypot(X(p.x) - x, Y(p.y) - y); if (d < bd) { bd = d; best = i; } }); return best; };
  hit.addEventListener('pointermove', e => { const i = near(e); if (i < 0) { hideTip(); ring.style.opacity = 0; hit.style.cursor = ''; return; } ring.setAttribute('cx', X(pts[i].x)); ring.setAttribute('cy', Y(pts[i].y)); ring.style.opacity = 1; hit.style.cursor = 'pointer'; showTip(e.clientX, e.clientY, pts[i].title, pts[i].rows); });
  hit.addEventListener('pointerleave', () => { hideTip(); ring.style.opacity = 0; });
  hit.addEventListener('click', e => { const i = near(e); if (i >= 0) o.pick(pts[i]); });
}
// Grouped horizontal bars on one count axis (output by area): one group per row, one bar per series.
function hbars(plot, W, rows, series, o) {
  const narrow = W < 560, lw = narrow ? 0 : 168, bh = 12, gap = 2, top = narrow ? 18 : 0, gh = top + series.length * (bh + gap) + 16;
  const m = { l: lw, r: 44, t: 6 }, iw = W - m.l - m.r, xt = ticks(Math.max(1, ...rows.flatMap(r => r.vals)), narrow ? 3 : 5), xm = xt.at(-1), X = v => m.l + v / xm * iw;
  const H = m.t + rows.length * gh + 24;
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(o.label)}">`;
  s += xt.map(v => `<line class="grid" x1="${X(v)}" x2="${X(v)}" y1="${m.t}" y2="${H - 22}"/><text class="axis" x="${X(v)}" y="${H - 6}" text-anchor="middle">${nf(v)}</text>`).join('');
  s += rows.map((r, i) => {
    const y = m.t + i * gh, sel = o.sel === r.key;
    return `<g class="mk${sel ? ' sel' : ''}" data-i="${i}" tabindex="0" role="button" aria-pressed="${sel}" aria-label="${esc(r.label + ': ' + series.map(([l], j) => `${l} ${r.vals[j]}`).join(', '))}">
<rect class="hit" x="0" y="${y}" width="${W}" height="${gh - 4}" rx="4"/>
<text class="rlabel" x="${narrow ? m.l : lw - 12}" y="${narrow ? y + 13 : y + 12 + (series.length - 1) * (bh + gap) / 2}" text-anchor="${narrow ? 'start' : 'end'}" style="${sel ? 'fill:var(--ink);font-weight:600' : ''}">${esc(r.label)}</text>
${r.vals.map((v, j) => { const by = y + top + j * (bh + gap) + 2; return `<path d="${bar(X(0), by, X(v) - X(0), bh)}" style="fill:var(${series[j][1]})"/><text class="vlabel mono" x="${X(v) + 6}" y="${by + 10}">${nf(v)}</text>`; }).join('')}</g>`;
  }).join('');
  s += `<line class="base" x1="${X(0)}" x2="${X(0)}" y1="${m.t}" y2="${H - 22}"/></svg>`;
  plot.innerHTML = s;
  hover(plot, (i, x, y) => showTip(x, y, rows[i].label, series.map(([l, c], j) => [nf(rows[i].vals[j]), l, c])), i => o.pick(rows[i].key));
}
// Dumbbell on the 0-100 score axis: hype (attention) and substance (discovery) components per project; no dot where unmeasured.
function dumbbell(plot, W, rows, o) {
  const narrow = W < 560, lw = narrow ? 0 : 190, rh = narrow ? 44 : 28, m = { l: lw, r: 18, t: 22 };
  const iw = W - m.l - m.r, X = v => m.l + v / 100 * iw, H = m.t + rows.length * rh + 8;
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(o.label)}">`;
  s += [0, 25, 50, 75, 100].map(v => `<line class="${v === 50 ? 'base' : 'grid'}" x1="${X(v)}" x2="${X(v)}" y1="${m.t - 4}" y2="${H - 4}"/><text class="axis" x="${X(v)}" y="12" text-anchor="${v === 0 ? 'start' : v === 100 ? 'end' : 'middle'}">${v}</text>`).join('');
  s += rows.map((r, i) => {
    const y = m.t + i * rh + (narrow ? 29 : rh / 2), has = r.d != null;
    return `<g class="mk" data-i="${i}" tabindex="0" role="button" aria-label="${esc(`${r.label}: ${o.a} ${nf(r.a)}, ${o.d} ${has ? nf(r.d) : '—'}`)}">
<rect class="hit" x="0" y="${m.t + i * rh}" width="${W}" height="${rh - 2}" rx="4"/>
<text class="rlabel" x="${narrow ? m.l : lw - 12}" y="${narrow ? m.t + i * rh + 15 : y + 4}" text-anchor="${narrow ? 'start' : 'end'}">${esc(r.label)}</text>
${has ? `<line x1="${X(r.a)}" x2="${X(r.d)}" y1="${y}" y2="${y}" style="stroke:var(--rule-2);stroke-width:2"/>` : ''}
<circle cx="${X(r.a)}" cy="${y}" r="5" style="fill:var(--s2);stroke:var(--panel);stroke-width:2"/>${has ? `<circle cx="${X(r.d)}" cy="${y}" r="5" style="fill:var(--s1);stroke:var(--panel);stroke-width:2"/>` : ''}</g>`;
  }).join('') + '</svg>';
  plot.innerHTML = s;
  hover(plot, (i, x, y) => showTip(x, y, rows[i].label, [[nf(rows[i].a), o.a, '--s2'], [rows[i].d == null ? '—' : nf(rows[i].d), rows[i].d == null ? o.none : o.d, '--s1']]), i => o.pick(rows[i].id));
}
const seg = (id, label, opts, cur) => `<div class="seg" role="group" aria-label="${esc(label)}" id="${id}">${opts.map(([v, l]) => `<button data-v="${esc(v)}" aria-pressed="${String(v) === String(cur)}">${esc(l)}</button>`).join('')}</div>`;
const onSeg = (id, fn) => $$(`#${id} button`).forEach(b => b.onclick = () => fn(b.dataset.v));
// ------------------------------------------------------------------ the evidence display (all stories here; the briefing in C3)
const kind = r => t(r.kind === 'news' ? 'kind.news' : 'kind.chatter'), SORT = { heat: 'stories.sort.heat', voices: 'stories.sort.voices', last: 'stories.sort.last', first: 'stories.sort.first' };
const LABELS = { REAL: 'label.real', OVERHYPED: 'label.overhyped', FALSE: 'label.false', PUSHED: 'label.pushed', UNVERIFIED: 'label.unverified' };
function verdictSlot(v) {
  if (!v) return `<div class="slot"><span class="lbl">${esc(t('ui.verdict'))}</span><span class="pill">${esc(t('ui.verdict.none'))}</span><span>${esc(t('state.proposed'))}</span></div>`;
  return `<div class="slot"><span class="lbl">${esc(t('ui.verdict'))}</span><span class="pill v">${esc(t(LABELS[v.label] || 'label.unverified'))}</span>${v.reason?.[lang] ? `<span>${esc(v.reason[lang])}</span>` : ''}${v.source ? link(v.source, esc(t('ui.source'))) : ''}${v.confirmed ? `<span class="dim mono">${esc(t('ui.confirmed', { date: v.confirmed }))}</span>` : ''}</div>`;
}
const nets = c => { const e = Object.entries(c.networks || {}); return e.filter(([, v]) => v !== 0).sort((a, b) => (typeof b[1] === 'number' ? b[1] : -1) - (typeof a[1] === 'number' ? a[1] : -1)).map(([k, v]) => `<span class="nw">${esc(k)} ${nf(v)}</span>`).join(' · ') || '—'; };
const rd = v => `<span class="num mono${typeof v === 'number' ? '' : ' s'}">${typeof v === 'boolean' || v === NOT_FETCHED || v == null ? esc(yesno(v)) : nf(v)}</span>`;
const yesno = v => v === true ? t('ui.yes') : v === false ? t('ui.no') : tr(v ?? NOT_FETCHED);
function evidence(r, s, v, i, now) {
  const c = r.computed || {}, sub = r.substance || {}, u = s && (s.link || s.url), fixed = rx('headline.count_only').test(r.headline || '');
  const hd = fixed ? esc(tr(r.headline, ['headline.count_only'])) : posted(r.headline, r.lang);
  const st = Object.entries(r.sources || {}), ok = st.filter(([, x]) => x === 'ok').length, weak = st.filter(([, x]) => x !== 'ok').map(([n, x]) => `${esc(n)} ${esc(tr(x))}`).join(' · ');
  const posts = (s?.posts || []).filter(p => p.title), counted = Object.entries(s?.nets || {}).filter(([n]) => COUNT_ONLY.has(n));
  const path = (s?.path || []).map(p => `${esc(['Newsletter', 'Official'].includes(p.net) && p.who ? p.who : p.net)} <span class="mono dim">${esc(day(p.at).slice(5))}</span>`).join(' → ');
  const rel = r.related_in_topic || {}, refs = [...(sub.repos || []), ...(sub.papers || [])];
  return `<li class="story" id="${esc(r.id)}"><span class="rk">${String(i + 1).padStart(2, '0')}</span><div>
<span class="seen${r.seen === 'new today' ? ' new' : ''}">${esc(tr(r.seen))}</span>${r.release ? ` <span class="meta">· ${esc(r.release)}</span>` : ''} <span class="meta">· ${esc(kind(r))}</span>
<h3>${u ? link(u, hd) : hd}</h3>
<div class="read"><div><span class="lbl">${esc(t('ui.voices'))}</span><span class="num mono">${nf(c.voices)}</span></div>
<div><span class="lbl">${esc(t('ui.networks'))}</span><span class="nets">${nets(c)}</span></div>
<div><span class="lbl">${esc(t('ui.newsletters'))}</span>${rd(c.newsletters)}</div>
<div><span class="lbl">${esc(t('ui.lab_post'))}</span>${rd(c.official)}</div>
<div><span class="lbl">${esc(t('ui.hn_points'))}</span>${rd(c.hn_points)}</div></div>
${verdictSlot(v)}
<div class="meta">${esc(t('ui.sources_ok', { n: ok, total: st.length }))}${weak ? ` · ${weak}` : ''} · ${esc(t('ui.newest', { ago: ago(r.last, now) }))}</div>
<details class="more"><summary>${esc(t('ui.evidence'))}</summary><div class="ev">
<h4>${esc(t('ui.path'))}</h4><p>${path || '—'}</p>
<h4>${esc(t('ui.posts'))}</h4><ul>${posts.map(p => `<li><span class="mono dim">${esc(p.net)}</span> ${link(p.url, posted(p.title, p.lang))}${['Newsletter', 'Official'].includes(p.net) && p.author ? ` <span class="dim">· ${esc(p.author)}</span>` : ''} <span class="mono dim">${esc(day(p.at))}</span></li>`).join('')}
${counted.map(([n, k]) => `<li class="dim">${esc(t('ui.counted', { net: n, n: k }))}</li>`).join('')}${!posts.length && !counted.length ? `<li class="dim">${esc(t('ui.none'))}</li>` : ''}</ul>
<h4>${esc(tr(sub.from || "the story's own links"))}</h4><ul>${refs.map(x => `<li>${link(x, `<span class="mono">${esc(x.replace(/^https:\/\/(github\.com|arxiv\.org\/abs)\//, ''))}</span>`)}</li>`).join('') || `<li class="dim">${esc(t('ui.none'))}</li>`}</ul>
<h4>${esc(tr(rel.reading || 'related in topic'))}</h4><ul>${(rel.items || []).map(x => `<li><span class="mono dim">${esc(x.net)}</span> ${link(x.url, posted(x.title, x.lang))}</li>`).join('') || `<li class="dim">${esc(t('ui.none'))}</li>`}</ul>
${c.newsletter_names?.length ? `<h4>${esc(t('ui.newsletters'))}</h4><p>${c.newsletter_names.map(esc).join(' · ')}</p>` : ''}
<p class="dim mono">${esc(r.id)} · ${esc(t('ui.first_last', { first: day(r.first), last: day(r.last) }))}</p></div></details></div></li>`;
}
// ------------------------------------------------------------------ all stories
async function stories() {
  const [B, P, V] = await Promise.all([load('briefing.json'), load('pulse.json'), opt('verdicts.json', { rows: [] })]);
  const by = new Map((P.stories || []).map(s => [s.id, s])), ver = new Map((V.rows || []).map(r => [r.id, r])), now = Date.parse(B.generated_at), R = B.records || [];
  const F = { q: '', kind: 'all', seen: 'all', sort: 'heat', view: 'list' };
  const x0 = Math.min(...R.map(r => Date.parse(r.first))), x1 = now;
  render = () => {
    const main = $('#body');
    main.innerHTML = `<p class="reads mono">${esc(t('ui.window', { end: B.window?.end_brt || '', h: B.window?.hours ?? 24 }))}</p>
${kpis([[t('stories.k.stories'), nf(R.length), esc(t('stories.k.stories_sub'))], [t('stories.k.new'), nf(R.filter(r => r.seen === 'new today').length), esc(t('stories.k.new_sub'))],
  [t('stories.k.news'), nf(R.filter(r => r.kind === 'news').length), esc(t('stories.k.news_sub'))], [t('stories.k.official'), nf(R.filter(r => r.computed?.official === true).length), esc(t('stories.k.official_sub'))]])}
${sources(B.sources)}<div id="map"></div>
<div class="bar-row"><input type="search" id="q" placeholder="${esc(t('ui.search'))}" aria-label="${esc(t('ui.search'))}" value="${esc(F.q)}">
${seg('kind', t('ui.kind'), [['all', t('ui.all')], ['news', t('kind.news')], ['chatter', t('kind.chatter')]], F.kind)}
${seg('seen', t('ui.seen'), [['all', t('ui.all')], ['new', t('seen.new_today')]], F.seen)}
<select id="sort" aria-label="${esc(t('ui.sort'))}">${['heat', 'voices', 'last', 'first'].map(k => `<option value="${k}"${F.sort === k ? ' selected' : ''}>${esc(t(SORT[k]))}</option>`).join('')}</select>
${seg('view', t('ui.view'), [['list', t('ui.evidence_view')], ['table', t('ui.table')]], F.view)}<span class="count" id="count" aria-live="polite"></span></div><div id="list"></div>`;
    const pts = R.map(r => ({ id: r.id, x: Date.parse(r.first), y: r.computed?.voices || 0, s: r.kind === 'news' ? 0 : 1, title: r.headline, rows: [[nf(r.computed?.voices), t('ui.voices'), r.kind === 'news' ? '--s1' : '--s2'], [day(r.first), t('ui.first_seen')], [nets(r.computed || {}).replace(/<[^>]+>/g, ''), '']] }));
    card($('#map'), { title: t('stories.map.title'), sub: t('stories.map.sub'), legend: [[t('kind.news'), '--s1'], [t('kind.chatter'), '--s2']],
      draw: (p, W) => scatter(p, W, pts, { x0, x1, label: t('stories.map.title'), pick: pt => { const el = document.getElementById(pt.id); if (F.view !== 'list' || !el) { F.q = ''; F.kind = 'all'; F.seen = 'all'; F.view = 'list'; render(); } const go = document.getElementById(pt.id); if (go) { go.scrollIntoView({ block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }); $('details', go).open = true; $('a, summary', go).focus({ preventScroll: true }); } } }),
      table: { caption: t('stories.map.sub'), cols: [[t('ui.headline')], [t('ui.kind')], [t('ui.first_seen'), 'n'], [t('ui.voices'), 'n']], rows: R.map(r => ({ cells: [posted(r.headline, r.lang), esc(kind(r)), esc(day(r.first)), nf(r.computed?.voices)] })) } });
    const list = () => {
      const q = F.q.trim().toLowerCase(), key = { heat: r => r.computed?.heat || 0, voices: r => r.computed?.voices || 0, last: r => Date.parse(r.last), first: r => Date.parse(r.first) }[F.sort];
      const rows = R.filter(r => (F.kind === 'all' || (F.kind === 'news') === (r.kind === 'news')) && (F.seen === 'all' || r.seen === 'new today')
        && (!q || [r.headline, r.release, ...(r.computed?.tags || [])].join(' ').toLowerCase().includes(q))).sort((a, b) => key(b) - key(a));
      $('#count').textContent = t('ui.showing', { n: rows.length, total: R.length });
      $('#list').innerHTML = F.view === 'list' ? `<ol class="stories">${rows.map((r, i) => evidence(r, by.get(r.id), ver.get(r.id), i, now)).join('')}</ol>`
        : `<div class="tw">${table({ cols: [['#', 'n hm'], [t('ui.headline')], [t('ui.seen'), 'hm'], [t('ui.voices'), 'n'], [t('ui.networks'), 'hm'], [t('ui.newsletters'), 'n hm'], [t('ui.lab_post'), 'hm'], [t('ui.hn_points'), 'n hm'], [t('ui.verdict'), 'hm']],
          rows: rows.map((r, i) => ({ cells: [i + 1, link(by.get(r.id)?.link || by.get(r.id)?.url, posted(r.headline, r.lang)), esc(tr(r.seen)), nf(r.computed?.voices), `<span class="mono">${nets(r.computed || {})}</span>`, nf(r.computed?.newsletters), esc(yesno(r.computed?.official)), nf(r.computed?.hn_points), esc(ver.get(r.id) ? t(LABELS[ver.get(r.id).label]) : t('ui.verdict.none'))] })) })}</div>`;
    };
    $('#q').oninput = e => { F.q = e.target.value; list(); };
    $('#sort').onchange = e => { F.sort = e.target.value; list(); };
    for (const k of ['kind', 'seen', 'view']) onSeg(k, v => { F[k] = v; $$(`#${k} button`).forEach(b => b.setAttribute('aria-pressed', b.dataset.v === v)); list(); });
    list();
  };
  render();
}
// ------------------------------------------------------------------ output by area (Papers and Repos)
async function output() {
  const [B, D] = await Promise.all([load('briefing.json'), load('data.json')]);
  const now = Date.parse(B.generated_at), g = (B.gauges || []).find(x => x.id === 'output_by_area'), areas = (D.views || []).filter(a => a !== 'all');
  const F = { days: 7, area: 'all', tab: 'papers', q: '', all: false };
  const date = { papers: it => it.published, repos: it => it.created };
  render = () => {
    const cut = new Date(now - (F.days - 1) * DAY).toISOString().slice(0, 10), wk = F.days + 'd';
    const inWin = tab => Object.entries(D[tab]?.items || {}).filter(([, it]) => (date[tab](it) || '') >= cut);
    const P = inWin('papers'), Rp = inWin('repos'), count = (L, a) => L.filter(([, it]) => it.tag === a).length;
    const rows = areas.map(a => ({ key: a, label: a, vals: [count(P, a), count(Rp, a)] }));
    const same = F.days === 7 && g?.value && g.value.since === cut && g.value.areas.every(x => { const r = rows.find(y => y.key === x.area); return r && r.vals[0] === x.papers && r.vals[1] === x.repos; });
    const gnote = !g ? '' : g.value == null ? tr(g.reason) : F.days === 7 ? (same ? t('output.gauge.same', { name: tr(g.name) }) : t('output.gauge.differs', { name: tr(g.name) })) : t('output.gauge.other', { name: tr(g.name) });
    $('#body').innerHTML = `<div class="bar-row">${seg('days', t('ui.window_label'), [[7, '7d'], [30, '30d'], [90, '90d']], F.days)}
<select id="area" aria-label="${esc(t('output.area'))}"><option value="all">${esc(t('output.all_areas'))}</option>${areas.map(a => `<option${F.area === a ? ' selected' : ''}>${esc(a)}</option>`).join('')}</select>
<span class="count mono">${esc(t('output.since', { date: cut }))}</span></div>
${kpis([[t('output.k.papers'), nf(P.length), esc(t('output.k.of', { n: nf(Object.keys(D.papers?.items || {}).length) }))], [t('output.k.repos'), nf(Rp.length), esc(t('output.k.of', { n: nf(Object.keys(D.repos?.items || {}).length) }))],
  [t('output.k.areas'), nf(areas.length), esc(t('output.k.areas_sub'))], [t('output.k.tracked'), nf((D.tracked?.papers || 0) + (D.tracked?.repos || 0)), esc(t('output.k.tracked_sub', { p: nf(D.tracked?.papers), r: nf(D.tracked?.repos) }))]])}
${sources(D.sources)}<p class="reads">${esc(gnote)}${g ? ` <span class="pill">${esc(tr(g.status))}</span>` : ''}</p><div id="bars"></div><div id="drill"></div>`;
    card($('#bars'), { title: t('output.chart.title', { n: F.days }), sub: t('output.chart.sub'), legend: [[t('output.papers'), '--s1'], [t('output.repos'), '--s2']],
      draw: (p, W) => hbars(p, W, rows, [[t('output.papers'), '--s1'], [t('output.repos'), '--s2']], { sel: F.area, label: t('output.chart.title', { n: F.days }), pick: a => { F.area = F.area === a ? 'all' : a; F.all = false; render(); ($('#bars .mk.sel') || $('#bars .mk'))?.focus(); } }),
      table: { cols: [[t('output.area')], [t('output.papers'), 'n'], [t('output.repos'), 'n']], rows: rows.map(r => ({ cells: [esc(r.label), nf(r.vals[0]), nf(r.vals[1])] })) } });
    $('#area').onchange = e => { F.area = e.target.value; F.all = false; render(); };
    onSeg('days', v => { F.days = +v; F.all = false; render(); });
    drill(F, D, wk, F.tab === 'papers' ? P : Rp);
  };
  function drill(F, D, wk, L) {
    const score = new Map((D[F.tab]?.[wk]?.all?.rows || []).map(r => [r.id, r]));
    const q = F.q.trim().toLowerCase();
    const items = L.filter(([id, it]) => (F.area === 'all' || it.tag === F.area) && (!q || [id, it.title, it.desc, it.lab, it.owner].join(' ').toLowerCase().includes(q)))
      .sort((a, b) => (score.get(b[0])?.score ?? -1) - (score.get(a[0])?.score ?? -1) || ((b[1].upvotes || b[1].stars || 0) - (a[1].upvotes || a[1].stars || 0)));
    const shown = F.all ? items : items.slice(0, 25);
    const cols = F.tab === 'papers' ? [[t('output.col.paper')], [t('output.col.lab'), 'hm'], [t('output.area'), 'hm'], [t('output.col.published'), 'n hm'], [t('output.col.upvotes'), 'n'], [t('output.col.score'), 'n']]
      : [[t('output.col.repo')], [t('output.col.desc'), 'hm'], [t('output.area'), 'hm'], [t('output.col.created'), 'n hm'], [t('output.col.stars'), 'n'], [t('output.col.gained'), 'n hm'], [t('output.col.score'), 'n']];
    const cells = ([id, it]) => F.tab === 'papers' ? [link('https://arxiv.org/abs/' + id, posted(it.title)), esc(it.lab || '—'), esc(it.tag || '—'), esc(it.published || '—'), nf(it.upvotes), nf(score.get(id)?.score)]
      : [link(it.url, `<span class="mono">${esc(id)}</span>`), it.desc ? posted(it.desc) : '—', esc(it.tag || '—'), esc(day(it.created) || '—'), nf(it.stars), nf(score.get(id)?.gained), nf(score.get(id)?.score)];
    $('#drill').innerHTML = `<div class="bar-row">${seg('tab', t('output.kind'), [['papers', t('output.papers')], ['repos', t('output.repos')]], F.tab)}
<input type="search" id="q" placeholder="${esc(t('ui.search'))}" aria-label="${esc(t('ui.search'))}" value="${esc(F.q)}"><span class="count" aria-live="polite">${esc(t('ui.showing', { n: shown.length, total: items.length }))}</span></div>
<div class="tw">${table({ caption: t('output.table.caption', { area: F.area === 'all' ? t('output.all_areas') : F.area, wk }), cols, rows: shown.map(x => ({ cells: cells(x) })) })}</div>
${items.length > shown.length ? `<p><button class="btn" id="all">${esc(t('ui.show_all', { n: items.length }))}</button></p>` : ''}`;
    onSeg('tab', v => { F.tab = v; F.all = false; render(); });
    const qi = $('#q'); qi.oninput = e => { F.q = e.target.value; drill(F, D, wk, L); const n = $('#q'); n.focus(); n.setSelectionRange(n.value.length, n.value.length); };
    $('#all')?.addEventListener('click', () => { F.all = true; drill(F, D, wk, L); });
  }
  render();
}
// ------------------------------------------------------------------ Hype projects (research dossier, content cut)
const GAP = { insufficient: 'hype.gap.insufficient', similar: 'hype.gap.similar', evidence_ahead: 'hype.gap.evidence_ahead', attention_ahead: 'hype.gap.attention_ahead' };
const CITE = ['cite.x_post', 'cite.net_post', 'cite.account_post'], FIG = ['figure.x_post', 'figure.net_post'];
function at(o, path) { return path.split(/\.|\[(\d+)\]/).filter(x => x != null && x !== '').reduce((v, k) => v == null ? v : v[k], o); }
async function hype() {
  const [H, R, G, PT, XF] = await Promise.all([load('hype.json'), opt('removals.json', { entries: [] }), opt('checks/dossier-gone.json', { gone: [] }), opt('i18n/dossier.pt.json', { entries: [] }), opt('i18n/dossier-x-figures.json', {})]);
  const drop = new Set([...(R.entries || []), ...(G.gone || [])].map(e => e.sha256)), gone = new Set(), pt = new Map(), subtle = !!globalThis.crypto?.subtle;
  if (subtle && drop.size) for (const it of Object.values(H.items)) for (const p of it.posts || []) if (p.url && drop.has(await sha(p.url))) gone.add(p.url);
  if (subtle) for (const e of PT.entries || []) {                                   // a reviewed entry whose hash matches the current English
    const en = e.slug == null ? at(H, e.field) : at(H.items[e.slug] || {}, e.field);
    if (typeof en === 'string' && e.reviewed_in && e.pt && await sha(en) === e.sha256) pt.set(`${e.slug}|${e.field}`, e.pt);
  }
  const ph = XF.placeholder?.en;
  const wins = ['1d', '7d', '30d', '90d', 'overall'].filter(w => H.windows?.[w]?.enabled && H[w]);
  const F = { win: wins.includes('7d') ? '7d' : wins[0], area: 'all', q: '', all: false, open: decodeURIComponent((location.hash.match(/^#p=(.+)$/) || [])[1] || '') };
  function block() {                                             // dossier prose, with the Portuguese notice when any field falls back
    const b = { fb: false };
    b.p = (slug, field) => {
      const en = slug == null ? at(H, field) : at(H.items[slug] || {}, field);
      if (en == null || en === '') return '—';
      if (lang === 'en') return esc(en);
      if (ph && en === ph) return esc(t('dossier.x_figure_placeholder'));
      const x = pt.get(`${slug}|${field}`); if (x) return `<span lang="pt-BR">${esc(x)}</span>`;
      b.fb = true; return `<span lang="en">${esc(en)}</span>`;
    };
    b.raw = s => { if (s == null || s === '') return '—'; if (lang === 'en') return esc(s); b.fb = true; return `<span lang="en">${esc(s)}</span>`; };
    b.wrap = h => (b.fb && lang === 'pt' ? `<p class="notice" lang="pt-BR">${esc(t('dossier.pt_notice'))}</p>` : '') + h;
    return b;
  }
  const src = u => /^https?:\/\//.test(u || '') ? link(u, esc(t('ui.source'))) : u ? `<span class="dim">${esc(tr(u, CITE))}</span>` : '';
  const cutLine = () => t('hype.cut', { date: day(H.content_cutoff) });
  function detail(slug) {
    const it = H.items[slug], el = $('#panel'), sc = $('#scrim');
    if (!it) { el.classList.remove('on'); sc.classList.remove('on'); return; }
    const r = (H[F.win]?.all?.rows || []).find(x => x.id === slug) || {}, d = it.discovery || {}, m = it.win?.[F.win] || {}, b = block();
    const L = it.links || {}, links = [['site', 'hype.link.site'], ['repo', 'hype.link.repo'], ['paper', 'hype.link.paper'], ['hf', 'hype.link.hf'], ['x_handle', 'hype.link.x']].filter(([k]) => L[k]).map(([k, s]) => link(L[k], esc(t(s)))).join(' · ');
    const posts = (it.posts || []).filter(p => !gone.has(p.url)), cnt = {};
    for (const p of posts) if (COUNT_ONLY.has(p.pl) || !p.url) cnt[p.pl] = (cnt[p.pl] || 0) + 1;
    const shown = posts.filter(p => p.url && !COUNT_ONLY.has(p.pl));
    const body = b.wrap(`<section><h3>${esc(t('hype.summary'))}</h3><p>${b.p(slug, 'summary')}</p><p class="dim">${esc(t('hype.category'))}: ${b.p(slug, 'category')}</p></section>
<section><h3>${esc(t('hype.timeline'))}</h3><ul><li>${esc(t('hype.first_seen'))}: <span class="mono">${esc(it.first_seen || '—')}</span> ${src(it.first_seen_url)} <span class="dim">(${b.p(slug, 'first_seen_meaning')})</span></li>
<li>${esc(t('hype.peak'))}: ${it.peak ? `<span class="mono">${esc(day(it.peak))}</span>` : `<span class="dim">${b.p(slug, 'peak_reason')}</span>`}</li><li>${esc(t('hype.now'))}: ${b.p(slug, 'status')}</li>
<li>${esc(t('hype.viral'))}: ${b.p(slug, 'viral.reason')}${it.viral?.cand_platform ? ` <span class="dim">· ${esc(t('hype.earliest', { net: it.viral.cand_platform }))}</span>` : ''}</li></ul></section>
<section><h3>${esc(t('hype.coord'))}</h3><p>${b.p(slug, 'coord.assessment')}</p><p class="dim">${b.p(slug, 'coord.limitations')}</p>${(it.coord?.evidence || []).length ? `<ul>${it.coord.evidence.map((e, i) => `<li>${b.p(slug, `coord.evidence[${i}].t`)} ${src(e.url)}</li>`).join('')}</ul>` : ''}</section>
<section><h3>${esc(t('hype.traction'))}</h3><ul>${(it.traction || []).map((s, i) => `<li><span class="mono">${typeof s.value === 'number' ? nf(s.value) : rx('figure.x_post').test(s.value) || rx('figure.net_post').test(s.value) ? esc(tr(s.value, FIG)) : b.raw(typeof s.value === 'object' ? JSON.stringify(s.value) : s.value)}</span> ${b.raw(s.unit)} · ${b.raw(s.type)} <span class="dim">${s.asof ? esc(s.asof) : ''}</span> ${src(s.url)}${s.notes ? `<div class="dim">${b.p(slug, `traction[${i}].notes`)}</div>` : ''}</li>`).join('') || `<li class="dim">${esc(t('ui.none'))}</li>`}</ul></section>
<section><h3>${esc(t('hype.skeptic'))}</h3><p class="dim">${esc(t('hype.skeptic.note'))}</p><ul>${(it.skeptic || []).map((s, i) => `<li>${b.p(slug, `skeptic[${i}].claim`)} <span class="dim">— ${b.p(slug, `skeptic[${i}].by`)}${s.d ? ', ' + esc(s.d) : ''}</span> ${src(s.url)}</li>`).join('') || `<li class="dim">${esc(t('ui.none'))}</li>`}</ul></section>
${Object.keys(it.notes || {}).length || it.qual_gap ? `<section><h3>${esc(t('hype.notes'))}</h3><ul>${Object.keys(it.notes || {}).sort().map(k => `<li><span class="mono dim">${esc(k)}</span> ${b.p(slug, `notes.${k}`)}</li>`).join('')}${it.qual_gap ? `<li>${b.p(slug, 'qual_gap.text')}</li>` : ''}</ul></section>` : ''}`);
    el.innerHTML = `<button class="btn x" id="close">${esc(t('ui.close'))}</button><p class="eyebrow">${esc(cutLine())}</p><h2>${posted(it.name)}</h2><p>${links}</p>
<section><h3>${esc(t('ui.verdict'))}</h3><div class="slot"><span class="pill">${esc(t('ui.verdict.none'))}</span><span>${esc(t('hype.verdict.note'))}</span></div></section>
<section><h3>${esc(t('hype.gap.title'))} · ${esc(F.win)}</h3><p class="dim">${esc(t('hype.gap.note'))}</p><div class="comp">
<div><span class="lbl">${esc(t('hype.attention'))}</span><span class="num mono">${nf(r.score)}</span><small class="dim">${esc(t('hype.cov', { n: r.coverage == null ? '—' : Math.round(r.coverage * 100) }))}</small></div>
<div><span class="lbl">${esc(t('hype.discovery'))}</span><span class="num mono">${nf(d.score)}</span><small class="dim">${esc(t('hype.cov', { n: d.coverage == null ? '—' : Math.round(d.coverage * 100) }))}</small></div>
<div><span class="lbl">${esc(t('hype.gap.class'))}</span><span class="mono">${esc(t(GAP[r.label] || 'hype.gap.insufficient'))}</span><small class="dim">${esc(t('hype.gap.diff', { n: r.gap == null ? '—' : (r.gap > 0 ? '+' : '') + nf(r.gap) }))}</small></div></div></section>
<section><h3>${esc(t('hype.sample'))} · ${esc(t('sample.posts_in_our_sample'))}</h3><p>${esc(t('hype.sample.line', { posts: m.mentions ?? '—', voices: m.voices ?? '—', w: F.win }))}</p>
<ul>${Object.entries(cnt).map(([n, k]) => `<li class="dim">${esc(t('ui.counted', { net: n, n: k }))}</li>`).join('')}${shown.map(p => `<li><span class="mono dim">${esc(p.pl)} ${esc(p.d || '')}</span> ${link(p.url, posted(p.t || p.url))}${p.score != null ? ` <span class="mono dim">${nf(p.score)} ${esc(t('hype.pts'))}</span>` : ''}</li>`).join('')}</ul></section>${body}`;
    el.classList.add('on'); sc.classList.add('on'); el.setAttribute('aria-label', it.name);
    const close = () => { el.classList.remove('on'); sc.classList.remove('on'); F.open = ''; history.replaceState(null, '', location.pathname + location.search); $(`[data-p="${CSS.escape(slug)}"]`)?.focus(); };
    $('#close').onclick = close; sc.onclick = close; el.onkeydown = e => { if (e.key === 'Escape') close(); };
    $('#close').focus();
  }
  const open = slug => { F.open = slug; history.replaceState(null, '', '#p=' + encodeURIComponent(slug)); detail(slug); };
  render = () => {
    const rows = (H[F.win]?.all?.rows || []).filter(r => H.items[r.id] && (F.area === 'all' || H.items[r.id].tag === F.area)), q = F.q.trim().toLowerCase();
    const list = rows.filter(r => !q || [r.id, H.items[r.id].name, ...(H.items[r.id].aliases || [])].join(' ').toLowerCase().includes(q));
    const b = block(), cov = (H.coverage_short || []).map((_, i) => `<li>${b.p(null, `coverage_short[${i}]`)}</li>`).join('');
    $('#banner').innerHTML = `<p><b>${esc(cutLine())}</b></p><p>${esc(t('x_route.disclosure'))}</p>${b.wrap(`<ul class="dim">${cov}</ul>`)}`;
    const dots = list.slice(0, F.all ? list.length : 15).map(r => ({ id: r.id, label: H.items[r.id].name, a: r.score, d: H.items[r.id].discovery?.score ?? null }));
    $('#body').innerHTML = `${kpis([[t('hype.k.projects'), nf(H.n_projects), esc(t('hype.k.projects_sub'))], [t('hype.k.ranked'), nf(rows.length), esc(t('hype.k.ranked_sub', { w: F.win }))],
  [t('hype.k.discovery'), nf(rows.filter(r => H.items[r.id].discovery?.score != null).length), esc(t('hype.k.discovery_sub'))], [t('hype.k.cut'), `<span style="font-size:.7em">${esc(day(H.content_cutoff))}</span>`, esc(t('hype.k.cut_sub'))]])}
<div class="bar-row">${seg('win', t('ui.window_label'), wins.map(w => [w, w]), F.win)}<select id="area" aria-label="${esc(t('output.area'))}"><option value="all">${esc(t('output.all_areas'))}</option>${(H.views || []).filter(v => v !== 'all').map(a => `<option${F.area === a ? ' selected' : ''}>${esc(a)}</option>`).join('')}</select>
<input type="search" id="q" placeholder="${esc(t('ui.search'))}" aria-label="${esc(t('ui.search'))}" value="${esc(F.q)}"><span class="count" aria-live="polite">${esc(t('ui.showing', { n: list.length, total: rows.length }))}</span></div>
<div id="dumb"></div><div class="tw" id="tbl"></div>`;
    card($('#dumb'), { title: t('hype.gap.title'), sub: `${t('hype.gap.note')} · ${cutLine()}`, legend: [[t('hype.attention'), '--s2'], [t('hype.discovery'), '--s1']],
      draw: (p, W) => { dumbbell(p, W, dots, { a: t('hype.attention'), d: t('hype.discovery'), none: t('hype.no_discovery'), label: t('hype.gap.title'), pick: open }); if (list.length > 15) p.insertAdjacentHTML('beforeend', `<p><button class="btn" id="more">${esc(F.all ? t('ui.show_top', { n: 15 }) : t('ui.show_all', { n: list.length }))}</button></p>`); $('#more', p)?.addEventListener('click', () => { F.all = !F.all; render(); }); },
      table: { cols: [[t('hype.project')], [t('hype.attention'), 'n'], [t('hype.discovery'), 'n']], rows: dots.map(x => ({ cells: [posted(x.label), nf(x.a), nf(x.d)] })) } });
    $('#tbl').innerHTML = table({ caption: cutLine(), cols: [['#', 'n hm'], [t('hype.project')], [t('hype.attention'), 'n'], [t('hype.discovery'), 'n'], [t('hype.gap.class'), 'hm'], [t('ui.voices'), 'n hm'], [t('hype.posts'), 'n hm'], [t('hype.platforms'), 'hm']],
      rows: list.map(r => { const it = H.items[r.id], m = it.win?.[F.win] || {}; return { attr: ` class="go" tabindex="0" data-p="${esc(r.id)}"`, cells: [r.rank ?? '—', `<b>${posted(it.name)}</b>`, nf(r.score), nf(it.discovery?.score), esc(t(GAP[r.label] || 'hype.gap.insufficient')), nf(m.voices), nf(m.mentions), `<span class="mono dim">${esc((m.platforms || []).join(' · '))}</span>`] }; }) });
    $$('#tbl tr.go').forEach(tr_ => { tr_.onclick = () => open(tr_.dataset.p); tr_.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); open(tr_.dataset.p); } }; });
    onSeg('win', v => { F.win = v; render(); });
    $('#area').onchange = e => { F.area = e.target.value; render(); };
    $('#q').oninput = e => { F.q = e.target.value; render(); const n = $('#q'); n.focus(); n.setSelectionRange(n.value.length, n.value.length); };
    if (F.open) detail(F.open);
  };
  render();
}
// ------------------------------------------------------------------ start
async function start() {
  const u = new URLSearchParams(location.search);
  lang = ['en', 'pt'].includes(u.get('lang')) ? u.get('lang') : store.get('dehype.lang') === 'pt' ? 'pt' : 'en';
  theme = store.get('dehype.theme') === 'light' ? 'light' : 'dark';
  try {
    I = await load('i18n/strings.json');
    for (const [k, v] of Object.entries(I.strings)) if (v.ref) { const [f, key] = v.ref.split('#'); REF[k] = at(await load('i18n/' + f), key); }
    DATA_KEYS = [...new Set(Object.values(I.fields || {}).flatMap(p => Object.values(p).flatMap(s => Array.isArray(s) ? s : s.keys || [])))];
    shell();
    $('#main').classList.add('loading');
    await ({ stories, output, hype })[page]();
  } catch (e) { $('#body').innerHTML = `<div class="err">${esc(t('ui.error'))} <span class="mono">${esc(e.message)}</span></div>`; }
  $('#main').classList.remove('loading');
}
start();
return { t, tr, load, evidence, verdictSlot, sources, kpis, card, table, scatter, hbars, dumbbell, METHOD };
})();
