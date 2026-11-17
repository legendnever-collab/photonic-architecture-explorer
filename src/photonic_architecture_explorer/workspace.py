"""Local Two-Port editor for the existing bounded Gaussian Design engine."""

import argparse
import copy
from decimal import Decimal, InvalidOperation
from html import escape
import json
import math

from .design import design_two_ports
from .design_report import render_design_report, review_snapshot
from .external import InputIssue, unit_vector, vector
from .geometry import cross, dot, mul, norm, sub
from .inspector import CSS, ROOT, make_server


POSITION = ("position_m", "Position [mm]", ("X", "Y", "Z"), 3)
DIRECTION = ("propagation_direction", "Propagation Direction · unit vector", ("X", "Y", "Z"), 0)
SAGITTAL = ("sagittal_axis", "Sagittal Axis · unit vector", ("X", "Y", "Z"), 0)
MFD = ("mfd_ts_m", "Mode Field Diameter (1/e² intensity) [µm]", ("t", "s"), 6)
PHASE = ("wavefront_curvature_ts_per_m", "Wavefront Curvature 1/R [m⁻¹]", ("t", "s"), 0)
Q = ("complex_q_ts_m", "Ordinary complex q [mm]", ("Re qₜ", "Im qₜ", "Re qₛ", "Im qₛ"), 3)
WAVELENGTH = ("wavelength_m", "Vacuum Wavelength [nm]", ("λ",), 9)
INDEX = ("ambient_index", "External Ambient Index", ("n",), 0)
PORTS = ("source", "target")
PORT_FIELDS = (POSITION, DIRECTION, SAGITTAL, MFD, PHASE, Q)
SHARED_FIELDS = (WAVELENGTH, INDEX)
INPUT_SOURCE = "User input in Two-Port Workspace"
# Match the frozen external adapter and coplanarity guard.
FRAME_TOL = 1e-10


def field_name(prefix, spec, index):
    return f"{prefix}{spec[0]}_{index}"


def field_values(node, spec):
    key, _, labels, exponent = spec
    value = node.get(key, {}).get("value")
    if value is None:
        return [""] * len(labels)
    if spec == Q:
        value = [part for axis in value for part in axis]
    elif len(labels) == 1:
        value = [value]
    return ["" if part is None else format(Decimal(str(part)).scaleb(exponent).normalize(), 'f')
            for part in value]


def initial_values(document, entry):
    raw = {"entry": entry}
    groups = [("", document, SHARED_FIELDS)]
    groups.extend((name + "_", document[name], PORT_FIELDS) for name in PORTS)
    for prefix, node, specs in groups:
        for spec in specs:
            for index, value in enumerate(field_values(node, spec)):
                raw[field_name(prefix, spec, index)] = value
    for name in PORTS:
        port = document[name]
        if port.get(Q[0], {}).get("value") is not None:
            raw[name + "_mode"] = "q"
        elif entry == "blank":
            raw[name + "_mode"] = "round"
        else:
            raw[name + "_mode"] = "mfd"
    return raw


def parse_number(text, label, exponent):
    if not text.strip():
        return None
    try:
        decimal_value = Decimal(text.strip()).scaleb(-exponent)
        value = float(decimal_value)
        if math.isfinite(value) and (value != 0 or decimal_value.is_zero()):
            return value
    except (InvalidOperation, OverflowError, ValueError):
        pass
    raise ValueError(f"{label}: 유한한 숫자를 입력하세요.")


def assign(node, prefix, spec, raw, unit, round_mode=False):
    key, label, axes, exponent = spec
    parts = [parse_number(raw[field_name(prefix, spec, i)], f"{prefix}{label} {axis}", exponent)
             for i, axis in enumerate(axes[:1] if round_mode else axes)]
    if round_mode:
        parts *= 2
    if all(value is None for value in parts):
        value = None
    elif len(parts) == 1:
        value = parts[0]
    elif spec == Q:
        value = [parts[:2], parts[2:]]
    else:
        value = parts

    previous = node.get(key, {})
    if previous.get("value") == value:
        return False
    node[key] = {**previous, "value": value, "unit": unit,
                 "provenance": "supplied" if value is not None else "unprovided",
                 "source": INPUT_SOURCE if value is not None else "", "uncertainty": None}
    return True


def build_document(template, raw):
    """Translate display units to SI, preserving unedited supplied records."""
    document = copy.deepcopy(template)
    shared_changed = assign(document, "", WAVELENGTH, raw, "m")
    shared_changed |= assign(document, "", INDEX, raw, "1")
    edited = shared_changed
    for name in PORTS:
        port = document[name]
        prefix = name + "_"
        position_changed = assign(port, prefix, POSITION, raw, "m")
        direction_changed = assign(port, prefix, DIRECTION, raw, "1")
        basis_changed = assign(port, prefix, SAGITTAL, raw, "1")
        update_reference_plane(port, template[name])
        mode = raw[prefix + "mode"]
        previous_q = template[name].get(Q[0], {}).get("value") is not None
        if mode == "q":
            mode_changed = assign(port, prefix, Q, raw, "m")
            if Q[0] not in port:
                port[Q[0]] = {"value": None, "unit": "m", "provenance": "unprovided",
                              "source": "", "uncertainty": None}
            if not previous_q:
                mode_changed |= port.pop(MFD[0], None) is not None
                mode_changed |= port.pop(PHASE[0], None) is not None
        else:
            mode_changed = assign(port, prefix, MFD, raw, "m", round_mode=mode == "round")
            mode_changed |= assign(port, prefix, PHASE, raw, "m^-1", round_mode=mode == "round")
            mode_changed |= port.pop(Q[0], None) is not None

        if shared_changed or position_changed or direction_changed or basis_changed or mode_changed:
            port["mode_evidence"] = {"value": {"kind": "gaussian_assumption"},
                                     "unit": "evidence", "provenance": "assumed",
                                     "source": "User-defined external scalar Gaussian at the stated reference plane",
                                     "uncertainty": None}
            edited = True
    if edited:
        document["description"] = "Two-Port Workspace: explicit external Port inputs, scalar Gaussian model"
    return document



def update_reference_plane(port, previous):
    # Workspace coordinates are explicitly entered at the named external plane.
    # Preserve a distinct supplied plane so the existing adapter checks it.
    plane = port.get("reference_plane")
    if not plane or not plane.get("value") or plane["value"].get("side") != "external":
        return
    changed = False
    for key, field in (("origin_m", POSITION[0]), ("normal", DIRECTION[0])):
        old = plane["value"].get(key)
        value = port[field]["value"]
        if old == value or (old is not None and old != previous[field]["value"]):
            continue
        if value is not None:
            try:
                if key == "origin_m":
                    vector(value, 3, field)
                else:
                    unit_vector(value, field)
            except InputIssue:
                continue
        plane["value"][key] = value
        changed = True
    if changed:
        plane.update(provenance="supplied", uncertainty=None,
                     source="Workspace external reference plane: origin_m = position_m; "
                            "normal = propagation_direction in the named frame")

def resolve_coordinates(document):
    """Supply only geometry-defined metadata and a rotation-invariant Mode basis."""
    ports = [document[name] for name in PORTS]
    positions = []
    directions = []
    for name, port in zip(PORTS, ports):
        position = port["position_m"]["value"]
        direction = port["propagation_direction"]["value"]
        if position is None or direction is None:
            raise InputIssue("Uncomputed", name, "External Reference Plane의 Position과 Direction을 입력하세요.")
        positions.append(vector(position, 3, name + ".position"))
        directions.append(unit_vector(direction, name + ".direction"))
    frames = [(port.get("reference_plane", {}).get("value") or {}).get("frame_id") for port in ports]
    if None in frames:
        raise InputIssue("Uncomputed", "reference_plane", "공통 Frame의 External Reference Plane이 필요합니다.")
    if frames[0] != frames[1]:
        raise InputIssue("Fail", "frame_id", "두 Port를 같은 Frame으로 변환해 입력하세요.")
    delta = sub(positions[1], positions[0])
    separation = norm(delta)
    if not math.isfinite(separation) or separation == 0:
        raise InputIssue("Fail", "position_m", "서로 다른 유한한 두 Port Position을 입력하세요.")
    baseline = tuple(component / separation for component in delta)
    rays = [*directions, baseline]
    crosses = [cross(rays[i], rays[j]) for i, j in ((0, 1), (0, 2), (1, 2))]
    normal = max(crosses, key=norm)
    magnitude = norm(normal)
    axis = mul(normal, 1 / magnitude) if magnitude > FRAME_TOL else None
    if axis is not None and any(abs(dot(axis, ray)) > FRAME_TOL for ray in rays):
        raise InputIssue("Fail", "port_geometry",
                         "Skew · 두 Direction과 Port 간 변위가 한 평면에 놓이지 않습니다.")

    supplied = {}
    for name, port, direction in zip(PORTS, ports, directions):
        value = port.get(SAGITTAL[0], {}).get("value")
        if value is not None:
            sagittal = unit_vector(value, name + ".sagittal_axis")
            if abs(dot(sagittal, direction)) > FRAME_TOL:
                raise InputIssue("Fail", name + ".sagittal_axis", "Mode Axis는 Port Direction에 수직이어야 합니다.")
            if axis is not None and norm(cross(axis, sagittal)) > FRAME_TOL:
                raise InputIssue("Fail", name + ".sagittal_axis",
                                 "Rolled · 명시한 Mode Axis가 Fold Plane의 법선과 정렬되지 않습니다.")
            supplied[name] = sagittal
    if len(supplied) == len(PORTS):
        return

    missing = {}
    for name, port in zip(PORTS, ports):
        if name in supplied:
            continue
        q = port.get(Q[0], {}).get("value")
        if Q[0] in port:
            pairs = list(zip(*q)) if q is not None else [None]
            mode_message = "완전한 Complex q를 입력하세요."
        else:
            pairs = [port.get(spec[0], {}).get("value") for spec in (MFD, PHASE)]
            mode_message = "MFD와 Wavefront Phase를 입력하세요. Flat Phase는 0으로 명시하세요."
        if any(pair is None or None in pair for pair in pairs):
            raise InputIssue("Uncomputed", name, mode_message)
        if not all(first == second for first, second in pairs):
            raise InputIssue("Uncomputed", name + ".sagittal_axis",
                             "Elliptical / Astigmatic Mode · 이 Port의 실제 Sagittal Axis를 상세 입력에 지정하세요.")
        missing[name] = port
    if axis is None:
        raise InputIssue("Uncomputed", "fold_plane",
                         "Ambiguous Fold Plane · Position과 Direction이 공선입니다. "
                         "상세 입력에 두 Port의 공통 Sagittal Axis를 지정하세요.")

    # The normal is an unoriented line. Keep an explicit sign when available;
    # otherwise use the largest component for a deterministic coordinate convention.
    explicit = next(iter(supplied.values()), None)
    if explicit is not None:
        axis = explicit
    elif max(axis, key=abs) < 0:
        axis = mul(axis, -1)
    for port in missing.values():
        port[SAGITTAL[0]] = {
            "value": [component or 0.0 for component in axis], "unit": "1",
            "provenance": "supplied", "uncertainty": None,
            "source": "Derived by Workspace: unique coplanar normal from Source/Target "
                      "propagation_direction and position_m displacement; rotation-invariant "
                      "Gaussian (equal complex axes). Sign follows supplied sagittal_axis "
                      "when present, otherwise largest component is positive.",
        }


def new_input(example):
    document = copy.deepcopy(example)
    document["description"] = "New external scalar Gaussian inputs"
    for node, specs in ((document, SHARED_FIELDS), *((document[name], PORT_FIELDS) for name in PORTS)):
        for key, *_ in specs:
            if key in node:
                node[key].update(value=None, provenance="unprovided", source="", uncertainty=None)
    for name in PORTS:
        port = document[name]
        plane = port["reference_plane"]
        plane["value"].update(origin_m=None, normal=None)
        plane.update(provenance="assumed", source="External plane defined by the input position and propagation direction")
        for key, value in (("mode_evidence", {"kind": "gaussian_assumption"}),
                           ("polarization", {"treatment": "scalar_ignored"})):
            port[key].update(value=value, provenance="assumed",
                             source="Workspace scalar Gaussian model assumption", uncertainty=None)
    return document


def render_fields(prefix, spec, raw, round_mode=False):
    _, label, axes, _ = spec
    controls = []
    for index, axis in enumerate(axes):
        name = field_name(prefix, spec, index)
        attrs = ''
        if spec in (MFD, PHASE):
            attrs = f' data-mode-axis="{index}"' + (' hidden' if round_mode and index == 1 else '')
        controls.append(f'<label{attrs}><span>{axis}</span><input name="{name}" inputmode="decimal" '
                        f'aria-label="{escape(label)} · {axis}" value="{escape(raw[name])}" autocomplete="off"></label>')
    return f'<fieldset><legend>{escape(label)}</legend><div class="values">{"".join(controls)}</div></fieldset>'


def render_port(port, raw, issue_path):
    prefix = port + "_"
    mode = raw[prefix + "mode"]
    position, direction, sagittal, mfd, phase, q = [
        render_fields(prefix, spec, raw, round_mode=mode == "round") for spec in PORT_FIELDS]
    mode_tip = "출사 방향" if port == "source" else "Target에 도착하는 방향"
    advanced = (mode == "q" or issue_path in ("fold_plane", port + ".sagittal_axis"))
    return f'''<section class="card" data-port="{port}" data-mode-kind="{mode}"><h2>{port.title()} Port</h2>
    <p class="caption">External Reference Plane · 원점은 Position, 법선은 {mode_tip}입니다.</p>
    {position}{direction}
    <div data-mode-group="mfd"{' hidden' if mode == 'q' else ''}>{mfd}{phase}
    <p class="caption" data-round-tip{' hidden' if mode != 'round' else ''}>Rotation-symmetric Mode · 같은 MFD와 Phase를 두 축에 적용합니다.</p>
    <p class="caption">Flat Phase는 0으로 명시하세요.</p></div>
    <details data-advanced{' open' if advanced else ''}><summary>상세 입력 · Mode 표현 및 좌표축</summary>
    <label class="mode">Mode 표현 <select name="{prefix}mode" data-mode>
      <option value="round"{' selected' if mode == 'round' else ''}>Rotation-symmetric · MFD + Phase</option>
      <option value="mfd"{' selected' if mode == 'mfd' else ''}>Elliptical / Astigmatic · MFD(t/s) + Phase(t/s)</option>
      <option value="q"{' selected' if mode == 'q' else ''}>Complex q</option>
    </select></label>
    <div data-mode-group="q"{' hidden' if mode != 'q' else ''}>{q}</div>
    {sagittal}
    <p class="caption">Rotation-symmetric Mode는 Fold Plane이 유일할 때 축을 자동으로 구합니다.
    Elliptical / Astigmatic Mode에는 실제 Sagittal Axis를 입력하세요.</p></details>
    </section>'''


WORKSPACE_JS = """
const form = document.querySelector('#design-form');
const output = document.querySelector('#design-output');
const pending = document.querySelector('#pending');
const frame = document.querySelector('#design-review');
function edit() {
  if (output) output.hidden = true;
  pending.hidden = false;
}
form.addEventListener('input', edit);
form.addEventListener('change', edit);
form.addEventListener('submit', edit);
window.addEventListener('pageshow', () => {
  // Browsers can restore edited values when returning via history.
  for (const control of form.elements) {
    if (control instanceof HTMLInputElement && control.value !== control.defaultValue ||
        control instanceof HTMLSelectElement && !control.selectedOptions[0]?.defaultSelected) {
      edit();
      break;
    }
  }
});
for (const select of form.querySelectorAll('[data-mode]')) {
  select.addEventListener('change', () => {
    const port = select.closest('[data-port]');
    port.dataset.modeKind = select.value;
    port.querySelector('[data-mode-group="mfd"]').hidden = select.value === 'q';
    port.querySelector('[data-mode-group="q"]').hidden = select.value !== 'q';
    port.querySelector('[data-round-tip]').hidden = select.value !== 'round';
    for (const axis of port.querySelectorAll('[data-mode-axis="1"]')) axis.hidden = select.value === 'round';
  });
}
if (frame) {
  const fit = () => {
    const body = frame.contentDocument.body;
    if (body && !output.hidden) frame.style.height = body.scrollHeight + 'px';
  };
  let observer;
  const watch = () => {
    if (!frame.contentDocument.querySelector('#design-result')) return;
    if (observer) observer.disconnect();
    observer = new ResizeObserver(fit);
    observer.observe(frame.contentDocument.body);
    fit();
  };
  frame.addEventListener('load', watch);
  watch();
  for (const button of output.querySelectorAll('[data-export]')) {
    button.addEventListener('click', () => {
      if (output.hidden) return;
      const format = button.dataset.export;
      const script = frame.contentDocument.querySelector('#design-result');
      const original = script.textContent;
      const viewed = frame.contentDocument.querySelector('#candidate-select')?.value;
      // Preserve the engine JSON's exact numbers and recommendation; save the viewed candidate separately.
      const encodedId = viewed && JSON.stringify(viewed);
      const payload = viewed ? '{"viewed_candidate_id":' + encodedId + ',' + original.slice(1) : original;
      const start = '<script type="application/json" id="design-result">';
      const html = frame.getAttribute('srcdoc');
      const data = format === 'html' ?
        html.replace(start + original, () => start + payload) : payload + '\\n';
      const url = URL.createObjectURL(new Blob([data], {
        type: format === 'html' ? 'text/html;charset=utf-8' : 'application/json;charset=utf-8'
      }));
      const link = document.createElement('a');
      link.href = url;
      link.download = 'design.' + format;
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 30000);
    });
  }
}
"""


def render_workspace(raw, result=None, error=None):
    entry = raw["entry"]
    description = ("M5-A Synthetic Example · 입력값을 바꾸면 다음 실행의 고정 조건이 됩니다."
                   if entry == "example" else "새 입력 · External Gaussian 가정, 편광은 scalar 모델에서 제외")
    fields = "".join(render_fields("", spec, raw) for spec in SHARED_FIELDS)
    issue_path = result.get("input_contract", {}).get("path") if result else None
    ports = "".join(render_port(port, raw, issue_path) for port in PORTS)
    review = ""
    if result is not None:
        report = escape(render_design_report(review_snapshot(result)))
        status = escape(result["status"])
        review = f'''<section id="design-output" class="output" data-status="{status}">
          <div class="toolbar"><a href="#design-form">입력 편집</a><div class="export-actions">
          <button type="button" data-export="html">HTML 저장</button>
          <button type="button" data-export="json">JSON 저장</button></div></div>
          <iframe id="design-review" title="Two-Port 설계 결과" srcdoc="{report}"></iframe></section>'''
    elif error:
        review = f'<section id="design-output" class="card output" role="alert">입력 오류 · {escape(error)}</section>'

    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Photonic Architecture Explorer · Two-Port Workspace</title><style>{CSS}
    .ports,.values,.shared{{display:grid;gap:12px;min-width:0}}.ports,.shared{{grid-template-columns:repeat(2,minmax(0,1fr))}}
    .values{{grid-template-columns:repeat(auto-fit,minmax(min(100%,84px),1fr))}}
    fieldset{{min-width:0;padding:8px 0 12px;margin:0;border:0}}legend{{font-weight:600}}
    [data-mode-kind="round"] [data-mode-axis="0"] span{{display:none}}
    .values label{{display:grid;gap:4px;min-width:0;color:#506b7b}}
    input{{width:100%;min-width:0;font:inherit;padding:8px;border:1px solid #b7c5cf;border-radius:4px}}
    input:focus,select:focus,button:focus{{outline:2px solid #176d92;outline-offset:2px}}
    .mode{{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:8px 0 14px}}
    .mode select{{max-width:100%}}.shared,.output,.form-actions{{margin-top:16px}}
    .output iframe{{display:block;width:100%;min-height:35rem;border:1px solid #d6e0e7;border-radius:8px;background:#fff}}
    .toolbar .example-links,.export-actions{{display:flex;gap:10px;flex-wrap:wrap}}
    #design-form{{scroll-margin-top:12px}}
    @media(max-width:760px){{.ports{{grid-template-columns:minmax(0,1fr)}}}}
    </style></head><body><header><h1>Photonic Architecture Explorer</h1>
    <p>Two-Port Design Workspace</p></header><main class="wrap">
    {review}
    <p class="notice" id="pending" role="status" hidden>지금 입력으로 결과를 확인하려면 Design을 실행하세요.</p>
    <div class="toolbar"><div class="example-links"><a href="/">Synthetic Example</a>
    <a href="/?entry=blank">새 입력</a></div><span>{description}</span></div>
    <form id="design-form" method="post" action="/design#design-output">
      <input type="hidden" name="entry" value="{entry}">
      <div class="ports">{ports}</div>
      <section class="card shared" aria-label="공통 전파 조건">{fields}</section>
      <div class="form-actions"><button type="submit">Design</button></div>
    </form></main><script>{WORKSPACE_JS}</script></body></html>'''


class Workspace:
    def __init__(self):
        example = json.loads((ROOT / "examples/m5a_two_ports.json").read_text(encoding="utf-8"))
        self.templates = {"example": example, "blank": new_input(example)}
        self.fields = set(initial_values(example, "example"))

    def get(self, entry):
        return render_workspace(initial_values(self.templates[entry], entry))

    def post(self, raw):
        entry = raw.get("entry")
        if entry not in self.templates or set(raw) != self.fields:
            return self.get("example"), 400
        if any(raw[port + "_mode"] not in ("mfd", "round", "q") for port in PORTS):
            return self.get(entry), 400
        try:
            document = build_document(self.templates[entry], raw)
        except ValueError as exc:
            return render_workspace(raw, error=str(exc)), 200
        try:
            resolve_coordinates(document)
        except InputIssue as exc:
            result = design_two_ports(document)
            # The frozen engine refuses unresolved inputs. Explain the workspace
            # prerequisite with the same snapshot, without publishing candidates.
            if result["status"] != "Computed":
                result.update(status=exc.status, reason=str(exc),
                              input_contract={"status": exc.status, "path": exc.path, "reason": exc.reason})
            return render_workspace(raw, result=result), 200
        return render_workspace(raw, result=design_two_ports(document)), 200


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    with make_server((), args.port, workspace=Workspace()) as server:
        print(f"Workspace: http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
