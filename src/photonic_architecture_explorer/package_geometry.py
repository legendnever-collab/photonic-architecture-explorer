"""Bounded world-AABB checks, never a full optical/mechanical clearance claim."""

import math
from .geometry import cross, dot, unit


def patch_world_aabb(mirror, sagittal):
    """Exact coordinate extrema of existing rectangular quadratic patch.

    Each world coordinate is a sum of two independent 1D quadratics. Checking
    endpoints and their interior stationary points bounds the WHOLE surface.
    """
    tangent = unit(cross(sagittal, mirror.normal))
    lows, highs = [], []
    for i in range(3):
        lo = hi = mirror.vertex[i]
        for linear, curvature, aperture in zip((tangent[i], sagittal[i]), mirror.curvatures, mirror.half_aperture):
            quadratic = mirror.normal[i]*curvature/2
            samples = [linear*x+quadratic*x*x for x in (-aperture, aperture)]
            if quadratic != 0:
                x = -linear/(2*quadratic)
                if -aperture <= x <= aperture:
                    samples.append(linear*x+quadratic*x*x)
            lo += min(samples); hi += max(samples)
        lows.append(lo); highs.append(hi)
    return (tuple(lows), tuple(highs))


def box_distance(a, b):
    return math.hypot(*(max(bl-ah, al-bh, 0.) for al, ah, bl, bh in zip(a[0], a[1], b[0], b[1])))


def segment_hits_box(start, end, box):
    lower, upper = 0., 1.
    for x, y, lo, hi in zip(start, end, box[0], box[1]):
        if y == x:
            if not lo <= x <= hi: return False
        else:
            a, b = sorted(((lo-x)/(y-x), (hi-x)/(y-x)))
            lower, upper = max(lower, a), min(upper, b)
            if lower > upper: return False
    return True


def assess_package(document, adapted, read, issue):
    checks = []

    def stop(status, label, reason):
        raise issue(status, label, reason)

    def box(value, label):
        if not isinstance(value, dict): stop('Fail', label, 'explicit solid object required')
        if value.get('type') != 'aabb': stop('Uncomputed', label, 'only world AABB solids supported')
        if set(value)-{'type', 'min_m', 'max_m', 'frame_id'}:
            stop('Uncomputed', label, 'unsupported AABB transform/extra solid fields')
        if 'frame_id' in value and value['frame_id'] != adapted.frame_id:
            stop('Fail', label, 'solid frame mismatch; transforms unsupported')
        coords = []
        for name in ('min_m', 'max_m'):
            row = value.get(name)
            if not isinstance(row, list) or len(row) != 3:
                stop('Fail', label, 'min_m/max_m must be 3-vectors in metres')
            if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in row):
                stop('Fail', label, 'finite box coordinates required')
            coords.append(tuple(row))
        if any(lo >= hi for lo, hi in zip(*coords)):
            stop('Fail', label, 'positive box extents required')
        return tuple(coords)

    def attempt(label, fn):
        try:
            value = fn()
            checks.append({'path': label, 'status': 'Pass'})
            return value
        except issue as exc:
            checks.append({'path': exc.path, 'status': exc.status, 'reason': exc.reason})
            return None

    package = document.get('package')
    if isinstance(package, dict) and set(package)-{'frame_id', 'available_volume', 'required_clearance_m', 'keepout_bodies'}:
        checks.append({'path': 'package', 'status': 'Uncomputed', 'reason': 'unsupported package fields'})
    frame = attempt('package.frame_id', lambda: read(package, 'frame_id', 'frame', 'package'))
    frame_ok = frame == adapted.frame_id
    if frame is not None and not frame_ok:
        checks.append({'path': 'package.frame_id', 'status': 'Fail', 'reason': 'package and Port frames differ'})
    volume = attempt('package.available_volume', lambda: box(read(package, 'available_volume', 'volume', 'package'), 'package.available_volume'))
    clearance = attempt('package.required_clearance_m', lambda: read(package, 'required_clearance_m', 'clearance', 'package'))
    if clearance is not None and (isinstance(clearance, bool) or not isinstance(clearance, (int, float)) or not math.isfinite(clearance) or clearance < 0):
        checks.append({'path': 'package.required_clearance_m', 'status': 'Fail', 'reason': 'finite nonnegative clearance required'})
        clearance = None
    keepout_values = attempt('package.keepout_bodies', lambda: read(package, 'keepout_bodies', 'keepouts', 'package'))
    keepouts = []
    if keepout_values is not None:
        if not isinstance(keepout_values, list):
            checks.append({'path': 'package.keepout_bodies', 'status': 'Fail', 'reason': 'explicit solid list required'})
        else:
            for j, value in enumerate(keepout_values):
                label = f'package.keepout_bodies[{j}]'
                item = attempt(label, lambda value=value, label=label: box(value, label))
                if item is not None: keepouts.append(item)
    bodies = []
    for j, node in enumerate(document['reflectors']):
        label = f'reflectors[{j}].body_envelope'
        bodies.append(attempt(label, lambda node=node, j=j, label=label:
                              box(read(node, 'body_envelope', 'body', f'reflectors[{j}]'), label)))

    def condition(label, passed, reason):
        checks.append({'path': label, 'status': 'Pass' if passed else 'Fail', 'reason': reason})

    def contains(outer, inner, margin=0.):
        return all(lo+margin <= il and ih <= hi-margin for lo, hi, il, ih in zip(outer[0], outer[1], inner[0], inner[1]))

    # Without a declared common package frame, comparisons have no meaning.
    if frame_ok:
        for j, (mirror, body) in enumerate(zip(adapted.reflectors, bodies)):
            if abs(dot(adapted.source.sagittal, mirror.normal)) > 1e-10:
                checks.append({'path': f'patch[{j}]', 'status': 'Uncomputed', 'reason': 'unsupported patch orientation'})
                continue
            patch = patch_world_aabb(mirror, adapted.source.sagittal)
            if volume is not None:
                condition(f'patch[{j}].volume', contains(volume, patch), 'entire quadratic patch extent')
            if body is not None:
                condition(f'body[{j}].patch', contains(body, patch), 'declared total envelope must enclose entire surface')
                if volume is not None and clearance is not None:
                    condition(f'body[{j}].volume', contains(volume, body, clearance), 'total envelope plus boundary clearance')
                for k, keepout in enumerate(keepouts):
                    gap = box_distance(body, keepout)
                    if clearance is not None:
                        condition(f'body[{j}].keepout[{k}]', gap > 0 and gap >= clearance, 'envelope Euclidean clearance; closed contact rejected')
        points = [adapted.source.position, *(m.vertex for m in adapted.reflectors), adapted.target.position]
        if volume is not None:
            for j, point in enumerate(points):
                condition(f'path_point[{j}].volume', contains(volume, (point, point)), 'chief path points only')
        for j, (start, end) in enumerate(zip(points, points[1:])):
            for k, keepout in enumerate(keepouts):
                condition(f'chief_segment[{j}].keepout[{k}]', not segment_hits_box(start, end, keepout), 'centreline intersection only; no finite-beam clearance')
        if all(b is not None for b in bodies) and clearance is not None:
            gap = box_distance(*bodies)
            condition('reflector_envelope_pair', gap > 0 and gap >= clearance, 'envelope separation, not actual-solid distance')
    status = 'Fail' if any(c['status'] == 'Fail' for c in checks) else (
        'Uncomputed' if any(c['status'] == 'Uncomputed' for c in checks) else 'Pass')
    return {'status': 'Fail' if status == 'Fail' else 'Uncomputed',
            'reason': 'known package constraint failed' if status == 'Fail' else 'full finite-beam/body/support clearance not evaluated',
            'envelope_geometry': {'status': status, 'scope': 'declared world AABBs and quadratic patch extents only', 'checks': checks},
            'finite_beam_clearance': {'status': 'Uncomputed'}}
