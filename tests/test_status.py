"""The Sources page (status.html): live sources read at runtime from the data files' sources blocks, the rest and the roadmap from the
owner-reviewed web/i18n/sources-plan.json. Fixtures follow Decision 14: each case overlays a copy of the committed web/ and
check_page.mjs must fail with that rule's own finding, or pass."""
import copy, json, os, re, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_i18n import check_page, findings, read
WEB = os.path.join(ROOT, 'web')
PLAN = 'i18n/sources-plan.json'
GROUPS = {'ready', 'pending', 'held', 'free'}


class StatusPageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = read(os.path.join(WEB, 'dehype.js'))
        cls.html = read(os.path.join(WEB, 'status.html'))
        cls.plan = json.loads(read(os.path.join(WEB, PLAN)))

    def assert_only(self, r, *msgs):
        self.assertEqual(r.returncode, 1, r.stdout)
        got = findings(r)
        for m in msgs: self.assertTrue(any(g.startswith(m) for g in got), (m, got))
        self.assertEqual(len(got), len(msgs), got)

    def plan_with(self, fn):
        P = copy.deepcopy(self.plan); fn(P); return {PLAN: P}

    def test_committed_page_and_plan_pass(self):
        r = check_page()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('status.html', r.stdout)
        self.assertRegex(r.stdout, r'sources plan \d+ rows in 4 groups, \d+ roadmap steps')

    def test_page_loads_the_shell_and_names_its_data_files(self):
        body = re.search(r'<body data-page="status" data-src="([^"]*)">', self.html)
        self.assertEqual(body[1].split(), ['briefing.json', 'pulse.json', 'data.json', 'ledger/index.json', PLAN])
        h = self.html.replace(' data.json', '')
        self.assert_only(check_page({'status.html': h}), 'status.html does not name the data files it reads')
        h = self.html.replace('<script src="dehype.js" defer></script>', '')
        self.assert_only(check_page({'status.html': h}), 'status.html does not load dehype.css and dehype.js')
        self.assert_only(check_page({'status.html': self.html.replace('</body>', '<script>1</script></body>')}), 'status.html carries an inline script')

    def test_every_page_links_the_sources_page(self):
        self.assertIn("['status', 'nav.status']", self.js)               # NAV: shell() writes the nav on every page from this list
        S = json.loads(read(os.path.join(WEB, 'i18n', 'strings.json')))['strings']
        self.assertEqual((S['nav.status']['en'], S['nav.status']['pt']), ('Sources', 'Fontes'))

    def test_live_rows_are_read_from_the_data_files_not_written_in_the_plan(self):
        for f in ('briefing.json', 'pulse.json', 'data.json'): self.assertIn(f"opt('{f}', null)", self.js)
        self.assertTrue(all(set(e) <= {'id', 'group', 'name', 'live', 'feeds', 'en', 'pt'} for e in self.plan['sources']))
        self.assertTrue(all(e['group'] in GROUPS for e in self.plan['sources']))          # no live group in the plan
        def add_status(P): P['sources'][0]['status'] = 'ok'
        self.assert_only(check_page(self.plan_with(add_status)), f'{PLAN}: row carries a field outside its shape')

    def test_plan_rows_need_en_and_pt(self):
        def drop_pt(P): del P['sources'][0]['pt']['terms']
        self.assert_only(check_page(self.plan_with(drop_pt)), f'{PLAN}: row lacks its en or pt text')
        def drop_step(P): P['roadmap'][1]['en']['what'] = ' '
        self.assert_only(check_page(self.plan_with(drop_step)), f'{PLAN}: row lacks its en or pt text')

    def test_plan_groups_gauges_and_states_are_known(self):
        def group(P): P['sources'][0]['group'] = 'live'
        self.assert_only(check_page(self.plan_with(group)), f'{PLAN}: source row in an unknown group')
        def feed(P): P['sources'][0]['feeds'] = ['doom_dial']
        self.assert_only(check_page(self.plan_with(feed)), f'{PLAN}: source row feeds no known gauge')
        def state(P): P['roadmap'][0]['state'] = 'shipped'
        self.assert_only(check_page(self.plan_with(state)), f'{PLAN}: roadmap step in an unknown state')
        def no_s1(P): P['roadmap'] = [s for s in P['roadmap'] if s['id'] != 'S1']
        self.assert_only(check_page(self.plan_with(no_s1)), f'{PLAN} roadmap lacks its S1 step')
        def dup(P): P['sources'][1]['id'] = P['sources'][0]['id']
        self.assert_only(check_page(self.plan_with(dup)), f'{PLAN}: source row without a unique id')

    def test_plan_keeps_the_public_data_rules(self):
        def reddit(P): P['sources'][0]['en']['terms'] += ' See https://www.reddit.com/wiki/api'
        self.assert_only(check_page(self.plan_with(reddit)), f'{PLAN}: Reddit link')
        def handle(P): P['sources'][0]['pt']['what'] += ' via @someone'
        self.assert_only(check_page(self.plan_with(handle)), f'{PLAN}: person handle (@name)')
        self.assert_only(check_page({'status.html': self.html.replace('</main>', '<a href="https://x.com/someone/status/1">x</a></main>')}), 'status.html: X link')

    def test_the_page_knows_every_gauge_the_plan_may_name(self):
        js = self.js.replace("awareness: 'status.feeds.awareness' };", "};")
        self.assertNotEqual(js, self.js)
        self.assert_only(check_page({'dehype.js': js}), 'dehype.js FEEDS does not name every gauge id the plan may use')

    def test_status_keys_have_entries(self):
        self.assert_only(check_page({'dehype.js': self.js + "\nt('status.not_a_key');"}), 'dehype.js: string key with no entry in i18n/strings.json')

    def test_plan_is_owner_reviewed(self):
        sys.path.insert(0, ROOT)
        from scripts.check_owner_files import OWNER_FILES
        self.assertIn('web/i18n/sources-plan.json', OWNER_FILES)
        self.assertIn("'web/i18n/sources-plan.json'", read(os.path.join(ROOT, 'scripts', 'check_page.mjs')).split('const OWNER_REVIEWED = ')[1].split(';')[0])

    def test_missing_plan_fails(self):
        r = check_page({PLAN: None})
        self.assertEqual(r.returncode, 1)
        self.assertTrue(any(g.startswith(f'{PLAN} missing') for g in findings(r)), findings(r))


if __name__ == '__main__':
    unittest.main()
