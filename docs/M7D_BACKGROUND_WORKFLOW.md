# M7-D — Local Background Near-Match Workflow

Base Main `2094eca2dfbee359a18930d328525eaa84ac2305` contains user-authorized
M7-C #28. Follow [M7-C's contract](M7C_NEAR_MATCH_WORKFLOW.md), Product Charter
and roadmap Tracks A/D. This milestone connects the frozen Near-Match search to
one default Workspace Design action without changing the exact solver or guards.

## Contract fixed before implementation

- Preserve exact-q public API, Fixed Ports, all kernel/Adapter guards and M6-C
  selection. Only Completed exact search with zero accepted candidates qualifies.
- Extract the M7-B/M7-C search and independent numerical checks for reuse in an
  installed local worker. Preserve every bound/seed/generation and the 600 s cap.
  No geometry reduction, retry expansion, threshold bin change or fixture lookup.
- Keep at most one active subprocess per Workspace. Cancel the previous job before
  starting a new immutable snapshot. A watchdog enforces timeout/crash handling.
- Match job ID, server-issued revision and input SHA for polling/cancel/publication.
  Editing invalidates the displayed result immediately, cancels the job and makes
  late responses inert. Interrupted work publishes no recommendation or exports.
- Retain exact evidence, search policy/cost, provenance, independent checks and
  candidate/figure traceability. Display Near-Match and numerical guard margins in
  the shared report/A4. A model guard margin is not a physical tolerance.
- Install the pinned NumPy/SciPy worker dependencies with the application. Missing
  dependencies/worker errors are execution failures, not no-candidate conclusions.
- Validate Frozen exact outcomes, real SMF–Glass worker, cancellation/retry/input
  edits, late responses, timeout/crash, Desktop/Mobile and HTML/JSON/A4 identity.
  Physics kernels and exact baseline retain numerical equality. Actual field,
  assembly tolerance, yield, Total Coupling and Patentability remain Uncomputed.

## Use and reproduce

```bash
python -m pip install -e '.[test]'
pae-workspace
# Existing regression / numerical checks:
python scripts/validate.py
python scripts/validate_m7c.py --output-dir results/runtime-m7c-m7d
# Browser, real installed worker, exports and one-page A4 (Chromium/poppler/fonts required):
node scripts/check_m7d.cjs results/runtime-m7d-review
```

Open the printed loopback URL. Choose **SMF–Glass Proxy**, inspect the explicit
Gaussian assumptions, and press **Design**. Exact-q is evaluated first. When
eligible, a new page shows progress and **취소** while the inputs stay editable.
The completed result reuses the ordinary candidate inspector, Mode Match,
Sensitivity, HTML/JSON export and A4 summary. Source and Target are immutable
within each run. Near-Match does not force output q to equal Target q.

Editing hides the old report/exports immediately and requests cancellation.
Design after an edit or cancellation creates a new ID and Revision. No stale
worker result is published into a changed page. Timeout/failure/cancellation
withholds the report and offers another explicit Design; there is no automatic
retry, expanded budget or cached fixture result. Known domain/missing-input
failures retain their exact-path report, without starting a worker.

## Implementation and evidence contract

`near_match.py` is the extracted orchestration/generation; independent NumPy ABCD
and complex quadrature live in `near_match_reference.py`. The old M7-B/M7-C CLI
entry points delegate to these modules and retain their reference-case checks.
`design_two_ports`, Gaussian, Geometry, Solver and External Adapter kernels have
no changes. The historical M7-C all-source fingerprint assertion is narrowed to
these five protected kernels for the integration replay; UI/source fingerprints
are still recorded per execution, and numerical comparisons retain all 36 rows.

`workflow_jobs.py` runs one isolated installed `workflow_worker` subprocess at a
time, with a 600 s watchdog. It records a private immutable request, atomic progress,
source hashes and terminal numerical evidence. Cancellation is cooperative; after
0.5 s an unresponsive child is terminated and after 2 s killed. A replacement waits
for the old process to exit. Workspace shutdown reaps children. At most 16 recent
job identities remain queryable; runtime directories are private and temporary
for the normal app. Engineering exports retain the input, ID/Revision, policy,
counts, exact search evidence, candidate prescriptions and independent checks.

The existing loopback Host/Origin checks cover the status/cancel routes. A poll or
cancel must match all identity fields. The UI separately checks ID, Revision and
SHA before accepting a response. Per-run source changes, numerical verification
failure, crash and identity mismatch prevent publication. Guard readings and
limit-minus-reading values are displayed as diagnostics, never as manufacturing
tolerances or an overlap-error bound. M6-C ranking stays unchanged; only G036-NM
is in the best observed overlap bin for this Proxy. 0.90 remains the M7-B concept
criterion, not a product specification or new recommendation interval.

## Acceptance

- `test_workflow_jobs.py` exercises real process timeout, crash, replacement order,
  immutable request, wrong identity, exact-path replacement and stale input refusal.
- `check_m7d.cjs` uses the real HTTP Workspace/worker: Desktop cancellation, Mobile
  input edit, deliberately injected delayed-response control (transport test only),
  fresh-ID retry and a full SMF–Glass run. It compares all 36 rows with M7-B, checks
  responsive HTTP during computation, Desktop/Mobile output, fixed ports and
  independent checks, HTML/JSON identity and one-page A4 with SHA and candidate ID.
- CI retains the prior Frozen exact cases, Browser/print checks and M7-C replay;
  `m7d-background-workflow-evidence` contains the new reports, raw workers, exports,
  PDF, screenshots and acceptance JSON. Exact HEAD/CI/artifact are recorded in the PR.

## Next instruction — M7-E / Sol Work

Recover Main and the M7-D Draft HEAD/CI/artifacts. Review the integrated default
Two-Port path on the three Frozen cases and the SMF–Glass Proxy, then prepare a
small distributable user-review package with its dependencies and source/input
provenance. Address only reproducible workflow/distribution issues. Preserve
physical guards, ranking and Uncomputed claims; do not add new topology or solver.
Submit a separate Draft PR with exact HEAD, CI, artifact and user review steps.
Main merge requires separate approval.
