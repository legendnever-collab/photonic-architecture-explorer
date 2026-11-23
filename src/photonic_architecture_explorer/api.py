"""Pure functions behind the JSON API. No HTTP here, so tests call them directly.

`preview` draws Ports before any design. `design` runs the P2 continuous generator
(`search.design_continuous`) on the converted Design Document; every candidate it returns
was accepted by the unchanged external Adapter. The result `pae.result/1` adds drawable
geometry, the explored (a, c) map and plain next-step guidance.
"""

from .design import review_snapshot
from .design_document import DocumentError, document_sha256, search_constraints, to_engine_input, validate_document
from .external import InputIssue
from .gaussian import DomainError
from .scene import candidate_scene, ports_scene
from .search import OBJECTIVES, design_continuous
from .solver import MAX_DIVERGENCE, MAX_FOOTPRINT_SLOPE

RESULT_SCHEMA = 'pae.result/1'
STATUS_KEYS = ('input_contract', 'geometry', 'model_domain', 'gaussian_mode_matching',
               'package_feasibility', 'physical_losses', 'fabrication', 'actual_applicability')
UNCOMPUTED = ['Total Coupling (interfaces, coatings, polarization, diffraction)',
              'Vector / non-paraxial field validation',
              'Assembly tolerance distribution and yield',
              'Full package clearance beyond declared boxes (supports, bodies, finite beam)',
              'Patentability']


def _invalid(document, issues):
    return {'schema': RESULT_SCHEMA, 'status': 'Invalid', 'reason': '입력 문서에 오류가 있습니다',
            'issues': issues, 'document_sha256': document_sha256(document) if isinstance(document, dict) else None,
            'ports': None, 'candidates': [], 'guidance': []}


def port_guidance(scene, ambient_index):
    """Divergence θ = λ/(π n w0): the same waist passes the guard in a medium with n ≥ n_now·θ/θ_max."""
    out = []
    for port in scene['ports']:
        guard = port['divergence_guard']
        if guard['status'] != 'Fail':
            continue
        required_index = ambient_index * guard['max_divergence_rad'] / MAX_DIVERGENCE
        out.append({'kind': 'port_divergence', 'port': port['name'], 'phase': 'P3·P4',
                    'values': {'max_divergence_rad': guard['max_divergence_rad'], 'limit_rad': guard['limit_rad'],
                               'min_waist_mfd_um': guard['min_waist_mfd_um'], 'required_index': required_index},
                    'message': f"{port['name']} Mode 발산각 {guard['max_divergence_rad']:.3f} rad > {guard['limit_rad']} rad. "
                               f"현재 매질에서는 Waist MFD가 {guard['min_waist_mfd_um']:.2f} µm 이상이어야 합니다. 같은 Mode를 "
                               f"굴절률 n ≥ {required_index:.2f}인 매질 안에서 다루거나(P3), Lens로 Mode를 키우는 Family(P4)가 필요합니다."})
    return out


def preview(document):
    """Port geometry and per-Port guards only; never generates or ranks candidates."""
    issues = validate_document(document)
    if issues:
        return _invalid(document, issues)
    try:
        scene = ports_scene(to_engine_input(document))
    except (InputIssue, DomainError) as exc:
        return _invalid(document, [{'path': getattr(exc, 'path', '$'), 'message': getattr(exc, 'reason', str(exc))}])
    return {'schema': RESULT_SCHEMA, 'status': 'Preview', 'document_sha256': document_sha256(document),
            'ports': scene, 'candidates': [], 'guidance': port_guidance(scene, document['ambient_index'])}


def _candidate(rank, candidate):
    evaluation, ranking = candidate['evaluation'], candidate['ranking']
    scene = candidate_scene(candidate['prescription'])
    matching = evaluation['gaussian_mode_matching']
    roles = candidate.get('roles') or [candidate.get('recommendation_role')]
    return {
        'id': candidate['id'],
        'rank': rank,
        'role': roles[0],
        'roles': roles,
        'role_labels': [OBJECTIVES.get(r, (None, None, r))[2] for r in roles],
        'family': candidate.get('family', 'exact'),
        'parameters_mm': {k[:-2]: v * 1e3 for k, v in candidate.get('parameters', {}).items() if k.endswith('_m')},
        'metrics': {
            'total_path_mm': scene['path']['total_length_mm'],
            'normalized_mode_overlap': matching.get('normalized_mode_overlap'),
            'mode_mismatch_db': matching.get('mismatch_db'),
            'max_projected_beam_radius_um': ranking['max_projected_radius_m'] * 1e6,
            'max_3w_footprint_curvature': ranking['max_3w_footprint_curvature'],
            'footprint_curvature_limit': MAX_FOOTPRINT_SLOPE,
            'max_abs_curvature_per_m': ranking.get('max_abs_curvature_per_m'),
            'worst_pose_mismatch_db': candidate.get('worst_pose_mismatch_db'),
            'incidence_deg': [m['incidence_deg'] for m in scene['mirrors']],
            'radius_of_curvature_ts_mm': [m['radius_of_curvature_ts_mm'] for m in scene['mirrors']],
        },
        'status': {key: evaluation[key]['status'] for key in STATUS_KEYS if key in evaluation},
        'scene': scene,
    }


def design_guidance(report, ports, ambient_index):
    out = port_guidance(ports, ambient_index) if ports else []
    reason = report.get('reason') or ''
    search = report.get('search', {})
    counts = search.get('screening_counts', {})
    if 'noncoplanar' in reason:
        out.append({'kind': 'noncoplanar', 'phase': 'P3',
                    'message': '두 Port가 한 평면에 있지 않습니다. 평면 밖으로 꺾이는 경로는 3D q-tensor 모델(P3)에서 다룹니다. '
                               '지금은 두 Port를 한 평면에 두면 계산할 수 있습니다.'})
    closest = search.get('closest_exact')
    if closest and report.get('candidates'):
        out.append({'kind': 'exact_outside_guard', 'phase': 'P3',
                    'values': {**closest, 'a_mm': closest['a_m'] * 1e3, 'c_mm': closest['c_m'] * 1e3},
                    'message': f"Exact-q 해는 있지만 가장 여유 있는 배치도 3w·|κ| = {closest['max_footprint_slope']:.4f} > "
                               f"{closest['limit']}입니다. Guard 안에서 Overlap을 최대로 한 Near-match 후보(η < 1)를 표시합니다. "
                               "Glass 매질 안 배치(P3)는 발산각을 줄여 Exact 해를 Guard 안으로 들일 수 있습니다."})
    constrained = {k.split(': ', 1)[1]: v for k, v in counts.items() if k.startswith('constraint:')}
    if constrained:
        out.append({'kind': 'constraints', 'values': constrained,
                    'message': f'탐색한 {search.get("grid_points", 0)}개 배치 중 {sum(constrained.values())}개가 '
                               'Port 뒤 공간·Envelope·Keep-out 등 공간 제약으로 제외됐습니다.'})
    if report.get('status') == 'Fail' and search.get('status') == 'Completed':
        top = sorted(counts.items(), key=lambda kv: -kv[1])[:3]
        out.append({'kind': 'no_candidate', 'phase': 'P4',
                    'message': '두 반사면 Family 안에서 Guard와 제약을 모두 만족하는 배치가 없습니다(물리적 불가능의 증명은 아님). '
                               '주요 사유: ' + ', '.join(f'{k} ({v})' for k, v in top)})
    return out


def _map(search):
    grid = search.get('map')
    if not grid:
        return None
    return {'a_mm': [v * 1e3 for v in grid['a_m']], 'c_mm': [v * 1e3 for v in grid['c_m']],
            'cells': grid['cells'], 'slope_limit': MAX_FOOTPRINT_SLOPE,
            'near_match': [{'a_mm': p['a_m'] * 1e3, 'c_mm': p['c_m'] * 1e3, 'eta': p['eta']} for p in grid['near_match']]}


def design(document):
    issues = validate_document(document)
    if issues:
        return _invalid(document, issues)
    try:
        engine_input = to_engine_input(document)
        ports = ports_scene(engine_input)
        constraints = search_constraints(document)
    except (DocumentError, InputIssue, DomainError) as exc:
        return _invalid(document, [{'path': getattr(exc, 'path', '$'), 'message': getattr(exc, 'reason', str(exc))}])
    report = design_continuous(engine_input, constraints)
    if report['candidates']:
        report = review_snapshot(report)
    search = report.get('search', {})
    summary = {k: search.get(k) for k in ('status', 'reason', 'grid_points', 'exact_feasible', 'near_match_feasible',
                                          'screening_counts', 'closest_exact', 'elapsed_seconds', 'verification')}
    return {
        'schema': RESULT_SCHEMA,
        'status': report['status'],
        'reason': report.get('reason'),
        'document_sha256': document_sha256(document),
        'engine_input_sha256': report.get('input_sha256'),
        'selected_candidate_id': report.get('selected_candidate_id'),
        'family': report['candidates'][0].get('family') if report['candidates'] else None,
        'ports': ports,
        'constraints': report.get('constraints'),
        'candidates': [_candidate(i + 1, c) for i, c in enumerate(report['candidates'])],
        'search': {**summary, 'policy': report.get('search_policy', {}).get('id'), 'map': _map(search)},
        'guidance': design_guidance(report, ports, document['ambient_index']),
        'limitations': report.get('limitations', []),
        'uncomputed': UNCOMPUTED,
        'engine_report': {**report, 'search': {k: v for k, v in search.items() if k != 'map'}},
    }
