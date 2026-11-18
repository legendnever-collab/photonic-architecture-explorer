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
from photonic_architecture_explorer.near_match import run_workflow as run_trial











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
