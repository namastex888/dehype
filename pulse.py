#!/usr/bin/env python3
"""Pulse: sampled AI conversation across networks -> topic graph (web/pulse.json).

Run:   python3 pulse.py              fetch live feeds, merge with web/data.json + web/hype.json, write web/pulse.json
       python3 pulse.py --offline    rebuild from stored signals only (no network)
Env:   REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT   enable the Reddit adapter (official OAuth API)
       BSKY_HANDLE, BSKY_APP_PASSWORD                               enable the Bluesky adapter (app password)
State: history/signals.sqlite keeps 45 days of normalised posts; it rides in the same Actions cache as run.py's history.

Networks are samples, never totals: Hacker News stories above a points floor, the Lobsters AI tag, a fixed set of Mastodon
hashtags, plus (when connected) chosen subreddits and Bluesky searches, AI newsletter feeds (newsletters.json) and lab/vendor
announcement feeds (official_feeds.json, the 'Official' network). X is not collected; newsletter links to X are kept as citations. Every topic node carries the
posts that matched it, so a node is never more than the evidence behind it. Standard library only.
"""
import os, sys, re, json, math, time, bisect, sqlite3, base64, html, urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
WEB, HIST = os.path.join(BASE, 'web'), os.path.join(BASE, 'history')
DB = os.path.join(HIST, 'signals.sqlite')
NOW = datetime.now(timezone.utc)
RETAIN_DAYS = 45
WINDOWS = {'1d': 1, '7d': 7, '30d': 30}
CONVERSATION = {'HN', 'Lobsters', 'Mastodon', 'Reddit', 'Bluesky'}          # live chatter; used for "rising"
DIGEST = {'Newsletter'}                                                      # digests: the end point of a spread, not chatter
OFFICIAL = {'Official'}                                                      # lab/vendor announcements: the origin of a launch, not spread
UA = 'trend-observatory/1.0 (+https://github.com/namastex888/trending-research)'
SOURCES = {}

def note(name, status, detail=''):
    SOURCES[name] = {'status': status, 'detail': detail}

def iso(dt): return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def parse_dt(s):
    if not s: return None
    try:
        s = str(s).replace('Z', '+00:00')
        if len(s) == 10: s += 'T00:00:00+00:00'
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None

def http(url, headers=None, data=None, timeout=30):
    h = {'User-Agent': UA, 'Accept': 'application/json'}
    h.update(headers or {})
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 2: time.sleep(4 * (attempt + 1)); continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt < 2: time.sleep(3 * (attempt + 1)); continue
            raise

def strip_html(s):
    s = re.sub(r'<(style|script)\b.*?</\1>', ' ', s or '', flags=re.S | re.I)
    s = re.sub(r'<a\b(?![^>]*hashtag)[^>]*>.*?</a>', ' ', s, flags=re.S)        # links and @mentions, not #hashtags
    s = html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'</p>|<br\s*/?>', ' ', s)))
    return re.sub(r'\s+', ' ', re.sub(r'https?://\S+', ' ', s)).replace('\u200b', '').strip()

def post(net, pid, url, title, author, created, score=None, comments=None, source='live', extra=None):
    return {'net': net, 'pid': str(pid), 'url': url, 'title': re.sub(r'\s+', ' ', title or '').strip()[:400],
            'author': (author or '').strip()[:80], 'created': created, 'score': score, 'comments': comments, 'source': source,
            'extra': extra or {}}

def link_extra(u):
    """The external page a post points at (kept for link_push); own-site links are not targets."""
    return {'link': u} if u and re.match(r'https?://', u) else None

# ------------------------------------------------------------------ adapters (each returns a list of posts or raises)
def fetch_hn(days=30, min_points=20, step=3):
    """Stories above a points floor, fetched in 3-day slices (Algolia returns at most 1,000 hits per query)."""
    out, end = {}, int(NOW.timestamp())
    for k in range(0, days, step):
        hi, lo = end - k * 86400, end - min(days, k + step) * 86400
        q = urllib.parse.urlencode({'tags': 'story', 'numericFilters': f'created_at_i>{lo},created_at_i<={hi},points>{min_points}',
                                    'hitsPerPage': 1000})
        for h in http('https://hn.algolia.com/api/v1/search_by_date?' + q).get('hits', []):
            out[h['objectID']] = post('HN', h['objectID'], f"https://news.ycombinator.com/item?id={h['objectID']}", h.get('title'),
                                      h.get('author'), h.get('created_at'), h.get('points'), h.get('num_comments'), extra=link_extra(h.get('url')))
    return list(out.values())

def fetch_lobsters(pages=4):
    out = []
    for p in range(1, pages + 1):
        d = http('https://lobste.rs/t/ai.json' if p == 1 else f'https://lobste.rs/t/ai/page/{p}.json')
        for s in d:
            out.append(post('Lobsters', s['short_id'], s.get('comments_url') or s.get('url'), s.get('title'),
                            (s.get('submitter_user') or {}).get('username') if isinstance(s.get('submitter_user'), dict) else s.get('submitter_user'),
                            s.get('created_at'), s.get('score'), s.get('comment_count'), extra=link_extra(s.get('url'))))
    return out

MASTODON_TAGS = ['ai', 'llm', 'genai', 'claude', 'openai', 'anthropic', 'chatgpt', 'machinelearning', 'localllm']
def fetch_mastodon(instance='mastodon.social', pages=4):
    out, cutoff = [], NOW - timedelta(days=30)
    for tag in MASTODON_TAGS:
        max_id = None
        for _ in range(pages):
            q = {'limit': 40}
            if max_id: q['max_id'] = max_id
            d = http(f'https://{instance}/api/v1/timelines/tag/{tag}?' + urllib.parse.urlencode(q))
            if not d: break
            for s in d:
                if s.get('reblog'): continue
                text = strip_html(s.get('content'))
                if not text: continue
                card = (s.get('card') or {}).get('url') or next(iter(re.findall(r'<a\b(?![^>]*(?:hashtag|mention))[^>]*href="([^"]+)"', s.get('content') or '')), None)
                out.append(post('Mastodon', s['id'], s.get('url') or s.get('uri'), text[:280],
                                (s.get('account') or {}).get('acct'), s.get('created_at'),
                                (s.get('favourites_count') or 0) + (s.get('reblogs_count') or 0), s.get('replies_count'), extra=link_extra(card)))
            max_id = d[-1]['id']
            if parse_dt(d[-1].get('created_at')) and parse_dt(d[-1]['created_at']) < cutoff: break
    return out

REDDIT_SUBS = ['ClaudeAI', 'OpenAI', 'LocalLLaMA', 'singularity', 'MachineLearning', 'artificial', 'ChatGPT', 'AI_Agents',
               'Bard', 'StableDiffusion']
PARTIAL = {}
def fetch_reddit_archive(days=7, pages=10, pause=1.0):
    """Recent posts from chosen subreddits via the arctic-shift public Reddit archive (no key, any IP).
    Approach adapted from mvanhorn/last30days-skill (MIT, lib/reddit_arctic.py). Third-party archive: no uptime guarantee,
    scores are snapshots taken at ingestion, so Pulse weighs distinct authors, not votes."""
    out, after, failed = {}, (NOW - timedelta(days=days)).strftime('%Y-%m-%d'), []
    def get(q):
        for wait in (0, 6, 15, 30):                                   # the archive answers 422 "slow down" under load
            time.sleep(wait)
            try: return http('https://arctic-shift.photon-reddit.com/api/posts/search?' + urllib.parse.urlencode(q)).get('data') or []
            except urllib.error.HTTPError as e:
                if e.code != 422: raise
        raise TimeoutError('archive kept asking to slow down')
    for sub in REDDIT_SUBS:
        before = None
        for _ in range(pages):
            q = {'subreddit': sub, 'after': after, 'limit': 100, 'sort': 'desc'}
            if before: q['before'] = before
            try: d = get(q)
            except (TimeoutError, urllib.error.URLError) as e:
                failed.append(sub); break
            for p in d:
                out[p['id']] = post('Reddit', p['id'], 'https://www.reddit.com' + (p.get('permalink') or ''), p.get('title'),
                                    p.get('author'), iso(datetime.fromtimestamp(p.get('created_utc', 0), timezone.utc)),
                                    p.get('score'), p.get('num_comments'), extra=None if p.get('is_self') else link_extra(p.get('url')))
            time.sleep(pause)
            if len(d) < 100: break
            before = int(min(p.get('created_utc', 0) for p in d))
    if failed: PARTIAL['Reddit (arctic-shift archive)'] = 'no data this run for r/' + ', r/'.join(failed)
    if failed and not out: raise TimeoutError(PARTIAL['Reddit (arctic-shift archive)'])
    return list(out.values())

def fetch_reddit():
    cid, sec = os.environ.get('REDDIT_CLIENT_ID'), os.environ.get('REDDIT_CLIENT_SECRET')
    if not (cid and sec): raise PermissionError('no credentials (set REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET)')
    ua = os.environ.get('REDDIT_USER_AGENT') or UA
    auth = base64.b64encode(f'{cid}:{sec}'.encode()).decode()
    tok = http('https://www.reddit.com/api/v1/access_token', {'Authorization': 'Basic ' + auth, 'User-Agent': ua,
               'Content-Type': 'application/x-www-form-urlencoded'}, data=b'grant_type=client_credentials')['access_token']
    out, hdr = [], {'Authorization': 'bearer ' + tok, 'User-Agent': ua}
    for sort, t in (('top', 'week'), ('top', 'month'), ('new', None)):
        q = {'limit': 100, 'raw_json': 1}
        if t: q['t'] = t
        d = http(f"https://oauth.reddit.com/r/{'+'.join(REDDIT_SUBS)}/{sort}?" + urllib.parse.urlencode(q), hdr)
        for c in d.get('data', {}).get('children', []):
            p = c['data']
            out.append(post('Reddit', p['id'], 'https://www.reddit.com' + p.get('permalink', ''), p.get('title'),
                            p.get('author'), iso(datetime.fromtimestamp(p.get('created_utc', 0), timezone.utc)),
                            p.get('score'), p.get('num_comments'), extra=None if p.get('is_self') else link_extra(p.get('url'))))
    return out

def _rss_date(s):
    if not s: return None
    try: return iso(parsedate_to_datetime(s))
    except (TypeError, ValueError, IndexError):
        d = parse_dt(s)
        return iso(d) if d else None

CITE_SKIP = {'t.co', 'substack.com', 'substackcdn.com', 'beehiiv.com', 'beehiiv.net', 'typeform.com', 'list-manage.com', 'mailchimp.com',
             'x.com', 'twitter.com', 'eepurl.com', 'buttondown.email', 'ghost.io', 'feedburner.com', 'gravatar.com', 'w3.org'}
X_SKIP = {'i', 'search', 'intent', 'hashtag', 'home', 'share', 'explore', 'settings', 'messages', 'notifications', 'compose', 'login',
          'signup', 'tos', 'privacy', 'about', 'download'}

def host(u):
    h = urllib.parse.urlsplit(u).hostname or ''
    return h[4:] if h.startswith('www.') else h

def citations(body, own=()):
    """Domains and X/Twitter handles linked from a newsletter item's HTML (read before the HTML is stripped).
    Newsletter infrastructure (Substack, beehiiv, trackers) and the newsletter's own site are not citations."""
    doms, handles = set(), set()
    for u in re.findall(r'href=["\'](https?://[^"\'\s>]+)', body or '', flags=re.I):
        h = host(u)
        m = re.match(r'https?://(?:www\.|mobile\.)?(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})(?:[/?#]|$)', u, re.I)
        if m and m.group(1).lower() not in X_SKIP: handles.add(m.group(1).lower())
        if not h or any(h == d or h.endswith('.' + d) for d in CITE_SKIP): continue
        if is_own(h, own): continue
        doms.add(h)
    return sorted(doms), sorted(handles)

def parse_feed(raw, name, net, cutoff, cite=False, own=()):
    """RSS 2.0 or Atom bytes -> posts on `net` authored by the feed `name`. Every item is date-filtered (no fixed head count:
    some vendor feeds carry a thousand items). Title + stripped body (capped) are kept for matching; the page shows the title."""
    root = ET.fromstring(raw)
    ns = {'a': 'http://www.w3.org/2005/Atom', 'c': 'http://purl.org/rss/1.0/modules/content/'}
    out = []
    for it in root.findall('.//item') or root.findall('.//a:entry', ns):
        title = (it.findtext('title') or it.findtext('a:title', namespaces=ns) or '').strip()
        link = (it.findtext('link') or '').strip()
        if not link:
            le = it.find("a:link[@rel='alternate']", ns)
            if le is None: le = it.find('a:link', ns)
            link = le.get('href') if le is not None else ''
        date = _rss_date(it.findtext('pubDate') or it.findtext('a:published', namespaces=ns) or it.findtext('a:updated', namespaces=ns))
        if not date or parse_dt(date) < cutoff: continue
        body = it.findtext('c:encoded', namespaces=ns) or it.findtext('description') or it.findtext('a:content', namespaces=ns) or it.findtext('a:summary', namespaces=ns) or ''
        extra = None
        if cite:
            d, x = citations(body, tuple(own) + (host(link),))
            extra = {'domains': d, 'x': x}
        text = (title + ' \u241f ' + strip_html(body))[:1500]          # U+241F separator: body kept for matching only
        out.append(post(net, link or f"{name}:{title}", link, text, name, date, extra=extra, source='official' if net in OFFICIAL else 'live'))
    return out

def own_hosts(f):
    """A feed's own sites (newsletters.json 'site': a domain or a list; subdomains count as the same site) plus the feed host."""
    sites = f.get('site') or []
    return [host(x if '://' in x else 'https://' + x) for x in ([sites] if isinstance(sites, str) else sites)] + [host(f['url'])]

_OWN = {}
def newsletter_sites(name):
    """Own sites of a newsletter by name, so citations stored before a 'site' was added are filtered too."""
    if not _OWN:
        try: _OWN.update({f['name']: tuple(own_hosts(f)) for f in json.load(open(os.path.join(BASE, 'newsletters.json')))['feeds']})
        except (OSError, ValueError, KeyError): _OWN[''] = ()
    return _OWN.get(name, ())

def is_own(h, own):
    return any(o and (h == o or h.endswith('.' + o) or o.endswith('.' + h)) for o in own)

def fetch_feedlist(cfg_file, net, cite, days=30):
    path = os.path.join(BASE, cfg_file)
    if not os.path.exists(path): raise PermissionError(f'not configured (add feeds to {cfg_file})')
    out, failed, cutoff = [], [], NOW - timedelta(days=days)
    for f in json.load(open(path))['feeds']:
        try:
            req = urllib.request.Request(f['url'], headers={'User-Agent': UA, 'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml'})
            with urllib.request.urlopen(req, timeout=30) as r: raw = r.read()
            out += parse_feed(raw, f['name'], net, cutoff, cite, own_hosts(f))
        except Exception:
            failed.append(f['name'])
    return out, failed

def fetch_newsletters(days=30):
    """Public RSS/Atom feeds of AI newsletters listed in newsletters.json. An issue is one post on the 'Newsletter' network;
    its text (title + summary, HTML stripped, capped) is matched against topics, so the spread trace shows when a topic
    reached the digests. Links in the issue are recorded as citations (domains, X handles). Only the item title, date and
    public link are published."""
    out, failed = fetch_feedlist('newsletters.json', 'Newsletter', True, days)
    if failed: PARTIAL['Newsletters (RSS)'] = 'unreachable: ' + ', '.join(failed)
    if failed and not out: raise ConnectionError(PARTIAL['Newsletters (RSS)'])
    return out

def fetch_official(days=30):
    """Lab and vendor announcement feeds listed in official_feeds.json (network 'Official'): where launches originate.
    Not conversation (no rising), not a digest; it can be the first point of a spread."""
    out, failed = fetch_feedlist('official_feeds.json', 'Official', False, days)
    if failed: PARTIAL['Official feeds (RSS)'] = 'unreachable: ' + ', '.join(failed)
    if failed and not out: raise ConnectionError(PARTIAL['Official feeds (RSS)'])
    return out

BSKY_QUERIES = ['Claude', 'Anthropic', 'OpenAI', 'ChatGPT', 'Gemini', 'LLM', 'AI agent', 'open-weight model']
def fetch_bluesky():
    handle, pw = os.environ.get('BSKY_HANDLE'), os.environ.get('BSKY_APP_PASSWORD')
    if not (handle and pw): raise PermissionError('no credentials (set BSKY_HANDLE / BSKY_APP_PASSWORD)')
    s = http('https://bsky.social/xrpc/com.atproto.server.createSession', {'Content-Type': 'application/json'},
             data=json.dumps({'identifier': handle, 'password': pw}).encode())
    hdr, out = {'Authorization': 'Bearer ' + s['accessJwt']}, []
    for q in BSKY_QUERIES:
        d = http('https://bsky.social/xrpc/app.bsky.feed.searchPosts?' + urllib.parse.urlencode(
            {'q': q, 'sort': 'top', 'limit': 100, 'since': iso(NOW - timedelta(days=30))}), hdr)
        for p in d.get('posts', []):
            a = p.get('author', {}).get('handle', '')
            rkey = p.get('uri', '').rsplit('/', 1)[-1]
            ext = ((p.get('embed') or {}).get('external') or {}).get('uri')
            out.append(post('Bluesky', p.get('uri'), f'https://bsky.app/profile/{a}/post/{rkey}',
                            (p.get('record') or {}).get('text', '')[:280], a, (p.get('record') or {}).get('createdAt'),
                            (p.get('likeCount') or 0) + (p.get('repostCount') or 0), p.get('replyCount'), extra=link_extra(ext)))
    return out

# ------------------------------------------------------------------ internal sources (already collected by run.py / research)
def internal_posts():
    out = []
    try:
        D = json.load(open(os.path.join(WEB, 'data.json')))
        for pid, p in D['papers']['items'].items():
            out.append(post('arXiv', pid, f'https://arxiv.org/abs/{pid}', p.get('title'), p.get('lab') or (p.get('authors') or [''])[0],
                            p.get('published'), p.get('upvotes'), p.get('mentions'), source='tracker'))
        ranked = {r['id'] for v in D['repos'].get('7d', {}).values() for r in v.get('rows', [])}
        for rid in ranked:
            r = D['repos']['items'].get(rid) or {}
            out.append(post('GitHub', rid, r.get('url'), f"{rid.split('/')[-1]}: {r.get('desc') or ''}", rid.split('/')[0],
                            D.get('generated_at'), r.get('stars'), r.get('contributors'), source='tracker'))
        note('Tracker (papers + repos)', 'ok', f"{len(D['papers']['items'])} papers, {len(ranked)} repos ranked in 7d")
    except (OSError, KeyError, ValueError) as e:
        note('Tracker (papers + repos)', 'failed', str(e)[:120])
    try:
        H = json.load(open(os.path.join(WEB, 'hype.json')))
        n = 0
        for it in H['items'].values():
            for p in it.get('posts', []):
                if not p.get('url'): continue
                out.append(post(p.get('pl') or 'other', p['url'], p['url'], p.get('t'), p.get('au'), p.get('d'),
                                p.get('likes') if p.get('likes') is not None else p.get('score'), p.get('cm') or p.get('rp'), source='dossier'))
                n += 1
        note('HYPE research dossier', 'ok', f"{n} sampled posts, content cutoff {H.get('content_cutoff')} (static, refreshed by hand)")
    except (OSError, KeyError, ValueError) as e:
        note('HYPE research dossier', 'failed', str(e)[:120])
    return out

def official_meta():
    try: return [{'name': f['name'], 'site': f.get('site'), 'mirror': bool(f.get('mirror'))} for f in json.load(open(os.path.join(BASE, 'official_feeds.json')))['feeds']]
    except (OSError, ValueError, KeyError): return []

def tracker_repos():
    """Repo rows ranked by run.py in the Pulse windows (any paradigm view): text for topic matching, paradigm tag,
    stars gained per window (common reach) and the anti-noise flags per window (coordination signals)."""
    try: D = json.load(open(os.path.join(WEB, 'data.json')))
    except (OSError, ValueError): return []
    out = {}
    for w in WINDOWS:
        for view in (D.get('repos', {}).get(w) or {}).values():
            for row in view.get('rows', []):
                it = D['repos']['items'].get(row['id']) or {}
                r = out.setdefault(row['id'], {'id': row['id'], 'text': f"{row['id'].split('/')[-1]}: {it.get('desc') or ''}", 'tag': it.get('tag'),
                                               'gained': {}, 'flags': {}})
                r['gained'][w] = row.get('gained'); r['flags'][w] = row.get('flags') or []; r['created'] = it.get('created')
    return list(out.values())

# ------------------------------------------------------------------ storage
def db():
    os.makedirs(HIST, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute('''CREATE TABLE IF NOT EXISTS signals(net TEXT, pid TEXT, url TEXT, title TEXT, author TEXT, created TEXT,
                   score INT, comments INT, source TEXT, fetched TEXT, extra TEXT, PRIMARY KEY(net, pid))''')
    if 'extra' not in [r[1] for r in con.execute('PRAGMA table_info(signals)')]:
        con.execute('ALTER TABLE signals ADD COLUMN extra TEXT')       # stores from before target links / citations were kept
    return con

def store(con, posts):
    for p in posts:
        con.execute('INSERT OR REPLACE INTO signals(net,pid,url,title,author,created,score,comments,source,fetched,extra) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                    (p['net'], p['pid'], p['url'], p['title'], p['author'], p['created'], p['score'], p['comments'], p['source'], iso(NOW),
                     json.dumps(p.get('extra')) if p.get('extra') else None))
    con.execute('DELETE FROM signals WHERE created IS NULL OR created < ?', (iso(NOW - timedelta(days=RETAIN_DAYS)),))
    con.commit()

def load_stored(con):
    cols = ['net', 'pid', 'url', 'title', 'author', 'created', 'score', 'comments', 'source', 'extra']
    out = [dict(zip(cols, r)) for r in con.execute(f'SELECT {",".join(cols)} FROM signals')]
    for p in out: p['extra'] = json.loads(p['extra']) if p['extra'] else {}
    return out

# ------------------------------------------------------------------ topic extraction
VARIANTS = {'pro', 'flash', 'mini', 'nano', 'ultra', 'max', 'turbo', 'lite', 'next', 'thinking', 'instant', 'opus', 'sonnet', 'haiku'}
STOP_PHRASE = set('The A An How Why What When Where Who Show Ask Tell Launch Is Are Do Does Can I We My Our Your This That These Those New Using Use '
                  'Introducing Announcing Building Build Making Make Inside Hacker News HN Today Yesterday Week Day Year In On Of For And Or To With From '
                  'By At Via About Not No Yes Its It Here There Part One Two Three First Last Next Best Top All Every Just Now Why'.split())

COMMON = set('''a about after again against ai all also an and any app apps are as at back be because been before being best better big
billion both build but by call can case change chat could data day days deal did do does down each early easy eight end even ever every
fast few first five for four free from full get gets give go going good great group half has have he her here high his home how i if
in into is it its just know large last launch launches law life like line little live local long look made make makes man many may
me million model models more most much must my need never new news next nine no not now number of off old on once one only open or
other our out over own part people per phone plan post power pro real report said same say says see seven she should show six small so
some spend start state states still study such take tech tells ten than that the their them then there these they thing think this
those three through time to today too top two under up us use used user users using very via want was way we week well were what when
where which while who why will with without work world would year years yet you your employees company companies version music image
video audio voice code model release app api update review demo test tests paper study chat beta'''.split())

EMERGING_STOP = set()
PROJECT_TOPIC = {}                                   # hype item id -> topic id that counts its live mentions

def compile_lexicon(lex, hype_items):
    topics = []
    PROJECT_TOPIC.clear()
    def rx(aliases, case):
        alts = sorted({a for a in aliases if a}, key=len, reverse=True)
        if not alts: return None
        return re.compile(r'(?<![\w-])(?:' + '|'.join(re.escape(a).replace(r'\ ', r'[\s-]') for a in alts) + r')(?![\w-])',
                          0 if case else re.I)
    for t in lex['topics']:
        topics.append({'id': t['id'], 'label': t['label'], 'kind': t['kind'], 'parent': t.get('parent'), 'tracker_tag': t.get('tracker_tag'), 'hn_ai': t.get('hn_ai', False),
                       'rx': re.compile(t['pattern'], re.I) if t.get('pattern') else rx(t.get('aliases', []), t.get('case', False))})
    ambiguous = set(lex.get('ambiguous_hype_names', []))
    for hid, it in hype_items.items():
        name = it.get('name') or hid
        same = [t for t in topics if t['label'].lower() == name.lower()]
        if same:
            PROJECT_TOPIC[hid] = same[0]['id']; continue
        PROJECT_TOPIC[hid] = 'p:' + hid
        aliases = [a for a in it.get('aliases', []) if '/' not in a and '@' not in a]
        cat = (it.get('category') or '').lower()
        kind = 'model' if 'model' in cat and 'product' not in cat and 'platform' not in cat else 'product'
        case = name in ambiguous
        topics.append({'id': 'p:' + hid, 'label': name, 'kind': kind, 'parent': None,
                       'rx': rx(([] if case else [name]) + aliases, False) if not case else None,
                       'rx_case': rx([name], True) if case else None})
    fams = {}
    for t in lex['topics']:
        if t.get('versioned'):
            fams[(t.get('family') or t['label']).lower()] = (t.get('family') or t['label'], t['id'])
    vrx = re.compile(r'(?<![\w-])(' + '|'.join(re.escape(f) for f, _ in fams.values()) +
                     r')[\s-]?(v?\d+(?:\.\d+)*)(?:[\s-](Pro|Flash|Mini|Nano|Ultra|Max|Turbo|Lite|Next|Thinking|Instant|Opus|Sonnet|Haiku|[A-Za-z]{3,12}))?(?![\w.])', re.I)
    kw = re.compile(r'(?<![\w-])(?:' + '|'.join(re.escape(k) for k in lex.get('ai_keywords', [])) + r')(?![\w-])', re.I)
    return topics, fams, vrx, kw

def match_topics(text, topics, fams, vrx):
    found = {}
    for t in topics:
        r = t.get('rx') or t.get('rx_case')
        if r and r.search(text): found[t['id']] = t
    for m in vrx.finditer(text):
        fam, ver, sub = m.group(1), m.group(2).lstrip('vV'), m.group(3)
        canon, parent = fams[fam.lower()]
        if not re.match(r'^\d{1,2}(\.\d{1,2})?$', ver): continue          # 2026, 1000 etc. are not model versions
        # a trailing word is a tier (Pro, Flash) or a capitalised codename (Argon, Astra); anything else is ordinary text
        nxt = text[m.end():m.end() + 20]
        if sub and not (sub.lower() in VARIANTS or (sub[0].isupper() and sub.lower() not in COMMON and sub not in STOP_PHRASE
                                                    and not (re.match(r'[\s-]+([A-Z][a-z]+)', nxt) and re.match(r'[\s-]+([A-Z][a-z]+)', nxt).group(1).lower() not in COMMON
                                                             and re.match(r'[\s-]+([A-Z][a-z]+)', nxt).group(1) not in STOP_PHRASE))): sub = None   # 'Opus 5.5 Music Video' is not a codename
        label = f'{canon} {ver}' + (f' {sub.title()}' if sub else '')
        tid = 'v:' + re.sub(r'[^a-z0-9.]+', '-', label.lower())
        found[tid] = {'id': tid, 'label': label, 'kind': 'version', 'parent': parent}
    return found

def emerging_phrases(posts, known_labels, covered=None, min_authors=3, limit=30):
    """Capitalised multi-word phrases and CamelCase names said by >= min_authors distinct authors in live conversation.
    Hashtags are ignored; phrases made only of common words, or already covered by a known topic/version, are dropped."""
    seen = {}
    pat = re.compile(r'\b([A-Z][A-Za-z0-9]+(?:[ -](?:[A-Z][A-Za-z0-9.]+|\d+(?:\.\d+)?)){1,2}|[A-Z][a-z]+[A-Z][A-Za-z0-9]+)\b')
    for p in posts:
        if p['net'] not in CONVERSATION: continue
        for m in pat.finditer(re.sub(r'#\w+', ' ', p['title'] or '')):
            ph = m.group(1).strip()
            words = re.split(r'[ -]', ph)
            if words[0] in STOP_PHRASE or words[-1] in STOP_PHRASE: continue
            if ph.lower() in known_labels or len(ph) < 5: continue
            if not [w for w in words if w.lower() not in COMMON and not re.fullmatch(r'[\d.]+', w) and w.lower() not in known_labels]: continue
            if covered and covered(ph): continue
            if ph.lower() in EMERGING_STOP: continue
            if re.match(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*[ -]\d', ph): continue   # dates
            seen.setdefault(ph, set()).add((p['net'], p['author']))
    for ph in sorted(seen, key=lambda x: -len(x)):       # "Muse Spark Open" folds into "Muse Spark" when both were said
        words = re.split(r'[ -]', ph)
        pre = next((q for k in range(len(words) - 1, 1, -1) for q in seen if q != ph and re.split(r'[ -]', q) == words[:k]), None)
        if pre: seen[pre] |= seen.pop(ph)
    keep = [(ph, a) for ph, a in seen.items() if len(a) >= min_authors]
    keep.sort(key=lambda x: -len(x[1]))
    return [ph for ph, _ in keep[:limit]]

# ------------------------------------------------------------------ graph
def shown(p):
    """Display text: newsletters keep their body only for matching; the page shows the issue title."""
    t = p['title'] or ''
    return t.split('\u241f', 1)[0].strip() if p['net'] in DIGEST | OFFICIAL else t

def build(posts, lex, hype_items, repos=None):
    """posts -> (nodes, edges, totals, projects, extras). repos: tracker repo rows [{id, text, tag, gained: {w}, flags: {w}}]."""
    topics, fams, vrx, kw = compile_lexicon(lex, hype_items)
    by_id = {t['id']: t for t in topics}
    rel, author_total = [], {}
    for p in posts:
        dt = parse_dt(p['created'])
        if not dt or dt > NOW + timedelta(hours=1) or dt < NOW - timedelta(days=30): continue
        if p['net'] in OFFICIAL and p['source'] == 'live': p = {**p, 'source': 'official'}     # rows stored before the official source existed
        if crowd(p): author_total[(p['net'], p['author'])] = author_total.get((p['net'], p['author']), 0) + 1   # before the HN AI filter
        text = p['title'] or ''
        found = match_topics(text, topics, fams, vrx)
        # HN is general-interest: keep a story only if it names an AI model/product/version or uses an AI keyword
        if p['net'] == 'HN' and p['source'] == 'live' and not kw.search(text) and not any(t['kind'] in ('model', 'version', 'product') or t.get('hn_ai') for t in found.values()): continue
        rel.append((p, dt, found))
    labels = {t['label'].lower() for t in topics} | {w.lower() for t in topics if t['kind'] != 'person' for w in t['label'].split()}
    vwords = [set(t['label'].lower().split()) for _, _, f in rel for t in f.values() if t['kind'] == 'version']
    def covered(ph):
        r = [t.get('rx') or t.get('rx_case') for t in topics]
        words = set(ph.lower().replace('-', ' ').split())
        return bool(vrx.search(ph)) or any(x and x.fullmatch(ph) for x in r) or any(words <= v for v in vwords)
    for ph in emerging_phrases([p for p, _, _ in rel], labels, covered):
        prx = re.compile(r'(?<![\w-])' + re.escape(ph).replace(r'\ ', r'[\s-]') + r'(?![\w-])')
        tid = 'e:' + re.sub(r'[^a-z0-9.]+', '-', ph.lower())
        for p, dt, found in rel:
            if prx.search(p['title'] or ''): found[tid] = {'id': tid, 'label': ph, 'kind': 'emerging', 'parent': None}

    # common reach: each item's percentile within its own type and window (posts per network, papers, repos), never raw sums
    item_pct = {w: {} for w in WINDOWS}
    for w, days in WINDOWS.items():
        groups = {}
        for p, dt, _ in rel:
            if (NOW - dt).total_seconds() / 86400 > days or p['score'] is None: continue
            if p['source'] == 'live' and p['net'] in REACH_POST_NETS: groups.setdefault(('posts', p['net']), []).append(p)
            elif p['source'] == 'tracker' and p['net'] == 'arXiv': groups.setdefault(('papers', 'arXiv'), []).append(p)
        for (typ, _), ps in groups.items():
            for p, v in zip(ps, pct_rank([max(0, x['score']) for x in ps])): item_pct[w][(p['net'], p['pid'])] = (typ, v)
    repo_topics, repo_pct = {}, {w: {} for w in WINDOWS}
    tag_topics = {}
    for t in topics:
        if t.get('tracker_tag'): tag_topics.setdefault(t['tracker_tag'], []).append(t['id'])
    for r in repos or []:
        repo_topics[r['id']] = set(match_topics(r['text'], topics, fams, vrx)) | set(tag_topics.get(r.get('tag'), ()))
    for w in WINDOWS:
        rs = [r for r in repos or [] if (r.get('gained') or {}).get(w) is not None]
        for r, v in zip(rs, pct_rank([max(0, r['gained'][w]) for r in rs])): repo_pct[w][r['id']] = v
    r30 = [r for r in repos or [] if '30d' in (r.get('flags') or {})]
    base = round(sum(1 for r in r30 if 'stars>activity' in r['flags']['30d']) / len(r30), 3) if r30 else None
    dupes = near_dupes([p for p, dt, _ in rel if crowd(p) and (NOW - dt).total_seconds() / 86400 <= 30])

    nodes, edges = {}, {}
    proj = {hid: {w: {'authors': set(), 'posts': 0, 'nets': set()} for w in PROJECT_WINDOWS} for hid in PROJECT_TOPIC}
    by_topic = {}
    for hid, tid in PROJECT_TOPIC.items(): by_topic.setdefault(tid, []).append(hid)
    def node(t):
        n = nodes.get(t['id'])
        if not n:
            n = nodes[t['id']] = {'id': t['id'], 'label': t['label'], 'kind': t['kind'], 'parent': t.get('parent'),
                                  'w': {w: {'posts': 0, 'authors': set(), 'nets': {}, 'eng': 0.0, 'eng_xr': 0.0, 'conv': 0, 'nl': set(),
                                          'obs': {}, 'where': {}, 'rp': []} for w in WINDOWS},
                                  'first': None, 'last': None, 'samples': [], 'origin': {}, 'crowd': [], 'tracker_tag': t.get('tracker_tag')}
        return n
    for p, dt, found in rel:
        age = (NOW - dt).total_seconds() / 86400
        ids = sorted(found)
        if p['source'] == 'live':
            for tid in ids:
                for hid in by_topic.get(tid, ()):
                    for w in PROJECT_WINDOWS:
                        if age <= WINDOWS[w]:
                            s = proj[hid][w]; s['posts'] += 1; s['authors'].add((p['net'], p['author'])); s['nets'].add(p['net'])
        for tid in ids:
            n = node(found[tid])
            for w, days in WINDOWS.items():
                if age <= days:
                    s = n['w'][w]; s['posts'] += 1; s['nets'][p['net']] = s['nets'].get(p['net'], 0) + 1
                    if p['source'] != 'official': s['authors'].add((p['net'], p['author']))     # a vendor's own feed is not a voice
                    wh = s['where'].setdefault(p['net'], [0, set()]); wh[0] += 1
                    if p['source'] != 'official': wh[1].add(p['author'])
                    if (p['net'], p['pid']) in item_pct[w]: s['rp'].append(item_pct[w][(p['net'], p['pid'])])
                    e = math.log1p(max(0, p['score'] or 0) + max(0, p['comments'] or 0))
                    s['eng'] += e
                    if p['net'] != 'Reddit': s['eng_xr'] += e
                    if p['net'] in DIGEST: s['nl'].add(p['author'])
                    if p['source'] == 'live' and p['net'] not in DIGEST and (p['score'] is not None or p['comments'] is not None):
                        o = s['obs'].setdefault(p['net'], {'posts': 0, 'score': 0, 'comments': 0})
                        o['posts'] += 1; o['score'] += max(0, p['score'] or 0); o['comments'] += max(0, p['comments'] or 0)
                    if p['net'] in CONVERSATION and p['source'] == 'live': s['conv'] += 1
            if crowd(p): n['crowd'].append((p, dt))
            n['first'] = min(n['first'] or p['created'], p['created']); n['last'] = max(n['last'] or p['created'], p['created'])
            n['samples'].append((math.log1p(max(0, p['score'] or 0)) - age / 30, p, dt))
            o = n['origin'].get(p['net'])
            if p['source'] != 'tracker' and (o is None or dt < o[0]): n['origin'][p['net']] = (dt, p)
        if p['net'] in DIGEST | OFFICIAL: continue            # a digest lists many stories, a vendor post many products: co-mention there is not a link
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                k = (ids[i], ids[j])
                e = edges.setdefault(k, {w: 0 for w in WINDOWS})
                for w, days in WINDOWS.items():
                    if age <= days: e[w] += 1
    # parent links make families visible even when they are never co-mentioned
    for n in list(nodes.values()):
        par = n['parent']
        if par and par in nodes:
            k = tuple(sorted((n['id'], par)))
            edges.setdefault(k, {w: 0 for w in WINDOWS})
    out_nodes = []
    for n in nodes.values():
        W = {}
        for w, s in n['w'].items():
            nets = len(s['nets'])
            other = len([k for k in s['nets'] if k not in DIGEST | OFFICIAL])
            reach = other + len(s['nl'])
            for rid, ts in repo_topics.items():
                if n['id'] in ts and rid in repo_pct[w]: s['rp'].append(('repos', repo_pct[w][rid]))
            top5 = sorted((v for _, v in s['rp']), reverse=True)[:5]
            parts = {}
            for typ, v in s['rp']:
                q = parts.setdefault(typ, {'n': 0, 'best': 0.0}); q['n'] += 1; q['best'] = max(q['best'], round(v, 1))
            W[w] = {'posts': s['posts'], 'authors': len(s['authors']), 'nets': s['nets'], 'eng': round(s['eng'], 1),
                    'eng_ex_reddit': round(s['eng_xr'], 1), 'newsletters': len(s['nl']), 'newsletter_names': sorted(s['nl']),
                    'reach': reach, 'reach_label': f"{other} network{'s' if other != 1 else ''} + {len(s['nl'])} newsletter{'s' if len(s['nl']) != 1 else ''}"
                                                   + (' (+ official post)' if 'Official' in s['nets'] else ''),
                    'reach_pct': round(sum(top5) / len(top5), 1) if top5 else None, 'reach_parts': parts,
                    'where': {k: {'posts': v[0], 'voices': None if k in OFFICIAL else len(v[1])} for k, v in s['where'].items()},
                    'engagement': s['obs'], 'weight': round(len(s['authors']) * (1 + 0.5 * max(0, nets - 1)), 2)}
        conv1, conv7 = n['w']['1d']['conv'], n['w']['7d']['conv']
        rising = round(conv1 / (conv7 / 7), 2) if conv7 >= 4 and conv1 >= 2 else None
        n['samples'].sort(key=lambda x: -x[0])
        seen_u, samples = set(), []
        for _, p, dt in n['samples']:
            if p['url'] in seen_u: continue
            seen_u.add(p['url'])
            samples.append({'net': p['net'], 'title': shown(p)[:200], 'url': p['url'], 'date': iso(dt)[:10],
                            'score': p['score'], 'comments': p['comments'], 'author': p['author'], 'source': p['source']})
            if len(samples) >= 8: break
        spread = [{'net': net, 'at': iso(dt), 'day_only': dt.hour == dt.minute == dt.second == 0, 'author': p['author'], 'url': p['url'],
                   'title': shown(p)[:160], 'source': p['source']}
                  for net, (dt, p) in sorted(n['origin'].items(), key=lambda x: (x[1][0].date(), x[0] in DIGEST, x[1][0]))]
        out_nodes.append({'id': n['id'], 'label': n['label'], 'kind': n['kind'], 'parent': n['parent'], 'w': W, 'rising': rising, 'spread': spread,
                          'first': (n['first'] or '')[:10], 'last': (n['last'] or '')[:10], 'samples': samples,
                          'organic': organic(n, dupes, author_total, [r for r in r30 if n['id'] in repo_topics.get(r['id'], ())], base,
                                             [(h, hype_items[h]) for h in hype_items if PROJECT_TOPIC.get(h) == n['id'] or
                                              (n['tracker_tag'] and hype_items[h].get('tag') == n['tracker_tag'])])})
    out_nodes.sort(key=lambda x: -x['w']['30d']['weight'])
    out_nodes = [x for x in out_nodes if x['w']['30d']['posts'] >= 2][:160]
    keep = {x['id'] for x in out_nodes}
    score_signal(out_nodes)
    novelty(rel, out_nodes, repo_topics, repos or [], tag_topics)
    kinds = {x['id']: x['kind'] for x in out_nodes}
    for x in out_nodes:                                      # who/where: people and subjects named in the same posts
        x['with'] = {}
        for w in WINDOWS:
            nb = sorted(((b if a == x['id'] else a, e[w]) for (a, b), e in edges.items() if x['id'] in (a, b) and e[w] > 0
                         and (b if a == x['id'] else a) in keep), key=lambda z: -z[1])
            x['with'][w] = {'people': [[i, c] for i, c in nb if kinds[i] == 'person'][:3],
                            'subjects': [[i, c] for i, c in nb if kinds[i] != 'person'][:5]}
    out_edges = [{'a': a, 'b': b, 'w': w} for (a, b), w in edges.items() if a in keep and b in keep and (w['30d'] >= 2 or
                 any(x['id'] in (a, b) and x['parent'] in (a, b) for x in out_nodes))]
    totals = {w: {} for w in WINDOWS}
    for p, dt, _ in rel:
        age = (NOW - dt).total_seconds() / 86400
        for w, days in WINDOWS.items():
            if age <= days: totals[w][p['net']] = totals[w].get(p['net'], 0) + 1
    projects = {hid: {w: {'voices': len(s['authors']), 'posts': s['posts'], 'nets': len(s['nets'])} for w, s in ws.items()}
                for hid, ws in proj.items()}
    return out_nodes, out_edges, totals, projects, {'citations': cite_table(rel), 'stories': stories(rel)}

REACH_PCT_METHOD = ('reach_pct (per window) = mean of the five highest item percentiles among the items matching the topic; an item\'s percentile '
                    'is taken within its own type and window: posts per network (HN points, Mastodon favourites + boosts, Lobsters score, Bluesky likes + reposts; '
                    'Reddit excluded, its archive scores are ingestion snapshots), papers (HF upvotes), repos (stars gained in the window); raw counts are never summed across types')
ORGANIC_METHOD = ('organic (30d live conversation by named authors): burst = share of posts in the densest 6 hours; dupe = share of posts (5+ words) whose '
                  '5-word-shingle Jaccard with a post by a different author is >= 0.6; single_topic = share of authors with 2+ stored posts whose posts all match the topic; '
                  'link_push = largest share of posts pointing at one target URL; repos = anti-noise flags on matching tracker repos; dossier = HYPE coordination assessment. '
                  'Label: too few posts (< 10); a signal fires at burst >= 0.5, dupe >= 0.2, single_topic >= 0.5 (5+ authors), link_push >= 0.3 (5+ posts), '
                  'repos stars>activity on half of 3+ repos, dossier disclosed or measured coordination; strong = two signals or burst >= 0.7, dupe >= 0.4, link_push >= 0.5. '
                  'Signals, not proof')
REACH_POST_NETS = ('HN', 'Mastodon', 'Lobsters', 'Bluesky')     # Reddit scores are ingestion snapshots; newsletters/official have none
LINKS_SINCE = '2026-10-16'                                       # adapters keep target links from this date

def crowd(p):
    """Live conversation by a named account: the population the coordination signals look at."""
    return p['source'] == 'live' and p['net'] in CONVERSATION and (p['author'] or '') not in ('', '[deleted]', 'AutoModerator')

def pct_rank(vals):
    """Share (0-100) of the other values that are strictly lower; ties share the lower rank; zero (or a lone value) scores 0."""
    srt, n = sorted(vals), len(vals)
    return [0.0 if v <= 0 or n < 2 else 100.0 * bisect.bisect_left(srt, v) / (n - 1) for v in vals]

def burst_share(times, hours=6):
    """(share of posts inside the densest `hours` window, window start)."""
    ts = sorted(times)
    if not ts: return None, None
    best, start, j = 0, ts[0], 0
    for i, t in enumerate(ts):
        while t - ts[j] > timedelta(hours=hours): j += 1
        if i - j + 1 > best: best, start = i - j + 1, ts[j]
    return best / len(ts), start

def shingles(text, k=5):
    w = re.findall(r'[a-z0-9]+', re.sub(r'https?://\S+', ' ', (text or '').lower()))
    return {tuple(w[i:i + k]) for i in range(len(w) - k + 1)}

def near_dupes(posts, thr=0.6):
    """Keys (net, pid) of posts whose 5-word-shingle Jaccard with a post by a different author is >= thr.
    Posts under five words cannot be compared and are left out (they are not in the result and not in its denominator)."""
    sh = {(p['net'], p['pid']): (shingles(p['title']), (p['net'], p['author'])) for p in posts}
    sh = {k: v for k, v in sh.items() if v[0]}
    index = {}
    for k, (ss, _) in sh.items():
        for g in ss: index.setdefault(g, []).append(k)
    out = set()
    for k, (ss, au) in sh.items():
        shared = {}
        for g in ss:
            for o in index[g]:
                if o != k and sh[o][1] != au: shared[o] = shared.get(o, 0) + 1
        if any(c / (len(ss) + len(sh[o][0]) - c) >= thr for o, c in shared.items()): out.add(k)
    return out, set(sh)

def norm_link(u):
    u = re.sub(r'#.*$', '', u or '')
    u = re.sub(r'([?&])(utm_[a-z]+|ref|s|t)=[^&]*', r'\1', u)
    return re.sub(r'[?&]+$', '', u).rstrip('/')

ORG_MIN_POSTS = 10
def organic(n, dupes, author_total, repos, base, dossier):
    """Organic-vs-orchestrated signals over the topic's 30-day live conversation (named authors only). Signals, not proof."""
    ps = n['crowd']; cnt = len(ps); flags, strong, rd = [], [], {}
    out = {'window': '30d', 'posts': cnt}
    b, at = burst_share([dt for _, dt in ps])
    out['burst'] = round(b, 3) if b is not None else None
    out['burst_at'] = iso(at) if at else None
    if b is not None:
        if cnt >= ORG_MIN_POSTS and b >= 0.5: flags.append('burst')
        if cnt >= ORG_MIN_POSTS and b >= 0.7: strong.append('burst')
        rd['burst'] = (f"{round(100 * b)}% of {cnt} posts fell in the busiest 6 hours (from {iso(at)[:16].replace('T', ' ')}Z). "
                       + ('High: a synchronized push looks like this, but so does a launch or a news day.' if 'burst' in flags else
                          'Spread over time, as ongoing discussion usually is.' if b < 0.3 else 'Some clustering, typical of a news day.'))
    dk, elig = dupes
    e = [p for p, _ in ps if (p['net'], p['pid']) in elig]
    if len(e) >= ORG_MIN_POSTS:
        d = sum(1 for p in e if (p['net'], p['pid']) in dk) / len(e)
        out['dupe'], out['dupe_n'] = round(d, 3), len(e)
        if d >= 0.2: flags.append('dupe')
        if d >= 0.4: strong.append('dupe')
        rd['dupe'] = (f"{round(100 * d)}% of {len(e)} comparable posts near-duplicate a post by a different author. "
                      + ('High: copy-paste campaigns look like this; so do many people submitting the same article title.' if d >= 0.2 else 'Low: little copy-paste across authors.'))
    else:
        out['dupe'], out['dupe_n'] = None, len(e)
        rd['dupe'] = f'Too few posts of five or more words to compare ({len(e)}).'
    authors = {}
    for p, _ in ps: authors[(p['net'], p['author'])] = authors.get((p['net'], p['author']), 0) + 1
    el = [a for a in authors if author_total.get(a, 0) >= 2]
    if len(el) >= 5:
        st = sum(1 for a in el if authors[a] >= author_total[a]) / len(el)
        out['single_topic'], out['single_topic_n'] = round(st, 3), len(el)
        if st >= 0.5: flags.append('single_topic')
        rd['single_topic'] = (f"{round(100 * st)}% of {len(el)} authors with two or more stored posts posted only about this topic. "
                              + ('High: new or single-purpose accounts look like this.' if st >= 0.5 else 'Most of them also post about other things.'))
    else:
        out['single_topic'], out['single_topic_n'] = None, len(el)
        rd['single_topic'] = f'Too few authors with two or more stored posts to judge ({len(el)}); one-post authors are not counted.'
    links = [norm_link(p['extra'].get('link')) for p, _ in ps if (p.get('extra') or {}).get('link')]
    if len(links) >= ORG_MIN_POSTS:
        top = max(set(links), key=links.count); lp = links.count(top) / len(links)
        out['link_push'], out['link_push_n'], out['link_top'] = round(lp, 3), len(links), top
        if lp >= 0.3 and links.count(top) >= 5: flags.append('link_push')
        if lp >= 0.5 and links.count(top) >= 5: strong.append('link_push')
        rd['link_push'] = (f"{round(100 * lp)}% of {len(links)} posts with a known target link point at the same URL. "
                           + ('High: one link pushed by many accounts looks like this.' if 'link_push' in flags else 'Links are varied.'))
    else:
        out['link_push'], out['link_push_n'] = None, len(links)
        rd['link_push'] = f'Unknown: target links are kept only from {LINKS_SINCE} ({len(links)} posts with one so far).'
    fl = {}
    for r in repos:
        for f in (r.get('flags') or {}).get('30d') or []: fl[f] = fl.get(f, 0) + 1
    out['repos'] = {'n': len(repos), 'flags': fl, 'baseline_stars_activity': base}
    if len(repos) >= 3 and fl.get('stars>activity', 0) / len(repos) >= 0.5: flags.append('repos')
    rd['repos'] = ('No tracked repo matches this topic.' if not repos else
                   f"{len(repos)} tracked repos ranked in 30d match: {fl.get('stars>activity', 0)} stars>activity, {fl.get('solo', 0)} solo, {fl.get('spike', 0)} spike"
                   + (f" (stars>activity across all 30d rows: {round(100 * base)}%). " if base is not None else '. ')
                   + ('Star growth without matching activity in most of them is a star-farming pattern.' if 'repos' in flags else 'Mostly backed by activity.'))
    out['dossier'] = [{'id': h, 'name': it.get('name') or h, 'assessment': (it.get('coord') or {}).get('assessment'),
                       'disclosed': bool((it.get('coord') or {}).get('disclosed')), 'evidence': len((it.get('coord') or {}).get('evidence') or [])}
                      for h, it in dossier]
    measured = [d for d in out['dossier'] if d['disclosed'] or (re.search(r'coordinat', d['assessment'] or '', re.I) and not re.search(r'not assessed|^no ', d['assessment'] or '', re.I))]
    if measured: flags.append('dossier')
    rd['dossier'] = ('No HYPE research project maps to this topic.' if not out['dossier'] else
                     '; '.join(f"{d['name']}: {d['assessment'] or 'not assessed'}{' (disclosed sponsorship)' if d['disclosed'] else ''}" for d in out['dossier']))
    out['flags'], out['readings'] = flags, rd
    out['label'] = ('too few posts' if cnt < ORG_MIN_POSTS else 'strong coordination signals' if strong or len(flags) >= 2 else
                    'some coordination signals' if flags else 'no coordination signal')
    return out

def cite_table(rel, top=50):
    """What the digests link to: domains and X/Twitter handles cited by newsletter items, per window."""
    out = {}
    for w, days in WINDOWS.items():
        dom, xh = {}, {}
        for p, dt, found in rel:
            if p['net'] not in DIGEST or (NOW - dt).total_seconds() / 86400 > days: continue
            ex = p.get('extra') or {}
            own = newsletter_sites(p['author']) + (host(p['url'] or ''),)
            for d in ex.get('domains') or []:
                if is_own(d, own): continue
                q = dom.setdefault(d, [0, set()]); q[0] += 1; q[1].add(p['author'])
            for h in ex.get('x') or []:
                q = xh.setdefault(h, [0, set(), {}]); q[0] += 1; q[1].add(p['author'])
                for t in found.values(): q[2][t['label']] = q[2].get(t['label'], 0) + 1
        out[w] = {'domains': [[d, c, sorted(nl)] for d, (c, nl) in sorted(dom.items(), key=lambda x: (-x[1][0], x[0]))[:top]],
                  'x_handles': [[h, c, sorted(nl), [k for k, _ in sorted(tp.items(), key=lambda z: -z[1])[:3]]]
                                for h, (c, nl, tp) in sorted(xh.items(), key=lambda x: (-x[1][0], x[0]))[:top]]}
    return out

SIGNAL_WEIGHTS = {'voices': 0.4, 'reach': 0.25, 'rising': 0.2, 'eng': 0.15}
SIGNAL_METHOD = ('signal (0-100, per window) = 0.40 x pct(voices) + 0.25 x pct(reach) + 0.20 x pct(rising) + 0.15 x pct(engagement excl. Reddit); '
                 'pct(x) = share of the other topics on the map with a strictly lower value (ties share the lower rank; a zero value scores 0); '
                 'reach = distinct networks other than newsletters and Official + distinct newsletters; voices exclude Official feeds; '
                 'rising is the node-level 24h-vs-7d ratio, a missing rising or a ratio below 1 scores 0; '
                 'engagement = sum of log(1 + score + comments) over matching posts outside Reddit (Reddit archive scores are ingestion snapshots). '
                 'A heuristic for ordering attention, not a measure of truth or importance')

def score_signal(nodes):
    """Per-window signal: weighted mean of percentile ranks among the nodes kept on the map. Components are stored next to it."""
    pct = pct_rank
    rising = pct([x['rising'] if x['rising'] and x['rising'] >= 1 else 0 for x in nodes])     # slower than its 7-day average: no lift
    for w in WINDOWS:
        parts = {'voices': pct([x['w'][w]['authors'] for x in nodes]), 'reach': pct([x['w'][w]['reach'] for x in nodes]),
                 'rising': rising, 'eng': pct([x['w'][w]['eng_ex_reddit'] for x in nodes])}
        for i, x in enumerate(nodes):
            comp = {k: round(parts[k][i], 1) for k in SIGNAL_WEIGHTS}
            x['w'][w]['signal'] = round(sum(SIGNAL_WEIGHTS[k] * parts[k][i] for k in SIGNAL_WEIGHTS), 1) if x['w'][w]['authors'] else 0.0
            x['w'][w]['signal_parts'] = comp

# ------------------------------------------------------------------ stories: events, not topics
STORY_DAYS = 7
SEED_NETS = {'HN', 'Lobsters'} | DIGEST | OFFICIAL            # edited or launch sources seed a story; chatter attaches to one
TOK_RX = re.compile(r"[a-z0-9][a-z0-9.+'\-]*[a-z0-9+]|[a-z0-9]")
STORY_STOP = set("""the a an and or of to in on for with by from at as is are was were be been it its this that these those you your we our i my me
he she they them his her their not no yes do does did have has had will would can could should just more most less than then so very really
how why what when where who which new now today via vs about into over out up down off one two all any some get got make made using use used
like say says said here there s t ve ll re d m don doesn didn isn aren won can't don't i'm it's you're show ask hn tell launch introducing
announces announced launches launched releases released open-source opensource open source free first best guide week day news update updates""".split()) | COMMON

def toks(text):
    t = re.sub(r'https?://\S+|#\w+|@\w+', ' ', (text or '').lower())
    return {w.strip("'") for w in TOK_RX.findall(t) if w.strip("'") not in STORY_STOP and (len(w) > 2 or any(c.isdigit() for c in w))}

def canon(u):
    u = re.sub(r'[?#].*$', '', (u or '').strip().lower())
    u = re.sub(r'^https?://(www\.|m\.|mobile\.)?', '', u).rstrip('/')
    return u if '/' in u else ''          # a bare domain is not one story

def anchors(found):
    """The named release a post is about; a post naming several (a comparison, a digest) anchors nothing, or it would bridge events."""
    a = [t for t, x in found.items() if x['kind'] in ('version', 'emerging')]
    return a if len(a) == 1 else []

def _uf(n):
    par = list(range(n))
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    def join(a, b): par[find(b)] = find(a)
    return find, join

def stories(rel, limit=60):
    """Cluster the last 7 days into events. Seeds: HN, Lobsters, newsletter and official items, joined when they share
    a canonical target link or most of their idf-weighted title words. Reddit, Mastodon and Bluesky posts attach to the
    best-matching seed; chatter that matches no seed forms its own story only with >= 5 voices on it.
    A newsletter whose body names a story's key words carries it. Ids hash a canonical URL: stable across runs."""
    import hashlib
    rows = [(p, dt, f) for p, dt, f in rel if (NOW - dt).total_seconds() / 86400 <= STORY_DAYS and p['source'] in ('live', 'official')]
    docs = [(p, dt, f, toks(shown(p))) for p, dt, f in rows]
    df = {}
    for _, _, _, t in docs:
        for w in t: df[w] = df.get(w, 0) + 1
    N = max(1, len(docs))
    idf = {w: math.log(N / c) for w, c in df.items()}
    def sim(a, b):
        sh = a & b
        if len([w for w in sh if df[w] < N * 0.02]) < 2: return 0.0       # two shared words that are not everyday AI vocabulary
        return sum(idf[w] for w in sh) / (sum(idf[w] for w in a | b) or 1)
    seeds = [d for d in docs if d[0]['net'] in SEED_NETS and len(d[3]) >= 2]
    find, join = _uf(len(seeds))
    link = {}
    for i, (p, _, _, t) in enumerate(seeds):
        c = canon((p.get('extra') or {}).get('link') or (p['url'] if p['net'] in OFFICIAL else ''))
        if c: link.setdefault(c, []).append(i)
    for ids in link.values():
        for j in ids[1:]: join(ids[0], j)
    anchor = {}                                               # a named release (a model version or a new name) is one event
    for i, d in enumerate(seeds):
        for tid in anchors(d[2]): anchor.setdefault(tid, []).append(i)
    for ids in anchor.values():
        for j in ids[1:]: join(ids[0], j)
    for i in range(len(seeds)):
        for j in range(i + 1, len(seeds)):
            if sim(seeds[i][3], seeds[j][3]) >= 0.45: join(i, j)
    groups = {}
    for i, d in enumerate(seeds): groups.setdefault(find(i), []).append(d)
    clusters = list(groups.values())
    by_anchor = {}
    for k, c in enumerate(clusters):
        for d in c:
            for tid in anchors(d[2]): by_anchor.setdefault(tid, k)
    stray = []
    for d in docs:                                            # chatter attaches to its release, else to the best seed
        if d[0]['net'] in SEED_NETS: continue
        a = [by_anchor[t] for t in anchors(d[2]) if t in by_anchor]
        if a: clusters[a[0]].append(d); continue
        best, bs = None, 0.0
        for k, c in enumerate(clusters):
            for s_ in c[:6]:
                v = sim(d[3], s_[3])
                if v > bs: best, bs = k, v
        if best is not None and bs >= 0.4: clusters[best].append(d)
        else: stray.append(d)
    idx = {}                                                  # chatter-only stories: stricter threshold, 5+ voices
    for i, d in enumerate(stray):
        for w in d[3]:
            if 2 <= df[w] <= 80: idx.setdefault(w, []).append(i)
    find2, join2 = _uf(len(stray))
    first_a = {}
    for i, d in enumerate(stray):
        for tid in anchors(d[2]):
            if tid in first_a: join2(first_a[tid], i)
            else: first_a[tid] = i
    tried = set()
    for ids in idx.values():
        for x, a in enumerate(ids):
            for b in ids[x + 1:]:
                if (a, b) in tried: continue
                tried.add((a, b))
                if stray[a][0]['author'] != stray[b][0]['author'] and sim(stray[a][3], stray[b][3]) >= 0.55: join2(a, b)
    g2 = {}
    for i, d in enumerate(stray): g2.setdefault(find2(i), []).append(d)
    clusters += [c for c in g2.values() if len({(d[0]['net'], d[0]['author']) for d in c}) >= 5]
    digests = [d for d in docs if d[0]['net'] in DIGEST]
    rank = {n: i for i, n in enumerate(['Official', 'Newsletter', 'HN', 'Lobsters', 'Reddit', 'Mastodon', 'Bluesky'])}
    out = []
    for c in clusters:
        c.sort(key=lambda d: d[1])
        voices = {(d[0]['net'], d[0]['author']) for d in c if d[0]['net'] not in OFFICIAL}
        nets = {}
        for d in c: nets[d[0]['net']] = nets.get(d[0]['net'], 0) + 1
        if len(voices) < 2 and not (set(nets) & (DIGEST | OFFICIAL)): continue
        ed = [d for d in c if d[0]['net'] in SEED_NETS] or c
        cnt = {}
        for d in ed:
            for w in d[3]: cnt[w] = cnt.get(w, 0) + 1
        key = sorted((w for w, k in cnt.items() if k >= max(1, len(ed) / 2) and df[w] < N * 0.02), key=lambda w: -idf[w])[:3]
        nl = {d[0]['author'] for d in c if d[0]['net'] in DIGEST}
        if len(key) >= 2:
            for d in digests:
                body = (d[0]['title'] or '').lower()
                if all(re.search(r'(?<![a-z0-9])' + re.escape(w) + r'(?![a-z0-9])', body) for w in key): nl.add(d[0]['author'])
        ac = {}
        for d in c:
            for t in anchors(d[2]): ac[t] = ac.get(t, 0) + 1
        top_a = max(ac, key=ac.get) if ac else None
        label = next((x[top_a]['label'] for _, _, x, _ in c if top_a in x), None) if top_a else None
        def hk(d):
            t = shown(d[0])
            junk = (bool(re.fullmatch(r'[\w.-]+ v?\d+(\.\w+)*', t)) or len(t) > 160 or len(t) < 12      # package bumps, run-ons, stubs
                    or t.count(',') >= 2 or bool(re.search('[\U0001F300-\U0001FAFF\u2600-\u27BF]', t)) or t.startswith('['))   # digest issue titles
            named = not label or label.lower() in t.lower()
            return (junk, not (named and d[0]['net'] in SEED_NETS), not named, rank.get(d[0]['net'], 9), -(d[0]['score'] or 0), d[1])
        head = min(c, key=hk)
        path, got = [], set()
        for d in c:
            k = d[0]['author'] if d[0]['net'] in DIGEST else d[0]['net']
            if k in got: continue
            got.add(k); path.append({'net': d[0]['net'], 'who': d[0]['author'] if d[0]['net'] in DIGEST | OFFICIAL else None, 'at': iso(d[1]), 'url': d[0]['url']})
        tags = {}
        for d in c:
            for tid in d[2]: tags[tid] = tags.get(tid, 0) + 1
        hn = max([d[0]['score'] or 0 for d in c if d[0]['net'] == 'HN'] or [0])
        age_h = (NOW - c[-1][1]).total_seconds() / 3600
        spread = (2 * math.log2(1 + len(voices)) + len([n for n in nets if n not in DIGEST | OFFICIAL]) + 1.5 * len(nl)
                  + (1 if 'Official' in nets else 0) + math.log10(1 + hn))
        e0 = ed[0]                                            # earliest editorial post (members are in time order)
        cid = ('release:' + top_a) if top_a else (canon((e0[0].get('extra') or {}).get('link')) or e0[0]['url'] or f"{e0[0]['net']}:{e0[0]['pid']}")
        covered = bool(set(nets) & SEED_NETS) or bool(nl)
        out.append({'id': 's:' + hashlib.sha1(cid.encode()).hexdigest()[:12], 'label': label, 'covered': covered,
                    'headline': shown(head[0])[:220], 'url': head[0]['url'],
                    'link': (head[0].get('extra') or {}).get('link'), 'first': iso(c[0][1]), 'last': iso(c[-1][1]),
                    'voices': len(voices), 'nets': nets, 'newsletters': sorted(nl), 'official': 'Official' in nets, 'hn_points': hn or None,
                    'key': key, 'path': path[:8], 'tags': [t for t, _ in sorted(tags.items(), key=lambda x: -x[1])[:5]],
                    'heat': round(spread * 0.5 ** (age_h / 48), 3),
                    'posts': [{'net': d[0]['net'], 'title': shown(d[0])[:200], 'url': d[0]['url'], 'author': d[0]['author'], 'at': iso(d[1]),
                               'score': d[0]['score'], 'comments': d[0]['comments']} for d in sorted(c, key=lambda d: -(d[0]['score'] or 0))[:10]]})
    out.sort(key=lambda x: -x['heat'])
    cov = [x for x in out if x['covered']][:limit]
    return cov + [x for x in out if not x['covered']][:limit // 2]

STORY_METHOD = ('stories (last 7 days): an event is a cluster of posts. HN, Lobsters, newsletter and official items seed clusters and join when they share a '
                'canonical target link or idf-weighted title overlap >= 0.45 with two shared uncommon words (each in < 2% of the window\'s posts); '
                'posts naming the same model version or emerging name join one story; Reddit, Mastodon and Bluesky posts attach to their release or the best seed at >= 0.40; unmatched chatter joins at >= 0.55 and stands alone only with 5+ voices. '
                'covered = seeded by HN, Lobsters, a newsletter or a lab/vendor feed, or carried by a newsletter; otherwise it is chatter not yet in the press. '
                'A newsletter carries a story when its item names all of the story\'s key words (up to three uncommon words shared by its editorial posts). '
                'heat = (2 x log2(1 + voices) + networks outside newsletters/official + 1.5 x newsletters carrying it + 1 if a lab or vendor posted it + log10(1 + HN points)) '
                'x 0.5^(hours since the newest post / 48). id = "s:" + first 12 hex of sha1("release:" + topic id when the story is about one named release, '
                'else the canonical target link of its earliest editorial post, else that post\'s URL)')

NOW_DAYS, BASE_DAYS = 7, 30
NOVELTY_METHOD = ('new (the default ranking): two legs, each a percentile among topics that qualify for it, and a topic ranks by the higher one. '
                  'talk = lift of the topic\'s share of posts in the last 7 days over its share in days 8-30, on the deep networks only '
                  '(live networks with posts on >= 70% of the baseline days and >= 50 baseline posts; shallower archives cannot show what is normal yet), '
                  'baseline smoothed by +1 post; it qualifies with >= 2 deep-network posts this week, >= 5 voices and >= 2 networks in 7 days. '
                  'build = count of tracker repos matching the topic (a repo in a tracker paradigm counts only for that paradigm\'s theme) that were born in the last 30 days; it qualifies with >= 3 born repos that are >= half of its repos (a new wave, not an old field). '
                  'always-on = mentioned on the deep networks on >= 60% of the baseline days with talk lift < 2: big but not news; its talk leg does not count. '
                  'Lift is relative to what we sampled, not to the whole internet')

def novelty(rel, nodes, repo_topics, repos, tag_topics=None):
    """What changed: this week's share against the topic's own baseline, and repos being born around it. Writes node['new']."""
    span = BASE_DAYS - NOW_DAYS
    tot, days = {}, {}
    for p, dt, _ in rel:
        if p['source'] != 'live' or p['net'] in OFFICIAL: continue
        per = 'now' if (NOW - dt).total_seconds() / 86400 <= NOW_DAYS else 'base'
        tot[(p['net'], per)] = tot.get((p['net'], per), 0) + 1
        if per == 'base': days.setdefault(p['net'], set()).add(dt.date())
    deep = sorted(n for n, d in days.items() if len(d) >= 0.7 * span and tot.get((n, 'base'), 0) >= 50)
    nn, nb = sum(tot.get((n, 'now'), 0) for n in deep), sum(tot.get((n, 'base'), 0) for n in deep)
    hits = {}
    for p, dt, found in rel:
        if p['source'] != 'live' or p['net'] not in deep: continue
        now = (NOW - dt).total_seconds() / 86400 <= NOW_DAYS
        for tid in found:
            h = hits.setdefault(tid, {'now': 0, 'base': 0, 'bdays': set()})
            if now: h['now'] += 1
            else: h['base'] += 1; h['bdays'].add(dt.date())
    born_cut = (NOW - timedelta(days=BASE_DAYS)).strftime('%Y-%m-%d')
    rows = {r['id']: r for r in repos}
    for x in nodes:
        h = hits.get(x['id'], {'now': 0, 'base': 0, 'bdays': set()})
        w7 = x['w']['7d']
        lift = round((h['now'] / nn) / ((h['base'] + 1) / nb), 2) if nn and nb else None
        talk_ok = lift is not None and h['now'] >= 2 and w7['authors'] >= 5 and len([k for k in w7['nets'] if k not in OFFICIAL]) >= 2
        mine = [rows[r] for r, ts in repo_topics.items() if x['id'] in ts and r in rows       # a paradigm's repos build only its own theme
                and (not (tag_topics or {}).get(rows[r].get('tag')) or x['id'] in tag_topics[rows[r]['tag']])]
        born = [r for r in mine if (r.get('created') or '') >= born_cut]
        x['new'] = {'lift': lift, 'now': h['now'], 'base': h['base'], 'base_days': len(h['bdays']), 'deep': deep,
                    'talk_ok': talk_ok, 'repos': len(mine), 'born': len(born),
                    'born_stars_7d': sum(max(0, (r['gained'] or {}).get('7d') or 0) for r in born),
                    'always_on': len(h['bdays']) >= 0.6 * span and (lift or 0) < 2}
        x['new']['born_share'] = round(len(born) / len(mine), 2) if mine else None
        x['new']['born_top'] = [[r['id'], (r['gained'] or {}).get('7d')] for r in sorted(born, key=lambda r: -((r['gained'] or {}).get('7d') or 0))[:3]]
    talk = pct_rank([math.log(x['new']['lift']) if x['new']['talk_ok'] and x['new']['lift'] > 1 else -99 for x in nodes])
    build_v = [x['new']['born'] if x['new']['born'] >= 3 and x['new']['born_share'] >= 0.5 else 0 for x in nodes]
    build = pct_rank(build_v)
    for i, x in enumerate(nodes):
        n = x['new']
        t = round(talk[i], 1) if n['talk_ok'] and n['lift'] > 1 and not n['always_on'] else 0.0
        b = round(build[i], 1) if build_v[i] else 0.0
        n['talk'], n['build'] = t, b
        n['score'] = max(t, b)
        n['leg'] = None if not n['score'] else ('talk' if t >= b else 'build')
    return deep

PROJECT_WINDOWS = ('7d', '30d')

ADAPTERS = ['Hacker News (Algolia)', 'Lobsters (ai tag)', 'Mastodon (mastodon.social tags)', 'Reddit (arctic-shift archive)',
            'Reddit (official API)', 'Bluesky (app password)', 'Newsletters (RSS)', 'Official feeds (RSS)']

def main():
    offline = '--offline' in sys.argv
    lex = json.load(open(os.path.join(BASE, 'topics_lexicon.json')))
    EMERGING_STOP.update(x.lower() for x in lex.get('emerging_stop', []))
    try: hype_items = json.load(open(os.path.join(WEB, 'hype.json')))['items']
    except (OSError, KeyError, ValueError): hype_items = {}
    con = db()
    if not offline:
        for name, fn in (('Hacker News (Algolia)', fetch_hn), ('Lobsters (ai tag)', fetch_lobsters), ('Mastodon (mastodon.social tags)', fetch_mastodon),
                         ('Reddit (arctic-shift archive)', fetch_reddit_archive), ('Reddit (official API)', fetch_reddit),
                         ('Bluesky (app password)', fetch_bluesky), ('Newsletters (RSS)', fetch_newsletters),
                         ('Official feeds (RSS)', fetch_official)):
            try:
                ps = fn(); store(con, ps)
                note(name, 'partial' if name in PARTIAL else 'ok', f'{len(ps)} posts fetched' + (f'; {PARTIAL[name]}' if name in PARTIAL else ''))
            except PermissionError as e:
                note(name, 'not connected', str(e))
            except Exception as e:                                           # a failed feed keeps its stored posts
                note(name, 'failed', f'{type(e).__name__}: {str(e)[:100]} (stored posts kept)')
            print(name, SOURCES[name], flush=True)
    if offline:                                              # keep the last live run's feed status, labelled as such
        try:
            prev = json.load(open(os.path.join(WEB, 'pulse.json'))).get('sources', {})
            for k, v in prev.items():
                if k not in ('Tracker (papers + repos)', 'HYPE research dossier'):
                    SOURCES[k] = {'status': v['status'], 'detail': v['detail'].split(' [as of last live run]')[0] + ' [as of last live run]'}
        except (OSError, ValueError, KeyError): pass
        for k in ADAPTERS:
            SOURCES.setdefault(k, {'status': 'unknown', 'detail': 'not fetched in this offline rebuild'})
    stored = load_stored(con)
    posts = stored + internal_posts()
    nodes, edges, totals, projects, extras = build(posts, lex, hype_items, tracker_repos())
    out = {'generated_at': iso(NOW), 'windows': list(WINDOWS), 'sources': SOURCES, 'totals': totals,
           'method': 'weight = distinct authors x (1 + 0.5 x (networks - 1)); rising = conversation posts in the last day / daily average over 7 days; ' + SIGNAL_METHOD
                     + '; ' + REACH_PCT_METHOD + '; ' + ORGANIC_METHOD + '; ' + NOVELTY_METHOD + '; ' + STORY_METHOD,
           'projects_note': 'projects: live sampled feeds only (no tracker, no dossier); voices = distinct (network, author) pairs, nets = distinct networks; 0 means no matching post in our sampled feeds, not zero attention',
           'coverage': ['Sampled feeds, not internet-wide totals: HN stories above 20 points, the Lobsters AI tag, nine Mastodon hashtags on mastodon.social, '
                        'ten AI subreddits via the arctic-shift public archive (up to 1,000 newest posts per subreddit per run, so busy subreddits reach back about a week), '
                        'twelve public AI newsletter feeds (the digest end point), lab and vendor announcement feeds (the Official network: where launches originate), '
                        'tracker papers and repos, and the static HYPE research dossier. '
                        'Bluesky appears only when an app password is configured. X appears only through the static dossier; it is not collected live.',
                        'Topics come from a reviewable lexicon (topics_lexicon.json), automatic model-version names, and capitalised phrases used by at least three distinct authors (marked emerging).',
                        'A node is only as strong as the posts listed under it; open it to read them.'],
           'stories': extras['stories'], 'nodes': nodes, 'edges': edges, 'projects': projects,
           'citations': {w: {'domains': c['domains']} for w, c in extras['citations'].items()},     # handles stay private (below)
           'official_feeds': official_meta()}
    with open(os.path.join(WEB, 'pulse.json'), 'w') as f:
        json.dump(out, f, separators=(',', ':'), ensure_ascii=False)
    # X handles cited by newsletters are a ranking of (often pseudonymous) accounts: kept for the owner's review, never published
    with open(os.path.join(HIST, 'citations.json'), 'w') as f:
        json.dump({'generated_at': iso(NOW), 'note': 'private: X handles cited by newsletter items, a candidate follow list; not published',
                   'x_handles': {w: c['x_handles'] for w, c in extras['citations'].items()}}, f, ensure_ascii=False, indent=1)
    print(f'pulse: {len(nodes)} topics, {len(edges)} links, 7d posts by network {totals["7d"]}')

if __name__ == '__main__':
    main()
