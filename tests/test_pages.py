"""dehype pages (design rows 10, 11, 13; C21, C24; group C2): the shared shell, the three pages, the Hype page's fixed wordings and the
reviewed-Portuguese dossier file. Fixtures follow Decision 14: each case overlays a copy of the committed web/ and check_page.mjs must
fail with that rule's own finding, or pass."""
import hashlib, json, os, subprocess, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_i18n import check_page, findings, read
WEB = os.path.join(ROOT, 'web')
PT = 'i18n/dossier.pt.json'


def dossier_fields():
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'hype_build.py'), '--dossier-fields', os.path.join(WEB, 'hype.json')],
                       capture_output=True, text=True, check=True)
    return [json.loads(l) for l in r.stdout.splitlines()]


class PagesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fields = dossier_fields()
        cls.js = read(os.path.join(WEB, 'dehype.js'))
        f = next(x for x in cls.fields if x['slug'] and x['field'] == 'summary')
        cls.entry = {'slug': f['slug'], 'field': f['field'], 'sha256': f['sha256'], 'pt': 'Resumo revisado.', 'reviewed_in': 40}

    def assert_fails(self, r, *msgs, only=True):
        self.assertEqual(r.returncode, 1, r.stdout)
        got = findings(r)
        for m in msgs: self.assertTrue(any(g.startswith(m) for g in got), (m, got))
        if only: self.assertEqual(len(got), len(msgs), got)

    def pt(self, *entries): return {PT: {'entries': list(entries)}}

    def test_committed_pages_pass_with_an_empty_dossier_file(self):
        self.assertEqual(json.loads(read(os.path.join(WEB, PT)))['entries'], [])
        r = check_page()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('pages index.html, stories.html, output.html, hype.html, method.html, audit.html', r.stdout)
        self.assertIn('dossier.pt.json 0 matching entries', r.stdout)

    def test_dossier_fields_name_every_prose_field_with_its_hash(self):
        self.assertGreater(len(self.fields), 100)
        for f in self.fields: self.assertEqual(f['sha256'], hashlib.sha256(f['en'].encode()).hexdigest())

    def test_reviewed_matching_entry_passes(self):
        r = check_page(self.pt(self.entry))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('dossier.pt.json 1 matching entries', r.stdout)

    def test_entry_without_reviewed_in_fails(self):
        e = dict(self.entry); del e['reviewed_in']
        self.assert_fails(check_page(self.pt(e)), 'i18n/dossier.pt.json: entry without reviewed_in')

    def test_entry_with_a_bad_hash_or_no_field_fails(self):
        self.assert_fails(check_page(self.pt(dict(self.entry, sha256='abc'))), 'i18n/dossier.pt.json: entry sha256 is not 64 hex')
        self.assert_fails(check_page(self.pt(dict(self.entry, field='nope'))), 'i18n/dossier.pt.json: entry names no dossier prose field')

    def test_stale_entry_is_a_warning_and_falls_back(self):
        r = check_page(self.pt(dict(self.entry, sha256='0' * 64)))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('1 entries no longer match the current English', r.stderr)

    def test_page_with_neither_notice_nor_match_fails(self):
        js = self.js.replace("t('dossier.pt_notice')", "''")
        self.assertNotEqual(js, self.js)
        self.assert_fails(check_page({'dehype.js': js}), 'the Portuguese Hype page shows dossier prose with no notice')

    def test_hype_wordings_are_fixed(self):
        S = json.loads(read(os.path.join(WEB, 'i18n', 'strings.json')))
        S['strings']['hype.gap.note']['en'] = 'heuristic'
        self.assert_fails(check_page({'i18n/strings.json': S}), 'the Hype page lacks the hype.gap.note wording')
        self.assert_fails(check_page({'dehype.js': self.js.replace("t('hype.skeptic.note')", "''")}), 'the Hype page lacks the hype.skeptic.note wording')

    def test_each_page_names_its_data_files(self):
        h = read(os.path.join(WEB, 'hype.html')).replace(' removals.json', '')
        self.assert_fails(check_page({'hype.html': h}), 'hype.html does not name the data files it reads')
        s = read(os.path.join(WEB, 'stories.html')).replace('</body>', '<script>alert(1)</script></body>')
        self.assert_fails(check_page({'stories.html': s}), 'stories.html carries an inline script')

    def test_page_sources_keep_the_public_data_rules(self):
        s = read(os.path.join(WEB, 'output.html')).replace('</main>', '<a href="https://www.reddit.com/r/x/comments/abc/t/">x</a></main>')
        self.assert_fails(check_page({'output.html': s}), 'output.html: Reddit link')

    def test_script_uses_only_known_keys_and_the_named_files(self):
        self.assert_fails(check_page({'dehype.js': self.js + "\nt('ui.not_a_key');"}), 'dehype.js: string key with no entry in i18n/strings.json')
        self.assert_fails(check_page({'dehype.js': self.js + "\nload('feeds.json');"}), 'dehype.js: loads a file no dehype page names')
        self.assert_fails(check_page({'dehype.js': self.js + '\n}'}), 'dehype.js does not parse')

        self.assert_fails(check_page({'dehype.js': self.js + "\nconst X = REPO + 'NOPE.md';"}), 'dehype.js: links a repository path (blob/dev/<path>) that does not exist')

    def test_x_profile_link_is_the_projects_own_account(self):
        sys.path.insert(0, ROOT)
        import hype_build
        H = json.loads(read(os.path.join(WEB, 'hype.json')))
        slug = next(s for s, it in H['items'].items() if it['links'].get('x_handle'))
        H['items'][slug]['links']['x_handle'] = 'https://x.com/somebody_else'
        self.assert_fails(check_page({'hype.json': H}), "hype.json: links.x_handle is not the project's own account")
        self.assertIsNone(hype_build.scrub(H, drop=set())['items'][slug]['links']['x_handle'])
        self.assertTrue(hype_build.own_account('claude-code', {'name': 'Claude Code'}, 'https://x.com/claudeai'))

    def test_listed_organisation_account_stays_and_a_person_goes(self):
        sys.path.insert(0, ROOT)
        import hype_build
        from scripts.check_owner_files import OWNER_FILES
        self.assertIn('web/i18n/x-org-accounts.json', OWNER_FILES)
        orgs = json.loads(read(os.path.join(WEB, 'i18n', 'x-org-accounts.json')))['accounts']
        self.assertIn('openai', orgs)
        H = json.loads(read(os.path.join(WEB, 'hype.json')))
        self.assertEqual(H['items']['sora']['links']['x_handle'], 'https://x.com/OpenAI')      # an organisation the owner listed
        self.assertIsNone(H['items']['skyvern']['links']['x_handle'])                       # a person: not listed, no token match
        self.assertTrue(hype_build.own_account('qwen3-8', {'name': 'Qwen3.8'}, 'https://x.com/Alibaba_Qwen', orgs))
        self.assertFalse(hype_build.own_account('skyvern', {'name': 'Skyvern'}, 'https://x.com/Suchintan', orgs))
        H['items']['skyvern']['links']['x_handle'] = 'https://x.com/Suchintan'
        self.assert_fails(check_page({'hype.json': H}), "hype.json: links.x_handle is not the project's own account")
        del orgs['openai']
        self.assert_fails(check_page({'i18n/x-org-accounts.json': {'accounts': orgs}}), "hype.json: links.x_handle is not the project's own account")


class FoldTest(unittest.TestCase):
    """Group C3 (design rows 9 display, 10, 11; C21, R2-4): the briefing first screen, the method and audit pages, and the fold of the
    console's URLs (tests/fixtures/console_anchors.json), each as a Decision 14 overlay."""
    @classmethod
    def setUpClass(cls):
        cls.js = read(os.path.join(WEB, 'dehype.js'))
        cls.anchors = json.loads(read(os.path.join(ROOT, 'tests', 'fixtures', 'console_anchors.json')))

    def assert_only(self, r, *msgs):
        self.assertEqual(r.returncode, 1, r.stdout)
        got = findings(r)
        for m in msgs: self.assertTrue(any(g.startswith(m) for g in got), (m, got))
        self.assertEqual(len(got), len(msgs), got)

    def test_committed_site_folds_every_console_url(self):
        r = check_page()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"fold {len(self.anchors['anchors'])} console URLs over 5 tabs", r.stdout)
        self.assertEqual({a['tab'] for a in self.anchors['anchors']}, set(self.anchors['tabs']))
        self.assertEqual(self.anchors['tabs'], ['Pulse', 'Papers', 'Repos', 'Hype', 'Method'])   # the console's TABS at 2bc0ace

    def test_a_console_url_that_folds_elsewhere_fails(self):
        js = self.js.replace("if (tab === 'methodology') return go('method.html'", "if (tab === 'methodology') return go('index.html'")
        self.assert_only(check_page({'dehype.js': js}), 'dehype.js: console URL does not fold to its dehype page')

    def test_a_missing_target_page_fails(self):
        r = check_page({'audit.html': None, 'method.html': None})
        self.assertEqual(r.returncode, 1)
        got = findings(r)
        self.assertTrue(any(g.startswith('method.html missing') for g in got), got)
        self.assertTrue(any(g.startswith('tests/fixtures/console_anchors.json: console URL folds to a missing page') for g in got), got)

    def test_a_kept_wording_dropped_from_the_pages_fails(self):
        js = self.js.replace("t('state.proposed')", "t('ui.none')")
        self.assert_only(check_page({'dehype.js': js}), 'dehype.js: a folded page lacks a kept wording')

    def test_the_briefing_shows_no_trend_or_arrow_and_at_most_four_gauges(self):
        js = self.js.replace("${esc(tr(g.status))}</span>${sources(", "${esc(tr(g.status))}</span>${g.trend ? '↑' : ''}${sources(")
        self.assertNotEqual(js, self.js)
        self.assert_only(check_page({'dehype.js': js}), 'dehype.js: the briefing shows a trend or arrow')
        js = self.js.replace("(B.gauges || []).slice(0, 4)", "(B.gauges || [])")
        self.assert_only(check_page({'dehype.js': js}), 'dehype.js: the briefing does not cap the gauge header at four gauges')

    def test_new_pages_keep_the_public_data_rules(self):
        h = read(os.path.join(WEB, 'audit.html')).replace('</main>', '<a href="https://x.com/someone/status/1">x</a></main>')
        self.assert_only(check_page({'audit.html': h}), 'audit.html: X link')

    def test_stale_since_cases_pass_under_node_test(self):              # Decision 15's runner, also run here until E1 adds it to ci.yml
        r = subprocess.run(['node', '--test', os.path.join(ROOT, 'tests', 'dehype_stale.test.mjs')], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('pass 7', r.stdout)

    def test_only_the_pinned_transformers_import(self):
        self.assert_only(check_page({'dehype.js': self.js + "\nimport('https://example.com/x.js');"}), 'dehype.js: imports code other than the exact-pinned transformers.js')
        js = self.js.replace("transformers@4.2.0'", "transformers@latest'")
        self.assert_only(check_page({'dehype.js': js}), 'dehype.js: imports code other than the exact-pinned transformers.js')
        js = self.js + "\nconst Y = 'https://cdn.jsdelivr.net/npm/@someone/pkg@1.0.0';"
        self.assert_only(check_page({'dehype.js': js}), 'dehype.js: account-naming URL (a person handle)')

    def test_verdicts_resolve_through_the_alias_file(self):
        for f in ('index.html', 'stories.html'):
            self.assertIn('story-aliases.json', read(os.path.join(WEB, f)).split('data-src="')[1].split('"')[0])
        self.assertIn("opt('story-aliases.json'", self.js)

    def test_method_page_reads_the_web_copies_and_links_no_blob(self):
        self.assertIn("load('METHODOLOGY.pt.md')", self.js)
        self.assertIn("load('POLICY.pt.md')", self.js)
        self.assertNotIn("REPO + 'METHODOLOGY.md'", self.js)                 # the method and policy links go to method.html now
        self.assertNotIn("'nav.console'", self.js)                          # the console tab is folded


if __name__ == '__main__':
    unittest.main()
