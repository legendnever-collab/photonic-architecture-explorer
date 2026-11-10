"""Adversarial execution checks, independent of optional optical dependencies."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from m4c_evidence import ROOT, check_legacy, head, sha, verify


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.report = (ROOT/'results/m4c_planar_control.json').read_bytes()
        (self.out/'m4c_planar_control.json').write_bytes(self.report)
        # Byte-integrity fixtures only; no claim these dummy bytes are physical arrays.
        for n in (512,1024):
            (self.out/f'm4c_fields_{n}.npz').write_bytes(b'array integrity fixture')
        self.p = {'completed':True, 'run_id':'this-run', 'evaluated_checkout_sha':head(),
                  'elapsed_s':1., 'peak_rss_bytes_linux':100_000_000,
                  'sha256':{}, 'output_sha256':{p.name:sha(p) for p in self.out.iterdir()},
                  'result_sha256':sha(self.out/'m4c_planar_control.json')}
        self.write()

    def write(self):
        (self.out/'m4c_provenance.json').write_text(json.dumps(self.p))

    def test_expected_stop_requires_fresh_identity(self):
        check_legacy(self.out, 1, 'this-run')
        with self.assertRaisesRegex(ValueError, 'run ID'):
            check_legacy(self.out, 1, 'next-run')

    def test_wrong_head_or_missing_completion_rejected(self):
        for key,value in [('evaluated_checkout_sha','0'*40), ('completed',False)]:
            p = copy.deepcopy(self.p)
            p[key] = value
            with self.assertRaises(ValueError):
                verify(self.out,p,'this-run')

    def test_missing_and_corrupt_raw_outputs_rejected(self):
        raw = self.out/'m4c_fields_512.npz'
        raw.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'Output mismatch'):
            check_legacy(self.out,1,'this-run')
        raw.unlink()
        with self.assertRaises(FileNotFoundError):
            check_legacy(self.out,1,'this-run')

    def test_stale_result_or_changed_source_rejected(self):
        self.p['sha256']['scripts/m4c_planar_control.py'] = '0'*64
        self.write()
        with self.assertRaisesRegex(ValueError,'Source mismatch'):
            check_legacy(self.out,1,'this-run')
        self.p['sha256'] = {}
        self.write()
        (self.out/'m4c_planar_control.json').write_bytes(self.report+b' ')
        with self.assertRaisesRegex(ValueError,'Output mismatch'):
            check_legacy(self.out,1,'this-run')

    def test_unexpected_exit_codes_rejected(self):
        for code in (0,2,-9):
            with self.assertRaisesRegex(ValueError,'exit 1'):
                check_legacy(self.out,code,'this-run')

    def test_importerror_cannot_reuse_prior_run(self):
        child = subprocess.run([sys.executable,'-c','raise ImportError("dependency unavailable")'],
                               capture_output=True,text=True)
        self.assertEqual(child.returncode,1)
        self.assertIn('ImportError',child.stderr)
        # The dangerous case: matching exit 1 with valid outputs from an earlier run.
        with self.assertRaisesRegex(ValueError,'run ID'):
            check_legacy(self.out,child.returncode,'new-run')
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaises(FileNotFoundError):
                check_legacy(Path(empty),child.returncode,'new-run')

    def test_fresh_launcher_refuses_preexisting_directory(self):
        child = subprocess.run([sys.executable,str(ROOT/'scripts/run_m4c_stop.py'),
                                '--output-dir',str(self.out)],capture_output=True,text=True)
        self.assertNotEqual(child.returncode,0)
        self.assertIn('FileExistsError',child.stderr)
        self.assertEqual((self.out/'m4c_planar_control.json').read_bytes(),self.report)


if __name__ == '__main__':
    unittest.main()
