"""Read-only design report; reuse Inspector drawing, never calculate physics in JS."""
from html import escape
import json
from .candidate_review import REVIEW_CSS, build_candidate_review, render_review_sheet
from .external import adapt_external
from .inspector import CSS, PROJECTIONS, plot_svg, result_panel, input_summary, visible_overlap
from .mode_match import MODE_MATCH_CSS, render_mode_match
from .sensitivity import compare_sensitivity, render_sensitivity


def review_snapshot(result):
    """Add optional review diagnostics while preserving the engine result and ranking."""
    sensitivity = compare_sensitivity(result)
    return {**result, 'candidate_sensitivity': sensitivity,
            'candidate_review': build_candidate_review(result, sensitivity)}


def render_design_report(result):
    payload=json.dumps(result,sort_keys=True,ensure_ascii=False,allow_nan=False).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    rows=[]; articles=[]; options=[]; sheets=[]
    review = result.get('candidate_review', {})
    for i,c in enumerate(result['candidates']):
        identifier=c['id'];d=c['prescription'];e=c['evaluation'];r=c['ranking']
        eta = visible_overlap(e)
        metric = f'<strong data-overlap-value="{eta}">{eta:.9g}</strong>' if eta is not None else '<strong>Uncomputed</strong>'
        table_eta = f'{eta:.9g}' if eta is not None else 'Uncomputed'
        options.append(f'<option value="{identifier}">{i+1} · {"추천" if i==0 else "대안"} · {r["total_path_m"]*1000:.3f} mm</option>')
        rows.append(f'<tr><td>{i+1}{" · 추천" if i==0 else ""}</td><td>{table_eta}</td><td>{r["max_3w_footprint_curvature"]:.6f}</td><td>{r["max_projected_radius_m"]*1e6:.2f}</td><td>{r["total_path_m"]*1000:.3f}</td></tr>')
        adapted=adapt_external(d)
        if review.get('status') == 'Computed':
            sheets.append(render_review_sheet(review, c, adapted, i == 0))
        plots=[]
        for proj,(_,_,omitted) in PROJECTIONS.items():
            plots.append(f'<div class="projection" data-projection="{proj}"'+(' hidden' if proj!='XZ' else '')+f'><h3>{proj} · 생략 축 {omitted} · mm · Equal Scale</h3>'+plot_svg(d,e,adapted,proj,identifier+'-'+proj)+'</div>')
        prescription_rows=[]
        for j,m in enumerate(adapted.reflectors,1):
            fmt=lambda vals: ', '.join(f'{v:.6g}' for v in vals)
            prescription_rows.append(f'<tr><td>M{j}</td><td>{fmt(v*1e3 for v in m.vertex)}</td><td>{fmt(m.normal)}</td><td>{fmt(m.curvatures)}</td><td>{fmt(v*1e3 for v in m.half_aperture)}</td></tr>')
        articles.append(f'''<article data-candidate="{identifier}"{' hidden' if i else ''}>
        <div class="layout"><section class="card drawing"><h2>{'추천 설계' if i==0 else '대안 설계 '+str(i+1)}</h2>{''.join(plots)}
        <p class="caption">파랑: Fixed Source / Chief Path · 보라: Fixed Target · 주황: Quadratic Reflectors</p>
        <p class="notice">Conceptual Geometry · Half-aperture는 자동 설계한 4×Beam Radius입니다. 실제 Package·제작 가능성은 Uncomputed입니다.</p></section>
        <section class="card"><h2>설계 판단</h2><div class="metric"><span>Normalized Mode Overlap · Approximate</span>{metric}<small>Total Coupling: Uncomputed · 실제 전송 효율이 아닙니다.</small></div>
        <p>Geometry와 Gaussian Domain 검사 통과. Path Length <b>{r['total_path_m']*1000:.3f} mm</b>.</p>
        <p>3w Footprint × Curvature 최대 <b>{r['max_3w_footprint_curvature']:.6f}</b> (Guard 0.15).
        최대 Projected Beam Radius <b>{r['max_projected_radius_m']*1e6:.2f} µm</b>.</p>
        <p>Overlap이 같은 수치 분해능이면 Footprint–Curvature 여유를 먼저 비교합니다. 더 짧은 경로 또는 더 작은 Beam Footprint가 항상 1순위는 아닙니다.</p>
        {render_mode_match(c, result.get('input_sha256', ''), adapted)}
        {render_sensitivity(result.get('candidate_sensitivity'), identifier)}
        <details><summary>Reflector 설계값 · 자동 생성</summary><div class="table-scroll"><table><tr><th>면</th><th>Vertex [mm]</th><th>Normal</th><th>κt, κs [m⁻¹]</th><th>Half-aperture [mm]</th></tr>{''.join(prescription_rows)}</table></div>
        <p>Segment Lengths [mm]: {', '.join(f'{v*1000:.6g}' for v in e['geometry']['lengths'])}</p></details>
        <details><summary>상세 Physics 판정 · 미계산 항목</summary>{result_panel(e)}</details>
        <details><summary>입력·생성 가정·수동 Adapter 재현 JSON</summary><pre>{escape(json.dumps(d,ensure_ascii=False,indent=2))}</pre></details></section></div></article>''')
    if not articles:
        status = escape(result["status"])
        reason = escape(result.get("reason", ""))
        digest = result.get("input_sha256")
        trace = f'<p>Input SHA256 <code>{escape(digest)}</code></p>' if digest else ''
        sensitivity = render_sensitivity(result.get("candidate_sensitivity"), "")
        articles = [f'''<section id="rejected-design" class="card">
        <h2>후보 생성 보류 · {status}</h2><p data-design-failure>{reason}</p>{trace}
        <p>Overlap: Uncomputed · 이 제한된 탐색의 실패는 구조의 물리적 불가능성을 입증하지 않습니다.</p>
        {sensitivity}<p>부품 배치 공차 · Package Yield · Total Coupling: Uncomputed</p></section>''']
    toolbar=(f'<div class="toolbar"><label>설계 후보 <select id="candidate-select">{"".join(options)}</select></label><label>Projection <select id="projection-select"><option>XZ</option><option>XY</option><option>YZ</option></select></label></div>' if options else '')
    comparison=(f'<section class="card compare"><h2>대표 후보 비교</h2><div class="table-scroll"><table><thead><tr><th>후보</th><th>η_mode</th><th>max 3w·κ</th><th>max Radius [µm]</th><th>Path [mm]</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div><p class="caption">가중합 Score 없음. Mode Matching → Footprint/Aperture 여유 → Path Length 순서. 서로 다른 Vertex Geometry의 상위 후보를 표시합니다.</p></section>' if rows else '')
    review_section = ('<section id="candidate-review"><div class="review-controls">'
                      '<button type="button" id="review-toggle" aria-controls="review-sheets" '
                      'aria-expanded="false">후보 요약 보기</button>'
                      '<button type="button" id="review-print">후보 요약 인쇄</button></div>'
                      f'<div id="review-sheets" hidden>{"".join(sheets)}</div></section>') if sheets else ''
    search=result.get('search',{})
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PAE · Two-Port Design</title><style>{CSS}{MODE_MATCH_CSS}{REVIEW_CSS}
    @media print{{body:has(#rejected-design)>header, main:has(#rejected-design)>:not(#rejected-design){{display:none !important}}
    main:has(#rejected-design){{padding:0;margin:0;max-width:none}}
    #rejected-design{{padding:0;border:0}}}}
    .wrap{{max-width:1240px}}.compare{{margin:18px 0}}th{{text-align:left;padding:9px 3px;font-size:12px}}.table-scroll{{overflow:auto}}.mode-match th[aria-current]{{color:#176d92}}.mode-match caption{{text-align:left;padding:8px 0}}.results .metric{{display:none}}.overview{{margin-bottom:18px}}code{{overflow-wrap:anywhere}}</style></head><body>
    <header><h1>Photonic Architecture Explorer / Two-Port Design</h1><p>Fixed Source + Fixed Target → 자동 생성한 Two-Reflector 후보 · Read-only Report</p></header>
    <main class="wrap"><section class="card overview"><h2>두 Port에서 설계한 결과</h2><p>탐색 상태: <b>{escape(result['status'])}</b> · 유효 후보 {search.get('accepted_count',0)}개 중 대표 {len(result['candidates'])}개</p>
    <p>Port Position·Direction·Mode는 고정했습니다. Reflector 위치·Normal·Curvature·Aperture를 입력할 필요가 없습니다.</p>
    <details><summary>두 Port 입력 확인</summary>{input_summary(result.get('input_snapshot'))}</details>
    <p class="caption">Synthetic 또는 명시 Gaussian 가정의 모델 내 개념 설계입니다. Actual Field·Total Coupling·Package·Fabrication Yield·Patentability는 Uncomputed입니다.</p></section>
    {toolbar}{review_section}{''.join(articles)}{comparison}
    <section class="card"><details><summary>탐색 범위·순위 근거·실패 진단</summary><p>최대 64 Geometry / 256 Curvature 후보. Frozen family를 모두 검사하며 범위를 자동 확대하지 않습니다.</p><p>대표 선정: Geometry별 최고 후보를 Lexicographic 순서로 최대 3개 선택.</p><pre>{escape(json.dumps({'policy':result['search_policy'],'ranking_order':result['ranking_order'],'search':search,'limitations':result['limitations']},ensure_ascii=False,indent=2))}</pre></details>
    <details><summary>전체 결과 JSON · 입력 Snapshot 포함</summary><pre>{escape(json.dumps(result,ensure_ascii=False,indent=2))}</pre></details>
    <p class="caption">이 파일은 재계산하지 않는 결과 Snapshot입니다. 다른 두 Port의 Design 실행은 Repository의 <code>pae-design ports.json</code> 진입점을 사용합니다.</p></section></main>
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
      selector.addEventListener('change',show);projection.addEventListener('change',show);show();
    }}
    </script></body></html>'''
