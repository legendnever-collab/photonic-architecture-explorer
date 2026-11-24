"""P4 (in progress): refracting aspheric surfaces and micro-lens converters for beyond-guard Ports."""

import json
import math
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from photonic_architecture_explorer import lens as L, nonparaxial  # noqa: E402
from photonic_architecture_explorer.design_document import to_engine_input  # noqa: E402
from photonic_architecture_explorer.external import adapt_ports  # noqa: E402

SCENARIOS = ROOT / 'src/photonic_architecture_explorer/scenarios'


def ssc_port():
    doc = json.loads((SCENARIOS / 'S3.json').read_text(encoding='utf-8'))
    return adapt_ports(to_engine_input(doc)).source


def trace(surfaces, origin, directions, plane, axis):
    basis = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]).T
    return nonparaxial.trace_bundle(origin, np.array(directions, float), surfaces, plane, basis, np.array(axis, float))


class RefractionTest(unittest.TestCase):
    def test_plane_parallel_plate(self):
        n, t = 1.5, 1e-3
        plate = [nonparaxial.refracting_surface((1e-3, 0, 0), (1, 0, 0), 0, 0, (), 1.0, n, 1e-2),
                 nonparaxial.refracting_surface((1e-3 + t, 0, 0), (1, 0, 0), 0, 0, (), n, 1.0, 1e-2)]
        angles = np.linspace(-0.4, 0.4, 9)
        dirs = np.stack([np.cos(angles), np.sin(angles), np.zeros_like(angles)], 1)
        ray = trace(plate, (0, 0, 0), dirs, (5e-3, 0, 0), (1, 0, 0))
        self.assertTrue(ray['alive'].all())
        np.testing.assert_allclose(ray['u'][:, 0], np.sin(angles), atol=1e-12)  # exit direction = entry direction
        centre = len(angles) // 2
        self.assertAlmostEqual(ray['opl'][centre], 5e-3 + (n - 1) * t, places=15)
        # lateral shift of a tilted plate: t sinθ (1 − cosθ / √(n² − sin²θ))
        theta = angles[-1]
        shift = t * math.sin(theta) * (1 - math.cos(theta) / math.sqrt(n * n - math.sin(theta) ** 2))
        self.assertAlmostEqual(ray['x'][-1, 0], 5e-3 * math.tan(theta) - shift / math.cos(theta), delta=1e-12)

    def test_lens_paraxial_matrix_matches_rays(self):
        port = ssc_port()
        lens = L.design(port, 0.01, 1.4468, 'source')
        surfaces = lens.surfaces()
        end = lens.curved_vertex
        h = 1e-7
        def out(y, slope):
            d = np.array([1.0, slope, 0.0])
            r = trace(surfaces, (lens.vertex[0] - 1e-12, y, 0), [d / np.linalg.norm(d)], end, (1, 0, 0))
            return np.array([r['x'][0, 0], r['u'][0, 0] / math.sqrt(1 - r['u'][0, 0] ** 2)])
        m = np.array([(out(h, 0) - out(-h, 0)) / (2 * h), (out(0, h) - out(0, -h)) / (2 * h)]).T
        np.testing.assert_allclose(m, L._reduced_matrix(lens), rtol=1e-5, atol=1e-9)

    def test_equal_path_collimator_collimates(self):
        port = ssc_port()
        lens = L.design(port, 0.01, 1.4468, 'source')
        residual = L.fit_collimator(lens)
        self.assertLess(residual, 5e-9)  # fitted asphere within 5 nm of the exact profile
        angles = np.linspace(-0.6, 0.6, 25)
        dirs = np.stack([np.cos(angles), np.sin(angles), np.zeros_like(angles)], 1)
        ray = trace(lens.surfaces(), port.position, dirs, (lens.curved_vertex[0] + 1e-4, 0, 0), (1, 0, 0))
        self.assertTrue(ray['alive'].all())
        self.assertLess(abs(ray['u'][:, 0]).max(), 2e-4)
        self.assertGreater(L.far_zone_ratio(port, lens), 10)


if __name__ == '__main__':
    unittest.main()
