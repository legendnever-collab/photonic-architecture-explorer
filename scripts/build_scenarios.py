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


def silica_index(wavelength_um):
    """Malitson (1965) three-term Sellmeier fit for fused silica, 20 °C."""
    b, c = (0.6961663, 0.4079426, 0.8974794), (0.0684043, 0.1162414, 9.896161)
    l2 = wavelength_um ** 2
    return round((1 + sum(bi * l2 / (l2 - ci * ci) for bi, ci in zip(b, c))) ** 0.5, 4)


GLASS = {
    'silica-1310': ('Fused silica', silica_index(1.31), 'measured',
                    'I. H. Malitson, J. Opt. Soc. Am. 55, 1205 (1965), Sellmeier fit evaluated at 1310 nm'),
    'silica-1550': ('Fused silica', silica_index(1.55), 'measured',
                    'I. H. Malitson, J. Opt. Soc. Am. 55, 1205 (1965), Sellmeier fit evaluated at 1550 nm'),
    'd263-1550': ('D 263 T eco (IOX host, assumed index)', 1.511, 'assumed',
                  'Two-term Cauchy extrapolation of SCHOTT D 263 T eco data-sheet nC = 1.5204, nF = 1.5300 '
                  'to 1550 nm; uncertainty about ±0.01; ion-exchange index change ignored'),
}


def glass_doc(scenario, title, wavelength, glass, thickness, source_preset, target_preset, depth, description,
              lateral=2.0, gap=0.1, lateral_y=0):
    """Vertical fiber above a glass top surface (z = 0, normal +Z) feeding a buried guide that runs +X."""
    label, index, provenance, citation = GLASS[glass]
    target = port(target_preset, [lateral, lateral_y, -depth], X)
    target['medium'] = 'block'
    return {**doc(scenario, title, wavelength, port(source_preset, [0, 0, gap], [0.0, 0.0, -1.0]), target, description),
            'medium_block': {'label': label, 'index': index, 'surface_point_mm': [0.0, 0.0, 0.0],
                             'surface_normal': [0.0, 0.0, 1.0], 'thickness_mm': thickness,
                             'index_source': {'provenance': provenance, 'source': citation}}}


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
     {'status': 'Computed', 'min_candidates': 3, 'family': 'exact', 'target': {'status': 'Computed', 'phase': 'P0'}}),
    ('S2a-1310', 'S2a · SMF → LDW Glass WG (1310 nm)', 'S2a-1310.json',
     'Mode size and ellipticity conversion into a laser-written glass guide',
     doc('S2a-1310', 'S2a · SMF-28 → LDW (Sun 2021), 1310 nm', 1310.0,
         port('smf28-ultra-1310', [0, 0, 0], X), port('sun-fldw-55mw-1310', [3.0, 0, 1.0], X),
         'Edge coupling in air: fiber at the origin, glass facet 3 mm ahead and 1 mm higher.'),
     {'status': 'Computed', 'min_candidates': 3, 'family': 'near_match', 'reason_contains': 'Near-match', 'target': {'status': 'Computed', 'family': 'exact', 'phase': 'P3'}}),
    ('S2a-1550', 'S2a · SMF → LDW Glass WG (1550 nm)', 'S2a-1550.json',
     'Mode size and ellipticity conversion into a laser-written glass guide',
     doc('S2a-1550', 'S2a · SMF-28 → LDW (Desmet 2021), 1550 nm', 1550.0,
         port('smf28-ultra-1550', [0, 0, 0], X), port('desmet-fldw-1550', [3.0, 0, 1.0], X),
         'Edge coupling in air: fiber at the origin, glass facet 3 mm ahead and 1 mm higher.'),
     {'status': 'Computed', 'min_candidates': 3, 'family': 'exact', 'target': {'status': 'Computed', 'phase': 'P2'}}),
    ('S2b-1550', 'S2b · SMF → IOX Glass WG (1550 nm)', 'S2b-1550.json',
     'Asymmetric elliptical mode conversion into an ion-exchanged glass guide',
     doc('S2b-1550', 'S2b · SMF-28 → IOX (Brusberg 2012), 1550 nm', 1550.0,
         port('smf28-ultra-1550', [0, 0, 0], X), port('brusberg-iox-1550', [3.0, 0, 1.0], X),
         'Edge coupling in air: fiber at the origin, glass facet 3 mm ahead and 1 mm higher.'),
     {'status': 'Computed', 'min_candidates': 3, 'family': 'near_match', 'reason_contains': 'Near-match', 'target': {'status': 'Computed', 'family': 'exact', 'phase': 'P3'}}),
    ('S2a-1310-glass', 'S2a · 수직 SMF → Glass 상면 → 매립 LDW (1310 nm, 1.1 mm)', 'S2a-1310-glass.json',
     'Same Mode pair as S2a-1310, but the relay runs inside the glass block',
     glass_doc('S2a-1310-glass', 'S2a · vertical SMF-28 → fused-silica top → buried LDW (Sun 2021), 1310 nm', 1310.0,
               'silica-1310', 1.1, 'smf28-ultra-1310', 'sun-fldw-55mw-1310', 0.5,
               'Fiber 0.1 mm above a 1.1 mm fused-silica block; guide 0.5 mm deep, 2 mm to the side (all assumed).'),
     {'status': 'Computed', 'min_candidates': 1, 'family': 'near_match', 'reason_contains': 'Near-match',
      'target': {'status': 'Computed', 'phase': 'P3'}}),
    ('S2a-1550-glass', 'S2a · 수직 SMF → Glass 상면 → 매립 LDW (1550 nm, 2.0 mm)', 'S2a-1550-glass.json',
     'Same Mode pair as S2a-1550, relay inside a thicker glass block',
     glass_doc('S2a-1550-glass', 'S2a · vertical SMF-28 → fused-silica top → buried LDW (Desmet 2021), 1550 nm', 1550.0,
               'silica-1550', 2.0, 'smf28-ultra-1550', 'desmet-fldw-1550', 0.5,
               'Fiber 0.1 mm above a 2.0 mm fused-silica block; guide 0.5 mm deep, 2 mm to the side (all assumed). '
               'With 1.1 mm the family has no candidate.'),
     {'status': 'Computed', 'min_candidates': 3, 'family': 'exact', 'target': {'status': 'Computed', 'phase': 'P3'}}),
    ('S2b-1550-glass', 'S2b · 수직 SMF → Glass 상면 → 얕은 IOX (1550 nm)', 'S2b-1550-glass.json',
     'Can a shallow ion-exchanged guide be fed from above with two in-glass reflectors?',
     glass_doc('S2b-1550-glass', 'S2b · vertical SMF-28 → D 263 top → shallow IOX (Brusberg 2012), 1550 nm', 1550.0,
               'd263-1550', 1.1, 'smf28-ultra-1550', 'brusberg-iox-1550', 0.02,
               'Guide 20 µm below the surface (class value, assumed). The reflector on the guide axis would '
               'have to sit inside 20 µm of glass.'),
     {'status': 'Fail', 'reason_contains': 'No valid two-reflector', 'target': {'status': 'Computed', 'phase': 'P4'}}),
    ('S2b-1550-glass-deep', 'S2b · 수직 SMF → Glass 상면 → 깊게 매립한 IOX 가정 (0.3 mm, 2.0 mm)', 'S2b-1550-glass-deep.json',
     'What burial depth and glass thickness would let the in-glass two-reflector family reach an IOX guide?',
     glass_doc('S2b-1550-glass-deep', 'S2b · vertical SMF-28 → D 263-index glass top → IOX buried 0.3 mm (hypothetical)', 1550.0,
               'd263-1550', 2.0, 'smf28-ultra-1550', 'brusberg-iox-1550', 0.3,
               'Hypothetical 0.3 mm burial in 2.0 mm of glass with the D 263 index, to show what the family needs; '
               'neither value is a process or product claim. With 1.1 mm the family has no candidate at any depth tried.'),
     {'status': 'Computed', 'min_candidates': 3, 'family': 'exact', 'target': {'status': 'Computed', 'phase': 'P3'}}),
    ('S3', 'S3 · SiPh SSC → SMF', 'S3.json', 'Which structure can relay a 3 µm SSC mode (needs P3/P4)',
     doc('S3', 'S3 · SiPh SSC class (3 µm) → SMF-28, 1310 nm', 1310.0,
         port('synthetic-siph-ssc-3um', [0, 0, 0], X), port('smf28-ultra-1310', [3.0, 0, 1.0], X),
         'SSC-class synthetic mode in air; expected to exceed the paraxial divergence guard.'),
     {'status': 'Computed', 'min_candidates': 1, 'family': 'lens_two_reflector', 'reason_contains': 'divergence',
      'target': {'status': 'Computed', 'phase': 'P4'}}),
    ('S4', 'S4 · PIC Edge → 수직 Fiber (평면 밖 전환)', 'S4.json', 'Out-of-plane turn (needs 3D q-tensor, P3)',
     doc('S4', 'S4 · PIC edge (+X) → vertical fiber (+Z) offset in Y', 1310.0,
         synthetic_port('PIC edge, SMF-matched mode (Synthetic)', [9.2, 9.2], [0, 0, 0], X,
                        note='Synthetic SMF-sized edge mode to isolate the geometric limitation'),
         port('smf28-ultra-1310', [2.0, 1.0, 1.5], Z, sagittal=Y),
         'The fiber is offset sideways, so no single fold plane contains both Ports.'),
     {'status': 'Computed', 'min_candidates': 3, 'family': 'near_match', 'reason_contains': 'Near-match',
      'target': {'status': 'Computed', 'phase': 'P3'}}),
    ('S4-glass', 'S4 · 수직 SMF → Glass 상면 → 옆으로 비켜 선 매립 LDW (평면 밖, 1550 nm)', 'S4-glass.json',
     'Out-of-plane turn inside glass: q-tensor relay after the surface crossing',
     glass_doc('S4-glass', 'S4 · vertical SMF-28 → fused-silica top → buried LDW offset 1 mm sideways, 1550 nm', 1550.0,
               'silica-1550', 2.0, 'smf28-ultra-1550', 'desmet-fldw-1550', 0.5,
               'Same as S2a-1550-glass but the guide is 1 mm to the side (Y), so the fiber and guide axes are skew '
               '(placement assumed).', lateral_y=1.0),
     {'status': 'Computed', 'min_candidates': 3, 'family': 'exact', 'target': {'status': 'Computed', 'phase': 'P3'}}),
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
                    'reason': result.get('reason'), 'family': result.get('family')}
        ok = observed['status'] == expect['status'] and (
            observed['candidates'] >= expect.get('min_candidates', 0)) and (
            expect.get('reason_contains', '') in (observed['reason'] or '')) and (
            expect.get('family') in (None, observed['family']))
        print(f'{sid:9s} {observed["status"]:9s} {observed["family"] or "-":10s} candidates={observed["candidates"]} '
              f'{"OK" if ok else "MISMATCH"}  {observed["reason"]}')
        index.append({'id': sid, 'title': title, 'file': filename, 'decision': decision, 'expect': expect})
    index += UNSUPPORTED
    (OUT / 'index.json').write_text(json.dumps({'schema': 'pae.scenarios/1', 'scenarios': index},
                                               indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
