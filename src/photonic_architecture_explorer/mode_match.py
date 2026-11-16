"""Mode Match diagnostics from already evaluated aligned scalar Gaussian fields."""

from html import escape
import math

from .gaussian import Gaussian
from .geometry import cross
from .inspector import visible_overlap


MODE_MATCH_CSS = """
.mode-match { margin: 12px 0; border-top: 1px solid #d6e0e7; }
.mode-match h4 { margin: 12px 0 4px; }
.mode-match .mode-charts { display: grid; gap: 8px; grid-template-columns:
  repeat(auto-fit, minmax(min(100%, 250px), 1fr)); }
.mode-match figure { margin: 0; min-width: 0; background: #f4f8fa; padding: 6px; border-radius: 4px; }
.mode-match figcaption { padding: 4px; font-size: 12px; font-weight: 650; }
.mode-match svg { display: block; width: 100%; height: auto; }
.mode-match svg text { fill: #324f64; font-size: 13px; }
.mode-match .match-legend { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 12px; }
.mode-match .arrived { color: #176d92; }.mode-match .target { color: #704b9d; }
.mode-match .metadata { overflow-wrap: anywhere; font-size: 12px; }
"""


def loss_label(eta):
    if eta is None:
        return "Uncomputed"
    if eta == 0:
        return "∞ dB"
    return f"{max(0., -10 * math.log10(eta)):.6g} dB"


def axis_profiles(first, axis, second=None):
    """Return a shared grid in metres, intensity in µm⁻¹, and phase in radians."""
    a = first.parameters()[axis]
    b = second.parameters()[axis] if second is not None else a
    extent = 3 * max(a["radius_m"], b["radius_m"])
    coordinates = [extent * (i - 60) / 60 for i in range(121)]

    def intensity(mode):
        return [abs(mode.axis_field(x, axis))**2 * 1e-6 for x in coordinates]

    primary = intensity(first)
    if second is None:
        return coordinates, primary, None, None
    k = 2 * math.pi * first.index / first.wavelength
    delta_curvature = a["curvature_per_m"] - b["curvature_per_m"]
    phase = [-0.5 * k * delta_curvature * x**2 for x in coordinates]
    return coordinates, primary, intensity(second), phase


def plot_series(title, axis, coordinates, primary, target=None, *, phase=False):
    """Draw bounded analytic samples without any browser-side field calculation."""
    x_left, x_right = 57, 342
    y_top, y_bottom = 11, 94
    span = coordinates[-1]
    limit = max(.1, max(abs(value) for value in primary)) if phase else max(primary + (target or []))
    low = -limit if phase else 0.
    y_zero = y_bottom - (0 - low) / (limit - low) * (y_bottom - y_top)
    x_zero = (x_left + x_right) / 2

    def curve(values, color, dash=""):
        points = []
        for x, value in zip(coordinates, values):
            px = x_zero + (x / span) * (x_right - x_zero)
            py = y_bottom - (value - low) / (limit - low) * (y_bottom - y_top)
            points.append(f"{px:.3f},{py:.3f}")
        return (f'<polyline points="{" ".join(points)}" stroke="{color}" stroke-width="2"'
                f' stroke-dasharray="{dash}" fill="none"/>')

    unit = "rad" if phase else "µm⁻¹"
    lines = curve(primary, "#213e4e" if phase else "#176d92")
    if target is not None:
        lines += curve(target, "#704b9d", "5 4")
    return f'''<figure><figcaption>{escape(title)} [{unit}]</figcaption>
    <svg viewBox="0 0 368 131" role="img" aria-label="{escape(title)}">
    <path d="M{x_left} {y_top}V{y_bottom} M{x_zero} {y_top}V{y_bottom} M{x_left} {y_zero}H{x_right}"
          stroke="#9eb1be" fill="none"/>
    <text x="53" y="16" text-anchor="end">{limit:.3g}</text>
    <text x="53" y="98" text-anchor="end">{low:.3g}</text>
    <text x="{x_left}" y="113" text-anchor="middle">{-span*1e6:.3g}</text>
    <text x="{x_zero}" y="113" text-anchor="middle">0</text>
    <text x="{x_right}" y="113" text-anchor="middle">{span*1e6:.3g}</text>
    <text x="{x_zero}" y="129" text-anchor="middle">{axis} [µm]</text>
    {lines}</svg></figure>'''


def describe_plane(record, port):
    plane = record["value"]
    t = cross(port.sagittal, port.direction)

    def vector(values):
        return "(" + ", ".join(f"{v:.6g}" for v in values) + ")"

    return (f'{plane["id"]} · {plane["frame_id"]} · origin {vector(plane["origin_m"])} m'
            f' · t {vector(t)} · s {vector(port.sagittal)} · normal {vector(plane["normal"])}')


def arrived_mode(evaluation, target):
    # These are the evaluated output beam parameters at the Target plane.
    output_axes = evaluation["gaussian_mode_matching"]["output_axes"]
    return Gaussian(*(complex(-p["waist_distance_m"], p["rayleigh_range_m"])
                         for p in output_axes), target.wavelength, target.index)


def render_mode_match(candidate, input_sha, adapted):
    evaluation = candidate["evaluation"]
    eta = visible_overlap(evaluation)
    if eta is None:
        return '<p>Mode Match · Uncomputed</p>'
    source = adapted.source.mode
    target = adapted.target.mode
    arrival = arrived_mode(evaluation, target)
    source_plots, target_plots, phase_plots = [], [], []
    for index, axis in enumerate(("t", "s")):
        x, incident, _, _ = axis_profiles(source, index)
        source_plots.append(plot_series(f"Source · {axis} intensity", axis, x, incident))
        x, incoming, desired, phase = axis_profiles(arrival, index, target)
        target_plots.append(plot_series(f"Target plane · {axis} intensity", axis, x, incoming, desired))
        phase_plots.append(plot_series(f"Target plane · Δφ along {axis}", axis, x, phase, phase=True))

    prescription = candidate["prescription"]
    sp = prescription["source"]["reference_plane"]
    tp = prescription["target"]["reference_plane"]
    source_plane = escape(describe_plane(sp, adapted.source))
    target_plane = escape(describe_plane(tp, adapted.target))
    candidate_id = escape(candidate["id"])
    digest = escape(input_sha)
    return f'''<details class="mode-match" data-mode-match="{candidate_id}" data-input-sha="{digest}"
          data-source-plane="{escape(sp["value"]["id"])}" data-target-plane="{escape(tp["value"]["id"])}"
          data-mode-eta="{eta}">
    <summary>Mode Match 상세 · {eta:.6%} · {loss_label(eta)}</summary>
    <p>Normalized Mode Overlap <strong>{eta:.6%}</strong> ·
    Mode Mismatch Loss <strong data-mismatch-loss>{loss_label(eta)}</strong> · Total Coupling Uncomputed</p>
    <p class="metadata">후보 {candidate_id} · Input SHA256 <code>{digest}</code></p>
    <h4>Source Reference Plane</h4><p class="metadata">{source_plane}</p>
    <div class="mode-charts">{"".join(source_plots)}</div>
    <h4>Target Reference Plane</h4><p class="metadata">{target_plane}</p>
    <div class="match-legend"><span class="arrived">━━ 도착 빔</span><span class="target">┄┄ Target Mode</span></div>
    <p class="caption">각 축은 적분이 1인 강도 주변분포입니다. 도착 빔과 Target Mode에 동일한 좌표와 눈금을 씁니다.</p>
    <div class="mode-charts">{"".join(target_plots)}</div>
    <p class="caption">Δφ는 도착 빔 − Target의 공간 위상 차이입니다. 포트 중심을 0 rad로 두고 연속 위상을 표시합니다.</p>
    <div class="mode-charts">{"".join(phase_plots)}</div></details>'''
