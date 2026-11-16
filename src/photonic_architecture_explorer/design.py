"""Bounded two-Port exact Gaussian matching; no generic topology/optimization engine."""
import argparse
import copy
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path

from .external import adapt_ports, evaluate_external, InputIssue, fail
from .gaussian import DomainError
from .geometry import add, sub, mul, dot, norm, unit
from .solver import MAX_DIVERGENCE, MIN_COSINE

POLICY = {
    'id': 'M5A-BOUNDED-EXACT-1', 'distance_fractions': [0.125, 0.25, 0.5, 1., 2.],
    'geometry_limit': 64, 'candidate_limit': 256, 'representatives': 3,
    'aperture_projected_radius_factor': 4., 'dedup_relative_decimals': 12,
    'termination': 'exhaust frozen finite family; never expand or optimize Target',
}
RANKING = ['overlap_deficit_at_1e-12', 'max_3w_footprint_curvature',
           'negative_min_aperture_radius_ratio_at_1e-12', 'max_projected_radius_m',
           'total_path_m', 'package_evidence_missing_checks', 'stable_id']
LIMITS = ['Conceptual Geometry; prescribed aperture is not fabrication capability',
          'Scalar paraxial normalized overlap is not Total Coupling',
          'Finite-field aberration, coating, interface and polarization losses Uncomputed',
          'Full Package, fabrication/yield and patentability Uncomputed',
          'Bounded exact-matching family; no global feasibility/optimality guarantee']


def record(value, unit_name):
    return {'value': value, 'unit': unit_name, 'provenance': 'assumed',
            'source': 'M5A autonomous concept prescription; not a measured device fact', 'uncertainty': None}


def power_pairs(qsource, qtarget, a, b, c):
    """All real two-power exact-q solutions for one axis; at most two."""
    if min(a,b,c) < 1e-9:
        raise DomainError('zero/short segment in power design')
    qa, qb = qsource+a, qtarget-c
    u, v = 1/qa, 1/qb
    discriminant = u.imag/v.imag-(b*u.imag)**2
    if discriminant < 0:
        return []  # Do not force a negative discriminant to zero.
    solutions = []
    for sign in (1., -1.):
        p1 = u.real+(1-sign*math.sqrt(discriminant))/b
        before_second = 1/(u-p1)+b
        p2 = (1/before_second).real-v.real
        if not all(math.isfinite(x) for x in (p1,p2)):
            raise DomainError('nonfinite power solution')
        if (p1,p2) not in solutions:
            solutions.append((p1,p2))
    return solutions


def distances(source, target):
    delta = sub(target.position, source.position)
    scale = norm(delta)
    if scale < 1e-9:
        raise DomainError('coincident/near-coincident Ports outside bounded family')
    raw = [scale*f for f in POLICY['distance_fractions']]
    raw += [abs(dot(delta,p.direction))/2 for p in (source,target)]
    raw += [norm(sub(delta,mul(source.direction,dot(delta,source.direction))))/2]
    unique = {}
    for value in sorted(raw):
        if value >= 1e-9:
            unique.setdefault(round(value/scale,12),value)
    return scale, list(unique.values())


def candidate_document(document, ports, vertices, normals, lengths, curvatures):
    """Generated concept surfaces; Package is copied only if actually supplied."""
    out = copy.deepcopy(document)
    out['design'] = {'reflectors': []}
    out['reflectors'] = []
    beam = ports.source.mode
    for j in range(2):
        cosine = -dot((ports.source.direction if j==0 else unit(sub(vertices[1],vertices[0]))),normals[j])
        beam = beam.propagate(lengths[j])
        pars = beam.parameters()
        radii = (pars[0]['radius_m']/cosine, pars[1]['radius_m'])
        out['design']['reflectors'].append({
            'vertex_m':record(vertices[j],'m'), 'illuminated_normal':record(normals[j],'1'),
            'principal_curvature_ts_per_m':record(curvatures[j],'m^-1'),
            'half_aperture_ts_m':record([POLICY['aperture_projected_radius_factor']*r for r in radii],'m')})
        out['reflectors'].append({'surface_prescription':record('quadratic_patch','model')})
        kt,ks = curvatures[j]
        beam = beam.power((2*kt/cosine,2*ks*cosine))
    return out


def prescriptions(document, ports, ledger):
    """Deterministic bounded family; ledger records geometry/power rejection too."""
    source, target = ports.source, ports.target
    scale, values = distances(source,target)
    seen = set()
    for geometry_index,(a,c) in enumerate(itertools.product(values,repeat=2),1):
        vertices = (add(source.position,mul(source.direction,a)), sub(target.position,mul(target.direction,c)))
        prefix = f'G{geometry_index:03d}'
        try:
            b = norm(sub(vertices[1],vertices[0]))
            if b < 1e-9: raise DomainError('zero/short middle segment')
            mid = unit(sub(vertices[1],vertices[0]))
            normals = (unit(sub(mid,source.direction)),unit(sub(target.direction,mid)))
            cosines = (-dot(source.direction,normals[0]),-dot(mid,normals[1]))
            if min(cosines) < MIN_COSINE: raise DomainError('incidence exceeds 70 degrees')
            axes = [power_pairs(qs,qt,a,b,c) for qs,qt in zip(source.mode.q,target.mode.q)]
            if not all(axes): raise DomainError('no real exact-q power solution for one or both axes')
            for branch,(t,s) in enumerate(itertools.product(*axes),1):
                identifier = f'{prefix}-B{branch}'
                curvatures = ((t[0]*cosines[0]/2,s[0]/(2*cosines[0])),
                              (t[1]*cosines[1]/2,s[1]/(2*cosines[1])))
                key = (round(a/scale,12),round(c/scale,12),
                       *(round(k*scale,12) for pair in curvatures for k in pair))
                if key in seen:
                    ledger.append({'id':identifier,'status':'Duplicate'});continue
                seen.add(key)
                try:
                    generated = candidate_document(document,ports,vertices,normals,(a,b,c),curvatures)
                except (DomainError,ArithmeticError) as exc:
                    ledger.append({'id':identifier,'status':'Rejected','stage':'power_design','reason':str(exc)})
                    continue
                yield identifier, prefix, generated
        except (DomainError,ArithmeticError) as exc:
            ledger.append({'id':prefix,'status':'Rejected','stage':'geometry_or_power','reason':str(exc)})


def ranking(evaluation, document, identifier):
    overlap = evaluation['gaussian_mode_matching']['normalized_mode_overlap']
    before = [s for s in evaluation['samples'] if 'surface_radii_m' in s]
    ratios = [a/r for sample,mirror in zip(before,document['design']['reflectors'])
              for a,r in zip(mirror['half_aperture_ts_m']['value'],sample['surface_radii_m'])]
    metrics = {'overlap_deficit_at_1e-12':round(1-overlap,12),
               'max_3w_footprint_curvature':max(s['footprint_slope_3w'] for s in before),
               'negative_min_aperture_radius_ratio_at_1e-12':-round(min(ratios),12),
               'max_projected_radius_m':max(r for s in before for r in s['surface_radii_m']),
               'total_path_m':sum(evaluation['geometry']['lengths']),
               'package_evidence_missing_checks':sum(c['status']!='Pass' for c in
                   evaluation['package_feasibility'].get('envelope_geometry',{}).get('checks',[])),
               'stable_id':identifier}
    return metrics


def design_two_ports(document):
    """Two fixed optical ports in; up to 3 independently Engine-checked concepts out."""
    result = {'schema':'M5A-design-result-1','status':'Uncomputed','input_snapshot':None,
              'input_contract':{'status':'Uncomputed'}, 'search_policy':copy.deepcopy(POLICY),
              'ranking_order':RANKING, 'candidates':[], 'selected_candidate_id':None,
              'search':{'status':'Uncomputed','attempts':[]}, 'limitations':LIMITS,
              'actual_applicability':{'status':'Uncomputed'},
              'physical_losses':{'status':'Uncomputed','total_coupling':None},
              'package_feasibility':{'status':'Uncomputed'},
              'fabrication_yield':{'status':'Uncomputed'},'patentability':{'status':'Uncomputed'}}
    try:
        snapshot = json.dumps(document,sort_keys=True,allow_nan=False)
        result['input_snapshot'] = json.loads(snapshot)
        result['input_sha256'] = hashlib.sha256(snapshot.encode()).hexdigest()
        if not isinstance(document,dict): fail('input','two-Port object required')
        if any(k in document for k in ('design','reflectors')):
            fail('input','Design takes two Ports and optional Package, not manual reflector prescriptions')
        ports = adapt_ports(document)
        result['input_contract'] = {'status':'Pass','scope':'explicit two-Port subset of M3A contract'}
        source,target = ports.source,ports.target
        if norm(sub(source.sagittal,target.sagittal)) > 1e-10:
            raise DomainError('rolled Target axes unsupported')
        if abs(dot(source.sagittal,target.direction))>1e-10:
            raise DomainError('noncoplanar Target direction')
        scale, values = distances(source,target)
        if abs(dot(source.sagittal,sub(target.position,source.position)))/scale>1e-10:
            raise DomainError('noncoplanar Port positions')
        if any(p['divergence_rad']>MAX_DIVERGENCE for port in (source,target) for p in port.mode.parameters()):
            raise DomainError('Gaussian divergence exceeds 0.1 rad')
        result['search']['distance_values_m'] = values
        accepted = []
        ledger = result['search']['attempts']
        for identifier,geometry_id,generated in prescriptions(document,ports,ledger):
            evaluation = evaluate_external(generated)
            bad = [k for k in ('input_contract','geometry','model_domain') if evaluation[k]['status']!='Pass']
            bad += [k for k in ('design_constraints','package_feasibility') if evaluation[k]['status']=='Fail']
            overlap = evaluation['gaussian_mode_matching'].get('normalized_mode_overlap')
            if bad or overlap is None:
                stage = bad[0] if bad else 'gaussian_mode_matching'
                reason = evaluation[stage].get('reason','incomplete or failed evaluation')
                ledger.append({'id':identifier,'status':'Rejected','stage':stage,'reason':reason,
                               'normalized_mode_overlap':None})
                continue
            metrics = ranking(evaluation,generated,identifier)
            ledger.append({'id':identifier,'geometry_id':geometry_id,'status':'Accepted',
                           'segment_lengths_m':evaluation['geometry']['lengths'], 'ranking':metrics})
            accepted.append({'id':identifier,'geometry_id':geometry_id,'classification':'Conceptual Geometry',
                             'prescription':generated,'evaluation':evaluation,'ranking':metrics,
                             'advantages':['Fixed Port closure and frozen domain guards passed',
                                           'Two-axis exact-q design, checked by existing manual Adapter'],
                             'limitations':LIMITS})
        accepted.sort(key=lambda c:tuple(c['ranking'][k] for k in RANKING))
        # Diversify vertices, preserving the lexicographic order among geometry winners.
        chosen=[];geometries=set()
        for candidate in accepted:
            if candidate['geometry_id'] in geometries: continue
            chosen.append(candidate);geometries.add(candidate['geometry_id'])
            if len(chosen)==POLICY['representatives']:break
        result['candidates'] = chosen
        result['selected_candidate_id'] = chosen[0]['id'] if chosen else None
        result['status'] = 'Computed' if chosen else 'Fail'
        result['search'].update(status='Completed', accepted_count=len(accepted),
            representatives=len(chosen), geometry_count=len(values)**2,
            rejection_counts=dict(sorted(Counter(a.get('stage','')+': '+a.get('reason','')
                for a in ledger if a['status']=='Rejected').items())),
            termination='Frozen finite family exhausted',
            selection='best lexicographic candidate per distinct vertex geometry; first 3')
        result['reason'] = ('Valid conceptual candidates generated' if chosen else
                            'No valid candidate in bounded exact-q family; not proof of physical impossibility')
    except InputIssue as exc:
        result['status'] = exc.status
        result['input_contract'] = {'status':exc.status,'path':exc.path,'reason':exc.reason}
        result['reason'] = str(exc)
    except (DomainError,TypeError,ValueError,ArithmeticError) as exc:
        result['status'] = 'Fail'
        result['reason'] = str(exc)
        if result['input_contract']['status']!='Pass':
            result['input_contract'] = {'status':'Fail','reason':str(exc)}
        else:
            result['search'] = {**result['search'],'status':'Not started','reason':str(exc)}
    # Always JSON-safe, and no mutable object shared with caller or kernel tuples.
    return json.loads(json.dumps(result,allow_nan=False))


def main():
    parser=argparse.ArgumentParser(description='Design from two fixed Ports; no mirror or solver settings')
    parser.add_argument('input',type=Path)
    parser.add_argument('--output-dir',type=Path,default=Path('results/m5a'))
    args=parser.parse_args()
    try:
        document=json.loads(args.input.read_text())
        result=design_two_ports(document)
    except (OSError, ValueError) as exc:
        result=design_two_ports(None)
        result['reason']=f'Cannot read two-Port JSON: {exc}'
        result['input_contract']={'status':'Fail','path':str(args.input),'reason':result['reason']}
    from .design_report import render_design_report
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'design.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    (args.output_dir/'design.html').write_text(render_design_report(result),encoding='utf-8')
    print(json.dumps({'status':result['status'],'selected':result['selected_candidate_id'],
                      'candidates':len(result['candidates']),'reason':result['reason']},ensure_ascii=False))
    return 0 if result['status']=='Computed' else 1


if __name__=='__main__':
    raise SystemExit(main())
