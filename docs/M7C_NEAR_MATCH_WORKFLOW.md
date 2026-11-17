# M7-C — Near-Match Workflow Integration Design

Base Main `6ef261b2eb3bba5d24bf98c986ced876aee66cfc` contains #25, #26 and #27.
This milestone implements an executable **integration trial**, then specifies the
smallest production handoff. The default Workspace and production solver are not
connected to the trial yet. Follow [Product Charter](PRODUCT_CHARTER.md),
[Product Vision](PATENT_ORIENTED_PRODUCT_VISION.md) and roadmap Tracks A/D.

## Frozen trial contract — before implementation

1. Run the existing `design_two_ports` first. Keep its exact result unchanged when
   it returns a candidate. Start Near-Match only when input prechecks passed and
   the exact search is `Completed` with zero accepted candidates. Missing phase,
   invalid/skew/rolled/high-divergence inputs and pre-search failures cannot fall
   through to an approximate calculation.
2. Reuse M7-B's `make_prescription`, full `evaluate_external`, power bounds,
   4w concept apertures, differential-evolution settings and seed 7100+geometry.
   Do not reduce geometries, generations or population. Use the current general
   `distances` rule (at most 64 geometries); reject degenerate or out-of-incidence
   geometries before prescription construction. The M7-A case stays at 36.
   Maximum calls = geometry count ×32×121, at most 247,808. Runtime limit 600 s
   for the whole trial. These are execution bounds, not convergence guarantees.
3. Keep each geometry's best valid observation. Use the existing `ranking` and
   `select_concepts` unchanged. Overlap >=0.90 is only the M7-B concept criterion;
   it does not define a new ranking bin, acceptance guard or product requirement.
   Infer no alternative when the unchanged best-bin policy supplies none.
4. Keep ports, wavelength, external medium and package records unchanged. Known
   constraint failures and non-Pass geometry/domain results withhold overlap.
   Validate the three highest-overlap observations and any displayed candidate
   with M7-B's independent ABCD, closure, two-grid field integral and surface
   checks. A numerical check failure invalidates the whole trial result.
5. Retain exact-search evidence, per-geometry counts/termination, rejected reasons,
   input snapshot/SHA, algorithm/seed/settings, candidate ID, generated assumptions,
   file/version hashes and guard readings. Store exact result separately from the
   trial recommendation. Write fresh output directories; no result-cache reuse.
6. Trial states: Running, Succeeded, NoCandidate, NotNeeded, Ineligible, Cancelled,
   TimedOut, Failed. Check cancellation/deadline between exact search and fallback,
   before every Adapter evaluation and before publication. Publish no candidate
   for interrupted/failed execution; partial progress is evidence only. A retry
   uses a fresh run directory and the same frozen policy, not enlarged bounds.
7. Prototype CLI takes a Two-Port JSON, output directory and optional cancellation
   file. No user topology, optimizer or power controls. A future Workspace uses
   the same single Design action with a background worker; do not keep its HTTP
   request blocked for the observed ~75 s. See production handoff below.

## Validation plan

- Compare the complete exact result for equal-q, different-q and high-divergence
  Frozen cases; measure trial overhead and assert that Near-Match was not invoked.
- Run M7-A through the full 36-geometry trial. Compare all best overlaps and
  counts with committed M7-B evidence (overlap absolute tolerance 1e-10), preserve
  input SHA and reuse the independent checks. Record elapsed time and ranking.
- Check missing phase, cancellation during search, timeout, numerical failure,
  no-candidate termination and fresh-output enforcement. Interrupted output must
  contain no recommended candidate or displayed overlap.
- Existing regression and validation gates remain required. Actual Applicability,
  Assembly Tolerance, Package Yield, Total Coupling and Patentability remain
  Uncomputed. M6-E Off-Vertex Field Reference remains Not Ready.

## Reproduce and review

```bash
python -m pip install -e '.[test]' -r requirements-m7c.txt
python scripts/validate_m7c.py --output-dir results/runtime-m7c-review
# A single two-Port input, with no search controls:
python scripts/m7c_workflow_trial.py examples/m7a_smf_glass_proxy.json \
  --output-dir results/runtime-m7c-single --cancel-file /tmp/pae-m7c-cancel
```

Open `trial.html` in the single-run directory. It reuses the existing geometry
and Mode Match figures, labels the trial and assumptions, and embeds the same
Engineering JSON as `trial.json`. Create the cancellation file from another
process to stop a run; use an absent file for a fresh retry. A pre-existing output
directory is refused. `progress.json` contains only diagnostic partial evidence.
Only a terminal `trial.json` with `Succeeded` or `NotNeeded` supplies a result.
`acceptance.json` records Frozen result equality, the 36-layout M7-B comparison,
numerical checks, cancellation and source fingerprints. CI uploads these files
in `m7c-workflow-trial-evidence`; optional NumPy/SciPy versions are pinned there.
Production installation continues to use its existing dependencies.

## Observed trial result

The local full trial used 124,160 Adapter calls: 95,533 valid evaluations (with
revisits), 26,496 first divergence failures and 2,131 first unintended-reflector
interceptions. All 36 per-geometry call/count/termination/overlap records matched
M7-B. The top three passed the independent checks. M6-C selected only G036-NM,
overlap 0.9999366495865395, path 20.839734 mm, max projected radius 558.024 µm.
Its footprint–curvature margin is 0.00000133825. No new ranking bin was introduced.

| Case | Trial state | Result | Observed local time [s] |
|---|---|---|---:|
| Equal q | NotNeeded | Exact result unchanged, G009-B1 | 0.128 |
| Different q | NotNeeded | Exact result unchanged, G009-B1 | 0.126 |
| High divergence | Ineligible | Exact pre-search rejection unchanged | 0.00084 |
| SMF–Glass Proxy | Succeeded | Same 36 search summaries as M7-B; G036-NM | 205.208 |

The local trial cost was higher than M7-B's earlier ~75 s observation. These
measurements are from different runs; they do not isolate orchestration overhead
or provide a runtime guarantee. Exact-path timings likewise have interpreter/load
variation. Preserve the 600 s cap and use a responsive background worker rather
than making the Workspace wait on a synchronous POST. Search reduction was not
attempted. Cancellation after the first real geometry withheld the recommendation.
HTML and JSON carry identical results and numerical evidence.

[Committed local summary](../results/m7c_workflow_trial.json) retains the local
execution fingerprint before publication-provenance checks were strengthened.
The final CI job replays the full search from its published HEAD and uploads
all raw reports. CLI provenance is captured before execution; source or frozen
contract changes during a run invalidate publication. The summary's local HEAD
identifies the earlier local execution, not the published PR commit.

| Milestone criterion | Evidence and limits |
|---|---|
| Physics | Unchanged Gaussian kernels/guards; M7-B numerical result reproduced; actual field and off-vertex applicability unresolved |
| Usability | One Two-Port trial invocation, exact-first decision and cancellation tested; default Workspace integration is M7-D |
| Patent Utility | Existing geometry and intensity/relative-phase figures retain input SHA, candidate and assumptions; no novelty conclusion |

## Minimum production handoff — M7-D proposal

The trial is deliberately outside the production import path. Its orchestration
is the reference for the following small implementation, not a new physics model.

| Trigger / state | Default Two-Port workflow |
|---|---|
| Design | Freeze validated input snapshot, revision and SHA; one action, no solver choice |
| Exact result computed | Show the existing report unchanged; no optimizer is invoked |
| Exact result ineligible | Explain missing input/domain failure and withhold candidates |
| Eligible zero-accepted result | Start one isolated local background worker; show progress and Cancel |
| Search / independent checks running | Keep inputs responsive; suppress previous recommendation and exports |
| Completed valid trial | Publish only for matching job ID, input revision and SHA; use M6-C selection |
| NoCandidate | Explain the finite search outcome; no physical-impossibility claim |
| Cancelled / TimedOut / Failed / crashed worker | Withhold recommendation/export; retain diagnostics; offer explicit retry |

Reuse `ThreadingHTTPServer`, current Workspace input builder and result renderer.
The CPU search belongs in a separate local process so HTTP requests remain short
and cancellation/worker exit can be observed independently. One active worker per
Workspace is sufficient. Input edits invalidate the visible result immediately,
request cancellation and invalidate that job's revision. A new Design queues the
new snapshot after the old process exits; no overlapping optimizer workers.
Late poll responses must match all three identifiers before replacing the view.
Use a new run ID/directory on retry, preserving input, policy and seed; no implicit
retry, expanded budget, fixture hardcoding or cached M7-B prescription lookup.

Keep the existing exact solver public entry point unchanged. Add a small workflow
orchestrator, move only the trial's generation/search lifecycle into a reusable
worker module, and keep the physics kernels and Frozen Guards intact. Packaging
must explicitly include the optional optimizer for the worker; missing dependency
is an execution failure, never a no-candidate physics result. Retain a background
600 s watchdog and cooperative stop before each Adapter call. An unresponsive
worker may be terminated after cancellation, with no result publication.

Update the result renderer's hardcoded exact-family budget caption for the
workflow result, and clearly label Near-Match q mismatch. The 0.90 threshold stays
an M7-B concept criterion. Keep input SHA, reference planes, candidate ID, search
method, bounds and termination in HTML/JSON/A4 evidence. Display both raw guard
readings and limit-minus-reading margins; explain that neither is a tolerance or
aberration error bound. Actual field and Total Coupling claims remain Uncomputed.

M6-C resolves overlap ties at 1e-12. M7-B's G029/G030/G023 have different overlaps
from G036, so they are comparison evidence, not same-bin recommendation alternatives.
Do not silently broaden the bin or treat all >=0.90 designs as tied. A product
trade-off policy change would require its own explicit rationale and acceptance.

M7-D acceptance must exercise the real worker and Desktop/Mobile paths: existing
exact success; SMF–Glass fallback; input edit while running; cancel and retry;
old response arriving after a new revision; missing phase/high divergence;
timeout and worker failure; identical input/candidate/metric values in report,
HTML/JSON and A4. Reuse the full search first. Search reduction, if later needed,
requires a new frozen general rule and quality/runtime comparison; this milestone
provides no basis to select only the four successful M7-B geometries.

## Next development instruction

**Photonic Architecture Explorer — M7-D / Sol Work**

Recover latest Main and the M7-C Draft HEAD/CI/artifacts. Read AGENTS.md,
PRODUCT_CHARTER.md and this contract. Implement the minimum local background
Near-Match workflow described above using the trial as the reference, preserving
exact behavior, M6-C ranking, immutable inputs and Frozen Guards. Complete the
listed lifecycle/browser/export acceptance checks. Submit a separate Draft PR
with exact HEAD, CI, evidence and next work order. Main merge requires separate
approval. Do not add new topology, surface physics or actual coupling claims.
