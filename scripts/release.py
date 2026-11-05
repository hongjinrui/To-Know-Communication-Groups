#!/usr/bin/env python3
"""Compare reviewed editorial content against a Git revision and advance badges."""
import argparse
import copy
import datetime as dt
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIELDS = ('name', 'schoolId', 'leaders', 'tagline', 'whyFollow', 'past', 'current',
          'next', 'confidence', 'topics', 'sources', 'papers', 'logs')


def semantic(group):
    return {key: group.get(key) for key in FIELDS}


def release(catalog, previous, edition):
    result = copy.deepcopy(catalog)
    old = {g['id']: g for g in previous.get('groups', [])}
    baseline = not old
    changed = []
    for group in result['groups']:
        prior = old.get(group['id'])
        different = prior is None or semantic(group) != semantic(prior)
        group['updatedThisEdition'] = bool(different and not baseline)
        group['revision'] = 1 if prior is None else int(prior.get('revision', 1)) + int(different)
        group['previousRevision'] = 0 if prior is None else prior.get('revision', 1)
        if group['updatedThisEdition']:
            changed.append(group['id'])
    result['edition'] = edition
    result['previousEdition'] = previous.get('edition')
    result['changedGroupIds'] = changed
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--against', default='HEAD', help='Git ref containing previous data/groups.json')
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'data/groups.json'
    catalog = json.loads(path.read_text())
    previous = {}
    if not args.baseline:
        raw = subprocess.run(['git', 'show', f'{args.against}:data/groups.json'],
                             cwd=ROOT, capture_output=True, text=True, check=True)
        previous = json.loads(raw.stdout)
    edition = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec='seconds')
    updated = release(catalog, previous, edition)
    path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'edition': edition, 'changedGroupIds': updated['changedGroupIds']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
