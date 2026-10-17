"""Pulse topic extraction and metrics on fixed posts (offline), and the public-data rules (design group A)."""
import copy, hashlib, json, os, shutil, subprocess, sys, tempfile, unittest
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
        self.assertEqual(pulse.headline_of(reddit, [reddit], 'GPT 6'), ('GPT 6', None, None))
        self.assertEqual(pulse.headline_of(reddit, [reddit], None), ('Reddit discussion, title not shown', None, None))

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
        # the counts of the committed file at 2bc0ace: a group that removes dossier posts (B3) or a research pass must update them
        raw = open(os.path.join(ROOT, 'web', 'hype.json'), 'rb').read()
        H = json.loads(raw)
        nets = {}
        for it in H['items'].values():
            for x in it['posts']: nets[x['pl']] = nets.get(x['pl'], 0) + 1
        self.assertEqual((len(H['items']), nets), (82, {'X': 125, 'HN': 268, 'YouTube': 4, 'LinkedIn': 6, 'Telegram': 1, 'GitHub': 1}))  # as at 2bc0ace
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

if __name__ == '__main__':
    unittest.main()
