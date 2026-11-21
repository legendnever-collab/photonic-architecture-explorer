"""De-embed spatial sampling using native DFT coordinates; retain a common E/H scale."""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import CubicSpline

from scripts import m7r19_capture as source
from scripts import m7r19_reference as prior


def interpolate_z(grid, field, z, count):
    ids = np.sort(np.argsort(abs(grid - z), kind="stable")[:count])
    nodes = grid[ids]
    weights = np.ones(len(nodes))
    for i, node in enumerate(nodes):
        other = np.delete(nodes, i)
        weights[i] = np.prod((z - other) / (node - other))
    return field[..., ids] @ weights


def sample(d, label, z, radii=None, count=8, linear=False):
    rows = []
    for c in d["components"]:
        key = f"{label}_{c}"
        values = interpolate_z(d[key + "_z"], d[key], z, count)
        if radii is not None:
            r = d[key + "_r"]
            if linear:
                values = np.interp(radii, r, values)
            else:
                values = CubicSpline(r, values)(radii)
        rows.append(values)
    return np.stack(rows, axis=-1)


def axial_power(f):
    return float(0.5 * (f[0] * f[1].conj()).real)


def discrete_power(d, label, guide):
    # Meep interpolates native components to cell centers, forms products there,
    # then averages the two adjacent center fluxes for an integer-z monitor.
    z = float(d[label + "_z"])
    dx = 1 / int(d["resolution"])
    r = (np.arange(round(43 / dx)) + 0.5) * dx if guide else None
    power = 0.0
    for plane in [z - dx / 2, z + dx / 2]:
        f = sample(d, label, plane, r, count=2, linear=True)
        power += (prior.radial_flux(f, r) if guide else axial_power(f)) / 2
    return power


def plane_result(d):
    z = float(d["input_z"])
    n = float(d["index"])
    dx = 1 / int(d["resolution"])
    dt = float(d["dt"])
    k = source.K * n
    k_grid = 2 / dx * np.arcsin(n * dx / dt * np.sin(source.K * dt / 2))
    f = sample(d, "input", z)
    coarse = sample(d, "input", z, count=6)
    centered = d["input_centered"][0]
    native_monitor = float(d["input_flux"]) / 2
    p_expected = n * abs(f[0]) ** 2 / 2
    ratio = f[1] / (n * f[0])
    cos = np.cos(k_grid * dx / 2)
    profile = d["input_Ex"]
    axial_phase = np.angle(np.vdot(profile[:-1], profile[1:])) / dx
    return dict(
        impedance_mag_error=float(abs(1 / abs(ratio) - 1)),
        relative_H=abs(ratio - 1),
        H_phase_rad=float(np.angle(ratio)),
        centered_H_relative=abs(centered[1] / (n * centered[0]) - 1),
        centered_E_over_native=float(abs(centered[0] / f[0])),
        centered_H_over_native=float(abs(centered[1] / f[1])),
        predicted_centered_E=cos**2,
        predicted_centered_H=cos,
        half_time_step_phase_rad=source.K * dt / 2,
        measured_k_per_um=axial_phase,
        yee_k_per_um=k_grid,
        continuum_k_per_um=k,
        physical_flux_vs_analytic=abs(axial_power(f) / p_expected - 1),
        monitor_vs_physical=abs(native_monitor / axial_power(f) - 1),
        discrete_replay_vs_monitor=abs(
            discrete_power(d, "input", False) / native_monitor - 1
        ),
        corrected_monitor_vs_analytic=abs(native_monitor / (cos * p_expected) - 1),
        interpolation_H_six_vs_eight=abs(coarse[1] / f[1] - 1),
        E_z_origin_um=float(d["input_Ex_z"][0]),
        H_z_origin_um=float(d["input_Hy_z"][0]),
        dx_um=dx,
        dt=dt,
    )


def modal_difference(f, ref, r):
    # E fixes the sole complex coefficient; H is assessed with that scale.
    w = np.sqrt(r[:, None])
    a, b = w * ref[:, :2], w * f[:, :2]
    coeff = np.vdot(a, b) / np.vdot(a, a)
    errors = {}
    for name, part in [("E", slice(0, 2)), ("H", slice(3, 5))]:
        x, y = w * ref[:, part] * coeff, w * f[:, part]
        errors[name] = float(np.linalg.norm(y - x) / np.linalg.norm(x))
        errors[name + "_phase_rad"] = float(np.angle(np.vdot(x, y)))
    return errors


def guide_result(d):
    beta, mode = source.guided_mode()
    r = d["r_um"]
    exact = mode(r)
    profiles = {}
    rows = {}
    for label in ["input", "output"]:
        z = float(d[label + "_z"])
        centered = d[label + "_centered"]
        f = sample(d, label, z, r)
        profiles[label] = f
        monitor = float(d[label + "_flux"]) / 4
        power = prior.radial_flux(f, r)
        # Known HE11 sampled on the same staggered mesh. Its reconstruction
        # residual quantifies the interface interpolation on this analytic mode.
        ideal = {"components": d["components"]}
        for i, c in enumerate(d["components"]):
            key = label + "_" + c
            rr, zz = d[key + "_r"], d[key + "_z"]
            ideal[key + "_r"], ideal[key + "_z"] = rr, zz
            ideal[key] = mode(rr)[:, i, None] * np.exp(1j * beta * (zz - z))
        reconstructed_exact = sample(ideal, label, z, r)
        w = np.sqrt(r[:, None])
        c_e = (
            np.vdot(w * exact[:, :2], w * f[:, :2])
            / np.linalg.norm(w * exact[:, :2]) ** 2
        )
        p_ref = prior.radial_flux(c_e * exact, r)
        rows[label] = dict(
            HE11=modal_difference(f, exact, r),
            analytic_interpolation=modal_difference(reconstructed_exact, exact, r),
            same_sampling_HE11=modal_difference(f, reconstructed_exact, r),
            physical_flux_vs_HE11_E_scale=abs(power / p_ref - 1),
            centered_HE11=modal_difference(centered, exact, r),
            interpolation=modal_difference(sample(d, label, z, r, count=6), f, r),
            physical_flux_vs_monitor=abs(power / monitor - 1),
            discrete_replay_vs_monitor=abs(
                discrete_power(d, label, True) / monitor - 1
            ),
            centered_to_native_H_change=float(
                np.linalg.norm((centered[:, 3:5] - f[:, 3:5]) * np.sqrt(r[:, None]))
                / np.linalg.norm(f[:, 3:5] * np.sqrt(r[:, None]))
            ),
        )
    dx = 1 / int(d["resolution"])
    offsets = {
        c: [
            float((d["input_" + c + "_r"][0] / dx) % 1),
            float(np.round(d["input_" + c + "_z"][0] / dx, 8) % 1),
        ]
        for c in d["components"]
    }
    return dict(
        planes=rows,
        profile_change_between_planes=modal_difference(
            profiles["output"], profiles["input"], r
        ),
        backward_over_forward_monitor=float(-d["before_flux"] / d["input_flux"]),
        yee_r_z_offsets_in_cells=offsets,
    ), profiles


def run(folder, profile_output=None):
    base = source.ROOT / "references/m7r19"
    with np.load(base / "straight12.npz") as s, np.load(base / "facet12.npz") as f:
        replay = prior.controls(s, f)
    planes = {}
    for medium in ["air", "clad"]:
        for n in [8, 12, 24]:
            key = f"plane-{medium}-{n}"
            with np.load(folder / f"{key}.npz") as d:
                planes[key] = plane_result(d)
    guides, profiles = {}, {}
    for key in ["guide-12", "guide-24", "guide-dual-12"]:
        with np.load(folder / f"{key}.npz") as d:
            guides[key], profiles[key] = guide_result(d)
            r = d["r_um"]
    if profile_output is not None:
        arrays = {
            f"{key}_{plane}": field
            for key, planeset in profiles.items()
            for plane, field in planeset.items()
        }
        np.savez_compressed(
            profile_output,
            r_um=r,
            components=["Er", "Ep", "Ez", "Z0Hr", "Z0Hp", "Z0Hz"],
            z_um_input=-4.0,
            z_um_output=5.0,
            phasor="exp(-i omega t + i phi)",
            **arrays,
        )
    # For the integer-z point export, point power / discrete monitor ∝ cos²(k_h dx/2).
    predicted = (
        planes["plane-air-12"]["predicted_centered_E"]
        / planes["plane-clad-12"]["predicted_centered_E"]
        - 1
    )
    return dict(
        control_limit=5e-5,
        guide_input_field_within_limit={
            key: guides["guide-24"]["planes"]["input"]["HE11"][key] <= 5e-5
            for key in ("E", "H")
        },
        nominal_guided_fraction=None,
        nominal_U=None,
        rotation_optics=None,
        plane_prediction_r19_power_difference=predicted,
        r19_H=replay["straight_transverse_error"]["H"],
        r19_power=replay["air_export_vs_native_rel"],
        planes=planes,
        guides=guides,
        source_change={
            p: modal_difference(
                profiles["guide-dual-12"][p], profiles["guide-12"][p], r
            )
            for p in ["input", "output"]
        },
        grid_change={
            p: modal_difference(profiles["guide-24"][p], profiles["guide-12"][p], r)
            for p in ["input", "output"]
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--profiles", type=Path)
    args = parser.parse_args()
    result = run(args.folder, args.profiles)
    print(json.dumps(result, indent=2, allow_nan=False))
