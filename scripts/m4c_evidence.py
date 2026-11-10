"""Small run-identity/hash checks shared by the two bounded controls (no physics)."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def head():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def seal(out, provenance, outputs):
    """Written only after all outputs exist; runner supplies a fresh unpredictable ID."""
    provenance.update(run_id=os.environ.get('M4C_RUN_ID'), completed=True,
                      completed_at_ns=time.time_ns(),
                      output_sha256={name: sha(out/name) for name in outputs})
    for name in ('scripts/m4c_evidence.py', 'scripts/run_m4c_stop.py'):
        provenance['sha256'][name] = sha(ROOT/name)


def verify(out, provenance, run_id=None, expected_head=None):
    require(provenance.get('completed') is True, 'Missing completion marker')
    require(provenance.get('evaluated_checkout_sha') == (expected_head or head()), 'Wrong HEAD')
    if run_id is not None:
        require(provenance.get('run_id') == run_id, 'Stale or missing run ID')
    require(0 <= provenance['elapsed_s'] < 120, 'Time budget exceeded')
    require(0 < provenance['peak_rss_bytes_linux'] < 1_000_000_000, 'Memory budget exceeded')
    require(bool(provenance.get('output_sha256')), 'Missing output manifest')
    for name, digest in provenance['output_sha256'].items():
        require(sha(out/name) == digest, 'Output mismatch: '+name)
    for name, digest in provenance['sha256'].items():
        require(sha(ROOT/name) == digest, 'Source mismatch: '+name)


def check_legacy(out, exit_code, run_id=None):
    require(exit_code == 1, 'Expected frozen Control exit 1')
    r = json.loads((out/'m4c_planar_control.json').read_text())
    p = json.loads((out/'m4c_provenance.json').read_text())
    verify(out, p, run_id)
    require(set(p['output_sha256']) == {'m4c_planar_control.json', 'm4c_fields_512.npz', 'm4c_fields_1024.npz'}, 'Incomplete legacy output manifest')
    require(r['control_id'] == 'M4C-TE-PLANAR-001' and r['status'] == 'Fail', 'Wrong control')
    require(len(r['gates']) == 11 and
            {k for k,v in r['gates'].items() if not v} == {'continuous_flux_angular'},
            'Unexpected failed gates')
    error = r['quadrature_outside_fraction_abs_difference']
    require(error > 0.02 and abs(error-0.027777663568040678) < 1e-12, 'Changed historical error')
    require(max(r['quadrature_relative_difference'].values()) < 1e-4, 'Unexpected smooth error')
    require(r['actual_overlap'] is None and r['total_coupling'] is None and
            r['actual_external_field'] == 'Uncomputed' and
            r['full_package_feasibility'] == 'Uncomputed', 'Changed actual performance state')
    require(sha(out/'m4c_planar_control.json') == p['result_sha256'], 'Wrong result digest')
    return p
