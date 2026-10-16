"""Pulse topic extraction and metrics on fixed posts (offline)."""
import json, os, sys, unittest
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pulse

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


if __name__ == '__main__':
    unittest.main()
