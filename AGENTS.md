# Photonic Architecture Explorer — development contract

## Standing product directive (user-confirmed 2026-11-14)

- **Read and honor [docs/PRODUCT_CHARTER.md](docs/PRODUCT_CHARTER.md) before planning or implementing any milestone.** This directive persists until the user **explicitly** changes it.
- **End goal:** two fixed optical ports in; autonomously generated, technically justified and ranked optical interconnect design candidates out, suitable for early R&D and patent-oriented concept exploration.
- **Minimize user intervention:** the user supplies two-port information, not reflector locations/curvatures, algorithm/solver/topology choices or a long checklist of optional parameters. Prefer one clear default action; progressively disclose advanced parameters.
- **Engineering ownership:** the developing agent chooses internal methods, defaults, architecture exploration strategy, milestones and acceptance tests without asking the user to settle routine technical tradeoffs.
- **Do not fake missing information:** label design-only assumptions and synthetic inputs. Distinguish conceptual feasibility from actual field/total-coupling/package/fabrication claims. User-owned unknowns are requested only when essential.
- **Product priority:** a usable auto-generated design loop and interpretable candidate comparison, not indefinitely expanding validation documents. Existing scope and model gates remain intact until separately justified.
- These product instructions govern UX/roadmap; existing physics safety, tests and GitHub draft-PR/merge controls below continue to apply.

## Existing engineering and repository controls

- Physics correctness, feasibility, reproducibility, simplicity, in that order.
- Read README, docs/PHYSICS.md, docs/M1_BENCHMARK.md and docs/NEXT_TASK.md first.
- Preserve fixed Port position, direction, external medium, wavelength and complex mode.
- Keep Geometry, model domain, normalized Mode Overlap, physical losses and fabrication separate.
- Never report normalized overlap as total coupling. Uncomputed is not zero.
- No confidential company inputs. All M1 examples are synthetic.
- Existing Photonic Connector Studio is read-only; no UI or broad engine migration.
- **Current validated physics scope** (not the permanent product end goal): exactly two reflectors, coplanar aligned separable Gaussian fields.
- Refuse skew/rolled/high-NA/clipped inputs rather than silently approximating them.
- Numerical references must be independent of production kernels.
- Do not relax frozen guards or fit the frozen Target to computed output.
- Run `PYTHONPATH=src python scripts/validate.py` after physics changes.
- No additional optical elements, topology synthesis, Maxwell solver or complex UI without separately justified engineering scope. The two-reflector candidate generator in the Product Charter is the next intended design-level extension, not an assertion of current support.
- Keep PRs Draft; no Main merge without explicit user approval.
- Explain key engineering choices and limitations in Korean; use English technical terms.

## M7-R21 이후의 작업 절차

- 시작할 때 이 파일, [Product Charter](docs/PRODUCT_CHARTER.md), [운영 정책](docs/DEVELOPMENT_OPERATING_POLICY.md), [기존 지시문 기록](docs/NEXT_TASK.md)과 대화의 최신 Work Order를 읽고 원격 상태부터 복구한다.
- 개발 Agent가 모델·탐색·검증·Milestone을 설계한다. UI, Tutorial, Report 및 인수인계는 한국어 문장과 표준 영어 Technical Terminology를 사용한다.
- 완료 또는 Blocked 시 운영 정책의 종료 절차를 실행하고 다음 Work Order와 Sol/Astra 추천을 사용자 대화에 전달한다. 작성과 실행은 별개이며 다음 Milestone 실행과 Main 병합에는 사용자 승인이 필요하다.
