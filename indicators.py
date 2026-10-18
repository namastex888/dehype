"""Context panels of the daily briefing (pulse.py): free, no-key public sources read once a day, inside pulse.py's live run.

  BLS public API v1 (no key)            a fixed list of US employment series (indicators.json bls.series): Jobs context
  HN Algolia "Who is hiring?" threads   the share of a month's hiring posts that name AI work: Jobs context
  Wikimedia pageviews REST API          7-day user views of a fixed list of AI articles on en and pt Wikipedia: page views, not awareness

fetch_all() makes the only network calls: the three sources in parallel, Wikipedia's articles one after another (the Wikimedia access
policy asks for sequential requests), every request capped by the time left of one shared budget (BUDGET seconds), no retry. Its result
is the stored input (history/indicators.json): BLS and Wikimedia responses as received, and for Hacker News only each thread's id, title,
date and two counts (no post text, no poster name). panels() is a pure function of that input and the run time: the same input gives
the same panels. A source that failed or was not fetched reads null with its reason, never 0, and no value carries over from an earlier
run. Standard library only.
"""
import os, re, json, html, time, urllib.request, urllib.parse, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE, 'indicators.json')
STORE = os.path.join(BASE, 'history', 'indicators.json')
BUDGET, REQ_SECONDS = 45.0, 15.0                      # all three sources together; one request
UA = 'dehype/1.0 (+https://github.com/namastex888/dehype; felipe@namastex.ai) python-urllib'
PREVIEW, NOT_FETCHED = 'preview, not yet reproducible', 'not fetched'
NAMES = {'bls': 'BLS (public API v1)', 'hn_hiring': 'Hacker News "Who is hiring?" (Algolia)', 'wikipedia': 'Wikipedia page views (Wikimedia REST)'}
BLS_NOTICE = 'BLS.gov cannot vouch for the data or analyses derived from these data'
CONTEXT_NOTE = 'context, not a forecast: general labour figures and hiring posts; none of them attributes a change to AI'
WINDOW_DAYS = 7

def config(path=CONFIG):
    with open(path, encoding='utf-8') as f: return json.load(f)

# ------------------------------------------------------------------ network (live run only)
def _http(url, deadline, data=None):
    left = deadline - time.monotonic()
    if left <= 0.5: raise TimeoutError('time budget spent')
    h = {'User-Agent': UA, 'Accept': 'application/json'}
    if data is not None: h['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=min(REQ_SECONDS, left)) as r: return json.loads(r.read().decode('utf-8'))

def fetch_bls(cfg, now, deadline, get=_http):
    year = now.year
    body = {'seriesid': [s['id'] for s in cfg['series']], 'startyear': str(year - 2), 'endyear': str(year)}   # in January the latest month's year-earlier is two years back
    d = get(cfg['endpoint'], deadline, json.dumps(body).encode('utf-8'))
    if d.get('status') != 'REQUEST_SUCCEEDED': raise RuntimeError(f"BLS status {d.get('status')}: {'; '.join(d.get('message') or [])[:120]}")
    return {'request': body, 'response': d}

def hiring_counts(item, cfg):
    """(top-level posts with text, those naming AI work) of one thread: the item tree's direct children are the job posts."""
    cs, ci = re.compile(cfg['terms_cs']), re.compile(cfg['terms_ci'], re.I)
    posts = [c for c in item.get('children') or [] if c.get('text') and c.get('parent_id') == item.get('id')]
    plain = lambda t: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', t)))
    return len(posts), sum(1 for c in posts if cs.search(plain(c['text'])) or ci.search(plain(c['text'])))

def fetch_hn_hiring(cfg, now, deadline, get=_http):
    q = cfg['endpoint'] + 'search_by_date?' + urllib.parse.urlencode({'tags': 'story,author_whoishiring', 'hitsPerPage': 12})
    hits = [h for h in get(q, deadline).get('hits') or [] if (h.get('title') or '').startswith(cfg['thread_title'])]
    hits.sort(key=lambda h: (h.get('created_at') or '', str(h.get('objectID'))), reverse=True)
    threads = []
    for h in hits[:cfg['months']]:
        n, ai = hiring_counts(get(cfg['endpoint'] + 'items/' + str(h['objectID']), deadline), cfg)
        threads.append({'id': int(h['objectID']), 'title': h['title'], 'created_at': h['created_at'], 'posts': n, 'ai_posts': ai})
    if not threads: raise RuntimeError('no "Who is hiring?" thread in the search result')
    return {'threads': threads}

def fetch_wikipedia(cfg, now, deadline, get=_http):
    end, start = (now - timedelta(days=1)).strftime('%Y%m%d'), (now - timedelta(days=21)).strftime('%Y%m%d')
    out = {'start': start, 'end': end, 'projects': {}}
    for proj, arts in cfg['projects'].items():
        got = out['projects'][proj] = {}
        for a in arts:                                                  # sequential, as the access policy asks
            u = f"{cfg['endpoint']}{proj}/{cfg['access']}/{cfg['agent']}/{urllib.parse.quote(a, safe='')}/daily/{start}/{end}"
            try: got[a] = {'items': [{'timestamp': x['timestamp'], 'views': x['views']} for x in get(u, deadline).get('items') or []]}
            except Exception as e: got[a] = {'error': f'{type(e).__name__}: {str(e)[:80]}'}
    return out

FETCHERS = {'bls': fetch_bls, 'hn_hiring': fetch_hn_hiring, 'wikipedia': fetch_wikipedia}

def fetch_all(now, cfg=None, get=_http, budget=BUDGET):
    """{fetched_at, inputs: {source: raw}, errors: {source: reason}}: the three sources in parallel under one time budget."""
    cfg = cfg or config()
    deadline = time.monotonic() + budget
    out = {'fetched_at': now.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'inputs': {}, 'errors': {}}
    with ThreadPoolExecutor(len(FETCHERS)) as ex:
        futs = {k: ex.submit(fn, cfg[k], now, deadline, get) for k, fn in FETCHERS.items()}
        for k, f in futs.items():
            try: out['inputs'][k] = f.result(timeout=max(0.1, deadline - time.monotonic() + 1))
            except Exception as e: out['errors'][k] = f'{type(e).__name__}: {str(e)[:100]}'
    return out

def save(raw, path=STORE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f: json.dump(raw, f, separators=(',', ':'), ensure_ascii=False)

def load(path=STORE):
    try:
        with open(path, encoding='utf-8') as f: return json.load(f)
    except (OSError, ValueError): return None

# ------------------------------------------------------------------ panels (pure)
def _status(n, total):
    return 'ok' if n == total and total else 'partial' if n else 'failed'

def _terms(c):
    return {'urls': list(c['terms']), 'read': c['terms_read']}

def _period(p):                                          # BLS "M09" of 2026 -> "2026-09"; annual averages (M13) are skipped
    return f"{p['year']}-{p['period'][1:]}" if re.fullmatch(r'M(0[1-9]|1[0-2])', p.get('period') or '') else None

def _num(v):
    try: return float(v.replace(',', '')) if isinstance(v, str) else None
    except ValueError: return None

def bls_item(cfg, raw, err, day):
    name = 'US employment in selected industries (BLS)'
    by = {s.get('seriesID'): s.get('data') or [] for s in ((raw or {}).get('response') or {}).get('Results', {}).get('series', [])} if raw else {}
    rows = []
    for s in cfg['series']:
        pts = [(_period(p), _num(p.get('value')), p) for p in by.get(s['id'], [])]
        pts = sorted([x for x in pts if x[0] and x[1] is not None], key=lambda x: x[0], reverse=True)
        if not pts:
            rows.append({'id': s['id'], 'name': s['name'], 'unit': s['unit'], 'period': None, 'value': None,
                         'reason': 'insufficient data: the series was not in the response'}); continue
        per, val, p = pts[0]
        ago = f'{int(per[:4]) - 1}{per[4:]}'
        prev = next((x for x in pts if x[0] == ago), None)
        rows.append({'id': s['id'], 'name': s['name'], 'unit': s['unit'], 'period': per, 'value': val,
                     'preliminary': any((f or {}).get('code') == 'P' for f in p.get('footnotes') or []),
                     'year_earlier': {'period': ago, 'value': prev[1] if prev else None}})
    n = sum(1 for r in rows if r['value'] is not None)
    st = NOT_FETCHED if not raw else _status(n, len(rows))
    cov = {'sources': {NAMES['bls']: st}, 'series_read': n if raw else NOT_FETCHED, 'series_listed': len(rows)}
    base = {'id': 'bls', 'name': name, 'status': PREVIEW, 'retrieved': day if raw else None, 'terms': _terms(cfg), 'coverage': cov}
    if not n:
        return dict(base, value=None, reason='insufficient data: ' + ('not fetched in this run' if not raw and not err else
                                                                     f'the source failed in this run ({err})' if err else 'no listed series was in the response'))
    return dict(base, value={'series': rows}, reason=None, notice=BLS_NOTICE)

MONTHS = 'January February March April May June July August September October November December'.split()

def _month(t):                                           # "Ask HN: Who is hiring? (October 2026)" -> "2026-10"
    m = re.search(r'\((\w+) (\d{4})\)', t['title'])
    if m and m.group(1) in MONTHS: return f'{m.group(2)}-{MONTHS.index(m.group(1)) + 1:02d}'
    return t['created_at'][:7]

def hn_item(cfg, raw, err, day):
    name = 'Hacker News "Who is hiring?" posts that mention AI'
    T = (raw or {}).get('threads') or []
    rows = [{'month': _month(t), 'thread': f"https://news.ycombinator.com/item?id={t['id']}", 'posts': t['posts'], 'ai_posts': t['ai_posts'],
             'share': round(t['ai_posts'] / t['posts'], 3) if t['posts'] else None} for t in T]
    read = [r for r in rows if r['posts']]
    st = NOT_FETCHED if not raw else _status(len(read), cfg['months'])
    cov = {'sources': {NAMES['hn_hiring']: st}, 'threads_read': len(read) if raw else NOT_FETCHED, 'threads_listed': cfg['months'],
           'counted': 'top-level posts with text (deleted posts left out); a month still open counts the posts so far'}
    base = {'id': 'hn_hiring', 'name': name, 'status': PREVIEW, 'retrieved': day if raw else None, 'terms': _terms(cfg), 'coverage': cov}
    if not read:
        return dict(base, value=None, reason='insufficient data: ' + ('not fetched in this run' if not raw and not err else
                                                                     f'the source failed in this run ({err})' if err else 'no hiring thread had a post'))
    return dict(base, value={'months': read}, reason=None)

def wiki_panel(cfg, raw, err, day):
    name = 'Page views on Wikipedia (AI articles)'
    projects, read_all = [], 0
    for proj, arts in cfg['projects'].items():
        got = ((raw or {}).get('projects') or {}).get(proj) or {}
        days = {a: {x['timestamp'][:8]: x['views'] for x in (got.get(a) or {}).get('items') or []} for a in arts if 'items' in (got.get(a) or {})}
        last = max((d for v in days.values() for d in v), default=None)
        row = {'project': proj, 'articles_listed': len(arts), 'articles_read': len(days) if raw else NOT_FETCHED}
        if last:
            end = datetime.strptime(last, '%Y%m%d')
            span = [(end - timedelta(days=i)).strftime('%Y%m%d') for i in range(2 * WINDOW_DAYS)]
            full = [a for a in arts if a in days and all(d in days[a] for d in span)]
            iso = lambda s: f'{s[:4]}-{s[4:6]}-{s[6:]}'
            row.update({'window': {'start': iso(span[WINDOW_DAYS - 1]), 'end': iso(span[0])},
                        'prior_window': {'start': iso(span[-1]), 'end': iso(span[WINDOW_DAYS])}, 'articles_complete': len(full)})
            if len(full) == len(arts):
                row.update({'views_7d': sum(days[a][d] for a in arts for d in span[:WINDOW_DAYS]),
                            'views_prior_7d': sum(days[a][d] for a in arts for d in span[WINDOW_DAYS:]),
                            'articles': [{'title': a, 'lang': proj.split('.')[0], 'views_7d': sum(days[a][d] for d in span[:WINDOW_DAYS])} for a in arts], 'reason': None})
                read_all += 1
            else:
                row.update({'views_7d': None, 'views_prior_7d': None,
                            'reason': f'insufficient data: {len(full)} of {len(arts)} articles had all {2 * WINDOW_DAYS} days in the response'})
        else:
            row.update({'views_7d': None, 'views_prior_7d': None, 'reason': 'insufficient data: ' + ('not fetched in this run' if not raw else 'no article was read')})
        projects.append(row)
    st = NOT_FETCHED if not raw else _status(read_all, len(projects))
    cov = {'sources': {NAMES['wikipedia']: st}, 'access': cfg['access'], 'agent': cfg['agent'],
           'projects_read': read_all if raw else NOT_FETCHED, 'projects_listed': len(projects)}
    base = {'id': 'pageviews', 'name': name, 'form': 'panel', 'status': PREVIEW, 'retrieved': day if raw else None, 'terms': _terms(cfg), 'coverage': cov}
    if not read_all:
        return dict(base, value=None, reason='insufficient data: ' + ('not fetched in this run' if not raw and not err else
                                                                     f'the source failed in this run ({err})' if err else 'no project had every article and day'))
    return dict(base, value={'projects': projects}, reason=None)

def panels(stored, cfg=None):
    """(jobs context items, page-views panel) from the stored input (None: not fetched in this run)."""
    cfg = cfg or config()
    I, E = (stored or {}).get('inputs') or {}, (stored or {}).get('errors') or {}
    day = (stored or {}).get('fetched_at', '')[:10] or None
    return ([bls_item(cfg['bls'], I.get('bls'), E.get('bls'), day), hn_item(cfg['hn_hiring'], I.get('hn_hiring'), E.get('hn_hiring'), day)],
            wiki_panel(cfg['wikipedia'], I.get('wikipedia'), E.get('wikipedia'), day))

def source_status(stored, cfg=None):
    """{source name: {status, detail}} for pulse.py's sources block, from one stored input."""
    cfg = cfg or config()
    ctx, wiki = panels(stored, cfg)
    E, out = (stored or {}).get('errors') or {}, {}
    for key, item in (('bls', ctx[0]), ('hn_hiring', ctx[1]), ('wikipedia', wiki)):
        st = item['coverage']['sources'][NAMES[key]]
        if key in E: out[NAMES[key]] = {'status': 'failed', 'detail': f'{E[key]} (not fetched; no earlier value shown)'}
        elif key not in ((stored or {}).get('inputs') or {}): out[NAMES[key]] = {'status': NOT_FETCHED, 'detail': 'not fetched in this run'}
        elif key == 'bls': out[NAMES[key]] = {'status': st, 'detail': f"{item['coverage']['series_read']} of {item['coverage']['series_listed']} series read"}
        elif key == 'hn_hiring': out[NAMES[key]] = {'status': st, 'detail': f"{item['coverage']['threads_read']} of {item['coverage']['threads_listed']} hiring threads read"}
        else:
            proj = (((stored or {}).get('inputs') or {}).get('wikipedia') or {}).get('projects') or {}
            arts, n = sum(1 for p in proj.values() for a in p.values() if 'items' in a), sum(len(v) for v in cfg['wikipedia']['projects'].values())
            out[NAMES[key]] = {'status': st, 'detail': f'{arts} of {n} articles read'}
    return out
