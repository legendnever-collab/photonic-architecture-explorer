"""Render the literature catalog as an offline, read-only mode comparison."""

import argparse
import hashlib
import json
from html import escape
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from photonic_architecture_explorer.mode_reference import CATALOG, REFERENCE_CSS, plot_cut, render_record

OUTPUT = ROOT / "results/m7r1-mode-library.html"


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
<style>{REFERENCE_CSS}</style>
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
