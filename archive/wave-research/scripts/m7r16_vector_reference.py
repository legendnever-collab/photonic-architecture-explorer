"""Frozen-port vector propagation and infinite tangent-plane PEC controls."""

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.m7r13_target_acceptance import ROOT, verify_hash
from scripts.m7r14_guided_power import cross_normal

K = 2 * np.pi / 1.31e-6
LIMIT = 1e-10


def frame(port):
    n = np.array(port["propagation_direction"]["value"])
    s = np.array(port["sagittal_axis"]["value"])
    return np.array([np.cross(s, n), s, n])


def directions(orders, period):
    transverse = -orders * (2 * np.pi / (K * period))
    axial_squared = 1 - np.sum(transverse**2, axis=1)
    if np.any(axial_squared <= 0):
        raise ValueError("Control requires strictly propagating forward orders")
    return np.column_stack((transverse, np.sqrt(axial_squared)))


def evaluate(points, origin, rays, coefficients):
    """Sum global Cartesian fields from amplitudes at a common phase origin."""
    return np.exp(-1j * K * ((points - origin) @ rays.T)) @ coefficients


def reflect(rays, electric, magnetic, normal):
    transform = np.eye(3) - 2 * np.outer(normal, normal)
    return rays @ transform, -electric @ transform, magnetic @ transform


def relative(a, b):
    return float(np.linalg.norm(a - b) / np.linalg.norm(b))


def require(errors):
    if not all(np.isfinite(x) and x <= LIMIT for x in errors.values()):
        raise ValueError(f"Vector control outside budget: {errors}")
    return errors


def free_control():
    # Two oblique harmonics with distinct azimuths, phases and polarizations.
    length = 8 * (2 * np.pi / K)
    rays = directions(np.array([[-2, 0], [0, 4]]), length)
    a, b = np.sqrt(15) / 4, np.sqrt(3) / 2
    electric = np.array([[0, 1, 0], [0, b, 0.5]], complex)
    electric[1] *= 0.3 + 0.8j
    magnetic = np.cross(rays, electric)
    pts = np.array([[0.7, 2, 23], [-0.4, 1.5, 11], [1, -0.6, 0]]) * 1e-6
    x, y, z = pts.T
    p = np.exp(-1j * K * (x / 4 + a * z))
    q = (0.3 + 0.8j) * np.exp(-1j * K * (-y / 2 + b * z))
    expected_e = np.column_stack((0*p, p + b*q, q/2))
    expected_h = np.column_stack((-a*p - q, 0*p, p/4))
    result = evaluate(pts, np.zeros(3), rays, np.hstack((electric, magnetic)))
    return require({"E_relative": relative(result[:, :3], expected_e),
                    "H_relative": relative(result[:, 3:], expected_h),
                    "flux_relative": relative(
                        cross_normal(result[:, :3].T, result[:, 3:].conj().T).real,
                        cross_normal(expected_e.T, expected_h.conj().T).real)})


def pec_controls():
    errors = []
    normal = np.array([0, 0, 1])
    for angle in np.deg2rad([0, 30, 60]):
        u, v = np.sin(angle), np.cos(angle)
        ray = np.array([u, 0, v])
        for te, tm in [(1, 0), (0, 1), (1 + 0.2j, -0.4j)]:
            e = np.array([tm*v, te, -tm*u])
            h = np.cross(ray, e)
            kr, er, hr = reflect(ray, e, h, normal)
            expected_e = np.array([-tm*v, -te, -tm*u])
            expected_h = np.array([-te*v, tm, -te*u])
            incident_flux = cross_normal(e, h.conj()).real
            errors.extend([relative(kr, [u, 0, -v]), relative(er, expected_e),
                           relative(hr, expected_h), np.linalg.norm((e+er)[:2])/np.linalg.norm(e),
                           abs(cross_normal(er, hr.conj()).real / incident_flux + 1)])
    return require({"max_polarization_boundary_flux_error": float(max(errors))})


def grid(center, basis, period):
    axis = (np.arange(64) + 0.5 - 32) * period / 64
    t, s = np.meshgrid(axis, axis, indexing="ij")
    pts = center + t.ravel()[:, None]*basis[0] + s.ravel()[:, None]*basis[1]
    return axis, pts


def run(directory):
    def read(path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    manifest = read("references/m7r12/summary.json")["inputs"]
    for name, digest in manifest.items():
        verify_hash(ROOT / name, digest)
    ports = read("examples/m7r6_smf_glass_1310.json")
    ledger = read("references/m7r15/power.json")["smf_forward"]["runs"]["window"]
    launch = ledger["export_power_signed_m2"]["outgoing"]
    path = ROOT / "references/m7r6/window.npz"
    verify_hash(path, ledger["frozen_npz_sha256"])
    with np.load(path) as src:
        orders = src["orders"]
        period = src["period_um"].item() * 1e-6
        coeff = src["coefficients"].T * ((-1.)**orders.sum(axis=1))[:, None]
    rays = directions(orders, period)
    e, h = coeff[:, :3], coeff[:, 3:]
    results = {"free": free_control(), "PEC": pec_controls()}
    errors = {"H_vs_k_cross_E": relative(h, np.cross(rays, e)),
              "longitudinal_residual": float(np.linalg.norm(np.sum(rays*e, axis=1))/np.linalg.norm(e))}
    basis = frame(ports["source"])
    rays, e, h = (a @ basis for a in (rays, e, h))
    origin = np.array(ports["source"]["position_m"]["value"])
    for distance in [0, 25e-6]:
        _, points = grid(origin + distance*basis[2], basis, period)
        values = evaluate(points, origin, rays, np.hstack((e, h)))
        el, mag = values[:, :3] @ basis.T, values[:, 3:] @ basis.T
        power = 0.5 * period**2 * cross_normal(el.T, mag.conj().T).real.mean()
        errors[f"cell_flux_relative_at_{distance:g}m"] = abs(power/launch - 1)
    results["R15_source"] = require(errors)
    mirrors = read("references/m7r8/summary.json")["candidates"]["expansion"]["mirror_prescriptions"]
    initial = (origin, rays, np.hstack((e, h)))
    for mirror in mirrors:
        vertex = np.array(mirror["vertex_m"]["value"])
        phase = np.exp(-1j*K*(rays @ (vertex-origin)))[:, None]
        rays, e, h = reflect(rays, phase*e, phase*h, mirror["illuminated_normal"]["value"])
        origin = vertex
    basis = frame(ports["target"])
    center = np.array(ports["target"]["position_m"]["value"])
    axis, points = grid(center, basis, period)
    values = evaluate(points, origin, rays, np.hstack((e, h)))
    el, mag = values[:, :3] @ basis.T, values[:, 3:] @ basis.T
    tangential = dict(zip(("E_t", "E_s", "H_t", "H_s"),
                          [v.reshape(64, 64) for v in (el[:, 0], el[:, 1], mag[:, 0], mag[:, 1])],
                          strict=True))
    # Unfold selected Target observation points into source space. This uses
    # image coordinates rather than advancing spectral phase origins at mirrors.
    probes = np.array([0, 1001, 2048, 2080, 4095])
    image_points = points[probes].copy()
    for mirror in reversed(mirrors):
        normal = np.array(mirror["illuminated_normal"]["value"])
        vertex = mirror["vertex_m"]["value"]
        image_points -= 2 * ((image_points - vertex) @ normal)[:, None] * normal
    unfolded = evaluate(image_points, *initial)
    for mirror in mirrors:
        normal = np.array(mirror["illuminated_normal"]["value"])
        for vector, parity in [(unfolded[:, :3], -1), (unfolded[:, 3:], 1)]:
            vector[:] = parity * (vector - 2 * (vector @ normal)[:, None] * normal)
    results["double_plane_image"] = require({
        "E_relative": relative(values[probes, :3], unfolded[:, :3]),
        "H_relative": relative(values[probes, 3:], unfolded[:, 3:])})
    directory.mkdir(parents=True, exist_ok=True)
    file = directory / "infinite-plane-control.npz"
    np.savez_compressed(file, **tangential, t_m=axis, s_m=axis, center_m=center,
                        basis_tsn=basis, cell_area_m2=(period/64)**2, wavelength_m=2*np.pi/K,
                        launch_power_m2=launch, source_sha256=ledger["frozen_npz_sha256"],
                        case="periodic-source double infinite tangent-plane control",
                        units="E/E_ref, Z0 H/E_ref", phasor="exp(+i omega t)")
    with np.load(file) as data:
        for key, field in tangential.items():
            np.testing.assert_array_equal(data[key], field)
    results.update(control_export=file.name, launch_power_m2=launch,
                   nominal_target_field=None, nominal_guided_fraction=None, rotation_response=None)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    print(json.dumps(run(parser.parse_args().output_dir), indent=2, allow_nan=False))
