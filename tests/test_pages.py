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
        self.assertIn('pages stories.html, output.html, hype.html', r.stdout)
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


if __name__ == '__main__':
    unittest.main()
