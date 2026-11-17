"""Isolated installed worker; immutable request and atomic evidence publication."""
import hashlib
import json
from pathlib import Path
import sys

from .near_match import run_workflow


def fingerprint():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(__file__).parent.glob('*.py'))}


def atomic_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')
    temporary.replace(path)


def main():
    directory = Path(sys.argv[1])
    request = json.loads((directory / 'request.json').read_text())
    identity = request['identity']
    document, exact = request['document'], request['exact']
    before = fingerprint()
    try:
        digest = hashlib.sha256(json.dumps(document, sort_keys=True, allow_nan=False).encode()).hexdigest()
        if digest != identity['input_sha256'] or exact['input_snapshot'] != document or exact['input_sha256'] != digest:
            raise ValueError('Worker input snapshot/SHA mismatch')

        def progress(value):
            atomic_json(directory / 'progress.json', {
                'completed_geometries': len(value['geometries']),
                'geometry_count': value['geometry_count'], 'adapter_calls': value['adapter_calls'],
                'maximum_adapter_calls': value['maximum_adapter_calls']})

        report = run_workflow(document, exact_result=exact,
                              cancelled=lambda: (directory / 'cancel').exists(), progress=progress)
        if fingerprint() != before:
            raise RuntimeError('Application source changed during execution')
        if (directory / 'cancel').exists():
            report.update(state='Cancelled', design_result=None)
        report.update(identity=identity, source_sha256=before)
    except Exception as error:
        report = {'state': 'Failed', 'error': repr(error), 'design_result': None,
                  'identity': identity, 'source_sha256': before}
    atomic_json(directory / 'worker.json', report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
