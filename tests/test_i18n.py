"""Two languages (design rows 12 and 14; group C1): our own text in en and pt, lang tags on headlines and post titles, and the
English and Portuguese method sources. Fixtures follow Decision 14: each case overlays a copy of the committed web/ and
check_page.mjs must fail with that rule's own finding."""
import json, os, re, shutil, subprocess, sys, tempfile, unittest
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import pulse
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'i18n')
WEB = os.path.join(ROOT, 'web')
LANG = re.compile(r'^(?:und|[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-(?:[A-Z]{2}|\d{3}))?)$')


def read(path):
    with open(path, encoding='utf-8') as f: return f.read()


def strings():
    return json.loads(read(os.path.join(WEB, 'i18n', 'strings.json')))


def check_page(files=None, tree=None, root=None):
    """check_page.mjs on a copy of the committed web/ with `files` ({path: text, or None to delete}) and `tree` written over it;
    root: {name: text} written beside the copy, as the repository-root sources are beside web/."""
    with tempfile.TemporaryDirectory() as d:
        web = os.path.join(d, 'web')
        shutil.copytree(WEB, web)
        if tree: shutil.copytree(tree, web, dirs_exist_ok=True)
        for rel, body in (files or {}).items():
            if body is None: os.remove(os.path.join(web, rel)); continue
            with open(os.path.join(web, rel), 'w', encoding='utf-8') as f: f.write(body if isinstance(body, str) else json.dumps(body, ensure_ascii=False))
        for name, body in (root or {}).items():
            with open(os.path.join(d, name), 'w', encoding='utf-8') as f: f.write(body)
        return subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)


def findings(r): return [l[2:] for l in r.stderr.splitlines() if l.startswith('- ')]


class StringsTest(unittest.TestCase):
    def test_every_entry_has_en_and_pt_with_the_same_placeholders(self):
        S = strings()['strings']
        self.assertGreater(len(S), 50)
        for k, v in S.items():
            with self.subTest(k):
                if 'ref' in v:                                  # Decision 10: the X-figure placeholder lives beside its list
                    f, key = v['ref'].split('#')
                    v = json.loads(read(os.path.join(WEB, 'i18n', f)))[key]
                self.assertTrue(v['en'].strip() and v['pt'].strip())
                ph = lambda t: sorted(re.findall(r'\{(\w+)\}', t))
                self.assertEqual(ph(v['en']), ph(v['pt']))

    def test_fields_and_methods_name_existing_entries_and_anchors(self):
        I = strings()
        for f, paths in I['fields'].items():
            for p, spec in paths.items():
                for k in (spec if isinstance(spec, list) else spec['keys']): self.assertIn(k, I['strings'], (f, p))
        en = read(os.path.join(ROOT, 'METHODOLOGY.md'))
        for f, m in I['methods'].items():
            for field, anchor in m.items(): self.assertIn(anchor, method_ids(en), (f, field))

    def test_pulse_fixed_words_are_entries(self):
        """The fixed lines pulse.py writes into public files have their en entry (the gate checks the built values too)."""
        en = {v.get('en') for v in strings()['strings'].values()}
        for s in (pulse.PREVIEW, pulse.NOT_FETCHED, pulse.RELATED, pulse.NEW_TODAY, pulse.NO_SOURCE, pulse.COUNT_ONLY_HEADLINE):
            self.assertIn(s, en)


class LangTagTest(unittest.TestCase):
    """C17/C33: a title's lang comes from its source's own metadata, else und; no language is detected or guessed."""
    def test_tag_normalisation(self):
        cases = {'en': 'en', 'EN-us': 'en-US', 'pt_BR': 'pt-BR', 'zh-Hant-TW': 'zh-Hant-TW', 'en-GB-oxendict': 'en-GB', 'es-419': 'es-419',
                 'english': None, 'und': None, 'x-klingon': None, '': None, None: None, '123': None}
        for v, want in cases.items(): self.assertEqual(pulse.lang_tag(v), want, v)
        self.assertEqual(pulse.lang_tag(['ja', 'en']), 'ja')
        self.assertEqual(pulse.lang_tag([]), None)

    def test_feed_language_rss_channel_and_atom_xml_lang(self):
        cut = datetime(2026, 10, 1, tzinfo=timezone.utc)
        rss = (b'<rss version="2.0"><channel><title>t</title><language>en-us</language><item><title>Hello</title><link>https://e.test/a</link>'
               b'<pubDate>Fri, 16 Oct 2026 10:00:00 GMT</pubDate></item></channel></rss>')
        atom = (b'<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="pt-BR"><entry><title>Ola</title><link href="https://e.test/b"/>'
                b'<published>2026-10-16T10:00:00Z</published></entry><entry xml:lang="fr"><title>Salut</title><link href="https://e.test/c"/>'
                b'<published>2026-10-16T10:00:00Z</published></entry></feed>')
        bare = (b'<rss version="2.0"><channel><title>t</title><item><title>No language</title><link>https://e.test/d</link>'
                b'<pubDate>Fri, 16 Oct 2026 10:00:00 GMT</pubDate></item></channel></rss>')
        got = [pulse.lang_of(p) for p in pulse.parse_feed(rss, 'N', 'Newsletter', cut) + pulse.parse_feed(atom, 'O', 'Official', cut)
               + pulse.parse_feed(bare, 'B', 'Newsletter', cut)]
        self.assertEqual(got, ['en-US', 'pt-BR', 'fr', 'und'])

    def test_mastodon_language_and_bluesky_langs_are_stored(self):
        now = pulse.NOW.strftime('%Y-%m-%dT%H:%M:%SZ')
        status = lambda i, lang: {'id': str(i), 'url': f'https://mastodon.social/@a/{i}', 'content': '<p>Claude Code news</p>', 'language': lang,
                                  'account': {'acct': 'a'}, 'created_at': now, 'favourites_count': 1, 'reblogs_count': 0, 'replies_count': 0}
        bsky = lambda i, langs: {'uri': f'at://did:plc:x/app.bsky.feed.post/{i}', 'author': {'handle': 'a.bsky.social'},
                                 'record': {'text': 'Claude Code news', 'createdAt': now, **({'langs': langs} if langs is not None else {})}}
        old_http, old_env = pulse.http, dict(os.environ)
        def http(url, headers=None, data=None, timeout=30):
            if 'mastodon.social' in url: return [status(1, 'de'), status(2, None)] if 'max_id' not in url else []
            if 'createSession' in url: return {'accessJwt': 'x'}
            return {'posts': [bsky(3, ['pt']), bsky(4, None)]}
        try:
            pulse.http = http
            os.environ.update(BSKY_HANDLE='h', BSKY_APP_PASSWORD='p')
            m = pulse.fetch_mastodon(pages=1)
            b = pulse.fetch_bluesky()
        finally:
            pulse.http = old_http; os.environ.clear(); os.environ.update(old_env)
        self.assertEqual(sorted({(p['pid'], pulse.lang_of(p)) for p in m}), [('1', 'de'), ('2', 'und')])
        self.assertEqual(sorted({(p['pid'].rsplit('/', 1)[-1], pulse.lang_of(p)) for p in b}), [('3', 'pt'), ('4', 'und')])
        self.assertEqual(m[0]['extra'].get('lang'), 'de')         # kept in extra, so signals.sqlite stores it for offline rebuilds

    def test_networks_without_language_metadata_read_und(self):
        for p in (pulse.post('HN', 1, 'https://news.ycombinator.com/item?id=1', 'Show HN', 'a', '2026-10-16T10:00:00Z'),
                  pulse.post('Reddit', 'x', 'https://www.reddit.com/r/a/x', 't', 'a', '2026-10-16T10:00:00Z')):
            self.assertEqual(pulse.lang_of(p), 'und')

    def test_public_record_drops_lang_with_the_title_of_a_count_only_post(self):
        rec = {'net': 'Reddit', 'title': 't', 'lang': 'en', 'url': 'https://www.reddit.com/r/a/x', 'at': '2026-10-16T10:00:00Z'}
        self.assertNotIn('lang', pulse.public(rec))
        self.assertEqual(pulse.public(dict(rec, net='HN', url='https://news.ycombinator.com/item?id=1'))['lang'], 'en')


class CommittedFilesTest(unittest.TestCase):
    def test_every_published_title_and_headline_carries_a_valid_lang(self):
        n = 0
        for f in ('pulse.json', 'briefing.json'):
            def walk(o):
                nonlocal n
                if isinstance(o, dict):
                    for k in ('title', 'headline'):
                        if isinstance(o.get(k), str): n += 1; self.assertRegex(o.get('lang') or '', LANG, (f, o.get(k)))
                    for v in o.values(): walk(v)
                elif isinstance(o, list):
                    for v in o: walk(v)
            walk(json.loads(read(os.path.join(WEB, f))))
        self.assertGreater(n, 0)

    def test_web_method_copies_equal_their_root_sources_and_deploy_syncs_both(self):
        for name in ('METHODOLOGY.md', 'METHODOLOGY.pt.md'):
            self.assertEqual(read(os.path.join(ROOT, name)), read(os.path.join(WEB, name)), name)
        y = read(os.path.join(ROOT, '.github', 'workflows', 'deploy.yml'))
        self.assertRegex(y, r"paths: \[[^\]]*'METHODOLOGY\.pt\.md'")
        self.assertIn('cp METHODOLOGY.pt.md web/METHODOLOGY.pt.md', y.split('cloudflare:')[0])   # the GitHub Pages job's sync step (Decision 8)
        self.assertIn("'METHODOLOGY.pt.md'", read(os.path.join(ROOT, 'run.py')))

    def test_method_texts_state_the_disclosure_and_the_decision_13_figure(self):
        S = strings()['strings']
        flat = lambda t: re.sub(r'\s+', ' ', t)
        for name, lang in (('METHODOLOGY.md', 'en'), ('METHODOLOGY.pt.md', 'pt')):
            text = flat(read(os.path.join(ROOT, name)))
            for k in strings()['method_keys']: self.assertIn(flat(S[k][lang]), text, (name, k))
            self.assertIn('history-38948143514', text)
        self.assertIn('posts in our sample', S['x_route.disclosure']['en'])
        self.assertIn('posts na nossa amostra', S['x_route.disclosure']['pt'])
        for fig in ('-0,2%', '-3,5%', '1,7', '157', '133', '2026-11-06'): self.assertIn(fig, S['method.scrub_effect']['pt'])   # pt-BR notation

    def test_portuguese_method_translates_the_english_line_by_line(self):
        """METHODOLOGY.pt.md, without its anchor lines, has one line per English line: same kind (heading level, list, table cells,
        code fence), the same inline code and numbers (each in its language's notation: 2,019 and 0.75 in English are 2.019 and 0,75
        in Portuguese, so a separator compares as either), the same link targets, and code blocks byte-identical."""
        en = read(os.path.join(ROOT, 'METHODOLOGY.md')).split('\n')
        pt = [l for l in read(os.path.join(ROOT, 'METHODOLOGY.pt.md')).split('\n') if not re.fullmatch(r'<a id="[^"]+"></a>', l)]
        self.assertEqual(len(en), len(pt))
        code, num, url = re.compile(r'`[^`]*`'), re.compile(r'(?<![A-Za-z_])\d+(?:[.,]\d+)*'), re.compile(r'\]\(([^)\s]+)\)')
        def kind(l):
            m = re.match(r'^(#{1,6})\s|^(\s*)([-*]|\d+\.)\s|^\s*(\|)|^(```)|^(>)', l)
            return 'blank' if not l.strip() else 'text' if not m else m.group(0).strip() if not m.group(4) else 'table%d' % l.count('|')
        fence = False
        for i, (a, b) in enumerate(zip(en, pt), 1):
            with self.subTest(line=i):
                if a.startswith('```'): fence = not fence; self.assertEqual(a, b); continue
                if fence: self.assertEqual(a, b); continue
                self.assertEqual(re.sub(r'\d+\.', '1.', kind(a)), re.sub(r'\d+\.', '1.', kind(b)))
                self.assertEqual(Counter(code.findall(a)), Counter(code.findall(b)))
                sep = lambda l: Counter(re.sub(r'[.,]', '·', n) for n in num.findall(code.sub('', l)))
                self.assertEqual(sep(a), sep(b))
                self.assertEqual(Counter(url.findall(a)), Counter(url.findall(b)))


def method_ids(md):
    slug = lambda t: re.sub(r'^-|-$', '', re.sub(r'[^a-z0-9]+', '-', re.sub(r'<[^>]+>', '', t.lower())))
    return [slug(m) for m in re.findall(r'^#{1,4}\s+(.*)$', md, flags=re.M)]


class GateFixtureTest(unittest.TestCase):
    """SC-8 and SC-21 (C17, C31, C33): each overlay fails with its rule's own finding; the committed tree passes."""
    @classmethod
    def setUpClass(cls):
        cls.S = strings()
        cls.pt = read(os.path.join(WEB, 'METHODOLOGY.pt.md'))
        cls.en = read(os.path.join(WEB, 'METHODOLOGY.md'))
        cls.B = json.loads(read(os.path.join(WEB, 'briefing.json')))

    def strings_without(self, key, lang):
        I = json.loads(json.dumps(self.S)); del I['strings'][key][lang]
        return {'i18n/strings.json': I}

    def assert_fails(self, r, *msgs, only=False):
        self.assertEqual(r.returncode, 1, r.stdout)
        got = findings(r)
        for m in msgs: self.assertTrue(any(g.startswith(m) for g in got), (m, got))
        if only: self.assertEqual(len(got), len(msgs), got)

    def test_committed_tree_passes(self):
        r = check_page()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r'strings \d+ entries in en and pt, \d+ own-text values matched, \d+ titles tagged, method \d+ anchors in both languages')

    def test_missing_pt_or_en_key(self):
        self.assert_fails(check_page(self.strings_without('seen.new_today', 'pt')),
                          'i18n/strings.json: entry lacks its pt text (every string of our own text has en and pt) at 1 place, e.g. strings.seen.new_today.pt', only=True)
        self.assert_fails(check_page(self.strings_without('gauge.daily_movers', 'en')),
                          'i18n/strings.json: entry lacks its en text (every string of our own text has en and pt) at 1 place, e.g. strings.gauge.daily_movers.en')

    def test_placeholders_must_match(self):
        I = json.loads(json.dumps(self.S)); I['strings']['seen.first_seen']['pt'] = 'visto pela primeira vez em {dia}'
        self.assert_fails(check_page({'i18n/strings.json': I}), 'i18n/strings.json: entry has different placeholders in en and pt at 1 place, e.g. strings.seen.first_seen')

    def test_translated_headline_and_untagged_titles(self):
        r = check_page(tree=os.path.join(FIX, 'translated_headline'))
        self.assert_fails(r, 'pulse.json: translated headline or title (headlines and post titles stay as posted) at 2 places, e.g. stories[0].headline_pt, stories[1].headline',
                          'pulse.json: headline or title without a valid lang tag (source metadata, else "und") at 2 places, e.g. nodes[0].samples[0].lang, nodes[0].samples[1].lang',
                          'pulse.json: our fixed headline line does not read lang "en" at 1 place, e.g. stories[2].lang', only=True)

    def test_clean_minimal_pulse_passes(self):
        r = check_page(tree=os.path.join(ROOT, 'tests', 'fixtures', 'public_leaks', 'clean_pulse'))   # tagged titles, our fixed line in en
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_own_text_not_in_strings(self):
        B = json.loads(json.dumps(self.B))
        B['sources']['Lobsters (ai tag)']['detail'] = 'a new sentence nobody translated'
        self.assert_fails(check_page({'briefing.json': B}), 'briefing.json: own text not in i18n/strings.json (add its en and pt entry) at 1 place, e.g. sources.Lobsters (ai tag).detail', only=True)

    def test_count_only_figure_words_are_entries(self):
        H = json.loads(read(os.path.join(WEB, 'hype.json')))
        slug, i = next((k, j) for k, it in H['items'].items() for j, r in enumerate(it.get('traction') or []) if r.get('value') == 'figure from an X post, not shown')
        H['items'][slug]['traction'][i]['value'] = 'figure from somewhere, not shown'
        self.assert_fails(check_page({'hype.json': H}), f'hype.json: own text not in i18n/strings.json (add its en and pt entry) at 1 place, e.g. items.{slug}.traction[{i}].value', only=True)

    def test_method_copy_lacking_the_disclosure(self):
        pt = self.pt.replace(self.S['strings']['x_route.disclosure']['pt'], '')
        self.assert_fails(check_page({'METHODOLOGY.pt.md': pt}), 'METHODOLOGY.pt.md: lacks the x_route.disclosure text in pt (i18n/strings.json)', only=True)
        en = self.en.replace(self.S['strings']['x_route.disclosure']['en'], 'X route: not described.')
        self.assert_fails(check_page({'METHODOLOGY.md': en}), 'METHODOLOGY.md: lacks the x_route.disclosure text in en (i18n/strings.json)', only=True)
        self.assert_fails(check_page({'METHODOLOGY.pt.md': None}), 'METHODOLOGY.pt.md missing', only=True)

    def test_method_copies_share_anchors_and_code(self):
        pt = self.pt.replace('<a id="briefing"></a>', '<a id="resumo"></a>', 1)
        self.assert_fails(check_page({'METHODOLOGY.pt.md': pt}), 'METHODOLOGY.pt.md: headings do not match METHODOLOGY.md', 'i18n/strings.json: method paragraph\'s anchor not in METHODOLOGY.pt.md', only=True)
        pt = self.pt.replace('0.40 × pct(voices)', '0,40 × pct(vozes)', 1)
        self.assertNotEqual(pt, self.pt)
        self.assert_fails(check_page({'METHODOLOGY.pt.md': pt}), 'METHODOLOGY.pt.md: code blocks differ from METHODOLOGY.md', only=True)

    def test_web_copy_must_equal_the_root_source_beside_it(self):
        self.assertEqual(check_page(root={'METHODOLOGY.md': self.en, 'METHODOLOGY.pt.md': self.pt}).returncode, 0)
        self.assert_fails(check_page(root={'METHODOLOGY.md': self.en, 'METHODOLOGY.pt.md': self.pt + '\nnew line\n'}),
                          'web/METHODOLOGY.pt.md differs from the root METHODOLOGY.pt.md', only=True)


if __name__ == '__main__':
    unittest.main()
