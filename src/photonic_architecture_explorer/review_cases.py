"""Fixed synthetic M3-B review controls evaluated through the existing Adapter.

Moved from the retired HTML Inspector (P1). Used by scripts/validate.py evidence.
"""

import copy
import json
from pathlib import Path

from .external import adapt_external, evaluate_external

ROOT = Path(__file__).resolve().parents[2]


def review_cases(root=ROOT):
    """Fixed synthetic review controls; no search or automatic design changes."""
    nominal = json.loads((root/'examples/m3a_synthetic.json').read_text())
    blank = json.loads((root/'examples/external_ports_unprovided.json').read_text())
    cases = [('nominal', 'Synthetic Relay', nominal), ('blank', 'Actual Ports · 미제공', blank)]
    for key, title in (
        ('missing-phase', 'Missing Phase'), ('bad-unit', '잘못된 단위'),
        ('target-direction', '잘못된 Target Direction'), ('high-divergence', 'High Divergence'),
        ('bounds-fail', 'Bounds Fail'), ('package-fail', 'Package Fail')):
        data = copy.deepcopy(nominal)
        if key == 'missing-phase':
            del data['source']['wavefront_curvature_ts_per_m']; del data['source']['complex_q_ts_m']
        elif key == 'bad-unit': data['source']['position_m']['unit'] = 'mm'
        elif key == 'target-direction':
            data['target']['propagation_direction']['value'] = [-1, 0, 0]
            data['target']['reference_plane']['value']['normal'] = [-1, 0, 0]
        elif key == 'high-divergence':
            del data['source']['complex_q_ts_m']; data['source']['mfd_ts_m']['value'] = [2e-6, 2e-6]
        elif key == 'bounds-fail':
            data['reflectors'][0]['principal_curvature_bounds_per_m']['value'] = [[0, 1], [0, 1]]
        elif key == 'package-fail':
            data['package']['available_volume']['value'] = {
                'type': 'aabb', 'min_m': [-.0001, -.0001, -.0001], 'max_m': [.0021, .0001, .0021]}
        cases.append((key, title, data))
    return cases


def evaluate_view(document, error=None):
    """One fresh Adapter evaluation; no persisted previous result or fitted Port."""
    result = evaluate_external(document if error is None else {})
    if error is not None:
        result['input_contract'] = {'status': 'Fail', 'path': 'JSON editor', 'reason': str(error)}
    adapted = None
    if result['input_contract']['status'] == 'Pass': adapted = adapt_external(document)
    return result, adapted
