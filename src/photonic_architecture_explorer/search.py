"""Continuous two-reflector candidate generator (policy P3-CONTINUOUS-2).

P3-CONTINUOUS-2 = P2-CONTINUOUS-1 plus the glass region constraint, beam clearance, obstruction and
incidence margins for the pose study, and extra near-match trials.

Two fixed coplanar Ports leave exactly two free lengths for a two-reflector relay:
a (Source → M1 along the Source axis) and c (M2 → Target, back along the Target axis).
Everything else (middle segment, fold normals, incidence) follows, and the exact-q
reflector powers per axis have at most two closed-form branches (`design.power_pairs`).
P2 therefore maps the whole (a, c) plane on a log grid instead of the frozen 8 × 8
family, refines representatives continuously, and, only when no exact candidate
exists, maximises overlap inside the frozen guards (Near-match).

Screening here uses closed-form q algebra. Every reported candidate is re-evaluated by
the unchanged external Adapter (`evaluate_external`), which alone decides acceptance.
Frozen guards are never relaxed; user constraints can only tighten them.
"""

from collections import Counter
from dataclasses import dataclass, field
import copy
import hashlib
import itertools
import json
import math
import time

from scipy.optimize import minimize

from .design import candidate_document, power_pairs
from .diagnostics import ray_to_target
from .external import InputIssue, adapt_external, adapt_ports, evaluate_external, fail
from .gaussian import DomainError, mode_overlap
from .geometry import Reflector, add, cross, dot, mul, norm, patch_intersections, sub, unit
from .package_geometry import box_distance, patch_world_aabb, segment_hits_box
from .placement import ROTATION_RAD, TRANSLATION_M, reflector_poses
from .solver import MAX_DIVERGENCE, MAX_FOOTPRINT_SLOPE, MIN_COSINE

APERTURE_FACTOR = 4.0  # same projected-radius factor as the M5-A prescription
POLICY = {
    'id': 'P3-CONTINUOUS-2',
    'free_parameters': 'a = |Source→M1|, c = |M2→Target| (two coplanar reflectors)',
    'grid_points_per_axis': 64,
    'length_range': 'log-spaced from 1 % to 400 % of the Port separation',
    'exact': 'closed-form two-power exact-q branches per axis, all four branch pairs',
    'refinement': 'Nelder-Mead on (ln a, ln c) per objective, branch pair fixed',
    'near_match': 'only if no exact candidate: per-axis bounded overlap maximisation inside the guards',
    'incidence_margin_deg': 1.0,
    'chief_ray_margin': 'prescribed patches grown by 10 µm + 2 % when screening chief-ray obstruction',
    'beam_clearance': ('fold-plane beam edges at 2.63 w (1e-6 power tail), 16 samples per segment, must miss the '
                       'illuminated 2.63 w region of the reflector the segment does not end on'),
    'near_match_geometries': ('the 64 grid points closest to the 3w|κ| guard plus up to 32 without a real exact branch; '
                              'if none of these is feasible, further guard-limited points up to 256 trials'),
    'acceptance': 'unchanged external Adapter evaluation (geometry, domain, interception, aperture tail)',
    'guards': 'frozen: divergence 0.1 rad, 3w|κ| 0.15, incidence 70°, aperture tail 1e-6',
    'aperture_projected_radius_factor': APERTURE_FACTOR,
    'alignment_tolerance': f'one-at-a-time ±{TRANSLATION_M * 1e6:g} µm / ±{ROTATION_RAD * 1e3:g} mrad reflector pose, '
                           'chief-ray miss and tilt applied to the arriving Gaussian at the Target',
}
OBJECTIVES = {
    'best_overlap': ('mismatch', 'min', '최대 Overlap'),
    'short_path': ('total_path_m', 'min', '최단 광경로'),
    'model_margin': ('max_footprint_slope', 'min', 'Guard 여유'),
    'small_beam': ('max_footprint_radius_m', 'min', '작은 Beam'),
    'gentle_curvature': ('max_abs_curvature_per_m', 'min', '완만한 곡률'),
    'robust_alignment': ('worst_pose_mismatch_db', 'min', '정렬 공차'),
    'pareto_alternative': (None, None, 'Pareto 대안'),
}
INCIDENCE_MARGIN_DEG = 1.0  # room for the ±5 µm / ±1 mrad pose study to stay inside the 70° guard
CLEARANCE_TAIL_FACTOR = math.sqrt(math.log(1e6) / 2)  # radius outside which a Gaussian carries < 1e-6 of its power (per axis)
CLEARANCE_SAMPLES = 16
POSE_PATCH_MARGIN = (10e-6, 0.02)  # m, fraction: chief-ray obstruction margin around each prescribed patch
NEAR_MATCH_FIRST_TRIALS = 96
NEAR_MATCH_MAX_TRIALS = 256
LIMITS = ['Conceptual Geometry; prescribed aperture is not fabrication capability',
          'Scalar paraxial normalized overlap is not Total Coupling',
          'Finite-field aberration, coating, interface and polarization losses Uncomputed',
          'Port bodies are modelled only as the half-spaces behind the reference planes (when enabled)',
          'Two coplanar reflectors in one homogeneous medium (ambient or one glass block); other families are later phases']


@dataclass(frozen=True)
class Constraints:
    """User constraints. They can only tighten the frozen guards."""
    port_halfspace: bool = True
    envelope: tuple | None = None          # ((min xyz), (max xyz)) m
    keepouts: tuple = ()                   # (((min), (max)), ...) m
    keepout_labels: tuple = ()
    clearance: float = 0.0                 # m, between reflector patches and keep-outs
    max_incidence_deg: float = 70.0
    min_radius_of_curvature: float | None = None  # m, |R| lower bound for curved axes
    block: object | None = None            # media.Block
    block_side: str = 'inside'             # reflectors must lie 'inside' or 'outside' the block

    @property
    def min_cosine(self):
        """Search limit: the tighter of the user and frozen limits, less a margin for the pose study."""
        limit = min(self.max_incidence_deg, 70.0) - INCIDENCE_MARGIN_DEG
        return max(MIN_COSINE, math.cos(math.radians(limit)))


@dataclass
class Point:
    a: float
    c: float
    status: str
    reason: str = ''
    branch: tuple | None = None
    metrics: dict = field(default_factory=dict)
    prescription: tuple | None = None  # (vertices, normals, lengths, curvatures)


# ---------- closed-form per-axis chain ----------

def axis_chain(q0, lengths, cosines, kappas, axis, lam_n):
    """Propagate one principal axis through both reflectors; None if q leaves the domain."""
    q = q0
    footprint, slope, divergence = [], [], []
    for j in (0, 1):
        q = q + lengths[j]
        inv = 1 / q
        if inv.imag >= 0:
            return None
        w = math.sqrt(-lam_n / inv.imag)
        fp = w / cosines[j] if axis == 0 else w
        k = kappas[j]
        power = 2 * k / cosines[j] if axis == 0 else 2 * k * cosines[j]
        den = 1 - power * q
        if abs(den) < 1e-14:
            return None
        q = q / den
        if not q.imag > 0:
            return None
        footprint.append(fp)
        slope.append(3 * fp * abs(k))
        divergence.append(lam_n / math.sqrt(lam_n * q.imag))
    return {'q': q + lengths[2], 'footprint': footprint, 'slope': slope, 'divergence': divergence}


def axis_log_eta(q, qt, lam_n):
    """1D normalized overlap on the Target plane, same algebra as gaussian.mode_overlap."""
    inv_i, inv_t = 1 / q, 1 / qt
    wi, wt = math.sqrt(-lam_n / inv_i.imag), math.sqrt(-lam_n / inv_t.imag)
    k = 2 / lam_n
    scale2 = wi * wt
    a = complex(wt / wi, k * inv_i.real * scale2 / 2) + complex(wi / wt, -k * inv_t.real * scale2 / 2)
    return math.log(2) - math.log(abs(a))


# ---------- geometry and constraints ----------

def fold(ports, a, c):
    source, target = ports.source, ports.target
    vertices = (add(source.position, mul(source.direction, a)), sub(target.position, mul(target.direction, c)))
    middle = sub(vertices[1], vertices[0])
    b = norm(middle)
    if b < 1e-9:
        raise DomainError('zero/short middle segment')
    direction = unit(middle)
    normals = (unit(sub(direction, source.direction)), unit(sub(target.direction, direction)))
    cosines = (-dot(source.direction, normals[0]), -dot(direction, normals[1]))
    return vertices, normals, (a, b, c), cosines


def patch_extent_along(mirror, sagittal, direction):
    """Exact min/max of (p - vertex)·direction over the rectangular quadratic patch."""
    tangent = unit(cross(sagittal, mirror.normal))
    lo = hi = 0.0
    for axis_vector, curvature, aperture in zip((tangent, sagittal), mirror.curvatures, mirror.half_aperture):
        linear = dot(axis_vector, direction)
        quadratic = dot(mirror.normal, direction) * curvature / 2
        samples = [linear * x + quadratic * x * x for x in (-aperture, aperture)]
        if quadratic != 0:
            x = -linear / (2 * quadratic)
            if -aperture <= x <= aperture:
                samples.append(linear * x + quadratic * x * x)
        lo += min(samples)
        hi += max(samples)
    return lo, hi


def block_violation(constraints, mirror, sagittal):
    block = constraints.block
    if block is None:
        return None
    lo, hi = patch_extent_along(mirror, sagittal, block.normal)
    height = -block.depth(mirror.vertex)  # signed height above the surface
    if constraints.block_side == 'inside':
        if height + hi > 0:
            return 'reflector crosses the block surface'
        if block.thickness is not None and height + lo < -block.thickness:
            return 'reflector leaves the block bottom'
    elif height + lo < 0:
        return 'reflector enters the block'
    return None


def constraint_violation(ports, constraints, vertices, mirrors):
    """First violated user/package constraint for a fully specified candidate, else None."""
    source, target, sagittal = ports.source, ports.target, ports.source.sagittal
    for mirror in mirrors:
        violation = block_violation(constraints, mirror, sagittal)
        if violation:
            return violation
        if constraints.min_radius_of_curvature:
            if any(abs(k) > 1 / constraints.min_radius_of_curvature for k in mirror.curvatures):
                return 'radius of curvature below the user minimum'
        if constraints.port_halfspace:
            lo, _ = patch_extent_along(mirror, sagittal, source.direction)
            if dot(sub(mirror.vertex, source.position), source.direction) + lo < 0:
                return 'reflector enters the Source body half-space'
            _, hi = patch_extent_along(mirror, sagittal, target.direction)
            if dot(sub(mirror.vertex, target.position), target.direction) + hi > 0:
                return 'reflector enters the Target body half-space'
        if constraints.envelope or constraints.keepouts:
            box = patch_world_aabb(mirror, sagittal)
            if constraints.envelope and not all(lo <= bl and bh <= hi for lo, hi, bl, bh in
                                                zip(*constraints.envelope, *box)):
                return 'reflector outside the package envelope'
            for keepout in constraints.keepouts:
                gap = box_distance(box, keepout)
                if gap <= 0 or gap < constraints.clearance:
                    return 'reflector inside a keep-out clearance'
    points = [source.position, *vertices, target.position]
    for start, end in zip(points, points[1:]):
        for keepout in constraints.keepouts:
            if segment_hits_box(start, end, keepout):
                return 'chief ray crosses a keep-out'
    if constraints.envelope:
        if not all(all(lo <= p <= hi for lo, p, hi in zip(constraints.envelope[0], point, constraints.envelope[1]))
                   for point in points):
            return 'chief path outside the package envelope'
    return None


def build(ports, geometry, kappas_t, kappas_s, chains):
    vertices, normals, lengths, cosines = geometry
    mirrors = []
    for j in (0, 1):
        aperture = (APERTURE_FACTOR * chains[0]['footprint'][j], APERTURE_FACTOR * chains[1]['footprint'][j])
        mirrors.append(Reflector(vertices[j], normals[j], (kappas_t[j], kappas_s[j]), aperture))
    return mirrors


def intercepted(ports, vertices, lengths, mirrors, chains, lam_n):
    """Reflector obstruction while screening.

    The chief-ray rule is the engine's (solver.evaluate), applied to patches grown by a pose margin so
    the ±5 µm / ±1 mrad pose study does not run into the same obstruction. In addition the beam itself must clear the
    reflector a segment does not end on: the fold-plane edges of the segment's t-axis beam, at the
    1e-6 power-tail radius and sampled along the segment, must miss that reflector's illuminated
    region (its own beam's 1e-6 tail radius, smaller than the prescribed 4w aperture).
    """
    points = [ports.source.position, *vertices, ports.target.position]
    sagittal = ports.source.sagittal
    grown = [Reflector(m.vertex, m.normal, m.curvatures,
                       tuple(a * (1 + POSE_PATCH_MARGIN[1]) + POSE_PATCH_MARGIN[0] for a in m.half_aperture)) for m in mirrors]
    for (start, end), length in zip(zip(points, points[1:]), lengths):
        direction = unit(sub(end, start))
        for mirror in grown:
            if any(1e-10 < x < length - 1e-10 for x in patch_intersections(start, direction, mirror, sagittal)):
                return 'unintended reflector interception'
    shrink = CLEARANCE_TAIL_FACTOR / APERTURE_FACTOR
    lit = [Reflector(m.vertex, m.normal, m.curvatures, tuple(a * shrink for a in m.half_aperture)) for m in mirrors]
    q_start = (ports.source.mode.q[0], chains[0]['q'] - lengths[2])  # t-axis q at the start of segments 0 and 2
    for j, other, q0 in ((0, lit[1], q_start[0]), (2, lit[0], q_start[1])):
        start, end = points[j], points[j + 1]
        direction = unit(sub(end, start))
        t_axis = unit(cross(sagittal, direction))
        n = CLEARANCE_SAMPLES
        z = [lengths[j] * k / n for k in range(n + 1)]
        r = [CLEARANCE_TAIL_FACTOR * math.sqrt(-lam_n / (1 / (q0 + zk)).imag) for zk in z]
        for sign in (1, -1):
            for k in range(n):
                a = add(add(start, mul(direction, z[k])), mul(t_axis, sign * r[k]))
                b = add(add(start, mul(direction, z[k + 1])), mul(t_axis, sign * r[k + 1]))
                span = norm(sub(b, a))
                if any(1e-10 < x < span for x in patch_intersections(a, unit(sub(b, a)), other, sagittal)):
                    return 'beam clips another reflector'
    return None


def evaluate_point(ports, constraints, a, c, lam_n, *, branch=None, kappas=None):
    """Screen one (a, c): exact branches (or given curvatures) through guards and constraints."""
    try:
        geometry = fold(ports, a, c)
    except (DomainError, ZeroDivisionError, ValueError, ArithmeticError):
        return [Point(a, c, 'geometry', 'zero/short middle segment')]
    vertices, normals, lengths, cosines = geometry
    if min(cosines) < constraints.min_cosine:
        return [Point(a, c, 'geometry', 'incidence exceeds limit')]
    if constraints.port_halfspace:  # vertex-level test first; the patch extent is checked later
        if dot(sub(vertices[1], ports.source.position), ports.source.direction) < 0:
            return [Point(a, c, 'constraint', 'reflector enters the Source body half-space')]
        if dot(sub(vertices[0], ports.target.position), ports.target.direction) > 0:
            return [Point(a, c, 'constraint', 'reflector enters the Target body half-space')]
    if constraints.block is not None:
        inside = [constraints.block.contains(v) for v in vertices]
        if constraints.block_side == 'inside' and not all(inside):
            return [Point(a, c, 'constraint', 'reflector crosses the block surface')]
        if constraints.block_side == 'outside' and any(inside):
            return [Point(a, c, 'constraint', 'reflector enters the block')]
    qs, qt = ports.source.mode.q, ports.target.mode.q
    if kappas is not None:
        options = [(('NM', 'NM'), kappas)]
    else:
        try:
            axes = [power_pairs(qs[i], qt[i], *lengths) for i in (0, 1)]
        except (DomainError, ArithmeticError):
            return [Point(a, c, 'power', 'nonfinite power solution')]
        if not all(axes):
            return [Point(a, c, 'power', 'no real exact-q power solution')]
        options = []
        for (it, pt), (is_, ps) in itertools.product(enumerate(axes[0]), enumerate(axes[1])):
            if branch is not None and (it, is_) != branch:
                continue
            kt = tuple(pt[j] * cosines[j] / 2 for j in (0, 1))
            ks = tuple(ps[j] / (2 * cosines[j]) for j in (0, 1))
            options.append(((it, is_), (kt, ks)))
    points = []
    for key, (kt, ks) in options:
        chains = [axis_chain(qs[0], lengths, cosines, kt, 0, lam_n), axis_chain(qs[1], lengths, cosines, ks, 1, lam_n)]
        if None in chains:
            points.append(Point(a, c, 'domain', 'invalid paraxial transformation', key))
            continue
        slope = max(chains[0]['slope'] + chains[1]['slope'])
        divergence = max(chains[0]['divergence'] + chains[1]['divergence'])
        log_eta = axis_log_eta(chains[0]['q'], qt[0], lam_n) + axis_log_eta(chains[1]['q'], qt[1], lam_n)
        metrics = {
            'total_path_m': sum(lengths), 'max_footprint_slope': slope, 'max_divergence_rad': divergence,
            'max_footprint_radius_m': max(chains[0]['footprint'] + chains[1]['footprint']),
            'max_abs_curvature_per_m': max(abs(k) for k in (*kt, *ks)),
            'incidence_deg': [math.degrees(math.acos(min(1.0, x))) for x in cosines],
            'normalized_mode_overlap': math.exp(min(0.0, log_eta)),
            'a_m': a, 'b_m': lengths[1], 'c_m': c,
        }
        point = Point(a, c, 'ok', '', key, metrics, (vertices, normals, lengths, (tuple(zip(kt, ks)))))
        if slope > MAX_FOOTPRINT_SLOPE:
            point.status, point.reason = 'domain', '3w projected footprint/curvature exceeds 0.15'
        elif divergence > MAX_DIVERGENCE:
            point.status, point.reason = 'domain', 'Gaussian divergence exceeds 0.1 rad'
        else:
            mirrors = build(ports, geometry, kt, ks, chains)
            obstruction = intercepted(ports, vertices, lengths, mirrors, chains, lam_n)
            if obstruction:
                point.status, point.reason = 'geometry', obstruction
            else:
                violation = constraint_violation(ports, constraints, vertices, mirrors)
                if violation:
                    point.status, point.reason = 'constraint', violation
        points.append(point)
    return points


# ---------- near-match inside the guards ----------

def near_match_curvatures(ports, lengths, cosines, lam_n):
    """Per-axis bounded maximisation of overlap with |3w κ| ≤ 0.15 and divergence ≤ 0.1 rad.

    Each axis is independent (separable Gaussian), with two curvature coordinates in [-1, 1]
    scaled by the slope limit at that reflector. Returns ((kt1, kt2), (ks1, ks2)), log_eta.
    """
    qs, qt = ports.source.mode.q, ports.target.mode.q
    limit = MAX_FOOTPRINT_SLOPE * (1 - 1e-9)
    result, total = [], 0.0
    for axis in (0, 1):
        def curvatures(x, axis=axis):
            q = qs[axis] + lengths[0]
            w1 = math.sqrt(-lam_n / (1 / q).imag)
            fp1 = w1 / cosines[0] if axis == 0 else w1
            k1 = x[0] * limit / (3 * fp1)
            power = 2 * k1 / cosines[0] if axis == 0 else 2 * k1 * cosines[0]
            q2 = q / (1 - power * q) + lengths[1]
            if (1 / q2).imag >= 0:
                return k1, 0.0
            w2 = math.sqrt(-lam_n / (1 / q2).imag)
            fp2 = w2 / cosines[1] if axis == 0 else w2
            return k1, x[1] * limit / (3 * fp2)

        def cost(x, axis=axis):
            try:
                kappas = curvatures(x)
                chain = axis_chain(qs[axis], lengths, cosines, kappas, axis, lam_n)
            except (ZeroDivisionError, ValueError, OverflowError):
                return 1e6
            if chain is None:
                return 1e6
            penalty = sum(max(0.0, d - MAX_DIVERGENCE) for d in chain['divergence']) * 1e3
            return -axis_log_eta(chain['q'], qt[axis], lam_n) + penalty

        best = None
        for seed in ((0.9, 0.6), (0.4, 0.9), (0.0, 0.0)):
            run = minimize(cost, seed, method='L-BFGS-B', bounds=[(-1, 1), (-1, 1)], options={'maxiter': 80})
            if best is None or run.fun < best.fun:
                best = run
        result.append(curvatures(best.x))
        total += -best.fun
    return (result[0], result[1]), total


def near_match_seeds(grid):
    """Geometries worth a Near-match, in trial order.

    First the 64 exact branches closest to the guard and up to 32 points without a real exact
    branch (the P2 set), then the remaining guard-limited points. Guard-limited points are not yet
    checked against the region constraints, so the later ones replace seeds that a constraint rejects.
    """
    near_guard = sorted((p for p in grid if p.status == 'domain' and p.metrics), key=lambda p: p.metrics['max_footprint_slope'])
    power = [p for p in grid if p.status == 'power']
    no_branch = power[::max(1, len(power) // 32)][:32]
    return near_guard[:64] + no_branch + near_guard[64:]


# ---------- alignment tolerance ----------

def pose_tolerance(prescription):
    """Worst Gaussian mismatch (dB) for one-at-a-time reflector pose errors of the placement study."""
    design = adapt_external(prescription)
    source, target, mirrors = design.source, design.target, design.reflectors
    evaluation = evaluate_external(prescription)
    arrival = evaluation['gaussian_mode_matching'].get('output_axes')
    if not arrival:
        return None
    from .mode_match import arrived_mode
    incident = arrived_mode(evaluation, target.mode)
    nominal = mode_overlap(incident, target.mode)['log_overlap']
    worst = 0.0
    for _, changed in reflector_poses(mirrors, source.sagittal):
        try:
            ray = ray_to_target(source.position, source.direction, target, changed, source.sagittal)
            log_eta = mode_overlap(incident, target.mode, offset=tuple(ray['target_offset_m']),
                                   slope=tuple(ray['target_slope']))['log_overlap']
        except DomainError:
            return None
        worst = max(worst, -10 * (log_eta - nominal) / math.log(10))  # log form stays finite on underflow
    return worst


# ---------- driver ----------

def grid_values(scale):
    n = POLICY['grid_points_per_axis']
    lo, hi = 0.01 * scale, 4.0 * scale
    return [lo * (hi / lo) ** (i / (n - 1)) for i in range(n)]


def refine(ports, constraints, lam_n, point, metric):
    """Continuous improvement of one objective on the feasible set, branch pair fixed."""
    def cost(x):
        found = evaluate_point(ports, constraints, math.exp(x[0]), math.exp(x[1]), lam_n, branch=point.branch)
        if not found or found[0].status != 'ok':
            return 1e9
        return found[0].metrics[metric]
    start = [math.log(point.a), math.log(point.c)]
    run = minimize(cost, start, method='Nelder-Mead',
                   options={'xatol': 1e-4, 'fatol': 1e-12, 'maxiter': 160, 'initial_simplex': [
                       start, [start[0] + 0.05, start[1]], [start[0], start[1] + 0.05]]})
    better = evaluate_point(ports, constraints, math.exp(run.x[0]), math.exp(run.x[1]), lam_n, branch=point.branch)
    if better and better[0].status == 'ok' and better[0].metrics[metric] <= point.metrics[metric]:
        return better[0]
    return point


def pareto(points, keys):
    front = []
    for p in points:
        if not any(all(q.metrics[k] <= p.metrics[k] for k in keys) and any(q.metrics[k] < p.metrics[k] for k in keys)
                   for q in points if q is not p):
            front.append(p)
    return front


def design_continuous(document, constraints=Constraints(), *, include_map=True):
    """Two fixed Ports (M3A-1 document, optional package) in; verified concepts out."""
    started = time.perf_counter()
    result = {'schema': 'P2-design-result-1', 'status': 'Uncomputed', 'input_snapshot': None,
              'input_contract': {'status': 'Uncomputed'}, 'search_policy': copy.deepcopy(POLICY),
              'constraints': constraints_record(constraints), 'candidates': [], 'selected_candidate_id': None,
              'search': {'status': 'Uncomputed'}, 'limitations': LIMITS,
              'actual_applicability': {'status': 'Uncomputed'}, 'physical_losses': {'status': 'Uncomputed', 'total_coupling': None},
              'package_feasibility': {'status': 'Uncomputed'}, 'fabrication_yield': {'status': 'Uncomputed'},
              'patentability': {'status': 'Uncomputed'}}
    try:
        snapshot = json.dumps(document, sort_keys=True, allow_nan=False)
        result['input_snapshot'] = json.loads(snapshot)
        result['input_sha256'] = hashlib.sha256(snapshot.encode()).hexdigest()
        if not isinstance(document, dict):
            fail('input', 'two-Port object required')
        if any(k in document for k in ('design', 'reflectors')):
            fail('input', 'Design takes two Ports and optional Package, not manual reflector prescriptions')
        ports = adapt_ports(document)
        result['input_contract'] = {'status': 'Pass', 'scope': 'explicit two-Port subset of M3A contract'}
        source, target = ports.source, ports.target
        if norm(sub(source.sagittal, target.sagittal)) > 1e-10:
            raise DomainError('rolled Target axes unsupported')
        if abs(dot(source.sagittal, target.direction)) > 1e-10:
            raise DomainError('noncoplanar Target direction')
        scale = norm(sub(target.position, source.position))
        if scale < 1e-9:
            raise DomainError('coincident/near-coincident Ports outside the two-reflector family')
        if abs(dot(source.sagittal, sub(target.position, source.position))) / scale > 1e-10:
            raise DomainError('noncoplanar Port positions')
        if any(p['divergence_rad'] > MAX_DIVERGENCE for port in (source, target) for p in port.mode.parameters()):
            raise DomainError('Gaussian divergence exceeds 0.1 rad')
        lam_n = source.mode.wavelength / (math.pi * source.mode.index)

        values = grid_values(scale)
        grid, counts = [], Counter()
        for a in values:
            for c in values:
                found = evaluate_point(ports, constraints, a, c, lam_n)
                feasible = [p for p in found if p.status == 'ok']
                chosen = min(feasible, key=lambda p: p.metrics['max_footprint_slope']) if feasible else (
                    min((p for p in found if p.metrics), key=lambda p: p.metrics['max_footprint_slope'], default=found[0]))
                grid.append(chosen)
                counts[chosen.status if chosen.status == 'ok' else f'{chosen.status}: {chosen.reason}'] += 1
        exact = [p for p in grid if p.status == 'ok']
        family = 'exact'
        pool = exact
        near_matches = []
        if not exact:
            for tried, point in enumerate(near_match_seeds(grid)):
                if tried >= NEAR_MATCH_MAX_TRIALS or (tried >= NEAR_MATCH_FIRST_TRIALS and near_matches):
                    break
                try:
                    vertices, normals, lengths, cosines = fold(ports, point.a, point.c)
                except (DomainError, ZeroDivisionError, ValueError, ArithmeticError):
                    continue
                kappas, _ = near_match_curvatures(ports, lengths, cosines, lam_n)
                found = evaluate_point(ports, constraints, point.a, point.c, lam_n, kappas=kappas)
                if found[0].status == 'ok':
                    near_matches.append(found[0])
            family = 'near_match'
            pool = near_matches
        result['search'].update(status='Completed', grid_points=len(grid), exact_feasible=len(exact),
                                near_match_feasible=len(near_matches), screening_counts=dict(sorted(counts.items())))
        if include_map:
            result['search']['map'] = {
                'a_m': values, 'c_m': values,
                'cells': [{'status': p.status, 'reason': p.reason,
                           'slope': p.metrics.get('max_footprint_slope'),
                           'path_m': p.metrics.get('total_path_m')} for p in grid],
                'near_match': [{'a_m': p.a, 'c_m': p.c, 'eta': p.metrics['normalized_mode_overlap']} for p in near_matches],
            }
        if not exact:
            closest = min((p for p in grid if p.metrics and p.status == 'domain'), key=lambda p: p.metrics['max_footprint_slope'], default=None)
            if closest:
                result['search']['closest_exact'] = {'a_m': closest.a, 'c_m': closest.c, 'reason': closest.reason,
                                                     'max_footprint_slope': closest.metrics['max_footprint_slope'],
                                                     'limit': MAX_FOOTPRINT_SLOPE}
        plan, front = select(ports, constraints, lam_n, pool, family)
        accepted, ledger = [], []

        def attempt(point, role):
            candidate = verify(document, ports, point, role, family)
            ledger.append({'role': role, 'a_m': point.a, 'c_m': point.c, 'status': candidate['status'],
                           'reason': candidate.get('reason')})
            if candidate['status'] == 'Accepted':
                accepted.append(candidate)
                return True
            return False

        for role, ranked in plan:
            for point in ranked:
                shared = next((c for c in accepted if same_point(point, c)), None)
                if shared:  # the same concept is already best for an earlier objective
                    shared['roles'].append(role)
                    break
                if attempt(point, role):
                    break
        # Too few distinct concepts: add Pareto points farthest (in ln a, ln c) from those shown.
        remaining = [p for p in front if not any(same_point(p, c) for c in accepted)]
        while len(accepted) < 3 and remaining:
            far = max(remaining, key=lambda p: min((math.hypot(math.log(p.a / c['parameters']['a_m']),
                                                               math.log(p.c / c['parameters']['c_m'])) for c in accepted),
                                                   default=0.0))
            remaining.remove(far)
            attempt(far, 'pareto_alternative')
        accepted = add_tolerance_roles(accepted)
        result['candidates'] = accepted
        result['search']['verification'] = ledger
        result['selected_candidate_id'] = accepted[0]['id'] if accepted else None
        result['status'] = 'Computed' if accepted else 'Fail'
        result['reason'] = ({'exact': 'Valid exact-q candidates generated',
                             'near_match': 'No exact-q candidate within the guards; Near-match candidates generated'}[family]
                            if accepted else
                            'No valid two-reflector candidate within the guards and constraints; not proof of physical impossibility')
    except InputIssue as exc:
        result['status'] = exc.status
        result['input_contract'] = {'status': exc.status, 'path': exc.path, 'reason': exc.reason}
        result['reason'] = str(exc)
    except (DomainError, TypeError, ValueError, ArithmeticError) as exc:
        result['status'] = 'Fail'
        result['reason'] = str(exc)
        if result['input_contract']['status'] != 'Pass':
            result['input_contract'] = {'status': 'Fail', 'reason': str(exc)}
        else:
            result['search'] = {**result['search'], 'status': 'Not started', 'reason': str(exc)}
    result['search']['elapsed_seconds'] = round(time.perf_counter() - started, 3)
    return json.loads(json.dumps(result, allow_nan=False))


ROLES = {'exact': ('short_path', 'model_margin', 'small_beam', 'gentle_curvature'),
         'near_match': ('best_overlap', 'short_path', 'small_beam', 'gentle_curvature')}


def select(ports, constraints, lam_n, pool, family, tries=6):
    """Per objective, a short ranked list of Pareto points (refined first choice, then runners-up)."""
    if not pool:
        return [], []
    keys = ['total_path_m', 'max_footprint_slope', 'max_footprint_radius_m', 'max_abs_curvature_per_m']
    if family == 'near_match':
        keys.append('mismatch')
        for p in pool:
            p.metrics['mismatch'] = 1 - p.metrics['normalized_mode_overlap']
        best = min(p.metrics['mismatch'] for p in pool)
        good = [p for p in pool if p.metrics['mismatch'] <= best + 0.01]
    else:
        good = pool
    front = pareto(good, keys) if family == 'exact' else good
    plan = []
    for role in ROLES[family]:
        metric = 'mismatch' if role == 'best_overlap' else OBJECTIVES[role][0]
        ranked = sorted(front, key=lambda p: (p.metrics[metric], p.metrics['total_path_m']))[:tries]
        if family == 'exact' and ranked:
            ranked[0] = refine(ports, constraints, lam_n, ranked[0], metric)
        plan.append((role, ranked))
    return plan, front


def verify(document, ports, point, role, family):
    vertices, normals, lengths, curvatures = point.prescription
    identifier = f"P2-{'E' if family == 'exact' else 'N'}-a{point.a * 1e3:.4f}-c{point.c * 1e3:.4f}-{''.join(map(str, point.branch))}"
    try:
        prescription = candidate_document(document, ports, vertices, normals, lengths, curvatures)
    except (DomainError, ArithmeticError) as exc:
        return {'status': 'Rejected', 'reason': str(exc)}
    evaluation = evaluate_external(prescription)
    bad = [k for k in ('input_contract', 'geometry', 'model_domain') if evaluation[k]['status'] != 'Pass']
    bad += [k for k in ('design_constraints', 'package_feasibility') if evaluation[k]['status'] == 'Fail']
    overlap = evaluation['gaussian_mode_matching'].get('normalized_mode_overlap')
    if bad or overlap is None:
        stage = bad[0] if bad else 'gaussian_mode_matching'
        return {'status': 'Rejected', 'reason': f"{stage}: {evaluation[stage].get('reason', 'failed')}"}
    before = [s for s in evaluation['samples'] if 'surface_radii_m' in s]
    ranking = {'overlap_deficit_at_1e-12': round(1 - overlap, 12),
               'total_path_m': sum(evaluation['geometry']['lengths']),
               'max_projected_radius_m': max(r for s in before for r in s['surface_radii_m']),
               'max_3w_footprint_curvature': max(s['footprint_slope_3w'] for s in before),
               'max_abs_curvature_per_m': max(abs(k) for pair in curvatures for k in pair),
               'stable_id': identifier}
    return {'status': 'Accepted', 'id': identifier, 'geometry_id': identifier.rsplit('-', 1)[0], 'family': family,
            'classification': 'Conceptual Geometry', 'recommendation_role': role, 'roles': [role],
            'objective_label': OBJECTIVES[role][2], 'parameters': {'a_m': point.a, 'b_m': lengths[1], 'c_m': point.c,
                                                                  'branch': list(point.branch)},
            'prescription': prescription, 'evaluation': evaluation, 'ranking': ranking,
            'worst_pose_mismatch_db': pose_tolerance(prescription),
            'advantages': ['Fixed Port closure and frozen domain guards passed', 'Checked by the unchanged external Adapter'],
            'limitations': LIMITS}


def same_point(point, candidate):
    p = candidate['parameters']
    return (abs(math.log(point.a / p['a_m'])) < 0.02 and abs(math.log(point.c / p['c_m'])) < 0.02
            and list(point.branch) == p['branch'])


def add_tolerance_roles(accepted):
    """Keep objective order; mark the most alignment-tolerant concept explicitly."""
    tolerant = [c for c in accepted if c['worst_pose_mismatch_db'] is not None]
    if len(tolerant) > 1:
        best = min(tolerant, key=lambda c: c['worst_pose_mismatch_db'])
        best['roles'].append('robust_alignment')
    return accepted


def constraints_record(constraints):
    return {'port_body_halfspace': constraints.port_halfspace,
            'envelope_m': [list(v) for v in constraints.envelope] if constraints.envelope else None,
            'keepouts_m': [{'label': label, 'min_m': list(box[0]), 'max_m': list(box[1])}
                           for label, box in zip(constraints.keepout_labels or [''] * len(constraints.keepouts), constraints.keepouts)],
            'clearance_m': constraints.clearance, 'max_incidence_deg': constraints.max_incidence_deg,
            'min_radius_of_curvature_m': constraints.min_radius_of_curvature,
            'block': None if constraints.block is None else {
                'label': constraints.block.label, 'index': constraints.block.index, 'side': constraints.block_side,
                'surface_point_m': list(constraints.block.point), 'surface_normal': list(constraints.block.normal),
                'thickness_m': constraints.block.thickness}}
