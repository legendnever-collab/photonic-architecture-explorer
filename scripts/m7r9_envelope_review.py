"""Replay the frozen R8 prescriptions and compare their M6-D pose sensitivity."""

import argparse
import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path

from photonic_architecture_explorer.envelope_geometry import limiting_boundary
from photonic_architecture_explorer.external import adapt_external, evaluate_external
from photonic_architecture_explorer.near_match_reference import independent_check
from photonic_architecture_explorer.placement import (
    CASES_PER_CANDIDATE,
    ROTATION_RAD,
    TRANSLATION_M,
    placement_cases,
)
from photonic_architecture_explorer.solver import MAX_FOOTPRINT_SLOPE
from scripts.m7r7_package import (
    CASE_PATH,
    INPUT_PATH,
    ROOT,
    apply_envelopes,
    box_bounds,
    load,
    margin_metrics,
    package_evidence,
    package_record,
    record,
    write,
)

R8_SUMMARY = ROOT / "references/m7r8/summary.json"


def prescription(fixed, case, archived):
    proposal = {
        **deepcopy(fixed),
        "package": package_record(case),
        "reflectors": [
            {"surface_prescription": record("quadratic_patch", "model", "M7-R8")}
            for _ in archived["mirror_prescriptions"]
        ],
        "design": {"reflectors": deepcopy(archived["mirror_prescriptions"])},
    }
    if "expanded_volume_adapter_pass" in archived:
        proposal["package"]["available_volume"] = record(
            deepcopy(archived["expanded_volume_adapter_pass"]),
            "m",
            "M7-R8 envelope diagnostic",
        )
    return apply_envelopes(proposal, case, aperture_scale=None)


def review_candidate(fixed, case, archived):
    proposal = prescription(fixed, case, archived)
    if proposal["design"]["reflectors"] != archived["mirror_prescriptions"]:
        raise AssertionError("Frozen reflector prescription changed")

    adapted = adapt_external(proposal)
    evaluated = evaluate_external(proposal)
    package = package_evidence(proposal, evaluated)
    overlap = evaluated["gaussian_mode_matching"]["normalized_mode_overlap"]
    if package["envelope_geometry"] != "Pass" or overlap is None:
        raise AssertionError("Frozen R8 prescription did not reproduce")
    if not math.isclose(
        overlap, archived["normalized_gaussian_overlap"], abs_tol=1e-12, rel_tol=0
    ):
        raise AssertionError("Frozen R8 overlap changed")

    quadrature = independent_check(
        {"prescription": proposal, "evaluation": evaluated, "overlap": overlap}, adapted
    )["quadrature_overlap"]
    for actual, expected in zip(
        quadrature, archived["quadrature_overlap"], strict=True
    ):
        if not math.isclose(actual, expected, abs_tol=1e-12, rel_tol=0):
            raise AssertionError("Frozen R8 quadrature did not reproduce")

    guard = margin_metrics(evaluated, adapted.target)
    targets = case["guard_margin_targets"]
    margins = {key: limit - guard[key] for key, limit in targets.items()}
    if min(margins.values()) < 0:
        raise AssertionError("Frozen design guard targets did not reproduce")

    diagnostics = placement_cases(adapted.source, adapted.target, adapted.reflectors)
    if (
        diagnostics["nominal"]["status"] != "Computed"
        or len(diagnostics["cases"]) != CASES_PER_CANDIDATE
    ):
        raise AssertionError("Frozen M6-D nominal trace did not close")
    # The review reports signed Target-plane errors, with the full ray trace
    # available from the existing placement diagnostic when needed.
    for trace in [diagnostics["nominal"], *diagnostics["cases"]]:
        for key in ("hits", "target_point_m", "target_ray_direction", "target_slope"):
            trace.pop(key, None)

    clearance = proposal["package"]["required_clearance_m"]["value"]
    minimum_gap = min(
        package[key]
        for key in (
            "minimum_boundary_gap_m",
            "mirror_pair_aabb_gap_m",
            "minimum_body_keepout_aabb_gap_m",
        )
    )
    volume = proposal["package"]["available_volume"]["value"]
    low, high = box_bounds(volume)
    eta_target = case["min_normalized_gaussian_overlap"]
    return {
        "envelope": volume,
        "envelope_width_m": [upper - lower for lower, upper in zip(low, high)],
        "path_m": sum(evaluated["geometry"]["lengths"]),
        "package": package,
        "limiting_envelope_boundary": limiting_boundary(proposal),
        "minimum_aabb_gap_m": minimum_gap,
        "aabb_clearance_margin_m": minimum_gap - clearance,
        "guard_metrics": guard,
        "guard_target_margins": margins,
        "footprint_model_guard_margin": MAX_FOOTPRINT_SLOPE
        - guard["max_3w_footprint_curvature"],
        "normalized_gaussian_overlap": overlap,
        "quadrature_overlap": quadrature,
        "overlap_margin_to_target": overlap - eta_target,
        "meets_nominal_overlap_target": min(overlap, *quadrature) >= eta_target,
        "chief_ray_placement": diagnostics,
    }


def review():
    baseline, case, fixed = map(load, (R8_SUMMARY, CASE_PATH, INPUT_PATH))
    digest = hashlib.sha256(
        json.dumps(fixed, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()
    if digest != baseline["fixed_input_sha256"]:
        raise AssertionError("Frozen R8 Port input changed")
    candidates = {
        name: review_candidate(fixed, case, baseline["candidates"][name])
        for name in ("nominal", "expansion")
    }
    threshold_candidates = [
        name for name, row in candidates.items() if row["meets_nominal_overlap_target"]
    ]
    return {
        "package_case": case["id"],
        "package_input_provenance": case["evidence"],
        "fixed_input_sha256": digest,
        "minimum_clearance_m": case["minimum_envelope_clearance_mm"] * 1e-3,
        "nominal_overlap_target": case["min_normalized_gaussian_overlap"],
        "translation_m": TRANSLATION_M,
        "rotation_rad": ROTATION_RAD,
        "nominal_threshold_candidates": threshold_candidates,
        "candidates": candidates,
        "finite_beam_clearance": "Uncomputed",
        "perturbed_gaussian_mode_overlap": "Uncomputed",
        "actual_assembly_tolerance": "Uncomputed",
        "total_coupling": None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = review()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write(args.output_dir / "summary.json", result)


if __name__ == "__main__":
    main()
