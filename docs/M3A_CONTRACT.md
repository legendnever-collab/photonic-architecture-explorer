# M3-A frozen implementation scope

2026-11-10 KST. Base PR #3 / 17bd1ad6bfa5715f6371fe0e41f52a6d1a93e199.
Recovery: Main fe730295672047878274d9013edc255b88d16ce2; PR #1/#2/#3
Draft/unmerged, base stack unchanged; PR #3 exact-HEAD CI 42702995771 success,
Python 3.11/3.12 artifacts 13713185292 / 13712251959 non-expired. Metadata and
job steps checked; ZIP contents not re-downloaded. Baseline rerun: 32 tests OK,
M1 benchmark gate Pass; existing m1/m2/m25 report JSON unchanged.

Implement external record adapter and classified result only, Standard Library.
Exactly two explicit vertex quadratic-patch Reflectors; no new optical physics.
Preserve M1/M2/M2.5 kernels, fixtures, guards and their tests. Add independent
input-conversion and adversarial geometry/result tests, a synthetic external case
and JSON CLI evidence. No actual company inputs, no UI/optimizer/handoff.

MFD+phase and ordinary q alternatives; validate redundant supplied mode values.
Strict supported SI units, common frame, external reference planes and explicit
scalar-ignored polarization; provenance and uncertainty retained in snapshots.
No default real Port/waist/ambient/package. Missing input -> Uncomputed;
invalid/unsupported optical domain -> Fail. Unknown geometry/loss is not zero.

Package support: world AABB volume, reflector envelopes and keepout boxes only.
Check entire quadratic patch extent within declared body envelope, body/volume
containment, envelope pairs/keepouts and chief-ray/keepout intersection. Report
these as envelope checks; full finite-beam/support/fabrication clearance remains
Uncomputed even if envelope checks pass. Unsupported solids -> Uncomputed.
Known constraint or package failure withholds published normalized overlap.
Missing package/bounds does not invalidate an otherwise computed paraxial
optical diagnostic; result must explicitly retain conditional scope.

Success: frozen regression passes, input-to-engine equivalence, fixed Ports and
snapshots survive roundtrip, non-waist phase preserved, independent q conversion,
missing/bad phase/unit/basis/plane/high divergence/bounds/volume/collision cases
classified correctly, no overlap for invalid/uncomputed optical inputs.
New tests bounded to <=20 methods with subcases; no parameter search. Separate
Draft PR on PR #3, exact-head CI/evidence, M3-B proposal and copyable order.
