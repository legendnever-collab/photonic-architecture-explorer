"""P3 stage 3: non-paraxial scalar check of a two-reflector relay (angular spectrum + exact rays).

The paraxial q model is trusted only inside the frozen guards. This module evaluates the same relay
without the paraxial approximation, in the regime where both waists are far (≫ Rayleigh range) from
the reflectors and the reflector patches are much larger than the wavelength:

1. The Source mode is expanded exactly into plane waves (scalar angular spectrum, no small-angle
   approximation). For a Gaussian with complex q-matrix q_s the spectrum is analytic,
   A(p) ∝ exp(i pᵀ q_s p / 2k), p the transverse wave vector.
2. Every plane-wave direction is followed as an exact ray from the Source point through the clipped
   quadric patches to the Target plane. In the far zone each direction is carried by one ray
   (stationary phase), so the arriving plane-wave component at the Target point has
     amplitude  |A| · √(k_z / q_z / J)   (flux conservation, J = |∂q/∂p|)
     phase      −k W,  W = OPL − d'·x_r  (optical path to the plane less the tilt across the plane).
3. The arriving spectrum is overlapped with the Target mode's spectrum (Parseval, exact):
     η = |∫ A B* e^{−ikW} √(J k_z/q_z) d²u|² / (∫ |A|² k_z/q_z d²u · ∫ |B|² d²u').

This is the scalar Debye (Richards–Wolf type) treatment: exact in the propagation angles, geometric
in the reflectors. It omits edge diffraction at the apertures (rays outside a patch are dropped and
reported as clipped power), polarization and the Fresnel coefficients, and the Target overlap is
normalized by the arriving field, as for the paraxial η. Convergence is checked by doubling the grid.
"""

import math

import numpy as np

from .gaussian import DomainError
from .geometry import cross, unit

GRID = 129                 # points per axis of the direction-cosine grid (doubled for the convergence check)
SCREEN_GRID = 65           # coarse grid used to rank many screened geometries
SCREEN_POINTS = 400        # at most this many feasible geometries are ranked by the non-paraxial overlap
SPECTRUM_SIGMAS = 3.6      # half-width of the grid in units of the 1/e² intensity half-angle (|A|² ≈ e^-26 at the edge)
MAX_DIRECTION_COSINE = 0.95
CONVERGENCE_LIMIT = 1e-4


def mirror_tuple(vertex, normal, second_axis, curvatures, half_aperture):
    n = unit(normal)
    e2 = unit(second_axis)
    e1 = unit(cross(e2, n))
    return (np.array(vertex, float), np.array(n), np.array(e1), np.array(e2),
            float(curvatures[0]), float(curvatures[1]), float(half_aperture[0]), float(half_aperture[1]))


def trace_bundle(origin, directions, mirrors, target_position, target_basis, target_direction):
    """Vectorised exact rays through clipped quadric patches to the Target plane."""
    o = np.broadcast_to(np.array(origin, float), directions.shape).copy()
    d = directions.copy()
    alive = np.ones(len(d), bool)
    opl = np.zeros(len(d))
    for vertex, n, e1, e2, k1, k2, h1, h2 in mirrors:
        rel = o - vertex
        u, v, h = rel @ e1, rel @ e2, rel @ n
        du, dv, dh = d @ e1, d @ e2, d @ n
        a = -(k1 * du * du + k2 * dv * dv) / 2
        b = dh - k1 * u * du - k2 * v * dv
        c = h - (k1 * u * u + k2 * v * v) / 2
        with np.errstate(divide='ignore', invalid='ignore'):
            disc = b * b - 4 * a * c
            sq = np.sqrt(np.where(disc >= 0, disc, np.nan))
            qq = -0.5 * (b + np.copysign(sq, b))
            linear = np.abs(a) < 1e-14
            r1 = np.where(linear, -c / b, qq / a)
            r2 = np.where(linear, np.nan, c / qq)
        best = np.full(len(d), np.inf)
        for r in (r1, r2):
            ok = np.isfinite(r) & (r > 1e-12)
            uu, vv = u + r * du, v + r * dv
            ok &= (np.abs(uu) <= h1) & (np.abs(vv) <= h2)
            best = np.where(ok & (r < best), r, best)
        alive &= np.isfinite(best)
        best = np.where(np.isfinite(best), best, 0.0)
        d = np.where(alive[:, None], d, np.array(target_direction))  # dead rays: keep finite placeholders
        o = o + d * best[:, None]
        opl += best
        rel = o - vertex
        u, v = rel @ e1, rel @ e2
        normal = n[None, :] - (k1 * u)[:, None] * e1[None, :] - (k2 * v)[:, None] * e2[None, :]
        normal /= np.linalg.norm(normal, axis=1)[:, None]
        d = d - 2 * (d * normal).sum(1)[:, None] * normal
    den = d @ target_direction
    alive &= den > 1e-9
    with np.errstate(divide='ignore', invalid='ignore'):
        t = ((np.array(target_position) - o) @ target_direction) / den
    alive &= t > 0
    t = np.where(alive, t, 0.0)
    x = o + d * t[:, None] - np.array(target_position)
    opl += t
    keep = alive[:, None]
    return {'alive': alive, 'opl': np.where(alive, opl, 0.0), 'x': np.where(keep, x @ target_basis, 0.0),
            'u': np.where(keep, d @ target_basis, 0.0)}


def _spectrum(qmatrix, k, u):
    """Plane-wave amplitude of a Gaussian with q-matrix (= Q⁻¹) at direction cosines u (…, 2)."""
    p = k * u
    return np.exp(1j * np.einsum('...i,ij,...j', p, qmatrix, p) / (2 * k))


def overlap(source_q, source_basis, source_position, source_direction, target_q, target_basis, target_position,
            target_direction, mirrors, k, half_angle, grid=GRID):
    """Non-paraxial η, clipped power fraction and the mapped region, for one grid size."""
    limit = min(MAX_DIRECTION_COSINE, SPECTRUM_SIGMAS * half_angle)
    axis = np.linspace(-limit, limit, grid)
    step = axis[1] - axis[0]
    uu, vv = np.meshgrid(axis, axis, indexing='ij')
    inside = uu ** 2 + vv ** 2 < limit ** 2
    kz = np.sqrt(np.clip(1 - uu ** 2 - vv ** 2, 0, None))
    directions = (uu[..., None] * source_basis[:, 0] + vv[..., None] * source_basis[:, 1]
                  + kz[..., None] * np.array(source_direction))
    ray = trace_bundle(source_position, directions.reshape(-1, 3), mirrors, target_position, target_basis,
                       np.array(target_direction))
    shape = uu.shape
    alive = ray['alive'].reshape(shape) & inside
    uq = ray['u'].reshape(shape + (2,))
    xr = ray['x'].reshape(shape + (2,))
    qz = np.sqrt(np.clip(1 - (uq ** 2).sum(-1), 1e-300, None))
    w = ray['opl'].reshape(shape) - (uq * xr).sum(-1)
    jac = np.abs(np.gradient(uq[..., 0], step, axis=0) * np.gradient(uq[..., 1], step, axis=1)
                 - np.gradient(uq[..., 0], step, axis=1) * np.gradient(uq[..., 1], step, axis=0))
    a = _spectrum(source_q, k, np.stack([uu, vv], -1))
    b = _spectrum(target_q, k, uq)
    weight = np.where(alive, np.sqrt(np.nan_to_num(jac) * kz / qz), 0.0)
    integral = (a * b.conj() * np.exp(-1j * k * w) * weight).sum() * step * step
    arriving = (np.where(alive, abs(a) ** 2 * kz / qz, 0.0)).sum() * step * step
    launched = (np.where(inside, abs(a) ** 2 * kz, 0.0)).sum() * step * step
    flux = (np.where(alive, abs(a) ** 2 * kz, 0.0)).sum() * step * step
    m = target_q.imag * k  # |B|² = exp(-uᵀ (k Im q_t) u) in direction-cosine units
    target_norm = math.pi / math.sqrt(np.linalg.det(m))
    if arriving <= 0:
        raise DomainError('no ray reaches the Target plane')
    eta = abs(integral) ** 2 / (arriving * target_norm)
    return {'eta': float(eta), 'clipped_power_fraction': float(1 - flux / launched), 'grid': grid,
            'max_direction_cosine': float(limit)}


def check(source_q, source_basis, source_position, source_direction, target_q, target_basis, target_position,
          target_direction, mirrors, k, half_angle):
    """η at GRID and 2·GRID−1 points per axis; converged when they agree to 1e-4."""
    args = (source_q, source_basis, source_position, source_direction, target_q, target_basis, target_position,
            target_direction, mirrors, k, half_angle)
    coarse = overlap(*args, grid=GRID)
    fine = overlap(*args, grid=2 * GRID - 1)
    change = abs(fine['eta'] - coarse['eta'])
    return {'status': 'Computed' if change <= CONVERGENCE_LIMIT else 'Unconverged',
            'normalized_mode_overlap': fine['eta'], 'grid_change': change,
            'clipped_power_fraction': fine['clipped_power_fraction'], 'max_direction_cosine': fine['max_direction_cosine'],
            'method': ('scalar angular spectrum of both modes, exact rays through the quadric patches, '
                       f'{2 * GRID - 1}² directions (convergence vs {GRID}²)'),
            'omits': 'aperture-edge diffraction, polarization, Fresnel coefficients, multiple reflections'}


# ---------- adapters for both candidate kinds ----------

def ports_q(ports):
    from .qtensor import port_beam
    qs, a_s = port_beam(ports.source)
    qt, a_t = port_beam(ports.target)
    return np.linalg.inv(qs), a_s, np.linalg.inv(qt), a_t


def half_angle(ports):
    return max(p['divergence_rad'] for port in (ports.source, ports.target) for p in port.mode.parameters())


def check_mirrors(ports, mirrors):
    """mirrors: objects with vertex, normal, curvatures, half_aperture and an `axis` (or the Source sagittal)."""
    q_s, a_s, q_t, a_t = ports_q(ports)
    tuples = [mirror_tuple(m.vertex, m.normal, getattr(m, 'axis', None) or ports.source.sagittal,
                           m.curvatures, m.half_aperture) for m in mirrors]
    k = 2 * math.pi * ports.source.mode.index / ports.source.mode.wavelength
    return check(q_s, a_s, ports.source.position, ports.source.direction, q_t, a_t, ports.target.position,
                 ports.target.direction, tuples, k, half_angle(ports))


def check_candidate(candidate, engine_document):
    """Non-paraxial check of one accepted candidate (separable engine prescription or q-tensor record)."""
    from .external import adapt_external, adapt_ports
    from .qtensor import TensorReflector
    if candidate.get('model') == 'qtensor':
        ports = adapt_ports(engine_document)
        mirrors = [TensorReflector(r['vertex_m'], r['normal'], r['curvatures_per_m'], r['half_aperture_m'],
                                   r['principal_axes'][1]) for r in candidate['prescription']['reflectors']]
    else:
        design = adapt_external(candidate['prescription'])
        ports, mirrors = design, design.reflectors
    return check_mirrors(ports, mirrors)


def point_mirrors(ports, point):
    """Reflector tuples for a screened search.Point (separable curvature pairs or q-tensor reflectors)."""
    vertices, normals, _, curvatures = point.prescription
    out = []
    for j in (0, 1):
        item = curvatures[j]
        if hasattr(item, 'curvatures'):
            out.append(mirror_tuple(item.vertex, item.normal, item.axis, item.curvatures, item.half_aperture))
        else:  # separable pair (κ_t, κ_s); apertures are not part of the screened point, so none are applied
            out.append(mirror_tuple(vertices[j], normals[j], ports.source.sagittal, item, (1.0, 1.0)))
    return out


def screen(ports, points):
    """Coarse non-paraxial η for up to SCREEN_POINTS feasible geometries (evenly thinned), best first."""
    q_s, a_s, q_t, a_t = ports_q(ports)
    k = 2 * math.pi * ports.source.mode.index / ports.source.mode.wavelength
    angle = half_angle(ports)
    chosen = points[::max(1, math.ceil(len(points) / SCREEN_POINTS))]
    ranked = []
    for point in chosen:
        try:
            eta = overlap(q_s, a_s, ports.source.position, ports.source.direction, q_t, a_t, ports.target.position,
                          ports.target.direction, point_mirrors(ports, point), k, angle, grid=SCREEN_GRID)['eta']
        except (DomainError, ValueError, FloatingPointError, np.linalg.LinAlgError):
            continue
        if math.isfinite(eta):
            point.metrics['nonparaxial_overlap_screen'] = eta
            ranked.append(point)
    return sorted(ranked, key=lambda p: -p.metrics['nonparaxial_overlap_screen'])


def guard_study(engine_document, constraints, cases=4):
    """Ports beyond the paraxial divergence guard: how far off is the best paraxial two-reflector design?

    The frozen guards stay in force, so nothing here is a candidate. Exact-q geometries are screened with
    the guards switched off (space constraints and reflector clearance still apply); the ones closest to
    the 3w·|κ| guard are evaluated with the non-paraxial check. Apertures are the 1e-6 power-tail
    radius (2.63 w) rather than the 4 w prescription, so the study asks for the smallest clear patch.
    The result is evidence for a decision (another family, or a reviewed guard change), not a design.
    """
    from . import qtensor
    from .external import adapt_ports
    from .geometry import norm, sub
    from .search import CLEARANCE_TAIL_FACTOR, constraint_violation, grid_values
    ports = adapt_ports(engine_document)
    lam_n = ports.source.mode.wavelength / (math.pi * ports.source.mode.index)
    k = 2 / lam_n
    scale = norm(sub(ports.target.position, ports.source.position))
    pool = []
    for a in grid_values(scale):
        for c in grid_values(scale):
            for point in qtensor.evaluate_point(ports, constraints, a, c, lam_n):
                if point.metrics and (point.status == 'ok' or (point.status == 'domain' and point.prescription)):
                    pool.append(point)
    pool.sort(key=lambda p: p.metrics['max_footprint_slope'])
    chosen, rows = [], []
    for point in pool:
        if len(chosen) >= cases:
            break
        if any(abs(math.log(point.a / q.a)) < 0.2 and abs(math.log(point.c / q.c)) < 0.2 for q in chosen):
            continue
        vertices, _, lengths, mirrors = point.prescription
        try:
            run = qtensor.chain(ports, mirrors, lengths, k)
            mirrors = qtensor.with_apertures(mirrors, run['footprints'], CLEARANCE_TAIL_FACTOR)
            if qtensor.obstruction(ports, vertices, lengths, mirrors, run, k) or constraint_violation(ports, constraints, vertices, mirrors):
                continue
            result = check_mirrors(ports, mirrors)
        except (DomainError, ValueError, ArithmeticError, np.linalg.LinAlgError):
            continue
        chosen.append(point)
        rows.append({'a_mm': point.a * 1e3, 'c_mm': point.c * 1e3, 'total_path_mm': sum(lengths) * 1e3,
                     'max_3w_footprint_curvature': point.metrics['max_footprint_slope'],
                     'max_divergence_rad': point.metrics['max_divergence_rad'],
                     'incidence_deg': point.metrics['incidence_deg'], 'paraxial_overlap': point.metrics['normalized_mode_overlap'],
                     'nonparaxial_overlap': result['normalized_mode_overlap'], 'nonparaxial_status': result['status'],
                     'clipped_power_fraction': result['clipped_power_fraction']})
    if not rows:
        return {'status': 'Uncomputed', 'reason': 'no exact-q geometry clears the space constraints', 'cases': [],
                'message': ('Port 발산각이 Guard(0.1 rad)를 넘어 후보는 내지 않았습니다. Guard를 끈 근축 Exact 설계도 '
                            'Port 뒤 공간·반사면 가림 같은 공간 조건을 통과하지 못해 비근축 검산을 하지 않았습니다. '
                            '두 반사면 Family 밖(렌즈·고차 곡면, P4)의 문제입니다.')}
    best = max(r['nonparaxial_overlap'] for r in rows)
    return {'status': 'Study', 'cases': rows,
            'summary': {'cases': len(rows), 'best_nonparaxial_overlap': best,
                        'source_divergence_rad': max(p['divergence_rad'] for p in ports.source.mode.parameters()),
                        'target_divergence_rad': max(p['divergence_rad'] for p in ports.target.mode.parameters())},
            'meaning': ('Exact-q two-reflector geometries outside the frozen paraxial guards, evaluated with the '
                        'non-paraxial scalar check (apertures 2.63 w). Not candidates; evidence for the next decision.'),
            'message': (f'Port 발산각이 Guard(0.1 rad)를 넘어 후보는 내지 않았습니다. 대신 Guard를 끈 근축 Exact 설계 중 '
                        f'3w·|κ|가 가장 작은 {len(rows)}개를 비근축 Scalar로 검산했습니다: 최고 η {best:.3f}. '
                        + ('두 반사면(국소 이차곡면) Family로는 이 Mode 쌍을 근축 예측만큼 결합할 수 없습니다. '
                           '렌즈·고차 곡면 Family(P4)가 필요합니다.' if best < 0.9 else
                           '비근축 검산 결과가 좋아 Guard 재검토 근거가 될 수 있습니다(Guard 변경은 사용자 승인 사항).'))}
