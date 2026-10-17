#!/usr/bin/env python3
"""Pulse: sampled AI conversation across networks -> topic graph (web/pulse.json) and the daily briefing (web/briefing.json:
one evidence record per story, the Top 10 cut and the gauge header values).

Run:   python3 pulse.py              fetch live feeds, merge with web/data.json + web/hype.json, recheck by id that the posts the outputs could
                                     show still exist (removals.json and checks/dossier-gone.json applied), write web/pulse.json and web/briefing.json
       python3 pulse.py --offline    rebuild from stored signals only (no network: the recheck makes no call, so every recheckable post is a count)
       python3 pulse.py --relink     the same rebuild after the Mastodon render check, keeping this run's source status and recheck result as
                                     written (refresh.yml only, inside the same run as the live pulse.py: it republishes that run's sources)
Env:   REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT   enable the Reddit adapter (official OAuth API)
       BSKY_HANDLE, BSKY_APP_PASSWORD                               enable the Bluesky adapter (app password)
State: history/signals.sqlite keeps 45 days of normalised posts; it rides in the same Actions cache as run.py's history.

Networks are samples, never totals: Hacker News stories above a points floor, the Lobsters AI tag, a fixed set of Mastodon
hashtags, plus (when connected) chosen subreddits and Bluesky searches, AI newsletter feeds (newsletters.json) and lab/vendor
announcement feeds (official_feeds.json, the 'Official' network). X is not collected; newsletter links to X are kept as citations. Every topic node carries the
posts that matched it, so a node is never more than the evidence behind it. Standard library only.
"""
import os, sys, re, json, math, time, bisect, sqlite3, base64, hashlib, html, urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
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
def internal_posts(drop=frozenset()):
    """Tracker and dossier posts. drop: URL hashes web/removals.json names or web/checks/dossier-gone.json lists (removal_lists());
    such a post is left out here, before build(), so no run reloads it from web/hype.json."""
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
        out = [p for p in out if not (p['url'] and url_hash(p['url']) in drop)]
        note('Tracker (papers + repos)', 'ok', f"{len(D['papers']['items'])} papers, {len(ranked)} repos ranked in 7d")
    except (OSError, KeyError, ValueError) as e:
        note('Tracker (papers + repos)', 'failed', str(e)[:120])
    try:
        H = json.load(open(os.path.join(WEB, 'hype.json')))
        ds = [p for p in dossier_posts(H) if not (p['url'] and url_hash(p['url']) in drop)]; out += ds
        note('HYPE research dossier', 'ok', f"{len(ds)} sampled posts, content cutoff {H.get('content_cutoff')} (static, refreshed by hand)")
    except (OSError, KeyError, ValueError) as e:
        note('HYPE research dossier', 'failed', str(e)[:120])
    return out

def dossier_posts(H):
    """The research dossier's sampled posts. An X, LinkedIn, YouTube or Telegram post is a count-only record: network, date and
    project (the hype item id, so PROJECT_TOPIC places it), with no text, author, link, figures or URL-built id."""
    out = []
    for hid, it in H['items'].items():
        for i, p in enumerate(it.get('posts', [])):
            if (p.get('pl') or 'other') in COUNT_ONLY:
                out.append(post(p['pl'], f'{hid}#{i}', None, '', '', p.get('d'), source='dossier', extra={'hype': hid}))
            elif p.get('url'):
                out.append(post(p.get('pl') or 'other', p['url'], p['url'], p.get('t'), p.get('au'), p.get('d'),
                                p.get('likes') if p.get('likes') is not None else p.get('score'), p.get('cm') or p.get('rp'), source='dossier'))
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

# ------------------------------------------------------------------ public-data rules: what of a post a public file may carry
# Reddit, X, LinkedIn, YouTube and Telegram are counts only (their terms); Mastodon too, except a post whose render check passed (below).
COUNT_ONLY = {'Reddit', 'X', 'LinkedIn', 'YouTube', 'Telegram', 'Discord', 'Mastodon'}
NAMED = DIGEST | OFFICIAL | {'arXiv', 'GitHub'}       # newsletter, feed, lab or paper and repo names stay; other authors are person handles
POST_BODY = ('title', 'author', 'url', 'link', 'score', 'comments', 'who')
NET_URL = [(n, re.compile(r'^https?://(?:[\w-]+\.)*(?:' + h + r')(?=[/:?#]|$)', re.I)) for n, h in
           (('Reddit', r'reddit\.com|redd\.it'), ('X', r'x\.com|twitter\.com|t\.co|nitter\.net|fxtwitter\.com|vxtwitter\.com'), ('LinkedIn', r'linkedin\.com|lnkd\.in'),
            ('YouTube', r'youtube\.com|youtu\.be|youtube-nocookie\.com'), ('Telegram', r't\.me|telegram\.me'))]
# a URL that names an account: an /@user path segment (npm scoped packages are not people), a Fediverse /users/<name>/statuses/
# URI, a Bluesky profile post, a DID
ACCOUNT_URL = re.compile(r'^https?://(?!(?:[\w-]+\.)*npmjs\.(?:org|com)/)[^\s?#]*/@|bsky\.app/profile/[^/\s]+/post/|/users/[^/\s]+/statuses/|did:(?:plc|web):', re.I)

# a mastodon.social status link in any form: published only as a checked Mastodon record's own url (public() below), never as an
# HN or newsletter target link, a story link or text, so no link reaches a file without its own passing check
STATUS_ANY = re.compile(r'mastodon\.social/(?:redirect/)?statuses/', re.I)

def url_net(u):
    """The count-only network a URL points into, 'account' for a URL that names an account, else None (publishable)."""
    return (next((n for n, rx in NET_URL if rx.match(u or '')), None) or ('account' if ACCOUNT_URL.search(u or '') else None)
            or ('Mastodon' if STATUS_ANY.search(u or '') else None))

def public_url(u): return None if url_net(u) else u

def pool(stored, internal):
    """Stored posts plus the tracker and dossier posts; a dossier post already stored (same network and URL, e.g. an HN item
    the live fetch also read) counts once, as the stored one."""
    have = {(p['net'], p['url']) for p in stored}
    return stored + [p for p in internal if not p['url'] or (p['net'], p['url']) not in have]

HANDLE = re.compile(r'(?<![\w/.@])@[A-Za-z0-9_][\w.-]*(?![\w/-])', re.A)       # @user in a shown title, not an npm @scope/package
def unhandle(t): return HANDLE.sub('@…', t) if isinstance(t, str) else t

# A live Mastodon post links to https://mastodon.social/statuses/<id> (mastodon.social's own status id, no handle) only while its latest
# logged-out render check (scripts/check_mastodon_links.mjs, cached in web/checks/mastodon-links.json) passed less than LINK_DAYS
# before NOW; every other Mastodon post is a count. An unreadable cache links nothing (fail-closed).
CHECKS, CANDIDATES = os.path.join(WEB, 'checks', 'mastodon-links.json'), os.path.join(HIST, 'mastodon-candidates.json')
LINK_DAYS = 7
STATUS_URL = re.compile(r'https://mastodon\.social/statuses/(\d{1,20})')
class _Every:                                  # the links set while main() lists the candidates a page would show
    def __contains__(self, _): return True
EVERY = _Every()

def load_links(path=CHECKS):
    try: C = json.load(open(path))['statuses']
    except (OSError, ValueError, KeyError, TypeError): return set()
    ok = set()
    for sid, e in C.items():
        at = parse_dt(e.get('passed_at')) if isinstance(e, dict) and e.get('result') == 'pass' else None
        if at and at == parse_dt(e.get('checked_at')) and timedelta(0) <= NOW - at < timedelta(days=LINK_DAYS): ok.add(sid)
    return ok

def mastodon_cache(path=CHECKS):
    """The render-check cache's entries by status id ({} when missing or unreadable)."""
    try: C = json.load(open(path))['statuses']
    except (OSError, ValueError, KeyError, TypeError): return {}
    return C if isinstance(C, dict) else {}

def masto_link(p, links):
    """The handle-free link of a live Mastodon post with a fresh passing check, else None. Only a post made on mastodon.social can pass:
    logged out, mastodon.social sends a post from another server off-site, so such a post stays a count and is never checked."""
    if p['net'] != 'Mastodon' or p.get('source') != 'live' or p.get('unreached') or not re.fullmatch(r'\d{1,20}', str(p.get('pid') or '')): return None
    if not (p.get('url') or '').startswith('https://mastodon.social/'): return None   # a post from another server: mastodon.social redirects it
    return f"https://mastodon.social/statuses/{p['pid']}" if p['pid'] in links else None

def hidden(p, links):
    """A post shown only as a count: a count-only network without its checked link, or a post the deleted-post recheck did not reach."""
    return bool(p.get('unreached')) or (p['net'] in COUNT_ONLY and not masto_link(p, links))
def link_url(p, links): return masto_link(p, links) or p['url']

def linked_url(net, u, links):
    m = net == 'Mastodon' and STATUS_URL.fullmatch(u or '')
    return bool(m) and m[1] in links

def public(rec, links=frozenset(), count=None):
    """A post record as published: a count-only network keeps its network, date and source (a Mastodon post with a passing check
    keeps its text, score and handle-free link too); elsewhere a person's author leaves, and so does a link that names an account.
    links: the ids whose check passed (load_links). count: hidden(post) of the post the record is made from, so a post the
    deleted-post recheck did not reach is a count too (default: the network rule alone)."""
    own = linked_url(rec['net'], rec.get('url'), links)
    if (rec['net'] in COUNT_ONLY if count is None else count) and not own: return {k: v for k, v in rec.items() if k not in POST_BODY}
    named = rec['net'] in NAMED and rec.get('source') != 'dossier'      # a dossier post's author is its poster
    return {k: (v if k == 'url' and own else public_url(v)) if k in ('url', 'link') else unhandle(v) if k == 'title' else v
            for k, v in rec.items() if k != 'author' or named}

# ------------------------------------------------------------------ graph
def shown(p):
    """Display text: newsletters keep their body only for matching; the page shows the issue title."""
    t = p['title'] or ''
    return t.split('\u241f', 1)[0].strip() if p['net'] in DIGEST | OFFICIAL else t

def build(posts, lex, hype_items, repos=None, links=frozenset()):
    """posts -> (nodes, edges, totals, projects, extras). repos: tracker repo rows [{id, text, tag, gained: {w}, flags: {w}}].
    links: Mastodon ids with a fresh passing render check (load_links); EVERY lists the candidates."""
    topics, fams, vrx, kw = compile_lexicon(lex, hype_items)
    by_id = {t['id']: t for t in topics}
    rel, author_total = [], {}
    for p in posts:
        dt = parse_dt(p['created'])
        if not dt or dt > NOW + timedelta(hours=1) or dt < NOW - timedelta(days=30): continue
        if p['net'] in OFFICIAL and p['source'] == 'live': p = {**p, 'source': 'official'}     # rows stored before the official source existed
        if crowd(p): author_total[(p['net'], p['author'])] = author_total.get((p['net'], p['author']), 0) + 1   # before the HN AI filter
        text, hid = p['title'] or '', (p.get('extra') or {}).get('hype')
        # a count-only dossier record has no text left to match: its project's node counts it
        found = {PROJECT_TOPIC[hid]: by_id[PROJECT_TOPIC[hid]]} if hid in PROJECT_TOPIC else match_topics(text, topics, fams, vrx)
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
        n['samples'].sort(key=lambda x: (-x[0], x[1]['url'] or '', x[1]['net'], str(x[1]['pid'])))   # ties: a fixed order, not the input's
        seen_u, samples = set(), []
        for _, p, dt in n['samples']:
            if p['url'] in seen_u or hidden(p, links): continue                   # a count-only post is in the counts, never a sample
            seen_u.add(p['url'])
            samples.append(public({'net': p['net'], 'title': shown(p)[:200], 'url': link_url(p, links), 'date': iso(dt)[:10],
                                   'score': p['score'], 'comments': p['comments'], 'author': p['author'], 'source': p['source']}, links, False))
            if len(samples) >= 8: break
        spread = [public({'net': net, 'at': iso(dt), 'day_only': dt.hour == dt.minute == dt.second == 0, 'author': p['author'], 'url': link_url(p, links),
                          'title': shown(p)[:160], 'source': p['source']}, links, hidden(p, links))
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
    return out_nodes, out_edges, totals, projects, {'citations': cite_table(rel), 'stories': stories(rel, links=links)}

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
        out['link_push'], out['link_push_n'], out['link_top'] = round(lp, 3), len(links), public_url(top)
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

PAIN_RX = re.compile(r"\b((is|are|it'?s|still)\b[^.?!]{0,30}\bdown\b|outage|lobotomi[sz]ed|nerf(ed)?|usage limits?|rate.?limit|limit reset|bug|broken|not working|"
                     r"doesn'?t work|stopped working|error|worse|degrad|refund|banned|deactivat|disappear|missing|dumber|declin(ing|es) (all|my))", re.I)
ASK_RX = re.compile(r"\?\s*$|^(is|are|does|do|can|should|how|why|what|which|anyone|has anyone|noob)\b", re.I)
def mode(title):
    """say (a statement or report), ask (a question) or pain (a complaint, outage or support problem), from the title alone."""
    return 'pain' if PAIN_RX.search(title or '') else 'ask' if ASK_RX.search(title or '') else 'say'

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

def headline_of(head, members, topic_label, links=frozenset()):
    """(headline, url, link) of a story. A count-only title is never shown: the earliest post of a shown network stands in,
    else the topic label, else a fixed line naming the network."""
    d = head if not hidden(head[0], links) else next((m for m in members if not hidden(m[0], links)), None)
    if d: return unhandle(shown(d[0])[:220]), masto_link(d[0], links) or public_url(d[0]['url']), public_url((d[0].get('extra') or {}).get('link'))
    return topic_label or f"{head[0]['net']} discussion, title not shown", None, None

# the substance a story's own posts link to (C8): a GitHub repository or an arXiv paper, read off the url and target link of its shown
# posts only (a count-only post's link stays a count); tracker samples of its topics are "related in topic", never its substance
REPO_URL = re.compile(r'^https?://(?:www\.)?github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))/([A-Za-z0-9_.-]+)', re.I)
GH_PAGES = {'about', 'apps', 'blog', 'collections', 'contact', 'customer-stories', 'enterprise', 'events', 'explore', 'features', 'join',
            'login', 'marketplace', 'new', 'notifications', 'orgs', 'pricing', 'readme', 'resources', 'search', 'security', 'settings',
            'site', 'solutions', 'sponsors', 'team', 'topics', 'trending'}
PAPER_URL = re.compile(r'^https?://(?:www\.)?(?:arxiv\.org/(?:abs|pdf|html)|huggingface\.co/papers|alphaxiv\.org/abs)/(\d{4}\.\d{4,5})(?!\d)', re.I)

def own_refs(urls):
    """{'repos': [...], 'papers': [...]}: canonical GitHub repository and arXiv abstract URLs among a story's own links, sorted."""
    repos, papers = {}, set()
    for u in urls:
        if not u or not public_url(u): continue
        m = REPO_URL.match(u)
        if m and m[1].lower() not in GH_PAGES:
            name = re.sub(r'\.git$', '', m[2])
            if name and name not in ('.', '..'): repos.setdefault(f'{m[1]}/{name}'.lower(), f'https://github.com/{m[1]}/{name}')
        m = PAPER_URL.match(u)
        if m: papers.add(f'https://arxiv.org/abs/{m[1]}')
    return {'repos': [repos[k] for k in sorted(repos)], 'papers': sorted(papers)}

def stories(rel, limit=60, links=frozenset()):
    """Cluster the last 7 days into events. Seeds: HN, Lobsters, newsletter and official items, joined when they share
    a canonical target link or most of their idf-weighted title words. Reddit, Mastodon and Bluesky posts attach to the
    best-matching seed; chatter that matches no seed forms its own story only with >= 5 voices on it.
    A newsletter whose body names a story's key words carries it. Ids hash a canonical URL: stable across runs."""
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
        key = sorted((w for w, k in cnt.items() if k >= max(1, len(ed) / 2) and df[w] < N * 0.02), key=lambda w: (-idf[w], w))[:3]
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
            return (junk, mode(t) != 'say', not (named and d[0]['net'] in SEED_NETS), not named, rank.get(d[0]['net'], 9), -(d[0]['score'] or 0), d[1])
        head = min(c, key=hk)
        path, got = [], set()
        for d in c:
            k = d[0]['author'] if d[0]['net'] in DIGEST else d[0]['net']
            if k in got: continue
            got.add(k); path.append(public({'net': d[0]['net'], 'who': d[0]['author'] if d[0]['net'] in DIGEST | OFFICIAL else None, 'at': iso(d[1]), 'url': link_url(d[0], links)}, links, hidden(d[0], links)))
        tags = {}
        for d in c:
            for tid in d[2]: tags[tid] = tags.get(tid, 0) + 1
        top_t = max(tags, key=tags.get) if tags else None
        headline, url, link = headline_of(head, c, label or next((x[top_t]['label'] for _, _, x, _ in c if top_t in x), None), links)
        hn = max([d[0]['score'] or 0 for d in c if d[0]['net'] == 'HN'] or [0])
        age_h = (NOW - c[-1][1]).total_seconds() / 3600
        spread = (2 * math.log2(1 + len(voices)) + len([n for n in nets if n not in DIGEST | OFFICIAL]) + 1.5 * len(nl)
                  + (1 if 'Official' in nets else 0) + math.log10(1 + hn))
        e0 = ed[0]                                            # earliest editorial post (members are in time order)
        alt = canon((e0[0].get('extra') or {}).get('link')) or e0[0]['url'] or f"{e0[0]['net']}:{e0[0]['pid']}"
        cid = ('release:' + top_a) if top_a else alt
        covered = bool(set(nets) & SEED_NETS) or bool(nl)
        pain = sum(1 for d in c if mode(shown(d[0])) == 'pain') / len(c)
        kind = 'news' if covered else 'pain' if pain >= 0.5 else 'chatter'
        out.append({'id': cid, '_alt': alt, '_e0': iso(e0[1]), 'label': label, 'covered': covered, 'kind': kind, 'pain': round(pain, 2),
                    'headline': headline, 'url': url, 'link': link, 'first': iso(c[0][1]), 'last': iso(c[-1][1]),
                    'voices': len(voices), 'nets': nets, 'newsletters': sorted(nl), 'official': 'Official' in nets, 'hn_points': hn or None,
                    'key': key, 'path': path[:8], 'tags': [t for t, _ in sorted(tags.items(), key=lambda x: -x[1])[:5]],
                    'heat': round(spread * 0.5 ** (age_h / 48), 3),
                    'refs': own_refs([u for d in c if not hidden(d[0], links) for u in (d[0]['url'], (d[0].get('extra') or {}).get('link'))]),
                    'posts': [public({'net': d[0]['net'], 'title': shown(d[0])[:200], 'url': link_url(d[0], links), 'author': d[0]['author'], 'at': iso(d[1]),
                                      'score': d[0]['score'], 'comments': d[0]['comments']}, links, False)
                              for d in sorted(c, key=lambda d: -(d[0]['score'] or 0)) if not hidden(d[0], links)][:10]})
    # one id per story: when two clusters name the same release, the one whose earliest editorial post is earliest (then the lower
    # fallback key) keeps "release:<topic>": later posts do not move it, so the two ids do not swap as a story grows. Every
    # other takes its earliest editorial post's key, as a story about no named release does; a key still taken gets '#' appended
    taken = set()
    for x in sorted(out, key=lambda x: (not x['id'].startswith('release:'), x['_e0'], x['_alt'])):
        k = x['id'] if x['id'] not in taken else x['_alt']
        while k in taken: k += '#'
        taken.add(k)
        x['id'] = 's:' + hashlib.sha1(k.encode()).hexdigest()[:12]
        del x['_alt'], x['_e0']
    out.sort(key=lambda x: -x['heat'])
    return ([x for x in out if x['kind'] == 'news'][:limit] + [x for x in out if x['kind'] == 'chatter'][:limit // 2]
            + [x for x in out if x['kind'] == 'pain'][:limit // 3])

STORY_METHOD = ('stories (last 7 days): an event is a cluster of posts. HN, Lobsters, newsletter and official items seed clusters and join when they share a '
                'canonical target link or idf-weighted title overlap >= 0.45 with two shared uncommon words (each in < 2% of the window\'s posts); '
                'posts naming the same model version or emerging name join one story; Reddit, Mastodon and Bluesky posts attach to their release or the best seed at >= 0.40; unmatched chatter joins at >= 0.55 and stands alone only with 5+ voices. '
                'covered = seeded by HN, Lobsters, a newsletter or a lab/vendor feed, or carried by a newsletter; otherwise it is chatter not yet in the press. '
                'pain = share of its post titles that read as a complaint, outage or support problem (keyword list); kind = news when covered, '
                'else pain when pain >= 0.5, else chatter. Headlines prefer statements over questions and complaints. '
                'A newsletter carries a story when its item names all of the story\'s key words (up to three uncommon words shared by its editorial posts). '
                'heat = (2 x log2(1 + voices) + networks outside newsletters/official + 1.5 x newsletters carrying it + 1 if a lab or vendor posted it + log10(1 + HN points)) '
                'x 0.5^(hours since the newest post / 48). id = "s:" + first 12 hex of sha1("release:" + topic id when the story is about one named release, '
                'else the canonical target link of its earliest editorial post, else that post\'s URL); when two stories name the same release, the one whose '
                'earliest editorial post is earliest (then the lower key) keeps the release key and the other takes its earliest editorial post\'s key, '
                'with "#" appended while that key is still taken, so ids are unique and do not swap as posts arrive. '
                'Reddit, X, LinkedIn, YouTube and Telegram posts (and Mastodon posts without a logged-out render check passed in the last 7 days) count but are never shown: no title, '
                'author, link or score; a headline that would be one reads the earliest shown post\'s title, else the topic label, '
                'else "<network> discussion, title not shown". Conversation-network authors are never published. '
                'refs = the GitHub repositories and arXiv papers (arxiv.org, huggingface.co/papers, alphaxiv.org ids) that the story\'s shown posts link to, by post URL or target link; '
                'a count-only post\'s link is not read')

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

def mastodon_candidates(posts, lex, hype_items, repos):
    """The live Mastodon ids the outputs would show if every one passed its render check, newest first: built once with every
    such post linked, then read off the output (the check runs on these; history/, so never published)."""
    nodes, _, _, _, extras = build(posts, lex, hype_items, repos, links=EVERY)
    return sorted(set(STATUS_URL.findall(json.dumps([nodes, extras['stories']]))), key=int, reverse=True)

# ------------------------------------------------------------------ removal requests and the deleted-post recheck (design row 7, C34)
# The fetchers are search and timeline queries that never report a deletion, so each live run looks up by id, under one time cap,
# every recheckable post the outputs could show (stored posts of the last RECHECK_DAYS) and every dossier post that keeps a source id
# (its HN posts): HN through the Firebase item endpoint (deleted or dead), Mastodon through mastodon.social /api/v1/statuses/<id> (a 404
# is removed; a 404 the render check recorded in web/checks/mastodon-links.json counts too, Decision 12), Bluesky through
# app.bsky.feed.getPosts (a URI missing from the answer is removed) and Reddit through arctic-shift by id ([deleted] or [removed]; Reddit
# is counts only, so such a record leaves the counts). A post found gone is deleted from the history DB and, when a dossier post has its
# URL, the URL's SHA256 is appended to web/checks/dossier-gone.json (hashes only), which internal_posts() and hype_build.py --scrub apply.
# Fail-closed: a recheckable post the lookup did not reach (time cap, rate budget, network error) shows as a count. --offline makes no
# call, so every recheckable post is a count; --relink reuses the result its own refresh run recorded (history/recheck.json, private).
# web/removals.json (owner-reviewed) names posts by the SHA256 of their URL as stored; a named post leaves the outputs and the DB.
RECHECK_CAP = 180              # seconds, inside C12's 15-minute margin beside the Mastodon check (install 3 + check 4 minutes)
RECHECK_DAYS = 30              # the widest window an output shows
RELINK_HOURS = 2               # --relink reuses a recheck at most this old: the live pulse.py of the same refresh run
MASTO_RESERVE = 120            # own Mastodon lookups stop while this many of the IP's API calls are left (the render check spends them)
REQ_SECONDS = 10               # one lookup's timeout, never past the cap
HN_ITEM = re.compile(r'^https://news\.ycombinator\.com/item\?id=(\d{1,12})$')
SHA_HEX = re.compile(r'[0-9a-f]{64}')

def url_hash(u): return hashlib.sha256(u.encode('utf-8')).hexdigest()

def post_hashes(p):
    """The hashes a removal entry may name a post by: its URL as stored, and for a live Mastodon post its handle-free link too."""
    out = {url_hash(p['url'])} if p.get('url') else set()
    if p['net'] == 'Mastodon' and p.get('source') == 'live' and re.fullmatch(r'\d{1,20}', str(p.get('pid') or '')):
        out.add(url_hash(f"https://mastodon.social/statuses/{p['pid']}"))
    return out

def removal_lists(web=None):
    """(hashes web/removals.json names, [entries] of web/checks/dossier-gone.json). A missing file names nothing; an unreadable one
    raises, so a run never publishes what a list it cannot read may name."""
    web = web or WEB
    try: R = json.load(open(os.path.join(web, 'removals.json')))['entries']
    except FileNotFoundError: R = []
    try: G = json.load(open(os.path.join(web, 'checks', 'dossier-gone.json')))['gone']
    except FileNotFoundError: G = []
    return {e['sha256'] for e in R if SHA_HEX.fullmatch(str(e.get('sha256')))}, G

def write_gone(entries, web=None):
    path = os.path.join(web or WEB, 'checks', 'dossier-gone.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump({'note': 'Bot-written, append-only: the SHA256 of the URL (as stored in web/hype.json) of each dossier post the deleted-post '
                           'recheck found deleted or removed at its source (pulse.py); internal_posts() and hype_build.py --scrub drop such a post.',
                   'gone': entries}, f, separators=(',', ':'), ensure_ascii=False)

def recheck_key(p):
    """'<network>:<source id>' the recheck looks a post up by, or None. A stored HN post and its dossier copy share one key."""
    pid = str(p.get('pid') or '')
    if p['net'] == 'HN' and HN_ITEM.match(p.get('url') or ''): return 'HN:' + HN_ITEM.match(p['url'])[1]
    if p.get('source') != 'live': return None
    if p['net'] == 'Mastodon' and re.fullmatch(r'\d{1,20}', pid): return 'Mastodon:' + pid
    if p['net'] == 'Bluesky' and pid.startswith('at://'): return 'Bluesky:' + pid
    if p['net'] == 'Reddit' and re.fullmatch(r'(?:t3_)?[0-9a-z]{1,13}', pid): return 'Reddit:' + pid.removeprefix('t3_')
    return None

def due_for_recheck(p):
    if not recheck_key(p): return False
    if p.get('source') == 'dossier': return True                     # the Hype page shows every dossier post, whatever its date
    dt = parse_dt(p.get('created'))
    return bool(dt) and dt >= NOW - timedelta(days=RECHECK_DAYS)

def get_json(url, timeout):
    """One GET, no retry (the cap bounds the recheck): (HTTP status, parsed body or None, headers). A network error raises."""
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read().decode('utf-8')), r.headers
    except urllib.error.HTTPError as e: return e.code, None, e.headers
GET = get_json

def _left(deadline): return deadline - time.monotonic()
def _wait(deadline): return min(REQ_SECONDS, max(0.5, _left(deadline)))

def _each(ids, one, workers):
    """{id: state} of one(id) over ids, in order, with workers threads; a lookup that raises or returns None did not reach."""
    def safe(i):
        try: return one(i)
        except Exception: return None
    with ThreadPoolExecutor(workers) as ex: return {i: r for i, r in zip(ids, ex.map(safe, ids)) if r}

def hn_lookup(ids, deadline):
    def one(i):
        if _left(deadline) <= 0: return None
        st, d, _ = GET(f'https://hacker-news.firebaseio.com/v0/item/{i}.json', _wait(deadline))
        if st != 200 or not isinstance(d, dict): return None
        return 'gone' if d.get('deleted') or d.get('dead') else 'alive'
    return _each(ids, one, 16)

def masto_lookup(ids, deadline):
    left = [None]                                      # the IP's API calls left, from the last answer
    def one(i):
        if _left(deadline) <= 0 or (left[0] is not None and left[0] < MASTO_RESERVE): return None
        st, _, h = GET(f'https://mastodon.social/api/v1/statuses/{i}', _wait(deadline))
        rem = (h or {}).get('X-RateLimit-Remaining')
        if st == 429: left[0] = 0
        elif str(rem or '').isdigit(): left[0] = int(rem)
        return 'alive' if st == 200 else 'gone' if st == 404 else None
    return _each(ids, one, 2)

def _batches(ids, n, deadline, url, read):
    out = {}
    for k in range(0, len(ids), n):
        if _left(deadline) <= 0: break
        batch = ids[k:k + n]
        try: st, d, _ = GET(url(batch), _wait(deadline))
        except Exception: continue
        if st == 200 and isinstance(d, dict): out.update(read(batch, d))
    return out

def bsky_lookup(uris, deadline):
    def read(batch, d):
        if not isinstance(d.get('posts'), list): return {}
        got = {p.get('uri') for p in d['posts'] if isinstance(p, dict)}
        return {u: 'alive' if u in got else 'gone' for u in batch}
    return _batches(uris, 25, deadline, lambda b: 'https://public.api.bsky.app/xrpc/app.bsky.feed.getPosts?'
                    + urllib.parse.urlencode([('uris', u) for u in b]), read)

def reddit_lookup(ids, deadline):
    def read(batch, d):
        gone = lambda x: x.get('author') == '[deleted]' or x.get('selftext') in ('[deleted]', '[removed]')
        return {x['id']: 'gone' if gone(x) else 'alive' for x in d.get('data') or [] if isinstance(x, dict) and x.get('id') in batch}
    return _batches(ids, 250, deadline, lambda b: 'https://arctic-shift.photon-reddit.com/api/posts/ids?'
                    + urllib.parse.urlencode({'ids': ','.join(b), 'fields': 'id,author,selftext'}), read)

LOOKUPS = {'HN': hn_lookup, 'Mastodon': masto_lookup, 'Bluesky': bsky_lookup, 'Reddit': reddit_lookup}

def recheck(posts, first=(), last=None, cap=None):
    """Look up every due post by id, the four networks side by side under one time cap -> ({key: 'alive' | 'gone'}, {network: ids asked}).
    first: Mastodon ids asked before the rest (those the day's outputs link); last: {key: time} of earlier Mastodon lookups, so the
    rest rotate (never asked first, then the oldest answer); the rate budget rarely reaches every Mastodon count in one run."""
    ids = {}
    for p in posts:
        if due_for_recheck(p): n, i = recheck_key(p).split(':', 1); ids.setdefault(n, set()).add(i)
    order = {n: sorted(v) for n, v in ids.items()}
    if 'HN' in order: order['HN'].sort(key=int, reverse=True)
    if 'Mastodon' in order:
        order['Mastodon'].sort(key=lambda i: (i not in first, (last or {}).get('Mastodon:' + i, ''), -int(i)))
    deadline = time.monotonic() + (RECHECK_CAP if cap is None else cap)
    res = {}
    with ThreadPoolExecutor(max(1, len(order))) as ex:
        futs = {n: ex.submit(LOOKUPS[n], order[n], deadline) for n in order}
        for n, f in futs.items():
            try: res.update({f'{n}:{i}': s for i, s in f.result().items()})
            except Exception: pass                                         # a failed lookup reaches nothing: its posts stay counts
    return res, {n: len(v) for n, v in order.items()}

def load_recheck(path=None):
    try: S = json.load(open(path or os.path.join(HIST, 'recheck.json')))
    except (OSError, ValueError): S = {}
    return {'gone': S.get('gone') or {}, 'last': S.get('last') or {}, 'run': S.get('run')}

def apply_removals(con, stored, internal, posts, want, links, cache, state, mode, gone_list):
    """The recheck and both lists over the pooled posts (mutates state and the DB) -> (posts to build from, run-log line, the run record).
    mode: 'live' (looks up), 'relink' (this run's recorded result) or 'offline' (no call)."""
    t0, res, run = time.monotonic(), {}, None
    due = [p for p in posts if due_for_recheck(p)]
    if mode == 'live':
        res, asked = recheck(due, first=set(want) & set(links), last=state['last'])
        run = {'at': iso(NOW), 'cap_seconds': RECHECK_CAP, 'asked': asked, 'results': res}
        state['run'] = run
        for k in res:
            if k.startswith('Mastodon:'): state['last'][k] = iso(NOW)
    elif mode == 'relink' and state['run'] and timedelta(0) <= NOW - (parse_dt(state['run'].get('at')) or NOW + timedelta(1)) <= timedelta(hours=RELINK_HOURS):
        run, res = state['run'], dict(state['run'].get('results') or {})
    for sid, e in cache.items():                                         # the render check's lookups of the same endpoint (Decision 12)
        if not isinstance(e, dict) or e.get('api_status') not in (200, 404): continue
        k, seen = 'Mastodon:' + sid, 'alive' if e['api_status'] == 200 else 'gone'
        if run and mode == 'relink' and str(e.get('checked_at') or '') >= run['at']: res[k] = seen     # looked up in this run, after the recheck
        elif seen == 'gone': res.setdefault(k, 'gone')                                                 # a recorded 404 removes, never revives
    gone = {k for k, s in res.items() if s == 'gone'} | set(state['gone'])
    in_db = {id(p) for p in stored}
    dead = [p for p in posts if recheck_key(p) in gone]
    forget(con, [p for p in dead if id(p) in in_db])
    dossier = {p['url'] for p in internal if p.get('source') == 'dossier' and p.get('url')}
    have = {e.get('sha256') for e in gone_list}
    new = sorted({url_hash(p['url']) for p in dead if p.get('url') in dossier} - have)
    if new: write_gone(gone_list + [{'sha256': h, 'found': iso(NOW)[:10]} for h in new])
    for k in gone: state['gone'].setdefault(k, iso(NOW)[:10])
    keep = [p for p in posts if recheck_key(p) not in gone]
    unreached = 0
    for p in keep:
        if due_for_recheck(p) and res.get(recheck_key(p)) != 'alive': p['unreached'] = True; unreached += 1
    by = {}
    for p in dead: by[p['net']] = by.get(p['net'], 0) + 1
    how = {'live': f'time cap {RECHECK_CAP}s, {round(time.monotonic() - t0)}s', 'relink': f"this run's recheck of {run['at']}, time cap {run['cap_seconds']}s" if run else
           'no recheck of this run found: no call', 'offline': 'offline: no call'}[mode]
    line = (f'recheck: {len(due)} due, {sum(1 for p in due if res.get(recheck_key(p)) == "alive")} reached and present, removed {len(dead)} '
            f'found gone {dict(sorted(by.items()))} ({len(new)} dossier hashes appended), {unreached} unreached shown as counts ({how})')
    return keep, line, run

def forget(con, posts):
    for p in posts: con.execute('DELETE FROM signals WHERE net = ? AND pid = ?', (p['net'], p['pid']))
    con.commit()

def save_recheck(state, posts, path=None):
    keys = {recheck_key(p) for p in posts}
    lo = iso(NOW - timedelta(days=RETAIN_DAYS))[:10]
    out = {'note': 'private (history/, never published): the deleted-post recheck by id; gone keys stay out of every later run',
           'gone': {k: d for k, d in sorted(state['gone'].items()) if d >= lo},
           'last': {k: t for k, t in sorted(state['last'].items()) if k in keys}, 'run': state['run']}
    os.makedirs(HIST, exist_ok=True)
    with open(path or os.path.join(HIST, 'recheck.json'), 'w') as f: json.dump(out, f, separators=(',', ':'))

# ------------------------------------------------------------------ briefing: evidence records, Top 10 and gauge values (web/briefing.json)
BRIEFING_VERSION = 'briefing/1'
BRT = timezone(timedelta(hours=-3), 'BRT')            # America/Sao_Paulo: UTC-3 all year since 2019 (no DST); fixed, so no tzdata is needed
PREVIEW, NOT_FETCHED, RELATED, NEW_TODAY, NO_SOURCE = 'preview, not yet reproducible', 'not fetched', 'related in topic', 'new today', 'no qualified source'
TREND_DAYS = 14                                       # no trend line or day-over-day arrow before 14 ledger days (R2-4)
AREA_DAYS, MOVERS, RELATED_MAX = 7, 5, 3
CONFIG_FILES = ('topics_lexicon.json', 'newsletters.json', 'official_feeds.json')
NET_ADAPTERS = {'HN': ('Hacker News (Algolia)',), 'Lobsters': ('Lobsters (ai tag)',), 'Mastodon': ('Mastodon (mastodon.social tags)',),
                'Reddit': ('Reddit (arctic-shift archive)', 'Reddit (official API)'), 'Bluesky': ('Bluesky (app password)',),
                'Newsletter': ('Newsletters (RSS)',), 'Official': ('Official feeds (RSS)',)}
SPREAD_NETS = ('HN', 'Lobsters', 'Mastodon', 'Reddit', 'Bluesky')     # posts per network; newsletters and the official post are read apart
TOP10_METHOD = ('Top 10 (new today first): the covered news stories (kind news) with a post in the 24 hours ending at the window end '
                '(pulse.py NOW, printed in BRT, UTC-3). First the stories first seen in that window (first seen = the earliest post in our sample), '
                'by heat; then the rest by heat, up to 10 in all. Ties break by the newest post (later first), then by stable id (ascending). '
                'Each row reads "new today" or "first seen <date>" (BRT date); every other story of the day keeps the same evidence record')
RECORD_METHOD = ('evidence record (one per story; state proposed: the pipeline proposes no verdict and writes no label word, the owner confirms by PR): '
                 'the stable story id, the computed fields it was built from (voices, posts per network, newsletters carrying it, official post, '
                 'HN points, heat, complaint share, key words, topics), the status of each source, the method version and the config hash '
                 '(first 16 hex of sha256 over the version, the method text and the sha256 of topics_lexicon.json, newsletters.json and official_feeds.json). '
                 'A network is fetched when one of its adapters read ok, partial when one read partial, else not fetched. A count reads "not fetched", '
                 'never 0 or false, when no post of it was seen and its source was not fully fetched; official reads true when a lab or vendor feed posted '
                 'the story and false only when the official feeds were fully fetched. Substance is the story\'s own links (its refs: GitHub repositories '
                 'and arXiv papers its shown posts link to) and its official post; tracker samples of its topics read "related in topic" and never count as substance')
GAUGE_METHOD = ('gauges (at most four; each reads "preview, not yet reproducible" until 14 ledger days, a green recompute verifier and the owner\'s confirm; '
                'no trend line or arrow before 14 ledger days; no combined score). "Releases / research output by area" = papers published and repos '
                'created on the 7 UTC dates ending with the window end\'s, per tracker area, among the papers and repos in data.json (output volume, '
                'not capability); null when the tracker was not read in this run or its data is older than the window. "Hype vs substance" = for each '
                'Top 10 story its spread (voices, posts per network, newsletters, HN points) beside its substance (official post, own repo and paper links), '
                'components only, no ratio; null with no Top 10 story. "Daily movers" = the five topics whose rising ratio (conversation posts in the last '
                'day / daily average over 7 days; it needs 4+ conversation posts in 7 days and 2+ in the last day) is highest above 1 (up) and the five '
                'lowest below 1 (down), with all-network posts in 1 and 7 days for context; null when no topic has a reading or no conversation network '
                'was fetched. Below its floor a gauge is null with the reason; no value carries over from an earlier run. Coverage is the status of the '
                'sources a gauge reads. Risk (a dated, sourced event log, no dial) and Jobs read "no qualified source" until a qualified source exists')

def net_status(sources):
    """Per network: 'ok' when one of its adapters read ok, else 'partial' when one read partial, else 'not fetched'."""
    out = {}
    for net, ads in NET_ADAPTERS.items():
        st = [(sources.get(a) or {}).get('status') for a in ads]
        out[net] = 'ok' if 'ok' in st else 'partial' if 'partial' in st else NOT_FETCHED
    return out

def reading(n, status):
    """A count read from one source: the count when posts were seen, 0 only when the source was fully fetched, else 'not fetched'."""
    return n if n else 0 if status == 'ok' else NOT_FETCHED

def official_reading(s, st):
    return True if s['official'] else False if st['Official'] == 'ok' else NOT_FETCHED

def seen_reading(first, lo):
    dt = parse_dt(first)
    return NEW_TODAY if dt >= lo else 'first seen ' + dt.astimezone(BRT).date().isoformat()

def top10(stories_, now):
    """R6-1 rows: covered news stories with a post in the 24h ending at now; those first seen in that window first, by heat,
    then the rest by heat, up to 10; ties by the newest post, then by stable id."""
    lo = now - timedelta(days=1)
    live = [s for s in stories_ if s['kind'] == 'news' and s['covered'] and parse_dt(s['last']) >= lo]
    live.sort(key=lambda s: (parse_dt(s['first']) < lo, -s['heat'], -parse_dt(s['last']).timestamp(), s['id']))
    return [{'rank': i + 1, 'id': s['id'], 'seen': seen_reading(s['first'], lo), 'heat': s['heat'], 'last': s['last']} for i, s in enumerate(live[:10])]

def ledger_days(path=None):
    """Days the ledger holds (web/ledger/index.json from group E1 on: a list of day entries, or {'entries': [...]}); 0 without one."""
    try: L = json.load(open(path or os.path.join(WEB, 'ledger', 'index.json')))
    except (OSError, ValueError): return 0
    L = L.get('entries') if isinstance(L, dict) else L
    return len(L) if isinstance(L, list) else 0

def config_hash(method):
    files = {}
    for name in CONFIG_FILES:
        try: files[name] = hashlib.sha256(open(os.path.join(BASE, name), 'rb').read()).hexdigest()
        except OSError: files[name] = None
    blob = json.dumps({'version': BRIEFING_VERSION, 'method': method, 'files': files}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()[:16]

def evidence(s, st, nodes, chash, lo):
    """One story's evidence record (design row 6, C7-C9)."""
    refs = s.get('refs') or {'repos': [], 'papers': []}
    off = official_reading(s, st)
    related, taken = [], set(refs['repos']) | set(refs['papers'])
    for tid in s['tags']:
        for x in (nodes.get(tid) or {}).get('samples', []):
            if len(related) >= RELATED_MAX: break
            if x.get('source') == 'tracker' and x.get('url') and x['url'] not in taken:
                taken.add(x['url']); related.append({'topic': tid, 'net': x['net'], 'title': x.get('title'), 'url': x['url']})
    return {'id': s['id'], 'state': 'proposed', 'method_version': BRIEFING_VERSION, 'config_hash': chash,
            'headline': s['headline'], 'kind': s['kind'], 'release': s['label'], 'first': s['first'], 'last': s['last'],
            'seen': seen_reading(s['first'], lo), 'sources': st,
            'computed': {'covered': s['covered'], 'voices': s['voices'],
                         'networks': {n: reading(s['nets'].get(n), st[n]) for n in SPREAD_NETS},
                         'newsletters': reading(len(s['newsletters']), st['Newsletter']), 'newsletter_names': s['newsletters'],
                         'official': off, 'hn_points': reading(s['hn_points'], st['HN']), 'heat': s['heat'], 'pain': s['pain'],
                         'key': s['key'], 'tags': s['tags']},
            'substance': {'from': "the story's own links", 'official': off, 'repos': refs['repos'], 'papers': refs['papers']},
            'related_in_topic': {'reading': RELATED, 'items': related}}

def gauge(gid, name, coverage, value, reason):
    return {'id': gid, 'name': name, 'status': PREVIEW, 'coverage': coverage, 'value': value,
            'reason': None if value is not None else 'insufficient data: ' + reason, 'trend': None}

def output_by_area(D, sources, now):
    name, tr = 'Releases / research output by area', (sources.get('Tracker (papers + repos)') or {}).get('status')
    cov = {'sources': {'Tracker (papers + repos)': tr or NOT_FETCHED}, 'window': f'{AREA_DAYS}d'}
    if not D or tr != 'ok': return gauge('output_by_area', name, cov, None, 'the tracker (papers + repos) was not read in this run')
    papers, repos = (D.get('papers') or {}).get('items') or {}, (D.get('repos') or {}).get('items') or {}
    cov.update({'data_generated_at': D.get('generated_at'), 'scoring_version': D.get('scoring_version'), 'config_sha': D.get('config_sha'),
                'papers_in_file': len(papers), 'repos_in_file': len(repos), 'tracked': D.get('tracked')})
    gen = parse_dt(D.get('generated_at'))
    if not gen or now - gen > timedelta(days=1): return gauge('output_by_area', name, cov, None, 'the tracker data is older than the 24h window')
    cut = (now - timedelta(days=AREA_DAYS - 1)).date().isoformat()                  # 7 UTC dates, the window end's included
    rows = [{'area': a, 'papers': sum(1 for p in papers.values() if p.get('tag') == a and (p.get('published') or '') >= cut),
             'repos': sum(1 for r in repos.values() if r.get('tag') == a and (r.get('created') or '') >= cut)}
            for a in D.get('views') or [] if a != 'all']
    return gauge('output_by_area', name, cov, {'since': cut, 'areas': rows}, '')

def hype_vs_substance(top, recs, st):
    cov = {'sources': st, 'stories': len(top)}
    if not top: return gauge('hype_vs_substance', 'Hype vs substance', cov, None, 'no covered news story had a post in the last 24h')
    rows = []
    for t in top:
        c, sub = recs[t['id']]['computed'], recs[t['id']]['substance']
        rows.append({'id': t['id'], 'hype': {'voices': c['voices'], 'networks': c['networks'], 'newsletters': c['newsletters'], 'hn_points': c['hn_points']},
                     'substance': {'official': sub['official'], 'repos': len(sub['repos']), 'papers': len(sub['papers'])}})
    return gauge('hype_vs_substance', 'Hype vs substance', cov, {'stories': rows}, '')

def daily_movers(nodes, st):
    conv = {n: st[n] for n in SPREAD_NETS}
    have = [x for x in nodes if x.get('rising') is not None]
    cov = {'sources': conv, 'topics_with_reading': len(have), 'topics': len(nodes)}
    if all(v == NOT_FETCHED for v in conv.values()): return gauge('daily_movers', 'Daily movers', cov, None, 'no conversation network was fetched')
    if not have: return gauge('daily_movers', 'Daily movers', cov, None, 'no topic had 4+ conversation posts in 7 days and 2+ in the last day')
    row = lambda x: {'topic': x['id'], 'label': x['label'], 'rising': x['rising'], 'posts_1d': x['w']['1d']['posts'], 'posts_7d': x['w']['7d']['posts']}
    up = sorted((x for x in have if x['rising'] > 1), key=lambda x: (-x['rising'], x['id']))[:MOVERS]
    down = sorted((x for x in have if x['rising'] < 1), key=lambda x: (x['rising'], x['id']))[:MOVERS]
    return gauge('daily_movers', 'Daily movers', cov, {'up': [row(x) for x in up], 'down': [row(x) for x in down]}, '')

def briefing(stories_, nodes, sources, D, now, method, days=0):
    """web/briefing.json: one evidence record per story, the Top 10 cut and the gauge header values (design rows 6, 8, 9).
    A pure function of the day's stories, topic nodes, source status and tracker data: the same inputs give the same bytes."""
    lo = now - timedelta(days=1)
    st = net_status(sources)
    chash = config_hash(' '.join((method, TOP10_METHOD, RECORD_METHOD, GAUGE_METHOD)))
    by_node = {x['id']: x for x in nodes}
    recs = [evidence(s, st, by_node, chash, lo) for s in stories_]
    top = top10(stories_, now)
    by_id = {r['id']: r for r in recs}
    return {'generated_at': iso(now),
            'window': {'start': iso(lo), 'end': iso(now), 'end_brt': now.astimezone(BRT).strftime('%Y-%m-%d %H:%M BRT'), 'hours': 24},
            'method': {'version': BRIEFING_VERSION, 'config_hash': chash, 'config_files': list(CONFIG_FILES),
                       'top10': TOP10_METHOD, 'records': RECORD_METHOD, 'gauges': GAUGE_METHOD},
            'ledger_days': days, 'sources': sources, 'top10': top, 'records': recs,
            'gauges': [output_by_area(D, sources, now), hype_vs_substance(top, by_id, st), daily_movers(nodes, st)],
            'panels': [{'id': 'risk', 'name': 'Risk', 'form': 'dated, sourced event log; no dial', 'events': [], 'reading': NO_SOURCE},
                       {'id': 'jobs', 'name': 'Jobs', 'form': 'panel', 'reading': NO_SOURCE}]}

# ------------------------------------------------------------------ story-id aliases (web/story-aliases.json; design row 7, C2, C32)
ALIAS_METHOD = ('story-id aliases (bot-written each run, apart from the owner-reviewed web/verdicts.json): the day\'s stories are compared with '
                'the previous pulse.json. A post is its network and its post time, never its link (a Mastodon link comes and goes with the render '
                'check, and pulse.json publishes no post id); newsletter issues are left out because one issue carries many stories. An earlier story maps to the story of the day that holds the most '
                'of its posts when that is at least half of them and more than the story under its own id still holds (a tie keeps no alias; '
                'among other stories the lower id wins). The map is cumulative: an old alias follows its target\'s move, an alias back to itself '
                'is dropped, and since = the BRT date the alias was first written. A verdict row resolves through an alias before a live story '
                'of the same id, because the alias names the story that took its posts')

def post_keys(s):
    """A story's posts by a stable identity: (network, post time), whether or not a link is shown (pulse.json carries no post id)."""
    return {(x.get('net'), x.get('at')) for x in (s.get('posts') or []) + (s.get('path') or [])
            if x.get('net') not in DIGEST}

def story_aliases(prev, today, old=None, day=''):
    """Old story id -> {to, since}. prev / today: story lists of the previous and the day's pulse.json; old: the previous alias map."""
    cur = [(s['id'], post_keys(s)) for s in today]
    held = dict(cur)
    moved = {}
    for s in prev:
        k = post_keys(s)
        if not k: continue
        own = len(k & held.get(s['id'], set()))
        hits = sorted(((len(k & kk), sid) for sid, kk in cur if sid != s['id'] and k & kk), key=lambda t: (-t[0], t[1]))
        if hits and hits[0][0] > own and 2 * hits[0][0] >= len(k): moved[s['id']] = hits[0][1]
    out = {}
    for a, e in sorted((old or {}).items()):
        to = moved.get(e.get('to'), e.get('to')) if isinstance(e, dict) else None
        if isinstance(to, str) and to != a: out[a] = {'to': to, 'since': e.get('since') or day}
    for a, to in sorted(moved.items()):
        if a in out: out[a]['to'] = to
        else: out[a] = {'to': to, 'since': day}
    return out

def write_aliases(prev_stories, today, now, path=None):
    """Write web/story-aliases.json from the previous pulse.json's stories (None: no readable previous file) and the day's."""
    path = path or os.path.join(WEB, 'story-aliases.json')
    try: old = json.load(open(path)).get('aliases') or {}
    except (OSError, ValueError, AttributeError): old = {}
    A = story_aliases(prev_stories or [], today, old, now.astimezone(BRT).date().isoformat())
    with open(path, 'w') as f:
        json.dump({'generated_at': iso(now), 'method': ALIAS_METHOD, 'aliases': A}, f, separators=(',', ':'), ensure_ascii=False, sort_keys=True)
    return A

def main():
    relink = '--relink' in sys.argv
    offline = '--offline' in sys.argv or relink
    lex = json.load(open(os.path.join(BASE, 'topics_lexicon.json')))
    EMERGING_STOP.update(x.lower() for x in lex.get('emerging_stop', []))
    try: hype_items = json.load(open(os.path.join(WEB, 'hype.json')))['items']
    except (OSError, KeyError, ValueError): hype_items = {}
    try: prev_pulse = json.load(open(os.path.join(WEB, 'pulse.json')))      # the previous run's file: feed status, story-id aliases
    except (OSError, ValueError): prev_pulse = None
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
            for k, v in prev_pulse.get('sources', {}).items():
                if k not in ('Tracker (papers + repos)', 'HYPE research dossier'):
                    SOURCES[k] = v if relink else {'status': v['status'], 'detail': v['detail'].split(' [as of last live run]')[0] + ' [as of last live run]'}
        except (AttributeError, KeyError): pass
        for k in ADAPTERS:
            SOURCES.setdefault(k, {'status': 'unknown', 'detail': 'not fetched in this offline rebuild'})
    stored = load_stored(con)
    removed, gone_list = removal_lists()                 # web/removals.json (owner-reviewed) and web/checks/dossier-gone.json (bot-written)
    named = [p for p in stored if post_hashes(p) & removed]
    forget(con, named)                                   # a removal-listed post leaves the history DB too
    stored = [p for p in stored if not post_hashes(p) & removed]
    internal = internal_posts(removed | {e.get('sha256') for e in gone_list})
    posts, repos = pool(stored, internal), tracker_repos()
    checks = os.path.join(WEB, 'checks', 'mastodon-links.json')
    links = load_links(checks)
    want = mastodon_candidates(posts, lex, hype_items, repos)
    state = load_recheck()
    posts, recheck_line, _ = apply_removals(con, stored, internal, posts, want, links, mastodon_cache(checks), state,
                                            'relink' if relink else 'offline' if offline else 'live', gone_list)
    save_recheck(state, posts)
    print(f'{recheck_line}; removals.json {len(removed)} entries ({len(named)} stored posts removed), dossier-gone.json '
          f'{len({e.get("sha256") for e in gone_list})} hashes before this run', flush=True)
    alive = {p['pid'] for p in posts if p['net'] == 'Mastodon'}
    want = [i for i in want if i in alive]
    os.makedirs(HIST, exist_ok=True)
    with open(CANDIDATES, 'w') as f: json.dump({'generated_at': iso(NOW), 'ids': want}, f)
    nodes, edges, totals, projects, extras = build(posts, lex, hype_items, repos, links=links)
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
                        'A node is only as strong as the posts behind it; posts from counts-only networks are counted, not shown.'],
           'stories': extras['stories'], 'nodes': nodes, 'edges': edges, 'projects': projects,
           'citations': {w: {'domains': c['domains']} for w, c in extras['citations'].items()},     # handles stay private (below)
           'official_feeds': official_meta()}
    try: D = json.load(open(os.path.join(WEB, 'data.json')))
    except (OSError, ValueError): D = None
    brief = briefing(extras['stories'], nodes, SOURCES, D, NOW, out['method'], ledger_days())
    for name, data in (('pulse.json', out), ('briefing.json', brief)):        # written together, so the pair always comes from one run
        with open(os.path.join(WEB, name), 'w') as f:
            json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
    # --relink rebuilds the same day's stories over this run's own pulse.json, so the aliases from the previous day's file stay as written
    aliases = None if relink else write_aliases(prev_pulse.get('stories') if isinstance(prev_pulse, dict) else None, extras['stories'], NOW)
    # X handles cited by newsletters are a ranking of (often pseudonymous) accounts: kept for the owner's review, never published
    with open(os.path.join(HIST, 'citations.json'), 'w') as f:
        json.dump({'generated_at': iso(NOW), 'note': 'private: X handles cited by newsletter items, a candidate follow list; not published',
                   'x_handles': {w: c['x_handles'] for w, c in extras['citations'].items()}}, f, ensure_ascii=False, indent=1)
    shown_ids = set(STATUS_URL.findall(json.dumps([nodes, extras['stories']])))
    print(f'pulse: {len(nodes)} topics, {len(edges)} links, 7d posts by network {totals["7d"]}; Mastodon render-check candidates {len(want)}, '
          f'linked {len(shown_ids)} (fresh passes in the cache {len(links)}); briefing: {len(brief["records"])} records, Top 10 '
          f'{sum(1 for t in brief["top10"] if t["seen"] == NEW_TODAY)} new today + {sum(1 for t in brief["top10"] if t["seen"] != NEW_TODAY)} heat fill, '
          f'window end {brief["window"]["end_brt"]}; story-id aliases ' + ('kept (relink)' if aliases is None else str(len(aliases))))

if __name__ == '__main__':
    main()
