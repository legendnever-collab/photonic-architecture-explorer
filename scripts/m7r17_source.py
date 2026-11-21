"""Isolated Love-current radiation and independent padded vector Weyl evaluation."""

import argparse
import ctypes
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from numpy.polynomial.legendre import leggauss
from scripts.m7r16_vector_reference import ROOT, K, relative, verify_hash

REF = ROOT / "references/m7r17"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


M1 = read_json(ROOT / "references/m7r8/summary.json")["candidates"]["expansion"][
    "mirror_prescriptions"
][0]
BASIS = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]])  # local t,s,d to world
LEDGER = read_json(ROOT / "references/m7r15/power.json")["smf_forward"]["runs"]
LAUNCH = LEDGER["window"]["export_power_signed_m2"]["outgoing"]


def source(path, pitch):
    with np.load(path) as f:
        period = float(f["period_um"]) * 1e-6
        n = round(period / pitch)
        order, coeff = f["orders"], f["coefficients"]
        # Cell-center samples, FFT corner at -L/2.
        spectrum = np.zeros((6, n, n), complex)
        spectrum[:, order[:, 0] % n, order[:, 1] % n] = coeff * np.exp(
            1j * np.pi * order.sum(axis=1) / n
        )
        field = np.fft.ifft2(spectrum) * n * n
    power = (
        pitch**2
        / 2
        * (field[0] * field[4].conj() - field[1] * field[3].conj()).real.sum()
    )
    factor = np.sqrt(LAUNCH / power)
    return field * factor, float(factor)


def receivers(n):
    q, w = leggauss(n)
    a, b = M1["half_aperture_ts_m"]["value"]
    u, v = np.meshgrid(q * a, q * b, indexing="ij")
    points, incident_area = surface(u, v)
    weights = np.outer(w, w) * a * b
    return points.reshape(-1, 3), (incident_area * weights[..., None]).reshape(-1, 3)


def surface(u, v):
    """Return M1 positions and incident-oriented area vectors per projected area."""
    normal = np.array(M1["illuminated_normal"]["value"])
    s = BASIS[1]
    t = np.cross(s, normal)
    kt, ks = M1["principal_curvature_ts_per_m"]["value"]
    points = (
        M1["vertex_m"]["value"]
        + u[..., None] * t
        + v[..., None] * s
        + (kt * u * u + ks * v * v)[..., None] * normal / 2
    )
    oriented = normal - kt * u[..., None] * t - ks * v[..., None] * s
    return points @ BASIS.T, -oriented @ BASIS.T


def sheet_currents(e, h):
    normal = np.array([0.0, 0.0, 1.0])
    return np.cross(normal, h), -np.cross(normal, e)


def direct(field, pitch, points):
    """Radiate equivalent electric and magnetic currents from one isolated cell."""
    n = field.shape[-1]
    axis = (np.arange(n) + 0.5 - n / 2) * pitch
    x, y = np.meshgrid(axis, axis, indexing="ij")
    locations = np.column_stack((x.ravel(), y.ravel(), np.zeros(n * n)))
    src = field.reshape(6, -1).T
    j, m = sheet_currents(src[:, :3], src[:, 3:])
    values = []
    for batch in np.array_split(points, max(1, len(points) // 8)):
        delta = batch[:, None, :] - locations
        r = np.linalg.norm(delta, axis=-1)
        unit = delta / r[..., None]
        g = np.exp(-1j * K * r) * (pitch**2 / (4 * np.pi * r))
        near = (1 - 1j / (K * r)) / r
        isotropic = (-1j * K - near)[..., None]
        radial = (1j * K + 3 * near)[..., None] * unit
        curl = (-1 / r - 1j * K)[..., None]

        def dyadic(current):
            return (
                isotropic * current
                + radial * np.sum(unit * current, axis=-1)[..., None]
            )

        e = dyadic(j) - curl * np.cross(unit, m)
        h = dyadic(m) + curl * np.cross(unit, j)
        values.append(np.hstack([np.einsum("ij,ijk->ik", g, v) for v in (e, h)]))
    return np.vstack(values)


def padded(field, pitch, size, points, lib):
    n = field.shape[-1]
    freq = 2 * np.pi * np.fft.fftfreq(size, pitch)
    x, y = np.meshgrid(freq, freq, indexing="ij")
    # Fourier convention +i(kx*x+ky*y), forward carrier -i*kz*z.
    # pitch 1 um puts the entire square within the 1310 nm light cone.
    z = np.sqrt(K * K - x * x - y * y)
    k = np.stack((x, y, -z), axis=-1).reshape(-1, 3)
    spec = np.fft.fft2(field, s=(size, size), axes=(-2, -1)) / size**2
    spec *= np.exp(1j * (x + y) * (n / 2 - 0.5) * pitch)
    spectra = spec.reshape(6, -1).T
    j, m = sheet_currents(spectra[:, :3], spectra[:, 3:])
    unit = -k / K

    def transverse(current):
        return current - np.sum(unit * current, axis=1)[:, None] * unit

    denom = 2 * unit[:, 2, None]
    coeff = np.ascontiguousarray(
        np.hstack(
            (
                (np.cross(unit, m) - transverse(j)) / denom,
                (-np.cross(unit, j) - transverse(m)) / denom,
            )
        )
    )
    del spec, spectra, j, m, unit
    points = np.ascontiguousarray(points)
    out = np.empty((len(points), 6), complex)
    lib.evaluate.restype = None
    lib.evaluate(
        len(points),
        len(k),
        *[ctypes.c_void_p(a.ctypes.data) for a in (points, k, coeff, out)],
    )
    return out


def metrics(a, b, weights):
    def power(f):
        return float(
            np.sum(np.cross(f[:, :3], f[:, 3:].conj()).real * weights) / (2 * LAUNCH)
        )

    return dict(
        E_relative=relative(a[:, :3], b[:, :3]),
        H_relative=relative(a[:, 3:], b[:, 3:]),
        flux_over_launch=power(a),
        reference_flux_over_launch=power(b),
        flux_delta=abs(power(a) - power(b)),
    )


def run(out):
    for name, sha in read_json(ROOT / "references/m7r12/summary.json")[
        "inputs"
    ].items():
        verify_hash(ROOT / name, sha)
    paths = [
        ROOT / "references/m7r6/basis.npz",
        ROOT / "references/m7r6/window.npz",
        REF / "source48.npz",
    ]
    for path, row in zip(paths[:2], ("basis", "window")):
        verify_hash(path, LEDGER[row]["frozen_npz_sha256"])
    verify_hash(
        REF / "source48.npz",
        "94d478d66aff719a723b975112f3158e2b55891ea4245adc5610bf044a0f3140",
    )
    verify_hash(
        REF / "source48.json", read_json(REF / "source48.power.json")["case_sha256"]
    )
    pts, w = receivers(28)
    results, fields = {}, []
    for name, path in zip(("32", "40", "48"), paths):
        f, scale = source(path, 0.5e-6)
        values = direct(f, 0.5e-6, pts)
        results[name] = dict(
            amplitude_factor=scale,
            **metrics(values, fields[-1] if fields else values, w),
        )
        fields.append(values)
    f, _ = source(paths[-1], 1e-6)
    results["pitch_1_vs_half_um"] = metrics(direct(f, 1e-6, pts), fields[-1], w)
    fine, wfine = receivers(40)
    fine_field = direct(f, 1e-6, fine)
    results["receiver40_flux_over_launch"] = metrics(fine_field, fine_field, wfine)[
        "flux_over_launch"
    ]
    with tempfile.TemporaryDirectory() as tmp:
        so = Path(tmp) / "weyl.so"
        subprocess.run(
            [
                "g++",
                "-O3",
                "-fopenmp",
                "-shared",
                "-fPIC",
                str(REF / "weyl.cpp"),
                "-o",
                str(so),
            ],
            check=True,
        )
        lib = ctypes.CDLL(str(so))
        for size in (768, 1152, 1536):
            values = padded(f, 1e-6, size, pts, lib)
            results[f"window_{size}um_vs_isolated48"] = metrics(values, fields[-1], w)
    np.savez_compressed(
        out / "m1.npz",
        points_tsd_m=pts,
        incident_area_vectors_m2=w,
        fields_32_40_48=np.array(fields),
        launch_power_m2=LAUNCH,
    )
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    dest = parser.parse_args().output
    dest.mkdir(parents=True, exist_ok=True)
    print(json.dumps(run(dest), indent=2, allow_nan=False))
