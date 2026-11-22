"""Two bounded R8 seed neighborhoods, re-screened under both R9 envelopes."""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from itertools import product
import json
import math

from scipy.special import erfcinv

from .design import POLICY, RANKING, ranking, recommendation_key
from .envelope_geometry import (
    apply_envelopes, limiting_boundary, margin_metrics, package_evidence, package_record, record,
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


def compare_envelopes(document, selected):
    case, aperture, archive, plan, reference = [
        json.loads((ROOT / name).read_text(encoding="utf-8")) for name in FILES]
    if digest(document) != archive["fixed_input_sha256"] or digest(document) != reference["fixed_input_sha256"]:
        raise ValueError("R9 Package의 Keepout과 Seed는 원본 Example A의 두 Port에 귀속됩니다. "
                         "편집한 Port를 설계하려면 Package Envelope를 해제하세요.")
    ports = adapt_ports(document)
    factor = erfcinv(aperture["fraction_of_existing_tail_guard"] * MAX_APERTURE_TAIL / 4) / math.sqrt(2)
    trials = list(proposals(document, ports, case, archive, plan["grid_step_mm"],
                            factor / POLICY["aperture_projected_radius_factor"]))
    if len(trials) > 74:
        raise ValueError("Envelope 탐색 예산을 초과해 추천을 보류했습니다.")
    summaries = {}
    for key in WIDTHS:
        baseline = reference["candidates"][key]
        package = package_record(case)
        if key == "expansion":
            package["available_volume"] = record(archive["candidates"][key]["expanded_volume_adapter_pass"],
                                                 "m", "M7-R8 expanded envelope")
        if (package["available_volume"]["value"] != baseline["envelope"]
                or package["required_clearance_m"]["value"] != reference["minimum_clearance_m"]):
            raise ValueError("R9 Envelope 또는 AABB Clearance 기준과 달라 추천을 보류했습니다.")
        snapshot = {**document, "package": package}
        input_sha = digest(snapshot)
        accepted, rejected = [], {}
        for identifier, trial in trials:
            candidate, failures = screen({**trial, "package": package}, ports, case, identifier)
            if candidate:
                accepted.append(candidate)
            else:
                rejected[identifier] = failures
        anchor_id = "R8-" + key
        anchor = next((row for row in accepted if row["id"] == anchor_id), None)
        if anchor is None or abs(anchor["overlap"] - baseline["normalized_gaussian_overlap"]) > OVERLAP_TOL:
            raise ValueError("R9의 Envelope 또는 기준 Overlap 재현에 실패해 추천을 보류했습니다.")
        accepted.sort(key=recommendation_key)
        best = accepted[0]
        for row in (anchor, best):
            if "independent_validation" not in row:
                try:
                    row["independent_validation"] = independent_check(row, ports)
                except AssertionError as exc:
                    raise ValueError("독립 ABCD·Quadrature 검산에 실패해 추천을 보류했습니다.") from exc
        passing_trials = []
        for row in accepted:
            boundary = limiting_boundary(row["prescription"])
            passing_trials.append({"id": row["id"], "overlap": row["overlap"],
                                   "max_projected_radius_m": row["ranking"]["max_projected_radius_m"],
                                   "nearest_envelope_face": boundary,
                                   "footprint_curvature": row["guard_metrics"]["max_3w_footprint_curvature"]})
        evidence = package_evidence(best["prescription"], best["evaluation"])
        min_gap = min(evidence[name] for name in ("minimum_boundary_gap_m", "mirror_pair_aabb_gap_m",
                                                  "minimum_body_keepout_aabb_gap_m"))
        counted = Counter(reason for reasons in rejected.values() for reason in reasons)
        summaries[key] = {
            "input_sha256": input_sha, "envelope": package["available_volume"]["value"],
            "passing_trials": passing_trials, "rejected": rejected,
            "rejection_counts": dict(counted), "evaluations": len(trials),
            "selected": best["id"], "overlap": best["overlap"], "minimum_gap_m": min_gap,
            "limiting_boundary": passing_trials[0]["nearest_envelope_face"], "max_projected_radius_m": best["ranking"]["max_projected_radius_m"],
            "guard_metrics": best["guard_metrics"], "quadrature": best["independent_validation"]["quadrature_overlap"],
            "threshold_met": min(best["overlap"], *best["independent_validation"]["quadrature_overlap"])
                             >= case["min_normalized_gaussian_overlap"],
            "r9_replay": {"id": anchor_id, "overlap": anchor["overlap"],
                          "absolute_error": abs(anchor["overlap"] - baseline["normalized_gaussian_overlap"]),
                          "quadrature": anchor["independent_validation"]["quadrature_overlap"]},
        }
        if key == selected:
            result = {"schema": "M7R23-envelope-design-1", "status": "Computed", "input_snapshot": snapshot,
                      "input_sha256": input_sha, "input_contract": {"status": "Pass"},
                      "selected_candidate_id": best["id"], "candidates": [best],
                      "search": {"status": "Completed", "accepted_count": len(accepted)},
                      "ranking_order": RANKING, "search_policy": {"id": "R8-local-seeds", "grid_step_mm": plan["grid_step_mm"],
                                                                 "maximum_trials_per_envelope": 74},
                      "limitations": ["Synthetic Package", "Finite-beam Clearance, Assembly Tolerance, Total Coupling: Uncomputed"]}
    result["envelope_comparison"] = {"selected": selected, "cases": summaries, "reference_files": FILES,
                                     "minimum_clearance_m": reference["minimum_clearance_m"],
                                     "target_overlap": case["min_normalized_gaussian_overlap"]}
    return result
