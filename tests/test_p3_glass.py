"""P3 glass block: document validation, equivalent in-block Ports, region constraint and scenes."""

import copy
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from photonic_architecture_explorer import api, search  # noqa: E402
from photonic_architecture_explorer.design_document import (to_engine_input, to_engine_problem,  # noqa: E402
                                                            validate_document)
from photonic_architecture_explorer.geometry import Reflector  # noqa: E402
from photonic_architecture_explorer.media import Block  # noqa: E402

SCENARIOS = ROOT / 'src/photonic_architecture_explorer/scenarios'


def load(name):
    return json.loads((SCENARIOS / f'{name}.json').read_text(encoding='utf-8'))


def reversed_glass():
    """S2a-1550-glass run backwards: the buried guide emits, the fiber above the glass receives."""
    doc = load('S2a-1550-glass')
    fiber, guide = doc['ports']['source'], doc['ports']['target']
    doc['ports'] = {'source': {**guide, 'direction': [-1.0, 0.0, 0.0]},
                    'target': {**fiber, 'direction': [0.0, 0.0, 1.0], 'medium': 'ambient'}}
    return doc


class BlockDocumentTest(unittest.TestCase):
    def test_block_and_media_are_validated(self):
        doc = load('S2a-1550-glass')
        self.assertEqual(validate_document(doc), [])
        bad = copy.deepcopy(doc)
        bad['medium_block']['index'] = 0.9
        bad['medium_block']['surface_normal'] = [0, 0, 2]
        bad['medium_block']['colour'] = 'blue'
        paths = {i['path'] for i in validate_document(bad)}
        self.assertEqual(paths, {'medium_block', 'medium_block.index', 'medium_block.surface_normal'})
        wrong_side = copy.deepcopy(doc)
        wrong_side['ports']['source']['medium'] = 'block'  # the fiber sits above the surface
        self.assertEqual([i['path'] for i in validate_document(wrong_side)], ['ports.source.medium'])
        orphan = copy.deepcopy(doc)
        del orphan['medium_block']
        self.assertEqual([i['path'] for i in validate_document(orphan)], ['ports.target.medium'])

    def test_ambient_documents_are_unchanged(self):
        doc = load('S2a-1550')
        problem = to_engine_problem(doc)
        self.assertEqual(problem['medium'], 'ambient')
        self.assertEqual(problem['engine'], to_engine_input(doc))

    def test_port_on_the_surface_keeps_its_width_and_divides_its_curvature_by_n(self):
        doc = load('S2a-1550-glass')
        doc['ports']['source']['position_mm'] = [0.0, 0.0, 0.0]  # zero gap, normal incidence
        doc['ports']['source']['wavefront_curvature_per_m'] = [100.0, -50.0]
        problem = to_engine_problem(doc)
        n = doc['medium_block']['index']
        port = problem['engine']['source']
        self.assertEqual(problem['engine']['ambient_index']['value'], n)
        for got, mfd in zip(port['mfd_ts_m']['value'], doc['ports']['source']['mfd_um']):
            self.assertAlmostEqual(got, mfd * 1e-6, places=15)
        for got, curvature in zip(port['wavefront_curvature_ts_per_m']['value'], (100.0, -50.0)):
            self.assertAlmostEqual(got, curvature / n, places=9)
        self.assertIn('Equivalent source Port inside the block', port['mfd_ts_m']['source'])


class RegionConstraintTest(unittest.TestCase):
    def test_patch_must_stay_between_surface_and_bottom(self):
        block = Block(1.5, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 1e-3)
        flat = lambda z: Reflector((0.0, 0.0, z), (0.0, 0.0, 1.0), (0.0, 0.0), (5e-5, 5e-5))  # noqa: E731
        tilted = Reflector((0.0, 0.0, -3e-5), (math.sqrt(0.5), 0.0, math.sqrt(0.5)), (0.0, 0.0), (5e-5, 5e-5))
        inside = search.Constraints(block=block)
        y = (0.0, 1.0, 0.0)
        self.assertIsNone(search.block_violation(inside, flat(-5e-4), y))
        self.assertEqual(search.block_violation(inside, tilted, y), 'reflector crosses the block surface')
        self.assertEqual(search.block_violation(inside, flat(-1.1e-3), y), 'reflector leaves the block bottom')
        outside = search.Constraints(block=block, block_side='outside')
        self.assertEqual(search.block_violation(outside, flat(-5e-4), y), 'reflector enters the block')
        self.assertIsNone(search.block_violation(outside, flat(2e-4), y))


class GlassDesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.forward = api.design(load('S2a-1550-glass'))
        cls.backward = api.design(reversed_glass())

    def test_reflectors_lie_inside_the_glass(self):
        doc = load('S2a-1550-glass')
        thickness = doc['medium_block']['thickness_mm']
        self.assertEqual(self.forward['relay_medium'], 'block')
        self.assertGreaterEqual(len(self.forward['candidates']), 3)
        for candidate in self.forward['candidates']:
            for mirror in candidate['scene']['mirrors']:
                heights = [p[2] for row in mirror['surface_grid_mm'] for p in row]
                self.assertLess(max(heights), 0.0)
                self.assertGreater(min(heights), -thickness)
                self.assertIn('tir_possible', mirror)
        reasons = [v['reason'] for v in self.forward['search']['verification'] if v['status'] != 'Accepted']
        self.assertNotIn('geometry: unintended reflector interception', reasons)

    def test_pose_study_runs_for_every_candidate(self):
        """Incidence margin and obstruction margins keep the ±5 µm / ±1 mrad study inside the guards."""
        for result in (self.forward, self.backward):
            for candidate in result['candidates']:
                self.assertIsNotNone(candidate['metrics']['worst_pose_mismatch_db'], candidate['id'])
                self.assertLessEqual(max(candidate['metrics']['incidence_deg']), 70.0 - search.INCIDENCE_MARGIN_DEG + 1e-9)

    def test_source_crossing_prepends_the_air_gap(self):
        doc = load('S2a-1550-glass')
        crossing = self.forward['crossing']
        self.assertEqual(crossing['side'], 'source')
        self.assertAlmostEqual(crossing['ambient_length_mm'], 0.1, places=12)
        self.assertLess(crossing['fresnel_transmission_uncoated']['mean'], 1.0)
        waist = doc['ports']['source']['mfd_um'][0] / 2
        for candidate in self.forward['candidates']:
            scene = candidate['scene']
            self.assertEqual(scene['path']['points_mm'][0], doc['ports']['source']['position_mm'])
            self.assertEqual(scene['path']['segments'][0]['medium'], 'ambient')
            self.assertEqual({s['medium'] for s in scene['path']['segments'][1:]}, {'block'})
            self.assertAlmostEqual(scene['beam']['samples'][0]['radius_t_um'], waist, places=6)
            self.assertAlmostEqual(candidate['metrics']['ambient_path_mm'], 0.1, places=9)
            self.assertAlmostEqual(scene['path']['total_length_mm'], candidate['metrics']['total_path_mm'], places=9)

    def test_target_crossing_arrives_at_the_fiber_mode(self):
        """Exact relay to the equivalent in-block Port, then the air gap, must recover the fiber waist."""
        self.assertEqual(self.backward['crossing']['side'], 'target')
        self.assertEqual(self.backward['family'], 'exact')
        waist = load('S2a-1550-glass')['ports']['source']['mfd_um'][0] / 2
        for candidate in self.backward['candidates']:
            scene = candidate['scene']
            self.assertEqual(scene['path']['segments'][-1]['medium'], 'ambient')
            last = scene['beam']['samples'][-1]
            self.assertAlmostEqual(last['radius_t_um'], waist, delta=waist * 1e-6)
            self.assertAlmostEqual(last['radius_s_um'], waist, delta=waist * 1e-6)

    def test_shallow_guide_reports_the_region_limit(self):
        result = api.design(load('S2b-1550-glass'))
        self.assertEqual(result['status'], 'Fail')
        kinds = {g['kind'] for g in result['guidance']}
        self.assertIn('block_region', kinds)
        self.assertIn('no_candidate', kinds)


if __name__ == '__main__':
    unittest.main()
