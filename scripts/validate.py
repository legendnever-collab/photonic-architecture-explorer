"""Reproduce the benchmark and record tests with hashes of the evaluated files."""

import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import os

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from photonic_architecture_explorer.benchmark import run
from photonic_architecture_explorer.diagnostics import run as run_m2
from assess_m25 import run as run_m25
from assess_m3a import run as run_m3a


def main():
    checkout_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty_before = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    results = ROOT/'results'
    results.mkdir(exist_ok=True)
    benchmark = run(ROOT/'examples/m1_001.json')
    (results/'m1_001.json').write_text(json.dumps(benchmark, indent=2, allow_nan=False)+'\n')
    m2 = run_m2(ROOT/'examples/m1_001.json')
    (results/'m2_001.json').write_text(json.dumps(m2, indent=2, allow_nan=False)+'\n')
    m25 = run_m25()
    (results/'m25_001.json').write_text(json.dumps(m25, indent=2, allow_nan=False)+'\n')
    m3a = run_m3a()
    (results/'m3a_001.json').write_text(json.dumps(m3a, indent=2, allow_nan=False)+'\n')
    env = {**os.environ, 'PYTHONPATH': str(ROOT/'src')}
    tests = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                           cwd=ROOT, env=env, capture_output=True, text=True)
    output = tests.stdout+tests.stderr
    (results/'unittest.txt').write_text(output)
    paths = sorted(p for folder in ('src', 'tests', 'examples', 'scripts')
                   for p in (ROOT/folder).rglob('*') if p.suffix in ('.py', '.json'))
    paths += [ROOT/'pyproject.toml', ROOT/'docs/M1_BENCHMARK.md', ROOT/'docs/M2_CONTRACT.md',
              ROOT/'docs/M25_CONTRACT.md', ROOT/'docs/EXTERNAL_PORT_CONTRACT.md',
              ROOT/'docs/M25_ASSESSMENT.md', ROOT/'docs/M3A_CONTRACT.md',
              ROOT/'docs/M3A_ADAPTER.md', ROOT/'.github/workflows/validate.yml']
    import numpy
    evidence = {'python': platform.python_version(), 'numpy': numpy.__version__,
                'test_command': 'python -m unittest discover -s tests -v',
                'test_exit_code': tests.returncode,
                'evaluated_checkout_sha': checkout_sha,
                'checkout_dirty_before_run': dirty_before,
                'm25_actual_applicability': m25['actual_applicability']['status'],
                'm3a_adapter_gate': m3a['completion_gate'],
                'benchmark_gate': benchmark['completion_gate'],
                'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (results/'validation.json').write_text(json.dumps(evidence, indent=2)+'\n')
    print(output, end='')
    print('Benchmark gate:', benchmark['completion_gate']['status'])
    print('M3-A adapter gate:', m3a['completion_gate']['status'])
    return tests.returncode or (benchmark['completion_gate']['status'] != 'Pass') or (m3a['completion_gate']['status'] != 'Pass')


if __name__ == '__main__':
    raise SystemExit(main())
