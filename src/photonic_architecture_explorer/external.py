"""External record adapter. Physics remains in the frozen M1/M2 kernels."""

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path

from .gaussian import Gaussian, DomainError
from .geometry import Port, Reflector, norm, sub
from .solver import evaluate
from .package_geometry import assess_package

CONVENTION = 'right-handed world XYZ; t=s cross d; target d is arriving direction'
PROVENANCE = {'measured', 'supplied', 'independently_validated', 'simulated',
              'assumed', 'synthetic', 'unprovided'}
# Exact known spellings only; never strip an arbitrary unit prefix (e.g. mm).
UNITS = {
    'length': {'m', 'm [x,y,z]'},
    'wavelength': {'m', 'vacuum m'},
    'index': {'1', 'positive real external homogeneous index'},
    'vector': {'1', 'unit vector [x,y,z]'},
    'aperture': {'m', 'm [t,s]'},
    'mfd': {'m', 'm [t,s], 1/e^2 intensity diameter'},
    'phase': {'m^-1', 'inverse m [t,s]'},
    'q': {'m', 'm [[real,imag],[real,imag]], alternative to MFD+curvature'},
    'polarization': {'1', 'complex Jones [t,s] or explicit scalar-ignored assumption'},
    'plane': {'plane', 'id and external side, origin=position, normal=propagation_direction'},
    'evidence': {'evidence', 'external complex field/fit at named plane; measured/simulated/assumed'},
    'surface': {'model', 'quadratic patch or supported explicit prescription'},
    'position_bounds': {'m', 'm [[min_xyz],[max_xyz]]'},
    'normal_bounds': {'rad', 'unit vectors or angular bounds rad'},
    'curvature_bounds': {'m^-1', 'inverse m [[t_min,t_max],[s_min,s_max]], signed'},
    'aperture_bounds': {'m', 'm [[t_min,t_max],[s_min,s_max]]'},
    'volume': {'m', 'm, closed world-coordinate AABB or explicit solid'},
    'keepouts': {'m', 'm, explicit solid list (empty requires explicit assumption)'},
    'clearance': {'m', 'm nonnegative'},
    'frame': {'frame', 'common world frame and transform origin'},
    'body': {'m', 'm explicit backing/support solid'},
}


class InputIssue(ValueError):
    def __init__(self, status, path, reason):
        self.status, self.path, self.reason = status, path, reason
        super().__init__(f'{path}: {reason}')


def fail(path, reason):
    raise InputIssue('Fail', path, reason)


def number(value, path):
    if value is None:
        raise InputIssue('Uncomputed', path, 'scalar component not supplied')
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        fail(path, 'finite real scalar required; ranges are not nominal values')
    return value


def vector(value, size, path):
    if not isinstance(value, (list, tuple)) or len(value) != size:
        fail(path, f'{size} coordinates required')
    return tuple(number(v, path) for v in value)


def unit_vector(value, path):
    value = vector(value, 3, path)
    if abs(norm(value)-1) > 1e-10:
        fail(path, 'explicit unit vector required; no silent direction normalization')
    return value


def read(node, key, kind, path, required=True):
    label = f'{path}.{key}' if path else key
    if node is not None and not isinstance(node, dict):
        fail(path, 'object required')
    record = node.get(key) if isinstance(node, dict) else None
    if record is None:
        if not required:
            return None
        raise InputIssue('Uncomputed', label, 'record not supplied')
    if not isinstance(record, dict) or not {'value', 'unit', 'provenance', 'source', 'uncertainty'} <= record.keys():
        fail(label, 'record requires value/unit/provenance/source/uncertainty')
    if not isinstance(record['unit'], str) or record['unit'] not in UNITS[kind]:
        fail(label, f'unsupported unit; expected {sorted(UNITS[kind])}')
    if not isinstance(record['provenance'], str) or record['provenance'] not in PROVENANCE:
        fail(label, 'unknown provenance')
    value = record['value']
    if value is None:
        if not required:
            return None
        raise InputIssue('Uncomputed', label, 'value not supplied')
    if record['provenance'] == 'unprovided' or not isinstance(record['source'], str) or not record['source'].strip():
        fail(label, 'provided value requires explicit provenance and source')
    return value


def _keys(node, allowed, path):
    if not isinstance(node, dict):
        fail(path, 'object required')
    if set(node)-set(allowed):
        fail(path, 'unsupported fields: '+', '.join(sorted(set(node)-set(allowed))))


def _mode(node, wavelength, index, label):
    mfd = read(node, 'mfd_ts_m', 'mfd', label, False)
    phase = read(node, 'wavefront_curvature_ts_per_m', 'phase', label, False)
    q = read(node, 'complex_q_ts_m', 'q', label, False)
    widths = vector(mfd, 2, label+'.mfd') if mfd is not None else None
    curvatures = vector(phase, 2, label+'.phase') if phase is not None else None
    if widths is not None and min(widths) <= 0:
        fail(label, 'positive MFD required')
    from_q = None
    if q is not None:
        if not isinstance(q, list) or len(q) != 2:
            fail(label, 'ordinary complex q requires two [real,imag] pairs in metres')
        values = [complex(*vector(axis, 2, label+'.q')) for axis in q]
        from_q = Gaussian(*values, wavelength, index)
        # Every supplied redundant component is checked, including partial MFD/C.
        for j, pars in enumerate(from_q.parameters()):
            if widths is not None and not math.isclose(widths[j], 2*pars['radius_m'], rel_tol=1e-9, abs_tol=1e-15):
                fail(label, 'MFD and q are inconsistent')
            if curvatures is not None and not math.isclose(curvatures[j], pars['curvature_per_m'], rel_tol=1e-9, abs_tol=1e-8):
                fail(label, 'phase curvature and q are inconsistent')
    if from_q is not None:
        return from_q
    if widths is None or curvatures is None:
        raise InputIssue('Uncomputed', label, 'MFD+phase or complete ordinary q required; no waist default')
    return Gaussian.from_radii(tuple(w/2 for w in widths), wavelength, index, curvatures)


def _port(node, wavelength, index, label):
    if node is None:
        raise InputIssue('Uncomputed', label, 'Port not supplied')
    _keys(node, {'position_m', 'propagation_direction', 'sagittal_axis', 'reference_plane',
                 'polarization', 'mode_evidence', 'mfd_ts_m', 'wavefront_curvature_ts_per_m', 'complex_q_ts_m'}, label)
    position = vector(read(node, 'position_m', 'length', label), 3, label+'.position')
    direction = unit_vector(read(node, 'propagation_direction', 'vector', label), label+'.direction')
    sagittal = unit_vector(read(node, 'sagittal_axis', 'vector', label), label+'.sagittal')
    plane = read(node, 'reference_plane', 'plane', label)
    if not isinstance(plane, dict) or not all(isinstance(plane.get(k), str) and plane[k] for k in ('id', 'frame_id', 'side')):
        fail(label, 'reference plane needs id/frame_id/external side')
    _keys(plane, {'id', 'frame_id', 'side', 'origin_m', 'normal'}, label+'.reference_plane')
    if plane['side'] != 'external':
        fail(label, 'guided/facet-internal planes unsupported; external field required')
    if vector(plane.get('origin_m'), 3, label+'.plane.origin') != position:
        fail(label, 'reference plane origin differs from fixed Port position')
    if norm(sub(unit_vector(plane.get('normal'), label+'.plane.normal'), direction)) > 1e-10:
        fail(label, 'reference plane normal must equal propagation direction (incoming at Target)')
    pol = read(node, 'polarization', 'polarization', label)
    if not isinstance(pol, dict) or pol.get('treatment') != 'scalar_ignored':
        fail(label, 'explicit scalar_ignored polarization assumption required; no Jones transport')
    _keys(pol, {'treatment', 'jones_ts'}, label+'.polarization')
    if 'jones_ts' in pol:
        jones = pol['jones_ts']
        if not isinstance(jones, list) or len(jones) != 2:
            fail(label, 'Jones vector requires two complex pairs')
        if sum(abs(complex(*vector(v, 2, label+'.Jones')))**2 for v in jones) <= 0:
            fail(label, 'nonzero Jones vector required')
    evidence = read(node, 'mode_evidence', 'evidence', label)
    if not isinstance(evidence, dict) or evidence.get('kind') not in {'synthetic_gaussian', 'gaussian_assumption', 'complex_field_fit'}:
        fail(label, 'explicit Gaussian assumption or complex field-fit evidence required')
    port = Port(position, direction, sagittal, _mode(node, wavelength, index, label))
    return port, plane['frame_id']


@dataclass(frozen=True)
class AdaptedDesign:
    source: Port
    target: Port
    reflectors: tuple
    frame_id: str
    input_json: str  # immutable, complete original values/units/provenance/uncertainty


def adapt_external(document):
    """No defaults; convert one explicit nominal design without changing Ports."""
    snapshot = json.dumps(document, allow_nan=False, sort_keys=True)
    if not isinstance(document, dict):
        fail('input', 'object required')
    _keys(document, {'contract_version', 'coordinate_convention', 'wavelength_m', 'ambient_index',
                     'source', 'target', 'reflectors', 'package', 'design', 'description'}, 'input')
    if document.get('contract_version') is None or document.get('coordinate_convention') is None:
        raise InputIssue('Uncomputed', 'input', 'contract version and coordinate convention required')
    if document.get('contract_version') not in ('M25-1', 'M3A-1'):
        fail('contract_version', 'supported versions: M25-1 or M3A-1')
    if document.get('coordinate_convention') != CONVENTION:
        fail('coordinate_convention', 'explicit supported right-handed convention required')
    wavelength = number(read(document, 'wavelength_m', 'wavelength', ''), 'wavelength')
    index = number(read(document, 'ambient_index', 'index', ''), 'ambient_index')
    if document['ambient_index'].get('quantity') != 'external_ambient_refractive_index':
        if 'quantity' not in document['ambient_index']:
            raise InputIssue('Uncomputed', 'ambient_index.quantity', 'external ambient identity not declared')
        fail('ambient_index.quantity', 'guided effective index is not an external ambient input')
    source, frame = _port(document.get('source'), wavelength, index, 'source')
    target, target_frame = _port(document.get('target'), wavelength, index, 'target')
    if frame != target_frame:
        fail('frame_id', 'Source/Target need one shared frame; transforms unsupported')
    constraints = document.get('reflectors')
    if constraints is None:
        raise InputIssue('Uncomputed', 'reflectors', 'surface contracts not supplied')
    if not isinstance(constraints, list) or len(constraints) != 2:
        fail('reflectors', 'exactly two reflector contracts required')
    design = document.get('design')
    if design is None:
        raise InputIssue('Uncomputed', 'design', 'explicit nominal reflector geometry required')
    _keys(design, {'reflectors'}, 'design')
    mirrors = design.get('reflectors')
    if not isinstance(mirrors, list) or len(mirrors) != 2:
        fail('design', 'exactly two explicit Reflectors required')
    result = []
    for j, node in enumerate(mirrors):
        label = f'design.reflectors[{j}]'
        _keys(node, {'vertex_m', 'illuminated_normal', 'principal_curvature_ts_per_m', 'half_aperture_ts_m'}, label)
        _keys(constraints[j], {'vertex_bounds_m', 'normal_constraints', 'principal_curvature_bounds_per_m',
                              'half_aperture_bounds_m', 'surface_prescription', 'body_envelope'}, f'reflectors[{j}]')
        prescription = read(constraints[j], 'surface_prescription', 'surface', f'reflectors[{j}]')
        if prescription != 'quadratic_patch':
            fail(label, 'only explicit quadratic_patch surface prescription supported')
        result.append(Reflector(
            vector(read(node, 'vertex_m', 'length', label), 3, label+'.vertex'),
            unit_vector(read(node, 'illuminated_normal', 'vector', label), label+'.normal'),
            vector(read(node, 'principal_curvature_ts_per_m', 'phase', label), 2, label+'.curvature'),
            vector(read(node, 'half_aperture_ts_m', 'aperture', label), 2, label+'.aperture')))
    return AdaptedDesign(source, target, tuple(result), frame, snapshot)


def _bounds(value, size, path):
    if not isinstance(value, list) or len(value) != size:
        fail(path, f'{size} [min,max] intervals required')
    pairs = [vector(v, 2, path) for v in value]
    if any(lo > hi for lo, hi in pairs):
        fail(path, 'inverted interval')
    return pairs


def assess_constraints(document, adapted):
    checks = []
    for j, (node, mirror) in enumerate(zip(document['reflectors'], adapted.reflectors)):
        for key, kind, values in (
            ('vertex_bounds_m', 'position_bounds', mirror.vertex),
            ('principal_curvature_bounds_per_m', 'curvature_bounds', mirror.curvatures),
            ('half_aperture_bounds_m', 'aperture_bounds', mirror.half_aperture),
            ('normal_constraints', 'normal_bounds', mirror.normal)):
            label = f'reflectors[{j}].{key}'
            try:
                raw = read(node, key, kind, f'reflectors[{j}]')
                if key == 'vertex_bounds_m':
                    if not isinstance(raw, list) or len(raw) != 2:
                        fail(label, '[min_xyz,max_xyz] required')
                    intervals = list(zip(vector(raw[0], 3, label), vector(raw[1], 3, label)))
                    if any(lo > hi for lo, hi in intervals): fail(label, 'inverted bounds')
                elif key == 'normal_constraints':
                    if not isinstance(raw, dict): fail(label, 'axis and max_angle_rad required')
                    _keys(raw, {'axis', 'max_angle_rad'}, label)
                    axis = unit_vector(raw.get('axis'), label)
                    angle = number(raw.get('max_angle_rad'), label)
                    if not 0 <= angle <= math.pi: fail(label, 'angle must be in [0,pi] rad')
                    if norm(sub(axis, values)) > 2*math.sin(angle/2)+1e-10:
                        fail(label, 'normal outside declared cone')
                    intervals = []
                else:
                    intervals = _bounds(raw, 2, label)
                if any(not lo <= v <= hi for v, (lo, hi) in zip(values, intervals)):
                    fail(label, 'nominal value outside declared bounds')
                checks.append({'path': label, 'status': 'Pass'})
            except InputIssue as exc:
                checks.append({'path': exc.path, 'status': exc.status, 'reason': exc.reason})
    status = 'Fail' if any(c['status'] == 'Fail' for c in checks) else (
        'Uncomputed' if any(c['status'] == 'Uncomputed' for c in checks) else 'Pass')
    return {'status': status, 'scope': 'declared nominal bounds only; no tolerance/yield', 'checks': checks}


def evaluate_external(document):
    """JSON-safe classified result with no unverified physical coupling number."""
    result = {key: {'status': 'Uncomputed'} for key in (
        'input_contract', 'geometry', 'model_domain', 'design_constraints',
        'gaussian_mode_matching', 'package_feasibility', 'physical_losses',
        'fabrication', 'actual_applicability')}
    result['physical_losses'].update(total_coupling=None, reason='interfaces/coatings/polarization/scatter not modeled')
    result['gaussian_mode_matching']['normalized_mode_overlap'] = None
    result['actual_applicability']['reason'] = 'external input adapter does not independently certify actual Port field or package performance'
    try:
        adapted = adapt_external(document)
    except InputIssue as exc:
        result['input_contract'] = {'status': exc.status, 'path': exc.path, 'reason': exc.reason}
        return result
    except (DomainError, TypeError, ValueError, OverflowError, ZeroDivisionError) as exc:
        result['input_contract'] = {'status': 'Fail', 'reason': str(exc)}
        return result
    result['input_snapshot'] = json.loads(adapted.input_json)
    result['uncertainty_treatment'] = 'metadata preserved; no uncertainty propagation or yield calculation'
    result['input_contract'] = {'status': 'Pass', 'scope': 'explicit nominal external Gaussian contract; field fit not certified'}
    for key, operation in (
        ('design_constraints', lambda: assess_constraints(document, adapted)),
        ('package_feasibility', lambda: assess_package(document, adapted, read, InputIssue))):
        try:
            result[key] = operation()
        except (InputIssue, ValueError, TypeError, OverflowError, ZeroDivisionError) as exc:
            result[key] = {'status': getattr(exc, 'status', 'Fail'), 'reason': str(exc)}
    engine = evaluate(adapted.source, adapted.target, adapted.reflectors)
    for key in ('geometry', 'model_domain', 'physical_losses', 'fabrication'):
        result[key] = engine[key]
    # Common-plane/basis/NA/footprint rejection stays with the frozen Engine.
    match = engine['gaussian_mode_matching']
    if match['status'] == 'Pass':
        blocked = [key for key in ('design_constraints', 'package_feasibility') if result[key]['status'] == 'Fail']
        if blocked:
            result['gaussian_mode_matching']['reason'] = 'withheld: '+', '.join(blocked)+' failed'
        else:
            result['gaussian_mode_matching'] = {**match, 'status': 'Approximate',
                'scope': 'normalized scalar paraxial Gaussian diagnostic; not total coupling',
                'conditions': ['explicit scalar-ignored polarization', 'finite-field aberration unvalidated',
                               'package/bounds status remains separate']}
    else:
        result['gaussian_mode_matching']['reason'] = 'optical Geometry/domain incomplete or failed'
    result['evaluated_ports'] = {
        name: {'position_m': port.position, 'direction': port.direction,
               'sagittal_axis': port.sagittal, 'complex_q_ts_m': [[q.real, q.imag] for q in port.mode.q],
               'wavelength_m': port.mode.wavelength, 'ambient_index': port.mode.index}
        for name, port in (('source', adapted.source), ('target', adapted.target))}
    result['samples'] = engine.get('samples', [])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = evaluate_external(json.loads(args.input.read_text()))
    except (ValueError, OSError) as exc:
        result = {'input_contract': {'status': 'Fail', 'reason': str(exc)}}
    text = json.dumps(result, indent=2, allow_nan=False)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end='')
    return int(any(result.get(key, {}).get('status') == 'Fail' for key in (
        'input_contract', 'geometry', 'model_domain', 'design_constraints', 'package_feasibility')))


if __name__ == '__main__':
    raise SystemExit(main())
