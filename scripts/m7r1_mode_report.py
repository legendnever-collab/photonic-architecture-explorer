"""Render the literature catalog as an offline, read-only mode comparison."""

import argparse
import hashlib
import json
import math
from html import escape
from itertools import cycle
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references/m7r1/mode_references.json"
OUTPUT = ROOT / "results/m7r1-mode-library.html"
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


def render(catalog_bytes):
    catalog = json.loads(catalog_bytes)
    records = catalog["records"]
    shown = [record for record in records if record["gaussian_intensity_preview"] is not None]
    controls = [record for record in shown if record["wavelength_m"] == 1.31e-6]
    comparisons = [record for record in shown if record["wavelength_m"] == 1.55e-6]
    plots = (
        plot_cut(controls, 1310, 0, "circular cut")
        + plot_cut(comparisons, 1550, 0, "lateral / x cut")
        + plot_cut(comparisons, 1550, 1, "vertical / y cut")
    )
    cards = "".join(render_record(record, catalog["sources"][record["source_id"]]) for record in records)
    state = catalog["actual_external_port"]
    title = escape(catalog["title"])
    digest = hashlib.sha256(catalog_bytes).hexdigest()
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ margin: 0 auto; padding: 1.5rem; max-width: 72rem; color: #142239;
        background: #f9fbfe; font: 1rem/1.5 system-ui, sans-serif; }}
h1, h2, h3, p {{ margin: 0 0 .7rem; }}
h1 {{ line-height: 1.2; }} h2 {{ margin-top: 1.6rem; }}
a {{ color: #164d9b; text-underline-offset: .14em; }}
.plots {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
          gap: 1rem; }}
figure, article {{ background: white; border: 1px solid #c9d6e5; border-radius: .6rem;
                  padding: 1rem; margin: 0; }}
figcaption {{ font-weight: 650; }}
svg {{ width: 100%; height: auto; display: block; }}
svg text {{ text-anchor: middle; fill: #293b52; font: 11px system-ui, sans-serif; }}
.grid path {{ stroke: #d4deea; }}
.legend {{ list-style: none; padding: 0; font-size: .88rem; }}
article {{ margin-bottom: .8rem; }}
.source, footer {{ color: #3b4d65; font-size: .91rem; overflow-wrap: anywhere; }}
</style>
</head>
<body>
<main>
<h1>{title}</h1>
<p><strong>Actual external Port: {escape(state["status"])}.</strong> {escape(state["reason"])}</p>
<section>
<h2>Gaussian intensity illustrations</h2>
<p>Each cut uses the published nominal width under the stated Gaussian assumptions.
The cuts are centered and peak-normalized. Phase, overlap and coupling are uncomputed.
Axes here follow the source labels, with no world-frame mapping.</p>
<div class="plots">{plots}</div>
</section>
<section><h2>Literature evidence</h2>{cards}</section>
</main>
<footer>Catalog {escape(catalog["schema_version"])} · SHA-256 {digest}</footer>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(CATALOG.read_bytes()), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
