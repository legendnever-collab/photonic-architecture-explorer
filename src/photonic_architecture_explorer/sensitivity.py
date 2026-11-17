"""Compare received-mode sensitivity on the fixed Target reference plane."""

from html import escape
import math

from .external import adapt_external
from .gaussian import DomainError, mode_overlap
from .inspector import visible_overlap
from .mode_match import arrived_mode


OFFSET_UM = 5
SLOPE_MRAD = 10


def target_scenarios():
    scenarios = [{"id": "nominal", "label": "Nominal", "offset_m": [0., 0.], "slope_rad": [0., 0.]}]
    for key, symbol, magnitude, scale, unit in (
        ("offset_m", "Δ", OFFSET_UM, 1e-6, "µm"),
        ("slope_rad", "θ", SLOPE_MRAD, 1e-3, "mrad"),
    ):
        for axis, name in enumerate(("t", "s")):
            for sign, prefix in ((-1, "−"), (1, "+")):
                offset, slope = [0., 0.], [0., 0.]
                values = offset if key == "offset_m" else slope
                values[axis] = sign * magnitude * scale
                scenarios.append({"id": f"{key}-{name}-{'minus' if sign < 0 else 'plus'}",
                                  "label": f"{symbol}{name} {prefix}{magnitude} {unit}",
                                  "offset_m": offset, "slope_rad": slope})
    return scenarios


def evaluate_perturbation(arrival, target, nominal_eta, scenario):
    """Keep Gaussian q and the Target fixed. Perturb only the relative incident field."""
    if nominal_eta is None:
        return {"status": "Uncomputed", "reason": "Nominal overlap is unavailable"}
    try:
        nominal = scenario["id"] == "nominal"
        eta = nominal_eta if nominal else mode_overlap(
            arrival, target, offset=scenario["offset_m"],
            slope=scenario["slope_rad"])["normalized_mode_overlap"]
    except (DomainError, ArithmeticError, ValueError) as exc:
        return {"status": "Uncomputed", "reason": str(exc)}

    loss = max(0., -10 * math.log10(eta)) if eta > 0 else None
    baseline_loss = max(0., -10 * math.log10(nominal_eta)) if nominal_eta > 0 else None
    delta = loss - baseline_loss if loss is not None and baseline_loss is not None else None
    delta_status = ("Computed" if delta is not None else
                    "Infinite" if loss is None and baseline_loss is not None else "Uncomputed")
    return {"status": "Approximate", "normalized_mode_overlap": eta, "mode_mismatch_loss_db": loss,
            "loss_status": "Computed" if loss is not None else "Infinite",
            "delta_loss_db": delta, "delta_status": delta_status}


def compare_sensitivity(result):
    diagnostic = {
        "status": "Uncomputed",
        "scope": "fixed Target plane; scalar Gaussian relative offset and linear phase ramp",
        "part_placement_status": "Uncomputed",
        "package_yield_status": "Uncomputed",
        "total_coupling_status": "Uncomputed",
    }
    if result["status"] != "Computed" or not result["candidates"]:
        return diagnostic

    scenarios = target_scenarios()
    comparisons = []
    for candidate in result["candidates"]:
        evaluation = candidate["evaluation"]
        nominal_eta = visible_overlap(evaluation)
        if nominal_eta is None:
            samples = {row["id"]: {"status": "Uncomputed", "reason": "Nominal overlap is unavailable"}
                       for row in scenarios}
        else:
            target = adapt_external(candidate["prescription"]).target.mode
            arrival = arrived_mode(evaluation, target)
            samples = {row["id"]: evaluate_perturbation(arrival, target, nominal_eta, row)
                       for row in scenarios}
        comparisons.append({"candidate_id": candidate["id"], "samples": samples})
    return {**diagnostic, "status": "Approximate", "input_sha256": result["input_sha256"],
            "target_reference_plane": result["input_snapshot"]["target"]["reference_plane"]["value"],
            "recommended_candidate_id": result["selected_candidate_id"],
            "scenarios": scenarios, "candidates": comparisons}


def format_db(value, status, *, delta=False):
    if status == "Infinite":
        return "∞"
    if status != "Computed":
        return "Uncomputed"
    if delta and abs(value) >= 0.00005:
        return f"{value:+.4f}"
    return f"{abs(value):.4f}"


def render_sensitivity(diagnostic, viewed_id):
    if diagnostic is None:
        return ""
    if diagnostic["status"] == "Uncomputed":
        return '<p data-sensitivity-uncomputed>Target 기준면 민감도 · Uncomputed</p>'

    columns = []
    for index, entry in enumerate(diagnostic["candidates"]):
        identifier = entry["candidate_id"]
        label = "추천" if identifier == diagnostic["recommended_candidate_id"] else f"대안 {index}"
        current = ' aria-current="true"' if identifier == viewed_id else ""
        columns.append(f'<th scope="col" data-sensitivity-candidate="{escape(identifier)}"{current}>'
                       f'{label}<br>{escape(identifier)}</th>')

    rows = []
    for scenario in diagnostic["scenarios"]:
        row_id = scenario["id"]
        cells = []
        for entry in diagnostic["candidates"]:
            sample = entry["samples"][row_id]
            column = escape(entry["candidate_id"])
            if sample["status"] == "Uncomputed":
                label = "Uncomputed"
                status = sample["status"]
            else:
                absolute = format_db(sample["mode_mismatch_loss_db"], sample["loss_status"])
                delta = format_db(sample["delta_loss_db"], sample["delta_status"], delta=True)
                label = f"{absolute} ({delta})"
                status = sample["delta_status"]
            cells.append(f'<td data-sensitivity-cell="{column}" data-delta-status="{status}">{label}</td>')
        rows.append(f'<tr data-sensitivity-scenario="{row_id}"><th scope="row">'
                    f'{escape(scenario["label"])}</th>{"".join(cells)}</tr>')

    return f'''<details class="mode-match" data-sensitivity="{escape(viewed_id)}"
        data-input-sha="{escape(diagnostic["input_sha256"])}"
        data-target-plane="{escape(diagnostic["target_reference_plane"]["id"])}">
    <summary>Target 기준면 민감도</summary>
    <p>각 후보의 Nominal 설계를 고정합니다. 도착 빔에 t/s 위치 오차 또는 작은 각도 오차를 하나씩 적용합니다.</p>
    <p class="caption">진단 조건 ±{OFFSET_UM} µm, ±{SLOPE_MRAD} mrad. 각도는 Target 기준면의 선형 Phase ramp로 적용합니다.</p>
    <div class="table-scroll" tabindex="0" role="region" aria-label="후보별 민감도 비교">
    <table><caption>Mode Mismatch Loss (Nominal 대비 변화) [dB]</caption>
    <thead><tr><th scope="col">Target 상대 오차</th>{"".join(columns)}</tr></thead>
    <tbody>{"".join(rows)}</tbody></table></div>
    <p class="caption">부품 배치 공차, Package Yield, Total Coupling은 모두 Uncomputed입니다.</p></details>'''
