"""Independent lossless, open-boundary SMF facet pilot (Meep; micrometre units)."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.special import jv, jvp, kv, kvp

ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = ROOT / "references/m7r6/case.json"
CASE = json.loads(CASE_PATH.read_text())
WL = CASE["vacuum_wavelength_um"]
K = 2 * np.pi / WL
A = CASE["core_radius_um"]
# Malitson at the frozen wavelength, in micrometres.
NCL = np.sqrt(
    1
    + sum(
        b * WL**2 / (WL**2 - c**2)
        for b, c in zip(
            [0.6961663, 0.4079426, 0.8974794], [0.0684043, 0.1162414, 9.896161]
        )
    )
)
NCO = NCL + CASE["delta_n"]


def mode_matrix(beta):
    """Continuity of E_phi and Z0 H_phi at r=a; longitudinal fields normalized there."""
    q1, q2 = (K * NCO) ** 2 - beta**2, (K * NCL) ** 2 - beta**2
    h, p = np.sqrt(q1), np.sqrt(-q2)
    d1, d2 = h * jvp(1, h * A) / jv(1, h * A), p * kvp(1, p * A) / kv(1, p * A)
    diag = 1j * beta / A * (1 / q1 - 1 / q2)
    return np.array(
        [
            [diag, -K * (d1 / q1 - d2 / q2)],
            [K * (NCO**2 * d1 / q1 - NCL**2 * d2 / q2), diag],
        ]
    )


def guided_mode():
    beta = brentq(
        lambda b: np.linalg.det(mode_matrix(b)).real,
        K * (NCL + 1e-9),
        K * (NCO - 1e-9),
        xtol=2e-14,
    )
    matrix = mode_matrix(beta)
    ratio = -matrix[0, 0] / matrix[0, 1]

    def fields(r):
        r = np.atleast_1d(np.abs(r)).astype(float).clip(min=1e-9)
        result = np.empty((len(r), 6), complex)
        for mask, n, f, df in [(r <= A, NCO, jv, jvp), (r > A, NCL, kv, kvp)]:
            rm = r[mask]
            q = (K * n) ** 2 - beta**2
            h = np.sqrt(abs(q))
            ez, deriv = f(1, h * rm) / f(1, h * A), h * df(1, h * rm) / f(1, h * A)
            hz = ratio * ez
            er = 1j / q * (beta * deriv + K * 1j * hz / rm)
            ep = 1j / q * (beta * 1j * ez / rm - K * ratio * deriv)
            hr = 1j / q * (beta * ratio * deriv - K * n * n * 1j * ez / rm)
            hp = 1j / q * (beta * 1j * hz / rm + K * n * n * deriv)
            result[mask] = np.column_stack((er, ep, ez, hr, hp, hz))
        return result

    return beta, fields


def capture(out, resolution, radius, pml, straight):
    import meep as mp

    beta, mode = guided_mode()
    frequency = 1 / WL

    # Electric sheet only. The backward wave exits the bottom PML. A straight
    # control measures the forward illumination on the facet side of the sheet.
    def sheet(component, sign):
        def value(point):
            # Meep passes the displacement from the source center.
            return sign * mode(point.x + radius / 2)[0, component]

        return value

    sources = [
        mp.Source(
            mp.GaussianSource(frequency, fwidth=0.18 * frequency),
            component=component,
            center=mp.Vector3(radius / 2, 0, -7),
            size=mp.Vector3(radius),
            amp_func=sheet(idx, sign),
        )
        for component, idx, sign in [(mp.Er, 4, -1), (mp.Ep, 3, 1)]
    ]
    half_z = 12 + pml
    height = 2 * half_z if straight else half_z
    center = mp.Vector3(z=0 if straight else -half_z / 2)
    sim = mp.Simulation(
        dimensions=mp.CYLINDRICAL,
        m=1,
        resolution=resolution,
        cell_size=mp.Vector3(radius + pml, 0, 2 * half_z),
        boundary_layers=[mp.PML(pml)],
        sources=sources,
        geometry=[
            mp.Block(
                center=center,
                size=mp.Vector3(mp.inf, mp.inf, height),
                material=mp.Medium(index=NCL),
            ),
            mp.Cylinder(
                radius=A, height=height, center=center, material=mp.Medium(index=NCO)
            ),
        ],
    )
    components = [mp.Er, mp.Ep, mp.Ez, mp.Hr, mp.Hp, mp.Hz]
    extent = radius - 1
    r = (np.arange(round(extent * 4)) + 0.5) / 4
    fields, fluxes = {}, {}
    for key, z in [("input", -4), ("air", CASE["plane_z_um"])]:
        center = mp.Vector3(extent / 2, 0, z)
        size = mp.Vector3(extent)
        fields[key] = [
            sim.add_dft_fields(
                components,
                frequency,
                0,
                1,
                center=mp.Vector3(rad, 0, z),
                size=mp.Vector3(),
            )
            for rad in r
        ]
        fluxes[key] = sim.add_flux(
            frequency, 0, 1, mp.FluxRegion(center=center, size=size, direction=mp.Z)
        )
    fluxes["side"] = sim.add_flux(
        frequency,
        0,
        1,
        mp.FluxRegion(
            center=mp.Vector3(extent, 0, 0.5), size=mp.Vector3(z=9), direction=mp.R
        ),
    )
    sim.run(until_after_sources=35)

    def read(key):
        return np.array(
            [
                [sim.get_dft_array(monitor, c, 0).item() for c in components]
                for monitor in fields[key]
            ]
        )

    early = read("air")
    early_time = sim.meep_time()
    sim.run(until=25)
    arrays = {key: read(key) for key in fields}
    np.savez_compressed(
        out,
        **arrays,
        r_um=r,
        air_early=early,
        input_flux=mp.get_fluxes(fluxes["input"])[0],
        output_flux=mp.get_fluxes(fluxes["air"])[0],
        side_flux=mp.get_fluxes(fluxes["side"])[0],
        resolution=resolution,
        radius_um=radius,
        pml_um=pml,
        straight=straight,
        n_eff=beta / K,
        meep_version=mp.__version__,
        case_sha256=sha256(CASE_PATH.read_bytes()).hexdigest(),
        components=["Er", "Ep", "Ez", "Z0Hr", "Z0Hp", "Z0Hz"],
        phasor="exp(-i omega t + i phi)",
        wavelength_um=WL,
        input_z_um=-4.0,
        air_z_um=CASE["plane_z_um"],
        source_z_um=-7.0,
        radial_pitch_um=0.25,
        linear_polarization="x",
        early_time=early_time,
        final_time=sim.meep_time(),
    )
    sim.reset_meep()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--resolution", type=int, default=8)
    parser.add_argument("--radius", type=float, default=44)
    parser.add_argument("--pml", type=float, default=2)
    parser.add_argument("--straight", action="store_true")
    args = parser.parse_args()
    capture(args.output, args.resolution, args.radius, args.pml, args.straight)
