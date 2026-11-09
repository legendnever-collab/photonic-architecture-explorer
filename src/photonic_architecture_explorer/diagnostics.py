"""Bounded exact-ray diagnostics for local quadratic patches; no field efficiency."""

import math
from dataclasses import replace
from .gaussian import DomainError, finite
from .geometry import (add, sub, mul, dot, norm, unit, cross, frame, to_local,
                       reflect, patch_intersections)
from .benchmark import load_case
from .solver import evaluate, MIN_COSINE


def ray_to_target(origin, direction, target, mirrors, sagittal):
    """Forward intersections with actual patches; normal evaluated at each hit."""
    if len(mirrors) != 2:
        raise DomainError('exactly two reflectors required')
    origin, direction, sagittal = tuple(origin), unit(direction), unit(sagittal)
    finite(*origin)
    if any(abs(dot(sagittal, m.normal)) > 1e-10 for m in mirrors):
        raise DomainError('patch sagittal axis must be transverse to its normal')
    hits = []
    for index, mirror in enumerate(mirrors):
        roots = [r for r in patch_intersections(origin, direction, mirror, sagittal) if r > 1e-9]
        if not roots:
            raise DomainError(f'M{index+1}: no forward aperture hit')
        distance = min(roots)
        other = mirrors[1-index]
        other_roots = patch_intersections(origin, direction, other, sagittal)
        if any(1e-9 < r < distance-1e-9 for r in other_roots):
            raise DomainError('unintended reflector interception')
        hit = add(origin, mul(direction, distance))
        tangent = unit(cross(sagittal, mirror.normal))
        u, v, h = to_local(sub(hit, mirror.vertex), (tangent, sagittal, mirror.normal))
        kt, ks = mirror.curvatures
        normal = unit(sub(sub(mirror.normal, mul(tangent, kt*u)), mul(sagittal, ks*v)))
        cosine = -dot(direction, normal)
        if cosine < MIN_COSINE:
            raise DomainError('local incidence is back-facing or exceeds 70 degrees')
        outgoing = reflect(direction, normal)
        hits.append(dict(position_m=hit, incoming=direction, outgoing=outgoing,
                         normal=normal, surface_residual_m=h-(kt*u*u+ks*v*v)/2))
        origin, direction = hit, outgoing
    den = dot(direction, target.direction)
    if den <= 0:
        raise DomainError('ray does not propagate toward Target plane')
    distance = dot(sub(target.position, origin), target.direction)/den
    if distance <= 1e-9:
        raise DomainError('Target plane is not forward')
    for mirror in mirrors:
        if any(1e-9 < r < distance-1e-9 for r in patch_intersections(origin, direction, mirror, sagittal)):
            raise DomainError('unintended interception before Target')
    point = add(origin, mul(direction, distance))
    basis = frame(target.direction, target.sagittal)
    offset = to_local(sub(point, target.position), basis)[:2]
    slope = tuple(dot(direction, axis)/den for axis in basis[:2])
    return dict(status='Pass', target_offset_m=offset, target_slope=slope, hits=hits)


def linear_reference(height, slope, source, target, mirrors):
    """M1 vertex paraxial ray relay, including physical reflection parity.

    Input is in the first mirror's incident transverse reference plane.
    """
    d = source.direction
    h, a = list(height), list(slope)
    for index, mirror in enumerate(mirrors):
        powers = mirror.powers(-dot(d, mirror.normal))
        a = [v-p*x for v, p, x in zip(a, powers, h)]
        h[0], a[0] = -h[0], -a[0]
        d = reflect(d, mirror.normal)
        length = norm(sub(mirrors[1].vertex, mirror.vertex)) if index == 0 else norm(sub(target.position, mirror.vertex))
        h = [x+length*v for x, v in zip(h, a)]
    return h, a


def finite_fan(source, target, mirrors, extent):
    finite(extent)
    if not 0 < extent <= 2:
        raise DomainError('diagnostic extent must be in (0,2] beam radii')
    nominal = evaluate(source, target, mirrors)
    if nominal['model_domain']['status'] != 'Pass':
        return dict(status='Fail', reason='nominal design fails M1 model domain', mode_overlap=None)
    length = norm(sub(mirrors[0].vertex, source.position))
    beam = source.mode.propagate(length)
    parameters = beam.parameters()
    basis = frame(source.direction, source.sagittal)
    residuals, angles, failures = [], [], []
    for i in (-extent, 0., extent):
        for j in (-extent, 0., extent):
            height = [scale*p['radius_m'] for scale, p in zip((i, j), parameters)]
            slope = [h*p['curvature_per_m'] for h, p in zip(height, parameters)]
            point = add(mirrors[0].vertex, add(mul(basis[0], height[0]), mul(basis[1], height[1])))
            direction = unit(add(source.direction, add(mul(basis[0], slope[0]), mul(basis[1], slope[1]))))
            # Start safely upstream along the same straight ray; no negative propagation.
            origin = sub(point, mul(direction, length/4))
            try:
                exact = ray_to_target(origin, direction, target, mirrors, source.sagittal)
                linear_h, linear_a = linear_reference(height, slope, source, target, mirrors)
                residuals.append(math.hypot(*(x-y for x, y in zip(exact['target_offset_m'], linear_h))))
                angles.append(math.hypot(*(x-y for x, y in zip(exact['target_slope'], linear_a))))
            except DomainError as exc:
                failures.append(str(exc))
    return dict(status='Fail' if failures else 'Pass', extent_beam_radii=extent,
                attempted_rays=9, traced_rays=len(residuals), failures=failures,
                max_transverse_residual_m=max(residuals, default=None),
                rms_transverse_residual_m=math.sqrt(sum(x*x for x in residuals)/len(residuals)) if residuals else None,
                max_slope_residual=max(angles, default=None),
                scope='uniform wavefront-normal fan, not Gaussian power or field overlap',
                mode_overlap=None)


def run(fixture):
    source, target, mirrors = load_case(fixture)
    frozen_ports = repr((source, target))
    curvature_cases = []
    for mirror_index in range(2):
        for axis in range(2):
            for fraction in (-.01, .01):
                changed = list(mirrors)
                curvatures = list(mirrors[mirror_index].curvatures)
                curvatures[axis] *= 1+fraction
                changed[mirror_index] = replace(mirrors[mirror_index], curvatures=curvatures)
                result = evaluate(source, target, changed)
                curvature_cases.append(dict(mirror=mirror_index+1, axis='ts'[axis], fraction=fraction,
                                            geometry=result['geometry']['status'], domain=result['model_domain']['status'],
                                            mode_matching=result['gaussian_mode_matching']))
    placement_cases = []
    for mirror_index in range(2):
        for axis in range(3):
            for delta in (-5e-6, 5e-6):
                changed = list(mirrors)
                vertex = list(mirrors[mirror_index].vertex)
                vertex[axis] += delta
                changed[mirror_index] = replace(mirrors[mirror_index], vertex=vertex)
                try:
                    ray = ray_to_target(source.position, source.direction, target, changed, source.sagittal)
                    miss = math.hypot(*ray['target_offset_m'])
                    slope = math.hypot(*ray['target_slope'])
                    geometric = dict(status='Pass', target_miss_m=miss, target_slope_norm=slope,
                                     target_closure='Pass' if miss < 1e-10 and slope < 1e-10 else 'Fail',
                                     target_offset_m=ray['target_offset_m'], target_slope=ray['target_slope'])
                except DomainError as exc:
                    geometric = dict(status='Fail', reason=str(exc))
                placement_cases.append(dict(mirror=mirror_index+1, axis='XYZ'[axis], delta_m=delta,
                                            geometry=geometric, gaussian_mode_matching={'status': 'Uncomputed',
                                            'reason': 'off-vertex Gaussian handoff not validated'}))
    fans = {case: [finite_fan(*load_case(fixture, case), extent) for extent in (.5, 1., 2.)]
            for case in ('flat', 'curved')}
    assert frozen_ports == repr((source, target))
    return dict(benchmark_id='M2-001', actual_ssc_applicability={'status': 'Uncomputed',
                'reason': 'actual external Port specification not supplied'},
                curvature_cases=curvature_cases, placement_cases=placement_cases,
                finite_fans=fans, total_coupling={'status': 'Uncomputed'},
                fabrication={'status': 'Uncomputed'})
