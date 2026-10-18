"""Pulse topic extraction and metrics on fixed posts (offline), and the public-data rules (design group A)."""
import contextlib, copy, hashlib, io, json, os, re, shutil, sqlite3, subprocess, sys, tempfile, unittest, urllib.parse
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import pulse, hype_build
FIX = os.path.join(ROOT, 'tests', 'fixtures')

LEX = json.load(open(os.path.join(os.path.dirname(pulse.__file__), 'topics_lexicon.json')))
HYPE = {'claude-code': {'name': 'Claude Code', 'aliases': ['Claude Code CLI'], 'category': 'terminal coding agent'},
        'pi': {'name': 'Pi', 'aliases': ['Pi coding agent'], 'category': 'agent harness'}}


def p(net, pid, title, author, hours_ago, score=10):
    return pulse.post(net, pid, f'https://example.test/{net}/{pid}', title, author,
                      pulse.iso(pulse.NOW - timedelta(hours=hours_ago)), score, 1)


class PulseTest(unittest.TestCase):
    def setUp(self):
        pulse.EMERGING_STOP.clear()
        pulse.EMERGING_STOP.update(x.lower() for x in LEX.get('emerging_stop', []))

    def build(self, posts):
        nodes, edges, totals, self.projects, self.extras = pulse.build(posts, LEX, HYPE, getattr(self, 'repos', None))
        return {n['id']: n for n in nodes}, edges, totals

    def test_version_codename_and_parent(self):
        posts = [p('HN', 1, 'Claude Opus 5.5 spotted in the API', 'a', 2), p('Mastodon', 2, 'Is Opus 5.5 routing real?', 'b', 3),
                 p('Reddit', 3, 'Gemini 4 Argon beats everything', 'c', 5), p('HN', 4, 'Gemini 4 Argon plays StarCraft', 'd', 30)]
        n, edges, _ = self.build(posts)
        self.assertIn('v:opus-5.5', n)
        self.assertEqual(n['v:opus-5.5']['parent'], 'claude-opus')
        self.assertEqual(n['v:opus-5.5']['w']['7d']['authors'], 2)
        self.assertEqual(set(n['v:opus-5.5']['w']['7d']['nets']), {'HN', 'Mastodon'})
        self.assertIn('v:gemini-4-argon', n)                      # capitalised codename joins the version
        self.assertTrue(any({e['a'], e['b']} == {'claude', 'v:opus-5.5'} or {e['a'], e['b']} == {'claude-opus', 'v:opus-5.5'} for e in edges))

    def test_years_and_common_words_are_not_versions(self):
        n, _, _ = self.build([p('HN', 1, 'GPT 2026 roadmap and Claude 1000 tokens', 'a', 1), p('HN', 2, 'GPT 5 is here', 'b', 1)])
        self.assertNotIn('v:gpt-2026', n)
        self.assertNotIn('v:claude-1000', n)
        self.assertNotIn('v:gpt-5-is', n)

    def test_weight_counts_distinct_voices_and_network_spread(self):
        posts = [p('Mastodon', i, 'Anthropic news', 'same-bot', 1) for i in range(6)] + [p('HN', 9, 'Anthropic raises funds for AI', 'x', 1)]
        n, _, _ = self.build(posts)
        w = n['anthropic']['w']['7d']
        self.assertEqual(w['posts'], 7)
        self.assertEqual(w['authors'], 2)                          # six posts from one account count once
        self.assertEqual(w['weight'], 2 * 1.5)                     # two networks: x1.5

    def test_emerging_needs_three_authors_and_skips_hashtags_and_stop(self):
        posts = [p('Reddit', i, f'Muse Spark Open released #GenAI {i}', f'u{i}', 1) for i in range(3)] + \
                [p('Reddit', 10 + i, 'Phone Number leak via chatbot', f'v{i}', 1) for i in range(3)] + \
                [p('Mastodon', 20 + i, 'Hello #MachineLearning world', f'w{i}', 1) for i in range(4)]
        n, _, _ = self.build(posts)
        self.assertIn('e:muse-spark-open', n)
        self.assertEqual(n['e:muse-spark-open']['kind'], 'emerging')
        self.assertNotIn('e:phone-number', n)                      # only common words
        self.assertFalse(any(k.startswith('e:machinelearning') or k.startswith('e:genai') for k in n))

    def test_ambiguous_hype_name_is_case_sensitive_and_hn_needs_ai(self):
        posts = [p('HN', 1, 'Raspberry pi cluster at home', 'a', 1), p('HN', 2, 'Pi coding agent ships', 'b', 1),
                 p('HN', 3, 'Postgres 19 released', 'c', 1)]
        n, _, totals = self.build(posts)
        self.assertEqual(n.get('p:pi', {}).get('w', {}).get('7d', {}).get('posts'), None)  # one post only: below the 2-post floor
        self.assertNotIn('HN', {k for k in totals['7d'] if totals['7d'][k] > 2})

    def test_rising_needs_volume(self):
        posts = [p('Reddit', i, 'MCP servers everywhere', f'a{i}', 2) for i in range(4)] + [p('Reddit', 10, 'MCP spec update', 'z', 100)]
        n, _, _ = self.build(posts)
        self.assertGreaterEqual(n['mcp']['rising'], 2)
        n2, _, _ = self.build([p('Reddit', 1, 'MCP note', 'a', 2), p('Reddit', 2, 'MCP note 2', 'b', 50)])
        self.assertIsNone(n2['mcp']['rising'])

    def test_hn_needs_ai_signal_not_just_a_lab_or_theme(self):
        posts = [p('HN', 1, 'Supreme Court rules on database', 'a', 1), p('HN', 2, 'Microsoft killed FoxPro', 'b', 1),
                 p('HN', 3, 'Supreme Court and AI copyright', 'c', 1), p('HN', 4, 'Court filing on AI training data', 'd', 2)]
        n, _, _ = self.build(posts)
        self.assertEqual(n['policy-law']['w']['7d']['posts'], 2)       # only the AI stories
        self.assertNotIn('microsoft', n)

    def test_digest_never_takes_the_earliest_slot_of_a_day(self):
        nl = pulse.post('Newsletter', 'n1', 'https://nl.test/1', 'Opus 5.5 is coming \u241f long body text', 'Digest',
                        pulse.iso(pulse.NOW.replace(hour=0, minute=0, second=0, microsecond=0)))
        posts = [nl, p('Reddit', 2, 'Opus 5.5 rumour', 'r', 0.2), p('HN', 3, 'Opus 5.5 leak', 'h', 0.1)]
        n, edges, _ = self.build(posts)
        tr = n['v:opus-5.5']['spread']
        self.assertEqual(tr[-1]['net'], 'Newsletter')
        self.assertTrue(tr[-1]['day_only'])
        self.assertTrue(all(s['title'] == 'Opus 5.5 is coming' for s in n['v:opus-5.5']['samples'] if s['net'] == 'Newsletter'))

    def test_codename_not_taken_from_ordinary_words(self):
        n, _, _ = self.build([p('Reddit', i, 'Opus 5.5 Music Video', f'a{i}', 1) for i in range(2)] +
                             [p('Reddit', 5 + i, 'Qwen 2.1 Image edit', f'b{i}', 1) for i in range(2)])
        self.assertIn('v:opus-5.5', n)
        self.assertFalse(any(k.startswith('v:opus-5.5-') or k.startswith('v:qwen-2.1-') for k in n))

    def test_codename_survives_title_case_and_dates_are_not_topics(self):
        n, _, _ = self.build([p('Reddit', i, 'Gemini 4 Argon Is Out', f'a{i}', 1) for i in range(2)] +
                             [p('Reddit', 5 + i, f'Recap Oct 16 Dispatch {i}', f'b{i}', 1) for i in range(4)])
        self.assertIn('v:gemini-4-argon', n)
        self.assertFalse(any(k.startswith('e:oct-16') for k in n))

    def test_rising_ignores_dossier_posts(self):
        dossier = [pulse.post('Reddit', f'd{i}', f'https://x.test/{i}', 'Grok 5 hype', f'u{i}', pulse.iso(pulse.NOW - timedelta(hours=1)),
                              source='dossier') for i in range(5)]
        n, _, _ = self.build(dossier + [p('Reddit', 9, 'Grok 5 note', 'z', 100)])
        self.assertIsNone(n['grok']['rising'])

    def test_person_is_case_sensitive_and_links_to_its_organisation(self):
        posts = [p('Reddit', 1, 'Sam Altman says GPT 6 is close', 'a', 2), p('HN', 2, 'Altman on AI compute deals', 'b', 3),
                 p('Mastodon', 3, 'sam altman lowercase is not matched', 'c', 3), p('Reddit', 4, 'OpenAI ships a thing', 'd', 4),
                 p('Reddit', 5, 'OpenAI again', 'e', 5)]
        n, edges, _ = self.build(posts)
        self.assertEqual(n['sam-altman']['kind'], 'person')
        self.assertEqual(n['sam-altman']['parent'], 'openai')
        self.assertEqual(n['sam-altman']['w']['7d']['authors'], 2)          # lowercase mention ignored
        self.assertEqual(n['openai']['w']['7d']['posts'], 2)                 # a person mention is not a lab mention
        self.assertTrue(any({e['a'], e['b']} == {'sam-altman', 'openai'} for e in edges))
        self.assertFalse(any(k.startswith('e:sam-altman') for k in n))

    def test_newsletters_count_distinct_digests_and_reach(self):
        nl = lambda i, name: pulse.post('Newsletter', f'n{i}', f'https://nl.test/{i}', 'MCP everywhere \u241f body', name,
                                        pulse.iso(pulse.NOW - timedelta(hours=5 + i)))
        posts = [nl(1, 'Digest A'), nl(2, 'Digest A'), nl(3, 'Digest B'), p('HN', 9, 'MCP servers for AI', 'h', 1),
                 p('Reddit', 10, 'MCP rocks', 'r', 1, score=500)]
        n, _, _ = self.build(posts)
        w = n['mcp']['w']['7d']
        self.assertEqual(w['newsletters'], 2)
        self.assertEqual(w['newsletter_names'], ['Digest A', 'Digest B'])
        self.assertEqual(w['reach'], 4)                                      # HN + Reddit + two newsletters
        self.assertEqual(w['reach_label'], '2 networks + 2 newsletters')
        self.assertLess(w['eng_ex_reddit'], w['eng'])                        # Reddit snapshot scores excluded
        self.assertEqual(w['engagement']['Reddit']['score'], 500)

    def test_signal_orders_more_voices_and_reach_higher(self):
        posts = [p(net, f'{net}{i}', 'Gemma is great for AI', f'{net}-g{i}', 2) for net in ('HN', 'Reddit', 'Mastodon') for i in range(3)] + \
                [p('Reddit', f'k{i}', 'Kimi is fine', f'k{i}', 2) for i in range(2)] + \
                [p('Reddit', f'm{i}', 'MiniMax note', f'm{i}', 2) for i in range(3)]
        n, _, _ = self.build(posts)
        s = lambda k: n[k]['w']['7d']['signal']
        self.assertGreater(s('gemma'), s('minimax'))
        self.assertGreater(s('minimax'), s('moonshot-kimi'))
        self.assertTrue(all(0 <= x['w'][w]['signal'] <= 100 for x in n.values() for w in pulse.WINDOWS))
        self.assertEqual(set(n['gemma']['w']['7d']['signal_parts']), {'voices', 'reach', 'rising', 'eng'})
        self.assertIsNone(n['moonshot-kimi']['rising'])
        self.assertEqual(n['moonshot-kimi']['w']['7d']['signal_parts']['rising'], 0)    # no rising value scores 0

    def test_projects_map_covers_every_hype_item_live_only(self):
        dossier = pulse.post('X', 'd1', 'https://x.test/1', 'Claude Code is magic', 'fan', pulse.iso(pulse.NOW - timedelta(hours=3)),
                             source='dossier')
        posts = [dossier, p('HN', 1, 'Claude Code CLI ships hooks', 'a', 2), p('Reddit', 2, 'Claude Code broke my repo', 'b', 50),
                 p('Reddit', 3, 'Claude Code again', 'b', 400)]
        self.build(posts)
        self.assertEqual(set(self.projects), set(HYPE))
        self.assertEqual(self.projects['pi'], {'7d': {'voices': 0, 'posts': 0, 'nets': 0}, '30d': {'voices': 0, 'posts': 0, 'nets': 0}})
        self.assertEqual(self.projects['claude-code']['7d'], {'voices': 2, 'posts': 2, 'nets': 2})
        self.assertEqual(self.projects['claude-code']['30d'], {'voices': 2, 'posts': 3, 'nets': 2})

    # ---- v3: sources, common reach, organic-vs-orchestrated signals
    def test_official_feed_parsing_rss_and_atom(self):
        now = pulse.NOW
        rss = f"""<?xml version="1.0"?><rss version="2.0"><channel><title>Lab</title>
          <item><title>Introducing Gemma 9</title><link>https://lab.test/gemma-9</link><pubDate>{(now - timedelta(hours=5)).strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
          <description>&lt;p&gt;Gemma 9 is &lt;a href="https://x.com/googlegemma/status/1"&gt;here&lt;/a&gt;&lt;/p&gt;</description></item>
          <item><title>Old post</title><link>https://lab.test/old</link><pubDate>Mon, 01 Jan 2024 00:00:00 +0000</pubDate></item>
        </channel></rss>""".encode()
        ps = pulse.parse_feed(rss, 'Lab blog', 'Official', now - timedelta(days=30))
        self.assertEqual(len(ps), 1)                                          # date filter, not a head count
        self.assertEqual((ps[0]['net'], ps[0]['author'], ps[0]['url']), ('Official', 'Lab blog', 'https://lab.test/gemma-9'))
        self.assertEqual(pulse.shown(ps[0]), 'Introducing Gemma 9')           # body kept for matching only
        atom = f"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><entry><title>v2.0</title>
          <link rel="alternate" href="https://github.com/org/repo/releases/tag/v2.0"/><updated>{pulse.iso(now - timedelta(hours=5))}</updated>
          <content type="html">Release of DeepSeek 5</content></entry></feed>""".encode()
        ps = pulse.parse_feed(atom, 'Repo releases', 'Official', now - timedelta(days=30))
        self.assertEqual(ps[0]['url'], 'https://github.com/org/repo/releases/tag/v2.0')
        n, _, _ = self.build(ps + [p('HN', 1, 'DeepSeek 5 weights are out', 'a', 1)])
        self.assertIsNone(n['deepseek']['rising'])
        self.assertEqual(n['deepseek']['w']['7d']['reach'], 1)               # an official post is the origin, not spread
        self.assertEqual(n['deepseek']['spread'][0]['net'], 'Official')

    def test_newsletter_citations_skip_infrastructure_and_own_site(self):
        body = ('<a href="https://www.anthropic.com/news/x">a</a> <a href="https://x.com/karpathy/status/9?s=20">k</a>'
                '<a href="https://twitter.com/i/web/status/1">i</a> <a href="https://substackcdn.com/img.png">c</a>'
                '<a href="https://mynews.test/sub">own</a> <a href="https://github.com/a/b">g</a>')
        doms, xs = pulse.citations(body, ('mynews.test',))
        self.assertEqual(doms, ['anthropic.com', 'github.com'])
        self.assertEqual(xs, ['karpathy'])
        nl = pulse.post('Newsletter', 'n1', 'https://mynews.test/1', 'Claude news ␟ body', 'My News', pulse.iso(pulse.NOW - timedelta(hours=3)),
                        extra={'domains': doms, 'x': xs})
        self.build([nl])
        c = self.extras['citations']['7d']
        self.assertEqual(c['x_handles'][0][:3], ['karpathy', 1, ['My News']])
        self.assertIn('Claude', c['x_handles'][0][3])

    def test_burst_share(self):
        t0 = pulse.NOW - timedelta(days=10)
        times = [t0 + timedelta(minutes=10 * i) for i in range(6)] + [t0 + timedelta(days=d) for d in range(1, 5)]
        share, start = pulse.burst_share(times)
        self.assertAlmostEqual(share, 0.6)
        self.assertEqual(start, t0)

    def test_dupe_counts_only_other_authors(self):
        txt = 'Grok 5 is the best model ever released buy now'
        posts = [p('Reddit', i, txt + ('!' if i else ''), f'acct{i}', 2) for i in range(3)] + \
                [p('Reddit', 10 + i, txt, 'same', 3) for i in range(2)] + [p('Reddit', 20, 'A completely different take on Grok 5 here today', 'x', 3)]
        dk, elig = pulse.near_dupes(posts)
        self.assertEqual({k[1] for k in dk}, {'0', '1', '2', '10', '11'})   # 10/11 copy acct0-2, who are other authors
        self.assertEqual(len(elig), 6)
        dk2, _ = pulse.near_dupes([p('Reddit', 1, txt, 'same', 1), p('Mastodon', 2, txt, 'other', 1)][:1] + [p('Reddit', 3, txt, 'same', 1)])
        self.assertEqual(dk2, set())                                         # one author repeating themself is not a campaign

    def test_single_topic_and_link_push(self):
        link = {'link': 'https://grok.test/launch?utm_source=x'}
        mono = [pulse.post('Reddit', f'm{i}', f'https://r.test/m{i}', f'Grok 5 thoughts number {i} from me today', f'mono{i // 2}',
                           pulse.iso(pulse.NOW - timedelta(hours=5 + 30 * i)), 1, 1, extra=link) for i in range(10)]
        mixed = [pulse.post('Reddit', f'x{i}', f'https://r.test/x{i}', f'Grok 5 and the weather number {i} with friends', f'mixed{i}',
                            pulse.iso(pulse.NOW - timedelta(hours=7 + 30 * i)), 1, 1, extra={'link': f'https://site{i}.test/'}) for i in range(4)]
        other = [pulse.post('Reddit', f'o{i}', f'https://r.test/o{i}', f'Kimi update {i} is interesting stuff today', f'mixed{i}',
                            pulse.iso(pulse.NOW - timedelta(hours=9 + 30 * i)), 1, 1) for i in range(4)]
        n, _, _ = self.build(mono + mixed + other)
        o = n['grok']['organic']
        self.assertEqual(o['posts'], 14)
        self.assertEqual(o['single_topic_n'], 9)                             # authors with 2+ stored posts: 5 mono, 4 mixed (Grok + Kimi)
        self.assertAlmostEqual(o['single_topic'], round(5 / 9, 3))
        self.assertAlmostEqual(o['link_push'], round(10 / 14, 3))           # utm stripped before comparing
        self.assertIn('link_push', o['flags'])
        self.assertEqual(o['label'], 'strong coordination signals')
        n2, _, _ = self.build(mixed)
        self.assertEqual(n2['grok']['organic']['label'], 'too few posts')

    def test_reach_percentile_per_type_and_repo_flags(self):
        posts = [p('HN', i, f'Gemma story {i} about AI', f'h{i}', 2, score=10 * i) for i in range(1, 6)] + \
                [p('HN', 9, 'Unrelated AI story', 'z', 2, score=1000)] + \
                [pulse.post('arXiv', 'a1', 'https://arxiv.org/abs/a1', 'A Gemma paper', 'lab', pulse.iso(pulse.NOW - timedelta(hours=3)), 50, 0, source='tracker'),
                 pulse.post('arXiv', 'a2', 'https://arxiv.org/abs/a2', 'Another paper on AI', 'lab', pulse.iso(pulse.NOW - timedelta(hours=3)), 5, 0, source='tracker')]
        self.repos = [{'id': 'o/gemma-tools', 'text': 'gemma-tools: tools for Gemma', 'tag': 'other', 'gained': {'7d': 500, '30d': 900},
                       'flags': {'7d': [], '30d': ['stars>activity']}},
                      {'id': 'o/x', 'text': 'x: unrelated', 'tag': 'other', 'gained': {'7d': 10, '30d': 20}, 'flags': {'30d': []}}]
        n, _, _ = self.build(posts)
        w = n['gemma']['w']['7d']
        self.assertEqual(w['reach_parts']['papers'], {'n': 1, 'best': 100.0})
        self.assertEqual(w['reach_parts']['repos'], {'n': 1, 'best': 100.0})
        self.assertEqual(w['reach_parts']['posts']['n'], 5)
        self.assertEqual(w['reach_parts']['posts']['best'], 80.0)            # 4 of the 5 other HN stories score lower; the 1000-pt one does not match
        self.assertAlmostEqual(w['reach_pct'], round((100 + 100 + 80 + 60 + 40) / 5, 1))   # mean of the top five, all types
        self.assertEqual(n['gemma']['organic']['repos']['flags'], {'stars>activity': 1})
        self.assertEqual(w['where']['HN'], {'posts': 5, 'voices': 5})

    def test_jev_pattern_matches_run_py(self):
        with open(os.path.join(os.path.dirname(pulse.__file__), 'run.py')) as f: src = f.read()
        pat = next(t['pattern'] for t in LEX['topics'] if t['id'] == 'jev')
        self.assertIn(f"JEV_RX = r'{pat}'", src)
        n, _, _ = self.build([p('HN', 1, 'Show HN: JevBench for decision models', 'a', 1), p('HN', 2, 'OpenJev ships', 'b', 2),
                              p('HN', 3, 'Jevons paradox and GPUs', 'c', 2)])
        self.assertEqual(n['jev']['w']['7d']['posts'], 2)                      # HN keeps JEV stories without another AI keyword

    # ---- review hotfix
    def test_own_site_subdomains_and_tco_are_not_citations(self):
        f = {'name': 'Rundown', 'url': 'https://rss.beehiiv.com/feeds/x.xml', 'site': ['therundown.ai', 'rundown.ai']}
        body = ('<a href="https://app.therundown.ai/x">a</a><a href="https://www.rundown.ai/y">b</a><a href="https://t.co/abc">c</a>'
                '<a href="https://openai.com/news/z">d</a>')
        self.assertEqual(pulse.citations(body, tuple(pulse.own_hosts(f)))[0], ['openai.com'])

    def test_official_items_are_not_voices(self):
        off = pulse.post('Official', 'o1', 'https://lab.test/1', 'Gemma 9 released ␟ body', 'Lab blog', pulse.iso(pulse.NOW - timedelta(hours=5)),
                         source='official')
        legacy = {**pulse.post('Official', 'o2', 'https://lab.test/2', 'Gemma 9 docs', 'Lab blog', pulse.iso(pulse.NOW - timedelta(hours=4)))}
        n, _, _ = self.build([off, legacy, p('HN', 1, 'Gemma 9 is fast', 'a', 1), p('Reddit', 2, 'Gemma 9 local test', 'b', 1)])
        w = n['gemma']['w']['7d']
        self.assertEqual(w['authors'], 2)                                     # HN + Reddit; the vendor feed is not a voice
        self.assertEqual(w['posts'], 4)
        self.assertIsNone(w['where']['Official']['voices'])
        self.assertEqual(n['gemma']['spread'][0]['net'], 'Official')

    def test_rising_below_one_scores_zero_in_signal(self):
        slow = [p('Reddit', f's{i}', 'Kimi notes', f's{i}', 30 + 6 * i) for i in range(18)] + [p('Reddit', f't{i}', 'Kimi now', f't{i}', 2) for i in range(2)]
        fast = [p('Reddit', f'g{i}', 'Gemma now', f'g{i}', 2) for i in range(4)] + [p('Reddit', 'g9', 'Gemma before', 'gz', 100)]
        n, _, _ = self.build(slow + fast)
        self.assertAlmostEqual(n['moonshot-kimi']['rising'], 0.7)            # 2 today vs 20/7 a day: slower than usual
        self.assertEqual(n['moonshot-kimi']['w']['7d']['signal_parts']['rising'], 0)
        self.assertGreater(n['gemma']['w']['7d']['signal_parts']['rising'], 0)


    def test_always_on_recedes_and_new_topic_ranks_with_counts(self):
        base = [p('HN', 100 + d, f'Claude tip number {d} for coding', f'u{d}', 24 * d + 5) for d in range(8, 30)]
        base += [p('HN', 200 + d, f'LLM inference note {d}', f'v{d}', 24 * d + 9) for d in range(8, 30)]
        base += [p('HN', 300 + d, f'Another LLM paper {d}', f'w{d}', 24 * d + 13) for d in range(8, 30)]
        week = [p('HN', 400 + i, f'Muse Spark: new open-weight LLM released ({i})', f'h{i}', 10 + i) for i in range(3)]
        week += [p('Mastodon', 500 + i, f'Muse Spark Open is fun, take {i}', f'm{i}', 5 + i) for i in range(4)]
        week += [p('HN', 600 + i, f'Claude update {i}', f'c{i}', 20 + i) for i in range(2)]
        n, _, _ = self.build(base + week)
        self.assertTrue('e:muse-spark' in n, sorted(n))
        self.assertFalse('e:muse-spark-open' in n, sorted(n))             # a longer phrase that starts with a kept one folds into it
        ms = n['e:muse-spark']['new']
        self.assertEqual(ms['deep'], ['HN'])                 # Mastodon has no baseline days: not deep
        self.assertEqual((ms['now'], ms['base']), (3, 0))
        self.assertTrue(ms['talk_ok']); self.assertGreater(ms['score'], 0); self.assertEqual(ms['leg'], 'talk')
        cl = n['claude']['new']
        self.assertTrue(cl['always_on']); self.assertEqual(cl['talk'], 0.0)

    def test_build_leg_needs_a_wave_of_new_repos(self):
        born, old = pulse.iso(pulse.NOW - timedelta(days=5))[:10], '2024-01-01'
        self.repos = ([{'id': f'x/jev-thing-{i}', 'text': f'jev-thing-{i}: a JEV harness', 'tag': 'JEV', 'gained': {'7d': 10 * i}, 'flags': {}, 'created': born} for i in range(4)]
                      + [{'id': f'y/agent-{i}', 'text': f'agent-{i}: an AI agent framework', 'tag': 'agents', 'gained': {'7d': 5}, 'flags': {},
                          'created': born if i < 3 else old} for i in range(10)])
        posts = [p('GitHub', r['id'], r['text'], r['id'].split('/')[0], 1) for r in self.repos]
        for x in posts: x['source'] = 'tracker'
        n, _, _ = self.build(posts + [p('Reddit', 1, 'JEV models are fun', 'r', 3), p('Reddit', 2, 'AI agents are fun', 's', 3)])
        jev = n['jev']['new']
        self.assertEqual((jev['born'], jev['repos'], jev['leg']), (4, 4, 'build'))
        self.assertEqual(jev['born_top'][0], ['x/jev-thing-3', 30])
        ag = n['ai-agents']['new']
        self.assertEqual(ag['born'], 3); self.assertEqual(ag['build'], 0.0)   # 3 of 10: an old field, not a wave
        del self.repos


    def test_release_is_one_story_with_editorial_headline_and_stable_id(self):
        posts = [p('HN', 1, 'Muse Spark Open: Meta releases open LLM weights', 'h1', 30, score=400),
                 pulse.post('Official', 'https://ai.meta.test/muse-spark-open', 'https://ai.meta.test/muse-spark-open',
                            'Introducing Muse Spark Open ␟ weights today', 'Meta AI', pulse.iso(pulse.NOW - timedelta(hours=40)), source='official')]
        posts += [p('Reddit', 10 + i, f'Muse Spark is great at coding, test {i}', f'r{i}', 20 - i) for i in range(5)]
        posts += [p('Mastodon', 30 + i, f'Muse Spark Open looks strong {i}', f'm{i}', 10 + i) for i in range(3)]
        posts += [p('HN', 50, 'Postgres 19 delayed by LLM-assisted patches', 'h9', 5, score=200),
                  p('Reddit', 60, 'Unrelated question about GPUs', 'z', 3)]
        self.build(posts)
        st = self.extras['stories']
        muse = [s for s in st if s['label'] == 'Muse Spark']
        self.assertEqual(len(muse), 1, [s['headline'] for s in st])
        m = muse[0]
        self.assertEqual(m['headline'], 'Introducing Muse Spark Open')      # lab post first, body never shown
        self.assertTrue(m['covered']); self.assertTrue(m['official'])
        self.assertEqual(m['voices'], 9)                                      # official feed is not a voice
        self.assertEqual(m['path'][0]['net'], 'Official')
        self.assertEqual(m['id'], 's:' + __import__('hashlib').sha1(b'release:e:muse-spark').hexdigest()[:12])
        self.assertFalse(any('GPUs' in s['headline'] for s in st))           # a lone chatter post is not a story

    def test_post_mode_reads_complaints_and_questions(self):
        self.assertEqual(pulse.mode('IS GPT 6 DOWN ? WHY AM I GETTING THIS'), 'pain')
        self.assertEqual(pulse.mode('Gpt 6 Astra lobotomised?'), 'pain')
        self.assertEqual(pulse.mode('ChatGPT Plus usage limit hit after 10 messages'), 'pain')
        self.assertEqual(pulse.mode('Which model is best right now for video?'), 'ask')
        self.assertEqual(pulse.mode('Google slows down Gemini rollout in the EU'), 'say')
        self.assertEqual(pulse.mode('Flux 3 Klein is out'), 'say')


def legacy_copy(H):
    """The dossier copy as it was at 2bc0ace (pulse.py:311-318): text, handle and figures of every post with a URL. The 'before' side."""
    return [pulse.post(p.get('pl') or 'other', p['url'], p['url'], p.get('t'), p.get('au'), p.get('d'),
                       p.get('likes') if p.get('likes') is not None else p.get('score'), p.get('cm') or p.get('rp'), source='dossier')
            for it in H['items'].values() for p in it.get('posts', []) if p.get('url')]


class PublicRulesTest(unittest.TestCase):
    def test_url_rules(self):
        for u, net in [('https://www.reddit.com/r/ClaudeAI/comments/abc/x/', 'Reddit'), ('https://i.redd.it/x.png', 'Reddit'),
                       ('https://x.com/user/status/1', 'X'), ('https://mobile.twitter.com/u', 'X'), ('https://www.linkedin.com/posts/a', 'LinkedIn'),
                       ('https://youtu.be/abc', 'YouTube'), ('https://t.me/chan/7', 'Telegram'), ('https://mastodon.social/@user/1', 'account'),
                       ('https://bsky.app/profile/did:plc:abc/post/1', 'account'), ('https://fosstodon.org/@a/2', 'account'),
                       ('https://fosstodon.org/users/a/statuses/2', 'account'), ('https://mastodon.social/statuses/2', 'Mastodon'),
                       ('https://api.npmjs.org/downloads/point/last-month/@anthropic-ai/claude-code', None),
                       ('https://news.ycombinator.com/item?id=1', None), ('https://box.com/x', None), ('https://art.me/x', None)]:
            self.assertEqual(pulse.url_net(u), net, u)

    def test_public_record_drops_handles_and_count_only_bodies(self):
        rec = lambda net, **k: {'net': net, 'title': 't', 'url': 'https://example.test/1', 'author': 'someone', 'score': 3, 'comments': 1,
                                'source': 'live', **k}
        self.assertEqual(pulse.public(rec('Reddit')), {'net': 'Reddit', 'source': 'live'})
        self.assertEqual(pulse.public(rec('Mastodon', at='2026-10-16')), {'net': 'Mastodon', 'source': 'live', 'at': '2026-10-16'})  # no check
        self.assertNotIn('author', pulse.public(rec('HN')))
        self.assertEqual(pulse.public(rec('Newsletter'))['author'], 'someone')                         # newsletter names stay
        self.assertNotIn('author', pulse.public(rec('GitHub', source='dossier')))                       # a dossier post's poster
        self.assertIsNone(pulse.public(rec('Bluesky', url='https://bsky.app/profile/a.b/post/1'))['url'])
        self.assertIsNone(pulse.public(rec('HN', link='https://x.com/u/status/1'))['link'])
        self.assertEqual(pulse.public(rec('HN', title='Thanks @dang for @scope/pkg'))['title'], 'Thanks @… for @scope/pkg')

    def test_reddit_headline_fallback_order(self):
        at = lambda h: pulse.NOW - timedelta(hours=h)
        d = lambda net, title, h: (p(net, title[:6], title, 'u', h), at(h), {}, set())
        reddit, hn = d('Reddit', 'GPT 6 leaked benchmark', 9), d('HN', 'GPT 6 benchmark notes', 5)
        self.assertEqual(pulse.headline_of(reddit, [reddit, d('Mastodon', 'GPT 6 toot', 7), hn], 'GPT 6')[0], 'GPT 6 benchmark notes')
        self.assertEqual(pulse.headline_of(reddit, [reddit], 'GPT 6'), ('GPT 6', None, None, 'und'))
        self.assertEqual(pulse.headline_of(reddit, [reddit], None), ('Reddit discussion, title not shown', None, None, 'en'))

    def test_built_stories_and_nodes_hold_no_count_only_text(self):
        posts = [p('Reddit', i, f'Claude Opus 5.5 routing is broken {i}', f'r{i}', 2 + i) for i in range(6)]
        posts += [p('HN', 9, 'Claude Opus 5.5 spotted in the API', 'h', 30, score=300)]
        nodes, _, _, _, extras = pulse.build(posts, LEX, HYPE)
        for x in nodes:
            for r in x['samples'] + x['spread']: self.assertTrue(r['net'] not in pulse.COUNT_ONLY or not set(r) & set(pulse.POST_BODY), r)
        self.assertTrue(extras['stories'])
        for st in extras['stories']:
            self.assertFalse(any(r['net'] in pulse.COUNT_ONLY or 'author' in r for r in st['posts']))
            self.assertTrue(all(not set(r) & set(pulse.POST_BODY) for r in st['path'] if r['net'] in pulse.COUNT_ONLY))
            self.assertNotIn('broken', st['headline'])


class MastodonLinkTest(unittest.TestCase):
    """Design row 3 (C25): a live mastodon.social post links to /statuses/<id> only while its latest check passed < 7 days ago."""
    def cache(self, statuses):
        d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, d)
        f = os.path.join(d, 'mastodon-links.json')
        with open(f, 'w') as fh: json.dump({'statuses': statuses}, fh)
        return f

    def test_only_a_fresh_latest_pass_links(self):
        at = lambda days: pulse.iso(pulse.NOW - timedelta(days=days))
        ok = lambda days: {'result': 'pass', 'checked_at': at(days), 'passed_at': at(days), 'api_status': 200}
        f = self.cache({'1': ok(6.9), '2': ok(7.1), '3': {'result': 'fail', 'checked_at': at(1), 'passed_at': at(2), 'api_status': 404},
                        '4': ok(-1), '5': 'junk'})
        self.assertEqual(pulse.load_links(f), {'1'})              # stale, failed since, from the future, malformed: none link
        self.assertEqual(pulse.load_links(f + '.missing'), set())  # no cache, no link (fail-closed)

    def test_link_is_handle_free_and_only_for_live_mastodon_social_posts(self):
        links = {'7', '8'}
        here = pulse.post('Mastodon', '7', 'https://mastodon.social/@someone/7', 'Opus 5.5 is out', 'someone', pulse.iso(pulse.NOW), 3, 1)
        away = pulse.post('Mastodon', '8', 'https://fosstodon.org/@a/99', 'Opus 5.5 is out', 'a', pulse.iso(pulse.NOW))
        self.assertEqual(pulse.masto_link(here, links), 'https://mastodon.social/statuses/7')
        self.assertIsNone(pulse.masto_link(away, links))                                  # another server: mastodon.social redirects it
        self.assertIsNone(pulse.masto_link({**here, 'source': 'dossier'}, links))
        self.assertIsNone(pulse.masto_link({**here, 'pid': '9'}, links))                   # no passing check
        rec = {'net': 'Mastodon', 'title': 'hi @someone', 'url': pulse.link_url(here, links), 'author': 'someone', 'score': 3, 'comments': 1}
        self.assertEqual(pulse.public(rec, links), {'net': 'Mastodon', 'title': 'hi @…', 'url': 'https://mastodon.social/statuses/7', 'score': 3, 'comments': 1})
        self.assertNotIn('title', pulse.public(rec))                                       # no links given: a count
        self.assertNotIn('title', pulse.public({**rec, 'url': 'https://mastodon.social/statuses/9'}, links))
        self.assertNotIn('title', pulse.public({**rec, 'url': here['url']}, links))
        # an orphan status link (an HN target, a story link) never publishes, checked or not: only a Mastodon record's own url does
        for u in ('https://mastodon.social/statuses/7', 'http://mastodon.social/statuses/7?x=1', 'https://mastodon.social/redirect/statuses/7'):
            self.assertIsNone(pulse.public({'net': 'HN', 'title': 't', 'url': 'https://news.ycombinator.com/item?id=1', 'link': u}, links)['link'], u)
        self.assertIsNone(pulse.public({'net': 'HN', 'title': 't', 'url': 'https://mastodon.social/statuses/7'}, links)['url'])

    def test_built_outputs_link_passed_posts_and_list_candidates(self):
        at = lambda h: pulse.iso(pulse.NOW - timedelta(hours=h))
        posts = [pulse.post('Mastodon', str(100 + i), f'https://mastodon.social/@m{i}/{100 + i}', f'Claude Opus 5.5 routing take {i}', f'm{i}',
                            at(2 + i), 5 + i, 1) for i in range(3)]
        posts += [pulse.post('Mastodon', '200', 'https://fosstodon.org/@far/200', 'Claude Opus 5.5 routing from afar', 'far', at(3), 50, 1),
                  pulse.post('HN', '9', 'https://news.ycombinator.com/item?id=9', 'Claude Opus 5.5 spotted in the API', 'h', at(30), 300, 1,
                             extra={'link': 'https://mastodon.social/statuses/555'})]
        want = pulse.mastodon_candidates(posts, LEX, HYPE, None)
        self.assertEqual(want, ['102', '101', '100'])                                     # newest first; the remote post never
        nodes, _, _, _, extras = pulse.build(posts, LEX, HYPE, links={'101', '555'})
        out = json.dumps([nodes, extras['stories']])
        self.assertEqual(set(pulse.STATUS_URL.findall(out)), {'101'})                    # the HN post's status target link is dropped
        self.assertNotIn('/@', out); self.assertNotIn('"author": "m1"', out)
        for x in nodes:
            for r in x['samples'] + x['spread']:
                if r['net'] == 'Mastodon': self.assertTrue(r.get('url') == 'https://mastodon.social/statuses/101' or not set(r) & set(pulse.POST_BODY), r)


@unittest.skipUnless(shutil.which('node'), 'node not installed')
class MastodonCheckTest(unittest.TestCase):
    """scripts/check_mastodon_links.mjs on recorded lookups and page snapshots (--fixture): no network, no browser."""
    def run_check(self, cap='300', **over):
        F = json.load(open(os.path.join(FIX, 'mastodon_check.json'))); F.update(over)
        d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, d)
        for name, key in (('fixture.json', None), ('candidates.json', 'candidates'), ('cache.json', 'cache')):
            with open(os.path.join(d, name), 'w') as fh: json.dump(F[key] if key else F, fh)
        r = subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_mastodon_links.mjs'), '--fixture', os.path.join(d, 'fixture.json'),
                            '--candidates', os.path.join(d, 'candidates.json'), '--cache', os.path.join(d, 'cache.json'), '--cap-seconds', cap],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout, json.load(open(os.path.join(d, 'cache.json')))['statuses']

    def test_results_reasons_and_lookup_status_per_id(self):
        out, st = self.run_check()
        self.assertIn('9 candidates, 7 due, 1 pass, 5 fail, 1 not reached (time cap 300s)', out)
        self.assertEqual({k: (v['result'], v.get('reason'), v['api_status']) for k, v in st.items() if v['checked_at'] == '2026-10-17T05:00:00Z'}, {
            '201': ('pass', None, 200), '202': ('fail', 'api 404', 404),
            '203': ('fail', 'redirects off mastodon.social (a post from another server)', 200),
            '205': ('fail', 'not-found page', 200), '207': ('fail', 'login wall', 200), '208': ('fail', 'empty page after 15s', 200)})
        self.assertEqual(st['201']['passed_at'], '2026-10-17T05:00:00Z')
        self.assertEqual(st['205']['passed_at'], '2026-10-10T17:00:00Z')                  # the last pass is kept through a later fail
        self.assertEqual(st['204']['checked_at'], '2026-10-15T05:00:00Z')                 # a 2-day-old pass is not due
        self.assertEqual(st['206']['checked_at'], '2026-10-17T03:00:00Z')                 # nor a fail from 2 hours ago
        self.assertNotIn('209', st)                                                        # not reached: no entry, so a count
        self.assertNotIn('300', st); self.assertIn('301', st)                              # pruned after 45 days unless needed

    def test_time_cap_stops_and_leaves_the_rest_unreached(self):
        out, st = self.run_check(cap='2', ms_per_check=1000)
        self.assertIn('0 pass, 2 fail, 5 not reached (time cap 2s; stopped: time cap reached)', out)
        self.assertEqual(sorted(k for k, v in st.items() if v['checked_at'] >= '2026-10-17T05:00:00Z'), ['207', '208'])


class ScrubTest(unittest.TestCase):
    """hype_build --scrub and the count-only dossier copy (design rows 1, 2, 4, 5; Decision 13, C35)."""
    def setUp(self):
        self.fx = json.load(open(os.path.join(FIX, 'dossier_scrub.json')))
        self.before = self.fx['hype']
        self.after = hype_build.scrub(copy.deepcopy(self.before), self.fx['dossier_sources'], self.fx['dossier_x_figures'])
        self.now = pulse.NOW
        pulse.NOW = datetime(2026, 10, 8, tzinfo=timezone.utc)

    def tearDown(self): pulse.NOW = self.now

    def nets(self, H): return [{k: sum(1 for p in it['posts'] if p['pl'] == k) for k in {p['pl'] for p in it['posts']}} for it in H['items'].values()]

    def test_scrub_keeps_counts_and_removes_handles_links_and_figures(self):
        a, cc = self.after, self.after['items']['claude-code']
        self.assertEqual(list(a['items']), list(self.before['items']))
        self.assertEqual(self.nets(a), self.nets(self.before))                              # items and per-network post counts kept
        self.assertTrue(all(set(x) == {'pl', 'd'} for x in cc['posts'] if x['pl'] in pulse.COUNT_ONLY))
        self.assertTrue(all('au' not in x and x['url'] and x['t'] for x in cc['posts'] if x['pl'] == 'HN'))
        self.assertFalse({'account', 'followers', 'cand_account'} & set(cc['viral']))
        self.assertEqual((cc['viral']['cand_post'], cc['first_seen_url'], cc['status_urls']), ('an X post', 'an X post', ['a Telegram post']))
        self.assertEqual(cc['summary_urls'], ['https://example.test/a', 'an X post', 'a Reddit post'])
        self.assertEqual(cc['links']['x_handle'], 'https://x.com/claudeai')                 # the project's own account stays
        self.assertEqual(cc['traction'][0]['value'], 'figure from an X post, not shown')
        self.assertEqual(cc['traction'][1]['value'], 1000)
        self.assertIsNone(cc['evidence_in']['usage'][0]['value'])
        self.assertEqual([s['by'] for s in cc['skeptic']], ['X user, sampled X post', 'Example Outlet'])
        self.assertEqual(cc['coord']['evidence'][0]['url'], 'an X post')
        place = self.fx['dossier_x_figures']['placeholder']['en']
        self.assertEqual(cc['notes']['momentum'], place + ' Release dated October 1.')
        self.assertEqual(a['items']['zephyr']['summary'], self.before['items']['zephyr']['summary'])   # listed keep
        self.assertEqual([h for h in hype_build.x_hits(a)], [('zephyr', 'summary', a['items']['zephyr']['summary'])])
        again = hype_build.scrub(copy.deepcopy(a), self.fx['dossier_sources'], self.fx['dossier_x_figures'])
        self.assertEqual(json.dumps(again, ensure_ascii=False), json.dumps(a, ensure_ascii=False))     # a second run changes nothing

    def test_count_only_records_are_placed_by_project_topic(self):
        recs = pulse.dossier_posts(self.after)
        x = [r for r in recs if r['net'] in pulse.COUNT_ONLY]
        self.assertEqual(len(x), 7)
        self.assertTrue(all(r['url'] is None and r['title'] == '' and r['author'] == '' and r['score'] is None and r['comments'] is None
                            and '/' not in r['pid'] and r['extra']['hype'] in self.after['items'] for r in x))
        nodes, *_ = pulse.build(recs, LEX, self.after['items'])
        n = {z['id']: z for z in nodes}
        tid = pulse.PROJECT_TOPIC['claude-code']
        self.assertEqual(n[tid]['w']['30d']['nets'], {'X': 3, 'HN': 2, 'LinkedIn': 1, 'YouTube': 1, 'Telegram': 1})   # all 3 X posts, text or not
        self.assertFalse(any(s['net'] in pulse.COUNT_ONLY for s in n[tid]['samples']))

    def test_scrub_changes_voices_weight_and_signal_in_the_expected_direction(self):
        def run(posts):
            nodes, *_ = pulse.build(posts, LEX, self.before['items'])
            return {z['id']: z['w']['30d'] for z in nodes}
        old, new = run(legacy_copy(self.before)), run(pulse.dossier_posts(self.after))
        tid = pulse.PROJECT_TOPIC['claude-code']
        self.assertEqual((old[tid]['authors'], new[tid]['authors']), (6, 5))    # X 2 (by text) + HN 2 + LinkedIn + YouTube -> one per network
        self.assertEqual((old[tid]['where']['HN']['voices'], new[tid]['where']['HN']['voices']), (2, 1))   # HN dossier voices merge
        self.assertEqual((old[tid]['nets']['X'], new[tid]['nets']['X']), (2, 3))     # the X post whose text missed the name is placed too
        for z in set(old) & set(new):                                                 # node voices, weight and engagement never rise
            for k in ('authors', 'weight', 'eng'): self.assertLessEqual(new[z][k], old[z][k], (z, k))
        # 'claude' held the dossier's X, LinkedIn and YouTube posts only by text match: it loses them, and its signal falls;
        # signal is a percentile among nodes, so the project node can rank higher while its own counts do not rise
        self.assertLess(new['claude']['authors'], old['claude']['authors'])
        self.assertLess(new['claude']['signal'], old['claude']['signal'])

    def test_dossier_post_already_stored_counts_once(self):
        live = self.fx['live']                                                       # stored live copies of the two HN dossier posts
        nodes, *_ = pulse.build(pulse.pool(live, pulse.dossier_posts(self.after)), LEX, self.after['items'])
        w = {z['id']: z for z in nodes}[pulse.PROJECT_TOPIC['claude-code']]['w']['30d']
        self.assertEqual((w['nets']['HN'], w['where']['HN']['voices']), (2, 2))        # not 4 posts and a third, author-less voice
        nodes, *_ = pulse.build(live + pulse.dossier_posts(self.after), LEX, self.after['items'])
        self.assertEqual({z['id']: z for z in nodes}[pulse.PROJECT_TOPIC['claude-code']]['w']['30d']['where']['HN'], {'posts': 4, 'voices': 3})

    def test_committed_hype_is_scrubbed_with_counts_kept(self):
        # the counts of the committed file at 2bc0ace; from B3 on, the daily refresh's scrub removes the dossier posts that
        # web/removals.json or web/checks/dossier-gone.json names (one hash can drop a URL two items share), so a count may only fall,
        # and no post left in the file is one either list names (a research pass resets the counts)
        raw = open(os.path.join(ROOT, 'web', 'hype.json'), 'rb').read()
        H = json.loads(raw)
        nets = {}
        for it in H['items'].values():
            for x in it['posts']: nets[x['pl']] = nets.get(x['pl'], 0) + 1
        base = {'X': 125, 'HN': 268, 'YouTube': 4, 'LinkedIn': 6, 'Telegram': 1, 'GitHub': 1}                         # as at 2bc0ace
        removed, gone = pulse.removal_lists(os.path.join(ROOT, 'web'))
        self.assertEqual(len(H['items']), 82); self.assertLessEqual(set(nets), set(base))
        drop = removed | {e['sha256'] for e in gone}
        for net, n in base.items(): self.assertLessEqual(nets.get(net, 0), n, net)
        self.assertFalse([x['url'] for it in H['items'].values() for x in it['posts'] if x.get('url') and hashlib.sha256(x['url'].encode()).hexdigest() in drop])
        self.assertEqual(json.dumps(hype_build.scrub(H), ensure_ascii=False, separators=(',', ':')).encode(), raw)   # idempotent
        figs = json.load(open(os.path.join(ROOT, 'web', 'i18n', 'dossier-x-figures.json')))
        keep = {(e['slug'], e['field'], e['sha256']) for e in figs['hits'] if e['disposition'] == 'keep'}
        strip = {e['sha256'] for e in figs['hits'] if e['disposition'] == 'strip'}
        self.assertTrue(all((s, f, hype_build.sha(t)) in keep for s, f, t in hype_build.x_hits(H)))
        shown = {hype_build.sha(t) for _, f, c, k in hype_build.prose_fields(H)
                 for t in hype_build.sentences(c[k] if isinstance(c, list) else c.get(k) if isinstance(c.get(k), str) else '')}
        self.assertFalse(strip & shown)
        self.assertNotIn(b'1,692 API-observed likes', raw)                             # the round-9 example sentence
        pulse.NOW = datetime(2026, 10, 8, tzinfo=timezone.utc)                         # the dossier's 30-day window, pinned
        recs = pulse.dossier_posts(H)
        nodes, *_ = pulse.build(recs, LEX, H['items'])
        n = {z['id']: z for z in nodes}
        want = {}
        for r in recs:
            if r['net'] in pulse.COUNT_ONLY and pulse.parse_dt(r['created']) >= pulse.NOW - timedelta(days=30):
                k = (pulse.PROJECT_TOPIC[r['extra']['hype']], r['net']); want[k] = want.get(k, 0) + 1
        placed = {k: v for k, v in want.items() if k[0] in n}
        self.assertGreaterEqual(len(placed), 10)                                       # nodes under the 2-post floor are not on the map
        for (tid, net), c in placed.items(): self.assertEqual(n[tid]['w']['30d']['nets'].get(net), c, (tid, net))


@unittest.skipUnless(shutil.which('node'), 'node not installed')
class LeakFixtureTest(unittest.TestCase):
    """Decision 14: each fixture overlays a copy of the committed web/; check_page.mjs must fail with that rule's own finding."""
    MASTO = 'Mastodon link without a render check passed less than 7 days before pulse.json generated_at'
    RULES = {'handle': 'person handle: HN author', 'skeptic_handle': 'person handle (@name)', 'account_url': 'account-naming URL (a person handle)',
             'reddit': 'Reddit link (Reddit is counts only)', 'linkedin': 'LinkedIn link (LinkedIn is counts only)',
             'x': "X link (X is counts only; only links.x_handle may link the project's own account) at 2 places",   # with and without a scheme
             'youtube': ('YouTube link (YouTube is counts only)', 'figure from a count-only post is shown at 2 places'),  # traction, metrics
             'telegram': 'Telegram link (Telegram is counts only)', 'x_figure': 'unlisted X-figure sentence',
             'title_handle': 'pulse.json: person handle (@name)',
             # design row 3: a Mastodon link needs a passing check younger than 7 days before generated_at, a handle-free URL and no author
             'mastodon_unchecked': f'pulse.json: {MASTO} (no check in checks/mastodon-links.json)',
             'mastodon_origin_url': ('pulse.json: count-only Mastodon record carries url', 'pulse.json: account-naming URL (a person handle)'),
             'mastodon_author': 'pulse.json: person handle: Mastodon author',
             'mastodon_failed_after_pass': (f'pulse.json: {MASTO} (its latest check failed) at 1 place',    # 111: a 404 after a pass
                                            f'pulse.json: {MASTO} (its check never passed) at 1 place'),   # 112: never passed
             'mastodon_stale_or_future': (f'pulse.json: {MASTO} (its last pass is 7 days or more before generated_at) at 1 place',  # 111
                                          f'pulse.json: {MASTO} (its pass is later than generated_at) at 1 place'),               # 112
             'mastodon_noncanonical': 'pulse.json: Mastodon status link not in the form https://mastodon.social/statuses/<id>'}
    CLEAN = ['clean_hype', 'clean_pulse', 'clean_mastodon']    # clean_mastodon: a pass 6 days before generated_at, weeks before the clock

    def check(self, name):
        with tempfile.TemporaryDirectory() as d:
            web = os.path.join(d, 'web')
            shutil.copytree(os.path.join(ROOT, 'web'), web)
            src = os.path.join(FIX, 'public_leaks', name)
            shutil.copytree(src, web, dirs_exist_ok=True)                 # files and subdirectories (checks/) over the copy
            return subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)

    def test_each_leak_fails_on_its_own_rule(self):
        self.assertEqual(sorted(os.listdir(os.path.join(FIX, 'public_leaks'))), sorted(list(self.RULES) + self.CLEAN))
        for name, msg in self.RULES.items():
            with self.subTest(name):
                r = self.check(name)
                self.assertEqual(r.returncode, 1, r.stdout)
                for m in (msg,) if isinstance(msg, str) else msg: self.assertIn(m, r.stderr)

    def test_clean_overlays_pass(self):
        for name in self.CLEAN:
            with self.subTest(name):
                r = self.check(name)
                self.assertEqual(r.returncode, 0, r.stderr)

# ------------------------------------------------------------------ briefing (design rows 6, 8, 9; group B1)
BRT = timezone(timedelta(hours=-3))
LABEL_WORDS = {'REAL', 'OVERHYPED', 'FALSE', 'PUSHED', 'UNVERIFIED'}


def read(path):
    with open(path, 'rb') as f: return f.read()


def recompute_top10(P):
    """SC-14, written apart from pulse.top10: the published rule applied to a pulse.json's stories at its generated_at."""
    now = datetime.fromisoformat(P['generated_at'].replace('Z', '+00:00'))
    lo, t = now - timedelta(hours=24), lambda s: datetime.fromisoformat(s.replace('Z', '+00:00'))
    live = [s for s in P['stories'] if s['kind'] == 'news' and s['covered'] and t(s['last']) >= lo]
    by_heat = lambda ss: sorted(ss, key=lambda s: (-s['heat'], -t(s['last']).timestamp(), s['id']))
    new, rest = by_heat([s for s in live if t(s['first']) >= lo]), by_heat([s for s in live if t(s['first']) < lo])
    return [(s['id'], 'new today' if s in new else 'first seen ' + t(s['first']).astimezone(BRT).date().isoformat()) for s in (new + rest)[:10]]


def top10_problems(P, B):
    """Empty when the briefing's ten ids, their order and their "new today" / first-seen readings equal the recompute."""
    want, got = recompute_top10(P), [(r['id'], r['seen']) for r in B['top10']]
    out = [] if B.get('generated_at') == P['generated_at'] else ['briefing and pulse.json come from different runs']
    if [i for i, _ in got] != [i for i, _ in want]: out.append(f'ids or order differ: {[i for i, _ in got]} != {[i for i, _ in want]}')
    elif got != want: out.append(f'seen readings differ: {got} != {want}')
    if [r['rank'] for r in B['top10']] != list(range(1, len(B['top10']) + 1)): out.append('ranks are not 1..n')
    return out


def offline_rebuild(d, now='2026-10-17T08:25:00Z'):
    """Decision 20 in miniature: store the fixture posts in a fresh history DB under d, then run pulse.py --offline against a web/
    holding only the fixture data.json and hype.json (no earlier pulse.json, so every adapter reads unknown). Returns d/web."""
    src = os.path.join(FIX, 'offline_rebuild')
    web, hist = os.path.join(d, 'web'), os.path.join(d, 'history')
    os.makedirs(web, exist_ok=True)
    for f in ('data.json', 'hype.json'): shutil.copy(os.path.join(src, f), web)
    keep = {k: getattr(pulse, k) for k in ('WEB', 'HIST', 'DB', 'CANDIDATES', 'NOW')}
    argv, sources = sys.argv, dict(pulse.SOURCES)
    try:
        pulse.WEB, pulse.HIST, pulse.DB = web, hist, os.path.join(hist, 'signals.sqlite')
        pulse.CANDIDATES = os.path.join(hist, 'mastodon-candidates.json')
        pulse.NOW = datetime.fromisoformat(now.replace('Z', '+00:00'))
        pulse.SOURCES.clear()
        con = pulse.db()
        pulse.store(con, [pulse.post(*r[:8], source=r[8], extra=r[9]) for r in json.loads(read(os.path.join(src, 'posts.json')))['posts']])
        con.close()
        sys.argv = ['pulse.py', '--offline']
        with contextlib.redirect_stdout(io.StringIO()): pulse.main()
    finally:
        for k, v in keep.items(): setattr(pulse, k, v)
        sys.argv = argv
        pulse.SOURCES.clear(); pulse.SOURCES.update(sources)
    return web


class BriefingRulesTest(unittest.TestCase):
    """Top 10 rule (R6-1), evidence records (C7-C9) and gauge values (C36) on fixed inputs."""
    def setUp(self):
        self.P = json.loads(read(os.path.join(FIX, 'top10', 'pulse.json')))
        self.now = datetime.fromisoformat(self.P['generated_at'].replace('Z', '+00:00'))

    def test_top10_new_today_first_then_heat_with_ties(self):
        rows = pulse.top10(self.P['stories'], self.now)
        self.assertEqual([r['id'] for r in rows], ['s:bbbbbbbbbbbb', 's:aaaaaaaaaaaa', 's:0fffffffffff', 's:eeeeeeeeeeee', 's:666666666666',
                                                   's:cccccccccccc', 's:111111111111', 's:dddddddddddd', 's:222222222222', 's:333333333333'])
        self.assertEqual([(r['id'], r['seen']) for r in rows], recompute_top10(self.P))
        self.assertEqual(rows[4]['seen'], 'new today')                    # first seen exactly at the window start is in the window
        self.assertEqual(rows[7]['seen'], 'first seen 2026-10-11')        # 2026-10-12T02:00Z is the 11th in BRT
        self.assertNotIn('s:999999999999', [r['id'] for r in rows])       # chatter, however hot
        self.assertNotIn('s:888888888888', [r['id'] for r in rows])       # no post in the last 24h

    def test_recompute_passes_the_fixture_and_fails_the_reordered_one(self):
        self.assertEqual(top10_problems(self.P, json.loads(read(os.path.join(FIX, 'top10', 'briefing.json')))), [])
        bad = top10_problems(self.P, json.loads(read(os.path.join(FIX, 'top10', 'briefing_reordered.json'))))
        self.assertEqual(len(bad), 1); self.assertIn('ids or order differ', bad[0])

    def story(self, **over):
        s = {'id': 's:aaaaaaaaaaaa', 'label': None, 'covered': True, 'kind': 'news', 'pain': 0.0, 'headline': 'A FALSE start, for REAL',
             'first': '2026-10-17T01:00:00Z', 'last': '2026-10-17T07:00:00Z', 'voices': 4, 'nets': {'HN': 1, 'Mastodon': 2, 'Reddit': 1},
             'newsletters': [], 'official': False, 'hn_points': 120, 'key': ['start'], 'tags': [], 'heat': 3.0, 'refs': {'repos': [], 'papers': []}}
        s.update(over)
        return s

    def sources(self, **status):
        out = {a: {'status': 'ok', 'detail': 'fixture'} for a in pulse.ADAPTERS}
        for a, v in status.items(): out[a]['status'] = v
        return out

    def test_unfetched_source_reads_not_fetched_never_false_or_zero(self):
        src = self.sources(**{'Official feeds (RSS)': 'unknown', 'Newsletters (RSS)': 'partial', 'Bluesky (app password)': 'not connected',
                              'Reddit (official API)': 'not connected', 'Lobsters (ai tag)': 'failed'})
        B = pulse.briefing([self.story(), self.story(id='s:bbbbbbbbbbbb', official=True, newsletters=['Example Weekly'])], [], src, None, self.now, 'm')
        a, b = B['records']
        self.assertEqual(a['computed']['official'], 'not fetched'); self.assertEqual(a['substance']['official'], 'not fetched')
        self.assertIs(b['computed']['official'], True)                      # true where it is true
        self.assertEqual(a['computed']['newsletters'], 'not fetched')       # partial: no newsletter seen is not 0
        self.assertEqual(b['computed']['newsletters'], 1)
        self.assertEqual(a['computed']['networks'], {'HN': 1, 'Lobsters': 'not fetched', 'Mastodon': 2, 'Reddit': 1, 'Bluesky': 'not fetched'})
        self.assertEqual(a['sources']['Reddit'], 'ok')                      # one Reddit adapter read ok
        rows = B['gauges'][1]['value']['stories']
        self.assertEqual(rows[0]['substance']['official'], 'not fetched'); self.assertEqual(rows[0]['hype']['newsletters'], 'not fetched')
        self.assertEqual(rows[0]['hype']['networks']['Bluesky'], 'not fetched')
        ok = pulse.briefing([self.story(nets={'HN': 1})], [], self.sources(), None, self.now, 'm')['records'][0]['computed']
        self.assertEqual((ok['official'], ok['newsletters'], ok['networks']['Bluesky']), (False, 0, 0))   # fully fetched: a real 0

    def test_records_are_proposals_with_stable_id_method_and_no_label_word(self):
        B = pulse.briefing([self.story()], [], self.sources(), None, self.now, 'm')
        r = B['records'][0]
        self.assertEqual(r['state'], 'proposed')
        self.assertFalse({'label', 'verdict'} & set(r))
        self.assertEqual((r['id'], r['method_version'], r['config_hash']), ('s:aaaaaaaaaaaa', pulse.BRIEFING_VERSION, B['method']['config_hash']))
        self.assertRegex(r['config_hash'], r'^[0-9a-f]{16}$')
        def values(o):
            if isinstance(o, dict): return [v for k, x in o.items() if k != 'headline' for v in values(x)]
            return [v for x in o for v in values(x)] if isinstance(o, list) else [o]
        self.assertFalse(LABEL_WORDS & {v for v in values(r) if isinstance(v, str)})
        self.assertNotEqual(pulse.briefing([self.story()], [], self.sources(), None, self.now, 'other method')['method']['config_hash'],
                            B['method']['config_hash'])                   # the hash follows the method text

    def test_substance_is_the_storys_own_links_and_topic_samples_are_related(self):
        node = {'id': 'p:claude-code', 'samples': [{'net': 'GitHub', 'title': 'hookkit: hooks', 'url': 'https://github.com/example/hookkit', 'source': 'tracker'},
                                                   {'net': 'GitHub', 'title': 'hooks', 'url': 'https://github.com/example/hooks', 'source': 'tracker'},
                                                   {'net': 'HN', 'title': 'a post', 'url': 'https://news.ycombinator.com/item?id=1', 'source': 'live'}]}
        s = self.story(tags=['p:claude-code'], refs={'repos': ['https://github.com/example/hooks'], 'papers': []})
        r = pulse.briefing([s], [node], self.sources(), None, self.now, 'm')['records'][0]
        self.assertEqual(r['substance']['repos'], ['https://github.com/example/hooks'])
        self.assertEqual(r['related_in_topic'], {'reading': 'related in topic', 'items': [
            {'topic': 'p:claude-code', 'net': 'GitHub', 'title': 'hookkit: hooks', 'lang': 'und', 'url': 'https://github.com/example/hookkit'}]})
        self.assertEqual(pulse.own_refs(['https://github.com/example/hooks/tree/main', 'https://github.com/Example/Hooks.git', 'https://github.com/features/copilot',
                                         'https://github.com/example', 'https://arxiv.org/pdf/2610.01234v2', 'https://huggingface.co/papers/2610.01234',
                                         'https://www.reddit.com/r/x/comments/abc/github.com/a/b', None]),
                         {'repos': ['https://github.com/example/hooks'], 'papers': ['https://arxiv.org/abs/2610.01234']})

    def test_gauges_previews_with_coverage_floors_and_placeholders(self):
        D = {'generated_at': '2026-10-17T07:00:00Z', 'views': ['all', 'agents', 'other'], 'tracked': {'papers': 3, 'repos': 1},
             'papers': {'items': {'1': {'tag': 'agents', 'published': '2026-10-11'}, '2': {'tag': 'agents', 'published': '2026-10-10'},
                                  '3': {'tag': 'other', 'published': '2026-10-17'}}},
             'repos': {'items': {'a/b': {'tag': 'agents', 'created': '2026-10-16'}}}}
        src = self.sources(); src['Tracker (papers + repos)'] = {'status': 'ok', 'detail': 'fixture'}
        nodes = [{'id': 't1', 'label': 'Up', 'rising': 3.0, 'w': {'1d': {'posts': 6}, '7d': {'posts': 14}}},
                 {'id': 't2', 'label': 'Down', 'rising': 0.5, 'w': {'1d': {'posts': 2}, '7d': {'posts': 28}}},
                 {'id': 't3', 'label': 'Quiet', 'rising': None, 'w': {'1d': {'posts': 0}, '7d': {'posts': 1}}}]
        B = pulse.briefing([self.story()], nodes, src, D, self.now, 'm')
        names = [g['name'] for g in B['gauges']]
        self.assertEqual(names, ['Releases / research output by area', 'Hype vs substance', 'Daily movers'])
        self.assertLessEqual(len(B['gauges']), 4)
        for g in B['gauges']:
            self.assertEqual((g['status'], g['trend']), ('preview, not yet reproducible', None)); self.assertTrue(g['coverage'])
        self.assertEqual(B['gauges'][0]['value']['areas'], [{'area': 'agents', 'papers': 1, 'repos': 1}, {'area': 'other', 'papers': 1, 'repos': 0}])
        self.assertEqual(B['gauges'][2]['value']['up'][0]['topic'], 't1'); self.assertEqual(B['gauges'][2]['value']['down'][0]['topic'], 't2')
        self.assertEqual(B['gauges'][2]['coverage']['topics_with_reading'], 2)
        self.assertEqual([(p['name'], p['reading']) for p in B['panels']], [('Risk', 'no qualified source'), ('Jobs', 'no qualified source')])
        self.assertEqual(B['panels'][0]['events'], [])
        self.assertFalse([k for k in B if 'score' in k])
        # below the floor: null with the reason, never a value carried over
        stale = dict(D, generated_at='2026-10-15T07:00:00Z')
        down = dict(src, **{'Tracker (papers + repos)': {'status': 'failed', 'detail': 'x'}})
        old = pulse.briefing([self.story(last='2026-10-15T00:00:00Z')], [nodes[2]], src, stale, self.now, 'm')
        for g, why in zip(old['gauges'], ('the tracker data is older', 'no covered news story', 'no topic had 4+')):
            self.assertIsNone(g['value']); self.assertTrue(g['reason'].startswith('insufficient data: ' + why), g['reason'])
        self.assertIn('was not read', pulse.briefing([], [], down, D, self.now, 'm')['gauges'][0]['reason'])
        self.assertIn('no conversation network', pulse.briefing([], nodes, {}, None, self.now, 'm')['gauges'][2]['reason'])

    def test_window_end_is_now_printed_in_brt_and_ledger_days(self):
        B = pulse.briefing([], [], {}, None, self.now, 'm', days=3)
        self.assertEqual(B['window'], {'start': '2026-10-16T08:25:00Z', 'end': '2026-10-17T08:25:00Z', 'end_brt': '2026-10-17 05:25 BRT', 'hours': 24})
        self.assertEqual(B['generated_at'], B['window']['end']); self.assertEqual(B['ledger_days'], 3)
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, 'index.json')
            self.assertEqual(pulse.ledger_days(f), 0)
            for body, n in (([{'date': '2026-10-16'}, {'date': '2026-10-17'}], 2), ({'entries': [{}]}, 1), ({'x': 1}, 0)):
                with open(f, 'w') as fh: json.dump(body, fh)
                self.assertEqual(pulse.ledger_days(f), n)

    def test_story_ids_are_unique_when_two_clusters_name_one_release(self):
        # an HN seed naming no release carries a Reddit post that names Qwen 3.8 (attached by its words); five Mastodon posts naming
        # Qwen 3.8 form their own story: both name the release, so before B1 both took the id of "release:v:qwen-3.8"
        posts = [p('HN', 1, 'Llama.cpp on a jailbroken PS5 console runs any GGUF model', 'h1', 10, score=300),
                 p('Reddit', 2, 'Qwen 3.8 on my jailbroken PS5 console through llama.cpp GGUF', 'r1', 8)]
        posts += [p('Mastodon', 10 + i, f'Qwen 3.8 is great at coding, take {i}', f'm{i}', 2 + i) for i in range(5)]
        posts += [p('Mastodon', 100 + i, f'zq{i}word xv{i}thing kp{i}stuff', f'f{i}', 30) for i in range(150)]   # uncommon-word floor
        st = {s['kind']: s for s in pulse.build(posts, LEX, HYPE)[4]['stories']}
        sha = lambda k: 's:' + hashlib.sha1(k.encode()).hexdigest()[:12]
        self.assertEqual((st['news']['label'], st['chatter']['label']), ('Qwen 3.8', 'Qwen 3.8'))
        self.assertEqual(st['news']['id'], sha('release:v:qwen-3.8'))                        # earliest editorial post (10h ago): release key
        self.assertEqual(st['chatter']['id'], sha('https://example.test/Mastodon/14'))       # the other: its earliest post (6h ago)
        # more posts naming the release on the later story do not swap the two ids
        more = posts + [p('Mastodon', 40 + i, f'Qwen 3.8 is great at coding, again {i}', f'n{i}', 1) for i in range(8)]
        st2 = {s['kind']: s['id'] for s in pulse.build(more, LEX, HYPE)[4]['stories']}
        self.assertEqual(st2, {'news': st['news']['id'], 'chatter': st['chatter']['id']})

    def test_node_samples_with_equal_scores_keep_one_order(self):
        posts = [p('HN', 1, 'Claude Opus 5.5 lands in the API', 'a', 3, score=50), p('HN', 2, 'Claude Opus 5.5 pricing explained', 'b', 3, score=50),
                 p('HN', 3, 'Claude Opus 5.5 benchmarks for agents', 'c', 3, score=50)]
        urls = lambda ps: {n['id']: [x['url'] for x in n['samples']] for n in pulse.build(ps, LEX, HYPE)[0]}
        fwd, rev = urls(posts), urls(posts[::-1])
        self.assertEqual(fwd, rev)
        self.assertTrue(any(len(u) == 3 for u in fwd.values()), fwd)
        for u in fwd.values(): self.assertEqual(u, sorted(u))            # equal score and age: by url


class OfflineRebuildTest(unittest.TestCase):
    """The offline-rebuild fixture: pulse.py --offline with every adapter unknown writes briefing.json beside pulse.json, the
    records and the Hype vs substance values read "not fetched", the output is byte-identical across runs and hash seeds,
    and check_page.mjs accepts it on a copy of the committed web/."""
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.web = offline_rebuild(cls.tmp.name)
        cls.raw = read(os.path.join(cls.web, 'briefing.json'))
        cls.B, cls.P = json.loads(cls.raw), json.loads(read(os.path.join(cls.web, 'pulse.json')))

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def test_records_and_gauge_values_read_not_fetched(self):
        B, P = self.B, self.P
        self.assertEqual(B['generated_at'], P['generated_at'])
        self.assertEqual({v['status'] for k, v in B['sources'].items() if k in pulse.ADAPTERS}, {'unknown'})
        self.assertEqual([r['id'] for r in B['records']], [s['id'] for s in P['stories']])
        # B3: --offline makes no recheck call, so HN 501 and 502 are counts (C34, Decision 20): the Lobsters title leads the hooks
        # story and muse loses the paper only HN 502 linked; both HN posts are counted and never shown
        hooks = next(r for r in B['records'] if 'hookmarket' in r['headline'].lower())
        muse = next(r for r in B['records'] if 'muse' in r['headline'].lower())
        self.assertEqual(hooks['computed']['official'], 'not fetched'); self.assertIs(muse['computed']['official'], True)
        self.assertEqual(hooks['computed']['newsletters'], 'not fetched')
        self.assertEqual(hooks['computed']['networks']['Bluesky'], 'not fetched')
        self.assertEqual(hooks['computed']['networks']['HN'], 1)
        self.assertEqual(hooks['substance']['repos'], ['https://github.com/example/hooks'])          # not the Reddit post's link
        self.assertEqual((hooks['headline'], muse['substance']['papers'], muse['computed']['networks']['HN']),
                         ('HookMarket plugin marketplace for Claude Code explained', [], 1))
        self.assertNotIn('item?id=50', json.dumps([P, B])); self.assertNotIn('open weights for a new LLM', json.dumps([P, B]))
        self.assertIn('https://github.com/example/hookkit', [x['url'] for x in hooks['related_in_topic']['items']])
        self.assertEqual(hooks['related_in_topic']['reading'], 'related in topic')
        for r in B['records']: self.assertEqual(r['state'], 'proposed')
        self.assertEqual([(t['id'], t['seen']) for t in B['top10']], [(hooks['id'], 'new today'), (muse['id'], 'first seen 2026-10-14')])
        self.assertEqual(top10_problems(P, B), [])
        g = {x['id']: x for x in B['gauges']}
        for row in g['hype_vs_substance']['value']['stories']:
            self.assertEqual(row['hype']['newsletters'], 'not fetched'); self.assertEqual(row['hype']['networks']['Bluesky'], 'not fetched')
        self.assertEqual(g['hype_vs_substance']['value']['stories'][0]['substance']['official'], 'not fetched')
        self.assertIsNone(g['daily_movers']['value']); self.assertIn('no conversation network was fetched', g['daily_movers']['reason'])
        self.assertEqual(g['output_by_area']['value'], {'since': '2026-10-11', 'areas': [{'area': 'agents', 'papers': 1, 'repos': 1},
                                                                                          {'area': 'other', 'papers': 1, 'repos': 0}]})
        self.assertNotIn(b'\n', self.raw)                                                          # Decision 19: compact, one line

    def test_same_inputs_give_byte_identical_briefing(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(read(os.path.join(offline_rebuild(d), 'briefing.json')), self.raw)
        code = 'import sys; sys.path[:0] = [sys.argv[1], sys.argv[2]]; import test_pulse; test_pulse.offline_rebuild(sys.argv[3])'
        for seed in ('1', '2'):
            with tempfile.TemporaryDirectory() as d:
                r = subprocess.run([sys.executable, '-c', code, os.path.join(ROOT, 'tests'), ROOT, d], capture_output=True, text=True,
                                   env=dict(os.environ, PYTHONHASHSEED=seed), cwd=ROOT)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(read(os.path.join(d, 'web', 'briefing.json')), self.raw, f'PYTHONHASHSEED={seed}')

    @unittest.skipUnless(shutil.which('node'), 'node not installed')
    def test_page_check_accepts_the_rebuilt_briefing(self):
        with tempfile.TemporaryDirectory() as d:
            web = os.path.join(d, 'web')
            shutil.copytree(os.path.join(ROOT, 'web'), web)
            shutil.copy(os.path.join(self.web, 'briefing.json'), web)
            r = subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)


class DayFilesTest(unittest.TestCase):
    """SC-14 on the committed day's files: the briefing's ten ids and order equal a recompute from web/pulse.json, and every story
    has its record with the story's own computed fields and links (C8, C9, C13, C19)."""
    def setUp(self):
        self.P = json.loads(read(os.path.join(ROOT, 'web', 'pulse.json')))
        self.B = json.loads(read(os.path.join(ROOT, 'web', 'briefing.json')))

    def test_top10_equals_the_recompute(self):
        self.assertEqual(top10_problems(self.P, self.B), [])
        self.assertLessEqual(len(self.B['top10']), 10)

    def test_one_record_per_story_built_from_its_fields(self):
        st = {s['id']: s for s in self.P['stories']}
        self.assertEqual([r['id'] for r in self.B['records']], list(st))
        for r in self.B['records']:
            s = st[r['id']]
            self.assertEqual((r['state'], r['headline'], r['first'], r['last'], r['computed']['voices'], r['computed']['heat']),
                             ('proposed', s['headline'], s['first'], s['last'], s['voices'], s['heat']))
            self.assertEqual((r['substance']['repos'], r['substance']['papers']), (s['refs']['repos'], s['refs']['papers']))
            self.assertFalse({x['url'] for x in r['related_in_topic']['items']} & set(s['refs']['repos'] + s['refs']['papers']))
            if r['sources']['Official'] != 'ok' and not s['official']: self.assertEqual(r['computed']['official'], 'not fetched')

    def test_refresh_commits_the_briefing(self):
        wf = read(os.path.join(ROOT, '.github', 'workflows', 'refresh.yml')).decode()
        self.assertRegex(wf, r'git add [^\n]*web/pulse\.json[^\n]*web/briefing\.json|git add [^\n]*web/briefing\.json[^\n]*web/pulse\.json')


def ledger_companions(web):
    """A fixture ledger/index.json holds complete entries; their day files ({date, manifest: {asset, sha256}}, the bytes whose SHA256 is
    the entry's ledger_sha256), empty archive files and pending OpenTimestamps proofs (one attestation on the manifest SHA256, the bytes
    whose SHA256 is the entry's ots.sha256; group E2) are written here, so a 13-day fixture needs no 39 committed files."""
    try: E = json.loads(read(os.path.join(web, 'ledger', 'index.json')))
    except FileNotFoundError: return
    os.makedirs(os.path.join(web, 'ledger', 'ids'), exist_ok=True); os.makedirs(os.path.join(web, 'ledger', 'ots'), exist_ok=True)
    uri = b'https://alice.btc.calendar.opentimestamps.org'; att = bytes([len(uri)]) + uri
    for e in E:
        with open(os.path.join(web, 'ledger', 'ots', e['date'] + '.ots'), 'wb') as f:
            f.write(bytes.fromhex('004f70656e54696d657374616d7073000050726f6f6600bf89e2e884e89294') + b'\x01\x08' + bytes.fromhex(e['manifest_sha256'])
                    + b'\x00' + bytes.fromhex('83dfe30d2ef90c8e') + bytes([len(att)]) + att)
        day = json.dumps({'date': e['date'], 'manifest': {'asset': e['asset'], 'sha256': e['manifest_sha256']}}, separators=(',', ':'))
        with open(os.path.join(web, 'ledger', e['date'] + '.json'), 'w') as f: f.write(day)
        with open(os.path.join(web, 'ledger', 'ids', e['date'] + '.json'), 'w') as f: json.dump({'date': e['date'], 'generated_at': e['generated_at'], 'ids': []}, f)


@unittest.skipUnless(shutil.which('node'), 'node not installed')
class BriefingFixtureTest(unittest.TestCase):
    """Decision 14 for the briefing: each fixture overlays a copy of the committed web/ with its briefing.json; check_page.mjs must fail
    with that rule's own finding (SC-10 REAL-carrying record and not-fetched, SC-15 trend at 13 ledger days, SC-25 shipped gauge)."""
    RULES = {'real_record': 'briefing.json: pipeline record carries a label word (REAL)',          # state "REAL (proposed)"
             'trend_13_days': 'briefing.json: trend or arrow before 14 ledger days at 1 place',     # with a 13-entry ledger/index.json
             'shipped_gauge': 'briefing.json: gauge marked shipped (no gauge ships in S1)',
             'unfetched_false': 'briefing.json: Official not fully fetched but a count reads false (must read "not fetched")',
             'combined_score': 'briefing.json: gauge not named by the council (no combined score)',
             'reddit_leak': 'briefing.json: Reddit link (Reddit is counts only)'}
    CLEAN = ['clean_briefing']
    def check(self, name):
        with tempfile.TemporaryDirectory() as d:
            web = os.path.join(d, 'web')
            shutil.copytree(os.path.join(ROOT, 'web'), web)
            own = os.path.isdir(os.path.join(FIX, 'briefing', name, 'ledger'))
            if own: shutil.rmtree(os.path.join(web, 'ledger'))                           # a fixture with a ledger: its own ledger only
            shutil.copytree(os.path.join(FIX, 'briefing', name), web, dirs_exist_ok=True)
            if own: ledger_companions(web)
            return subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)

    def test_each_fixture_fails_on_its_own_rule(self):
        self.assertEqual(sorted(os.listdir(os.path.join(FIX, 'briefing'))), sorted(list(self.RULES) + self.CLEAN))
        for name, msg in self.RULES.items():
            with self.subTest(name):
                r = self.check(name)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(msg, r.stderr)
        r = self.check('trend_13_days')                                    # the 13-day path alone: ledger_days agrees with the ledger
        self.assertEqual([l for l in r.stderr.splitlines() if l.startswith('- ')], ['- ' + self.RULES['trend_13_days'] + ', e.g. gauges[0].trend'])

    def test_clean_overlay_passes(self):
        for name in self.CLEAN:
            with self.subTest(name):
                r = self.check(name)
                self.assertEqual(r.returncode, 0, r.stderr)



# ------------------------------------------------------------------ verdicts, story-id aliases and corrections (design row 7; group B2)
def story(sid, *names, net='HN', link=True):
    # one post per name, at a time of its own (the alias key is network and post time; the link is never part of it)
    at = lambda n: pulse.iso(datetime(2026, 10, 16, tzinfo=timezone.utc) + timedelta(seconds=int(hashlib.sha1(n.encode()).hexdigest()[:5], 16)))
    return {'id': sid, 'posts': [{'net': net, 'at': at(n), **({'url': 'https://example.test/' + n} if link else {})} for n in names], 'path': []}


class StoryAliasTest(unittest.TestCase):
    """SC-11, alias part (C2, C32): pulse.py maps a story id whose posts carried over to a new id, from the previous pulse.json."""
    def setUp(self): self.now = pulse.NOW

    def tearDown(self): pulse.NOW = self.now

    def posts(self):
        posts = [p('HN', 1, 'Llama.cpp runs on a jailbroken PS5 console with any GGUF model', 'h1', 10, score=300),
                 p('Lobsters', 2, 'A jailbroken PS5 console runs llama.cpp GGUF models', 'l1', 9)]
        return posts + [p('Mastodon', 100 + i, f'zq{i}word xv{i}thing kp{i}stuff', f'f{i}', 30) for i in range(250)]   # uncommon-word floor

    def test_story_gaining_an_earlier_post_maps_old_id_to_new(self):
        posts = self.posts()
        prev = [s for s in pulse.build(posts, LEX, HYPE)[4]['stories'] if 'PS5' in s['headline']]
        self.assertEqual(len(prev), 1)
        earlier = p('HN', 0, 'Llama.cpp runs on a jailbroken PS5 console with any GGUF model', 'h0', 20, score=50)   # an earlier submission
        today = [s for s in pulse.build(posts + [earlier], LEX, HYPE)[4]['stories'] if 'PS5' in s['headline']]
        self.assertEqual(len(today), 1)
        old, new = prev[0]['id'], today[0]['id']
        self.assertEqual(old, 's:' + hashlib.sha1(b'https://example.test/HN/1').hexdigest()[:12])
        self.assertEqual(new, 's:' + hashlib.sha1(b'https://example.test/HN/0').hexdigest()[:12])       # the earlier post's key
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, 'pulse.json'), 'w') as f: json.dump({'stories': prev}, f)          # the previous pulse.json
            path = os.path.join(d, 'story-aliases.json')
            pulse.NOW = datetime(2026, 10, 17, 8, 25, tzinfo=timezone.utc)
            pulse.write_aliases(json.loads(read(os.path.join(d, 'pulse.json')))['stories'], today, pulse.NOW, path)
            A = json.loads(read(path))
            self.assertEqual(A['aliases'], {old: {'to': new, 'since': '2026-10-17'}})
            self.assertEqual(A['generated_at'], '2026-10-17T08:25:00Z')
            self.assertNotIn(b'\n', read(path))                                         # generated: one compact line (Decision 19)
            pulse.write_aliases(today, today, pulse.NOW, path)                           # a later run with no move keeps the alias
            self.assertEqual(json.loads(read(path))['aliases'], {old: {'to': new, 'since': '2026-10-17'}})

    def test_alias_wins_over_a_live_id_whose_posts_moved(self):
        # B1 note: the old id still exists today, but the story that took its posts is the other one
        prev = [story('s:aaaaaaaaaaaa', 'u1', 'u2', 'u3')]
        today = [story('s:aaaaaaaaaaaa', 'u9', 'u1'), story('s:bbbbbbbbbbbb', 'u2', 'u3', 'u4')]
        self.assertEqual(pulse.story_aliases(prev, today, {}, 'd'), {'s:aaaaaaaaaaaa': {'to': 's:bbbbbbbbbbbb', 'since': 'd'}})

    def test_a_post_maps_the_same_with_or_without_its_link(self):
        # a Mastodon post gains or loses its handle-free link with the render check; the alias follows its posts either way
        prev = [story('s:aaaaaaaaaaaa', 'm1', 'm2', net='Mastodon')]
        today = [story('s:bbbbbbbbbbbb', 'm1', 'm2', 'm3', net='Mastodon', link=False)]
        self.assertEqual(pulse.post_keys(prev[0]), pulse.post_keys(story('s:aaaaaaaaaaaa', 'm1', 'm2', net='Mastodon', link=False)))
        self.assertEqual(pulse.story_aliases(prev, today, {}, 'd'), {'s:aaaaaaaaaaaa': {'to': 's:bbbbbbbbbbbb', 'since': 'd'}})
        self.assertEqual(pulse.story_aliases(today, [story('s:cccccccccccc', 'm1', 'm2', 'm3', net='Mastodon')], {}, 'd'),
                         {'s:bbbbbbbbbbbb': {'to': 's:cccccccccccc', 'since': 'd'}})

    def test_no_alias_without_most_of_the_posts(self):
        prev = [story('s:aaaaaaaaaaaa', 'u1', 'u2', 'u3'), story('s:cccccccccccc', 'n1', net='Newsletter') ]
        cases = {'a third carried': [story('s:bbbbbbbbbbbb', 'u1', 'x')],
                 'tie with its own id': [story('s:aaaaaaaaaaaa', 'u1', 'u2'), story('s:bbbbbbbbbbbb', 'u2', 'u3')],
                 'a shared newsletter issue only': [story('s:dddddddddddd', 'n1', net='Newsletter')]}
        for name, today in cases.items():
            with self.subTest(name): self.assertEqual(pulse.story_aliases(prev, today, {}, 'd'), {})

    def test_aliases_are_cumulative_follow_moves_and_drop_self_maps(self):
        old = {'s:aaaaaaaaaaaa': {'to': 's:bbbbbbbbbbbb', 'since': 'd0'}, 's:eeeeeeeeeeee': {'to': 's:ffffffffffff', 'since': 'd0'}}
        prev = [story('s:bbbbbbbbbbbb', 'u1', 'u2'), story('s:ffffffffffff', 'v1', 'v2')]
        today = [story('s:cccccccccccc', 'u1', 'u2', 'u3'), story('s:eeeeeeeeeeee', 'v1', 'v2')]   # f moved back to e
        self.assertEqual(pulse.story_aliases(prev, today, old, 'd1'),
                         {'s:aaaaaaaaaaaa': {'to': 's:cccccccccccc', 'since': 'd0'}, 's:bbbbbbbbbbbb': {'to': 's:cccccccccccc', 'since': 'd1'},
                          's:ffffffffffff': {'to': 's:eeeeeeeeeeee', 'since': 'd1'}})

    def test_offline_run_writes_the_alias_file_without_a_previous_pulse(self):
        with tempfile.TemporaryDirectory() as d:
            A = json.loads(read(os.path.join(offline_rebuild(d), 'story-aliases.json')))
            self.assertEqual((A['aliases'], A['generated_at']), ({}, '2026-10-17T08:25:00Z'))
            self.assertEqual(A['method'], pulse.ALIAS_METHOD)

    def test_refresh_stages_aliases_and_never_the_owner_files(self):
        wf = read(os.path.join(ROOT, '.github', 'workflows', 'refresh.yml')).decode()
        add = [l for l in wf.splitlines() if l.strip().startswith('git add ')]
        self.assertEqual(len(add), 1)
        self.assertIn('web/story-aliases.json', add[0].split())
        for f in ('web/verdicts.json', 'web/corrections.json', 'web', 'web/', '.', '-A', '--all'): self.assertNotIn(f, add[0].split()[2:])

    def test_committed_alias_file_maps_ids(self):
        A = json.loads(read(os.path.join(ROOT, 'web', 'story-aliases.json')))
        for k, e in A['aliases'].items():
            self.assertRegex(k, r'^s:[0-9a-f]{12}$'); self.assertRegex(e['to'], r'^s:[0-9a-f]{12}$'); self.assertNotEqual(k, e['to'])


@unittest.skipUnless(shutil.which('node'), 'node not installed')
class VerdictFixtureTest(unittest.TestCase):
    """SC-11 (C2, C10, C11, C30, C32), Decision 14: each case overlays a copy of the committed web/ with its files; check_page.mjs exits 1
    with exactly that case's findings, or 0 with its summary; archive/ is a row confirmed 9 days before the committed pulse.json whose
    story is gone from it but whose id is in that day's archive file."""
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(read(os.path.join(FIX, 'verdicts', 'cases.json')))['cases']
        cls.live = [s['id'] for s in json.loads(read(os.path.join(ROOT, 'web', 'pulse.json')))['stories']]

    def check(self, files=None, tree=None):
        with tempfile.TemporaryDirectory() as d:
            web = os.path.join(d, 'web')
            shutil.copytree(os.path.join(ROOT, 'web'), web)
            with open(os.path.join(web, 'story-aliases.json'), 'w') as f: json.dump({'aliases': {}}, f)   # the committed map moves daily
            shutil.rmtree(os.path.join(web, 'ledger'), ignore_errors=True); os.makedirs(os.path.join(web, 'ledger'))   # so does the ledger
            with open(os.path.join(web, 'ledger', 'index.json'), 'w') as f: f.write('[]')
            if tree: shutil.copytree(tree, web, dirs_exist_ok=True)
            for rel, body in (files or {}).items():
                if body is None: os.remove(os.path.join(web, rel)); continue
                text = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
                text = text.replace('$LIVE0', self.live[0]).replace('$LIVE1', self.live[1])
                os.makedirs(os.path.dirname(os.path.join(web, rel)), exist_ok=True)
                with open(os.path.join(web, rel), 'w') as f: f.write(text)
            return subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)

    def test_each_case_fails_on_its_own_rule_or_passes(self):
        self.assertNotIn('s:000000000000', self.live)
        for name, c in self.cases.items():
            with self.subTest(name):
                r = self.check(c['files'])
                if 'ok' in c:
                    self.assertEqual(r.returncode, 0, r.stderr); self.assertIn(c['ok'], r.stdout)
                    continue
                self.assertEqual(r.returncode, 1, r.stdout)
                got = [l[2:] for l in r.stderr.splitlines() if l.startswith('- ')]
                want = [m.replace('$LIVE0', self.live[0]) for m in c['expect']]
                self.assertEqual(len(got), len(want), r.stderr)
                for m in want: self.assertTrue(any(g.startswith(m) for g in got), (m, got))

    def test_row_confirmed_nine_days_before_resolves_through_the_archive(self):
        tree = os.path.join(FIX, 'verdicts', 'archive')
        V = json.loads(read(os.path.join(tree, 'verdicts.json')))['rows'][0]
        A = json.loads(read(os.path.join(tree, 'ledger', 'ids', V['confirmed'] + '.json')))
        self.assertEqual(V['confirmed'], '2026-10-08')                  # 9 days before the 2026-10-17 pulse.json this group committed
        self.assertNotIn(V['id'], self.live); self.assertIn(V['id'], A['ids'])
        r = self.check(tree=tree)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('verdicts 1 rows (0 live, 0 by alias, 1 by archive; 0 aliases, 1 archive days)', r.stdout)
        r = self.check(files={'ledger/ids/2026-10-08.json': {'date': '2026-10-08', 'ids': ['s:1b1b1b1b1b1b']}}, tree=tree)
        self.assertEqual(r.returncode, 1)                                # the same row without its id in the archive is orphaned
        self.assertIn('verdicts.json: orphaned s: id', r.stderr)

    def test_x_and_youtube_mirrors_are_counts_only_in_pulse_too(self):
        for u, net in [('https://t.co/AbCdEf123', 'X'), ('https://nitter.net/i/status/1', 'X'), ('https://fxtwitter.com/i/status/1', 'X'),
                       ('https://vxtwitter.com/i/status/1', 'X'), ('https://www.youtube-nocookie.com/embed/x', 'YouTube'), ('https://t.com/x', None)]:
            with self.subTest(u): self.assertEqual(pulse.url_net(u), net)

    def test_committed_owner_files_are_valid(self):
        # shape only: both grow by the owner's pull requests, and the refresh Gate runs this suite (check_page.mjs checks each row)
        V, C = (json.loads(read(os.path.join(ROOT, 'web', f))) for f in ('verdicts.json', 'corrections.json'))
        self.assertEqual((set(V), set(C)), ({'rows'}, {'entries'}))
        self.assertIsInstance(V['rows'], list); self.assertIsInstance(C['entries'], list)
        for r in V['rows']: self.assertRegex(r['id'], r'^s:[0-9a-f]{12}$'); self.assertIn(r['label'], LABEL_WORDS)
        for i, e in enumerate(C['entries']): self.assertEqual(e['id'], f'c:{i + 1}')


@unittest.skipUnless(shutil.which('git'), 'git not installed')
class OwnerFilesTest(unittest.TestCase):
    """SC-12 (C11, C40): the ci.yml check fails a commit that edits or removes a web/corrections.json entry against the base commit and
    passes one that appends; and it fails a refresh-bot commit that touches web/verdicts.json or web/corrections.json."""
    FX = json.loads(read(os.path.join(FIX, 'corrections_commits.json')))

    def repo(self, d):
        def git(*a, who=('Owner', 'owner@example.org')):
            env = dict(os.environ, GIT_AUTHOR_NAME=who[0], GIT_AUTHOR_EMAIL=who[1], GIT_COMMITTER_NAME=who[0], GIT_COMMITTER_EMAIL=who[1])
            return subprocess.run(['git', '-C', d, *a], capture_output=True, text=True, env=env, check=True).stdout.strip()
        git('init', '-q'); os.makedirs(os.path.join(d, 'web'))
        return git

    def commit(self, git, d, rel, body, who=('Owner', 'owner@example.org')):
        with open(os.path.join(d, rel), 'w') as f: json.dump(body, f, indent=1)
        git('add', rel, who=who); git('commit', '-q', '-m', rel, who=who)
        return git('rev-parse', 'HEAD')

    def run_check(self, d, base):
        return subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'check_owner_files.py'), '--repo', d, base], capture_output=True, text=True)

    def test_edit_and_remove_fail_append_passes(self):
        want = {'edit': (1, 'web/corrections.json entry c:2 edited since the base commit'),
                'remove': (1, 'web/corrections.json entry c:2 removed since the base commit'),
                'append': (0, 'web/corrections.json 2 entries at')}
        for name, (code, msg) in want.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as d:
                git = self.repo(d)
                base = self.commit(git, d, 'web/corrections.json', self.FX['base'])
                self.commit(git, d, 'web/corrections.json', self.FX[name])
                r = self.run_check(d, base)
                self.assertEqual(r.returncode, code, r.stdout + r.stderr)
                self.assertIn(msg, r.stderr if code else r.stdout)
                if code: self.assertEqual(len([l for l in r.stderr.splitlines() if l.startswith('- ')]), 1, r.stderr)
                else: self.assertIn('(1 appended)', r.stdout)

    def test_bot_commit_touching_an_owner_file_fails(self):
        bot = ('trend-observatory-bot', '41898282+github-actions[bot]@users.noreply.github.com')   # refresh.yml's identity
        with tempfile.TemporaryDirectory() as d:
            git = self.repo(d)
            base = self.commit(git, d, 'web/verdicts.json', {'rows': []})
            self.commit(git, d, 'web/pulse.json', {'stories': []}, who=bot)              # the bot's own data: fine
            r = self.run_check(d, base)
            self.assertEqual(r.returncode, 0, r.stderr)
            sha = self.commit(git, d, 'web/verdicts.json', {'rows': [{'id': 's:0a0a0a0a0a0a', 'label': 'UNVERIFIED'}]}, who=bot)
            r = self.run_check(d, base)
            self.assertEqual(r.returncode, 1)
            self.assertIn(f'commit {sha[:7]}', r.stderr)
            self.assertIn('by the refresh bot touches web/verdicts.json (owner-reviewed: enters only by a merged pull request)', r.stderr)
        with tempfile.TemporaryDirectory() as d:                                         # B3: web/removals.json is owner-reviewed too
            git = self.repo(d)
            base = self.commit(git, d, 'web/removals.json', {'entries': []})
            sha = self.commit(git, d, 'web/removals.json', {'entries': [{'sha256': '0' * 64, 'date': '2026-10-17'}]}, who=bot)
            r = self.run_check(d, base)
            self.assertEqual(r.returncode, 1)
            self.assertIn(f'commit {sha[:7]} by the refresh bot touches web/removals.json (owner-reviewed', r.stderr)

    def test_missing_base_falls_back_to_the_parent_and_ci_passes_the_base(self):
        with tempfile.TemporaryDirectory() as d:
            git = self.repo(d)
            self.commit(git, d, 'web/corrections.json', self.FX['base'])
            self.assertEqual(self.run_check(d, '').returncode, 0)                       # one commit: nothing to compare
            self.commit(git, d, 'web/corrections.json', self.FX['remove'])
            r = self.run_check(d, '0' * 40)
            self.assertEqual(r.returncode, 1); self.assertIn('entry c:2 removed', r.stderr)
            self.assertEqual(self.run_check(d, 'f' * 40).returncode, 1)                 # an unknown base fails closed
        ci = read(os.path.join(ROOT, '.github', 'workflows', 'ci.yml')).decode()
        self.assertIn('fetch-depth: 0', ci)
        self.assertIn('python scripts/check_owner_files.py "$BASE"', ci)
        self.assertIn('github.event.pull_request.base.sha || github.event.before', ci)
        # the refresh pushes with github.token (no ci.yml run), so it checks its own commit after `git commit` and before the push
        wf = read(os.path.join(ROOT, '.github', 'workflows', 'refresh.yml')).decode()
        c, k, push = wf.index('git commit -m "data: daily refresh'), wf.index('python scripts/check_owner_files.py HEAD~1'), wf.index('git push')
        self.assertLess(c, k); self.assertLess(k, push)
        dep = read(os.path.join(ROOT, '.github', 'workflows', 'deploy.yml')).decode()
        self.assertEqual(dep.count('python3 scripts/check_owner_files.py "$BASE"'), 2)          # both publishing jobs
        self.assertEqual(dep.count('fetch-depth: 0'), 2)
        for job in dep.split('\n  cloudflare:'):
            self.assertLess(job.index('check_owner_files.py'), job.index('check_page.mjs'))


# ------------------------------------------------------------------ removal requests and the deleted-post recheck (design row 7, C34; group B3)
RM = json.loads(read(os.path.join(FIX, 'removals', 'cases.json')))
FETCHERS = ('fetch_hn', 'fetch_lobsters', 'fetch_mastodon', 'fetch_reddit_archive', 'fetch_reddit', 'fetch_bluesky', 'fetch_newsletters', 'fetch_official')
sha = lambda u: hashlib.sha256(u.encode()).hexdigest()


class Lookups:
    """The four recheck endpoints, stubbed at pulse.GET (no network): answers per network and id, as in the fixture; every call is kept."""
    def __init__(self, answers=None):
        self.a, self.calls = answers or {}, []

    def __call__(self, url, timeout):
        self.calls.append(url)
        a, q = self.a, urllib.parse.urlparse(url)
        m = re.fullmatch(r'/v0/item/(\d+)\.json', q.path)
        if m:
            s = a.get('HN', {}).get(m[1])
            if s == 'timeout': raise TimeoutError('timed out')
            return 200, {'id': int(m[1]), **({s: True} if s else {})}, {}
        m = re.fullmatch(r'/api/v1/statuses/(\d+)', q.path)
        if m:
            s = a.get('Mastodon', {}).get(m[1], 200)
            if s == 'timeout': raise TimeoutError('timed out')
            return s, None, {'X-RateLimit-Remaining': '299'}
        if q.path.endswith('app.bsky.feed.getPosts'):
            return 200, {'posts': [{'uri': u} for u in urllib.parse.parse_qs(q.query)['uris'] if u not in a.get('Bluesky', [])]}, {}
        if q.path == '/api/posts/ids':
            ids = urllib.parse.parse_qs(q.query)['ids'][0].split(',')
            return 200, {'data': [{'id': i, 'author': 'x', 'selftext': a.get('Reddit', {}).get(i, '')} for i in ids]}, {}
        raise AssertionError(url)


def pulse_run(d, argv=(), posts=(), hype=None, removals=(), passes=(), answers=None, now=None):
    """pulse.py main() on a scratch web/ (the offline-rebuild data.json, the given hype.json and lists) and history DB under d, with
    every collector returning nothing and the recheck lookups stubbed -> (web dir, run log, the Lookups stub)."""
    web, hist = os.path.join(d, 'web'), os.path.join(d, 'history')
    os.makedirs(os.path.join(web, 'checks'), exist_ok=True)
    shutil.copy(os.path.join(FIX, 'offline_rebuild', 'data.json'), web)
    if hype is not None:
        with open(os.path.join(web, 'hype.json'), 'w') as f: json.dump(hype, f)
    if not os.path.exists(os.path.join(web, 'removals.json')):
        with open(os.path.join(web, 'removals.json'), 'w') as f: json.dump({'entries': [{'sha256': sha(u), 'date': '2026-10-17'} for u in removals]}, f)
    if passes:                                       # a pass the day before: fresh, so the post links if the recheck finds it
        with open(os.path.join(web, 'checks', 'mastodon-links.json'), 'w') as f:
            json.dump({'statuses': {i: {'result': 'pass', 'checked_at': '2026-10-16T08:00:00Z', 'passed_at': '2026-10-16T08:00:00Z', 'api_status': 200}
                                    for i in passes}}, f)
    keep = {k: getattr(pulse, k) for k in ('WEB', 'HIST', 'DB', 'CANDIDATES', 'NOW', 'GET') + FETCHERS}
    argv0, sources, stub, log = sys.argv, dict(pulse.SOURCES), Lookups(answers), io.StringIO()
    try:
        pulse.WEB, pulse.HIST, pulse.DB = web, hist, os.path.join(hist, 'signals.sqlite')
        pulse.CANDIDATES = os.path.join(hist, 'mastodon-candidates.json')
        pulse.NOW = datetime.fromisoformat((now or RM['now']).replace('Z', '+00:00'))
        pulse.GET = stub
        for n in FETCHERS: setattr(pulse, n, lambda: [])
        pulse.SOURCES.clear()
        if posts:
            con = pulse.db()
            pulse.store(con, [pulse.post(*r[:8], source=r[8], extra=r[9]) for r in posts])
            con.close()
        sys.argv = ['pulse.py', *argv]
        with contextlib.redirect_stdout(log): pulse.main()
    finally:
        for k, v in keep.items(): setattr(pulse, k, v)
        sys.argv = argv0
        pulse.SOURCES.clear(); pulse.SOURCES.update(sources)
    return web, log.getvalue(), stub


def outputs(web):
    return read(os.path.join(web, 'pulse.json')).decode() + read(os.path.join(web, 'briefing.json')).decode()


def db_keys(d):
    con = sqlite3.connect(os.path.join(d, 'history', 'signals.sqlite'))
    try: return {(n, p) for n, p in con.execute('SELECT net, pid FROM signals')}
    finally: con.close()


class RecheckTest(unittest.TestCase):
    """SC-13: a stored post its source reports gone, or that web/removals.json names, leaves pulse.json, briefing.json and the history
    DB; a post the recheck could not reach shows only as a count; --relink reuses the run's result and --offline makes no call."""
    def test_hn_mastodon_bluesky_reddit_gone_leave_every_output_and_the_db(self):
        F = RM['stored']
        with tempfile.TemporaryDirectory() as d:
            web, log, stub = pulse_run(d, posts=F['posts'], hype={'items': {'claude-code': {'name': 'Claude Code', 'posts': []}}},
                                       passes=F['passes'], answers=F['answers'])
            out, P = outputs(web), json.loads(read(os.path.join(web, 'pulse.json')))
            for w in F['words']['gone'] + F['words']['count']: self.assertNotIn(w, out)
            for w in F['words']['shown']: self.assertIn(w, out)
            for net, pid in F['gone'].items():
                self.assertNotIn((net, pid), db_keys(d))
                self.assertNotIn(pid, out)
            self.assertIn(('HN', '104'), db_keys(d))                                      # not reached: kept, and shown as a count
            self.assertNotIn('item?id=104', out)
            conv = {k: v for k, v in P['totals']['30d'].items() if k not in ('arXiv', 'GitHub')}   # the tracker's papers and repos aside
            self.assertEqual(conv, F['totals_30d'])                                       # 104 is counted; the four gone posts are not
            self.assertIn('https://mastodon.social/statuses/9002', out); self.assertNotIn('statuses/9001', out)
            B = json.loads(read(os.path.join(web, 'briefing.json')))                      # the deleted 101 (300 points) would lead the story
            self.assertEqual([r['headline'] for r in B['records']], ['Claude Code Yankee hooks still on HN'])
            self.assertIn({'net': 'HN', 'at': '2026-10-17T04:00:00Z'}, P['stories'][0]['path'])   # 104 in the story, as a count
            self.assertIn('recheck: 9 due, 4 reached and present, removed 4 found gone ', log)
            self.assertIn('1 unreached shown as counts (time cap 180s, ', log)
            self.assertIn("found gone {'Bluesky missing': 1, 'HN deleted': 1, 'Mastodon 404': 1, 'Reddit selftext [removed]': 1}", log)
            self.assertEqual(len([u for u in stub.calls if '/v0/item/' in u]), 3)       # one lookup per id, no retry
            first = {k: P[k] for k in ('totals', 'nodes', 'stories')}
            # --relink in the same refresh run: no call, the same posts shown and counted
            web, log, stub = pulse_run(d, ['--relink'], now='2026-10-17T08:35:00Z')
            P2 = json.loads(read(os.path.join(web, 'pulse.json')))
            self.assertEqual(stub.calls, [])
            self.assertEqual(P2['totals'], first['totals'])
            for w in F['words']['shown']: self.assertIn(w, outputs(web))
            for w in F['words']['gone'] + F['words']['count']: self.assertNotIn(w, outputs(web))
            self.assertIn("this run's recheck of 2026-10-17T08:25:00Z, time cap 180s", log)
            # --offline: no call, so every recheckable post is a count (Lobsters is not rechecked)
            web, log, stub = pulse_run(d, ['--offline'], now='2026-10-17T08:45:00Z')
            self.assertEqual(stub.calls, [])
            self.assertEqual(json.loads(read(os.path.join(web, 'pulse.json')))['totals'], first['totals'])
            for w in ('Yankee', 'Victor', 'Tango'): self.assertNotIn(w, outputs(web))
            self.assertIn('Quebec', outputs(web))
            self.assertIn('5 unreached shown as counts (offline: no call)', log)

    def test_removal_listed_post_reaches_no_output_and_leaves_the_db(self):
        F = RM['removal']
        with tempfile.TemporaryDirectory() as d:
            web, log, _ = pulse_run(d, posts=F['posts'], hype={'items': {}}, removals=F['removals'])
            self.assertNotIn('Papa', outputs(web)); self.assertNotIn('item?id=105', outputs(web))
            self.assertIn('Oscar', outputs(web)); self.assertIn('November', outputs(web))
            self.assertNotIn(('HN', '105'), db_keys(d))
            self.assertIn('removals.json 1 entries (1 stored posts removed)', log)
        # a Mastodon post is named by its stored address or by its handle-free link
        m = pulse.post('Mastodon', '9001', 'https://mastodon.social/@m_a/9001', 't', 'm_a', RM['now'])
        self.assertEqual(pulse.post_hashes(m), {sha('https://mastodon.social/@m_a/9001'), sha('https://mastodon.social/statuses/9001')})

    def test_reddit_gone_only_on_a_post_level_signal(self):
        # [deleted] or [removed] in the selftext or title, or a removed_by_category; an author deleted later leaves the post up
        data = [{'id': 'a', 'author': '[deleted]', 'selftext': 'still here', 'title': 't', 'removed_by_category': None},
                {'id': 'b', 'author': 'x', 'selftext': '[deleted]', 'title': 't'}, {'id': 'c', 'author': 'x', 'selftext': '', 'title': '[removed]'},
                {'id': 'd', 'author': 'x', 'selftext': '', 'title': 't', 'removed_by_category': 'moderator'}]
        keep = pulse.GET
        try:
            pulse.GET = lambda url, timeout: (200, {'data': data}, {})
            got = pulse.reddit_lookup(['a', 'b', 'c', 'd', 'e'], pulse.time.monotonic() + 30)
        finally:
            pulse.GET = keep
        self.assertEqual(got, {'a': 'alive', 'b': 'gone:selftext [deleted]', 'c': 'gone:title [removed]', 'd': 'gone:removed_by_category moderator'})

    def test_time_cap_and_failed_lookups_reach_nothing(self):
        posts = [pulse.post('HN', str(i), f'https://news.ycombinator.com/item?id={i}', 't', 'a', RM['now']) for i in (1, 2)]
        keep = pulse.GET
        try:
            pulse.GET = Lookups()
            self.assertEqual(pulse.recheck(posts, cap=0)[0], {})                         # the cap is spent before the first call
            self.assertEqual(pulse.GET.calls, [])
            pulse.GET = lambda url, timeout: (_ for _ in ()).throw(OSError('network down'))
            self.assertEqual(pulse.recheck(posts)[0], {})
        finally:
            pulse.GET = keep

    def test_dossier_posts_gone_or_listed_leave_outputs_and_hype_json_and_never_return(self):
        F = RM['dossier']
        with tempfile.TemporaryDirectory() as d:
            web, log, _ = pulse_run(d, posts=F['stored'], hype=F['hype'], removals=F['removals'], answers=F['answers'])
            for w in F['words']['gone'] + F['words']['count']: self.assertNotIn(w, outputs(web))
            for w in F['words']['shown']: self.assertIn(w, outputs(web))
            G = json.loads(read(os.path.join(web, 'checks', 'dossier-gone.json')))
            self.assertEqual(G['gone'], [{'sha256': h, 'found': '2026-10-17'} for h in sorted(sha(u) for u in F['found_gone'])])
            self.assertNotIn(b'\n', read(os.path.join(web, 'checks', 'dossier-gone.json')))
            self.assertNotIn(('HN', '305'), db_keys(d))                                   # the stored copy too; its dossier copy by hash
            # the refresh's scrub: the dropped posts leave web/hype.json, and only they; a second scrub changes nothing
            hype = os.path.join(web, 'hype.json')
            r = subprocess.run([sys.executable, os.path.join(ROOT, 'hype_build.py'), '--scrub', hype], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr); self.assertIn('3 posts removed', r.stdout)
            H = json.loads(read(hype))['items']['claude-code']
            self.assertEqual([p.get('url') for p in H['posts']], [p.get('url') for p in F['hype']['items']['claude-code']['posts']
                                                                   if p.get('url') not in F['dropped']])
            self.assertIsNone(H['first_seen_url'])                                        # the URL elsewhere in the item: null, no link
            once = read(hype)
            subprocess.run([sys.executable, os.path.join(ROOT, 'hype_build.py'), '--scrub', hype], capture_output=True, check=True)
            self.assertEqual(read(hype), once)
            # the next run reads the rewritten file: every lookup answers present, yet no dropped post comes back
            web, log, _ = pulse_run(d, answers={}, now='2026-10-17T09:25:00Z')
            for w in F['words']['gone']: self.assertNotIn(w, outputs(web))
            self.assertIn('Kilo', outputs(web))                                           # reached this time: shown again
            self.assertEqual(json.loads(read(os.path.join(web, 'checks', 'dossier-gone.json')))['gone'], G['gone'])

    def test_hype_scrub_with_no_listed_post_is_byte_identical(self):
        H = json.loads(read(os.path.join(ROOT, 'web', 'hype.json')))
        url = next(p['url'] for it in H['items'].values() for p in it['posts'] if p.get('url'))
        out = hype_build.scrub(copy.deepcopy(H), drop={sha(url)})
        self.assertFalse(any(p.get('url') == url for it in out['items'].values() for p in it['posts']))
        self.assertNotIn(url, json.dumps(out))
        self.assertEqual(json.dumps(hype_build.scrub(copy.deepcopy(H), drop=set())), json.dumps(hype_build.scrub(copy.deepcopy(H))))

    def test_refresh_scrubs_after_the_relink_and_stages_the_bot_lists_only(self):
        wf = read(os.path.join(ROOT, '.github', 'workflows', 'refresh.yml')).decode()
        add = next(l for l in wf.splitlines() if l.strip().startswith('git add ')).split()
        self.assertIn('web/hype.json', add); self.assertIn('web/checks/dossier-gone.json', add); self.assertNotIn('web/removals.json', add)
        i = lambda s: wf.index(s)
        self.assertLess(i('run: python pulse.py\n'), i('python pulse.py --relink'))
        self.assertLess(i('python pulse.py --relink'), i('run: python hype_build.py --scrub web/hype.json'))
        self.assertLess(i('run: python hype_build.py --scrub web/hype.json'), i('node scripts/embed/embed.mjs'))
        self.assertLess(i('run: python hype_build.py --scrub web/hype.json'), i('node scripts/check_page.mjs'))
        self.assertIn('web/removals.json', __import__('scripts.check_owner_files', fromlist=['OWNER_FILES']).OWNER_FILES)

    def test_committed_lists(self):
        R = json.loads(read(os.path.join(ROOT, 'web', 'removals.json')))              # owner-reviewed: grows by pull request, so shape only
        self.assertEqual(set(R), {'entries'})
        for e in R['entries']: self.assertEqual(set(e), {'sha256', 'date'}); self.assertRegex(e['sha256'], r'^[0-9a-f]{64}$'); self.assertRegex(e['date'], r'^\d{4}-\d{2}-\d{2}$')
        G = json.loads(read(os.path.join(ROOT, 'web', 'checks', 'dossier-gone.json')))
        for e in G['gone']: self.assertRegex(e['sha256'], r'^[0-9a-f]{64}$'); self.assertRegex(e['found'], r'^\d{4}-\d{2}-\d{2}$')


@unittest.skipUnless(shutil.which('node'), 'node not installed')
class RemovalFixtureTest(unittest.TestCase):
    """Decision 14 for removals: each case overlays a copy of the committed web/ with its files; check_page.mjs exits 1 with exactly that
    case's findings, or 0 with its summary. $HN0 is the hash of the first HN post in the committed hype.json (read at test time, so a
    later scrub of that post does not break the case)."""
    def test_each_case_fails_on_its_own_rule_or_passes(self):
        H = json.loads(read(os.path.join(ROOT, 'web', 'hype.json')))
        hn0 = sha(next(p['url'] for it in H['items'].values() for p in it['posts'] if p.get('pl') == 'HN' and p.get('url')))
        for name, c in RM['overlays'].items():
            with self.subTest(name), tempfile.TemporaryDirectory() as d:
                web = os.path.join(d, 'web')
                shutil.copytree(os.path.join(ROOT, 'web'), web)
                for rel, body in c['files'].items():
                    if body is None: os.remove(os.path.join(web, rel)); continue
                    with open(os.path.join(web, rel), 'w') as f: f.write((body if isinstance(body, str) else json.dumps(body)).replace('$HN0', hn0))
                r = subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)
                if 'ok' in c:
                    self.assertEqual(r.returncode, 0, r.stderr); self.assertIn(c['ok'], r.stdout); continue
                self.assertEqual(r.returncode, 1, r.stdout)
                got = [l[2:] for l in r.stderr.splitlines() if l.startswith('- ')]
                self.assertEqual(len(got), len(c['expect']), r.stderr)
                for m in c['expect']: self.assertTrue(any(g.startswith(m) for g in got), (m, got))

    def test_request_applies_to_pulse_and_briefing_from_the_next_daily_rebuild(self):
        # the owner's removal pull request (removals.json and the scrubbed hype.json) must pass CI against the day's pulse.json and
        # briefing.json, which drop the post at the next daily rebuild; an entry dated before their generated_at day must be applied
        P, hraw = json.loads(read(os.path.join(ROOT, 'web', 'pulse.json'))), read(os.path.join(ROOT, 'web', 'hype.json')).decode()
        url = next(x['url'] for x in P['stories'] if x.get('url') and x['url'] not in hraw)
        day = datetime.fromisoformat(P['generated_at'][:10])
        braw = read(os.path.join(ROOT, 'web', 'briefing.json')).decode()
        for when, code in ((day + timedelta(days=1), 0), (day - timedelta(days=2), 1)):    # today on yesterday's data; two days before
            with self.subTest(str(when.date())), tempfile.TemporaryDirectory() as d:
                web = os.path.join(d, 'web')
                shutil.copytree(os.path.join(ROOT, 'web'), web)
                with open(os.path.join(web, 'removals.json'), 'w') as f: json.dump({'entries': [{'sha256': sha(url), 'date': str(when.date())}]}, f)
                r = subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)
                self.assertEqual(r.returncode, code, r.stdout + r.stderr)
                got = [l[2:] for l in r.stderr.splitlines() if l.startswith('- ')]
                if code:
                    want = ['pulse.json: post named by removals.json is still published'] + (
                        ['briefing.json: post named by removals.json is still published'] if json.dumps(url)[1:-1] in braw else [])
                    self.assertEqual(len(got), len(want), r.stderr)
                    for m in want: self.assertTrue(any(g.startswith(m) for g in got), (m, got))
                else:
                    self.assertIn('removals: 1 requests, 0 dossier posts found gone, none published (', r.stdout)
                    self.assertIn('await the next daily rebuild)', r.stdout)

    def test_node_whose_posts_are_all_counts_passes_and_one_hiding_a_shown_post_fails(self):
        # a node seen only through posts the recheck did not reach has no samples and a spread of counts; a shown title there fails
        P = json.loads(read(os.path.join(ROOT, 'web', 'pulse.json')))
        n = P['nodes'][0]
        n['samples'], n['w']['30d']['nets'], n['spread'] = [], {'HN': 1}, [{'net': 'HN', 'at': '2026-10-17T04:00:00Z', 'day_only': False, 'source': 'live'}]
        for spread, code in ((n['spread'], 0), ([{**n['spread'][0], 'title': 'a shown HN title', 'lang': 'und', 'url': 'https://news.ycombinator.com/item?id=1'}], 1)):
            with tempfile.TemporaryDirectory() as d:
                web = os.path.join(d, 'web')
                shutil.copytree(os.path.join(ROOT, 'web'), web)
                with open(os.path.join(web, 'pulse.json'), 'w') as f: json.dump({**P, 'nodes': [{**n, 'spread': spread}] + P['nodes'][1:]}, f)
                r = subprocess.run(['node', os.path.join(ROOT, 'scripts', 'check_page.mjs'), web], capture_output=True, text=True)
                self.assertEqual(r.returncode, code, r.stderr)
                if code: self.assertEqual([l for l in r.stderr.splitlines() if l.startswith('- ')], [f"- pulse node {n['id']} has no evidence posts"])

    def test_shown_title_drops_links_to_counts_only_networks(self):
        t = pulse.unhandle('See https://x.com/someone/status/123 and x.com/abc/status/9 or https://www.reddit.com/r/a/comments/b/ via @bob, docs https://example.com/a')
        self.assertNotIn('x.com', t); self.assertNotIn('reddit.com', t); self.assertNotIn('@bob', t)
        self.assertIn('https://example.com/a', t)
        self.assertEqual(pulse.unhandle('npm @scope/pkg stays'), 'npm @scope/pkg stays')

if __name__ == '__main__':
    unittest.main()
