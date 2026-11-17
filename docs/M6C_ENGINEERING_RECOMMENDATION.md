# M6-C Engineering Recommendation

Base: M6-B Main `7dc868b2b1a8d4531bb6616c962e185f8ab8060f`, Push CI 43994025294.

## Baseline audit

M5-A sorts accepted candidates by overlap deficit (rounded to 12 decimal
places), max 3w·κ, minimum aperture/radius ratio, max projected radius, then path
length. In the fixed equal-q example, G036-B1 (20.840 mm / 0.078205) outranks
G029-B1 (9.825 mm / 0.078239) and G022-B1 (4.993 mm / 0.078426) despite
equivalent normalized overlap. The 4w aperture prescription yields the same
rounded minimum ratio for all three. The legacy order is documented in
[M5-A](M5A_DESIGN_CONTRACT.md) and its archived results.

## Decision policy and acceptance before implementation

1. Keep the existing accepted set, including its Fixed-Port Geometry, Gaussian
   Domain, declared Design Constraint and Package checks. A known violation
   disqualifies the concept. Retain missing-package evidence as Uncomputed.
2. Compare accepted designs using the same rounded overlap deficit as M5-A.
   This bin resolves model calculation ties and makes no claim about physical
   overlap accuracy. The default within the best bin minimizes path length.
   Break ties by smaller max projected beam radius, smaller max 3w·κ, then
   stable ID. Round only these three comparison keys to 12 decimal places in
   their stored units (metres for lengths/radii); preserve reported values.
3. In the best overlap bin, keep distinct-vertex alternatives for the lowest
   max projected beam radius and the lowest max 3w·κ. Select in that order,
   preferring the default ordering on ties. Each alternative must improve its
   objective over every already displayed design by at least one displayed
   bin (0.01 µm or 0.000001). Omit an alternative if no distinct geometry
   qualifies. Within these objectives, the other attributes and short path
   serve as secondary criteria. Do not pad a shortlist with similar designs.
4. Explain which metric drove selection and show its trade-off in path, radius,
   and max 3w·κ. With the unchanged 0.15 limit, lower max 3w·κ implies more
   distance from that one model guard. Aberration, assembly robustness and
   yield require their own validation. A shorter optical path supports an
   early routing comparison. Physical package size requires package geometry.
   The automatic 4w ratio remains diagnostic and does not affect ordering.
5. Gate acceptance on identical inputs, per-candidate physics/guard outcomes,
   candidate membership and rejection counts relative to M6-B. Equal-q and
   different-q must recommend a shortest path within the best overlap bin;
   high-divergence must retain the 0.1 rad rejection with no recommendation.
   Verify metric tie handling and lack of duplicate geometries, representative
   IDs and figures in Workspace/HTML/JSON/A4, and Desktop/Mobile regressions.
   Actual assembly tolerance, package yield, total coupling and patentability
   stay Uncomputed.

## Results

| Fixture | M6-B shortlist, in order | M6-C recommended | M6-C alternatives |
|---|---|---|---|
| Equal q, 56 accepted | G036-B1, G029-B1, G022-B1 | G009-B1, 3.728 mm | G015-B1 (footprint), G036-B1 (model margin) |
| Different q, 60 accepted | G016-B1, G030-B1, G023-B1 | G009-B1, 3.728 mm | G016-B1 (model margin) |
| High divergence | Rejected before search | Rejected before search at the frozen 0.1 rad limit | None |

Both recommended candidates have normalized Gaussian overlap 1.000000.
The equal-q recommendation shortens the old 20.840 mm path by 17.111 mm and
reduces max projected radius from 296.62 to 80.65 µm. Its 3w·κ increases
from 0.078205 to 0.100158, still within the 0.15 guard. G015-B1 reaches
74.58 µm and 0.079100 at 4.000 mm. G036-B1 offers the largest margin to
this guard in the best overlap bin. Its 0.000896 improvement over G015-B1
comes with 16.840 mm of extra path.

For different q, G009-B1 trades 0.014424 of 3w·κ margin for a 0.728 mm
shorter path and a smaller max projected radius (64.43 vs. 76.25 µm).
There is no second footprint alternative because the recommendation
already has the smallest radius in the best overlap bin.

The two versions evaluated 120 equal-q and 116 different-q prescriptions
with exactly matching inputs, per-prescription Adapter outputs and search
ledgers when run with the same interpreter. High divergence stopped
before any prescription evaluation. Reflection, closure, ABCD q transport,
mode overlap and Target-plane sensitivity are checked by the existing
independent references. Use the shortlist to choose a concept for further
engineering. Actual placement tolerance, package yield, loss, total
coupling and patentability are Uncomputed.

## Reproduce

```bash
python -m pip install -e '.[test]'
python scripts/validate.py
python scripts/validate_m5a.py --output-dir results/runtime-m5a-m6c
python scripts/validate_m5f.py --output-dir results/runtime-m5f-m6c
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install --with-deps chromium
# Install poppler-utils and fonts-noto-cjk for the PDF checks.
node scripts/check_design.cjs results/runtime-m5a-m6c
node scripts/check_workspace.cjs results/runtime-m5e-m6c results/runtime-m5a-m6c
node scripts/check_m5f_print.cjs results/runtime-m5f-m6c
```

Use a fresh checkout or new output directories. The M5-F evidence artifact
contains the prior and current shortlists in `acceptance.json`, as well as
each case's HTML, engineering JSON, A4 PDF and `print-evidence.json`.
The archived M5-A contract and results retain their historical policy.
