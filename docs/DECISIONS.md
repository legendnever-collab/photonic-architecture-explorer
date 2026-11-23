# Decision Log

새 항목을 위에 추가한다. 항목당 10줄 이내: 새로 가능해진 설계 판단, 주요 기술 선택, 남은 한계.
2026-11-24 이전의 Milestone 기록(M1~M7-R28)은 [history/](history/)에 있다.

## 2026-11-24 · P0 정리와 기반 (`phase/p0-foundation`)

- **가능해진 판단**: 시나리오 S1~S6에서 현재 엔진이 어디까지 답하는지 한 번에 확인할 수 있다. S2a·S2b(SMF → LDW/IOX)는
  고정 Exact-q Family(거리 비율 5개)에서 후보가 없다는 것이 수치로 확인됐다. 대표 거절 사유는 실수 Exact-q 해 부재,
  3w·|κ| > 0.15, 입사각 > 70°다. 11개 배치를 훑었을 때 S2a-1310 한 경우만 Guard 경계(0.150)에서 통과했다. → P2 연속 탐색의 근거.
- **Design Document `pae.design/1`**: mm·µm·nm 단위와 Port별 출처(placement/mode/phase)를 가진 단일 입력 기록.
  정규화나 기본값 없이 기존 M3A-1 계약으로 변환하고, 엔진은 변경하지 않았다.
- **Scene**: 화면은 계산하지 않고 엔진 결과(Vertex, 곡률, Aperture, Beam 샘플, 반사면 Grid)만 그린다.
  테스트는 경로 좌표를 1 pm, Beam 반경을 엔진 평면값과 1e-9 µm 이내로 비교한다.
- **API**: 표준 라이브러리 HTTP(`pae-app`, Loopback 전용), `/api/preview`·`/api/design`·`/api/presets`·`/api/scenarios`.
- **Preset**: 공개 Mode Library(M7-R1)의 SMF-28, LDW(Sun·Desmet·Lee), IOX(Brusberg)와 Synthetic SSC.
  Flat Phase와 축 대응(t = vertical)은 가정으로 표시한다.
- **보관**: M4-C, M7-R11~R20 Wave/FDTD 연구물은 `archive/wave-research/`로, Milestone 문서는 `docs/history/`로 옮겼다.
  R5~R9·R12·R20 자료는 기존 Workspace가 쓰므로 P1에서 함께 정리한다.
- **한계**: P0 화면은 임시 API Console이다. 기존 Workspace(`pae-workspace`)와 CI 검사는 P1까지 유지한다.
