"""P4b alignment tolerance: simultaneous placement errors, passive assembly and active alignment.

Model. Every rigid body (a reflector, or a lens = its two refracting surfaces) has five placement DOFs:
three translations and two rotations (reflector: global X, Y, Z and about its two principal axes at the
vertex; lens: across its axis (two), along it, and tilts about the lens middle). The chief ray from the
Source Port is traced exactly (same tracer as the non-paraxial check) through the perturbed system; its
offset d and direction u at the Target plane are linear in the errors near the design (Jacobian J by
central differences). For a beam equal to the Target mode except for d and u, the Gaussian overlap is
exact: with field exp(−ik/2 xᵀQx),

    η(d, u) = exp(2 Re[¼ bᵀM⁻¹b − (ik/2) dᵀQd]),  M = −k Im Q,  b = ik(Qd + u),

so the loss in nepers is a quadratic form of the errors, L(δ) = δᵀ H δ with H = Jᵀ G J. Changes of beam size
and focus (second order in the errors) are not included; the single-error losses are checked against the
non-paraxial pose study.

Passive assembly: all DOFs drawn independently and uniformly within ± their tolerance (Monte Carlo, fixed seed).
Active alignment: the chosen compensator DOFs are set to the least-squares optimum for each sample, then a
post-bond shift (uniform within ± its tolerance) is added to them. Every body is tried as compensator
(translations, or rotations) and the one with the lowest 90th-percentile loss is reported first.
"""

import math

import numpy as np

from .gaussian import DomainError
from . import nonparaxial

TOLERANCE_DEFAULTS = {  # assumed (user editable in the Design Document `tolerances`); ± bounds
    'mirror_translation_um': 5.0, 'mirror_rotation_mrad': 1.0,
    'lens_translation_um': 1.0, 'lens_axial_um': 1.0, 'lens_rotation_mrad': 1.0,
    'bond_translation_um': 0.2, 'bond_rotation_mrad': 0.05,
}
ACTIVE_RANGE = {'translation': 50e-6, 'rotation': 20e-3}  # assumed stage travel; larger corrections are not practical
SAMPLES = 20000
SEED = 20261125
STEP_M = 1e-7
STEP_RAD = 1e-6
DOF_NAMES = ('t1', 't2', 't3', 'r1', 'r2')


def _rotate(v, axis, angle):
    v, k = np.asarray(v, float), np.asarray(axis, float)
    return v * math.cos(angle) + np.cross(k, v) * math.sin(angle) + k * (k @ v) * (1 - math.cos(angle))


def _unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


class Body:
    """A rigid group of element tuples with its five DOF axes."""

    def __init__(self, label, kind, elements, pivot, translations, rotations):
        self.label, self.kind, self.elements = label, kind, list(elements)
        self.pivot = np.asarray(pivot, float)
        self.translations = [_unit(t) for t in translations]
        self.rotations = [_unit(r) for r in rotations]

    def moved(self, dof, amount):
        if dof < 3:
            shift, axis, angle = self.translations[dof] * amount, None, 0.0
        else:
            shift, axis, angle = np.zeros(3), self.rotations[dof - 3], amount

        def point(p):
            p = np.asarray(p, float)
            if axis is not None:
                p = self.pivot + _rotate(p - self.pivot, axis, angle)
            return p + shift

        def vector(v):
            return _rotate(v, axis, angle) if axis is not None else np.asarray(v, float)
        out = []
        for e in self.elements:
            if isinstance(e[0], str) and e[0] == 'refract':
                out.append((e[0], point(e[1]), vector(e[2]), *e[3:]))
            else:
                out.append((point(e[0]), vector(e[1]), vector(e[2]), vector(e[3]), *e[4:]))
        return out


def mirror_body(label, element):
    vertex, normal, e1, e2 = element[:4]
    return Body(label, 'mirror', [element], vertex, np.eye(3), (e1, e2))


def lens_body(label, surfaces):
    first, second = surfaces
    axis = _unit(np.asarray(second[1]) - np.asarray(first[1]))
    side = np.array([0.0, 0.0, 1.0]) if abs(axis[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    side = _unit(side - (side @ axis) * axis)
    other = np.cross(axis, side)
    middle = (np.asarray(first[1]) + np.asarray(second[1])) / 2
    return Body(label, 'lens', surfaces, middle, (side, other, axis), (side, other))


def gaussian_loss(Q, k):
    """Quadratic form G (4×4, nepers) of the overlap loss in e = (d_t, d_s, u_t, u_s) for Target mode Q."""
    M = -k * Q.imag
    Minv = np.linalg.inv(M)

    def nepers(e):
        d, u = np.asarray(e[:2], float), np.asarray(e[2:], float)
        b = 1j * k * (Q @ d + u)
        return -2 * (0.25 * b @ Minv @ b - 0.5j * k * d @ Q @ d).real
    G = np.zeros((4, 4))
    basis = np.eye(4)
    for i in range(4):
        G[i, i] = nepers(basis[i])
    for i in range(4):
        for j in range(i + 1, 4):
            G[i, j] = G[j, i] = 0.5 * (nepers(basis[i] + basis[j]) - G[i, i] - G[j, j])
    return G


class System:
    """Chief-ray model of one candidate: ordered element tuples grouped in bodies."""

    def __init__(self, args, bodies):
        # args: nonparaxial argument tuple (q_s, a_s, p_s, d_s, q_t, a_t, p_t, d_t, k, angle) without elements
        self.args, self.bodies = args, bodies
        self.k = args[8]
        self.G = gaussian_loss(np.linalg.inv(args[4]), self.k)  # args carry q (the inverse of Q)

    def elements(self, replace=None):
        out = []
        for index, body in enumerate(self.bodies):
            out += replace[1] if replace is not None and replace[0] == index else body.elements
        return out

    def chief(self, elements):
        q_s, a_s, p_s, d_s, q_t, a_t, p_t, d_t = self.args[:8]
        ray = nonparaxial.trace_bundle(np.asarray(p_s, float), np.asarray(d_s, float)[None, :], elements,
                                       np.asarray(p_t, float), a_t, np.asarray(d_t, float))
        if not ray['alive'][0]:
            raise DomainError('chief ray lost in the alignment study')
        return np.concatenate([ray['x'][0], ray['u'][0]])

    def jacobian(self):
        nominal = self.chief(self.elements())
        columns, names = [], []
        for index, body in enumerate(self.bodies):
            for dof in range(5):
                step = STEP_M if dof < 3 else STEP_RAD
                plus = self.chief(self.elements((index, body.moved(dof, step))))
                minus = self.chief(self.elements((index, body.moved(dof, -step))))
                columns.append((plus - minus) / (2 * step))
                names.append((body.label, DOF_NAMES[dof]))
        return nominal, np.array(columns).T, names


def bounds(bodies, tolerances):
    out = []
    for body in bodies:
        if body.kind == 'mirror':
            t, r = tolerances['mirror_translation_um'] * 1e-6, tolerances['mirror_rotation_mrad'] * 1e-3
            out += [t, t, t, r, r]
        else:
            t, a, r = (tolerances['lens_translation_um'] * 1e-6, tolerances['lens_axial_um'] * 1e-6,
                       tolerances['lens_rotation_mrad'] * 1e-3)
            out += [t, t, a, r, r]
    return np.array(out)


def _stats(nepers):
    db = 10 / math.log(10) * nepers
    return {'median_db': float(np.median(db)), 'p90_db': float(np.percentile(db, 90)),
            'p99_db': float(np.percentile(db, 99)), 'yield_1db': float(np.mean(db <= 1.0)),
            'yield_0p5db': float(np.mean(db <= 0.5))}


def study(system, tolerances=None, samples=SAMPLES):
    tolerances = {**TOLERANCE_DEFAULTS, **(tolerances or {})}
    nominal, J, names = system.jacobian()
    H = J.T @ system.G @ J
    limit = bounds(system.bodies, tolerances)
    rng = np.random.default_rng(SEED)
    errors = rng.uniform(-1, 1, (samples, len(limit))) * limit
    passive = np.einsum('ni,ij,nj->n', errors, H, errors)
    single = []  # loss of each DOF alone at its tolerance (linear model)
    for i, (label, dof) in enumerate(names):
        single.append({'body': label, 'dof': dof, 'tolerance': float(limit[i] * (1e6 if dof.startswith('t') else 1e3)),
                       'unit': 'um' if dof.startswith('t') else 'mrad',
                       'loss_db': float(10 / math.log(10) * H[i, i] * limit[i] ** 2)})
    options = []
    for b, body in enumerate(system.bodies):
        for group, picks in (('translation', (0, 1, 2)), ('rotation', (3, 4))):
            idx = [5 * b + p for p in picks]
            P = H[np.ix_(idx, idx)]
            if not np.any(np.diag(P) > 0):
                continue
            # least-squares compensation: c* = −P⁺ H[idx, :] δ (the compensator's own error is overwritten;
            # a DOF without effect, e.g. lens axial shift in this model, gets no correction)
            others = errors.copy()
            others[:, idx] = 0.0
            c = -(np.linalg.pinv(P, rcond=1e-9) @ (H[idx, :] @ others.T)).T
            bond = np.array([tolerances['bond_translation_um'] * 1e-6 if p < 3 else tolerances['bond_rotation_mrad'] * 1e-3
                             for p in picks])
            after = others.copy()
            after[:, idx] = c + rng.uniform(-1, 1, c.shape) * bond
            residual = np.einsum('ni,ij,nj->n', after, H, after)
            travel = np.abs(c).max(axis=0)
            options.append({'body': body.label, 'kind': body.kind, 'dofs': group, **_stats(residual),
                            'max_travel': [float(v * (1e6 if group == 'translation' else 1e3)) for v in travel],
                            'travel_unit': 'um' if group == 'translation' else 'mrad',
                            'practical': bool(travel.max() <= ACTIVE_RANGE[group])})
    options.sort(key=lambda o: (not o['practical'], o['p90_db']))
    return {'model': 'chief-ray Jacobian + exact Gaussian offset/tilt overlap (focus and size changes not included)',
            'samples': samples, 'seed': SEED, 'distribution': 'uniform within ± tolerance, independent',
            'tolerances': tolerances, 'passive': _stats(passive), 'single': single,
            'active': options[:6], 'best_compensator': options[0] if options and options[0]['practical'] else None,
            'active_range': {'translation_um': ACTIVE_RANGE['translation'] * 1e6, 'rotation_mrad': ACTIVE_RANGE['rotation'] * 1e3},
            'nominal_chief_offset_um': [float(v * 1e6) for v in nominal[:2]],
            'nominal_chief_tilt_mrad': [float(v * 1e3) for v in nominal[2:]]}


def loss_db(system, errors):
    """Linear-model loss [dB] of one error vector (DOF order of `system.jacobian`)."""
    _, J, _ = system.jacobian()
    e = J @ np.asarray(errors, float)
    return 10 / math.log(10) * float(e @ system.G @ e)


def mirror_system(candidate, engine_document, freeform_record=None):
    """System of a two-reflector candidate (corrected surfaces when the P4 correction was computed)."""
    from .freeform import candidate_mirrors
    from .lens import system_args
    ports, mirrors = candidate_mirrors(candidate, engine_document)
    polys = [()] * len(mirrors)
    if freeform_record and freeform_record.get('status') == 'Computed' and not freeform_record.get('constraint'):
        polys = [tuple((t['u_power'], t['v_power'], t['coefficient_si']) for t in r['terms'])
                 for r in freeform_record['reflectors']]
    tuples = [nonparaxial.mirror_tuple(m.vertex, m.normal, getattr(m, 'axis', None) or ports.source.sagittal,
                                       m.curvatures, m.half_aperture, poly) for m, poly in zip(mirrors, polys)]
    return System(system_args(ports), [mirror_body(f'M{i + 1}', t) for i, t in enumerate(tuples)])


def lens_system(args, lenses, mirror_elements):
    bodies = [lens_body('L1', l.surfaces()) for l in lenses if l.side == 'source']
    bodies += [mirror_body(f'M{i + 1}', m) for i, m in enumerate(mirror_elements)]
    bodies += [lens_body('L2', l.surfaces()) for l in lenses if l.side == 'target']
    return System(args, bodies)
