"""Feeds and the one-shot Cordis composition (design rows 15, 16; C1, C14, C17, C18, C43; SC-16, SC-17 and the feed parts of SC-10
and SC-13; group D). The structural validator reads the four built feeds with no network: RSS 2.0 and JSON Feed 1.1, each required
element named, the same ids and headlines in both languages, the stable id, the verdict state and the source links on every item.
The composition cases run scripts/dehype/compose.mjs (pinned @deepseek-ai/cordis 4.0.4) on scratch copies; the leak cases follow
Decision 14 (an overlay of the committed web/, check_page.mjs failing with that rule's own finding)."""
import email.utils, hashlib, json, os, re, shutil, subprocess, sys, tempfile, unittest
import xml.etree.ElementTree as ET
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_i18n import check_page, findings
import test_pulse


def read(path):
    with open(path, 'rb') as f: return f.read()


WEB, DH = os.path.join(ROOT, 'web'), os.path.join(ROOT, 'scripts', 'dehype')
FEEDS = {'en': ('feed.xml', 'feed.json'), 'pt': ('feed.pt.xml', 'feed.pt.json')}
OUT = ('feed.xml', 'feed.json', 'feed.pt.xml', 'feed.pt.json', 'i18n/table.en.json', 'i18n/table.pt.json')
CODE = {'en': 'en', 'pt': 'pt-BR'}
SID = re.compile(r'^s:[0-9a-f]{12}$')
SITE = 'https://namastex888.github.io/dehype/'
COUNT_ONLY_URL = re.compile(r'https?://(?:[\w-]+\.)*(?:reddit\.com|redd\.it|x\.com|twitter\.com|linkedin\.com|youtube\.com|youtu\.be|t\.me|discord\.com|discord\.gg|mastodon\.social)[/:?#]', re.I)
S = json.loads(read(os.path.join(WEB, 'i18n', 'strings.json')))['strings']
# CI installs the pinned tree before the tests (ci.yml); a local run without `npm ci --prefix scripts/dehype` skips the compose cases
need_cordis = unittest.skipUnless(os.path.isdir(os.path.join(DH, 'node_modules', '@deepseek-ai', 'cordis')) or os.environ.get('CI'),
                                  'npm ci --prefix scripts/dehype --ignore-scripts first')


def rss(text):
    root = ET.fromstring(text)
    ch = root.findall('channel')
    return root, ch, [{c.tag: c for c in it} | {'_cats': it.findall('category')} for it in (ch[0].findall('item') if ch else [])]


def rfc3339(s):
    d = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if d.tzinfo is None: raise ValueError('no offset')
    return d


def compose(d, script=None):
    """compose.mjs with d as the repository root (it reads and writes d/web)."""
    return subprocess.run(['node', script or os.path.join(DH, 'compose.mjs')], cwd=d, capture_output=True, text=True)


def scratch(d, web=None):
    """d/web: a copy of the committed web/ (or web with the committed i18n/ beside its files) for compose.mjs."""
    dst = os.path.join(d, 'web')
    if web is None: shutil.copytree(WEB, dst)
    elif os.path.abspath(web) != dst: shutil.copytree(web, dst)
    if not os.path.isdir(os.path.join(dst, 'i18n')): shutil.copytree(os.path.join(WEB, 'i18n'), os.path.join(dst, 'i18n'))
    return dst


def xesc(u): return re.sub(r'[&<>"\']', lambda m: {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;'}[m[0]], u)


def owner_rows():
    """{story id: owner row}, resolved through story-aliases.json as web/dehype.js verdicts() and feed.mjs do."""
    V = json.loads(read(os.path.join(WEB, 'verdicts.json'))); A = json.loads(read(os.path.join(WEB, 'story-aliases.json'))).get('aliases', {})
    def to(i):
        seen = [i]
        while A.get(seen[-1], {}).get('to') and A[seen[-1]]['to'] not in seen: seen.append(A[seen[-1]]['to'])
        return seen[-1]
    m = {}
    for r in V.get('rows', []):
        m[to(r['id'])] = r
        m.setdefault(r['id'], r)
    return m


def feeds(web):
    return {f: read(os.path.join(web, f)) for pair in FEEDS.values() for f in pair}


class FeedFormatTest(unittest.TestCase):
    """SC-16 on the four committed feed files."""
    @classmethod
    def setUpClass(cls):
        cls.F = feeds(WEB)
        cls.B = json.loads(read(os.path.join(WEB, 'briefing.json')))

    def assert_rss(self, text, lang, J):
        root, ch, items = rss(text)
        self.assertEqual((root.tag, root.get('version')), ('rss', '2.0'))
        self.assertEqual(len(ch), 1)
        for k in ('title', 'link', 'description', 'language'): self.assertTrue((ch[0].findtext(k) or '').strip(), k)
        self.assertEqual(ch[0].findtext('language'), CODE[lang])
        for it, j in zip(items, J['items'], strict=True):
            for k in ('title', 'link', 'guid', 'pubDate', 'description'): self.assertTrue((it[k].text or '').strip(), k)
            self.assertEqual(it['guid'].get('isPermaLink'), 'false')
            self.assertRegex(it['guid'].text, SID)
            self.assertIsNotNone(email.utils.parsedate_to_datetime(it['pubDate'].text).tzinfo)       # RFC 822
            self.assertEqual([c.text for c in it['_cats']], [j['_dehype']['verdict']['text']])          # the verdict state
            self.assertTrue(it['link'].text.startswith(SITE) and it['link'].text.endswith('#' + it['guid'].text))
            for s in j['_dehype']['sources']: self.assertIn(f'href="{xesc(s["url"])}"', it['description'].text)   # the source links
        return [(it['guid'].text, it['title'].text) for it in items]

    def assert_json(self, J, lang):
        self.assertEqual(J['version'], 'https://jsonfeed.org/version/1.1')
        self.assertTrue(J['title'].strip()); self.assertEqual(J['language'], CODE[lang]); self.assertIsInstance(J['items'], list)
        for it in J['items']:
            self.assertIsInstance(it['id'], str); self.assertRegex(it['id'], SID)
            self.assertTrue(it['url'].startswith(SITE) and it['url'].endswith('#' + it['id']))
            self.assertTrue(it['content_text'].strip()); rfc3339(it['date_published'])
            x = it['_dehype']
            self.assertEqual(x['id'], it['id'])
            self.assertIn(x['verdict']['state'], ('proposed', 'confirmed'))
            self.assertTrue(x['verdict']['text'])
            self.assertIsInstance(x['sources'], list)
            for s in x['sources']:
                self.assertRegex(s['url'], r'^https?://'); self.assertIn(s['url'], it['content_text'])
        return [(it['id'], it['title']) for it in J['items']]

    def test_rss_2_0_and_json_feed_1_1_in_both_languages_with_the_same_ids_and_headlines(self):
        got = {}
        for lang, (x, j) in FEEDS.items():
            J = json.loads(self.F[j])
            got[x], got[j] = self.assert_rss(self.F[x], lang, J), self.assert_json(J, lang)
        self.assertEqual(len({json.dumps(v) for v in got.values()}), 1, got)                      # same ids, order and headlines
        recs = {r['id']: r for r in self.B['records']}
        self.assertEqual(got['feed.json'], [(t['id'], recs[t['id']]['headline']) for t in self.B['top10']])   # the briefing's Top 10, as posted

    def test_every_item_reads_proposed_until_an_owner_row(self):
        rows = owner_rows()
        for lang, (x, j) in FEEDS.items():
            want = {}
            for it in json.loads(self.F[j])['items']:
                r = rows.get(it['id']); v = it['_dehype']['verdict']
                if r: self.assertEqual((v['state'], v['label'], v['text']), ('confirmed', r['label'], S['label.' + r['label'].lower()][lang]))
                else: self.assertEqual(v, {'state': 'proposed', 'label': None, 'text': S['state.proposed'][lang]})
                want[it['id']] = v['text']
            self.assertEqual({it['guid'].text: it['_cats'][0].text for it in rss(self.F[x])[2]}, want)

    def test_headline_lang_no_count_only_link_no_author(self):
        recs = {r['id']: r for r in self.B['records']}
        for lang, (x, j) in FEEDS.items():
            J = json.loads(self.F[j])
            self.assertEqual([it['language'] for it in J['items']], [recs[it['id']]['lang'] for it in J['items']])
            self.assertEqual([e.text for e in ET.fromstring(self.F[x]).iter('{http://purl.org/dc/elements/1.1/}language')],
                             [it['language'] for it in J['items']])
            for f in (x, j):
                self.assertIsNone(COUNT_ONLY_URL.search(self.F[f].decode()), f)
                self.assertNotIn('"author"', self.F[f].decode())
            self.assertNotIn(b'\n', self.F[j])                                                       # Decision 19: compact, one line


@need_cordis
class ComposeTest(unittest.TestCase):
    """Row 16 and SC-17: compose.mjs on scratch copies; the feed parts of SC-10 and SC-13."""
    def test_committed_outputs_are_what_compose_writes_with_cordis_4_0_4_and_nothing_left_open(self):
        with tempfile.TemporaryDirectory() as d:
            web = scratch(d)
            for f in OUT: os.remove(os.path.join(web, f))
            r = compose(d)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('compose: @deepseek-ai/cordis 4.0.4, plugins dehype-feed and dehype-frontend loaded and disposed', r.stdout)
            self.assertIn('no server, socket or timer left open', r.stdout)
            for f in OUT: self.assertEqual(read(os.path.join(web, f)), read(os.path.join(WEB, f)), f'{f} is stale: run node scripts/dehype/compose.mjs')
            self.assertEqual(sorted(os.listdir(web)), sorted(os.listdir(WEB)))                       # no other file, no temporary left

    def test_tables_carry_every_string_with_its_ref_resolved(self):
        T = {l: json.loads(read(os.path.join(WEB, 'i18n', f'table.{l}.json'))) for l in ('en', 'pt')}
        I = json.loads(read(os.path.join(WEB, 'i18n', 'strings.json')))
        for l, t in T.items():
            self.assertEqual((t['lang'], t['fields'], t['methods'], set(t['strings'])), (l, I['fields'], I['methods'], set(I['strings'])))
        ref = I['strings']['dossier.x_figure_placeholder']['ref'].split('#')
        self.assertEqual(T['pt']['strings']['dossier.x_figure_placeholder'], json.loads(read(os.path.join(WEB, 'i18n', ref[0])))[ref[1]])
        self.assertEqual(T['en']['strings']['state.proposed'], {'en': S['state.proposed']['en']})

    def test_an_owner_row_resolved_through_an_alias_reads_its_label(self):
        B = json.loads(read(os.path.join(WEB, 'briefing.json')))
        if not B['top10']: self.skipTest('the committed briefing has no Top 10 story today')
        top, old = B['top10'][0]['id'], 's:0123456789ab'
        row = {'id': old, 'label': 'OVERHYPED', 'claim': 'c', 'source': 'https://example.org/primary', 'reason': {'en': 'Reason.', 'pt': 'Motivo.'},
               'commit': 'abcdef1', 'confirmed': '2026-10-17'}
        with tempfile.TemporaryDirectory() as d:
            web = scratch(d)
            with open(os.path.join(web, 'verdicts.json'), 'w') as f: json.dump({'rows': [row]}, f)
            with open(os.path.join(web, 'story-aliases.json'), 'w') as f: json.dump({'aliases': {old: {'since': '2026-10-16', 'to': top}}}, f)
            self.assertEqual(compose(d).returncode, 0)
            for lang, (x, j) in FEEDS.items():
                items = json.loads(read(os.path.join(web, j)))['items']
                v = next(it for it in items if it['id'] == top)['_dehype']['verdict']
                self.assertEqual((v['state'], v['label'], v['text'], v['reason']), ('confirmed', 'OVERHYPED', S['label.overhyped'][lang], row['reason'][lang]))
                self.assertEqual({it['_dehype']['verdict']['state'] for it in items if it['id'] != top}, {'proposed'})
                cats = {it['guid'].text: it['_cats'][0].text for it in rss(read(os.path.join(web, x)))[2]}
                self.assertEqual(cats[top], S['label.overhyped'][lang])
            self.assertEqual(S['label.overhyped']['pt'], 'EXAGERADO')

    def test_offline_rebuild_feeds_read_not_fetched_never_false_or_zero(self):
        with tempfile.TemporaryDirectory() as d:
            web = scratch(d, test_pulse.offline_rebuild(d))
            self.assertEqual(compose(d).returncode, 0)
            F = feeds(web)
            for lang, (x, j) in FEEDS.items():
                items = json.loads(F[j])['items']
                hooks = next(it for it in items if 'hookmarket' in it['title'].lower())
                rd = hooks['_dehype']['readings']
                self.assertEqual((rd['official'], rd['newsletters'], rd['networks']['Bluesky']), ('not fetched',) * 3)
                self.assertEqual(set(rd['sources'].values()), {'not fetched'})
                nf = S['reading.not_fetched'][lang]
                for k in ('ui.newsletters', 'ui.lab_post'): self.assertIn(f'{S[k][lang]}: {nf}', hooks['content_text'])
                desc = next(it['description'].text for it in rss(F[x])[2] if it['guid'].text == hooks['id'])
                self.assertIn(f'{S["ui.lab_post"][lang]}: {nf}', desc)
                for it in items:
                    for k, v in it['_dehype']['readings']['networks'].items():
                        if it['_dehype']['readings']['sources'].get(k) != 'ok': self.assertNotIn(v, (0, False), (it['id'], k))
            self.assertEqual(S['reading.not_fetched']['pt'], 'não buscado')

    def test_posts_gone_or_removal_listed_reach_no_feed(self):
        for case in ('stored', 'removal'):
            F = test_pulse.RM[case]
            with tempfile.TemporaryDirectory() as d:
                web, _, _ = test_pulse.pulse_run(d, posts=F['posts'], hype={'items': {}}, removals=F.get('removals', ()),
                                                 passes=F.get('passes', ()), answers=F.get('answers'))
                scratch(d, web)
                self.assertEqual(compose(d).returncode, 0)
                out = b''.join(feeds(web).values()).decode()
                self.assertGreater(len(json.loads(read(os.path.join(web, 'feed.json')))['items']), 0, case)
                if case == 'stored':
                    for w in F['words']['gone'] + F['words']['count']: self.assertNotIn(w, out)
                    for pid in F['gone'].values(): self.assertNotIn(pid, out)
                    self.assertNotIn('statuses/9001', out); self.assertNotIn('item?id=104', out)
                    for w in ('Yankee', 'Quebec'): self.assertIn(w, out)                         # the briefing's one story keeps its live posts
                else:
                    self.assertNotIn('Papa', out); self.assertNotIn('item?id=105', out)
                    for u in F['removals']: self.assertNotIn(u, out)

    def test_a_plugin_failure_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            web = scratch(d)
            B = json.loads(read(os.path.join(web, 'briefing.json'))); B['generated_at'] = 'not a date'
            with open(os.path.join(web, 'briefing.json'), 'w') as f: json.dump(B, f)
            r = compose(d)
            self.assertNotEqual(r.returncode, 0); self.assertIn('generated_at is not a date', r.stderr)
            for f in OUT: self.assertEqual(read(os.path.join(web, f)), read(os.path.join(WEB, f)), f)
            self.assertFalse([f for f in os.listdir(web) if f.endswith('.tmp')])

    def test_another_cordis_version_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            dh = os.path.join(d, 'scripts', 'dehype')
            shutil.copytree(DH, dh, symlinks=True)
            pj = os.path.join(dh, 'node_modules', '@deepseek-ai', 'cordis', 'package.json')
            P = json.loads(read(pj)); P['version'] = '4.0.5'
            with open(pj, 'w') as f: json.dump(P, f)
            scratch(d)
            r = compose(d, os.path.join(dh, 'compose.mjs'))
            self.assertEqual(r.returncode, 1); self.assertIn('@deepseek-ai/cordis 4.0.5 installed, 4.0.4 required', r.stderr)


class FeedLeakTest(unittest.TestCase):
    """Decision 14: the feeds and tables keep the public-data rules in check_page.mjs."""
    @classmethod
    def setUpClass(cls):
        cls.J = json.loads(read(os.path.join(WEB, 'feed.json')))
        cls.X = read(os.path.join(WEB, 'feed.pt.xml')).decode()

    def assert_fails(self, r, *msgs):
        self.assertEqual(r.returncode, 1, r.stdout)
        got = findings(r)
        for m in msgs: self.assertTrue(any(g.startswith(m) for g in got), (m, got))
        self.assertEqual(len(got), len(msgs), got)

    def item(self, **x):
        if not self.J['items']: self.skipTest('the committed feeds have no item today')
        J = json.loads(json.dumps(self.J)); J['items'][0]['_dehype']['sources'].append(x); return {'feed.json': J}

    def test_committed_feeds_and_tables_pass(self):
        r = check_page()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"feeds 4 of 4 ({len(self.J['items'])} items), page tables en and pt", r.stdout)

    def test_each_leak_fails_on_its_own_rule(self):
        self.assert_fails(check_page(self.item(net='own', url='https://www.reddit.com/r/x/comments/abc/t/')), 'feed.json: Reddit link (Reddit is counts only)')
        self.assert_fails(check_page(self.item(net='X', title='a post')), 'feed.json: count-only X record carries title')
        self.assert_fails(check_page({'feed.pt.xml': self.X.replace('<title>', '<title>@someone ', 2)}), 'feed.pt.xml: person handle (@name)')
        self.assert_fails(check_page({'feed.pt.xml': self.X.replace('<link>', '<link>https://x.com/someone/status/1 ', 2)}), 'feed.pt.xml: X link')
        self.assert_fails(check_page(self.item(net='own', url='https://mastodon.social/statuses/1')),                  # 1: never checked
                          'feed.json: Mastodon link without a render check passed less than 7 days before pulse.json generated_at (no check in',
                          'feed.json: Mastodon link in a feed (the feeds count Mastodon posts, never link them)')
        self.assert_fails(check_page({'feed.xml': None}), 'feed.xml missing (scripts/dehype/compose.mjs writes the four feeds)')
        u = 'https://example.org/removed-post'
        self.assert_fails(check_page({**self.item(net='own', url=u), 'removals.json': {'entries': [{'sha256': hashlib.sha256(u.encode()).hexdigest(), 'date': '2026-10-01'}]}}),
                          'feed.json: post named by removals.json is still published')

    def test_tables_and_the_loader(self):
        T = json.loads(read(os.path.join(WEB, 'i18n', 'table.pt.json'))); T['strings']['ui.yes'] = {'en': 'yes'}
        self.assert_fails(check_page({'i18n/table.pt.json': T}), 'i18n/table.pt.json is not the pt page table')
        js = read(os.path.join(WEB, 'dehype.js')).decode()
        self.assertIn('I = await load(TABLE[lang]);', js); self.assertIn('I = await load(TABLE[l]);', js)       # setLang loads the other table
        self.assertNotIn("load('i18n/strings.json')", js)
        self.assert_fails(check_page({'dehype.js': js.replace('load(TABLE[lang])', "load('i18n/table.en.json')").replace('load(TABLE[l])', "load('i18n/table.pt.json')")}), "dehype.js: does not load its language's page table")


class LicenceAndStepTest(unittest.TestCase):
    """C14 and C18: the exact pin, the MIT notice, the licence-closure audit; the refresh step (C42, Decision 7)."""
    def test_pin_lockfile_audit_and_notice_agree(self):
        P = json.loads(read(os.path.join(DH, 'package.json'))); L = json.loads(read(os.path.join(DH, 'package-lock.json')))
        A = json.loads(read(os.path.join(DH, 'licence-closure.json'))); N = read(os.path.join(DH, 'NOTICE')).decode()
        self.assertEqual(P['dependencies'], {'@deepseek-ai/cordis': '4.0.4'})
        c = L['packages']['node_modules/@deepseek-ai/cordis']
        self.assertEqual((c['version'], c['resolved']), ('4.0.4', 'https://registry.npmjs.org/@deepseek-ai/cordis/-/cordis-4.0.4.tgz'))
        lock = [{'name': k.split('node_modules/')[-1], 'version': v['version'], 'license': v['license'], 'integrity': v['integrity']}
                for k, v in sorted(L['packages'].items()) if k]
        self.assertEqual([{k: p[k] for k in ('name', 'version', 'license', 'integrity')} for p in A['packages']], lock)
        self.assertEqual(A['licences'], ['MIT']); self.assertTrue(A['result'].startswith('closed: 3 packages, all MIT'))
        self.assertIn('Permission is hereby granted, free of charge, to any person obtaining a copy', N)
        for p in A['packages']:
            self.assertIn(f"{p['name']}@{p['version']} (MIT)", N); self.assertIn(p['copyright'], N)
            lic = os.path.join(DH, 'node_modules', p['name'], 'LICENSE')
            if os.path.exists(lic):                                                                # the installed tree, when present
                self.assertEqual(hashlib.sha256(read(lic)).hexdigest(), p['licence_file_sha256'])
                self.assertIn(read(lic).decode().strip(), N)
        self.assertFalse(any(os.path.exists(os.path.join(DH, 'node_modules', n['name'])) for n in A['not_installed']))
        src = read(os.path.join(DH, 'compose.mjs')).decode() + ''.join(read(os.path.join(DH, 'plugins', f)).decode() for f in ('feed.mjs', 'frontend.mjs'))
        self.assertEqual(re.findall(r"from '([^'.][^']*)'", src).count('@deepseek-ai/cordis'), 1)       # one import of Cordis, in compose.mjs
        self.assertFalse(re.search(r"node:(?:net|http|https|dgram|tls|child_process|os|worker_threads)|\b(?:ctx|root)\.(?:provide|on|emit|set|get|mixin|service|loader)\b|homedir|process\.env", src))

    def test_refresh_runs_compose_after_pulse_with_no_secret_and_stages_only_the_four_feeds(self):
        wf = read(os.path.join(ROOT, '.github', 'workflows', 'refresh.yml')).decode()
        step = wf[wf.index('      - name: Compose the feeds'):]; step = step[:step.index('\n      - ', 10)]
        i = wf.index
        self.assertLess(i('python pulse.py --relink'), i('- name: Compose the feeds'))
        self.assertLess(i('run: python hype_build.py --scrub web/hype.json'), i('- name: Compose the feeds'))
        self.assertLess(i('- name: Compose the feeds'), i('python -m unittest discover tests && node scripts/check_page.mjs'))
        self.assertIn('timeout-minutes: 2', step); self.assertIn('echo "cordis step: $((SECONDS - start))s', step)
        self.assertIn('npm ci --prefix scripts/dehype --ignore-scripts --no-audit --no-fund', step)
        self.assertIn("npm ls @deepseek-ai/cordis --prefix scripts/dehype | grep -q '@deepseek-ai/cordis@4.0.4'", step)
        self.assertIn('node scripts/dehype/compose.mjs', step)
        for x in ('secrets.', 'env:', 'continue-on-error', 'id-token', 'TOKEN'): self.assertNotIn(x, step)
        job = wf[wf.index('  refresh:'):wf.index('  deploy:')]
        self.assertNotIn('id-token', job); self.assertNotIn('permissions:', job)                    # the workflow's contents: write only
        add = next(l for l in wf.splitlines() if l.strip().startswith('git add ')).split()
        for f in FEEDS['en'] + FEEDS['pt']: self.assertIn('web/' + f, add)
        self.assertFalse([f for f in add if 'table.' in f or 'strings.json' in f or 'verdicts.json' in f])
        ci = read(os.path.join(ROOT, '.github', 'workflows', 'ci.yml')).decode()
        self.assertLess(ci.index('npm ci --prefix scripts/dehype --ignore-scripts'), ci.index('python -m unittest discover tests'))
        self.assertIn('scripts/dehype/node_modules/', read(os.path.join(ROOT, '.gitignore')).decode())


if __name__ == '__main__':
    unittest.main()
