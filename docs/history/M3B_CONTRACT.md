# M3-B frozen Inspector scope

2026-11-10 KST. Base PR #4 / 61bafc61d50b0c934e9fa17c4220bb44dbaf5b96.
Main fe730295672047878274d9013edc255b88d16ce2; PR #1→Main, #2→#1,
#3→#2, #4→#3 all Draft/unmerged. PR #4 CI 42705770777 success;
Python 3.11/3.12 artifacts 13712618639 / 13713038062 non-expired (metadata
checked, ZIP not re-downloaded). Baseline rerun: 49 tests and both gates Pass.

Implement Standard Library Python loopback Inspector plus portable static HTML
review from the same renderer. Every evaluation calls existing evaluate_external;
geometry rendering uses existing adapt_external. No optical JS/solver changes.
Local input editing separates Fixed Port boundary data, Reflector Design values
and Package data; submitted changes are new explicit inputs, never auto-fitting.
Static mode is read-only snapshots with precomputed case/projection selection.

Draw Fixed Port positions/directions, actual quadratic patch wireframes, verified
chief paths, supported declared AABBs in equal-scale XZ/XY/YZ projections [mm].
Omitted axis and projection limits must be visible; 2D overlap is not 3D collision.
Input-contract failure may withhold plot; never invent geometry from bad units.
Geometry closure failure must not show a specular chief path. Do not draw Beam
Envelopes in this minimal checkpoint; existing samples remain inspectable.

Separate Input/Geometry/Domain/Bounds/Approximate Overlap/Envelope/Full Package/
Loss/Actual Applicability states. No stale overlap after edits/case switch/invalid
JSON. Preserve provenance, original input and engine result for review.

Eight review controls: synthetic nominal, blank actual, missing phase, bad units,
wrong Target direction, high divergence, bounds failure and package failure.
Add <=12 meaningful tests with subcases plus browser checks at desktop/mobile,
case transitions and valid→invalid→valid local edits. Keep all old sources/tests,
fixtures/guards/benchmark JSON unchanged. No UI polish, extra optics, search,
new physics, Main merge or automatic next checkpoint. Separate Draft on PR #4.
