import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('library', Path(__file__).with_name('library.py'))
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'NBC'
        (self.root / 'Studio').mkdir(parents=True)
        (self.root / 'Characters').mkdir()
        self.restricted = [{'id': i, 'path': None, 'effective_use_policy': {'allowed_uses': [], 'provenance': 'supplemental' if i == 'B30' else 'restricted'}} for i in ('N35', 'B08', 'B25', 'B30')]
        (self.root / 'Characters/reference-policy.json').write_text(json.dumps({'references': self.restricted}))
        (self.root / 'README.md').write_text('[Guide](Studio/guide.md)\n')
        (self.root / 'Studio/guide.md').write_text('# Guide\n')
        self.control = {'files': {p: dict(size=f.stat().st_size, sha256=lib.sha(f)) for p, f in lib.files(self.root).items()}}
        self.save()

    def save(self):
        (self.root / lib.CONTROL).write_text(json.dumps(self.control))

    def test_complete_accounting_detects_changed_added_and_missing(self):
        self.assertEqual(lib.verify(self.root), [])
        (self.root / 'README.md').write_text('altered')
        (self.root / 'extra.md').write_text('new')
        (self.root / 'Studio/guide.md').unlink()
        errors = lib.verify(self.root)
        self.assertTrue(any('Changed file: README.md' == e for e in errors))
        self.assertIn('Unaccounted file: extra.md', errors)
        self.assertIn('Missing accounted file: Studio/guide.md', errors)

    def test_authoring_clone_ignores_machine_state_and_separate_frozen_deliveries(self):
        for name in ['.git/config', '.venv/pyvenv.cfg',
                     'Productions/Library-Refinement/delivery-v001/README.md']:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('[not an active link](missing.md)')
        self.assertEqual(lib.verify(self.root), [])
        # New working sources and the portable reader must still be accounted.
        for name in ['Reader/index.html', 'Productions/Library-Refinement/brief.md']:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('working file')
            self.assertIn('Unaccounted file: ' + name, lib.verify(self.root))

    def test_broken_relative_link_detected(self):
        (self.root / 'Studio/guide.md').unlink()
        self.assertTrue(any('missing link' in e for e in lib.links(self.root)))

    def test_external_recovery_is_optional_but_other_missing_links_are_errors(self):
        (self.root / 'Studio/guide.md').write_text(
            '[Archive](/elsewhere/NBC_Archives/snapshot.tar.gz)\n'
            '[Missing art](/elsewhere/art.png)\n')
        errors = lib.links(self.root)
        self.assertEqual(len(errors), 1)
        self.assertIn('/elsewhere/art.png', errors[0])

    def test_photo_hash_mismatch_detected(self):
        photo = self.root / 'Characters/photo.jpeg'
        photo.write_bytes(b'original')
        policy = {'references': self.restricted + [{'id': 'N01', 'path': 'Characters/photo.jpeg', 'sha256': lib.sha(photo)}]}
        (self.root / 'Characters/reference-policy.json').write_text(json.dumps(policy))
        self.assertEqual(lib.policies(self.root), [])
        photo.write_bytes(b'replaced')
        self.assertTrue(lib.policies(self.root))

    def test_restriction_broadening_rejected(self):
        self.restricted[0]['effective_use_policy']['allowed_uses'] = ['visible_anatomy']
        (self.root / 'Characters/reference-policy.json').write_text(json.dumps({'references': self.restricted}))
        self.assertIn('Reference restriction broadened: N35', lib.policies(self.root))

    def prepare_archive(self):
        source = self.base / 'original.txt'
        source.write_bytes(b'exact historical text\n')
        archive = self.base / 'snapshot.tar.gz'
        with tarfile.open(archive, 'w:gz') as tf:
            tf.add(source, arcname='NBC/old/original.txt')
        manifest = self.base / 'manifest.json'
        manifest.write_text(json.dumps({'entries': [{'path': 'old/original.txt', 'type': 'file', 'size': source.stat().st_size, 'sha256': lib.sha(source)}]}))
        self.control['recovery'] = {'archive': '../snapshot.tar.gz', 'manifest': '../manifest.json', 'archive_sha256': lib.sha(archive), 'manifest_sha256': lib.sha(manifest)}
        self.save()
        return source, manifest

    def test_recovery_matches_original_and_refuses_overwrite_or_active_destination(self):
        source, _ = self.prepare_archive()
        dest = self.base / 'restored.txt'
        self.assertEqual(lib.recover(self.root, 'old/original.txt', dest), lib.sha(source))
        self.assertEqual(dest.read_bytes(), source.read_bytes())
        with self.assertRaises(ValueError):
            lib.recover(self.root, 'old/original.txt', dest)
        with self.assertRaises(ValueError):
            lib.recover(self.root, 'old/original.txt', self.root / 'replace.txt')
        with self.assertRaises(ValueError):
            lib.recover(self.root, '../escape', self.base / 'escape')

    def test_recovery_rejects_changed_manifest(self):
        _, manifest = self.prepare_archive()
        manifest.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'manifest identity'):
            lib.recover(self.root, 'old/original.txt', self.base / 'restored.txt')


if __name__ == '__main__':
    unittest.main()
