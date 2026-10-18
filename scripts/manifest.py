#!/usr/bin/env python3
"""Daily input manifest, ledger and story-id archive (design rows 17, 18; C3, C15, C16, C25, C32, C42; group E1).

Run:   python3 scripts/manifest.py daily [--web web] [--history history] [--out dist/manifest]
           refresh.yml, after the composition and the search index, only when the Pulse step succeeded. Writes
           web/ledger/ids/<date>.json, builds <out>/manifest-<date>.json.gz from the history DB and the day's web/ files, runs the
           manifest check on it, then writes web/ledger/<date>.json and the <date> entry of web/ledger/index.json.
       python3 scripts/manifest.py check <manifest>
           the manifest check alone (a per-deploy check, C39): exit 1 with its findings.
       python3 scripts/manifest.py release <asset> --tag <tag> --url <url> [--web web]
           the Release asset as downloaded back from the dated Release: its SHA256 must equal the manifest_sha256 of its ledger entry,
           which then records the Release (tag, url, sha256); exit 1 on a mismatch, so the ledger never names a Release it does not equal.

<date> is the America/Sao_Paulo date of briefing.json generated_at (the date dehype.js gives the briefing). A rerun on the same date
replaces that date's ledger entry and day file and adds to its archive file (ids are never removed); an earlier date is never touched.

The manifest lists every stored post of the last 30 days (pulse.RECHECK_DAYS, the widest window an output shows) that the day's outputs
were built from, minus the posts the deleted-post recheck found gone (history/recheck.json) and those web/removals.json or
web/checks/dossier-gone.json name. HN, Lobsters, Newsletter and Official records carry a stable id, their handle-free URL, the observed
score and comments and the created and fetched times; a Mastodon record carries https://mastodon.social/statuses/<id> (C25). A Reddit
record is only {"net", "sha256"} (C16); so is a Bluesky record (its id and URL name the account) and any record whose URL would break
a public-data rule. The manifest also carries each source's status and the SHA256 of every file the refresh publishes. No author,
handle or title is written. Standard library only.
"""
import argparse, gzip, hashlib, json, os, re, sqlite3, sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import pulse                                                     # one copy of the recheck and removal rules

SP = ZoneInfo('America/Sao_Paulo')
COLUMNS = ('net', 'pid', 'url', 'title', 'author', 'created', 'score', 'comments', 'source', 'fetched', 'extra')
LINKED = {'HN', 'Lobsters', 'Mastodon', 'Newsletter', 'Official'}       # every other network is a record hash only
HASH_RULE = ('sha256 of the UTF-8 JSON of the stored history/signals.sqlite row {' + ', '.join(COLUMNS) + '}: keys sorted, '
             'separators "," and ":", non-ASCII kept, every value as stored (extra as its stored text, or null)')
# the files the refresh publishes (refresh.yml's git add line) and the owner-reviewed files the outputs apply; a missing file reads null
FILES = ('data.json', 'search-index.json', 'search-vectors.bin', 'pulse.json', 'briefing.json', 'checks/mastodon-links.json',
         'story-aliases.json', 'hype.json', 'checks/dossier-gone.json', 'feed.xml', 'feed.json', 'feed.pt.xml', 'feed.pt.json',
         'verdicts.json', 'removals.json', 'corrections.json')
HEX64, DAY = re.compile(r'^[0-9a-f]{64}$'), re.compile(r'^\d{4}-\d{2}-\d{2}$')
SID = re.compile(r'^s:[0-9a-f]{12}$')
STATUS_URL = re.compile(r'^https://mastodon\.social/statuses/(\d{1,20})$')
SAFE_ID = re.compile(r'^[\w.-]{1,40}$')
# the public-data rules of scripts/check_page.mjs (NET_URL, ACCOUNT_URL, HANDLE), as the manifest needs them
COUNT_ONLY_URL = re.compile(r'https?://(?:[\w-]+\.)*(?:reddit\.com|redd\.it|x\.com|twitter\.com|t\.co|nitter\.net|fxtwitter\.com|vxtwitter\.com|'
                            r'linkedin\.com|lnkd\.in|youtube\.com|youtu\.be|youtube-nocookie\.com|t\.me|telegram\.me|discord\.com|discord\.gg)(?=[/:?#]|$)', re.I)
ACCOUNT_URL = re.compile(r'https?://[^\s?#]*/@|bsky\.app/profile/|/users/[^/\s]+/statuses/|did:(?:plc|web):', re.I)
HANDLE = re.compile(r'(?<![A-Za-z0-9_/.@])@[A-Za-z0-9_][A-Za-z0-9_.-]*(?![A-Za-z0-9_/-])')
REDDIT = re.compile(r'reddit\.com|redd\.it|(?<![0-9a-z])t3_[0-9a-z]+', re.I)


def canonical(o): return json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
def sha256(b): return hashlib.sha256(b).hexdigest()
def compact(o): return json.dumps(o, ensure_ascii=False, separators=(',', ':'))          # generated web/ files stay on one line (Decision 19)
def sp_date(iso): return datetime.fromisoformat(iso.replace('Z', '+00:00')).astimezone(SP).date().isoformat()


def read_json(path, default=None):
    try:
        with open(path, encoding='utf-8') as f: return json.load(f)
    except FileNotFoundError:
        if default is not None: return default
        raise


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + '.tmp', 'w', encoding='utf-8') as f: f.write(text)
    os.replace(path + '.tmp', path)


def file_sha(path):
    try:
        with open(path, 'rb') as f: return sha256(f.read())
    except FileNotFoundError: return None


def stored_rows(db):
    con = sqlite3.connect(db)
    try: return [dict(zip(COLUMNS, r)) for r in con.execute(f'SELECT {",".join(COLUMNS)} FROM signals')]
    finally: con.close()


def record(row):
    """One manifest record from a stored row: linked (id, handle-free URL, observed values, times) or {"net", "sha256"} only."""
    net, pid = row['net'], str(row['pid'] or '')
    url = None
    if net == 'Mastodon' and row.get('source') == 'live' and re.fullmatch(r'\d{1,20}', pid): url = f'https://mastodon.social/statuses/{pid}'
    elif net in LINKED - {'Mastodon'} and isinstance(row['url'], str) and re.match(r'^https?://', row['url']) \
            and not COUNT_ONLY_URL.search(row['url']) and not ACCOUNT_URL.search(row['url']) and not HANDLE.search(row['url']):
        url = row['url']
    if not url: return {'net': net, 'sha256': sha256(canonical(row))}
    rid = f'{net}:{pid}' if SAFE_ID.match(pid) else f'{net}:h{sha256(pid.encode("utf-8"))[:16]}'
    return {'id': rid, 'net': net, 'url': url, 'created': row['created'], 'fetched': row['fetched'],
            'score': row['score'], 'comments': row['comments']}


def inputs(rows, web, recheck_path, generated_at):
    """The stored rows the day's outputs were built from: the last RECHECK_DAYS, minus every post found gone or named for removal."""
    lo = pulse.iso(pulse.parse_dt(generated_at) - timedelta(days=pulse.RECHECK_DAYS))
    removal, gone_list = pulse.removal_lists(web)
    gone_urls, gone_keys = {e.get('sha256') for e in gone_list}, set(pulse.load_recheck(recheck_path)['gone'])
    keep = []
    for r in rows:
        if not r['created'] or r['created'] < lo: continue
        if pulse.recheck_key(r) in gone_keys or pulse.post_hashes(r) & removal: continue
        if r['url'] and pulse.url_hash(r['url']) in gone_urls: continue
        keep.append(r)
    return keep


def build(web, history, out):
    """-> (manifest path, its SHA256, the manifest, the briefing). Writes the day's archive file first: the manifest pins its hash."""
    B = read_json(os.path.join(web, 'briefing.json'))
    if B.get('stale'): raise SystemExit('manifest: briefing.json is a stale briefing (the Pulse step failed): no manifest and no ledger entry today')
    date = sp_date(B['generated_at'])
    write_ids(web, date, B)
    rows = inputs(stored_rows(os.path.join(history, 'signals.sqlite')), web, os.path.join(history, 'recheck.json'), B['generated_at'])
    recs = sorted((record(r) for r in rows), key=lambda x: (x['net'], x.get('id') or '', x.get('sha256') or ''))
    counts = {}
    for x in recs: counts[x['net']] = counts.get(x['net'], 0) + 1
    files = {f'web/{f}': file_sha(os.path.join(web, f)) for f in FILES}
    files[f'web/ledger/ids/{date}.json'] = file_sha(os.path.join(web, 'ledger', 'ids', f'{date}.json'))
    M = {'manifest': 'dehype daily input manifest', 'version': 1, 'date': date, 'generated_at': B['generated_at'],
         'window': {k: B.get('window', {}).get(k) for k in ('start', 'end')},
         'method': {k: B.get('method', {}).get(k) for k in ('version', 'config_hash')},
         'sources': {n: {'status': s.get('status'), 'detail': s.get('detail')} for n, s in (B.get('sources') or {}).items()},
         'files': files, 'hash_rule': HASH_RULE, 'counts': counts, 'records': recs}
    bad = check(M)
    if bad: raise SystemExit('manifest check FAILED (nothing written but the archive file)\n- ' + '\n- '.join(bad))
    path = os.path.join(out, f'manifest-{date}.json.gz')
    os.makedirs(out, exist_ok=True)
    blob = gzip.compress(canonical(M), compresslevel=9, mtime=0)
    with open(path, 'wb') as f: f.write(blob)
    return path, sha256(blob), M, B


def load_manifest(path):
    with open(path, 'rb') as f: b = f.read()
    return json.loads(gzip.decompress(b) if b[:2] == b'\x1f\x8b' else b)


def check(M):
    """The manifest check (SC-4, SC-5 manifest part): findings, empty when it passes."""
    bad = []
    if not isinstance(M, dict) or not isinstance(M.get('records'), list): return ['manifest is not an object with its records list']
    if not DAY.match(str(M.get('date'))): bad.append('manifest date is not YYYY-MM-DD')
    files = M.get('files')
    if not isinstance(files, dict) or not all(v is None or HEX64.match(str(v)) for v in files.values()): bad.append('manifest files are not path -> SHA256 (or null)')
    text = canonical(M).decode('utf-8')
    if REDDIT.search(text): bad.append(f'manifest holds a Reddit URL or t3_ id ({REDDIT.search(text)[0]})')
    def walk(o, at):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ('author', 'title', 'handle', 'who', 'text'): bad.append(f'manifest carries a {k} field at {at}.{k}')
                walk(v, f'{at}.{k}')
        elif isinstance(o, list):
            for i, v in enumerate(o): walk(v, f'{at}[{i}]')
        elif isinstance(o, str):
            for u in re.findall(r'https?://[^\s"\'<>]+', o):
                if COUNT_ONLY_URL.search(u): bad.append(f'manifest links a counts-only network at {at}')
                if ACCOUNT_URL.search(u): bad.append(f'manifest URL names an account at {at}')
            if ACCOUNT_URL.search(o) or HANDLE.search(o): bad.append(f'manifest names a person handle or account at {at}')
    walk({k: v for k, v in M.items() if k != 'hash_rule'}, 'manifest')
    for i, r in enumerate(M['records']):
        at = f'records[{i}]'
        if not isinstance(r, dict): bad.append(f'{at} is not an object'); continue
        if r.get('net') == 'Reddit' and set(r) != {'net', 'sha256'}:
            bad.append(f'{at}: a Reddit record carries a field other than the hash and the network name ({", ".join(sorted(set(r) - {"net", "sha256"}))})')
        if 'sha256' in r:
            if set(r) != {'net', 'sha256'} or not HEX64.match(str(r['sha256'])): bad.append(f'{at}: a hashed record is not {{"net", "sha256": <64 hex>}}')
        elif r.get('net') not in LINKED: bad.append(f'{at}: a {r.get("net")} record is linked (only {", ".join(sorted(LINKED))} may be)')
        elif r.get('net') == 'Mastodon' and not (STATUS_URL.match(str(r.get('url'))) and r.get('id') == 'Mastodon:' + STATUS_URL.match(r['url'])[1]):
            bad.append(f'{at}: a Mastodon record without its https://mastodon.social/statuses/<id> URL')
    return list(dict.fromkeys(bad))


def write_ids(web, date, B):
    """web/ledger/ids/<date>.json in B2's shape: every story id the day's pulse.json and briefing.json published, never shrunk."""
    path = os.path.join(web, 'ledger', 'ids', f'{date}.json')
    P = read_json(os.path.join(web, 'pulse.json'))
    ids = {s['id'] for s in P.get('stories') or []} | {r['id'] for r in B.get('records') or []} | {r['id'] for r in B.get('top10') or []}
    old = read_json(path, {})
    if old and (old.get('date') != date or not isinstance(old.get('ids'), list)): raise SystemExit(f'manifest: {path} is not this date\'s archive file')
    ids |= set(old.get('ids') or [])
    if not all(SID.match(x) for x in ids): raise SystemExit('manifest: a story id is not s:<12 hex>')
    write(path, compact({'date': date, 'generated_at': B['generated_at'], 'ids': sorted(ids)}))


def entries(web):
    L = read_json(os.path.join(web, 'ledger', 'index.json'), [])
    E = L.get('entries') if isinstance(L, dict) else L
    if not isinstance(E, list): raise SystemExit('manifest: web/ledger/index.json is not a list of day entries')
    return E


def ledger(web, path, digest, M, B):
    """web/ledger/<date>.json (the day's gauge and verdict ledger) and its web/ledger/index.json entry; release is filled by `release`."""
    date, E = M['date'], entries(web)
    if E and E[-1].get('date', '') > date: raise SystemExit(f'manifest: the ledger already holds {E[-1]["date"]}, later than {date}')
    V = read_json(os.path.join(web, 'verdicts.json'), {'rows': []})
    day = {'date': date, 'generated_at': B['generated_at'], 'method': M['method'],
           'manifest': {'asset': os.path.basename(path), 'sha256': digest, 'counts': M['counts']},
           'files': M['files'], 'top10': [{'rank': t['rank'], 'id': t['id']} for t in B.get('top10') or []],
           'gauges': [{'id': g.get('id'), 'status': g.get('status'), 'value': g.get('value')} for g in B.get('gauges') or []],
           'verdicts': [{k: r.get(k) for k in ('id', 'label', 'confirmed', 'commit')} for r in V.get('rows') or []]}
    text = compact(day)
    write(os.path.join(web, 'ledger', f'{date}.json'), text)
    entry = {'date': date, 'generated_at': B['generated_at'], 'manifest_sha256': digest, 'asset': os.path.basename(path),
             'ledger_sha256': sha256(text.encode('utf-8')), 'release': None, 'block': None}
    E = [e for e in E if e.get('date') != date] + [entry]
    write(os.path.join(web, 'ledger', 'index.json'), compact(E))
    return entry


def release(web, asset, tag, url):
    """Record the dated Release in its ledger entry once its asset, downloaded back, hashes to the ledger's manifest_sha256."""
    E, name = entries(web), os.path.basename(asset)
    e = next((x for x in E if x.get('asset') == name), None)
    if not e: raise SystemExit(f'manifest: no ledger entry names {name}')
    with open(asset, 'rb') as f: got = sha256(f.read())
    if got != e['manifest_sha256']:
        raise SystemExit(f'manifest: the Release asset {name} hashes to {got}, the ledger records {e["manifest_sha256"]}')
    e['release'] = {'tag': tag, 'url': url, 'sha256': got}
    write(os.path.join(web, 'ledger', 'index.json'), compact(E))
    return e


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = a.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('daily'); d.add_argument('--web', default='web'); d.add_argument('--history', default='history'); d.add_argument('--out', default='dist/manifest')
    c = sub.add_parser('check'); c.add_argument('manifest')
    r = sub.add_parser('release'); r.add_argument('asset'); r.add_argument('--tag', required=True); r.add_argument('--url', required=True); r.add_argument('--web', default='web')
    o = a.parse_args(argv)
    if o.cmd == 'check':
        bad = check(load_manifest(o.manifest))
        if bad: print('manifest check FAILED\n- ' + '\n- '.join(bad), file=sys.stderr); return 1
        print(f'manifest check ok: {o.manifest}'); return 0
    if o.cmd == 'release':
        e = release(o.web, o.asset, o.tag, o.url)
        print(f'ledger {e["date"]}: Release {o.tag} asset sha256 {e["release"]["sha256"]} equals the ledger\'s manifest_sha256'); return 0
    path, digest, M, B = build(o.web, o.history, o.out)
    e = ledger(o.web, path, digest, M, B)
    print(f'manifest {path} sha256 {digest}: {len(M["records"])} records ({", ".join(f"{n} {k}" for n, k in sorted(M["counts"].items()))}); '
          f'ledger {e["date"]} written, {len(entries(o.web))} days; archive web/ledger/ids/{e["date"]}.json')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f: f.write(f'date={e["date"]}\nasset={e["asset"]}\npath={path}\nsha256={digest}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
