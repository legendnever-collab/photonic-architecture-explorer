"""Regenerate the User Decision Benchmark fixtures (scenarios/*.json and index.json).

Placements are synthetic and labelled so; Mode widths come from the public Mode Library
presets. Run after changing presets or scenario definitions, then run the tests, which
check every expectation recorded in the index.
"""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from photonic_architecture_explorer.api import design  # noqa: E402
from photonic_architecture_explorer.design_document import SCHEMA  # noqa: E402
from photonic_architecture_explorer.presets import port_from_preset  # noqa: E402

OUT = ROOT / 'src/photonic_architecture_explorer/scenarios'
X, Y, Z = [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]
PLACEMENT = 'Synthetic scenario placement (not a package drawing)'


def doc(scenario, title, wavelength, source, target, description):
    return {'schema': SCHEMA, 'title': title, 'scenario': scenario, 'description': description,
            'wavelength_nm': wavelength, 'ambient_index': 1.0,
            'ports': {'source': source, 'target': target}}


def port(preset, position, direction, sagittal=Y, label=None):
    item = port_from_preset(preset, position_mm=position, direction=direction, sagittal_axis=sagittal,
                            t_is='vertical', placement_source=PLACEMENT)
    if label:
        item['label'] = label
    return item


def synthetic_port(label, mfd, position, direction, sagittal=Y, note=''):
    return {'label': label, 'preset': None, 'position_mm': position, 'direction': direction,
            'sagittal_axis': sagittal, 'mfd_um': mfd, 'wavefront_curvature_per_m': [0.0, 0.0],
            'evidence': {'placement': {'provenance': 'synthetic', 'source': PLACEMENT},
                         'mode': {'provenance': 'synthetic', 'source': note},
                         'phase': {'provenance': 'synthetic', 'source': 'Flat phase, synthetic assumption'}}}


SCENARIOS = [
    ('S1', 'S1 · SMF → SMF, 공기 중 90° Fold', 'S1.json', 'Tool sanity check against a known exact-q relay',
     doc('S1', 'S1 · SMF-28 → SMF-28, 90° Fold', 1310.0,
         port('smf28-ultra-1310', [0, 0, 0], X), port('smf28-ultra-1310', [2.0, 0, 2.0], Z),
         'Source travels +X, Target arrives travelling +Z; both SMF-28 Ultra 1310 nm.'),
     {'status': 'Computed', 'min_candidates': 1, 'target': {'status': 'Computed', 'phase': 'P0'}}),
    ('S2a-1310', 'S2a · SMF → LDW Glass WG (1310 nm)', 'S2a-1310.json',
     'Mode size and ellipticity conversion into a laser-written glass guide',
     doc('S2a-1310', 'S2a · SMF-28 → LDW (Sun 2021), 1310 nm', 1310.0,
         port('smf28-ultra-1310', [0, 0, 0], X), port('sun-fldw-55mw-1310', [3.0, 0, 1.0], X),
         'Edge coupling in air: fiber at the origin, glass facet 3 mm ahead and 1 mm higher.'),
     {'status': 'Fail', 'reason_contains': 'bounded exact-q family', 'target': {'status': 'Computed', 'phase': 'P2'}}),
    ('S2a-1550', 'S2a · SMF → LDW Glass WG (1550 nm)', 'S2a-1550.json',
     'Mode size and ellipticity conversion into a laser-written glass guide',
     doc('S2a-1550', 'S2a · SMF-28 → LDW (Desmet 2021), 1550 nm', 1550.0,
         port('smf28-ultra-1550', [0, 0, 0], X), port('desmet-fldw-1550', [3.0, 0, 1.0], X),
         'Edge coupling in air: fiber at the origin, glass facet 3 mm ahead and 1 mm higher.'),
     {'status': 'Fail', 'reason_contains': 'bounded exact-q family', 'target': {'status': 'Computed', 'phase': 'P2'}}),
    ('S2b-1550', 'S2b · SMF → IOX Glass WG (1550 nm)', 'S2b-1550.json',
     'Asymmetric elliptical mode conversion into an ion-exchanged glass guide',
     doc('S2b-1550', 'S2b · SMF-28 → IOX (Brusberg 2012), 1550 nm', 1550.0,
         port('smf28-ultra-1550', [0, 0, 0], X), port('brusberg-iox-1550', [3.0, 0, 1.0], X),
         'Edge coupling in air: fiber at the origin, glass facet 3 mm ahead and 1 mm higher.'),
     {'status': 'Fail', 'reason_contains': 'bounded exact-q family', 'target': {'status': 'Computed', 'phase': 'P2'}}),
    ('S3', 'S3 · SiPh SSC → SMF', 'S3.json', 'Which structure can relay a 3 µm SSC mode (needs P3/P4)',
     doc('S3', 'S3 · SiPh SSC class (3 µm) → SMF-28, 1310 nm', 1310.0,
         port('synthetic-siph-ssc-3um', [0, 0, 0], X), port('smf28-ultra-1310', [3.0, 0, 1.0], X),
         'SSC-class synthetic mode in air; expected to exceed the paraxial divergence guard.'),
     {'status': 'Fail', 'reason_contains': 'divergence', 'target': {'status': 'Computed', 'phase': 'P3-P4'}}),
    ('S4', 'S4 · PIC Edge → 수직 Fiber (평면 밖 전환)', 'S4.json', 'Out-of-plane turn (needs 3D q-tensor, P3)',
     doc('S4', 'S4 · PIC edge (+X) → vertical fiber (+Z) offset in Y', 1310.0,
         synthetic_port('PIC edge, SMF-matched mode (Synthetic)', [9.2, 9.2], [0, 0, 0], X,
                        note='Synthetic SMF-sized edge mode to isolate the geometric limitation'),
         port('smf28-ultra-1310', [2.0, 1.0, 1.5], Z, sagittal=Y),
         'The fiber is offset sideways, so no single fold plane contains both Ports.'),
     {'status': 'Fail', 'reason_contains': 'noncoplanar', 'target': {'status': 'Computed', 'phase': 'P3'}}),
    ('S5', 'S5 · Laser → PIC SSC', 'S5.json', 'Elliptical laser mode conversion (needs P4)',
     doc('S5', 'S5 · DFB laser class (1.5 × 3.5 µm) → SSC class (3 µm), 1310 nm', 1310.0,
         synthetic_port('DFB laser class (Synthetic)', [1.5, 3.5], [0, 0, 0], X,
                        note='Representative laser-class elliptical mode; not a specific device'),
         port('synthetic-siph-ssc-3um', [1.0, 0, 0.5], X),
         'Both modes are far outside the paraxial divergence guard.'),
     {'status': 'Fail', 'reason_contains': 'divergence', 'target': {'status': 'Computed', 'phase': 'P4'}}),
]

UNSUPPORTED = [
    {'id': 'S6', 'title': 'S6 · Channel 배열 → FAU', 'file': None,
     'decision': 'Channel-to-channel variation through shared optics (P6 or later)',
     'expect': {'status': 'Unsupported', 'reason': 'Multi-channel arrays are outside the two-Port model', 'target': {'status': 'Computed', 'phase': 'P6'}}},
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for sid, title, filename, decision, document, expect in SCENARIOS:
        (OUT / filename).write_text(json.dumps(document, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        result = design(document)
        observed = {'status': result['status'], 'candidates': len(result['candidates']),
                    'reason': result.get('reason')}
        ok = observed['status'] == expect['status'] and (
            observed['candidates'] >= expect.get('min_candidates', 0)) and (
            expect.get('reason_contains', '') in (observed['reason'] or ''))
        print(f'{sid:9s} {observed["status"]:9s} candidates={observed["candidates"]} '
              f'{"OK" if ok else "MISMATCH"}  {observed["reason"]}')
        index.append({'id': sid, 'title': title, 'file': filename, 'decision': decision, 'expect': expect})
    index += UNSUPPORTED
    (OUT / 'index.json').write_text(json.dumps({'schema': 'pae.scenarios/1', 'scenarios': index},
                                               indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
