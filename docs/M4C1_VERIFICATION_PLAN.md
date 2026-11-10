# M4-C.1 pre-execution plan

2026-11-11 KST. Base Main `f42a6b1701eeb8c0500092a95e0b4202be86aa8b`.
Written before any new Window calculations. Historical M4-C plan/results stay frozen.

## Decision, scope and budget

같은 Window에서 N만 증가시키면 dx는 감소하지만 Δkx=2π/L는 그대로다.
가장 작은 변경은 기존 tmm/NumPy grid 함수에 optional Window 길이를 전달하는 것이다.
Bin-boundary interpolation을 새로 도입하지 않고 Window convergence를 선택한다.
원래 Gaussian seed, bandlimit, TE symmetry, n1/n2, wavelength, phase, z=0/5 µm,
quadrature x=0/1/2/4 µm, 0.1 rad 경계 및 normalization을 보존한다.
실제 WAFT 또는 두 Reflector 계산으로 확장하지 않는다.

- New ID: M4C1-TE-WINDOW-001. Fixed deterministic sequence L=80,160,320,640,1280 µm.
- At each L, dx=156.25 and 78.125 nm (N=512/1024 through 8192/16384).
- Ten grids maximum; one unchanged continuous quadrature plus independent reflected
  flux integral; <=120 s and <1 GB per complete execution. No adaptive extra windows.
- Store raw complex E/H and spectra separately from legacy M4-C outputs.
- Spatial sampling: compare both dx values at each L on shared x coordinates.
- Window convergence: fixed dx=78.125 nm; compare successive L against continuous
  quadrature, not raw arrays of different domain sizes. Report Δu=λ0/L and cutoff bin.
- Check exact-coordinate complex Ey,Z0Hx,Z0Hz without phase fit, integrated flux,
  RMS sin(theta), flux fraction |theta|>0.1 rad, spatial/spectral flux and power balance.
- Continuous quadrature reuses analytic Gaussian transform and direct Maxwell
  admittances (no FFT or tmm coefficients); independent implementation of the SAME
  planar model, not independent physical validation of a device.

## Frozen success / stop criteria

Preserve historical absolute tail error 0.0277776636 (>0.02), Fail/Stop and all
original thresholds. L=80 µm failure is an expected diagnostic, not an accepted case.

At EVERY L: sampling complex E and Z0H relative L2 <1e-6; R/T/RMS relative change
<1e-6; tail absolute change <1e-6; power residual and spatial/spectral flux error
<1e-10; continuous E/H max error / incident peak <1e-4; continuous T/RMS relative
error <1e-4. Preserve plane-wave, TIR and incident-cut gates from M4-C.

Success requires BOTH final windows (640 and 1280 µm) to meet the original
continuous tail absolute error <0.02 and their mutual absolute difference <0.02.
Independent reflected-flux relative error <1e-4 and continuous power residual
<1e-10 are additional checks. Report the full sequence: no monotonic-convergence
claim, early selection or replacing a failed value with the reference answer.
Stop after this bounded sequence if any required criterion fails; do not relax
thresholds, increase the budget or proceed to actual-device/reflector calculations.

## Execution evidence and external inputs

Run legacy and new controls in fresh, exclusive directories with unique run IDs.
Check child exit code, result creation, run ID, exact checkout SHA, source hashes,
result/raw-array hashes and completion marker. No marker after ImportError/early exit.
Negative checks must reject missing outputs, stale run IDs, wrong HEAD, corrupt
outputs and unexpected exit codes. CI must distinguish expected legacy Stop from
execution failure and new numerical acceptance.

Audit references/m4c_external_field_request.json and supplied files; this request
provides no actual external arrays or reproducible interface model. Keep M4A actual
input, M4B literature Proxy and Synthetic Control distinct. Missing data remain null;
actual Field/Overlap/Total Coupling/Package remain Uncomputed. Resume only with the
non-confidential complex E/H export and metadata or reproducible local facet model
specified by the existing request; reciprocal Target input is separately required.
