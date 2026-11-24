"""P4b alignment study: linear chief-ray model against the non-paraxial computation, compensation, document."""

import json
import math
import pathlib
import sys
import unittest

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from photonic_architecture_explorer import alignment as A, api, lens as L, nonparaxial as N  # noqa: E402
from photonic_architecture_explorer.design_document import (search_constraints, to_engine_input,  # noqa: E402
                                                             validate_document)
from photonic_architecture_explorer.freeform import POSE_GRID  # noqa: E402

SCENARIOS = ROOT / 'src' / 'photonic_architecture_explorer' / 'scenarios'


def load(name):
    return json.loads((SCENARIOS / f'{name}.json').read_text(encoding='utf-8'))


def moved(system, errors):
    elements = []
    for b, body in enumerate(system.bodies):
        current = body
        for dof in range(5):
            current = A.Body(current.label, current.kind, current.moved(dof, errors[5 * b + dof]), current.pivot,
                             current.translations, current.rotations)
        elements += current.elements
    return elements


def nonparaxial_loss_db(system, elements):
    def eta(e):
        f = N.field(*system.args[:8], e, *system.args[8:], grid=POSE_GRID)
        return abs((f['amplitude'] * np.exp(1j * f['phase'])).sum()) ** 2 / f['norm']
    return -10 * math.log10(eta(elements) / eta(system.elements()))


class GaussianFormTest(unittest.TestCase):
    def test_offset_and_tilt_at_a_waist(self):
        lam, w = 1.31e-6, 4.6e-6
        k = 2 * math.pi / lam
        Q = np.diag([-1j * lam / (math.pi * w ** 2)] * 2)
        G = A.gaussian_loss(Q, k)
        self.assertAlmostEqual(G[0, 0], 1 / w ** 2, delta=1e-6 / w ** 2)                # η = exp(−d²/w²)
        self.assertAlmostEqual(G[2, 2], (math.pi * w / lam) ** 2, delta=1e-6 * (math.pi * w / lam) ** 2)
        self.assertAlmostEqual(G[0, 2], 0.0, delta=1e-9 / w ** 2)                         # no cross term at a waist


class LensSystemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        doc = load('S3')
        family = L.lens_family(to_engine_input(doc), search_constraints(doc), cases=1)
        row = next(r for run in family['runs'] for r in run['candidates'] if 'args' in r)
        cls.row = row
        cls.system = A.lens_system(row['args'], row['lens_objects'], row['mirror_elements'])

    def test_linear_model_matches_nonparaxial_for_simultaneous_errors(self):
        limit = A.bounds(self.system.bodies, A.TOLERANCE_DEFAULTS)
        rng = np.random.default_rng(7)
        for _ in range(3):
            errors = rng.uniform(-0.5, 0.5, len(limit)) * limit
            linear = A.loss_db(self.system, errors)
            exact = nonparaxial_loss_db(self.system, moved(self.system, errors))
            self.assertAlmostEqual(linear, exact, delta=0.15 * exact + 0.05)

    def test_single_lens_decenter_matches_the_pose_study(self):
        study = A.study(self.system)
        decenter = max(s['loss_db'] for s in study['single'] if s['body'] == 'L1' and s['dof'] in ('t1', 't2'))
        self.assertAlmostEqual(decenter, self.row['pose']['lenses'][0]['decenter_loss_db'], delta=0.15 * decenter)

    def test_active_alignment_beats_passive(self):
        study = A.study(self.system)
        self.assertLess(study['passive']['yield_1db'], 0.5)
        best = study['best_compensator']
        self.assertTrue(best['practical'])
        self.assertLess(best['p90_db'], 0.5)
        self.assertTrue(all(o['p90_db'] >= best['p90_db'] for o in study['active'] if o['practical']))
        tight = A.study(self.system, {k: v / 10 for k, v in A.TOLERANCE_DEFAULTS.items()})
        self.assertGreater(tight['passive']['yield_1db'], study['passive']['yield_1db'])  # tighter parts, better yield


class MirrorSystemTest(unittest.TestCase):
    def test_qtensor_candidate_linear_model(self):
        result = api.design(load('S4'))
        candidate = result['candidates'][0]
        self.assertGreater(candidate['alignment']['passive']['p90_db'], 1.0)
        self.assertLess(candidate['alignment']['best_compensator']['p90_db'], 0.5)
        from photonic_architecture_explorer.design_document import to_engine_problem
        from photonic_architecture_explorer.search import design_continuous
        doc = load('S4')
        problem = to_engine_problem(doc)
        report = design_continuous(problem['engine'], search_constraints(doc), include_map=False, nonparaxial_checks=False)
        system = A.mirror_system(report['candidates'][0], problem['engine'])
        errors = np.array([2e-6, -1e-6, 1e-6, 2e-4, -3e-4, -1e-6, 2e-6, 0.0, -2e-4, 1e-4])
        self.assertAlmostEqual(A.loss_db(system, errors), nonparaxial_loss_db(system, moved(system, errors)),
                               delta=0.15 * A.loss_db(system, errors) + 0.05)


class WhatIfTest(unittest.TestCase):
    def test_shallow_iox_needs_a_deeper_waveguide_not_thicker_glass(self):
        result = api.whatif(load('S2b-1550-glass'))
        rows = {r['parameter']: r for r in result['whatif']['rows']}
        self.assertEqual(rows['target_depth']['status'], 'Found')
        self.assertLessEqual(rows['target_depth']['found_mm'], 0.4)
        self.assertGreater(rows['target_depth']['found_mm'], 0.1)
        self.assertEqual(rows['block_thickness']['status'], 'Not found')  # up to 3.3 mm does not help
        self.assertIsNone(api.whatif(load('S1'))['whatif'])                # no Glass, nothing to vary


class DocumentTest(unittest.TestCase):
    def test_tolerance_validation(self):
        doc = load('S1')
        doc['tolerances'] = {'mirror_translation_um': 2, 'bond_rotation_mrad': 0.01}
        self.assertEqual(validate_document(doc), [])
        doc['tolerances'] = {'mirror_translation_um': -1, 'glue': 3}
        self.assertEqual({i['path'] for i in validate_document(doc)}, {'tolerances', 'tolerances.mirror_translation_um'})


if __name__ == '__main__':
    unittest.main()
