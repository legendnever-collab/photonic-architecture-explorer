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
