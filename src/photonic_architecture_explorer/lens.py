"""P4: aspheric micro-lens converters for Ports beyond the paraxial divergence guard.

A Port whose mode diverges faster than the frozen 0.1 rad guard (SiPh SSC, laser) cannot enter the
paraxial two-reflector search. A plano-convex singlet on the Port axis (flat side facing the Port)
expands the mode so that it leaves the lens with a small divergence; the beam just after the lens is
an equivalent Port inside the guard, and the unchanged search designs the relay from there.

Paraxial design (reduced ray matrices, indices relative to the ambient medium):

    output waist  w' = λ_m / (π θ'),   EFL f = π w₀ w' / λ_m,   curved side c₂ = n₀ / (f (n₀ − n_L))
    Port at the front focal point: d + t·n₀/n_L = f

The lens itself is high-NA, so it is never trusted paraxially: its conic and r⁴, r⁶ aspheric terms
are fitted by maximising the non-paraxial overlap of (Port → lens → plane) with the equivalent Port
mode, and the whole relay (lens, reflectors, lens) is checked non-paraxially. Candidates of this
family are therefore accepted only on the non-paraxial check, which is reported separately from the
paraxial family (the frozen guards still govern the paraxial model).
"""

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize

from . import nonparaxial
from .gaussian import DomainError, Gaussian
from .geometry import add, mul, unit

LENS_EXPANSION_OPTIONS = (0.01, 0.02)  # output divergence θ' [rad]; small θ' puts the lens ≥ 10 Rayleigh ranges from the Port
THICKNESS_FRACTION = 0.5               # centre thickness as a fraction of the EFL
APERTURE_MARGIN = 1.6                  # clear radius = margin × 2.63 w at the curved surface
LENS_FIT_GRID = 65


@dataclass
class Lens:
    side: str                 # 'source' or 'target'
    vertex: tuple             # flat-side vertex (towards the Port)
    axis: tuple               # unit vector from the Port into the relay
    thickness: float
    index: float              # relative to the ambient medium
    curvature: float          # curved side, sag along `axis` measured from the flat side outwards
    conic: float = 0.0
    aspheric: tuple = (0.0, 0.0)
    radius: float = 1e-3
    focal_length: float = 0.0
    port_distance: float = 0.0
    material: dict = field(default_factory=dict)

    @property
    def curved_vertex(self):
        return add(self.vertex, mul(self.axis, self.thickness))

    def surfaces(self, forward=True):
        """Refracting surfaces in propagation order (forward = Source → Target)."""
        flat = (self.vertex, 0.0, 0.0, ())
        curved = (self.curved_vertex, self.curvature, self.conic, self.aspheric)
        if self.side == 'source':
            order = [(flat, 1.0, self.index), (curved, self.index, 1.0)]
            axis = self.axis
        else:  # target lens: light meets the curved side first, travelling against `axis`
            order = [(curved, 1.0, self.index), (flat, self.index, 1.0)]
            axis = mul(self.axis, -1.0)
        out = []
        for (vertex, c, kappa, asph), n1, n2 in order:
            sign = 1.0 if self.side == 'source' else -1.0  # sag along the forward axis
            out.append(nonparaxial.refracting_surface(vertex, axis, sign * c, kappa, tuple(sign * a for a in asph),
                                                      n1, n2, self.radius))
        return out


def _reduced_matrix(lens):
    """Port-side reduced ray matrix of the lens from the flat vertex to the curved vertex."""
    n0, nl = 1.0, lens.index
    flat = np.eye(2)
    inside = np.array([[1.0, lens.thickness / nl], [0.0, 1.0]])
    curved = np.array([[1.0, 0.0], [-(n0 - nl) * lens.curvature, 1.0]])
    return curved @ inside @ flat


def transform(q, lens):
    """Port q (physical, ambient) at the flat vertex → q just after the curved vertex (ambient)."""
    (a, b), (c, d) = _reduced_matrix(lens)
    return (a * q + b) / (c * q + d)


def design(port, theta_out, lens_index, side='source', label='Micro-lens'):
    """Paraxial plano-convex converter for one Port (`port` from external.adapt_ports, ambient medium)."""
    mode = port.mode
    lam_m = mode.wavelength / mode.index
    w0 = min(p['waist_radius_m'] for p in mode.parameters())
    w_out = lam_m / (math.pi * theta_out)
    f = math.pi * w0 * w_out / lam_m
    n_rel = lens_index / mode.index
    t = THICKNESS_FRACTION * f
    d = f - t / n_rel
    if d <= 0:
        raise DomainError('lens too thick for its focal length')
    curvature = 1.0 / (f * (1.0 - n_rel))
    axis = port.direction if side == 'source' else mul(port.direction, -1.0)
    vertex = add(port.position, mul(axis, d))
    lens = Lens(side, vertex, unit(axis), t, n_rel, curvature, focal_length=f, port_distance=d)
    q_end = equivalent_q(port, lens)
    widest = max(math.sqrt(-lam_m / (math.pi * (1 / q).imag)) for q in q_end)
    lens.radius = APERTURE_MARGIN * math.sqrt(math.log(1e6) / 2) * widest
    lens.material = {'relative_index': n_rel}
    return lens


def equivalent_q(port, lens):
    """Per-axis q just after the lens, for the beam leaving the Port (target side: time-reversed)."""
    qs = port.mode.q
    if lens.side == 'target':
        qs = tuple(-q.conjugate() for q in qs)
    return tuple(transform(q + lens.port_distance, lens) for q in qs)


def equivalent_port_record(port, lens, wavelength, name):
    """Engine (M3A-1) Port record of the beam just after the lens (target side: just before it)."""
    from .design_document import _record
    qs = equivalent_q(port, lens)
    if lens.side == 'target':
        qs = tuple(-q.conjugate() for q in qs)
    g = Gaussian(*qs, port.mode.wavelength, port.mode.index)
    params = g.parameters()
    position = list(lens.curved_vertex)
    direction = list(port.direction)
    ev = {'provenance': 'assumed', 'source': f'Equivalent {name} Port after a designed plano-convex micro-lens '
                                             f'(EFL {lens.focal_length * 1e6:.2f} µm, paraxial reduced ray matrix)'}
    return {
        'position_m': _record(position, 'm', ev),
        'propagation_direction': _record(direction, '1', ev),
        'sagittal_axis': _record(list(port.sagittal), '1', ev),
        'reference_plane': _record({'id': f'{name}-lens', 'frame_id': 'world', 'side': 'external',
                                    'origin_m': position, 'normal': direction}, 'plane', ev),
        'polarization': _record({'treatment': 'scalar_ignored'}, '1', {'provenance': 'assumed', 'source': 'Scalar model'}),
        'mode_evidence': _record({'kind': 'gaussian_assumption', 'label': f'{name} after lens'}, 'evidence', ev),
        'mfd_ts_m': _record([2 * p['radius_m'] for p in params], 'm', ev),
        'wavefront_curvature_ts_per_m': _record([p['curvature_per_m'] for p in params], 'm^-1', ev),
    }


def collimator_profile(lens, samples=200):
    """Exact equal-path (Cartesian-oval) curved surface that collimates rays from the Port point.

    A ray leaving the Port at angle α meets the flat face at r₀ = d tan α, refracts to β (sin α = n sin β)
    and reaches the curved face at depth z behind the flat face, where equal optical path to a plane
    after the lens gives z = (d + (n − 1)t − d/cos α) / (n/cos β − 1) and r = r₀ + z tan β.
    Returns (r, sag relative to the curved vertex), out to the clear radius.
    """
    n, d, t = lens.index, lens.port_distance, lens.thickness
    rows = []
    for alpha in np.linspace(0, math.pi / 2 * 0.95, 4000):
        beta = math.asin(math.sin(alpha) / n)
        z = (d + (n - 1) * t - d / math.cos(alpha)) / (n / math.cos(beta) - 1)
        r = d * math.tan(alpha) + z * math.tan(beta)
        if z <= 0 or r > lens.radius:
            break
        rows.append((r, z - t))
    rows = np.array(rows)
    pick = np.linspace(0, len(rows) - 1, min(samples, len(rows))).astype(int)
    return rows[pick, 0], rows[pick, 1]


def fit_collimator(lens):
    """Conic and r⁴…r¹⁰ terms (curvature fixed by the paraxial design) fitted to the exact collimator profile."""
    from scipy.optimize import least_squares
    r, z = collimator_profile(lens)
    scale = max(r.max(), 1e-12)

    def residual(x):
        sag, _ = nonparaxial.asphere_sag(r * r, lens.curvature, x[0], tuple(a / scale ** (2 * i + 1) for i, a in enumerate(x[1:], start=1)))
        return (sag - z) / scale
    run = least_squares(residual, [-lens.index ** 2, 0, 0, 0, 0], method='lm')
    lens.conic = float(run.x[0])
    lens.aspheric = tuple(float(a / scale ** (2 * i + 1)) for i, a in enumerate(run.x[1:], start=1))
    return float(np.abs(residual(run.x)).max() * scale)


def far_zone_ratio(port, lens):
    """Port-to-lens distance in Rayleigh ranges (the ray mapping needs the lens in the Port's far zone)."""
    return lens.port_distance / min(p['rayleigh_range_m'] for p in port.mode.parameters())


def system_args(ports):
    from .qtensor import port_beam
    q_s, a_s = port_beam(ports.source)
    q_t, a_t = port_beam(ports.target)
    k = 2 * math.pi * ports.source.mode.index / ports.source.mode.wavelength
    angle = max(p['divergence_rad'] for port in (ports.source, ports.target) for p in port.mode.parameters())
    return (np.linalg.inv(q_s), a_s, ports.source.position, ports.source.direction, np.linalg.inv(q_t), a_t,
            ports.target.position, ports.target.direction, k, angle)


def fit_system(ports, lenses, mirror_tuples, footprints):
    """Lens aspheres and reflector sag terms that maximise the non-paraxial overlap of the whole relay.

    Valid because both ends are true Port waists (point-like emitter and focus in the far zone of
    the lens and reflectors). Alternates: lens conic + r⁴, r⁶ (Nelder–Mead on the exact overlap), then
    the reflector correction of freeform.correct with the lenses fixed, then the lenses again.
    """
    from . import freeform
    args = system_args(ports)
    wavelength = ports.source.mode.wavelength / ports.source.mode.index
    source_lens = [l for l in lenses if l.side == 'source']
    target_lens = [l for l in lenses if l.side == 'target']
    poly = [()] * len(mirror_tuples)

    def surfaces(poly_):
        prefix = [s for l in source_lens for s in l.surfaces()]
        suffix = [s for l in target_lens for s in l.surfaces()]
        middle = [nonparaxial.mirror_tuple(m[0], m[1], m[3], (m[4], m[5]), (m[6], m[7]), p) for m, p in zip(mirror_tuples, poly_)]
        return prefix, middle, suffix

    def eta(grid=LENS_FIT_GRID):
        prefix, middle, suffix = surfaces(poly)
        try:
            r = nonparaxial.overlap(*args[:8], [*prefix, *middle, *suffix], *args[8:], grid=grid)
        except DomainError:
            return 0.0
        ok = r['folded_power_fraction'] <= nonparaxial.FOLD_LIMIT and r['eta'] <= 1 + nonparaxial.CONVERGENCE_LIMIT
        return r['eta'] if ok and math.isfinite(r['eta']) else 0.0

    def fit_lenses():
        if not lenses:
            return
        def cost(x):
            for j, l in enumerate(lenses):
                rest = l.aspheric[2:] if len(l.aspheric) > 2 else ()
                l.conic, l.aspheric = x[3 * j], (x[3 * j + 1] / l.radius ** 3, x[3 * j + 2] / l.radius ** 5, *rest)
            return -eta()
        saved = [(l.conic, l.aspheric) for l in lenses]
        before = eta()
        start = [v for l in lenses for v in (l.conic, l.aspheric[0] * l.radius ** 3, l.aspheric[1] * l.radius ** 5)]
        best = minimize(cost, start, method='Nelder-Mead', options={'xatol': 1e-5, 'fatol': 1e-7, 'maxiter': 300})
        if -best.fun > before:
            cost(best.x)
        else:  # keep the higher-order collimator terms if the 3-term search does not improve
            for l, (kappa, asph) in zip(lenses, saved):
                l.conic, l.aspheric = kappa, asph

    history = [{'step': 'spherical lens, quadric reflectors', 'eta': eta()}]
    for l in lenses:  # start from the exact equal-path collimator, fitted as an even asphere
        fit_collimator(l)
    history.append({'step': 'equal-path collimator lens', 'eta': eta()})
    for round_ in range(2):
        fit_lenses()
        history.append({'step': f'lens asphere {round_ + 1}', 'eta': eta()})
        prefix, _, suffix = surfaces([()] * len(mirror_tuples))
        result = freeform.correct(args, mirror_tuples, footprints, wavelength, prefix=prefix, suffix=suffix)
        if result['check'].get('status') != 'Invalid':
            poly = result['poly']
        history.append({'step': f'reflector correction {round_ + 1}', 'eta': eta()})
    prefix, middle, suffix = surfaces(poly)
    check = nonparaxial.check(*args[:8], [*prefix, *middle, *suffix], *args[8:])
    return {'check': check, 'poly': poly, 'history': history}


def lens_family(engine_document, constraints, guard=0.1, options=LENS_EXPANSION_OPTIONS, cases=3):
    """Micro-lens + two-reflector relays for Ports beyond the divergence guard (accepted only non-paraxially)."""
    import copy
    from .external import adapt_ports
    from .search import APERTURE_FACTOR, design_continuous
    from .freeform import candidate_mirrors
    ports = adapt_ports(engine_document)
    sides = [side for side in ('source', 'target')
             if max(p['divergence_rad'] for p in getattr(ports, side).mode.parameters()) > guard]
    if not sides:
        return None
    lens_index = (engine_document.get('lens_index') or {}).get('value', 1.4468)
    runs = []
    for theta in options:
        try:
            lenses = [design(getattr(ports, side), theta, lens_index, side) for side in sides]
        except DomainError as exc:
            runs.append({'theta_out_rad': theta, 'status': 'Fail', 'reason': str(exc), 'candidates': []})
            continue
        equivalent = copy.deepcopy(engine_document)
        for l in lenses:
            equivalent[l.side] = equivalent_port_record(getattr(ports, l.side), l, ports.source.mode.wavelength, l.side)
        report = design_continuous(equivalent, constraints, include_map=False, nonparaxial_checks=False)
        rows = []
        for candidate in report['candidates'][:cases]:
            _, mirrors = candidate_mirrors(candidate, equivalent)
            tuples = [nonparaxial.mirror_tuple(m.vertex, m.normal, getattr(m, 'axis', None) or ports.source.sagittal,
                                               m.curvatures, m.half_aperture) for m in mirrors]
            footprints = [tuple(a / APERTURE_FACTOR for a in m.half_aperture) for m in mirrors]
            fitted = [copy.deepcopy(l) for l in lenses]
            try:
                fit = fit_system(ports, fitted, tuples, footprints)
            except DomainError as exc:
                rows.append({'id': candidate['id'], 'status': 'Fail', 'reason': str(exc)})
                continue
            rows.append({'id': candidate['id'], 'equivalent_candidate': candidate, 'status': fit['check']['status'],
                         'nonparaxial_check': fit['check'], 'fit_history': fit['history'],
                         'lenses': [lens_record(l, getattr(ports, l.side)) for l in fitted],
                         'reflector_terms': [[{'u_power': m, 'v_power': n, 'coefficient_si': c} for m, n, c in p] for p in fit['poly']]})
        runs.append({'theta_out_rad': theta, 'status': report['status'], 'reason': report.get('reason'),
                     'lenses': [lens_record(l, getattr(ports, l.side)) for l in lenses], 'candidates': rows})
    return {'status': 'Review', 'sides': sides, 'runs': runs,
            'meaning': ('Micro-lens converters bring the beyond-guard Ports inside the paraxial guard; the two-reflector '
                        'relay is designed between the equivalent Ports, then the whole relay (lens, reflectors, lens) '
                        'is fitted and accepted only by the non-paraxial check. Not yet counted as Computed candidates: '
                        'promoting this family is a policy decision for the user.')}


def lens_record(lens, port):
    return {'side': lens.side, 'flat_vertex_m': list(lens.vertex), 'axis': list(lens.axis),
            'curved_vertex_m': list(lens.curved_vertex), 'thickness_m': lens.thickness,
            'relative_index': lens.index, 'curvature_per_m': lens.curvature, 'conic': lens.conic,
            'aspheric_even_si': list(lens.aspheric), 'clear_radius_m': lens.radius,
            'focal_length_m': lens.focal_length, 'port_distance_m': lens.port_distance,
            'far_zone_rayleigh_ranges': far_zone_ratio(port, lens)}
