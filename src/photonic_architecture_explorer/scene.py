"""Drawable geometry for the Workspace, derived only from engine inputs and results.

The frontend draws what this module returns and computes no optics of its own, so a
drawing can never disagree with the evaluated numbers. Lengths are mm, beam radii µm.
"""

import math

from .external import adapt_external, adapt_ports
from .geometry import add, cross, mul, trace, unit
from .solver import MAX_DIVERGENCE

BEAM_SAMPLES_PER_SEGMENT = 32
SURFACE_GRID = 13


def _mm(point):
    return [v * 1e3 for v in point]


def _t_axis(sagittal, direction):
    return list(unit(cross(sagittal, direction)))


def port_scene(name, port):
    """Reference plane, mode ellipse and the per-Port divergence guard with its threshold."""
    axes = port.mode.parameters()
    wavelength, index = port.mode.wavelength, port.mode.index
    min_mfd_um = 2 * wavelength / (math.pi * index * MAX_DIVERGENCE) * 1e6
    worst = max(p['divergence_rad'] for p in axes)
    return {
        'name': name,
        'position_mm': _mm(port.position),
        'direction': list(port.direction),
        'sagittal_axis': list(port.sagittal),
        't_axis': _t_axis(port.sagittal, port.direction),
        'mode': [{'axis': a, 'radius_um': p['radius_m'] * 1e6, 'waist_radius_um': p['waist_radius_m'] * 1e6,
                  'waist_distance_mm': p['waist_distance_m'] * 1e3, 'rayleigh_range_mm': p['rayleigh_range_m'] * 1e3,
                  'divergence_rad': p['divergence_rad'], 'curvature_per_m': p['curvature_per_m']}
                 for a, p in zip(('t', 's'), axes)],
        'divergence_guard': {
            'status': 'Pass' if worst <= MAX_DIVERGENCE else 'Fail',
            'max_divergence_rad': worst,
            'limit_rad': MAX_DIVERGENCE,
            'min_waist_mfd_um': min_mfd_um,
            'meaning': 'Per-Port paraxial screening guard only; the full path is checked by the engine',
        },
    }


def ports_scene(engine_input):
    ports = adapt_ports(engine_input)
    return {'frame_id': ports.frame_id,
            'ports': [port_scene('source', ports.source), port_scene('target', ports.target)]}


def _surface_grid(mirror, sagittal):
    t = unit(cross(sagittal, mirror.normal))
    kt, ks = mirror.curvatures
    at, as_ = mirror.half_aperture
    n = SURFACE_GRID
    rows = []
    for i in range(n):
        u = -at + 2 * at * i / (n - 1)
        row = []
        for j in range(n):
            v = -as_ + 2 * as_ * j / (n - 1)
            h = (kt * u * u + ks * v * v) / 2
            row.append(_mm(add(add(add(mirror.vertex, mul(t, u)), mul(sagittal, v)), mul(mirror.normal, h))))
        rows.append(row)
    return rows


def candidate_scene(prescription):
    """Mirrors, chief path and sampled 1/e² beam radii for one engine prescription."""
    design = adapt_external(prescription)
    source, target, mirrors = design.source, design.target, design.reflectors
    sagittal = source.sagittal
    path = trace(source, target, mirrors)
    points = [source.position, *(m.vertex for m in mirrors), target.position]
    beam = source.mode
    samples, segments, footprints, travelled = [], [], [], 0.0
    for j, (start, direction, length) in enumerate(zip(points, path['directions'], path['lengths'])):
        segments.append({'start_mm': _mm(start), 'end_mm': _mm(points[j + 1]), 'length_mm': length * 1e3,
                         'direction': list(direction), 't_axis': _t_axis(sagittal, direction),
                         's_axis': list(sagittal)})
        for k in range(BEAM_SAMPLES_PER_SEGMENT + 1):
            z = length * k / BEAM_SAMPLES_PER_SEGMENT
            radii = [p['radius_m'] for p in beam.propagate(z).parameters()]
            samples.append({'segment': j, 'distance_mm': (travelled + z) * 1e3,
                            'point_mm': _mm(add(start, mul(direction, z))),
                            'radius_t_um': radii[0] * 1e6, 'radius_s_um': radii[1] * 1e6})
        beam = beam.propagate(length)
        travelled += length
        if j < len(mirrors):
            mirror, cosine = mirrors[j], path['cosines'][j]
            radii = [p['radius_m'] for p in beam.parameters()]
            footprints.append([radii[0] / cosine * 1e6, radii[1] * 1e6])
            beam = beam.power(mirror.powers(cosine))
    mirror_records = []
    for j, (mirror, cosine) in enumerate(zip(mirrors, path['cosines'])):
        mirror_records.append({
            'id': f'M{j + 1}',
            'vertex_mm': _mm(mirror.vertex),
            'normal': list(mirror.normal),
            't_axis': list(unit(cross(sagittal, mirror.normal))),
            's_axis': list(sagittal),
            'curvature_ts_per_m': list(mirror.curvatures),
            'radius_of_curvature_ts_mm': [None if abs(k) < 1e-12 else 1e3 / k for k in mirror.curvatures],
            'half_aperture_ts_mm': [a * 1e3 for a in mirror.half_aperture],
            'incidence_deg': math.degrees(math.acos(min(1.0, cosine))),
            'beam_footprint_radius_ts_um': footprints[j],
            'surface_grid_mm': _surface_grid(mirror, sagittal),
        })
    return {
        'mirrors': mirror_records,
        'path': {'points_mm': [_mm(p) for p in points], 'segments': segments,
                 'total_length_mm': sum(path['lengths']) * 1e3},
        'beam': {'definition': '1/e² intensity radius along the chief ray, scalar paraxial model',
                 'samples': samples},
    }


def arrival_check(scene, target):
    """Beam radii at the Target plane from the scene samples (used by consistency tests)."""
    last = scene['beam']['samples'][-1]
    return [last['radius_t_um'], last['radius_s_um']], [p['radius_m'] * 1e6 for p in target.mode.parameters()]


def extend_with_crossing(scene, crossing, original, arrival_q_in_block=None):
    """Add the ambient segment between an ambient Port and the block surface to a relay scene.

    `original` is the ambient Port (position, direction, sagittal, mode). For a Target-side
    crossing, `arrival_q_in_block` is the beam evaluated at the surface inside the block.
    """
    from .gaussian import Gaussian
    length = crossing.ambient_length
    d, s = original.direction, original.sagittal
    t = _t_axis(s, d)
    if crossing.side == 'source':
        start, beam, offset = original.position, original.mode, 0.0
    else:
        q_air = tuple(q * f for q, f in zip(arrival_q_in_block, crossing.q_scale))
        start, beam = crossing.point, Gaussian(*q_air, original.mode.wavelength, original.mode.index)
        offset = scene['path']['total_length_mm'] * 1e-3
    samples = []
    for k in range(BEAM_SAMPLES_PER_SEGMENT + 1):
        z = length * k / BEAM_SAMPLES_PER_SEGMENT
        radii = [p['radius_m'] for p in beam.propagate(z).parameters()]
        samples.append({'segment': 0, 'distance_mm': (offset + z) * 1e3, 'point_mm': _mm(add(start, mul(d, z))),
                        'radius_t_um': radii[0] * 1e6, 'radius_s_um': radii[1] * 1e6, 'medium': 'ambient'})
    segment = {'start_mm': _mm(start), 'end_mm': _mm(add(start, mul(d, length))), 'length_mm': length * 1e3,
               'direction': list(d), 't_axis': t, 's_axis': list(s), 'medium': 'ambient'}
    path, relay = scene['path'], scene['beam']['samples']
    for sample in relay:
        sample.setdefault('medium', 'block')
    for seg in path['segments']:
        seg.setdefault('medium', 'block')
    if crossing.side == 'source':
        for sample in relay:
            sample['segment'] += 1
            sample['distance_mm'] += length * 1e3
        path['points_mm'] = [_mm(original.position), *path['points_mm']]
        path['segments'] = [segment, *path['segments']]
        scene['beam']['samples'] = samples + relay
    else:
        index = len(path['segments'])
        for sample in samples:
            sample['segment'] = index
        path['points_mm'] = [*path['points_mm'], _mm(original.position)]
        path['segments'] = [*path['segments'], segment]
        scene['beam']['samples'] = relay + samples
    path['total_length_mm'] += length * 1e3
    path['surface_point_mm'] = _mm(crossing.point)
    return scene
