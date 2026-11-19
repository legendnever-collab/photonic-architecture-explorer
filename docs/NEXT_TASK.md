# M7-R9 — Envelope 결정과 조립 여유 검토

[M7-R8](M7R8_LOCAL_PACKAGE_SEARCH.md)의 고정 Package η = 0.985044 처방과 X 폭
5.023725 mm 확장 처방을 재현한다. 두 안의 Package·곡률 여유와 기존 M6-D 배치
민감도를 비교하고, 합격에 필요한 공차 자료와 Finite-beam 검증을 명시한다.
실제 고객 치수가 미제공이면 M7-R7 Nominal 입력과 확장 진단을 유지한다.
Draft PR을 작성하고 Main 병합은 별도 승인한다.

---

# M7-R8 — Package 내부의 반사면 위치 탐색

[M7-R7](M7R7_PACKAGE_AND_MARGIN.md)의 고정 Port와 Nominal Envelope, Aperture, Clearance 및
Guard 목표를 사용한다. G029-NM 주변에서 두 반사면까지의 거리 a/c를 기존 고정 구간 내에서
촘촘하게 탐색할 예산을 사전 기록한다. 기존 Adapter로 Package, Chief Ray와 Guard를 검사하고
독립 ABCD/Quadrature로 유효 후보를 검증한다. η ≥ 0.99와 여유를 함께 만족하는지 판정한다.
관측 범위에서 후보가 없으면 지배 제약과 필요한 치수를 기록한다. Draft PR을 작성하고 Main
병합은 별도 승인한다.

---

# M7-R7 — 1310 nm Fixed-Port Package와 설계 여유

[M7-R6](M7R6_SMF_GLASS_FIXED_PORT.md)의 고정 배치와 G036-NM·G029-NM을 재현한다.
Package·Aperture·Clearance와 수치 Guard 여유의 목표를 명시하고, 입수한 실측 조건 또는
명시적 Nominal Envelope를 기존 Adapter에 입력한다. M6-D 배치 민감도와 기존 Near-Match
평가를 재사용해 Overlap·경로 길이·Guard 여유를 함께 비교한다. 두 Port 및 기존 Guard는
고정하고, 허용 후보가 없으면 지배적인 제약을 보고한다. 실제 손실과 생산 수율은 근거를
확보할 때까지 Uncomputed다. Main 병합은 별도 승인한다.

---

# M7-R6 — 1310 nm 두 번째 Port와 Fixed-Port 설계 준비

[M7-R5 단일 Guide의 결과](M7R5_SINGLE_PORT_FIELD.md)를 기준으로 1310 nm에서 같은 공기 매질을 사용하는 SMF Port의 출처와 독립적인 외부 Complex Field를 확인한다. Port의 진행 방향·Phase Convention·기준면을 등록하고 이 Port의 Fit 예산을 먼저 정한다. 측정 자료 또는 별도 시뮬레이션을 사용하면 Case ID와 입력 가정을 기록한다. 두 Port가 각각 통과하고 상대 위치·방향이 명시될 때 기존 Adapter와 전체 Guard로 설계를 평가한다. Nominal 모의 설계와 실제 Device 판정을 구분한다. Southampton 원본을 입수하면 M7-R3의 55 mW 사례에만 대조한다. Main 병합은 별도 승인한다.

---

# 1310 nm Single-Port Field Capture and Fit

추천 모델 **Sol Work**로 비기밀 1310 nm 한 Port의 자료를 우선 확보한다. 복소장이 준비되면
독립 Gaussian Fit 검증에는 **Astra Work**를 권장한다. 최신 Main과
[M7-R4 원본 확인·최소 취득 절차](M7R4_1310_EXTERNAL_FIELD_EVIDENCE.md)를 기준으로 한다.
Southampton 파일을 받으면 Fig. 3.5(c–d)의 55 mW 사례와 측정 메타데이터를 대조한다.
별도 Guide를 측정하거나 외부 Solver 자료를 쓰는 경우 독립 Case ID로 등록한다.
[입력 계약](EXTERNAL_PORT_CONTRACT.md)에 맞춰 External Plane, 매질, 축, Polarization과
복소장·Sampling·불확도를 기록한다. Fit 오차 예산을 먼저 정하고 한 Port를 평가한다.
두 번째 Port가 확보되면 기존 Adapter와 Guard에 연결한다. 미확보 항목의 판정은 Uncomputed다.

---

# M7-E — Integrated Workflow Acceptance & Distribution (historical)

추천 모델 **Sol Work**. 최신 Main과 M7-D Draft HEAD/CI/Artifact를 복구하고
[M7-D](M7D_BACKGROUND_WORKFLOW.md)를 따른다. 기본 Two-Port 경로와 SMF–Glass Proxy를
검토하고 의존성·출처가 포함된 사용자 검토용 실행 패키지를 준비한다. 확인된 Workflow/
Distribution 결함만 수정하며 물리 가드·순위·Uncomputed를 보존한다. 별도 Draft PR,
정확한 HEAD·CI·Artifact·사용자 검토 절차를 제출한다. Main 병합은 별도 승인한다.

---

# M7-D — Local Background Near-Match Workflow (historical)

추천 모델 **Sol Work**. 최신 Main과 M7-C Draft를 복구하고
[M7-C 실행 계약·Production Handoff](M7C_NEAR_MATCH_WORKFLOW.md)를 따른다.
기존 exact-q 결과가 정상 완료됐지만 후보가 없을 때에만 Near-Match worker를 시작한다.
동일 입력·가드·M6-C Ranking과 600 s 예산을 유지하며 Input Revision/SHA, 취소,
Timeout, Worker Failure, Late Response와 Export 일치를 검증한다. 별도 Draft PR,
정확한 HEAD·CI·Evidence를 제출한다. Main 병합은 별도 승인 후 진행한다.
아래 지시문은 완료된 단계의 이력이다.

---

# M6-A — Draft Stack Integration Review

추천 모델 **Sol Work**. M5-F Draft PR을 기준으로 현재 원격 Main과 PR stack을 검토한다.

1. AGENTS.md, PRODUCT_CHARTER.md, M5F_TWO_PORT_CONCEPT_ACCEPTANCE.md 및 기존 M4
   검증 기록을 읽고 Main과 열린 Draft PR의 Base·HEAD·diff·CI를 확인한다.
2. M5-F까지 필요한 패치의 의존 순서, 충돌, 중복과 통합 전 확인 사항을 정리한다.
   별도 M4 검증 브랜치의 범위와 적용 여부는 증거를 확인해 명시한다.
3. 별도 검증 브랜치에서 기존 Physics와 Workspace, 세 Synthetic 입력,
   HTML·JSON·A4 PDF를 재현하고 실제 배치 공차·Yield·Total Coupling의 상태를 확인한다.
4. 통합 가능 여부, 정확한 SHA·CI·artifact와 병합 순서안을 제출한다.
   Main 병합과 새 기능 개발은 별도 요청에서 진행한다.

---

# M5-F — Two-Port Concept Acceptance

추천 모델 **Sol Work**. M5-E Draft PR을 기준으로 한다. 병합됐다면 해당 변경이 포함된
Main을 기준으로 한다.

1. AGENTS.md, PRODUCT_CHARTER.md, M5E_CANDIDATE_REVIEW_SUMMARY.md를 읽고 기존
   Workspace, Frozen 입력, CI와 A4 요약을 재현한다.
2. 비기밀 Synthetic 포트 쌍으로 같은 q의 기준 케이스, 서로 다른 Gaussian q의 설계
   케이스, 적용 범위 밖의 케이스를 고정한다. 위치·방향·Mode 및 출처를 입력에 명시한다.
3. 각 케이스에서 Design 결과와 실패 이유, Fixed Ports, Nominal Mode Match, 상대 오차
   민감도, HTML/JSON/PDF 일치를 검토한다. 확인된 결함만 해당 범위에서 수정한다.
4. 설계 검토에 사용할 수 있는 기능과 실제 반사면 공차·Package Yield·Total Coupling의
   미검증 범위를 기록한다. 별도 Draft PR과 CI 증거, 다음 채팅 지시문을 제출한다.
   Main 병합이나 이후 개발은 별도 요청에서 진행한다.

---

# M5-E — Candidate Review Summary

추천 모델 **Sol Work**. M5-D Draft PR을 기준으로 한다. 병합됐다면 해당 변경이
포함된 Main에서 시작한다.

1. AGENTS.md, PRODUCT_CHARTER.md, M5C_MODE_MATCH_VIEW.md, M5D_CANDIDATE_SENSITIVITY.md를
   읽고 Workspace와 이전 CI를 재현한다.
2. 선택 후보 하나의 Fixed Ports, 경로, Nominal Mode Match, Target 기준면 민감도와
   모델 범위를 1페이지 인쇄용 요약으로 제공한다. 기존 보고서의 계산 결과를 재사용한다.
3. 추천과 대안의 민감도가 같은 경우 Nominal의 차이 및 실제 부품 공차의 미검증 범위를
   명시한다. 근거 없는 새로운 순위, 합격 공차, Yield 또는 Total Coupling을 만들지 않는다.
4. 화면·인쇄·HTML/JSON의 후보 ID, 입력 SHA, 수치와 Uncomputed 상태를 대조한다.
   새 Draft PR과 CI 검증을 제출하고 다음 개발 지시문을 채팅에 복사 가능한 텍스트로 쓴다.
   Main 병합과 후속 개발은 별도 요청에서 진행한다.

---

# M5-D — Candidate Sensitivity Review

추천 모델 **Sol Work**. M5-C Draft PR을 기준으로 추천과 대안의 정렬 민감도를
비교한다. 병합됐다면 해당 변경이 포함된 Main을 기준으로 한다.

1. AGENTS.md, PRODUCT_CHARTER.md, M5C_MODE_MATCH_VIEW.md와 기존 M2 진단 문서를 읽고
   정확한 Base HEAD·CI를 확인한다. Workspace와 Mode Match 결과를 재현한다.
2. 설계는 그대로 고정하고, 기존 Gaussian overlap의 상대 offset/slope 또는 검증된
   M2 배치 진단만 재사용한다. 먼저 기존 진단이 지원하는 조립 오차와 Target-plane
   상대 오차를 구분하고, 같은 위치·각도 가정에서 추천과 대안을 비교한다.
3. 명시한 범위와 단위로 Nominal과 perturbation의 Mode Mismatch Loss를 비교한다.
   물리 적용 범위를 벗어나면 Uncomputed로 표시한다. Package Yield와 Total Coupling은
   별도 유효 증거가 있을 때까지 Uncomputed다.
4. Mode Match 뒤의 선택형 상세로 결과를 제공하고 기존 Fixed Ports, 후보 순위, Frozen
   Guards, HTML/JSON 동기화를 검증한다. 작은 Synthetic 오차의 독립 검산을 포함한다.
5. 별도 Draft PR과 CI 증거를 제출한다. Main 병합이나 다음 단계 실행은 범위 밖이다.
   다음 개발 지시문은 채팅에 바로 복사할 수 있는 텍스트로 작성한다.

---

# M5-C — Mode Match View

추천 모델 **Sol Work**. 기존 Gaussian 결과를 선택 후보 화면에서 검토할 수 있게 한다.
M5-B Draft PR을 Base로 복구한다. 병합됐다면 Main의 해당 변경을 확인한다.

1. AGENTS.md, PRODUCT_CHARTER.md, M5A_DESIGN_CONTRACT.md와
   M5B_TWO_PORT_WORKSPACE.md를 읽고 Workspace 및 기존 M5-A 결과를 재현하라.
2. 기존 Python Gaussian의 Source·Target Mode와 선택 후보의 도착 빔을 사용한다.
   Source는 Source Reference Plane에 표시하고, 도착 빔과 Target Mode는 같은
   Target Reference Plane의 t/s 축, 단위, 범위와 정규화로 겹쳐 보여라.
3. 기존 Workspace/Report에 펼쳐볼 수 있는 Mode Match 상세를 추가하라. 강도
   분포와 상대 Wavefront Phase를 비교할 수 있게 하라. 전역 위상을 비교 기준으로
   삼지 말고, 강도 그림을 더한 값으로 Complex Mode Overlap을 추정하지 마라.
4. 기존 엔진의 Normalized Mode Overlap과 -10 log10(η) Mode Mismatch Loss를
   표시하라. η=0은 무한대 손실로, 누락 또는 도메인 실패는 Uncomputed로 구분한다.
   Total Coupling은 경로·계면·개구 손실이 검증될 때까지 Uncomputed로 둔다.
5. Matched Synthetic case와 강도는 같지만 Phase가 다른 진단용 Synthetic control을
   검증하라. 화면·내보내기의 후보 ID, 입력 SHA, 기준면, Overlap 일치를 검사하라.
   유효하지 않은 경우 이전 Mode 그림과 수치를 노출하지 마라.
6. Frozen Guards와 Fixed Ports를 보존하고 별도 Draft PR을 작성하라.
   새 Topology, Optimizer, Vector Adapter 및 후속 자동 진행은 이번 범위 밖이다.

---

## 완료 전 단계 지시문 (M5-B, M4-C)

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
