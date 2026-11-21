# M7-R23 · 1310 nm의 Package 제약과 후보 비교

**Mission / Objective.** 두 Port에서 생성된 후보가 지정 Envelope에 들어가는지 비교하고, 작은 Envelope에서 명목 Overlap과 Beam Footprint가 어떻게 바뀌는지 확인한다. **Astra Work**를 권장한다. 제한된 Search에서 Package와 광학 Guard를 동시에 적용할 때 제약과 오차를 검증해야 한다.

**Repository / Verified Base.** [photonic-architecture-explorer](https://github.com/legendnever-collab/photonic-architecture-explorer). [R21 #52](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/52)의 검증 SHA는 `d0cd44ae677f3b6c070be04c9e56808827b5a017`이다. 로컬 검증한 [R22 Draft #53](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/53)의 구현 SHA는 `4caf99ee4fd527ecf3f48a20c52391dcbe190795`다. 최신 HEAD에 대응하는 CI와 Artifact는 Draft 검증 기록과 Actions에서 확인한다. 원본·편집 수치는 [R22 Design Notes](M7R22_REFERENCE_REDESIGN.md)를 따른다.

1. **Recovery.** AGENTS.md, Product Charter, DEVELOPMENT_OPERATING_POLICY.md 및 이 지시문을 읽는다. 열린 R22 Draft의 최신 HEAD·Base·CI를 확인한다. 병합됐다면 최신 검증 Main에서 R22 포함을 확인한다. R22의 원본·편집 SHA, Browser와 Windows Evidence, R7–R9의 각 Envelope·Overlap 근거를 대조한다.
2. **Scope.** R22 Workspace에 선택형 Package 입력의 최소 방식을 정한다. 먼저 R7–R9의 저장된 Nominal Envelope 두 조건과 기존 Clearance/Footprint Guard를 재사용해 같은 1310 nm Port에서 후보가 어디서 탈락하는지 보여준다. 기구 근사가 허용하는 최소 범위를 먼저 확인하고, 기존 Package Geometry와 Bounded Search로 비교한다. 기본 Two-Port 동작과 Source/Target를 보존한다.
3. **Acceptance / Budget.** 동결 처방 재평가에서 R9의 4.30 mm Envelope와 5.023725 mm Envelope의 η를 해당 Artifact의 수치와 절대차 1e−8 이내로 재현한다. 기존 50 µm 최소 AABB Clearance 판정을 대조한다. 편집한 Envelope에서 결과 SHA가 바뀌고 옛 추천·검증 근거가 숨겨져야 한다. 자동 탐색은 기존 시간·호출 예산과 Guard를 계승한다. 통과 후보가 없거나 기준 재현에 실패하면 원인을 기록하고 해당 추천을 보류한다.
4. **Regression.** 무제약 R6 Test, 변경된 입력의 새 SHA, Missing Phase·취소·Export, Synthetic와 1550 nm, Tutorial과 Confidence, Windows 패키지 회귀를 확인한다.
5. **Non-Goals / Remaining Uncomputed.** 새 Solver·Topology, Guard 변경 및 실제 Manufacturing 판정은 범위 밖이다. 전체 Beam/Body Clearance, 실제 Package Yield와 조립 공차, Guided Power·U·Total Coupling은 Uncomputed로 남긴다.
6. **Deliverables / 승인.** 제한된 Package 비교 UI 또는 그 구현 가능성 판정, 수치와 Evidence, Draft PR, 후속 Work Order를 제출한다. 운영 정책의 Engineering Ownership·언어·Evidence 규칙을 계승한다. Main 병합 및 다음 Milestone 실행에는 각각 사용자 승인이 필요하다.

---

## 이전 Work Order 기록

# M7-R22 · 1310 nm SMF–Glass Reference에서 사용자 입력 재설계

**Mission / Objective.** Tutorial에서 확인한 두 Port를 Workspace에서 열어 Design을 실행하고, 한 조건을 바꾼 뒤 새 후보와 Confidence를 검토한다. R21의 설명과 실제 후보 생성 사이의 단절을 해결한다. **Sol Work**를 권장한다. 기존 입력·Worker·Gaussian 평가·Export를 재사용하는 통합 작업이다.

**Repository / Verified Base SHA.** [photonic-architecture-explorer](https://github.com/legendnever-collab/photonic-architecture-explorer) · [R21 Draft #52](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/52) 구현 SHA `1b64a7f5672f9e4feb622094b754ccb14a2e482a`. [Physics·Browser CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44895226164)와 [Windows Package CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44895226263)에서 이 구현에 귀속되는 Evidence를 확인한다. 인수인계 문서가 추가된 최신 HEAD는 Recovery에서 대조한다.

**관련 Physics Evidence.** R20 Draft #51의 검증 SHA는 `ddf8ce0bca3a887f24fae45671a93e11ce7760ec`이다. Physics CI 44893958127, Windows CI 44893958128 및 R6 design_summary.json, R20 summary.json을 참조한다. R21의 구현·검증 범위는 [R21 Design Notes](M7R21_ENGINEERING_TRUST.md)를 따른다.

1. **Recovery.** AGENTS.md, docs/PRODUCT_CHARTER.md, docs/DEVELOPMENT_OPERATING_POLICY.md, 이 첫 지시문을 읽는다. R21 Draft가 열려 있으면 해당 최신 HEAD·Base·Diff와 Physics/Windows CI를 확인한 후 시작한다. 병합됐다면 최신 검증 Main에서 R21 포함을 확인한다. R6 Port JSON·Hash·단위와 현재 1550 nm Proxy를 구분한다.
2. **Scope.** Example A에 명시적 ‘이 두 Port로 설계’ 진입점을 추가한다. 기존 inputs/Workspace/Job/Export를 재사용하고 저장된 R6 Port의 위치·축·q·기준면·출처를 손실 없이 전달한다. 사용자가 Position 하나를 바꾸면 이전 결과를 즉시 숨기고 새 Snapshot으로 기존 Design을 재실행한다. 미편집 Port의 근거를 유지하고 변경된 조건 및 적용되지 않는 Reference를 표시한다.
3. **Acceptance / Budget.** 원본 1310 nm에서 Exact-q 36배치/144처방/유효 0, Guarded Near-Match G036-NM 및 R6 η=0.9990889546173051을 재현한다. 동일 Snapshot의 독립 Quadrature와 η 절대차 ≤1e−8을 적용한다. 편집 입력은 동일 입력의 독립 Adapter 재평가와 대조하고 성공·유효 후보 없음·중단을 구분한다. 기존 Worker 시간·호출 예산과 취소 동작을 계승한다. 재현 차이 또는 입력 출처 손실 시 해당 추천을 보류하고 원인을 기록한다.
4. **Regression.** 원본·편집 1건·미제공 Phase·취소·오래된 응답·HTML/JSON의 Candidate ID와 Input SHA를 검사한다. Synthetic와 1550 nm 흐름, Geometry/Domain Guard, R21 Tutorial·Confidence, Physics CI와 압축 해제한 Windows Review Package를 확인한다.
5. **Non-Goals / Remaining Uncomputed.** 새 Topology·Solver·실시간 Meep, Guard 완화, 실제 SSC 성능 산출은 범위 밖이다. 실제 Total Coupling, 명목 Guided Power 비율·U, M2 회전 광학 응답과 Assembly Tolerance는 Uncomputed다.
6. **Deliverables / 승인.** 검토 가능한 UI, 재현 결과·오차·제한, Regression과 Draft PR, 후속 docs/NEXT_TASK.md를 제출한다. 운영 정책의 Engineering Ownership·언어·Evidence 규칙을 계승한다. Main 병합 및 다음 Milestone 실행은 각각 사용자 승인이 필요하다.

---

## 이전 Work Order 기록 · 아래 지시문은 역사적 기록이다

### 보류된 R20 후속 Physics 제안 — 원형 core 경계에 맞춘 HE11 독립 대조

Astra Work. [R20](M7R20_YEE_FIELD_EXTRACTION.md)의 24 px/µm E/H 잔차를
재현한다. 동일한 1310 nm SMF의 경계 일치형 vector FEM eigenmode를 해석 HE11과
비교한다. 계산 전 mesh·order·개방경계 예산과 중단 기준을 정한다.
Er는 core 경계 양쪽에서 따로 비교하고 H와 Power에 E에서 정한 공통 계수를 쓴다.
5e−5 정확도를 입증하면 독립 Facet 여기·monitor 경로를 확정한다.
미달하면 원인과 최소 외부 입력을 기록한다. Draft PR, Main 병합은 별도 승인한다.

---

# M7-R20 — Vector Field Export의 H와 Power 검증

Astra Work. [R19](M7R19_OPEN_FACET_REFERENCE.md)의 직선 guide H 오차와
복원 Power/native flux 차이를 재현한다. 균일 매질 평면파와 직선 HE11을
사용해 Yee 성분의 공간·시간 위치, 파동 임피던스, 공통 진폭과 Flux 정규화를
분리한다. 사전 예산 안에서 대조가 통과한 경우 Facet을 재계산한다.
통과하지 않으면 잔여 원인과 대체 Reference를 기록하고 계산을 중단한다.
Main 병합은 별도 승인한다.

---

# M7-R19 — 개방 SMF 기준장과 M1 Source 오차 판정

Astra Work. [R18](M7R18_SOURCE_EDGE_IMPACT.md)의 두 효과가 모두 예산을 넘었다.
두 Port·Launch·M1을 고정하고 공통 영역의 장과 외곽 기여를 함께 검증할
독립 개방경계 vector facet reference의 제공 가능성을 먼저 확인한다.
계산 전에 자원 한도와 정련 기준을 정하고, 독립장이 있으면 동일 평면·위상·Power에서
M1 E/H 및 Flux를 비교한다. 미확보 시 외부 실행에 필요한 최소 입력·출력 계약과
중단 근거를 남긴다. 검증 전에는 곡면 전달 비율과 회전 응답을 Uncomputed로 둔다.
결과는 Draft PR에 남기고 Main 병합은 별도 승인한다.

---

# M7-R18 — M1 Edge의 설계 영향과 Source 수렴 판정

Astra Work. [R17](M7R17_ISOLATED_SOURCE_EDGE.md)의 Source와 Edge 결과를 재현한다.
같은 Launch에서 Source 셀 경계의 truncation과 고유모드 정련 효과를 분리한다.
실제 M1 둘레의 입사 E/H 및 Edge strip의 flux를 구하고, 국소 PO 불일치가
수신 모드 투영 오차에 줄 수 있는 영향을 정량화할 방법을 검토한다. 가장자리의
세기만으로 전달 오차를 한정하지 않는다. 사전 예산 안에서 근거가 확보될 때
곡면 계산을 진행한다. Draft PR, Main 병합은 별도 승인한다.

---

# M7-R17 — 고립 SMF Source와 유한 PEC 단면 검증

Astra Work. [R16](M7R16_VECTOR_RELAY.md)의 주기 셀 대조와 R15 Launch를 재현한다.
고립 Source 구성 후 M1 입사장·Flux의 셀/창 수렴을 확인한다. 고정 처방의 M1과 같은
입사각·Aperture에서 유한 평면 PEC의 Vector Physical Optics와 독립 edge diffraction
Reference를 대조한다. 편광별 E/H 및 오차가 예산 안에 있을 때 곡면으로 확장한다.
명목 전달 비율·회전 판정은 별도 검증 후 진행한다. Draft PR, Main 병합은 별도 승인한다.

---

# M7-R16 — 1310 nm 명목 Vector Relay 검증 경로

추천 Astra Work. [R15 Port ledger](M7R15_PORT_POWER.md)의 Power와 동일한 SMF Source
E/H를 사용한다. 고정 두 반사면의 공개 Ideal PEC 또는 명시 경계, 수치 예산과 중단 기준을
설정한다. 자유공간 Vector 전파와 평면 반사의 편광·Flux control을 독립 해와 대조한다.
통과하면 고정 Target에서 복소 E_t,E_s,H_t,H_s를 Export할 경로를 확인하고, 독립 Glass
guided-mode monitor를 포함한 대조 계산 범위를 기록한다. 근거가 부족한 전달 비율과
회전 광학 응답은 Uncomputed로 판정한다. 결과는 Draft PR에 남기고 병합은 별도 승인한다.

---

# M7-R15 — 1310 nm 두 Port의 Vector Power 정규화

추천 Sol Work. [R14의 재개 입력](M7R14_GUIDED_POWER.md)에 따라 기존 FMMAX 캡처에서
Glass 역여기와 SMF 순방향에 대해 내부 incident/reflected, 외부 outgoing flux 및 그 비율,
E/H 단위와 amplitude scale을 함께 내보낸다. R5/R6 case와 기존 Field를 고정하고
양의 방향, 상대장 복원, 단면 Power balance 및 Grid/Basis/Window 변화로 교차 검증한다.
Port별 정규화를 판정하고, 남은 Target 입사 Vector E/H와 내부 독립 monitor 요구를 기록한다.
명목 relay·회전·실물 성능은 각각 근거가 확보될 때 판정한다. Draft PR 및 별도 병합 승인.

---

# M7-R14 — 고정 Glass Mode로의 전달 Power 평가 가능성

Astra Work. [R13 수광 판정](M7R13_TARGET_ACCEPTANCE.md)과 R5/R6/R12 저장장을 사용한다.
평가하려는 양을 launch 대비 고정 guided mode의 power로 정의하고, reciprocal E/H 투영의
공통 기준면·좌표·power 정규화·오차 예산을 먼저 기록한다. R12 scalar 도착장과 R5
vector mode 간 연결을 입증할 수 있는지 양성 대조로 확인한다. 입력이 부족하면 필요한
최소 비기밀 Field export와 실행 절차를 기록한다. R10 전체면 η와 회전 검증 상태를 보존한다.
Draft PR을 작성하고 Main 병합은 별도 승인한다.

---

# M7-R12 이후 — Target 수광 영역과 Overlap 정의

추천 Astra Work. [R12](M7R12_CURVED_QUADRATURE.md)의 명목 M2 Power 초과는 곡면
정련으로 해소됐다. 유한 Window의 η는 약 0.989811이고 전체면 U는 미확정이다.
다음에는 고정 Target의 유효 수광면 또는 수집 NA가 입력 근거로 정의되는지 검토한다.
그 정의로 달라지는 metric과 원래 R10 지표를 구분하고 외부장 norm이나 유한 경계
적분의 오차 상한을 제시할 수 있을 때 판정한다. 회전 광학 성능은 명목 검증 이후다.

---

# M7-R12 — M1→M2 회절 적분 수렴

Astra Work. [M7-R11](M7R11_CURVED_FIELD_REFERENCE.md)의 동결 처방과 명목 raw Field를
사용해 M2/M1 flux 초과가 발생하는 전파 구간부터 조사한다. 위상 sampling과 aliasing을
점검하고 기존의 검증 가능한 oscillatory quadrature 또는 독립 Physical Optics 경로를
선정한다. 사전 계산 예산 안에서 고정 Target Window와 곡면 정련을 독립 대조한다.
M7-R10의 U 기준을 만족할 때 M2 ±1 mrad로 진행한다. Draft PR, Main 병합 별도 승인.

---

# M7-R11 — 독립 Curved-Surface Field Reference

Astra Work 권장. [M7-R10](M7R10_FINITE_BEAM_SCOPE.md)의 1310 nm 확장 처방과
검증 기준을 사용한다. 독립 Wave-Optics 경로에 Gaussian과 단일 Aperture 대조를 적용한
뒤 명목 두 반사면의 복소장과 power ledger를 고정 Target 면에서 검증한다. Solver와
오차·실행 예산은 첫 계산 전에 기록한다. 명목 적용성·수렴과 독립 대조가 확인되면
M2 ±1 mrad를 진단한다. +1 mrad의 50 µm AABB Clearance 미달을 함께 보고한다.
실제 차폐 형상이나 손실 근거가 없으면 해당 성능은 Uncomputed로 둔다. Draft PR을
작성하고 Main 병합은 별도 승인한다.

---

# M7-R10 — 확장안 Finite-beam 검증 범위

[M7-R9](M7R9_ENVELOPE_ASSEMBLY_REVIEW.md)의 확장 처방을 동결하고, 1310 nm에서
두 Aperture와 Backing·Keepout에 대한 Finite-beam 검증 입력과 합격 기준을 명시한다.
M4-C 외부 필드 검증 근거를 참고해 기존 유한 필드 방법의 적용 범위를 먼저 판단한다.
사용 가능한 실제 형상과 공차가 없으면 개념 검증 범위와 필요한 자료를 기록한다.
명목 및 배치 교란 상태의 η 검증 필요 범위를 제시하고, 검증 근거가 없는 실물 성능은
Uncomputed로 유지한다. Draft PR을 작성하고 Main 병합은 별도 승인한다.

---

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
