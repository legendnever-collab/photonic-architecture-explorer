# M5-A bounded autonomous two-Port design — pre-implementation contract

2026-11-17 KST. Base PR #12 c1525d7750476d03f675feee12a3198b1a76c02f.
PRODUCT_CHARTER is unchanged. M4-C.1/M4-D are separate actual-field tracks.

## Algorithm and budget

Input: only the existing explicit Source/Target records, wavelength, external ambient
and common coordinate convention; optional existing Package records. No user mirror,
curvature, aperture, solver or search controls. Phase is required via MFD+C or q.
Reuse the Adapter's Port reader and frozen Engine; generated prescriptions enter the
same evaluate_external path as manual designs. No Target fitting or Port movement.

Let delta=T-S, D=|delta|. M1=S+a*dS, M2=T-c*dT. Positive a,c come from a deterministic
set: D times {1/8,1/4,1/2,1,2}, |delta.dS|/2, |delta.dT|/2, and half the transverse
Source-to-Target separation. Drop values <1e-9 m and deduplicate relative to D at
12 decimal digits. At most 8x8 geometries, 4 real power-branch combinations each:
**256 candidates maximum**; exhaust this set, no retries/expanded search. Reject
coincident Ports, zero middle segments, noncoplanar/rolled frames and zero deflections.
Illuminated normal=unit(d_out-d_in); Engine independently checks reflection and closure.

Per axis qa=qSource+a, qb=qTarget-c, v=Im(1/qa), w=Im(1/qb), b=|M2-M1|.
Real power solutions satisfy (1+b*x)^2=v/w-(b*v)^2, with x=Re(1/qa)-P1.
If the discriminant is negative, no exact match in this geometry/axis is admitted.
P1=Re(1/qa)+(1-sign*sqrt(discriminant))/b;
P2=Re(1/(1/(1/qa-P1)+b))-Re(1/qb).
Transform back to surface curvatures using existing P_t=2κ_t/cosθ, P_s=2κ_s*cosθ.
The backpropagated qb is an algebraic matching condition, not negative-distance physical
propagation. Both real branches per axis are considered; no generic optimizer.

Automatic half-apertures = 4 times incident projected Gaussian radius at each mirror,
explicit **concept prescriptions**, not supplied/measured manufacturing capability.
No backing, package volume, empty keepouts or clearance values are fabricated.
All frozen incidence/divergence/footprint/aperture/patch-obstruction guards still apply.
Package failures withhold overlap via the existing Adapter; missing Package remains
Uncomputed and the optical candidate is labeled Conceptual Geometry.

Dedup by generated a/D,c/D and κ*D rounded to 12 decimals; deterministic iteration IDs.
Return at most 3 valid representatives, distinct geometries preferred over another power
branch of the same vertices. Keep rejected counts/reasons and a compact deterministic
attempt ledger. Absence of a valid candidate means **No candidate in this bounded exact-
matching family**, not global physical impossibility or proof against approximate matches.

## Ranking and acceptance

Only Geometry/Domain valid candidates without known declared constraint failure qualify.
Lexicographic, no weighted score: overlap deficit rounded at 1e-12 numerical resolution;
smaller max 3w footprint-curvature slope; larger minimum aperture/radius ratio (rounded
at 1e-12 to avoid artificial roundoff ranks); smaller maximum projected beam footprint;
shorter total path; available declared package evidence as final tie criterion; stable ID.
All ranks disclose values. Two mirrors/quadratic prescription is fixed simplicity.

Acceptance: M1 relay geometry/powers/q reproduced in generated family without importing
its reflector values; Source/Target record invariance; direct reflection/closure;
independent NumPy ABCD and scalar Fresnel propagation on accepted designs; negatives
for missing phase, invalid directions, degenerate/noncoplanar/high-divergence inputs,
no-real-power matching and explicit Package rejection; deterministic reruns/manual
Adapter equality; static report JSON/visible result consistency and browser checks.
No guard relaxation. Report field/total coupling/fabrication/yield/patentability limits.
Runtime budget: <=30 s for the frozen example on CI, independent validation <=120 s.
If no valid example is found, record the failure and stop; do not expand the bounds.
