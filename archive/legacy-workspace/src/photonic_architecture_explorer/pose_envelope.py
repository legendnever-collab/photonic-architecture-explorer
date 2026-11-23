"""Size the World X envelope for the frozen R8-expansion and R27 poses."""
from copy import deepcopy

from .diagnostics import ray_to_target
from .envelope_geometry import apply_envelopes, boundary_distances, record, separation_distances
from .external import InputIssue, adapt_external, read
from .gaussian import DomainError
from .package_geometry import assess_package
from .placement import reflector_poses

X_PAD_M = 1e-12  # R26 outward allowance for the AABB comparison.


def x_requirements(proposal, points, clearance):
    bodies = [reflector["body_envelope"]["value"] for reflector in proposal["reflectors"]]
    low = min((body["min_m"][0] - clearance, f"M{i}", "X-")
              for i, body in enumerate(bodies, 1))
    high = max((body["max_m"][0] + clearance, f"M{i}", "X+")
               for i, body in enumerate(bodies, 1))
    return (min(low, (min(point[0] for point in points), "Chief Ray", "X-")),
            max(high, (max(point[0] for point in points), "Chief Ray", "X+")))


def posed_prescription(anchor, case, mirrors, pose):
    proposal = deepcopy(anchor)
    if pose:
        index = pose["mirror"] - 1
        mirror = mirrors[index]
        design = proposal["design"]["reflectors"][index]
        if pose["kind"] == "translation":
            design["vertex_m"]["value"] = list(mirror.vertex)
        else:
            design["illuminated_normal"]["value"] = list(mirror.normal)
        apply_envelopes(proposal, case, aperture_scale=None)
    return proposal


def pose_label(pose):
    if not pose:
        return "Nominal"
    if pose["kind"] == "translation":
        motion = f'{pose["axis"]} {pose["delta_m"] * 1e6:+g} µm'
    else:
        motion = f'sagittal {pose["delta_rad"] * 1e3:+g} mrad'
    return f'M{pose["mirror"]} {motion}'


def check_pose(proposal, adapted, points):
    envelope = assess_package(proposal, adapted, read, InputIssue, chief_path=points)["envelope_geometry"]
    distances = [(gap, f"body[{mirror - 1}].volume", face)
                 for gap, mirror, face in boundary_distances(proposal)]
    distances.extend(separation_distances(proposal))
    gap, path, face = min(distances)
    return {"status": envelope["status"], "minimum_gap_m": gap,
            "limiting_check": {"path": path, "face": face},
            "adapter_checks": envelope["checks"]}


def size_pose_envelope(anchor, case, input_sha256):
    """Find the common interval, then verify each posed AABB and actual ray."""
    nominal = adapt_external(anchor)
    package = anchor["package"]
    original = package["available_volume"]["value"]
    clearance = package["required_clearance_m"]["value"]
    poses = [({}, nominal.reflectors), *(item for item in reflector_poses(
        nominal.reflectors, nominal.source.sagittal) if item[0]["axis"] != "Y")]
    result = {
        "candidate_id": "R8-expansion", "input_sha256": input_sha256,
        "required_clearance_m": clearance, "pose_count": len(poses), "suggestion": None,
        "baseline_package": package, "nominal_reflectors": anchor["design"]["reflectors"],
        "perturbed_gaussian_eta": "Uncomputed", "actual_assembly_tolerance": "Uncomputed",
        "finite_beam_clearance": "Uncomputed", "total_coupling": "Uncomputed",
    }
    bounds, inputs = [], []
    for pose, mirrors in poses:
        proposal = posed_prescription(anchor, case, mirrors, pose)
        adapted = adapt_external(proposal)
        label = pose_label(pose)
        try:
            ray = ray_to_target(adapted.source.position, adapted.source.direction,
                                adapted.target, adapted.reflectors, adapted.source.sagittal)
        except DomainError as exc:
            return {**result, "status": "VerificationWithheld", "reason": str(exc), "limiting_pose": label}
        points = [adapted.source.position, *(hit["position_m"] for hit in ray["hits"]), ray["target_point_m"]]
        bounds.append(x_requirements(proposal, points, clearance))
        inputs.append((label, pose, proposal, adapted, points))

    nominal_x = [bounds[0][0][0] - X_PAD_M, bounds[0][1][0] + X_PAD_M]
    low_index, low = min(enumerate(row[0] for row in bounds), key=lambda item: item[1][0])
    high_index, high = max(enumerate(row[1] for row in bounds), key=lambda item: item[1][0])
    limits = [low[0] - X_PAD_M, high[0] + X_PAD_M]
    limiting_sides = [{"pose": inputs[index][0], "limiting_element": body, "face": face}
                      for index, (_, body, face) in ((low_index, low), (high_index, high))]
    result.update(nominal_x_m=nominal_x, limiting_sides=limiting_sides, cases=[])
    if any(abs(x - original[key][0]) > 2e-12 for x, key in zip(nominal_x, ("min_m", "max_m"))):
        return {**result, "status": "VerificationWithheld", "reason": "명목 경계가 R26의 2 pm 허용차를 벗어났습니다."}

    for label, pose, proposal, adapted, points in inputs:
        baseline = check_pose(proposal, adapted, points)
        volume = deepcopy(original)
        volume["min_m"][0], volume["max_m"][0] = limits
        proposal["package"]["available_volume"] = record(volume, "m", "M7-R28 common World X")
        verification = check_pose(proposal, adapted, points)
        result["cases"].append({"pose": label, "perturbation": pose, "chief_path_m": [list(p) for p in points],
                                "baseline_minimum_gap_m": baseline["minimum_gap_m"],
                                "baseline_limiting_check": baseline["limiting_check"],
                                "baseline_status": baseline["status"],
                                "body_aabbs": [r["body_envelope"]["value"] for r in proposal["reflectors"]],
                                **verification})

    failing = [row for row in result["cases"]
               if row["status"] != "Pass" or row["minimum_gap_m"] < clearance]
    if failing:
        limiting = min(failing, key=lambda row: row["minimum_gap_m"])
        return {**result, "status": "VerificationWithheld", "limiting_pose": limiting["pose"],
                "limiting_check": limiting["limiting_check"],
                "failed_checks": [check["path"] for check in limiting["adapter_checks"] if check["status"] != "Pass"],
                "reason": "공통 World X 경계에서도 기구 또는 Chief Ray 검사 기준을 충족하지 못했습니다."}
    deltas = [x - baseline for x, baseline in zip(limits, nominal_x)]
    return {**result, "status": "Verified", "suggestion": {
        "x_min_m": limits[0], "x_max_m": limits[1], "x_min_change_m": deltas[0],
        "x_max_change_m": deltas[1], "width_m": limits[1] - limits[0],
        "width_increase_m": deltas[1] - deltas[0],
        "minimum_gap_m": min(row["minimum_gap_m"] for row in result["cases"]),
    }}
