"""P3 step 1: one homogeneous glass block with a planar surface, and Ports on either side.

A Port in the ambient medium whose axis crosses the block surface is replaced by an
equivalent Port just inside the block, so the two-reflector relay is solved in one
homogeneous medium (index n_block) by the unchanged P2 generator and external Adapter.

Crossing a planar surface (paraxial, axes aligned with the plane of incidence):
  direction   Snell's law, n1 sin θ1 = n2 sin θ2
  q (this code's convention 1/q = 1/R - i λ/(π n w²), physical lengths)
      tangential  q2 = q1 · n2 cos²θ2 / (n1 cos²θ1)
      sagittal    q2 = q1 · n2 / n1
  i.e. the plane-surface Coddington equations for the wavefront and w_t2 = w_t1 cos θ2 / cos θ1.
Tests check these against an exact ray trace and against field continuity.
"""

from dataclasses import dataclass
import math

from .gaussian import DomainError
from .geometry import add, cross, dot, mul, sub, unit

MAX_SURFACE_INCIDENCE_DEG = 60.0  # paraxial interface model; beyond this the Port is refused


@dataclass(frozen=True)
class Block:
    index: float
    point: tuple          # a point on the surface (m)
    normal: tuple         # unit, from the block into the ambient medium
    thickness: float | None = None  # m below the surface; None = half-space
    label: str = 'Glass'

    def depth(self, p):
        """Signed distance below the surface (positive inside the block)."""
        return -dot(sub(p, self.point), self.normal)

    def contains(self, p, tol=1e-12):
        d = self.depth(p)
        return d >= -tol and (self.thickness is None or d <= self.thickness + tol)


def refract(direction, normal, n1, n2):
    """Snell refraction of a unit direction at a plane with unit normal (either orientation)."""
    n = normal if dot(direction, normal) < 0 else mul(normal, -1)
    cos1 = -dot(direction, n)
    ratio = n1 / n2
    sin2_sq = ratio * ratio * (1 - cos1 * cos1)
    if sin2_sq >= 1:
        raise DomainError('total internal reflection at the block surface')
    cos2 = math.sqrt(1 - sin2_sq)
    out = add(mul(direction, ratio), mul(n, ratio * cos1 - cos2))
    return unit(out), cos1, cos2


def q_scale(n1, n2, cos1, cos2):
    """(tangential, sagittal) factors with q_after = factor · q_before."""
    return (n2 * cos2 * cos2 / (n1 * cos1 * cos1), n2 / n1)


def fresnel_transmission(n1, n2, cos1, cos2):
    """Plane-wave power transmission (s, p, mean) of an uncoated surface; information only."""
    rs = (n1 * cos1 - n2 * cos2) / (n1 * cos1 + n2 * cos2)
    rp = (n2 * cos1 - n1 * cos2) / (n2 * cos1 + n1 * cos2)
    ts, tp = 1 - rs * rs, 1 - rp * rp
    return ts, tp, (ts + tp) / 2


@dataclass(frozen=True)
class Crossing:
    side: str               # 'source' or 'target'
    point: tuple            # where the axis meets the surface (m)
    ambient_length: float   # m between the Port and the surface
    incidence_deg: float    # in the ambient medium
    refraction_deg: float   # in the block
    direction_in_block: tuple
    q_in_block: tuple       # complex (t, s) just inside the block, block index
    q_scale: tuple
    transmission: tuple     # (s, p, mean) plane-wave Fresnel, uncoated


def _check_axes(sagittal, normal, cos1):
    if cos1 < 1 - 1e-12 and abs(dot(sagittal, normal)) > 1e-10:
        raise DomainError('oblique surface crossing with Port axes rolled out of the plane of incidence')


def cross_source(port, block, ambient_index):
    """Source in the ambient medium travelling into the block."""
    d, s = port.direction, port.sagittal
    toward = dot(d, block.normal)
    if toward >= -1e-12:
        raise DomainError('Source axis does not travel into the block surface')
    length = dot(sub(block.point, port.position), block.normal) / toward
    if length < 0:
        raise DomainError('Source Port lies inside the block')
    d2, cos1, cos2 = refract(d, block.normal, ambient_index, block.index)
    if math.degrees(math.acos(min(1.0, cos1))) > MAX_SURFACE_INCIDENCE_DEG:
        raise DomainError('surface incidence exceeds 60 degrees')
    _check_axes(s, block.normal, cos1)
    scale = q_scale(ambient_index, block.index, cos1, cos2)
    q = tuple((qa + length) * f for qa, f in zip(port.mode.q, scale))
    return Crossing('source', add(port.position, mul(d, length)), length,
                    math.degrees(math.acos(min(1.0, cos1))), math.degrees(math.acos(min(1.0, cos2))),
                    d2, q, scale, fresnel_transmission(ambient_index, block.index, cos1, cos2))


def cross_target(port, block, ambient_index):
    """Target in the ambient medium, reached by light leaving the block."""
    d, s = port.direction, port.sagittal
    leaving = dot(d, block.normal)
    if leaving <= 1e-12:
        raise DomainError('Target arrival does not come out of the block surface')
    length = dot(sub(port.position, block.point), block.normal) / leaving
    if length < 0:
        raise DomainError('Target Port lies inside the block')
    point = sub(port.position, mul(d, length))
    # Reverse the exit: the arriving ray travelling -d refracts from the ambient into the block.
    back, cos_air, cos_glass = refract(mul(d, -1), block.normal, ambient_index, block.index)
    if math.degrees(math.acos(min(1.0, cos_air))) > MAX_SURFACE_INCIDENCE_DEG:
        raise DomainError('surface incidence exceeds 60 degrees')
    _check_axes(s, block.normal, cos_air)
    scale = q_scale(block.index, ambient_index, cos_glass, cos_air)  # block → ambient
    q = tuple((qa - length) / f for qa, f in zip(port.mode.q, scale))
    return Crossing('target', point, length, math.degrees(math.acos(min(1.0, cos_air))),
                    math.degrees(math.acos(min(1.0, cos_glass))), mul(back, -1), q, scale,
                    fresnel_transmission(block.index, ambient_index, cos_glass, cos_air))


def q_to_record(q, wavelength, index):
    """(w, 1/R) per axis for the engine's MFD + curvature Port fields."""
    w, c = [], []
    for value in q:
        inv = 1 / value
        if inv.imag >= 0:
            raise DomainError('invalid Gaussian after the surface')
        w.append(math.sqrt(-wavelength / (math.pi * index * inv.imag)))
        c.append(inv.real)
    return [2 * x for x in w], c


def tir_possible(index, ambient_index, incidence_deg):
    """Whether a reflector inside the block at this incidence could work by total internal reflection."""
    if index <= ambient_index:
        return False
    return incidence_deg > math.degrees(math.asin(ambient_index / index))


def surface_axes(block):
    """Two unit vectors spanning the surface (for drawing)."""
    seed = (1.0, 0.0, 0.0) if abs(block.normal[0]) < 0.9 else (0.0, 1.0, 0.0)
    u = unit(cross(block.normal, seed))
    return u, unit(cross(block.normal, u))

