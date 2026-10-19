"""Daily input manifest, ledger, story-id archive and stale since (design rows 17, 18; C3, C5, C15, C16, C25, C32, C37; SC-4, the
manifest part of SC-5, the ledger part of SC-18, the failed-Pulse part of SC-19; group E1). scripts/manifest.py runs on a scratch copy
of the committed web/ with a scratch history DB built from tests/fixtures/manifest/signals.json; the dated Release asset is simulated by
a local copy of the manifest file (no network, no Release). The check_page.mjs cases follow Decision 14 (an overlay of the committed
web/, failing with that rule's own finding, or passing)."""
import gzip, hashlib, json, os, shutil, sqlite3, subprocess, sys, tempfile, unittest
from datetime import timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from test_i18n import findings
from test_feed import compose, need_cordis
import pulse

WEB, FIX = os.path.join(ROOT, 'web'), os.path.join(ROOT, 'tests', 'fixtures', 'manifest')
MANIFEST = os.path.join(ROOT, 'scripts', 'manifest.py')
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import manifest


def read(path):
    with open(path, 'rb') as f: return f.read()


def put(path, text):
    with open(path, 'w', encoding='utf-8') as f: f.write(text)


def run(*args):
    return subprocess.run([sys.executable, MANIFEST, *args], capture_output=True, text=True)


def scratch(d):
    """d/web (a copy of the committed web/ with an empty ledger, one removal request added) and d/history (signals.sqlite from the
    fixture rows, one post the recheck found gone) -> {fixture key: stored row}."""
    web, hist = os.path.join(d, 'web'), os.path.join(d, 'history')
    shutil.copytree(WEB, web); os.makedirs(hist)
    shutil.rmtree(os.path.join(web, 'ledger'), ignore_errors=True); os.makedirs(os.path.join(web, 'ledger'))
    put(os.path.join(web, 'ledger', 'index.json'), '[]')              # the committed ledger grows daily: these cases start from day 0
    _B = os.path.join(web, 'briefing.json'); _b = json.loads(open(_B).read()); _b['ledger_days'] = 0
    with open(_B, 'w') as _f: json.dump(_b, _f, separators=(',', ':'), ensure_ascii=False)   # its briefing counts the same day-0 ledger
    gen = pulse.parse_dt(json.loads(read(os.path.join(web, 'briefing.json')))['generated_at'])
    rows = {}
    con = sqlite3.connect(os.path.join(hist, 'signals.sqlite'))
    con.execute('''CREATE TABLE signals(net TEXT, pid TEXT, url TEXT, title TEXT, author TEXT, created TEXT, score INT, comments INT,
                   source TEXT, fetched TEXT, extra TEXT, PRIMARY KEY(net, pid))''')                    # pulse.db()'s table
    for r in json.loads(read(os.path.join(FIX, 'signals.json')))['rows']:
        row = {k: r[k] for k in manifest.COLUMNS if k in r}
        row['created'], row['fetched'] = pulse.iso(gen - timedelta(hours=r['hours_ago'])), pulse.iso(gen - timedelta(minutes=5))
        con.execute(f'INSERT INTO signals({",".join(manifest.COLUMNS)}) VALUES({",".join("?" * len(manifest.COLUMNS))})', [row[k] for k in manifest.COLUMNS])
        rows[r['key']] = row
    con.commit(); con.close()
    with open(os.path.join(hist, 'recheck.json'), 'w') as f: json.dump({'gone': {'HN:50000002': '2026-10-17'}}, f)
    with open(os.path.join(web, 'removals.json'), 'w') as f:
        json.dump({'entries': [{'sha256': pulse.url_hash(rows['removed']['url']), 'date': '2026-10-01'}]}, f)
    return rows


def daily(d):
    return run('daily', '--web', os.path.join(d, 'web'), '--history', os.path.join(d, 'history'), '--out', os.path.join(d, 'dist'))


def published(d, date):
    """The dated Release, simulated: the manifest copied to a download folder, read back by `manifest.py release`."""
    asset = os.path.join(d, 'release', f'manifest-{date}.json.gz')
    os.makedirs(os.path.dirname(asset), exist_ok=True)
    shutil.copy(os.path.join(d, 'dist', os.path.basename(asset)), asset)
    return asset, run('release', asset, '--tag', f'ledger-{date}', '--url', f'https://github.com/owner/repo/releases/download/ledger-{date}/{os.path.basename(asset)}',
                      '--web', os.path.join(d, 'web'))


class ManifestTest(unittest.TestCase):
    """SC-4 and the manifest part of SC-5: the manifest check, its Reddit fixture, and the hash an outsider recomputes."""
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(); d = cls.d = cls.tmp.name
        cls.rows = scratch(d)
        cls.r = daily(d)
        B = json.loads(read(os.path.join(d, 'web', 'briefing.json')))
        cls.date = manifest.sp_date(B['generated_at'])
        cls.path = os.path.join(d, 'dist', f'manifest-{cls.date}.json.gz')
        cls.M = json.loads(gzip.decompress(read(cls.path))) if os.path.exists(cls.path) else None

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def test_the_reddit_fixture_fails_the_manifest_check(self):
        r = run('check', os.path.join(FIX, 'reddit_leak.json'))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn('manifest holds a Reddit URL or t3_ id', r.stderr)
        self.assertIn('records[1]: a Reddit record carries a field other than the hash and the network name (id, url)', r.stderr)

    def test_daily_manifest_passes_its_check_and_holds_no_reddit_field_but_the_hash(self):
        self.assertEqual(self.r.returncode, 0, self.r.stderr)
        self.assertEqual(run('check', self.path).returncode, 0)
        text = gzip.decompress(read(self.path)).decode('utf-8')
        for s in ('reddit.com', 't3_', 'LocalLLaMA', 'u_fixture', 'A Reddit fixture', 'someone', 'hn_person', 'did:plc', 'bsky.app', '/@'):
            self.assertNotIn(s, text)
        reddit = [x for x in self.M['records'] if x['net'] == 'Reddit']
        self.assertEqual(len(reddit), 2)
        for x in reddit: self.assertEqual(set(x), {'net', 'sha256'})

    def test_an_outsider_recomputes_a_reddit_record_hash_from_its_canonical_json(self):
        row = self.rows['reddit2']                                   # non-ASCII title and permalink: kept as UTF-8, not escaped
        blob = json.dumps({k: row[k] for k in ('net', 'pid', 'url', 'title', 'author', 'created', 'score', 'comments', 'source', 'fetched', 'extra')},
                          sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        self.assertIn(hashlib.sha256(blob).hexdigest(), {x['sha256'] for x in self.M['records'] if x['net'] == 'Reddit'})

    def test_records_carry_ids_handle_free_urls_observed_values_and_fetch_times(self):
        by = {x.get('id'): x for x in self.M['records']}
        hn = by['HN:50000001']
        self.assertEqual((hn['url'], hn['score'], hn['comments'], hn['created'], hn['fetched']),
                         (self.rows['hn']['url'], 120, 40, self.rows['hn']['created'], self.rows['hn']['fetched']))
        self.assertEqual(by['Mastodon:113000000000000001']['url'], 'https://mastodon.social/statuses/113000000000000001')    # C25
        self.assertTrue(all(x['url'].startswith('https://mastodon.social/statuses/') for x in self.M['records'] if x['net'] == 'Mastodon'))
        self.assertEqual(by['Lobsters:abc123']['url'], 'https://lobste.rs/s/abc123/a_fixture')
        news = [x for x in self.M['records'] if x['net'] == 'Newsletter']
        self.assertEqual(sorted(set(x) for x in news), sorted([{'net', 'sha256'}, set(hn)]))         # a URL with /@writer is a hash only
        self.assertTrue(any(x['net'] == 'Bluesky' and set(x) == {'net', 'sha256'} for x in self.M['records']))
        self.assertEqual(self.M['counts'], {'Bluesky': 1, 'HN': 1, 'Lobsters': 1, 'Mastodon': 1, 'Newsletter': 2, 'Official': 2, 'Reddit': 2})
        official = sorted((set(x) for x in self.M['records'] if x['net'] == 'Official'), key=len)
        self.assertEqual(official[0], {'net', 'sha256'})                                    # a t3_ id in any URL: a hash only

    def test_posts_gone_removed_or_older_than_the_widest_window_are_left_out(self):
        ids = {x.get('id') for x in self.M['records']}
        for k in ('HN:49000001', 'HN:50000002', 'Lobsters:zzz999'): self.assertNotIn(k, ids)

    def test_source_status_and_a_sha256_per_published_file(self):
        B = json.loads(read(os.path.join(self.d, 'web', 'briefing.json')))
        self.assertEqual(self.M['sources'], {n: {'status': s['status'], 'detail': s['detail']} for n, s in B['sources'].items()})
        for f in ('briefing.json', 'pulse.json', 'feed.xml', 'verdicts.json', f'ledger/ids/{self.date}.json'):
            self.assertEqual(self.M['files'][f'web/{f}'], hashlib.sha256(read(os.path.join(self.d, 'web', f))).hexdigest(), f)

    def test_a_stale_briefing_gets_no_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            scratch(d)
            p = os.path.join(d, 'web', 'briefing.json'); B = json.loads(read(p)); B['stale'] = {'since': '2026-10-16'}
            with open(p, 'w') as f: json.dump(B, f)
            r = daily(d)
            self.assertEqual(r.returncode, 1); self.assertIn('stale briefing', r.stderr)
            self.assertFalse(os.path.exists(os.path.join(d, 'web', 'ledger', 'index.json')) and json.loads(read(os.path.join(d, 'web', 'ledger', 'index.json'))))


OTS_MAGIC = bytes.fromhex('004f70656e54696d657374616d7073000050726f6f6600bf89e2e884e89294')     # opentimestamps 0.4.9's detached-proof header


def varuint(n):
    out = b''
    while n > 127: out += bytes([n & 127 | 128]); n >>= 7
    return out + bytes([n])


def ots_proof(digest, *attestations, nonce=b'\x00' * 16):
    """A version-1 OpenTimestamps proof of a SHA256 digest, built by hand: append a nonce, SHA256, then each attestation (('pending',
    uri) or ('bitcoin', height)) on that message. The shape of a real proof (tests/fixtures/ots/live-stamp.ots), with no calendar."""
    tags = {'pending': '83dfe30d2ef90c8e', 'bitcoin': '0588960d73d71901'}
    att = [b'\x00' + bytes.fromhex(tags[k]) + (lambda p: varuint(len(p)) + p)(varuint(len(v)) + v.encode() if k == 'pending' else varuint(v))
           for k, v in attestations or [('pending', 'https://alice.btc.calendar.opentimestamps.org')]]
    tree = b''.join(b'\xff' + a for a in att[:-1]) + att[-1]
    return OTS_MAGIC + b'\x01\x08' + bytes.fromhex(digest) + b'\xf0' + varuint(len(nonce)) + nonce + b'\x08' + tree


def stamped(web, date, proof=None):
    """What scripts/ots.mjs stamp leaves (group E2), without a calendar: ledger/ots/<date>.ots and the entry's ots field."""
    L = os.path.join(web, 'ledger', 'index.json'); E = json.loads(read(L)); e = next(x for x in E if x['date'] == date)
    b = proof or ots_proof(e['manifest_sha256'])
    os.makedirs(os.path.join(web, 'ledger', 'ots'), exist_ok=True)
    with open(os.path.join(web, 'ledger', 'ots', f'{date}.ots'), 'wb') as f: f.write(b)
    e['ots'] = {'file': f'ots/{date}.ots', 'sha256': hashlib.sha256(b).hexdigest()}
    put(L, json.dumps(E, ensure_ascii=False, separators=(',', ':')))


class StoredInputsTest(unittest.TestCase):
    """S5 groundwork: the stored inputs of the context panels and the Hub check go into the manifest whole when this run's live Pulse step
    wrote them (their fetched_at is the run time history/recheck.json records); another run's file, or none, reads null, and an input that
    breaks a public-data rule is left out alone, never the day."""
    IND_FIX = os.path.join(ROOT, 'tests', 'fixtures', 'indicators', 'stored_2026-10-18.json')
    HUB_FIX = os.path.join(ROOT, 'tests', 'fixtures', 'hub', 'stored_2026-10-19.json')

    def run_with(self, d, ind_at, hub_at, run_at='2026-10-19T12:00:00Z', hub_edit=None, ind_edit=None):
        with open(os.path.join(d, 'history', 'recheck.json'), 'w') as f: json.dump({'gone': {'HN:50000002': '2026-10-17'}, 'run': {'at': run_at}}, f)
        for f, fix, at, edit in (('indicators.json', self.IND_FIX, ind_at, ind_edit), ('hub.json', self.HUB_FIX, hub_at, hub_edit)):
            if at is None: continue
            S = json.loads(read(fix)); S['fetched_at'] = at
            if edit: edit(S)
            with open(os.path.join(d, 'history', f), 'w', encoding='utf-8') as fh: json.dump(S, fh, ensure_ascii=False)
        r = daily(d)
        date = manifest.sp_date(json.loads(read(os.path.join(d, 'web', 'briefing.json')))['generated_at'])
        path = os.path.join(d, 'dist', f'manifest-{date}.json.gz')
        return r, (json.loads(gzip.decompress(read(path))) if os.path.exists(path) else None), path

    def test_this_runs_inputs_are_kept_whole_and_pass_the_check(self):
        with tempfile.TemporaryDirectory() as d:
            scratch(d)
            r, M, path = self.run_with(d, '2026-10-19T12:00:00Z', '2026-10-19T12:00:00Z')
            self.assertEqual(r.returncode, 0, r.stderr)
            si = M['stored_inputs']
            self.assertEqual(M['version'], 2); self.assertIn(pulse.IND.BLS_NOTICE, M['notices'])
            self.assertEqual(si['history/indicators.json']['inputs']['hn_hiring']['threads'][0]['title'], 'Ask HN: Who is hiring? (October 2026)')
            self.assertEqual(si['history/hub.json']['inputs']['Muse Spark'][0]['id'].split('/')[0], 'meta-models')
            self.assertEqual(run('check', path).returncode, 0)

    def test_another_runs_or_a_missing_input_reads_null(self):
        with tempfile.TemporaryDirectory() as d:
            scratch(d)
            r, M, _ = self.run_with(d, '2026-10-18T12:00:00Z', None)          # yesterday's indicators, no Hub file
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(M['stored_inputs'], {'history/indicators.json': None, 'history/hub.json': None})

    def test_a_failed_hub_fetch_on_a_same_day_rerun_leaves_the_earlier_file_out(self):
        with tempfile.TemporaryDirectory() as d:
            scratch(d)
            r, M, _ = self.run_with(d, '2026-10-19T12:00:00Z', '2026-10-19T10:30:00Z')   # the Hub file of the 10:30 run, kept by a failed fetch
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIsNone(M['stored_inputs']['history/hub.json']); self.assertIsNotNone(M['stored_inputs']['history/indicators.json'])

    def test_an_input_breaking_a_rule_is_left_out_alone(self):
        def handle(S): S['inputs']['Muse Spark'][0]['id'] = 'see @someone'
        def prose(S): S['inputs']['wikipedia']['note'] = {'text': 'free text a source might return'}
        with tempfile.TemporaryDirectory() as d:
            scratch(d)
            r, M, path = self.run_with(d, '2026-10-19T12:00:00Z', '2026-10-19T12:00:00Z', hub_edit=handle, ind_edit=prose)
            self.assertEqual(r.returncode, 0, r.stderr)                                 # the day still gets its manifest
            self.assertEqual(M['stored_inputs'], {'history/indicators.json': None, 'history/hub.json': None})
            self.assertIn('history/hub.json left out', r.stderr); self.assertIn('history/indicators.json left out', r.stderr)
            self.assertEqual(run('check', path).returncode, 0)

    def test_the_check_reads_the_block_shape(self):
        M = {'date': '2026-10-19', 'files': {}, 'records': [], 'stored_inputs': {'history/other.json': None}}
        self.assertTrue(any('stored_inputs' in b for b in manifest.check(M)))


class LedgerTest(unittest.TestCase):
    """The ledger part of SC-18 (C3) and the story-id archive (C32, Decision 13): the ledger's SHA256 equals the Release asset's."""
    def test_ledger_entry_day_file_archive_and_the_release_asset_hash(self):
        with tempfile.TemporaryDirectory() as d:
            scratch(d); r = daily(d); self.assertEqual(r.returncode, 0, r.stderr)
            web = os.path.join(d, 'web')
            B, P = (json.loads(read(os.path.join(web, f))) for f in ('briefing.json', 'pulse.json'))
            date = manifest.sp_date(B['generated_at'])
            [e] = json.loads(read(os.path.join(web, 'ledger', 'index.json')))
            self.assertEqual((e['date'], e['asset'], e['release']), (date, f'manifest-{date}.json.gz', None))
            self.assertFalse({'ots', 'anchored', 'block'} & set(e))                          # the proof fields are scripts/ots.mjs's (E2)
            self.assertEqual(e['ledger_sha256'], hashlib.sha256(read(os.path.join(web, 'ledger', f'{date}.json'))).hexdigest())
            day = json.loads(read(os.path.join(web, 'ledger', f'{date}.json')))
            self.assertEqual(day['manifest']['sha256'], e['manifest_sha256']); self.assertEqual([g['id'] for g in day['gauges']], [g['id'] for g in B['gauges']])
            A = json.loads(read(os.path.join(web, 'ledger', 'ids', f'{date}.json')))         # B2's read shape
            self.assertEqual((A['date'], A['generated_at']), (date, B['generated_at']))
            self.assertTrue({s['id'] for s in P['stories']} | {x['id'] for x in B['records']} <= set(A['ids']))
            asset, r = published(d, date)
            self.assertEqual(r.returncode, 0, r.stderr)
            [e] = json.loads(read(os.path.join(web, 'ledger', 'index.json')))
            self.assertEqual(e['release']['sha256'], hashlib.sha256(read(asset)).hexdigest())
            self.assertEqual(e['release']['sha256'], e['manifest_sha256'])
            stamped(web, date)                                                             # the day's proof (E2) before the gate
            g = subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)
            self.assertEqual(g.returncode, 0, g.stderr); self.assertIn('ledger 1 days', g.stdout)
            with open(asset, 'ab') as f: f.write(b'\0')                                       # a Release asset that is not the manifest
            r = run('release', asset, '--tag', 'x', '--url', 'https://example.test/x', '--web', web)
            self.assertEqual(r.returncode, 1); self.assertIn('the ledger records', r.stderr)
            self.assertEqual(json.loads(read(os.path.join(web, 'ledger', 'index.json')))[0]['release']['sha256'], e['manifest_sha256'])

    def test_a_published_date_is_never_replaced_by_a_different_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            scratch(d); self.assertEqual(daily(d).returncode, 0)
            web = os.path.join(d, 'web'); L = os.path.join(web, 'ledger', 'index.json')
            date = json.loads(read(L))[0]['date']
            self.assertEqual(published(d, date)[1].returncode, 0)
            before = read(L)
            r = daily(d); self.assertEqual(r.returncode, 0, r.stderr)                       # the same inputs: the same manifest, Release kept
            self.assertEqual(read(L), before)
            with open(os.path.join(web, 'feed.xml'), 'a') as f: f.write(' ')            # a published file changed: a different manifest
            r = daily(d)
            self.assertEqual(r.returncode, 1)
            self.assertIn(f'manifest: {date} is already in the ledger with its Release ledger-{date}', r.stderr)
            self.assertIn('differs, so no ledger entry is written for it', r.stderr)
            self.assertEqual(read(L), before)

    def test_a_rerun_on_the_same_date_replaces_its_entry_and_never_shrinks_its_archive(self):
        with tempfile.TemporaryDirectory() as d:
            scratch(d); self.assertEqual(daily(d).returncode, 0)
            web = os.path.join(d, 'web'); date = json.loads(read(os.path.join(web, 'ledger', 'index.json')))[0]['date']
            ids = os.path.join(web, 'ledger', 'ids', f'{date}.json'); A = json.loads(read(ids)); A['ids'].append('s:0123456789ab')
            with open(ids, 'w') as f: json.dump(A, f)
            self.assertEqual(daily(d).returncode, 0)
            self.assertEqual(len(json.loads(read(os.path.join(web, 'ledger', 'index.json')))), 1)
            self.assertIn('s:0123456789ab', json.loads(read(ids))['ids'])
            L = os.path.join(web, 'ledger', 'index.json'); E = json.loads(read(L)); E[0]['date'] = '2999-01-01'
            with open(L, 'w') as f: json.dump(E, f)
            r = daily(d); self.assertEqual(r.returncode, 1); self.assertIn('later than', r.stderr)      # an earlier date is never written


class LedgerGateTest(unittest.TestCase):
    """check_page.mjs on the ledger (Decision 14: a copy of web/, here with the scratch ledger in place of the committed one, since an
    overlay cannot remove committed day files): a published day passes; each broken record fails on its own rule."""
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(); d = cls.tmp.name
        scratch(d); assert daily(d).returncode == 0
        B = json.loads(read(os.path.join(d, 'web', 'briefing.json')))
        cls.date = manifest.sp_date(B['generated_at'])
        assert published(d, cls.date)[1].returncode == 0
        cls.web = os.path.join(d, 'web')
        stamped(cls.web, cls.date)

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def overlay(self, change=None):
        with tempfile.TemporaryDirectory() as t:
            web = os.path.join(t, 'web'); shutil.copytree(self.web, web)
            if change: change(os.path.join(web, 'ledger'))
            return subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)

    def edit(self, rel, fn):
        def change(L):
            p = os.path.join(L, rel); X = json.loads(read(p)); X = fn(X) or X
            with open(p, 'w') as f: json.dump(X, f)
        return change

    def assert_only(self, r, msg):
        self.assertEqual(r.returncode, 1, r.stdout)
        got = findings(r)
        self.assertEqual(len(got), 1, got); self.assertTrue(got[0].startswith(msg), got)

    def test_a_published_day_passes(self):
        r = self.overlay(); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn('ledger 1 days', r.stdout)

    def test_an_entry_without_its_release_fails(self):
        self.assert_only(self.overlay(self.edit('index.json', lambda E: E[0].update(release=None))),
                         'ledger/index.json: entry whose dated Release asset is missing or does not hash to its manifest_sha256')

    def test_an_edited_day_file_fails(self):
        self.assert_only(self.overlay(self.edit(f'{self.date}.json', lambda D: D.update(top10=[]))),
                         'ledger/index.json: entry ledger_sha256 is not the SHA256 of its day file')

    def test_an_index_in_another_shape_fails(self):
        r = self.overlay(lambda L: put(os.path.join(L, 'index.json'), '{"days": []}'))
        self.assertEqual(r.returncode, 1); self.assertIn('ledger/index.json is not a list of day entries (or {"entries": [...]})', findings(r))

    def test_an_archive_file_missing_a_published_story_id_fails(self):
        self.assert_only(self.overlay(self.edit(f'ids/{self.date}.json', lambda A: A.update(ids=A['ids'][1:]))),
                         f"ledger/ids/{self.date}.json: the day's archive file lacks a story id its pulse.json or briefing.json publishes")

    def test_the_archive_is_covered_even_when_the_index_has_no_entry_for_its_date(self):
        def change(L):
            put(os.path.join(L, 'index.json'), '[]'); os.remove(os.path.join(L, f'{self.date}.json'))      # the Release failed: no entry
            os.remove(os.path.join(L, 'ots', f'{self.date}.ots'))                                     # and no proof (refresh.yml's drop step)
            self.edit(f'ids/{self.date}.json', lambda A: A.update(ids=A['ids'][1:]))(L)
        self.assert_only(self.overlay(change), f"ledger/ids/{self.date}.json: the day's archive file lacks a story id its pulse.json or briefing.json publishes")

    def test_a_handle_in_a_day_file_fails_the_public_rules(self):
        def change(L):
            p = os.path.join(L, f'{self.date}.json'); D = json.loads(read(p)); D['note'] = 'see https://fosstodon.org/@someone/1'
            text = json.dumps(D); put(p, text)
            E = json.loads(read(os.path.join(L, 'index.json'))); E[0]['ledger_sha256'] = hashlib.sha256(text.encode()).hexdigest()
            put(os.path.join(L, 'index.json'), json.dumps(E))
        r = self.overlay(change)
        self.assertEqual(r.returncode, 1); self.assertTrue(any(g.startswith(f'ledger/{self.date}.json: account-naming URL') for g in findings(r)), findings(r))


@need_cordis
class StaleSinceTest(unittest.TestCase):
    """The failed-Pulse part of SC-19 (C5): compose.mjs on a failed-Pulse fixture; the briefing, gauges and feed read "stale since"
    the date with the reason and carry no value over, and the stale outputs pass check_page.mjs."""
    def test_a_failed_pulse_step_makes_the_briefing_gauges_and_feeds_read_stale_since(self):
        with tempfile.TemporaryDirectory() as d:
            web = os.path.join(d, 'web'); shutil.copytree(WEB, web)
            B0 = json.loads(read(os.path.join(web, 'briefing.json'))); since = manifest.sp_date(B0['generated_at'])
            failed_at = pulse.iso(pulse.parse_dt(B0['generated_at']) + timedelta(days=1))
            with open(os.path.join(web, 'checks', 'pulse-failed.json'), 'w') as f: json.dump({'at': failed_at, 'run': '4242'}, f)
            r = compose(d); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn('web/briefing.json', r.stdout)
            B = json.loads(read(os.path.join(web, 'briefing.json')))
            reason = 'the Pulse step failed in refresh run 4242'
            self.assertEqual(B['stale'], {'since': since, 'reason': reason, 'at': failed_at, 'run': '4242'})
            self.assertEqual((B['records'], B['top10'], B['generated_at'], B['ledger_days']), ([], [], B0['generated_at'], B0['ledger_days']))
            self.assertEqual([g['id'] for g in B['gauges']], [g['id'] for g in B0['gauges']])
            for g in B['gauges']:
                self.assertIsNone(g['value']); self.assertEqual(g['reason'], f'insufficient data: stale since {since}, {reason}')
            self.assertTrue(all(p.get('events') in (None, []) for p in B['panels']))
            for f, word, why in (('feed.json', 'Stale since', reason), ('feed.pt.json', 'Desatualizado desde', 'a etapa Pulse falhou na execução de atualização 4242')):
                J = json.loads(read(os.path.join(web, f)))
                self.assertTrue(J['description'].startswith(f'{word} {since}: {why}'), J['description'])
                self.assertEqual([i['id'] for i in J['items']], [f'stale:{since}']); self.assertEqual(J['_dehype']['stale']['since'], since)
                self.assertEqual(J['items'][0]['date_published'], failed_at)
            for f in ('feed.xml', 'feed.pt.xml'):
                X = read(os.path.join(web, f)).decode()
                self.assertIn(f'<guid isPermaLink="false">stale:{since}</guid>', X); self.assertNotIn('<guid isPermaLink="false">s:', X)
            g = subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)
            self.assertEqual(g.returncode, 0, g.stderr); self.assertIn(f'briefing stale since {since}', g.stdout)
            self.assertEqual(compose(d).returncode, 0)                                    # a second failed day keeps the date
            self.assertEqual(json.loads(read(os.path.join(web, 'briefing.json')))['stale']['since'], since)
            B['records'] = B0['records'][:1]                                              # a stale briefing that carries a record over
            with open(os.path.join(web, 'briefing.json'), 'w') as f: json.dump(B, f)
            g = subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)
            self.assertEqual(g.returncode, 1)
            self.assertIn('briefing.json: stale briefing carries a value over (records, Top 10 and gauge values stay empty) at 1 place, e.g. stale',
                          findings(g))

    def test_a_stale_briefing_carries_no_context_or_page_view_value(self):
        # the recorded indicator input (tests/fixtures/indicators) in the day's briefing; a failed Pulse step nulls every context value
        import indicators
        with tempfile.TemporaryDirectory() as d:
            web = os.path.join(d, 'web'); shutil.copytree(WEB, web)
            p = os.path.join(web, 'briefing.json'); B0 = json.loads(read(p)); since = manifest.sp_date(B0['generated_at'])
            S = json.loads(read(os.path.join(ROOT, 'tests', 'fixtures', 'indicators', 'stored_2026-10-18.json')))
            ctx, views = indicators.panels(S)
            B0['panels'] = [x for x in B0['panels'] if x['id'] == 'risk'] + [
                {'id': 'jobs', 'name': 'Jobs', 'form': 'panel', 'reading': 'no qualified source', 'context_note': indicators.CONTEXT_NOTE, 'context': ctx}, views]
            with open(p, 'w') as f: json.dump(B0, f, ensure_ascii=False)
            with open(os.path.join(web, 'checks', 'pulse-failed.json'), 'w') as f:
                json.dump({'at': pulse.iso(pulse.parse_dt(B0['generated_at']) + timedelta(days=1)), 'run': '4243'}, f)
            r = compose(d); self.assertEqual(r.returncode, 0, r.stderr)
            B = json.loads(read(p)); P = {x['id']: x for x in B['panels']}
            why = f'insufficient data: stale since {since}, the Pulse step failed in refresh run 4243'
            for x in P['jobs']['context'] + [P['pageviews']]: self.assertIsNone(x['value']); self.assertEqual(x['reason'], why)
            self.assertEqual(P['jobs']['reading'], 'no qualified source')
            g = subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)
            self.assertEqual(g.returncode, 0, g.stderr)
            B['panels'] = B0['panels']                                                     # a stale briefing that carries a view count over
            with open(p, 'w') as f: json.dump(B, f, ensure_ascii=False)
            g = subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)
            self.assertIn('briefing.json: stale briefing carries a value over (records, Top 10 and gauge values stay empty) at 1 place, e.g. stale', findings(g))

    def test_a_marker_without_the_run_is_refused_and_nothing_is_written(self):
        with tempfile.TemporaryDirectory() as d:
            web = os.path.join(d, 'web'); shutil.copytree(WEB, web)
            with open(os.path.join(web, 'checks', 'pulse-failed.json'), 'w') as f: json.dump({'at': 'yesterday'}, f)
            r = compose(d); self.assertNotEqual(r.returncode, 0)
            self.assertEqual(read(os.path.join(web, 'briefing.json')), read(os.path.join(WEB, 'briefing.json')))


if __name__ == '__main__':
    unittest.main()
