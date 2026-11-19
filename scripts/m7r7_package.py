"""Run the preregistered 1310 nm nominal Package and margin review."""

import argparse
import hashlib
import json
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path

from scipy.special import erfcinv

from photonic_architecture_explorer.design import POLICY as DESIGN_POLICY
from photonic_architecture_explorer.design import design_two_ports
from photonic_architecture_explorer.external import (
    adapt_external,
    adapt_ports,
    evaluate_external,
)
from photonic_architecture_explorer.near_match import (
    POLICY,
    eligible,
    search_near_match,
)
from photonic_architecture_explorer.near_match_reference import independent_check
from photonic_architecture_explorer.package_geometry import (
    box_distance,
    patch_world_aabb,
)
from photonic_architecture_explorer.placement import placement_cases
from photonic_architecture_explorer.solver import (
    MAX_APERTURE_TAIL,
    MAX_DIVERGENCE,
    MAX_FOOTPRINT_SLOPE,
)

ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = ROOT / "references/m7r7/case.json"
APERTURE_DIAGNOSTIC_PATH = CASE_PATH.with_name("aperture_diagnostic.json")
INPUT_PATH = ROOT / "examples/m7r6_smf_glass_1310.json"
REFERENCE_PATH = ROOT / "references/m7r6/design_summary.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, data):
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def record(value, unit, source):
    return {
        "value": value,
        "unit": unit,
        "provenance": "assumed",
        "source": source,
        "uncertainty": None,
    }


def world_box(low, high):
    return {
        "type": "aabb",
        "min_m": list(low),
        "max_m": list(high),
        "frame_id": "world",
    }


def from_mm(bounds):
    return world_box(*([x * 1e-3 for x in side] for side in bounds))


def box_bounds(box):
    return box["min_m"], box["max_m"]


def package_record(case):
    source = case["id"]
    return {
        "frame_id": record("world", "frame", source),
        "available_volume": record(from_mm(case["available_volume_mm"]), "m", source),
        "keepout_bodies": record(
            [from_mm(k["bounds"]) for k in case["keepouts_mm"]], "m", source
        ),
        "required_clearance_m": record(
            case["minimum_envelope_clearance_mm"] * 1e-3, "m", source
        ),
    }


def apply_envelopes(proposal, case, aperture_scale):
    """Attach declared bounds and derive a nominal solid envelope for each patch."""
    source = case["id"]
    cap = [a * 0.5e-3 for a in case["max_full_clear_aperture_ts_mm"]]
    for mirror, contract in zip(
        proposal["design"]["reflectors"], proposal["reflectors"], strict=True
    ):
        contract["half_aperture_bounds_m"] = record(
            [[0.0, a] for a in cap], "m", source
        )
        if aperture_scale is not None:
            generated = mirror["half_aperture_ts_m"]["value"]
            apertures = [
                min(a * aperture_scale, limit)
                for a, limit in zip(generated, cap, strict=True)
            ]
            mirror["half_aperture_ts_m"] = record(
                apertures,
                "m",
                source
                + f" generated half-aperture scaled by {aperture_scale:.12g} and capped",
            )
    adapted = adapt_external(proposal)
    padding = case["mirror_body_padding_mm"] * 1e-3
    depth = case["mirror_backing_depth_mm"] * 1e-3
    for mirror, contract in zip(
        adapted.reflectors, proposal["reflectors"], strict=True
    ):
        patch_low, patch_high = patch_world_aabb(mirror, adapted.source.sagittal)
        offset = [-depth * n for n in mirror.normal]
        low = [x + min(0.0, dx) - padding for x, dx in zip(patch_low, offset)]
        high = [x + max(0.0, dx) + padding for x, dx in zip(patch_high, offset)]
        contract["body_envelope"] = record(
            world_box(low, high), "m", source + " padded patch and backing AABB"
        )
    return proposal


def margin_metrics(evaluation, target):
    samples = evaluation["samples"]
    return {
        "max_3w_footprint_curvature": max(
            s["footprint_slope_3w"] for s in samples if "surface_radii_m" in s
        ),
        "max_post_mirror_divergence_rad": max(
            axis["divergence_rad"]
            for s in samples
            if s["plane"] in {"M1_after", "M2_after"}
            for axis in s["axes"]
        ),
        "fixed_target_divergence_rad": max(
            a["divergence_rad"] for a in target.mode.parameters()
        ),
        "aperture_tail_union_estimate": evaluation["model_domain"][
            "aperture_tail_union_estimate"
        ],
    }


def failed_paths(evaluation, section):
    checks = evaluation[section].get("checks", [])
    return [row["path"] for row in checks if row["status"] == "Fail"]


def package_evidence(proposal, evaluation):
    package = proposal["package"]
    low, high = box_bounds(package["available_volume"]["value"])
    bodies = [box_bounds(r["body_envelope"]["value"]) for r in proposal["reflectors"]]
    keepouts = [box_bounds(k) for k in package["keepout_bodies"]["value"]]
    return {
        "envelope_geometry": evaluation["package_feasibility"]["envelope_geometry"][
            "status"
        ],
        "failed_checks": failed_paths(evaluation, "design_constraints")
        + failed_paths(evaluation["package_feasibility"], "envelope_geometry"),
        "minimum_boundary_gap_m": min(
            min(bl - lo, hi - bh)
            for body in bodies
            for bl, bh, lo, hi in zip(*body, low, high)
        ),
        "mirror_pair_aabb_gap_m": box_distance(*bodies),
        "minimum_body_keepout_aabb_gap_m": min(
            box_distance(body, keepout) for body in bodies for keepout in keepouts
        ),
        "max_full_clear_aperture_m": max(
            2 * x
            for mirror in proposal["design"]["reflectors"]
            for x in mirror["half_aperture_ts_m"]["value"]
        ),
        "finite_beam_clearance": evaluation["package_feasibility"][
            "finite_beam_clearance"
        ]["status"],
    }


def binding_metrics(candidate, case, package_proposal=None, package_evaluation=None):
    proposal, evaluation = candidate["prescription"], candidate["evaluation"]
    adapted = adapt_external(proposal)
    placement = placement_cases(adapted.source, adapted.target, adapted.reflectors)
    metrics = margin_metrics(evaluation, adapted.target)
    return {
        "id": candidate["id"],
        "path_m": sum(evaluation["geometry"]["lengths"]),
        "normalized_gaussian_overlap": candidate["overlap"],
        "nominal_limits": metrics,
        "remaining_footprint_guard_margin": MAX_FOOTPRINT_SLOPE
        - metrics["max_3w_footprint_curvature"],
        "remaining_post_mirror_divergence_guard_margin_rad": (
            MAX_DIVERGENCE - metrics["max_post_mirror_divergence_rad"]
        ),
        "margin_targets_met": all(
            metrics[key] <= value for key, value in case["guard_margin_targets"].items()
        ),
        "overlap_target_met": candidate["overlap"]
        >= case["min_normalized_gaussian_overlap"],
        "placement": {"status": placement["status"], "summary": placement["summary"]},
        "package": package_evidence(
            package_proposal or proposal, package_evaluation or evaluation
        ),
        "package_screen_overlap": (package_evaluation or evaluation)[
            "gaussian_mode_matching"
        ]["normalized_mode_overlap"],
        "package_screen_aperture_tail": (package_evaluation or evaluation)[
            "model_domain"
        ].get("aperture_tail_union_estimate"),
        "independent_overlap": independent_check(candidate, adapted)[
            "quadrature_overlap"
        ],
    }


def replay_baseline(fixed, package, case, aperture_scale=None):
    reference = load(REFERENCE_PATH)
    reviewed = []
    expected = {"G036-NM", "G029-NM"}
    for row in reference["candidates"]:
        if row["id"] not in expected:
            continue
        proposal = {
            **deepcopy(fixed),
            "design": {"reflectors": deepcopy(row["reflectors"])},
            "reflectors": [
                {"surface_prescription": record("quadratic_patch", "model", "R6")}
                for _ in row["reflectors"]
            ],
        }
        evaluation = evaluate_external(proposal)
        eta = evaluation["gaussian_mode_matching"]["normalized_mode_overlap"]
        if eta is None or abs(row["overlap"] - eta) > 1e-12:
            raise AssertionError(f"Frozen R6 overlap differs for {row['id']}")
        with_package = apply_envelopes(
            {**deepcopy(proposal), "package": package}, case, aperture_scale
        )
        packaged_evaluation = evaluate_external(with_package)
        reviewed.append(
            binding_metrics(
                {
                    "id": row["id"],
                    "overlap": eta,
                    "prescription": proposal,
                    "evaluation": evaluation,
                },
                case,
                with_package,
                packaged_evaluation,
            )
        )
    if {row["id"] for row in reviewed} != expected:
        raise AssertionError("Both archived R6 candidates must be replayed")
    return reviewed


def search(fixed, exact, case, name, require_margin, aperture_scale):
    started = time.monotonic()
    report = {"versions": {}, "fallback": {}}
    failures = Counter()
    margin_failures = Counter()
    adapted = adapt_ports(fixed)
    targets = case["guard_margin_targets"]

    def checkpoint():
        if time.monotonic() - started > POLICY["runtime_seconds"]:
            raise TimeoutError(
                "Nominal review exceeded the existing per-search runtime budget"
            )

    def screen(proposal):
        proposal = apply_envelopes(proposal, case, aperture_scale)
        evaluation = evaluate_external(proposal)
        envelope = evaluation["package_feasibility"]["envelope_geometry"]
        failures.update(failed_paths(evaluation, "design_constraints"))
        if any(
            row["status"] != "Pass" and row["path"].startswith("package.")
            for row in envelope["checks"]
        ):
            raise ValueError("Invalid shared package records")
        failures.update(
            row["path"] for row in envelope["checks"] if row["status"] == "Fail"
        )
        reason = None
        if envelope["status"] not in {"Pass", "Fail"}:
            reason = "declared envelope screen incomplete"
        elif (
            require_margin
            and envelope["status"] == "Pass"
            and evaluation["model_domain"]["status"] == "Pass"
            and evaluation["design_constraints"]["status"] != "Fail"
        ):
            metrics = margin_metrics(evaluation, adapted.target)
            unmet = [key for key, upper in targets.items() if metrics[key] > upper]
            margin_failures.update(unmet)
            reason = ", ".join(unmet) or None
        return proposal, evaluation, reason

    scale = (
        targets["max_3w_footprint_curvature"] / MAX_FOOTPRINT_SLOPE
        if require_margin
        else 1.0
    )
    result = search_near_match(
        fixed,
        exact,
        report,
        checkpoint,
        lambda _: None,
        screen_candidate=screen,
        coordinate_scale=scale,
    )
    ledger = report["fallback"]
    invalid = Counter()
    best_rows = []
    for row in ledger["geometries"]:
        invalid.update(row["counts"])
        if row["best"]:
            best_rows.append(row["best"])
    valid = invalid.pop("valid_evaluations", 0)
    reviewed = [
        binding_metrics(candidate, case)
        for candidate in ledger["verified_observations"]
    ]
    summary = {
        "name": name,
        "aperture_scale": aperture_scale,
        "coordinate_scale": scale,
        "geometry_count": ledger["geometry_count"],
        "adapter_calls": ledger["adapter_calls"],
        "valid_evaluations": valid,
        "rejections_first_reason": dict(invalid),
        "failed_design_and_package_checks": dict(failures),
        "margin_checks_failed_where_package_and_model_passed": dict(margin_failures),
        "valid_geometries": len(best_rows),
        "geometries_meeting_overlap_target": sum(
            row["overlap"] >= case["min_normalized_gaussian_overlap"]
            for row in best_rows
        ),
        "selected_by_existing_ranking": result["selected_candidate_id"],
        "candidates": reviewed,
        "shortest_passing_geometry": min(
            (
                row
                for row in best_rows
                if row["overlap"] >= case["min_normalized_gaussian_overlap"]
            ),
            key=lambda row: row["ranking"]["total_path_m"],
            default=None,
        ),
    }
    return summary, ledger


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    case, fixed = load(CASE_PATH), load(INPUT_PATH)
    digest = hashlib.sha256(
        json.dumps(fixed, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()
    if digest != load(REFERENCE_PATH)["input_sha256"]:
        raise AssertionError("M7-R6 Fixed-Port input differs from archived evidence")
    package = package_record(case)
    package_input = {**fixed, "package": package}
    exact = design_two_ports(package_input)
    if not eligible(exact):
        raise AssertionError("R6 zero-candidate exact-q baseline did not reproduce")
    baseline = replay_baseline(fixed, package, case)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write(args.output_dir / "baseline.json", baseline)
    diagnostic = load(APERTURE_DIAGNOSTIC_PATH)
    projected_radius_factor = float(
        erfcinv(diagnostic["fraction_of_existing_tail_guard"] * MAX_APERTURE_TAIL / 4)
        / (2**0.5)
    )
    equal_tail_scale = (
        projected_radius_factor / DESIGN_POLICY["aperture_projected_radius_factor"]
    )
    resized = replay_baseline(fixed, package, case, aperture_scale=equal_tail_scale)
    profiles = []
    for name, require_margin, scale in (
        ("package_only", False, 1.0),
        ("package_and_margin", True, 1.0),
        ("equal_tail_package_and_margin", True, equal_tail_scale),
    ):
        summary, ledger = search(
            package_input, exact, case, name, require_margin, scale
        )
        profiles.append(summary)
        write(args.output_dir / (summary["name"] + "_ledger.json"), ledger)
        print(
            summary["name"],
            summary["valid_geometries"],
            summary["selected_by_existing_ranking"],
            flush=True,
        )
    review = {
        "case_id": case["id"],
        "fixed_input_sha256": digest,
        "scenario_input_sha256": exact["input_sha256"],
        "baseline": baseline,
        "aperture_diagnostic": {
            "projected_radius_factor": projected_radius_factor,
            "resized_archive": resized,
        },
        "searches": profiles,
        "status": "Pass"
        if any(profile["geometries_meeting_overlap_target"] for profile in profiles[1:])
        else "NoCandidate",
        "actual_package_feasibility": "Uncomputed",
        "perturbed_gaussian_mode_overlap": "Uncomputed",
        "total_coupling": None,
        "fabrication_yield": "Uncomputed",
    }
    write(args.output_dir / "summary.json", review)


if __name__ == "__main__":
    main()
