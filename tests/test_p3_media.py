"""P3 planar block surface: q transform against an exact ray trace and field continuity."""

import cmath
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from photonic_architecture_explorer import media  # noqa: E402
from photonic_architecture_explorer.gaussian import Gaussian  # noqa: E402
from photonic_architecture_explorer.geometry import Port, add, cross, dot, mul, sub, unit  # noqa: E402


def snell(direction, normal, n1, n2):
    """Independent textbook Snell (normal points against the incoming ray)."""
    cos1 = -dot(direction, normal)
    tangent = add(direction, mul(normal, cos1))
    sin2 = n1 / n2 * math.sqrt(max(0.0, 1 - cos1 * cos1))
    t = unit(tangent) if math.hypot(*tangent) > 1e-15 else (0.0, 0.0, 0.0)
    return unit(add(mul(t, sin2), mul(normal, -math.sqrt(1 - sin2 * sin2))))


def plane_hit(origin, direction, point, normal):
    t = dot(sub(point, origin), normal) / dot(direction, normal)
    return add(origin, mul(direction, t))


def closest_approach(p1, d1, p2, d2):
    """Parameter along ray 1 of its closest approach to ray 2."""
    w = sub(p1, p2)
    a, b, c, d, e = dot(d1, d1), dot(d1, d2), dot(d2, d2), dot(d1, w), dot(d2, w)
    return (b * e - c * d) / (a * c - b * b)


class InterfaceTest(unittest.TestCase):
    def test_coddington_factors_match_an_exact_ray_trace(self):
        surface, normal = (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)  # block below z = 0
        n1, n2 = 1.0, 1.4440236
        for incidence in (0.0, 10.0, 25.0, 40.0):
            a = math.radians(incidence)
            chief = (math.sin(a), 0.0, -math.cos(a))
            s_obj = 1.7e-3
            source = sub(plane_hit((0, 0, 1e-3), chief, surface, normal), mul(chief, s_obj))
            hit0 = plane_hit(source, chief, surface, normal)
            d0 = snell(chief, normal, n1, n2)
            for axis, perp in (('t', unit(cross((0.0, 1.0, 0.0), chief))), ('s', (0.0, 1.0, 0.0))):
                delta = 1e-4  # small pencil; well conditioned and aberration ~ delta^2
                images = []
                for sign in (1, -1):  # a symmetric pencil cancels the first-order (coma-like) term
                    ray = unit(add(chief, mul(perp, sign * delta)))
                    hit = plane_hit(source, ray, surface, normal)
                    refracted = snell(ray, normal, n1, n2)
                    # Virtual image: where the refracted pencil appears to diverge from, measured along d0.
                    images.append(closest_approach(hit0, d0, hit, refracted))
                image = sum(images) / 2
                predicted = media.q_scale(n1, n2, math.cos(a), dot(d0, mul(normal, -1)))[0 if axis == 't' else 1] * s_obj
                self.assertAlmostEqual(-image / predicted, 1, places=5, msg=f'{axis} at {incidence} deg')

    def test_field_is_continuous_across_a_normal_surface(self):
        lam, n1, n2 = 1.55e-6, 1.0, 1.51
        beam = Gaussian.from_radii((5.2e-6, 6e-6), lam, n1, (120.0, -40.0))
        factor = media.q_scale(n1, n2, 1.0, 1.0)
        inside = Gaussian(*(q * f for q, f in zip(beam.q, factor)), lam, n2)
        for axis in (0, 1):
            for x in (0.0, 2e-6, 5e-6, 9e-6):
                self.assertAlmostEqual(abs(beam.axis_field(x, axis) - inside.axis_field(x, axis)), 0, places=9)

    def test_cross_source_and_cross_target_are_reverse_paths(self):
        block = media.Block(1.444, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        a = math.radians(20)
        d = (math.sin(a), 0.0, -math.cos(a))
        mode = Gaussian.from_radii((4.6e-6, 4.6e-6), 1.31e-6, 1.0)
        source = Port((0.0, 0.0, 0.3e-3), d, (0.0, 1.0, 0.0), mode)
        going = media.cross_source(source, block, 1.0)
        # A Target in air receiving the time-reversed beam: same plane, reversed direction, conjugate history.
        back_dir = mul(d, -1)
        q_air_at_port = tuple(-(q.conjugate()) for q in mode.q)  # time reversal of a Gaussian: q -> -q*
        target = Port((0.0, 0.0, 0.3e-3), back_dir, (0.0, 1.0, 0.0), Gaussian(*q_air_at_port, 1.31e-6, 1.0))
        coming = media.cross_target(target, block, 1.0)
        for q_out, q_in in zip(going.q_in_block, coming.q_in_block):
            self.assertAlmostEqual(abs(q_out - (-(q_in.conjugate()))) / abs(q_out), 0, places=12)
        self.assertAlmostEqual(dot(going.direction_in_block, coming.direction_in_block), -1, places=12)

    def test_refusals(self):
        block = media.Block(1.444, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        mode = Gaussian.from_radii((4.6e-6, 4.6e-6), 1.31e-6, 1.0)
        away = Port((0.0, 0.0, 1e-3), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), mode)
        with self.assertRaises(Exception):
            media.cross_source(away, block, 1.0)
        d = unit((0.5, 0.0, -1.0))
        rolled = Port((0.0, 0.0, 1e-3), d, unit(cross(d, (0.0, 1.0, 0.0))), mode)  # s lies in the plane of incidence
        with self.assertRaises(Exception):
            media.cross_source(rolled, block, 1.0)
        aligned = Port((0.0, 0.0, 1e-3), d, (0.0, 1.0, 0.0), mode)
        self.assertGreater(media.cross_source(aligned, block, 1.0).refraction_deg, 0)
        self.assertGreater(media.fresnel_transmission(1.0, 1.444, 1.0, 1.0)[2], 0.96)
        self.assertTrue(media.tir_possible(1.444, 1.0, 50.0))
        self.assertFalse(media.tir_possible(1.444, 1.0, 22.5))


if __name__ == '__main__':
    unittest.main()
