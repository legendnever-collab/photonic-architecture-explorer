# M1 validation evidence

Executed on 2026-11-09. `python scripts/validate.py` produces deterministic
benchmark JSON, test logs and a source/fixture SHA-256 manifest. Execution runtime
and NumPy version are stored in `results/validation.json`. CI repeats the same
command on Python 3.11 and 3.12 and uploads the reports.

| Requirement | Independent reference | Acceptance |
|---|---|---|
| Free-space Gaussian | Closed w(z)/R(z), air and n=1.45; sampled Fourier Fresnel propagation at two grids/windows | Field overlap with analytic profile 1 to 1e-11; power 1 to 1e-12 |
| Flat reflection | Euclidean reflection-law checks, handed frame and tangential parity; unfolded path analytic q | Unit direction, equal angles, correct output width |
| Curved reflection | Exact quadratic-surface ray/normal reflection, central differential at 10/5 nm | Principal powers within 2e-5 m^-1 at 0/15/45/65 degrees; concave/convex/flat |
| Curved q transformation | Sampled quadratic phase mask + Fresnel propagation | Profile overlap 1 to 1e-10 |
| Full relay | Independent sampled fields through 1–2–1 mm path, fixed numerical phase powers | Flat/Curved/spherical control η agreement to 1e-10 |
| Mode Overlap | Identity, size mismatch, offset/tilt, defocus; explicit complex-field quadrature at two grids | η agreement to 1e-12 or tighter |
| Normalization/coordinates | Integrated power at every benchmark stage, generic rigid rotation/translation, reflection parity | Power conserved to 1e-12; world-frame invariant result |
| Stability/rejection | Underflow retains log/dB; invalid q/NaN/Inf, wrong port/normal, mismatched medium, skew/roll, grazing, high NA, footprint, aperture | No stale overlap for invalid/out-of-domain design |

19 test methods pass, with parameterized subcases within methods.
Numerical tests call production code only for the value being compared;
reference Fresnel, phase-mask and exact-surface reflection kernels are separate.
The reference phase-screen validation proves quadratic/paraxial implementation,
not the accuracy of a real finite curved mirror or full device coupling.

Observed M1-001 results:

| Case | Geometry | Model domain | η_mode | Output w_t / w_s (µm) | Output 1/R_t / 1/R_s (m^-1) |
|---|---|---|---:|---|---|
| Flat | Pass | Pass | 0.01301922494 | 208.646401 / 139.512358 | 249.632465 / 248.150403 |
| Curved | Pass | Pass | 1.00000000000 | 8.000000 / 12.000000 | ~0 / ~0 |
| Spherical control | Pass | Pass | 0.38896880846 | 25.834511 / 28.132345 | 1223.759311 / -894.813467 |

An initial negative test using curvature 3000 m^-1 triggered a geometric
unintended interception before the intended footprint-domain guard. The design
was correctly rejected; the test was classified as Geometry Fail, and a separate
900 m^-1 case isolates Model Domain Fail. No frozen threshold was changed.

M1 completion is limited to a physical specular chief path, independently
validated paraxial Gaussian transformations, and clearly distinguishable
curvature effects. Actual SSC↔Glass total coupling, finite-beam aberration,
manufacturability and alignment yield remain Uncomputed.
