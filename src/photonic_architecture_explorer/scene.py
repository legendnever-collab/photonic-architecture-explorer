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
