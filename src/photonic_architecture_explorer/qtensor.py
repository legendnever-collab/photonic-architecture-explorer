"""P3 stage 2: general astigmatic Gaussian beams (2×2 complex q-tensor) on two-reflector paths.

The separable engine needs both Ports in one fold plane with aligned axes. When the Ports are not
coplanar (or their axes are rolled), the two incidence planes differ and the beam axes rotate between
reflections, so the beam is described by a complex symmetric 2×2 matrix instead of two scalars.

Field on a transverse plane with orthonormal basis A = [t s] (3×2 columns):

    E(x) ∝ exp(-i k/2 · xᵀ Q x),   k = 2π n / λ,   Q complex symmetric, physical lengths.

For a separable beam Q = diag(1/q_t, 1/q_s), the engine's convention.

    free space   Q → Q (I + L Q)⁻¹
    reflector    Q → Q − 2 cosθ · M⁻ᵀ K M⁻¹,   M = Aᵀ E,   A → (I − 2 n nᵀ) A

E = [e1 e2] is the reflector's tangent basis and K its curvature tensor (positive = concave; sag
h = ½ ξᵀ K ξ along the normal, as in geometry.patch_intersections); cosθ = −d·n. For coplanar,
aligned axes this is exactly the engine's power pair (2κ_t / cosθ, 2κ_s cosθ).

Exact relay. Only the real part of Q changes at a reflector, so M1 fixes the beam width just after it
and may choose its curvature R freely; M2 then needs the beam to arrive with the width that the Target
requires. With W the intensity second-moment matrix, free propagation over b gives

    W(b) = (I + bR) W₀ (I + bR) + b² W₀⁻¹ / (4k²)

so (I + bR) = W₀^-½ Y W₀^-½ with Y² = W₀^½ (W_req − b² W₀⁻¹/(4k²)) W₀^½: up to four real symmetric
solutions (signs of the two square roots), the tensor form of the engine's two branches per axis.
K1 and K2 then follow from the jumps in Q at each reflector.

Verification is independent of this algebra: a 4×4 ray-transfer matrix is built by central
differences of exact rays through the quadric patches, and the generalized ABCD law
Q_out = (C + D Q)(A + B Q)⁻¹ must reproduce the arrived Q-tensor.
"""

import math
from dataclasses import dataclass, replace

import numpy as np

from .gaussian import DomainError
from .geometry import Reflector, add, cross, dot, frame, mul, norm, patch_intersections, reflect, sub, unit
from .placement import ROTATION_RAD, TRANSLATION_M
from .solver import MAX_DIVERGENCE, MAX_FOOTPRINT_SLOPE, MIN_COSINE

MODEL_SCOPE = 'general astigmatic scalar paraxial Gaussian (2×2 complex q-tensor), two reflectors'
RAY_STEP_M = 1e-7       # central-difference step for ray positions
RAY_STEP_RAD = 1e-6     # central-difference step for ray slopes
CHECK_TOLERANCE = 1e-6  # ray-transfer vs closed-form agreement required to accept a candidate
EDGE_DIRECTIONS = 8     # beam-edge directions around the chief ray for the clearance screen


@dataclass(frozen=True)
class TensorReflector(Reflector):
    """Quadric patch with its own principal axes: e1 = axis × normal, e2 = axis."""
    axis: tuple = (0.0, 1.0, 0.0)

    def __post_init__(self):
        super().__post_init__()
        axis = unit(self.axis)
        if abs(dot(axis, self.normal)) > 1e-9:
            raise DomainError('reflector axis must lie in its tangent plane')
        object.__setattr__(self, 'axis', axis)

    @property
    def first_axis(self):
        return unit(cross(self.axis, self.normal))

    @property
    def basis(self):
        return np.array([self.first_axis, self.axis]).T


# ---------- beam algebra ----------

def _sym(m):
    return (m + m.T) / 2


def _det(m):
    return m[0, 0] * m[1, 1] - m[0, 1] * m[1, 0]


def _inv(m):
    """Explicit 2×2 inverse (numpy.linalg overhead dominates for these tiny matrices)."""
    det = _det(m)
    if det == 0 or not np.isfinite(det):
        raise DomainError('singular 2×2 matrix')
    return np.array([[m[1, 1], -m[0, 1]], [-m[1, 0], m[0, 0]]]) / det


def _eig_max(m):
    half = (m[0, 0] + m[1, 1]) / 2
    return half + math.sqrt(max(0.0, (half - m[1, 1]) ** 2 + m[0, 1] * m[1, 0]))


def transverse_basis(direction, sagittal):
    t, s, _ = frame(direction, sagittal)
    return np.array([t, s]).T


def port_beam(port):
    return np.diag([1 / port.mode.q_t, 1 / port.mode.q_s]).astype(complex), transverse_basis(port.direction, port.sagittal)


def wavenumber(port):
    return 2 * math.pi * port.mode.index / port.mode.wavelength


def propagate(q, length):
    return _sym(q @ _inv(np.eye(2) + length * q))


def intensity(q, k):
    """Π with |E|² ∝ exp(−xᵀ Π x); positive definite for a physical beam."""
    return _sym(-k * q.imag)


def physical(q, k):
    p = -k * q.imag
    return bool(p[0, 0] > 0 and p[0, 0] * p[1, 1] - p[0, 1] * p[1, 0] > 0)


def extents(q, k):
    """Projected 1/e² half-widths along the two basis axes (= the radii for a separable beam)."""
    w = _inv(intensity(q, k))
    return math.sqrt(2 * w[0, 0]), math.sqrt(2 * w[1, 1])


def ellipse(q, k):
    """1/e² intensity semi-axes (major, minor) and the major axis angle from the first basis axis."""
    values, vectors = np.linalg.eigh(intensity(q, k))
    major = vectors[:, 0]
    return math.sqrt(2 / values[0]), math.sqrt(2 / values[1]), math.atan2(major[1], major[0])


def divergence(q, k):
    """Largest 1/e² half-angle: 2√λmax of the (propagation-invariant) angular second moment."""
    p = intensity(q, k)
    w = _inv(p) / 2
    r = q.real
    t = _sym(r @ w @ r + p / (2 * k * k))
    return 2 * math.sqrt(_eig_max(t))


def reflect_beam(q, basis, direction, mirror):
    n = np.array(mirror.normal)
    m = basis.T @ mirror.basis
    cosine = -float(direction @ n)
    if cosine <= 1e-12:
        raise DomainError('reflector is grazing or back-facing')
    inverse = _inv(m)
    out = _sym(q - 2 * cosine * inverse.T @ np.diag(mirror.curvatures) @ inverse)
    h = np.eye(3) - 2 * np.outer(n, n)
    return out, h @ basis, h @ direction


def footprint(q, basis, mirror, k):
    """Projected 1/e² half-widths of the incident beam on the reflector along its principal axes."""
    m = basis.T @ mirror.basis
    return extents(_sym(m.T @ q @ m), k)


def log_overlap(q_incident, q_target, k, offset=(0.0, 0.0), slope=(0.0, 0.0)):
    """ln of the normalized scalar overlap on one plane; offset/slope of the incident beam (target basis)."""
    ai, at = 0.5j * k * q_incident, 0.5j * k * q_target
    s = ai + at.conj()
    d, theta = np.array(offset, float), np.array(slope, float)
    j = 2 * ai @ d - 1j * k * theta
    value = (0.5 * (math.log(_det(2 * ai.real)) + math.log(_det(2 * at.real)))
             - math.log(abs(_det(s))) + 2 * (j @ _inv(s) @ j / 4 - d @ ai @ d).real)
    if not math.isfinite(value) or value > 1e-9:
        raise DomainError('overlap normalization or numerical range failure')
    return min(0.0, value)


# ---------- exact relay ----------

def width_matching_curvatures(q_start, length, required, k):
    """Real symmetric R with Im[propagate(R + i Im q_start, length)] = required, as (signs, R) pairs."""
    w0 = np.linalg.inv(intensity(q_start, k)) / 2
    p_req = -k * required
    if not np.all(np.linalg.eigvalsh(_sym(p_req)) > 0):
        return []
    w_req = np.linalg.inv(_sym(p_req)) / 2
    values, vectors = np.linalg.eigh(w0)
    half = vectors @ np.diag(np.sqrt(values)) @ vectors.T
    half_inv = vectors @ np.diag(1 / np.sqrt(values)) @ vectors.T
    d = _sym(half @ (w_req - length * length * np.linalg.inv(w0) / (4 * k * k)) @ half)
    dv, dvec = np.linalg.eigh(d)
    scale = max(abs(dv).max(), 1e-300)
    if dv.min() < -1e-12 * scale:
        return []
    roots = np.sqrt(np.clip(dv, 0.0, None))
    found = []
    for signs in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        if any(sg < 0 and r <= 1e-12 * math.sqrt(scale) for sg, r in zip(signs, roots)):
            continue  # a zero root gives no second branch
        y = dvec @ np.diag(np.array(signs) * roots) @ dvec.T
        found.append((signs, _sym((half_inv @ y @ half_inv - np.eye(2)) / length)))
    return found


def _tangent_basis(normal, hint):
    n = np.array(normal)
    e2 = np.cross(n, hint)
    if np.linalg.norm(e2) < 1e-6:
        e2 = np.cross(n, [1.0, 0.0, 0.0] if abs(n[0]) < 0.9 else [0.0, 1.0, 0.0])
    e2 /= np.linalg.norm(e2)
    return np.array([np.cross(e2, n), e2]).T


def principal(vertex, normal, basis, tensor, aperture=(1.0, 1.0)):
    values, vectors = np.linalg.eigh(_sym(tensor))
    axis = tuple(float(x) for x in basis @ vectors[:, 1])
    return TensorReflector(vertex, normal, (float(values[0]), float(values[1])), aperture, axis)


def _frames(ports, geometry):
    """Tangent bases of both reflectors and the beam bases between them, for one fold geometry."""
    _, normals, _, _ = geometry
    q_source, a0 = port_beam(ports.source)
    d0 = np.array(ports.source.direction)
    e1 = _tangent_basis(normals[0], d0)
    h1 = np.eye(3) - 2 * np.outer(normals[0], normals[0])
    a1, d1 = h1 @ a0, h1 @ d0
    e2 = _tangent_basis(normals[1], d1)
    h2 = np.eye(3) - 2 * np.outer(normals[1], normals[1])
    return {'q_source': q_source, 'a0': a0, 'e1': e1, 'a1': a1, 'e2': e2, 'a2': h2 @ a1}


def relay_solutions(ports, geometry, k):
    """All exact-q curvature tensor pairs for one fold geometry: [(branch, (M1, M2))] with unit apertures."""
    vertices, normals, lengths, cosines = geometry
    a, b, c = lengths
    f = _frames(ports, geometry)
    q_target, at = port_beam(ports.target)
    q_m1 = propagate(f['q_source'], a)
    m1, m2 = f['a0'].T @ f['e1'], f['a1'].T @ f['e2']
    u = f['a2'].T @ at
    q_after_m2 = _sym(u @ propagate(q_target, -c) @ u.T)
    found = []
    for signs, r in width_matching_curvatures(q_m1, b, q_after_m2.imag, k):
        q_after_m1 = r + 1j * q_m1.imag
        k1 = m1.T @ (q_m1 - q_after_m1) @ m1 / (2 * cosines[0])
        k2 = m2.T @ (propagate(q_after_m1, b) - q_after_m2) @ m2 / (2 * cosines[1])
        size = max(abs(k1).max(), abs(k2).max(), 1.0)
        if max(abs(k1.imag).max(), abs(k2.imag).max()) > 1e-6 * size:
            continue
        branch = tuple(0 if s > 0 else 1 for s in signs)
        found.append((branch, (principal(vertices[0], normals[0], f['e1'], k1.real),
                               principal(vertices[1], normals[1], f['e2'], k2.real))))
    return found


def near_match_mirrors(ports, geometry, k, seeds=()):
    """Maximise the overlap inside the guards (q-tensor counterpart of search.near_match_curvatures).

    Each reflector has a principal-axis angle φ and two coordinates u, v in [-1, 1]; the principal
    curvatures are u, v times 0.15 / (3 · projected footprint along that axis), so the 3w·|κ| guard holds
    by construction. Divergence above 0.1 rad is penalised. Seeds: the given exact solutions clipped
    to the guard, and flat reflectors. Returns (M1, M2) or None.
    """
    from scipy.optimize import minimize
    vertices, normals, lengths, _ = geometry
    f = _frames(ports, geometry)
    limit = MAX_FOOTPRINT_SLOPE * (1 - 1e-9)
    q_target, _ = port_beam(ports.target)

    a_target = port_beam(ports.target)[1]

    def run(x, keep=False):
        """One pass: build both reflectors from x, return (-log η + divergence penalty, mirrors)."""
        q, basis, direction = propagate(f['q_source'], lengths[0]), f['a0'], np.array(ports.source.direction)
        mirrors, worst = [], 0.0
        for j, frame_basis in enumerate((f['e1'], f['e2'])):
            phi, u, v = x[3 * j:3 * j + 3]
            cs, sn = math.cos(phi), math.sin(phi)
            axes = frame_basis @ np.array([[cs, -sn], [sn, cs]])
            m = basis.T @ axes
            fp = extents(_sym(m.T @ q @ m), k)
            kappas = (u * limit / (3 * fp[0]), v * limit / (3 * fp[1]))
            if keep:
                mirrors.append(TensorReflector(vertices[j], normals[j], kappas, (1.0, 1.0), tuple(axes[:, 1])))
            inverse = _inv(m)
            cosine = -float(direction @ normals[j])
            q = _sym(q - 2 * cosine * inverse.T @ np.diag(kappas) @ inverse)
            h = np.eye(3) - 2 * np.outer(normals[j], normals[j])
            basis, direction = h @ basis, h @ direction
            if not physical(q, k):
                raise DomainError('invalid paraxial transformation')
            worst = max(worst, divergence(q, k))
            q = propagate(q, lengths[j + 1])
            if not physical(q, k):
                raise DomainError('invalid paraxial transformation')
        u_t = basis.T @ a_target
        arrival = _sym(u_t.T @ q @ u_t)
        return -log_overlap(arrival, q_target, k) + 1e3 * max(0.0, worst - MAX_DIVERGENCE), mirrors

    def build(x):
        return run(x, keep=True)[1]

    def cost(x):
        try:
            return run(x)[0]
        except (DomainError, np.linalg.LinAlgError, ValueError, ArithmeticError):
            return 1e6

    starts = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
    for mirrors in seeds:
        try:
            x, q, basis, direction = [], propagate(f['q_source'], lengths[0]), f['a0'], np.array(ports.source.direction)
            for j, (mirror, frame_basis) in enumerate(zip(mirrors, (f['e1'], f['e2']))):
                local = frame_basis.T @ np.array([mirror.first_axis, mirror.axis]).T
                phi = math.atan2(local[1, 0], local[0, 0])
                fp = footprint(q, basis, mirror, k)
                x += [phi, *(max(-1.0, min(1.0, kappa * 3 * w / limit)) for kappa, w in zip(mirror.curvatures, fp))]
                q, basis, direction = reflect_beam(q, basis, direction, mirror)
                q = propagate(q, lengths[1])
            starts.append(x)
        except (DomainError, np.linalg.LinAlgError, ValueError):
            continue
    bounds = [(-2 * math.pi, 2 * math.pi), (-1, 1), (-1, 1)] * 2
    best = None
    for start in starts:
        found = minimize(cost, start, method='L-BFGS-B', bounds=bounds, options={'maxiter': 120})
        if best is None or found.fun < best.fun:
            best = found
    if best is None or best.fun >= 1e5:
        return None
    return tuple(build(best.x))


def chain(ports, mirrors, lengths, k):
    """Forward q-tensor run; arrival in the Target basis plus the screening quantities."""
    q, basis = port_beam(ports.source)
    direction = np.array(ports.source.direction)
    segments, footprints, slopes, divergences = [], [], [], []
    for j, mirror in enumerate(mirrors):
        segments.append((q, basis, direction))
        q = propagate(q, lengths[j])
        if not physical(q, k):
            raise DomainError('invalid paraxial transformation')
        fp = footprint(q, basis, mirror, k)
        q, basis, direction = reflect_beam(q, basis, direction, mirror)
        if not physical(q, k):
            raise DomainError('invalid paraxial transformation')
        footprints.append(fp)
        slopes.append(max(3 * f * abs(kappa) for f, kappa in zip(fp, mirror.curvatures)))
        divergences.append(divergence(q, k))
    segments.append((q, basis, direction))
    q = propagate(q, lengths[2])
    _, at = port_beam(ports.target)
    if np.linalg.norm(direction - np.array(ports.target.direction)) > 1e-9:
        raise DomainError('relay does not arrive along the Target direction')
    u = basis.T @ at
    arrival = _sym(u.T @ q @ u)
    q_target, _ = port_beam(ports.target)
    return {'arrival': arrival, 'segments': segments, 'footprints': footprints, 'slope': max(slopes),
            'divergence': max(divergences), 'log_eta': log_overlap(arrival, q_target, k)}


# ---------- screening (same contract as search.evaluate_point) ----------

def with_apertures(mirrors, footprints, factor):
    return [replace(m, half_aperture=(factor * f[0], factor * f[1])) for m, f in zip(mirrors, footprints)]


def obstruction(ports, vertices, lengths, mirrors, run, k):
    """Engine chief-ray rule on margin-grown patches, plus the beam edge clearing the other reflector."""
    from .search import APERTURE_FACTOR, CLEARANCE_SAMPLES, CLEARANCE_TAIL_FACTOR, POSE_PATCH_MARGIN
    points = [ports.source.position, *vertices, ports.target.position]
    grown = [replace(m, half_aperture=tuple(x * (1 + POSE_PATCH_MARGIN[1]) + POSE_PATCH_MARGIN[0] for x in m.half_aperture))
             for m in mirrors]
    for (start, end), length in zip(zip(points, points[1:]), lengths):
        direction = unit(sub(end, start))
        for mirror in grown:
            if any(1e-10 < x < length - 1e-10 for x in patch_intersections(start, direction, mirror, mirror.axis)):
                return 'unintended reflector interception'
    shrink = CLEARANCE_TAIL_FACTOR / APERTURE_FACTOR
    lit = [replace(m, half_aperture=tuple(a * shrink for a in m.half_aperture)) for m in mirrors]
    for j, other in ((0, lit[1]), (2, lit[0])):
        q0, basis, direction = run['segments'][j]
        start = points[j]
        z = [lengths[j] * i / CLEARANCE_SAMPLES for i in range(CLEARANCE_SAMPLES + 1)]
        widths = [intensity(propagate(q0, zi), k) for zi in z]
        for e in range(EDGE_DIRECTIONS):
            phi = 2 * math.pi * e / EDGE_DIRECTIONS
            local = np.array([math.cos(phi), math.sin(phi)])
            offset = tuple(basis @ local)
            edge = [add(add(start, mul(tuple(direction), zi)), mul(offset, CLEARANCE_TAIL_FACTOR * math.sqrt(2 / (local @ p @ local))))
                    for zi, p in zip(z, widths)]
            for p0, p1 in zip(edge, edge[1:]):
                span = norm(sub(p1, p0))
                if any(1e-10 < x < span for x in patch_intersections(p0, unit(sub(p1, p0)), other, other.axis)):
                    return 'beam clips another reflector'
    return None


def near_match_point(ports, constraints, seed, lam_n):
    """Best guard-respecting overlap at the seed's (a, c), screened like an exact point.

    Returns (Point or None, optimised). The seed's exact-solution reflectors already have nearly the
    Near-match apertures (same incident beam on M1), so a seed whose patches violate a space constraint
    is skipped without optimising; the optimised result is still screened in full.
    """
    from .search import constraint_violation, fold
    if seed.prescription is not None:
        vertices, _, _, mirrors = seed.prescription
        if constraint_violation(ports, constraints, vertices, mirrors):
            return None, False
    try:
        geometry = fold(ports, seed.a, seed.c)
        seeds = [seed.prescription[3]] if seed.prescription is not None else []
        mirrors = near_match_mirrors(ports, geometry, 2 / lam_n, seeds)
    except (DomainError, np.linalg.LinAlgError, ArithmeticError, ValueError):
        return None, True
    if mirrors is None:
        return None, True
    return evaluate_point(ports, constraints, seed.a, seed.c, lam_n, kappas=mirrors)[0], True


def evaluate_point(ports, constraints, a, c, lam_n, *, branch=None, kappas=None):
    """q-tensor counterpart of search.evaluate_point; `kappas` = a given (M1, M2) pair (Near-match)."""
    from .search import APERTURE_FACTOR, Point, constraint_violation, fold, prescreen
    try:
        geometry = fold(ports, a, c)
    except (DomainError, ZeroDivisionError, ValueError, ArithmeticError):
        return [Point(a, c, 'geometry', 'zero/short middle segment')]
    rejected = prescreen(ports, constraints, a, c, geometry)
    if rejected:
        return [rejected]
    vertices, normals, lengths, cosines = geometry
    k = 2 / lam_n
    if kappas is not None:
        solutions = [(('NM', 'NM'), tuple(kappas))]
    else:
        try:
            solutions = relay_solutions(ports, geometry, k)
        except (DomainError, np.linalg.LinAlgError, ArithmeticError, ValueError):
            return [Point(a, c, 'power', 'nonfinite power solution')]
        if not solutions:
            return [Point(a, c, 'power', 'no real exact-q curvature tensor')]
    points = []
    for key, mirrors in solutions:
        if branch is not None and tuple(key) != tuple(branch):
            continue
        try:
            run = chain(ports, mirrors, lengths, k)
        except (DomainError, np.linalg.LinAlgError, ArithmeticError, ValueError):
            points.append(Point(a, c, 'domain', 'invalid paraxial transformation', key))
            continue
        mirrors = with_apertures(mirrors, run['footprints'], APERTURE_FACTOR)
        metrics = {
            'total_path_m': sum(lengths), 'max_footprint_slope': run['slope'], 'max_divergence_rad': run['divergence'],
            'max_footprint_radius_m': max(max(f) for f in run['footprints']),
            'max_abs_curvature_per_m': max(abs(x) for m in mirrors for x in m.curvatures),
            'incidence_deg': [math.degrees(math.acos(min(1.0, x))) for x in cosines],
            'normalized_mode_overlap': math.exp(run['log_eta']),
            'a_m': a, 'b_m': lengths[1], 'c_m': c,
        }
        point = Point(a, c, 'ok', '', key, metrics, (vertices, normals, lengths, tuple(mirrors)))
        if run['slope'] > MAX_FOOTPRINT_SLOPE:
            point.status, point.reason = 'domain', '3w projected footprint/curvature exceeds 0.15'
        elif run['divergence'] > MAX_DIVERGENCE:
            point.status, point.reason = 'domain', 'Gaussian divergence exceeds 0.1 rad'
        else:
            blocked = obstruction(ports, vertices, lengths, mirrors, run, k)
            if blocked:
                point.status, point.reason = 'geometry', blocked
            else:
                violation = constraint_violation(ports, constraints, vertices, mirrors)
                if violation:
                    point.status, point.reason = 'constraint', violation
        points.append(point)
    return points


# ---------- independent ray check, pose study, scene ----------

def local_normal(mirror, point):
    e1 = mirror.first_axis
    rel = sub(point, mirror.vertex)
    u, v = dot(rel, e1), dot(rel, mirror.axis)
    k1, k2 = mirror.curvatures
    return unit(sub(sub(mirror.normal, mul(e1, k1 * u)), mul(mirror.axis, k2 * v)))


def trace_ray(origin, direction, mirrors, target):
    """Exact ray through the clipped quadric patches to the Target plane: offset and slope in the Target basis."""
    origin, direction = tuple(origin), unit(direction)
    incidence = []
    for index, mirror in enumerate(mirrors):
        roots = [r for r in patch_intersections(origin, direction, mirror, mirror.axis) if r > 1e-9]
        if not roots:
            raise DomainError(f'M{index + 1}: ray misses the aperture')
        distance = min(roots)
        other = mirrors[1 - index]
        if any(1e-9 < r < distance - 1e-9 for r in patch_intersections(origin, direction, other, other.axis)):
            raise DomainError('unintended reflector interception')
        hit = add(origin, mul(direction, distance))
        normal = local_normal(mirror, hit)
        cosine = -dot(direction, normal)
        if cosine < MIN_COSINE:
            raise DomainError(f'M{index + 1}: local incidence exceeds 70 degrees')
        incidence.append(math.degrees(math.acos(min(1.0, cosine))))
        origin, direction = hit, reflect(direction, normal)
    den = dot(direction, target.direction)
    if den <= 0:
        raise DomainError('ray does not propagate toward the Target plane')
    distance = dot(sub(target.position, origin), target.direction) / den
    if distance <= 1e-9:
        raise DomainError('Target plane is not forward')
    point = add(origin, mul(direction, distance))
    basis = transverse_basis(target.direction, target.sagittal)
    offset = basis.T @ np.array(sub(point, target.position))
    slope = basis.T @ np.array(direction) / den
    return {'offset': offset, 'slope': slope, 'incidence_deg': incidence}


def ray_transfer(ports, mirrors):
    """4×4 ray-transfer matrix (x_t, x_s, θ_t, θ_s), Source basis → Target basis, by central differences."""
    source = ports.source
    basis = transverse_basis(source.direction, source.sagittal)
    d0 = np.array(source.direction)
    columns = []
    for i in range(4):
        values = []
        for sign in (1, -1):
            position, direction = np.array(source.position, float), d0.copy()
            if i < 2:
                position = position + sign * RAY_STEP_M * basis[:, i]
            else:
                direction = direction + sign * RAY_STEP_RAD * basis[:, i - 2]
            ray = trace_ray(tuple(position), tuple(direction), mirrors, ports.target)
            values.append(np.concatenate([ray['offset'], ray['slope']]))
        columns.append((values[0] - values[1]) / (2 * (RAY_STEP_M if i < 2 else RAY_STEP_RAD)))
    return np.array(columns).T


def symplectic_error(matrix, length):
    """max |TᵀJT − J| after scaling positions by `length` so that all four blocks are dimensionless."""
    scale = np.diag([length, length, 1.0, 1.0])
    t = np.linalg.inv(scale) @ matrix @ scale
    j = np.block([[np.zeros((2, 2)), np.eye(2)], [-np.eye(2), np.zeros((2, 2))]])
    return float(abs(t.T @ j @ t - j).max())


def rotate(vector, axis, angle):
    v, e = np.array(vector), np.array(axis)
    return tuple(v * math.cos(angle) + np.cross(e, v) * math.sin(angle) + e * (e @ v) * (1 - math.cos(angle)))


def poses(mirrors):
    """±5 µm along X, Y, Z and ±1 mrad about both principal axes, one reflector at a time."""
    for index, mirror in enumerate(mirrors):
        for axis in range(3):
            for delta in (-TRANSLATION_M, TRANSLATION_M):
                vertex = list(mirror.vertex)
                vertex[axis] += delta
                changed = list(mirrors)
                changed[index] = replace(mirror, vertex=tuple(vertex))
                yield changed
        for pivot in (mirror.first_axis, mirror.axis):
            for angle in (-ROTATION_RAD, ROTATION_RAD):
                changed = list(mirrors)
                changed[index] = replace(mirror, normal=rotate(mirror.normal, pivot, angle),
                                         axis=rotate(mirror.axis, pivot, angle))
                yield changed


def pose_tolerance(ports, mirrors, arrival, k):
    q_target, _ = port_beam(ports.target)
    nominal = log_overlap(arrival, q_target, k)
    worst = 0.0
    for changed in poses(mirrors):
        try:
            ray = trace_ray(ports.source.position, ports.source.direction, changed, ports.target)
            log_eta = log_overlap(arrival, q_target, k, ray['offset'], ray['slope'])
        except (DomainError, np.linalg.LinAlgError):
            return None
        worst = max(worst, -10 * (log_eta - nominal) / math.log(10))
    return worst


def _mm(p):
    return [float(v) * 1e3 for v in p]


def tensor_scene(ports, mirrors, lengths, run, k):
    from .scene import BEAM_SAMPLES_PER_SEGMENT, _surface_grid
    points = [ports.source.position, *(m.vertex for m in mirrors), ports.target.position]
    samples, segments, travelled = [], [], 0.0
    for j, (start, end, length) in enumerate(zip(points, points[1:], lengths)):
        q0, basis, direction = run['segments'][j]
        segments.append({'start_mm': _mm(start), 'end_mm': _mm(end), 'length_mm': length * 1e3,
                         'direction': [float(x) for x in direction], 't_axis': [float(x) for x in basis[:, 0]],
                         's_axis': [float(x) for x in basis[:, 1]]})
        for i in range(BEAM_SAMPLES_PER_SEGMENT + 1):
            z = length * i / BEAM_SAMPLES_PER_SEGMENT
            q = propagate(q0, z)
            et, es = extents(q, k)
            major, minor, angle = ellipse(q, k)
            samples.append({'segment': j, 'distance_mm': (travelled + z) * 1e3,
                            'point_mm': _mm(add(start, mul(tuple(direction), z))),
                            'radius_t_um': et * 1e6, 'radius_s_um': es * 1e6,
                            'ellipse': {'major_um': major * 1e6, 'minor_um': minor * 1e6, 'angle_rad': angle}})
        travelled += length
    records = []
    for j, mirror in enumerate(mirrors):
        incoming = unit(sub(mirror.vertex, points[j]))
        cosine = -dot(incoming, mirror.normal)
        records.append({
            'id': f'M{j + 1}', 'vertex_mm': _mm(mirror.vertex), 'normal': list(mirror.normal),
            't_axis': list(mirror.first_axis), 's_axis': list(mirror.axis),
            'curvature_ts_per_m': list(mirror.curvatures),
            'radius_of_curvature_ts_mm': [None if abs(x) < 1e-12 else 1e3 / x for x in mirror.curvatures],
            'half_aperture_ts_mm': [x * 1e3 for x in mirror.half_aperture],
            'incidence_deg': math.degrees(math.acos(min(1.0, cosine))),
            'beam_footprint_radius_ts_um': [f * 1e6 for f in run['footprints'][j]],
            'principal_axes': 'reflector principal curvature axes (t = s × normal), not the Port axes',
            'surface_grid_mm': _surface_grid(mirror, mirror.axis),
        })
    return {'mirrors': records,
            'path': {'points_mm': [_mm(p) for p in points], 'segments': segments, 'total_length_mm': sum(lengths) * 1e3},
            'beam': {'definition': ('1/e² intensity of a general astigmatic beam along the chief ray; radius_t/s are '
                                    'projected half-widths along the segment axes, ellipse gives the true semi-axes'),
                     'model': 'qtensor', 'samples': samples}}


def verify(document, ports, point, role, family):
    """Accept a q-tensor candidate only if an exact-surface ray-transfer matrix reproduces it."""
    from .search import LIMITS, OBJECTIVES
    vertices, normals, lengths, mirrors = point.prescription
    k = wavenumber(ports.source)
    identifier = f"P3-T{'E' if family == 'exact' else 'N'}-a{point.a * 1e3:.4f}-c{point.c * 1e3:.4f}-{''.join(map(str, point.branch))}"
    try:
        run = chain(ports, mirrors, lengths, k)
        nominal = trace_ray(ports.source.position, ports.source.direction, mirrors, ports.target)
        matrix = ray_transfer(ports, mirrors)
    except (DomainError, np.linalg.LinAlgError) as exc:
        return {'status': 'Rejected', 'reason': f'ray check: {exc}'}
    q_source, _ = port_beam(ports.source)
    q_target, _ = port_beam(ports.target)
    a_, b_, c_, d_ = matrix[:2, :2], matrix[:2, 2:], matrix[2:, :2], matrix[2:, 2:]
    q_ray = _sym((c_ + d_ @ q_source) @ np.linalg.inv(a_ + b_ @ q_source))
    symplectic = symplectic_error(matrix, sum(lengths))
    difference = float(np.linalg.norm(q_ray - run['arrival']) / np.linalg.norm(run['arrival']))
    try:
        log_ray = log_overlap(q_ray, q_target, k)
    except DomainError as exc:
        return {'status': 'Rejected', 'reason': f'ray check: {exc}'}
    closure = max(abs(nominal['offset']).max(), abs(nominal['slope']).max())
    failures = []
    if closure > 1e-9:
        failures.append(f'chief ray misses the Target by {closure:.2e}')
    if difference > CHECK_TOLERANCE or symplectic > CHECK_TOLERANCE:
        failures.append(f'ray-transfer check differs by {difference:.2e} (symplectic error {symplectic:.2e})')
    if abs(log_ray - run['log_eta']) > CHECK_TOLERANCE:
        failures.append('ray-transfer overlap differs')
    if run['slope'] > MAX_FOOTPRINT_SLOPE or run['divergence'] > MAX_DIVERGENCE:
        failures.append('model guard exceeded')
    if failures:
        return {'status': 'Rejected', 'reason': 'ray check: ' + '; '.join(failures)}
    eta = math.exp(log_ray)
    evaluation = {
        'input_contract': {'status': 'Pass', 'scope': 'explicit two-Port subset of M3A contract'},
        'geometry': {'status': 'Pass', 'lengths': list(lengths), 'local_incidence_deg': nominal['incidence_deg']},
        'model_domain': {'status': 'Pass', 'scope': MODEL_SCOPE,
                         'max_3w_footprint_curvature': run['slope'], 'max_divergence_rad': run['divergence']},
        'gaussian_mode_matching': {'status': 'Pass', 'normalized_mode_overlap': eta,
                                   'mismatch_db': -10 * log_ray / math.log(10), 'meaning': 'Scalar paraxial overlap, not Total Coupling'},
        'ray_transfer_check': {'status': 'Pass', 'method': ('4×4 ray-transfer matrix from exact rays through the quadric '
                                                            'patches (central differences 0.1 µm / 1 µrad); Q = (C + DQ)(A + BQ)⁻¹'),
                               'q_tensor_relative_difference': difference, 'symplectic_error': symplectic,
                               'log_overlap_difference': abs(log_ray - run['log_eta'])},
    }
    ranking = {'overlap_deficit_at_1e-12': round(1 - eta, 12), 'total_path_m': sum(lengths),
               'max_projected_radius_m': max(max(f) for f in run['footprints']),
               'max_3w_footprint_curvature': run['slope'],
               'max_abs_curvature_per_m': max(abs(x) for m in mirrors for x in m.curvatures), 'stable_id': identifier}
    prescription = {'model': 'qtensor', 'lengths_m': list(lengths), 'reflectors': [
        {'vertex_m': list(m.vertex), 'normal': list(m.normal), 'principal_axes': [list(m.first_axis), list(m.axis)],
         'curvatures_per_m': list(m.curvatures), 'half_aperture_m': list(m.half_aperture)} for m in mirrors]}
    return {'status': 'Accepted', 'id': identifier, 'geometry_id': identifier.rsplit('-', 1)[0], 'family': family,
            'model': 'qtensor', 'classification': 'Conceptual Geometry', 'recommendation_role': role, 'roles': [role],
            'objective_label': OBJECTIVES[role][2],
            'parameters': {'a_m': point.a, 'b_m': lengths[1], 'c_m': point.c, 'branch': list(point.branch)},
            'prescription': prescription, 'evaluation': evaluation, 'ranking': ranking,
            'scene': tensor_scene(ports, mirrors, lengths, run, k),
            'worst_pose_mismatch_db': pose_tolerance(ports, mirrors, run['arrival'], k),
            'advantages': ['Fixed Port closure and frozen domain guards passed',
                           'Checked against an exact-surface ray-transfer matrix (independent of the q-tensor algebra)'],
            'limitations': LIMITS + ['Non-coplanar path: general astigmatic q-tensor model; the separable engine does not apply']}
