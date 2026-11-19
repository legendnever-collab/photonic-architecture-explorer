"""Acquire the independent nominal 1310 nm guide facet case with FMMAX (CPU, x64)."""

import argparse
import hashlib
import json
from pathlib import Path

import fmmax as fm
import jax
import jax.numpy as jnp
import numpy as np

jax.config.update("jax_enable_x64", True)
CASE_PATH = Path(__file__).resolve().parents[1] / "references/m7r5/case.json"


def silica_index(wavelength_um):
    b = np.array([0.6961663, 0.4079426, 0.8974794])
    c = np.array([0.0684043, 0.1162414, 9.896161])
    return np.sqrt(1 + np.sum(b * wavelength_um**2 / (wavelength_um**2 - c**2)))


def capture(case, run, output):
    length, n = run["period_um"], run["samples"]
    wl = case["vacuum_wavelength_um"]
    ncl = silica_index(wl)
    coord = (np.arange(n) + 0.5) * length / n - length / 2
    rx, ry = case["index_1e_radii_um_xy"]
    index = ncl + case["delta_n"] * np.exp(
        -((coord[:, None] / rx) ** 2) - (coord[None, :] / ry) ** 2
    )
    lattice = fm.LatticeVectors(
        jnp.asarray([float(length), 0.0]), jnp.asarray([0.0, float(length)])
    )
    expansion = fm.generate_expansion(lattice, run["approx_terms"])

    def layer(eps):
        return fm.eigensolve_isotropic_media(
            jnp.asarray(wl),
            jnp.zeros(2),
            lattice,
            jnp.asarray(eps),
            expansion,
            fm.Formulation.FFT,
        )

    # Limiting absorption selects positive beta for forward propagating modes.
    # Roundoff in a strictly real stack can otherwise choose either square root.
    guide = layer(index**2 + 1j * case["passive_eps_imag_regulator"])
    air = layer([[case["ambient_index"] ** 2]])
    neff = np.asarray(guide.eigenvalues) * wl / (2 * np.pi)
    fundamental_pair = np.argsort(neff.real)[-2:]
    if not np.all(
        (neff[fundamental_pair].real > ncl)
        & (neff[fundamental_pair].real < index.max())
        & (abs(neff[fundamental_pair].imag) < 1e-9)
    ):
        raise ValueError(
            f"Fundamental guided pair unresolved: {neff[fundamental_pair]}"
        )
    excite = jnp.asarray(np.eye(len(neff))[:, fundamental_pair])
    (ex, ey, _), _ = fm.fields_from_wave_amplitudes(
        excite, jnp.zeros_like(excite), guide
    )
    x_fraction = np.asarray(
        jnp.sum(abs(ex) ** 2, axis=0) / jnp.sum(abs(ex) ** 2 + abs(ey) ** 2, axis=0)
    )
    which = int(np.argmax(x_fraction))
    if x_fraction[which] < case["incident_min_x_transverse_fraction"]:
        raise ValueError("x-polarized incident mode unresolved")
    inc = excite[:, which : which + 1]
    stack = fm.stack_s_matrix((guide, air), (jnp.asarray(0.0), jnp.asarray(0.0)))
    reflected, outgoing = stack.s21 @ inc, stack.s11 @ inc
    at_plane = fm.propagate_amplitude(outgoing, jnp.asarray(case["plane_z_um"]), air)
    zero = jnp.zeros_like(inc)
    e, h = fm.fields_from_wave_amplitudes(at_plane, zero, air)
    pin, pref = fm.amplitude_poynting_flux(inc, reflected, guide)
    pout, _ = fm.amplitude_poynting_flux(at_plane, zero, air)
    inc_flux = float(pin.sum())
    if inc_flux <= 0:
        raise ValueError("Non-forward incident flux")
    balance = abs(1 - float((pout.sum() - pref.sum()) / inc_flux))
    if balance > case["power_balance_abs_limit"]:
        raise ValueError("Facet power balance outside budget")

    # Transform FMMAX exp(-iwt) to engine convention, including Fourier order signs.
    orders = -np.asarray(expansion.basis_coefficients)
    coeff = np.stack([np.asarray(f[:, 0]).conj() for f in (*e, *h)])
    # Fix one arbitrary global complex scale by the on-axis Ex, common to all components.
    center = np.sum(coeff[0] * (-1.0) ** orders.sum(axis=1))
    coeff /= center
    # Check all six components at physical coordinates, including off-axis points.
    locations = length / 2 + np.array(
        [[0.0, 0.0], [1.1, 0.7], [-2.4, 3.1], [4.0, -1.3]]
    )
    samples_e, samples_h, _ = fm.fields_on_coordinates(
        e, h, air, jnp.asarray(locations[:, 0]), jnp.asarray(locations[:, 1])
    )
    solver_samples = np.stack(
        [np.asarray(f[:, 0]).conj() / center for f in (*samples_e, *samples_h)]
    )
    reconstructed = coeff @ np.exp(2j * np.pi * (orders @ locations.T) / length)
    export_error = np.max(abs(reconstructed - solver_samples))
    if export_error > 1e-9:
        raise ValueError(
            f"Fourier export differs from solver monitor by {export_error}"
        )
    np.savez_compressed(
        output,
        orders=orders,
        coefficients=coeff,
        case_id=case["case_id"],
        case_sha256=hashlib.sha256(
            CASE_PATH.read_text(encoding="utf-8").encode("utf-8")
        ).hexdigest(),
        wavelength_um=wl,
        plane_z_um=case["plane_z_um"],
        ambient_index=case["ambient_index"],
        components=["Ex", "Ey", "Ez", "Hx", "Hy", "Hz"],
        period_um=length,
        samples=n,
        n_cladding=ncl,
        n_eff=neff[fundamental_pair[which]].real,
        incident_x_fraction=x_fraction[which],
        power_balance_abs=balance,
        export_max_abs=export_error,
    )
    print(
        output,
        "terms",
        len(orders),
        "neff",
        neff[fundamental_pair[which]].real,
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--run", choices=("base", "grid", "basis", "window"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    config = json.loads(CASE_PATH.read_text())
    for name, spec in config["runs"].items():
        if args.run is None or args.run == name:
            capture(config, spec, args.output_dir / (name + ".npz"))
            jax.clear_caches()
