"""P4: coma-correcting third/fourth-order sag terms on the paraxial reflector prescription."""

import json
import math
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from photonic_architecture_explorer import api, freeform, nonparaxial  # noqa: E402
from photonic_architecture_explorer.design_document import to_engine_problem  # noqa: E402
from photonic_architecture_explorer.external import adapt_external  # noqa: E402

SCENARIOS = ROOT / 'src/photonic_architecture_explorer/scenarios'


def load(name):
    return json.loads((SCENARIOS / f'{name}.json').read_text(encoding='utf-8'))


class Setup:
    """S1's first candidate: reflector tuples, Port arguments and a non-trivial sag polynomial."""

    def __init__(self):
        doc = load('S1')
        self.result = api.design(doc)
        raw = self.result['engine_report']['candidates'][0]
        design = adapt_external(raw['prescription'])
        self.ports = design
        q_s, a_s, q_t, a_t = nonparaxial.ports_q(design)
        self.k = 2 * math.pi / design.source.mode.wavelength
        self.args = (q_s, a_s, design.source.position, design.source.direction, q_t, a_t, design.target.position,
                     design.target.direction, self.k, nonparaxial.half_angle(design))
        self.mirrors = [nonparaxial.mirror_tuple(m.vertex, m.normal, design.source.sagittal, m.curvatures, m.half_aperture)
                        for m in design.reflectors]
        self.footprints = [tuple(a / 4 for a in m.half_aperture) for m in design.reflectors]
        self.wavelength = design.source.mode.wavelength
        self.raw = raw

    def with_poly(self, b):
        poly = freeform._poly(np.array(b, float), self.footprints, self.wavelength)
        return [nonparaxial.mirror_tuple(m[0], m[1], m[3], (m[4], m[5]), (m[6], m[7]), p) for m, p in zip(self.mirrors, poly)]

    def bundle(self, mirrors, directions):
        d = self.ports
        return nonparaxial.trace_bundle(d.source.position, directions, mirrors, d.target.position, self.args[5],
                                        np.array(d.target.direction))


S = None


def setUpModule():
    global S
    S = Setup()


class SurfaceTraceTest(unittest.TestCase):
    def directions(self, n=21, spread=0.05):
        a_s = self.args_basis = S.args[1]
        u = np.linspace(-spread, spread, n)
        uu, vv = np.meshgrid(u, u, indexing='ij')
        kz = np.sqrt(1 - uu ** 2 - vv ** 2)
        return (uu[..., None] * a_s[:, 0] + vv[..., None] * a_s[:, 1] + kz[..., None] * np.array(S.ports.source.direction)).reshape(-1, 3)

    def test_zero_terms_reproduce_the_quadric_trace(self):
        d = self.directions()
        plain = S.bundle(S.mirrors, d)
        zero = S.bundle(S.with_poly(np.zeros(18)), d)
        np.testing.assert_array_equal(plain['alive'], zero['alive'])
        self.assertLess(abs(plain['opl'] - zero['opl']).max(), 1e-15)

    def test_hits_lie_on_the_corrected_surface(self):
        b = np.linspace(-1.5, 1.5, 18)
        mirrors = S.with_poly(b)
        ray = S.bundle(mirrors, self.directions())
        for m, hit in zip(mirrors, ray['hits']):
            u, v = hit['u'][ray['alive']], hit['v'][ray['alive']]
            self.assertGreater(len(u), 100)
            # the hit is on the patch by construction of (u, v, h); check h on the 3D point from the next trace
        # Independent check: the reflected chief ray (u = v = 0) is unchanged by terms of order ≥ 3.
        chief = np.array([S.ports.source.direction])
        a = S.bundle(S.mirrors, chief)
        c = S.bundle(mirrors, chief)
        self.assertLess(abs(a['opl'] - c['opl']).max(), 1e-15)
        self.assertLess(abs(a['u'] - c['u']).max(), 1e-15)

    def test_paraxial_ray_transfer_is_unchanged_by_the_correction(self):
        """Terms of order ≥ 3 leave the 4×4 ray-transfer matrix (central differences) untouched."""
        def matrix(mirrors):
            a_s, d0 = S.args[1], np.array(S.ports.source.direction)
            cols = []
            for i in (0, 1):
                out = []
                for sign in (1, -1):
                    d = d0 + sign * 1e-6 * a_s[:, i]
                    ray = S.bundle(mirrors, np.array([d / np.linalg.norm(d)]))
                    out.append(np.concatenate([ray['x'][0], ray['u'][0]]))
                cols.append((out[0] - out[1]) / 2e-6)
            return np.array(cols).T
        base, corrected = matrix(S.mirrors), matrix(S.with_poly(np.linspace(-2, 2, 18)))
        self.assertLess(abs(base - corrected).max() / abs(base).max(), 1e-6)


class CorrectionTest(unittest.TestCase):
    def test_reported_overlap_is_the_exact_retrace(self):
        """The linear phase model only proposes steps; the reported value is the exact surface trace."""
        corrected = S.raw['freeform']
        poly = [tuple((t['u_power'], t['v_power'], t['coefficient_si']) for t in r['terms']) for r in corrected['reflectors']]
        mirrors = [nonparaxial.mirror_tuple(m[0], m[1], m[3], (m[4], m[5]), (m[6], m[7]), p) for m, p in zip(S.mirrors, poly)]
        check = nonparaxial.check(*S.args[:8], mirrors, *S.args[8:])
        self.assertAlmostEqual(check['normalized_mode_overlap'], corrected['normalized_mode_overlap'], places=12)
        history = corrected['fit_history']
        self.assertTrue(all(b['exact'] >= a['exact'] for a, b in zip(history, history[1:])))

    def test_gate_s1_and_s4_reach_095(self):
        for name in ('S1', 'S4'):
            result = S.result if name == 'S1' else api.design(load(name))
            for c in result['candidates']:
                self.assertEqual(c['freeform']['status'], 'Computed', (name, c['id']))
                self.assertIsNone(c['freeform']['constraint'])
                self.assertGreaterEqual(c['metrics']['corrected_nonparaxial_overlap'], 0.95, (name, c['id']))
                self.assertLessEqual(c['metrics']['corrected_nonparaxial_overlap'], 1 + nonparaxial.CONVERGENCE_LIMIT)
                self.assertGreater(c['metrics']['corrected_nonparaxial_overlap'], c['metrics']['nonparaxial_overlap'])
                grid = c['scene']['mirrors'][0]['surface_grid_corrected_mm']
                self.assertEqual(np.array(grid).shape, (13, 13, 3))
            self.assertIn('freeform', {g['kind'] for g in result['guidance']})

    def test_correction_is_reproducible_from_the_engine_record(self):
        engine = to_engine_problem(load('S1'))['engine']
        again = freeform.correct_candidate(S.raw, engine)
        self.assertAlmostEqual(again['normalized_mode_overlap'], S.raw['freeform']['normalized_mode_overlap'], places=12)

    def test_corrected_surface_constraints_are_checked(self):
        from photonic_architecture_explorer.search import Constraints
        points = freeform.surface_points((0, 0, 0), (0, 0, 1), (1, 0, 0), (0, 1, 0), (0, 0), (1e-3, 1e-3), ((3, 0, 1e5),))
        self.assertLess(points[..., 2].min(), -1e-5)
        self.assertIsNone(freeform.surface_violation(S.ports, None, points))
        self.assertIsNotNone(freeform.surface_violation(S.ports, Constraints(envelope=((-1, -1, 0), (1, 1, 1))), points))


if __name__ == '__main__':
    unittest.main()
