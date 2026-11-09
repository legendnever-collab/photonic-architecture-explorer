"""Ordinary q in metres, exp(+i omega t), vacuum wavelength, scalar unit power.

Public textbook equations, independently implemented in Python. See REUSE_REVIEW.
"""

from dataclasses import dataclass
import math
import cmath


class DomainError(ValueError):
    """Input is invalid or outside the explicitly supported model domain."""


def finite(*values):
    if not all(math.isfinite(v) for v in values):
        raise DomainError("finite real values required")


def positive(*values):
    finite(*values)
    if not all(v > 0 for v in values):
        raise DomainError("positive values required")


@dataclass(frozen=True)
class Gaussian:
    q_t: complex
    q_s: complex
    wavelength: float = 1.31e-6
    index: float = 1.0

    def __post_init__(self):
        positive(self.wavelength, self.index)
        for q in self.q:
            finite(q.real, q.imag)
            positive(q.imag)

    @property
    def q(self):
        return (self.q_t, self.q_s)

    @classmethod
    def from_radii(cls, radii, wavelength=1.31e-6, index=1.0, curvature=(0., 0.)):
        if len(radii) != 2 or len(curvature) != 2:
            raise DomainError("two principal axes required")
        positive(*radii, wavelength, index)
        finite(*curvature)
        q = tuple(1 / complex(c, -wavelength / (math.pi * index * w*w))
                  for w, c in zip(radii, curvature))
        return cls(*q, wavelength, index)

    def parameters(self):
        result = []
        for q in self.q:
            inv = 1/q
            w0 = math.sqrt(self.wavelength*q.imag/(math.pi*self.index))
            w = math.sqrt(-self.wavelength/(math.pi*self.index*inv.imag))
            row = dict(radius_m=w, curvature_per_m=inv.real,
                       waist_radius_m=w0, waist_distance_m=-q.real,
                       rayleigh_range_m=q.imag,
                       divergence_rad=self.wavelength/(math.pi*self.index*w0))
            finite(*row.values())
            result.append(row)
        return tuple(result)

    def propagate(self, length):
        finite(length)
        if length < 0:
            raise DomainError("physical propagation length must be nonnegative")
        return Gaussian(*(q+length for q in self.q), self.wavelength, self.index)

    def power(self, powers):
        if len(powers) != 2:
            raise DomainError("two principal powers required")
        finite(*powers)
        values = []
        for q, power in zip(self.q, powers):
            den = 1-power*q
            if abs(den) < 1e-14:
                raise DomainError("ill-conditioned paraxial transformation")
            values.append(q/den)
        return Gaussian(*values, self.wavelength, self.index)

    def axis_field(self, x, axis=0):
        """Unit-integral 1D scalar field; global phase is intentionally omitted."""
        finite(x)
        p = self.parameters()[axis]
        w, c = p['radius_m'], p['curvature_per_m']
        k = 2*math.pi*self.index/self.wavelength
        return (2/(math.pi*w*w))**0.25 * cmath.exp(-x*x/(w*w)-0.5j*k*c*x*x)


def mode_overlap(incident, target, offset=(0., 0.), slope=(0., 0.)):
    """Squared normalized overlap on one common transverse plane.

    Offset and small slope describe incident relative to centered target.
    Both Gaussian phases are retained. This is NOT transmission/total coupling.
    """
    if len(offset) != 2 or len(slope) != 2:
        raise DomainError("two offsets and slopes required")
    finite(*offset, *slope)
    if math.hypot(*slope) > 0.05:
        raise DomainError("relative slope exceeds 50 mrad")
    if incident.wavelength != target.wavelength or incident.index != target.index:
        raise DomainError("overlap requires identical wavelength and medium")
    k = 2*math.pi*incident.index/incident.wavelength
    log_eta = 0.
    for pi, pt, h, theta in zip(incident.parameters(), target.parameters(), offset, slope):
        wi, wt = pi['radius_m'], pt['radius_m']
        scale = math.sqrt(wi*wt)
        ai = complex(wt/wi, k*pi['curvature_per_m']*scale*scale/2)
        at = complex(wi/wt, -k*pt['curvature_per_m']*scale*scale/2)
        d, tilt = h/scale, k*theta*scale
        a = ai+at
        b = 2*ai*d-1j*tilt
        c = -ai*d*d+1j*tilt*d
        log_eta += math.log(2)-math.log(abs(a))+2*(c+b*b/(4*a)).real
    if not math.isfinite(log_eta) or log_eta > 1e-10:
        raise DomainError("overlap normalization or numerical range failure")
    log_eta = min(0., log_eta)
    eta = math.exp(log_eta)
    return dict(normalized_mode_overlap=eta, log_overlap=log_eta,
                mismatch_db=-10*log_eta/math.log(10), underflow=(eta == 0.))
