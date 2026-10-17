#!/usr/bin/env python3
"""HYPE tab builder: hype/hype_research.json -> web/hype.json (compact) + rank history.

Run standalone:  python3 hype_build.py [--no-history]
Scrub only:      python3 hype_build.py --scrub web/hype.json   (the public-data rules on the committed file; idempotent; also drops every
                 post that removals.json or checks/dossier-gone.json beside the file names: deletion-only, refresh.yml runs it daily)
Dossier fields:  python3 hype_build.py --dossier-fields web/hype.json   (slug, field path and SHA256 per prose field, for web/i18n/dossier.pt.json)
run.py calls build(con=..., run_id=...) automatically when hype/hype_research.json exists.

NEVER INVENTS NUMBERS. Unknown -> null (rendered '—'). All social counts are the research agent's
*sampled* observations (purposive, not exhaustive, no global counts).

Scoring is in scoring.py. Current method 3.0 separates sampled attention,
activity/discussion discovery proxies and source usage metric families.
Evidence coverage controls heuristic shrinkage, not truth probability.
Verification, freshness and common-origin independence remain unqualified.
Usage operations, users and customers never enter one pooled magnitude.
The attention/discovery gap is a relative heuristic, not a validation verdict.
"""
import os, sys, re, json, math, time, sqlite3, glob, hashlib, urllib.request, urllib.error
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import scoring
from pulse import COUNT_ONLY, url_net, url_hash, removal_lists   # the network, URL and removal rules the daily file uses
WEB, HIST = (os.path.join(BASE, d) for d in ('web', 'history'))
CACHE = os.environ.get('TRENDING_CACHE') or os.path.join(BASE, 'cache')
RESEARCH = os.path.join(BASE, 'hype', 'hype_research.json')
SUMMARY = os.path.join(BASE, 'hype', 'hype_summary.json')
OUT = os.path.join(WEB, 'hype.json')
TZ = ZoneInfo('America/Sao_Paulo')
UA = 'trending-research/2.0 (+https://github.com/namastex888/trending-research)'

PLATFORMS = ['X', 'Reddit', 'LinkedIn', 'HN', 'YouTube', 'Discord', 'Telegram']
RES_WINDOWS = [('1d', 1), ('7d', 7), ('30d', 30), ('90d', 90)]      # windows the research measured
ALL_WINDOWS = ['1d', '7d', '30d', '90d', '180d', '1y', 'overall']
TOPN = 100

def P(s):
    if not s: return None
    try:
        x = datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except ValueError:
        try: x = datetime.fromisoformat(str(s)[:10])
        except ValueError: return None
    return x if x.tzinfo else x.replace(tzinfo=timezone.utc)

def load(path, default):
    try:
        with open(path) as f: return json.load(f)
    except Exception: return default

def save(path, obj):
    tmp = path + '.tmp'
    with open(tmp, 'w') as f: json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, path)

def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:60]
def cut(s, n): s = ' '.join(str(s or '').split()); return s if len(s) <= n else s[:n - 1] + '…'
def is_url(u): return isinstance(u, str) and u.startswith('http')
def urls(lst, n=8): return [u for u in (lst or []) if is_url(u)][:n]
def arxiv_id(u):
    m = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})', u or '')
    return m.group(1) if m else None
def repo_name(u):
    m = re.search(r'github\.com/([^/\s]+/[^/\s#?]+)', u or '')
    return m.group(1).removesuffix('.git').lower() if m else None

# ---------------------------------------------------------------- joins with the other tabs
def gh_trust_map(repo_trust=None):
    """full_name(lower) -> current discovery activity input; no legacy-cache confidence inference."""
    rt = repo_trust or (load(os.path.join(CACHE, 'repo_trust.json'), None) or {}).get('repos')
    out = {}
    for k, v in (rt or {}).items():
        if v.get('trust') is not None and v.get('coverage') is not None:
            out[k.lower()] = dict(v=v['trust'], coverage=v['coverage'],
                                  src='GitHub tab activity discovery index (30d)')
    return out

def hf_upvotes(ids):
    """arXiv id -> (upvotes|None, source_url). Uses the pipeline's HF caches, then the HF API (cached 24h)."""
    known = {}
    for f in glob.glob(os.path.join(CACHE, 'hf_month_*.json')) + glob.glob(os.path.join(CACHE, 'hf_search_*.json')):
        for it in (load(f, {}) or {}).get('items', []):
            if it.get('id') and it.get('upvotes') is not None: known[it['id']] = it['upvotes']
    for pid, c in (load(os.path.join(CACHE, 'hf_papers.json'), {}) or {}).items():
        if c.get('data') and c['data'].get('upvotes') is not None: known[pid] = c['data']['upvotes']
    own_p = os.path.join(CACHE, 'hype_hf_papers.json')
    own = load(own_p, {})
    out, fetched = {}, 0
    for pid in ids:
        src = f'https://huggingface.co/papers/{pid}'
        if pid in known: out[pid] = (known[pid], src); continue
        c = own.get(pid)
        if not c or time.time() - c['ts'] > 24 * 3600:
            try:
                req = urllib.request.Request(f'https://huggingface.co/api/papers/{pid}', headers={'User-Agent': UA})
                with urllib.request.urlopen(req, timeout=20) as r: d = json.loads(r.read())
                c = {'ts': time.time(), 'upvotes': d.get('upvotes')}
            except urllib.error.HTTPError as e:
                c = {'ts': time.time(), 'upvotes': None, 'note': f'HTTP {e.code}'} if e.code == 404 else c
            except Exception:
                pass
            if c: own[pid] = c; fetched += 1
        out[pid] = ((c or {}).get('upvotes'), src)
    if fetched and os.path.isdir(CACHE): save(own_p, own)
    return out

# ---------------------------------------------------------------- compact per-project record
def likes_of(p):
    cm = (p.get('component_measurements') or {}).get('likes') or {}
    if cm.get('value') is not None: return cm['value']
    return (p.get('engagement') or {}).get('likes')

def top_posts(posts, n=6):
    def key(p):
        e = p.get('engagement') or {}
        return -(likes_of(p) or e.get('score') or p.get('reactions') or e.get('views') or 0)
    out = []
    for p in sorted(posts, key=key)[:n]:
        e = p.get('engagement') or {}
        out.append(dict(pl=p.get('platform'), au=p.get('author'), d=(p.get('date_utc') or '')[:10],
                        likes=likes_of(p), score=e.get('score'), cm=e.get('comments'), rp=e.get('replies'),
                        views=e.get('views'), url=p.get('url') if is_url(p.get('url')) else p.get('source_url'),
                        t=cut(p.get('title') or p.get('content_excerpt') or p.get('text_excerpt') or p.get('context'), 180)))
    return out

def usage_signals(sigs):
    """Preserve sourced metrics, including observed zero; never choose a largest mixed unit."""
    out = []
    for s in sigs:
        if s.get('type') not in scoring.METRIC_FAMILIES or not is_url(s.get('source_url')):
            continue
        value = s.get('value')
        if isinstance(value, dict):
            value = value.get('last_month')
        observed = scoring.isnum(value) and value >= 0
        out.append(dict(value=value if observed else None, unit=s.get('unit'), type=s['type'],
                        metric_family=scoring.METRIC_FAMILIES[s['type']],
                        period=dict(start=s.get('period_start_utc'), end=s.get('period_end_utc')),
                        scope=s.get('scope'), vendor=s.get('verification') == 'vendor_claim',
                        url=s['source_url'], missingness='observed' if observed else 'unobserved'))
    return out

def project(it, cutoff):
    L = it.get('links') or {}
    tl = it.get('timeline') or {}
    fs = tl.get('first_seen') or {}
    vo = it.get('viral_origin') or {}
    cand = vo.get('candidate_earliest_observed') or {}
    co = it.get('coordination_signals') or {}
    gh = it.get('github_snapshot') or {}
    hn = it.get('hn_sampling') or {}
    rk = it.get('ranking') or {}
    qg = rk.get('qualitative_hype_gap') or {}
    rn = it.get('ranking_notes') or {}
    disclosed = 'disclos' in (co.get('assessment') or '').lower() or any(
        re.search(r'#ad\b|sponsored|paid partnership', (e.get('evidence_excerpt') or '') + ' ' + (e.get('observation') or ''), re.I)
        and not re.search(r'not evidence|not proof|payment not established', e.get('observation') or '', re.I)
        for e in co.get('evidence') or [])
    return dict(
        name=it['name'], aliases=[a for a in (it.get('aliases') or [])[:6] if isinstance(a, str)],
        links={k: L.get(k) for k in ('site', 'x_handle', 'repo', 'paper', 'hf', 'github_org') if is_url(L.get(k))},
        category=it.get('category'), ptags=(it.get('paradigm_tags') or [])[:6], seed=bool(it.get('seed')),
        summary=it.get('exec_summary'), summary_urls=urls(it.get('exec_summary_source_urls'), 8),
        first_seen=fs.get('date_utc'), first_seen_url=fs.get('source_url'), first_seen_meaning=fs.get('meaning'),
        peak=tl.get('peak_date_utc'), peak_reason=tl.get('peak_reason'),
        status=(tl.get('current_status') or {}).get('text'), status_urls=urls((tl.get('current_status') or {}).get('source_urls'), 6),
        viral=dict(platform=vo.get('platform'), post=vo.get('post_url'), account=vo.get('account'),
                   followers=vo.get('follower_count'), reason=vo.get('reason'),
                   cand_platform=cand.get('platform'), cand_post=cand.get('post_url'), cand_account=cand.get('account')),
        coord=dict(assessment=co.get('assessment'), limitations=co.get('limitations'), disclosed=disclosed,
                   evidence=[dict(t=cut(e.get('evidence_excerpt') or e.get('observation'), 300), url=e.get('source_url'),
                                  d=(e.get('date_utc') or '')[:10]) for e in co.get('evidence') or []]),
        traction=[dict(type=s.get('type'), value=s.get('value'), unit=s.get('unit'), ver=s.get('verification'),
                       asof=(s.get('as_of_utc') or s.get('period_end_utc') or '')[:10] or None, url=s.get('source_url'),
                       notes=cut(s.get('notes'), 220)) for s in it.get('real_traction_signals') or []],
        skeptic=[dict(claim=cut(s.get('claim'), 400), by=cut(s.get('attribution'), 160), d=(s.get('date_utc') or '')[:10] or None,
                      url=s.get('source_url') or (urls(s.get('source_urls'), 1) or [None])[0]) for s in it.get('skeptic_signals') or []],
        posts=top_posts(it.get('observed_social_posts') or []),
        gh=dict(stars=gh.get('stars'), forks=gh.get('forks'), created=(gh.get('repo_created_at_utc') or '')[:10] or None,
                pushed=(gh.get('last_pushed_at_utc') or '')[:10] or None, observed=(gh.get('observed_at_utc') or '')[:10] or None,
                url=gh.get('source_url')) if gh.get('stars') is not None else None,
        hn=dict(returned=hn.get('returned_hits'), reported=hn.get('reported_search_hits'),
                accepted=hn.get('accepted_exact_phrase_stories'), url=hn.get('api_url'), capped=(hn.get('returned_hits') or 0) >= 100),
        proxy=dict(rank=rk.get('momentum_proxy_rank'), score=rk.get('momentum_proxy_score')) if rk.get('momentum_proxy_score') is not None else None,
        qual_gap=dict(pos=qg.get('position'), text=qg.get('assessment'), urls=urls(qg.get('source_urls'), 4)) if qg else None,
        notes=dict(momentum=rn.get('momentum_evidence'), traction=rn.get('traction_evidence'), gap=rn.get('hype_gap_evidence'),
                   confidence=rn.get('confidence')),
    )

# ---------------------------------------------------------------- public-data rules (design group A): the full build and --scrub share them
I18N = os.path.join(WEB, 'i18n')
X_PROFILE = re.compile(r'^https?://(?:www\.)?(?:x|twitter)\.com/\w+/?$', re.I)     # links.x_handle: the project's own account
X_WORD = re.compile(r'(?<![\w-])X(?![\w-])', re.A)
X_TERMS = re.compile(r'x\.com|twitter|tweet|repost|retweet|x_search|syndication|\b(?:likes|replies|views|reposts|followers|impressions|bookmarks)\b', re.I | re.A)

def cite(net): return {'X': 'an X post', 'account': 'a post whose link names its account'}.get(net) or f'a {net} post'
def link_net(u):
    """Network of a link, or of the words that replaced it."""
    return url_net(u) if is_url(u) else next((n for n in sorted(COUNT_ONLY) + ['account'] if u == cite(n)), None)
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def sentences(t): return [s for s in re.split(r'(?<=[.!?])\s+', t or '') if s]
def x_figure(s):
    """A sentence that may quote an X figure: a numeral plus an X or engagement term."""
    return bool(re.search(r'[0-9]', s) and (X_WORD.search(s) or X_TERMS.search(s)))

def prose_fields(H):
    """(slug, field path, container, key) of every prose field the research pass wrote; slug None for file-level text.
    scripts/check_page.mjs walks the same list."""
    for k in ('ranking_interpretation', 'gap_note'): yield None, k, H, k
    for k in ('coverage', 'coverage_short'):
        for i in range(len(H.get(k) or [])): yield None, f'{k}[{i}]', H[k], i
    for slug, it in H['items'].items():
        for k in ('summary', 'status', 'first_seen_meaning', 'peak_reason', 'category'): yield slug, k, it, k
        yield slug, 'viral.reason', it.get('viral') or {}, 'reason'
        for k in ('assessment', 'limitations'): yield slug, f'coord.{k}', it.get('coord') or {}, k
        for i, e in enumerate((it.get('coord') or {}).get('evidence') or []): yield slug, f'coord.evidence[{i}].t', e, 't'
        for i, s in enumerate(it.get('traction') or []): yield slug, f'traction[{i}].notes', s, 'notes'
        for i, s in enumerate(it.get('skeptic') or []):
            yield slug, f'skeptic[{i}].claim', s, 'claim'
            yield slug, f'skeptic[{i}].by', s, 'by'
        for k in sorted(it.get('notes') or {}): yield slug, f'notes.{k}', it['notes'], k
        if it.get('qual_gap'): yield slug, 'qual_gap.text', it['qual_gap'], 'text'

def x_hits(H):
    """[(slug, field, sentence)] of every X-figure detector hit in the prose."""
    out = []
    for slug, f, c, k in prose_fields(H):
        t = c[k] if isinstance(c, list) else c.get(k)
        if isinstance(t, str): out += [(slug, f, s) for s in sentences(t) if x_figure(s)]
    return out

def relink(o):
    """Every link into a count-only network, or naming an account, becomes the words for it ("an X post"); the claim stays.
    links.x_handle keeps the project's own profile link."""
    for k, v in (o.items() if isinstance(o, dict) else enumerate(o)):
        if isinstance(v, (dict, list)): relink(v)
        elif is_url(v) and url_net(v) and not (k == 'x_handle' and X_PROFILE.match(v)): o[k] = cite(url_net(v))

def drop_removed(o, drop):
    """Any other field that still carries a removed post's URL becomes null (the claim beside it stays; the page shows no link)."""
    for k, v in (o.items() if isinstance(o, dict) else enumerate(o)):
        if isinstance(v, (dict, list)): drop_removed(v, drop)
        elif is_url(v) and url_hash(v) in drop: o[k] = None

def own_account(slug, it, url):
    """links.x_handle stays only when it is the project's own account: the handle (lower case, punctuation stripped) contains a
    token of 4+ characters from the project's name, slug or repository name; otherwise it may be a person, and the link goes.
    scripts/check_page.mjs applies the same rule."""
    h = re.sub(r'[^a-z0-9]', '', url.rstrip('/').rsplit('/', 1)[-1].lower())
    repo = ((it.get('links') or {}).get('repo') or '').rstrip('/').rsplit('/', 1)[-1]
    return any(len(t) >= 4 and t in h for s in (it.get('name') or '', slug, repo) for t in re.split(r'[^a-z0-9]+', s.lower()))

def scrub(H, srcs=None, figs=None, drop=None):
    """Apply the group-A rules to a built hype.json in place; a second run changes nothing. srcs, figs: the owner-reviewed
    skeptic[].by disposition list and X-figure list (default: web/i18n/). An unlisted name or hit is left for CI to fail.
    drop: SHA256 hashes of post URLs that web/removals.json names or web/checks/dossier-gone.json lists (default: both files in
    web/); each such post leaves its item's posts, and the same URL anywhere else in an item becomes null (deletion-only, C34)."""
    if drop is None:
        removed, gone = removal_lists()
        drop = removed | {e.get('sha256') for e in gone}
    srcs = srcs if srcs is not None else load(os.path.join(I18N, 'dossier-sources.json'), {})
    figs = figs if figs is not None else load(os.path.join(I18N, 'dossier-x-figures.json'), {})
    keep_by, by_net = set(srcs.get('keep') or []), {e['sha256']: e['by'] for e in srcs.get('network') or []}
    strip = {(e.get('slug'), e['field'], e['sha256']) for e in figs.get('hits') or [] if e['disposition'] == 'strip'}
    place = (figs.get('placeholder') or {}).get('en')
    for slug, it in H['items'].items():
        it['posts'] = [p for p in it.get('posts') or [] if not (is_url(p.get('url')) and url_hash(p['url']) in drop)]
        drop_removed(it, drop)
        # counts only: an X, LinkedIn, YouTube, Telegram (or Reddit) post keeps its network and date; other posts lose the author
        it['posts'] = [{'pl': p['pl'], 'd': p.get('d')} if p.get('pl') in COUNT_ONLY else
                       {k: v for k, v in p.items() if k != 'au' and not (k == 'url' and url_net(v))} for p in it.get('posts') or []]
        for k in ('account', 'followers', 'cand_account'): (it.get('viral') or {}).pop(k, None)
        relink(it)
        L = it.get('links') or {}
        if is_url(L.get('x_handle')) and not own_account(slug, it, L['x_handle']): L['x_handle'] = None
        for rows, words in ((it.get('traction') or [], True), ((it.get('evidence_in') or {}).get('usage') or [], False),
                            ((it.get('discovery') or {}).get('metrics') or [], False)):
            for r in rows:                                    # a figure read from a count-only post is not shown
                n = link_net(r.get('url'))
                if n in COUNT_ONLY: r['value'] = f'figure from {cite(n)}, not shown' if words else None
        for s in it.get('skeptic') or []:
            if s.get('by') and s['by'] not in keep_by and sha(s['by']) in by_net: s['by'] = by_net[sha(s['by'])]
    for slug, f, c, k in prose_fields(H):
        t = c[k] if isinstance(c, list) else c.get(k)
        if not isinstance(t, str) or not any((slug, f, sha(s)) in strip for s in sentences(t)): continue
        out = []
        for s in sentences(t):
            s = place if (slug, f, sha(s)) in strip else s
            if not (s == place and out and out[-1] == place): out.append(s)
        c[k] = ' '.join(out)
    return H

# ---------------------------------------------------------------- history
def db_connect():
    os.makedirs(HIST, exist_ok=True)
    con = sqlite3.connect(os.path.join(HIST, 'trending.db'))
    con.executescript('''
    CREATE TABLE IF NOT EXISTS runs(run_id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, ts_local TEXT, seconds REAL, sources TEXT);
    CREATE TABLE IF NOT EXISTS ranks(run_id INT, tab TEXT, win TEXT, item_id TEXT, rank INT, score REAL);
    CREATE INDEX IF NOT EXISTS i_ranks ON ranks(tab, win, run_id);''')
    for col in ('scoring_version TEXT', 'kind TEXT', 'config_sha TEXT'):
        try: con.execute(f'ALTER TABLE runs ADD COLUMN {col}')
        except Exception: pass
    return con

def prev_hype(con, before=None):
    """-> ({(tab, win): {id: (rank, score)}}, ts_local, scoring_version of that run)."""
    q = "SELECT MAX(run_id) FROM ranks WHERE tab='hype'" + (' AND run_id < ?' if before else '')
    r = con.execute(q, (before,) if before else ()).fetchone()[0]
    if r is None: return {}, None, None
    out = {}
    for tab, win, item, rank, score in con.execute("SELECT tab, win, item_id, rank, score FROM ranks WHERE run_id=? AND (tab='hype' OR tab LIKE 'hype|%')", (r,)):
        out.setdefault((tab, win), {})[item] = (rank, score)
    try: row = con.execute('SELECT ts_local, scoring_version FROM runs WHERE run_id=?', (r,)).fetchone()
    except sqlite3.OperationalError: row = con.execute('SELECT ts_local, NULL FROM runs WHERE run_id=?', (r,)).fetchone()
    return out, (row[0] if row else None), ((row[1] if row else None) or '1.x')

# ---------------------------------------------------------------- main build
def build(con=None, run_id=None, repo_trust=None, tagger=None, tags=None, record=True, log=print, cfg=None):
    t0 = time.time()
    cfg = cfg or scoring.load_config()
    research = load(RESEARCH, None)
    if not isinstance(research, list) or not research:
        raise RuntimeError(f'{RESEARCH} missing or not a list of projects')
    summ = load(SUMMARY, {}) or {}
    if tagger is None or tags is None:
        sys.path.insert(0, BASE)
        from run import tag_for as tagger, TAGS as tags   # same paradigm buckets as the other tabs
    cutoff = P(summ.get('content_cutoff_utc') or ((research[0].get('research_scope') or {}).get('cutoff_utc'))) or datetime.now(timezone.utc)
    lookback = P(summ.get('lookback_start_utc') or (research[0].get('research_scope') or {}).get('lookback_start_utc'))
    look_days = max(1, round((cutoff - lookback).total_seconds() / 86400)) if lookback else 365

    items, ids = {}, []
    trust = gh_trust_map(repo_trust)
    papers = {}
    for it in research:
        pid = arxiv_id((it.get('links') or {}).get('paper'))
        if pid: papers[pid] = None
    ups = hf_upvotes(list(papers))
    used_slugs = set()
    for it in research:
        pid = slug(it['name'])
        while pid in used_slugs: pid += '-x'
        used_slugs.add(pid); ids.append(pid)
        rec = project(it, cutoff)
        text = ' '.join([it['name'], it.get('category') or '', ' '.join(it.get('paradigm_tags') or [])])
        rec['tag'] = tagger(text, it.get('exec_summary') or '') or 'other'
        fs = P(rec['first_seen'])
        rec['age_at_cutoff'] = round((cutoff - fs).total_seconds() / 86400, 1) if fs else None
        # ---- per-window sampled metrics (research windows) + overall from the post list
        M = it.get('metrics') or {}
        win = {}
        for w, days in RES_WINDOWS:
            per = {}
            have = False
            for pl in PLATFORMS:
                s = ((M.get(pl) or {}).get(w) or {}).get('sample')
                if s is None: continue
                have = True
                per[pl] = (s.get('observed_post_count') or 0, s.get('observed_unique_authors') or 0)
            if not have: win[w] = None; continue
            win[w] = dict(mentions=sum(v[0] for v in per.values()), voices=sum(v[1] for v in per.values()),
                          platforms=[pl for pl, v in per.items() if v[0] > 0], days=days)
        posts = it.get('observed_social_posts') or []
        dated = [p for p in posts if P(p.get('date_utc'))]
        win['overall'] = dict(mentions=len(posts), voices=len({(p.get('platform'), p.get('author')) for p in posts if p.get('author')}),
                              platforms=sorted({p.get('platform') for p in posts if p.get('platform')} & set(PLATFORMS + ['GitHub'])),
                              days=look_days)
        rec['win'] = win
        # ---- real-score raw inputs
        rn = repo_name((it.get('links') or {}).get('repo'))
        t = trust.get(rn) if rn else None
        pa = arxiv_id((it.get('links') or {}).get('paper'))
        up = ups.get(pa, (None, None)) if pa else (None, None)
        us = usage_signals(it.get('real_traction_signals') or [])
        hn = it.get('hn_sampling') or {}
        hn_ok = bool(hn) and hn.get('error') is None
        hn_c = sum(((p.get('engagement') or {}).get('comments') or 0) for p in posts if p.get('platform') == 'HN') if hn_ok else None
        hn_n = sum(1 for p in posts if p.get('platform') == 'HN')
        rec['evidence_in'] = dict(
            gh_trust=None if not t else dict(t, repo=rn),
            paper=None if up[0] is None else dict(v=up[0], id=pa, url=up[1]),
            usage=us,
            discussion=None if hn_c is None else dict(v=hn_c, stories=hn_n))
        items[pid] = rec

    # Current discovery composite excludes usage magnitudes and records independent dimensions.
    PJ = {pid: dict(win=items[pid]['win'], age=items[pid]['age_at_cutoff'],
                    evidence_in=items[pid]['evidence_in']) for pid in ids}
    discovery, discovery_prior = scoring.discovery_scores(PJ, cfg)
    for pid in ids:
        items[pid]['discovery'] = discovery[pid]

    if con is None and record: con = db_connect()
    prev, prev_ts, prev_ver = prev_hype(con, run_id) if con is not None else ({}, None, None)
    comparable = prev_ver == scoring.SCORING_VERSION
    views = ['all'] + list(tags)
    out_w, ranks_rows = {}, []
    win_meta, priors = {}, {'discovery': scoring.r1(discovery_prior)}
    for w in ALL_WINDOWS:
        if w in ('180d', '1y'):
            win_meta[w] = dict(enabled=False, reason=f'not a research window (research measured 1d/7d/30d/90d; overall = {look_days}-day lookback)')
            continue
        scored, prior = scoring.hype_window(PJ, w, discovery, cfg)
        if not scored:
            win_meta[w] = dict(enabled=False, reason='no sampled posts in this window'); continue
        priors[w] = scoring.r1(prior)
        win_meta[w] = dict(enabled=True, days=items[scored[0]['id']]['win'][w]['days'])
        vv = {}
        for v in views:
            sub = scored if v == 'all' else [r for r in scored if items[r['id']]['tag'] == v]
            hkey = 'hype' if v == 'all' else f'hype|{v}'
            pr = prev.get((hkey, w), {})
            top = sub[:TOPN]
            mvs = scoring.movement([(r['id'], r['score']) for r in top], pr, cfg, comparable=comparable)
            rows = []
            for k, (r, mv) in enumerate(zip(top, mvs), 1):
                ranks_rows.append((hkey, w, r['id'], k, r['score']))
                rows.append(dict(r, rank=k, prev=(pr.get(r['id']) or (None,))[0], mv=mv))
            vv[v] = dict(rows=rows, candidates=len(sub))
        out_w[w] = vv

    now = datetime.now(timezone.utc)
    if record and con is not None:
        if run_id is None:
            cur = con.execute('INSERT INTO runs(ts, ts_local, seconds, sources, scoring_version, kind, config_sha) VALUES(?,?,?,?,?,?,?)',
                              (now.strftime('%Y-%m-%dT%H:%M:%SZ'), now.astimezone(TZ).isoformat(timespec='seconds'),
                               round(time.time() - t0, 1), json.dumps({'hype_build': 'standalone'}),
                               scoring.SCORING_VERSION, 'hype', scoring.config_sha()))
            run_id = cur.lastrowid
        con.executemany('INSERT INTO ranks VALUES(?,?,?,?,?,?)', [(run_id,) + r for r in ranks_rows])
        con.commit()
        os.makedirs(os.path.join(HIST, 'runs'), exist_ok=True)
        save(os.path.join(HIST, 'runs', now.astimezone(TZ).strftime('%Y%m%d-%H%M%S') + '-hype.json'),
             {'run_id': run_id, 'ranks': {f'{t}/{w}': [[i, k, s] for (tt, ww, i, k, s) in ranks_rows if tt == t and ww == w]
                                          for t in sorted({r[0] for r in ranks_rows}) for w in ALL_WINDOWS}})

    cov = summ.get('coverage_limitations') or []
    def pick(rx):
        return next((c for c in cov if re.search(rx, c, re.I)), None)
    short = [c for c in (pick(r'not exhaustive'), pick(r'growth cannot'), pick(r'^HN')) if c] or cov[:3]
    comp_counts = {
        'hype': {k: sum(1 for w in out_w.values() for r in w['all']['rows'] if r['z'].get(k) is not None) for k in cfg['hype']['weights']},
        'discovery': {k: sum(1 for pid in ids if items[pid]['discovery']['z'][k] is not None)
                      for k in cfg['discovery']['weights']},
    }
    data = dict(
        generated_at=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        generated_local=now.astimezone(TZ).strftime('%Y-%m-%d %H:%M') + ' BRT',
        research_generated_at=summ.get('generated_at_utc'), content_cutoff=cutoff.strftime('%Y-%m-%dT%H:%M:%SZ'),
        lookback_days=look_days, run_id=run_id, previous_run=prev_ts,
        coverage_short=short, coverage=cov, ranking_interpretation=summ.get('ranking_interpretation'),
        gap_note=summ.get('gap_ranking_note'),
        scoring_version=scoring.SCORING_VERSION, config_sha=scoring.config_sha(), priors=priors,
        movement_note=(None if comparable or not prev else f'movement reset: the previous HYPE run used scoring v{prev_ver}'),
        weights=dict(hype=cfg['hype']['weights'], discovery=cfg['discovery']['weights']),
        gap_thresholds=[cfg['gap']['evidence_ahead'], cfg['gap']['attention_ahead']],
        gap_min_coverage=cfg['gap']['min_coverage'],
        penalties=dict(single_platform=cfg['hype']['single_platform_penalty'], few_voices=cfg['hype']['few_voices'],
                       few_voices_penalty=cfg['hype']['few_voices_penalty']),
        missing=dict(acceleration='No growth series in the research (no repeated snapshots; HN sample = first 100 hits by date, so a recent/older ratio would be biased). Weight renormalised over the other three.'),
        component_counts=comp_counts, n_projects=len(ids), views=views, windows=win_meta,
        items=items, **out_w)
    save(OUT, scrub(data))
    sz = os.path.getsize(OUT)
    log(f'[HYPE v{scoring.SCORING_VERSION}] wrote {OUT} ({sz/1024:.0f} KB): {len(ids)} projects; windows ' +
        ', '.join(f'{w}={len(out_w[w]["all"]["rows"])}' for w in out_w) + f'; prev hype run: {prev_ts}')
    return data

def scrub_file(path):
    """--scrub: apply the rules to a committed hype.json without a research pass; rewrites only when a byte changes. The removal lists
    are read beside the file (<dir>/removals.json, <dir>/checks/dossier-gone.json)."""
    raw = open(path, 'rb').read()
    removed, gone = removal_lists(os.path.dirname(os.path.abspath(path)))
    drop = removed | {e.get('sha256') for e in gone}
    H = json.loads(raw)
    before = sum(len(it.get('posts') or []) for it in H['items'].values())
    H = scrub(H, drop=drop)
    after = sum(len(it.get('posts') or []) for it in H['items'].values())
    changed = json.dumps(H, ensure_ascii=False, separators=(',', ':')).encode() != raw
    if changed: save(path, H)
    nets = {}
    for it in H['items'].values():
        for p in it.get('posts') or []: nets[p.get('pl')] = nets.get(p.get('pl'), 0) + 1
    print(f"scrub {path}: {len(H['items'])} items, posts by network {nets}, {len(x_hits(H))} X-figure hits kept; "
          f"{before - after} posts removed (removals.json {len(removed)} entries, checks/dossier-gone.json {len(gone)} hashes); "
          + ('rewritten' if changed else 'unchanged'))

def dossier_fields(path):
    """--dossier-fields: the slug, field path and SHA256 of every dossier prose field in a built hype.json, one JSON object per line,
    for web/i18n/dossier.pt.json entries (design row 13, C24). Read-only."""
    H = json.load(open(path, encoding='utf-8'))
    for slug, f, c, k in prose_fields(H):
        t = c[k] if isinstance(c, list) else c.get(k)
        if isinstance(t, str) and t: print(json.dumps({'slug': slug, 'field': f, 'sha256': sha(t), 'en': t}, ensure_ascii=False))

if __name__ == '__main__':
    if '--dossier-fields' in sys.argv: dossier_fields((sys.argv[sys.argv.index('--dossier-fields') + 1:] or [OUT])[0])
    elif '--scrub' in sys.argv: scrub_file((sys.argv[sys.argv.index('--scrub') + 1:] or [OUT])[0])
    else: build(record='--no-history' not in sys.argv)
