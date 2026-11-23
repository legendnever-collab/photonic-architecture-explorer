"""Compare collocated cylindrical facet exports at the frozen M1 receivers."""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import CubicSpline

from scripts import m7r17_source as r17
from scripts import m7r18_edge_impact as r18
from scripts.m7r19_capture import CASE_PATH, WL, guided_mode
from hashlib import sha256


def radial_flux(field, r):
    # Linear polarization from the m=+1 solution and its y-reflected partner.
    density = (field[:, 0] * field[:, 4].conj() - field[:, 1] * field[:, 3].conj()).real
    return float(np.pi / 2 * (r * density).sum() * (r[1] - r[0]))


def grid_field(field, r, pitch_um):
    parity = np.array([1, 1, -1, 1, 1, -1])
    spline = CubicSpline(np.r_[-r[::-1], r], np.vstack([field[::-1] * parity, field]))
    axis_field = spline(0.0)
    center = (axis_field[0] - 1j * axis_field[1]) / 2
    power = radial_flux(field, r) * 1e-12
    if power <= 0 or abs(center) == 0:
        raise ValueError("Invalid independent launch or phase reference")
    scale = np.sqrt(r17.LAUNCH / power) * np.exp(-1j * np.angle(center))
    radius = r[-1] + (r[1] - r[0]) / 2
    n = round(2 * radius / pitch_um)
    axis = (np.arange(n) + 0.5 - n / 2) * pitch_um
    x, y = np.meshgrid(axis, axis, indexing="ij")
    rho = np.hypot(x, y)
    co, si = x / rho, y / rho
    er, ep, ez, hr, hp, hz = np.moveaxis(spline(np.minimum(rho, radius)), -1, 0)
    ex, ey = er * co * co - 1j * ep * si * si, (er + 1j * ep) * co * si
    hx, hy = (1j * hr - hp) * si * co, 1j * hr * si * si + hp * co * co
    # Meep exp(-iwt) -> stored R6/R17 exp(+iwt); E and H both conjugated.
    grid = (np.stack((ex, ey, ez * co, hx, hy, 1j * hz * si)) * scale).conj()
    grid[:, rho > radius] = 0
    return grid, dict(
        center_phase_meep_rad=float(np.angle(center)),
        launch_scale_abs=float(abs(scale)),
        raw_linear_flux_um2=power * 1e12,
    )


def compare(a, b, reference, area):
    return dict(
        **r18.relative_change(a - b, reference),
        signed_flux_delta=r18.signed_flux(a, area) - r18.signed_flux(b, area),
    )


def controls(straight, facet):
    r = facet["r_um"]
    np.testing.assert_array_equal(r, straight["r_um"])
    _, mode = guided_mode()
    exact = mode(r)
    observed = straight["input"]
    # One complex excitation coefficient fixed by tangential E; same scale used for H.
    weight = np.sqrt(r[:, None])
    a, b = exact[:, :2] * weight, observed[:, :2] * weight
    c = np.vdot(a, b) / np.vdot(a, a)
    guide_error = {
        name: r17.relative(observed[:, idx] * weight, c * exact[:, idx] * weight)
        for name, idx in [("E", slice(0, 2)), ("H", slice(3, 5))]
    }
    pin = float(straight["input_flux"])
    pnet, pout, side = (
        float(facet[key]) / pin for key in ("input_flux", "output_flux", "side_flux")
    )
    native_to_linear = radial_flux(observed, r) / pin
    refl = -radial_flux(facet["input"] - observed, r) / radial_flux(observed, r)
    return dict(
        straight_transverse_error=guide_error,
        ref_input_native_flux=pin,
        guide_to_native_flux_factor=native_to_linear,
        input_net_over_incident=pnet,
        reflection_subtracted_over_incident=refl,
        output_over_incident=pout,
        side_over_incident=side,
        closed_monitor_balance_abs=abs(pnet - pout - side),
        reflected_transmitted_side_balance_abs=abs(1 - refl - pout - side),
        air_export_vs_native_rel=abs(
            radial_flux(facet["air"], r) / (native_to_linear * pin * pout) - 1
        ),
        dft_extension_relative=r18.relative_change(
            (facet["air_early"] - facet["air"]) * weight, facet["air"] * weight
        ),
    )


def run(folder):
    pts, area = r17.receivers(28)
    with np.load(r17.REF / "m1.npz") as stored:
        r48 = stored["fields_32_40_48"][2]
    old_grid, _ = r17.source(r17.REF / "source48.npz", r18.PITCH)
    old40 = r17.direct(r18.crop(old_grid, 40), r18.PITCH, pts)
    rows, pilots = {}, []
    for res in (8, 12):
        with (
            np.load(folder / f"straight{res}.npz") as s,
            np.load(folder / f"facet{res}.npz") as f,
        ):
            for export, straight in [(s, True), (f, False)]:
                if (
                    str(export["case_sha256"])
                    != sha256(CASE_PATH.read_bytes()).hexdigest()
                    or bool(export["straight"]) != straight
                    or int(export["resolution"]) != res
                    or float(export["wavelength_um"]) != WL
                    or float(export["air_z_um"]) != 5
                    or str(export["phasor"]) != "exp(-i omega t + i phi)"
                    or list(export["components"])
                    != ["Er", "Ep", "Ez", "Z0Hr", "Z0Hp", "Z0Hz"]
                ):
                    raise ValueError("Facet pilot metadata mismatch")
            for key in (
                "radius_um",
                "pml_um",
                "meep_version",
                "input_z_um",
                "source_z_um",
            ):
                np.testing.assert_array_equal(s[key], f[key])
            ctrl = controls(s, f)
            grid, gauge = grid_field(f["air"], f["r_um"], 0.5)
            version = str(f["meep_version"])
        values = {w: r17.direct(r18.crop(grid, w), r18.PITCH, pts) for w in (40, 48)}
        full = r17.direct(grid, r18.PITCH, pts)
        pilots.append(full)
        rows[res] = dict(
            controls=ctrl,
            gauge=gauge,
            full_flux_over_launch=r18.signed_flux(full, area),
            common40=compare(values[40], old40, r48, area),
            common48=compare(values[48], r48, r48, area),
            common48_source_plane=r18.relative_change(
                np.moveaxis(r18.crop(grid, 48) - old_grid, 0, -1),
                np.moveaxis(old_grid, 0, -1),
            ),
            added_outside48=compare(full, values[48], r48, area),
            full_vs_r17_48=compare(full, r48, r48, area),
        )
    return dict(
        meep_version=version,
        normalized_launch_m2=r17.LAUNCH,
        runs=rows,
        grid12_vs8_using_r17_norm=compare(pilots[1], pilots[0], r48, area),
        status="Unqualified pilot",
        independent_accuracy_bound=None,
        nominal_guided_fraction=None,
        nominal_U=None,
        rotation_optics=None,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.folder), indent=2, allow_nan=False))
