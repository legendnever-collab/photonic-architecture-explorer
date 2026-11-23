# M6-D Reflector placement sensitivity

Base Main `5b747eead870bcd7b3ba4a4ebd7a043b115aa378`. Baseline CI 43996678002.

## Validation contract

Evaluate the existing M6-C shortlist after nominal design and ranking. Keep the
two frozen Ports, recommendation order and nominal prescriptions. A valid
candidate is traced once at zero perturbation and up to 16 more times. Each
trace starts at the fixed Source with its nominal direction and visits M1 then
M2 before the fixed Target reference plane.

| Cases per candidate | Applied to one reflector at a time |
|---:|---|
| 12 | Translate M1 or M2 by −5 or +5 µm along global X, Y or Z |
| 4 | Rotate M1 or M2 by −1 or +1 mrad about the common sagittal axis through its vertex, positive by the right-hand rule |

Curvature and rectangular half-aperture follow the local surface frame. For
rotation, `n' = n cos(θ) + (s × n) sin(θ)` with fixed unit sagittal axis `s`.
The existing M2 analytic quadratic roots and pointwise normals determine the
two hits and reflection directions. Compare the actual ray to the fixed Target:
signed offset projected onto `t = s × d` and `s`, and signed projected angles
`atan2(k·t, k·d)` and `atan2(k·s, k·d)` for outgoing unit ray `k` and nominal
Target direction `d`. These angles differ from the dimensionless M2 slopes
`(k·t)/(k·d)` and `(k·s)/(k·d)`. Group maxima use transverse offset norm and
the full angle between `k` and `d`. JSON uses metres and radians, UI uses µm
and mrad. Offsets and angles are signed relative to the fixed plane and direction.
The nominal row records the zero-error reference for comparison.

Close the zero-error trace at both vertices and the Target within 1e-10 m
and preserve the 1e-10 direction-slope closure threshold. Keep the existing
forward distance cutoff (1e-9 m), incidence guard (70°), and finite rectangular
aperture check. Stop the candidate sweep on nominal failure. Individual invalid
rays stop with a reason (no forward root, aperture miss, back-face, incidence
guard, unintended interception, invalid Target-plane crossing, or invalid
geometry). Record remaining one-at-a-time cases. Failed cases have no target
error value and group maxima describe successful rays only. A rejected nominal
design has no placement sweep.

Independently verify the two intersections with the existing Newton reference
and check hit coordinates against the rotated local quadratic equations.
Acceptance tolerances are 1e-13 m for position/surface residual and 1e-11 rad for
Target angular agreement on the supported fixtures. Verify local normal and
specular direction against independent 3D vector algebra within 1e-11, and the
flat M2 rotation control against the exact 2θ angular response within 1e-11 rad.
For ± perturbations, verify both signed vectors against Newton independently
and check that the rotation pairs' even residual is less than 10% of the
odd response plus 1e-11 m or 1e-9 rad respectively. Translation pairs can have
near-zero first-order response and a larger even term. Both signs must still
agree individually with the independent reference. A failed rotation reference blocks publishing rotation results.

Perturbed Gaussian Mode Overlap, actual Assembly Tolerance, Package Yield,
Total Coupling and Patentability stay Uncomputed. The existing Target-plane
relative Gaussian sensitivity covers its own imposed arrival offset and slope.
The placement sweep covers exact chief rays for the prescribed local patches.

## Frozen case results

The five nominal chief rays closed. All 60 translations and all 20 sagittal
rotations reached the fixed Target plane inside the two prescribed apertures.
High divergence still fails design at 0.1 rad, with placement and Mode
Overlap Uncomputed. The M6-C output is identical after removing the new
`reflector_placement` report field. Each successful trace records both hits,
their local normals and reflected directions, the fixed-plane crossing,
signed t/s position and angles, and slopes.

| Fixture / Candidate | Role | Path [mm] | Max radius [µm] | Max 3w·κ | Translation max [µm / mrad] | Rotation max [µm / mrad] |
|---|---|---:|---:|---:|---:|---:|
| Equal q / G009-B1 | Recommended | 3.728 | 80.65 | 0.100158 | 5.938 / 8.921 | 2.000 / 2.659 |
| Equal q / G015-B1 | Footprint | 4.000 | 74.58 | 0.079100 | 5.000 / 5.006 | 2.004 / 2.004 |
| Equal q / G036-B1 | Model margin | 20.840 | 296.62 | 0.078205 | 5.002 / 0.883 | 11.317 / 2.000 |
| Different q / G009-B1 | Recommended | 3.728 | 64.43 | 0.088658 | 6.191 / 8.053 | 2.000 / 2.393 |
| Different q / G016-B1 | Model margin | 4.457 | 76.25 | 0.074233 | 6.156 / 3.850 | 2.828 / 2.000 |

Within each group the position and angle maxima can come from different
perturbations. Equal-q G036-B1 reduces the maximum translation angle compared
with G009-B1, from 8.921 to 0.883 mrad, while increasing the maximum rotation
offset from 2.000 to 11.317 µm. Equal-q G015-B1 reduces the angle maxima for
both groups compared with G009-B1 at a similar rotation offset. Both
different-q concepts show the same direction of trade-off between smaller
maximum angle and larger rotation offset. These are geometric comparisons
at the specified one-at-a-time disturbances. The nominal recommendation stands.

The independent Newton, vector reflection and flat 2θ reference tests are in
`tests/test_placement.py`. Tests also separate aperture miss, no forward hit,
back-face, unintended interception, invalid Target-plane and invalid geometry.
The existing one-page Candidate Review retains its nominal content. The live
Workspace and standalone HTML expose placement in a separate collapsed panel;
the engineering JSON carries every case.

## Reproduce

Use a clean checkout or fresh output directories. The CI artifact
`m5f-concept-acceptance-evidence` contains `acceptance.json` with the
summary values, each fixture's `design.html` and `design.json`, and the
existing A4 print evidence.

```bash
python -m pip install -e '.[test]'
python scripts/validate.py
python scripts/validate_m5a.py --output-dir results/runtime-m5a-m6d
python scripts/validate_m5f.py --output-dir results/runtime-m5f-m6d
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install --with-deps chromium
# Install poppler-utils and fonts-noto-cjk for the PDF checks.
node scripts/check_workspace.cjs results/runtime-m5e-m6d results/runtime-m5a-m6d
node scripts/check_m5f_print.cjs results/runtime-m5f-m6d
```
