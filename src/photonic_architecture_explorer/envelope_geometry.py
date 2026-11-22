"""Shared nominal backing, AABB and Gaussian margin checks from M7-R7/R9."""
from .external import adapt_external
from .package_geometry import box_distance, patch_world_aabb


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


def limiting_boundary(proposal):
    low, high = box_bounds(proposal["package"]["available_volume"]["value"])
    distances = []
    for index, reflector in enumerate(proposal["reflectors"], start=1):
        body_low, body_high = box_bounds(reflector["body_envelope"]["value"])
        for axis, label in enumerate("XYZ"):
            distances.append((body_low[axis] - low[axis], index, label + "-"))
            distances.append((high[axis] - body_high[axis], index, label + "+"))
    gap, mirror, face = min(distances)
    return {"gap_m": gap, "mirror": mirror, "face": face}


def clearance_margin(proposal, evaluation):
    """Measure the three AABB clearances and tie the minimum to its Adapter check."""
    package = proposal["package"]
    required = package["required_clearance_m"]["value"]
    boundary = limiting_boundary(proposal)
    bodies = [box_bounds(r["body_envelope"]["value"]) for r in proposal["reflectors"]]
    keepouts = [box_bounds(k) for k in package["keepout_bodies"]["value"]]
    distances = [(boundary["gap_m"], f'body[{boundary["mirror"] - 1}].volume', boundary["face"]),
                 (box_distance(*bodies), "reflector_envelope_pair", None)]
    distances.extend((box_distance(body, keepout), f"body[{i}].keepout[{j}]", None)
                     for i, body in enumerate(bodies) for j, keepout in enumerate(keepouts))
    gap, path, face = min(distances, key=lambda distance: distance[0])
    checks = {check["path"]: check for check in evaluation["package_feasibility"]["envelope_geometry"]["checks"]}
    if any(checks.get(path, {}).get("status") != "Pass" for _, path, _ in distances):
        raise ValueError("AABB 거리의 Adapter 원본 판정을 확인하지 못했습니다.")
    return {"minimum_gap_m": gap, "additional_clearance_m": gap - required,
            "limiting_check": {**checks[path], "face": face},
            "nearest_envelope_face": boundary}
