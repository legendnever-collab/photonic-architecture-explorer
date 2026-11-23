"""Finite PEC plate edge diagnostic in wavelength and optical-period units."""

import json
import numpy as np
from scipy.special import erfc
from scripts.m7r17_source import K, M1, relative

WL = 2 * np.pi / K
WIDTH, LENGTH = 2 * np.array(M1["half_aperture_ts_m"]["value"]) / WL
COS = -M1["illuminated_normal"]["value"][0]
SIN = np.sqrt(1 - COS**2)  # inward coordinate from one of the tangential edges
ANGLE = np.arccos(-SIN)
PROBES = np.array([[-2.0, 0, 3], [0.0, 0, 3], [2.0, 0, 3], [8.0, 0, 3]])
DURATION = 32.0
TIME = 20.0


def pulse(t):
    """Analytic carrier with a compact sin^4 envelope, plus derivative and primitive."""
    # sin^4(pi*t/D) = (3 - 4 cos(2pi*t/D) + cos(4pi*t/D))/8.
    f = np.zeros_like(t, complex)
    deriv, primitive = f.copy(), f.copy()
    for order, weight in zip(range(-2, 3), (1 / 16, -1 / 4, 3 / 8, -1 / 4, 1 / 16)):
        iw = 2j * np.pi * (1 + order / DURATION)
        z = np.exp(iw * t)
        f += weight * z
        deriv += weight * iw * z
        primitive += weight * (z - 1) / iw
    mask = (t >= 0) & (t <= DURATION)
    return f * mask, deriv * mask, primitive * mask


def physical_optics(cells_per_wl, polarization):
    # PEC lies at z=0, 0<x<WIDTH, |y|<LENGTH/2. J=2 n×Hinc.
    current = (
        np.array([0, 2 * COS, 0]) if polarization == "TE" else np.array([-2, 0, 0])
    )
    values = []
    for pt in PROBES:
        # Causality: SIN*x + R <= TIME, so x>=0 gives R<=TIME.
        # All omitted cells of the finite rectangle contribute exactly zero.
        lo = np.maximum([0, -LENGTH / 2], pt[:2] - TIME)
        hi = np.minimum([WIDTH, LENGTH / 2], pt[:2] + TIME)
        count = np.ceil((hi - lo) * cells_per_wl).astype(int)
        step = (hi - lo) / count
        x, y = np.meshgrid(
            *(lo[j] + (np.arange(count[j]) + 0.5) * step[j] for j in range(2)),
            indexing="ij",
        )
        delta = np.stack((pt[0] - x, pt[1] - y, np.full_like(x, pt[2])), axis=-1)
        r = np.linalg.norm(delta, axis=-1)
        ray = delta / r[..., None]
        f, df, integ = pulse(TIME - SIN * x - r)
        along = ray * (ray @ current)[..., None]
        # Retarded free-space electric-current dyadic and its curl, c=Z0=1.
        e = (
            -(current - along) * (df / r)[..., None]
            - (current - 3 * along) * (f / r**2 + integ / r**3)[..., None]
        )
        h = -np.cross(ray, current) * (df / r + f / r**2)[..., None]
        values.append(
            np.r_[e.sum(axis=(0, 1)), h.sum(axis=(0, 1))] * step.prod() / (4 * np.pi)
        )
    return np.array(values)


def sommerfeld(x, z, k, sign):
    phi = np.arctan2(z, x)
    rho = np.hypot(x, z)

    def wave(theta):
        arg = np.sqrt(2 * k * rho) * np.cos(theta / 2)
        return (
            np.exp(1j * k * rho * np.cos(theta))
            * erfc(-np.exp(0.25j * np.pi) * arg)
            / 2
        )

    incident = np.exp(-1j * k * (SIN * x - COS * z))
    return wave(phi - ANGLE) + sign * wave(phi + ANGLE) - incident


def exact_pulse(polarization, duration, dt=1 / 8, h=1e-4):
    # Synthesize the causal response of the canonical PEC edge via its
    # frequency response. Negative-frequency transfers are complex conjugates.
    t = np.arange(round(duration / dt)) * dt
    spectrum = np.fft.fft(pulse(t)[0]) / len(t)
    omega = 2 * np.pi * np.fft.fftfreq(len(t), dt)
    keep = abs(omega) > 0
    omega = omega[keep]
    k = abs(omega)
    temporal = spectrum[keep] * np.exp(1j * omega * TIME)
    sign = -1 if polarization == "TE" else 1
    result = []
    for x, _, z in PROBES:

        def scalar(a, b):
            return sommerfeld(a, b, k, sign)

        u = scalar(x, z)
        dx = (scalar(x + h, z) - scalar(x - h, z)) / (2 * h)
        dz = (scalar(x, z + h) - scalar(x, z - h)) / (2 * h)
        # TE uses E_y, TM uses Z0 H_y. Recover the other vector by Maxwell curl.
        trans = np.column_stack((-1j * dz / k, 0 * u, 1j * dx / k))
        axial = np.column_stack((0 * u, u, 0 * u))
        vectors = (
            np.hstack((axial, trans)) if sign == -1 else np.hstack((-trans, axial))
        )
        vectors[omega < 0] = vectors[omega < 0].conj()
        result.append(temporal @ vectors)
    return np.array(result)


def comparisons(fields, reference):
    def flux(x):
        return np.cross(x[:, :3], x[:, 3:].conj()).real[:, 2] / 2

    return dict(
        E_relative=relative(fields[:, :3], reference[:, :3]),
        H_relative=relative(fields[:, 3:], reference[:, 3:]),
        max_flux_delta_over_incident_peak=float(
            max(abs(flux(fields) - flux(reference))) / (COS / 2)
        ),
        flux_z=flux(fields).tolist(),
    )


def run():
    rows = {}
    for pol in ("TE", "TM"):
        ref = exact_pulse(pol, 1024)
        coarse = exact_pulse(pol, 512)
        finer_dt = exact_pulse(pol, 1024, dt=1 / 12, h=5e-5)
        rows[pol] = {
            "reference_period_check": comparisons(coarse, ref),
            "reference_step_check": comparisons(finer_dt, ref),
        }
        previous = None
        for order in (4, 8, 16, 32):
            field = physical_optics(order, pol)
            row = comparisons(field, ref)
            if previous is not None:
                row["mesh_change"] = comparisons(field, previous)
            rows[pol][str(order)] = row
            previous = field
        for key, a in [("reference_fields", ref), ("PO_fields", field)]:
            rows[pol][key] = {"real": a.real.tolist(), "imag": a.imag.tolist()}
    return dict(
        plate_size_wavelengths=[WIDTH, LENGTH],
        incidence_deg=float(np.degrees(np.arccos(COS))),
        probes_wavelengths=PROBES.tolist(),
        time_periods=TIME,
        pulse_duration_periods=DURATION,
        polarization=rows,
    )


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, allow_nan=False))
