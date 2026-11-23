# Roadmap

2026-11-24 사용자 승인 계획. 원본 계획 문서: [재설계 개발 계획](https://claude.ai/artifact/6C7546ZCMJQvjxzFqgdWRb).
각 Phase는 Gate(시나리오 통과 기준)를 만족해야 다음으로 넘어간다. 순서는 Phase가 끝날 때마다 다시 정한다.

| Phase | 상태 | 핵심 산출물 | Gate |
|---|---|---|---|
| P0 정리와 기반 | **진행 중** | 연구물 보관, 핵심 문서 통합, Design Document `pae.design/1`, JSON API(`pae-app`), 시나리오 Fixture S1~S6 | 기존 물리 테스트 통과, S1을 API로 재현, 모든 시나리오가 기록된 현재 상태를 재현 |
| P1 3D/2D 시각 Workspace | 예정 | 3D Viewer(Port·Mode·반사면 Sag·Beam 튜브·Envelope), Gizmo↔표 동기화, XY/XZ/YZ/Fold 도면과 치수, Preset, 후보 오버레이, SVG/JSON Export, Windows ZIP(Chrome/Edge) | S1 전 과정을 새 화면에서 완료. S2a·S2b는 입력·Preview·실패 원인 표시까지. 도면 좌표가 엔진 값과 1 nm 이내 일치. 기존 Workspace와 R5~R9·R20 의존 자료 보관 |
| P2 후보 생성 v2 | 예정 | 제약 기반 연속 탐색(Envelope·Keep-out·입사각·최소 곡률반경), Pareto 순위, 실행 가능한 Fail 안내 | S2a·S2b(공기 중 Edge 배치)에서 서로 다른 절충의 후보 3개 이상. S3는 수치 안내. 기본 Design 5초 이내 |
| P3 물리 Domain 확장 | 예정 | 균질 매질·평면 굴절 계면(Glass 상면, Glass 내부 반사면, 매립 WG 깊이) → 3D q-tensor(비동일평면) → 비근축 Scalar 검산 | 첫 Gate: S2a·S2b의 수직 SMF → Glass 내부 반사 → 매립 WG 후보와 Edge 배치 비교. 다음: S3·S4 |
| P4 Architecture Family | 예정 | Lens–Mirror, 단일·이중 Lens, Cylindrical Lens, Family 자동 선택 | S5 통과, Family 간 비교 |
| P5 특허·설계 산출물 | 예정 | 부호 붙은 특허 Figure, 치수 도면, 후보 보고서, glTF/STL(STEP은 요청 시) | 시나리오별 Figure 세트 일괄 생성 |
| P6 Field Import와 배열 | 미정 | FDTD/측정 Sampled Field 입력, 다채널(S6) | 실제 수요 확인 후 범위 확정 |

## 시나리오 현재 상태 (P0 측정)

| ID | 내용 | 현재 | 목표 Phase |
|---|---|---|---|
| S1 | SMF → SMF, 90° Fold | Computed, 후보 1개(3w·\|κ\| = 0.147 / 0.15) | P0 |
| S2a-1310 | SMF-28 → LDW(Sun 2021, 11 × 18 µm) | Fail: 고정 Exact-q Family에 유효 후보 없음 | P2 |
| S2a-1550 | SMF-28 → LDW(Desmet 2021, 12.8 × 12.1 µm) | Fail: 위와 같음 | P2 |
| S2b-1550 | SMF-28 → IOX(Brusberg 2012, 18.8 × 12.0 µm) | Fail: 위와 같음 | P2 |
| S3 | SiPh SSC 3 µm → SMF | Fail: 발산각 0.1 rad 초과 | P3·P4 |
| S4 | PIC Edge → 측면으로 비켜 선 수직 Fiber | Fail: 비동일평면 | P3 |
| S5 | Laser 1.5 × 3.5 µm → SSC 3 µm | Fail: 발산각 | P4 |
| S6 | Channel 배열 → FAU | 지원 범위 밖 | P6 |
