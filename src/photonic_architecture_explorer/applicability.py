"""Per-Port precheck only; no geometry certification or physical efficiency."""

import math
from .gaussian import DomainError, Gaussian
from .solver import MAX_DIVERGENCE


def gaussian_port_domain(wavelength_m, ambient_index, mfd_m, curvature_per_m):
    """Explicit external-plane MFD and inverse wavefront radii, t/s axes.

    None means missing, including phase: it must never default to a waist.
    This is a partial precheck; the path may still fail every other M1 guard.
    """
    values = (wavelength_m, ambient_index, mfd_m, curvature_per_m)
    if any(v is None for v in values):
        return {'status': 'Uncomputed', 'reason': 'wavelength, ambient, MFD and phase required'}
    try:
        if len(mfd_m) != 2 or len(curvature_per_m) != 2:
            raise DomainError('two principal axes required')
        if any(v is None for v in (*mfd_m, *curvature_per_m)):
            return {'status': 'Uncomputed', 'reason': 'both axis widths and phases required'}
        beam = Gaussian.from_radii(tuple(v/2 for v in mfd_m), wavelength_m,
                                   ambient_index, curvature_per_m)
        axes = beam.parameters()
        status = 'Fail' if max(p['divergence_rad'] for p in axes) > MAX_DIVERGENCE else 'Pass'
        return {'status': status, 'scope': 'per-Port divergence precheck only',
                'reason': 'outside existing 0.1 rad guard' if status == 'Fail' else 'inside divergence guard only',
                'axes': axes, 'max_divergence_rad': MAX_DIVERGENCE}
    except (DomainError, TypeError, ValueError, OverflowError, ZeroDivisionError) as exc:
        return {'status': 'Fail', 'reason': str(exc)}


def residual_scale_comparison(residual_m, mode_radii_m):
    """Norm residual divided by each axis scale, NOT axis-resolved errors/loss.

    Only use with modes and residuals from the SAME fixed architecture/fixture.
    """
    if residual_m is None or mode_radii_m is None or any(v is None for v in mode_radii_m):
        return {'status': 'Uncomputed', 'reason': 'residual and same-fixture mode scales required'}
    if (len(mode_radii_m) != 2 or not math.isfinite(residual_m) or residual_m < 0
            or any(not math.isfinite(w) or w <= 0 for w in mode_radii_m)):
        raise DomainError('finite nonnegative residual and two positive radii required')
    return {'status': 'Computed', 'norm_residual_m': residual_m,
            'norm_over_axis_radius': [residual_m/w for w in mode_radii_m],
            'meaning': 'dimensionless scale comparison, not axis-resolved displacement or coupling loss'}
