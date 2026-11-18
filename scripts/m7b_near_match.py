"""Bounded M7-B benchmark using the existing production adapter."""
import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import scipy
from scipy.optimize import differential_evolution

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from photonic_architecture_explorer.design import candidate_document, design_two_ports, distances
from photonic_architecture_explorer.external import adapt_ports, evaluate_external
from photonic_architecture_explorer.geometry import add, sub, mul, norm, unit, dot
from photonic_architecture_explorer.solver import MAX_FOOTPRINT_SLOPE

from photonic_architecture_explorer.near_match import make_prescription
from photonic_architecture_explorer.near_match_reference import independent_check

FIXTURE = ROOT / "examples/m7a_smf_glass_proxy.json"
MAX_CALLS = 36 * 32 * 121






def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    manifest = {
        "status": "Running",
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
        "maximum_adapter_calls": MAX_CALLS,
        "source_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((ROOT / "src").rglob("*.py"))
        },
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "contract_sha256": hashlib.sha256((ROOT / "docs/M7B_GUARDED_NEAR_MATCH.md").read_bytes()).hexdigest(),
    }
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    try:
        if scipy.__version__ != "1.17.0":
            raise RuntimeError("Reproduction requires scipy==1.17.0")
        document = json.loads(FIXTURE.read_text())
        ports = adapt_ports(document)
        baseline = design_two_ports(document)
        assert baseline["search"]["geometry_count"] == 36
        assert baseline["search"]["accepted_count"] == 0
        assert baseline["search"]["rejection_counts"] == {
            "model_domain: 3w projected footprint/curvature exceeds 0.15": 141,
            "model_domain: Gaussian divergence exceeds 0.1 rad": 3,
        }
        _, values = distances(ports.source, ports.target)
        geometries = []
        total_calls = 0
        for number, (a, c) in enumerate(itertools.product(values, repeat=2), 1):
            vertices = (add(ports.source.position, mul(ports.source.direction, a)),
                        sub(ports.target.position, mul(ports.target.direction, c)))
            middle = unit(sub(vertices[1], vertices[0]))
            normals = (unit(sub(middle, ports.source.direction)),
                       unit(sub(ports.target.direction, middle)))
            lengths = (a, norm(sub(vertices[1], vertices[0])), c)
            counts = Counter()
            best = None
            calls = 0

            def objective(coordinates):
                nonlocal best, calls, total_calls
                if total_calls >= MAX_CALLS or time.monotonic() - started > 600:
                    raise RuntimeError("Frozen evaluation or runtime budget exhausted")
                calls += 1
                total_calls += 1
                prescription = make_prescription(document, ports, vertices, normals, lengths, coordinates)
                evaluation = evaluate_external(prescription)
                for stage in ("input_contract", "geometry", "model_domain", "design_constraints", "package_feasibility"):
                    if evaluation[stage]["status"] == "Fail":
                        counts[stage + ": " + evaluation[stage].get("reason", "failed")] += 1
                        return 2.
                eta = evaluation["gaussian_mode_matching"].get("normalized_mode_overlap")
                if eta is None:
                    raise RuntimeError("Unexpected incomplete adapter result")
                counts["valid_evaluations"] += 1
                if best is None or eta > best["overlap"]:
                    best = {"id": f"G{number:03d}-NM", "overlap": eta,
                            "coordinates": [float(v) for v in coordinates],
                            "prescription": prescription, "evaluation": evaluation}
                return 1 - eta

            population = np.random.default_rng(7100 + number).uniform(-1, 1, (32, 4))
            population[0] = 0.
            result = differential_evolution(
                objective, [(-1, 1)] * 4, strategy="best1bin", init=population,
                seed=7100 + number, maxiter=120, mutation=(.5, 1), recombination=.7,
                tol=0, atol=0, polish=False, workers=1, updating="immediate")
            row = {"geometry_id": f"G{number:03d}", "calls": calls, "counts": dict(counts),
                   "iterations": result.nit, "termination": str(result.message), "best": best}
            geometries.append(row)
            # Preserve completed geometry evidence on a later failure.
            (args.output_dir / "progress.json").write_text(json.dumps(geometries, indent=2) + "\n")
            print(number, calls, None if best is None else best["overlap"], flush=True)
        top = sorted([g["best"] for g in geometries if g["best"]], key=lambda item: -item["overlap"])[:3]
        for candidate in top:
            candidate["independent_validation"] = independent_check(candidate, ports)
            for label in ("source", "target"):
                assert candidate["prescription"][label] == document[label]
        report = {"input_snapshot": document, "input_sha256": baseline["input_sha256"],
                  "exact_q_search": baseline["search"], "geometries": geometries, "top": top,
                  "adapter_calls": total_calls, "threshold": .9,
                  "threshold_met": bool(top and top[0]["overlap"] >= .9),
                  "actual_applicability": "Uncomputed", "assembly_tolerance": "Uncomputed",
                  "package_yield": "Uncomputed", "total_coupling": None}
        path = args.output_dir / "result.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
        manifest.update(status="Pass", result_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    except Exception as error:
        manifest.update(status="Fail", error=repr(error))
        raise
    finally:
        manifest["elapsed_seconds"] = time.monotonic() - started
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
