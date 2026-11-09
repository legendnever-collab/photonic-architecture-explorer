"""Independent analytical, sampled-field and exact-surface differential references.

Reference kernels below do not call production propagation, power or reflection.
"""

import json
import math
from dataclasses import replace
from pathlib import Path
import unittest
import numpy as np

from photonic_architecture_explorer.gaussian import Gaussian, DomainError, mode_overlap
from photonic_architecture_explorer.geometry import (
    Port, Reflector, frame, to_local, to_world, reflect, patch_intersections,
)
from photonic_architecture_explorer.solver import evaluate
from photonic_architecture_explorer.benchmark import load_case, run

FIXTURE = Path(__file__).resolve().parents[1]/'examples/m1_001.json'
LAM = 1.31e-6


def sampled_field(x, width, curvature, index=1., center=0., slope=0.):
    """Direct normalized field definition, independent of production field code."""
    y = x-center
    return (2/(np.pi*width**2))**0.25 * np.exp(
        -(y/width)**2-1j*np.pi*index/LAM*curvature*y*y-2j*np.pi*index/LAM*slope*y)


def fresnel(field, dx, distance, index=1.):
    freq = np.fft.fftfreq(len(field), d=dx)
    return np.fft.ifft(np.fft.fft(field)*np.exp(1j*np.pi*LAM/index*distance*freq**2))


def exact_surface_ray(height, axis, angle, kt, ks):
    """Exact Euclidean ray / quadratic surface intersection and vector reflection.

    Local surface z=(kt*x²+ks*y²)/2, normal into +z. Input/output planes pass
    through vertex perpendicular to their chief rays. Returns physical h,theta.
    """
    normal = np.array([0., 0., 1.])
    di = np.array([math.sin(angle), 0., -math.cos(angle)])
    do = np.array([math.sin(angle), 0., math.cos(angle)])
    sagittal = np.array([0., 1., 0.])
    ti, to = np.cross(sagittal, di), np.cross(sagittal, do)
    ei = ti if axis == 0 else sagittal
    eo = to if axis == 0 else sagittal
    origin = height*ei
    # Newton solve for the near-vertex root; no paraxial power in this reference.
    distance = -origin[2]/di[2]
    for _ in range(12):
        hit = origin+distance*di
        residual = hit[2]-(kt*hit[0]**2+ks*hit[1]**2)/2
        derivative = di[2]-kt*hit[0]*di[0]-ks*hit[1]*di[1]
        distance -= residual/derivative
    hit = origin+distance*di
    n = normal-np.array([kt*hit[0], ks*hit[1], 0.])
    n /= np.linalg.norm(n)
    reflected = di-2*np.dot(di, n)*n
    at_plane = hit-reflected*np.dot(hit, do)/np.dot(reflected, do)
    return np.dot(at_plane, eo), np.dot(reflected, eo)/np.dot(reflected, do)


class GaussianReferences(unittest.TestCase):
    def test_free_propagation_closed_form_in_air_and_dielectric(self):
        for n in (1., 1.45):
            for length in (0., 1e-5, 1e-3, 0.01):
                g = Gaussian.from_radii((8e-6, 12e-6), index=n).propagate(length)
                for w0, p in zip((8e-6, 12e-6), g.parameters()):
                    zr = np.pi*n*w0**2/LAM
                    self.assertAlmostEqual(p['radius_m']/w0, math.hypot(1, length/zr), places=12)
                    self.assertAlmostEqual(p['curvature_per_m'], length/(length**2+zr**2), places=9)

    def test_free_propagation_independent_fresnel_grid_convergence(self):
        for count, span in ((4096, 0.0012), (8192, 0.0016)):
            dx = span/count
            x = (np.arange(count)-count/2)*dx
            for n in (1., 1.45):
                w0, length = 8e-6, 0.0013
                numerical = fresnel(sampled_field(x, w0, 0., n), dx, length, n)
                p = Gaussian.from_radii((w0, w0), index=n).propagate(length).parameters()[0]
                ref = sampled_field(x, p['radius_m'], p['curvature_per_m'], n)
                self.assertAlmostEqual(float(np.sum(abs(numerical)**2)*dx), 1., places=12)
                self.assertAlmostEqual(float(abs(np.vdot(ref, numerical)*dx)**2), 1., places=11)

    def test_curved_reflection_independent_phase_screen(self):
        count, span = 8192, 0.0016
        dx = span/count
        x = (np.arange(count)-count/2)*dx
        for power in (-1200., 0., 600., 1400.):
            g = Gaussian.from_radii((8e-6, 12e-6)).propagate(0.001)
            for axis, p in enumerate(g.parameters()):
                field = sampled_field(x, p['radius_m'], p['curvature_per_m'])
                numerical = fresnel(field*np.exp(1j*np.pi/LAM*power*x*x), dx, 0.0007)
                final = g.power((power, power)).propagate(0.0007).parameters()[axis]
                ref = sampled_field(x, final['radius_m'], final['curvature_per_m'])
                self.assertAlmostEqual(float(abs(np.vdot(ref, numerical)*dx)**2), 1., places=10)

    def test_full_two_mirror_relay_fresnel_reference(self):
        count, span = 16384, 0.0024
        dx = span/count
        x = (np.arange(count)-count/2)*dx
        for case in ('flat', 'curved', 'spherical_control'):
            source, target, mirrors = load_case(FIXTURE, case)
            # Fixed benchmark values, not production matrix/power calls.
            powers = {'flat': (0., 0.), 'curved': (1000., 1000.),
                      'spherical_control': (1000/math.sqrt(.5), 1000*math.sqrt(.5))}[case]
            eta = 1.
            for w0, power in zip((8e-6, 12e-6), powers):
                initial = sampled_field(x, w0, 0.)
                field = fresnel(initial, dx, .001)
                field *= np.exp(1j*np.pi/LAM*power*x*x)
                field = fresnel(field, dx, .002)
                field *= np.exp(1j*np.pi/LAM*power*x*x)
                field = fresnel(field, dx, .001)
                self.assertAlmostEqual(float(np.sum(abs(field)**2)*dx), 1., places=12)
                eta *= float(abs(np.vdot(initial, field)*dx)**2)
            actual = evaluate(source, target, mirrors)['gaussian_mode_matching']['normalized_mode_overlap']
            self.assertAlmostEqual(actual, eta, places=10)

    def test_overlap_analytical_identity_width_offset_tilt_defocus(self):
        w, v = 8e-6, 12e-6
        g = Gaussian.from_radii((w, v))
        self.assertAlmostEqual(mode_overlap(g, g)['normalized_mode_overlap'], 1., places=14)
        h = Gaussian.from_radii((2*w, 3*v))
        self.assertAlmostEqual(mode_overlap(g, h)['normalized_mode_overlap'], (4/5)*(6/10), places=14)
        offset, tilt = (2e-6, -3e-6), (.005, -.008)
        expected = math.exp(-sum((d/a)**2+(math.pi*a*t/LAM)**2
                                for d, a, t in zip(offset, (w, v), tilt)))
        self.assertAlmostEqual(mode_overlap(g, g, offset, tilt)['normalized_mode_overlap'], expected, places=13)
        length = .004
        expected = math.prod((1+(length/(2*q.imag))**2)**-0.5 for q in g.q)
        self.assertAlmostEqual(mode_overlap(g.propagate(length), g)['normalized_mode_overlap'], expected, places=14)

    def test_overlap_independent_quadrature_with_two_curved_fields(self):
        gi = Gaussian.from_radii((14e-6, 19e-6), curvature=(230., -650.))
        gt = Gaussian.from_radii((9e-6, 11e-6), curvature=(-400., 120.))
        offset, slope = (3e-6, -2e-6), (.012, -.009)
        expected = mode_overlap(gi, gt, offset, slope)['normalized_mode_overlap']
        for count in (2048, 4096):
            dx = 240e-6/count
            x = (np.arange(count)-count/2)*dx
            eta = 1.
            for pi, pt, h, t in zip(gi.parameters(), gt.parameters(), offset, slope):
                a = sampled_field(x, pi['radius_m'], pi['curvature_per_m'], center=h, slope=t)
                b = sampled_field(x, pt['radius_m'], pt['curvature_per_m'])
                self.assertAlmostEqual(float(np.sum(abs(a)**2)*dx), 1., places=13)
                self.assertAlmostEqual(float(np.sum(abs(b)**2)*dx), 1., places=13)
                eta *= float(abs(np.vdot(b, a)*dx)**2)
            self.assertAlmostEqual(expected, eta, places=12)

    def test_overlap_reciprocity_and_underflow(self):
        a = Gaussian.from_radii((8e-6, 12e-6)).propagate(.001)
        b = Gaussian.from_radii((11e-6, 7e-6)).propagate(.0004)
        self.assertAlmostEqual(mode_overlap(a, b)['normalized_mode_overlap'], mode_overlap(b, a)['normalized_mode_overlap'], places=14)
        r = mode_overlap(a, b, offset=(.01, .01))
        self.assertTrue(r['underflow'])
        self.assertTrue(math.isfinite(r['mismatch_db']))

    def test_normalization_at_every_benchmark_plane(self):
        source, _, _ = load_case(FIXTURE)
        g = source.mode
        for distance, powers in ((.001, (1000., 1000.)), (.002, (1000., 1000.)), (.001, (0., 0.))):
            g = g.propagate(distance).power(powers)
            for axis, p in enumerate(g.parameters()):
                w = p['radius_m']
                x = (np.arange(2048)-1024)*16*w/2048
                integral = sum(abs(g.axis_field(float(v), axis))**2 for v in x)*16*w/2048
                self.assertAlmostEqual(integral, 1., places=12)

    def test_nonphysical_and_numerically_invalid_inputs(self):
        for q in (0j, 1-1j, complex(float('nan'), 1), complex(0, float('inf'))):
            with self.subTest(q=q), self.assertRaises(DomainError):
                Gaussian(q, 1j)
        for radii in ((0., 1e-5), (-1., 1.), (float('nan'), 1.), (1.,)):
            with self.subTest(radii=radii), self.assertRaises(DomainError):
                Gaussian.from_radii(radii)
        g = Gaussian.from_radii((8e-6, 12e-6))
        for fn in (lambda: g.propagate(-1), lambda: g.power((float('nan'), 0.)),
                   lambda: mode_overlap(g, g, slope=(.06, 0.)),
                   lambda: mode_overlap(g, g, offset=(float('inf'), 0.)),
                   lambda: mode_overlap(g, replace(g, index=1.5)),
                   lambda: mode_overlap(g, replace(g, wavelength=1.55e-6)),
                   lambda: Gaussian(1+1e-16j, 1j).power((1., 1.))):
            with self.subTest(fn=fn), self.assertRaises(DomainError):
                fn()


class ReflectionReferences(unittest.TestCase):
    def test_surface_derivatives_recover_oblique_principal_powers(self):
        for degrees in (0., 15., 45., 65.):
            angle = math.radians(degrees)
            for kt, ks in ((0., 0.), (500., 500.), (350., 700.), (-350., -700.)):
                m = Reflector((0, 0, 0), (0, 0, 1), (kt, ks), (.001, .001))
                powers = m.powers(math.cos(angle))
                for axis in (0, 1):
                    for epsilon in (1e-8, 5e-9):
                        hp, sp = exact_surface_ray(epsilon, axis, angle, kt, ks)
                        hm, sm = exact_surface_ray(-epsilon, axis, angle, kt, ks)
                        actual = -(sp-sm)/(hp-hm)
                        self.assertAlmostEqual(actual, powers[axis], delta=2e-5)
                        parity = (hp-hm)/(2*epsilon)
                        self.assertAlmostEqual(parity, -1. if axis == 0 else 1., places=7)

    def test_reflection_and_frame_transport(self):
        source, target, mirrors = load_case(FIXTURE)
        d = source.direction
        for m in mirrors:
            before = frame(d, source.sagittal)
            out = reflect(d, m.normal)
            after = frame(out, source.sagittal)
            self.assertAlmostEqual(np.linalg.norm(out), 1., places=14)
            self.assertAlmostEqual(np.dot(d, m.normal), -np.dot(out, m.normal), places=14)
            # Physical reflection reverses tangential parity; intensity/Q axes retained.
            self.assertTrue(np.allclose(reflect(before[0], m.normal), -np.array(after[0])))
            self.assertTrue(np.allclose(reflect(before[1], m.normal), after[1]))
            value = (3e-6, -8e-6, 2e-6)
            self.assertTrue(np.allclose(to_world(to_local(value, after), after), value, atol=1e-18))
            self.assertAlmostEqual(np.linalg.det(after), 1., places=14)
            d = out
        self.assertTrue(np.allclose(d, target.direction))

    def test_flat_fold_equals_unfolded_propagation(self):
        source, target, mirrors = load_case(FIXTURE, 'flat')
        result = evaluate(source, target, mirrors)
        for p, q in zip(result['gaussian_mode_matching']['output_axes'], source.mode.q):
            w0 = math.sqrt(LAM*q.imag/math.pi)
            expected = w0*math.hypot(1, .004/q.imag)
            self.assertAlmostEqual(p['radius_m'], expected, places=15)
        self.assertEqual(result['geometry']['status'], 'Pass')

    def test_quadratic_patch_intersection(self):
        m = Reflector((0, 0, 0), (0, 0, 1), (500., 700.), (.001, .001))
        roots = patch_intersections((.0001, .0002, .001), (0, 0, -1), m, (0, 1, 0))
        expected = .001-(500*(.0001)**2+700*(.0002)**2)/2
        self.assertEqual(len(roots), 1)
        self.assertAlmostEqual(roots[0], expected, places=15)


class BenchmarkAndDomain(unittest.TestCase):
    def setUp(self):
        self.source, self.target, self.mirrors = load_case(FIXTURE)

    def test_frozen_acceptance_and_fixed_ports(self):
        before = repr((self.source, self.target, self.mirrors))
        evaluate(self.source, self.target, self.mirrors)
        report = run(FIXTURE)
        self.assertEqual(report['completion_gate']['status'], 'Pass')
        self.assertEqual(before, repr((self.source, self.target, self.mirrors)))
        self.assertGreater(report['cases']['curved']['gaussian_mode_matching']['normalized_mode_overlap'], .9999999999)
        for case in report['cases'].values():
            self.assertEqual(case['physical_losses']['status'], 'Uncomputed')
            self.assertIsNone(case['physical_losses']['total_coupling'])
            self.assertEqual(case['fabrication']['status'], 'Uncomputed')
        p = report['cases']['spherical_control']['samples'][1]['powers_per_m']
        self.assertAlmostEqual(p[0]/p[1], 2., places=13)

    def test_common_rigid_transform_preserves_results(self):
        # Rodrigues rotation about a generic axis, plus common translation.
        axis = np.array([1., 2., 3.]); axis /= np.linalg.norm(axis)
        angle = .71
        k = np.array([[0., -axis[2], axis[1]], [axis[2], 0., -axis[0]], [-axis[1], axis[0], 0.]])
        rotation = np.eye(3)+np.sin(angle)*k+(1-np.cos(angle))*(k@k)
        vector = lambda v: tuple(rotation@np.array(v))
        point = lambda v: tuple(rotation@np.array(v)+np.array([.1, -.03, .07]))
        ports = [replace(p, position=point(p.position), direction=vector(p.direction), sagittal=vector(p.sagittal))
                 for p in (self.source, self.target)]
        mirrors = [replace(m, vertex=point(m.vertex), normal=vector(m.normal)) for m in self.mirrors]
        a, b = evaluate(self.source, self.target, self.mirrors), evaluate(*ports, mirrors)
        self.assertEqual(b['model_domain']['status'], 'Pass', b)
        self.assertAlmostEqual(a['gaussian_mode_matching']['normalized_mode_overlap'], b['gaussian_mode_matching']['normalized_mode_overlap'], places=12)

    def assert_rejected(self, source, target, mirrors, category):
        result = evaluate(source, target, mirrors)
        self.assertEqual(result[category]['status'], 'Fail', result)
        self.assertEqual(result['gaussian_mode_matching']['status'], 'Uncomputed')
        self.assertNotIn('normalized_mode_overlap', result['gaussian_mode_matching'])

    def test_geometry_failures(self):
        source, target, mirrors = self.source, self.target, self.mirrors
        cases = [
            (replace(source, direction=(0, 0, 1)), target, mirrors),
            (source, replace(target, direction=(0, 0, 1)), mirrors),
            (source, target, (replace(mirrors[0], normal=(1, 0, 0)), mirrors[1])),
            (source, target, (replace(mirrors[0], vertex=source.position), mirrors[1])),
            (source, target, (replace(mirrors[0], normal=(1, 0, -1)), mirrors[1])),
            (source, target, (replace(mirrors[0], curvatures=(3000., 3000.)), mirrors[1])),
            (source, target, mirrors[:1]),
        ]
        for args in cases:
            with self.subTest(args=args):
                self.assert_rejected(*args, 'geometry')

    def test_domain_failures(self):
        source, target, mirrors = self.source, self.target, self.mirrors
        cases = [
            (source, replace(target, mode=replace(target.mode, index=1.5)), mirrors),
            (source, replace(target, mode=replace(target.mode, wavelength=1.55e-6)), mirrors),
            (source, replace(target, sagittal=(0, 0, 1)), mirrors),
            (replace(source, sagittal=(0, 0, 1)), target, mirrors),
            (replace(source, mode=Gaussian.from_radii((1e-6, 1e-6))), target, mirrors),
            (source, replace(target, mode=Gaussian.from_radii((1e-6, 1e-6))), mirrors),
            (source, target, (replace(mirrors[0], half_aperture=(1e-6, 1e-6)), mirrors[1])),
            (source, target, (replace(mirrors[0], curvatures=(900., 900.)), mirrors[1])),
        ]
        for args in cases:
            with self.subTest(args=args):
                self.assert_rejected(*args, 'model_domain')

    def test_grazing_and_nonplanar_paths_are_withheld(self):
        # Build geometrically exact paths to isolate model-domain rejection.
        for middle in ((math.cos(.2), 0., math.sin(.2)), (0., .6, .8)):
            source = self.source
            v1 = np.array([.001, 0., 0.]); mid = np.array(middle)
            v2 = v1+.002*mid
            d0 = np.array(source.direction); dout = np.array([1., 0., 0.])
            m1 = replace(self.mirrors[0], vertex=tuple(v1), normal=tuple(mid-d0))
            m2 = replace(self.mirrors[1], vertex=tuple(v2), normal=tuple(dout-mid))
            target = replace(self.target, position=tuple(v2+.001*dout))
            self.assert_rejected(source, target, (m1, m2), 'model_domain')

    def test_vector_input_validation(self):
        for fn in (lambda: replace(self.source, direction=(0, 0, 0)),
                   lambda: replace(self.source, position=(float('nan'), 0, 0)),
                   lambda: replace(self.source, sagittal=(1, 0, 0)),
                   lambda: replace(self.mirrors[0], curvatures=(float('inf'), 0)),
                   lambda: replace(self.mirrors[0], half_aperture=(-1, 1))):
            with self.subTest(fn=fn), self.assertRaises(DomainError):
                fn()


if __name__ == '__main__':
    unittest.main()
