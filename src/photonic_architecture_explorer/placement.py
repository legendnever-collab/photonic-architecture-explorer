"""One-at-a-time pose errors on a frozen, two-reflector nominal prescription."""

from dataclasses import replace
import math

from .diagnostics import ray_to_target
from .external import adapt_external
from .gaussian import DomainError
from .geometry import add, cross, mul, norm, sub

TRANSLATION_M = 5e-6
ROTATION_RAD = 1e-3
CASES_PER_CANDIDATE = 16
NOMINAL_ATOL = 1e-10


def rotate_in_plane(mirror, sagittal, angle):
    normal = add(mul(mirror.normal, math.cos(angle)),
                 mul(cross(sagittal, mirror.normal), math.sin(angle)))
    return replace(mirror, normal=normal)


def trace_placement(source, target, mirrors):
    try:
        ray = ray_to_target(source.position, source.direction, target, mirrors, source.sagittal)
    except DomainError as exc:
        return {'status': 'Fail', 'failure': getattr(exc, 'code', 'invalid_geometry'), 'reason': str(exc)}

    for key in ('target_offset_m', 'target_slope', 'target_point_m', 'target_ray_direction'):
        ray[key] = list(ray[key])
    for hit in ray['hits']:
        for key in ('position_m', 'incoming', 'outgoing', 'normal'):
            hit[key] = list(hit[key])
    slope = ray['target_slope']
    ray.update(status='Computed',
               target_angular_error_rad=[math.atan(x) for x in slope],
               target_angle_rad=math.atan(math.hypot(*slope)),
               target_miss_m=math.hypot(*ray['target_offset_m']))
    return ray


def reflector_poses(mirrors, sagittal):
    """Generate the frozen one-reflector-at-a-time placement cases."""
    for index, mirror in enumerate(mirrors):
        for axis, label in enumerate('XYZ'):
            for delta in (-TRANSLATION_M, TRANSLATION_M):
                vertex = list(mirror.vertex)
                vertex[axis] += delta
                changed = list(mirrors)
                changed[index] = replace(mirror, vertex=vertex)
                yield {'kind': 'translation', 'mirror': index + 1, 'axis': label,
                       'delta_m': delta}, changed
        for angle in (-ROTATION_RAD, ROTATION_RAD):
            changed = list(mirrors)
            changed[index] = rotate_in_plane(mirror, sagittal, angle)
            yield {'kind': 'rotation', 'mirror': index + 1, 'axis': 's',
                   'delta_rad': angle}, changed


def placement_cases(source, target, mirrors):
    nominal = trace_placement(source, target, mirrors)
    if nominal['status'] == 'Computed' and (
        nominal['target_miss_m'] > NOMINAL_ATOL
        or math.hypot(*nominal['target_slope']) > NOMINAL_ATOL
        or any(norm(sub(h['position_m'], m.vertex)) > NOMINAL_ATOL
               for h, m in zip(nominal['hits'], mirrors))
    ):
        nominal = {'status': 'Fail', 'failure': 'nominal_closure',
                   'reason': 'Nominal ray did not close at both vertices and fixed Target'}
    if nominal['status'] == 'Fail':
        return {'status': 'Fail', 'nominal': nominal, 'cases': [], 'summary': {}}

    cases = [{**pose, **trace_placement(source, target, changed)}
             for pose, changed in reflector_poses(mirrors, source.sagittal)]

    summaries = {}
    for kind in ('translation', 'rotation'):
        group = [case for case in cases if case['kind'] == kind]
        traced = [case for case in group if case['status'] == 'Computed']
        summaries[kind] = {'computed': len(traced), 'failed': len(group) - len(traced),
                           'max_target_miss_m': max((c['target_miss_m'] for c in traced), default=None),
                           'max_target_angle_rad': max((c['target_angle_rad'] for c in traced), default=None)}
    status = 'Fail' if any(case['status'] == 'Fail' for case in cases) else 'Computed'
    return {'status': status, 'nominal': nominal, 'cases': cases, 'summary': summaries}


def compare_placement(result):
    """Evaluate only displayed concepts, in the existing recommendation order."""
    candidates = []
    for candidate in result['candidates']:
        design = adapt_external(candidate['prescription'])
        candidates.append({'candidate_id': candidate['id'],
                           **placement_cases(design.source, design.target, design.reflectors)})
    status = 'Uncomputed'
    if candidates:
        status = 'Fail' if any(row['status'] == 'Fail' for row in candidates) else 'Computed'
    return {
        'status': status,
        'input_sha256': result.get('input_sha256'),
        'recommended_candidate_id': result['selected_candidate_id'],
        'target_reference_plane': (result['input_snapshot']['target']['reference_plane']['value']
                                   if candidates else None),
        'translation_m': TRANSLATION_M, 'rotation_rad': ROTATION_RAD,
        'case_budget_per_candidate': CASES_PER_CANDIDATE,
        'perturbed_gaussian_mode_overlap': 'Uncomputed',
        'actual_assembly_tolerance': 'Uncomputed',
        'package_yield': 'Uncomputed', 'total_coupling': 'Uncomputed',
        'patentability': 'Uncomputed',
        'candidates': candidates,
    }
