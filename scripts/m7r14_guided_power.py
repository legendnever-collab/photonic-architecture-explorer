"""Reciprocity controls and input audit for the frozen 1310 nm case."""

import json

import numpy as np
from scipy.constants import physical_constants

from scripts.m7r13_target_acceptance import ROOT, verify_hash

Z0 = physical_constants["characteristic impedance of vacuum"][0]
TOL = 1e-12


def cross_normal(e, h):
    return e[0] * h[1] - e[1] * h[0]


def projected_fraction(ei, hi, er, hr, area_weight, reverse_power, launch_power):
    """Unconjugated reverse fields. Both powers are incident port powers."""
    if min(reverse_power, launch_power) <= 0:
        raise ValueError("Incident port powers must be positive")
    pairing = np.sum(area_weight * (cross_normal(er, hi) - cross_normal(ei, hr)))
    return float(abs(pairing)**2 / (16 * reverse_power * launch_power))


def check(actual, expected):
    if not np.isclose(actual, expected, atol=TOL, rtol=0):
        raise ValueError(f"Control failed: {actual} versus {expected}")
    return actual


def controls(samples):
    broad, narrow, wavelength = 1e-6, 0.4e-6, 1.31e-6
    area = broad * narrow
    # The guide is uniform along its narrow axis. TE10 varies along s.
    s = (np.arange(samples) + 0.5) / samples
    impedance = Z0 / np.sqrt(1 - (wavelength / (2 * broad))**2)
    profile = np.sin(np.pi * s)
    source, reverse = 2 - 3j, -0.6 + 0.4j
    ei, hi = (source * profile, 0), (0, source * profile / impedance)
    er, hr = (reverse * profile, 0), (0, -reverse * profile / impedance)
    guided_unit_power = area / (4 * impedance)
    pr = abs(reverse)**2 * guided_unit_power
    pl = abs(source)**2 * guided_unit_power
    matched = projected_fraction(ei, hi, er, hr, area / samples, pr, pl)
    wrong_direction = projected_fraction(ei, hi, er, (0, -hr[1]), area / samples, pr, pl)

    # Reverse excitation comes from the dielectric. Only its transmitted field
    # appears on the external plane, while its launch power is inside the glass.
    n = 1.5
    transmitted = 2 * n / (1 + n) * reverse
    glass_incident = area * abs(reverse)**2 * n / (2 * Z0)
    air_incident = area * abs(source)**2 / (2 * Z0)
    fresnel = projected_fraction((0, source), (-source / Z0, 0),
                                 (0, transmitted), (transmitted / Z0, 0),
                                 area, glass_incident, air_incident)
    return {"TE10": check(matched, 1), "same_direction": check(wrong_direction, 0),
            "facet": check(fresnel, 4 * n / (1 + n)**2)}


def glass_flux():
    folder = ROOT / "references/m7r5"
    path = folder / "window.npz"
    fit = json.loads((folder / "result.json").read_text())
    verify_hash(path, fit["runs"]["window"]["sha256"])
    with np.load(path) as data:
        if data["components"].tolist() != ["Ex", "Ey", "Ez", "Hx", "Hy", "Hz"]:
            raise ValueError("Unexpected R5 component order")
        coeff = data["coefficients"][[0, 1, 3, 4]]
        orders, n = data["orders"], int(data["samples"])
        area = (float(data["period_um"]) * 1e-6)**2
    emit = 0.5 * area * np.sum(cross_normal(coeff[:2], coeff[2:].conj())).real
    # x_emit=-t, y_emit=s. With the FFT origin in the corner of the
    # centered period, reflecting x about its center maps the order m to -m.
    spectrum = np.zeros((4, n, n), dtype=complex)
    spectrum[:, -orders[:, 0] % n, orders[:, 1] % n] = coeff
    et, es, ht, hs = np.fft.ifft2(spectrum) * n**2
    signed = 0.5 * area * cross_normal((-et, es), (-ht.conj(), hs.conj())).real.mean()
    if not (emit > 0 and signed < 0):
        raise ValueError("R5 flux direction mismatch")
    residual = check(abs(signed / emit + 1), 0)
    return {"relative_flux_times_m2_signed": float(signed), "relative_parseval_error": residual}


def review():
    summary = json.loads((ROOT / "references/m7r12/summary.json").read_text())
    for name, digest in summary["inputs"].items():
        verify_hash(ROOT / name, digest)
    fields = {}
    for name, digest in summary["sha256"].items():
        if name.startswith("target-"):
            path = ROOT / "references/m7r12" / name
            verify_hash(path, digest)
            with np.load(path) as data:
                fields[name] = sorted(data.files)
    if len(fields) != 2 or any(keys != ["E", "dE_dx", "ts_m"] for keys in fields.values()):
        raise ValueError("Reassess applicability for the changed R12 export")
    return {"controls": {n: controls(n) for n in (16, 32)}, "R5_air": glass_flux(),
            "R12_target_arrays": fields, "scalar_launch_flux": summary["replay"]["row"]["launch_flux"],
            "nominal_guided_fraction": None, "nominal_absolute_uncertainty": None,
            "status": "Uncomputed"}


if __name__ == "__main__":
    print(json.dumps(review(), indent=2, allow_nan=False))
