"""CI evidence check: preserve the known failed Control, never label it Pass."""
import hashlib
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[1]
r=json.loads((root/'results/m4c_planar_control.json').read_text())
p=json.loads((root/'results/m4c_provenance.json').read_text())
assert len(sys.argv)==2 and int(sys.argv[1])==1, 'Control must exit 1 at its frozen stop'
assert r['status']=='Fail'
assert {k for k,v in r['gates'].items() if not v}=={'continuous_flux_angular'}
assert r['quadrature_outside_fraction_abs_difference']>0.02
assert max(r['quadrature_relative_difference'].values())<1e-4
assert r['actual_overlap'] is None and r['total_coupling'] is None
assert r['actual_external_field']=='Uncomputed'
assert p['elapsed_s']<120 and p['peak_rss_bytes_linux']<1_000_000_000
assert hashlib.sha256((root/'results/m4c_planar_control.json').read_bytes()).hexdigest()==p['result_sha256']
for path,digest in p['sha256'].items():
    assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
(root/'results/m4c_execution.json').write_text(json.dumps({
    'evidence_check':'Pass','control_acceptance':'Fail','control_exit_code':1,
    'stop_reason':'angular-bin tail fraction exceeds frozen 0.02 absolute error budget',
    'evaluated_checkout_sha':p['evaluated_checkout_sha'],
    'actual_device_performance':'Uncomputed'},indent=2)+'\n')
print('Evidence preserved: Control FAIL / stopped; actual performance Uncomputed.')
