"""Paired centered-point and component-native DFT monitors on the same Meep fields."""

import argparse
from pathlib import Path

import numpy as np

from scripts.m7r19_capture import NCL, WL, guide_simulation, guided_mode


def run(out, resolution, geometry, index, dual):
    import meep as mp

    freq = 1 / WL
    guide = geometry == "guide"
    if guide:
        sim = guide_simulation(resolution, 44, 2, True)
        if dual:
            # Same forward analytic HE11, adding the complementary magnetic sheet.
            _, mode = guided_mode()

            def profile(i, sign):
                return lambda p: sign * mode(p.x + 22.0)[0, i]

            sim.sources = [
                *sim.sources,
                *[
                    mp.Source(
                        mp.GaussianSource(freq, fwidth=0.18 * freq),
                        component=c,
                        center=mp.Vector3(22, 0, -7),
                        size=mp.Vector3(44),
                        amp_func=profile(i, sign),
                    )
                    for c, i, sign in [(mp.Hr, 1, 1), (mp.Hp, 0, -1)]
                ],
            ]
        components = [mp.Er, mp.Ep, mp.Ez, mp.Hr, mp.Hp, mp.Hz]
        names = ["Er", "Ep", "Ez", "Hr", "Hp", "Hz"]
        radii = (np.arange(172) + 0.5) / 4
    else:
        sim = mp.Simulation(
            dimensions=1,
            resolution=resolution,
            cell_size=mp.Vector3(z=28),
            default_material=mp.Medium(index=index),
            boundary_layers=[mp.PML(2)],
            force_complex_fields=True,
            sources=[
                mp.Source(
                    mp.GaussianSource(freq, fwidth=0.18 * freq),
                    component=mp.Ex,
                    center=mp.Vector3(z=-7),
                )
            ],
        )
        components, names = [mp.Ex, mp.Hy], ["Ex", "Hy"]
        radii = np.array([0.0])

    data = dict(
        resolution=resolution,
        geometry=geometry,
        dual=dual,
        index=index,
        r_um=radii,
        components=names,
        meep_version=mp.__version__,
    )
    monitors = []
    span = 43.5 if guide else 0.0
    for label, z in [("before", -9.0), ("input", -4.0), ("output", 5.0)]:
        extent = 43.0 if guide else 0.0
        flux = sim.add_flux(
            freq,
            0,
            1,
            mp.FluxRegion(
                center=mp.Vector3(extent / 2, 0, z),
                size=mp.Vector3(extent),
                direction=mp.Z,
            ),
        )
        if label == "before":
            monitors.append((label, z, flux, None, None, None))
            continue
        box = mp.Volume(
            center=mp.Vector3(span / 2, 0, z), size=mp.Vector3(span, 0, 12 / resolution)
        )
        native = sim.add_dft_fields(
            components, freq, 0, 1, where=box, yee_grid=True, decimation_factor=1
        )
        points = [
            sim.add_dft_fields(
                components, freq, 0, 1, center=mp.Vector3(r, 0, z), size=mp.Vector3()
            )
            for r in radii
        ]
        monitors.append((label, z, flux, native, points, box))
    sim.run(until_after_sources=60)
    data["dt"] = sim.fields.dt
    for label, z, flux, native, points, box in monitors:
        data[label + "_flux"] = mp.get_fluxes(flux)[0]
        if native is None:
            continue
        data[label + "_z"] = z
        data[label + "_centered"] = np.array(
            [[sim.get_dft_array(m, c, 0).item() for c in components] for m in points]
        )
        for name, c in zip(names, components):
            key = label + "_" + name
            raw = sim.get_dft_array(native, c, 0)
            dims, lo, hi = sim.get_array_slice_dimensions(c, vol=box)
            if tuple(dims) != raw.shape:
                raise ValueError(f"{key}: metadata {dims} vs array {raw.shape}")
            if guide:
                # Meep cylindrical slices are indexed (z,r); export (r,z).
                raw = raw.T
            if raw.shape[-1] != 1 + round((hi.z - lo.z) * resolution):
                raise ValueError("Axial coordinate count disagrees with native spacing")
            if guide and raw.shape[0] != 1 + round((hi.x - lo.x) * resolution):
                raise ValueError(
                    "Radial coordinate count disagrees with native spacing"
                )
            data[key] = raw
            data[key + "_z"] = np.linspace(lo.z, hi.z, raw.shape[-1])
            if guide:
                data[key + "_r"] = np.linspace(lo.x, hi.x, raw.shape[0])
    np.savez_compressed(out, **data)
    sim.reset_meep()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--geometry", choices=["plane", "guide"], required=True)
    parser.add_argument("--resolution", type=int, required=True)
    parser.add_argument("--cladding", action="store_true")
    parser.add_argument("--dual", action="store_true")
    args = parser.parse_args()
    args.folder.mkdir(parents=True, exist_ok=True)
    medium = "clad" if args.cladding else "air"
    name = (
        ("guide-dual" if args.dual else "guide")
        if args.geometry == "guide"
        else "plane-" + medium
    )
    run(
        args.folder / f"{name}-{args.resolution}.npz",
        args.resolution,
        args.geometry,
        NCL if args.cladding or args.geometry == "guide" else 1.0,
        args.dual,
    )
