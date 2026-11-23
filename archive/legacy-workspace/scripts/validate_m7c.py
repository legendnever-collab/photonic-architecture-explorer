"""Reproduce the trial and compare it with Frozen exact-q and M7-B evidence."""
import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import time

from m7c_workflow_trial import ROOT, design_two_ports, run_trial, render_trial, write_json


class EmbeddedTrial(HTMLParser):
    def __init__(self):
        super().__init__()
        self.recording = False
        self.payload = ""

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("id") == "trial-result":
            self.recording = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.recording = False

    def handle_data(self, text):
        if self.recording:
            self.payload += text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    evidence = {"status": "Running", "cases": {}}
    for label, name in (("equal-q", "m5a_two_ports.json"),
                        ("different-q", "m5f_different_q.json"),
                        ("high-divergence", "m5f_high_divergence.json")):
        document = json.loads((ROOT / "examples" / name).read_text())
        started = time.monotonic()
        exact = design_two_ports(document)
        exact_seconds = time.monotonic() - started
        report = run_trial(document)
        assert report["exact_result"] == report["design_result"] == exact
        assert report["fallback"] == {"state": "NotStarted"}
        assert report["state"] == ("Ineligible" if label == "high-divergence" else "NotNeeded")
        write_json(args.output_dir / (label + ".json"), report)
        evidence["cases"][label] = {
            "state": report["state"], "input_sha256": exact["input_sha256"],
            "exact_seconds": exact_seconds, "trial_seconds": report["elapsed_seconds"],
            "selected": exact["selected_candidate_id"], "exact_result_equal": True,
            "fallback_started": False,
        }

    command = [sys.executable, str(ROOT / "scripts/m7c_workflow_trial.py"),
               str(ROOT / "examples/m7a_smf_glass_proxy.json"),
               "--output-dir", str(args.output_dir / "smf-glass")]
    subprocess.run(command, check=True, timeout=660)
    trial = json.loads((args.output_dir / "smf-glass/trial.json").read_text())
    reference = json.loads((ROOT / "results/m7b_near_match.json").read_text())
    changed = [path for path, digest in reference["manifest"]["source_sha256"].items()
               if Path(path).name in {"design.py", "external.py", "gaussian.py", "geometry.py", "solver.py"}
               and hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest]
    evidence["physics_kernels_changed"] = bool(changed)
    assert not changed, changed
    assert trial["state"] == "Succeeded"
    assert trial["input_sha256"] == reference["input_sha256"]
    assert trial["exact_result"]["search"]["accepted_count"] == 0
    assert trial["fallback"]["adapter_calls"] == reference["adapter_calls"]
    assert len(trial["fallback"]["geometries"]) == len(reference["geometries"]) == 36
    for actual, expected in zip(trial["fallback"]["geometries"], reference["geometries"]):
        for key in ("geometry_id", "calls", "counts", "termination"):
            assert actual[key] == expected[key], (key, actual, expected)
        if actual["best"] is None:
            assert expected["best_overlap"] is None
        else:
            assert abs(actual["best"]["overlap"] - expected["best_overlap"]) <= 1e-10
    result = trial["design_result"]
    assert result["recommendation_policy"] == "M6C-PATH-WITH-TRADEOFFS-1"
    assert [candidate["id"] for candidate in result["candidates"]] == ["G036-NM"]
    assert len(trial["fallback"]["verified_observations"]) == 3
    for candidate in trial["fallback"]["verified_observations"]:
        assert candidate["independent_validation"]["status"] == "Pass"
        assert candidate["origin"]["input_sha256"] == trial["input_sha256"]
        assert candidate["evaluation"]["gaussian_mode_matching"]["normalized_mode_overlap"] == candidate["overlap"]
        for label in ("source", "target"):
            assert candidate["prescription"][label] == result["input_snapshot"][label]
    for key in ("actual_applicability", "physical_losses", "fabrication_yield", "patentability"):
        assert result[key]["status"] == "Uncomputed"
    html = EmbeddedTrial()
    html.feed((args.output_dir / "smf-glass/trial.html").read_text())
    assert json.loads(html.payload) == trial
    for path, digest in trial["provenance"]["source_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    counts = Counter()
    for row in trial["fallback"]["geometries"]:
        counts.update(row["counts"])
    candidate = result["candidates"][0]
    evidence["cases"]["smf-glass"] = {
        "state": trial["state"], "input_sha256": trial["input_sha256"],
        "trial_seconds": trial["elapsed_seconds"], "calls": trial["fallback"]["adapter_calls"],
        "counts": dict(counts), "all_36_search_summaries_match_m7b": True,
        "selected": result["selected_candidate_id"], "representatives": len(result["candidates"]),
        "overlap": candidate["overlap"], "ranking": candidate["ranking"],
        "independent_validation": candidate["independent_validation"],
        "html_json_equal": True, "provenance": trial["provenance"],
    }

    # Exercise actual optimizer cancellation after one complete geometry.
    flag = [False]
    document = result["input_snapshot"]
    cancelled = run_trial(document, cancelled=lambda: flag[0],
                          progress=lambda value: flag.__setitem__(0, True))
    assert cancelled["state"] == "Cancelled" and cancelled["design_result"] is None
    assert 0 < cancelled["fallback"]["adapter_calls"] < trial["fallback"]["adapter_calls"]
    assert 'data-candidate=' not in render_trial(cancelled)
    write_json(args.output_dir / "cancelled.json", cancelled)
    evidence["cancellation"] = {"state": cancelled["state"],
                                "calls": cancelled["fallback"]["adapter_calls"],
                                "seconds": cancelled["elapsed_seconds"], "recommendation_withheld": True}
    evidence["status"] = "Pass"
    write_json(args.output_dir / "acceptance.json", evidence)
    print(json.dumps({"status": "Pass", "selected": candidate["id"],
                      "overlap": candidate["overlap"], "seconds": trial["elapsed_seconds"]}))


if __name__ == "__main__":
    main()
