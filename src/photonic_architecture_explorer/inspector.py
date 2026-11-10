"""Minimal Python Inspector: existing Adapter evaluation, HTML/SVG presentation."""

import argparse
import copy
import hashlib
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit

from .external import adapt_external, evaluate_external, read, InputIssue
from .geometry import cross, dot, unit

ROOT = Path(__file__).resolve().parents[2]
PROJECTIONS = {'XZ': (0, 2, 'Y'), 'XY': (0, 1, 'Z'), 'YZ': (1, 2, 'X')}


def review_cases(root=ROOT):
    """Fixed synthetic review controls; no search or automatic design changes."""
    nominal = json.loads((root/'examples/m3a_synthetic.json').read_text())
    blank = json.loads((root/'examples/external_ports_unprovided.json').read_text())
    cases = [('nominal', 'Synthetic Relay', nominal), ('blank', 'Actual Ports · 미제공', blank)]
    for key, title in (
        ('missing-phase', 'Missing Phase'), ('bad-unit', '잘못된 단위'),
        ('target-direction', '잘못된 Target Direction'), ('high-divergence', 'High Divergence'),
        ('bounds-fail', 'Bounds Fail'), ('package-fail', 'Package Fail')):
        data = copy.deepcopy(nominal)
        if key == 'missing-phase':
            del data['source']['wavefront_curvature_ts_per_m']; del data['source']['complex_q_ts_m']
        elif key == 'bad-unit': data['source']['position_m']['unit'] = 'mm'
        elif key == 'target-direction':
            data['target']['propagation_direction']['value'] = [-1, 0, 0]
            data['target']['reference_plane']['value']['normal'] = [-1, 0, 0]
        elif key == 'high-divergence':
            del data['source']['complex_q_ts_m']; data['source']['mfd_ts_m']['value'] = [2e-6, 2e-6]
        elif key == 'bounds-fail':
            data['reflectors'][0]['principal_curvature_bounds_per_m']['value'] = [[0, 1], [0, 1]]
        elif key == 'package-fail':
            data['package']['available_volume']['value'] = {
                'type': 'aabb', 'min_m': [-.0001, -.0001, -.0001], 'max_m': [.0021, .0001, .0021]}
        cases.append((key, title, data))
    return cases


def groups(document):
    if not isinstance(document, dict): return {'ports': document, 'reflectors': {}, 'package': {}}
    return {'ports': {k: v for k, v in document.items() if k not in ('design', 'reflectors', 'package')},
            'reflectors': {k: document[k] for k in ('design', 'reflectors') if k in document},
            'package': {'package': document['package']} if 'package' in document else {}}


def parse_groups(raw):
    if set(raw) != {'ports', 'reflectors', 'package'}: raise ValueError('세 입력 그룹이 필요합니다.')
    document = {}
    def invalid_constant(value): raise ValueError(f'Nonfinite JSON value: {value}')
    for name in ('ports', 'reflectors', 'package'):
        group = json.loads(raw[name], parse_constant=invalid_constant)
        # Exponent notation can overflow without using NaN/Infinity tokens.
        json.dumps(group, allow_nan=False)
        if not isinstance(group, dict): raise ValueError(f'{name}: JSON object가 필요합니다.')
        if document.keys() & group.keys(): raise ValueError('입력 그룹 사이에 중복된 Field가 있습니다.')
        document.update(group)
    return document


def evaluate_view(document, error=None):
    """One fresh Adapter evaluation; no persisted previous result or fitted Port."""
    result = evaluate_external(document if error is None else {})
    if error is not None:
        result['input_contract'] = {'status': 'Fail', 'path': 'JSON editor', 'reason': str(error)}
    adapted = None
    if result['input_contract']['status'] == 'Pass': adapted = adapt_external(document)
    return result, adapted


def surface_lines(mirror, sagittal):
    """Display samples of the SAME quadratic patch; no spherical substitution."""
    tangent = unit(cross(sagittal, mirror.normal))
    at, ass = mirror.half_aperture
    def point(u, v):
        sag = (mirror.curvatures[0]*u*u+mirror.curvatures[1]*v*v)/2
        return tuple(mirror.vertex[i]+tangent[i]*u+sagittal[i]*v+mirror.normal[i]*sag for i in range(3))
    lines = [[point(-at+2*at*j/24, v) for j in range(25)] for v in (-ass, 0., ass)]
    lines += [[point(u, -ass+2*ass*j/24) for j in range(25)] for u in (-at, 0., at)]
    return lines


def declared_boxes(document, adapted):
    """Display only supported, finite, correctly unit-tagged common-frame AABBs."""
    package = document.get('package')
    try:
        if read(package, 'frame_id', 'frame', 'package') != adapted.frame_id: return []
    except (InputIssue, TypeError, ValueError): return []
    boxes = []
    def add_box(value, label, kind):
        if not isinstance(value, dict) or value.get('type') != 'aabb': return
        if set(value)-{'type', 'min_m', 'max_m', 'frame_id'}: return
        if value.get('frame_id', adapted.frame_id) != adapted.frame_id: return
        lo, hi = value.get('min_m'), value.get('max_m')
        if not all(isinstance(v, list) and len(v) == 3 for v in (lo, hi)): return
        try:
            if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in lo+hi): return
        except OverflowError: return
        if any(a >= b for a, b in zip(lo, hi)): return
        boxes.append((label, kind, lo, hi))
    records = [(package, 'available_volume', 'volume', 'Package Volume', 'volume')]
    records += [(node, 'body_envelope', 'body', f'M{j+1} Envelope', 'body') for j, node in enumerate(document['reflectors'])]
    for node, key, unit_kind, label, kind in records:
        try: add_box(read(node, key, unit_kind, label), label, kind)
        except (InputIssue, TypeError, ValueError): pass
    try:
        values = read(package, 'keepout_bodies', 'keepouts', 'package')
        if isinstance(values, list):
            for j, value in enumerate(values): add_box(value, f'Keepout {j+1}', 'keepout')
    except (InputIssue, TypeError, ValueError): pass
    return boxes


def plot_svg(document, result, adapted, projection, seed):
    if adapted is None:
        return '<div class="empty-plot">Geometry 표시 보류<br><small>Input Contract를 먼저 확인하세요. 잘못된 단위를 좌표로 그리지 않습니다.</small></div>'
    a, b, omitted = PROJECTIONS[projection]
    ports = [('Source', adapted.source), ('Target', adapted.target)]
    surfaces = [surface_lines(m, adapted.source.sagittal)
                if abs(dot(adapted.source.sagittal, m.normal)) <= 1e-10 else []
                for m in adapted.reflectors]
    boxes = declared_boxes(document, adapted)
    points = [p.position for _, p in ports]+[point for lines in surfaces for line in lines for point in line]
    points += [v for _, _, lo, hi in boxes for v in (lo, hi)]
    xs, ys = [p[a]*1000 for p in points], [p[b]*1000 for p in points]
    xlo, xhi, ylo, yhi = min(xs), max(xs), min(ys), max(ys)
    span = max(xhi-xlo, yhi-ylo, .001)
    cx, cy = (xlo+xhi)/2, (ylo+yhi)/2
    # Equal mm-to-screen scale, including degenerate projections.
    sx, sy = max(xhi-xlo, span*.25)*1.25, max(yhi-ylo, span*.25)*1.25
    scale = min(620/sx, 380/sy)
    def xy(p): return (360+(p[a]*1000-cx)*scale, 250-(p[b]*1000-cy)*scale)
    def pairs(line): return ' '.join(f'{x:.5f},{y:.5f}' for x, y in map(xy, line))
    out = [f'<svg viewBox="0 0 720 510" role="img" aria-label="{projection} geometry projection [mm]" data-scale="equal">',
           f'<defs><marker id="{seed}-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7" fill="context-stroke"/></marker></defs>']
    for j in range(6):
        x, y = xlo+(xhi-xlo)*j/5, ylo+(yhi-ylo)*j/5
        px, py = 360+(x-cx)*scale, 250-(y-cy)*scale
        out += [f'<line x1="{px}" y1="50" x2="{px}" y2="450" class="grid"/>',
                f'<line x1="50" y1="{py}" x2="670" y2="{py}" class="grid"/>',
                f'<text x="{px}" y="474" text-anchor="middle" class="tick">{x:.3g}</text>',
                f'<text x="45" y="{py+4}" text-anchor="end" class="tick">{y:.3g}</text>']
    out += [f'<text x="658" y="498" class="axis">{projection[0]} [mm]</text>',
            f'<text x="18" y="30" class="axis">{projection[1]} [mm]</text>']
    for label, kind, lo, hi in boxes:
        x1, y1 = xy(lo); x2, y2 = xy(hi)
        out.append(f'<rect x="{min(x1,x2)}" y="{min(y1,y2)}" width="{abs(x2-x1)}" height="{abs(y2-y1)}" class="box {kind}" data-kind="{kind}"><title>{escape(label)}</title></rect>')
    if result['geometry']['status'] == 'Pass':
        path = [adapted.source.position, *(m.vertex for m in adapted.reflectors), adapted.target.position]
        out.append(f'<polyline points="{pairs(path)}" class="chief" data-kind="verified-chief" marker-end="url(#{seed}-arrow)"/>')
    for j, lines in enumerate(surfaces):
        for line in lines:
            out.append(f'<polyline points="{pairs(line)}" class="surface" data-kind="quadratic-surface"/>')
        x, y = xy(adapted.reflectors[j].vertex)
        suffix = '' if lines else ' · surface orientation unsupported'
        out.append(f'<text x="{x+9}" y="{y-10}" class="mirror-label">M{j+1}{suffix}</text>')
    for label, port in ports:
        x, y = xy(port.position)
        end = tuple(port.position[i]+port.direction[i]*span*.00012 for i in range(3))
        ex, ey = xy(end)
        color = '#176d92' if label == 'Source' else '#704b9d'
        out.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{color}" data-kind="fixed-port"/>')
        if math.hypot(ex-x, ey-y) > .001:
            out.append(f'<line x1="{x}" y1="{y}" x2="{ex}" y2="{ey}" stroke="{color}" stroke-width="2.5" marker-end="url(#{seed}-arrow)"/>')
        else:
            out.append(f'<text x="{x+10}" y="{y+28}" class="tick">axis along {omitted}</text>')
        out.append(f'<text x="{x+10}" y="{y+16}" class="port-label">{label}</text>')
    out.append('</svg>')
    return ''.join(out)


def badge(status): return f'<span class="badge {escape(status.lower())}">{escape(status)}</span>'


def visible_overlap(result):
    value = result['gaussian_mode_matching'].get('normalized_mode_overlap')
    valid = (result['gaussian_mode_matching']['status'] == 'Approximate'
             and result['geometry']['status'] == 'Pass' and result['model_domain']['status'] == 'Pass'
             and all(result[key]['status'] != 'Fail' for key in ('input_contract', 'design_constraints', 'package_feasibility')))
    return value if valid and isinstance(value, (int, float)) and math.isfinite(value) and 0 <= value <= 1 else None


def result_panel(result):
    eta = visible_overlap(result)
    metric = f'<strong data-overlap-value="{eta}">{eta:.8g}</strong>' if eta is not None else '<strong data-overlap-withheld>—</strong>'
    rows = []
    for label, key in (
        ('Input Contract', 'input_contract'), ('Chief-Ray Geometry', 'geometry'), ('Gaussian Domain', 'model_domain'),
        ('Design Bounds', 'design_constraints'), ('Normalized Mode Overlap', 'gaussian_mode_matching'),
        ('Envelope Geometry', 'envelope_geometry'), ('Full Package Feasibility', 'package_feasibility'),
        ('Physical Losses / Total Coupling', 'physical_losses'), ('Fabrication / Assembly', 'fabrication'),
        ('Actual Applicability', 'actual_applicability')):
        entry = result['package_feasibility'].get('envelope_geometry', {'status': 'Uncomputed'}) if key == 'envelope_geometry' else result[key]
        rows.append(f'<tr data-result="{key}"><td>{label}</td><td>{badge(entry["status"])}</td></tr>')
    issues = []
    for key, value in result.items():
        if isinstance(value, dict) and value.get('status') in ('Fail', 'Uncomputed') and value.get('reason'):
            issues.append(f'<li><b>{escape(key)}</b>: {escape(value["reason"])}</li>')
    for key in ('design_constraints', 'package_feasibility'):
        group = result[key].get('envelope_geometry', result[key])
        issues += [f'<li>{escape(c.get("path", ""))}: {escape(c.get("reason", ""))}</li>' for c in group.get('checks', []) if c['status'] == 'Fail']
    raw = escape(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return f'''<div class="results"><div class="metric"><span>η_mode · Approximate scalar diagnostic</span>{metric}<small>Total Coupling: Uncomputed · 실제 제품 효율이 아닙니다.</small></div>
    <table class="states"><tbody>{''.join(rows)}</tbody></table>
    <details><summary>판정 근거 / 미계산 항목</summary><ul>{''.join(issues)}</ul></details>
    <details><summary>Adapter Result JSON · 기존 Samples 포함</summary><pre>{raw}</pre></details></div>'''


def input_summary(document):
    document = document if isinstance(document, dict) else {}
    rows = []
    for label in ('source', 'target'):
        node = document.get(label, {})
        node = node if isinstance(node, dict) else {}
        for field in ('position_m', 'propagation_direction', 'mfd_ts_m'):
            record = node.get(field, {})
            record = record if isinstance(record, dict) else {}
            value = 'Unprovided' if record.get('value') is None else json.dumps(record['value'], ensure_ascii=False)
            rows.append(f'<tr><td>{label.title()} · {field}</td><td>{escape(value)}</td><td>{escape(str(record.get("unit", "—")))}</td></tr>')
    return '<table class="input-summary"><tbody>'+''.join(rows)+'</tbody></table>'


CSS = '''
:root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#263747;background:#f3f6f8;font-size:14px}*{box-sizing:border-box}body{margin:0}header{background:#142b3d;color:white;padding:22px max(20px,calc((100vw - 1400px)/2));}header p{color:#c6d5df;margin:6px 0 0}h1{font-size:23px;margin:0}h2{font-size:18px;margin:0 0 12px}h3{font-size:14px;margin:0 0 6px}.wrap{max-width:1400px;margin:auto;padding:20px}.toolbar{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:16px}.toolbar label{display:flex;gap:8px;align-items:center}select,button{font:inherit;padding:9px 12px;border:1px solid #b7c5cf;border-radius:5px;background:white;color:#203849}button{background:#176d92;color:white;border-color:#176d92;cursor:pointer}a{color:#176d92}article[hidden],[hidden]{display:none!important}.layout{display:grid;grid-template-columns:minmax(0,1.65fr) minmax(320px,1fr);gap:18px;align-items:start}.card{background:white;border:1px solid #d6e0e7;border-radius:8px;padding:18px;min-width:0}.drawing{position:sticky;top:16px}.muted,small{color:#617789}.notice{background:#eaf2f6;border-left:3px solid #176d92;padding:11px 14px;line-height:1.6;margin:12px 0}.caption{font-size:12px;color:#506b7b}.projection svg{display:block;width:100%;height:auto}.grid{stroke:#e6edf1;stroke-width:1}.tick{font-size:11px;fill:#657b8b}.axis{font-size:12px;fill:#324f64}.box{stroke-width:1.1}.volume{fill:#f0f5f8;stroke:#9bb1c1;stroke-dasharray:6 4}.body{fill:#e8e1d7;fill-opacity:.5;stroke:#ad997d}.keepout{fill:#edc6c6;fill-opacity:.5;stroke:#b34545}.surface{fill:none;stroke:#bd762e;stroke-width:1.8;stroke-linejoin:round}.chief{fill:none;stroke:#176d92;stroke-width:2.5}.port-label{font-size:12px;font-weight:650;fill:#203d52}.mirror-label{font-size:13px;font-weight:650;fill:#9c5b1d}.legend{display:flex;flex-wrap:wrap;gap:12px;font-size:12px;color:#4b6576}.legend b{font-size:18px}.metric{background:#f4f8fa;border-radius:6px;padding:14px;margin-bottom:14px;display:flex;flex-direction:column;gap:5px}.metric strong{font-size:30px;color:#193f57}.metric span{font-size:12px;color:#576f7d}table{border-collapse:collapse;width:100%;font-size:12px}td{border-bottom:1px solid #e5ecf0;padding:9px 3px;vertical-align:top}.states td:last-child{text-align:right}.input-summary td{overflow-wrap:anywhere}.input-summary td:first-child{color:#617789}summary{cursor:pointer;color:#2f596e;padding:12px 0;font-weight:600}pre,textarea{font-family:ui-monospace,monospace;font-size:11px;white-space:pre-wrap;overflow-wrap:anywhere}pre{max-height:350px;overflow:auto;background:#f5f7f9;padding:12px}textarea{width:100%;height:280px;padding:12px;border:1px solid #bcccd6;border-radius:4px;resize:vertical;background:#fbfcfd}.badge{font-size:11px;font-weight:600;padding:4px 7px;border-radius:4px;display:inline-block}.pass{background:#e7f4ed;color:#236848}.fail{background:#fbe7e7;color:#a52f35}.approximate{background:#e7f1fa;color:#216694}.uncomputed{background:#fff2d9;color:#916618}.empty-plot{min-height:360px;display:grid;place-content:center;text-align:center;line-height:2;color:#667e8e}.dirty-note{background:#fff2d9;padding:16px;border:1px solid #e2c381}li{font-size:12px;margin:7px 0;overflow-wrap:anywhere}.editors{margin-top:16px}.digest{font-size:11px;overflow-wrap:anywhere}.review{line-height:1.8;font-size:13px}.form-note{margin:10px 0;color:#5d7381;font-size:12px}@media(max-width:850px){.layout{grid-template-columns:1fr}.drawing{position:static}.wrap{padding:12px}.card{padding:14px}h1{font-size:19px}.toolbar label{width:100%;justify-content:space-between}.toolbar select{max-width:68%}.empty-plot{min-height:220px}}@media print{header{color:#203849;background:white}.toolbar,.editors{display:none}.layout{display:block}.drawing{position:static}.card{break-inside:avoid}}
'''

JS = '''
const caseSelect=document.querySelector('#case-select');
const projectionSelect=document.querySelector('#projection-select');
function showViews(){
 document.querySelectorAll('article[data-case]').forEach(a=>a.hidden=a.dataset.case!==caseSelect.value);
 document.querySelectorAll('[data-projection]').forEach(v=>v.hidden=v.dataset.projection!==projectionSelect.value);
}
caseSelect.addEventListener('change',showViews);projectionSelect.addEventListener('change',showViews);
document.querySelectorAll('textarea:not([readonly])').forEach(t=>t.addEventListener('input',()=>{
 const a=t.closest('article');a.querySelectorAll('.results,.projection-group,[data-evaluated]').forEach(r=>r.hidden=true);
 a.querySelector('.dirty-note').hidden=false;
}));showViews();
'''


def render_report(cases, editable=False, raw_groups=None, error=None):
    """Render fresh results; JS only selects precomputed views or hides dirty ones."""
    articles, options = [], []
    for index, (key, title, document) in enumerate(cases):
        key = re.sub('[^a-zA-Z0-9_-]', '-', key)
        result, adapted = evaluate_view(document, error)
        options.append(f'<option value="{key}">{escape(title)}</option>')
        plots = []
        for projection, (_, _, omitted) in PROJECTIONS.items():
            plots.append(f'<div class="projection" data-projection="{projection}"'+(' hidden' if projection != 'XZ' else '')+f'><h3>{projection} Projection · 생략 축 {omitted} · mm · Equal Scale</h3>'+plot_svg(document, result, adapted, projection, key+'-'+projection)+'</div>')
        split = raw_groups or {k: json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False) for k, v in groups(document).items()}
        editor_parts = []
        for name, label in (('ports', 'Fixed Optical Ports · Boundary Conditions'), ('reflectors', 'Reflector Design Variables · Nominal / Bounds / Envelopes'), ('package', 'Package Geometry')):
            editor_parts.append(f'<details><summary>{label}</summary><textarea name="{name}" aria-label="{label}" spellcheck="false"'+('' if editable else ' readonly')+'>'+escape(split[name])+'</textarea></details>')
        digest = hashlib.sha256(json.dumps(document, sort_keys=True, allow_nan=False).encode()).hexdigest() if error is None else 'JSON syntax error · no evaluated input'
        input_action = '<button type="submit">Adapter로 재평가</button>' if editable else '<p class="form-note">정적 Snapshot · 수정·재평가는 Python Local Inspector에서 실행합니다.</p>'
        path_note = 'Verified chief path' if result['geometry']['status'] == 'Pass' else 'Chief path 표시 보류 · Geometry '+result['geometry']['status']
        articles.append(f'''<article data-case="{key}"{' hidden' if index else ''}><div class="layout">
        <section class="card drawing"><h2>{escape(title)}</h2><p class="caption" data-evaluated>{escape(path_note)}</p><div class="projection-group">{''.join(plots)}</div>
        <div class="dirty-note" hidden>입력이 변경되었습니다. 재평가 전에는 이전 결과와 Geometry를 표시하지 않습니다.</div>
        <div class="legend"><span><b style="color:#176d92">●</b> Source / Chief Ray</span><span><b style="color:#704b9d">●</b> Fixed Target</span><span><b style="color:#bd762e">—</b> Quadratic Surfaces</span><span>▧ Declared AABBs</span></div>
        <p class="notice">2D Projection의 중첩은 3D 충돌 판정이 아닙니다. Port 화살표 길이는 표시용입니다. Beam Envelope는 표시하지 않습니다.</p>
        <details data-evaluated><summary>Fixed Port 입력 요약 · SI Units</summary>{input_summary(document)}</details>
        <p class="digest" data-evaluated>Input SHA256: {escape(digest)}</p></section>
        <section class="card"><h2>모델 결과와 적용 범위</h2>{result_panel(result)}
        <form class="editors" method="post" action="/evaluate"><h3>입력 · Port / Design / Package 분리</h3>{''.join(editor_parts)}
        <p class="form-note">직접 변경한 Port는 다음 평가의 새 고정 조건입니다. 자동 이동·Mode Fitting은 수행하지 않습니다.</p>{input_action}</form></section></div></article>''')
    mode = 'Python Local Inspector · 입력 수정 후 Adapter 재평가' if editable else 'Static Review · 모든 결과는 Python Adapter로 사전 계산'
    reset = '<a href="/">기본 Review Cases로 돌아가기</a>' if editable else ''
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Photonic Architecture Explorer · M3-B</title><style>{CSS}</style></head><body>
    <header><h1>Photonic Architecture Explorer <span style="font-weight:400">/ M3-B Inspector</span></h1><p>Fixed Optical I/O → Two Reflectors · {mode}</p></header>
    <main class="wrap"><div class="toolbar"><label>Review Case <select id="case-select" aria-label="Review Case">{''.join(options)}</select></label><label>Projection <select id="projection-select" aria-label="Projection"><option>XZ</option><option>XY</option><option>YZ</option></select></label>{reset}</div>
    {''.join(articles)}<section class="card review" style="margin-top:18px"><h2>User Review</h2>
    ① Synthetic Relay의 고정 Port와 두 곡면을 확인하세요. ② XZ/XY/YZ와 생략 축을 비교하세요.
    ③ 실패 사례에서 Overlap이 —로 바뀌는지 확인하세요. ④ Envelope Pass와 Full Package Uncomputed를 구분하세요.
    <p class="muted">Approximate Overlap은 Normalized Scalar Gaussian 진단입니다. 실제 Applicability·Total Coupling·Finite-Beam Clearance는 Uncomputed입니다.</p></section></main><script>{JS}</script></body></html>'''


def make_server(cases, port=8765):
    """Loopback only; no files written and no remote evaluation service."""
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def send_page(self, page, status=200):
            payload = page.encode()
            self.send_response(status); self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(payload))); self.send_header('Cache-Control', 'no-store')
            self.end_headers(); self.wfile.write(payload)
        def do_GET(self):
            query = urlsplit(self.path)
            if self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}': self.send_error(403); return
            if query.path != '/': self.send_error(404); return
            key = parse_qs(query.query).get('case', [cases[0][0]])[0]
            selected = [c for c in cases if c[0] == key]
            if not selected: self.send_error(404); return
            # Case options remain available; editor/result is evaluated fresh.
            ordered = selected+[c for c in cases if c[0] != key]
            self.send_page(render_report(ordered, editable=True))
        def do_POST(self):
            if self.path != '/evaluate': self.send_error(404); return
            if self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}': self.send_error(403); return
            origin = self.headers.get('Origin')
            allowed = f'http://127.0.0.1:{self.server.server_port}'
            if origin and origin != allowed: self.send_error(403); return
            try: length = int(self.headers.get('Content-Length', '0'))
            except ValueError: self.send_error(400); return
            if not 0 < length <= 1_000_000: self.send_error(413); return
            try: values = parse_qs(self.rfile.read(length).decode('utf-8', errors='strict'), keep_blank_values=True)
            except UnicodeError: self.send_error(400); return
            if any(len(v) != 1 for v in values.values()): self.send_error(400); return
            raw = {k: v[0] for k, v in values.items()}
            try:
                document = parse_groups(raw)
                self.send_page(render_report([('custom', '수정 입력 · 새 평가', document)], editable=True))
            except (ValueError, TypeError, OverflowError) as exc:
                safe = {k: raw.get(k, '') for k in ('ports', 'reflectors', 'package')}
                self.send_page(render_report([('custom', '입력 오류 · 평가 보류', {})], editable=True, raw_groups=safe, error=exc))
    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, help='one external JSON input instead of built-in review cases')
    parser.add_argument('--output', type=Path, default=Path('results/m3b-inspector.html'))
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    try:
        cases = [('input', args.input.name, json.loads(args.input.read_text()))] if args.input else review_cases()
        json.dumps(cases, allow_nan=False)
    except (ValueError, OSError) as exc: parser.error(str(exc))
    if args.serve:
        server = make_server(cases, args.port)
        print(f'Inspector: http://127.0.0.1:{server.server_port}', flush=True)
        try: server.serve_forever()
        except KeyboardInterrupt: pass
        finally: server.server_close()
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_report(cases), encoding='utf-8')
        print(args.output)
    return 0


if __name__ == '__main__': raise SystemExit(main())
