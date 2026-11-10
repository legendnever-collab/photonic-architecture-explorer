# M2 handoff — Port applicability before further performance claims

M1: Draft PR #1, HEAD 55de4c5f26d3bacc9e22ec64ba385de8acfc4dbe.
M2: feature/m2-bounded-diagnostics, stacked on M1; keep both Draft/unmerged.
Recover exact remote HEAD/CI/artifacts before continuing. Read M2_CONTRACT.md,
M2_RESULTS.md and results/m2_001.json. Run scripts/validate.py.

Implemented: individual curvature ±1%; actual quadratic-patch chief-ray tracing
for ±5 µm individual placement; finite wavefront-normal ray fan and linear
residuals. Independent Newton surface-intersection tests. No extra optics.
M1 fixture/solver remains unchanged.

Key limitation: Curved 2w fan max nonlinear position residual ~2.680 µm.
This is a geometric diagnostic, not a finite-field coupling reference. Placement
Gaussian overlap, total coupling, physical losses, fabrication/yield and actual
SSC applicability remain Uncomputed.

Next recommended checkpoint: external Port applicability decision. Sol can
handle known-input contract/checking. Use Astra for assessing a new off-vertex
Gaussian/field handoff if needed; do not implement that handoff automatically.
Obtain non-confidential Source/Target external MFD_t/MFD_s, phase curvature,
ambient, wavelength, positions/directions and allowed package/curvature ranges.
Use ranges if exact values are unavailable; label estimates explicitly.
If inputs are still unavailable, preserve Uncomputed instead of inventing actual
SSC values. Model-domain rejection is not proof architecture is impossible.

Copyable next instruction:

    Photonic Architecture Explorer — external Port applicability gate
    Recommended Model: Sol Work (Astra only for new physics formulation).
    Recover current M2 Draft PR HEAD, CI and artifacts.
    Read AGENTS.md, docs/NEXT_TASK.md and docs/M2_RESULTS.md.
    Using explicitly provided non-confidential external Port ranges, assess
    divergence/domain and finite-footprint residual significance. Preserve fixed
    Ports and M1/M2 benchmarks. If inputs are absent, list required inputs and
    retain actual applicability as Uncomputed. Propose the smallest next change;
    no topology synthesis, new optics, general solver or Main merge.
