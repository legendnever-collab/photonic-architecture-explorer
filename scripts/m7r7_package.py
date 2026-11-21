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
from photonic_architecture_explorer.envelope_geometry import (
    apply_envelopes, box_bounds, failed_paths, margin_metrics,
    package_evidence, package_record, record,
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
