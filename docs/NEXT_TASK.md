# M3-A handoff → M3-B proposal

M3-A: docs/M3A_ADAPTER.md, results/m3a_001.json.
External adapter / declared AABB checks implemented; Optical Kernels unchanged.
Actual Applicability, full Package Clearance, Total Coupling = Uncomputed.
M3-A Draft PR → PR #3 → PR #2 → PR #1 → Main. 모든 PR을 미병합으로 유지한다.

Recommended: Sol Work. 기존 API와 결과 표시를 연결하는 작은 UI 작업이다.
Off-vertex/Finite-Field Physics Formulation은 별도 Astra Checkpoint로 다룬다.
아래는 다음 개발 제안이며 이번에 M3-B를 시작하지 않는다.

```text
Photonic Architecture Explorer — M3-B
Recommended Mode: Sol Work
Mission: Minimal 2D Inspector · Honest Result States · User Review
Repository: https://github.com/legendnever-collab/photonic-architecture-explorer
Base: latest M3-A Draft PR on feature/m3a-external-adapter; recover exact HEAD.

Main/PR Stack/HEAD/CI/Artifacts를 복구하고 기존 검증을 재실행하라.
AGENTS.md, docs/M3A_ADAPTER.md와 docs/EXTERNAL_PORT_CONTRACT.md를 읽어라.
Physics/Fixture/Guard/Adapter Contract를 보존하라. Main을 병합하지 마라.

기존 adapt_external/evaluate_external을 호출하는 최소 2D Inspector를 구현하라.
작은 Python local interface 또는 static report 중 기존 구조에 맞는 최소 방식을 선택하라.
UI에서 Physics를 재구현하거나 별도 JavaScript Solver를 작성하지 마라.

Synthetic example/blank JSON을 읽고 Fixed Source/Target의 위치·방향, 두 quadratic
surface, chief path와 명시 Package AABB를 공통 좌표·단위로 표시하라.
Projection 방향과 생략 축을 명시하고 2D에서 겹쳐 보이는 물체를 3D 충돌로 단정하지 마라.
기존 samples를 쓰는 Beam envelope는 Approximate 표시, Clearance 증거로 쓰지 마라.

Port 입력과 Reflector Design Variables를 구분하고, 변경 시 Adapter로 재평가하라.
Geometry/Domain/Bounds/Approximate Overlap/Envelope/Full Package/Loss 상태를 분리하라.
Invalid/Uncomputed 상태에서 이전 Overlap을 표시하지 마라. Source/Target를 자동 이동하거나
Mode를 output에 fit하지 마라. Actual Applicability와 Total Coupling은 Uncomputed 유지.

Missing Phase, 잘못된 단위/Target Direction, High Divergence, Bounds/Package Fail 사례를
UI에서도 재현하라. 화면은 Engineering 검토에 필요한 최소 구성으로 제한하라.
Off-vertex/Finite-Field Solver, Optimizer, 추가 Optical Components, 자동 Topology는 금지한다.

검증 가능한 실행 방법과 사용자 Review 항목을 제공하라.
M3-A 위 별도 Draft PR을 만들고 정확한 SHA/Tests/CI/Artifacts와 다음 지시문을
채팅에 제출하라. Main 병합과 후속 개발 자동 시작은 하지 마라.
```
