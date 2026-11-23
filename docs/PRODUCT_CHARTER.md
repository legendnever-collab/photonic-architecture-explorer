# Photonic Architecture Explorer — Product Charter

**개정 2026-11-24** (사용자 승인 재설계 계획 반영). 이전 판은 [history/PRODUCT_CHARTER_2026-11-14.md](history/PRODUCT_CHARTER_2026-11-14.md)에 보존한다.
이 Charter는 사용자의 명시적 지시로만 바뀐다.

## 목표

고정 Optical Port 두 개를 도면 위에 놓으면, 만들 수 있는 광학 연결 구조 후보를 자동으로 생성하고,
물리 근거로 평가·비교하여 보여 준다. 후보가 없으면 그 이유와 필요한 다음 단계를 수치로 설명한다.
쓰임새는 초기 R&D 설계 판단과 특허용 개념 도출이며, 특허성·FTO 판단은 하지 않는다.

## 사용자 약속

1. **Two-Port-First** — 사용자는 Port의 기준면 위치, 전파 방향, 파장, Mode만 준다. 공개 문헌 Preset을 제공한다.
2. **시각 우선** — Port, 반사면, Beam, Package를 3D 장면과 2D 정투상·Fold 도면에서 보며 입력하고 비교한다.
   도면은 엔진이 계산한 Geometry를 그대로 그린다.
3. **최소 부담** — Solver, Topology, 반사면 수, 최적화 설정을 묻지 않는다. 고급 정보는 펼쳐 볼 때만 보인다.
4. **근거 있는 비교** — 추천과 대안을 투명한 기준(광경로, 공차 민감도, 제작성, Footprint, Package 여유)으로 비교한다.
5. **꾸며 내지 않음** — 모르는 Field, Phase, 손실, 형상, 공차를 지어내지 않는다. 가정과 Synthetic 값은 표시한다.
6. **정직한 실패** — 한 근사 모델의 Domain 실패는 구조 불가능의 증명이 아니다. 실패 원인, 임계값, 다음 단계를 보여 준다.
7. **내보내기** — 결과는 치수 도면(SVG), 특허 Figure, 재현 가능한 JSON 설계 기록으로 내보낸다.

## 진척의 기준

User Decision Benchmark 시나리오(S1~S6)에서 쓸모 있는 답이 나오는지로 판정한다. 최우선은
SMF → Glass WG(LDW와 IOX 각각, S2a·S2b)다. 검증 문서나 Reference Solver가 늘어나는 것만으로는 진척이 아니다.

## 경계

- 회사 기밀 데이터를 저장소에 두지 않는다(Public 저장소).
- 단계와 Gate는 [Roadmap](ROADMAP.md), 결정 이력은 [Decision Log](DECISIONS.md)를 따른다.
- main 병합은 Phase 단위 사용자 승인 후에만 한다.
