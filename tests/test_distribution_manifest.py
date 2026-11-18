"""Portable manifest verification, independent of a Windows build host."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('review_build',ROOT/'scripts/build_m7e_review.py')
build=importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class DistributionManifestTests(unittest.TestCase):
    def test_inventory_detects_changed_missing_and_extra_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source=root/'source.py';source.write_text('original')
            manifest={'files_sha256':build.hashes(root)}
            (root/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest))
            self.assertEqual(build.verify(root),manifest)
            source.write_text('changed')
            with self.assertRaises(RuntimeError):build.verify(root)
            source.unlink()
            with self.assertRaises(RuntimeError):build.verify(root)
            source.write_text('original')
            (root/'extra.txt').write_text('extra')
            with self.assertRaises(RuntimeError):build.verify(root)

    def test_runtime_bytecode_does_not_change_the_distribution_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'source.py').write_text('source')
            manifest={'files_sha256':build.hashes(root)}
            (root/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest))
            (root/'__pycache__').mkdir()
            (root/'__pycache__/source.pyc').write_bytes(b'generated')
            self.assertEqual(build.verify(root),manifest)
