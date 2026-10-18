"""OpenTimestamps proof, upgrade loop and anchored state (design row 18, proof part; C4, C38; the E2 part of SC-18; group E2).

Offline: no calendar, explorer or Bitcoin call. The check_page.mjs cases (Decision 14: a scratch copy of web/, failing with that rule's
own finding, or passing) use hand-built proofs (test_manifest.ots_proof) and the real pending proof of the one live stamp
(tests/fixtures/ots/live-stamp.ots). The client cases run scripts/ots.mjs with the pinned opentimestamps 0.4.9 against a local server
that answers as a calendar and as the Esplora explorer, replaying recorded responses (tests/fixtures/ots/esplora-358391.json); they skip
when scripts/checks is not installed (npm ci --prefix scripts/checks --ignore-scripts)."""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, threading, unittest
from datetime import date as Date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_manifest import ROOT, read, put, scratch, daily, published, stamped, ots_proof, varuint
from test_i18n import findings

FIX, CHECKS = os.path.join(ROOT, 'tests', 'fixtures', 'ots'), os.path.join(ROOT, 'scripts', 'checks')
OTS, PAGE = os.path.join(ROOT, 'scripts', 'ots.mjs'), os.path.join(ROOT, 'scripts', 'check_page.mjs')
CLIENT = os.path.join(CHECKS, 'node_modules', 'opentimestamps')
HAVE_CLIENT = os.path.exists(os.path.join(CLIENT, 'package.json'))
sha = lambda b: hashlib.sha256(b).hexdigest()
compact = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))
CAL, PATH = 'https://alice.btc.calendar.opentimestamps.org', bytes.fromhex('5a1d0c0ffee0b10c')


def ledger(web): return json.loads(read(os.path.join(web, 'ledger', 'index.json')))
def save(web, E): put(os.path.join(web, 'ledger', 'index.json'), compact(E))
def proof_path(web, d): return os.path.join(web, 'ledger', 'ots', f'{d}.ots')


def add_day(web, d):
    """The next day's ledger entry, day file and archive file, as the next run would write them (same manifest: no proof yet)."""
    E = ledger(web); last = E[-1]
    D = json.loads(read(os.path.join(web, 'ledger', f'{last["date"]}.json'))); D['date'] = d; text = compact(D)
    put(os.path.join(web, 'ledger', f'{d}.json'), text)
    A = json.loads(read(os.path.join(web, 'ledger', 'ids', f'{last["date"]}.json'))); A['date'] = d
    put(os.path.join(web, 'ledger', 'ids', f'{d}.json'), compact(A))
    save(web, E + [{**{k: v for k, v in last.items() if k not in ('ots', 'anchored')}, 'date': d, 'ledger_sha256': sha(text.encode())}])


def rebind(web, d, digest):
    """Point the <d> entry, its Release and its day file at another manifest SHA256 (to place a real proof of another digest)."""
    E = ledger(web); e = next(x for x in E if x['date'] == d)
    p = os.path.join(web, 'ledger', f'{d}.json'); D = json.loads(read(p)); D['manifest']['sha256'] = digest; text = compact(D); put(p, text)
    e.update(manifest_sha256=digest, ledger_sha256=sha(text.encode())); e['release']['sha256'] = digest
    save(web, E)


def gate(web): return subprocess.run(['node', PAGE, web], capture_output=True, text=True)


def ledger_web(d, days=1):
    """d/web: a published first day (scratch, manifest.py daily and release) plus days-1 later days; -> (web, [dates])."""
    scratch(d); assert daily(d).returncode == 0
    web = os.path.join(d, 'web'); first = ledger(web)[0]['date']
    assert published(d, first)[1].returncode == 0
    dates = [first]
    for _ in range(days - 1):
        dates.append((Date.fromisoformat(dates[-1]) + timedelta(days=1)).isoformat()); add_day(web, dates[-1])
    return web, dates


class ProofGateTest(unittest.TestCase):
    """check_page.mjs: a proof per entry that commits to its manifest, anchored records with their block, no proof edited after."""
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.web, (cls.d1, cls.d2) = ledger_web(cls.tmp.name, 2)
        for x in (cls.d1, cls.d2): stamped(cls.web, x)
        cls.digest = ledger(cls.web)[0]['manifest_sha256']

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def overlay(self, change=None):
        with tempfile.TemporaryDirectory() as t:
            web = os.path.join(t, 'web'); shutil.copytree(self.web, web)
            if change: change(web)
            return gate(web)

    def anchor(self, web, block=868000, upgraded=None, record=None):
        """Day 1's proof upgraded in place (a Bitcoin attestation added) and recorded in day 2's entry, as scripts/ots.mjs upgrade does."""
        b = upgraded or ots_proof(self.digest, ('pending', CAL), ('bitcoin', block))
        with open(proof_path(web, self.d1), 'wb') as f: f.write(b)
        E = ledger(web)
        E[1]['anchored'] = [record or {'date': self.d1, 'block': block, 'time': '2026-10-18T03:12:44Z', 'ots_sha256': sha(b)}]
        save(web, E)

    def assert_only(self, r, msg):
        self.assertEqual(r.returncode, 1, r.stdout); got = findings(r)
        self.assertEqual(len(got), 1, got); self.assertTrue(got[0].startswith(msg), got)

    def test_pending_proofs_pass(self):
        r = self.overlay(); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn('ledger 2 days, proofs 2 (0 anchored)', r.stdout)

    def test_a_proof_anchored_in_a_later_entry_passes(self):
        r = self.overlay(self.anchor); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn('proofs 2 (1 anchored)', r.stdout)

    def test_the_real_pending_proof_of_the_live_stamp_parses_and_passes(self):
        live = json.loads(read(os.path.join(FIX, 'live-stamp.json')))
        b = read(os.path.join(FIX, 'live-stamp.ots')); self.assertEqual(sha(b), live['proof_sha256'])
        def change(web): rebind(web, self.d1, live['digest']); stamped(web, self.d1, b)
        r = self.overlay(change); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn('proofs 2 (0 anchored)', r.stdout)

    def test_an_entry_without_its_proof_file_fails(self):
        self.assert_only(self.overlay(lambda w: os.remove(proof_path(w, self.d2))), 'ledger/index.json: entry without its OpenTimestamps proof file')

    def test_an_entry_that_does_not_name_its_proof_fails(self):
        def change(web): E = ledger(web); del E[1]['ots']; save(web, E)
        self.assert_only(self.overlay(change), 'ledger/index.json: entry does not name its OpenTimestamps proof')

    def test_a_proof_of_another_manifest_fails(self):
        def change(web): stamped(web, self.d2, ots_proof('ab' * 32))
        self.assert_only(self.overlay(change), f"ledger/ots/{self.d2}.ots: proof does not commit to its entry's manifest_sha256")

    def test_a_file_that_is_not_a_proof_fails(self):
        def change(web): stamped(web, self.d2, ots_proof(self.digest)[:-3])
        self.assert_only(self.overlay(change), f'ledger/ots/{self.d2}.ots: not an OpenTimestamps proof (truncated)')

    def test_an_anchored_record_without_its_block_fails(self):
        def change(web):
            self.anchor(web); E = ledger(web); E[1]['anchored'][0]['block'] = None; save(web, E)
        self.assert_only(self.overlay(change), 'ledger/index.json: anchored record without its Bitcoin block height')

    def test_a_proof_edited_after_anchoring_fails(self):
        def change(web):
            self.anchor(web)
            with open(proof_path(web, self.d1), 'wb') as f: f.write(ots_proof(self.digest, ('bitcoin', 868000), ('bitcoin', 868001)))
        self.assert_only(self.overlay(change), f'ledger/ots/{self.d1}.ots: proof edited after anchoring')

    def test_a_block_the_proof_does_not_attest_fails(self):
        def change(web):
            self.anchor(web); E = ledger(web); E[1]['anchored'][0]['block'] = 868999; save(web, E)
        self.assert_only(self.overlay(change), f'ledger/ots/{self.d1}.ots: the proof attests no Bitcoin block 868999')

    def test_a_record_in_the_dates_own_or_an_earlier_entry_fails(self):    # the block goes in a later run's entry: none is edited
        def change(web):
            self.anchor(web); E = ledger(web); E[0]['anchored'] = E[1].pop('anchored'); save(web, E)
        self.assert_only(self.overlay(change), 'ledger/index.json: anchored record names no entry before the entry that records it')

    def test_a_date_recorded_anchored_twice_fails(self):
        def change(web):
            self.anchor(web); E = ledger(web); E[1]['anchored'] *= 2; save(web, E)
        self.assert_only(self.overlay(change), f'ledger/index.json: {self.d1} is recorded anchored twice')

    def test_a_proof_file_with_no_entry_fails(self):
        def change(web):
            with open(os.path.join(web, 'ledger', 'ots', f'{self.d2}.ots.bak'), 'wb') as f: f.write(b'x')
        self.assert_only(self.overlay(change), 'ledger/index.json: ledger/ots file with no index entry')


class RerunTest(unittest.TestCase):
    """E1's same-date rerun keeps the proof fields: `ots` while the manifest is the same, `anchored` always (manifest.py ledger)."""
    def test_a_rerun_keeps_the_proof_and_the_anchored_records(self):
        with tempfile.TemporaryDirectory() as d:
            scratch(d); self.assertEqual(daily(d).returncode, 0); web = os.path.join(d, 'web')   # Release not yet published
            [e] = ledger(web); stamped(web, e['date'])
            E = ledger(web); E[0]['anchored'] = [{'date': '2026-10-01', 'block': 868000, 'time': '2026-10-02T03:12:44Z', 'ots_sha256': 'cd' * 32}]
            save(web, E); before = read(os.path.join(web, 'ledger', 'index.json'))
            r = daily(d); self.assertEqual(r.returncode, 0, r.stderr)               # the same inputs, the same manifest: both kept
            self.assertEqual(read(os.path.join(web, 'ledger', 'index.json')), before)
            with open(os.path.join(web, 'feed.xml'), 'a') as f: f.write(' ')        # a different manifest: its proof no longer applies
            r = daily(d); self.assertEqual(r.returncode, 0, r.stderr)
            [x] = ledger(web)
            self.assertNotEqual(x['manifest_sha256'], E[0]['manifest_sha256']); self.assertNotIn('ots', x)
            self.assertEqual(x['anchored'], E[0]['anchored'])


class AuditStateTest(unittest.TestCase):
    """web/dehype.js proofStates (its ots:start ... ots:end block): "anchored" for a date only once a ledger entry records its block."""
    def test_anchored_only_once_an_entry_records_the_block(self):
        js = read(os.path.join(ROOT, 'web', 'dehype.js')).decode()
        block = re.search(r'// ots:start[^\n]*\n([\s\S]*?)// ots:end', js)[1]
        E = [{'date': '2026-10-17', 'ots': {}}, {'date': '2026-10-18', 'ots': {}},
             {'date': '2026-10-19', 'ots': {}, 'anchored': [{'date': '2026-10-17', 'block': 868000}, {'date': '2026-10-18', 'block': None}]},
             {'date': '2026-10-20', 'ots': {}, 'anchored': [{'date': '2026-10-17', 'block': 1}]}]
        src = f'{block}\nconsole.log(JSON.stringify([...proofStates({json.dumps(E)})]));'
        r = subprocess.run(['node', '-e', src], capture_output=True, text=True); self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), [['2026-10-17', {'block': 868000, 'by': '2026-10-19'}]])
        self.assertIn("t('audit.anchored', { n: S.get(e.date).block })", js); self.assertIn('ots verify -f ', js)
        self.assertIn('ots-cli.js verify --ignore-bitcoin-node -f ', js); self.assertNotIn('e.block', js)


class Server:
    """127.0.0.1 only: a calendar (POST /digest -> a pending attestation; GET /timestamp/<commitment> -> 404 "Pending confirmation"
    until anchored, then, as a real calendar does, a path (append, sha256) to a Bitcoin attestation at a height of its own) and an Esplora
    explorer (GET /block-height/<h>, /block/<hash>) whose block's merkle root ends that path, or the recorded responses of block 358391."""
    def __init__(self):
        self.mode, self.esplora, self.log, self.heights, self.roots = 'pending', 'up', [], {}, {}
        self.recorded = json.loads(read(os.path.join(FIX, 'esplora-358391.json')))
        srv = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def send(self, code, body, ctype='application/octet-stream'):
                self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(body)))
                self.end_headers(); self.wfile.write(body)
            def do_POST(self):
                self.rfile.read(int(self.headers.get('Content-Length') or 0)); srv.log.append(('POST', self.path))
                if srv.mode == 'down': return self.send(503, b'down')
                uri = srv.url.encode()
                payload = varuint(len(uri)) + uri
                self.send(200, b'\x00' + bytes.fromhex('83dfe30d2ef90c8e') + varuint(len(payload)) + payload)
            def do_GET(self):
                p = self.path.strip('/'); srv.log.append(('GET', p))
                if p.startswith('timestamp/'):
                    if srv.mode != 'anchored': return self.send(404, b'Pending confirmation in Bitcoin blockchain', 'text/plain')
                    c = p.split('/')[1]; h = srv.heights.setdefault(c, 868000 + len(srv.heights)); v = varuint(h)
                    srv.roots[h] = hashlib.sha256(bytes.fromhex(c) + PATH).digest()[::-1].hex()      # the path a calendar answers: append, sha256
                    return self.send(200, b'\xf0' + varuint(len(PATH)) + PATH + b'\x08\x00' + bytes.fromhex('0588960d73d71901') + varuint(len(v)) + v)
                if srv.esplora == 'down': return self.send(503, b'down', 'text/plain')
                if p in srv.recorded:
                    x = srv.recorded[p]; return self.send(200, (x if isinstance(x, str) else json.dumps(x)).encode(), 'application/json')
                if p.startswith('block-height/'): return self.send(200, f'{int(p.split("/")[1]):064x}'.encode(), 'text/plain')
                if p.startswith('block/'):
                    return self.send(200, json.dumps({'merkle_root': srv.roots[int(p.split('/')[1], 16)], 'timestamp': 1792300000}).encode(), 'application/json')
                self.send(404, b'')
        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), H)
        self.url = f'http://127.0.0.1:{self.httpd.server_address[1]}'
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self): self.httpd.shutdown(); self.httpd.server_close()


@unittest.skipUnless(HAVE_CLIENT, 'opentimestamps 0.4.9 not installed (npm ci --prefix scripts/checks --ignore-scripts)')
class ClientTest(unittest.TestCase):
    """scripts/ots.mjs with the pinned client: stamp, the upgrade loop, verify --ignore-bitcoin-node, recorded in the run's own entry."""
    def setUp(self): self.srv = Server(); self.tmp = tempfile.TemporaryDirectory()
    def tearDown(self): self.srv.close(); self.tmp.cleanup()

    def ots(self, *a):
        env = {**os.environ, 'NO_PROXY': '127.0.0.1', 'no_proxy': '127.0.0.1', 'NODE_OPTIONS': '--no-deprecation'}
        for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy'): env.pop(k, None)
        return subprocess.run(['node', OTS, *a], capture_output=True, text=True, env=env, timeout=60)

    def stamp(self, web, d): return self.ots('stamp', '--web', web, '--date', d, '--calendar', self.srv.url)
    def upgrade(self, web, d): return self.ots('upgrade', '--web', web, '--date', d, '--calendar', self.srv.url, '--esplora', self.srv.url)

    def test_the_day_is_stamped_pending_and_a_rerun_keeps_its_proof(self):
        web, [d1] = ledger_web(self.tmp.name)
        r = self.stamp(web, d1); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn(f'ots {d1}: stamped manifest', r.stdout)
        b = read(proof_path(web, d1)); [e] = ledger(web)
        self.assertEqual(e['ots'], {'file': f'ots/{d1}.ots', 'sha256': sha(b)})
        info = json.loads(self.ots('info', proof_path(web, d1)).stdout)
        self.assertEqual((info['digest'], info['complete'], info['pending']), (e['manifest_sha256'], False, [self.srv.url]))
        g = gate(web); self.assertEqual(g.returncode, 0, g.stderr); self.assertIn('proofs 1 (0 anchored)', g.stdout)
        r = self.stamp(web, d1); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn('kept', r.stdout)
        self.assertEqual(read(proof_path(web, d1)), b); self.assertEqual([x for x in self.srv.log if x[0] == 'POST'], [('POST', '/digest')])

    def test_no_calendar_answer_is_no_proof_and_a_failed_step(self):
        web, [d1] = ledger_web(self.tmp.name); self.srv.mode = 'down'
        r = self.stamp(web, d1); self.assertEqual(r.returncode, 1); self.assertIn('no calendar answered', r.stderr)
        self.assertFalse(os.path.exists(proof_path(web, d1))); self.assertNotIn('ots', ledger(web)[0])

    def test_a_proof_recorded_anchored_is_never_stamped_again(self):
        web, [d1, d2] = ledger_web(self.tmp.name, 2)
        self.assertEqual(self.stamp(web, d1).returncode, 0)
        E = ledger(web); E[1]['anchored'] = [{'date': d1, 'block': 868000, 'time': '2026-10-18T03:12:44Z', 'ots_sha256': sha(read(proof_path(web, d1)))}]
        E[0]['manifest_sha256'] = 'ab' * 32; save(web, E)
        r = self.stamp(web, d1); self.assertEqual(r.returncode, 1); self.assertIn('is never replaced', r.stderr)

    def test_day_n_minus_1_pending_when_published_is_anchored_in_a_later_entry_and_no_earlier_entry_changes(self):
        web, [d1] = ledger_web(self.tmp.name)
        self.assertEqual(self.stamp(web, d1).returncode, 0)                    # day 1: published pending
        published1 = read(proof_path(web, d1))
        d2, d3, d4 = ((Date.fromisoformat(d1) + timedelta(days=i)).isoformat() for i in (1, 2, 3))
        add_day(web, d2); self.assertEqual(self.stamp(web, d2).returncode, 0)  # day 2: the calendars have no block yet
        r = self.upgrade(web, d2); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn(f'ots {d1}: pending', r.stdout)
        self.assertEqual(read(proof_path(web, d1)), published1); self.assertNotIn('anchored', ledger(web)[1])
        add_day(web, d3); self.assertEqual(self.stamp(web, d3).returncode, 0)  # day 3: both earlier proofs are in a block
        before = [compact(e) for e in ledger(web)]
        self.srv.mode = 'anchored'
        r = self.upgrade(web, d3); self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('2 pending proofs checked, 2 anchored and recorded in the', r.stdout)
        E = ledger(web)
        self.assertEqual([compact(e) for e in E[:2]], before[:2])               # no earlier entry changed
        self.assertTrue(read(os.path.join(web, 'ledger', 'index.json')).decode().startswith('[' + ','.join(before[:2]) + ','))
        A = {a['date']: a for a in E[2]['anchored']}
        self.assertEqual(sorted(A), [d1, d2])
        for x in (d1, d2):
            b = read(proof_path(web, x)); info = json.loads(self.ots('info', proof_path(web, x)).stdout)
            self.assertEqual(A[x]['ots_sha256'], sha(b)); self.assertIn(A[x]['block'], info['blocks']); self.assertTrue(info['complete'])
            self.assertEqual(A[x]['time'], '2026-10-18T05:06:40Z')        # the replayed block header's time
        self.assertNotEqual(read(proof_path(web, d1)), published1)              # upgraded in place
        g = gate(web); self.assertEqual(g.returncode, 0, g.stderr); self.assertIn('ledger 3 days, proofs 3 (2 anchored)', g.stdout)
        anchored = {x: read(proof_path(web, x)) for x in (d1, d2)}
        add_day(web, d4); self.assertEqual(self.stamp(web, d4).returncode, 0)  # day 4: only day 3's proof is still pending
        n = len(self.srv.log); before = [compact(e) for e in ledger(web)]
        r = self.upgrade(web, d4); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn('1 pending proofs checked, 1 anchored', r.stdout)
        self.assertEqual([a['date'] for a in ledger(web)[3]['anchored']], [d3]); self.assertEqual([compact(e) for e in ledger(web)[:3]], before[:3])
        self.assertEqual({x: read(proof_path(web, x)) for x in (d1, d2)}, anchored)       # never touched after anchoring
        self.assertEqual(len([x for x in self.srv.log[n:] if x[1].startswith('timestamp/')]), 1)
        self.assertEqual(gate(web).returncode, 0)

    def test_verify_ignore_bitcoin_node_accepts_the_package_example_against_recorded_block_358391(self):
        web = os.path.join(self.tmp.name, 'web'); b = read(os.path.join(CLIENT, 'examples', 'hello-world.txt.ots'))
        os.makedirs(os.path.join(web, 'ledger', 'ots'))
        with open(proof_path(web, '2026-10-16'), 'wb') as f: f.write(b)
        digest = sha(read(os.path.join(CLIENT, 'examples', 'hello-world.txt')))
        save(web, [{'date': '2026-10-16', 'manifest_sha256': digest, 'ots': {'file': 'ots/2026-10-16.ots', 'sha256': sha(b)}},
                   {'date': '2026-10-17', 'manifest_sha256': 'ab' * 32}])
        r = self.upgrade(web, '2026-10-17'); self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(ledger(web)[1]['anchored'], [{'date': '2026-10-16', 'block': 358391, 'time': '2015-05-28T15:41:18Z', 'ots_sha256': sha(b)}])
        self.assertEqual(read(proof_path(web, '2026-10-16')), b)
        h = self.srv.recorded['block-height/358391']
        self.assertEqual([x for x in self.srv.log], [('GET', 'block-height/358391'), ('GET', f'block/{h}')])   # the explorer only
        self.srv.esplora = 'down'; save(web, ledger(web)[:1] + [{'date': '2026-10-17', 'manifest_sha256': 'ab' * 32}])
        r = self.upgrade(web, '2026-10-17'); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn('left pending', r.stdout)
        self.assertNotIn('anchored', ledger(web)[1])                            # an explorer that does not answer: still pending

    def test_info_reads_the_live_stamp(self):
        live = json.loads(read(os.path.join(FIX, 'live-stamp.json')))
        info = json.loads(self.ots('info', os.path.join(FIX, 'live-stamp.ots')).stdout)
        self.assertEqual((info['digest'], info['complete'], len(info['pending'])), (live['digest'], False, 4))


class LicenceTest(unittest.TestCase):
    """C4, C38: opentimestamps exactly 0.4.9 by lockfile (sha512 integrity), the closure audit of scripts/checks, the LGPL-3.0 notice."""
    def test_pin_lockfile_audit_and_notice_agree(self):
        P = json.loads(read(os.path.join(CHECKS, 'package.json'))); L = json.loads(read(os.path.join(CHECKS, 'package-lock.json')))
        A = json.loads(read(os.path.join(CHECKS, 'licence-closure.json'))); N = read(os.path.join(CHECKS, 'NOTICE')).decode()
        self.assertEqual(P['dependencies'], {'opentimestamps': '0.4.9', 'playwright-core': '1.59.1'})
        o = L['packages']['node_modules/opentimestamps']
        self.assertEqual((o['version'], o['license'], o['resolved']), ('0.4.9', 'LGPL-3.0', 'https://registry.npmjs.org/opentimestamps/-/opentimestamps-0.4.9.tgz'))
        lock = [(k.split('node_modules/')[-1], v['version'], v.get('license'), v['integrity']) for k, v in sorted(L['packages'].items()) if k]
        self.assertTrue(all(re.match(r'^sha512-', x[3]) for x in lock)); self.assertFalse([k for k, v in L['packages'].items() if v.get('hasInstallScript')])
        self.assertEqual([(p['name'], p['version'], p['license'], p['integrity']) for p in A['packages']], lock)
        self.assertEqual(A['direct'], P['dependencies']); self.assertIn('LGPL-3.0', A['licences'])
        self.assertTrue(A['result'].startswith(f'closed: {len(lock)} packages, all permissive'))
        self.assertEqual(sorted({p.get('used_under') or p['license'] for p in A['packages']}), A['licences'])
        self.assertIn('opentimestamps@0.4.9 (LGPL-3.0)', N); self.assertIn('GNU LESSER GENERAL PUBLIC LICENSE', N)
        for p in A['packages']:
            d = os.path.join(CHECKS, p.get('path') or f'node_modules/{p["name"]}')
            if p['licence_file'] and os.path.exists(os.path.join(d, p['licence_file'])):           # the installed tree, when present
                self.assertEqual(sha(read(os.path.join(d, p['licence_file']))), p['licence_file_sha256'], p['name'])
        if HAVE_CLIENT: self.assertIn(read(os.path.join(CLIENT, 'LICENSE')).decode().strip(), N)
        src = read(OTS).decode()                                                 # node built-ins and the pinned client only
        self.assertEqual(sorted(set(re.findall(r"from '([^']+)'", src))), ['node:crypto', 'node:fs', 'node:module', 'node:path'])
        self.assertIn("require('opentimestamps/index.js')", src); self.assertIn("'0.4.9'", src)


if __name__ == '__main__':
    unittest.main()
