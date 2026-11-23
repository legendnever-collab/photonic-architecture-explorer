# M7-R11 pre-execution contract

Base #41 at 7222853b0d84c4fd9a766ee8b6b530f03ee31a3c. Use R8 expansion mirror prescriptions and R6 external fitted Ports in air, R7 package plus the R8 expansion. No optimization. The R10 mechanical deficit at M2 +1 mrad is 0.710287 µm.

Reference v1 uses direct complex128 scalar Helmholtz surface quadrature (NumPy 2.3.5, SciPy 1.17.0, compiled CPU kernel). Use exp(+iωt), outgoing G=exp(−ikr)/(4πr). Launch with the plane Rayleigh–Sommerfeld double layer. For each smooth illuminated quadratic surface use the local tangent-plane physical-optics approximation to a sound-soft (Dirichlet) reflector: reflected single-layer density −2 ∂n E_inc on the finite clear patch, zero elsewhere. Evaluate the actual sag, oriented normal and surface Jacobian. This is a single-pass high-frequency scalar approximation. Edge currents, coatings, back-side reflections and mount solids have no model here. No production q or propagation kernels.

Before the relay, require a propagated waist Gaussian complex-field relative error below 1e−3 against its paraxial solution in a low-NA control, and on-axis complex field error below 1e−4 of unit illumination against the exact circular aperture RS integral. Check reflected sign and density on a flat, wide mirror against the unfolded Gaussian (1e−3). Stop relay execution on control failure.

Nominal first. Midpoint patch quadrature 96, 144, 216 cells per axis, plus a higher-order composite Gauss quadrature at the same physical boundaries. Inspect Target pitch 2, 1, 0.5 µm separately from half-window 12, 24, 48 µm, centred at the fixed Target. Preserve raw complex field and axes. Budget up to 8 nominal transfers, 15 minutes per transfer, 4 GiB working set. Allow one further mirror refinement up to 324 cells per axis if under budget. Report incident normal current through each clear aperture relative to unit incident launch flux and the M2/M1 intercepted flux ratio under the ideal-reflection assumption. Check independently integrated output current and loss ledger on the finite window. Unresolved energy outside that window enters the uncertainty.

Use the R10 absolute budgets of 1e−6 each for grid, window and surface/edge, 2e−6 for independent reference and remainder. Treat observed differences as diagnostics until bounds are substantiated. Record raw values even if unresolved. Only advance to the two poses after nominal applicability, convergence and independent agreement support the gate. Compare η−U to 0.99. Actual coupling remains Uncomputed.

Before the edge-only runs, allocate two of the eight transfers to bisecting and quartering the two boundary cells on each axis at 216 midpoint cells. Interior panels and physical aperture edges stay fixed. This isolates edge sampling from whole-surface quadrature.

Use the eighth transfer as a cross-check on the finest 324-cell midpoint mesh with four subdivisions of its edge cells. This choice followed the midpoint sweep and precedes this cross-check.
