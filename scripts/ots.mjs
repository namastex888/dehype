#!/usr/bin/env node
// OpenTimestamps proof of each day's manifest, its upgrade loop and the anchored state (design row 18, proof part; C4, C38; group E2).
// The client is the JavaScript `opentimestamps` package pinned exactly to 0.4.9 (LGPL-3.0) in scripts/checks/package-lock.json, installed
// unmodified by `npm ci --prefix scripts/checks --ignore-scripts` and called through its own API (the calls ots-cli.js makes); see
// scripts/checks/NOTICE.
//
// Run:   node scripts/ots.mjs stamp [--web web] [--date D] [--calendar URL ...]
//          refresh.yml, after the manifest step and before the Release step: stamps the day's manifest_sha256 (the SHA256 of the
//          Release asset) into web/ledger/ots/<date>.ots and records it as that entry's `ots`. A same-date rerun keeps a proof that
//          already commits to the same manifest (no calendar call); a proof that commits to another manifest is replaced only while no
//          ledger entry records it anchored. Exit 1 when no calendar answers: the day then gets no ledger entry (refresh.yml drops it).
//        node scripts/ots.mjs upgrade [--web web] [--date D] [--budget SECONDS] [--calendar URL ...] [--esplora URL] [--timeout MS]
//          refresh.yml step "OpenTimestamps upgrade and verify", after the Release step: runs `upgrade` on every proof of an earlier date
//          that no ledger entry records anchored yet, commits the upgraded file in place, and for each complete one runs `verify --ignore-bitcoin-node` (the
//          block header from the public Esplora explorer, https://blockstream.info/api by default, assumed valid); each proof it accepts
//          is recorded in the <date> entry's `anchored` list as {date, block, time, ots_sha256}. Earlier entries are never edited, and a
//          proof recorded anchored is never touched again. A calendar or explorer that does not answer leaves the proof pending (exit 0).
//          --budget stops the loop once that many seconds have passed and saves the records gathered so far; the rest wait for the next run.
//        node scripts/ots.mjs info <file.ots>      the proof's digest, pending calendars and Bitcoin block heights (no network)
// <date> defaults to the last ledger entry's. --calendar replaces the calendars (the client's -c), --esplora the explorer. Every client
// call (one calendar submission, one proof's upgrade, one verify) races a deadline (--deadline, 45 s): the 0.4.9 client sets no timeout
// on calendar requests, so a calendar that accepts and never answers would otherwise hold the step until its cap. A leftover *.tmp in
// web/ledger/ots/ (a write cut short) is removed first.
import { readFileSync, writeFileSync, renameSync, mkdirSync, existsSync, readdirSync, rmSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';

const sha = b => createHash('sha256').update(b).digest('hex');
const HEX64 = /^[0-9a-f]{64}$/;
let OTS = null;
function client() {                                              // scripts/checks/node_modules/opentimestamps (index.js: its main field names a missing file)
  if (!OTS) {
    const require = createRequire(new URL('./checks/package.json', import.meta.url));
    if (require('opentimestamps/package.json').version !== '0.4.9') throw new Error('opentimestamps is not the pinned 0.4.9 (npm ci --prefix scripts/checks)');
    OTS = require('opentimestamps/index.js');
  }
  return OTS;
}

function args(argv) {
  const o = { web: 'web', date: null, calendar: [], esplora: null, timeout: 15000, deadline: 45, budget: Infinity, _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--calendar') o.calendar.push(argv[++i]);
    else if (['--web', '--date', '--esplora', '--timeout', '--deadline', '--budget'].includes(a)) o[a.slice(2)] = argv[++i];
    else o._.push(a);
  }
  for (const k of ['timeout', 'deadline', 'budget']) { o[k] = Number(o[k]); if (!(o[k] >= 0)) throw new Error(`--${k} is not a number of ${k === 'timeout' ? 'ms' : 'seconds'}`); }
  return o;
}
function within(promise, seconds, what) {                        // the call's result, or a rejection once its deadline passes
  let timer;
  return Promise.race([promise, new Promise((_, reject) => { timer = setTimeout(() => reject(new Error(`${what}: no answer within ${seconds} s`)), seconds * 1000); })])
    .finally(() => clearTimeout(timer));
}
function sweep(web) {                                            // a *.tmp left in web/ledger/ots/ by a write cut short
  const dir = join(web, 'ledger', 'ots');
  for (const f of existsSync(dir) ? readdirSync(dir) : []) if (f.endsWith('.tmp')) { rmSync(join(dir, f)); console.log(`ots: removed the leftover ledger/ots/${f}`); }
}

function ledger(web) {
  const path = join(web, 'ledger', 'index.json'), L = JSON.parse(readFileSync(path, 'utf8')), E = Array.isArray(L) ? L : L?.entries;
  if (!Array.isArray(E)) throw new Error(`${path} is not a list of day entries`);
  return { path, E, save: () => put(path, JSON.stringify(Array.isArray(L) ? E : { ...L, entries: E })) };   // one line, as manifest.py writes it
}
function put(path, data) { mkdirSync(dirname(path), { recursive: true }); writeFileSync(path + '.tmp', data); renameSync(path + '.tmp', path); }
const anchoredDates = E => new Set(E.flatMap(e => (e.anchored || []).map(a => a.date)));

const info = bytes => describe(client().DetachedTimestampFile.deserialize(Uint8Array.from(bytes)));
function describe(d) {                                           // -> {d, digest, complete, pending: [calendar URIs], blocks: [heights]}
  const { Notary, Utils } = client(), pending = [], blocks = [];
  for (const a of d.timestamp.allAttestations().values()) {          // a Map of msg -> attestation
    if (a instanceof Notary.PendingAttestation) pending.push(a.uri);
    else if (a instanceof Notary.BitcoinBlockHeaderAttestation) blocks.push(a.height);
  }
  return { d, digest: Utils.bytesToHex(d.fileDigest()), op: d.fileHashOp._HASHLIB_NAME(), complete: d.timestamp.isTimestampComplete(),
    pending: [...new Set(pending)].sort(), blocks: [...new Set(blocks)].sort((x, y) => x - y) };
}
const bytesOf = d => Buffer.from(d.serializeToBytes());
const verifyCmd = (date, digest) => `node scripts/checks/node_modules/opentimestamps/ots-cli.js verify --ignore-bitcoin-node -d ${digest} web/ledger/ots/${date}.ots`;

async function stamp(o) {
  const { E, save } = ledger(o.web), date = o.date || E.at(-1)?.date, e = E.find(x => x.date === date);
  if (!e) throw new Error(`no ledger entry for ${date}`);
  if (!HEX64.test(e.manifest_sha256 || '')) throw new Error(`the ${date} entry has no manifest_sha256`);
  const file = join(o.web, 'ledger', 'ots', `${date}.ots`);
  if (existsSync(file)) {
    const p = info(readFileSync(file));
    if (p.digest === e.manifest_sha256) {
      if (e.ots?.file !== `ots/${date}.ots`) { e.ots = { file: `ots/${date}.ots`, sha256: sha(readFileSync(file)) }; save(); }   // ots.sha256: at stamp time
      return console.log(`ots ${date}: kept web/ledger/ots/${date}.ots, it already commits to manifest ${e.manifest_sha256} (no calendar call)`);
    }
    if (anchoredDates(E).has(date)) throw new Error(`web/ledger/ots/${date}.ots is recorded anchored for manifest ${p.digest}; it is never replaced`);
    console.log(`ots ${date}: the proof commits to ${p.digest}, not this run's manifest ${e.manifest_sha256}; stamping again (unpublished Release)`);
  }
  // OpenTimestamps.stamp (makeMerkleTree, then createTimestamp) with a deadline per calendar: it would wait for every calendar at once
  const C = client(), d = C.DetachedTimestampFile.fromHash(new C.Ops.OpSHA256(), C.Utils.hexToBytes(e.manifest_sha256));
  const tip = C.makeMerkleTree([d]), calendars = o.calendar.length ? o.calendar : C.Calendar.DEFAULT_AGGREGATORS;  // default aggregators unless --calendar
  const answers = await Promise.all(calendars.map(url => { console.log(`Submitting to remote calendar ${url}`);
    return within(new C.Calendar.RemoteCalendar(url).submit(tip.msg), o.deadline, url).catch(err => { console.log(`ots: calendar ${err.message}`); return null; }); }));
  for (const t of answers) if (t) tip.merge(t);
  if (!describe(d).pending.length) throw new Error('no calendar answered: no OpenTimestamps proof today');
  const b = bytesOf(d), p = info(b);
  put(file, b);
  e.ots = { file: `ots/${date}.ots`, sha256: sha(b) }; save();
  console.log(`ots ${date}: stamped manifest ${e.manifest_sha256} -> web/ledger/ots/${date}.ots (sha256 ${sha(b)}), pending at ${p.pending.join(', ')}`);
}

async function upgrade(o) {
  const C = client(), { E, save } = ledger(o.web), date = o.date || E.at(-1)?.date, e = E.find(x => x.date === date);
  if (!e) throw new Error(`no ledger entry for ${date}`);
  const done = anchoredDates(E), opts = { ...(o.calendar.length ? { calendars: o.calendar } : {}) }, records = [];
  const todo = E.filter(x => x.date < date && x.ots && !done.has(x.date));   // a later run upgrades: never the day it stamps
  const start = Date.now(), left = () => o.budget - (Date.now() - start) / 1000;
  let checked = 0;
  for (const x of todo) {
    if (left() <= 0) { console.log(`ots upgrade: the ${o.budget} s budget is spent; ${todo.length - checked} proofs wait for the next run`); break; }
    checked++;
    const file = join(o.web, 'ledger', 'ots', `${x.date}.ots`), cap = () => Math.max(0.001, Math.min(o.deadline, left()));
    try {
      const before = readFileSync(file), p = info(before);
      if (p.digest !== x.manifest_sha256) { console.log(`::warning::ots ${x.date}: the proof commits to ${p.digest}, not the entry's manifest; left as it is`); continue; }
      await within(C.upgrade(p.d, opts), cap(), `upgrade of ${x.date}`);    // `upgrade`: asks each pending calendar for its Bitcoin path
      let b = bytesOf(p.d);
      if (!p.d.timestamp.isTimestampComplete()) {
        if (!b.equals(before)) put(file, b);
        console.log(`ots ${x.date}: pending (${info(b).pending.join(', ')})`); continue;
      }
      const original = C.DetachedTimestampFile.fromHash(new C.Ops.OpSHA256(), C.Utils.hexToBytes(x.manifest_sha256));
      const r = await within(C.verify(p.d, original, { ...opts, ignoreBitcoinNode: true, timeout: o.timeout, ...(o.esplora ? { url: o.esplora } : {}) }), cap(), `verify of ${x.date}`);
      b = bytesOf(p.d);                                          // verify upgrades again before it checks: keep what it checked
      if (!b.equals(before)) put(file, b);
      const btc = r?.bitcoin;
      if (!btc || !info(b).blocks.includes(btc.height)) { console.log(`::warning::ots ${x.date}: complete, but verify --ignore-bitcoin-node accepted no Bitcoin block; left pending`); continue; }
      records.push({ date: x.date, block: btc.height, time: new Date(btc.timestamp * 1000).toISOString().replace('.000Z', 'Z'), ots_sha256: sha(b) });
      console.log(`ots ${x.date}: anchored, Bitcoin block ${btc.height} (${records.at(-1).time}); check: ${verifyCmd(x.date, x.manifest_sha256)}`);
    } catch (err) { console.log(`::warning::ots ${x.date}: ${err.message}; left pending`); }
  }
  if (records.length) { e.anchored = [...(e.anchored || []), ...records].sort((a, b) => a.date.localeCompare(b.date)); save(); }
  console.log(`ots upgrade: ${checked} pending proofs checked, ${records.length} anchored and recorded in the ${date} entry, ${done.size} recorded before`);
}

try {
  const o = args(process.argv.slice(2)), cmd = o._.shift();
  if (cmd === 'stamp' || cmd === 'upgrade') sweep(o.web);
  if (cmd === 'stamp') await stamp(o);
  else if (cmd === 'upgrade') await upgrade(o);
  else if (cmd === 'info' && o._[0]) { const { d, ...p } = info(readFileSync(o._[0])); console.log(JSON.stringify(p)); }
  else { console.error('usage: node scripts/ots.mjs stamp|upgrade [--web web] [--date D] [--budget S] [--deadline S] [--calendar URL ...] [--esplora URL] [--timeout MS] | info <file.ots>'); process.exit(2); }
} catch (err) { console.error(`ots: ${err.message}`); process.exit(1); }
process.exit(0);                                                 // a request past its deadline must not keep the step open
