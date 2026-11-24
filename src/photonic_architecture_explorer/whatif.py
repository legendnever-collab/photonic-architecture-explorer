"""P4b Glass placement what-if: the smallest change of one assumed placement that gives candidates.

When a Glass (medium block) problem fails, the placements in the scenario are usually assumptions (block thickness,
waveguide depth, fibre height). Each one is changed alone, in growing steps, and the same continuous search
(coarser 32 × 32 grid, no non-paraxial check) is run until a candidate appears; one bisection step then narrows
the threshold. The answer is a sufficient change found by the search, not a proof that smaller changes fail
(the coarse grid can miss narrow feasible regions).
"""

import copy
import time
from dataclasses import replace

from .design_document import search_constraints, to_engine_problem
from .gaussian import DomainError

WHATIF_GRID = 32
STEPS = {'block_thickness': (1.25, 1.5, 2.0, 3.0), 'target_depth': (2.5, 5.0, 10.0, 20.0),
         'source_depth': (2.5, 5.0, 10.0, 20.0), 'source_height': (2.0, 4.0, 8.0, 16.0),
         'target_height': (2.0, 4.0, 8.0, 16.0)}
LABELS = {'block_thickness': 'Glass 두께', 'target_depth': 'Target(도파로) 매립 깊이', 'source_depth': 'Source 매립 깊이',
          'source_height': 'Source(Fiber)와 Glass 상면 거리', 'target_height': 'Target과 Glass 상면 거리'}


def _depth(document, name):
    block = document['medium_block']
    p, s, n = document['ports'][name]['position_mm'], block['surface_point_mm'], block['surface_normal']
    return -sum((a - b) * c for a, b, c in zip(p, s, n))  # mm below the surface


def _move(document, name, along, amount):
    port = document['ports'][name]
    port['position_mm'] = [p + a * amount for p, a in zip(port['position_mm'], along)]


def _apply(document, parameter, value):
    doc = copy.deepcopy(document)
    block = doc['medium_block']
    normal = block['surface_normal']
    if parameter == 'block_thickness':
        block['thickness_mm'] = value
    elif parameter in ('target_depth', 'source_depth'):
        name = parameter.split('_')[0]
        _move(doc, name, [-c for c in normal], value - _depth(document, name))  # deeper along −normal
    else:
        name = parameter.split('_')[0]
        _move(doc, name, normal, value + _depth(document, name))  # farther above the surface (depth is negative)
    return doc


def _feasible(document):
    problem = to_engine_problem(document)
    constraints = replace(search_constraints(document), block=problem['block'],
                          block_side='inside' if problem['medium'] == 'block' else 'outside')
    from .search import design_continuous
    report = design_continuous(problem['engine'], constraints, include_map=False, nonparaxial_checks=False,
                               grid_points=WHATIF_GRID)
    count = len(report['candidates'])
    family = report['candidates'][0].get('family') if count else None
    return count > 0, count, family, report.get('reason')


def parameters(document):
    block = document.get('medium_block')
    out = []
    if block and block.get('thickness_mm'):
        out.append(('block_thickness', block['thickness_mm']))
    for name in ('source', 'target'):
        depth = _depth(document, name)
        if document['ports'][name].get('medium', 'ambient') == 'block':
            out.append((f'{name}_depth', depth))
        else:
            out.append((f'{name}_height', -depth))
    return out


def study(document, budget_seconds=90.0):
    if not document.get('medium_block'):
        return None
    started = time.perf_counter()
    rows = []
    for parameter, original in parameters(document):
        row = {'parameter': parameter, 'label': LABELS[parameter], 'original_mm': original, 'found_mm': None,
               'tried_mm': [], 'candidates': 0, 'family': None, 'status': 'Not found'}
        if original <= 0:
            row['status'] = 'Skipped'
            rows.append(row)
            continue
        previous = original
        for factor in STEPS[parameter]:
            if time.perf_counter() - started > budget_seconds:
                row['status'] = 'Time limit'
                break
            value = original * factor
            if parameter.endswith('_depth') and document['medium_block'].get('thickness_mm'):
                value = min(value, document['medium_block']['thickness_mm'] * 0.9)
                if value <= previous:
                    break
            try:
                ok, count, family, _ = _feasible(_apply(document, parameter, value))
            except DomainError as exc:
                row['tried_mm'].append({'value_mm': value, 'result': str(exc)})
                previous = value
                continue
            row['tried_mm'].append({'value_mm': value, 'result': f'{count} candidates' if ok else 'Fail'})
            if ok:
                middle = (previous + value) / 2  # one bisection between the last failure and the first success
                try:
                    ok_mid, count_mid, family_mid, _ = _feasible(_apply(document, parameter, middle))
                except DomainError:
                    ok_mid = False
                row['tried_mm'].append({'value_mm': middle, 'result': f'{count_mid} candidates' if ok_mid else 'Fail'})
                if ok_mid:
                    value, count, family = middle, count_mid, family_mid
                row.update(found_mm=value, candidates=count, family=family, status='Found')
                break
            previous = value
        rows.append(row)
    return {'grid': WHATIF_GRID, 'rows': rows, 'elapsed_seconds': round(time.perf_counter() - started, 1),
            'meaning': ('한 번에 가정 배치 하나만 바꿔, 같은 연속 탐색(32 × 32 격자, 비근축 검산 없음)으로 후보가 처음 나오는 값을 찾았습니다. '
                        '충분 조건이지 최소값의 증명은 아닙니다. 실제 Design으로 다시 확인하세요.')}
