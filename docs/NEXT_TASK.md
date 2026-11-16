# M5-B — Two-Port Design Workspace

추천: **Sol Work**. 검증된 M5-A Engine을 최소 입력 흐름에 연결하는 점진적 개발이다.
새 Physics/Optimizer가 아니라 사용자가 두 Port를 수정하고 Design을 실행하는 경로를 완성한다.
M4-C.1/M4-D 실제 Field 검증은 별도 track으로 유지한다.

```text
Photonic Architecture Explorer — M5-B
Recommended Mode: Sol Work
Mission: Two-Port Editing → Design → Candidate Review
Repository: https://github.com/legendnever-collab/photonic-architecture-explorer
Base: M5-A Draft PR (병합됐다면 최신 Main)

1. 원격 HEAD/Base/CI/Artifacts를 복구하고 AGENTS.md, PRODUCT_CHARTER,
   M5A_DESIGN_CONTRACT, M5A_AUTONOMOUS_DESIGN, M3B_INSPECTOR를 읽어라.
   기존 Tests와 M5-A Synthetic 결과·실패 cases를 fresh directory에서 재현하라.
2. 기존 Python Inspector 구조를 재사용해 최소 Two-Port 입력과 단일 Design 동작을
   연결하라. 사용자가 Position/Direction/Mode/Phase를 입력·검토할 수 있게 하라.
   Reflector/Curvature/Solver/Search 옵션을 필수 입력으로 추가하지 마라.
3. design_two_ports를 그대로 호출하고 기존 Read-only Report/JSON Export를 재사용하라.
   편집 후 이전 후보/Overlap은 즉시 숨기고, 완료된 입력 snapshot과 결과를 일치시켜라.
   단위·기준면·누락 Phase를 분명히 표시하며 Flat Phase를 임의 기본값으로 채우지 마라.
4. 추천 후보와 짧은 경로 대안의 Trade-off, bounded failure 및 Uncomputed를 보여라.
   Package 미제공은 Conceptual Geometry로 유지하라. Product Charter를 수정하지 마라.
5. Nominal→Port edit→Design, valid→missing phase→valid, invalid direction/high-NA,
   Fixed Port 불변성, static export 일치, Desktop/Mobile을 검증하라.
   결과/재현 명령/한계/다음 지시문을 저장하고 별도 Draft PR을 작성하라.
6. Frozen Guards·기존 결과 보존. 새 Topology/Optimizer/Maxwell/Vector adapter,
   실제 Coupling/Yield 주장, Main 또는 기존 PR 임의 병합, 후속 자동 실행은 금지한다.
```

---

## Historical M4-C handoff (preserved)

# M4-C handoff — STOP / external input required

추천: **Astra Work**. 실제 Field 정의·기준면·수치 오차의 판단이 필요한 범위다.
M4-C Control acceptance는 Fail이며 기존 61 tests는 Pass다. CI success는 기록된
실패 보존과 regression 통과를 뜻한다. 실제 Field/Overlap/Total Coupling은 Uncomputed.

다음 최소 작업은 **M4-C.1 Angular Metric Verification & External Input Readiness**다.
실제 외부 데이터가 없더라도 angular-bin 실패 원인의 제한적 보정 검토는 가능하지만,
그것으로 실제 성능 개발을 시작하지 않는다. 이 지시문은 제안이며 자동 실행하지 않았다.

```text
Photonic Architecture Explorer — M4-C.1
Recommended Mode: Astra Work
Mission: Angular Metric Verification & External Input Readiness
Repository: https://github.com/legendnever-collab/photonic-architecture-explorer
Base: M4-C Draft PR (PR #8 위의 assessment/m4c-external-field-reference)

1. 원격 HEAD/Base/CI/Artifacts를 복구하고 AGENTS.md,
   docs/M4C_REFERENCE_PLAN.md, docs/M4C_EXTERNAL_FIELD_REFERENCE.md,
   results/m4c_planar_control.json을 읽어라. 기존 검증/기록된 Stop을 재현하라.
2. 기존 Control/기준을 보존하고, sharp angular-tail 적분의 0.0277777 오차에 대해
   Δkx=2π/L 영향과 bin 경계를 확인하라. 변경 전 예산/성공·중단 기준을 기록하라.
   허용된 최소 접근은 Window convergence 또는 검증 가능한 bin-boundary 적분이다.
   원래 0.02 기준을 완화하거나 예전 실패 결과를 덮어쓰지 마라.
3. 독립 continuous quadrature와 Field/Flux/Angular Content/Power Balance를 비교하라.
   Sampling 일치만으로 검증 완료를 주장하지 마라. 새 범용 Solver를 만들지 마라.
4. references/m4c_external_field_request.json을 기준으로 제공된 외부 입력을 audit하라.
   입력이 없으면 누락 상태를 보존하라. 실제 WAFT를 임의 index profile/phase로 재구성하지 마라.
5. Control 검증, 실제 입력 준비, production 적용성을 분리해 보고하라.
   실제 Complex Field 또는 재현 가능한 facet 모델이 없으면 실제 성능 단계로 넘어가지 마라.
6. M4A 실제 입력/M4B Proxy/Control을 구분하고 Fixed Ports/Guards/Uncomputed를 보존하라.
   결과·재현 명령·한계·다음 지시문을 기록하고 별도 Draft PR을 생성하라.
   새 UI/Optimizer/Topology, Reflector Reference, 전체 Fold Maxwell,
   Main 병합, 후속 자동 진행은 하지 마라.
```
