"""Design Document v1 (`pae.design/1`): the single user-facing input record.

The Workspace, the JSON API and the scenario fixtures all exchange this document.
It uses engineering units (mm, µm, nm) and carries provenance for every Port
quantity. `to_engine_input` converts it, without defaults or normalization, into
the existing M3A-1 two-Port contract that the validated engine consumes.
"""

import hashlib
import json
import math

from .external import CONVENTION, PROVENANCE

SCHEMA = 'pae.design/1'
PORT_NAMES = ('source', 'target')
EVIDENCE_KEYS = ('placement', 'mode', 'phase')
UNIT_TOLERANCE = 1e-10  # same tolerance as the engine's unit-vector check
DEFAULT_EVIDENCE = {
    'placement': {'provenance': 'assumed', 'source': 'User placement in the Design Document'},
    'mode': {'provenance': 'assumed', 'source': 'User-entered Gaussian MFD'},
    'phase': {'provenance': 'assumed', 'source': 'User-entered wavefront curvature at the external reference plane'},
}


class DocumentError(ValueError):
    """Structural problems; `issues` lists every problem found, not only the first."""

    def __init__(self, issues):
        self.issues = issues
        super().__init__('; '.join(f"{i['path']}: {i['message']}" for i in issues))


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _vector(issues, node, key, size, path, *, unit=False, positive=False):
    value = node.get(key) if isinstance(node, dict) else None
    label = f'{path}.{key}'
    if not isinstance(value, list) or len(value) != size or not all(_finite(v) for v in value):
        issues.append({'path': label, 'message': f'{size}개의 유한한 숫자가 필요합니다'})
        return None
    if positive and min(value) <= 0:
        issues.append({'path': label, 'message': '양수가 필요합니다'})
        return None
    if unit and abs(math.sqrt(sum(v * v for v in value)) - 1) > UNIT_TOLERANCE:
        issues.append({'path': label, 'message': '단위 벡터가 필요합니다(자동 정규화하지 않음)'})
        return None
    return value


def validate_document(document):
    """Return a list of {path, message}; an empty list means structurally valid."""
    issues = []
    if not isinstance(document, dict):
        return [{'path': '$', 'message': 'JSON object가 필요합니다'}]
    if document.get('schema') != SCHEMA:
        issues.append({'path': 'schema', 'message': f'"{SCHEMA}"가 필요합니다'})
    wavelength = document.get('wavelength_nm')
    if not _finite(wavelength) or not 200 <= wavelength <= 20000:
        issues.append({'path': 'wavelength_nm', 'message': '200~20000 nm 범위의 숫자가 필요합니다'})
    index = document.get('ambient_index')
    if not _finite(index) or index <= 0:
        issues.append({'path': 'ambient_index', 'message': '양의 실수가 필요합니다'})
    ports = document.get('ports')
    if not isinstance(ports, dict):
        issues.append({'path': 'ports', 'message': 'source와 target이 필요합니다'})
        return issues
    for name in PORT_NAMES:
        path = f'ports.{name}'
        port = ports.get(name)
        if not isinstance(port, dict):
            issues.append({'path': path, 'message': 'Port object가 필요합니다'})
            continue
        _vector(issues, port, 'position_mm', 3, path)
        direction = _vector(issues, port, 'direction', 3, path, unit=True)
        sagittal = _vector(issues, port, 'sagittal_axis', 3, path, unit=True)
        if direction and sagittal and abs(sum(a * b for a, b in zip(direction, sagittal))) > UNIT_TOLERANCE:
            issues.append({'path': f'{path}.sagittal_axis', 'message': 'direction과 수직이어야 합니다'})
        _vector(issues, port, 'mfd_um', 2, path, positive=True)
        _vector(issues, port, 'wavefront_curvature_per_m', 2, path)
        evidence = port.get('evidence', {})
        if not isinstance(evidence, dict):
            issues.append({'path': f'{path}.evidence', 'message': 'object가 필요합니다'})
            continue
        for key in EVIDENCE_KEYS:
            record = evidence.get(key)
            if record is None:
                continue
            if (not isinstance(record, dict) or record.get('provenance') not in PROVENANCE - {'unprovided'}
                    or not isinstance(record.get('source'), str) or not record['source'].strip()):
                issues.append({'path': f'{path}.evidence.{key}',
                               'message': f'provenance({", ".join(sorted(PROVENANCE - {"unprovided"}))})와 source가 필요합니다'})
    issues += validate_constraints(document.get('constraints'))
    return issues


def _box(issues, node, path):
    if not isinstance(node, dict):
        issues.append({'path': path, 'message': 'min/max 3-벡터가 필요합니다'})
        return
    lo, hi = node.get('min'), node.get('max')
    if not (isinstance(lo, list) and isinstance(hi, list) and len(lo) == 3 and len(hi) == 3
            and all(_finite(v) for v in lo + hi)):
        issues.append({'path': path, 'message': 'min/max 3-벡터가 필요합니다'})
    elif any(a >= b for a, b in zip(lo, hi)):
        issues.append({'path': path, 'message': '각 축에서 min < max 이어야 합니다'})


def validate_constraints(constraints):
    """Optional user constraints; they may only tighten the frozen guards."""
    if constraints is None:
        return []
    issues = []
    if not isinstance(constraints, dict):
        return [{'path': 'constraints', 'message': 'object가 필요합니다'}]
    unknown = set(constraints) - {'port_body_halfspace', 'envelope_mm', 'keepouts_mm', 'clearance_um',
                                  'max_incidence_deg', 'min_radius_of_curvature_mm', 'source'}
    if unknown:
        issues.append({'path': 'constraints', 'message': f'알 수 없는 항목: {", ".join(sorted(unknown))}'})
    if not isinstance(constraints.get('port_body_halfspace', True), bool):
        issues.append({'path': 'constraints.port_body_halfspace', 'message': 'true/false가 필요합니다'})
    if constraints.get('envelope_mm') is not None:
        _box(issues, constraints['envelope_mm'], 'constraints.envelope_mm')
    keepouts = constraints.get('keepouts_mm', [])
    if not isinstance(keepouts, list):
        issues.append({'path': 'constraints.keepouts_mm', 'message': '목록이 필요합니다'})
    else:
        for i, box in enumerate(keepouts):
            _box(issues, box, f'constraints.keepouts_mm[{i}]')
    clearance = constraints.get('clearance_um', 0)
    if not _finite(clearance) or clearance < 0:
        issues.append({'path': 'constraints.clearance_um', 'message': '0 이상의 숫자가 필요합니다'})
    incidence = constraints.get('max_incidence_deg', 70)
    if not _finite(incidence) or not 0 < incidence <= 70:
        issues.append({'path': 'constraints.max_incidence_deg', 'message': '0 초과 70 이하(Frozen Guard)여야 합니다'})
    roc = constraints.get('min_radius_of_curvature_mm')
    if roc is not None and (not _finite(roc) or roc <= 0):
        issues.append({'path': 'constraints.min_radius_of_curvature_mm', 'message': '양수 또는 null이 필요합니다'})
    return issues


def search_constraints(document):
    """Design Document constraints (mm/µm) as the generator's SI Constraints."""
    from .search import Constraints
    c = document.get('constraints') or {}
    box = lambda b: (tuple(v * 1e-3 for v in b['min']), tuple(v * 1e-3 for v in b['max']))  # noqa: E731
    keepouts = c.get('keepouts_mm', [])
    roc = c.get('min_radius_of_curvature_mm')
    return Constraints(port_halfspace=c.get('port_body_halfspace', True),
                       envelope=box(c['envelope_mm']) if c.get('envelope_mm') else None,
                       keepouts=tuple(box(k) for k in keepouts),
                       keepout_labels=tuple(k.get('label', f'keep-out {i + 1}') for i, k in enumerate(keepouts)),
                       clearance=c.get('clearance_um', 0) * 1e-6,
                       max_incidence_deg=c.get('max_incidence_deg', 70),
                       min_radius_of_curvature=roc * 1e-3 if roc else None)


def _package(document):
    """Envelope/keep-outs also go to the engine's own package check, so it re-verifies them independently."""
    c = document.get('constraints') or {}
    if not c.get('envelope_mm') and not c.get('keepouts_mm'):
        return None
    ev = {'provenance': 'assumed', 'source': c.get('source') or 'User package constraints in the Design Document'}
    aabb = lambda b: {'type': 'aabb', 'min_m': [v * 1e-3 for v in b['min']], 'max_m': [v * 1e-3 for v in b['max']]}  # noqa: E731
    package = {'frame_id': _record('world', 'frame', ev),
               'keepout_bodies': _record([aabb(k) for k in c.get('keepouts_mm', [])], 'm', ev),
               'required_clearance_m': _record(c.get('clearance_um', 0) * 1e-6, 'm', ev)}
    if c.get('envelope_mm'):
        package['available_volume'] = _record(aabb(c['envelope_mm']), 'm', ev)
    return package


def canonical_json(document):
    return json.dumps(document, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def document_sha256(document):
    return hashlib.sha256(canonical_json(document).encode('utf-8')).hexdigest()


def evidence(port, key):
    record = (port.get('evidence') or {}).get(key)
    return record if record is not None else DEFAULT_EVIDENCE[key]


def _record(value, unit, ev, uncertainty=None, **extra):
    return {'value': value, 'unit': unit, 'provenance': ev['provenance'], 'source': ev['source'],
            'uncertainty': uncertainty, **extra}


def _engine_port(name, port):
    placement, mode, phase = (evidence(port, k) for k in EVIDENCE_KEYS)
    position = [v * 1e-3 for v in port['position_mm']]
    direction = list(port['direction'])
    kind = 'synthetic_gaussian' if mode['provenance'] == 'synthetic' else 'gaussian_assumption'
    return {
        'position_m': _record(position, 'm', placement),
        'propagation_direction': _record(direction, '1', placement),
        'sagittal_axis': _record(list(port['sagittal_axis']), '1', placement),
        'reference_plane': _record({'id': f'{name}-external', 'frame_id': 'world', 'side': 'external',
                                    'origin_m': position, 'normal': direction}, 'plane', placement),
        'polarization': _record({'treatment': 'scalar_ignored'}, '1',
                                {'provenance': 'assumed', 'source': 'Scalar model; polarization not transported'}),
        'mode_evidence': _record({'kind': kind, 'label': port.get('label'), 'preset': port.get('preset')},
                                 'evidence', mode),
        'mfd_ts_m': _record([v * 1e-6 for v in port['mfd_um']], 'm', mode),
        'wavefront_curvature_ts_per_m': _record(list(port['wavefront_curvature_per_m']), 'm^-1', phase),
    }


def to_engine_input(document):
    """Convert a valid Design Document into the engine's M3A-1 two-Port contract."""
    issues = validate_document(document)
    if issues:
        raise DocumentError(issues)
    common = {'provenance': 'assumed', 'source': f'Design Document: {document.get("title") or "untitled"}'}
    engine = {
        'contract_version': 'M3A-1',
        'coordinate_convention': CONVENTION,
        'description': document.get('description') or document.get('title') or 'Design Document',
        'wavelength_m': _record(document['wavelength_nm'] * 1e-9, 'm', common),
        'ambient_index': _record(document['ambient_index'], '1', common,
                                 quantity='external_ambient_refractive_index'),
        **{name: _engine_port(name, document['ports'][name]) for name in PORT_NAMES},
    }
    package = _package(document)
    if package:
        engine['package'] = package
    return engine
