"""Bounded M2.5 assessment, with synthetic inputs only. No actual Port defaults."""

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from photonic_architecture_explorer.applicability import gaussian_port_domain, residual_scale_comparison


def run():
    fixture = json.loads((ROOT/'examples/m1_001.json').read_text())
    m2 = json.loads((ROOT/'results/m2_001.json').read_text())
    actual = json.loads((ROOT/'examples/external_ports_unprovided.json').read_text())
    missing = []
    populated = []

    def collect(value, path=''):
        if isinstance(value, dict) and 'provenance' in value:
            if value['value'] is None:
                missing.append(path)
            else:
                populated.append(path)
        elif isinstance(value, dict):
            for key, item in value.items():
                collect(item, f'{path}.{key}' if path else key)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                collect(item, f'{path}[{i}]')

    collect(actual)
    # This fixed report intentionally consumes only the blank contract. A future
    # external adapter must validate all fields before accepting populated data.
    if not missing or populated:
        raise ValueError('M2.5 report is not an external-input evaluator')
    wave, index = fixture['wavelength_m'], fixture['medium_index']
    radii = fixture['target']['waist_radii_m']
    return {
        'assessment_id': 'M25-001', 'units': 'm, rad, inverse m, dimensionless n',
        'synthetic_inputs': {'fixture': 'examples/m1_001.json', 'assumptions': 'fixed M1 waist fields, homogeneous ambient, scalar paraxial; not actual SSC data'},
        'base_m2_sha': '074930aab1b941d58c428b0644c1553dd23e9271',
        'actual_applicability': {'status': 'Uncomputed', 'missing_inputs': missing},
        'development_decision': {'path': 'B', 'meaning': 'bounded extension required for engineering goal; actual applicability not decided'},
        'synthetic_port_precheck': gaussian_port_domain(wave, index, [2*w for w in radii], [0., 0.]),
        'synthetic_waist_mfd_guard_min_m': 2*wave/(math.pi*index*0.1),
        'guard_note': 'waist only, homogeneous ambient, each axis; necessary not sufficient',
        'finite_footprint_scale': [
            {'extent_beam_radii': fan['extent_beam_radii'],
             **residual_scale_comparison(fan['max_transverse_residual_m'], radii)}
            for fan in m2['finite_fans']['curved']],
        'actual_finite_footprint_significance': {'status': 'Uncomputed', 'reason': 'M2 residual cannot transfer to different modes or geometry'},
        'geometry_package': {'status': 'Uncomputed', 'reason': 'no available volume, body or reflector constraints supplied'},
        'actual_mode_gaussian_fit': {'status': 'Uncomputed', 'reason': 'no complex external field or fit reference'},
        'total_coupling': {'status': 'Uncomputed'},
    }


if __name__ == '__main__':
    path = ROOT/'results/m25_001.json'
    path.write_text(json.dumps(run(), indent=2, allow_nan=False)+'\n')
    print('M2.5 actual applicability: Uncomputed; development path B')
