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
    apply_envelopes, boundary_distances, clearance_margin, margin_metrics, package_record, record,
    separation_distances,
)
from .external import adapt_ports, evaluate_external
from .inspector import ROOT
from .local_search import bounded_coordinates, exact_curvatures, geometry
from .near_match import make_prescription
from .near_match_reference import independent_check
from .pose_envelope import size_pose_envelope
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


def size_expansion(anchor, ports, reference, case, extra_m):
    """Size only World X for the frozen expansion prescription and replay the Adapter."""
    package = anchor["package"]
    baseline_volume = package["available_volume"]["value"]
    base_clearance = package["required_clearance_m"]["value"]
    bodies = [r["body_envelope"]["value"] for r in anchor["reflectors"]]
    chief_x = [ports.source.position[0], ports.target.position[0],
               *(mirror["vertex_m"]["value"][0] for mirror in anchor["design"]["reflectors"])]
    fixed_distances = [(gap, f"body[{mirror - 1}].volume", face)
                       for gap, mirror, face in boundary_distances(anchor) if face[0] != "X"]
    fixed_distances.extend(separation_distances(anchor))
    ceiling, path, face = min(fixed_distances, key=lambda row: row[0])
    maximum_extra = ceiling - base_clearance
    blocked = extra_m > maximum_extra

    # Replay a finite probe above the fixed limit to obtain the original Adapter
    # failure path. Larger requests have the same failure with World X unrestricted.
    pad_m = 1e-12  # Same outward rounding allowance as the R9 preset.
    required = ceiling + 2 * pad_m if blocked else base_clearance + extra_m
    x_min = min(min(chief_x), min(body["min_m"][0] for body in bodies) - required) - pad_m
    x_max = max(max(chief_x), max(body["max_m"][0] for body in bodies) + required) + pad_m
    proposal = deepcopy(anchor)
    volume = proposal["package"]["available_volume"]["value"]
    volume["min_m"][0], volume["max_m"][0] = x_min, x_max
    proposal["package"]["available_volume"] = record(volume, "m", "M7-R26 sized World X")
    proposal["package"]["required_clearance_m"] = record(required, "m", "M7-R26 total clearance")
    evaluation = evaluate_external(proposal)
    envelope = evaluation["package_feasibility"]["envelope_geometry"]
    result = {"candidate_id": "R8-expansion", "target_additional_m": extra_m,
              "baseline_clearance_m": base_clearance, "maximum_additional_m": maximum_extra,
              "limiting_check": None, "suggestion": None}
    if blocked:
        original = next((check for check in envelope["checks"] if check["path"] == path), None)
        if original and original["status"] == "Fail":
            return {**result, "status": "Limited", "limiting_check": {**original, "face": face},
                    "adapter_probe_clearance_m": required}
        return {**result, "status": "VerificationWithheld", "reason": "고정 검사 한계를 Adapter에서 재현하지 못했습니다."}

    eta = evaluation["gaussian_mode_matching"]["normalized_mode_overlap"]
    if (envelope["status"] != "Pass" or eta is None
            or any(evaluation[key]["status"] != "Pass" for key in ("input_contract", "geometry", "model_domain"))
            or evaluation["design_constraints"]["status"] == "Fail"):
        return {**result, "status": "VerificationWithheld", "reason": "제안 경계의 Adapter 검증을 통과하지 못했습니다.",
                "adapter_checks": [check for check in envelope["checks"] if check["status"] != "Pass"]}
    if extra_m == 0 and max(abs(actual - archived) for actual, archived in (
        (x_min, baseline_volume["min_m"][0]), (x_max, baseline_volume["max_m"][0])
    )) > 2e-12:
        return {**result, "status": "VerificationWithheld", "reason": "0 µm의 World X 경계가 R9 기준과 일치하지 않습니다."}

    try:
        measured = clearance_margin(proposal, evaluation)
    except ValueError as exc:
        return {**result, "status": "VerificationWithheld", "reason": str(exc)}
    guard = margin_metrics(evaluation, ports.target)
    if measured["minimum_gap_m"] < required or any(
        guard[key] > limit for key, limit in case["guard_margin_targets"].items()
    ):
        return {**result, "status": "VerificationWithheld", "reason": "Clearance 또는 Gaussian Guard 기준을 재현하지 못했습니다."}

    candidate = {"prescription": proposal, "evaluation": evaluation, "overlap": eta}
    try:
        validate_overlap(candidate, ports, reference["normalized_gaussian_overlap"])
    except EnvelopeValidationError as exc:
        return {**result, "status": "VerificationWithheld", "reason": str(exc)}
    quadrature = candidate["independent_validation"]["quadrature_overlap"]
    if min(eta, *quadrature) < case["min_normalized_gaussian_overlap"]:
        return {**result, "status": "VerificationWithheld", "reason": "독립 Quadrature에서 η 목표 충족을 확인하지 못했습니다."}
    width = x_max - x_min
    baseline_width = baseline_volume["max_m"][0] - baseline_volume["min_m"][0]
    return {**result, "status": "Verified", "suggestion": {
        "x_min_m": x_min, "x_max_m": x_max, "width_m": width, "r9_width_m": baseline_width,
        "width_increase_m": width - baseline_width, "required_clearance_m": required,
        "eta": eta, "quadrature": quadrature, "prescription": proposal,
        "achieved_additional_m": measured["minimum_gap_m"] - base_clearance,
        "prescription_sha256": digest(proposal), "adapter_checks": envelope["checks"],
    }}


def compare_envelopes(document, selected, *, x_limits_m=None, target_additional_m=None):
    if selected not in (*WIDTHS, "custom"):
        raise ValueError("지원되는 Package Envelope를 선택하세요.")
    if selected == "custom" and (
        x_limits_m is None or len(x_limits_m) != 2 or not all(math.isfinite(value) for value in x_limits_m)
        or not x_limits_m[0] < x_limits_m[1]
    ):
        raise ValueError("World X min과 max에 유한한 값을 입력하세요. min은 max보다 작아야 합니다.")

    if target_additional_m is not None and (not math.isfinite(target_additional_m) or target_additional_m < 0):
        raise ValueError("추가 Clearance 목표는 0 이상의 유한한 값이어야 합니다.")

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

    expansion_package = packages["expansion"]
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
    frozen = next(trial for identifier, trial in trials if identifier == "R8-expansion")
    anchor = {**frozen, "package": expansion_package}
    result["pose_envelope"] = size_pose_envelope(anchor, case, result["input_sha256"])
    if target_additional_m is not None:
        result["envelope_sizing"] = size_expansion(
            anchor, ports, reference["candidates"]["expansion"], case, target_additional_m)
    return result
