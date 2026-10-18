// dehype shell (design rows 9-11, 13; D5 amended: static pages, one stylesheet, one script, no build): the briefing (index.html), all
// stories, output, Hype, method, audit and Sources (status.html) pages; index.html also folds the console's old URLs (fold below). Each page names the data
// files it reads in <body data-src>; our own text comes from i18n/strings.json in en and pt, through the page language's table
// (i18n/table.en.json or i18n/table.pt.json, written by scripts/dehype/plugins/frontend.mjs, Decision 9); headlines and titles stay as posted with
// their lang tag. The data files carry our own text in English: tr() maps such a value back to its strings.json entry with the
// templates scripts/check_page.mjs uses (ours) and renders the page language. English method paragraphs are never shown: pages link
// the method anchors (strings.json methods). Dossier prose shows in Portuguese only from a reviewed i18n/dossier.pt.json entry whose
// SHA256 matches the current English, else in English under the fixed Portuguese notice (C24). Classic script: new Function parses it.
'use strict';
const DH = (() => {
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const REPO = 'https://github.com/namastex888/dehype/blob/dev/';            // repository files the method text links (code, config)
const ATTEST_REPO = REPO.split('/').slice(3, 5).join('/');                 // owner/name, for gh attestation verify --repo
const NAV = [['index', 'nav.briefing'], ['stories', 'nav.stories'], ['output', 'nav.output'], ['hype', 'nav.hype'], ['method', 'nav.method'], ['audit', 'nav.audit'], ['status', 'nav.status']];
const COUNT_ONLY = new Set(['Reddit', 'X', 'LinkedIn', 'YouTube', 'Telegram', 'Discord', 'Mastodon']);
const NOT_FETCHED = 'not fetched', DAY = 864e5;
const store = { get: k => { try { return localStorage.getItem(k); } catch { return null; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch { } } };
const page = document.body.dataset.page, files = (document.body.dataset.src || '').split(/\s+/).filter(Boolean);
let I = { strings: {}, fields: {} }, lang = 'en', theme = 'dark', DATA_KEYS = [], render = () => { };
const cache = {};
const TABLE = { en: 'i18n/table.en.json', pt: 'i18n/table.pt.json' };   // strings.json per language, refs resolved (frontend.mjs)
// ------------------------------------------------------------------ data and strings
function load(f) {                                              // the one loader: JSON, the method sources as text, the search vectors as bytes
  return cache[f] ||= fetch(f, { cache: 'no-cache' }).then(r => { if (!r.ok) throw new Error(`${f}: HTTP ${r.status}`); return /\.md$/.test(f) ? r.text() : /\.bin$/.test(f) ? r.arrayBuffer() : r.json(); });
}
const opt = (f, empty) => load(f).catch(() => empty);
const entry = k => I.strings[k];
function t(k, v = {}) { const e = entry(k), s = e ? (e[lang] || e.en) : k; return s.replace(/\{(\w+)\}/g, (m, x) => x in v ? v[x] : m); }
const RX = {}, TR = new Map();
const rx = k => RX[k] ||= new RegExp('^' + String(entry(k)?.en ?? '\u0000').replace(/[.*+?^$()|[\]\\]/g, '\\$&').replace(/\\?\{(\w+)\\?\}/g, '(?<$1>[\\s\\S]+?)') + '$');
const lit = k => String(entry(k)?.en || '').replace(/\{\w+\}/g, '').length;
function parse(v, keys, depth = 0) {                            // the best parse, as the gate's ours: most literal text, {detail} included
  let best = null;
  for (const k of keys) {
    const m = rx(k).exec(v); if (!m) continue;
    const g = { ...m.groups }; let sc = lit(k);
    if (g.detail != null) { const d = depth < 2 && parse(g.detail, keys.filter(x => x !== k), depth + 1); if (!d) continue; sc += d[0]; g.detail = d[1]; }
    if (!best || sc > best[0]) best = [sc, t(k, g)];
  }
  return best;
}
function tr(v, keys = DATA_KEYS) {                               // a data string that is our own text, in the page language
  if (lang === 'en' || typeof v !== 'string') return v;
  const ck = keys.length + '|' + v; if (!TR.has(ck)) TR.set(ck, parse(v, keys)?.[1] ?? v);
  return TR.get(ck);
}
const tn = (k, n, v = {}) => t(n === 1 && I.strings[k + '.one'] ? k + '.one' : k, { n: nf(n), ...v });   // singular or plural
let NAMES = null;                                                // names we write (sources, networks, areas, windows): name.* entries
const nm = x => { NAMES ||= new Map(Object.entries(I.strings).filter(([k]) => k.startsWith('name.')).map(([k, e]) => [e.en, k])); const k = NAMES.get(x); return k ? t(k) : x; };
const loc = () => lang === 'pt' ? 'pt-BR' : 'en-US';
const nf = n => typeof n === 'number' ? n.toLocaleString(loc(), { maximumFractionDigits: 1 }) : n == null ? '—' : esc(tr(n));
const day = s => (s || '').slice(0, 10);
const ago = (iso, now) => { const h = (now - Date.parse(iso)) / 36e5; return !isFinite(h) ? '—' : h < 1 ? t('ui.ago.now') : h < 48 ? tn('ui.ago.h', Math.round(h)) : tn('ui.ago.d', Math.round(h / 24)); };
const href = (p, q = '') => p + '.html' + ((q || lang === 'pt') ? '?' + [q, lang === 'pt' ? 'lang=pt' : ''].filter(Boolean).join('&') : '');
const METHOD = () => href('method'), POLICY = () => href('method', 'doc=policy');   // the method page renders both sources in the page language
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
  const nav = $('#top nav'), cur = $('[aria-current]', nav); if (cur && nav.scrollWidth > nav.clientWidth) nav.scrollLeft = cur.offsetLeft - 16;
  $$('[data-lang]').forEach(b => b.onclick = () => setLang(b.dataset.lang).catch(oops));
  $('#theme').onclick = () => { theme = theme === 'dark' ? 'light' : 'dark'; store.set('dehype.theme', theme); shell(); redraw(); };
  $$('[data-k]').forEach(el => el.textContent = t(el.dataset.k));
  document.documentElement.classList.add('ready');
  $('meta[name=description]')?.setAttribute('content', t(page + '.scope'));
  $('#reads').innerHTML = esc(t('ui.reads')) + ' ' + files.map(f => `<code class="mono">${esc(f)}</code>`).join(', ');
  $('#foot').innerHTML = `<div class="wrap"><p>${esc(t('ui.foot.data'))} ${files.map(f => `<a href="${esc(f)}"><code class="mono">${esc(f)}</code></a>`).join(' · ')}</p>
<p><a href="${METHOD()}">${esc(t('ui.method'))}</a> · <a href="${POLICY()}#corrections">${esc(t('ui.corrections'))}</a> · ${esc(t('ui.foot.counts'))}</p></div>`;
}
async function setLang(l) {
  I = await load(TABLE[l]);
  lang = l; store.set('dehype.lang', l); TR.clear(); NAMES = null;
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
function sources(S, compact) {                                   // coverage: a one-line summary (compact: the count only), each source's status behind it
  const cls = { ok: 'ok', partial: 'partial', failed: 'bad', [NOT_FETCHED]: 'nf' }, ico = { ok: '●', partial: '◐', failed: '✕' }, E = Object.entries(S || {}), st = s => typeof s === 'string' ? s : s.status;
  const weak = E.filter(([, s]) => st(s) !== 'ok').map(([n, s]) => `${esc(nm(n))} <span class="mono">${esc(tr(st(s)))}</span>`).join(' · ');
  return `<details class="cov"><summary><span class="lbl">${esc(t('ui.coverage'))}</span> <span class="st ok"><b aria-hidden="true">●</b> ${esc(t('ui.sources_ok', { n: E.filter(([, s]) => st(s) === 'ok').length, total: E.length }))}</span>${weak && !compact ? ` · ${weak}` : ''}</summary>
<ul>${E.map(([n, s]) => `<li class="st ${cls[st(s)] || 'nf'}"><b aria-hidden="true">${ico[st(s)] || '○'}</b> ${esc(nm(n))} <span class="mono">${esc(tr(st(s)))}</span>${s.detail ? ` <span class="dim">· ${esc(tr(s.detail))}</span>` : ''}</li>`).join('')}</ul></details>`;
}
function table(o) {
  return `<table class="t${o.stack ? ' stack' : ''}">${o.caption ? `<caption>${esc(o.caption)}</caption>` : ''}<thead><tr>${o.cols.map(([l, c]) => `<th scope="col"${c ? ` class="${c}"` : ''}>${esc(l)}</th>`).join('')}</tr></thead>
<tbody>${o.rows.map(r => `<tr${r.attr || ''}>${r.cells.map((c, i) => `<td${o.cols[i][1] ? ` class="${o.cols[i][1]}"` : ''}${o.stack ? ` data-l="${esc(o.cols[i][0])}"` : ''}>${c}</td>`).join('')}</tr>`).join('') || `<tr><td colspan="${o.cols.length}" class="dim">${esc(t('ui.none'))}</td></tr>`}</tbody></table>`;
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
  s += days.map((d, i) => i % every ? '' : `<text class="axis" x="${X(d)}" y="${H - 8}" text-anchor="middle">${esc(new Date(d).toLocaleDateString(loc(), { day: 'numeric', month: 'short', timeZone: 'UTC' }))}</text>`).join('');
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
// Small multiples of horizontal bars (output by area): one panel per series, each on its own count scale, rows in the same order;
// panels side by side when wide, stacked when narrow. A row (all its panels) is one hover, focus and pick target.
function hbars(plot, W, rows, series, o) {
  const narrow = W < 560, lw = narrow ? Math.min(W * .45, 18 + 6.8 * Math.max(...rows.map(r => r.label.length))) : 168, gap = 32, rh = 30, bh = 14, top = 28, ax = 22, n = series.length;
  const pw = narrow ? W - lw : (W - lw - gap * (n - 1)) / n, ph = top + rows.length * rh + ax, H = narrow ? n * ph + (n - 1) * 16 : ph;
  const P = series.map(([name, c], j) => {
    const ox = narrow ? lw : lw + j * (pw + gap), oy = narrow ? j * (ph + 16) : 0, xt = ticks(Math.max(1, ...rows.map(r => r.vals[j])), 3), xm = xt.at(-1);
    return { name, c, ox, oy, xt, X: v => ox + v / xm * (pw - 34) };
  });
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(o.label)}">`;
  for (const p of P) {
    const y1 = p.oy + top - 4, y2 = p.oy + top + rows.length * rh;
    s += `<circle cx="${p.ox + 4}" cy="${p.oy + 10}" r="4" style="fill:var(${p.c})"/><text class="rlabel" x="${p.ox + 14}" y="${p.oy + 14}" style="fill:var(--ink)">${esc(p.name)}</text>`;
    s += p.xt.map(v => `<line class="grid" x1="${p.X(v)}" x2="${p.X(v)}" y1="${y1}" y2="${y2}"/><text class="axis" x="${p.X(v)}" y="${y2 + 16}" text-anchor="middle">${nf(v)}</text>`).join('');
    s += `<line class="base" x1="${p.X(0)}" x2="${p.X(0)}" y1="${y1}" y2="${y2}"/>`;
  }
  s += rows.map((r, i) => {
    const sel = o.sel === r.key;
    return `<g class="mk${sel ? ' sel' : ''}" data-i="${i}" tabindex="0" role="button" aria-pressed="${sel}" aria-label="${esc(r.label + ': ' + series.map(([l], j) => `${l} ${r.vals[j]}`).join(', '))}">` +
      P.filter((p, j) => narrow || j === 0).map(p => `<rect class="hit" x="0" y="${p.oy + top + i * rh}" width="${W}" height="${rh - 2}" rx="4"/>`).join('') +
      P.map((p, j) => { const y = p.oy + top + i * rh + (rh - bh) / 2 - 1, v = r.vals[j];
        return `${narrow || j === 0 ? `<text class="rlabel" x="${lw - 12}" y="${y + 11}" text-anchor="end" style="${sel ? 'fill:var(--ink);font-weight:600' : ''}">${esc(r.label)}</text>` : ''}<path d="${bar(p.X(0), y, p.X(v) - p.X(0), bh)}" style="fill:var(${p.c})"/><text class="vlabel mono" x="${p.X(v) + 6}" y="${y + 11}">${nf(v)}</text>`; }).join('') + '</g>';
  }).join('') + '</svg>';
  plot.innerHTML = s;
  hover(plot, (i, x, y) => showTip(x, y, rows[i].label, series.map(([l, c], j) => [nf(rows[i].vals[j]), l, c])), i => o.pick(rows[i].key));
}
// Dumbbell on the 0-100 score axis: hype (attention) and substance (discovery) components per project; no dot where unmeasured.
function dumbbell(plot, W, rows, o) {
  const narrow = W < 560, lw = narrow ? 0 : 190, rh = narrow ? 40 : 28, m = { l: lw, r: 18, t: 22 };
  const iw = W - m.l - m.r, X = v => m.l + v / 100 * iw, H = m.t + rows.length * rh + 8;
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(o.label)}">`;
  s += [0, 25, 50, 75, 100].map(v => `<line class="${v === 50 ? 'base' : 'grid'}" x1="${X(v)}" x2="${X(v)}" y1="${m.t - 4}" y2="${H - 4}"/><text class="axis" x="${X(v)}" y="12" text-anchor="${v === 0 ? 'start' : v === 100 ? 'end' : 'middle'}">${v}</text>`).join('');
  s += rows.map((r, i) => {
    const y = m.t + i * rh + (narrow ? 26 : rh / 2), has = r.d != null;
    return `<g class="mk" data-i="${i}" tabindex="0" role="button" aria-label="${esc(`${r.label}: ${o.a} ${nf(r.a)}, ${o.d} ${has ? nf(r.d) : '—'}`)}">
<rect class="hit" x="0" y="${m.t + i * rh}" width="${W}" height="${rh - 2}" rx="4"/>${narrow && i ? `<line class="grid" x1="0" x2="${W}" y1="${m.t + i * rh}" y2="${m.t + i * rh}"/>` : ''}
<text class="rlabel halo" x="${narrow ? m.l : lw - 12}" y="${narrow ? m.t + i * rh + 13 : y + 4}" text-anchor="${narrow ? 'start' : 'end'}">${esc(r.label)}</text>
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
const nets = c => { const e = Object.entries(c.networks || {}); return e.filter(([, v]) => v !== 0).sort((a, b) => (typeof b[1] === 'number' ? b[1] : -1) - (typeof a[1] === 'number' ? a[1] : -1)).map(([k, v]) => `<span class="nw">${esc(nm(k))} ${nf(v)}</span>`).join(' · ') || '—'; };
const rd = v => `<span class="num mono${typeof v === 'number' ? '' : ' s'}">${typeof v === 'boolean' || v === NOT_FETCHED || v == null ? esc(yesno(v)) : nf(v)}</span>`;
const yesno = v => v === true ? t('ui.yes') : v === false ? t('ui.no') : tr(v ?? NOT_FETCHED);
function evidence(r, s, v, i, now, brief = false) {            // a story's evidence record; brief: the briefing row (spread path in view)
  const c = r.computed || {}, sub = r.substance || {}, u = s && (s.link || s.url), fixed = rx('headline.count_only').test(r.headline || '');
  const hd = fixed ? esc(tr(r.headline, ['headline.count_only'])) : posted(r.headline, r.lang);
  const st = Object.entries(r.sources || {}), ok = st.filter(([, x]) => x === 'ok').length, weak = st.filter(([, x]) => x !== 'ok').map(([n, x]) => `${esc(nm(n))} ${esc(tr(x))}`).join(' · ');
  const posts = (s?.posts || []).filter(p => p.title), counted = Object.entries(s?.nets || {}).filter(([n]) => COUNT_ONLY.has(n));
  const path = (s?.path || []).map(p => `${esc(['Newsletter', 'Official'].includes(p.net) && p.who ? p.who : nm(p.net))} <span class="mono dim">${esc(day(p.at).slice(5))}</span>`).join(' → ');
  const rel = r.related_in_topic || {}, refs = [...(sub.repos || []), ...(sub.papers || [])];
  const meta = `${esc(t('ui.sources_ok', { n: ok, total: st.length }))}${weak ? ` · ${weak}` : ''} · ${esc(t('ui.newest', { ago: ago(r.last, now) }))}`;
  return `<li class="story" id="${esc(r.id)}"><span class="rk">${String(i + 1).padStart(2, '0')}</span><div>
<span class="seen${r.seen === 'new today' ? ' new' : ''}">${esc(tr(r.seen))}</span>${r.release ? ` <span class="meta">· ${esc(r.release)}</span>` : ''} <span class="meta">· ${esc(kind(r))}</span>
<h3>${u ? link(u, hd) : hd}</h3>
<div class="read${brief ? ' b' : ''}"><div><span class="lbl">${esc(t('ui.voices'))}</span><span class="num mono">${nf(c.voices)}</span></div>
<div><span class="lbl">${esc(t('ui.networks'))}</span><span class="nets">${nets(c)}</span></div>
<div><span class="lbl">${esc(t('ui.newsletters'))}</span>${rd(c.newsletters)}</div>
${brief ? `<div class="sp"><span class="lbl">${esc(t('brief.spread'))}</span><span class="nets">${path || '—'}</span></div>` : `<div><span class="lbl">${esc(t('ui.lab_post'))}</span>${rd(c.official)}</div>
<div><span class="lbl">${esc(t('ui.hn_points'))}</span>${rd(c.hn_points)}</div>`}</div>
${verdictSlot(v)}
${brief ? '' : `<div class="meta">${meta}</div>`}<details class="more"><summary>${esc(t('ui.evidence'))}${brief ? ` <span class="meta">· ${esc(t('ui.newest', { ago: ago(r.last, now) }))}</span>` : ''}</summary><div class="ev">
${brief ? `<p class="meta">${meta}</p>` : ''}
${brief ? `<h4>${esc(t('ui.lab_post'))} · ${esc(t('ui.hn_points'))}</h4><p>${rd(c.official)} · ${rd(c.hn_points)}</p>` : ''}<h4>${esc(t('ui.path'))}</h4><p>${path || '—'}</p>
<h4>${esc(t('ui.posts'))}</h4><ul>${posts.map(p => `<li><span class="mono dim">${esc(nm(p.net))}</span> ${link(p.url, posted(p.title, p.lang))}${['Newsletter', 'Official'].includes(p.net) && p.author ? ` <span class="dim">· ${esc(p.author)}</span>` : ''} <span class="mono dim">${esc(day(p.at))}</span></li>`).join('')}
${counted.map(([n, k]) => `<li class="dim">${esc(tn('ui.counted', k, { net: nm(n) }))}</li>`).join('')}${!posts.length && !counted.length ? `<li class="dim">${esc(t('ui.none'))}</li>` : ''}</ul>
<h4>${esc(tr(sub.from || "the story's own links"))}</h4><ul>${refs.map(x => `<li>${link(x, `<span class="mono">${esc(x.replace(/^https:\/\/(github\.com|arxiv\.org\/abs)\//, ''))}</span>`)}</li>`).join('') || `<li class="dim">${esc(t('ui.none'))}</li>`}</ul>
<h4>${esc(tr(rel.reading || 'related in topic'))}</h4><ul>${(rel.items || []).map(x => `<li><span class="mono dim">${esc(nm(x.net))}</span> ${link(x.url, posted(x.title, x.lang))}</li>`).join('') || `<li class="dim">${esc(t('ui.none'))}</li>`}</ul>
${c.newsletter_names?.length ? `<h4>${esc(t('ui.newsletters'))}</h4><p>${c.newsletter_names.map(esc).join(' · ')}</p>` : ''}
<p class="dim mono">${esc(r.id)} · ${esc(t('ui.first_last', { first: day(r.first), last: day(r.last) }))}</p></div></details></div></li>`;
}
// ------------------------------------------------------------------ all stories
async function stories() {
  const [B, P, V, AL] = await Promise.all([load('briefing.json'), load('pulse.json'), opt('verdicts.json', { rows: [] }), opt('story-aliases.json', { aliases: {} })]);
  const by = new Map((P.stories || []).map(s => [s.id, s])), ver = verdicts(V, AL), now = Date.parse(B.generated_at), R = B.records || [];
  const F = { q: qp('q'), kind: 'all', seen: 'all', sort: 'heat', view: qp('view') === 'table' ? 'table' : 'list' };
  const x0 = Math.min(...R.map(r => Date.parse(r.first))), x1 = now;
  render = () => {
    const main = $('#body');
    main.innerHTML = `${staleBanner(B)}${foldNote('')}<p class="reads">${esc(t('ui.generated', { at: B.window?.end_brt || B.generated_at }))}</p>
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
  const F = { days: [7, 30, 90].includes(+qp('days')) ? +qp('days') : 7, area: areas.includes(qp('area')) ? qp('area') : 'all', tab: qp('tab') === 'repos' ? 'repos' : 'papers', q: qp('q'), all: false };
  const date = { papers: it => it.published, repos: it => it.created };
  render = () => {
    const cut = new Date(now - (F.days - 1) * DAY).toISOString().slice(0, 10), wk = F.days + 'd';
    const inWin = tab => Object.entries(D[tab]?.items || {}).filter(([, it]) => (date[tab](it) || '') >= cut);
    const P = inWin('papers'), Rp = inWin('repos'), count = (L, a) => L.filter(([, it]) => it.tag === a).length;
    const rows = areas.map(a => ({ key: a, label: nm(a), vals: [count(P, a), count(Rp, a)] }));
    const same = F.days === 7 && g?.value && g.value.since === cut && g.value.areas.every(x => { const r = rows.find(y => y.key === x.area); return r && r.vals[0] === x.papers && r.vals[1] === x.repos; });
    const gnote = !g ? '' : g.value == null ? tr(g.reason) : F.days === 7 ? (same ? t('output.gauge.same', { name: tr(g.name) }) : t('output.gauge.differs', { name: tr(g.name) })) : t('output.gauge.other', { name: tr(g.name) });
    $('#body').innerHTML = `${staleBanner(B)}${foldNote(F.days + 'd')}<div class="bar-row">${seg('days', t('ui.window_label'), [[7, '7d'], [30, '30d'], [90, '90d']], F.days)}
<select id="area" aria-label="${esc(t('output.area'))}"><option value="all">${esc(t('output.all_areas'))}</option>${areas.map(a => `<option value="${esc(a)}"${F.area === a ? ' selected' : ''}>${esc(nm(a))}</option>`).join('')}</select>
<span class="count mono">${esc(t('output.since', { date: cut }))}</span></div>
${kpis([[t('output.k.papers'), nf(P.length), esc(t('output.k.of', { n: nf(Object.keys(D.papers?.items || {}).length) }))], [t('output.k.repos'), nf(Rp.length), esc(t('output.k.of', { n: nf(Object.keys(D.repos?.items || {}).length) }))],
  [t('output.k.areas'), nf(areas.length), esc(t('output.k.areas_sub'))], [t('output.k.tracked'), nf((D.tracked?.papers || 0) + (D.tracked?.repos || 0)), esc(t('output.k.tracked_sub', { p: nf(D.tracked?.papers), r: nf(D.tracked?.repos) }))]])}
${sources(D.sources)}<p class="reads">${esc(gnote)}${g ? ` <span class="pill">${esc(tr(g.status))}</span>` : ''}</p><div id="bars"></div><div id="drill"></div>`;
    card($('#bars'), { title: t('output.chart.title', { n: F.days }), sub: t('output.chart.sub'),
      draw: (p, W) => hbars(p, W, rows, [[t('output.papers'), '--s1'], [t('output.repos'), '--s2']], { sel: F.area, label: t('output.chart.title', { n: F.days }), pick: a => { F.area = F.area === a ? 'all' : a; F.all = false; render(); ($('#bars .mk.sel') || $('#bars .mk'))?.focus(); } }),
      table: { cols: [[t('output.area')], [t('output.papers'), 'n'], [t('output.repos'), 'n']], rows: rows.map(r => ({ cells: [esc(r.label), nf(r.vals[0]), nf(r.vals[1])] })) } });
    $('#area').onchange = e => { F.area = e.target.value; F.all = false; render(); };
    onSeg('days', v => { F.days = +v; F.all = false; render(); });
    drill(F, D, wk, F.tab === 'papers' ? P : Rp);
  };
  function drill(F, D, wk, L) {
    const score = new Map((D[F.tab]?.[wk]?.all?.rows || []).map(r => [r.id, r]));
    const items = search(F.tab, L.filter(([, it]) => F.area === 'all' || it.tag === F.area)
      .sort((a, b) => (score.get(b[0])?.score ?? -1) - (score.get(a[0])?.score ?? -1) || ((b[1].upvotes || b[1].stars || 0) - (a[1].upvotes || a[1].stars || 0))), F.q, x => x[0], ([id, it]) => [id, it.title, it.desc, it.lab, it.owner].join(' '));
    SEM.redo = () => keepQ(() => drill(F, D, wk, L));
    const shown = F.all ? items : items.slice(0, 25);
    const cols = F.tab === 'papers' ? [[t('output.col.paper')], [t('output.col.lab'), 'hm'], [t('output.area'), 'hm'], [t('output.col.published'), 'n hm'], [t('output.col.upvotes'), 'n'], [t('output.col.score'), 'n']]
      : [[t('output.col.repo')], [t('output.col.desc'), 'hm'], [t('output.area'), 'hm'], [t('output.col.created'), 'n hm'], [t('output.col.stars'), 'n'], [t('output.col.gained'), 'n hm'], [t('output.col.score'), 'n']];
    const cells = ([id, it]) => F.tab === 'papers' ? [link('https://arxiv.org/abs/' + id, posted(it.title)), esc(it.lab || '—'), esc(nm(it.tag || '—')), esc(it.published || '—'), nf(it.upvotes), nf(score.get(id)?.score)]
      : [link(it.url, `<span class="mono">${esc(id)}</span>`), it.desc ? posted(it.desc) : '—', esc(nm(it.tag || '—')), esc(day(it.created) || '—'), nf(it.stars), nf(score.get(id)?.gained), nf(score.get(id)?.score)];
    $('#drill').innerHTML = `<div class="bar-row">${seg('tab', t('output.kind'), [['papers', t('output.papers')], ['repos', t('output.repos')]], F.tab)}
<input type="search" id="q" placeholder="${esc(t('ui.search'))}" aria-label="${esc(t('ui.search'))}" value="${esc(F.q)}">${semBtn()}<span class="count" aria-live="polite">${esc(t('ui.showing', { n: shown.length, total: items.length }))}</span></div>
<div class="tw">${table({ caption: t('output.table.caption', { area: F.area === 'all' ? t('output.all_areas') : nm(F.area), wk }), cols, rows: shown.map(x => ({ cells: cells(x) })) })}</div>
${items.length > shown.length ? `<p><button class="btn" id="all">${esc(t('ui.show_all', { n: items.length }))}</button></p>` : ''}`;
    onSeg('tab', v => { F.tab = v; F.all = false; render(); }); semUi();
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
  const blind = !subtle && drop.size > 0;                        // no hashing here: hide every linked post rather than risk a listed one
  if (subtle && drop.size) for (const it of Object.values(H.items)) for (const p of it.posts || []) if (p.url && drop.has(await sha(p.url))) gone.add(p.url);
  if (subtle) for (const e of PT.entries || []) {                                   // a reviewed entry whose hash matches the current English
    const en = e.slug == null ? at(H, e.field) : at(H.items[e.slug] || {}, e.field);
    if (typeof en === 'string' && e.reviewed_in && e.pt && await sha(en) === e.sha256) pt.set(`${e.slug}|${e.field}`, e.pt);
  }
  const ph = XF.placeholder?.en;
  const wins = ['1d', '7d', '30d', '90d', 'overall'].filter(w => H.windows?.[w]?.enabled && H[w]);
  const F = { win: wins.includes(qp('win')) ? qp('win') : wins.includes('7d') ? '7d' : wins[0], area: (H.views || []).includes(qp('area')) && qp('area') !== 'all' ? qp('area') : 'all', q: qp('q'), all: false, open: decodeURIComponent((location.hash.match(/^#p=(.+)$/) || [])[1] || '') };
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
  const cutLine = () => t('hype.cut', { date: day(H.content_cutoff) }), cutHtml = () => esc(t('hype.cut', { date: '\u0000' })).replace('\u0000', `<span class="nw">${esc(day(H.content_cutoff))}</span>`);
  function detail(slug) {
    const it = H.items[slug], el = $('#panel'), sc = $('#scrim');
    if (!it) { el.classList.remove('on'); sc.classList.remove('on'); return; }
    const r = (H[F.win]?.all?.rows || []).find(x => x.id === slug) || {}, d = it.discovery || {}, m = it.win?.[F.win] || {}, b = block();
    const L = it.links || {}, links = [['site', 'hype.link.site'], ['repo', 'hype.link.repo'], ['paper', 'hype.link.paper'], ['hf', 'hype.link.hf'], ['x_handle', 'hype.link.x']].filter(([k]) => L[k]).map(([k, s]) => link(L[k], esc(t(s)))).join(' · ');
    const posts = (it.posts || []).filter(p => !gone.has(p.url) && !(blind && p.url)), cnt = {};
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
    el.innerHTML = `<button class="btn x" id="close">${esc(t('ui.close'))}</button><p class="eyebrow">${cutHtml()}</p><h2>${posted(it.name)}</h2><p>${links}</p>
<section><h3>${esc(t('ui.verdict'))}</h3><div class="slot"><span class="pill">${esc(t('ui.verdict.none'))}</span><span>${esc(t('hype.verdict.note'))}</span></div></section>
<section><h3>${esc(t('hype.gap.title'))} · ${esc(nm(F.win))}</h3><p class="dim">${esc(t('hype.gap.note'))}</p><div class="comp">
<div><span class="lbl">${esc(t('hype.attention'))}</span><span class="num mono">${nf(r.score)}</span><small class="dim">${esc(t('hype.cov', { n: r.coverage == null ? '—' : Math.round(r.coverage * 100) }))}</small></div>
<div><span class="lbl">${esc(t('hype.discovery'))}</span><span class="num mono">${nf(d.score)}</span><small class="dim">${esc(t('hype.cov', { n: d.coverage == null ? '—' : Math.round(d.coverage * 100) }))}</small></div>
<div><span class="lbl">${esc(t('hype.gap.class'))}</span><span class="mono">${esc(t(GAP[r.label] || 'hype.gap.insufficient'))}</span><small class="dim">${esc(t('hype.gap.diff', { n: r.gap == null ? '—' : (r.gap > 0 ? '+' : '') + nf(r.gap) }))}</small></div></div></section>
<section><h3>${esc(t('hype.sample'))} · ${esc(t('sample.posts_in_our_sample'))}</h3><p>${esc(t('hype.sample.line', { posts: tn('n.posts', m.mentions), voices: tn('n.voices', m.voices), w: nm(F.win) }))}</p>
<h3>${esc(t('hype.sample.list'))}</h3><ul>${Object.entries(cnt).map(([n, k]) => `<li class="dim">${esc(tn('ui.counted', k, { net: nm(n) }))}</li>`).join('')}${shown.map(p => `<li><span class="mono dim">${esc(nm(p.pl))} ${esc(p.d || '')}</span> ${link(p.url, posted(p.t || p.url))}${p.score != null ? ` <span class="mono dim">${nf(p.score)} ${esc(t('hype.pts'))}</span>` : ''}</li>`).join('')}</ul></section>${body}`;
    el.classList.add('on'); sc.classList.add('on'); el.setAttribute('aria-label', it.name);
    const close = () => { el.classList.remove('on'); sc.classList.remove('on'); F.open = ''; history.replaceState(null, '', location.pathname + location.search); $(`[data-p="${CSS.escape(slug)}"]`)?.focus(); };
    $('#close').onclick = close; sc.onclick = close; el.onkeydown = e => { if (e.key === 'Escape') close(); };
    $('#close').focus();
  }
  const open = slug => { F.open = slug; history.replaceState(null, '', '#p=' + encodeURIComponent(slug)); detail(slug); };
  render = () => {
    const rows = (H[F.win]?.all?.rows || []).filter(r => H.items[r.id] && (F.area === 'all' || H.items[r.id].tag === F.area));
    const list = search('hype', rows, F.q, r => r.id, r => [r.id, H.items[r.id].name, ...(H.items[r.id].aliases || [])].join(' '));
    SEM.redo = () => keepQ(render);
    const b = block(), cov = (H.coverage_short || []).map((_, i) => `<li>${b.p(null, `coverage_short[${i}]`)}</li>`).join('');
    $('#banner').innerHTML = `<p><b>${cutHtml()}</b></p><p>${esc(t('x_route.disclosure'))}</p><details class="more"><summary>${esc(t('hype.more'))}</summary>${b.wrap(`<ul class="dim">${cov}</ul>`)}</details>`;
    const dots = list.slice(0, F.all ? list.length : 15).map(r => ({ id: r.id, label: H.items[r.id].name, a: r.score, d: H.items[r.id].discovery?.score ?? null }));
    $('#body').innerHTML = `${foldNote(nm(F.win))}${kpis([[t('hype.k.projects'), nf(H.n_projects), esc(t('hype.k.projects_sub'))], [t('hype.k.ranked'), nf(rows.length), esc(t('hype.k.ranked_sub', { w: nm(F.win) }))],
  [t('hype.k.discovery'), nf(rows.filter(r => H.items[r.id].discovery?.score != null).length), esc(t('hype.k.discovery_sub'))], [t('hype.k.ahead'), nf(rows.filter(r => r.label === 'attention_ahead').length), esc(t('hype.k.ahead_sub', { n: nf(rows.filter(r => r.gap > 0).length) }))]])}
<div class="bar-row">${seg('win', t('ui.window_label'), wins.map(w => [w, nm(w)]), F.win)}<select id="area" aria-label="${esc(t('output.area'))}"><option value="all">${esc(t('output.all_areas'))}</option>${(H.views || []).filter(v => v !== 'all').map(a => `<option value="${esc(a)}"${F.area === a ? ' selected' : ''}>${esc(nm(a))}</option>`).join('')}</select>
<input type="search" id="q" placeholder="${esc(t('ui.search'))}" aria-label="${esc(t('ui.search'))}" value="${esc(F.q)}">${semBtn()}<span class="count" aria-live="polite">${esc(t('ui.showing', { n: list.length, total: rows.length }))}</span></div>
<div id="dumb"></div><div class="tw" id="tbl"></div>`;
    card($('#dumb'), { title: t('hype.gap.title'), sub: `${t('hype.gap.note')} · ${cutLine()}`, legend: [[t('hype.attention'), '--s2'], [t('hype.discovery'), '--s1']],
      draw: (p, W) => { dumbbell(p, W, dots, { a: t('hype.attention'), d: t('hype.discovery'), none: t('hype.no_discovery'), label: t('hype.gap.title'), pick: open }); if (list.length > 15) p.insertAdjacentHTML('beforeend', `<p><button class="btn" id="more">${esc(F.all ? t('ui.show_top', { n: 15 }) : t('ui.show_all', { n: list.length }))}</button></p>`); $('#more', p)?.addEventListener('click', () => { F.all = !F.all; render(); }); },
      table: { cols: [[t('hype.project')], [t('hype.attention'), 'n'], [t('hype.discovery'), 'n']], rows: dots.map(x => ({ cells: [posted(x.label), nf(x.a), nf(x.d)] })) } });
    $('#tbl').innerHTML = table({ caption: cutLine(), cols: [['#', 'n hm'], [t('hype.project')], [t('hype.attention'), 'n'], [t('hype.discovery'), 'n'], [t('hype.gap.class'), 'hm'], [t('ui.voices'), 'n hm'], [t('hype.posts'), 'n hm'], [t('hype.platforms'), 'hm']],
      rows: list.map(r => { const it = H.items[r.id], m = it.win?.[F.win] || {}; return { attr: ` class="go" tabindex="0" data-p="${esc(r.id)}"`, cells: [r.rank ?? '—', `<b>${posted(it.name)}</b>`, nf(r.score), nf(it.discovery?.score), esc(t(GAP[r.label] || 'hype.gap.insufficient')), nf(m.voices), nf(m.mentions), `<span class="mono dim">${esc((m.platforms || []).map(nm).join(' · '))}</span>`] }; }) });
    $$('#tbl tr.go').forEach(tr_ => { tr_.onclick = () => open(tr_.dataset.p); tr_.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); open(tr_.dataset.p); } }; });
    onSeg('win', v => { F.win = v; render(); }); semUi();
    $('#area').onchange = e => { F.area = e.target.value; render(); };
    $('#q').oninput = e => { F.q = e.target.value; render(); const n = $('#q'); n.focus(); n.setSelectionRange(n.value.length, n.value.length); };
    if (F.open) detail(F.open);
  };
  render();
}
// ------------------------------------------------------------------ the fold (design row 11, C21): the console's URLs to their dehype pages
// fold:start. The console (web/index.html to 2bc0ace) wrote #pulse/<win>[/table], #papers|#repos|#hype/<win>/<area>, #methodology[/<section>],
// with ?q= (its search) and ?open= (an open item). Pure: tests/fixtures/console_anchors.json lists each form and scripts/check_page.mjs runs
// this function on it. Returns the dehype URL, or null when the URL is no console anchor (the briefing itself).
function fold(hash, search) {
  let h; try { h = decodeURIComponent(String(hash || '').replace(/^#/, '')).split('/'); } catch { h = []; }
  const u = new URLSearchParams(search || ''), q = u.get('q') || '', open = u.get('open') || '', tab = h[0], area = h.slice(2).join('/');
  // the console's query grammar (field comparisons, "over 1k", dates): no longer supported, the page says so and matches the words
  const filters = /[<>]=?\s*\d|\b(?:over|under|above|below|more than|less than|at least)\s+\d|\b\d+(?:\.\d+)?k\b|\b(?:this|last|past)\s+(?:day|week|month|year)\b|\b(?:today|yesterday)\b/i.test(q) && '1';
  const go = (p, o = {}, frag = '') => { const s = new URLSearchParams(Object.entries(o).filter(([, v]) => v)); if (u.get('lang') === 'pt') s.set('lang', 'pt'); return p + (String(s) ? '?' + s : '') + frag; };
  if (tab === 'methodology') return go('method.html', {}, h[1] ? '#' + h[1] : '');
  if (tab === 'papers' || tab === 'repos') {                     // the output page keeps 7, 30 and 90 days: 1d reads 7, 180d, 1y and overall read 90 (from= says so)
    const days = { '30d': '30', '90d': '90', '180d': '90', '1y': '90', overall: '90' }[h[1]];
    return go('output.html', { tab, days, area: area !== 'all' && area, q: q || open, from: ['1d', '180d', '1y', 'overall'].includes(h[1]) && h[1], filters });
  }
  if (tab === 'hype') { const kept = !h[1] || ['1d', '7d', '30d', '90d', 'overall'].includes(h[1]);
    return go('hype.html', { win: kept && h[1], area: area !== 'all' && area, q, from: !kept && h[1], filters }, open ? '#p=' + encodeURIComponent(open) : ''); }
  if (tab === 'pulse' || (!tab && (q || open))) return h[2] === 'table' || q ? go('stories.html', { view: h[2] === 'table' && 'table', q, filters }) : go('index.html');
  return null;
}
// fold:end
// stale:start (tests/dehype_stale.test.mjs runs this block)
// ------------------------------------------------------------------ stale since (C37): the briefing belongs to the America/Sao_Paulo date of
// its generated_at and reads "stale since" that date once 06:00 America/Sao_Paulo of the next date has passed, whatever the hour it was made.
const SPF = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
const spAt = ms => { const p = Object.fromEntries(SPF.formatToParts(ms).map(x => [x.type, x.value])); return { day: `${p.year}-${p.month}-${p.day}`, wall: Date.parse(`${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}:00Z`) }; };
function staleSince(generatedAt, now) {                          // the briefing's date when it is stale at now (ms), else null
  const g = Date.parse(generatedAt); if (!Number.isFinite(g)) return null;
  const d = spAt(g).day, next = new Date(Date.parse(d + 'T12:00:00Z') + DAY).toISOString().slice(0, 10), probe = Date.parse(next + 'T09:00:00Z');
  return now >= Date.parse(next + 'T06:00:00Z') - (spAt(probe).wall - probe) ? d : null;
}
// stale:end
const staleBanner = B => {                                       // "stale since" the briefing's date, and the 06:00 BRT update it missed (the next date)
  if (B.stale?.since)                                            // a failed Pulse step (compose.mjs, C5): its date and reason, whatever the hour
    return `<div class="banner stale" role="status"><p><b>${esc(t('stale.failed', { date: B.stale.since, reason: tr(B.stale.reason) }))}.</b> <span class="sn">${esc(t('stale.failed.note', { date: B.stale.since }))}</span></p></div>`;
  const d = staleSince(B.generated_at, Date.now()), next = d && new Date(Date.parse(d + 'T12:00:00Z') + DAY).toISOString().slice(0, 10);
  return d ? `<div class="banner stale" role="status"><p><b>${esc(t('stale.since', { date: d, deadline: next }))}.</b> <span class="sn">${esc(t('stale.note', { date: d, at: B.window?.end_brt || B.generated_at }))}</span></p></div>` : ''; };
// ------------------------------------------------------------------ search by meaning (the console's semantic search, kept by the fold, C21)
// The model and index of scripts/embed/embed.mjs: search-index.json and search-vectors.bin load on the first query and the query is embedded in
// the browser by transformers.js (pinned, from jsDelivr; the model from Hugging Face), so it never leaves the browser. Nothing downloads until
// the reader selects "Search by meaning" (a folded ?q= URL matches words); until the model is ready, or when it cannot load, every word of the
// query must match. The row count stays on screen either way.
const TF_URL = 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.2.0';
const SEM = { on: false, st: 'idle', pos: {}, cache: new Map(), redo: null };   // off on every load: the download starts only from a click
async function semLoad() {
  if (SEM.st !== 'idle') return; SEM.st = 'loading'; semUi();
  try {
    const [ix, bin] = await Promise.all([load('search-index.json'), load('search-vectors.bin')]);
    if (bin.byteLength !== ix.rows * ix.dim || !ix.revision) throw new Error('search index and vectors disagree');
    const tf = await import(TF_URL);
    SEM.ext = await tf.pipeline('feature-extraction', ix.model, { dtype: ix.dtype, revision: ix.revision, device: 'wasm' });
    SEM.ix = ix; SEM.vec = new Int8Array(bin);
    for (const [tab, v] of Object.entries(ix.tabs)) SEM.pos[tab] = new Map(v.ids.map((id, i) => [id, v.offset + i]));
    SEM.st = 'ready';
  } catch (e) { SEM.st = 'failed'; console.warn('search by meaning unavailable, matching words', e); }
  semUi(); SEM.redo?.();
}
function semVec(q) {
  if (SEM.st !== 'ready') { semLoad(); return null; }
  if (!SEM.cache.has(q)) { SEM.cache.set(q, null); SEM.ext(q, { pooling: 'mean', normalize: true }).then(x => { SEM.cache.set(q, x.data); SEM.redo?.(); }).catch(() => SEM.cache.delete(q)); }
  return SEM.cache.get(q);
}
function search(tab, rows, q, id, text) {                       // the console's rule: keyword hits, or rows within 0.2 of the best match (at least 0.3)
  const terms = q.trim().toLowerCase().split(/\s+/).filter(Boolean); if (!terms.length) return rows;
  const kw = r => { const s = text(r).toLowerCase(); return terms.filter(w => s.includes(w)).length; };
  const v = SEM.on && SEM.st !== 'failed' ? semVec(terms.join(' ')) : null;
  if (!v) return rows.filter(r => kw(r) === terms.length);
  const ix = SEM.ix, sim = r => { const p = SEM.pos[tab]?.get(id(r)); if (p == null) return null; let s = 0; for (let k = 0, o = p * ix.dim; k < ix.dim; k++) s += v[k] * SEM.vec[o + k]; return s / ix.scale; };
  const sc = rows.map(r => ({ r, s: sim(r), k: kw(r) })), best = Math.max(0, ...sc.map(x => x.s ?? 0)), rel = x => (x.s ?? 0) + .06 * x.k;
  return sc.filter(x => x.k === terms.length || (x.s != null && x.s >= Math.max(.3, best - .2))).sort((a, b) => rel(b) - rel(a)).map(x => x.r);
}
const semBtn = () => `<button class="btn sem" id="sem" aria-pressed="${SEM.on}" title="${esc(t('ui.sem.title'))}">${esc(t(!SEM.on ? 'ui.sem.off' : SEM.st === 'loading' ? 'ui.sem.loading' : SEM.st === 'failed' ? 'ui.sem.failed' : 'ui.sem.on'))}</button>`;
function semUi() { const b = $('#sem'); if (!b) return; b.outerHTML = semBtn(); $('#sem').onclick = () => { SEM.on = !SEM.on; semUi(); SEM.redo?.(); }; }
const keepQ = fn => { const a = document.activeElement?.id === 'q'; fn(); const n = $('#q'); if (a && n) { n.focus(); n.setSelectionRange(n.value.length, n.value.length); } };
const qp = k => new URLSearchParams(location.search).get(k) || '';
const foldNote = to => [qp('from') && to && t('fold.window', { from: qp('from'), to }), qp('filters') && t('fold.filters')].filter(Boolean).map(x => `<p class="notice">${esc(x)}</p>`).join('');
// ------------------------------------------------------------------ daily briefing (first screen): the State of AI header, then the Top 10
// briefing:start. At most four gauges, each with its coverage and its "preview, not yet reproducible" status; Risk and Jobs as placeholders;
// no combined score and no trend or arrow (none before 14 ledger days, R2-4): the header shows today's values only.
function gauge(g, body) {                                         // name; the reading (figure left, its small view right); status and coverage last
  return `<article class="g" id="g-${esc(g.id)}"><h3 class="lbl">${esc(tr(g.name))}</h3>
${g.value == null ? `<p class="none">${esc(tr(g.reason) || '—')}</p>` : body}<footer><span class="pill">${esc(tr(g.status))}</span>${sources(g.coverage?.sources, true)}</footer></article>`;
}
const GAUGE = {
  output_by_area: v => {
    const A = [...v.areas].sort((a, b) => b.papers - a.papers), hi = Math.max(1, ...A.map(a => a.papers)), sum = k => A.reduce((n, a) => n + a[k], 0);
    return `<div class="gb"><div><p class="big"><span class="num">${nf(sum('papers'))}</span><span class="u">${esc(t('brief.out.papers'))}</span></p>
<p class="sub">${esc(t('brief.out.sub', { r: nf(sum('repos')), date: '\u0000' })).replace('\u0000', `<span class="nw">${esc(v.since)}</span>`)} <a href="${href('output')}">${esc(t('brief.out.go'))}</a></p></div>
<ul class="hb" aria-label="${esc(t('brief.out.mini'))}">${A.map(a => `<li title="${esc(nm(a.area))}: ${nf(a.papers)} · ${nf(a.repos)}"><span>${esc(nm(a.area))}</span><i style="--w:${(a.papers / hi * 100).toFixed(1)}%"></i><b class="mono">${nf(a.papers)}</b></li>`).join('')}</ul></div>`;
  },
  hype_vs_substance: v => {                                      // no story known either way: the count of unknowns leads (never an invented 0)
    const S = v.stories || [], has = x => x.substance?.official === true || x.substance?.repos > 0 || x.substance?.papers > 0;
    const unk = S.filter(x => !has(x) && x.substance?.official === NOT_FETCHED).length, hi = Math.max(1, ...S.map(x => x.hype?.voices || 0));
    if (unk === S.length) return `<p class="big"><span class="num">${nf(unk)}</span><span class="u">${esc(t('brief.hvs.none', { n: S.length }))}</span></p><p class="sub">${esc(t('brief.hvs.sub'))}</p>`;
    return `<div class="gb"><div><p class="big"><span class="num">${nf(S.filter(has).length)}</span><span class="u">${esc(t('brief.hvs.of', { n: S.length }))}</span></p>
<p class="sub">${esc(t('brief.hvs.sub'))}${unk ? ' ' + esc(tn('brief.hvs.unknown', unk)) : ''}</p></div>
<div><div class="strip" aria-label="${esc(t('brief.hvs.mini'))}">${S.map((x, i) => `<a href="#${esc(x.id)}" aria-label="${esc(t('brief.hvs.col', { rank: i + 1, n: nf(x.hype?.voices) }))}${has(x) ? ', ' + esc(t('brief.hvs.has')) : ''}"><i style="--h:${((x.hype?.voices || 0) / hi * 100).toFixed(1)}%"></i><em class="${has(x) ? 'y' : ''}"></em><span class="mono">${i + 1}</span></a>`).join('')}</div>
<p class="key"><span><i class="kv"></i>${esc(t('ui.voices'))}</span><span><i class="ks"></i>${esc(t('brief.hvs.has'))}</span></p></div></div>`;
  },
  daily_movers: v => {
    const li = x => `<li title="${esc(t('brief.mv.posts', { d: nf(x.posts_1d), w: nf(x.posts_7d) }))}"><span>${posted(x.label, 'und')}</span><b class="mono">${nf(x.rising)}×</b></li>`, lead = (v.up || [])[0];
    return `<div class="gb"><div>${lead ? `<p class="big"><span class="num">${nf(lead.rising)}×</span><span class="u">${posted(lead.label, 'und')}</span></p>` : ''}<p class="sub">${esc(t('brief.mv.sub'))}</p></div>
<div class="mv"><p class="mini-t">${esc(t('brief.mv.up'))}</p><ul>${(v.up || []).slice(0, 2).map(li).join('')}</ul><p class="mini-t">${esc(t('brief.mv.down'))}</p><ul>${(v.down || []).slice(0, 2).map(li).join('')}</ul></div></div>`;
  }
};
function aliases(A) {                                            // story-aliases.json: an earlier id to the story that took its posts (check_page.mjs resolve)
  const M = A?.aliases || {};
  return id => { const seen = [id]; while (M[seen.at(-1)]?.to && !seen.includes(M[seen.at(-1)].to)) seen.push(M[seen.at(-1)].to); return seen.at(-1); };
}
const verdicts = (V, A) => { const to = aliases(A), m = new Map(); for (const r of V.rows || []) { m.set(to(r.id), r); if (!m.has(r.id)) m.set(r.id, r); } return m; };
async function index() {
  const [B, P, V, AL] = await Promise.all([load('briefing.json'), load('pulse.json'), opt('verdicts.json', { rows: [] }), opt('story-aliases.json', { aliases: {} })]);
  const by = new Map((P.stories || []).map(s => [s.id, s])), ver = verdicts(V, AL), now = Date.parse(B.generated_at);
  const recs = new Map((B.records || []).map(r => [r.id, r])), G = (B.gauges || []).slice(0, 4), anchor = I.methods?.['briefing.json']?.['method.top10'] || '';
  render = () => {
    $('#when').innerHTML = `${esc(t('brief.window', { end: B.window?.end_brt || B.generated_at }))} · <span class="dim">${esc(t('brief.made', { ago: ago(B.generated_at, Date.now()) }))}</span>`;
    $('#stale').innerHTML = staleBanner(B);
    $('#body').innerHTML = `<section class="soai" aria-labelledby="soai-h"><div class="soai-h"><h2 id="soai-h">${esc(t('soai.title'))}</h2><span class="mono">${esc(t('soai.line', { days: nf(B.ledger_days ?? 0) }))}</span></div>
<div class="gauges">${G.map(g => gauge(g, GAUGE[g.id] && g.value != null ? GAUGE[g.id](g.value) : '')).join('')}
<div class="panels">${(B.panels || []).map(p => `<p class="pn"><span class="lbl">${esc(tr(p.name))}</span> <span class="none">${(p.events || []).length ? p.events.map(e => `<span class="mono">${esc(e.date || '')}</span> ${link(e.url, esc(e.text || e.title || ''))}`).join(' · ') : esc(tr(p.reading))}</span>${p.form && p.form !== 'panel' ? ` <span class="dim">· ${esc(tr(p.form))}</span>` : ''}</p>`).join('')}</div></div><div class="dots" aria-hidden="true">${[...G, 0].map((_, i) => `<i${i ? '' : ' class="on"'}></i>`).join('')}</div></section>
<section class="top" aria-labelledby="top-h"><div class="sec-h"><h2 id="top-h">${esc(t('brief.top.title'))}</h2><p>${esc(t('brief.top.rule'))} <a href="${METHOD()}#${esc(anchor)}">${esc(t('ui.method'))}</a></p><a class="go" href="${href('stories')}">${esc(t('brief.top.all', { n: nf(recs.size) }))}</a></div>
<ol class="stories brief">${(B.top10 || []).map(x => recs.get(x.id)).filter(Boolean).map((r, i) => evidence(r, by.get(r.id), ver.get(r.id), i, now, true)).join('') || `<li class="dim">${esc(t('ui.none'))}</li>`}</ol></section>`;
    const strip = $('.gauges'), dots = $$('.dots i');                // narrow screens: the gauge strip scrolls; the dots show which card is in view
    strip.onscroll = () => { const w = strip.firstElementChild.getBoundingClientRect().width + 10, k = Math.round(strip.scrollLeft / w); dots.forEach((d, i) => d.classList.toggle('on', i === k)); };
  };
  render();
}
// briefing:end
// ------------------------------------------------------------------ method and policy: the web/ copies of the root sources, as written
// The English headings take the console's slug (old #methodology/<section> links land on the same id); a heading under <a id="x"></a>
// takes x, and a Portuguese heading takes only that (no slug of Portuguese text), so both languages share every anchor.
const SLUG = s => s.toLowerCase().replace(/<[^>]+>/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const mhref = (doc, l) => 'method.html' + ((doc === 'policy' || l === 'pt') ? '?' + [doc === 'policy' && 'doc=policy', l === 'pt' && 'lang=pt'].filter(Boolean).join('&') : '');
function inl(s) {
  return esc(s).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/(^|[\s(])\*([^*\s][^*]*?)\*(?=[\s).,;:]|$)/g, '$1<i>$2</i>')
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (m, x, u) => {
      u = u.replace(/&amp;/g, '&'); const [f, frag] = u.split('#'), d = /^METHODOLOGY(\.pt)?\.md$/.test(f) ? 'method' : /^POLICY(\.pt)?\.md$/.test(f) ? 'policy' : null;
      const h = !f ? '#' + frag : d ? mhref(d, /\.pt\.md$/.test(f) ? 'pt' : 'en') + (frag ? '#' + frag : '') : /^https?:/.test(u) ? u : REPO + u;
      return `<a href="${esc(h)}"${/^https?:/.test(h) ? ' target="_blank" rel="noopener"' : ''}>${x}</a>`;
    });
}
function md2html(src, slugs) {                                   // slugs: English text may take a slug id; toc: the level-2 headings
  const L = src.replace(/\r/g, '').split('\n'), LI = /^\s*([-*]|\d+\.)\s+/, A = /^<a id="([^"]+)"><\/a>$/, toc = [];
  let h = '', i = 0, pend = null;
  while (i < L.length) {
    const l = L[i], a = l.match(A);
    if (a) { pend = a[1]; i++; continue; }
    if (/^```/.test(l)) { const c = []; i++; while (i < L.length && !/^```/.test(L[i])) c.push(L[i++]); i++; h += `<pre><code>${esc(c.join('\n'))}</code></pre>`; continue; }
    const m = l.match(/^(#{1,4})\s+(.*)/);
    if (m) { const id = pend || (slugs ? SLUG(m[2]) : ''), n = m[1].length; pend = null; if (n === 2) toc.push([id, m[2]]); h += `<h${n}${id ? ` id="${esc(id)}"` : ''}>${inl(m[2])}</h${n}>`; i++; continue; }
    pend = null;
    if (/^\s*\|/.test(l)) { const rows = []; while (i < L.length && /^\s*\|/.test(L[i])) rows.push(L[i++]); const cells = r => r.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim());
      h += `<div class="tw"><table class="t"><thead><tr>${cells(rows[0]).map(c => `<th scope="col">${inl(c)}</th>`).join('')}</tr></thead><tbody>${rows.slice(2).map(r => `<tr>${cells(r).map(c => `<td>${inl(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`; continue; }
    if (LI.test(l)) { const ol = /^\s*\d+\./.test(l), it = []; while (i < L.length && (LI.test(L[i]) || (/^\s{2,}\S/.test(L[i]) && it.length))) { if (LI.test(L[i])) it.push(L[i].replace(LI, '')); else it[it.length - 1] += ' ' + L[i].trim(); i++; }
      h += `<${ol ? 'ol' : 'ul'}>${it.map(x => `<li>${inl(x)}</li>`).join('')}</${ol ? 'ol' : 'ul'}>`; continue; }
    if (/^>\s?/.test(l)) { const q = []; while (i < L.length && /^>\s?/.test(L[i])) q.push(L[i++].replace(/^>\s?/, '')); h += `<blockquote>${inl(q.join(' '))}</blockquote>`; continue; }
    if (!l.trim()) { i++; continue; }
    const p = []; while (i < L.length && L[i].trim() && !/^(#{1,4}\s|```|\s*\||>|<a id=)/.test(L[i]) && !LI.test(L[i])) p.push(L[i++]); h += `<p>${inl(p.join(' '))}</p>`;
  }
  return { html: h, toc };
}
async function method() {
  const doc = qp('doc') === 'policy' ? 'policy' : 'method';
  render = async () => {
    const src = await (doc === 'policy' ? (lang === 'pt' ? load('POLICY.pt.md') : load('POLICY.md')) : (lang === 'pt' ? load('METHODOLOGY.pt.md') : load('METHODOLOGY.md')));
    const M = md2html(src, lang === 'en'), file = { method: 'METHODOLOGY', policy: 'POLICY' }[doc] + (lang === 'pt' ? '.pt' : '') + '.md';
    $('#body').innerHTML = `<nav class="seg docs" aria-label="${esc(t('method.docs'))}">${['method', 'policy'].map(d => `<a href="${mhref(d, lang)}"${d === doc ? ' aria-current="page"' : ''}>${esc(t({ method: 'method.doc.method', policy: 'method.doc.policy' }[d]))}</a>`).join('')}</nav>
<div class="doc"><nav class="toc" aria-label="${esc(t('method.toc'))}"><details open><summary class="lbl">${esc(t('method.toc'))}</summary>${M.toc.map(([id, x]) => id ? `<a href="#${esc(id)}">${inl(x)}</a>` : '').join('')}</details>
<p class="dim">${esc(t('method.source'))} <a href="${esc(file)}"><code class="mono">${esc(file)}</code></a></p></nav><article class="md" lang="${lang === 'pt' ? 'pt-BR' : 'en'}">${M.html}</article></div>`;
    if (matchMedia('(max-width: 760px)').matches) $('.toc details').open = false;
    const go = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (go) { go.classList.add('hl'); go.scrollIntoView({ block: 'start' }); }
  };
  await render();
}
// ------------------------------------------------------------------ audit: what anyone can check today, and the slots the ledger groups fill
// Slots (E1, E2): #ledger (ledger/index.json entries: the SHA256 the ledger records for each day's manifest beside the SHA256 of the asset
// on its dated Release, read back by the refresh), #attestation (Sigstore attestation of the day's manifest, made by its own job: the page
// shows how to check the latest), #timestamp (OpenTimestamps proof, "pending" until a ledger entry records its Bitcoin block, then
// "anchored"; the page shows how to run `ots verify` on it). Until a file exists its slot reads "not yet published".
// ots:start (tests/test_ots.py runs this block)
function proofStates(E) {                                        // date -> {block, time, by}: a date reads "anchored" only once a ledger entry
  const m = new Map();                                           // records its block (the entry of the run that found it, by), else "pending"
  for (const e of E) for (const a of Array.isArray(e?.anchored) ? e.anchored : [])
    if (a && typeof a.date === 'string' && Number.isInteger(a.block) && a.block > 0 && !m.has(a.date)) m.set(a.date, { block: a.block, time: a.time, by: e.date });
  return m;
}
// ots:end
async function audit() {
  const [B, V, C, R] = await Promise.all([load('briefing.json'), opt('verdicts.json', { rows: [] }), opt('corrections.json', { entries: [] }), opt('removals.json', { entries: [] })]);
  const L = await opt('ledger/index.json', null);                  // ledger_days counts the days before the briefing: today's entry may be new
  const E = Array.isArray(L) ? L : L?.entries || [], last = E.at(-1), S = proofStates(E), proven = [...E].reverse().find(e => S.has(e.date)) || last, kv = (k, v) => `<div><span class="lbl">${esc(k)}</span><span class="mono">${v}</span></div>`, none = `<span class="pill">${esc(t('audit.pending'))}</span>`;
  render = () => {
    $('#body').innerHTML = `${staleBanner(B)}<section class="card"><div class="card-h"><div><h2>${esc(t('audit.today'))}</h2><p>${esc(t('audit.today.sub'))}</p></div></div>
<div class="kvs">${kv(t('audit.generated'), esc(B.window?.end_brt || B.generated_at))}${kv(t('audit.version'), esc(B.method?.version))}${kv(t('audit.hash'), esc(B.method?.config_hash))}${kv(t('audit.days'), esc(t('audit.days.n', { n: nf(B.ledger_days ?? 0) })))}${kv(t('audit.records'), nf((B.records || []).length))}</div>
<p class="dim">${esc(t('audit.hash.note', { files: (B.method?.config_files || []).join(', ') }))} <a href="${METHOD()}#${esc(I.methods?.['briefing.json']?.['method.records'] || '')}">${esc(t('ui.method'))}</a></p></section>
<section class="card slot-a" id="ledger" data-slot="ledger"><div class="card-h"><div><h2>${esc(t('audit.ledger'))}</h2><p>${esc(t('audit.ledger.sub'))}</p></div></div>
${E.length ? `<div class="tw">${table({ cols: [[t('audit.col.date')], [t('audit.col.manifest')], [t('audit.col.release')], [t('audit.col.proof')]], rows: E.map(e => ({ cells: [esc(e.date || '—'),
  `<span class="mono">${esc(e.manifest_sha256 || '—')}</span>`, e.release?.sha256 ? `${link(e.release.url, `<span class="mono">${esc(e.release.sha256)}</span>`)} <span class="pill">${esc(t(e.release.sha256 === e.manifest_sha256 ? 'audit.match' : 'audit.mismatch'))}</span>` : none,
  e.ots?.file ? `${S.has(e.date) ? `${esc(t('audit.anchored', { n: S.get(e.date).block }))} <span class="dim">${esc(t('audit.anchored.by', { date: S.get(e.date).by }))}</span>` : esc(t('audit.pending_proof'))} <a class="mono" href="ledger/${esc(e.ots.file)}">.ots</a>` : none] })) })}</div>` : `<p>${none} ${esc(t('audit.ledger.none'))}</p>`}</section>
<section class="card slot-a" id="attestation" data-slot="attestation"><div class="card-h"><div><h2>${esc(t('audit.attest'))}</h2><p>${esc(t('audit.attest.sub'))}</p></div></div>${last?.release?.url ? `<p>${esc(t('audit.attest.how', { date: last.date }))}</p>
<p>${link(last.release.url, `<code class="mono">${esc(last.asset)}</code>`)}</p><pre class="mono">gh attestation verify ${esc(last.asset)} --repo ${esc(ATTEST_REPO)}</pre>` : `<p>${none}</p>`}</section>
<section class="card slot-a" id="timestamp" data-slot="timestamp"><div class="card-h"><div><h2>${esc(t('audit.ots'))}</h2><p>${esc(t('audit.ots.sub'))}</p></div></div>${proven?.ots?.file ? `<p>${esc(t('audit.ots.how', { date: proven.date }))}</p>
<p>${proven.release?.url ? link(proven.release.url, `<code class="mono">${esc(proven.asset)}</code>`) : `<code class="mono">${esc(proven.asset)}</code>`} · <a class="mono" href="ledger/${esc(proven.ots.file)}">${esc(proven.date)}.ots</a> · ${esc(S.has(proven.date) ? t('audit.anchored', { n: S.get(proven.date).block }) : t('audit.pending_proof'))}</p>
${S.has(proven.date) ? '' : `<p class="dim">${esc(t('audit.ots.pending'))}</p>`}<p>${esc(t('audit.ots.node'))}</p><pre class="mono">ots verify -f ${esc(proven.asset)} ${esc(proven.date)}.ots</pre>
<p>${esc(t('audit.ots.explorer'))}</p><pre class="mono">npx -p opentimestamps@0.4.9 ots-cli.js verify --ignore-bitcoin-node -f ${esc(proven.asset)} ${esc(proven.date)}.ots</pre>
<p><a href="${METHOD()}#timestamp-proof">${esc(t('ui.method'))}</a></p>` : `<p>${none}</p>`}</section>
<section class="card"><div class="card-h"><div><h2>${esc(t('audit.owner'))}</h2><p>${esc(t('audit.owner.sub'))}</p></div></div>
<div class="kvs">${kv(t('audit.verdicts'), `<a href="verdicts.json">${nf((V.rows || []).length)}</a>`)}${kv(t('audit.corrections'), `<a href="corrections.json">${nf((C.entries || []).length)}</a>`)}${kv(t('audit.removals'), `<a href="removals.json">${nf((R.entries || []).length)}</a>`)}</div>
<p><a href="${POLICY()}">${esc(t('method.doc.policy'))}</a></p></section>`;
  };
  render();
}
// ------------------------------------------------------------------ status: the Sources page. Live rows come from the sources blocks of
// briefing.json, pulse.json and data.json at runtime (a name in more than one file shows once, briefing first); the other groups and the
// roadmap come from the owner-reviewed i18n/sources-plan.json (en and pt text, terms, the gauges a source would feed). A plan row whose
// `live` name a data file reports "not connected" carries that runtime status and leaves the Live group. The record line reads the
// ledger as the audit page does: days = ledger/index.json entries, the latest Release, its attestation and the latest proof state.
const FEEDS = { output_by_area: 'gauge.output_by_area', hype_vs_substance: 'gauge.hype_vs_substance', daily_movers: 'gauge.daily_movers', risk: 'panel.risk', jobs: 'panel.jobs', awareness: 'status.feeds.awareness' };
const GROUPS = { ready: 'status.group.ready', pending: 'status.group.pending', held: 'status.group.held', free: 'status.group.free' };
const STATES = { done: 'status.state.done', next: 'status.state.next', planned: 'status.state.planned' };
const SEV = { failed: 0, partial: 1, 'not connected': 2, ok: 4 };
const stCell = s => `<span class="st ${{ ok: 'ok', partial: 'partial', failed: 'bad' }[s] || 'nf'}"><b aria-hidden="true">${{ ok: '●', partial: '◐', failed: '✕' }[s] || '○'}</b> ${esc(tr(s ?? 'unknown'))}</span>`;
async function status() {
  const [P, L, B, U, D] = await Promise.all([load('i18n/sources-plan.json'), opt('ledger/index.json', null), opt('briefing.json', null), opt('pulse.json', null), opt('data.json', null)]);
  const read = [['briefing.json', B], ['pulse.json', U], ['data.json', D]], live = new Map();
  for (const [f, d] of read) for (const [n, s] of Object.entries(d?.sources || {})) {
    if (live.has(n)) { live.get(n).files.push([f, d.generated_at]); continue; }
    live.set(n, { status: typeof s === 'string' ? s : s?.status, detail: s?.detail, files: [[f, d.generated_at]] });
  }
  const plan = (P.sources || []).filter(e => e.group in GROUPS), claimed = new Set(plan.filter(e => live.get(e.live)?.status === 'not connected').map(e => e.live));
  const rows = [...live].filter(([n]) => !claimed.has(n)).sort((a, b) => (SEV[a[1].status] ?? 3) - (SEV[b[1].status] ?? 3));
  const E = Array.isArray(L) ? L : L?.entries || [], last = E.at(-1), S = proofStates(E), proven = [...E].reverse().find(e => S.has(e.date)) || last, days = E.length;
  const none = `<span class="pill">${esc(t('audit.pending'))}</span>`, txt = e => e[lang] || e.en || {};
  const feeds = e => (e.feeds || []).filter(f => f in FEEDS).map(f => esc(t(FEEDS[f]))).join(' · ') || '—';
  render = () => {
    const now = Date.now(), ok = rows.filter(([, s]) => s.status === 'ok').length, by = g => plan.filter(e => e.group === g);
    const rec = [[t('audit.days'), esc(t('audit.days.n', { n: nf(days) }))],
      [t('status.release'), last?.release?.sha256 ? `${link(last.release.url, `<span class="mono">${esc(last.release.tag || last.date)}</span>`)} <span class="pill">${esc(t(last.release.sha256 === last.manifest_sha256 ? 'status.release.match' : 'status.release.mismatch'))}</span>` : none],
      [t('audit.attest'), last?.release?.url ? `<span class="mono">${esc(t('status.attest.check'))}</span>` : none],
      [t('audit.ots'), proven?.ots?.file ? `<span class="mono">${esc(proven.date)}</span> ${esc(S.has(proven.date) ? t('audit.anchored', { n: S.get(proven.date).block }) : t('audit.pending_proof'))}` : none]];
    const head = (k, n, sub) => `<div class="sec-h"><h3>${esc(t(k))} <span class="pill">${esc(tn('status.n', n))}</span></h3><p>${esc(t(sub))}</p></div>`;
    const liveT = table({ stack: true, cols: [[t('status.col.source')], [t('status.col.status'), 'nw'], [t('status.col.detail')], [t('status.col.file'), 'nw']],
      rows: rows.map(([n, s]) => ({ cells: [esc(nm(n)), stCell(s.status), s.detail ? esc(tr(s.detail)) : '—', `${s.files.map(([f]) => `<code class="mono">${esc(f)}</code>`).join(', ')}<br><span class="dim">${esc(ago(s.files[0][1], now))}</span>`] })) });
    const planT = list => table({ stack: true, cols: [[t('status.col.source')], [t('status.col.what')], [t('status.col.terms')], [t('status.col.feeds')]],
      rows: list.map(e => { const x = txt(e), r = claimed.has(e.live) && live.get(e.live);
        return { cells: [`<b>${esc(e.name)}</b>${r ? `<br><span class="dim">${esc(t('status.reported'))}</span> ${stCell(r.status)}${r.detail ? ` <span class="dim">· ${esc(tr(r.detail))}</span>` : ''}` : ''}`, esc(x.what), `<span class="dim">${esc(x.terms)}</span>`, feeds(e)] }; }) });
    $('#body').innerHTML = `${B ? staleBanner(B) : ''}${read.filter(([, d]) => !d).map(([f]) => `<p class="notice">${esc(t('status.unread', { file: f }))}</p>`).join('')}
${kpis([[t('status.group.live'), nf(rows.length), esc(t('ui.sources_ok', { n: ok, total: rows.length }))], ...Object.entries(GROUPS).map(([g, k]) => [t(k), nf(by(g).length)])]).replace('class="kpis"', 'class="kpis k5"')}
<section class="card aline" id="record" aria-label="${esc(t('status.record'))}">${rec.map(([k, v]) => `<p><span class="lbl">${esc(k)}</span> ${v}</p>`).join('')}<p class="go"><a href="${href('audit')}">${esc(t('status.audit.more'))}</a></p></section>
<section class="card" id="sources"><div class="card-h"><div><h2>${esc(t('status.sources'))}</h2><p>${esc(t('status.sources.sub'))}</p></div></div>
<div class="grp" id="g-live">${head('status.group.live', rows.length, 'status.group.live.sub')}<div class="tw">${liveT}</div></div>
${Object.entries(GROUPS).map(([g, k]) => `<div class="grp plan" id="g-${g}">${head(k, by(g).length, k + '.sub')}<div class="tw">${planT(by(g))}</div></div>`).join('')}</section>
<section class="card" id="roadmap"><div class="card-h"><div><h2>${esc(t('status.roadmap'))}</h2><p>${esc(t('status.roadmap.sub'))}</p></div></div>
<ol class="rm">${(P.roadmap || []).map(r => { const x = txt(r), st = r.state in STATES ? r.state : 'planned';
  return `<li class="rm-${st}"><span class="mono id" aria-hidden="${/^[SG]\d$/.test(r.id) ? 'false' : 'true'}">${esc(/^[SG]\d$/.test(r.id) ? r.id : '→')}</span><div><h3>${esc(x.name)} <span class="pill${st === 'next' ? ' v' : ''}">${esc(t(STATES[st]))}</span></h3><p>${esc(x.what)}</p>${r.id === 'S1'
    ? `<div class="clock" aria-hidden="true">${Array.from({ length: 14 }, (_, i) => `<i${i < days ? ' class="on"' : ''}></i>`).join('')}</div><p class="dim mono">${esc(t('status.clock', { n: nf(days) }))}</p>` : ''}</div></li>`; }).join('')}</ol></section>`;
  };
  render();
}
// ------------------------------------------------------------------ start
const oops = e => { document.documentElement.classList.add('ready'); $('#body').innerHTML = `<div class="err">${esc(t('ui.error'))} <span class="mono">${esc(e.message)}</span></div>`; };
async function start() {
  if (page === 'index') { const to = fold(location.hash, location.search); if (to?.startsWith('index.html')) history.replaceState(null, '', to); else if (to) return location.replace(to); }
  const u = new URLSearchParams(location.search);
  lang = ['en', 'pt'].includes(u.get('lang')) ? u.get('lang') : store.get('dehype.lang') === 'pt' ? 'pt' : 'en';
  theme = store.get('dehype.theme') === 'light' ? 'light' : 'dark';
  try {
    I = await load(TABLE[lang]);
    DATA_KEYS = [...new Set(Object.values(I.fields || {}).flatMap(p => Object.values(p).flatMap(s => Array.isArray(s) ? s : s.keys || [])))];
    shell();
    $('#main').classList.add('loading');
    await ({ index, stories, output, hype, method, audit, status })[page]();
  } catch (e) { oops(e); }
  $('#main').classList.remove('loading');
}
start();
return { t, tr, load, evidence, verdictSlot, sources, kpis, card, table, scatter, hbars, dumbbell, METHOD, fold, staleSince, md2html };
})();
