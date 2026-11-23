"""P2 continuous candidate generator: physics cross-checks, guards, constraints, determinism."""

import copy
import json
import math
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from photonic_architecture_explorer import search  # noqa: E402
from photonic_architecture_explorer.design_document import to_engine_input  # noqa: E402
from photonic_architecture_explorer.external import adapt_external  # noqa: E402
from photonic_architecture_explorer.gaussian import Gaussian, mode_overlap  # noqa: E402
from photonic_architecture_explorer.geometry import dot, sub  # noqa: E402
from photonic_architecture_explorer.package_geometry import patch_world_aabb, segment_hits_box  # noqa: E402
from photonic_architecture_explorer.solver import MAX_FOOTPRINT_SLOPE  # noqa: E402

SCENARIOS = ROOT / 'src/photonic_architecture_explorer/scenarios'


def engine(name):
    return to_engine_input(json.loads((SCENARIOS / f'{name}.json').read_text(encoding='utf-8')))


RESULTS = {}


def run(name, constraints=search.Constraints()):
    key = (name, constraints)
    if key not in RESULTS:
        RESULTS[key] = search.design_continuous(engine(name), constraints, include_map=False)
    return RESULTS[key]


class ClosedFormTest(unittest.TestCase):
    def test_axis_chain_and_overlap_match_the_engine_gaussian(self):
        rng = random.Random(7)
        for _ in range(40):
            wavelength, index = rng.choice((1.31e-6, 1.55e-6)), rng.choice((1.0, 1.45))
            lam_n = wavelength / (math.pi * index)
            source = Gaussian.from_radii((rng.uniform(4e-6, 10e-6),) * 2, wavelength, index)
            target = Gaussian.from_radii((rng.uniform(4e-6, 10e-6), rng.uniform(4e-6, 10e-6)), wavelength, index)
            lengths = [rng.uniform(2e-4, 4e-3) for _ in range(3)]
            cosines = [rng.uniform(0.5, 1.0) for _ in range(2)]
            kt = [rng.uniform(-300, 300) for _ in range(2)]
            ks = [rng.uniform(-300, 300) for _ in range(2)]
            beam = source
            for j in (0, 1):
                beam = beam.propagate(lengths[j]).power((2 * kt[j] / cosines[j], 2 * ks[j] * cosines[j]))
            beam = beam.propagate(lengths[2])
            chains = [search.axis_chain(source.q[i], lengths, cosines, (kt, ks)[i], i, lam_n) for i in (0, 1)]
            for i in (0, 1):
                self.assertAlmostEqual(abs(chains[i]['q'] - beam.q[i]) / abs(beam.q[i]), 0, places=11)
            closed = sum(search.axis_log_eta(chains[i]['q'], target.q[i], lam_n) for i in (0, 1))
            self.assertAlmostEqual(closed, mode_overlap(beam, target)['log_overlap'], places=10)


class ScenarioSearchTest(unittest.TestCase):
    def assert_candidates_respect_guards(self, result, constraints=search.Constraints()):
        for candidate in result['candidates']:
            evaluation = candidate['evaluation']
            self.assertEqual(evaluation['geometry']['status'], 'Pass')
            self.assertEqual(evaluation['model_domain']['status'], 'Pass')
            self.assertLessEqual(candidate['ranking']['max_3w_footprint_curvature'], MAX_FOOTPRINT_SLOPE + 1e-12)
            design = adapt_external(candidate['prescription'])
            for mirror in design.reflectors:
                if constraints.port_halfspace:
                    self.assertGreaterEqual(dot(sub(mirror.vertex, design.source.position), design.source.direction), 0)
                    self.assertLessEqual(dot(sub(mirror.vertex, design.target.position), design.target.direction), 0)
                if constraints.min_radius_of_curvature:
                    self.assertTrue(all(abs(k) <= 1 / constraints.min_radius_of_curvature + 1e-9 for k in mirror.curvatures))

    def test_ldw_1550_has_three_distinct_exact_candidates(self):
        result = run('S2a-1550')
        self.assertEqual(result['status'], 'Computed')
        self.assertGreaterEqual(len(result['candidates']), 3)
        self.assertTrue(all(c['family'] == 'exact' for c in result['candidates']))
        for c in result['candidates']:
            self.assertAlmostEqual(c['evaluation']['gaussian_mode_matching']['normalized_mode_overlap'], 1, places=9)
        positions = {(round(c['parameters']['a_m'], 6), round(c['parameters']['c_m'], 6)) for c in result['candidates']}
        self.assertEqual(len(positions), len(result['candidates']))
        self.assert_candidates_respect_guards(result)

    def test_iox_and_ldw_1310_fall_back_to_labelled_near_match(self):
        for name in ('S2b-1550', 'S2a-1310'):
            with self.subTest(name):
                result = run(name)
                self.assertEqual(result['status'], 'Computed')
                self.assertIn('Near-match', result['reason'])
                self.assertGreaterEqual(len(result['candidates']), 3)
                self.assertEqual(result['search']['exact_feasible'], 0)
                closest = result['search']['closest_exact']
                self.assertGreater(closest['max_footprint_slope'], MAX_FOOTPRINT_SLOPE)
                for c in result['candidates']:
                    self.assertEqual(c['family'], 'near_match')
                    eta = c['evaluation']['gaussian_mode_matching']['normalized_mode_overlap']
                    self.assertTrue(0.95 < eta < 1)
                    self.assertAlmostEqual(1 - eta, c['ranking']['overlap_deficit_at_1e-12'], places=11)
                self.assert_candidates_respect_guards(result)

    def test_domain_refusals_are_unchanged(self):
        self.assertIn('divergence', run('S3')['reason'])
        self.assertIn('noncoplanar', run('S4')['reason'])

    def test_search_is_deterministic(self):
        first = search.design_continuous(engine('S2a-1550'), include_map=False)
        second = search.design_continuous(engine('S2a-1550'), include_map=False)
        strip = lambda r: [{k: v for k, v in c.items()} for c in r['candidates']]  # noqa: E731
        self.assertEqual(strip(first), strip(second))

    def test_port_halfspace_is_a_real_constraint(self):
        free = run('S2a-1550', search.Constraints(port_halfspace=False))
        bounded = run('S2a-1550')
        self.assertGreater(free['search']['exact_feasible'], bounded['search']['exact_feasible'])
        self.assert_candidates_respect_guards(bounded)

    def test_envelope_and_keepout_are_enforced_and_rechecked_by_the_engine(self):
        base = run('S2a-1550')
        middle = base['candidates'][0]['parameters']
        keep = ((0.6e-3, -0.2e-3, 0.3e-3), (1.2e-3, 0.2e-3, 0.7e-3))  # straddles the shortest concept's middle segment
        envelope = ((-0.5e-3, -1e-3, -2e-3), (3.5e-3, 1e-3, 3e-3))
        constraints = search.Constraints(envelope=envelope, keepouts=(keep,), keepout_labels=('connector',), clearance=1e-5)
        document = engine('S2a-1550')
        document['package'] = {
            'frame_id': {'value': 'world', 'unit': 'frame', 'provenance': 'synthetic', 'source': 'test', 'uncertainty': None},
            'available_volume': {'value': {'type': 'aabb', 'min_m': list(envelope[0]), 'max_m': list(envelope[1])}, 'unit': 'm', 'provenance': 'synthetic', 'source': 'test', 'uncertainty': None},
            'keepout_bodies': {'value': [{'type': 'aabb', 'min_m': list(keep[0]), 'max_m': list(keep[1])}], 'unit': 'm', 'provenance': 'synthetic', 'source': 'test', 'uncertainty': None},
            'required_clearance_m': {'value': 1e-5, 'unit': 'm', 'provenance': 'synthetic', 'source': 'test', 'uncertainty': None},
        }
        result = search.design_continuous(document, constraints, include_map=False)
        self.assertNotEqual(middle, result['candidates'][0]['parameters'] if result['candidates'] else None)
        for candidate in result['candidates']:
            design = adapt_external(candidate['prescription'])
            points = [design.source.position, *(m.vertex for m in design.reflectors), design.target.position]
            self.assertFalse(any(segment_hits_box(a, b, keep) for a, b in zip(points, points[1:])))
            for mirror in design.reflectors:
                lo, hi = patch_world_aabb(mirror, design.source.sagittal)
                self.assertTrue(all(e0 <= l and h <= e1 for e0, e1, l, h in zip(*envelope, lo, hi)))
            checks = candidate['evaluation']['package_feasibility']['envelope_geometry']['checks']
            self.assertFalse([c for c in checks if c['status'] == 'Fail'])

    def test_minimum_radius_of_curvature_tightens_the_search(self):
        constraints = search.Constraints(min_radius_of_curvature=4e-3)
        result = run('S2a-1550', constraints)
        self.assert_candidates_respect_guards(result, constraints)

    def test_pose_tolerance_is_finite_and_ordered(self):
        result = run('S2a-1550')
        values = [c['worst_pose_mismatch_db'] for c in result['candidates']]
        self.assertTrue(all(v is not None and 0 <= v < 100 for v in values))
        best = min(result['candidates'], key=lambda c: c['worst_pose_mismatch_db'])
        self.assertIn('robust_alignment', best['roles'])

    def test_budget(self):
        for name in ('S1', 'S2a-1310', 'S2b-1550'):
            self.assertLess(run(name)['search']['elapsed_seconds'], 15)


if __name__ == '__main__':
    unittest.main()
