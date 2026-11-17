"""Exercise the real CLI and Workspace against frozen two-Port acceptance cases."""

import argparse
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import subprocess
import sys

from photonic_architecture_explorer.workspace import Workspace, initial_values


ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ("equal-q", "examples/m5a_two_ports.json", "Computed"),
    ("different-q", "examples/m5f_different_q.json", "Computed"),
    ("high-divergence", "examples/m5f_high_divergence.json", "Fail"),
)


class ReviewFrame(HTMLParser):
    html = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "iframe" and attributes.get("id") == "design-review":
            self.html = attributes.get("srcdoc")


def multiply(left, right):
    return [[sum(left[i][k] * right[k][j] for k in range(2)) for j in range(2)] for i in range(2)]


def reference_mode(port, wavenumber):
    radii = [diameter / 2 for diameter in port["mfd_ts_m"]["value"]]
    curvature = port["wavefront_curvature_ts_per_m"]["value"]
    q = [1 / complex(c, -2 / (wavenumber * radius**2)) for radius, c in zip(radii, curvature)]
    return q, radii, curvature


def check_candidate(candidate, document, q_source, q_target, k):
    evaluation = candidate["evaluation"]
    prescription = candidate["prescription"]
    for name, q in (("source", q_source), ("target", q_target)):
        assert prescription[name] == document[name]
        actual = evaluation["evaluated_ports"][name]
        assert actual["position_m"] == document[name]["position_m"]["value"]
        assert actual["direction"] == document[name]["propagation_direction"]["value"]
        assert all(abs(complex(*pair) - expected) < 1e-15
                   for pair, expected in zip(actual["complex_q_ts_m"], q))
    assert evaluation["geometry"]["status"] == evaluation["model_domain"]["status"] == "Pass"
    mirrors = prescription["design"]["reflectors"]
    points = [document["source"]["position_m"]["value"],
              *(mirror["vertex_m"]["value"] for mirror in mirrors),
              document["target"]["position_m"]["value"]]
    segments = [[b - a for a, b in zip(start, end)] for start, end in zip(points, points[1:])]
    lengths = [math.hypot(*segment) for segment in segments]
    expected_lengths = evaluation["geometry"]["lengths"]
    assert max(abs(a - b) for a, b in zip(lengths, expected_lengths)) < 1e-12
    directions = [[component / length for component in ray] for ray, length in zip(segments, lengths)]
    for name, direction in zip(("source", "target"), (directions[0], directions[-1])):
        assert math.dist(direction, document[name]["propagation_direction"]["value"]) < 1e-10

    cosines = []
    for i, mirror in enumerate(mirrors):
        normal = mirror["illuminated_normal"]["value"]
        cosine = -sum(v * n for v, n in zip(directions[i], normal))
        cosines.append(cosine)
        reflected = [v + 2 * cosine * n for v, n in zip(directions[i], normal)]
        assert math.dist(reflected, directions[i + 1]) < 1e-10

    path = lambda length: [[1., length], [0., 1.]]
    for axis, (q_in, expected) in enumerate(zip(q_source, q_target)):
        transfer = path(lengths[0])
        for j, (mirror, cosine) in enumerate(zip(mirrors, cosines)):
            curvature = mirror["principal_curvature_ts_per_m"]["value"][axis]
            power = 2 * curvature / cosine if axis == 0 else 2 * curvature * cosine
            transfer = multiply(path(lengths[j + 1]), multiply([[1., 0.], [-power, 1.]], transfer))
        (a, b), (c, d) = transfer
        actual_q = (a * q_in + b) / (c * q_in + d)
        assert abs(actual_q - expected) < 2e-12
        output_axis = evaluation["gaussian_mode_matching"]["output_axes"][axis]
        report_q = complex(-output_axis["waist_distance_m"], output_axis["rayleigh_range_m"])
        assert abs(report_q - actual_q) < 2e-12
    overlap = evaluation["gaussian_mode_matching"]["normalized_mode_overlap"]
    assert abs(overlap - 1.) < 1e-10


def check_sensitivity(result, document, k):
    _, radii, curvature = reference_mode(document["target"], k)
    sensitivity = result["candidate_sensitivity"]
    assert sensitivity["status"] == "Approximate"
    assert sensitivity["target_reference_plane"] == document["target"]["reference_plane"]["value"]
    assert len(sensitivity["scenarios"]) == 9
    for candidate, entry in zip(result["candidates"], sensitivity["candidates"]):
        assert entry["candidate_id"] == candidate["id"]
        for row in sensitivity["scenarios"]:
            # Equal incident/target q. For each axis the normalized shifted-field
            # integral has squared magnitude exp(-(h/w)^2 - (k*w*(theta-C*h)/2)^2).
            exponent = sum((h / w)**2 + (k * w * (theta - c * h) / 2)**2
                           for h, theta, w, c in zip(row["offset_m"], row["slope_rad"], radii, curvature))
            sample = entry["samples"][row["id"]]
            assert sample["status"] == "Approximate"
            assert abs(sample["normalized_mode_overlap"] - math.exp(-exponent)) < 1e-9
            expected_delta = 10 * exponent / math.log(10)
            assert abs(sample["delta_loss_db"] - expected_delta) < 1e-8


def check_case(case_id, fixture, expected, directory):
    raw = fixture.read_bytes()
    document = json.loads(raw)
    process = subprocess.run(
        [sys.executable, "-m", "photonic_architecture_explorer.design", str(fixture),
         "--output-dir", str(directory)], capture_output=True, text=True, check=False,
    )
    assert process.returncode == (0 if expected == "Computed" else 1), process.stdout + process.stderr
    result = json.loads((directory / "design.json").read_text())
    assert result["status"] == expected
    assert result["input_snapshot"] == document
    assert result["input_sha256"] == hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()

    workspace = Workspace()
    workspace.templates["example"] = document
    workspace_html, http_status = workspace.post(initial_values(document, "example"))
    frame = ReviewFrame()
    frame.feed(workspace_html)
    assert http_status == 200
    assert frame.html == (directory / "design.html").read_text(), "CLI and Workspace report differ"
    assert result["fabrication_yield"]["status"] == "Uncomputed"
    assert result["physical_losses"] == {"status": "Uncomputed", "total_coupling": None}

    k = 2 * math.pi * document["ambient_index"]["value"] / document["wavelength_m"]["value"]
    q_source, _, _ = reference_mode(document["source"], k)
    q_target, _, _ = reference_mode(document["target"], k)
    if expected == "Computed":
        assert (q_source == q_target) == (case_id == "equal-q")
        assert result["candidates"]
        assert result["search"]["status"] == "Completed"
        assert result["selected_candidate_id"] == result["candidates"][0]["id"]
        for candidate in result["candidates"]:
            check_candidate(candidate, document, q_source, q_target, k)
        check_sensitivity(result, document, k)
    else:
        assert max(math.sqrt(2 / (k * q.imag)) for q in q_source) > 0.1
        assert result["reason"] == "Gaussian divergence exceeds 0.1 rad"
        assert result["search"]["status"] == "Not started"
        assert result["selected_candidate_id"] is None and result["candidates"] == []
        for key in ("candidate_review", "candidate_sensitivity"):
            assert result[key]["status"] == "Uncomputed"

    return {"id": case_id, "fixture": str(fixture.relative_to(ROOT)), "fixture_bytes_sha256": hashlib.sha256(raw).hexdigest(),
            "input_sha256": result["input_sha256"], "status": expected, "reason": result["reason"],
            "recommended": result["selected_candidate_id"], "candidate_ids": [c["id"] for c in result["candidates"]],
            "accepted_count": result["search"].get("accepted_count", 0),
            "q_source_m": [[q.real, q.imag] for q in q_source], "q_target_m": [[q.real, q.imag] for q in q_target]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "cases": [check_case(case_id, ROOT / fixture, expected, args.output_dir / case_id)
                  for case_id, fixture, expected in CASES],
    }
    (args.output_dir / "acceptance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
