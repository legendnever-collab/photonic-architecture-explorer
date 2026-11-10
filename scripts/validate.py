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


def main():
    results = ROOT/'results'
    results.mkdir(exist_ok=True)
    benchmark = run(ROOT/'examples/m1_001.json')
    (results/'m1_001.json').write_text(json.dumps(benchmark, indent=2, allow_nan=False)+'\n')
    env = {**os.environ, 'PYTHONPATH': str(ROOT/'src')}
    tests = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                           cwd=ROOT, env=env, capture_output=True, text=True)
    output = tests.stdout+tests.stderr
    (results/'unittest.txt').write_text(output)
    paths = sorted(p for folder in ('src', 'tests', 'examples', 'scripts')
                   for p in (ROOT/folder).rglob('*') if p.suffix in ('.py', '.json'))
    paths += [ROOT/'pyproject.toml', ROOT/'docs/M1_BENCHMARK.md']
    import numpy
    evidence = {'python': platform.python_version(), 'numpy': numpy.__version__,
                'test_command': 'python -m unittest discover -s tests -v',
                'test_exit_code': tests.returncode,
                'benchmark_gate': benchmark['completion_gate'],
                'sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (results/'validation.json').write_text(json.dumps(evidence, indent=2)+'\n')
    print(output, end='')
    print('Benchmark gate:', benchmark['completion_gate']['status'])
    return tests.returncode or (benchmark['completion_gate']['status'] != 'Pass')


if __name__ == '__main__':
    raise SystemExit(main())
