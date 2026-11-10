# M4-C.1 handoff — Synthetic numerical verification Pass / actual input Unprovided

추천: **Astra Work**. 다음 판단은 실제 Complex Field의 기준면·정규화·출처와
Gaussian applicability다. 일반 입력 정리는 Sol도 가능하지만 물리적 적용성 판정은 Astra를 권장한다.

M4-C 역사적 Fail(0.027777663568 > 0.02)은 보존했다. M4-C.1은 Window 확장으로
같은 Control의 tail error 0.000203618350을 확인했다. 68 tests Pass.
이는 실제 WAFT/PIC 또는 Reflector 연결 성능 검증이 아니다.
실제 데이터가 없는 상태에서 추가 Synthetic Reference 확장을 자동으로 시작하지 않는다.

```text
Photonic Architecture Explorer — M4-D
Recommended Mode: Astra Work
Mission: External Field Intake & Applicability Gate
Repository: https://github.com/legendnever-collab/photonic-architecture-explorer
Base: M4-C.1 Draft PR (Main에 병합됐다면 최신 Main)

1. 원격 HEAD/Base/CI/Artifacts를 복구하고 AGENTS.md,
   docs/M4C1_ANGULAR_VERIFICATION.md, docs/EXTERNAL_PORT_CONTRACT.md,
   references/m4c_external_field_request.json을 읽어라.
   기존 Tests, legacy Stop, M4-C.1 Window 검증을 실행별 격리해 재현하라.
2. 이번에 제공된 비기밀 complex E/H export 또는 재현 가능한 국소 facet model을
   audit하라. 데이터가 없으면 누락 항목과 재개 조건만 갱신하고 중단하라.
   Guided MFD, n_eff 또는 임의 index/phase로 빈 입력을 채우지 마라.
3. 입력이 있으면 source/units/reference plane/basis/phase/decomposition/normalization,
   power accounting 및 grid/window convergence를 검증하라.
   계산 전에 입력에 맞는 제한된 예산·오차 지표·성공/중단 기준을 기록하라.
4. 현재 코드로 검증 가능한 범위만 평가하라. Gaussian complex fit 및 Frozen Domain
   검사에 필요한 증거를 분리하라. 새 fitting/Vector adapter/solver가 필요하면
   최소 후속 범위만 제안하고 이번에 새로 구현하지 마라.
5. 검증된 입력/근사/미제공을 분리하고 Fixed Ports·Guards·기존 결과를 보존하라.
   미검증 Overlap·Total Coupling·Package는 Uncomputed로 유지하라.
   결과·한계·재현 명령·다음 지시문을 저장하고 별도 Draft PR을 생성하라.
   정확한 HEAD/Tests/CI/Artifacts를 보고하라.
6. 새 범용 Solver·FE Space·UI·Optimizer·Topology·Reflector Reference,
   전체 Fold Maxwell, Main 병합, 후속 자동 실행은 하지 마라.
```
