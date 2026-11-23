"""Decompose the frozen SMF source change and sample illumination on the actual M1."""

import argparse
import json
from pathlib import Path

import numpy as np
from numpy.polynomial.legendre import leggauss

from scripts import m7r17_source as r17

PITCH = 0.5e-6
WAVELENGTH = 2 * np.pi / r17.K
HALF_U, HALF_V = r17.M1["half_aperture_ts_m"]["value"]
SIDES = ("u-", "u+", "v-", "v+")


def crop(field, width_um):
    n = round(width_um * 1e-6 / PITCH)
    margin, extra = divmod(field.shape[-1] - n, 2)
    if extra or margin < 0 or n <= 0:
        raise ValueError("Crop must preserve the grid center")
    return field[:, margin : margin + n, margin : margin + n]


def signed_flux(field, area):
    poynting = 0.5 * np.cross(field[:, :3], field[:, 3:].conj()).real
    return float(np.sum(poynting * area) / r17.LAUNCH)


def relative_change(delta, reference):
    return dict(
        E=float(np.linalg.norm(delta[..., :3]) / np.linalg.norm(reference[..., :3])),
        H=float(np.linalg.norm(delta[..., 3:]) / np.linalg.norm(reference[..., 3:])),
    )


def decompose(native, cropped, full, area):
    common = cropped - native
    annulus = full - cropped
    total = full - native
    result = {}
    for key, delta, lo, hi in (
        ("common", common, native, cropped),
        ("annulus", annulus, cropped, full),
        ("total", total, native, full),
    ):
        result[key] = dict(
            **relative_change(delta, native),
            signed_flux_delta=signed_flux(hi, area) - signed_flux(lo, area),
        )
    result["cross_norm_squared"] = {
        name: float(
            2
            * np.vdot(common[:, part], annulus[:, part]).real
            / np.linalg.norm(native[:, part]) ** 2
        )
        for name, part in (("E", slice(3)), ("H", slice(3, 6)))
    }
    return result


def edge_coordinates():
    u = np.linspace(-HALF_U, HALF_U, 65)
    v = np.linspace(-HALF_V, HALF_V, 65)
    return np.array(
        [
            np.column_stack((np.full_like(v, -HALF_U), v)),
            np.column_stack((np.full_like(v, HALF_U), v)),
            np.column_stack((u, np.full_like(u, -HALF_V))),
            np.column_stack((u, np.full_like(u, HALF_V))),
        ]
    )


def strip_nodes(side, width, nlong, nshort):
    # u strips own corners; v strips stop at the two inner u boundaries.
    if side.startswith("u"):
        intervals = [(HALF_U - width, HALF_U), (-HALF_V, HALF_V)]
        orders = (nshort, nlong)
        short = 0
    else:
        intervals = [(-HALF_U + width, HALF_U - width), (HALF_V - width, HALF_V)]
        orders = (nlong, nshort)
        short = 1
    if side.endswith("-"):
        lo, hi = intervals[short]
        intervals[short] = (-hi, -lo)
    axes, weights = [], []
    for (lo, hi), order in zip(intervals, orders):
        x, w = leggauss(order)
        axes.append((hi + lo + (hi - lo) * x) / 2)
        weights.append(w * (hi - lo) / 2)
    u, v = np.meshgrid(*axes, indexing="ij")
    points, oriented = r17.surface(u, v)
    area = oriented * np.outer(*weights)[..., None]
    return points.reshape(-1, 3), area.reshape(-1, 3)


def strip_flux(field, width, orders):
    result = {}
    for side in SIDES:
        points, area = strip_nodes(side, width, *orders)
        result[side] = signed_flux(r17.direct(field, PITCH, points), area)
    result["union"] = sum(result.values())
    return result


def run(dest):
    paths = {
        32: r17.ROOT / "references/m7r6/basis.npz",
        40: r17.ROOT / "references/m7r6/window.npz",
        48: r17.REF / "source48.npz",
    }
    hashes = [r17.LEDGER[row]["frozen_npz_sha256"] for row in ("basis", "window")]
    hashes.append("94d478d66aff719a723b975112f3158e2b55891ea4245adc5610bf044a0f3140")
    pts, area = r17.receivers(28)
    native, sampled, gauges, replay = {}, {}, {}, {}
    with np.load(r17.REF / "m1.npz") as stored:
        np.testing.assert_allclose(pts, stored["points_tsd_m"], atol=1e-15, rtol=0)
        np.testing.assert_allclose(area, stored["incident_area_vectors_m2"], atol=1e-22)
        for i, (width, path) in enumerate(paths.items()):
            r17.verify_hash(path, hashes[i])
            with np.load(path) as data:
                et = data["coefficients"][0] @ ((-1.0) ** data["orders"].sum(axis=1))
                np.testing.assert_allclose(et, 1.0, atol=1e-12, rtol=0)
            native[width], scale = r17.source(path, PITCH)
            gauges[width] = dict(phase_rad=float(np.angle(et)), amplitude_scale=scale)
            sampled[width] = r17.direct(native[width], PITCH, pts)
            ref = stored["fields_32_40_48"][i]
            replay[width] = relative_change(sampled[width] - ref, ref)
            if max(replay[width].values()) > 1e-9:
                raise ValueError("Frozen M1 field replay failed")
    comparisons = {}
    for width in (32, 40):
        cropped = crop(native[48], width)
        partial = r17.direct(cropped, PITCH, pts)
        comparisons[width] = decompose(sampled[width], partial, sampled[48], area)
        reference = np.moveaxis(native[width], 0, -1)
        comparisons[width]["common_source_plane"] = relative_change(
            np.moveaxis(cropped, 0, -1) - reference, reference
        )
        comparisons[width]["cropped_flux_over_launch"] = signed_flux(partial, area)
    uv = edge_coordinates()
    points, _ = r17.surface(uv[..., 0], uv[..., 1])
    fields = r17.direct(native[48], PITCH, points.reshape(-1, 3)).reshape(4, 65, 6)
    np.savez_compressed(
        dest / "edge_fields.npz",
        sides=SIDES,
        uv_m=uv,
        points_tsd_m=points,
        fields_E_Z0H=fields,
        launch_power_m2=r17.LAUNCH,
    )
    peaks = {
        key: dict(
            E=float(np.linalg.norm(field[:, :3], axis=1).max()),
            Z0H=float(np.linalg.norm(field[:, 3:], axis=1).max()),
        )
        for key, field in zip(SIDES, fields)
    }
    strips = {}
    for nlambda in (1, 4, 16):
        w = nlambda * WAVELENGTH
        strips[nlambda] = dict(
            coarse48=strip_flux(native[48], w, (16, 2)),
            fine48=strip_flux(native[48], w, (24, 4)),
            fine40=strip_flux(native[40], w, (24, 4)),
        )
    max_strip_change = max(
        abs(row["fine48"][side] - row["coarse48"][side])
        for row in strips.values()
        for side in SIDES
    )
    change = comparisons[40]["total"]
    checks = dict(
        source_E_pass=change["E"] <= 5e-5,
        source_H_pass=change["H"] <= 5e-5,
        source_flux_pass=abs(change["signed_flux_delta"]) <= 5e-5,
        max_strip_quadrature_change=max_strip_change,
        strip_quadrature_pass=max_strip_change <= 1e-7,
        projected_edge_error_bound=None,
    )
    return dict(
        checks=checks,
        gauge=gauges,
        replay=replay,
        full_flux_over_launch={w: signed_flux(f, area) for w, f in sampled.items()},
        comparisons=comparisons,
        sampled_edge_peaks=peaks,
        strips_over_launch=strips,
        nominal_guided_fraction=None,
        nominal_uncertainty=None,
        rotation_optics=None,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    out = parser.parse_args().output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(
        json.dumps(run(out), indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
