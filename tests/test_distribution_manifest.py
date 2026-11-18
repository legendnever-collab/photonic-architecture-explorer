"""Portable manifest verification, independent of a Windows build host."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from photonic_architecture_explorer.workflow_worker import atomic_json

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('review_build',ROOT/'scripts/build_m7e_review.py')
build=importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class DistributionManifestTests(unittest.TestCase):
    def test_transient_windows_read_lock_retries_atomic_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'progress.json'
            target.write_text('{"old":true}')
            original=Path.replace
            calls=[]
            def replace(source,destination):
                calls.append(1)
                if len(calls)<3:
                    self.assertEqual(json.loads(target.read_text()),{'old':True})
                    raise PermissionError('simulated Windows reader lock')
                return original(source,destination)
            with patch.object(Path,'replace',replace), patch('photonic_architecture_explorer.workflow_worker.time.sleep'):
                atomic_json(target,{'complete':True})
            self.assertEqual(len(calls),3)
            self.assertEqual(json.loads(target.read_text()),{'complete':True})

    def test_persistent_read_lock_is_bounded_and_keeps_old_complete_record(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'progress.json'
            target.write_text('{"old":true}')
            with patch.object(Path,'replace',side_effect=PermissionError('locked')) as replace:
                with patch('photonic_architecture_explorer.workflow_worker.time.sleep'):
                    with self.assertRaises(PermissionError):atomic_json(target,{'complete':True})
            self.assertEqual(replace.call_count,100)
            self.assertEqual(json.loads(target.read_text()),{'old':True})

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
