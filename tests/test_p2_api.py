"""P2 API: Design Document constraints, engine package mapping, guidance and the search map."""

import copy
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from photonic_architecture_explorer import api  # noqa: E402
from photonic_architecture_explorer.design_document import search_constraints, to_engine_input, validate_document  # noqa: E402
from photonic_architecture_explorer.external import adapt_external  # noqa: E402
from photonic_architecture_explorer.package_geometry import segment_hits_box  # noqa: E402

SCENARIOS = ROOT / 'src/photonic_architecture_explorer/scenarios'


def load(name):
    return json.loads((SCENARIOS / f'{name}.json').read_text(encoding='utf-8'))


class ConstraintDocumentTest(unittest.TestCase):
    def test_validation_reports_each_bad_constraint(self):
        doc = load('S2a-1550')
        doc['constraints'] = {'envelope_mm': {'min': [0, 0, 0], 'max': [1, -1, 1]}, 'max_incidence_deg': 80,
                              'keepouts_mm': [{'label': 'x', 'min': [0, 0], 'max': [1, 1, 1]}], 'clearance_um': -1, 'colour': 'red'}
        paths = {issue['path'] for issue in validate_document(doc)}
        self.assertEqual(paths, {'constraints', 'constraints.envelope_mm', 'constraints.max_incidence_deg',
                                 'constraints.keepouts_mm[0]', 'constraints.clearance_um'})

    def test_package_and_constraints_convert_to_si_without_changing_ports(self):
        doc = load('S2a-1550')
        plain = to_engine_input(doc)
        doc['constraints'] = {'envelope_mm': {'min': [-1, -1, -1], 'max': [4, 1, 3]},
                              'keepouts_mm': [{'label': 'connector', 'min': [0.5, -0.2, 0.3], 'max': [1, 0.2, 0.7]}],
                              'clearance_um': 10, 'min_radius_of_curvature_mm': 4, 'port_body_halfspace': False}
        engine = to_engine_input(doc)
        self.assertEqual({k: v for k, v in engine.items() if k != 'package'}, plain)
        self.assertEqual(engine['package']['available_volume']['value']['max_m'], [4e-3, 1e-3, 3e-3])
        self.assertEqual(engine['package']['keepout_bodies']['value'][0]['min_m'], [0.5e-3, -0.2e-3, 0.3e-3])
        self.assertAlmostEqual(engine['package']['required_clearance_m']['value'], 1e-5)
        constraints = search_constraints(doc)
        self.assertFalse(constraints.port_halfspace)
        self.assertEqual(constraints.keepout_labels, ('connector',))
        self.assertAlmostEqual(constraints.min_radius_of_curvature, 4e-3)


class GuidanceTest(unittest.TestCase):
    def test_divergence_guidance_gives_the_required_index(self):
        result = api.design(load('S3'))
        item = next(g for g in result['guidance'] if g['kind'] == 'port_divergence')
        theta = 1310e-9 / (math.pi * 1.5e-6)
        self.assertAlmostEqual(item['values']['required_index'], theta / 0.1, places=9)
        self.assertEqual(item['port'], 'source')

    def test_near_match_result_explains_the_closest_exact_point(self):
        result = api.design(load('S2b-1550'))
        self.assertEqual(result['family'], 'near_match')
        kinds = {g['kind'] for g in result['guidance']}
        self.assertIn('exact_outside_guard', kinds)
        self.assertIn('constraints', kinds)  # Port body half-spaces removed back-folded layouts
        grid = result['search']['map']
        self.assertEqual(len(grid['cells']), len(grid['a_mm']) * len(grid['c_mm']))
        self.assertTrue(grid['near_match'])
        for c in result['candidates']:
            self.assertEqual(c['family'], 'near_match')
            self.assertLess(c['metrics']['normalized_mode_overlap'], 1)
            self.assertTrue(c['role_labels'])

    def test_keepout_from_the_document_is_respected(self):
        doc = load('S2a-1550')
        free = api.design(doc)
        shortest = free['candidates'][0]['scene']['path']['points_mm']
        mid = [(a + b) / 2 for a, b in zip(shortest[1], shortest[2])]
        doc['constraints'] = {'keepouts_mm': [{'label': 'bracket', 'min': [m - 0.1 for m in mid], 'max': [m + 0.1 for m in mid]}]}
        result = api.design(doc)
        box = ([(m - 0.1) * 1e-3 for m in mid], [(m + 0.1) * 1e-3 for m in mid])
        self.assertEqual(result['status'], 'Computed')
        for c in result['engine_report']['candidates']:
            design = adapt_external(c['prescription'])
            points = [design.source.position, *(m.vertex for m in design.reflectors), design.target.position]
            self.assertFalse(any(segment_hits_box(a, b, box) for a, b in zip(points, points[1:])))
        self.assertEqual(result['constraints']['keepouts_m'][0]['label'], 'bracket')

    def test_invalid_constraint_is_not_designed(self):
        doc = copy.deepcopy(load('S1'))
        doc['constraints'] = {'max_incidence_deg': 0}
        self.assertEqual(api.design(doc)['status'], 'Invalid')


if __name__ == '__main__':
    unittest.main()
