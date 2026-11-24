"""P4: coma-corrected reflector surfaces (third- and fourth-order sag terms).

The paraxial design fixes each reflector's vertex, normal and curvature tensor (second-order sag).
P3 showed that this local quadratic surface leaves large third-order aberration (coma) at oblique
incidence. Here each reflector gets higher sag terms in its principal coordinates (u, v):

    h(u, v) = ½(κ1 u² + κ2 v²) + Σ c_mn u^m v^n,   m + n ∈ {3, 4}

Terms of order ≥ 3 do not change the vertex, normal, curvatures or the paraxial q relay, so the
paraxial verification (engine Adapter or q-tensor ray check) still holds unchanged. They are chosen
to maximise the non-paraxial scalar overlap:

1. Trace the direction bundle once; for each ray record the hit (u, v) on each reflector and the
   local incidence cosine. A sag change δh shortens that ray's optical path by 2 δh cosθ, so the
   phase part of the overlap is linear in the coefficients. The model ignores the accompanying change
   of the direction mapping (ray positions on the Target plane and the amplitude), so it only proposes
   a step.
2. Maximise |Σ a e^{i(φ₀ + G b)}|² over the scaled coefficients b with an analytic gradient.
3. Re-trace exactly with the new surfaces (Newton intersections, exact normals), backtrack if the
   exact overlap does not improve, and relinearise. When the model keeps overshooting (steep
   incidence), the exact overlap is maximised directly on a coarse grid. The reported value is always
   the exact re-trace with the convergence check.

Coefficients are scaled as Δh = λ · Σ b_mn (u/w_u)^m (v/w_v)^n with w the 1/e² footprint on the
reflector, so b is the sag in wavelengths at one footprint radius.
"""

import math

import numpy as np
from scipy.optimize import minimize

from . import nonparaxial
from .gaussian import DomainError

EXPONENTS = ((3, 0), (2, 1), (1, 2), (0, 3), (4, 0), (3, 1), (2, 2), (1, 3), (0, 4))
FIT_GRID = 97
MAX_ROUNDS = 6
SAG_GRID = 41
EXACT_GRID = 49
EXACT_ITERATIONS = 15


def _basis(hits, footprints, wavelength):
    """Phase change per unit scaled coefficient for every ray (rays × 2·len(EXPONENTS))."""
    columns = []
    for hit, (wu, wv) in zip(hits, footprints):
        for m, n in EXPONENTS:
            columns.append(4 * math.pi * hit['cos'] * (hit['u'] / wu) ** m * (hit['v'] / wv) ** n)
    return np.stack(columns, 1)


def _poly(b, footprints, wavelength):
    """Physical sag terms per reflector from scaled coefficients."""
    out = []
    for j, (wu, wv) in enumerate(footprints):
        block = b[j * len(EXPONENTS):(j + 1) * len(EXPONENTS)]
        out.append(tuple((m, n, float(wavelength * c / (wu ** m * wv ** n))) for (m, n), c in zip(EXPONENTS, block)))
    return out


def _maximise(f, g):
    """Coefficients maximising |Σ a e^{i(φ + G b)}|² (linear phase model), from zero."""
    a = f['amplitude'] * np.exp(1j * (f['phase'] - f['phase'][np.argmax(abs(f['amplitude']))]))

    def cost(b):
        e = a * np.exp(1j * (g @ b))
        s = e.sum()
        grad = 2 * ((s.conjugate() * (1j * (e[:, None] * g)).sum(0)).real)
        return -abs(s) ** 2 / f['norm'], -grad / f['norm']
    run = minimize(cost, np.zeros(g.shape[1]), jac=True, method='L-BFGS-B',
                   bounds=[(-40, 40)] * g.shape[1], options={'maxiter': 400})
    return run.x, -run.fun


def _maximise_exact(evaluate, start, size):
    """Exact-overlap maximisation (finite-difference gradient) when the linear phase model misleads."""
    def cost(b):
        value = evaluate(b)
        return -value if value is not None else 1.0
    run = minimize(cost, start, method='L-BFGS-B', bounds=[(-40, 40)] * size,
                   options={'maxiter': EXACT_ITERATIONS, 'eps': 1e-3})
    return run.x, -run.fun


def max_sag(poly, half_aperture):
    """Largest |Δh| over the rectangular aperture."""
    u = np.linspace(-half_aperture[0], half_aperture[0], SAG_GRID)
    v = np.linspace(-half_aperture[1], half_aperture[1], SAG_GRID)
    uu, vv = np.meshgrid(u, v, indexing='ij')
    value, _, _ = nonparaxial._poly(poly, uu, vv)
    return float(abs(value).max())


def correct(args, mirrors, footprints, wavelength):
    """Coma-correcting sag terms for both reflectors.

    `args` are nonparaxial.check's leading arguments (both modes and Ports, k, half angle) without the
    mirror list; `mirrors` are quadric mirror tuples; `footprints` the 1/e² footprints (w_u, w_v).
    Returns the polynomial terms, the exact non-paraxial check with them and the fit history.
    """
    def with_poly(poly):
        return [nonparaxial.mirror_tuple(m[0], m[1], m[3], (m[4], m[5]), (m[6], m[7]), p) for m, p in zip(mirrors, poly)]

    def exact(poly, grid=FIT_GRID):
        f = nonparaxial.field(*args[:8], with_poly(poly), *args[8:], grid=grid)
        value = abs((f['amplitude'] * np.exp(1j * f['phase'])).sum()) ** 2 / f['norm']
        valid = f['folded_power_fraction'] <= nonparaxial.FOLD_LIMIT and value <= 1 + nonparaxial.CONVERGENCE_LIMIT
        return f, (value if valid else None)

    b = np.zeros(2 * len(EXPONENTS))
    poly = _poly(b, footprints, wavelength)
    f, eta = exact(poly)
    if eta is None:
        raise DomainError('direction mapping of the uncorrected relay is folded')
    history = [{'round': 0, 'exact': float(eta), 'method': 'quadric'}]
    for round_ in range(1, MAX_ROUNDS + 1):
        step, predicted = _maximise(f, _basis(f['hits'], footprints, wavelength))
        accepted = None
        for fraction in (1.0, 0.5, 0.25, 0.125):  # backtrack when the linear model overshoots
            trial = _poly(b + fraction * step, footprints, wavelength)
            try:
                f_new, eta_new = exact(trial)
            except DomainError:
                continue
            if eta_new is not None and eta_new > eta + 1e-6:
                accepted = (fraction, trial, f_new, eta_new)
                break
        history.append({'round': round_, 'method': 'linear phase', 'predicted': float(predicted),
                        'exact': float(accepted[3]) if accepted else float(eta),
                        'step_fraction': accepted[0] if accepted else 0.0})
        if accepted is None:
            break
        fraction, poly, f, eta = accepted
        b = b + fraction * step
    if history[-1]['step_fraction'] == 0.0 and history[-1]['predicted'] > eta + 0.005:
        # The phase-only model ignores the first-order change of the direction mapping (amplitude);
        # at steep incidence that dominates, so optimise the exact overlap directly on a coarse grid.
        def evaluate(trial_b):
            try:
                return exact(_poly(trial_b, footprints, wavelength), EXACT_GRID)[1]
            except DomainError:
                return None
        trial_b, _ = _maximise_exact(evaluate, b, len(b))
        trial = _poly(trial_b, footprints, wavelength)
        try:
            f_new, eta_new = exact(trial)
        except DomainError:
            eta_new = None
        history.append({'round': len(history), 'method': 'exact overlap', 'exact': float(eta_new or eta)})
        if eta_new is not None and eta_new > eta + 1e-6:
            b, poly, f, eta = trial_b, trial, f_new, eta_new
    check = nonparaxial.check(*args[:8], with_poly(poly), *args[8:])
    return {'scaled_coefficients': [float(x) for x in b], 'poly': poly, 'check': check, 'history': history}


def correct_mirrors(ports, mirrors, aperture_factor):
    """Correction for reflector objects (engine Reflector or q-tensor TensorReflector)."""
    q_s, a_s, q_t, a_t = nonparaxial.ports_q(ports)
    k = 2 * math.pi * ports.source.mode.index / ports.source.mode.wavelength
    tuples = [nonparaxial.mirror_tuple(m.vertex, m.normal, getattr(m, 'axis', None) or ports.source.sagittal,
                                       m.curvatures, m.half_aperture) for m in mirrors]
    footprints = [tuple(a / aperture_factor for a in m.half_aperture) for m in mirrors]
    args = (q_s, a_s, ports.source.position, ports.source.direction, q_t, a_t, ports.target.position,
            ports.target.direction, k, nonparaxial.half_angle(ports))
    wavelength = ports.source.mode.wavelength / ports.source.mode.index
    result = correct(args, tuples, footprints, wavelength)
    result['reflectors'] = [{
        'id': f'M{j + 1}', 'principal_axes': [list(t[2]), list(t[3])],
        'terms': [{'u_power': m, 'v_power': n, 'coefficient_si': c} for m, n, c in poly],
        'max_sag_change_um': max_sag(poly, m.half_aperture) * 1e6,
        'correction_size': fabrication(poly, m.curvatures, m.half_aperture, fp),
    } for j, (m, t, poly, fp) in enumerate(zip(mirrors, tuples, result['poly'], footprints))]
    corrected = [nonparaxial.mirror_tuple(t[0], t[1], t[3], (t[4], t[5]), (t[6], t[7]), p) for t, p in zip(tuples, result['poly'])]
    result['pose'] = {'quadric_worst_loss_db': pose_loss(args, tuples), 'corrected_worst_loss_db': pose_loss(args, corrected),
                      'cases': '±5 µm along X, Y, Z and ±1 mrad about both principal axes, one reflector at a time',
                      'grid': POSE_GRID, 'meaning': 'Non-paraxial overlap loss relative to the nominal of the same surface'}
    return result


POSE_GRID = 65


def _rotate(vector, axis, angle):
    e = np.asarray(axis, float)
    v = np.asarray(vector, float)
    return v * math.cos(angle) + np.cross(e, v) * math.sin(angle) + e * (e @ v) * (1 - math.cos(angle))


def poses(mirrors):
    """±5 µm along X, Y, Z and ±1 mrad about both principal axes, one reflector at a time (mirror tuples)."""
    from .placement import ROTATION_RAD, TRANSLATION_M
    for index, m in enumerate(mirrors):
        vertex, n, e1, e2 = m[:4]
        for axis in range(3):
            for delta in (-TRANSLATION_M, TRANSLATION_M):
                shifted = np.array(vertex, float)
                shifted[axis] += delta
                changed = list(mirrors)
                changed[index] = (shifted, *m[1:])
                yield changed
        for pivot in (e1, e2):
            for angle in (-ROTATION_RAD, ROTATION_RAD):
                changed = list(mirrors)
                changed[index] = (m[0], _rotate(n, pivot, angle), _rotate(e1, pivot, angle), _rotate(e2, pivot, angle), *m[4:])
                yield changed


def pose_loss(args, mirrors):
    """Worst non-paraxial overlap loss [dB] over the one-at-a-time pose cases (same grid for all cases)."""
    def eta(ms):
        f = nonparaxial.field(*args[:8], ms, *args[8:], grid=POSE_GRID)
        return abs((f['amplitude'] * np.exp(1j * f['phase'])).sum()) ** 2 / f['norm']
    nominal = eta(mirrors)
    worst = 0.0
    for changed in poses(mirrors):
        try:
            value = eta(changed)
        except DomainError:
            return None
        worst = max(worst, -10 * math.log10(max(value, 1e-300) / nominal))
    return worst


def fabrication(poly, curvatures, half_aperture, footprint, n=SAG_GRID):
    """Size of the correction: sag and slope departure from the quadric, over the 1/e² footprint and the aperture."""
    def stats(extent):
        u = np.linspace(-extent[0], extent[0], n)
        v = np.linspace(-extent[1], extent[1], n)
        uu, vv = np.meshgrid(u, v, indexing='ij')
        value, du, dv = nonparaxial._poly(poly, uu, vv)
        inside = (uu / extent[0]) ** 2 + (vv / extent[1]) ** 2 <= 1
        sag = value[inside]
        return {'pv_um': float(sag.max() - sag.min()) * 1e6, 'rms_um': float(np.sqrt(((sag - sag.mean()) ** 2).mean())) * 1e6,
                'max_slope_mrad': float(np.hypot(du, dv)[inside].max()) * 1e3}
    return {'footprint': stats(footprint), 'aperture': stats(half_aperture)}


def surface_points(vertex, normal, first_axis, second_axis, curvatures, half_aperture, poly, n=SAG_GRID):
    """World points (n × n × 3) of a corrected patch."""
    u = np.linspace(-half_aperture[0], half_aperture[0], n)
    v = np.linspace(-half_aperture[1], half_aperture[1], n)
    uu, vv = np.meshgrid(u, v, indexing='ij')
    extra, _, _ = nonparaxial._poly(poly, uu, vv)
    h = (curvatures[0] * uu * uu + curvatures[1] * vv * vv) / 2 + extra
    return (np.array(vertex) + uu[..., None] * np.array(first_axis) + vv[..., None] * np.array(second_axis)
            + h[..., None] * np.array(normal))


def surface_violation(ports, constraints, points):
    """Space constraints re-checked on the corrected surface points (the quadric patch was checked in the search)."""
    p = points.reshape(-1, 3)
    if constraints is None:
        return None
    if constraints.port_halfspace:
        if ((p - np.array(ports.source.position)) @ np.array(ports.source.direction)).min() < 0:
            return 'corrected surface enters the Source body half-space'
        if ((p - np.array(ports.target.position)) @ np.array(ports.target.direction)).max() > 0:
            return 'corrected surface enters the Target body half-space'
    block = constraints.block
    if block is not None:
        height = (p - np.array(block.point)) @ np.array(block.normal)
        if constraints.block_side == 'inside':
            if height.max() > 0:
                return 'corrected surface crosses the block surface'
            if block.thickness is not None and height.min() < -block.thickness:
                return 'corrected surface leaves the block bottom'
        elif height.min() < 0:
            return 'corrected surface enters the block'
    if constraints.envelope:
        lo, hi = (np.array(x) for x in constraints.envelope)
        if (p < lo).any() or (p > hi).any():
            return 'corrected surface outside the package envelope'
    for lo, hi in constraints.keepouts:
        gap = np.linalg.norm(np.maximum(0, np.maximum(np.array(lo) - p, p - np.array(hi))), axis=1)
        if (gap <= max(constraints.clearance or 0.0, 0.0)).any():
            return 'corrected surface inside a keep-out clearance'
    return None


def correct_candidate(candidate, engine_document, constraints=None):
    """Coma correction of one accepted candidate (separable engine prescription or q-tensor record)."""
    from .external import adapt_external, adapt_ports
    from .qtensor import TensorReflector
    from .search import APERTURE_FACTOR
    if candidate.get('model') == 'qtensor':
        ports = adapt_ports(engine_document)
        mirrors = [TensorReflector(r['vertex_m'], r['normal'], r['curvatures_per_m'], r['half_aperture_m'],
                                   r['principal_axes'][1]) for r in candidate['prescription']['reflectors']]
    else:
        design = adapt_external(candidate['prescription'])
        ports, mirrors = design, design.reflectors
    result = correct_mirrors(ports, mirrors, APERTURE_FACTOR)
    check = result['check']
    violation = None
    for mirror, record, poly in zip(mirrors, result['reflectors'], result['poly']):
        axis = getattr(mirror, 'axis', None) or ports.source.sagittal
        first = np.cross(axis, mirror.normal)
        violation = violation or surface_violation(ports, constraints, surface_points(
            mirror.vertex, mirror.normal, first / np.linalg.norm(first), axis, mirror.curvatures, mirror.half_aperture, poly))
    return {'status': check['status'], 'constraint': violation, 'normalized_mode_overlap': check['normalized_mode_overlap'],
            'grid_change': check['grid_change'], 'clipped_power_fraction': check['clipped_power_fraction'],
            'reflectors': result['reflectors'], 'fit_history': result['history'], 'pose': result['pose'],
            'surface': ('h = ½(κ1 u² + κ2 v²) + Σ c·u^m·v^n (m + n = 3, 4) in each reflector\'s principal axes '
                        '(u along t_axis, v along s_axis of the scene); coefficients in SI units (m^(1−m−n))'),
            'meaning': ('Third/fourth-order sag added to the paraxial prescription to maximise the non-paraxial '
                        'overlap; vertex, normal and curvatures (paraxial relay) are unchanged')}
