"""Re-screen the bounded R8 seed neighborhoods under declared World AABBs."""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from itertools import product
import json
import math

from scipy.special import erfcinv

from .design import POLICY, RANKING, ranking, recommendation_key
from .envelope_geometry import (
    apply_envelopes, clearance_margin, margin_metrics, package_record, record,
)
from .external import adapt_ports, evaluate_external
from .inspector import ROOT
from .local_search import bounded_coordinates, exact_curvatures, geometry
from .near_match import make_prescription
from .near_match_reference import independent_check
from .reference_redesign import OVERLAP_TOL
from .solver import MAX_APERTURE_TAIL, MAX_FOOTPRINT_SLOPE

WIDTHS = {"nominal": "4.30 mm", "expansion": "5.023725 mm"}
FILES = ("references/m7r7/case.json", "references/m7r7/aperture_diagnostic.json",
         "references/m7r8/summary.json", "references/m7r8/search_plan.json",
         "references/m7r9/summary.json")


R23_ACCEPTED_COUNTS = {"nominal": 19, "expansion": 48}
MAX_TRIALS = 74


class EnvelopeValidationError(ValueError):
    """A numerical or reference gate withheld the result."""


def digest(document):
    return sha256(json.dumps(document, sort_keys=True, allow_nan=False).encode()).hexdigest()


def proposals(document, ports, case, archive, step_mm, aperture_scale):
    scale = case["guard_margin_targets"]["max_3w_footprint_curvature"] / MAX_FOOTPRINT_SLOPE
    for key in WIDTHS:
        anchor = archive["candidates"][key]
        mirrors = deepcopy(anchor["mirror_prescriptions"])
        identifier = "R8-" + key
        frozen = {**document, "design": {"reflectors": mirrors}, "reflectors": [
            {"surface_prescription": record("quadratic_patch", "model", identifier)} for _ in mirrors]}
        yield identifier, apply_envelopes(frozen, case, None)
        for grid, offsets in enumerate(product((-1, 0, 1), repeat=2), 1):
            a, c = [(center + step_mm * delta) * 1e-3
                    for center, delta in zip(anchor["a_c_mm"], offsets, strict=True)]
            vertices, normals, lengths, cosines = geometry(ports, a, c)
            for branch, powers in enumerate(exact_curvatures(ports, lengths, cosines), 1):
                coordinates = bounded_coordinates(ports, lengths, cosines, powers, scale)
                generated = make_prescription(document, ports, vertices, normals, lengths,
                                              [value * scale for value in coordinates])
                yield f"{key}-G{grid}-B{branch}", apply_envelopes(generated, case, aperture_scale)


def screen(proposal, ports, case, identifier):
    evaluation = evaluate_external(proposal)
    envelope = evaluation["package_feasibility"]["envelope_geometry"]
    failures = [check["path"] for check in envelope.get("checks", []) if check["status"] == "Fail"]
    for key in ("input_contract", "geometry", "model_domain", "design_constraints"):
        stage = evaluation[key]
        if stage["status"] == "Fail" or (key != "design_constraints" and stage["status"] != "Pass"):
            failures.append(key + " · " + stage.get("reason", stage["status"]))
    if envelope["status"] != "Pass" or failures:
        return None, failures or ["Envelope · " + envelope["status"]]
    guard = margin_metrics(evaluation, ports.target)
    failures = [key for key, limit in case["guard_margin_targets"].items() if guard[key] > limit]
    eta = evaluation["gaussian_mode_matching"]["normalized_mode_overlap"]
    if failures or eta is None:
        return None, failures or ["Mode Overlap Uncomputed"]
    return {"id": identifier, "classification": "Synthetic Package · Guarded Near-Match",
            "prescription": proposal, "evaluation": evaluation, "overlap": eta,
            "ranking": ranking(evaluation, proposal, identifier), "guard_metrics": guard}, []


def validate_overlap(candidate, ports, expected=None):
    try:
        validation = independent_check(candidate, ports)
    except AssertionError as exc:
        raise EnvelopeValidationError("독립 ABCD·Quadrature 검산에 실패했습니다.") from exc
    eta = candidate["overlap"]
    quadrature = validation["quadrature_overlap"]
    target = eta if expected is None else expected
    if (validation["status"] != "Pass" or len(quadrature) != 2
            or not all(abs(value - target) <= OVERLAP_TOL for value in [eta, *quadrature])
            or not all(abs(value - eta) <= OVERLAP_TOL for value in quadrature)):
        raise EnvelopeValidationError("저장 η 또는 독립 Quadrature가 허용 오차를 벗어났습니다.")
    candidate["independent_validation"] = validation


def evaluate_envelope(snapshot, ports, case, trials, preset, reference):
    package = snapshot["package"]
    accepted, rejected = [], {}
    for identifier, trial in trials:
        candidate, failures = screen({**trial, "package": package}, ports, case, identifier)
        if candidate:
            accepted.append(candidate)
        else:
            rejected[identifier] = failures

    accepted.sort(key=recommendation_key)
    best = accepted[0] if accepted else None
    replay = None
    if preset:
        expected = reference["candidates"][preset]["normalized_gaussian_overlap"]
        if (len(accepted) != R23_ACCEPTED_COUNTS[preset]
                or best["id"] != "R8-" + preset):
            raise EnvelopeValidationError("R23 기준의 통과 처방 수 또는 최고 후보를 재현하지 못했습니다.")
        validate_overlap(best, ports, expected)
        replay = {"id": best["id"], "overlap": best["overlap"],
                  "absolute_error": abs(best["overlap"] - expected),
                  "quadrature": best["independent_validation"]["quadrature_overlap"]}
    elif best:
        validate_overlap(best, ports)

    passing_trials = []
    for row in accepted:
        try:
            row["clearance"] = clearance_margin(row["prescription"], row["evaluation"])
        except ValueError as exc:
            raise EnvelopeValidationError(str(exc)) from exc
        passing_trials.append({
            "id": row["id"], "overlap": row["overlap"],
            "max_projected_radius_m": row["ranking"]["max_projected_radius_m"],
            "footprint_curvature": row["guard_metrics"]["max_3w_footprint_curvature"],
            **row["clearance"],
        })

    target = case["min_normalized_gaussian_overlap"]
    clearance_selection = {"status": "NoTargetCandidate", "candidate": None}
    eligible = [row for row in accepted if row["overlap"] >= target]
    clearance_best = max(eligible, key=lambda row: row["clearance"]["additional_clearance_m"], default=None)
    if clearance_best:
        try:
            if clearance_best is not best:
                validate_overlap(clearance_best, ports)
            quadrature = clearance_best["independent_validation"]["quadrature_overlap"]
            if min(quadrature) < target:
                raise EnvelopeValidationError("독립 Quadrature에서 η 목표 충족을 확인하지 못했습니다.")
        except EnvelopeValidationError as exc:
            clearance_selection = {"status": "VerificationWithheld", "candidate": None, "reason": str(exc)}
            clearance_best = None
        else:
            clearance_selection = {
                "status": "Verified", "eligible_count": len(eligible),
                "candidate": next(row for row in passing_trials if row["id"] == clearance_best["id"]),
                "quadrature": quadrature,
            }
    candidates = [best] if best else []
    if clearance_best and clearance_best is not best:
        candidates.append({**clearance_best, "recommendation_role": "max_clearance"})

    summary = {
        "input_sha256": digest(snapshot), "envelope": package["available_volume"]["value"],
        "passing_trials": passing_trials, "rejected": rejected, "evaluations": len(trials),
        "rejection_counts": dict(Counter(reason for reasons in rejected.values() for reason in reasons)),
        "selected": None, "overlap": None, "minimum_gap_m": None, "limiting_boundary": None,
        "max_projected_radius_m": None, "guard_metrics": None, "quadrature": None,
        "threshold_met": None, "r9_replay": replay, "clearance_selection": clearance_selection,
    }
    if best:
        eta = best["overlap"]
        quadrature = best["independent_validation"]["quadrature_overlap"]
        summary.update(selected=best["id"], overlap=eta, minimum_gap_m=best["clearance"]["minimum_gap_m"],
                       limiting_boundary=passing_trials[0]["nearest_envelope_face"],
                       max_projected_radius_m=best["ranking"]["max_projected_radius_m"],
                       guard_metrics=best["guard_metrics"], quadrature=quadrature,
                       threshold_met=min(eta, *quadrature) >= case["min_normalized_gaussian_overlap"])
    return summary, candidates


def compare_envelopes(document, selected, *, x_limits_m=None):
    if selected not in (*WIDTHS, "custom"):
        raise ValueError("지원되는 Package Envelope를 선택하세요.")
    if selected == "custom" and (
        x_limits_m is None or len(x_limits_m) != 2 or not all(math.isfinite(value) for value in x_limits_m)
        or not x_limits_m[0] < x_limits_m[1]
    ):
        raise ValueError("World X min과 max에 유한한 값을 입력하세요. min은 max보다 작아야 합니다.")

    case, aperture, archive, plan, reference = [
        json.loads((ROOT / name).read_text(encoding="utf-8")) for name in FILES]
    if digest(document) != archive["fixed_input_sha256"] or digest(document) != reference["fixed_input_sha256"]:
        raise ValueError("R9 Package의 Keepout과 Seed는 원본 Example A의 두 Port에 귀속됩니다. "
                         "편집한 Port를 설계하려면 Package Envelope를 해제하세요.")
    packages = {key: package_record(case) for key in WIDTHS}
    packages["expansion"]["available_volume"] = record(
        archive["candidates"]["expansion"]["expanded_volume_adapter_pass"], "m", "M7-R8 expanded envelope")
    for key, package in packages.items():
        if (package["available_volume"]["value"] != reference["candidates"][key]["envelope"]
                or package["required_clearance_m"]["value"] != reference["minimum_clearance_m"]):
            raise EnvelopeValidationError("R9 Envelope 또는 AABB Clearance 기준을 재현하지 못했습니다.")

    matches = {key: key for key in WIDTHS}
    if selected == "custom":
        x_min, x_max = x_limits_m
        package = package_record(case)
        volume = package["available_volume"]["value"]
        volume["min_m"][0], volume["max_m"][0] = x_min, x_max
        matches = {"custom": next((key for key, package in packages.items()
                                   if package["available_volume"]["value"] == volume), None)}
        # The field mixes user-supplied X with synthetic R7 Y and Z.
        package["available_volume"] = {
            **record(volume, "m", "Workspace user-supplied World X min/max; Y/Z from M7-R7 synthetic preset"),
            "provenance": "supplied",
        }
        packages = {"custom": package}

    ports = adapt_ports(document)
    factor = erfcinv(aperture["fraction_of_existing_tail_guard"] * MAX_APERTURE_TAIL / 4) / math.sqrt(2)
    trials = list(proposals(document, ports, case, archive, plan["grid_step_mm"],
                            factor / POLICY["aperture_projected_radius_factor"]))
    if len(trials) != MAX_TRIALS:
        raise EnvelopeValidationError("기준 탐색의 처방 수를 재현하지 못했습니다.")
    summaries = {}
    for key, package in packages.items():
        snapshot = {**document, "package": package}
        summary, candidates = evaluate_envelope(snapshot, ports, case, trials, matches[key], reference)
        summaries[key] = summary
        if key == selected:
            result = {
                "schema": "M7R23-envelope-design-1", "status": "Computed" if candidates else "NoCandidate",
                "reason": "" if candidates else "이 World X 구간에서 74개 처방 중 통과한 후보가 없습니다.",
                "input_snapshot": snapshot, "input_sha256": summary["input_sha256"],
                "input_contract": {"status": "Pass"}, "selected_candidate_id": summary["selected"],
                "candidates": candidates,
                "search": {"status": "Completed", "accepted_count": len(summary["passing_trials"])},
                "ranking_order": RANKING, "search_policy": {"id": "R8-local-seeds",
                    "grid_step_mm": plan["grid_step_mm"], "maximum_trials_per_envelope": MAX_TRIALS},
                "limitations": ["Synthetic Package assumptions", "Finite-beam Clearance, Assembly Tolerance, Total Coupling: Uncomputed"],
            }
    result["envelope_comparison"] = {"selected": selected, "cases": summaries, "reference_files": FILES,
                                     "minimum_clearance_m": reference["minimum_clearance_m"],
                                     "target_overlap": case["min_normalized_gaussian_overlap"]}
    return result
