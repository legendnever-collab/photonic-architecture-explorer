"""Render archived reference cases independently of editable Workspace inputs."""
from functools import lru_cache
import json
from pathlib import Path
from string import Template

import numpy as np

from .design import record
from .external import adapt_external
from .gaussian import Gaussian
from .inspector import CSS, ROOT, plot_svg
from .mode_match import MODE_MATCH_CSS, axis_profiles, plot_series
from .reference_redesign import PORTS_FILE, SUMMARY_FILE

# The Windows build copies these small, original records alongside the app.
REFERENCE_FILES = (
    SUMMARY_FILE,
    "references/m7r20/profiles.npz",
    "results/m4b_literature_001.json",
)
EVIDENCE_BASE = ("https://github.com/legendnever-collab/photonic-architecture-explorer/"
                 "blob/ddf8ce0bca3a887f24fae45671a93e11ce7760ec/")


def read_json(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def profile_chart(title, x, curves, x_label, y_label):
    """Plot ordered nonnegative data in its supplied units with a shared linear scale."""
    x_max = max(x)
    y_max = max(max(values) for _, _, values in curves)
    lines = []
    for _, color, values in curves:
        points = " ".join(f"{70 + 420 * xi / x_max:.2f},{135 - 110 * yi / y_max:.2f}"
                          for xi, yi in zip(x, values, strict=True))
        lines.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2"/>')
    legend = " · ".join(f'<span style="color:{color}">{name}</span>' for name, color, _ in curves)
    return f"""<figure><figcaption>{title} · {legend}</figcaption>
    <svg viewBox="0 0 530 173" role="img" aria-label="{title}">
    <path d="M70 25V135H490" fill="none" stroke="#768998"/>
    <text x="69" y="17">{y_label}</text><text x="62" y="32" text-anchor="end">{y_max:.3g}</text>
    <text x="62" y="139" text-anchor="end">0</text><text x="70" y="153">0</text>
    <text x="490" y="153" text-anchor="end">{x_max:.3g}</text>
    <text x="265" y="168" text-anchor="middle">{x_label}</text>{''.join(lines)}</svg></figure>"""


@lru_cache(maxsize=1)
def render_tutorial():
    summary = read_json(REFERENCE_FILES[0])
    candidate = next(c for c in summary["candidates"] if c["id"] == summary["selected"])
    fixed = read_json(PORTS_FILE)
    prescription = {**fixed, "design": {"reflectors": candidate["reflectors"]},
                    "reflectors": [{"surface_prescription": record("quadratic_patch", "model")}
                                   for _ in candidate["reflectors"]]}
    adapted = adapt_external(prescription)
    geometry = {"geometry": {"status": candidate["states"]["geometry"]}}
    path_a = plot_svg(prescription, geometry, adapted, "XZ", "reference-a")
    proxy = read_json(REFERENCE_FILES[2])["adapter_result"]
    doc_b = proxy["input_snapshot"]
    path_b = plot_svg(doc_b, proxy, adapt_external(doc_b), "XZ", "reference-b")
    target = adapted.target.mode
    reference = candidate["independent_validation"]
    arrived = Gaussian(*(complex(*q) for q in reference["q_output_m"]), target.wavelength, target.index)
    x, incoming, desired, phase = axis_profiles(arrived, 0, target)
    modes = (plot_series("Target Plane · 도착 빔과 Target Mode", "t", x, incoming, desired)
             + plot_series("Target Plane · 중심 기준 상대 Phase", "t", x, phase, phase=True))

    z = np.linspace(0, candidate["segments_m"][0], 65)
    radii = np.array([[a["radius_m"] for a in adapted.source.mode.propagate(zi).parameters()] for zi in z])
    beam = profile_chart("SMF → M1 · Gaussian Beam Envelope", z * 1e3,
                         [("t", "#176d92", radii[:, 0] * 1e6), ("s", "#804493", radii[:, 1] * 1e6)],
                         "광축 거리 [mm]", "1/e² 반경 [µm]")

    with np.load(ROOT / REFERENCE_FILES[1]) as archive:
        r = archive["r_um"]
        field = archive["guide-24_input"]
        components = archive["components"].tolist()
        fields = profile_chart("직선 SMF 입력면 · 24 px/µm", r,
                               [("|Er|", "#176d92", abs(field[:, components.index("Er")])),
                                ("|Z₀Hφ|", "#804493", abs(field[:, components.index("Z0Hp")]))],
                               "반경 r [µm]", "진폭 [Solver 상대 단위]")
    template = Path(__file__).with_name("data") / "tutorial.html"
    return Template(template.read_text(encoding="utf-8")).substitute(
        css=CSS + MODE_MATCH_CSS, base=EVIDENCE_BASE, path_a=path_a, path_b=path_b,
        beam=beam, modes=modes, fields=fields, overlap=f'{candidate["overlap"]:.8f}',
        snapshot=summary["input_sha256"])
