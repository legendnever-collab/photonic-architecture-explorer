"""Replay the fixed single-Port fit from the exported FMMAX monitor coefficients."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import roots_legendre

from photonic_architecture_explorer.applicability import gaussian_port_domain

REFERENCE = Path(__file__).resolve().parents[1] / "references/m7r5"


def monitor(data):
    n, length = int(data["samples"]), float(data["period_um"])
    orders = data["orders"]
    grid = np.zeros((3, n, n), complex)
    grid[:, orders[:, 0] % n, orders[:, 1] % n] = data["coefficients"][:3]
    return (np.arange(n) - n / 2) * length / n, np.fft.ifft2(grid) * n**2


def norm2(field):
    return np.sum(abs(field) ** 2)


def fit(axis, electric, case):
    ex, ey, ez = electric
    intensity = abs(ex) ** 2
    total = norm2(ex) + norm2(ey)
    x2, y2 = axis[:, None] ** 2, axis[None, :] ** 2
    # The second moments set optimizer scales only. The center and axes are fixed.
    sx2 = 4 * np.sum(x2 * intensity) / intensity.sum()
    sy2 = 4 * np.sum(y2 * intensity) / intensity.sum()
    xx, yy = x2 / sx2, y2 / sy2

    def gaussian(p):
        return np.exp(-(p[0] + 1j * p[2]) * xx - (p[1] + 1j * p[3]) * yy)

    def objective(p):
        g = gaussian(p)
        mixed = g.conj() * ex
        c = mixed.sum()
        gg = norm2(g)
        eta = abs(c) ** 2 / (gg * total)
        dc = np.array([-np.sum(mixed * xx), -np.sum(mixed * yy)])
        dc = np.r_[dc, -1j * dc]
        dg = -2 * np.array([np.sum(abs(g) ** 2 * xx), np.sum(abs(g) ** 2 * yy), 0, 0])
        gradient = 2 * (c.conj() * dc).real / (gg * total) - eta * dg / gg
        return -eta, -gradient

    opt = minimize(
        objective,
        [1.0, 1.0, 0.0, 0.0],
        jac=True,
        method="L-BFGS-B",
        bounds=[(1e-4, None)] * 2 + [(None, None)] * 2,
        options={"gtol": 1e-10, "ftol": 1e-15},
    )
    if not opt.success or np.max(abs(opt.jac)) > 1e-6:
        raise RuntimeError(f"Fit did not converge: {opt.message}")
    g = gaussian(opt.x)
    projection = np.sum(g.conj() * ex) / norm2(g)
    residual = ex - projection * g
    eta = -float(opt.fun)
    # Independent closure from the energy of the orthogonal residual, including Ey.
    if abs(eta - (1 - (norm2(residual) + norm2(ey)) / total)) > 1e-10:
        raise ValueError("Projection and field residual disagree")
    mask = intensity >= case["phase_mask_min_relative_intensity"] * intensity.max()
    phase_difference = np.angle(ex[mask] * (projection * g[mask]).conj())
    rms = np.sqrt(np.average(phase_difference**2, weights=intensity[mask]))
    w = np.sqrt(np.array([sx2, sy2]) / opt.x[:2])
    k = 2 * np.pi * case["ambient_index"] / case["vacuum_wavelength_um"]
    curvature = 2 * opt.x[2:] / (k * np.array([sx2, sy2]))
    return {
        "eta_transverse": eta,
        "loss_dB": float(-10 * np.log10(eta)),
        "phase_rms_rad": float(rms),
        "phase_mask_Ex_energy_fraction": float(intensity[mask].sum() / intensity.sum()),
        "MFD_um_xy": (2 * w).tolist(),
        "curvature_per_m_xy": (1e6 * curvature).tolist(),
        "Ey_transverse_fraction": float(norm2(ey) / total),
        "Ez_all_E_fraction": float(norm2(ez) / (total + norm2(ez))),
    }


def spectral_overlap(data, fit_result, case):
    """Independent integration of the exported Fourier series against the fixed fit."""
    period = float(data["period_um"])
    orders = data["orders"]
    ex, ey = data["coefficients"][:2]
    nodes, weights = roots_legendre(96)
    x, weights = nodes * period / 2, weights * period / 2
    k = 2 * np.pi * case["ambient_index"] / case["vacuum_wavelength_um"]
    integrals = []
    g_norm = 1.0
    for j in range(2):
        w = fit_result["MFD_um_xy"][j] / 2
        c = fit_result["curvature_per_m_xy"][j] * 1e-6
        g = np.exp(-((x / w) ** 2) - 0.5j * k * c * x**2)
        harmonics = np.exp(2j * np.pi * orders[:, j, None] * (x / period + 0.5))
        integrals.append(harmonics @ (weights * g.conj()))
        g_norm *= np.sum(weights * abs(g) ** 2)
    inner = np.sum(ex * integrals[0] * integrals[1])
    return float(abs(inner) ** 2 / (g_norm * period**2 * (norm2(ex) + norm2(ey))))


def compare_fields(a, b):
    # The integer grids are nested. Compare on shared physical coordinates only.
    ax, ea = a
    bx, eb = b
    common, ia, ib = np.intersect1d(ax, bx, return_indices=True)
    if len(common) != min(len(ax), len(bx)):
        raise ValueError("Non-nested capture grids")
    ea = ea[:, ia][:, :, ia]
    eb = eb[:, ib][:, :, ib]
    ea = ea / np.sqrt(norm2(ea))
    eb = eb / np.sqrt(norm2(eb))
    piston = np.angle(np.sum(ea.conj() * eb))
    return float(np.sqrt(norm2(ea - eb * np.exp(-1j * piston))))


def replay(directory):
    case = json.loads((REFERENCE / "case.json").read_text())
    metrics, fields = {}, {}
    for name, spec in case["runs"].items():
        path = directory / (name + ".npz")
        with np.load(path, allow_pickle=False) as data:
            if (
                str(data["case_id"]) != case["case_id"]
                or str(data["case_sha256"])
                != hashlib.sha256(
                    (REFERENCE / "case.json")
                    .read_text(encoding="utf-8")
                    .encode("utf-8")
                ).hexdigest()
                or int(data["samples"]) != spec["samples"]
                or float(data["period_um"]) != spec["period_um"]
            ):
                raise ValueError(
                    f"{name}: capture metadata differs from the registered case"
                )
            axis, electric = monitor(data)
            fields[name] = axis, electric
            metrics[name] = fit(axis, electric, case)
            metrics[name]["eta_fourier_quadrature"] = spectral_overlap(
                data, metrics[name], case
            )
            metrics[name].update(
                {
                    k: float(data[k])
                    for k in (
                        "n_eff",
                        "n_cladding",
                        "incident_x_fraction",
                        "power_balance_abs",
                        "export_max_abs",
                    )
                }
            )
            metrics[name].update(
                terms=len(data["orders"]),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
    deltas = {}
    for a, b in (("base", "grid"), ("grid", "basis"), ("basis", "window")):
        deltas[a + "_" + b] = {
            "E_relative_l2": compare_fields(fields[a], fields[b]),
            "delta_loss_dB": abs(metrics[a]["loss_dB"] - metrics[b]["loss_dB"]),
            "delta_phase_rad": abs(
                metrics[a]["phase_rms_rad"] - metrics[b]["phase_rms_rad"]
            ),
        }
    numerical = all(
        d["E_relative_l2"] <= case["field_delta_l2_limit"]
        and d["delta_loss_dB"] <= case["numerical_reserve_dB"]
        and d["delta_phase_rad"] <= case["convergence_max_delta_phase_rms_rad"]
        for d in deltas.values()
    )
    quality = all(
        m["power_balance_abs"] <= case["power_balance_abs_limit"]
        and m["incident_x_fraction"] >= case["incident_min_x_transverse_fraction"]
        and m["export_max_abs"] <= 1e-9
        and abs(m["eta_transverse"] - m["eta_fourier_quadrature"]) <= 1e-5
        for m in metrics.values()
    )
    ref = metrics["window"]
    accepted = (
        ref["loss_dB"] + case["numerical_reserve_dB"]
        <= case["single_port_fit_limit_dB"]
        and ref["phase_rms_rad"] <= case["phase_rms_limit_rad"]
    )
    status = ("Pass" if accepted else "Fail") if numerical and quality else "Uncomputed"
    precheck = (
        gaussian_port_domain(
            case["vacuum_wavelength_um"] * 1e-6,
            case["ambient_index"],
            [d * 1e-6 for d in ref["MFD_um_xy"]],
            ref["curvature_per_m_xy"],
        )
        if status == "Pass"
        else {"status": "Uncomputed"}
    )
    return {
        "case_id": case["case_id"],
        "nominal_simulated_fit": status,
        "fitted_port_divergence": precheck,
        "runs": metrics,
        "convergence": deltas,
        "actual_device_fit": None,
        "two_port_overlap": None,
        "total_coupling": None,
    }


if __name__ == "__main__":
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("capture_dir", type=Path, nargs="?", default=REFERENCE)
    report = replay(args.parse_args().capture_dir)
    print(json.dumps(report, indent=2, allow_nan=False))
