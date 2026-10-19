"""Hub check (hub.py): models of a story's release name under the organisations hub_orgs.json lists. Offline only: every case reads the
input recorded by one bounded live fetch on 2026-10-19 (tests/fixtures/hub/stored_2026-10-19.json) or a fake transport. A name not
searched, or whose search failed, reads "not fetched", never 0; a story without a release name reads "no release name"; the same input
gives the same reading; --relink reuses only the same run's stored input; check_page accepts listed organisations only."""
import contextlib, io, json, os, shutil, subprocess, sys, tempfile, unittest, urllib.error
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.dirname(os.path.abspath(__file__))]
import hub as HUB
import pulse

FIX = os.path.join(ROOT, 'tests', 'fixtures', 'hub', 'stored_2026-10-19.json')
NOW = datetime(2026, 10, 19, 0, 43, 43, tzinfo=timezone.utc)

def stored():
    with open(FIX, encoding='utf-8') as f: return json.load(f)

class Matcher(unittest.TestCase):
    def test_words_and_numbers_in_order_and_a_version_exactly(self):
        for name, model, want in [('Qwen 3', 'Qwen3-235B-A22B', True), ('Qwen 3', 'Qwen3-8B', True), ('Qwen 3', 'Qwen3.8-27B', False),
                                  ('Qwen 3', 'Qwen3.8-Flash-Next-A3B', False), ('Qwen 3', 'Qwen3.5-35B', False), ('Qwen 3.8', 'Qwen3.8-27B-FP8', True),
                                  ('DeepSeek 4.1 Flash', 'DeepSeek-V4.1-Flash-1017', True), ('Flux 3 Klein', 'flux-3-image-klein', True),
                                  ('Muse Spark', 'Muse-Spark-Open-816B-A42B', True), ('Nemotron 3.5 Super', 'NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-BF16', True),
                                  ('Gemma 4', 'gemma-4-31B-it', True), ('Gemma 4', 'codegemma-4-7b', False), ('Gemma 4', 'gemma-3-4b-it', False),
                                  ('Minimax H3', 'MiniMax-H3', True), ('Minimax H3', 'MiniMax-H30', False), ('Gemini 4', 'gemma-4-31B-it', False),
                                  ('GPT 5.5', 'gpt-oss-120b', False), ('Ars Technica', 'gemma-4-31B-it', False),
                                  ('Gemma 2', 'gemma-2b-it', False), ('Krea 2', 'krea-2b', False), ('Gemma 2', 'gemma-2-9b-it', True),
                                  ('Muse Spark', 'museum-sparkle', False), ('DeepSeek 4', 'DeepSeek-V4-Flash', True)]:
            with self.subTest(name=name, model=model):
                self.assertEqual(bool(HUB.name_rx(name).search(model.lower())), want)
        self.assertIsNone(HUB.name_rx('—')); self.assertIsNone(HUB.name_rx('通义'))
        self.assertIsNone(HUB.name_rx('TypeScript')); self.assertIsNone(HUB.name_rx('ComfyUI'))       # one word, no number: not a release name
        for name in ('Krea 2', 'Muse Spark', 'MOSS-Image', 'H3', '5090'): self.assertIsNotNone(HUB.name_rx(name), name)

class Reading(unittest.TestCase):
    def test_recorded_input_names_listed_organisations_only(self):
        S = stored(); orgs = HUB.config()['orgs']
        self.assertEqual(set(S), {'fetched_at', 'inputs', 'errors'})
        for name, models in S['inputs'].items():
            for m in models: self.assertEqual(set(m), {'id', 'created', 'downloads', 'likes'}); self.assertIn(m['id'].split('/')[0], orgs)
        r = HUB.reading(S, 'Muse Spark')
        self.assertEqual(r['n'], 3)
        self.assertEqual([(m['id'], m['org']) for m in r['models']][:2], [('meta-models/Muse-Spark-Open-816B-A42B-NVFP4', 'Meta Inc.'),
                                                                           ('meta-models/Muse-Spark-Open-816B-A42B', 'Meta Inc.')])
        self.assertEqual(set(r['models'][0]), {'id', 'org', 'created', 'downloads_30d', 'likes'})

    def test_at_most_five_shown_most_downloaded_first(self):
        r = HUB.reading(stored(), 'Gemma 4')
        self.assertGreater(r['n'], 5); self.assertEqual(len(r['models']), 5)
        d = [m['downloads_30d'] for m in r['models']]; self.assertEqual(d, sorted(d, reverse=True))

    def test_states_never_an_invented_zero(self):
        S = stored()
        self.assertEqual(HUB.reading(S, None), HUB.NO_NAME)
        self.assertEqual(HUB.reading(None, 'Muse Spark'), HUB.NOT_FETCHED)                  # not fetched in this run
        self.assertEqual(HUB.reading(S, 'A name never searched'), HUB.NOT_FETCHED)
        S['errors']['Muse Spark'] = 'HTTP 429'; del S['inputs']['Muse Spark']
        self.assertEqual(HUB.reading(S, 'Muse Spark'), HUB.NOT_FETCHED)                     # a failed search
        self.assertEqual(HUB.reading(S, 'Gemini 4'), {'n': 0, 'models': []})              # searched: none under a listed organisation
        S['inputs']['通义'] = []
        self.assertEqual(HUB.reading(S, '通义'), HUB.NOT_FETCHED)                            # not a searchable name

    def test_same_input_same_reading(self):
        self.assertEqual(json.dumps(HUB.reading(stored(), 'Qwen 3.8')), json.dumps(HUB.reading(stored(), 'Qwen 3.8')))

class Fetch(unittest.TestCase):
    def test_keeps_listed_organisations_and_four_fields_only(self):
        seen = []
        def get(url, deadline, token):
            seen.append((url, token))
            if 'Broken' in url: raise urllib.error.HTTPError(url, 503, 'Service Unavailable', {}, io.BytesIO(b'{"error":"internal detail"}'))
            if 'Slow' in url: raise TimeoutError('time budget spent')
            if 'Odd' in url: return {'error': 'not a list'}
            return [{'id': 'Qwen/Qwen3.8-27B', 'createdAt': '2026-08-13T08:01:58.000Z', 'downloads': 7, 'likes': 2, 'cardData': {'x': 1}},
                    {'id': 'someone/Qwen3.8-27B-GGUF', 'createdAt': '2026-08-14T00:00:00.000Z', 'downloads': 9, 'likes': 1}, 'junk']
        S = HUB.fetch(['Qwen 3.8', 'Broken 1', '通义', 'TypeScript', 'Slow 2', 'Odd 3', 'Qwen 3.8'], NOW, get=get, token='t')
        self.assertEqual(S['fetched_at'], '2026-10-19T00:43:43Z')
        self.assertEqual(S['inputs'], {'Qwen 3.8': [{'id': 'Qwen/Qwen3.8-27B', 'created': '2026-08-13T08:01:58.000Z', 'downloads': 7, 'likes': 2}]})
        self.assertEqual(S['errors'], {'Broken 1': 'HTTP 503', 'Slow 2': 'TimeoutError', 'Odd 3': 'unexpected response'})   # never a body, never an invented 0
        self.assertEqual([u.split('search=')[1].split('&')[0] for u, _ in seen], ['Qwen+3.8', 'Broken+1', 'Slow+2', 'Odd+3'])   # given order, once each, 通义 and TypeScript skipped
        self.assertTrue(all(t == 't' for _, t in seen))
        self.assertIn('sort=downloads', seen[0][0]); self.assertIn('limit=100', seen[0][0])
        self.assertEqual(HUB.source_status(S), {HUB.NAME: {'status': 'partial', 'detail': '1 of 4 release names searched'}})
        self.assertEqual(HUB.source_status(None)[HUB.NAME]['status'], 'not fetched')

class Briefing(unittest.TestCase):
    now = datetime(2026, 10, 17, 8, 25, tzinfo=timezone.utc)
    def story(self, **over):
        s = {'id': 's:aaaaaaaaaaaa', 'label': 'Muse Spark', 'covered': True, 'kind': 'news', 'pain': 0.0, 'headline': 'Muse Spark Open is out',
             'first': '2026-10-17T01:00:00Z', 'last': '2026-10-17T07:00:00Z', 'voices': 4, 'nets': {'HN': 1}, 'newsletters': [], 'official': False,
             'hn_points': 120, 'key': ['muse'], 'tags': [], 'heat': 3.0, 'refs': {'repos': [], 'papers': []}}
        s.update(over); return s

    def test_records_and_gauge_carry_the_hub_reading(self):
        src = {a: {'status': 'ok', 'detail': 'fixture'} for a in pulse.ADAPTERS}
        stories = [self.story(), self.story(id='s:bbbbbbbbbbbb', label=None)]
        B = pulse.briefing(stories, [], src, None, self.now, 'm', hub=stored())
        a, b = B['records']
        self.assertEqual(a['substance']['hub']['n'], 3); self.assertEqual(b['substance']['hub'], HUB.NO_NAME)
        rows = {x['id']: x for x in B['gauges'][1]['value']['stories']}
        self.assertEqual((rows['s:aaaaaaaaaaaa']['substance']['hub'], rows['s:bbbbbbbbbbbb']['substance']['hub']), (3, HUB.NO_NAME))
        self.assertEqual(B['method']['hub'], HUB.METHOD)
        self.assertEqual(pulse.briefing(stories, [], src, None, self.now, 'm')['records'][0]['substance']['hub'], HUB.NOT_FETCHED)
        self.assertIn('hub_orgs.json', pulse.CONFIG_FILES)

class Relink(unittest.TestCase):
    """--relink reuses history/hub.json only when it is the same run's; --offline never reads it."""
    def run_pulse(self, d, mode, now):
        web, hist = os.path.join(d, 'web'), os.path.join(d, 'history')
        keep = {k: getattr(pulse, k) for k in ('WEB', 'HIST', 'DB', 'CANDIDATES', 'NOW')}
        argv, sources = sys.argv, dict(pulse.SOURCES)
        try:
            pulse.WEB, pulse.HIST, pulse.DB = web, hist, os.path.join(hist, 'signals.sqlite')
            pulse.CANDIDATES = os.path.join(hist, 'mastodon-candidates.json'); pulse.NOW = now
            pulse.SOURCES.clear(); sys.argv = ['pulse.py', mode]
            with contextlib.redirect_stdout(io.StringIO()): pulse.main()
        finally:
            for k, v in keep.items(): setattr(pulse, k, v)
            sys.argv = argv; pulse.SOURCES.clear(); pulse.SOURCES.update(sources)
        return json.load(open(os.path.join(web, 'briefing.json'), encoding='utf-8'))

    def test_relink_reuses_the_same_runs_input_only(self):
        import test_pulse
        with tempfile.TemporaryDirectory() as d:
            web = test_pulse.offline_rebuild(d)
            P = json.load(open(os.path.join(web, 'pulse.json')))
            names = sorted({s['label'] for s in P['stories'] if s.get('label') and HUB.name_rx(s['label'])})
            S = {'fetched_at': P['generated_at'], 'inputs': {n: [] for n in names}, 'errors': {}}
            with open(os.path.join(d, 'history', 'hub.json'), 'w') as f: json.dump(S, f)
            later = pulse.parse_dt(P['generated_at'])
            hubs = lambda B: {r['substance']['hub'] if isinstance(r['substance']['hub'], str) else 'searched' for r in B['records'] if r['release'] in names}
            self.assertTrue(names)                                                          # the fixture has release names
            skipped = {s['label'] for s in P['stories'] if s.get('label') and not HUB.name_rx(s['label'])}
            B = self.run_pulse(d, '--relink', later)
            self.assertEqual(hubs(B), {'searched'})
            self.assertLessEqual({r['substance']['hub'] for r in B['records'] if r['release'] in skipped}, {HUB.NOT_FETCHED})   # one word, no number
            S['fetched_at'] = '2026-10-01T00:00:00Z'                                         # another run's input: not shown
            with open(os.path.join(d, 'history', 'hub.json'), 'w') as f: json.dump(S, f)
            B = self.run_pulse(d, '--relink', later)
            self.assertLessEqual(hubs(B), {HUB.NOT_FETCHED})
            B = self.run_pulse(d, '--offline', later)
            self.assertLessEqual(hubs(B), {HUB.NOT_FETCHED})
            self.assertEqual(B['sources'][HUB.NAME], {'status': 'unknown', 'detail': 'not fetched in this offline rebuild'})

class LiveRun(unittest.TestCase):
    def test_a_failing_check_leaves_the_briefing_built_and_says_so(self):
        import test_pulse
        def broken(names, now, **k): raise OSError('hub_orgs.json unreadable')
        with tempfile.TemporaryDirectory() as d:
            web, log, _ = test_pulse.pulse_run(d, hub=broken)
            B = json.load(open(os.path.join(web, 'briefing.json'), encoding='utf-8'))
        self.assertEqual(B['sources'][HUB.NAME], {'status': 'failed', 'detail': 'OSError (not fetched; no earlier value shown)'})
        self.assertLessEqual({r['substance']['hub'] for r in B['records'] if r['release']}, {HUB.NOT_FETCHED})

    def test_relink_after_a_failed_check_keeps_the_failure(self):
        import test_pulse
        def broken(names, now, **k): raise OSError('hub_orgs.json unreadable')
        with tempfile.TemporaryDirectory() as d:
            test_pulse.pulse_run(d, hub=broken)
            web, _, _ = test_pulse.pulse_run(d, ['--relink'], hub=broken)
            with open(os.path.join(web, 'briefing.json'), encoding='utf-8') as f: B = json.load(f)
        self.assertEqual(B['sources'][HUB.NAME]['status'], 'failed')

@unittest.skipUnless(shutil.which('node'), 'node not installed')
class Gate(unittest.TestCase):
    def check(self, mutate):
        with tempfile.TemporaryDirectory() as d:
            web = os.path.join(d, 'web'); shutil.copytree(os.path.join(ROOT, 'web'), web)
            B = json.load(open(os.path.join(web, 'briefing.json'), encoding='utf-8'))
            S = stored()
            for r in B['records']: r['substance']['hub'] = HUB.reading(S, r['release'])
            for row in B['gauges'][1]['value']['stories']:
                h = next(r for r in B['records'] if r['id'] == row['id'])['substance']['hub']
                row['substance']['hub'] = h['n'] if isinstance(h, dict) else h
            B['sources'].update(HUB.source_status(S))
            mutate(B)
            with open(os.path.join(web, 'briefing.json'), 'w', encoding='utf-8') as f: json.dump(B, f, ensure_ascii=False)
            return subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)

    def test_a_briefing_with_hub_readings_passes(self):
        r = self.check(lambda B: None)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_an_unlisted_account_fails(self):
        def person(B):
            rec = next(r for r in B['records'] if isinstance(r['substance']['hub'], dict) and r['substance']['hub']['n'])
            rec['substance']['hub']['models'][0]['id'] = 'some-person/Muse-Spark-GGUF'
        r = self.check(person)
        self.assertNotEqual(r.returncode, 0); self.assertIn('listed-organisation models', r.stderr + r.stdout)

    def test_a_record_without_its_reading_fails_once_the_method_is_there(self):
        def drop(B): B['method']['hub'] = HUB.METHOD; del B['records'][0]['substance']['hub']
        r = self.check(drop)
        self.assertNotEqual(r.returncode, 0); self.assertIn('lacks its Hub reading', r.stderr + r.stdout)

    def test_no_release_name_on_a_named_story_fails(self):
        def lie(B): next(r for r in B['records'] if r['release'])['substance']['hub'] = HUB.NO_NAME
        r = self.check(lie)
        self.assertNotEqual(r.returncode, 0); self.assertIn('reads "no release name"', r.stderr + r.stdout)

if __name__ == '__main__':
    unittest.main()
