"""Pure functions behind the JSON API. No HTTP here, so tests call them directly.

`preview` draws Ports before any design. `design` runs the unchanged validated engine
on the converted Design Document and returns `pae.result/1`: engine verdicts plus
drawable geometry for every representative candidate.
"""

from .design import design_two_ports
from .design_document import DocumentError, document_sha256, to_engine_input, validate_document
from .external import InputIssue
from .gaussian import DomainError
from .placement import compare_placement
from .scene import candidate_scene, ports_scene
from .sensitivity import compare_sensitivity

RESULT_SCHEMA = 'pae.result/1'
STATUS_KEYS = ('input_contract', 'geometry', 'model_domain', 'gaussian_mode_matching',
               'package_feasibility', 'physical_losses', 'fabrication', 'actual_applicability')
UNCOMPUTED = ['Total Coupling (interfaces, coatings, polarization, diffraction)',
              'Vector / non-paraxial field validation',
              'Assembly tolerance distribution and yield',
              'Full package clearance (supports, bodies)',
              'Patentability']


def _invalid(document, issues):
    return {'schema': RESULT_SCHEMA, 'status': 'Invalid', 'reason': '입력 문서에 오류가 있습니다',
            'issues': issues, 'document_sha256': document_sha256(document) if isinstance(document, dict) else None,
            'ports': None, 'candidates': []}


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
            'ports': scene, 'candidates': []}


def _candidate(rank, candidate):
    evaluation, ranking = candidate['evaluation'], candidate['ranking']
    scene = candidate_scene(candidate['prescription'])
    matching = evaluation['gaussian_mode_matching']
    return {
        'id': candidate['id'],
        'rank': rank,
        'role': candidate.get('recommendation_role'),
        'metrics': {
            'total_path_mm': scene['path']['total_length_mm'],
            'normalized_mode_overlap': matching.get('normalized_mode_overlap'),
            'mode_mismatch_db': matching.get('mismatch_db'),
            'max_projected_beam_radius_um': ranking['max_projected_radius_m'] * 1e6,
            'max_3w_footprint_curvature': ranking['max_3w_footprint_curvature'],
            'footprint_curvature_limit': 0.15,
            'incidence_deg': [m['incidence_deg'] for m in scene['mirrors']],
            'radius_of_curvature_ts_mm': [m['radius_of_curvature_ts_mm'] for m in scene['mirrors']],
        },
        'status': {key: evaluation[key]['status'] for key in STATUS_KEYS if key in evaluation},
        'scene': scene,
    }


def design(document):
    issues = validate_document(document)
    if issues:
        return _invalid(document, issues)
    try:
        engine_input = to_engine_input(document)
        ports = ports_scene(engine_input)
    except (DocumentError, InputIssue, DomainError) as exc:
        return _invalid(document, [{'path': getattr(exc, 'path', '$'), 'message': getattr(exc, 'reason', str(exc))}])
    report = design_two_ports(engine_input)
    if report['candidates']:
        report = {**report, 'candidate_sensitivity': compare_sensitivity(report),
                  'reflector_placement': compare_placement(report)}
    search = report.get('search', {})
    return {
        'schema': RESULT_SCHEMA,
        'status': report['status'],
        'reason': report.get('reason'),
        'document_sha256': document_sha256(document),
        'engine_input_sha256': report.get('input_sha256'),
        'selected_candidate_id': report.get('selected_candidate_id'),
        'ports': ports,
        'candidates': [_candidate(i + 1, c) for i, c in enumerate(report['candidates'])],
        'search': {k: search.get(k) for k in ('status', 'reason', 'accepted_count', 'representatives',
                                              'geometry_count', 'rejection_counts', 'termination')},
        'limitations': report.get('limitations', []),
        'uncomputed': UNCOMPUTED,
        'engine_report': report,
    }
