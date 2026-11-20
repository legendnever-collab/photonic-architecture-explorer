# R12 nominal quadrature contract (before execution)

Base e21c165d5dd06f2fe18402ae664bd58287d92e3f. Freeze the R11 scalar PO
boundary, sign, launch, R6 ports, R8 expansion, R7 envelope/guards and R10
50 µm clearance. Use the original R11 controls and regenerate the 324 midpoint
nominal E, derivative and ledger. Stop on a failed control or replay mismatch
(relative field/ledger tolerance 1e-10). No renormalization of M2.

Use tensor composite Gauss-Legendre on the two finite rectangular quadratic
patches (sag, normals, area included), with independently coded vectorized
Green function/receiver derivative for the reflected layers. Compare M2 E and
normal derivative on identical points to the original direct kernel using
separate source quadrature. Compare integrated incident current on M2 using
independently refined receiver nodes. Diagnose phase using total source-to-M1
plus M1-to-receiver path (the separate carrier phases can cancel). Inspect
R11 residual on the same probes as the refined rule. Keep raw signs.

Budget: one 324 midpoint replay; up to 8 nominal mirror pairs, at most 768
nodes/axis, 15 min per pair, 4 GiB working set. Use 8 threads. Start with
composite Gauss orders 6, 8, 10 on 48 panels/axis; allow up to 16. Refine
only the two outermost panels separately; retain interior and exact edges.
Use nested half-windows 24, 48, 96 µm (up to 192 if needed) and pitches
2, 1, 0.5 µm at fixed window. Larger windows may be evaluated on a coarser
pitch if overlap and norm are checked at common pitch. Check cross-refinement.
Preserve M2 and target fields, derivative, coordinates, weights and raw flux.

Keep R10 absolute η budgets: grid 1e-6, window 1e-6, surface plus edge 1e-6,
independent check and remainder 2e-6. Deltas alone cannot bound tails.
Report U only with supported bounds for all terms and investigate persistent
flux excess, including PO boundary error. Stop at nominal if bounds,
applicability or agreement fail. If qualified, evaluate ±1 mrad about M2
vertex, world +Y, within the same budget per pose. Pass only if η−U ≥ 0.99;
below if η+U < 0.99, otherwise unresolved. Preserve unqualified metrics
and actual Total Coupling as Uncomputed.
