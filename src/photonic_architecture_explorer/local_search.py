"""R8 fixed-port geometry and Guard-limited Near-Match seed construction."""
import itertools
from .design import power_pairs
from .geometry import add, dot, mul, norm, sub, unit
from .solver import MAX_FOOTPRINT_SLOPE


def geometry(ports, a, c):
    source, target = ports.source, ports.target
    vertices = (
        add(source.position, mul(source.direction, a)),
        sub(target.position, mul(target.direction, c)),
    )
    middle = sub(vertices[1], vertices[0])
    direction = unit(middle)
    normals = (
        unit(sub(direction, source.direction)),
        unit(sub(target.direction, direction)),
    )
    lengths = (a, norm(middle), c)
    cosines = (-dot(source.direction, normals[0]), -dot(direction, normals[1]))
    return vertices, normals, lengths, cosines


def exact_curvatures(ports, lengths, cosines):
    tangential, sagittal = [
        power_pairs(source, target, *lengths)
        for source, target in zip(ports.source.mode.q, ports.target.mode.q, strict=True)
    ]
    for t, s in itertools.product(tangential, sagittal):
        yield tuple((t[j] * cos / 2, s[j] / (2 * cos)) for j, cos in enumerate(cosines))


def bounded_coordinates(ports, lengths, cosines, curvatures, scale):
    """Project an exact-q seed into the Near-Match footprint parameterization."""
    beam = ports.source.mode
    coordinates = []
    limit = MAX_FOOTPRINT_SLOPE * (1 - 1e-10) * scale
    for length, cos, proposed in zip(lengths[:2], cosines, curvatures, strict=True):
        beam = beam.propagate(length)
        tangential, sagittal = (axis["radius_m"] for axis in beam.parameters())
        factors = (3 * tangential / cos / limit, 3 * sagittal / limit)
        first, second = (max(-1.0, min(1.0, k * f)) for k, f in zip(proposed, factors))
        coordinates.extend((first, second))
        beam = beam.power((2 * first / factors[0] / cos, 2 * second / factors[1] * cos))
    return coordinates
