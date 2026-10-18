// One-shot Cordis composition (design row 16; C14, C18; Decisions 9, 16): run with no arguments from the repository root, after pulse.py.
// It creates a Cordis context, loads the feed and frontend adapter plugins with the committed web/ files as their config, collects what
// they emit, disposes them and the context, and only then writes web/feed.xml, web/feed.json, web/feed.pt.xml, web/feed.pt.json and
// web/i18n/table.{en,pt}.json (each through a temporary file and a rename). Only the qualified component API is used (new Context(),
// ctx.plugin, ctx.effect, and fiber.dispose on each plugin's fiber); git is the store: nothing is read or written outside web/, and no state outlives the run.
// No server, socket, profile, credential or home directory; no DSH launcher, WISH Run, task, worker or dispatch; no claim of WISH #4
// acceptance. @deepseek-ai/cordis is pinned exactly to 4.0.4 (package-lock.json; MIT, see NOTICE and licence-closure.json).
import { Context } from '@deepseek-ai/cordis';
import { createRequire } from 'node:module';
import { renameSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import feed, { readInputs as feedInputs } from './plugins/feed.mjs';
import frontend, { readInputs as frontendInputs } from './plugins/frontend.mjs';

const PIN = '4.0.4', WEB = 'web', t0 = performance.now();
const version = createRequire(import.meta.url)('@deepseek-ai/cordis/package.json').version;
if (version !== PIN) { console.error(`compose: @deepseek-ai/cordis ${version} installed, ${PIN} required (npm ci --prefix scripts/dehype)`); process.exit(1); }

const out = new Map();
const emit = (f, text) => { if (out.has(f)) throw new Error(`compose: two plugins write ${f}`); out.set(f, text); };
const root = new Context();
const fibers = [];
fibers.push(await root.plugin(feed, { inputs: feedInputs(WEB), emit }));
fibers.push(await root.plugin(frontend, { inputs: frontendInputs(WEB), emit }));
for (const f of fibers.reverse()) await f.dispose();

for (const [f, text] of out) writeFileSync(join(WEB, f + '.tmp'), text);
for (const f of out.keys()) renameSync(join(WEB, f + '.tmp'), join(WEB, f));
const open = process.getActiveResourcesInfo().filter(r => /TCP|UDP|Pipe(?!Wrap$)|Server|HTTP|DNS|GetAddrInfo|Timeout|Interval|FSWatcher|Process/i.test(r));
if (open.length) { console.error(`compose: resources left open after dispose: ${open.join(', ')}`); process.exit(1); }
console.log(`compose: @deepseek-ai/cordis ${version}, plugins ${feed.name} and ${frontend.name} loaded and disposed; wrote ${[...out.keys()].map(f => 'web/' + f).join(', ')}; `
  + `no server, socket or timer left open; ${Math.round(performance.now() - t0)} ms`);
