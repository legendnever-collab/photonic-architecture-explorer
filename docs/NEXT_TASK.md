# M1 handoff / minimal M2 recommendation

M1 model gate: Pass. Keep Draft PR until user review; do not merge automatically.
Before continuing, recover current branch/HEAD, CI and results/validation.json.
The frozen fixture and negative cases must remain reproducible.

Recommended M2: **Fixed architecture applicability and sensitivity**, not more
architectures or optics. Sol is suitable for scoped implementation; use deeper
physics review only if actual Port data invalidate the current domain.

1. Define a non-confidential external Port specification: position/direction,
   wavelength, ambient, both mode radii AND phase, acceptable curvature/aperture
   ranges. Do not substitute a guided-mode index for the external medium.
2. First run domain checks. If actual SSC divergence exceeds the supported range,
   report the minimum missing external-field adapter/reference and stop that
   performance claim. Do not enlarge the paraxial limits to force a result.
3. On this same two-reflector architecture, add small, bounded principal-curvature
   and placement perturbations, preserving Port invariance and classifying
   geometry failures separately from Mode mismatch. A displaced vertex requires
   real ray/surface intersection; never move the Ports to close the path.
4. Before using nominal η to rank real designs, validate finite-beam aberration
   with a bounded bundle of exact rays on the existing local surface model.
   This is the minimum check beyond the M1 vertex limit; do not add a general
   optical CAD, full freeform optimizer or Maxwell engine.

Proposed first checkpoint: recover M1, define M2 input contract and perturbation
budget/acceptance criteria. Implement only after those inputs are concrete.
Physical losses/total coupling/fabrication remain Uncomputed unless separately
specified and validated. No claim about patent novelty follows from M1 or M2.
