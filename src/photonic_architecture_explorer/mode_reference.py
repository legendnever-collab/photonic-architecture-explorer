"""Read-only views of literature Mode Width and Intensity evidence."""

import hashlib
import json
import math
from html import escape
from importlib.resources import files
from itertools import cycle


CATALOG = files(__package__).joinpath("data").joinpath("m7r1_mode_references.json")
REFERENCE_CSS = """
body { margin: 0 auto; padding: 1.5rem; max-width: 72rem; color: #142239;
        background: #f9fbfe; font: 1rem/1.5 system-ui, sans-serif; }
h1, h2, h3, p { margin: 0 0 .7rem; }
h1 { line-height: 1.2; } h2 { margin-top: 1.6rem; }
a { color: #164d9b; text-underline-offset: .14em; }
.plots { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
          gap: 1rem; }
figure, article { background: white; border: 1px solid #c9d6e5; border-radius: .6rem;
                  padding: 1rem; margin: 0; }
figcaption { font-weight: 650; }
svg { width: 100%; height: auto; display: block; }
svg text { text-anchor: middle; fill: #293b52; font: 11px system-ui, sans-serif; }
.grid path { stroke: #d4deea; }
.legend { list-style: none; padding: 0; font-size: .88rem; }
article { margin-bottom: .8rem; }
.source, footer { color: #3b4d65; font-size: .91rem; overflow-wrap: anywhere; }
"""
COLORS = ("#215bc6", "#b44e1e", "#127456")
DASHES = ("", "7 4", "2 4")


def gaussian_intensity(position_m, diameter_m):
    """Peak-normalized 1/e² Gaussian intensity cut for display."""
    return math.exp(-2 * (2 * position_m / diameter_m) ** 2)


def plot_cut(records, wavelength_nm, axis, axis_label):
    # Each cut uses the same fixed spatial and intensity scale.
    def screen_x(position_um):
        return 48 + (position_um + 12) * 304 / 24

    def screen_y(intensity):
        return 155 - intensity * 130

    grid = []
    for position_um in (-12, -6, 0, 6, 12):
        x = screen_x(position_um)
        grid.append(f'<path d="M{x} 25V155"/><text x="{x}" y="174">{position_um}</text>')
    for intensity in (0, 0.5, 1):
        y = screen_y(intensity)
        grid.append(f'<path d="M48 {y}H352"/><text x="28" y="{y + 4}">{intensity:g}</text>')

    curves = []
    legend = []
    for record, color, dash in zip(records, cycle(COLORS), cycle(DASHES)):
        width = record["mode_evidence"]["width"]
        diameter = width["diameter_m"][min(axis, len(width["diameter_m"]) - 1)]
        points = []
        for sample in range(97):
            position_um = -12 + sample * 0.25
            intensity = gaussian_intensity(position_um * 1e-6, diameter)
            points.append(f'{screen_x(position_um):.2f},{screen_y(intensity):.2f}')
        curves.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" '
            f'stroke-width="2.4" stroke-dasharray="{dash}"/>'
        )
        label = escape(record["label"])
        record_id = escape(record["id"])
        legend.append(
            f'<li><span style="color:{color}">●</span> '
            f'<a href="#{record_id}">{label}</a> · {diameter * 1e6:g} µm</li>'
        )

    title = f'{wavelength_nm} nm · {axis_label}'
    return (
        f'<figure><figcaption>{title}</figcaption>'
        f'<svg viewBox="0 0 372 198" role="img" aria-label="{title}, Gaussian intensity illustration">'
        f'<g class="grid">{"".join(grid)}</g>{"".join(curves)}'
        '<text x="200" y="194">Transverse position [µm]</text>'
        '<text x="11" y="91" transform="rotate(-90 11 91)">I / Ipeak</text></svg>'
        f'<ul class="legend">{"".join(legend)}</ul></figure>'
    )


def format_width(width):
    if width is None:
        return "Unprovided for this record"
    dimensions = []
    for index, (axis, value) in enumerate(zip(width["axes"], width["diameter_m"], strict=True)):
        tolerance = width["plus_minus_m"]
        variation = f' ± {tolerance[index] * 1e6:g}' if tolerance is not None else ''
        dimensions.append(f'{axis} {value * 1e6:g}{variation} µm')
    return escape(" / ".join(dimensions) + " · " + width["definition"])


def render_record(record, source):
    evidence = record["mode_evidence"]
    wavelength = record["wavelength_m"]
    band = record["wavelength_band_m"]
    if wavelength is not None:
        wavelength_label = f'{wavelength * 1e9:g} nm'
    elif band is not None:
        wavelength_label = f'{band[0] * 1e9:g}–{band[1] * 1e9:g} nm'
    else:
        wavelength_label = 'Unprovided for a single profile'

    source_links = " · ".join(
        f'<a href="{escape(link["url"])}">{escape(link["label"])}</a>'
        for link in source["links"]
    )
    citations = escape(f'{source["authors"]} · {source["publication"]}')
    if "doi" in source:
        citations += f' · DOI {escape(source["doi"])}'
    if "license" in source:
        citations += f' · {escape(source["license"])}'

    observations = []
    for item in record["observations"]:
        variation = f' ± {item["plus_minus"]:g}' if item["plus_minus"] is not None else ''
        bounds = item["value"]
        unit = item["unit"]
        if isinstance(bounds, list):
            if unit == "m":
                bounds = [length * 1e6 for length in bounds]
                unit = "µm"
            measurement = f'{bounds[0]:g}–{bounds[1]:g}'
        else:
            measurement = f'{bounds:g}{variation}'
        prefix = item.get("comparison", "")
        value = f'{prefix}{measurement} {unit}'
        reported = item["reported_convention"] or value
        kind = item["provenance"].replace("_", " ")
        observations.append(
            f'<li><strong>{escape(item["quantity"])} · {escape(value)}</strong> '
            f'({escape(kind)}) · {escape(item["locator"])}. {escape(item["conditions"])}'
            + (f' Source convention: {escape(reported)}.' if reported != value else '')
            + '</li>'
        )

    preview = record["gaussian_intensity_preview"]
    notes = record["notes"] + ([preview["assumption"]] if preview else [])
    width = evidence["width"]
    if width and width["plus_minus_meaning"]:
        notes = notes + [width["plus_minus_meaning"] + "."]
    kind = evidence["kind"].replace("_", " ")
    items = "".join(f'<li>{escape(note)}</li>' for note in notes) + "".join(observations)
    return (
        f'<article id="{escape(record["id"])}"><h3>{escape(record["label"])}</h3>'
        f'<p>{escape(record["process"])} · {escape(record["material"])} · {wavelength_label}</p>'
        f'<p><strong>{escape(kind.capitalize())}</strong> · {escape(evidence["locator"])}<br>'
        f'{format_width(width)}</p>'
        f'<p>{escape(record["geometry"])}. '
        f'Plane: {escape(evidence["plane"] or "Unprovided")}. '
        f'Polarization: {escape(record["polarization"] or "Unprovided")}.</p>'
        + (f'<ul>{items}</ul>' if items else '')
        + f'<p class="source">{citations}<br>{escape(source["access_notes"])}<br>{source_links}</p>'
        + '</article>'
    )


def render_reference_handoff():
    """Review references without creating or changing a Design input."""
    payload = CATALOG.read_bytes()
    catalog = json.loads(payload)
    records = {record["id"]: record for record in catalog["records"]}
    comparison = [records[record_id] for record_id in
                  ("smf28-ultra-1550", "desmet-fldw-1550", "lee-uncracked-y-1550")]
    cards = "".join(render_record(record, catalog["sources"][record["source_id"]])
                    for record in comparison)
    readiness_cards = "".join(render_record(record, catalog["sources"][record["source_id"]])
                               for record in (records["smf28-ultra-1310"],
                                              records["sun-fldw-55mw-1310"]))
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SMF–Glass Mode Reference · Photonic Architecture Explorer</title>
<style>{REFERENCE_CSS}
nav {{ display: flex; flex-wrap: wrap; gap: .5rem 1rem; margin-bottom: 1rem; }}
.missing {{ padding: .8rem; margin-bottom: .8rem; border-left: 4px solid #b44e1e; background: #fff4ed; }}
section {{ margin-bottom: 1.6rem; }}
</style>
</head>
<body>
<main>
<nav aria-label="Mode Reference navigation"><a href="/">Workspace</a>
<a href="#comparison-1550">1550 nm 비교</a><a href="#readiness-1310">1310 nm 입력 준비</a></nav>
<h1>SMF–Glass Mode Reference</h1>
<p>Actual External Port, Complex Overlap, Total Coupling은 <strong>Uncomputed</strong>입니다.
이 페이지의 곡선은 문헌 Mode Width로 그린 Gaussian Intensity Preview입니다.</p>
<section id="comparison-1550">
<h2>1550 nm · SMF와 LDW 비교</h2>
<p>세 곡선은 같은 µm 범위에서 중심을 맞춰 비교합니다. 각각의 Peak를 1로 정규화했으며,
Desmet과 Lee의 실측 Intensity Image는 아래 출처 링크에서 볼 수 있습니다.</p>
<div class="plots">
{plot_cut(comparison, 1550, 0, "lateral / x cut")}
{plot_cut(comparison, 1550, 1, "vertical / y cut")}
</div>
<p>Corning은 원형, Desmet과 Lee는 축이 정렬된 separable Gaussian의 Intensity를 가정합니다.
그림의 가로·세로 방향은 각 문헌의 축이며 Phase와 World Frame은 미제공입니다.</p>
{cards}
<p><a href="/?entry=smf-glass">1550 nm SMF–Glass 개념 Proxy 열기</a> ·
M7-A 예제의 공개 Width, 가정 Flat Phase, 고정 배치로 Concept Design을 검토합니다.</p>
</section>
<section id="readiness-1310">
<h2>1310 nm · SMF 사양과 Glass Waveguide 실측</h2>
<p class="missing"><strong>Glass Waveguide External Port · Uncomputed</strong> · 공개 강도 자료에는
설계에 필요한 Width 정의, Phase 및 등록된 External Reference Plane이 빠져 있습니다.</p>
{readiness_cards}
<h3>실제 입력을 준비할 때</h3>
<ul>
<li>두 Port의 1310 nm 외부 Mode를 같은 기준으로 확인합니다. 기존 Design 입력은 1/e² MFD와 Wavefront Curvature 또는 Ordinary Complex q를 받습니다.</li>
<li>External Reference Plane의 Position·Propagation Direction과 외부 매질의 굴절률을 지정합니다.</li>
<li>타원형 또는 Astigmatic Mode는 실제 Transverse Axis를 지정합니다. 복소장 자료의 Gaussian Fit과 적용 범위도 확인합니다.</li>
</ul>
<p><a href="/?entry=blank">검증한 Port 데이터로 새 입력 열기</a> · 빈 Workspace에서 내 값을 입력하고 기존 External Port 검사를 통해 Design을 실행합니다.</p>
</section>
</main>
<footer>Catalog {escape(catalog["schema_version"])} · SHA-256 {hashlib.sha256(payload).hexdigest()}</footer>
</body>
</html>
"""
