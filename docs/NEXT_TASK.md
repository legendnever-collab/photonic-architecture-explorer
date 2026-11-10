# M3-C handoff → M3-D conditional integration proposal

Read docs/M3C_REVIEW.md and docs/M3C_INTEGRATION_READINESS.md.
M3-C → PR #5 → #4 → #3 → #2 → #1 → Main; all Draft/unmerged.
Actual Applicability / Total Coupling / Full Finite-Beam Clearance remain Uncomputed.

다음은 **사용자가 화면 Review 후 Main 통합을 승인할 때** 보낼 지시문이다.
작성 자체로 병합을 승인하거나 다음 작업을 자동 시작하지 않는다.
Recommended: Sol Work. 기존 Stack 통합·Release 검증이며 새 Physics 작업이 아니다.

```text
Photonic Architecture Explorer — M3-D
Recommended Mode: Sol Work
Mission: Approved Stack Integration · Release Verification
Repository: https://github.com/legendnever-collab/photonic-architecture-explorer
Base: latest M3-C Draft PR; recover exact HEAD / CI / Artifacts.

AGENTS.md, docs/M3C_REVIEW.md, docs/M3C_INTEGRATION_READINESS.md를 읽어라.
사용자 Review가 완료된 현재 Stack을 Main에 통합하라.
원격 Snapshot·Diff·Tests·Browser CI·Artifact·충돌을 다시 확인한 후에만 병합한다.
이력을 보존하며 PR #1부터 M3-C까지 의존 순서대로 병합하고,
각 단계 뒤 다음 PR의 Base/Diff/CI를 확인한다. 검증 실패 시 중단하고 원인을 보고한다.
Fixed Ports / Physics / Adapter / Fixtures / Guards / Uncomputed를 보존하라.
최종 Main SHA에서 필수 검증과 HTML을 재생성하고 CI/Artifacts를 확인하라.
정확한 Main SHA·통합 PR·검증 결과·사용 가능한 HTML·다음 제안을 제출하라.
새 기능·새 Physics·다음 개발 자동 시작은 하지 마라.
```
