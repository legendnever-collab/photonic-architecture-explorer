"""One-page review based on the existing candidate and sensitivity data."""

from html import escape
import math

from .inspector import PROJECTIONS, plot_svg, visible_overlap
from .mode_match import loss_label
from .sensitivity import format_db


TIE_ATOL_DB = 1e-6
CONCEPT_LABELS = {
    "short_path": "최단 광경로",
    "smaller_footprint": "작은 Beam Footprint",
    "model_margin": "큰 Gaussian 모델 여유",
}

REVIEW_CSS = """
#candidate-review { margin: 12px 0 16px; }
.review-controls { display: flex; flex-wrap: wrap; gap: 8px; padding-bottom: 10px; }
.review-sheet { background: #fff; border: 1px solid #d6e0e7; border-radius: 10px; padding: 14px; }
.review-sheet h2 { margin: 0 0 5px; }
.review-sheet h3 { margin: 10px 0 4px; }
.review-sheet p { margin: 3px 0; overflow-wrap: anywhere; }
.review-sheet table { margin: 4px 0; }
.review-sheet th, .review-sheet td { text-align: left; padding: 3px 5px; vertical-align: top; }
.review-sheet th { border-bottom: 1px solid #ccdbe4; }
.review-sheet .review-columns { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 12px; }
.review-sheet .review-columns > div { min-width: 0; }
.review-sheet .review-figure { margin: 0; }
.review-sheet .review-figure svg { display: block; max-height: 225px; width: 100%; height: auto; }
.review-sheet code, .review-sheet td { overflow-wrap: anywhere; }
@media (max-width: 700px) {
  .review-sheet .review-columns { grid-template-columns: minmax(0,1fr); }
  .review-sheet .review-table { overflow: auto; }
}
@page { size: A4 portrait; margin: 12mm; }
@media print {
  body:has(#candidate-review) { color: #151e26; background: white; }
  body:has(#candidate-review) > header,
  main:has(#candidate-review) > :not(#candidate-review),
  #candidate-review .review-controls { display: none !important; }
  main:has(#candidate-review) { padding: 0; margin: 0; max-width: none; }
  #candidate-review { margin: 0; }
  #candidate-review #review-sheets[hidden] { display: block !important; }
  #candidate-review .review-sheet { border: 0; padding: 0; font-size: 9.5pt; }
  #candidate-review .review-sheet h2 { font-size: 16pt; }
  #candidate-review .review-sheet h3 { font-size: 10pt; }
  #candidate-review .review-sheet table { font-size: 8.5pt; table-layout: fixed; }
  #candidate-review .review-sheet .review-columns { grid-template-columns: repeat(2,minmax(0,1fr)); }
  #candidate-review .review-sheet .review-figure svg { max-height: 58mm; }
  #candidate-review table, #candidate-review figure { break-inside: avoid; }
}
"""


def build_candidate_review(result, sensitivity):
    if result["status"] != "Computed" or not result["candidates"]:
        return {"status": "Uncomputed"}
    candidates = result["candidates"]
    entries = {row["candidate_id"]: row["samples"] for row in sensitivity["candidates"]}
    scenarios = [row for row in sensitivity["scenarios"] if row["id"] != "nominal"]
    nominal_designs = [
        {"id": c["id"], "rank": i, "total_path_m": c["ranking"]["total_path_m"],
         "max_3w_footprint_curvature": c["ranking"]["max_3w_footprint_curvature"],
         "max_projected_radius_m": c["ranking"]["max_projected_radius_m"],
         "recommendation_role": c.get("recommendation_role")}
        for i, c in enumerate(candidates, start=1)
    ]
    reviews = {}
    for c, design in zip(candidates, nominal_designs):
        e = c["evaluation"]
        ports = {name: {**e["evaluated_ports"][name],
                        "reference_plane": c["prescription"][name]["reference_plane"]["value"]}
                 for name in ("source", "target")}
        readings = entries[c["id"]]
        profile = [readings[row["id"]].get("delta_loss_db") for row in scenarios]
        tied = []
        if all(value is not None for value in profile):
            for other_id, samples in entries.items():
                if other_id == c["id"]:
                    continue
                other = [samples[row["id"]].get("delta_loss_db") for row in scenarios]
                if all(b is not None and math.isclose(a, b, rel_tol=0., abs_tol=TIE_ATOL_DB)
                       for a, b in zip(profile, other)):
                    tied.append(other_id)
        reviews[c["id"]] = {
            **design,
            "ports": ports,
            "segment_lengths_m": e["geometry"]["lengths"],
            "overlap": visible_overlap(e),
            "mode_status": e["gaussian_mode_matching"]["status"],
            "geometry_status": e["geometry"]["status"],
            "domain_status": e["model_domain"]["status"],
            "model_scope": e["model_domain"]["scope"],
            "sensitivity_samples": readings,
            "sensitivity_ties": tied,
        }
    return {
        "status": "Computed", "input_sha256": result["input_sha256"],
        "recommended_candidate_id": result["selected_candidate_id"],
        "candidates": reviews, "nominal_designs": nominal_designs, "scenarios": scenarios,
        "tie_atol_db": TIE_ATOL_DB, "part_placement_status": sensitivity["part_placement_status"],
        "package_yield_status": sensitivity["package_yield_status"],
        "total_coupling_status": sensitivity["total_coupling_status"],
    }


def numbers(values, scale=1.):
    return ", ".join(f"{scale * value:.5g}" for value in values)


def render_review_sheet(review, candidate, adapted, active):
    identifier = candidate["id"]
    data = review["candidates"][identifier]
    digest = escape(review["input_sha256"])
    port_rows = []
    for name, port in data["ports"].items():
        plane = port["reference_plane"]
        frame = escape(plane["frame_id"][:40])
        plane_id = escape(plane["id"][:40])
        q = " / ".join(f"({numbers(axis, 1e3)})" for axis in port["complex_q_ts_m"])
        port_rows.append(f'<tr data-review-port="{name}"><th scope="row">{name.title()}<br>{frame} / {plane_id}</th>'
                         f'<td>{numbers(port["position_m"], 1e3)}</td><td>{numbers(port["direction"])}</td>'
                         f'<td>{q}</td></tr>')

    perturbations = []
    for row in review["scenarios"]:
        sample = data["sensitivity_samples"][row["id"]]
        loss = format_db(sample.get("mode_mismatch_loss_db"), sample.get("loss_status"))
        delta = format_db(sample.get("delta_loss_db"), sample.get("delta_status"), delta=True)
        perturbations.append(f'<tr data-review-scenario="{escape(row["id"])}">'
                             f'<th scope="row">{escape(row["label"])}</th><td>{loss}</td><td>{delta}</td></tr>')

    nominal_designs = []
    for design in review["nominal_designs"]:
        nominal_designs.append(f'<tr><th scope="row">{design["rank"]} · {escape(design["id"])}</th>'
                               f'<td>{design["total_path_m"] * 1e3:.3f}</td>'
                               f'<td>{design["max_3w_footprint_curvature"]:.6f}</td>'
                               f'<td>{design["max_projected_radius_m"] * 1e6:.2f}</td></tr>')

    # Show the fold from the principal projection with the largest plane-normal component.
    projection = max(PROJECTIONS, key=lambda key: abs(adapted.source.sagittal["XYZ".index(PROJECTIONS[key][2])]))
    plot = plot_svg(candidate["prescription"], candidate["evaluation"], adapted, projection, "review-" + identifier)
    eta = data["overlap"]
    eta_label = f"{eta:.6%}" if eta is not None else "Uncomputed"
    source = data["ports"]["source"]
    status = "추천" if identifier == review["recommended_candidate_id"] else "대안"
    concept_label = CONCEPT_LABELS.get(data["recommendation_role"], "")
    tie_note = ""
    if data["sensitivity_ties"]:
        tied_ids = ", ".join(escape(value) for value in data["sensitivity_ties"])
        tie_note = (f'<p data-review-ties>Target 상대 오차 응답은 {tied_ids}와 '
                    f'{review["tie_atol_db"]:.0e} dB 이내에서 같습니다. '
                    'Nominal 경로와 Footprint 지표는 아래 표에서 비교하세요.</p>')
    heading = escape(identifier)
    hidden = "" if active else " hidden"
    return f'''<section class="review-sheet" data-review-candidate="{heading}" data-input-sha="{digest}"{hidden}>
    <h2>Candidate Review · {heading}</h2>
    <p>{status} · <span data-review-concept>{concept_label}</span> · {escape(candidate["classification"])}</p>
    <p>Input SHA256 <code>{digest}</code></p>
    <h3>Fixed Ports</h3>
    <p>Vacuum λ {source["wavelength_m"] * 1e9:.6g} nm · Ambient n {source["ambient_index"]:.6g}</p>
    <div class="review-table"><table><thead><tr><th scope="col">Port / Plane</th><th scope="col">XYZ [mm]</th>
    <th scope="col">전파 방향</th><th scope="col">q t/s (Re, Im) [mm]</th></tr></thead>
    <tbody>{"".join(port_rows)}</tbody></table></div>
    <div class="review-columns"><div>
    <h3>Optical Path</h3>
    <p>Source → M1 → M2 → Target</p>
    <p data-review-length>Path {data["total_path_m"] * 1e3:.3f} mm</p>
    <p>구간 [mm] {numbers(data["segment_lengths_m"], 1e3)}</p>
    <figure class="review-figure">{plot}<figcaption>{projection} 투영 · 생략 축 {PROJECTIONS[projection][2]} · Equal Scale</figcaption></figure>
    <h3>Nominal Mode Match</h3>
    <p data-review-nominal>Overlap {eta_label} · Mode Mismatch Loss {loss_label(eta)}</p>
    <p>Geometry {escape(data["geometry_status"])} · Gaussian Domain {escape(data["domain_status"])}
    · Mode Match {escape(data["mode_status"])}</p>
    </div><div>
    <h3>Target-plane sensitivity</h3>
    <p>한 축씩 적용한 도착 빔의 상대 위치 또는 소각도 오차</p>
    <table><thead><tr><th scope="col">오차</th><th scope="col">Loss [dB]</th>
    <th scope="col">Δ [dB]</th></tr></thead><tbody>{"".join(perturbations)}</tbody></table>
    </div></div>
    <h3>Nominal 설계 비교</h3>{tie_note}
    <table><thead><tr><th scope="col">대표 후보</th><th scope="col">Path [mm]</th>
    <th scope="col">Max 3w·κ</th><th scope="col">Max Radius [µm]</th></tr></thead>
    <tbody>{"".join(nominal_designs)}</tbody></table>
    <h3>Model scope</h3>
    <p>{escape(data["model_scope"])}. 실제 부품 배치 공차 및 Off-vertex field handoff:
    <b data-review-placement>{escape(review["part_placement_status"])}</b>.</p>
    <p>Package Yield <b data-review-yield>{escape(review["package_yield_status"])}</b> ·
    Total Coupling <b data-review-coupling>{escape(review["total_coupling_status"])}</b></p></section>'''
