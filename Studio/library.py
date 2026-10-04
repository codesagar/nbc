#!/usr/bin/env python3
"""Small local NBC search, integrity and archive-recovery utility."""
import argparse
import hashlib
import json
import re
import sys
import tarfile
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
CONTROL = 'Studio/collection.json'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def files(root):
    # Git metadata and local environments are machine state. Frozen deliveries
    # retain their own manifests/accounting and are optional in an authoring clone.
    def included(p):
        rel = p.relative_to(root)
        if any(part in {'.git', '.venv', '__pycache__'} for part in rel.parts):
            return False
        if len(rel.parts) > 2 and rel.parts[:2] == ('Productions', 'Library-Refinement') and re.fullmatch(r'delivery-v[0-9]+', rel.parts[2]):
            return False
        return p.name != '.DS_Store' and rel.as_posix() != CONTROL
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*')
            if p.is_file() and included(p)}


def links(root):
    errors = []
    for rel, p in files(root).items():
        if p.suffix != '.md':
            continue
        for target in re.findall(r'!?\[[^\]]*\]\(([^\n]+?)\)', p.read_text()):
            target = target.strip().strip('<>')
            if re.match(r'^[a-z]+:', target) or target.startswith('#'):
                continue
            path = Path(unquote(target.split('#')[0]))
            # Historical absolute archive links are declared external recovery
            # dependencies, not required files in a portable authoring clone.
            if path.is_absolute() and 'NBC_Archives' in path.parts:
                continue
            dest = p.parent / path
            if not dest.exists():
                errors.append(f'{rel}: missing link {target}')
    return errors


def policies(root):
    errors = []
    p = root / 'Characters/reference-policy.json'
    if not p.exists():
        return ['Missing character reference policy']
    data = json.loads(p.read_text())
    # Policies are self-contained metadata; source photos must be pinned.
    records = data.get('references', []) if isinstance(data, dict) else data
    by_id = {entry['id']: entry for entry in records}
    if len(by_id) != len(records):
        errors.append('Duplicate reference IDs')
    ceilings = {'N35': {'provenance_review'}, 'B08': {'styling'},
                'B25': set(), 'B30': {'resting_pose', 'styling'}}
    for ref_id, ceiling in ceilings.items():
        entry = by_id.get(ref_id)
        if entry is None:
            errors.append('Missing restricted reference record: ' + ref_id)
            continue
        policy = entry.get('effective_use_policy', {})
        if not set(policy.get('allowed_uses', [])) <= ceiling:
            errors.append('Reference restriction broadened: ' + ref_id)
        if ref_id == 'B25' and entry.get('path'):
            errors.append('B25 remains unavailable')
        if ref_id == 'B30' and policy.get('provenance') != 'supplemental':
            errors.append('B30 must remain supplemental')
    for entry in records:
        path = entry.get('path')
        if path and 'source_use_policy' in entry:
            ceiling = set(entry['source_use_policy'].get('allowed_uses', []))
            allowed = set(entry.get('effective_use_policy', {}).get('allowed_uses', []))
            # Specific standing suitability narrows the source's general pose permission.
            allowed = {'pose' if use == 'standing_pose' else use for use in allowed}
            if not allowed <= ceiling:
                errors.append('Effective policy exceeds source ceiling: ' + entry['id'])
        if path:
            photo = root / path
            if not photo.is_file() or sha(photo) != entry.get('sha256'):
                errors.append('Reference bytes mismatch: ' + path)
    return errors


def verify(root):
    errors = links(root) + policies(root)
    control = json.loads((root / CONTROL).read_text())
    current = files(root)
    expected = control['files']
    for rel in sorted(current.keys() - expected.keys()):
        errors.append('Unaccounted file: ' + rel)
    for rel in sorted(expected.keys() - current.keys()):
        errors.append('Missing accounted file: ' + rel)
    for rel in current.keys() & expected.keys():
        if current[rel].stat().st_size != expected[rel]['size'] or sha(current[rel]) != expected[rel]['sha256']:
            errors.append('Changed file: ' + rel)
    return errors


def archive_info(root):
    control = json.loads((root / CONTROL).read_text())
    info = control['recovery']
    archive = (root / info['archive']).resolve()
    manifest = (root / info['manifest']).resolve()
    if sha(manifest) != info['manifest_sha256']:
        raise ValueError('Recovery manifest identity mismatch')
    entries = {e['path']: e for e in json.loads(manifest.read_text())['entries']}
    return archive, entries, info


def recover(root, original, destination):
    archive, entries, _ = archive_info(root)
    e = entries.get(original)
    if not e or e['type'] != 'file':
        raise ValueError('Supply an exact original file path from the migration map/manifest')
    dest = Path(destination).resolve()
    if dest == root.resolve() or root.resolve() in dest.parents:
        raise ValueError('Restore outside the active collection, then intentionally intake material')
    if dest.exists():
        raise ValueError('Recovery destination already exists')
    # Extract bytes only: no archive paths, symlinks or shell instructions are executed.
    with tarfile.open(archive, 'r:gz') as tf:
        member = tf.getmember('NBC/' + original)
        if not member.isfile() or member.size != e['size']:
            raise ValueError('Archive member does not match manifest')
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tf.extractfile(member) as source, dest.open('xb') as output:
            h = hashlib.sha256()
            for block in iter(lambda: source.read(1024 * 1024), b''):
                output.write(block)
                h.update(block)
    if h.hexdigest() != e['sha256']:
        dest.unlink()
        raise ValueError('Restored file hash mismatch')
    return e['sha256']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    search = sub.add_parser('search', help='Search full story text and meaningful alternatives')
    search.add_argument('phrase')
    sub.add_parser('verify', help='Check active bytes, complete accounting, links and photo pins')
    sub.add_parser('seal', help='After inspecting edits, update the single current file inventory')
    sub.add_parser('archive-check', help='Recheck compressed snapshot and manifest hashes')
    recover_parser = sub.add_parser('recover', help='Restore one exact original outside NBC and verify it')
    recover_parser.add_argument('original')
    recover_parser.add_argument('destination')
    args = parser.parse_args()
    if args.command == 'search':
        for p in sorted((ROOT / 'Stories').glob('*.md')):
            if p.name == 'README.md':
                continue
            rows = [(n, line.strip()) for n, line in enumerate(p.read_text().splitlines(), 1)
                    if args.phrase.casefold() in line.casefold()]
            if rows:
                print(p.relative_to(ROOT))
                for n, line in rows[:3]:
                    print(f'  {n}: {line[:240]}')
    elif args.command == 'verify':
        errors = verify(ROOT)
        print('\n'.join(errors) if errors else f'PASS: {len(files(ROOT))} files accounted; links and photo pins intact.')
        return bool(errors)
    elif args.command == 'seal':
        errors = links(ROOT) + policies(ROOT)
        if errors:
            raise ValueError('\n'.join(errors))
        control = json.loads((ROOT / CONTROL).read_text())
        control['files'] = {rel: dict(size=p.stat().st_size, sha256=sha(p)) for rel, p in sorted(files(ROOT).items())}
        (ROOT / CONTROL).write_text(json.dumps(control, indent=2) + '\n')
        print(f'Sealed current accounting for {len(control["files"])} files. This records bytes, not approval.')
    elif args.command == 'archive-check':
        archive, entries, info = archive_info(ROOT)
        if sha(archive) != info['archive_sha256']:
            raise ValueError('Recovery archive identity mismatch')
        print(f'PASS: original verified archive identity intact; {len(entries)} manifest entries.')
    elif args.command == 'recover':
        print('Recovered and verified SHA-256: ' + recover(ROOT, args.original, args.destination))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, json.JSONDecodeError, tarfile.TarError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
