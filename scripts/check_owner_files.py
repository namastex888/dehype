"""Owner-reviewed files in git (design row 7, C11, C40; row 19, C44), run by ci.yml against the base commit of the change:
web/corrections.json is appended to, never edited over (every entry at the base commit is still there, unchanged and in its place), and no
commit by the refresh bot touches web/verdicts.json or web/corrections.json (they enter only by a merged pull request).
Standard library only. Usage: python3 scripts/check_owner_files.py [--repo DIR] [--head REF] BASE
BASE is the pull request's base sha or the push's `before` sha; an empty or all-zero BASE (a new branch) is checked against HEAD~1."""
import argparse, json, subprocess, sys

CORRECTIONS = 'web/corrections.json'
OWNER_FILES = ('web/verdicts.json', 'web/corrections.json')
BOT = {'trend-observatory-bot', 'github-actions[bot]', '41898282+github-actions[bot]@users.noreply.github.com'}   # refresh.yml's identity


def git(repo, *args):
    return subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True)


def entries(repo, ref):
    """The corrections entries at ref; [] when the file does not exist there."""
    if git(repo, 'cat-file', '-e', f'{ref}:{CORRECTIONS}').returncode: return []
    data = json.loads(git(repo, 'show', f'{ref}:{CORRECTIONS}').stdout)
    e = data.get('entries') if isinstance(data, dict) else None
    if not isinstance(e, list): raise ValueError(f'{CORRECTIONS} at {ref[:12]} has no entries list')
    return e


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('base', nargs='?', default='')
    ap.add_argument('--head', default='HEAD')
    ap.add_argument('--repo', default='.')
    a = ap.parse_args(argv)
    repo, head, base = a.repo, a.head, a.base.strip()
    if not base or set(base) == {'0'}:
        if git(repo, 'rev-parse', '--verify', '--quiet', f'{head}~1^{{commit}}').returncode:
            print(f'owner files ok: no base commit and {head} has no parent; nothing to compare'); return 0
        base = f'{head}~1'
        print(f'notice: no base commit given; comparing with {base}', file=sys.stderr)
    if git(repo, 'rev-parse', '--verify', '--quiet', f'{base}^{{commit}}').returncode:
        print(f'owner-file check FAILED\n- base commit {base} is not in the checkout (check out with fetch-depth: 0)', file=sys.stderr); return 1
    short = git(repo, 'rev-parse', '--short', base).stdout.strip()
    fail = []
    try: old, new = entries(repo, base), entries(repo, head)
    except ValueError as e: old, new = [], []; fail.append(str(e))
    at = {e.get('id'): i for i, e in enumerate(new) if isinstance(e, dict)}
    for i, e in enumerate(old):
        name = e.get('id') if isinstance(e, dict) and e.get('id') else f'#{i + 1}'
        if not isinstance(e, dict) or name not in at: fail.append(f'{CORRECTIONS} entry {name} removed since the base commit {short}')
        elif at[name] != i or new[i] != e: fail.append(f'{CORRECTIONS} entry {name} edited since the base commit {short} (append a new entry instead)')
    log = git(repo, 'log', '--format=%x00%h%x09%an%x09%ae%x09%cn%x09%ce', '--name-only', f'{base}..{head}', '--', *OWNER_FILES).stdout
    commits = [c for c in log.split('\x00') if c.strip()]
    for c in commits:
        line, *files = [x for x in c.splitlines() if x]
        sha, *who = line.split('\t')
        if BOT & set(who): fail.append(f'commit {sha} by the refresh bot touches {", ".join(files)} (owner-reviewed: enters only by a merged pull request)')
    if fail:
        print('owner-file check FAILED\n- ' + '\n- '.join(fail), file=sys.stderr); return 1
    print(f'owner files ok: {CORRECTIONS} {len(old)} entries at {short}, {len(new)} now ({len(new) - len(old)} appended); '
          f'{len(commits)} commits since {short} touch {" or ".join(OWNER_FILES)}, none by the refresh bot')
    return 0


if __name__ == '__main__':
    sys.exit(main())
