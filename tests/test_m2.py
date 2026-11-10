"""M2 independent exact-surface Newton reference and linear-domain checks."""
import math
import unittest
from types import SimpleNamespace
from dataclasses import replace
from pathlib import Path
import numpy as np
from photonic_architecture_explorer.benchmark import load_case
from photonic_architecture_explorer.diagnostics import run, ray_to_target, finite_fan
from photonic_architecture_explorer.gaussian import DomainError

FIXTURE = Path(__file__).resolve().parents[1]/'examples/m1_001.json'


def newton_reference(source, target, mirrors):
    """Independent Newton surface roots and vector normals, no production geometry."""
    origin = np.array(source.position)
    direction = np.array(source.direction)
    s = np.array(source.sagittal)
    for mirror in mirrors:
        n = np.array(mirror.normal)
        t = np.cross(s, n); t /= np.linalg.norm(t)
        vertex = np.array(mirror.vertex)
        kt, ks = mirror.curvatures
        distance = np.dot(vertex-origin, n)/np.dot(direction, n)
        for _ in range(20):
            pos = origin+distance*direction-vertex
            u, v, h = np.dot(pos, t), np.dot(pos, s), np.dot(pos, n)
            distance -= (h-(kt*u*u+ks*v*v)/2)/(np.dot(direction,n)-kt*u*np.dot(direction,t)-ks*v*np.dot(direction,s))
        origin = origin+distance*direction
        pos = origin-vertex
        normal = n-kt*np.dot(pos,t)*t-ks*np.dot(pos,s)*s
        normal /= np.linalg.norm(normal)
        direction -= 2*np.dot(direction,normal)*normal
    d = np.array(target.direction)
    origin += direction*np.dot(np.array(target.position)-origin,d)/np.dot(direction,d)
    t = np.cross(np.array(target.sagittal),d)
    delta = origin-np.array(target.position)
    return [np.dot(delta,t),np.dot(delta,s)], [np.dot(direction,t)/np.dot(direction,d),np.dot(direction,s)/np.dot(direction,d)]


class M2References(unittest.TestCase):
    def test_nominal_chief_closes_and_surface_law_holds(self):
        source, target, mirrors = load_case(FIXTURE)
        r = ray_to_target(source.position, source.direction, target, mirrors, source.sagittal)
        self.assertLess(math.hypot(*r['target_offset_m']), 1e-15)
        self.assertLess(math.hypot(*r['target_slope']), 1e-14)
        for hit in r['hits']:
            self.assertLess(abs(hit['surface_residual_m']), 1e-15)
            di, do, n = map(np.array, (hit['incoming'], hit['outgoing'], hit['normal']))
            self.assertAlmostEqual(np.dot(di,n), -np.dot(do,n), places=13)
            self.assertTrue(np.allclose(di-n*np.dot(di,n),do-n*np.dot(do,n),atol=1e-13))

    def test_placement_independent_newton_reference_all_12_cases(self):
        source, target, mirrors = load_case(FIXTURE)
        for index in range(2):
            for axis in range(3):
                for delta in (-5e-6, 5e-6):
                    altered = list(mirrors)
                    v = list(mirrors[index].vertex); v[axis] += delta
                    altered[index] = replace(mirrors[index], vertex=v)
                    ray = ray_to_target(source.position, source.direction, target, altered, source.sagittal)
                    offset, slope = newton_reference(source,target,altered)
                    np.testing.assert_allclose(ray['target_offset_m'],offset,rtol=1e-8,atol=1e-14)
                    np.testing.assert_allclose(ray['target_slope'],slope,rtol=1e-8,atol=1e-12)

    def test_flat_fan_linear_exactness(self):
        for extent in (.5,1.,2.):
            fan = finite_fan(*load_case(FIXTURE,'flat'),extent)
            self.assertEqual(fan['status'],'Pass',fan)
            self.assertLess(fan['max_transverse_residual_m'],1e-10)
            self.assertLess(fan['max_slope_residual'],1e-12)

    def test_curved_near_axis_convergence(self):
        previous = None
        for extent in (.01,.005,.0025):
            fan = finite_fan(*load_case(FIXTURE),extent)
            self.assertEqual(fan['status'],'Pass',fan)
            scaled = fan['max_transverse_residual_m']/extent
            if previous is not None:
                self.assertLess(scaled, previous*.65)
            previous=scaled
        self.assertLess(previous,1e-7)

    def test_fan_independent_newton_nonzero_wavefront_rays(self):
        source,target,mirrors=load_case(FIXTURE)
        g=source.mode.propagate(.001).parameters()
        for scale in (-1.,.5,1.):
            t=np.array([0.,0.,-1.]); s=np.array([0.,1.,0.]); d=np.array(source.direction)
            h=np.array([scale*g[0]['radius_m'],scale*g[1]['radius_m']])
            direction=d+t*h[0]*g[0]['curvature_per_m']+s*h[1]*g[1]['curvature_per_m']
            direction/=np.linalg.norm(direction)
            point=np.array(mirrors[0].vertex)+t*h[0]+s*h[1]-.00025*direction
            altered=SimpleNamespace(position=point,direction=direction,sagittal=source.sagittal)
            expected=newton_reference(altered,target,mirrors)
            actual=ray_to_target(point,direction,target,mirrors,source.sagittal)
            np.testing.assert_allclose(actual['target_offset_m'],expected[0],atol=1e-14)
            np.testing.assert_allclose(actual['target_slope'],expected[1],atol=1e-12)

    def test_budget_fixed_ports_and_uncomputed_semantics(self):
        source,target,mirrors=load_case(FIXTURE)
        before=repr((source,target,mirrors))
        r=run(FIXTURE)
        self.assertEqual(len(r['curvature_cases']),8)
        self.assertEqual(len(r['placement_cases']),12)
        self.assertEqual(r['actual_ssc_applicability']['status'],'Uncomputed')
        for case in r['placement_cases']:
            self.assertEqual(case['gaussian_mode_matching']['status'],'Uncomputed')
            self.assertNotIn('normalized_mode_overlap',case['gaussian_mode_matching'])
            self.assertEqual(case['geometry']['target_closure'],'Fail')
        self.assertEqual(repr((source,target,mirrors)),before)
        for fans in r['finite_fans'].values():
            self.assertEqual(sum(f['attempted_rays'] for f in fans),27)
            self.assertTrue(all(f['mode_overlap'] is None for f in fans))
            self.assertTrue(all(f['status'] == 'Pass' and f['traced_rays'] == 9 for f in fans))
        for case in r['curvature_cases']:
            self.assertEqual(case['domain'],'Pass')
            self.assertLess(case['mode_matching']['normalized_mode_overlap'],1.)

    def test_misses_and_invalid_fan_withhold_results(self):
        source,target,mirrors=load_case(FIXTURE)
        with self.assertRaises(DomainError):
            ray_to_target((0.,1.,0.),source.direction,target,mirrors,source.sagittal)
        for extent in (0.,-1.,float('nan'),3.):
            with self.assertRaises(DomainError):
                finite_fan(source,target,mirrors,extent)
        tiny=(replace(mirrors[0],half_aperture=(1e-6,1e-6)),mirrors[1])
        self.assertEqual(finite_fan(source,target,tiny,1.)['status'],'Fail')


if __name__ == '__main__':
    unittest.main()
