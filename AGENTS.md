# Photonic Architecture Explorer — 개발 계약

2026-11-24부터 Claude가 단독으로 개발한다(GPT 개발 중단, 사용자 확정). 이 파일과
[Product Charter](docs/PRODUCT_CHARTER.md), [Roadmap](docs/ROADMAP.md), [Decision Log](docs/DECISIONS.md)를
작업 시작 전에 읽는다. 현재 진행 Phase와 다음 할 일은 Roadmap과 Decision Log의 마지막 항목이 기준이다.

## 제품 방향 (사용자 확정)

- 고정 Port 두 개를 도면 위에 놓으면, 만들 수 있는 광학 연결 구조 후보를 근거와 함께 보여 준다.
  쓰임새는 초기 R&D 판단과 특허용 개념 도출이다.
- 사용자는 Port 정보만 준다. 반사면 위치·곡률, Solver, Topology, 최적화 설정을 묻지 않는다.
- 시각 우선: 3D 장면과 2D 정투상·Fold 도면에서 배치를 보며 입력하고 결과를 비교한다.
- 진척은 User Decision Benchmark(S1~S6, `src/photonic_architecture_explorer/scenarios/`) 통과로 잰다.
  최우선 시나리오는 SMF → Glass WG(LDW, IOX 각각, S2a·S2b)다.

## 물리 정직성 (유지)

- Port의 위치·방향·매질·파장·Mode는 절대 바꾸지 않는다. Target을 결과에 맞추지 않는다.
- Geometry, Model Domain, Normalized Mode Overlap, 물리 손실, Package, 제조를 분리한다.
  Normalized Overlap을 Total Coupling이라 하지 않는다. Uncomputed는 0이 아니다.
- 모델 Domain 밖의 입력(Skew/Roll, 고 NA, Clipping 등)은 조용히 근사하지 않고 거절한다.
  거절할 때는 수치와 다음 단계를 함께 제시한다.
- 새 물리 커널은 Production 코드와 독립된 Reference 테스트와 오차 기준을 갖춘 뒤에만 결과에 쓴다.
- Frozen Guard(발산각 0.1 rad, 3w·|κ| 0.15, 입사각 70°, Aperture tail 1e-6)는 근거와 사용자 승인 없이 완화하지 않는다.
- 회사 기밀 입력 금지. 저장소는 Public이며 Synthetic·공개 문헌 값만 둔다.
  실제 Port 데이터는 저장소 밖 로컬 파일로만 불러온다.
- Photonic Connector Studio 저장소는 읽기 전용이다.

## 작업 방식

- Phase마다 브랜치(`phase/p<N>-<name>`)를 두고 Draft PR로 올린다. main 병합은 Phase 단위로 사용자 승인 후에만 한다.
- 물리 변경 후 `PYTHONPATH=src python scripts/validate.py`와 `python -m unittest discover -s tests`를 실행한다.
  시나리오 정의를 바꾸면 `python scripts/build_scenarios.py`로 Fixture를 다시 만든다.
- PR마다 `docs/DECISIONS.md`에 10줄 이내 항목을 추가한다: 새로 가능해진 설계 판단, 주요 기술 선택, 남은 한계.
- 일상적인 기술 선택은 개발자가 정하고 기록한다. 범위·외부 비용·검증 기준 완화·main 병합만 사용자 승인을 받는다.
- 연구성 검증은 "어떤 설계 판단이 바뀔 수 있는가"를 먼저 적고, 한 Phase 안에 답이 없으면 중단하고 재개 조건만 남긴다.
- UI, 보고서, 문서는 한국어 문장과 표준 영어 기술 용어로 쓴다.
