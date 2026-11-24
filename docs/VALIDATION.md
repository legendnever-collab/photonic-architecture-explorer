# Validation

무엇을 어떤 독립 Reference로 검증했고, 어디까지가 근거인지 정리한다. 세부 기록은 [history/](history/)에 있다.

## 실행

```bash
python -m pip install -e '.[test]'
PYTHONPATH=src python scripts/validate.py          # 물리 Benchmark + 전체 단위 테스트 + SHA 매니페스트
PYTHONPATH=src python -m unittest discover -s tests
python scripts/build_scenarios.py                  # 시나리오 Fixture 재생성과 기대 상태 확인
```

## 검증된 물리 커널

| 커널 | 독립 Reference | 기준 | 기록 |
|---|---|---|---|
| 자유공간 Gaussian(q 전파) | 닫힌 형식 w(z)/R(z), 샘플링 Fresnel 전파 | Field overlap 1e-11, Power 1e-12 | [M1](history/VALIDATION.md) |
| 평면·곡면 반사, q 변환 | 정확한 이차곡면 Ray/Normal 반사, 위상 Mask + Fresnel | Principal power 2e-5 m⁻¹, Profile overlap 1e-10 | [M1](history/VALIDATION.md) |
| Mode Overlap | 해석 사례, 2개 Grid의 복소장 적분 | 1e-12 | [M1](history/VALIDATION.md) |
| 유한 Fan·곡률·배치 진단 | Newton 표면 교차 | 문서 기준 | [M2](history/M2_RESULTS.md) |
| External Adapter(M3A-1) | 계약 테스트 | 거절·미계산 분류 | [M3-A](history/M3A_ADAPTER.md) |
| 두 반사면 Exact-q 설계 | 기존 Adapter로 재평가 | 후보마다 독립 재검사 | [M5-A](history/M5A_AUTONOMOUS_DESIGN.md) |

## P0에서 추가한 검사

| 대상 | 검사 |
|---|---|
| Design Document | 모든 오류를 경로와 함께 보고, 자동 정규화 없음, SI 변환과 출처 보존 |
| Scene | 경로 점 = 엔진 Vertex(1 pm), Beam 반경 = 엔진 평면값(1e-9 µm), 반사면 Footprint 일치, 표면 Grid가 이차곡면 위에 있음 |
| 시나리오 | S1~S6의 현재 상태와 사유를 고정. Fixture가 생성 스크립트와 같은지 확인 |
| API | 엔드포인트, Round trip, 경로 Traversal 거절 |

## P1에서 추가한 검사

| 대상 | 검사 |
|---|---|
| Workspace(브라우저) | `scripts/check_app.py`: 3D 렌더, S1 Design, 2D 도면의 반사면·Port 좌표와 Fold 반사면 거리 = 엔진 Scene(1 nm), 입력 변경 시 결과 무효화, S2b·S3 실패 사유와 다음 단계, 입력 JSON Export 왕복, WebGL 없는 환경의 2D 동작 |
| Frontend 빌드 | CI가 `npm ci && npm run build` 결과와 커밋된 `web/`가 같은지 확인 |
| Windows 패키지 | 파일 SHA 매니페스트, 오염된 환경 변수 무시, `.cmd` 실행, HTTP로 모든 시나리오 결과가 Checkout 엔진과 동일, Edge·Chrome 브라우저 검사 |

## P2에서 추가한 검사

| 대상 | 검사 |
|---|---|
| 닫힌 형식 q 계산 | 무작위 40 사례에서 축별 q 전파·반사와 1D Overlap을 엔진 `Gaussian`·`mode_overlap`과 비교(q 상대오차 1e-11, log η 1e-10) |
| 후보 채택 | 모든 후보를 기존 Adapter로 재평가. Geometry·Model Domain Pass, 3w·\|κ\| ≤ 0.15, Exact는 η = 1(1e-9), Near-match는 0.95 < η < 1 |
| 제약 | Port 반공간, 최소 곡률반경, Envelope(반사면 Patch AABB), Keep-out(주광선 교차)과 엔진 Package 검사 Fail 없음 |
| 재현성·시간 | 같은 입력에서 같은 후보, 시나리오당 15 s 예산(실측 0.2~1.1 s) |
| 화면 | 탐색 지도의 후보 위치 = 결과 a, c(1 nm), Keep-out 추가 후 후보 주광선이 박스를 지나지 않음, Near-match 표시와 안내 |

## P3(1단계, Glass 매질)에서 추가한 검사

| 대상 | 검사 |
|---|---|
| 평면 계면 | Coddington q 배율 vs 정확한 Snell Ray Trace(0/10/25/40°, 대칭 Pencil), 수직 입사 Field 연속, Source·Target 통과의 정·역방향 일관성(q → −q*), 축 기울어짐·TIR 거절, Fresnel 투과 범위 |
| 등가 Port | 상면 위 Port(간격 0)는 MFD 그대로, 곡률 1/n배. 외부 문서는 기존 변환과 완전히 같음 |
| Glass 영역 | 반사면 Patch가 상면 아래·하면 위에 있음(Patch 13×13 Grid 전 점). 외부 Relay일 때 Glass 침범 거절 |
| 장면 | Source 쪽 통과: 첫 구간이 외부, 첫 샘플 반경 = Fiber Waist, 외부 경로 0.1 mm. Target 쪽 통과(역방향 S2a-1550-glass): 마지막 샘플 반경 = Fiber Waist(상대 1e-6) |
| 탐색 여유 | 모든 후보에서 ±5 µm·±1 mrad 자세 검사가 계산됨(입사각 ≤ 69°, 가림 여유). Adapter 재평가에서 가림 거절 없음 |
| 화면 | Glass 카드, 2D 상면 선(Z = 0)과 반사면이 상면 아래, Fold 상면 표시 = 외부 구간 길이(1 nm), 3D Slab, Glass 끄기, 얕은 IOX 안내 |

### Edge(공기) 배치와 Glass 내부 배치 비교

Glass 배치: 수직 SMF-28을 상면 0.1 mm 위에 두고, 도파로는 2 mm 옆, 표의 깊이에 +X 방향으로 매립(모두 가정 값).
굴절률은 Fused silica Malitson(1310 nm 1.4468, 1550 nm 1.4440), D 263 T eco 1.511(Cauchy 외삽 가정, ±0.01).

| 시나리오 | 배치 | 결과 | η | 광경로 [mm] | 입사각 M1/M2 [°] | 정렬 민감도 [dB] |
|---|---|---|---|---|---|---|
| S2a-1310 | 공기 Edge | Near-match 3 | 0.989~0.995 | 4.93~6.26 | 17~27 (같음) | 5.5~6.0 |
| S2a-1310-glass | Glass 1.1 mm, 깊이 0.5 | Near-match 1 | 0.983 | 6.68 | 39.8 / 5.2 | 15.4 |
| S2a-1550 | 공기 Edge | Exact 3 | 1 | 4.68~7.40 | 13~31 (같음) | 3.6~4.3 |
| S2a-1550-glass | Glass 2.0 mm, 깊이 0.5 | Exact 3 | 1 | 3.53~4.60 | 12~24 / 57~69 | 6.8~8.9 |
| S2b-1550 | 공기 Edge | Near-match 3 | 0.981~0.990 | 4.73~6.58 | 16~30 (같음) | 3.7~4.5 |
| S2b-1550-glass | D 263 1.1 mm, 깊이 0.02 | Fail(반사면이 상면을 넘음) | — | — | — | — |
| S2b-1550-glass-deep | 2.0 mm, 깊이 0.3(가정) | Exact 3 | 1 | 3.31~3.90 | 15~24 / 60~69 | 7.9~9.5 |

두께·깊이 탐색(같은 배치, 2 mm 옆): 1.1 mm Glass에서는 S2a-1550과 IOX(깊이 0.1~0.8 mm) 모두 후보가 없고,
2.0 mm에서는 LDW 깊이 0.5 mm, IOX 깊이 0.3 mm 이상에서 Exact가 나온다(IOX 0.2 mm는 Near-match η 0.966). 수평 거리 4 mm는
2.0 mm에서도 후보가 없다. 관찰: Glass 안의 1/n 발산 감소가 Guard 여유로 바로 이어지지 않았다. 수직 입력을 90° 꺾으려면
M2 입사각이 55~69°로 커지고, 두께 안에 두 반사면을 넣으려면 경로가 짧아 곡률이 커진다. 그 결과 정렬 민감도는
공기 Edge 배치의 약 2배다. M2는 입사각이 임계각(약 43.8°)보다 커서 뒤가 공기라면 TIR이 가능하고, M1은 반사 Coating이 필요하다.

## P3(2단계, q-tensor)에서 추가한 검사

| 대상 | 검사 |
|---|---|
| 대수 | 분리형 Gaussian Overlap(Offset·기울기 포함)이 엔진 `mode_overlap`과 일치(1e-10). 회전된 비점수차 Beam의 Overlap을 2D 직접 적분과 비교(1e-8). 폭 맞춤 해 4개가 요구 폭을 재현(1e-9) |
| 동일평면 환원 | S2a-1550의 여러 (a, c)에서 Tensor 해의 곡률·3w·\|κ\|가 기존 Branch와 일치. 180° 돌린 Target 축(축 회전 경로)도 같은 해 |
| 비동일평면 | S4 정확한 해가 Target Mode로 닫힘(η = 1). 실제 곡면 광선의 Ray-transfer 행렬이 같은 Q를 재현(상대 1e-6), Symplectic(1e-6). 문제 전체를 임의 회전해도 해가 같음 |
| 설계 | S4 후보 3개 이상, 모두 Ray 검산 통과, 정렬 공차 계산, 장면 경로가 두 Port에서 닫히고 Beam 타원 표시 |
| 화면 | S4 2×2 도면 좌표가 장면과 1 nm 이내, Beam 타원, q-tensor 안내 |

## P3(3단계, 비근축 검산)에서 추가한 검사

| 대상 | 검사 |
|---|---|
| 자유공간 | 평면 반사면 두 개에서 광선 방식 = 각스펙트럼 직접 적분(Waist 20·5·2 µm). 발산각이 작으면 근축 결과(1 − η < 1e-5)로 수렴, 발산각이 커질수록 단조 감소 |
| 수차 | 같은 반사면 두 개의 Z형 배치는 비근축 η > 0.999, 같은 방향으로 꺾는 S1은 근축 η = 1이지만 비근축 η < 0.7 |
| 통합 | 모든 후보가 수렴(격자 변화 < 1e-4), "비근축 Overlap 최대" 역할은 최고값 후보에. q-tensor·Glass 후보도 재계산과 일치 |
| Guard 밖 | S3은 후보 없이 연구 결과(근축 Exact 설계 3개)만 표시 |

### 근축 η와 비근축 η

| 시나리오 | 근축 η | 비근축 η | 비고 |
|---|---|---|---|
| S1 | 1 | 0.32~0.58 | 두 반사면이 같은 방향(22.5° + 22.5°)으로 꺾어 Coma가 더해짐 |
| S2a-1310 | 0.985~0.995 | 0.91~0.96 | |
| S2a-1550 | 1 | 0.993~0.999 | 입사각 13~31°, 근축 결과가 맞음 |
| S2b-1550 | 0.981~0.990 | 0.958~0.986 | |
| S2a-1310-glass | 0.983 | 0.916 | 상면 통과는 근축 |
| S2a-1550-glass | 1 | 0.89~0.95 | M2 입사각 57~69° |
| S2b-1550-glass-deep | 1 | 0.79~0.85 | |
| S4 | 0.995~0.9996 | 0.47~0.54 | 평면 밖 90° 전환 |
| S4-glass | 1 | 0.91~0.94 | |
| S3(Guard 밖 연구) | 1 | ≤ 0.12 | 후보 아님, 3w·\|κ\| 0.44~0.58 |

관찰: 3w·|κ| ≤ 0.15 Guard 안이어도 국소 이차곡면 반사면은 경사 입사 Coma 때문에 근축 η를 크게 밑돌 수 있다. 두 반사면이
반대 방향으로 꺾고 수차가 상쇄되는 배치에서만 근축 결과가 유지된다. 따라서 근축 η = 1은 "이 처방이 좋다"는 근거가 아니며,
비근축 η를 함께 봐야 한다. Coma를 없애는 고차 곡면 처방을 P4 1순위로 올렸다.

## 근거의 한계

- 후보 생성은 Scalar Paraxial Gaussian(동일평면은 분리형, 비동일평면은 2×2 q-tensor) 범위다. Glass는 평면 상면 하나와 균질 굴절률만 모델링한다.
- Guard(발산각 0.1 rad, 3w·|κ| 0.15)는 Screening 규칙이며 오차의 엄밀한 상한이 아니다. 비근축 검산에서 Guard 안의 후보도 Coma로 η가 크게 떨어질 수 있음을 확인했다.
- Total Coupling, Vector Field, 조립 공차·수율, 전체 Package Clearance, 특허성은 Uncomputed다.
- 비근축 검산은 Scalar·기하광학 반사(Debye 방식)이며 Aperture 모서리 회절, 편광, Fresnel 계수는 포함하지 않는다. 이전 Physical Optics·Vector 연구 산출물은 [archive/wave-research](../archive/wave-research/README.md)에 보관했다.
