#!/usr/bin/env python3
"""Pulse: sampled AI conversation across networks -> topic graph (web/pulse.json).

Run:   python3 pulse.py              fetch live feeds, merge with web/data.json + web/hype.json, write web/pulse.json
       python3 pulse.py --offline    rebuild from stored signals only (no network)
Env:   REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT   enable the Reddit adapter (official OAuth API)
       BSKY_HANDLE, BSKY_APP_PASSWORD                               enable the Bluesky adapter (app password)
State: history/signals.sqlite keeps 45 days of normalised posts; it rides in the same Actions cache as run.py's history.

Networks are samples, never totals: Hacker News stories above a points floor, the Lobsters AI tag, a fixed set of Mastodon
hashtags, plus (when connected) chosen subreddits and Bluesky searches. X is not collected. Every topic node carries the
posts that matched it, so a node is never more than the evidence behind it. Standard library only.
"""
import os, sys, re, json, math, time, sqlite3, base64, html, urllib.request, urllib.parse, urllib.error
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

def post(net, pid, url, title, author, created, score=None, comments=None, source='live'):
    return {'net': net, 'pid': str(pid), 'url': url, 'title': re.sub(r'\s+', ' ', title or '').strip()[:400],
            'author': (author or '').strip()[:80], 'created': created, 'score': score, 'comments': comments, 'source': source}

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
                                      h.get('author'), h.get('created_at'), h.get('points'), h.get('num_comments'))
    return list(out.values())

def fetch_lobsters(pages=4):
    out = []
    for p in range(1, pages + 1):
        d = http('https://lobste.rs/t/ai.json' if p == 1 else f'https://lobste.rs/t/ai/page/{p}.json')
        for s in d:
            out.append(post('Lobsters', s['short_id'], s.get('comments_url') or s.get('url'), s.get('title'),
                            (s.get('submitter_user') or {}).get('username') if isinstance(s.get('submitter_user'), dict) else s.get('submitter_user'),
                            s.get('created_at'), s.get('score'), s.get('comment_count')))
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
                out.append(post('Mastodon', s['id'], s.get('url') or s.get('uri'), text[:280],
                                (s.get('account') or {}).get('acct'), s.get('created_at'),
                                (s.get('favourites_count') or 0) + (s.get('reblogs_count') or 0), s.get('replies_count')))
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
                                    p.get('score'), p.get('num_comments'))
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
                            p.get('score'), p.get('num_comments')))
    return out

def _rss_date(s):
    if not s: return None
    try: return iso(parsedate_to_datetime(s))
    except (TypeError, ValueError, IndexError):
        d = parse_dt(s)
        return iso(d) if d else None

def fetch_newsletters(days=30):
    """Public RSS/Atom feeds of AI newsletters listed in newsletters.json. An issue is one post on the 'Newsletter' network;
    its text (title + summary, HTML stripped, capped) is matched against topics, so the spread trace shows when a topic
    reached the digests. Only the item title, date and public link are published."""
    path = os.path.join(BASE, 'newsletters.json')
    if not os.path.exists(path): raise PermissionError('not configured (add feeds to newsletters.json)')
    cfg = json.load(open(path))
    out, failed, cutoff = [], [], NOW - timedelta(days=days)
    for nl in cfg['feeds']:
        try:
            req = urllib.request.Request(nl['url'], headers={'User-Agent': UA, 'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml'})
            with urllib.request.urlopen(req, timeout=30) as r: root = ET.fromstring(r.read())
        except Exception:
            failed.append(nl['name']); continue
        ns = {'a': 'http://www.w3.org/2005/Atom', 'c': 'http://purl.org/rss/1.0/modules/content/'}
        items = root.findall('.//item') or root.findall('.//a:entry', ns)
        for it in items[:60]:
            title = (it.findtext('title') or it.findtext('a:title', namespaces=ns) or '').strip()
            link = it.findtext('link') or ''
            if not link:
                le = it.find('a:link', ns); link = le.get('href') if le is not None else ''
            date = _rss_date(it.findtext('pubDate') or it.findtext('a:published', namespaces=ns) or it.findtext('a:updated', namespaces=ns))
            if not date or parse_dt(date) < cutoff: continue
            body = it.findtext('c:encoded', namespaces=ns) or it.findtext('description') or it.findtext('a:content', namespaces=ns) or it.findtext('a:summary', namespaces=ns) or ''
            text = (title + ' \u241f ' + strip_html(body))[:1500]          # U+241F separator: body kept for matching only
            out.append(post('Newsletter', link or f"{nl['name']}:{title}", link, text, nl['name'], date))
    if failed: PARTIAL['Newsletters (RSS)'] = 'unreachable: ' + ', '.join(failed)
    if failed and not out: raise ConnectionError(PARTIAL['Newsletters (RSS)'])
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
            out.append(post('Bluesky', p.get('uri'), f'https://bsky.app/profile/{a}/post/{rkey}',
                            (p.get('record') or {}).get('text', '')[:280], a, (p.get('record') or {}).get('createdAt'),
                            (p.get('likeCount') or 0) + (p.get('repostCount') or 0), p.get('replyCount')))
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

# ------------------------------------------------------------------ storage
def db():
    os.makedirs(HIST, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute('''CREATE TABLE IF NOT EXISTS signals(net TEXT, pid TEXT, url TEXT, title TEXT, author TEXT, created TEXT,
                   score INT, comments INT, source TEXT, fetched TEXT, PRIMARY KEY(net, pid))''')
    return con

def store(con, posts):
    for p in posts:
        con.execute('INSERT OR REPLACE INTO signals VALUES(?,?,?,?,?,?,?,?,?,?)',
                    (p['net'], p['pid'], p['url'], p['title'], p['author'], p['created'], p['score'], p['comments'], p['source'], iso(NOW)))
    con.execute('DELETE FROM signals WHERE created IS NULL OR created < ?', (iso(NOW - timedelta(days=RETAIN_DAYS)),))
    con.commit()

def load_stored(con):
    cols = ['net', 'pid', 'url', 'title', 'author', 'created', 'score', 'comments', 'source']
    return [dict(zip(cols, r)) for r in con.execute(f'SELECT {",".join(cols)} FROM signals')]

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

def compile_lexicon(lex, hype_items):
    topics = []
    def rx(aliases, case):
        alts = sorted({a for a in aliases if a}, key=len, reverse=True)
        if not alts: return None
        return re.compile(r'(?<![\w-])(?:' + '|'.join(re.escape(a).replace(r'\ ', r'[\s-]') for a in alts) + r')(?![\w-])',
                          0 if case else re.I)
    for t in lex['topics']:
        topics.append({'id': t['id'], 'label': t['label'], 'kind': t['kind'], 'parent': t.get('parent'),
                       'rx': rx(t.get('aliases', []), t.get('case', False))})
    ambiguous = set(lex.get('ambiguous_hype_names', []))
    for hid, it in hype_items.items():
        name = it.get('name') or hid
        if any(t['label'].lower() == name.lower() for t in topics): continue
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
    keep = [(ph, a) for ph, a in seen.items() if len(a) >= min_authors]
    keep.sort(key=lambda x: -len(x[1]))
    return [ph for ph, _ in keep[:limit]]

# ------------------------------------------------------------------ graph
def shown(p):
    """Display text: newsletters keep their body only for matching; the page shows the issue title."""
    t = p['title'] or ''
    return t.split('\u241f', 1)[0].strip() if p['net'] in DIGEST else t

def build(posts, lex, hype_items):
    topics, fams, vrx, kw = compile_lexicon(lex, hype_items)
    by_id = {t['id']: t for t in topics}
    rel = []
    for p in posts:
        dt = parse_dt(p['created'])
        if not dt or dt > NOW + timedelta(hours=1) or dt < NOW - timedelta(days=30): continue
        text = p['title'] or ''
        found = match_topics(text, topics, fams, vrx)
        # HN is general-interest: keep a story only if it names an AI model/product/version or uses an AI keyword
        if p['net'] == 'HN' and p['source'] == 'live' and not kw.search(text) and not any(t['kind'] in ('model', 'version', 'product') for t in found.values()): continue
        rel.append((p, dt, found))
    labels = {t['label'].lower() for t in topics} | {w.lower() for t in topics for w in t['label'].split()}
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

    nodes, edges = {}, {}
    def node(t):
        n = nodes.get(t['id'])
        if not n:
            n = nodes[t['id']] = {'id': t['id'], 'label': t['label'], 'kind': t['kind'], 'parent': t.get('parent'),
                                  'w': {w: {'posts': 0, 'authors': set(), 'nets': {}, 'eng': 0.0, 'conv': 0} for w in WINDOWS},
                                  'first': None, 'last': None, 'samples': [], 'origin': {}}
        return n
    for p, dt, found in rel:
        age = (NOW - dt).total_seconds() / 86400
        ids = sorted(found)
        for tid in ids:
            n = node(found[tid])
            for w, days in WINDOWS.items():
                if age <= days:
                    s = n['w'][w]; s['posts'] += 1; s['authors'].add((p['net'], p['author'])); s['nets'][p['net']] = s['nets'].get(p['net'], 0) + 1
                    s['eng'] += math.log1p(max(0, p['score'] or 0) + max(0, p['comments'] or 0))
                    if p['net'] in CONVERSATION and p['source'] == 'live': s['conv'] += 1
            n['first'] = min(n['first'] or p['created'], p['created']); n['last'] = max(n['last'] or p['created'], p['created'])
            n['samples'].append((math.log1p(max(0, p['score'] or 0)) - age / 30, p, dt))
            o = n['origin'].get(p['net'])
            if p['source'] != 'tracker' and (o is None or dt < o[0]): n['origin'][p['net']] = (dt, p)
        if p['net'] in DIGEST: continue                       # a digest lists many stories; co-mention there is not a link
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
            W[w] = {'posts': s['posts'], 'authors': len(s['authors']), 'nets': s['nets'], 'eng': round(s['eng'], 1),
                    'weight': round(len(s['authors']) * (1 + 0.5 * max(0, nets - 1)), 2)}
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
                          'first': (n['first'] or '')[:10], 'last': (n['last'] or '')[:10], 'samples': samples})
    out_nodes.sort(key=lambda x: -x['w']['30d']['weight'])
    out_nodes = [x for x in out_nodes if x['w']['30d']['posts'] >= 2][:160]
    keep = {x['id'] for x in out_nodes}
    out_edges = [{'a': a, 'b': b, 'w': w} for (a, b), w in edges.items() if a in keep and b in keep and (w['30d'] >= 2 or
                 any(x['id'] in (a, b) and x['parent'] in (a, b) for x in out_nodes))]
    totals = {w: {} for w in WINDOWS}
    for p, dt, _ in rel:
        age = (NOW - dt).total_seconds() / 86400
        for w, days in WINDOWS.items():
            if age <= days: totals[w][p['net']] = totals[w].get(p['net'], 0) + 1
    return out_nodes, out_edges, totals

ADAPTERS = ['Hacker News (Algolia)', 'Lobsters (ai tag)', 'Mastodon (mastodon.social tags)', 'Reddit (arctic-shift archive)',
            'Reddit (official API)', 'Bluesky (app password)', 'Newsletters (RSS)']

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
                         ('Bluesky (app password)', fetch_bluesky), ('Newsletters (RSS)', fetch_newsletters)):
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
    nodes, edges, totals = build(posts, lex, hype_items)
    out = {'generated_at': iso(NOW), 'windows': list(WINDOWS), 'sources': SOURCES, 'totals': totals,
           'method': 'weight = distinct authors x (1 + 0.5 x (networks - 1)); rising = conversation posts in the last day / daily average over 7 days',
           'coverage': ['Sampled feeds, not internet-wide totals: HN stories above 20 points, the Lobsters AI tag, nine Mastodon hashtags on mastodon.social, '
                        'ten AI subreddits via the arctic-shift public archive (up to 1,000 newest posts per subreddit per run, so busy subreddits reach back about a week), '
                        'eleven public AI newsletter feeds (the digest end point), tracker papers and repos, and the static HYPE research dossier. '
                        'Bluesky appears only when an app password is configured. X appears only through the static dossier; it is not collected live.',
                        'Topics come from a reviewable lexicon (topics_lexicon.json), automatic model-version names, and capitalised phrases used by at least three distinct authors (marked emerging).',
                        'A node is only as strong as the posts listed under it; open it to read them.'],
           'nodes': nodes, 'edges': edges}
    with open(os.path.join(WEB, 'pulse.json'), 'w') as f:
        json.dump(out, f, separators=(',', ':'), ensure_ascii=False)
    print(f'pulse: {len(nodes)} topics, {len(edges)} links, 7d posts by network {totals["7d"]}')

if __name__ == '__main__':
    main()
