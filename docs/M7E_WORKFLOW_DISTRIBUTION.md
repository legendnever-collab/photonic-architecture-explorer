# M7-E — Integrated Workflow Acceptance & Windows Review Distribution

Base is M7-D Draft #29, `54eada8a76977010114df0c2e71211913f27a63a`.
Main remains `2094eca2dfbee359a18930d328525eaa84ac2305`; no merge is part of
M7-E. Follow Product Charter and [M7-D](M7D_BACKGROUND_WORKFLOW.md).

## Contract before build and validation

- Ship a Windows x64 review ZIP with an isolated CPython 3.12 runtime, the exact
  application sources/examples/docs, pinned NumPy 2.3.5/SciPy 1.17.0, licenses,
  launch command and source/input/dependency/file-hash manifest. No system Python,
  pip download or administrator action is required on the review computer.
- Build from the actual Windows CI runtime and installed binary wheels. Trim only
  unused test/development/Tk/pip content. Use the same bundled runtime for parent
  Workspace and child worker; do not freeze the app into a recursively launched
  executable. Force UTF-8 and ignore external Python environment configuration.
- Verify extraction into a path containing spaces and non-ASCII characters, outside
  the checkout, and run the application from that extracted tree. The normal start
  opens the default browser; a no-browser mode is available for automated review.
- Preserve all production physics/ranking/guards and M7-D search bounds. Retain the
  existing Linux exact/Frozen/worker/browser/print gates and run the real packaged
  Windows application/worker through cancellation, edit/late response, retry,
  SMF–Glass completion, HTML/JSON and A4 checks. No cached candidate substitution.
- Initially retain the exact M7-D 36-layout comparison gate on Windows too. If
  platform floating-point behavior prevents exact optimizer-history reproduction,
  preserve that observation and assess it separately from independent field/ABCD
  tolerances; do not silently lower a gate or change solver policy.
- Verify every distributed file against SHA-256, input snapshots and application
  fingerprints, record runtime/dependency versions, and upload the ZIP plus raw
  acceptance evidence for the exact Draft HEAD. Keep actual device applicability,
  assembly tolerance, yield, Total Coupling and Patentability Uncomputed.

## User review

Download `m7e-windows-review-package` from a successful Windows Review CI run.
The GitHub Artifact is a container ZIP; inside it is
`Photonic-Architecture-Explorer-M7E-Windows-x64.zip` and its checksum. Extract that
review ZIP completely, then double-click `Start-Photonic-Architecture-Explorer.cmd`.
It opens the local Workspace in the default browser. Keep the console open while
using the app; Ctrl+C stops it. See the included `README_REVIEW.md`.

1. Synthetic Example → Design: G009-B1 should appear without Near-Match search.
2. SMF–Glass Proxy → Design: progress appears; cancel or edit and retry if desired.
   A full run may take minutes. The unchanged bounded search is capped at 600 s.
3. Review Mode Match, the Near-Match q difference, path and raw guard margins.
   The reference observation is G036-NM, normalized overlap ~0.99993665 and path
   20.840 mm. A finite optimizer observation is not a guaranteed global optimum.
4. Export HTML/JSON and print the one-page A4 summary. Compare candidate ID and
   input SHA between them. Missing Phase must remain Uncomputed.

The package manifest records exact source HEAD/tree, Python patch version, pinned
dependencies, canonical Proxy input SHA and all distributed files. It excludes
runtime-generated `__pycache__` files from the inventory. The ZIP checksum sits
beside the ZIP; the manifest does not self-authenticate. CI records the artifact
digest and executes the extracted tree in a folder with spaces and Korean text,
with deliberately wrong external Python environment settings in launcher tests.

## Build / acceptance

On Windows x64 CPython 3.12:

```text
python scripts/build_m7e_review.py --output-dir dist/m7e-review
python scripts/validate_m7e_review.py <extracted-package> --output-dir results/runtime-m7e-package
```

The Windows workflow runs the packaged runtime through the same full M7-D browser
gate (with `PAE_PYTHON` and `PAE_EXPECT_ROOT`), not the checkout runtime. It also
checks exact equality of the three Frozen results, actual launcher HTTP, `.cmd`
dispatch, dependency imports and the file inventory after use. All previous Linux
gates remain. Raw evidence is uploaded as `m7e-windows-review-evidence`.

The portable Browser test uses `pathToFileURL` for Windows paths; Linux file URLs
retain their previous behavior. Application/physics/guard/ranking sources are
unchanged relative to M7-D. The CLI launch wrapper sets UTF-8 for child workers,
while isolated startup ignores an unrelated system Python configuration.

## Next development instruction — M7-F / Sol Work

Recover Main and the M7-D/M7-E Draft stack HEADs, CI and package evidence. Review
the Windows package with the user on the fixed Synthetic and SMF–Glass Proxy
journeys. Fix only confirmed usability/distribution issues and decide the next
bounded engineering question from actual feedback and existing model limits.
Preserve guards, ranking, immutable inputs and Uncomputed states. Submit a separate
Draft PR with evidence and a concise next work order. Main merge requires separate
approval; no new topology or physical performance claim follows automatically.
