"""P3 stage 3: non-paraxial scalar check (angular spectrum + exact rays through the patches)."""

import copy
import json
import math
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from photonic_architecture_explorer import api, nonparaxial, qtensor, search  # noqa: E402
from photonic_architecture_explorer.design_document import to_engine_input, to_engine_problem  # noqa: E402
from photonic_architecture_explorer.external import adapt_ports  # noqa: E402

SCENARIOS = ROOT / 'src/photonic_architecture_explorer/scenarios'


def load(name):
    return json.loads((SCENARIOS / f'{name}.json').read_text(encoding='utf-8'))


def flat_relay(w0, wavelength=1.55e-6):
    """S2a-1550 fold with flat reflectors; Target = Source mode propagated (paraxially) over the path."""
    ports = adapt_ports(to_engine_input(load('S2a-1550')))
    vertices, normals, lengths, _ = search.fold(ports, 2e-3, 2e-3)
    mirrors = [nonparaxial.mirror_tuple(vertices[j], normals[j], ports.source.sagittal, (0, 0), (1, 1)) for j in (0, 1)]
    k = 2 * math.pi / wavelength
    q_source = np.diag([1j * k * w0 * w0 / 2] * 2)
    q_target = q_source + sum(lengths) * np.eye(2)
    _, a_s = qtensor.port_beam(ports.source)
    _, a_t = qtensor.port_beam(ports.target)
    args = (q_source, a_s, ports.source.position, ports.source.direction, q_target, a_t, ports.target.position,
            ports.target.direction, mirrors, k, wavelength / (math.pi * w0))
    return args, sum(lengths), k


def direct_free_space(q_source, q_target, k, length, limit, n=401):
    """Exact scalar free-space overlap by direct quadrature of the angular spectra (no rays)."""
    axis = np.linspace(-limit, limit, n)
    uu, vv = np.meshgrid(axis, axis, indexing='ij')
    inside = uu ** 2 + vv ** 2 < limit ** 2
    kz = np.sqrt(np.clip(1 - uu ** 2 - vv ** 2, 0, None))
    uv = np.stack([uu, vv], -1)
    a, b = nonparaxial._spectrum(q_source, k, uv), nonparaxial._spectrum(q_target, k, uv)
    integral = (a * b.conj() * np.exp(-1j * k * kz * length) * inside).sum()
    return abs(integral) ** 2 / ((abs(a) ** 2 * inside).sum() * (abs(b) ** 2 * inside).sum())


class FreeSpaceTest(unittest.TestCase):
    def test_rays_through_flat_reflectors_equal_the_direct_angular_spectrum(self):
        for w0 in (20e-6, 5e-6, 2e-6):
            args, length, k = flat_relay(w0)
            limit = min(nonparaxial.MAX_DIRECTION_COSINE, nonparaxial.SPECTRUM_SIGMAS * args[-1])
            ray = nonparaxial.overlap(*args, grid=401)['eta']
            self.assertAlmostEqual(ray, direct_free_space(args[0], args[4], k, length, limit), delta=2e-3 * ray + 1e-9)

    def test_low_divergence_limit_recovers_the_paraxial_result(self):
        args, _, _ = flat_relay(40e-6)
        self.assertGreater(nonparaxial.check(*args)['normalized_mode_overlap'], 1 - 1e-5)

    def test_non_paraxial_error_grows_with_divergence(self):
        etas = [nonparaxial.check(*flat_relay(w0)[0])['normalized_mode_overlap'] for w0 in (20e-6, 8e-6, 5e-6)]
        self.assertTrue(etas[0] > etas[1] > etas[2])


class AberrationTest(unittest.TestCase):
    """Two equal off-axis reflectors: coma adds when both turn the same way, cancels in a Z fold."""

    def design(self, position, direction):
        doc = copy.deepcopy(load('S1'))
        doc['ports']['target']['position_mm'], doc['ports']['target']['direction'] = position, direction
        return api.design(doc)

    def test_coma_cancels_in_a_z_fold_and_adds_in_a_u_turn(self):
        z_fold = self.design([4.0, 0.0, 2.0], [1.0, 0.0, 0.0])
        same_sense = self.design([2.0, 0.0, 2.0], [0.0, 0.0, 1.0])  # S1
        for c in z_fold['candidates']:
            self.assertGreater(c['metrics']['nonparaxial_overlap'], 0.999)
        for c in same_sense['candidates']:
            self.assertEqual(c['metrics']['normalized_mode_overlap'], 1.0)
            self.assertLess(c['metrics']['nonparaxial_overlap'], 0.7)
        self.assertIn('nonparaxial', {g['kind'] for g in same_sense['guidance']})


class IntegrationTest(unittest.TestCase):
    def test_every_candidate_is_checked_and_the_role_is_on_the_best(self):
        result = api.design(load('S2a-1550'))
        from photonic_architecture_explorer.search import best_nonparaxial_value
        values = [best_nonparaxial_value(c) for c in result['candidates']]  # P4: corrected surface counts if valid
        for c in result['candidates']:
            self.assertEqual(c['nonparaxial_check']['status'], 'Computed')
            self.assertLess(c['nonparaxial_check']['grid_change'], nonparaxial.CONVERGENCE_LIMIT)
        best = [c for c in result['candidates'] if 'best_nonparaxial' in c['roles']]
        self.assertEqual(len(best), 1)
        self.assertEqual(best_nonparaxial_value(best[0]), max(values))

    def test_tensor_and_glass_candidates_are_checked(self):
        for name in ('S4-glass',):
            doc = load(name)
            result = api.design(doc)
            engine = to_engine_problem(doc)['engine']
            for c, raw in zip(result['candidates'], result['engine_report']['candidates']):
                again = nonparaxial.check_candidate(raw, engine)
                self.assertAlmostEqual(again['normalized_mode_overlap'], c['metrics']['nonparaxial_overlap'], places=12)

    def test_beyond_guard_ports_get_a_study_not_candidates(self):
        result = api.design(load('S3'))
        self.assertEqual(result['status'], 'Fail')
        self.assertEqual(result['candidates'], [])
        study = result['nonparaxial_study']
        self.assertEqual(study['status'], 'Study')
        self.assertGreaterEqual(len(study['cases']), 1)
        self.assertLess(study['summary']['best_nonparaxial_overlap'], 0.5)
        self.assertIn('nonparaxial_study', {g['kind'] for g in result['guidance']})


if __name__ == '__main__':
    unittest.main()
