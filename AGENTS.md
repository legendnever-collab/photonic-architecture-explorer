# Photonic Architecture Explorer — development contract

- Physics correctness, feasibility, reproducibility, simplicity, in that order.
- Read README, docs/PHYSICS.md, docs/M1_BENCHMARK.md and docs/NEXT_TASK.md first.
- Preserve fixed Port position, direction, external medium, wavelength and complex mode.
- Keep Geometry, model domain, normalized Mode Overlap, physical losses and fabrication separate.
- Never report normalized overlap as total coupling. Uncomputed is not zero.
- No confidential company inputs. All M1 examples are synthetic.
- Existing Photonic Connector Studio is read-only; no UI or broad engine migration.
- Scope: exactly two reflectors, coplanar aligned separable Gaussian fields.
- Refuse skew/rolled/high-NA/clipped inputs rather than silently approximating them.
- Numerical references must be independent of production kernels.
- Do not relax frozen guards or fit the frozen Target to computed output.
- Run `PYTHONPATH=src python scripts/validate.py` after physics changes.
- No additional optical elements, topology synthesis, Maxwell solver or complex UI without new scope.
- Keep PRs Draft; no Main merge without explicit user approval.
- Explain key engineering choices and limitations in Korean; use English technical terms.
