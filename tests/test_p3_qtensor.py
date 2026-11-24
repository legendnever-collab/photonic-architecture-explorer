"""P3 stage 2: general astigmatic q-tensor relay for non-coplanar or rolled Ports."""

import copy
import json
import math
from pathlib import Path
import random
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from photonic_architecture_explorer import api, qtensor, search  # noqa: E402
from photonic_architecture_explorer.design_document import to_engine_input  # noqa: E402
from photonic_architecture_explorer.external import adapt_ports  # noqa: E402
from photonic_architecture_explorer.gaussian import Gaussian, mode_overlap  # noqa: E402

SCENARIOS = ROOT / 'src/photonic_architecture_explorer/scenarios'


def load(name):
    return json.loads((SCENARIOS / f'{name}.json').read_text(encoding='utf-8'))


def ports_of(doc):
    return adapt_ports(to_engine_input(doc))


def lam_n(ports):
    return ports.source.mode.wavelength / (math.pi * ports.source.mode.index)


def rotation(seed):
    rng = random.Random(seed)
    q = np.linalg.qr(np.array([[rng.gauss(0, 1) for _ in range(3)] for _ in range(3)]))[0]
    return q if np.linalg.det(q) > 0 else -q


def rotated(doc, matrix):
    out = copy.deepcopy(doc)
    for port in out['ports'].values():
        for key in ('position_mm', 'direction', 'sagittal_axis'):
            port[key] = [float(x) for x in matrix @ np.array(port[key], float)]
    return out


class AlgebraTest(unittest.TestCase):
    def test_overlap_matches_engine_for_separable_beams(self):
        rng = random.Random(3)
        for _ in range(20):
            g1 = Gaussian.from_radii((rng.uniform(4, 9) * 1e-6, rng.uniform(4, 9) * 1e-6), 1.55e-6, 1.0,
                                     (rng.uniform(-300, 300), rng.uniform(-300, 300)))
            g2 = Gaussian.from_radii((rng.uniform(4, 9) * 1e-6, rng.uniform(4, 9) * 1e-6), 1.55e-6, 1.0,
                                     (rng.uniform(-300, 300), rng.uniform(-300, 300)))
            offset, slope = (rng.uniform(-2, 2) * 1e-6, rng.uniform(-2, 2) * 1e-6), (rng.uniform(-5, 5) * 1e-3, rng.uniform(-5, 5) * 1e-3)
            k = 2 * math.pi / 1.55e-6
            mine = qtensor.log_overlap(np.diag([1 / g1.q_t, 1 / g1.q_s]), np.diag([1 / g2.q_t, 1 / g2.q_s]), k, offset, slope)
            self.assertAlmostEqual(mine, mode_overlap(g1, g2, offset, slope)['log_overlap'], places=10)

    def test_overlap_of_a_rotated_astigmatic_beam_by_quadrature(self):
        """Closed-form tensor overlap vs direct 2D integration of the two fields."""
        k = 2 * math.pi / 1.31e-6
        rot = np.array([[math.cos(0.6), -math.sin(0.6)], [math.sin(0.6), math.cos(0.6)]])
        q1 = rot @ np.diag([1 / complex(1e-4, 6e-5), 1 / complex(-5e-5, 8e-5)]) @ rot.T  # w ≈ 9.7 / 6.8 µm
        q2 = np.diag([1 / complex(0, 4e-5), 1 / complex(0, 3e-5)])
        offset, slope = np.array([1.5e-6, -1e-6]), np.array([2e-3, 1e-3])
        x = np.linspace(-60e-6, 60e-6, 601)
        xx, yy = np.meshgrid(x, x, indexing='ij')
        pts = np.stack([xx, yy], -1)

        def field(q, d=np.zeros(2), th=np.zeros(2)):
            r = pts - d
            return np.exp(-0.5j * k * np.einsum('...i,ij,...j', r, q, r) - 1j * k * pts @ th)
        e1, e2 = field(q1, offset, slope), field(q2)
        numeric = abs((e1 * e2.conj()).sum()) ** 2 / ((abs(e1) ** 2).sum() * (abs(e2) ** 2).sum())
        self.assertAlmostEqual(math.log(numeric), qtensor.log_overlap(q1, q2, k, offset, slope), places=8)

    def test_width_matching_hits_the_required_width(self):
        k = 2 * math.pi / 1.31e-6
        start = np.array([[1 / complex(2e-3, 5e-5), 0], [0, 1 / complex(1e-3, 3e-5)]])
        rot = np.array([[math.cos(0.4), -math.sin(0.4)], [math.sin(0.4), math.cos(0.4)]])
        target = qtensor.propagate(rot @ np.diag([1 / complex(0, 4e-5), 1 / complex(0, 6e-5)]) @ rot.T, -3e-3)
        found = qtensor.width_matching_curvatures(start, 2e-3, target.imag, k)
        self.assertEqual(len(found), 4)
        for _, r in found:
            reached = qtensor.propagate(r + 1j * start.imag, 2e-3)
            self.assertLess(abs(reached.imag - target.imag).max() / abs(target.imag).max(), 1e-9)


class CoplanarReductionTest(unittest.TestCase):
    def test_tensor_branches_equal_the_separable_branches(self):
        ports = ports_of(load('S2a-1550'))
        compared = 0
        for a, c in ((2e-3, 2e-3), (1.2e-3, 3.1e-3), (4e-3, 1.5e-3), (2.6e-3, 2.6e-3)):
            separable = search.evaluate_point(ports, search.Constraints(), a, c, lam_n(ports))
            tensor = qtensor.evaluate_point(ports, search.Constraints(), a, c, lam_n(ports))
            key = lambda p: (p.status if not p.metrics else 'computed', round(p.metrics.get('max_footprint_slope', -1), 9))  # noqa: E731
            self.assertEqual(sorted(map(key, separable)), sorted(map(key, tensor)))
            sep_curv = sorted(tuple(sorted(round(x, 6) for pair in p.prescription[3] for x in pair)) for p in separable if p.prescription)
            ten_curv = sorted(tuple(sorted(round(x, 6) for m in p.prescription[3] for x in m.curvatures)) for p in tensor if p.prescription)
            compared += len(ten_curv)
            self.assertEqual(sep_curv, ten_curv)
            for p in tensor:
                if p.metrics:
                    self.assertAlmostEqual(p.metrics['normalized_mode_overlap'], 1.0, places=10)
        self.assertGreaterEqual(compared, 8)

    def test_rolled_target_axes_are_solved_by_the_tensor_model(self):
        """A Target whose axes are rolled 180° is the same physical mode: same exact solutions."""
        doc = load('S2a-1550')
        flipped = copy.deepcopy(doc)
        flipped['ports']['target']['sagittal_axis'] = [-x for x in doc['ports']['target']['sagittal_axis']]
        p1, p2 = ports_of(doc), ports_of(flipped)
        a, c = 2.5e-3, 2.5e-3
        one = sorted(round(p.metrics['max_footprint_slope'], 9) for p in search.evaluate_point(p1, search.Constraints(), a, c, lam_n(p1)))
        two = sorted(round(p.metrics['max_footprint_slope'], 9) for p in qtensor.evaluate_point(p2, search.Constraints(), a, c, lam_n(p2)))
        self.assertEqual(one, two)


class NonCoplanarTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load('S4')
        cls.ports = ports_of(cls.doc)
        cls.geometry = search.fold(cls.ports, 2.5e-3, 3.0e-3)
        cls.k = qtensor.wavenumber(cls.ports.source)
        cls.solutions = qtensor.relay_solutions(cls.ports, cls.geometry, cls.k)

    def test_exact_tensors_close_on_the_target_mode(self):
        self.assertGreaterEqual(len(self.solutions), 1)
        for _, mirrors in self.solutions:
            run = qtensor.chain(self.ports, mirrors, self.geometry[2], self.k)
            self.assertGreater(run['log_eta'], -1e-10)
            for m in mirrors:  # principal axes really are non-aligned with the Port sagittal axis
                self.assertLess(abs(np.dot(m.axis, m.normal)), 1e-12)

    def test_ray_transfer_matrix_reproduces_the_tensor(self):
        """Exact rays through the quadric patches (independent of the q algebra) give the same arrival."""
        q_source, _ = qtensor.port_beam(self.ports.source)
        for _, mirrors in self.solutions:
            mirrors = qtensor.with_apertures(mirrors, [(1e-3, 1e-3)] * 2, 1.0)
            run = qtensor.chain(self.ports, mirrors, self.geometry[2], self.k)
            m = qtensor.ray_transfer(self.ports, mirrors)
            a, b, c, d = m[:2, :2], m[:2, 2:], m[2:, :2], m[2:, 2:]
            q_ray = (c + d @ q_source) @ np.linalg.inv(a + b @ q_source)
            self.assertLess(np.linalg.norm(q_ray - run['arrival']) / np.linalg.norm(run['arrival']), 1e-6)
            self.assertLess(qtensor.symplectic_error(m, sum(self.geometry[2])), 1e-6)

    def test_rigid_rotation_of_the_whole_problem_changes_nothing(self):
        spun = ports_of(rotated(self.doc, rotation(11)))
        geometry = search.fold(spun, 2.5e-3, 3.0e-3)
        mine = sorted(tuple(round(x, 6) for m in ms for x in m.curvatures) for _, ms in self.solutions)
        theirs = sorted(tuple(round(x, 6) for m in ms for x in m.curvatures) for _, ms in qtensor.relay_solutions(spun, geometry, self.k))
        self.assertEqual(mine, theirs)


class DesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = api.design(load('S4'))

    def test_s4_now_has_verified_candidates(self):
        r = self.result
        self.assertEqual(r['status'], 'Computed')
        self.assertEqual(r['engine_report']['model'], 'qtensor')
        self.assertGreaterEqual(len(r['candidates']), 3)
        self.assertIn('qtensor', {g['kind'] for g in r['guidance']})
        for c in r['candidates']:
            self.assertEqual(c['model'], 'qtensor')
            self.assertGreater(c['metrics']['normalized_mode_overlap'], 0.99)
            self.assertLessEqual(c['metrics']['max_3w_footprint_curvature'], 0.15 + 1e-12)
            self.assertLess(c['ray_transfer_check']['q_tensor_relative_difference'], 1e-6)
            self.assertIsNotNone(c['metrics']['worst_pose_mismatch_db'])

    def test_scene_closes_and_carries_beam_ellipses(self):
        doc = load('S4')
        for c in self.result['candidates']:
            scene = c['scene']
            self.assertEqual(scene['path']['points_mm'][0], [float(x) for x in doc['ports']['source']['position_mm']])
            self.assertEqual(scene['path']['points_mm'][-1], [float(x) for x in doc['ports']['target']['position_mm']])
            last = scene['beam']['samples'][-1]
            radius = doc['ports']['target']['mfd_um'][0] / 2
            eta = c['metrics']['normalized_mode_overlap']
            self.assertAlmostEqual(last['ellipse']['major_um'], radius, delta=radius * 4 * math.sqrt(1 - eta) + 1e-6)
            for m in scene['mirrors']:
                self.assertLess(abs(np.dot(m['s_axis'], m['normal'])), 1e-12)
                self.assertEqual(len(m['surface_grid_mm']), 13)


if __name__ == '__main__':
    unittest.main()
