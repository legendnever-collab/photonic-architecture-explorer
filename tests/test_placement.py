"""Independent checks for the exact chief ray on moved local quadratic patches."""

import json
import math
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import unittest

import numpy as np

from photonic_architecture_explorer.benchmark import load_case
from photonic_architecture_explorer.design import design_two_ports
from photonic_architecture_explorer.diagnostics import run
from photonic_architecture_explorer.external import adapt_external
from photonic_architecture_explorer.placement import (
    compare_placement, placement_cases, rotate_in_plane, trace_placement,
)
from test_m2 import FIXTURE, newton_reference


def rotation_reference(mirror, sagittal, angle):
    normal = np.array(mirror.normal)
    tangent = np.cross(sagittal, normal)
    axes = np.column_stack((tangent, sagittal, normal))
    c, s = np.cos(angle), np.sin(angle)
    rotation = axes @ np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]]) @ axes.T
    return rotation @ normal


class ReflectorPlacementTests(unittest.TestCase):
    def test_translation_matches_frozen_m2_and_zero_closes(self):
        source, target, mirrors = load_case(FIXTURE)
        diagnostic = placement_cases(source, target, mirrors)
        self.assertEqual(diagnostic['status'], 'Computed')
        nominal = diagnostic['nominal']
        np.testing.assert_allclose(nominal['target_point_m'], target.position, atol=1e-13, rtol=0)
        np.testing.assert_allclose(nominal['target_ray_direction'], target.direction, atol=1e-11, rtol=0)
        for hit, mirror in zip(nominal['hits'], mirrors):
            np.testing.assert_allclose(hit['position_m'], mirror.vertex, atol=1e-13, rtol=0)
        translation = [r for r in diagnostic['cases'] if r['kind'] == 'translation']
        baseline = run(FIXTURE)['placement_cases']
        self.assertEqual(len(translation), len(baseline), 12)
        for row, old in zip(translation, baseline):
            for key in ('mirror', 'axis', 'delta_m'):
                self.assertEqual(row[key], old[key])
            for key in ('target_offset_m', 'target_slope'):
                self.assertEqual(row[key], list(old['geometry'][key]))

    def test_flat_second_mirror_has_signed_double_angle_response(self):
        source, target, mirrors = load_case(FIXTURE, 'flat')
        for angle in (-.001, .001):
            changed = rotate_in_plane(mirrors[1], source.sagittal, angle)
            np.testing.assert_allclose(changed.normal, rotation_reference(mirrors[1], source.sagittal, angle),
                                       atol=1e-11, rtol=0)
            self.assertEqual((changed.vertex, changed.curvatures, changed.half_aperture),
                             (mirrors[1].vertex, mirrors[1].curvatures, mirrors[1].half_aperture))
            ray = trace_placement(source, target, (mirrors[0], changed))
            np.testing.assert_allclose(ray['target_angular_error_rad'], (2 * angle, 0), atol=1e-11, rtol=0)
            self.assertAlmostEqual(ray['target_angle_rad'], 2 * abs(angle), delta=1e-11)
            self.assertAlmostEqual(ray['target_slope'][0], math.tan(2 * angle), delta=1e-11)

    def test_all_80_perturbations_match_independent_quadratic_and_newton_reference(self):
        root = FIXTURE.parent
        expected = {
            'm5a_two_ports': ['G009-B1', 'G015-B1', 'G036-B1'],
            'm5f_different_q': ['G009-B1', 'G016-B1'],
        }
        for fixture, ids in expected.items():
            document = json.loads((root / (fixture + '.json')).read_text())
            result = design_two_ports(document)
            before = json.dumps(result, sort_keys=True)
            diagnostic = compare_placement(result)
            self.assertEqual(diagnostic, compare_placement(result))
            self.assertEqual(before, json.dumps(result, sort_keys=True))
            self.assertEqual([r['candidate_id'] for r in diagnostic['candidates']], ids)
            self.assertEqual(diagnostic['status'], 'Computed')
            for nominee, candidate in zip(result['candidates'], diagnostic['candidates']):
                design = adapt_external(nominee['prescription'])
                source, target, mirrors = design.source, design.target, design.reflectors
                self.assertEqual(len(candidate['cases']), 16)
                for row in candidate['cases']:
                    with self.subTest(fixture=fixture, candidate=nominee['id'], condition=row.get('delta_m', row.get('delta_rad')),
                                      mirror=row['mirror'], axis=row['axis']):
                        self.check_trace(row, source, target, mirrors)
                for negative, positive in zip(candidate['cases'][::2], candidate['cases'][1::2]):
                    self.assertLess(negative.get('delta_m', negative.get('delta_rad')), 0)
                    self.assertGreater(positive.get('delta_m', positive.get('delta_rad')), 0)
                    if negative['kind'] != 'rotation':
                        continue
                    for key, floor in [('target_offset_m', 1e-11), ('target_angular_error_rad', 1e-9)]:
                        a, b = np.array(negative[key]), np.array(positive[key])
                        self.assertLess(np.linalg.norm(a + b), .1 * np.linalg.norm(a - b) + floor)

    def check_trace(self, row, source, target, mirrors):
        s = np.array(source.sagittal)
        changed = list(mirrors)
        index = row['mirror'] - 1
        mirror = mirrors[index]
        n, vertex = mirror.normal, mirror.vertex
        if row['kind'] == 'rotation':
            n = rotation_reference(mirror, s, row['delta_rad'])
        else:
            vertex = np.array(vertex) + np.eye(3)['XYZ'.index(row['axis'])] * row['delta_m']
        changed[index] = SimpleNamespace(normal=n, vertex=vertex, curvatures=mirror.curvatures)
        expected_offset, expected_slope = newton_reference(source, target, changed)
        np.testing.assert_allclose(row['target_offset_m'], expected_offset, atol=1e-13, rtol=0)
        np.testing.assert_allclose(row['target_angular_error_rad'], np.arctan(expected_slope), atol=1e-11, rtol=0)
        origin, incoming = np.array(source.position), np.array(source.direction)
        for patch, hit in zip(changed, row['hits']):
            normal = np.array(patch.normal)
            t = np.cross(s, normal)
            point = np.array(hit['position_m'])
            u, v, h = np.column_stack((t, s, normal)).T @ (point - patch.vertex)
            kt, ks = patch.curvatures
            self.assertAlmostEqual(h, .5 * (kt*u*u + ks*v*v), delta=1e-13)
            self.assertAlmostEqual(hit['surface_residual_m'], 0, delta=1e-13)
            self.assertGreater(np.dot(point - origin, incoming), 0)
            self.assertLess(np.linalg.norm(np.cross(point - origin, incoming)), 1e-13)
            gradient = normal - kt*u*t - ks*v*s
            gradient /= np.linalg.norm(gradient)
            np.testing.assert_allclose(hit['normal'], gradient, atol=1e-11, rtol=0)
            np.testing.assert_allclose(hit['incoming'], incoming, atol=1e-11, rtol=0)
            outgoing = (np.eye(3) - 2 * np.outer(gradient, gradient)) @ incoming
            np.testing.assert_allclose(hit['outgoing'], outgoing, atol=1e-11, rtol=0)
            origin, incoming = point, outgoing

    def test_failed_traces_are_classified_and_withhold_target_errors(self):
        source, target, (m1, m2) = load_case(FIXTURE, 'flat')
        trials = [
            ('aperture_miss', source, target, (replace(m1, vertex=(m1.vertex[0], 1., m1.vertex[2])), m2)),
            ('no_hit', replace(source, direction=(-1., 0., 0.)), target, (m1, m2)),
            ('back_face', source, target, (replace(m1, normal=tuple(-n for n in m1.normal)), m2)),
            ('unintended_intersection', source, target, (m1, replace(m2, vertex=(.0005, 0., 0.)))),
            ('invalid_target_plane', source, replace(target, direction=(-1., 0., 0.)), (m1, m2)),
            ('invalid_geometry', source, target, (replace(m1, normal=source.sagittal), m2)),
        ]
        for category, launch, receiver, mirrors in trials:
            with self.subTest(category=category):
                result = trace_placement(launch, receiver, mirrors)
                self.assertEqual(result['status'], 'Fail')
                self.assertEqual(result['failure'], category)
                self.assertNotIn('target_offset_m', result)
                self.assertNotIn('target_slope', result)
        stopped = placement_cases(source, target, trials[-1][3])
        self.assertEqual(stopped['cases'], [])
        tiny = replace(m1, half_aperture=(1e-7, 1e-7))
        mixed = placement_cases(source, target, (tiny, m2))
        self.assertEqual(mixed['status'], 'Fail')
        self.assertGreater(mixed['summary']['translation']['failed'], 0)
        self.assertEqual(len(mixed['cases']), 16)

    def test_rejected_design_supplies_no_placement_results(self):
        document = json.loads((FIXTURE.parent / 'm5f_high_divergence.json').read_text())
        diagnostic = compare_placement(design_two_ports(document))
        self.assertEqual(diagnostic['status'], 'Uncomputed')
        self.assertEqual(diagnostic['candidates'], [])
        self.assertIsNone(diagnostic['recommended_candidate_id'])
        for field in ('perturbed_gaussian_mode_overlap', 'actual_assembly_tolerance',
                      'package_yield', 'total_coupling', 'patentability'):
            self.assertEqual(diagnostic[field], 'Uncomputed')
