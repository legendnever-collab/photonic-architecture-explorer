# Photonic Architecture Explorer — Product Charter

**Status:** Standing product directive, effective 2026-11-14. It remains in effect until the user explicitly changes it. This document records user intent and the engineering direction; it does not claim any unimplemented feature is available.

## End goal

Given information describing two **fixed optical ports**, autonomously explore, synthesize, evaluate, and explain optical interconnect architectures useful for early engineering R&D and patent-oriented concept development. The output must be a short, evidence-backed set of buildable/plausible candidates, or a clear explanation of why such candidates cannot yet be determined. This is a **design explorer**, not merely an analyzer for a manually selected pair of mirrors and not a patentability opinion.

## User interaction contract

1. **Two-port-first.** The primary workflow starts with Port A and Port B. Request only information intrinsically needed for a meaningful physical problem: reference-plane position, propagation direction, wavelength and field/mode characterization. Offer simple import/examples for complex fields.
2. **Minimal user burden.** Never make the user choose solver, topology, number of mirrors, optimization scheme, Gaussian conventions, or other implementation decisions in the default journey. Reasonable technical strategies and parameterizations are the engineering agent's responsibility.
3. **Progressive disclosure.** Show a clear recommendation, why it works, relevant limitations and alternatives first. Hide advanced controls and diagnostic metadata behind optional inspection; no sprawling forms or button-heavy UI.
4. **Autonomous engineering ownership.** The engineering agent selects the staged roadmap, modeling and test strategy, algorithms and internal defaults. Do not repeatedly ask the user to arbitrate engineering design choices. User review should emphasize practical usability and conceptual relevance.
5. **No invented device facts.** Do not fill unknown real E/H fields, phase, loss, index, geometry, clearances or fabrication constraints with fabricated measurements. For concept-only screening, transparent synthetic/default assumptions are allowed but must be prominently marked and never mistaken for verified product feasibility.
6. **Graceful missing inputs.** When package, process, tolerances or actual field data are missing, still provide the most useful bounded conceptual design supported by evidence; separately classify unresolved engineering validation. Ask only when an essential user-owned fact blocks the next useful step.
7. **Result-oriented criteria.** Favor automatic candidate generation, ranked comparison, clear physical reasons, compact visualization, and exportable design records. A growing set of reference solvers and tests does not alone qualify as product progress.
8. **Guarded physics.** Fixed ports never move to improve the answer; preserve verified applicability checks, independent numerical validation, provenance, and separation between normalized overlap, interface losses, total coupling, package, process and patentability. A domain failure in one approximation does not prove an architecture impossible.
9. **Scope discipline.** Ship a narrow, credible two-reflector Gaussian-domain design loop before considering broader topology classes or actual electromagnetic field integration. Expand physics only when supported by concrete use cases, independent reference evidence and error budgets. Avoid a monolithic Maxwell solver and generalized UI.
10. **Change control.** This charter is a stable user directive. Do not change it based on inferred preferences, arbitrary assistant opinions, milestone convenience or intermediate engineering discussions. Only an explicit user instruction changes it. Maintain staged delivery and the existing repository safety/integration controls.

## First meaningful release acceptance

With two immutable, sufficiently characterized ports and clearly labeled supplementary concept assumptions, the user can invoke **Design** once. The tool automatically generates one or more physically admissible two-reflector candidates if possible, visualizes the fixed optical path and surfaces, evaluates each only within the verified model domain, ranks them based on transparent criteria, and explains why candidates are accepted/rejected. Where no valid candidate exists, it explains what is unresolved or outside model scope without manufacturing performance numbers. The user need not manually specify reflector vertices, normals, curvatures or optimizer settings to start the exploration.

## Development priority

(1) two-port-first design workspace; (2) bounded two-reflector candidate generator; (3) transparent ranking and sensitivity; (4) actual-field integration when non-confidential evidence is available. Existing M1–M4 work remains a validation foundation, not the definition of product completion.

## Boundaries

- This charter does not authorize disclosure of confidential company data.
- Patent-oriented exploration means generating and comparing technical concepts, **not** assuring novelty, freedom to operate or grantability.
- Preserve existing GitHub draft-PR and main-merge controls unless explicitly superseded.
