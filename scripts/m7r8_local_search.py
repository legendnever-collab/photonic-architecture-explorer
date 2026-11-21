"""Bounded a/c search around G029 using the R7 Package and model targets."""

import argparse
import hashlib
import itertools
import json
import math
from collections import Counter
from copy import deepcopy
from pathlib import Path

import numpy as np
from scipy.optimize import differential_evolution
from scipy.special import erfcinv

from photonic_architecture_explorer.design import POLICY as DESIGN_POLICY
from photonic_architecture_explorer.design import candidate_document
from photonic_architecture_explorer.local_search import geometry, exact_curvatures, bounded_coordinates
from photonic_architecture_explorer.external import adapt_ports, evaluate_external
from photonic_architecture_explorer.geometry import norm, sub
from photonic_architecture_explorer.near_match import make_prescription
from photonic_architecture_explorer.near_match_reference import independent_check
from photonic_architecture_explorer.solver import MAX_APERTURE_TAIL, MAX_FOOTPRINT_SLOPE
from scripts.m7r7_package import (
    APERTURE_DIAGNOSTIC_PATH,
    CASE_PATH,
    INPUT_PATH,
    REFERENCE_PATH,
    ROOT,
    apply_envelopes,
    box_bounds,
    load,
    margin_metrics,
    package_evidence,
    package_record,
    write,
)

PLAN_PATH = ROOT / "references/m7r8/search_plan.json"
INV_MM = 1e3


def expansion_required(proposal):
    """Face increments for the union of the two padded mirror AABBs."""
    package = proposal["package"]
    low, high = box_bounds(package["available_volume"]["value"])
    clearance = package["required_clearance_m"]["value"]
    bodies = [
        box_bounds(row["body_envelope"]["value"]) for row in proposal["reflectors"]
    ]
    return [
        [
            max(0.0, low[i] + clearance - min(body[0][i] for body in bodies))
            for i in range(3)
        ],
        [
            max(0.0, max(body[1][i] for body in bodies) + clearance - high[i])
            for i in range(3)
        ],
    ]


def expansion_recheck(candidate):
    proposal = deepcopy(candidate["prescription"])
    record = proposal["package"]["available_volume"]
    record["source"] = (
        "M7-R8 observed prescription, nominal envelope expansion diagnostic"
    )
    box = record["value"]
    for key, sign, shifts in zip(("min_m", "max_m"), (-1, 1), candidate["expansion_m"]):
        # A picometre of numerical slack avoids boundary-rounding at exact equality.
        box[key] = [
            x + sign * (shift + 1e-12 if shift else 0.0)
            for x, shift in zip(box[key], shifts)
        ]
    evaluation = evaluate_external(proposal)
    if evaluation["package_feasibility"]["envelope_geometry"]["status"] != "Pass":
        raise AssertionError("Derived enclosure does not pass unchanged Adapter")
    if not math.isclose(
        evaluation["gaussian_mode_matching"]["normalized_mode_overlap"],
        candidate["overlap"],
        abs_tol=1e-12,
        rel_tol=0,
    ):
        raise AssertionError("Envelope-only change altered the optical result")
    return box


def search(document, ports, case, plan, center_mm, aperture_scale):
    counts, package_failures, margin_failures = Counter(), Counter(), Counter()
    best = {}
    qualifying = set()
    seeds = {"optical": [], "package": []}
    scale = (
        case["guard_margin_targets"]["max_3w_footprint_curvature"] / MAX_FOOTPRINT_SLOPE
    )
    threshold = case["min_normalized_gaussian_overlap"]
    continuous = plan["continuous"]

    def evaluate(proposal, stage):
        counts["prescription_trials"] += 1
        counts[stage] += 1
        if counts["prescription_trials"] > plan["maximum_prescription_trials"]:
            raise ValueError("Preregistered prescription budget exceeded")
        proposal = apply_envelopes(proposal, case, aperture_scale)
        packed = evaluate_external(proposal)
        counts["adapter_evaluations"] += 1
        if packed["input_contract"]["status"] != "Pass":
            raise AssertionError("Frozen Adapter input failed")
        envelope = packed["package_feasibility"]["envelope_geometry"]
        if envelope["status"] not in {"Pass", "Fail"}:
            raise AssertionError("Nominal Package check incomplete")
        failed = [row["path"] for row in envelope["checks"] if row["status"] == "Fail"]
        package_failures.update(failed)
        for key in ("geometry", "model_domain", "design_constraints"):
            check = packed[key]
            if check["status"] == "Fail":
                counts[f"{key}: {check.get('reason', 'declared bounds')}"] += 1
                return 3.0, 3.0
        metrics = margin_metrics(packed, ports.target)
        excess = {
            key: metrics[key] - limit
            for key, limit in case["guard_margin_targets"].items()
            if metrics[key] > limit
        }
        if excess:
            margin_failures.update(excess.keys())
            return 2.0, 2.0
        counts["guard_margin_pass"] += 1

        optical = packed
        if failed:
            # Preserve the withheld Adapter outcome. Diagnose the same mirrors with
            # the envelope omitted to measure optical performance separately.
            optical = evaluate_external(
                {k: v for k, v in proposal.items() if k != "package"}
            )
            counts["adapter_evaluations"] += 1
        overlap = optical["gaussian_mode_matching"]["normalized_mode_overlap"]
        if overlap is None:
            raise AssertionError("Optical diagnostic did not return an overlap")
        shifts = expansion_required(proposal) if failed else [[0.0] * 3, [0.0] * 3]
        expansion = sum(map(sum, shifts))
        other_failure = any(not p.endswith(".volume") for p in failed)
        candidate = {
            "prescription": proposal,
            "evaluation": optical,
            "overlap": overlap,
            "packed": packed,
            "expansion_m": shifts,
        }
        if not failed:
            counts["nominal_package_and_margin_pass"] += 1
            if overlap >= threshold:
                counts["nominal_target_trials"] += 1
                points = tuple(
                    tuple(m["vertex_m"]["value"])
                    for m in proposal["design"]["reflectors"]
                )
                qualifying.add(points)
            if "nominal" not in best or overlap > best["nominal"]["overlap"]:
                best["nominal"] = candidate
        if "optical" not in best or overlap > best["optical"]["overlap"]:
            best["optical"] = candidate
        if overlap >= threshold and failed and not other_failure:
            previous = best.get("expansion")
            if previous is None or expansion < sum(map(sum, previous["expansion_m"])):
                best["expansion"] = candidate
        penalty = continuous["package_penalty_per_mm"] * expansion * INV_MM
        return 1 - overlap, 1 - overlap + penalty + float(other_failure)

    steps = round(plan["half_width_mm"] / plan["grid_step_mm"])
    offsets = np.arange(-steps, steps + 1) * plan["grid_step_mm"]
    names = tuple(seeds)
    for a_mm, c_mm in itertools.product(*(center + offsets for center in center_mm)):
        a, c = a_mm / INV_MM, c_mm / INV_MM
        vertices, normals, lengths, cosines = geometry(ports, a, c)
        counts["grid_geometries"] += 1
        branches = list(exact_curvatures(ports, lengths, cosines))
        if 2 * len(branches) > plan["grid_prescriptions_per_geometry_max"]:
            raise ValueError("Preregistered per-grid budget exceeded")
        for curvatures in branches:
            evaluate(
                candidate_document(
                    document, ports, vertices, normals, lengths, curvatures
                ),
                "grid_exact_q",
            )
            coordinates = bounded_coordinates(
                ports, lengths, cosines, curvatures, scale
            )
            proposal = make_prescription(
                document,
                ports,
                vertices,
                normals,
                lengths,
                np.array(coordinates) * scale,
            )
            scores = evaluate(proposal, "grid_bounded_seed")
            vector = [float(a_mm), float(c_mm), *coordinates]
            for key, score in zip(names, scores):
                seeds[key].append((score, vector))

    bounds = [(c - plan["half_width_mm"], c + plan["half_width_mm"]) for c in center_mm]
    bounds += [(-1.0, 1.0)] * 4
    low, high = np.array(bounds).T
    for index, (name, seed) in enumerate(zip(names, continuous["seeds"], strict=True)):
        population = np.random.default_rng(seed).uniform(
            low, high, (continuous["population"], 6)
        )
        # The top grid seeds retain access to the sharp phase matching window.
        for row, (_, vector) in enumerate(
            sorted(seeds[name])[: continuous["population"] // 4]
        ):
            population[row] = vector

        def objective(vector, stage=name, objective_index=index):
            vertices, normals, lengths, _ = geometry(
                ports, vector[0] / INV_MM, vector[1] / INV_MM
            )
            proposal = make_prescription(
                document, ports, vertices, normals, lengths, vector[2:] * scale
            )
            return evaluate(proposal, "continuous_" + stage)[objective_index]

        differential_evolution(
            objective,
            bounds,
            init=population,
            seed=seed,
            maxiter=continuous["maxiter"],
            polish=False,
            tol=0,
            atol=0,
        )
    if (
        sum(counts["continuous_" + name] for name in names)
        > continuous["maximum_prescription_trials"]
    ):
        raise ValueError("Preregistered continuous budget exceeded")
    if counts["adapter_evaluations"] > plan["maximum_adapter_evaluations"]:
        raise ValueError("Preregistered Adapter evaluation budget exceeded")
    return best, counts, package_failures, margin_failures, len(qualifying)


def candidate_summary(candidate, ports):
    prescription = candidate["prescription"]
    evaluation = candidate["evaluation"]
    reference = independent_check(candidate, ports)
    mirrors = prescription["design"]["reflectors"]
    return {
        "a_c_mm": [evaluation["geometry"]["lengths"][i] * INV_MM for i in (0, 2)],
        "path_mm": sum(evaluation["geometry"]["lengths"]) * INV_MM,
        "normalized_gaussian_overlap": candidate["overlap"],
        "quadrature_overlap": reference["quadrature_overlap"],
        "nominal_package": package_evidence(prescription, candidate["packed"]),
        "guard_metrics": margin_metrics(evaluation, ports.target),
        "mirror_prescriptions": mirrors,
        "additional_envelope_mm": [
            [x * INV_MM for x in face] for face in candidate["expansion_m"]
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    plan, case, fixed = map(load, (PLAN_PATH, CASE_PATH, INPUT_PATH))
    baseline = load(REFERENCE_PATH)
    digest = hashlib.sha256(
        json.dumps(fixed, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()
    if digest != baseline["input_sha256"] or case["id"] != plan["case"]:
        raise AssertionError("R7 inputs differ from the frozen case")
    document = {**fixed, "package": package_record(case)}
    ports = adapt_ports(document)
    anchor = next(row for row in baseline["candidates"] if row["id"] == plan["anchor"])
    first, last = [row["vertex_m"]["value"] for row in anchor["reflectors"]]
    center_mm = [
        norm(sub(first, ports.source.position)) * INV_MM,
        norm(sub(ports.target.position, last)) * INV_MM,
    ]
    aperture = load(APERTURE_DIAGNOSTIC_PATH)
    if aperture["id"] != plan["aperture_allocation"]:
        raise AssertionError("Frozen aperture profile differs")
    factor = float(
        erfcinv(aperture["fraction_of_existing_tail_guard"] * MAX_APERTURE_TAIL / 4)
        / math.sqrt(2)
    )
    aperture_scale = factor / DESIGN_POLICY["aperture_projected_radius_factor"]
    best, counts, package_failures, margin_failures, qualifying = search(
        document, ports, case, plan, center_mm, aperture_scale
    )
    candidates = {
        key: candidate_summary(candidate, ports) for key, candidate in best.items()
    }
    threshold = case["min_normalized_gaussian_overlap"]
    if "expansion" in best:
        if min(candidates["expansion"]["quadrature_overlap"]) < threshold:
            raise AssertionError(
                "Envelope diagnostic does not meet independent overlap threshold"
            )
        candidates["expansion"]["expanded_volume_adapter_pass"] = expansion_recheck(
            best["expansion"]
        )

    if qualifying and min(candidates["nominal"]["quadrature_overlap"]) < threshold:
        raise AssertionError("Independent overlap does not meet threshold")
    status = "Pass" if qualifying else "NoCandidate"
    report = {
        "search_id": plan["id"],
        "status": status,
        "fixed_input_sha256": digest,
        "range_ac_mm": [
            [c - plan["half_width_mm"], c + plan["half_width_mm"]] for c in center_mm
        ],
        "counts": dict(counts),
        "package_failure_checks": dict(package_failures),
        "margin_failure_checks": dict(margin_failures),
        "nominal_target_geometries": qualifying,
        "candidates": candidates,
        "finite_beam_clearance": "Uncomputed",
        "total_coupling": None,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write(args.output_dir / "summary.json", report)
    print(status, counts["prescription_trials"], qualifying, flush=True)


if __name__ == "__main__":
    main()
