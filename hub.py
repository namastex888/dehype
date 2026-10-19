"""Hugging Face Hub check of the daily briefing (pulse.py): for each story with a release name, the models of that name that the
listed organisations (hub_orgs.json, owner-reviewed) hold on the Hub.

fetch() makes the only network calls: one Hub model search per release name (https://huggingface.co/api/models, sorted by 30-day
downloads, the first 100 results), one after another under one time budget (BUDGET seconds), no retry; HF_TOKEN, when set, only raises
the rate limit. Its result is the stored input (history/hub.json): per name, the id, creation time, 30-day downloads and likes of the
results whose organisation is listed, and nothing else of the response. reading() is a pure function of that input and a name: the
same input gives the same reading. A name that was not searched, or whose search failed, reads "not fetched", never 0; a searched name
with no match under a listed organisation reads 0 models, which says nothing about whether the model is open elsewhere or closed.
Standard library only.
"""
import os, re, json, time, urllib.request, urllib.parse, urllib.error
from datetime import timezone

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE, 'hub_orgs.json')
STORE = os.path.join(BASE, 'history', 'hub.json')
BUDGET = 40
UA = 'dehype/1.0 (+https://github.com/namastex888/dehype; felipe@namastex.ai) python-urllib'
NAME = 'Hugging Face Hub (model search)'
NOT_FETCHED, NO_NAME = 'not fetched', 'no release name'
SEARCH_LIMIT, SHOWN = 100, 5
METHOD = ('Hub check: a story with a release name (its label) is searched once on the Hugging Face Hub (models, the 100 most downloaded '
          'in 30 days whose id matches the name); a model counts when its organisation is listed in hub_orgs.json (owner-reviewed: labs and '
          'vendors, never a person) and its name carries the release name\'s words and numbers in order, a version exactly (Qwen 3 is not '
          'Qwen3.8). The record carries the count among those 100 and the five most downloaded matches (id, created, downloads in the last 30 days, likes); '
          '"no release name" when the story has none, "not fetched" when the search did not run or failed; 0 models is a reading of the '
          'listed organisations only, not a verdict that a model is closed, and a name that is not a model reads 0 too')

def config(path=CONFIG):
    with open(path, encoding='utf-8') as f: return json.load(f)

def _http(url, deadline, token=None):
    left = deadline - time.monotonic()
    if left <= 0: raise TimeoutError('time budget spent')
    h = {'User-Agent': UA, 'Accept': 'application/json'}
    if token: h['Authorization'] = 'Bearer ' + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=min(20, left)) as r:
        return json.loads(r.read().decode('utf-8'))

def search_url(name):
    return 'https://huggingface.co/api/models?' + urllib.parse.urlencode(
        {'search': name, 'sort': 'downloads', 'direction': -1, 'limit': SEARCH_LIMIT})

def fetch(names, now, cfg=None, get=_http, budget=BUDGET, token=None):
    """{fetched_at, inputs: {name: [model]}, errors: {name: reason}}: one search per searchable name, in the order given (a spent
    budget cuts the last), under one time budget."""
    orgs = set((cfg or config())['orgs'])
    deadline = time.monotonic() + budget
    out = {'fetched_at': now.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'inputs': {}, 'errors': {}}
    for name in dict.fromkeys(n for n in names if name_rx(n)):          # in the order given (the most important first), once each
        try: res = get(search_url(name), deadline, token)
        except urllib.error.HTTPError as e: out['errors'][name] = f'HTTP {e.code}'; continue      # status only, never the body
        except Exception as e: out['errors'][name] = type(e).__name__; continue
        if not isinstance(res, list): out['errors'][name] = 'unexpected response'; continue    # never an invented 0
        out['inputs'][name] = [{'id': m['id'], 'created': m.get('createdAt'), 'downloads': m.get('downloads'), 'likes': m.get('likes')}
                               for m in res if isinstance(m, dict) and isinstance(m.get('id'), str) and m['id'].split('/')[0] in orgs]
    return out

def save(raw, path=STORE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f: json.dump(raw, f, separators=(',', ':'), ensure_ascii=False)

def load(path=STORE):
    try:
        with open(path, encoding='utf-8') as f: return json.load(f)
    except (OSError, ValueError): return None

# ------------------------------------------------------------------ reading (pure)
def name_rx(name):
    """The release name's words and numbers, in order, inside a model name: words may have other words between them and end where a
    word ends (spark is not sparkle), a number follows its word directly (a separator or a v between) and is matched whole (3 is not 3.8,
    35 or 3b: Gemma 2 is not gemma-2b); None for a name with no Latin letter or digit, which is not searched."""
    toks = re.findall(r'[a-z]+|\d+(?:\.\d+)*', (name or '').lower())
    if not toks: return None
    num = lambda t: t[0].isdigit()
    rx = '' if num(toks[0]) else r'(?<![a-z])'
    for i, t in enumerate(toks):
        if i: rx += r'[-_. ]*v?' if num(t) else r'[^/]*?'
        rx += (r'(?<![\d.])' if num(t) and not i else '') + re.escape(t) + (r'(?![a-z\d]|\.\d)' if num(t) else r'(?!(?!v\d)[a-z])')
    return re.compile(rx)

def reading(stored, name, cfg=None):
    """A record's Hub reading: {'n', 'models'} for a searched name, NO_NAME without a name, NOT_FETCHED when not searched or failed."""
    if not name: return NO_NAME
    found, rx = ((stored or {}).get('inputs') or {}).get(name), name_rx(name)
    if found is None or rx is None: return NOT_FETCHED
    orgs = (cfg or config())['orgs']
    hit = [m for m in found if m['id'].split('/')[0] in orgs and rx.search(m['id'].split('/', 1)[1].lower())]
    hit.sort(key=lambda m: (-(m.get('downloads') or 0), m['id']))
    return {'n': len(hit), 'models': [{'id': m['id'], 'org': orgs[m['id'].split('/')[0]]['fullname'], 'created': m.get('created'),
                                       'downloads_30d': m.get('downloads'), 'likes': m.get('likes')} for m in hit[:SHOWN]]}

def source_status(stored):
    """{NAME: {status, detail}} for pulse.py's sources block, from one stored input (None: not fetched in this run)."""
    if stored is None: return {NAME: {'status': NOT_FETCHED, 'detail': 'not fetched in this run'}}
    n, e = len(stored.get('inputs') or {}), len(stored.get('errors') or {})
    st = 'ok' if not e else 'partial' if n else 'failed'
    return {NAME: {'status': st, 'detail': f'{n} of {n + e} release names searched'}}       # a failed name reads "not fetched" on its record
