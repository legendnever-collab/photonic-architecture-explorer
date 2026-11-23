# M2-001 observed results and interpretation

Synthetic M1 input only. Source/Target position, direction and mode never changed.
M1 Gaussian/Geometry kernels and fixture unchanged. M2 adds a separate diagnostic.

| Diagnostic | Observed result | Scope |
|---|---|---|
| Individual principal curvature ±1%, 8 cases | η_mode 0.9994445373–0.9998687191 | Paraxial Mode Matching, not combined tolerance or physical coupling |
| Individual vertex X/Y/Z ±5 µm, 12 cases | Chief-ray transverse miss 0.006234–5.000301 µm; all have direction/position closure Fail | Actual local quadratic patch intersection, fixed Target |
| Off-vertex Gaussian handoff | Uncomputed | No unvalidated overlap for placement cases |
| Flat wavefront-normal fan | Max transverse residual <1.5e-18 m | Linear model control |
| Curved fan ±0.5w | Max transverse residual 0.059644 µm | Exact ray vs vertex linear reference |
| Curved fan ±1w | Max transverse residual 0.380172 µm | Same |
| Curved fan ±2w | Max transverse residual 2.679648 µm | Same |
| Curved fan ±2w | Max slope residual 0.0135432 | Dimensionless slope norm, not exact angle |
| Actual SSC applicability | Uncomputed | Actual external mode, phase and geometry not supplied |
| Total coupling / fabrication / assembly yield | Uncomputed | Ray fan is not a normalized field calculation |

Small numerical miss values can coexist with direction closure failure. Both
position and direction must agree at the fixed Target. Placement results use
surface normals at actual hits rather than aiming each ray through moved vertices.

All 9 rays per extent reached the intended patches and forward Target plane.
Fan maxima are from a 3x3 discrete grid, not bounds over the full aperture.
Uniform RMS is not intensity-weighted RMS. Wavefront-normal rays omit Gaussian
phase-space diffraction; ray spread does not establish Gaussian coupling or
physical throughput. The exact surface used here is the explicit quadratic local
patch, not a full spherical/toroidal/freeform manufacturing prescription.

Independent verification uses Newton iteration for surface intersections versus
production analytic roots, checks surface residual and vector reflection, and
compares finite fans against the existing validated first-order ray powers.
Near-axis residual/extent decreases under successive halving; Flat residual is
roundoff. Existing M1 19 tests plus M2 7 tests all pass. No guard was relaxed.

Engineering judgment: M1's unity paraxial overlap proves a useful ideal reference.
M2 demonstrates measurable finite-footprint nonlinearity on the stated patch,
so that ideal overlap cannot yet rank real finite mirrors. Before implementing
an off-vertex Gaussian handoff, define actual non-confidential external Port
ranges and assess whether this geometric error matters for those modes.
