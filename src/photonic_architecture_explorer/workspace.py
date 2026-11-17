"""Local Two-Port editor for the existing bounded Gaussian Design engine."""

import argparse
import copy
from decimal import Decimal, InvalidOperation
from html import escape
import json
import math

from .design import design_two_ports
from .design_report import render_design_report
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
INPUT_SOURCE = "User input in M5-B Two-Port Workspace"


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
        raw[name + "_mode"] = "q" if document[name].get(Q[0], {}).get("value") is not None else "mfd"
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


def assign(node, prefix, spec, raw, unit):
    key, label, axes, exponent = spec
    parts = [parse_number(raw[field_name(prefix, spec, i)], f"{prefix}{label} {axis}", exponent)
             for i, axis in enumerate(axes)]
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
    """Translate display units to SI and keep only the explicitly chosen mode."""
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
        plane = port["reference_plane"]
        if position_changed or direction_changed:
            plane["value"]["origin_m"] = port["position_m"]["value"]
            plane["value"]["normal"] = port["propagation_direction"]["value"]
            plane.update(provenance="supplied", source="Defined by the entered external Port position and direction",
                         uncertainty=None)

        if raw[prefix + "mode"] == "mfd":
            mode_changed = assign(port, prefix, MFD, raw, "m")
            mode_changed |= assign(port, prefix, PHASE, raw, "m^-1")
            mode_changed |= port.pop(Q[0], None) is not None
        else:
            mode_changed = assign(port, prefix, Q, raw, "m")
            mode_changed |= port.pop(MFD[0], None) is not None
            mode_changed |= port.pop(PHASE[0], None) is not None

        if shared_changed or position_changed or direction_changed or basis_changed or mode_changed:
            port["mode_evidence"] = {"value": {"kind": "gaussian_assumption"},
                                     "unit": "evidence", "provenance": "assumed",
                                     "source": "User-defined external scalar Gaussian at the stated reference plane",
                                     "uncertainty": None}
            edited = True
    if edited:
        document["description"] = "M5-B workspace: explicit external Port inputs, scalar Gaussian model"
    return document


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


def render_fields(prefix, spec, raw):
    _, label, axes, _ = spec
    controls = []
    for index, axis in enumerate(axes):
        name = field_name(prefix, spec, index)
        controls.append(f'<label>{axis}<input name="{name}" inputmode="decimal" '
                        f'aria-label="{escape(label)} · {axis}" value="{escape(raw[name])}" autocomplete="off"></label>')
    return f'<fieldset><legend>{escape(label)}</legend><div class="values">{"".join(controls)}</div></fieldset>'


def render_port(port, raw):
    prefix = port + "_"
    mode = raw[prefix + "mode"]
    position, direction, sagittal, mfd, phase, q = [render_fields(prefix, spec, raw) for spec in PORT_FIELDS]
    mode_tip = "출사 방향" if port == "source" else "Target에 도착하는 방향"
    return f'''<section class="card" data-port="{port}"><h2>{port.title()} Port</h2>
    <p class="caption">External Reference Plane · 원점은 Position, 법선은 {mode_tip}입니다.</p>
    {position}{direction}
    <label class="mode">Mode 표현 <select name="{prefix}mode" data-mode>
      <option value="mfd"{' selected' if mode == 'mfd' else ''}>MFD + Wavefront Phase</option>
      <option value="q"{' selected' if mode == 'q' else ''}>Complex q</option>
    </select></label>
    <div data-mode-group="mfd"{' hidden' if mode != 'mfd' else ''}>{mfd}{phase}
    <p class="caption">Flat Phase인 경우에만 두 축에 0을 입력하세요.</p></div>
    <div data-mode-group="q"{' hidden' if mode != 'q' else ''}>{q}</div>
    <details{' open' if not raw[prefix + 'sagittal_axis_0'] else ''}><summary>Mode 기준축</summary>{sagittal}
    <p class="caption">두 Port는 같은 Sagittal 축을 사용합니다. Tangential 축은 s × d입니다.</p></details>
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
for (const select of form.querySelectorAll('[data-mode]')) {
  select.addEventListener('change', () => {
    for (const group of select.closest('[data-port]').querySelectorAll('[data-mode-group]')) {
      group.hidden = group.dataset.modeGroup !== select.value;
    }
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
      const data = format === 'html' ? frame.getAttribute('srcdoc') :
        frame.contentDocument.querySelector('#design-result').textContent + '\\n';
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
    ports = "".join(render_port(port, raw) for port in PORTS)
    review = ""
    if result is not None:
        report = escape(render_design_report(result))
        status = escape(result["status"])
        review = f'''<section id="design-output" class="output" data-status="{status}">
          <div class="toolbar"><button type="button" data-export="html">HTML 저장</button>
          <button type="button" data-export="json">JSON 저장</button></div>
          <iframe id="design-review" title="Two-Port 설계 결과" srcdoc="{report}"></iframe></section>'''
    elif error:
        review = f'<section id="design-output" class="card output" role="alert">입력 오류 · {escape(error)}</section>'

    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Photonic Architecture Explorer · Two-Port Workspace</title><style>{CSS}
    .ports,.values,.shared{{display:grid;gap:12px;min-width:0}}.ports,.shared{{grid-template-columns:repeat(2,minmax(0,1fr))}}
    .values{{grid-template-columns:repeat(auto-fit,minmax(min(100%,84px),1fr))}}
    fieldset{{min-width:0;padding:8px 0 12px;margin:0;border:0}}legend{{font-weight:600}}
    .values label{{display:grid;gap:4px;min-width:0;color:#506b7b}}
    input{{width:100%;min-width:0;font:inherit;padding:8px;border:1px solid #b7c5cf;border-radius:4px}}
    input:focus,select:focus,button:focus{{outline:2px solid #176d92;outline-offset:2px}}
    .mode{{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:8px 0 14px}}
    .mode select{{max-width:100%}}.shared,.output,.form-actions{{margin-top:16px}}
    .output iframe{{display:block;width:100%;min-height:35rem;border:1px solid #d6e0e7;border-radius:8px;background:#fff}}
    .toolbar .example-links{{display:flex;gap:14px;flex-wrap:wrap}}
    @media(max-width:760px){{.ports{{grid-template-columns:minmax(0,1fr)}}}}
    </style></head><body><header><h1>Photonic Architecture Explorer</h1>
    <p>Two-Port Design Workspace</p></header><main class="wrap">
    <div class="toolbar"><div class="example-links"><a href="/">Synthetic Example</a>
    <a href="/?entry=blank">새 입력</a></div><span>{description}</span></div>
    <form id="design-form" method="post" action="/design#design-output">
      <input type="hidden" name="entry" value="{entry}">
      <div class="ports">{ports}</div>
      <section class="card shared" aria-label="공통 전파 조건">{fields}</section>
      <div class="form-actions"><button type="submit">Design</button></div>
    </form><p class="notice" id="pending" role="status" hidden>지금 입력으로 결과를 확인하려면 Design을 실행하세요.</p>
    {review}</main><script>{WORKSPACE_JS}</script></body></html>'''


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
        if any(raw[port + "_mode"] not in ("mfd", "q") for port in PORTS):
            return self.get(entry), 400
        try:
            document = build_document(self.templates[entry], raw)
        except ValueError as exc:
            return render_workspace(raw, error=str(exc)), 200
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
