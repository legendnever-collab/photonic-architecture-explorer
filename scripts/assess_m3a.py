"""Reproducible external adapter evidence using explicit synthetic data only."""

import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from photonic_architecture_explorer.external import evaluate_external


def run():
    path = ROOT/'examples/m3a_synthetic.json'
    data = json.loads(path.read_text())
    nominal = evaluate_external(data)
    blank = evaluate_external(json.loads((ROOT/'examples/external_ports_unprovided.json').read_text()))
    controls = []

    def changes(before, after, path=''):
        if isinstance(before, dict) and isinstance(after, dict):
            output = []
            for key in sorted(before.keys() | after.keys()):
                label = f'{path}.{key}' if path else key
                if key not in after:
                    output.append({'op': 'remove', 'path': label})
                elif key not in before:
                    output.append({'op': 'add', 'path': label, 'value': after[key]})
                else:
                    output.extend(changes(before[key], after[key], label))
            return output
        return [] if before == after else [{'op': 'replace', 'path': path, 'value': after}]

    for name in ('missing_phase', 'bad_unit', 'guided_index', 'high_divergence', 'curvature_bounds', 'chief_keepout'):
        altered = copy.deepcopy(data)
        if name == 'missing_phase':
            del altered['source']['wavefront_curvature_ts_per_m']
            del altered['source']['complex_q_ts_m']
        elif name == 'bad_unit': altered['source']['position_m']['unit'] = 'mm'
        elif name == 'guided_index': altered['ambient_index']['quantity'] = 'guided_effective_index'
        elif name == 'high_divergence':
            del altered['source']['complex_q_ts_m']
            altered['source']['mfd_ts_m']['value'] = [2e-6, 2e-6]
        elif name == 'curvature_bounds':
            altered['reflectors'][0]['principal_curvature_bounds_per_m']['value'] = [[0, 1], [0, 1]]
        elif name == 'chief_keepout':
            altered['package']['keepout_bodies']['value'] = [
                {'type': 'aabb', 'min_m': [.0001, -1e-5, -1e-5], 'max_m': [.0002, 1e-5, 1e-5]}]
        result = evaluate_external(altered)
        controls.append({'name': name, 'input_changes_from_synthetic_fixture': changes(data, altered),
                         'states': {key: result[key]['status'] for key in (
                             'input_contract', 'geometry', 'model_domain', 'design_constraints', 'package_feasibility')},
                         'normalized_mode_overlap': result['gaussian_mode_matching']['normalized_mode_overlap']})
    passed = (nominal['geometry']['status'] == 'Pass' and nominal['model_domain']['status'] == 'Pass'
              and nominal['design_constraints']['status'] == 'Pass'
              and nominal['gaussian_mode_matching']['status'] == 'Approximate'
              and abs(nominal['gaussian_mode_matching']['normalized_mode_overlap']-1) < 1e-10
              and nominal['package_feasibility']['envelope_geometry']['status'] == 'Pass'
              and nominal['package_feasibility']['status'] == 'Uncomputed'
              and blank['input_contract']['status'] == 'Uncomputed'
              and blank['gaussian_mode_matching']['normalized_mode_overlap'] is None
              and all(c['normalized_mode_overlap'] is None for c in controls))
    return {'assessment_id': 'M3A-001', 'base_sha': '17bd1ad6bfa5715f6371fe0e41f52a6d1a93e199',
            'units': 'm, rad, m^-1, dimensionless n',
            'assumptions': 'synthetic external Gaussian M1-001 fields; synthetic declared package envelopes/clearance, polarization explicitly ignored',
            'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'completion_gate': {'status': 'Pass' if passed else 'Fail', 'scope': 'adapter controls, not actual engineering acceptance'},
            'synthetic_nominal': nominal, 'unprovided_actual': blank, 'rejection_controls': controls}


if __name__ == '__main__':
    report = run()
    (ROOT/'results/m3a_001.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print('M3-A adapter gate:', report['completion_gate']['status'])
    raise SystemExit(report['completion_gate']['status'] != 'Pass')
