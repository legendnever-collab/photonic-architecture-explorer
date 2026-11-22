"""Read-only design report; reuse Inspector drawing, never calculate physics in JS."""
from html import escape
import json
from .candidate_review import CONCEPT_LABELS, REVIEW_CSS, build_candidate_review, render_review_sheet, near_match_note
from .confidence import render_confidence
from .external import adapt_external
from .inspector import CSS, PROJECTIONS, plot_svg, result_panel, input_summary, visible_overlap
from .mode_match import MODE_MATCH_CSS, loss_label, render_mode_match
from .placement import compare_placement
from .reference_redesign import render_reference_context
from .sensitivity import compare_sensitivity, render_sensitivity
from .solver import MAX_FOOTPRINT_SLOPE


CONCEPT_REASONS = {
    'short_path': '유효 후보 중 가장 좋은 Overlap 구간에서 광경로가 가장 짧습니다.',
    'smaller_footprint': '같은 Overlap 구간에서 반사면 위 최대 투영 빔 반경이 더 작습니다.',
    'model_margin': '같은 Overlap 구간에서 Gaussian 모델의 곡률·Footprint 한계까지 여유가 더 큽니다.',
}


def review_snapshot(result):
    """Add optional review diagnostics while preserving the engine result and ranking."""
    sensitivity = compare_sensitivity(result)
    return {**result, 'candidate_sensitivity': sensitivity,
            'candidate_review': build_candidate_review(result, sensitivity),
            'reflector_placement': compare_placement(result)}


def render_placement(diagnostic, identifier):
    if not diagnostic:
        return ''
    if diagnostic['status'] == 'Uncomputed':
        return '<p data-placement-status="Uncomputed">Reflector Placement Sensitivity · Uncomputed</p>'

    def format_max(summary):
        miss = summary.get('max_target_miss_m')
        angle = summary.get('max_target_angle_rad')
        if miss is None:
            return f"— · {summary['failed']} 실패" if summary else '—'
        return f"{miss * 1e6:.3f} / {angle * 1e3:.3f} · {summary['failed']} 실패"

    candidate = next(c for c in diagnostic['candidates'] if c['candidate_id'] == identifier)
    comparisons = []
    for concept in diagnostic['candidates']:
        summary = concept['summary']
        comparisons.append(f'<tr><th>{escape(concept["candidate_id"])}</th>'
                           f'<td>{format_max(summary.get("translation", {}))}</td>'
                           f'<td>{format_max(summary.get("rotation", {}))}</td></tr>')

    rows = []
    for case in (candidate['nominal'], *candidate['cases']):
        label = 'Nominal'
        if case.get('kind') == 'translation':
            label = f"M{case['mirror']} {case['axis']} {case['delta_m'] * 1e6:+g} µm"
        elif case.get('kind') == 'rotation':
            label = f"M{case['mirror']} s {case['delta_rad'] * 1e3:+g} mrad"
        if case['status'] == 'Computed':
            values = [*(v * 1e6 for v in case['target_offset_m']),
                      *(v * 1e3 for v in case['target_angular_error_rad'])]
            cells = ''.join(f'<td>{v:.3f}</td>' for v in values)
        else:
            cells = f'<td colspan="4">Fail · {escape(case["reason"])}</td>'
        rows.append(f'<tr data-placement-case><th>{label}</th>{cells}</tr>')

    plane = escape(diagnostic['target_reference_plane']['id'])
    return f"""<details data-reflector-placement="{escape(identifier)}"
        data-input-sha="{escape(diagnostic['input_sha256'])}" data-placement-status="{candidate['status']}">
        <summary>Reflector Placement Sensitivity · Chief Ray</summary>
        <p>Fixed Target plane <code>{plane}</code> · Global X/Y/Z ±5 µm 또는 Sagittal 회전 ±1 mrad를 한 번에 한 면에 적용합니다.</p>
        <p>후보 비교 · 도달한 광선의 최대 위치 편차 [µm] / 최대 방향 편차 [mrad] 및 실패 건수.</p>
        <div class="table-scroll"><table><thead><tr><th>후보</th><th>Translation</th><th>Rotation</th></tr></thead>
        <tbody>{''.join(comparisons)}</tbody></table></div>
        <div class="table-scroll"><table><thead><tr><th>오차 조건</th><th>t [µm]</th><th>s [µm]</th>
        <th>θt [mrad]</th><th>θs [mrad]</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
        <p>위치는 Target 기준면의 t/s 성분입니다. 각도는 Target 방향과 각 횡축이 만드는 평면에 투영한 부호 있는 각도입니다.
        Perturbed Gaussian Mode Overlap과 실제 부품 배치 공차는 Uncomputed입니다.</p></details>"""


def render_envelope_comparison(comparison):
    if not comparison:
        return ""
    rows, details = [], []
    for key, case in comparison["cases"].items():
        volume = case["envelope"]
        width = (volume["max_m"][0] - volume["min_m"][0]) * 1e3
        choice = " · 선택됨" if key == comparison["selected"] else ""
        boundary = case["limiting_boundary"]
        label = f'{width:.6f}'.rstrip('0').rstrip('.') + ' mm'
        rows.append(f'<tr><th scope="row">{label}{choice}</th><td>{len(case["passing_trials"])}/{case["evaluations"]}</td>'
                    f'<td>{case["selected"]}</td><td>{case["overlap"]:.9f}</td>'
                    f'<td>{"충족" if case["threshold_met"] else "미달"}</td>'
                    f'<td>{case["max_projected_radius_m"]*1e6:.2f}</td>'
                    f'<td>{case["minimum_gap_m"]*1e6:.3f} · M{boundary["mirror"]} {boundary["face"]}</td></tr>')
        failures = "".join(f'<li>{escape(reason)} · {count}건</li>' for reason, count in case["rejection_counts"].items())
        candidates = []
        for trial in case["passing_trials"]:
            face = trial["nearest_envelope_face"]
            candidates.append(f'<tr><th scope="row">{trial["id"]}</th><td>{trial["overlap"]:.9f}</td>'
                              f'<td>{trial["max_projected_radius_m"]*1e6:.2f}</td><td>{trial["footprint_curvature"]:.6f}</td>'
                              f'<td>M{face["mirror"]} {face["face"]} · {face["gap_m"]*1e6:.3f}</td></tr>')
        details.append(f'<details><summary>{label} · 통과 처방과 탈락 사유</summary>'
                       f'<p>Input SHA256 <code>{case["input_sha256"]}</code></p>'
                       '<div class="table-scroll"><table><caption>통과 처방 · Normalized η 순위</caption>'
                       '<thead><tr><th>처방</th><th>η</th><th>최대 투영 반경 [µm]</th><th>최대 3w·|κ|</th>'
                       '<th>가장 가까운 Envelope 면 · Gap [µm]</th></tr></thead>'
                       f'<tbody>{"".join(candidates)}</tbody></table></div><p>탈락 사유별 건수</p><ul>{failures}</ul></details>')
    return (f'<section class="card" id="envelope-comparison"><h2>Package Envelope 비교</h2>'
            '<p>같은 두 Port에서 R8 기준 처방 두 개와 주변 Guarded Near-Match 처방을 두 Envelope로 다시 평가했습니다. '
            '통과 수는 Geometry·Gaussian Guard·기구 조건을 충족한 처방 수입니다. η 목표는 별도로 표시합니다.</p>'
            '<div class="table-scroll"><table><thead><tr><th>X 폭</th><th>통과/평가</th><th>최고 관측 후보</th>'
            '<th>Normalized η</th><th>η ≥ 0.99</th><th>최대 투영 1/e² 반경 [µm]</th>'
            '<th>최소 AABB Gap [µm] · 제한 경계</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div><p>Synthetic Package에서 50 µm Clearance를 적용합니다. '
            '전체 Beam Clearance, 실제 Assembly Tolerance 및 Total Coupling은 Uncomputed입니다.</p>'
            + "".join(details) + '</section>')


def render_design_report(result):
    payload=json.dumps(result,sort_keys=True,ensure_ascii=False,allow_nan=False).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    rows=[]; articles=[]; options=[]; sheets=[]; alternatives=[]
    envelope = result.get("envelope_comparison")
    aperture_note = ("R7 Equal-tail 배정과 축별 1.10 mm Half-aperture 상한을 적용했습니다." if envelope else
                     "Half-aperture는 각 반사면의 투영 빔 반경에 4배 규칙을 적용했습니다.")
    review = result.get('candidate_review', {})
    lead = result['candidates'][0]['ranking'] if result['candidates'] else None
    for i,c in enumerate(result['candidates']):
        identifier=c['id'];d=c['prescription'];e=c['evaluation'];r=c['ranking']
        eta = visible_overlap(e)
        metric = f'<strong data-overlap-value="{eta}">{eta:.9g}</strong>' if eta is not None else '<strong>Uncomputed</strong>'
        table_eta = f'{eta:.9g}' if eta is not None else 'Uncomputed'
        role = c.get('recommendation_role')
        concept = CONCEPT_LABELS.get(role, '추천' if i == 0 else '대안')
        reason = CONCEPT_REASONS.get(role, '')
        if i and role:
            extra_path = (r['total_path_m'] - lead['total_path_m']) * 1000
            reason += f' 추천 대비 광경로 {extra_path:+.3f} mm.'
            alternatives.append(f'<li><button type="button" data-select-candidate="{identifier}">'
                                f'{concept} · {identifier}</button><p>{reason}</p></li>')
        options.append(f'<option value="{identifier}">{identifier} · {concept}</option>')
        rows.append(f'<tr data-compared-concept="{identifier}"><td>{identifier} · {concept}</td><td>{table_eta}</td><td>{r["max_3w_footprint_curvature"]:.6f}</td><td>{r["max_projected_radius_m"]*1e6:.2f}</td><td>{r["total_path_m"]*1000:.3f}</td></tr>')
        adapted=adapt_external(d)
        if review.get('status') == 'Computed':
            sheets.append(render_review_sheet(review, c, adapted, i == 0))
        plots=[]
        for proj, omitted in [('Fold', 'Sagittal'), *((key, axes[2]) for key, axes in PROJECTIONS.items())]:
            plots.append(f'<div class="projection" data-projection="{proj}"'
                         + (' hidden' if proj != 'Fold' else '')
                         + f'><h3>{proj} · 생략 축 {omitted} · mm · Equal Scale</h3>'
                         + plot_svg(d, e, adapted, proj, identifier + '-' + proj) + '</div>')
        prescription_rows=[]
        for j,m in enumerate(adapted.reflectors,1):
            fmt=lambda vals: ', '.join(f'{v:.6g}' for v in vals)
            prescription_rows.append(f'<tr><td>M{j}</td><td>{fmt(v*1e3 for v in m.vertex)}</td><td>{fmt(m.normal)}</td><td>{fmt(m.curvatures)}</td><td>{fmt(v*1e3 for v in m.half_aperture)}</td></tr>')
        if i == 0:
            trade_off = "대안에서는 광경로를 늘려 Beam Footprint를 줄이거나 Gaussian 모델 여유를 늘릴 수 있습니다."
            if envelope:
                trade_off = "선택한 Envelope에서 통과한 처방의 최고 관측 η입니다. 위 표에서 다른 Envelope와 비교할 수 있습니다."
            elif len(result["candidates"]) == 1:
                trade_off = "현재 검증 범위에서 비교할 별도 대안이 없습니다."
            elif not any(item.get("recommendation_role") == "smaller_footprint" for item in result["candidates"]):
                trade_off = "대안에서는 광경로를 늘려 Gaussian 모델 여유를 늘릴 수 있습니다."
        else:
            trade_off = (f"추천 대비 최대 투영 빔 반경 "
                         f"{(r['max_projected_radius_m'] - lead['max_projected_radius_m'])*1e6:+.2f} µm · "
                         f"Max 3w·κ {r['max_3w_footprint_curvature'] - lead['max_3w_footprint_curvature']:+.6f} "
                         f"(Guard {MAX_FOOTPRINT_SLOPE}).")
        articles.append(f'''<article data-candidate="{identifier}" data-input-sha="{escape(result['input_sha256'])}"{' hidden' if i else ''}>
        <div class="layout"><section class="card drawing"><h2>{'Recommended Concept' if i==0 else 'Alternative Concept'} · {identifier}</h2>{''.join(plots)}
        <p class="caption">파랑 · Fixed Source와 Chief Path / 보라 · Fixed Target / 주황 · Quadratic Reflectors</p></section>
        <section class="card decision"><h2>Nominal Mode Match</h2>
        <div class="metric"><span>Normalized Mode Overlap · Approximate</span>{metric}
        <small>Mode Mismatch {loss_label(eta)} · Total Coupling Uncomputed</small></div>
        {near_match_note(c, adapted)}<p data-recommendation-role="{role or ''}"><b>{concept}</b> · {reason}</p>
        <p data-trade-off><b>광경로 {r['total_path_m']*1000:.3f} mm</b> · {trade_off}</p></section></div>
        {render_confidence(c, result["input_sha256"])}
        <details class="card candidate-details"><summary>Mode Match, Sensitivity, Reflector 상세</summary>
        <p>최대 Projected Beam Radius <b>{r['max_projected_radius_m']*1e6:.2f} µm</b> ·
        Max 3w·κ <b>{r['max_3w_footprint_curvature']:.6f}</b> (Guard {MAX_FOOTPRINT_SLOPE}).</p>
        {render_mode_match(c, result.get('input_sha256', ''), adapted)}
        {render_sensitivity(result.get('candidate_sensitivity'), identifier)}
        {render_placement(result.get('reflector_placement'), identifier)}
        <details><summary>Reflector 설계값 · 자동 생성</summary><p>{aperture_note}</p><div class="table-scroll"><table><tr><th>면</th><th>Vertex [mm]</th><th>Normal</th><th>κt, κs [m⁻¹]</th><th>Half-aperture [mm]</th></tr>{''.join(prescription_rows)}</table></div>
        <p>Segment Lengths [mm]: {', '.join(f'{v*1000:.6g}' for v in e['geometry']['lengths'])}</p></details>
        <details><summary>상세 Physics 판정 · 미계산 항목</summary>
        <p>Off-vertex Field 및 Perturbed Mode Overlap · Uncomputed. 실제 배치 공차, Package Yield, Total Coupling, Patentability · Uncomputed.</p>
        {result_panel(e)}</details>
        <details><summary>입력·생성 가정·수동 Adapter 재현 JSON</summary><pre>{escape(json.dumps(d,ensure_ascii=False,indent=2))}</pre></details></details></article>''')
    if not articles:
        status = escape(result["status"])
        reason = escape(result.get("reason", ""))
        digest = result.get("input_sha256")
        trace = f'<p>Input SHA256 <code>{escape(digest)}</code></p>' if digest else ''
        sensitivity = render_sensitivity(result.get("candidate_sensitivity"), "")
        articles = [f'''<section id="rejected-design" class="card">
        <h2>후보 생성 보류 · {status}</h2><p data-design-failure>{reason}</p>{trace}
        <p>Overlap: Uncomputed · 이 제한된 탐색의 실패는 구조의 물리적 불가능성을 입증하지 않습니다.</p>
        {sensitivity}{render_placement(result.get('reflector_placement'), '')}<p>부품 배치 공차 · Package Yield · Total Coupling: Uncomputed · Patentability: Uncomputed</p></section>''']
    toolbar=(f'<div class="toolbar"><label>설계 후보 <select id="candidate-select">{"".join(options)}</select></label><label>Projection <select id="projection-select"><option>Fold</option><option>XZ</option><option>XY</option><option>YZ</option></select></label></div>' if options else '')
    comparison=(f'<details class="card compare"><summary>후보 수치 비교 · Ranking 지표</summary><div class="table-scroll"><table><thead><tr><th>후보</th><th>η_mode</th><th>max 3w·κ</th><th>max Radius [µm]</th><th>Path [mm]</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div><p class="caption">같은 Overlap 구간에서 Path, Beam Footprint, 모델 한계 여유를 비교합니다. 3w·κ는 Gaussian 모델의 검사 지표입니다. 실제 Package 크기, Aberration과 조립 성능은 별도 검증이 필요합니다.</p></details>' if rows else '')
    review_section = ('<section id="candidate-review"><div class="review-controls">'
                      '<button type="button" id="review-toggle" aria-controls="review-sheets" '
                      'aria-expanded="false">후보 요약 보기</button>'
                      '<button type="button" id="review-print">후보 요약 인쇄</button></div>'
                      f'<div id="review-sheets" hidden>{"".join(sheets)}</div></section>') if sheets else ''
    alternative_section = ('<section id="concept-alternatives" class="card"><h2>Alternative Concepts</h2>'
                           f'<ul>{"".join(alternatives)}</ul></section>') if alternatives else ''
    search=result.get('search',{})
    budget_caption = '최대 64 Geometry / 256 Curvature 후보. Frozen family를 모두 검사하며 범위를 자동 확대하지 않습니다.'
    if result.get('workflow'):
        cost = result['workflow']['near_match']
        budget_caption = (f'Near-Match · {cost["geometry_count"]} Geometry / {cost["adapter_calls"]} Adapter 평가, '
                          f'상한 {cost["maximum_adapter_calls"]}회 / 600 s. '
                          '유한 탐색의 최고 관측값이며 전역 최적성은 보장하지 않습니다.')
    if envelope:
        budget_caption = "각 Envelope에서 R8 두 기준 처방과 25 µm 간격의 3×3 배치 두 곳을 평가합니다. 최대 74개 처방입니다."
    rerun_entry = 'pae-workspace' if envelope or result.get('workflow') else 'pae-design ports.json'
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PAE · Two-Port Design</title><style>{CSS}{MODE_MATCH_CSS}{REVIEW_CSS}
    @media print{{body:has(#rejected-design)>header, main:has(#rejected-design)>:not(#rejected-design){{display:none !important}}
    main:has(#rejected-design){{padding:0;margin:0;max-width:none}}
    #rejected-design{{padding:0;border:0}}}}
    .wrap{{max-width:1240px}}.compare,.candidate-details,#concept-alternatives{{margin:14px 0}}
    th{{text-align:left;padding:9px 3px;font-size:12px}}.table-scroll{{overflow:auto}}.mode-match th[aria-current]{{color:#176d92}}
    .mode-match caption{{text-align:left;padding:8px 0}}.results .metric{{display:none}}code{{overflow-wrap:anywhere}}
    .drawing{{position:static}}.drawing svg{{max-height:420px}}.decision p{{line-height:1.55}}
    #concept-alternatives ul{{padding-left:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}
    #concept-alternatives li{{list-style:none;margin:0}}#concept-alternatives button{{background:white;color:#176d92;text-align:left}}
    @media(max-width:560px){{body>header{{display:none}}.drawing svg{{max-height:205px}}
    .layout{{gap:10px}}#concept-alternatives ul{{grid-template-columns:minmax(0,1fr)}}}}
    </style></head><body>
    <header><h1>Two-Port Design</h1></header>
    <main class="wrap">
    {render_envelope_comparison(envelope)}{render_reference_context(result.get('reference_context'))}{''.join(articles)}{toolbar}{alternative_section}{review_section}{comparison}
    <section class="card"><details><summary>Fixed Ports · 입력 SHA · 기준면</summary>
    <p>Input SHA256 <code>{escape(result.get('input_sha256', ''))}</code></p>{input_summary(result.get('input_snapshot'))}</details>
    <details><summary>탐색 범위·순위 근거·실패 진단</summary><p>{budget_caption}</p><p>대표 선정은 추천 정책과 후보별 선택 근거를 따릅니다.</p><pre>{escape(json.dumps({'policy':result['search_policy'],'ranking_order':result['ranking_order'],'recommendation_policy':result.get('recommendation_policy'),'search':search,'limitations':result['limitations']},ensure_ascii=False,indent=2))}</pre></details>
    <details><summary>전체 결과 JSON · 입력 Snapshot 포함</summary><pre>{escape(json.dumps(result,ensure_ascii=False,indent=2))}</pre></details>
    <p class="caption">이 파일은 재계산하지 않는 결과 Snapshot입니다. 다른 두 Port의 Design 실행은 Repository의 <code>{rerun_entry}</code> 진입점을 사용합니다.</p></section></main>
    <script type="application/json" id="design-result">{payload}</script><script>
    const selector=document.querySelector('#candidate-select'), projection=document.querySelector('#projection-select');
    function show(){{
      document.querySelectorAll('[data-candidate]').forEach(e=>e.hidden=e.dataset.candidate!==selector.value);
      document.querySelectorAll('[data-review-candidate]').forEach(e=>e.hidden=e.dataset.reviewCandidate!==selector.value);
      document.querySelectorAll('[data-projection]').forEach(e=>e.hidden=e.dataset.projection!==projection.value);
    }}
    const reviewToggle=document.querySelector('#review-toggle');
    if(reviewToggle){{
      const reviewSheets=document.querySelector('#review-sheets');
      reviewToggle.addEventListener('click',()=>{{
        reviewSheets.hidden=!reviewSheets.hidden;
        reviewToggle.setAttribute('aria-expanded', String(!reviewSheets.hidden));
        reviewToggle.textContent=reviewSheets.hidden?'후보 요약 보기':'후보 요약 접기';
      }});
      document.querySelector('#review-print').addEventListener('click',()=>window.print());
    }}
    if(selector){{
      const viewed=JSON.parse(document.querySelector('#design-result').textContent).viewed_candidate_id;
      if(Array.from(selector.options).some(option=>option.value===viewed)) selector.value=viewed;
      document.querySelectorAll('[data-select-candidate]').forEach(button=>{{
        button.addEventListener('click',()=>{{
          selector.value=button.dataset.selectCandidate;
          show();
          document.querySelector('[data-candidate]:not([hidden])').scrollIntoView({{block:'start'}});
        }});
      }});
      selector.addEventListener('change',show);projection.addEventListener('change',show);show();
    }}
    </script></body></html>'''
