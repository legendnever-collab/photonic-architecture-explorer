"""Scope the R6 benchmark comparison to the matching Workspace snapshot."""

from html import escape

ENTRY = "smf-glass-1310"
PORTS_FILE = "examples/m7r6_smf_glass_1310.json"
SUMMARY_FILE = "references/m7r6/design_summary.json"
OVERLAP_TOL = 1e-8

FIELD_LABELS = {
    "position_m": "Position",
    "propagation_direction": "Propagation Direction",
    "sagittal_axis": "Sagittal Axis",
    "mfd_ts_m": "MFD",
    "wavefront_curvature_ts_per_m": "Wavefront Curvature",
    "complex_q_ts_m": "Complex q",
    "wavelength_m": "Wavelength",
    "ambient_index": "Ambient Index",
}


def reference_context(original, submitted, summary):
    changes = []
    for prefix, baseline, current in (
        ("", original, submitted),
        ("Source ", original["source"], submitted["source"]),
        ("Target ", original["target"], submitted["target"]),
    ):
        for key, label in FIELD_LABELS.items():
            if prefix and key in ("wavelength_m", "ambient_index"):
                continue
            if baseline.get(key, {}).get("value") != current.get(key, {}).get("value"):
                changes.append(prefix + label)
    return {
        "case_id": summary["case_id"],
        "reference_input_sha256": summary["input_sha256"],
        "scope": "Original" if original == submitted else "Edited",
        "changed_fields": changes,
    }


def nominal_exact_matches(result, summary):
    search = result["search"]
    return (
        result["input_sha256"] == summary["input_sha256"]
        and search["status"] == "Completed"
        and search["geometry_count"] == summary["exact_geometry_count"]
        and len(search["attempts"]) == summary["exact_attempt_count"]
        and search["accepted_count"] == summary["exact_accepted"]
    )


def nominal_replay_matches(result, summary):
    if result["selected_candidate_id"] != summary["selected"] or not result["candidates"]:
        return False
    candidate = result["candidates"][0]
    benchmark = next(c for c in summary["candidates"] if c["id"] == summary["selected"])
    overlap = candidate["evaluation"]["gaussian_mode_matching"].get("normalized_mode_overlap")
    validation = candidate.get("independent_validation", {})
    quadrature = validation.get("quadrature_overlap", [])
    return (
        candidate["id"] == summary["selected"]
        and overlap is not None
        and abs(overlap - benchmark["overlap"]) <= OVERLAP_TOL
        and validation.get("status") == "Pass"
        and bool(quadrature)
        and all(abs(overlap - value) <= OVERLAP_TOL for value in quadrature)
    )


def render_reference_context(context):
    if not context:
        return ""
    if context["scope"] == "Original":
        note = "1310 nm R6의 두 Port로 계산했습니다. 아래 판정은 이 입력과 선택 후보에 적용됩니다."
    else:
        changed = ", ".join(context["changed_fields"])
        note = (f"변경된 조건 · {changed}. 기존 R6의 후보 순위와 Overlap은 원본 SHA에만 적용됩니다. "
                "아래 판정은 편집한 입력에서 다시 계산한 결과입니다.")
    scope = escape(context["scope"])
    return (f'<aside class="notice" data-reference-scope="{scope}"><p>{escape(note)}</p>'
            f'<p>R6 원본 Input SHA256 <code>{escape(context["reference_input_sha256"])}</code></p></aside>')
