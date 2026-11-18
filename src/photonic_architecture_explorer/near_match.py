"""Bounded Near-Match orchestration extracted from the M7-B/M7-C references."""
from collections import Counter
import copy
import itertools
import time
import platform

from .design import design_two_ports, distances, ranking, recommendation_key, select_concepts, candidate_document
from .external import adapt_ports, evaluate_external
from .gaussian import DomainError
from .geometry import add, sub, mul, norm, unit, dot
from .solver import MIN_COSINE, MAX_FOOTPRINT_SLOPE

POLICY = {
    "id": "M7D-NEAR-MATCH-1", "population": 32, "maxiter": 120,
    "seed_rule": "7100 + geometry index", "coordinate_bounds": [-1, 1],
    "strategy": "best1bin", "mutation": [.5, 1], "recombination": .7,
    "tol": 0, "atol": 0, "polish": False, "workers": 1, "updating": "immediate",
    "maximum_geometries": 64, "runtime_seconds": 600, "scipy": "1.17.0",
    "scope": "bounded local background Gaussian near-match",
}


def make_prescription(document, ports, vertices, normals, lengths, coordinates):
    beam = ports.source.mode
    curvatures = []
    directions = (ports.source.direction, unit(sub(vertices[1], vertices[0])))
    for mirror in range(2):
        beam = beam.propagate(lengths[mirror])
        cosine = -dot(directions[mirror], normals[mirror])
        radii = [axis["radius_m"] for axis in beam.parameters()]
        limit = MAX_FOOTPRINT_SLOPE * (1 - 1e-10)
        kt = float(coordinates[2 * mirror]) * limit * cosine / (3 * radii[0])
        ks = float(coordinates[2 * mirror + 1]) * limit / (3 * radii[1])
        curvatures.append((kt, ks))
        beam = beam.power((2 * kt / cosine, 2 * ks * cosine))
    return candidate_document(document, ports, vertices, normals, lengths, curvatures)


class Stopped(Exception):
    def __init__(self, state):
        self.state = state


def eligible(exact):
    return (exact["input_contract"]["status"] == "Pass"
            and exact["search"]["status"] == "Completed"
            and exact["search"].get("accepted_count") == 0)


def search_near_match(document, exact, report, checkpoint, progress):
    # Optional reference dependencies are loaded only for an eligible fallback.
    import numpy as np
    import scipy
    from scipy.optimize import differential_evolution
    from .near_match_reference import independent_check

    if scipy.__version__ != POLICY["scipy"]:
        raise RuntimeError("Trial requires scipy==1.17.0")
    report["versions"].update(numpy=np.__version__, scipy=scipy.__version__)
    ports = adapt_ports(document)
    _, values = distances(ports.source, ports.target)
    if len(values)**2 > POLICY["maximum_geometries"]:
        raise RuntimeError("Geometry count exceeds frozen budget")
    maximum_calls = len(values)**2 * POLICY["population"] * (POLICY["maxiter"] + 1)
    fallback = report["fallback"]
    fallback.update(maximum_adapter_calls=maximum_calls, adapter_calls=0,
                    geometry_count=len(values)**2, geometries=[])
    accepted = []
    for number, (a, c) in enumerate(itertools.product(values, repeat=2), 1):
        checkpoint()
        row = {"geometry_id": f"G{number:03d}", "calls": 0, "counts": {}, "best": None}
        counts = Counter()
        best = None
        try:
            vertices = (add(ports.source.position, mul(ports.source.direction, a)),
                        sub(ports.target.position, mul(ports.target.direction, c)))
            b = norm(sub(vertices[1], vertices[0]))
            if b < 1e-9:
                raise DomainError("zero/short middle segment")
            middle = unit(sub(vertices[1], vertices[0]))
            normals = (unit(sub(middle, ports.source.direction)),
                       unit(sub(ports.target.direction, middle)))
            if min(-dot(ports.source.direction, normals[0]), -dot(middle, normals[1])) < MIN_COSINE:
                raise DomainError("incidence exceeds 70 degrees")
        except (DomainError, ArithmeticError) as error:
            row.update(termination="Geometry rejected", reason=str(error))
            fallback["geometries"].append(row)
            progress(fallback)
            continue

        def objective(coordinates):
            nonlocal best
            checkpoint()
            if fallback["adapter_calls"] >= maximum_calls:
                raise RuntimeError("Frozen evaluation budget exhausted")
            fallback["adapter_calls"] += 1
            row["calls"] += 1
            if fallback["adapter_calls"] % 64 == 0:
                progress(fallback)
            prescription = make_prescription(document, ports, vertices, normals, (a, b, c), coordinates)
            evaluation = evaluate_external(prescription)
            bad = [key for key in ("input_contract", "geometry", "model_domain")
                   if evaluation[key]["status"] != "Pass"]
            bad += [key for key in ("design_constraints", "package_feasibility")
                    if evaluation[key]["status"] == "Fail"]
            if bad:
                key = bad[0]
                counts[key + ": " + evaluation[key].get("reason", "incomplete evaluation")] += 1
                return 2.
            eta = evaluation["gaussian_mode_matching"].get("normalized_mode_overlap")
            if eta is None:
                raise RuntimeError("Unexpected incomplete Adapter result")
            counts["valid_evaluations"] += 1
            if best is None or eta > best["overlap"]:
                best = {"id": f"G{number:03d}-NM", "geometry_id": row["geometry_id"],
                        "overlap": eta, "coordinates": [float(v) for v in coordinates],
                        "prescription": prescription, "evaluation": evaluation}
            return 1 - eta

        population = np.random.default_rng(7100 + number).uniform(-1, 1, (32, 4))
        population[0] = 0.
        optimization = differential_evolution(
            objective, [(-1, 1)] * 4, strategy=POLICY["strategy"], init=population,
            seed=7100 + number, maxiter=POLICY["maxiter"], mutation=(.5, 1),
            recombination=.7, tol=0, atol=0, polish=False, workers=1, updating="immediate")
        row.update(counts=dict(counts), iterations=optimization.nit, termination=str(optimization.message))
        if best is not None:
            for mirror in best["prescription"]["design"]["reflectors"]:
                for record in mirror.values():
                    record["source"] = "M7D near-match concept prescription; not a measured device fact"
            best.update(ranking=ranking(best["evaluation"], best["prescription"], best["id"]),
                        classification="Conceptual Geometry",
                        advantages=["Fixed Ports and frozen guards passed; approximate q match"],
                        limitations=exact["limitations"] + ["Near-Match workflow; finite search, no global optimum"],
                        origin={"method": POLICY["id"], "seed": 7100 + number,
                                "input_sha256": exact["input_sha256"]})
            row["best"] = {key: best[key] for key in ("id", "overlap", "coordinates", "ranking")}
            accepted.append(best)
        fallback["geometries"].append(row)
        progress(fallback)
    chosen = select_concepts(accepted)
    verify = {candidate["id"]: candidate for candidate in sorted(accepted, key=recommendation_key)[:3] + chosen}
    for candidate in verify.values():
        checkpoint()
        candidate["independent_validation"] = independent_check(candidate, ports)
        for label in ("source", "target", "wavelength_m", "ambient_index", "coordinate_convention"):
            assert candidate["prescription"][label] == document[label]
        if "package" in document:
            assert candidate["prescription"]["package"] == document["package"]
    fallback["verified_observations"] = list(verify.values())
    result = copy.deepcopy(exact)
    result.update(candidates=chosen, selected_candidate_id=chosen[0]["id"] if chosen else None,
                  status="Computed" if chosen else "Fail",
                  reason="Guarded near-match trial completed" if chosen else "No candidate in finite trial",
                  search_policy=copy.deepcopy(POLICY))
    result["search"] = {"status": "Completed", "accepted_count": len(accepted),
                        "representatives": len(chosen), "geometry_count": len(values)**2,
                        "selection": "Unchanged M6-C policy over best valid observation per geometry"}
    result["limitations"] = [limit for limit in exact["limitations"] if "exact-matching family" not in limit]
    result["limitations"] += ["Bounded Near-Match workflow; no global feasibility/optimality guarantee"]
    return result


def run_workflow(document, *, exact_result=None, cancelled=lambda: False, progress=lambda value: None,
              clock=time.monotonic):
    started = clock()
    report = {"schema": "M7C-workflow-trial-1", "state": "Running", "policy": copy.deepcopy(POLICY),
              "versions": {"python": platform.python_version()},
              "exact_result": None, "design_result": None, "fallback": {"state": "NotStarted"}}

    def checkpoint():
        if cancelled():
            raise Stopped("Cancelled")
        if clock() - started >= POLICY["runtime_seconds"]:
            raise Stopped("TimedOut")

    try:
        checkpoint()
        exact = design_two_ports(document) if exact_result is None else copy.deepcopy(exact_result)
        report["exact_result"] = exact
        report["input_sha256"] = exact.get("input_sha256")
        checkpoint()
        if exact["candidates"]:
            report.update(state="NotNeeded", design_result=exact)
        elif not eligible(exact):
            report.update(state="Ineligible", design_result=exact)
        else:
            report["fallback"]["state"] = "Running"
            result = search_near_match(document, exact, report, checkpoint, progress)
            checkpoint()
            report.update(state="Succeeded" if result["candidates"] else "NoCandidate", design_result=result)
            report["fallback"]["state"] = report["state"]
    except Stopped as stopped:
        report.update(state=stopped.state, design_result=None)
        report["fallback"]["state"] = stopped.state
    except Exception as error:
        report.update(state="Failed", error=repr(error), design_result=None)
        report["fallback"]["state"] = "Failed"
    report["elapsed_seconds"] = clock() - started
    return report
