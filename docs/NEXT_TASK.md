# M2.5 handoff → M3-A

M2.5 결과: docs/M25_ASSESSMENT.md, External Contract: docs/EXTERNAL_PORT_CONTRACT.md.
Actual applicability / total coupling / package feasibility = Uncomputed.
Path B is the development-path decision; no claim a particular SSC requires it.

Recommended: Sol Work for adapter/geometry/result boundary. A new off-vertex
physics formulation is a separate Astra checkpoint, not automatic M3 scope.
Stack: M2.5 → M2 Draft PR #2 → M1 Draft PR #1 → Main. No merges authorized.
Recover exact remote SHA, CI and evidence artifacts before continuing.

## Copyable work order

```text
Photonic Architecture Explorer — M3-A
Recommended Mode: Sol Work
Mission: External Input Adapter · Fixed-Port Geometry · Result Contract
Repository: https://github.com/legendnever-collab/photonic-architecture-explorer
Base: latest M2.5 Draft PR on assessment/m25-external-port; recover exact HEAD first.

Read AGENTS.md, docs/EXTERNAL_PORT_CONTRACT.md, docs/M25_ASSESSMENT.md and
M1/M2 frozen contracts. Recover Main/stacked PRs/CI/artifacts; rerun validation.
Preserve all validated kernels, fixtures and guard values. Do not merge Main.

Implement the smallest UI-independent adapter from the external Contract to
existing immutable Port/Reflector/evaluate. Explicit MFD+phase OR complex q;
validate both if both supplied. No default waist, actual mode, ambient or package.
Validate units/frame/reference plane/polarization assumptions/provenance. Do not
accept guided n_eff as external ambient. Missing inputs remain Uncomputed.

Use supplied non-confidential inputs if present, otherwise synthetic controls
and the blank sheet. Keep actual applicability Uncomputed without real inputs.
Separate Geometry, Gaussian domain, approximate normalized Mode Overlap,
package feasibility and physical losses. Never create total coupling from overlap.

Support exactly two coplanar aligned reflectors. Define vertices with source and
backward-target axis distances, or validate explicitly supplied vertices. Check
fixed-port closure and declared curvature/aperture/position bounds. Implement
only a bounded world-AABB/explicit-envelope package representation with honest
scope: unsupported solids or absent envelopes -> package feasibility Uncomputed;
point containment alone must not become full-clearance Pass. No optimizer.

Run independent controls for phase/q conversions, fixed Port invariance, invalid
units/axes/high divergence, missing input, bounds failures, and no performance on
invalid/uncomputed physics. Reuse existing evaluate; do not implement off-vertex
handoff, finite-field propagation, extra optics or new topology synthesis.

After adapter/result gates pass, propose a minimal M3-B 2D inspector with fixed
ports, chief path, surfaces and separate state labels. Do not build the UI in M3-A.
If new physics is needed, preserve evidence and propose a bounded Astra task.

Create a separate Draft PR stacked on M2.5. Submit exact SHA, tests, CI/artifacts,
unchanged baseline evidence, remaining limits and the next copyable work order
in the chat. No Main merge or automatic M3-B start.
```
