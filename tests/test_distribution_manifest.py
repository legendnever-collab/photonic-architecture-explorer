"""Portable checks of the Windows package builder and launcher, independent of a Windows host."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('package_build', ROOT / 'scripts/build_windows_package.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class DistributionManifestTests(unittest.TestCase):
    def test_inventory_detects_changed_missing_and_extra_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.py'
            source.write_text('original')
            manifest = {'files_sha256': build.hashes(root)}
            (root / 'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest))
            self.assertEqual(build.verify(root), manifest)
            source.write_text('changed')
            with self.assertRaises(RuntimeError):
                build.verify(root)
            source.unlink()
            with self.assertRaises(RuntimeError):
                build.verify(root)
            source.write_text('original')
            (root / 'extra.txt').write_text('extra')
            with self.assertRaises(RuntimeError):
                build.verify(root)

    def test_runtime_bytecode_does_not_change_the_distribution_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'source.py').write_text('source')
            manifest = {'files_sha256': build.hashes(root)}
            (root / 'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest))
            (root / '__pycache__').mkdir()
            (root / '__pycache__/source.pyc').write_bytes(b'generated')
            self.assertEqual(build.verify(root), manifest)

    def test_launcher_self_test_runs_the_packaged_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / 'app'
            app.mkdir()
            (app / 'launcher.py').write_bytes((ROOT / 'distribution/launcher.py').read_bytes())
            try:
                (app / 'src').symlink_to(ROOT / 'src', target_is_directory=True)
            except OSError:
                self.skipTest('symlinks unavailable on this host')
            env = {'PYTHONPATH': str(app / 'src'), 'PATH': ''}
            run = subprocess.run([sys.executable, '-X', 'utf8', str(app / 'launcher.py'), '--self-test'],
                                 capture_output=True, text=True, env=env, cwd=directory)
            self.assertEqual(run.returncode, 0, run.stderr)
            record = json.loads(run.stdout)
            self.assertEqual((record['status'], record['S1'], record['web_index']), ('Pass', 'Computed', True))


if __name__ == '__main__':
    unittest.main()
