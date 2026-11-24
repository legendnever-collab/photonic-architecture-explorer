# Decision Log

새 항목을 위에 추가한다. 항목당 10줄 이내: 새로 가능해진 설계 판단, 주요 기술 선택, 남은 한계.
2026-11-24 이전의 Milestone 기록(M1~M7-R28)은 [history/](history/)에 있다.

## 2026-11-25 · P4b 종료, v0.4.0 Release (PR #67 병합)

- **사용자 결정**: Cylindrical Lens는 하지 않고 병합·Release. 근거: Port 바로 앞 Lens의 1 dB 편심 허용치 ≈ 0.48 × 그 축의 Port Waist로
  Lens 형태와 무관하다(S3 0.7 µm, S5 빠른 축 0.38 µm와 일치). S5는 이미 η 0.988이며 타원 보정은 반사면이 한다.
- **다음**: P5 특허·설계 산출물(순서는 사용자 피드백으로 확정).

## 2026-11-25 · P4b ② Glass 안 Lens 검토 → 배치 What-if (`phase/p4b-deferred`)

- **결론**: S2b-1550-glass는 Lens로 풀리지 않는다. 원인은 마지막 반사면이 얕은 도파로(20 µm) 축 위 86 µm 안에 있어야 하고 그 입사각이 70°를 넘는 것.
  Micro-lens는 Fiber–상면 0.1 mm에 들어갈 수 없고, 상면 곡면 Lens는 발산각 Guard에 먼저 걸린다(실험 후 코드 미반영).
  반사면 Aperture를 상면에서 잘라도(1e-6 꼬리 안) 결과가 같아 정책을 바꾸지 않았다.
- **가능해진 판단**: Glass Fail에서 어떤 가정 배치를 얼마나 바꾸면 되는지. S2b: 매립 깊이 0.3 mm, 두께·Fiber 높이는 무효. `/api/whatif`, 화면 버튼(수십 초, Opt-in).

## 2026-11-25 · P4b ① 동시 오차와 Active alignment (`phase/p4b-deferred`)

- **가능해진 판단**: Passive 조립이 되는지, 어느 소자를 Active 정렬해야 하는지. S1 Passive 90 % 31.7 dB(1 dB 이내 6 %) → M1 위치 Active 0.01 dB.
  S3 Passive 1 dB 이내 13~17 % → Active 0.06~0.08 dB. S5 → M2 기울기 Active 0.36~0.44 dB.
- **모델**: 주광선 Jacobian + 정확한 Gaussian 위치·각도 Overlap(크기·초점 변화 제외). 비근축 계산과 15 % 이내로 확인.
- **가정**: 공차 기본값과 고정 이동, 보정 범위(50 µm, 20 mrad)는 가정값이며 Design Document에서 바꾼다.

## 2026-11-25 · P4 Gate 통과, P4 종료 (PR #66 병합)

- **수용 기준**(재설계 계획): S5 통과, 같은 입력에서 Family별 최선 후보 비교표. 둘 다 충족(S5 Computed 0.987~0.988, `families[]` 비교표).
- **시나리오**: 12개 중 11개 Computed, S2b-1550-glass(얕은 IOX, Glass)만 Fail. 전 시나리오 기대값 일치(`build_scenarios.py`).
- **넘긴 항목**: Cylindrical Lens(S5가 회전대칭 Lens + 토로이드 반사면으로 통과해 필요성 낮음), Glass 안 Lens Family,
  Active alignment·동시 오차 공차. 다음 Phase 순서는 사용자 피드백으로 정한다(P5 특허·설계 산출물 예정).

## 2026-11-25 · P4 4단계: Lens 정렬 연구, Family 비교·자동 선택 (`phase/p4-family-selection`)

- **가능해진 판단**: Lens 후보의 편심·축 방향·기울기 손실과 1 dB 허용치(S3 0.7 µm, S5 L1 0.38 µm), 두 Family의 η·정렬 공차·소자 수 비교.
- **선택 규칙**: 최종 η 최고, 단 0.01 이내면 소자가 적은 Family. 정렬 공차는 규칙에 넣지 않고 표로 보여 준다(판단은 사용자).
- **스위치**: Design Document `families.lens_two_reflector` = auto(기본) / compare / off. compare는 S1·S2a에서 두 반사면을 그대로 선택.
- **관찰**: Lens는 반사면 정렬 민감도를 크게 줄인다(S1 5.67 → 0.70 dB) 대신 Lens 편심 1 dB 허용치 약 2 µm가 생긴다.
- **한계**: 다른 소자를 다시 맞추는 Active alignment, 제작 공차 분포, 동시 오차는 계산하지 않는다.

## 2026-11-25 · P4 3단계: 고NA Lens, 재료, Lens 가림 (`phase/p4-family-selection`)

- **가능해진 판단**: S5(Laser 0.556 rad → SSC)가 Silicon Lens + 두 반사면 + Silica Lens로 Computed(비근축 η 0.987~0.988, 수렴).
- **재료**: Port 발산각 0.39 rad 이하 Fused silica(Malitson), 넘으면 Silicon(Li 1980, λ ≥ 1.2 µm). 무코팅 Fresnel 투과는 정보로만.
- **맞춤**: 광선 부채꼴을 단계적으로 넓히고, 최대 출사 방향 오차로 해를 고름. Clear 구경은 방향 오차 1 mrad 이내 광선까지.
- **검산 수정**: 잘린 광선 옆 Jacobian을 한쪽 차분으로. Hard aperture가 있는 경우 격자 수렴이 정상화(기존 값 변화 ≤ 2e-3).
- **가림**: 다른 구간 Beam과 반사면이 Lens 몸체를 지나면 제약 위반. θ'는 0.005 → 0.0075 → 0.01 순으로, 채택이 나오면 멈춤.
- **한계**: Lens 공차·코팅·분산 미계산. S5 Design 약 35 s.

## 2026-11-24 · P4 2단계 채택 정책: Lens Family를 Computed로 (`phase/p4-coma-correction`)

- **사용자 결정**: Lens Family 후보를 Computed로 올린다. 채택 = 비근축 검산 수렴 ∧ η ≥ 0.95(P4 Gate와 같음) ∧ Lens 몸체가 Keep-out·Envelope 안.
- **범위**: Lens 없는 두 반사면이 발산각 Guard로 실패했을 때만 돈다. 결과 Computed, Family `lens_two_reflector`, 사유 `Lens Family: …`. S3 → Computed(3개).
- **유지**: Frozen Guard(0.1 rad 등)는 그대로다. Lens 뒤 등가 Port가 Guard 안에 있고, Guard 밖인 Lens 구간은 비근축 검산이 판정한다.

## 2026-11-24 · P4 2단계: Lens Family 검토 후보 (`phase/p4-coma-correction`)

- **가능해진 판단**: S3처럼 발산각 Guard를 넘는 Port에서 두 면 비구면 Micro-lens + 두 반사면 배치와 그 비근축 η를 3D/2D로 본다.
  S3 비근축 η 0.984~0.997(3개 모두 수렴). 결과 상태는 Fail 그대로이며 후보는 `lens_review`에만 있다(사용자 결정: 검토 후보로 둠).
- **원리**: Aplanatic 맞춤(평행 출사 + Abbe 사인 조건, EFL·FFD 유지 Bending), 1/e² 각 2.6배까지 맞춰 방향 대응이 접히지 않게 함.
  θ'는 0.005 rad(Lens가 Port에서 Rayleigh 거리 36배). 반사면은 P4 1단계 보정 곡면을 그대로 씀.
- **고친 것**: 비근축 접힘 판정이 잘린 광선 경계의 차분을 접힘으로 세던 문제. 자오면 추적이 Bending을 빠뜨리던 버그.
- **한계**: S5(0.556 rad)는 단일 Lens 한계(0.39 rad) 밖. Lens와 다른 구간 Beam의 가림, Lens 공차·코팅·분산 미계산. S3 Design 시간 약 22 s.

## 2026-11-24 · P4 2단계 착수: Micro-lens 변환기 (연구 중, 화면 미연결)

- **목표**: 발산각 Guard를 넘는 Port(S3 SSC, S5 Laser)를 평볼록 비구면 Micro-lens로 확대해 Guard 안의 등가 Port를 만들고, 기존 두 반사면 탐색으로 Relay를 설계.
- **구현**: 비근축 추적에 회전대칭 비구면 굴절면 추가(평행 평판 측면 이동·근축 행렬·등광로 Collimator 검증). 등가 Port 변환, 렌즈+반사면 전체를 비근축 η로 맞추는 Runner.
- **첫 결과(S3)**: 단일 비구면 등광로 Collimator로 시작하면 전체 비근축 η 0.71, 렌즈 비구면 재조정 후 최고 0.87(미수렴). 한 면만 비구면이면 등광로와 Sine 조건을
  동시에 못 맞춰 각스펙트럼 진폭이 찌그러지는 것이 한계로 보인다. 다음: 두 면 비구면(Aplanatic) 렌즈, 계산 시간 단축(현재 70 s), 그 뒤 화면 연결.
- **정책**: 이 Family의 후보는 비근축 검산으로만 채택하게 되므로, Computed로 셀지는 사용자 결정 사항으로 남긴다.

## 2026-11-24 · P4 1단계: Coma 보정 곡면 (`phase/p4-coma-correction`)

- **가능해진 판단**: 근축 설계를 그대로 두고 반사면에 3·4차 Sag(반사면당 9계수)를 더해 Coma를 없앤 처방과 그 비근축 η를 본다.
  S1 0.32~0.58 → 0.9999~1.000, S4 0.47~0.54 → 0.994~0.999(P4 Gate 통과). Glass 가파른 입사 배치는 0.94~0.99로 오르나 보정량이 크고 수렴 판정이 1e-4를 넘는다.
- **원리**: 선형 위상 모델(2δh·cosθ)로 계수 단계를 제안하고 정확한 재추적으로 채택·보폭 축소, 모델이 빗나가면 정확한 Overlap을 직접 최대화.
  3차 이상 항은 근축 Relay를 바꾸지 않으므로 기존 검산은 유효. 방향 대응이 접히면 Invalid. 보정 곡면은 공간 제약을 다시 검사.
- **정책**: "비근축 Overlap 최대" 역할은 보정 곡면까지 포함한 값으로 정한다. Guard·후보 채택 기준은 바꾸지 않았다.
- **보정 크기·공차**: 1/e² 발자국 안 보정 Sag는 PV 0.01~0.9 µm(모서리 4w에서만 수십 µm), 보정 곡면의 비근축 정렬 손실은 근축 공차와 일치.
- **한계**: 표면 오차와 실제 제작 공정 적합성은 계산하지 않는다. 시간은 Glass 배치에서 최대 약 20 s.

## 2026-11-24 · P3 2·3단계: q-tensor와 비근축 검산 (`phase/p3-glass-media`)

- **q-tensor**: 비동일평면·축 회전 Port는 2×2 복소 q로 푼다. 정확한 해는 2차 모멘트 식의 닫힌 해(최대 4 Branch), Near-match는
  3w·|κ| Guard를 매개변수에 넣은 6변수 최적화. 채택은 실제 곡면 광선의 4×4 Ray-transfer 행렬이 같은 q를 재현할 때(1e-6)만. 동일평면에서는 기존 Branch와 일치.
- **비근축 검산**: 두 Mode의 Scalar 각스펙트럼 + 실제 곡면 광선(Debye 방식). 자유공간 직접 적분과 1e-11 일치, Z형 배치 Coma 상쇄를 재현.
  모든 후보에 비근축 η를 붙이고 "비근축 Overlap 최대" 역할을 추가했다. Guard·채택 기준은 바꾸지 않았다.
- **결과**: 국소 이차곡면 처방은 같은 방향으로 꺾는 배치(S1, S4)에서 Coma가 커서 근축 η = 1이어도 비근축 η 0.3~0.6이다.
  P4 1순위를 Coma 보정 곡면(Conic·Freeform)으로 올린다. S3는 Guard 밖 연구만 표시(최고 비근축 η 0.12), 후보 아님.

## 2026-11-24 · P3 1단계: Glass 매질 (`phase/p3-glass-media`)

- **가능해진 판단**: 수직 SMF → Glass 상면 → Glass 안 두 반사면 → 매립 도파로 배치를 공기 Edge 배치와 같은 화면·지표로 비교한다.
  LDW는 2.0 mm Glass(깊이 0.5 mm)에서 Exact 3개, 1.1 mm에서는 1310 nm Near-match(η 0.983)뿐이다. 깊이 20 µm IOX는 Target 축 위
  반사면이 상면을 넘어 이 Family로는 안 되고(0.3 mm 매립 가정 시 Exact), Glass 배치의 정렬 민감도는 공기 Edge의 약 2배다.
- **원리**: 외부 Port를 상면에서 굴절한 등가 Port(Snell, Coddington q 배율)로 바꾸고, 엔진은 Glass 굴절률의 균질 매질로 변경 없이
  푼다. 반사면은 Glass 안에만 둔다. 외부 구간은 장면 앞·뒤에 붙이고 Fresnel 투과·TIR 가능 여부는 참고로만 표시한다.
- **탐색 정책 `P3-CONTINUOUS-2`**: Beam 가장자리(1e-6 꼬리 반경)가 다른 반사면의 조사 영역을 지나지 않을 것, 주광선 가림은 Patch를
  10 µm + 2 % 키워 검사, 입사각 1° 여유(정렬 검사가 Guard 안에서 돌도록), Near-match 시도 최대 256개. 공기 시나리오 결과는 그대로다.
- **한계**: 평면 상면 하나, 균질 굴절률, 하면은 평행. 반사면 뒤 매질·Coating, AR, 상면 오차, 이온 교환 굴절률 분포는 Uncomputed.

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
