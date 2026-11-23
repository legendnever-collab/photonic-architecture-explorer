"""Replay the 1310 nm fit and run the existing fixed-Port design workflow."""

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from photonic_architecture_explorer.design import review_snapshot
from photonic_architecture_explorer.external import (
    CONVENTION,
    adapt_ports,
    evaluate_external,
)
from photonic_architecture_explorer.near_match import run_workflow
from photonic_architecture_explorer.near_match_reference import independent_check
from scripts.m7r5_fit import replay

ROOT = Path(__file__).resolve().parents[1]
SMF = ROOT / "references/m7r6"
GLASS = ROOT / "references/m7r5"
GLASS_FIELD_SHA256 = "b6ecb48919877a213f45581d9ec844164b60a1e0950d6a866fe82b9ee6f1b027"


def write(path, data):
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def record(value, unit, source, provenance="synthetic"):
    return {
        "value": value,
        "unit": unit,
        "provenance": provenance,
        "source": source,
        "uncertainty": None,
    }


def build_document(layout, smf, glass):
    """Bind approved external fits to the frozen layout; Target uses reciprocity."""
    source = "M7-R6 frozen nominal layout, reuses M7-A reference-plane centers and axes"
    document = {
        "contract_version": "M3A-1",
        "coordinate_convention": CONVENTION,
        "description": layout["case_id"]
        + ": 1310 nm simulated SMF and glass, scalar concept",
        "wavelength_m": record(
            1.310e-6, "m", "Common simulated vacuum wavelength", "simulated"
        ),
        "ambient_index": {
            **record(1.0, "1", "Homogeneous ideal air", "assumed"),
            "quantity": "external_ambient_refractive_index",
        },
    }
    for label, report in (("source", smf), ("target", glass)):
        placement = layout[label]
        field = report["runs"]["window"]
        field_source = (
            report["case_id"] + ", air-side +5 um fit, NPZ SHA256 " + field["sha256"]
        )
        sign = 1 if label == "source" else -1
        if label == "target":
            field_source += "; reciprocal acceptance, conjugated and t-reversed"
        plane = {
            "id": report["case_id"] + "-air-plus5um-" + label,
            "frame_id": "world",
            "side": "external",
            "origin_m": placement["position_m"],
            "normal": placement["propagation_direction"],
        }
        document[label] = {
            **{
                key: record(value, "m" if key == "position_m" else "1", source)
                for key, value in placement.items()
            },
            "reference_plane": record(plane, "plane", source),
            "mfd_ts_m": record(
                [value * 1e-6 for value in field["MFD_um_xy"]],
                "m",
                field_source,
                "simulated",
            ),
            "wavefront_curvature_ts_per_m": record(
                [sign * value for value in field["curvature_per_m_xy"]],
                "m^-1",
                field_source,
                "simulated",
            ),
            "polarization": record(
                {"treatment": "scalar_ignored", "jones_ts": [[1, 0], [0, 0]]},
                "1",
                "Dominant linear t component; mirror Jones transport is outside scalar model",
                "assumed",
            ),
            "mode_evidence": record(
                {"kind": "complex_field_fit"}, "evidence", field_source, "simulated"
            ),
        }
    return document


def run(out, capture_dir):
    smf = replay(capture_dir, SMF / "case.json")
    frozen_smf = json.loads((SMF / "fit.json").read_text(encoding="utf-8"))
    glass = json.loads((GLASS / "result.json").read_text(encoding="utf-8"))
    if (
        smf["nominal_simulated_fit"] != "Pass"
        or glass["nominal_simulated_fit"] != "Pass"
        or hashlib.sha256((GLASS / "window.npz").read_bytes()).hexdigest()
        != GLASS_FIELD_SHA256
        or glass["runs"]["window"]["sha256"] != GLASS_FIELD_SHA256
    ):
        raise RuntimeError(
            "Both simulated complex-field fits and the frozen Glass field are required"
        )
    observed = smf["runs"]["window"]
    frozen = frozen_smf["runs"]["window"]
    for key in ("MFD_um_xy", "curvature_per_m_xy"):
        if not all(
            math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-8)
            for a, b in zip(observed[key], frozen[key], strict=True)
        ):
            raise RuntimeError(f"Replayed fit differs from frozen SMF input: {key}")
    layout = json.loads((SMF / "layout.json").read_text(encoding="utf-8"))
    document = build_document(layout, frozen_smf, glass)
    fixture = json.loads(
        (ROOT / "examples/m7r6_smf_glass_1310.json").read_text(encoding="utf-8")
    )
    if document != fixture:
        raise RuntimeError(
            "Fixed-Port input differs from its frozen fit and layout records"
        )
    ports = adapt_ports(document)
    out.mkdir(parents=True, exist_ok=True)
    write(out / "fit.json", smf)
    write(out / "input.json", document)
    workflow = run_workflow(document)
    write(out / "workflow.json", workflow)
    if workflow["state"] not in {"NotNeeded", "Succeeded", "NoCandidate", "Ineligible"}:
        raise RuntimeError(
            f"Design workflow ended in {workflow['state']}: {workflow.get('error')}"
        )
    exact = workflow["exact_result"]
    result = workflow["design_result"]
    fallback = workflow["fallback"]
    if fallback["state"] in {"Succeeded", "NoCandidate"}:
        result = {
            **result,
            "workflow": {
                "near_match": {
                    key: fallback[key]
                    for key in (
                        "geometry_count",
                        "adapter_calls",
                        "maximum_adapter_calls",
                    )
                }
            },
        }
    write(out / "design.json", review_snapshot(result))
    near_counts = Counter()
    for geometry in fallback.get("geometries", []):
        near_counts.update(geometry["counts"])
    candidates = []
    selected_candidates = {
        candidate["id"]: candidate for candidate in result["candidates"]
    }
    for candidate in fallback.get("verified_observations", []):
        selected_candidates.setdefault(candidate["id"], candidate)
    for candidate in selected_candidates.values():
        prescription = candidate["prescription"]
        for key, value in document.items():
            if prescription[key] != value:
                raise AssertionError(f"Port input changed: {key}")
        evaluation = candidate["evaluation"]
        reevaluated = evaluate_external(prescription)
        # Near-Match finalizes reflector provenance after its first evaluation.
        # Compare the evaluated results separately from that prose snapshot.
        for key in evaluation.keys() - {"input_snapshot"}:
            if json.dumps(evaluation[key], sort_keys=True) != json.dumps(
                reevaluated[key], sort_keys=True
            ):
                raise AssertionError(f"Adapter replay differs from candidate: {key}")
        overlap = evaluation["gaussian_mode_matching"]["normalized_mode_overlap"]
        validation = candidate.get("independent_validation") or independent_check(
            {**candidate, "overlap": overlap}, ports
        )
        candidates.append(
            {
                "id": candidate["id"],
                "overlap": overlap,
                "mode_mismatch_dB": -10 * math.log10(overlap) if overlap > 0 else None,
                "aperture_tail_union_estimate": evaluation["model_domain"][
                    "aperture_tail_union_estimate"
                ],
                "segments_m": evaluation["geometry"]["lengths"],
                "incidence_cosines": evaluation["geometry"]["cosines"],
                "reflectors": prescription["design"]["reflectors"],
                "ranking": candidate["ranking"],
                "independent_validation": validation,
                "states": {
                    key: evaluation[key]["status"]
                    for key in (
                        "input_contract",
                        "geometry",
                        "model_domain",
                        "design_constraints",
                        "gaussian_mode_matching",
                        "package_feasibility",
                        "fabrication",
                        "actual_applicability",
                    )
                },
                "physical_losses": evaluation["physical_losses"],
            }
        )
    summary = {
        "case_id": layout["case_id"],
        "input_sha256": exact["input_sha256"],
        "workflow_state": workflow["state"],
        "nominal_design_status": result["status"],
        "reason": result["reason"],
        "source_q_m": [[q.real, q.imag] for q in ports.source.mode.q],
        "target_q_m": [[q.real, q.imag] for q in ports.target.mode.q],
        "exact_geometry_count": exact["search"].get("geometry_count"),
        "exact_attempt_count": len(exact["search"]["attempts"]),
        "exact_accepted": exact["search"].get("accepted_count"),
        "exact_rejections": exact["search"].get("rejection_counts", {}),
        "near_match_state": fallback["state"],
        "near_match_calls": fallback.get("adapter_calls"),
        "near_match_counts": dict(near_counts),
        "near_match_accepted_geometries": (
            result["search"].get("accepted_count")
            if fallback["state"] in {"Succeeded", "NoCandidate"}
            else None
        ),
        "selected": result["selected_candidate_id"],
        "candidates": candidates,
        "actual_device_applicability": "Uncomputed",
        "physical_losses": result["physical_losses"],
    }
    write(out / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--capture-dir", type=Path, default=SMF)
    args = parser.parse_args()
    run(args.output_dir, args.capture_dir)
