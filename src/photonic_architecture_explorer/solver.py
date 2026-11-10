"""Classified M1 evaluation. Domain failure never produces a coupling number."""

import math
from .gaussian import DomainError, mode_overlap
from .geometry import dot, norm, sub, trace, patch_intersections

MAX_DIVERGENCE = 0.1
MIN_COSINE = math.cos(math.radians(70))
MAX_FOOTPRINT_SLOPE = 0.15
MAX_APERTURE_TAIL = 1e-6


def evaluate(source, target, mirrors):
    result = dict(geometry={'status': 'Uncomputed'}, model_domain={'status': 'Uncomputed'},
                  gaussian_mode_matching={'status': 'Uncomputed'},
                  physical_losses={'status': 'Uncomputed', 'total_coupling': None,
                                   'reason': 'coating/device interfaces/polarization/scatter not supplied'},
                  fabrication={'status': 'Uncomputed', 'reason': 'no process or assembly constraints'})
    try:
        path = trace(source, target, mirrors)
    except DomainError as exc:
        result['geometry'] = {'status': 'Fail', 'reason': str(exc)}
        return result
    result['geometry'] = {'status': 'Pass', 'scope': 'fixed-port specular vertex path', **path}
    try:
        if source.mode.wavelength != target.mode.wavelength or source.mode.index != target.mode.index:
            raise DomainError('common wavelength and homogeneous medium required; no interface adapter')
        s = source.sagittal
        if norm(sub(s, target.sagittal)) > 1e-10:
            raise DomainError('rolled target axes unsupported for separable Gaussian')
        if any(abs(dot(s, d)) > 1e-10 for d in path['directions']):
            raise DomainError('noncoplanar path or rolled Source axes unsupported')
        if any(abs(dot(s, m.normal)) > 1e-10 for m in mirrors):
            raise DomainError('reflector principal axes must align with common incidence plane')
        if min(path['cosines']) < MIN_COSINE:
            raise DomainError('incidence exceeds 70 degrees')
        # Reject any unintended intersection with either finite quadratic patch.
        points = [source.position, *(m.vertex for m in mirrors), target.position]
        for origin, direction, length in zip(points, path['directions'], path['lengths']):
            for m in mirrors:
                if any(1e-10 < l < length-1e-10 for l in patch_intersections(origin, direction, m, s)):
                    result['geometry'] = {'status': 'Fail', 'reason': 'unintended reflector interception'}
                    return result
        result['geometry']['patch_obstruction'] = 'Pass (chief ray, quadratic patches only)'

        def guard(beam):
            if max(p['divergence_rad'] for p in beam.parameters()) > MAX_DIVERGENCE:
                raise DomainError('Gaussian divergence exceeds 0.1 rad')

        guard(source.mode)
        guard(target.mode)
        beam = source.mode
        samples = [{'plane': 'source', 'axes': beam.parameters()}]
        tail = 0.
        for j, (m, cosine) in enumerate(zip(mirrors, path['cosines'])):
            beam = beam.propagate(path['lengths'][j])
            pars = beam.parameters()
            footprint = (pars[0]['radius_m']/cosine, pars[1]['radius_m'])
            slope = max(3*w*abs(c) for w, c in zip(footprint, m.curvatures))
            if slope > MAX_FOOTPRINT_SLOPE:
                raise DomainError('3w projected footprint/curvature exceeds 0.15')
            # Positive union bound avoids cancellation of 1-erf(a)*erf(b).
            loss_bound = sum(math.erfc(math.sqrt(2)*a/w)
                             for a, w in zip(m.half_aperture, footprint))
            tail += loss_bound
            if tail > MAX_APERTURE_TAIL:
                raise DomainError('cumulative aperture-tail estimate exceeds 1e-6')
            samples.append({'plane': f'M{j+1}_before', 'axes': pars,
                            'surface_radii_m': footprint, 'footprint_slope_3w': slope,
                            'aperture_tail_union_estimate': loss_bound,
                            'powers_per_m': m.powers(cosine)})
            beam = beam.power(m.powers(cosine))
            guard(beam)
            samples.append({'plane': f'M{j+1}_after', 'axes': beam.parameters()})
        beam = beam.propagate(path['lengths'][-1])
        samples.append({'plane': 'target', 'axes': beam.parameters()})
        overlap = mode_overlap(beam, target.mode)
        result['model_domain'] = {'status': 'Pass', 'scope': 'aligned coplanar scalar paraxial model',
                                  'aperture_tail_union_estimate': tail}
        result['gaussian_mode_matching'] = {'status': 'Pass', 'meaning': 'computed within model, not a product efficiency requirement',
                                            **overlap, 'output_axes': beam.parameters()}
        result['samples'] = samples
    except (DomainError, OverflowError, ZeroDivisionError) as exc:
        result['model_domain'] = {'status': 'Fail', 'reason': str(exc)}
    return result
