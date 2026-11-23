"""Compare FMMAX power ledgers against the frozen R5/R6 Fourier exports."""

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.m7r13_target_acceptance import ROOT, verify_hash
from scripts.m7r14_guided_power import cross_normal

REPLAY_TOL = 1e-8
PORT_BUDGET = 2.5e-4


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit_run(archive, replay, name, digest):
    frozen_file = archive / (name + ".npz")
    verify_hash(frozen_file, digest)
    ledger = read_json(replay / (name + ".power.json"))
    verify_hash(archive / "case.json", ledger["case_sha256"])
    with np.load(frozen_file) as frozen, np.load(replay / frozen_file.name) as regenerated:
        for key in ("orders", "case_id", "case_sha256", "wavelength_um", "plane_z_um",
                    "ambient_index", "components", "period_um", "samples"):
            np.testing.assert_array_equal(frozen[key], regenerated[key], err_msg=key)
        if frozen["case_id"].item() != ledger["case_id"]:
            raise ValueError("Power ledger has the wrong case ID")
        coeff = frozen["coefficients"]
        replay_error = np.linalg.norm(coeff - regenerated["coefficients"]) / np.linalg.norm(coeff)
        orders, samples = frozen["orders"], int(frozen["samples"])
        area = (float(frozen["period_um"]) * 1e-6)**2

    # Resolve all pairwise Fourier products on a uniform periodic grid.
    if samples <= 2 * abs(orders).max():
        raise ValueError("The periodic product would alias in the flux quadrature")
    spectrum = np.zeros((4, samples, samples), dtype=complex)
    spectrum[:, orders[:, 0] % samples, orders[:, 1] % samples] = coeff[[0, 1, 3, 4]]
    field = np.fft.ifft2(spectrum) * samples**2
    grid_power = float(0.5 * area * np.mean(cross_normal(field[:2], field[2:].conj()).real))
    monitor_power = ledger["export_power_signed_m2"]["outgoing"]
    if min(grid_power, monitor_power) <= 0:
        raise ValueError("Expected positive local +z outgoing power")
    power_error = abs(grid_power / monitor_power - 1)
    if max(replay_error, power_error) > REPLAY_TOL:
        raise ValueError(f"{ledger['case_id']} {name}: field or power mismatch")
    return {**ledger, "frozen_npz_sha256": digest,
            "replay_coefficients_relative_l2": float(replay_error),
            "frozen_grid_outgoing_power_m2": grid_power,
            "grid_vs_monitor_relative_error": power_error}


def audit_port(replay, ref, manifest):
    archive = ROOT / "references" / ref
    case = read_json(archive / "case.json")
    fit = read_json(archive / manifest)["runs"]
    runs = {name: audit_run(archive, replay, name, fit[name]["sha256"])
            for name in case["runs"]}
    changes = {}
    for first, second in zip(("base", "grid", "basis"), ("grid", "basis", "window"), strict=True):
        a, b = runs[first], runs[second]
        changes[second] = {
            "delta_T": abs(b["T"] - a["T"]), "delta_R": abs(b["R"] - a["R"]),
            "relative_changes_in_center_normalized_power": {
                key: abs(b["export_power_signed_m2"][key] / value - 1)
                for key, value in a["export_power_signed_m2"].items()
            },
        }
    max_balance = max(r["balance_abs"] for r in runs.values())
    max_joint_error = max(r["joint_guide_vs_separate_abs"] for r in runs.values())
    if max_balance > case["power_balance_abs_limit"] or max_joint_error > REPLAY_TOL:
        raise ValueError(f"{case['case_id']}: power balance mismatch")
    ratio_screen = sum(max(c["delta_T"], c["delta_R"]) for c in changes.values()) + max_balance
    center_scale_screen = sum(max(c["relative_changes_in_center_normalized_power"].values())
                              for c in changes.values()) + max_balance
    return {"runs": runs, "refinement_changes": changes,
            "max_balance_abs": max_balance, "max_joint_guide_vs_separate_abs": max_joint_error,
            "facet_ratio_screen": ratio_screen,
            "facet_ratio_screen_within_budget": ratio_screen <= PORT_BUDGET,
            "center_normalized_power_screen": center_scale_screen,
            "center_normalized_power_screen_within_budget": center_scale_screen <= PORT_BUDGET}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("glass_capture", type=Path)
    parser.add_argument("smf_capture", type=Path)
    args = parser.parse_args()
    result = {
        "port_diagnostic_budget": PORT_BUDGET,
        "glass_reverse": audit_port(args.glass_capture, "m7r5", "result.json"),
        "smf_forward": audit_port(args.smf_capture, "m7r6", "fit.json"),
        "nominal_relay_guided_fraction": None,
    }
    print(json.dumps(result, indent=2, allow_nan=False))
