"""Read-only evidence for a single evaluated prescription in a design snapshot."""
from html import escape

from .inspector import badge, visible_overlap


def render_confidence(candidate, input_sha):
    e = candidate["evaluation"]
    eta = visible_overlap(e)
    geometry = e["geometry"]
    domain = e["model_domain"]
    package = e["package_feasibility"]
    envelope = package.get("envelope_geometry", {}).get("status", "Uncomputed")
    independent = candidate.get("independent_validation") or {}
    overlap_note = "동일 Target Plane의 Scalar Field를 비교합니다."
    if eta is not None:
        overlap_note += f" η = {eta:.9g}."
        if independent.get("status") == "Pass" and independent.get("quadrature_overlap"):
            overlap_note += f' 별도 Quadrature η = {independent["quadrature_overlap"][-1]:.9g}.'

    rows = [
        ("Geometry Closure", geometry["status"], "Specular Chief Ray",
         geometry.get("reason") or "Fixed Source에서 두 Vertex를 거쳐 Target 위치와 방향에 도달하는지 검사합니다."),
        ("Gaussian Domain Applicability", domain["status"], "Gaussian Domain Guard",
         domain.get("reason") or f'Coplanar Gaussian에서 최대 3w·|κ| = {candidate["ranking"]["max_3w_footprint_curvature"]:.6g}입니다.'),
        ("Vector Wave Validation", "Uncomputed", "Vector Relay",
         "이 후보의 유한 곡면과 Aperture를 통과한 Vector Field 검증 기록이 없습니다."),
        ("E/H Field Consistency", "Evidence Insufficient", "Complex Field",
         "이 입력과 처방의 E/H 대조가 필요합니다. Tutorial의 직선 SMF 대조는 별도 Reference입니다."),
        ("Power Normalization", "Evidence Insufficient", "Poynting Flux",
         "이 후보에 대응하는 Launch 및 Target의 Flux Monitor와 공통 정규화 기록이 필요합니다."),
        ("Mode Overlap", "Approximate" if eta is not None else "Uncomputed",
         "Normalized Scalar Overlap", overlap_note),
        ("Total Coupling", e["physical_losses"]["status"], "Guided Power / Launch Power",
         "계면, 코팅, 회절 및 Port Power를 포함하는 전체 전달 검증이 필요합니다."),
        ("Package Feasibility", package["status"], "Package / Envelope",
         f"선언된 Envelope 검사는 {envelope}입니다. 지지대와 전체 Beam Clearance는 별도 평가합니다."),
        ("Assembly Tolerance", e["fabrication"]["status"], "Assembly",
         "단일 이동·회전에서의 Chief-Ray 진단과 실제 조립 후 성능 분포는 별도로 평가합니다."),
    ]
    cells = "".join(f"<tr><th scope='row'>{name}</th><td>{badge(status)}</td>"
                    f"<td>{model}<br>{escape(note)}</td></tr>" for name, status, model, note in rows)
    identity = escape(candidate["id"])
    return f"""<details class="card confidence" data-confidence="{identity}">
    <summary>Engineering Confidence · 판정과 근거</summary>
    <p>후보 {identity} · Input SHA256 <code>{escape(input_sha)}</code></p>
    <div class="table-scroll"><table><caption>선택 후보에 적용되는 Evidence</caption>
    <thead><tr><th>평가 항목</th><th>상태</th><th>Model 및 적용 범위</th></tr></thead>
    <tbody>{cells}</tbody></table></div>
    <p>아래 상세 Physics 판정과 Export JSON의 해당 후보 evaluation에서 원래 검사 결과를 확인할 수 있습니다.</p></details>"""
