"""Context panels (indicators.py): BLS v1, HN "Who is hiring?" and Wikipedia page views. Offline only: every case reads the input
recorded by one bounded live fetch on 2026-10-18 (tests/fixtures/indicators/stored_2026-10-18.json) or a fake transport built from it.
A source that failed or was not fetched reads null with its reason, never 0; the same input gives the same panels; --relink reuses only
the same run's stored input."""
import contextlib, copy, io, json, os, shutil, subprocess, sys, tempfile, time, unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.dirname(os.path.abspath(__file__))]
import indicators as IND
import pulse

FIX = os.path.join(ROOT, 'tests', 'fixtures', 'indicators', 'stored_2026-10-18.json')
NOW = datetime(2026, 10, 18, 15, 56, 5, tzinfo=timezone.utc)

def stored(): return json.load(open(FIX, encoding='utf-8'))

def item(children):                                       # an Algolia items/<id> tree: synthetic posts, no real post text or author
    return {'id': 7, 'children': [dict(c, parent_id=c.get('parent_id', 7)) for c in children]}

class PanelsFromTheRecordedInput(unittest.TestCase):
    def setUp(self): self.ctx, self.views = IND.panels(stored())

    def test_bls_series_latest_month_year_earlier_and_notice(self):
        b = self.ctx[0]
        self.assertEqual((b['id'], b['status'], b['retrieved'], b['notice']), ('bls', pulse.PREVIEW, '2026-10-18', IND.BLS_NOTICE))
        self.assertEqual(b['coverage'], {'sources': {'BLS (public API v1)': 'ok'}, 'series_read': 6, 'series_listed': 6})
        S = {r['id']: r for r in b['value']['series']}
        self.assertEqual(list(S), [s['id'] for s in IND.config()['bls']['series']])
        self.assertEqual((S['CES5051320001']['period'], S['CES5051320001']['value'], S['CES5051320001']['preliminary']), ('2026-08', 652.9, True))
        self.assertEqual(S['CES5051320001']['year_earlier'], {'period': '2025-08', 'value': 656.3})       # its own month: software publishers lag one
        self.assertEqual((S['CES0000000001']['period'], S['CES0000000001']['value']), ('2026-09', 159044.0))
        self.assertEqual((S['LNS14000000']['unit'], S['LNS14000000']['value']), ('percent', 4.2))
        self.assertTrue(b['terms']['urls'] and b['terms']['read'] == '2026-10-18')

    def test_hn_hiring_counts_only_and_share(self):
        h = self.ctx[1]
        self.assertEqual(h['value']['months'], [
            {'month': '2026-10', 'thread': 'https://news.ycombinator.com/item?id=49922569', 'posts': 266, 'ai_posts': 158, 'share': 0.594},
            {'month': '2026-09', 'thread': 'https://news.ycombinator.com/item?id=49522897', 'posts': 251, 'ai_posts': 156, 'share': 0.622}])
        self.assertNotIn('author', json.dumps(stored()['inputs']['hn_hiring']))

    def test_wikipedia_two_windows_from_the_newest_day_no_ratio(self):
        v = self.views
        self.assertEqual((v['id'], v['name'], v['coverage']['agent']), ('pageviews', 'Page views on Wikipedia (AI articles)', 'user'))
        en, pt = v['value']['projects']
        self.assertEqual((en['window'], en['prior_window']), ({'start': '2026-10-09', 'end': '2026-10-15'}, {'start': '2026-10-02', 'end': '2026-10-08'}))
        self.assertEqual((en['views_7d'], en['views_prior_7d'], pt['views_7d'], pt['views_prior_7d']), (188415, 190198, 4791, 5646))
        self.assertEqual(sum(a['views_7d'] for a in en['articles']), en['views_7d'])
        self.assertEqual({a['lang'] for a in pt['articles']}, {'pt'})
        for k in ('ratio', 'trend', 'delta', 'change'): self.assertNotIn(k, json.dumps(v))

    def test_same_input_same_panels(self):
        self.assertEqual(json.dumps(IND.panels(stored())), json.dumps(IND.panels(copy.deepcopy(stored()))))

    def test_source_status_details(self):
        self.assertEqual(IND.source_status(stored()), {
            'BLS (public API v1)': {'status': 'ok', 'detail': '6 of 6 series read'},
            'Hacker News "Who is hiring?" (Algolia)': {'status': 'ok', 'detail': '2 of 2 hiring threads read'},
            'Wikipedia page views (Wikimedia REST)': {'status': 'ok', 'detail': '14 of 14 articles read'}})

class BelowTheFloor(unittest.TestCase):
    def test_not_fetched_reads_null_never_zero(self):
        ctx, views = IND.panels(None)
        for x in ctx + [views]:
            self.assertIsNone(x['value']); self.assertEqual(x['reason'], 'insufficient data: not fetched in this run')
            self.assertIsNone(x['retrieved']); self.assertEqual(set(x['coverage']['sources'].values()), {'not fetched'})
        self.assertEqual(ctx[0]['coverage']['series_read'], 'not fetched')

    def test_a_failed_source_reads_null_with_its_reason(self):
        S = stored(); del S['inputs']['bls']; S['errors']['bls'] = 'URLError: <urlopen error timed out>'
        b = IND.panels(S)[0][0]
        self.assertIsNone(b['value']); self.assertEqual(b['reason'], 'insufficient data: the source failed in this run (URLError: <urlopen error timed out>)')
        self.assertEqual(IND.source_status(S)['BLS (public API v1)'], {'status': 'failed', 'detail': 'URLError: <urlopen error timed out> (not fetched; no earlier value shown)'})
        self.assertEqual(IND.panels(S)[0][1]['coverage']['sources'], {'Hacker News "Who is hiring?" (Algolia)': 'ok'})     # the others stand

    def test_a_missing_day_nulls_that_project_only(self):
        S = stored(); S['inputs']['wikipedia']['projects']['pt.wikipedia']['Aprendizagem_profunda']['items'].pop(-3)
        en, pt = IND.panels(S)[1]['value']['projects']
        self.assertEqual(en['views_7d'], 188415)
        self.assertEqual((pt['views_7d'], pt['views_prior_7d'], pt['reason']), (None, None, 'insufficient data: 6 of 7 articles had all 14 days in the response'))
        S['inputs']['wikipedia']['projects']['pt.wikipedia']['Inteligência_artificial'] = {'error': 'HTTPError: HTTP Error 404: Not Found'}
        self.assertEqual(IND.source_status(S)['Wikipedia page views (Wikimedia REST)'], {'status': 'partial', 'detail': '13 of 14 articles read'})

    def test_a_missing_bls_series_is_null_with_reason(self):
        S = stored(); R = S['inputs']['bls']['response']['Results']['series']; R[:] = [x for x in R if x['seriesID'] != 'LNS14000000']
        b = IND.panels(S)[0][0]
        row = next(r for r in b['value']['series'] if r['id'] == 'LNS14000000')
        self.assertEqual((row['value'], row['reason']), (None, 'insufficient data: the series was not in the response'))
        self.assertEqual((b['coverage']['series_read'], b['coverage']['sources']['BLS (public API v1)']), (5, 'partial'))

class HiringCounts(unittest.TestCase):
    def test_top_level_posts_with_text_and_ai_terms(self):
        cfg = IND.config()['hn_hiring']
        posts = [{'text': 'Acme | Backend engineer | we build <i>AI</i>-native tools'}, {'text': 'Beta | HTML and CSS developer'},
                 {'text': 'Gamma | partner of OpenAI | data engineer'}, {'text': 'Delta | ML platform'}, {'text': 'Eps | <p>machine&#x20;learning</p>'},
                 {'text': 'Zeta | said ai in lower case'}, {'text': None}, {'text': 'reply about AI', 'parent_id': 99}]
        self.assertEqual(IND.hiring_counts(item(posts), cfg), (6, 3))           # deleted and nested posts left out; "AI" is case-sensitive

class Fetch(unittest.TestCase):
    """fetch_all over a fake transport replaying the recorded responses: the parallel path, the budget and the stored shape."""
    def fake(self, S):
        hn = {'hits': [{'objectID': str(t['id']), 'title': t['title'], 'created_at': t['created_at']} for t in S['inputs']['hn_hiring']['threads']]
              + [{'objectID': '1', 'title': 'Ask HN: Who wants to be hired? (October 2026)', 'created_at': '2026-10-01T15:02:07Z'}]}
        trees = {t['id']: item([{'text': 'AI'}] * t['ai_posts'] + [{'text': 'Rust'}] * (t['posts'] - t['ai_posts'])) for t in S['inputs']['hn_hiring']['threads']}
        def get(url, deadline, data=None):
            if 'api.bls.gov' in url: self.assertEqual(json.loads(data)['seriesid'][0], 'CES0000000001'); return S['inputs']['bls']['response']
            if 'search_by_date' in url: return hn
            if '/items/' in url:
                i = int(url.rsplit('/', 1)[1]); t = trees[i]; t['id'] = i
                for c in t['children']: c['parent_id'] = i
                return t
            proj, art = url.split('/per-article/')[1].split('/')[0], urllib_unquote(url.split('/user/')[1].split('/')[0])
            return {'items': S['inputs']['wikipedia']['projects'][proj][art]['items']}
        return get

    def test_fetch_all_replays_to_the_recorded_panels(self):
        S = stored()
        got = IND.fetch_all(NOW, get=self.fake(S))
        self.assertEqual(got['errors'], {})
        self.assertEqual(got['inputs']['hn_hiring'], S['inputs']['hn_hiring'])
        self.assertEqual(json.dumps(IND.panels(got)), json.dumps(IND.panels(S)))

    def test_a_spent_budget_records_errors_never_values(self):
        def slow(url, deadline, data=None):
            time.sleep(0.3); raise TimeoutError('time budget spent')
        t = time.monotonic(); got = IND.fetch_all(NOW, get=slow, budget=2)
        self.assertLess(time.monotonic() - t, 10)
        self.assertLessEqual({'bls', 'hn_hiring'}, set(got['errors']))
        ctx, views = IND.panels(got)
        self.assertIsNone(ctx[0]['value']); self.assertIsNone(ctx[1]['value']); self.assertIsNone(views['value'])
        self.assertTrue(views['reason'].startswith('insufficient data: '))

def urllib_unquote(s):
    import urllib.parse; return urllib.parse.unquote(s)

class Relink(unittest.TestCase):
    """--relink reuses history/indicators.json only when it is the same run's (its fetched_at equals the pulse.json it rebuilds over)."""
    def run_pulse(self, d, mode, now):
        import test_pulse
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
            S = stored(); S['fetched_at'] = P['generated_at']
            with open(os.path.join(d, 'history', 'indicators.json'), 'w') as f: json.dump(S, f)
            later = pulse.parse_dt(P['generated_at'])
            B = self.run_pulse(d, '--relink', later)
            self.assertEqual(B['panels'][2]['value']['projects'][0]['views_7d'], 188415)
            self.assertEqual(B['panels'][1]['context'][0]['retrieved'], P['generated_at'][:10])
            S['fetched_at'] = '2026-10-01T00:00:00Z'                                    # another run's input: not shown
            with open(os.path.join(d, 'history', 'indicators.json'), 'w') as f: json.dump(S, f)
            B = self.run_pulse(d, '--relink', later)
            self.assertIsNone(B['panels'][2]['value']); self.assertEqual(B['panels'][2]['reason'], 'insufficient data: not fetched in this run')
            B = self.run_pulse(d, '--offline', later)                                  # an offline rebuild never reads the stored input
            self.assertIsNone(B['panels'][1]['context'][0]['value'])
            self.assertEqual(B['sources']['BLS (public API v1)'], {'status': 'unknown', 'detail': 'not fetched in this offline rebuild'})

@unittest.skipUnless(shutil.which('node'), 'node not installed')
class Gate(unittest.TestCase):
    def test_a_briefing_with_the_recorded_panels_passes_check_page(self):
        with tempfile.TemporaryDirectory() as d:
            web = os.path.join(d, 'web'); shutil.copytree(os.path.join(ROOT, 'web'), web)
            B = json.load(open(os.path.join(web, 'briefing.json'), encoding='utf-8'))
            ctx, views = IND.panels(stored())
            B['panels'] = [p for p in B['panels'] if p['id'] == 'risk'] + [
                {'id': 'jobs', 'name': 'Jobs', 'form': 'panel', 'reading': 'no qualified source', 'context_note': IND.CONTEXT_NOTE, 'context': ctx}, views]
            B['sources'].update(IND.source_status(stored()))
            with open(os.path.join(web, 'briefing.json'), 'w', encoding='utf-8') as f: json.dump(B, f, ensure_ascii=False)
            r = subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

if __name__ == '__main__':
    unittest.main()
