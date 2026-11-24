# Roadmap

2026-11-24 사용자 승인 계획. 원본 계획 문서: [재설계 개발 계획](https://claude.ai/artifact/6C7546ZCMJQvjxzFqgdWRb).
각 Phase는 Gate(시나리오 통과 기준)를 만족해야 다음으로 넘어간다. 순서는 Phase가 끝날 때마다 다시 정한다.

| Phase | 상태 | 핵심 산출물 | Gate |
|---|---|---|---|
| P0 정리와 기반 | **완료** (PR #61) | 연구물 보관, 핵심 문서 통합, Design Document `pae.design/1`, JSON API(`pae-app`), 시나리오 Fixture S1~S6 | 기존 물리 테스트 통과, S1을 API로 재현, 모든 시나리오가 기록된 현재 상태를 재현 |
| P1 3D/2D 시각 Workspace | **완료** (PR #62, P0와 함께 병합) | 3D Viewer(Port·Mode·반사면 Sag·Beam 튜브·Envelope), Gizmo↔표 동기화, XY/XZ/YZ/Fold 도면과 치수, Preset, 후보 오버레이, SVG/JSON Export, Windows ZIP(Chrome/Edge) | S1 전 과정을 새 화면에서 완료. S2a·S2b는 입력·Preview·실패 원인 표시까지. 도면 좌표가 엔진 값과 1 nm 이내 일치. 기존 Workspace와 R5~R9·R20 의존 자료 보관 |
| P2 후보 생성 v2 | **완료** (PR #63) | 제약 기반 연속 탐색(Envelope·Keep-out·입사각·최소 곡률반경), Pareto 순위, 실행 가능한 Fail 안내 | S2a·S2b(공기 중 Edge 배치)에서 서로 다른 절충의 후보 3개 이상. S3는 수치 안내. 기본 Design 5초 이내 |
| P3 물리 Domain 확장 | **완료** (PR #64, v0.3.0) | 균질 매질·평면 굴절 계면(Glass 상면, Glass 내부 반사면, 매립 WG 깊이), 3D q-tensor(비동일평면·축 회전), 비근축 Scalar 검산(모든 후보 + Guard 밖 연구) | Gate **통과**: S2a·S2b Glass 배치와 Edge 비교, S4 후보 생성(Ray-transfer 검산), S3 비근축 검산. 결과: 국소 이차곡면 반사면은 같은 방향으로 꺾는 배치에서 Coma가 커서 근축 η = 1이어도 비근축 η가 0.3~0.6까지 떨어짐([VALIDATION](VALIDATION.md)) |
| P4 Architecture Family | **완료** (PR #65, #66) | ① Coma 보정 곡면(3·4차 Sag) ② Micro-lens + 두 반사면(단일·양쪽 Lens, Aplanatic 두 면 비구면, Silica/Silicon) ③ Lens 정렬 연구 ④ Family 비교·자동 선택 | Gate **통과**(수용 기준: S5 통과, 같은 입력에서 Family별 최선 후보 비교표). S5 Silicon + Silica Lens 비근축 η 0.987~0.988 Computed. S3 0.986~0.998. S1·S4 보정 곡면 0.9999~1.000·0.994~0.999. `families.lens_two_reflector = compare`로 S1·S2a에서 두 Family 비교표, 선택 규칙(η, 0.01 이내면 소자 수). 미착수로 넘김: Cylindrical Lens(S5가 회전대칭 Lens로 통과), Glass 안 Lens(S2b-1550-glass 얕은 IOX는 Fail 유지) |
| P5 특허·설계 산출물 | 예정 | 부호 붙은 특허 Figure, 치수 도면, 후보 보고서, glTF/STL(STEP은 요청 시) | 시나리오별 Figure 세트 일괄 생성 |
| P6 Field Import와 배열 | 미정 | FDTD/측정 Sampled Field 입력, 다채널(S6) | 실제 수요 확인 후 범위 확정 |

## 시나리오 현재 상태 (P4 Gate, 2026-11-25 측정)

| ID | 내용 | 현재(근축 η / 비근축 η → 보정 곡면 η) | 다음 목표 |
|---|---|---|---|
| S1 | SMF → SMF, 90° Fold | Exact 3개, η 1 / 0.32~0.58 → **0.9999~1.000** | — |
| S2a-1310 | SMF-28 → LDW(Sun 2021, 11 × 18 µm) | Near-match 3개, η 0.985~0.995 / 0.91~0.96 → 0.985~0.995 | — |
| S2a-1550 | SMF-28 → LDW(Desmet 2021, 12.8 × 12.1 µm) | Exact 4개(4.68~7.40 mm), η 1 / 0.993~0.999 → 0.999~1.000, 정렬 민감도 3.6~4.3 dB | — |
| S2b-1550 | SMF-28 → IOX(Brusberg 2012, 18.8 × 12.0 µm) | Near-match 3개, η 0.981~0.990 / 0.958~0.986 → 0.980~0.990 | — |
| S2a-1310-glass | 수직 SMF → Fused silica 1.1 mm → 매립 LDW 0.5 mm | Near-match 1개, η 0.983 / 0.916 → 0.956 | — |
| S2a-1550-glass | 수직 SMF → Fused silica 2.0 mm → 매립 LDW 0.5 mm | Exact 4개(3.53~4.60 mm), η 1 / 0.89~0.95 → 0.97~0.98, 정렬 민감도 6.8~8.9 dB | — |
| S2b-1550-glass | 수직 SMF → D 263 1.1 mm → 얕은 IOX 0.02 mm | Fail: 반사면이 상면을 넘음(안내 표시). Lens Family는 Glass 문제에 아직 적용 안 함 | Glass 안 Lens·단일 반사면 Family(범위 결정 필요) |
| S2b-1550-glass-deep | 같은 IOX를 0.3 mm 매립(가정), 2.0 mm | Exact 3개(3.31~3.90 mm), η 1 / 0.79~0.85 → 0.94~0.95 | — |
| S3 | SiPh SSC 3 µm → SMF | Computed: Lens + 두 반사면, 비근축 η 0.986~0.998, Lens 1 dB 편심 0.7 µm | Lens 제작 공차·Active alignment 모델 |
| S4 | PIC Edge → 측면으로 비켜 선 수직 Fiber | q-tensor Near-match 4개, η 0.995~0.9996 / 0.47~0.54 → **0.995~0.999** | — |
| S4-glass | 수직 SMF → Glass → 옆으로 1 mm 비켜 선 매립 LDW(평면 밖) | q-tensor Exact 4개, η 1 / 0.91~0.94 → 0.985~0.991 | — |
| S5 | Laser 1.5 × 3.5 µm → SSC 3 µm | Computed: Silicon Lens + 두 반사면 + Silica Lens, 비근축 η 0.987~0.988, L1 1 dB 편심 0.38 µm | AR 코팅(Silicon 무코팅 투과 0.48), Active alignment 모델 |
| S6 | Channel 배열 → FAU | 지원 범위 밖 | P6 |

비근축 η는 같은 처방(국소 이차곡면)을 근축 근사 없이 계산한 값이다([PHYSICS](PHYSICS.md)). S2 계열은 모두 Port 뒤 공간 제약(기본)을 적용한 값이다. Glass 배치의 두께·깊이·수평 거리는 가정 값이며, 두께에 따른 변화는 [VALIDATION](VALIDATION.md)에 있다. 제약을 끄면 되접힌 배치에서 Exact 해가 더 나온다.
