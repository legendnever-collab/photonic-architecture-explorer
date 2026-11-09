"""World geometry and local reflection frames; no topology search."""

from dataclasses import dataclass
import math
from .gaussian import DomainError, Gaussian, finite, positive


def vec(v):
    if len(v) != 3:
        raise DomainError("3D vector required")
    finite(*v)
    return tuple(float(x) for x in v)


def add(a, b):
    return tuple(x+y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def mul(a, s):
    return tuple(x*s for x in a)


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def norm(a):
    return math.hypot(*a)


def unit(a):
    a = vec(a)
    if norm(a) < 1e-15:
        raise DomainError("zero direction vector")
    return mul(a, 1/norm(a))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def reflect(direction, normal):
    d, n = unit(direction), unit(normal)
    return sub(d, mul(n, 2*dot(d, n)))


def frame(direction, sagittal):
    d, s = unit(direction), unit(sagittal)
    if abs(dot(d, s)) > 1e-10:
        raise DomainError("sagittal axis must be transverse")
    return (unit(cross(s, d)), s, d)  # t cross s = d


def to_local(vector, basis):
    return tuple(dot(vector, axis) for axis in basis)


def to_world(vector, basis):
    return tuple(sum(vector[j]*basis[j][i] for j in range(3)) for i in range(3))


@dataclass(frozen=True)
class Port:
    position: tuple
    direction: tuple
    sagittal: tuple
    mode: Gaussian

    def __post_init__(self):
        object.__setattr__(self, 'position', vec(self.position))
        object.__setattr__(self, 'direction', unit(self.direction))
        object.__setattr__(self, 'sagittal', unit(self.sagittal))
        frame(self.direction, self.sagittal)


@dataclass(frozen=True)
class Reflector:
    vertex: tuple
    normal: tuple  # points into illuminated ambient
    curvatures: tuple  # positive concave, t/s, m^-1; zero = flat
    half_aperture: tuple

    def __post_init__(self):
        object.__setattr__(self, 'vertex', vec(self.vertex))
        object.__setattr__(self, 'normal', unit(self.normal))
        object.__setattr__(self, 'curvatures', tuple(self.curvatures))
        object.__setattr__(self, 'half_aperture', tuple(self.half_aperture))
        if len(self.curvatures) != 2 or len(self.half_aperture) != 2:
            raise DomainError("two principal curvatures and half-apertures required")
        finite(*self.curvatures)
        positive(*self.half_aperture)

    def powers(self, cosine):
        positive(cosine)
        if cosine > 1+1e-12:
            raise DomainError("invalid incidence cosine")
        return (2*self.curvatures[0]/cosine, 2*self.curvatures[1]*cosine)


def patch_intersections(origin, direction, mirror, sagittal):
    """Exact intersections with local quadratic patch; signed distances returned.

    This is a chief-ray obstruction guard, not a finite-beam aberration solver.
    """
    t = unit(cross(sagittal, mirror.normal))
    u, v, h = to_local(sub(origin, mirror.vertex), (t, sagittal, mirror.normal))
    du, dv, dh = to_local(direction, (t, sagittal, mirror.normal))
    kt, ks = mirror.curvatures
    a = -(kt*du*du+ks*dv*dv)/2
    b = dh-kt*u*du-ks*v*dv
    c = h-(kt*u*u+ks*v*v)/2
    if abs(a) < 1e-14:
        if abs(b) < 1e-14:
            if abs(c) < 1e-12:
                raise DomainError("ray lies on reflector patch surface")
            return []
        roots = [-c/b]
    else:
        disc = b*b-4*a*c
        if disc < 0:
            return []
        q = -0.5*(b+math.copysign(math.sqrt(disc), b))
        roots = [-b/(2*a)] if q == 0 else [q/a, c/q]
    return [l for l in roots if abs(u+l*du) <= mirror.half_aperture[0]
            and abs(v+l*dv) <= mirror.half_aperture[1]]


def trace(source, target, mirrors):
    if len(mirrors) != 2:
        raise DomainError("M1 requires exactly two reflectors")
    points = [source.position, *(m.vertex for m in mirrors), target.position]
    vectors = [sub(b, a) for a, b in zip(points, points[1:])]
    lengths = [norm(v) for v in vectors]
    if min(lengths) < 1e-9:
        raise DomainError("zero/short propagation segment")
    directions = [unit(v) for v in vectors]
    if norm(sub(directions[0], source.direction)) > 1e-10:
        raise DomainError("fixed Source direction does not reach M1 vertex")
    if norm(sub(directions[-1], target.direction)) > 1e-10:
        raise DomainError("fixed Target direction does not match arrival")
    for j, m in enumerate(mirrors):
        if dot(directions[j], m.normal) >= -1e-12:
            raise DomainError("reflector is grazing or back-facing")
        if norm(sub(reflect(directions[j], m.normal), directions[j+1])) > 1e-10:
            raise DomainError("specular reflection does not close fixed path")
    return dict(lengths=lengths, directions=directions,
                cosines=[-dot(directions[j], m.normal) for j, m in enumerate(mirrors)])
