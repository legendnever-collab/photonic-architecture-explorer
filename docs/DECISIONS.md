# Decision Log

새 항목을 위에 추가한다. 항목당 10줄 이내: 새로 가능해진 설계 판단, 주요 기술 선택, 남은 한계.
2026-11-24 이전의 Milestone 기록(M1~M7-R28)은 [history/](history/)에 있다.

## 2026-11-24 · P2 후보 생성 v2 (`phase/p2-candidate-search`)

- **가능해진 판단**: 최우선 시나리오 S2a·S2b(SMF → LDW/IOX)에서 서로 다른 후보 3개씩을 비교할 수 있다. S2a-1550은 Exact 3개,
  S2a-1310·S2b는 Guard 안 Near-match 3개(η 0.981~0.995)다. "Exact 해가 Guard를 얼마나 넘는지"(3w·|κ| ≥ 0.166, 0.175)도
  수치로 보여서, Glass 내부 배치(P3)가 왜 다음 과제인지 근거가 생겼다.
- **원리**: 두 동일평면 반사면은 a(Source→M1), c(M2→Target) 두 길이만 자유롭다. 고정 8×8 대신 (a, c)를 64×64 로그 격자로
  전부 훑고(닫힌 형식 q 계산, 축별 Exact 가지 4쌍), 목표별 Nelder–Mead로 다듬는다. Exact가 없을 때만 축별 L-BFGS-B로
  Guard 안 Overlap을 최대화한다. 채택은 항상 기존 Adapter(`evaluate_external`)가 결정한다. 계산 시간은 시나리오당 0.2~1.1 s다.
- **순위**: 최단 광경로, Guard 여유, 작은 Beam, 완만한 곡률(최대 |κ|), 정렬 공차(반사면 ±5 µm·±1 mrad 최악 손실), 최대 Overlap.
  같은 후보가 여러 목표에서 최선이면 역할을 합쳐 표시하고, 3개가 안 되면 "Pareto 대안"으로 채운다.
- **제약**: Port 본체 반공간(기본 켬), Package Envelope, Keep-out과 여유, 최대 입사각(≤ 70°), 최소 곡률반경. Envelope·Keep-out은
  엔진 Package 검사에도 전달되어 독립적으로 다시 확인된다. Frozen Guard는 완화하지 않았다.
- **화면**: 제약 입력 카드, 3D·2D의 Envelope·Keep-out 표시, (a, c) 탐색 지도, 후보 종류·역할·정렬 민감도 열, 해석과 다음 단계 안내.
- **한계**: 정렬 민감도는 주광선 Pointing만 반영한다(q 변화 제외). Near-match는 Guard 경계(3w·|κ| = 0.15)에 붙는다.
  `pae-design` CLI는 기존 M5-A 정책을 회귀 기준으로 유지한다.

## 2026-11-24 · P1 3D/2D 시각 Workspace (`phase/p1-visual-workspace`)

- **가능해진 판단**: Port를 표나 3D Gizmo로 배치하면서 Guard를 바로 확인하고, 후보를 3D(반사면 Sag·Beam 튜브)와
  2D(XY·XZ·YZ 정투상, 광로 길이·입사각·곡률반경 치수, Fold 전개 Beam Envelope)에서 비교한다. 실패하면 사유, 임계값,
  다음 Phase와 거절 사유 분포가 보인다(S2b: 91%가 3w·|κ| > 0.15).
- **기술 선택**: TypeScript + Vite + three.js 0.187, 빌드 결과는 패키지 `web/`에 커밋(사용자는 Node 불필요, CI가 재빌드
  결과 일치를 확인). 화면은 엔진 Scene만 그리고, Beam·Mode 반경만 표시 배율을 쓰며 배율을 화면에 적는다.
- **결과 무효화**: 입력이 바뀌면 이전 결과를 도면에서 숨겨 입력과 결과가 섞이지 않게 했다.
- **검사**: `scripts/check_app.py`(Playwright) — 도면 좌표·Fold 거리 = 엔진 값(1 nm), 결과 무효화, 실패 화면, Export, WebGL 없는 환경.
  Windows 패키지는 Edge·Chrome 채널로 같은 검사를 하고, 모든 시나리오 결과가 Checkout 엔진과 같은지 확인한다.
- **정리**: 기존 Workspace·Inspector·HTML 보고서·Near-match 작업·Envelope 화면을 `archive/legacy-workspace/`로 옮겼다.
  엔진 함수(`visible_overlap`, `review_cases`, `review_snapshot`)는 옮겨 두었다. `pae-design`은 JSON만 쓴다.
- **한계**: Package Envelope·Keep-out 입력 화면은 아직 없다(P2 제약 탐색과 함께). 2D 치수는 자동 배치라 겹칠 수 있다.

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
- **한계**: P0 화면은 임시 API Console이었다(P1에서 교체).
