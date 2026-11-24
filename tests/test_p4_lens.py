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
        self.assertLess(residual, 1e-7)  # fitted asphere within 0.1 µm of the exact profile
        angles = np.linspace(-0.6, 0.6, 25)
        dirs = np.stack([np.cos(angles), np.sin(angles), np.zeros_like(angles)], 1)
        ray = trace(lens.surfaces(), port.position, dirs, (lens.curved_vertex[0] + 1e-4, 0, 0), (1, 0, 0))
        self.assertTrue(ray['alive'].all())
        self.assertLess(abs(ray['u'][:, 0]).max(), 2e-4)
        self.assertGreater(L.far_zone_ratio(port, lens), 10)


class AplanaticLensTest(unittest.TestCase):
    def test_aplanatic_lens_meets_equal_path_and_sine_condition(self):
        port = ssc_port()
        lens = L.design(port, 0.005, 1.4468, 'source')
        f = lens.focal_length
        check = L.fit_aplanatic(lens, max(p['divergence_rad'] for p in port.mode.parameters()))
        self.assertTrue(check['rays_alive'])
        self.assertLess(check['max_direction_rad'], 2e-4)              # exit rays parallel to the axis
        self.assertLess(check['max_sine_condition_error_m'], 0.05e-6)  # h = f sin α within 50 nm
        # the bending keeps the EFL and the front focal distance (paraxial reduced matrix)
        m = L._reduced_matrix(lens)
        self.assertAlmostEqual(-1 / m[1, 0], f, delta=1e-9)
        # the mapping from Port angle to exit height is monotonic over the fitted fan (no fold)
        alphas = np.linspace(0, check['passes_to_angle_rad'], 60)
        alive, height, _ = L.meridional(lens, alphas)
        self.assertTrue(alive.all())
        self.assertTrue((np.diff(height) > 0).all())

    def test_material_choice_and_public_indices(self):
        from photonic_architecture_explorer import materials
        self.assertAlmostEqual(materials.silica_index(1.31e-6), 1.44680, places=5)   # Malitson 1965
        self.assertAlmostEqual(materials.silicon_index(1.31e-6), 3.5005, places=4)   # Li 1980, 293 K
        self.assertAlmostEqual(materials.silicon_index(1.55e-6), 3.4764, places=4)
        with self.assertRaises(L.DomainError):
            materials.silicon_index(1.0e-6)  # absorbing below 1.2 µm
        self.assertEqual(L.choose_material(ssc_port())['key'], 'fused_silica')  # 0.278 rad ≤ 0.39 rad
        doc = json.loads((SCENARIOS / 'S5.json').read_text(encoding='utf-8'))
        laser = adapt_ports(to_engine_input(doc)).source
        chosen = L.choose_material(laser)
        self.assertEqual(chosen['key'], 'silicon')  # 0.556 rad
        self.assertLess(chosen['uncoated_normal_transmission_two_faces'], 0.5)

    def test_high_na_silicon_lens_is_robust_to_the_port_angle(self):
        doc = json.loads((SCENARIOS / 'S5.json').read_text(encoding='utf-8'))
        laser = adapt_ports(to_engine_input(doc)).source
        theta = max(p['divergence_rad'] for p in laser.mode.parameters())
        for angle in (theta, round(theta, 3)):  # the fit used to jump to a misdirected edge for one of these
            lens = L.design(laser, 0.0075, 3.5005, 'source')
            check = L.fit_aplanatic(lens, angle)
            self.assertLess(check['max_direction_rad'], 2e-4)
            self.assertGreaterEqual(check['passes_to_sine'], L.MIN_APERTURE_FACTOR * angle)
        from types import SimpleNamespace
        from photonic_architecture_explorer.gaussian import Gaussian
        tiny = SimpleNamespace(position=laser.position, direction=laser.direction, sagittal=laser.sagittal,
                               mode=Gaussian.from_radii((0.3e-6, 0.3e-6), 1.31e-6, 1.0))  # θ ≈ 1.4 rad
        with self.assertRaises(L.DomainError):  # beyond what one singlet can take
            L.design(tiny, 0.0075, 3.5005, 'source')

    def test_scene_extension_is_continuous(self):
        port = ssc_port()
        lens = L.design(port, 0.005, 1.4468, 'source')
        start = np.array(lens.curved_vertex) * 1e3
        scene = {'path': {'points_mm': [list(start), list(start + [1, 0, 0])], 'total_length_mm': 1.0,
                          'segments': [{'start_mm': list(start), 'end_mm': list(start + [1, 0, 0]), 'length_mm': 1.0}]},
                 'beam': {'samples': [{'segment': 0, 'distance_mm': 0.0, 'radius_t_um': 99.0, 'radius_s_um': 99.0},
                                      {'segment': 0, 'distance_mm': 1.0, 'radius_t_um': 99.0, 'radius_s_um': 99.0}]}}
        L.extend_scene(scene, lens, port)
        segments = scene['path']['segments']
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[1]['medium'], 'lens')
        for a, b in zip(segments, segments[1:]):
            np.testing.assert_allclose(a['end_mm'], b['start_mm'], atol=1e-12)
        self.assertAlmostEqual(scene['path']['total_length_mm'], sum(s['length_mm'] for s in segments), places=9)
        distances = [x['distance_mm'] for x in scene['beam']['samples']]
        self.assertTrue(all(b >= a for a, b in zip(distances, distances[1:])))
        self.assertEqual(scene['lenses'][0]['id'], 'L1')
        self.assertEqual(len(scene['lenses'][0]['outline_mm']), 4)
        scene['mirrors'] = []
        self.assertIsNone(L.obstruction(scene, scene['lenses'][0]))  # its own gap, glass and exit are skipped
        centre = list((np.array(lens.vertex) + np.array(lens.curved_vertex)) / 2 * 1e3)
        scene['beam']['samples'].append({'segment': 99, 'distance_mm': 9.0, 'point_mm': centre,
                                         'radius_t_um': 5.0, 'radius_s_um': 5.0})
        self.assertEqual(L.obstruction(scene, scene['lenses'][0]), 'relay beam passes through lens L1')


class LensFamilyResultTest(unittest.TestCase):
    def test_s5_silicon_and_silica_lenses(self):
        from photonic_architecture_explorer import api
        doc = json.loads((SCENARIOS / 'S5.json').read_text(encoding='utf-8'))
        result = api.design(doc)
        self.assertEqual(result['status'], 'Computed')
        self.assertEqual(result['family'], 'lens_two_reflector')
        best = result['candidates'][0]
        self.assertEqual([l['material'] for l in best['scene']['lenses']], ['Silicon', 'Fused silica'])
        self.assertEqual([l['id'] for l in best['scene']['lenses']], ['L1', 'L2'])
        self.assertGreaterEqual(best['metrics']['nonparaxial_overlap'], 0.95)
        self.assertEqual(best['nonparaxial_check']['status'], 'Computed')
        segments = best['scene']['path']['segments']
        self.assertEqual([s.get('medium') for s in segments].count('lens'), 2)
        for a, b in zip(segments, segments[1:]):
            np.testing.assert_allclose(a['end_mm'], b['start_mm'], atol=1e-12)

    def test_s3_lens_family_candidates_are_computed_by_the_nonparaxial_rule(self):
        from photonic_architecture_explorer import api
        doc = json.loads((SCENARIOS / 'S3.json').read_text(encoding='utf-8'))
        result = api.design(doc)
        self.assertEqual(result['status'], 'Computed')
        self.assertEqual(result['family'], 'lens_two_reflector')
        self.assertTrue(result['reason'].startswith('Lens Family:'))
        review = result['lens_review']
        accepted = [c for c in review['candidates'] if c['accepted']]
        self.assertEqual([c['id'] for c in result['candidates']], [c['id'] for c in accepted])
        self.assertEqual(result['selected_candidate_id'], accepted[0]['id'])
        for c in review['candidates']:  # the rule: converged, η ≥ 0.95, lens body inside keep-outs and envelope
            rule = (c['review_status'] == 'Computed' and not c['lens_constraint']
                    and c['metrics']['nonparaxial_overlap'] >= L.LENS_ACCEPT_ETA)
            self.assertEqual(c['accepted'], rule)
            self.assertNotEqual(c['accepted'], c['review'])
            self.assertTrue(c['scene']['lenses'])
        self.assertGreaterEqual(min(c['metrics']['nonparaxial_overlap'] for c in accepted), 0.95)
        self.assertEqual(accepted[0]['role_labels'], ['Lens Family · 비근축 η 최대'])
        json.dumps(result)


if __name__ == '__main__':
    unittest.main()
