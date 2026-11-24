"""Pure functions behind the JSON API. No HTTP here, so tests call them directly.

`preview` draws Ports before any design. `design` runs the P2 continuous generator
(`search.design_continuous`) on the converted Design Document; every candidate it returns
was accepted by the unchanged external Adapter. The result `pae.result/1` adds drawable
geometry, the explored (a, c) map and plain next-step guidance.
"""

from dataclasses import replace

import numpy as np

from . import lens as lens_module
from .freeform import surface_violation

from .design import review_snapshot
from .design_document import (DocumentError, document_sha256, search_constraints, to_engine_problem,
                              validate_document)
from .external import InputIssue, adapt_ports
from .gaussian import DomainError
from .media import tir_possible
from .mode_match import arrived_mode
from .scene import candidate_scene, extend_with_crossing, ports_scene
from .search import APERTURE_FACTOR, OBJECTIVES, design_continuous
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
        problem = to_engine_problem(document)
        scene = native_ports_scene(document, problem)
    except (InputIssue, DomainError) as exc:
        return _invalid(document, [{'path': getattr(exc, 'path', '$'), 'message': getattr(exc, 'reason', str(exc))}])
    return {'schema': RESULT_SCHEMA, 'status': 'Preview', 'document_sha256': document_sha256(document),
            'ports': scene, 'crossing': crossing_record(problem), 'candidates': [],
            'guidance': port_guidance(scene, document['ambient_index'])}


def native_ports_scene(document, problem):
    """Each Port drawn and guarded in its own medium (ambient or block)."""
    ambient = ports_scene(problem['ambient_engine'])
    if problem['medium'] == 'ambient':
        return ambient
    block = ports_scene(problem['engine'])
    ports = []
    for item_a, item_b in zip(ambient['ports'], block['ports']):
        native = document['ports'][item_a['name']].get('medium', 'ambient')
        ports.append({**(item_b if native == 'block' else item_a), 'medium': native})
    return {'frame_id': ambient['frame_id'], 'ports': ports, 'equivalent_in_block': block['ports']}


def crossing_record(problem):
    crossing = problem['crossing']
    if crossing is None:
        return None
    return {'side': crossing.side, 'surface_point_mm': [v * 1e3 for v in crossing.point],
            'ambient_length_mm': crossing.ambient_length * 1e3, 'incidence_deg': crossing.incidence_deg,
            'refraction_deg': crossing.refraction_deg, 'q_scale_ts': list(crossing.q_scale),
            'fresnel_transmission_uncoated': {'s': crossing.transmission[0], 'p': crossing.transmission[1],
                                              'mean': crossing.transmission[2]},
            'meaning': 'Plane-wave Fresnel transmission of an uncoated surface; information only, not Total Coupling'}


def _candidate(rank, candidate, problem=None, ambient_ports=None):
    evaluation, ranking = candidate['evaluation'], candidate['ranking']
    scene = candidate.get('scene') or candidate_scene(candidate['prescription'])  # q-tensor candidates carry their scene
    crossing = problem['crossing'] if problem else None
    if crossing is not None:
        original = getattr(ambient_ports, crossing.side)
        arrival = None
        if crossing.side == 'target':
            relay_target = adapt_ports(problem['engine']).target
            arrival = arrived_mode(evaluation, relay_target.mode).q
        extend_with_crossing(scene, crossing, original, arrival)
    corrected = candidate.get('freeform') or {}
    if corrected.get('reflectors'):  # P4: draw the corrected surface (13 × 13, same grid as the quadric patch)
        from .freeform import surface_points
        for mirror, record in zip(scene['mirrors'], corrected['reflectors']):
            poly = tuple((t['u_power'], t['v_power'], t['coefficient_si']) for t in record['terms'])
            grid = surface_points(np.array(mirror['vertex_mm']) * 1e-3, mirror['normal'], mirror['t_axis'], mirror['s_axis'],
                                  mirror['curvature_ts_per_m'], [a * 1e-3 for a in mirror['half_aperture_ts_mm']], poly,
                                  n=len(mirror['surface_grid_mm']))
            mirror['surface_grid_corrected_mm'] = (grid * 1e3).tolist()
            mirror['max_sag_change_um'] = record['max_sag_change_um']
    if problem and problem['medium'] == 'block':
        for mirror in scene['mirrors']:
            mirror['tir_possible'] = tir_possible(problem['block'].index, problem['ambient_index'], mirror['incidence_deg'])
    matching = evaluation['gaussian_mode_matching']
    roles = candidate.get('roles') or [candidate.get('recommendation_role')]
    return {
        'id': candidate['id'],
        'rank': rank,
        'role': roles[0],
        'roles': roles,
        'role_labels': [OBJECTIVES.get(r, (None, None, r))[2] for r in roles],
        'family': candidate.get('family', 'exact'),
        'model': candidate.get('model', 'separable'),
        'ray_transfer_check': evaluation.get('ray_transfer_check'),
        'nonparaxial_check': candidate.get('nonparaxial_check'),
        'freeform': candidate.get('freeform'),
        'parameters_mm': {k[:-2]: v * 1e3 for k, v in candidate.get('parameters', {}).items() if k.endswith('_m')},
        'metrics': {
            'total_path_mm': scene['path']['total_length_mm'],
            'ambient_path_mm': sum(seg['length_mm'] for seg in scene['path']['segments'] if seg.get('medium') == 'ambient'),
            'normalized_mode_overlap': matching.get('normalized_mode_overlap'),
            'nonparaxial_overlap': (candidate.get('nonparaxial_check') or {}).get('normalized_mode_overlap'),
            'corrected_nonparaxial_overlap': (candidate.get('freeform') or {}).get('normalized_mode_overlap'),
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


def design_guidance(report, ports, ambient_index, medium='ambient', lens_review=None):
    out = port_guidance(ports, ambient_index) if ports else []
    search = report.get('search', {})
    counts = search.get('screening_counts', {})
    if report.get('model') == 'qtensor':
        out.append({'kind': 'qtensor', 'phase': 'P3',
                    'message': '두 Port가 한 평면에 있지 않거나 축이 돌아가 있어, 반사마다 Beam 축이 회전하는 일반 비점수차 '
                               'q-tensor 모델(2×2 복소 q)로 계산했습니다. 반사면 곡률 축은 Port 축과 다르며, 후보마다 실제 '
                               '곡면을 지나는 광선으로 만든 4×4 Ray-transfer 행렬로 따로 검산합니다.'})
    closest = search.get('closest_exact')
    if closest and report.get('candidates'):
        out.append({'kind': 'exact_outside_guard', 'phase': 'P3',
                    'values': {**closest, 'a_mm': closest['a_m'] * 1e3, 'c_mm': closest['c_m'] * 1e3},
                    'message': f"Exact-q 해는 있지만 가장 여유 있는 배치도 3w·|κ| = {closest['max_footprint_slope']:.4f} > "
                               f"{closest['limit']}입니다. Guard 안에서 Overlap을 최대로 한 Near-match 후보(η < 1)를 표시합니다. "
                               + ("Glass 두께·도파로 깊이·수평 거리를 바꾸면 반사면을 둘 공간이 달라집니다. 렌즈 Family는 P4입니다."
                                  if medium == 'block' else
                                  "Glass 매질 안 배치(P3)는 발산각을 줄여 Exact 해를 Guard 안으로 들일 수 있습니다.")})
    constrained = {k.split(': ', 1)[1]: v for k, v in counts.items() if k.startswith('constraint:')}
    if constrained:
        out.append({'kind': 'constraints', 'values': constrained,
                    'message': f'탐색한 {search.get("grid_points", 0)}개 배치 중 {sum(constrained.values())}개가 '
                               + ('Port 뒤 공간·Glass 영역·Envelope·Keep-out 등' if medium == 'block' else 'Port 뒤 공간·Envelope·Keep-out 등')
                               + ' 공간 제약으로 제외됐습니다.'})
    region = {k: v for k, v in constrained.items() if 'block' in k}
    if medium == 'block' and region and report.get('status') == 'Fail':
        out.append({'kind': 'block_region', 'values': region,
                    'message': f'{sum(region.values())}개 배치에서 반사면 Patch(Beam 반경의 {APERTURE_FACTOR:g}배 투영 Aperture)가 '
                               'Glass 상면이나 하면을 벗어났습니다. 두 반사면은 모두 Glass 안에 있어야 합니다. '
                               '도파로가 얕으면 Target 축 위의 반사면이 상면을 뚫고 나오므로, 매립 깊이나 Glass 두께를 늘리거나 '
                               'Edge(측면) 배치와 비교하세요.'})
    values = [c['nonparaxial_check']['normalized_mode_overlap'] for c in report.get('candidates', [])
              if (c.get('nonparaxial_check') or {}).get('status') == 'Computed']
    if values:
        paraxial = [c['evaluation']['gaussian_mode_matching']['normalized_mode_overlap'] for c in report['candidates']]
        low = min(values) < min(paraxial) - 0.01
        out.append({'kind': 'nonparaxial', 'phase': 'P3', 'level': 'warning' if max(values) < 0.95 else 'info',
                    'values': {'nonparaxial_min': min(values), 'nonparaxial_max': max(values)},
                    'message': f'비근축 Scalar 검산 η는 {min(values):.3f}~{max(values):.3f}입니다(근축 η {min(paraxial):.3f}~{max(paraxial):.3f}). '
                               + ('차이는 반사면을 국소 이차곡면으로 처방해서 생기는 3차 이상 수차(경사 입사의 Coma 등)와 근축 전파 오차입니다. '
                                  '두 반사면이 같은 방향으로 꺾는 배치에서는 Coma가 더해지고, 반대로 꺾는 Z형 배치에서는 상쇄됩니다. '
                                  '근축 η만으로 판단하지 말고 비근축 η와 보정 곡면 결과를 함께 보세요.' if low else
                                  '근축 결과와 차이가 작아 이 후보들에서는 근축 모델이 맞습니다.')})
    corrected = [c['freeform']['normalized_mode_overlap'] for c in report.get('candidates', [])
                 if (c.get('freeform') or {}).get('status') == 'Computed' and not c['freeform'].get('constraint')]
    if corrected:
        out.append({'kind': 'freeform', 'phase': 'P4', 'level': 'info',
                    'values': {'corrected_min': min(corrected), 'corrected_max': max(corrected)},
                    'message': f'3·4차 Sag 보정(Coma 보정 곡면)을 더하면 비근축 η가 {min(corrected):.3f}~{max(corrected):.3f}가 됩니다. '
                               '꼭짓점·법선·곡률(근축 설계)은 그대로이고, 보정량은 후보 상세의 반사면별 최대 Sag 변화로 확인합니다. '
                               '보정 곡면은 3D에 그려지고 결과 JSON에 계수가 있습니다.'})
    study = report.get('nonparaxial_study')
    if study:
        out.append({'kind': 'nonparaxial_study', 'phase': 'P3', 'level': 'info', 'values': study.get('summary'),
                    'message': study.get('message', '')})
    if lens_review:
        values = [c['metrics']['nonparaxial_overlap'] for c in lens_review['candidates'] if c.get('accepted')]
        out.append({'kind': 'lens_review', 'phase': 'P4', 'level': 'info',
                    'values': {'count': len(values), 'eta_min': min(values) if values else None,
                               'eta_max': max(values) if values else None},
                    'message': (f'Micro-lens + 두 반사면 Family 후보 {len(values)}개를 Computed로 채택했습니다: 비근축 η {min(values):.3f}~{max(values):.3f}. '
                                'Lens가 Port Mode를 Guard 안으로 키운 뒤 Relay를 설계하고, Lens·반사면 전체의 비근축 η(수렴, ≥ '
                                f'{lens_module.LENS_ACCEPT_ETA})와 Lens 몸체 제약으로 채택합니다. 표의 η는 등가 Port 사이 근축 값이므로 비근축 η 열을 보세요.'
                                if values else 'Micro-lens + 두 반사면 Family도 비근축 확인을 통과한 후보가 없습니다. '
                                + ' '.join(lens_reason_label(r) for r in sorted(set(lens_review.get('fail_reasons', []))))[:400])})
    if report.get('status') == 'Fail' and search.get('status') == 'Completed':
        top = sorted(counts.items(), key=lambda kv: -kv[1])[:3]
        out.append({'kind': 'no_candidate', 'phase': 'P4',
                    'message': 'Lens 없는 두 반사면 Family 안에서 Guard와 제약을 모두 만족하는 배치가 없습니다(물리적 불가능의 증명은 아님). '
                               '주요 사유: ' + ', '.join(f'{k} ({v})' for k, v in top)})
    return out


def lens_reason_label(reason):
    import re
    found = re.match(r'Port divergence ([0-9.]+) rad is beyond a single aspheric singlet \(limit ([0-9.]+) rad', reason or '')
    if found:
        return (f'Port 발산각 {found.group(1)} rad는 단일 비구면 Lens 하나로 받을 수 있는 범위({found.group(2)} rad)를 넘습니다 '
                '(1/e² 각의 2.6배 광선까지 sin 0.85 이하로 꺾어야 함). 두 Lens 또는 고굴절률 Lens가 필요합니다.')
    return reason or ''


def lens_family_review(engine_input, constraints, problem, ports):
    """P4 Lens Family (Micro-lens + two reflectors) as review candidates: never counted as Computed."""
    if problem['block'] is not None:
        return {'status': 'Uncomputed', 'candidates': [], 'runs': [],
                'meaning': 'Lens Family는 아직 공기(주변 매질) Relay만 다룹니다. Glass Block 문제에는 적용하지 않았습니다.'}
    family = lens_module.lens_family(engine_input, constraints)
    if family is None:
        return None
    real = adapt_ports(engine_input)
    candidates, reasons, runs = [], [], []
    for run in family['runs']:
        runs.append({'theta_out_rad': run['theta_out_rad'], 'status': run['status'], 'reason': run.get('reason'),
                     'lenses': run.get('lenses', [])})
        if run['status'] != 'Computed':
            reasons.append(run.get('reason') or run['status'])
        for row in run['candidates']:
            if 'equivalent_candidate' not in row:
                reasons.append(row.get('reason') or row['status'])
                continue
            record = _candidate(len(candidates) + 1, row['equivalent_candidate'])
            constraint = None
            for lens_object in row['lens_objects']:
                lens_module.extend_scene(record['scene'], lens_object, getattr(real, lens_object.side))
                points = np.array([q for line in record['scene']['lenses'][-1]['outline_mm'] for q in line]) * 1e-3
                found = surface_violation(real, replace(constraints, port_halfspace=False), points)
                if found and constraint is None:
                    constraint = found.replace('corrected surface', 'lens body')
            check = row['nonparaxial_check']
            record.update({
                'id': 'L-' + row['id'], 'review': True, 'role': 'lens_review', 'roles': ['lens_review'],
                'role_labels': ['Lens Family 검토 후보'], 'family': 'lens_two_reflector', 'review_status': row['status'],
                'theta_out_rad': run['theta_out_rad'], 'lenses': row['lenses'], 'lens_checks': row['lens_checks'],
                'lens_constraint': constraint,
                'nonparaxial_check': check, 'fit_history': row['fit_history'],
                'reflector_terms': row['reflector_terms'], 'freeform': None,
            })
            record['metrics'].update({'nonparaxial_overlap': check.get('normalized_mode_overlap'),
                                      'corrected_nonparaxial_overlap': None,
                                      'paraxial_equivalent_overlap': record['metrics']['normalized_mode_overlap']})
            candidates.append(record)
    def accepted(c):
        return (c['review_status'] == 'Computed' and not c['lens_constraint']
                and (c['metrics']['nonparaxial_overlap'] or 0) >= lens_module.LENS_ACCEPT_ETA)
    order = sorted(candidates, key=lambda c: (not accepted(c), -(c['metrics']['nonparaxial_overlap'] or 0)))
    for rank, c in enumerate(order, start=1):
        c['rank'] = rank
        c['accepted'] = accepted(c)
        c['review'] = not c['accepted']
        if c['accepted']:
            c['roles'] = ['lens_best'] if rank == 1 else ['lens_alternative']
            c['role_labels'] = ['Lens Family · 비근축 η 최대'] if rank == 1 else ['Lens Family 대안']
    return {'status': 'Computed' if any(c['accepted'] for c in order) else 'Review', 'sides': family['sides'],
            'runs': runs, 'candidates': order, 'fail_reasons': reasons,
            'accept_rule': {'nonparaxial_status': 'Computed', 'min_nonparaxial_overlap': lens_module.LENS_ACCEPT_ETA,
                            'lens_constraint': None},
            'meaning': family['meaning']}


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
        problem = to_engine_problem(document)
        problem['ambient_index'] = document['ambient_index']
        engine_input = problem['engine']
        ports = native_ports_scene(document, problem)
        constraints = search_constraints(document)
        if problem['block'] is not None:
            constraints = replace(constraints, block=problem['block'],
                                  block_side='inside' if problem['medium'] == 'block' else 'outside')
        ambient_ports = adapt_ports(problem['ambient_engine'])
    except (DocumentError, InputIssue, DomainError) as exc:
        return _invalid(document, [{'path': getattr(exc, 'path', '$'), 'message': getattr(exc, 'reason', str(exc))}])
    report = design_continuous(engine_input, constraints)
    if report['status'] == 'Fail' and 'divergence' in (report.get('reason') or ''):
        from .nonparaxial import guard_study
        report['nonparaxial_study'] = guard_study(engine_input, constraints)
    lens_review = None
    if report['status'] == 'Fail' and 'divergence' in (report.get('reason') or ''):
        lens_review = lens_family_review(engine_input, constraints, problem, ports)
    if report['candidates'] and report.get('model') != 'qtensor':  # sensitivity/placement studies are separable-engine tools
        report = review_snapshot(report)
    status, reason = report['status'], report.get('reason')
    selected_id = report.get('selected_candidate_id')
    family = report['candidates'][0].get('family') if report['candidates'] else None
    candidates = [_candidate(i + 1, c, problem, ambient_ports) for i, c in enumerate(report['candidates'])]
    accepted = [c for c in (lens_review or {}).get('candidates', []) if c.get('accepted')]
    if accepted:  # P4 Lens Family: accepted by the non-paraxial check only (user decision 2026-11-24)
        status, family, candidates, selected_id = 'Computed', 'lens_two_reflector', accepted, accepted[0]['id']
        if report.get('nonparaxial_study'):
            study = report['nonparaxial_study']
            study['message'] = study.get('message', '').replace('후보는 내지 않았습니다', 'Lens 없는 두 반사면 후보는 내지 않았습니다')
        reason = (f'Lens Family: {reason}; a micro-lens expands the Port mode inside the guard and '
                  f'{len(accepted)} candidates pass the non-paraxial check (η ≥ {lens_module.LENS_ACCEPT_ETA})')
    search = report.get('search', {})
    summary = {k: search.get(k) for k in ('status', 'reason', 'grid_points', 'exact_feasible', 'near_match_feasible',
                                          'screening_counts', 'closest_exact', 'elapsed_seconds', 'verification',
                                          'nonparaxial_screen')}
    return {
        'schema': RESULT_SCHEMA,
        'status': status,
        'reason': reason,
        'document_sha256': document_sha256(document),
        'engine_input_sha256': report.get('input_sha256'),
        'selected_candidate_id': selected_id,
        'family': family,
        'ports': ports,
        'constraints': report.get('constraints'),
        'relay_medium': problem['medium'],
        'crossing': crossing_record(problem),
        'candidates': candidates,
        'search': {**summary, 'policy': report.get('search_policy', {}).get('id'), 'map': _map(search)},
        'guidance': design_guidance(report, ports, document['ambient_index'], problem['medium'], lens_review),
        'nonparaxial_study': report.get('nonparaxial_study'),
        'lens_review': lens_review,
        'limitations': report.get('limitations', []),
        'uncomputed': UNCOMPUTED,
        'engine_report': {**report, 'search': {k: v for k, v in search.items() if k != 'map'}},
    }
