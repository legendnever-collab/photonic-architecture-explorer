"""Executable integration trial; production Design/Workspace remain separate."""
import argparse
from collections import Counter
import copy
import hashlib
from html import escape
import itertools
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from photonic_architecture_explorer.design import (
    design_two_ports, distances, ranking, recommendation_key, select_concepts,
)
from photonic_architecture_explorer.external import adapt_ports, evaluate_external
from photonic_architecture_explorer.gaussian import DomainError
from photonic_architecture_explorer.geometry import add, sub, mul, norm, unit, dot
from photonic_architecture_explorer.solver import MIN_COSINE

POLICY = {
    "id": "M7C-WORKFLOW-TRIAL-1", "population": 32, "maxiter": 120,
    "seed_rule": "7100 + geometry index", "coordinate_bounds": [-1, 1],
    "strategy": "best1bin", "mutation": [.5, 1], "recombination": .7,
    "tol": 0, "atol": 0, "polish": False, "workers": 1, "updating": "immediate",
    "maximum_geometries": 64, "runtime_seconds": 600, "scipy": "1.17.0",
    "scope": "standalone integration trial; no production fallback enabled",
}


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
    from m7b_near_match import make_prescription, independent_check

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
                    record["source"] = "M7C near-match concept prescription; not a measured device fact"
            best.update(ranking=ranking(best["evaluation"], best["prescription"], best["id"]),
                        classification="Conceptual Geometry",
                        advantages=["Fixed Ports and frozen guards passed; approximate q match"],
                        limitations=exact["limitations"] + ["Near-Match trial; finite search, no global optimum"],
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
    result["limitations"] += ["Standalone Near-Match integration trial; no global feasibility/optimality guarantee"]
    return result


def run_trial(document, *, cancelled=lambda: False, progress=lambda value: None,
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
        exact = design_two_ports(document)
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


def render_trial(report):
    """Reuse physical geometry drawing; label the experimental workflow explicitly."""
    from photonic_architecture_explorer.external import adapt_external
    from photonic_architecture_explorer.inspector import plot_svg
    from photonic_architecture_explorer.mode_match import render_mode_match
    from photonic_architecture_explorer.mode_match import MODE_MATCH_CSS
    result = report.get("design_result") or {}
    panels = []
    for candidate in result.get("candidates", []):
        adapted = adapt_external(candidate["prescription"])
        metrics = candidate["ranking"]
        panels.append(f'<section data-candidate="{candidate["id"]}"><h2>{candidate["id"]}</h2>'
                      f'<p>Normalized Mode Overlap {candidate["evaluation"]["gaussian_mode_matching"]["normalized_mode_overlap"]:.12g}'
                      f' · Path {metrics["total_path_m"]*1000:.6f} mm'
                      f' · Footprint–Curvature margin {0.15-metrics["max_3w_footprint_curvature"]:.12g}</p>'
                      + plot_svg(candidate["prescription"], candidate["evaluation"], adapted, "Fold", candidate["id"])
                      + render_mode_match(candidate, report["input_sha256"], adapted) + '</section>')
    payload = json.dumps(report, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c").replace("&", "\\u0026")
    return ('<!doctype html><html lang="ko"><meta charset="utf-8"><title>M7-C Workflow Trial</title>'
            '<style>body{font:16px sans-serif;max-width:1000px;margin:20px auto;padding:12px}svg{width:100%;max-height:440px}'
            'pre{white-space:pre-wrap;overflow-wrap:anywhere}table{width:100%}'
            + MODE_MATCH_CSS + '</style><h1>M7-C Workflow Trial</h1>'
            '<p>Standalone Integration Prototype · Production Workspace에는 아직 연결되지 않았습니다.</p>'
            f'<p>State: {escape(report["state"])} · Input SHA256: {escape(report.get("input_sha256") or "Uncomputed")}</p>'
            '<p>Gaussian Proxy 계산입니다. Actual Applicability, 실제 Assembly Tolerance, Package Yield, '
            'Total Coupling 및 Patentability: Uncomputed. Guard margin은 조립 공차가 아닙니다.</p>'
            + (''.join(panels) or '<p>추천 및 Overlap: Uncomputed</p>')
            + f'<details><summary>Engineering Evidence</summary><pre>{escape(json.dumps(report,ensure_ascii=False,indent=2))}</pre></details>'
            + f'<script type="application/json" id="trial-result">{payload}</script></html>')


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temporary.replace(path)


def provenance():
    paths = sorted([*(ROOT / "src").rglob("*.py"), Path(__file__),
                    ROOT / "scripts/m7b_near_match.py", ROOT / "scripts/validate_m7c.py",
                    ROOT / "requirements-m7c.txt"])
    contract = (ROOT / "docs/M7C_NEAR_MATCH_WORKFLOW.md").read_text().split("## Reproduce and review")[0]
    return {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in paths},
        "contract_sha256": hashlib.sha256(contract.encode()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cancel-file", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    before = provenance()
    try:
        document = json.loads(args.input.read_text())
        report = run_trial(document, cancelled=lambda: bool(args.cancel_file and args.cancel_file.exists()),
                           progress=lambda value: write_json(args.output_dir / "progress.json", value))
    except (OSError, ValueError) as error:
        report = {"state": "Failed", "error": repr(error), "design_result": None}
    report["provenance"] = before
    after = provenance()
    if after["source_sha256"] != before["source_sha256"] or after["contract_sha256"] != before["contract_sha256"]:
        report.update(state="Failed", error="Source or frozen contract changed during execution", design_result=None)
    if args.cancel_file and args.cancel_file.exists():
        report.update(state="Cancelled", design_result=None)
    try:
        html = render_trial(report)
    except Exception as error:
        report.update(state="Failed", error=repr(error), design_result=None)
        html = render_trial(report)
    (args.output_dir / "trial.html").write_text(html)
    write_json(args.output_dir / "trial.json", report)
    print(json.dumps({key: report.get(key) for key in ("state", "input_sha256", "elapsed_seconds", "error")}))
    return 0 if report["state"] in ("Succeeded", "NotNeeded") else 1


if __name__ == "__main__":
    raise SystemExit(main())
