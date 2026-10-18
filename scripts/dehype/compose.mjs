// One-shot Cordis composition (design row 16; C14, C18; Decisions 9, 16): run with no arguments from the repository root, after pulse.py.
// It creates a Cordis context, loads the feed and frontend adapter plugins with the committed web/ files as their config, collects what
// they emit, disposes them and the context, and only then writes web/feed.xml, web/feed.json, web/feed.pt.xml, web/feed.pt.json and
// web/i18n/table.{en,pt}.json (each through a temporary file and a rename). Only the qualified component API is used (new Context(),
// ctx.plugin, ctx.effect, and fiber.dispose on each plugin's fiber); git is the store: nothing is read or written outside web/, and no state outlives the run.
// No server, socket, profile, credential or home directory; no DSH launcher, WISH Run, task, worker or dispatch; no claim of WISH #4
// acceptance. @deepseek-ai/cordis is pinned exactly to 4.0.4 (package-lock.json; MIT, see NOTICE and licence-closure.json).
// Stale since (design row 18, C5; group E1): when the Pulse step failed, refresh.yml restores the committed pulse.json and briefing.json and
// writes web/checks/pulse-failed.json ({"at": <the failed run's time>, "run": <its run id>}; gitignored, never staged). compose.mjs then
// also rewrites web/briefing.json as a stale briefing: it keeps generated_at, window, method, sources and ledger_days, names "stale since"
// its São Paulo date with the reason, and carries no value over (no record, no Top 10, every gauge, context and page-view value null with
// the stale reason, no risk event); the feeds read the same (plugins/feed.mjs). Run again on a stale briefing, it keeps the date and takes the newer run.
import { Context } from '@deepseek-ai/cordis';
import { createRequire } from 'node:module';
import { readFileSync, renameSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import feed, { readInputs as feedInputs } from './plugins/feed.mjs';
import frontend, { readInputs as frontendInputs } from './plugins/frontend.mjs';

const PIN = '4.0.4', WEB = 'web', t0 = performance.now();
const version = createRequire(import.meta.url)('@deepseek-ai/cordis/package.json').version;
if (version !== PIN) { console.error(`compose: @deepseek-ai/cordis ${version} installed, ${PIN} required (npm ci --prefix scripts/dehype)`); process.exit(1); }

const out = new Map();
const emit = (f, text) => { if (out.has(f)) throw new Error(`compose: two plugins write ${f}`); out.set(f, text); };
const fill = (s, v) => s.replace(/\{(\w+)\}/g, (m, k) => k in v ? String(v[k]) : m);
function stale(B, M, S) {
  if (!Number.isFinite(Date.parse(M?.at)) || !/^\w+$/.test(String(M?.run ?? ''))) throw new Error('compose: checks/pulse-failed.json lacks the failed run\'s time (at) or id (run)');
  const since = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(B.generated_at));
  const reason = fill(S['stale.reason.pulse_failed'].en, { run: M.run });
  return { ...B, stale: { since, reason, at: M.at, run: String(M.run) }, top10: [], records: [],
    gauges: (B.gauges || []).map(g => ({ id: g.id, name: g.name, status: g.status, coverage: { sources: {} }, value: null,
      reason: fill(S['gauge.reason.stale'].en, { date: since, detail: reason }), trend: null })),
    panels: (B.panels || []).map(p => {                          // the Risk log empties; every context and page-view value reads null with the stale reason
      const gone = x => ({ ...x, value: null, reason: fill(S['gauge.reason.stale'].en, { date: since, detail: reason }) });
      if (Array.isArray(p.events)) return { ...p, events: [], reading: 'no qualified source' };
      if (Array.isArray(p.context)) return { ...p, context: p.context.map(gone) };
      return 'value' in p ? gone(p) : p;
    }) };
}
let mark = null;
try { mark = JSON.parse(readFileSync(join(WEB, 'checks', 'pulse-failed.json'), 'utf8')); } catch (e) { if (e.code !== 'ENOENT') throw e; }
const inputs = feedInputs(WEB);
if (mark) { inputs.briefing = stale(inputs.briefing, mark, inputs.strings); emit('briefing.json', JSON.stringify(inputs.briefing)); }
const root = new Context();
const fibers = [];
fibers.push(await root.plugin(feed, { inputs, emit }));
fibers.push(await root.plugin(frontend, { inputs: frontendInputs(WEB), emit }));
for (const f of fibers.reverse()) await f.dispose();

for (const [f, text] of out) writeFileSync(join(WEB, f + '.tmp'), text);
for (const f of out.keys()) renameSync(join(WEB, f + '.tmp'), join(WEB, f));
const open = process.getActiveResourcesInfo().filter(r => /TCP|UDP|Pipe(?!Wrap$)|Server|HTTP|DNS|GetAddrInfo|Timeout|Interval|FSWatcher|Process/i.test(r));
if (open.length) { console.error(`compose: resources left open after dispose: ${open.join(', ')}`); process.exit(1); }
console.log(`compose: @deepseek-ai/cordis ${version}, plugins ${feed.name} and ${frontend.name} loaded and disposed; wrote ${[...out.keys()].map(f => 'web/' + f).join(', ')}; `
  + `no server, socket or timer left open; ${Math.round(performance.now() - t0)} ms`);
