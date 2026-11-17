# M6-G — Two-Port Workflow Acceptance & Input Readiness

2026-11-17 KST. 실제 Port 데이터가 제공되지 않아 Synthetic 입력으로 검증했다.
Desktop은 Chromium 1440×1050, Mobile은 Chromium 393×852 Viewport다.
사용자가 이 Workspace를 직접 조작한 피드백은 제공되지 않았다. 아래 결함과
관찰은 자동화된 Browser 검토, 화면 점검, Export 검산에서 나온 결과다.

## 원격 기준 및 병합 관계

| 대상 | HEAD | CI | 주요 증거 |
|---|---|---|---|
| Main | `c3c66585d089c1c3c8a8a385dee192e18f89aec8` | [44018242353](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44018242353) | [세 Frozen 사례](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44018242353/artifacts/14299118316) |
| M6-E [Draft #22](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/22) | `e1434e7018b4288e0d952ed7e40d3b3e8c23dc2a` | [44018850475](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44018850475) | [세 Frozen 사례](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44018850475/artifacts/14299972604) |
| M6-F [Draft #23](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/23) | `b3c3726c53fcde7cb9dd0e0a3f9b52eb538e7488` | [44023496474](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44023496474) | [Frozen 사례](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44023496474/artifacts/14302142062), [Workspace](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44023496474/artifacts/14302127184) |

세 CI는 모두 4 jobs 성공이다. 표의 ZIP 4개는 내려받아 API SHA256과 대조했다.
두 Draft의 Base 및 Merge Base는 위 Main이다. #22의 변경은 Reference Gate 문서,
기존 Chief-Ray 증거 JSON, 다음 지시문에 한정된다. #23은 Workspace, Report,
Regression 및 문서 변경이다. 두 변경은 독립적이며 #23과 Main의 Merge Tree를
충돌 없이 생성했다. M6-E 결론은 **Reference Not Ready**다. #22의 변경 없이
#23을 통합할 수 있다. M6-G Draft는 #23을 Base로 하며, 승인 시 #23과 이 수정분을
차례로 통합할 수 있다. 최종 HEAD와 CI 및 Artifact 링크는 M6-G Draft에 기록한다.

## Workflow Acceptance

| 입력 | 결과 | Software evidence |
|---|---|---|
| Frozen equal-q | `Computed` · G009-B1 | 56개 유효 후보, 대안 G015-B1 / G036-B1 |
| Frozen different-q | `Computed` · G009-B1 | 60개 유효 후보, 대안 G016-B1 |
| Frozen high-divergence | `Fail` · 추천 없음 | 0.1 rad 초과로 탐색 전 중단. Overlap은 `Uncomputed` |
| M6-F XY-fold | `Computed` · G008-B1 | 빈 화면에서 숫자 18개, Design 한 번. λ₀=1310 nm, n=1, 두 방향 +X, Target (2,2,0) mm, MFD 20 µm, Phase 곡률 +50/−50 m⁻¹ |

- CLI와 Workspace의 세 Frozen 결과를 `validate_m5f.py`로 대조했다. Main, #22,
  #23의 원격 세 Design JSON은 사례별로 바이트까지 일치한다. 로컬 대조에서
  different-q의 `aperture_tail_union_estimate` 한 값만 3.95×10⁻³¹ 이내의
  roundoff 차이가 있었다. Input SHA, 후보, 상태 및 설계 수치는 일치한다.
- Mirror, Curvature, Solver, 최적화 방식 입력 없이 Design을 실행했다. XY-fold의
  sagittal +Z는 +X와 Source→Target 변위의 평면 법선이다. 복소 Mode가 두 축에서
  동일할 때만 자동 축을 사용한다. 명시 +Z와의 비교에서 후보 순서, Geometry,
  Domain, Nominal Mode Match가 일치했다. 축 출처는 Input Snapshot에 남는다.
- Phase 누락, 축 미제공 Elliptical Mode, 공선으로 인한 Fold Plane 모호성은
  `Uncomputed`다. Skew, Rolled, 잘못된 방향 및 High Divergence는 `Fail`이다.
  이 상태에서는 후보와 Overlap을 표시하지 않는다. 명시 q는 Advanced 입력에 있다.
- Port를 편집한 즉시 이전 결과와 HTML/JSON 저장 버튼을 숨겼다. 다시 Design한
  Input SHA와 Fixed Target Plane은 새 Position을 반영했다. Desktop에서 편집 후
  대안 G017-B1, Mobile에서 equal-q 대안 G015-B1, 별도로 XY-fold G008-B1의
  HTML/JSON/A4를 확인했다. 같은 Export에서 선택 후보, SHA, 경로 길이, Nominal
  Overlap 및 미계산 범위를 확인했다. 대안 ID는 `viewed_candidate_id`로 보존한다.

## Recommendation 검산

Frozen equal-q의 56개 유효 후보를 기존 Overlap 구간과 광경로 정책으로 검산했다.
세 대표 후보는 동일한 최상위 구간에 있고, 표시 정밀도에서 Nominal Mode Match는
모두 100%다. 반사 법칙, Fixed Port Closure, 구간 길이 및 q 전파는 기존 독립
검산을 통과한다. 수치는 Synthetic scalar Gaussian 모델 범위다.

| 후보 | 광경로 [mm] | 최대 투영 빔 반경 [µm] | Max 3w·κ | 선택 의미 |
|---|---:|---:|---:|---|
| G009-B1 | 3.728 | 80.65 | 0.100158 | 최상위 Overlap 구간의 최단 광경로 |
| G015-B1 | 4.000 | 74.58 | 0.079100 | 광경로 +0.272 mm, 최대 반경 −6.07 µm |
| G036-B1 | 20.840 | 296.62 | 0.078205 | Max 3w·κ 최저. G015-B1보다 0.000896 낮고 광경로 +16.840 mm |

0.15는 기존 Gaussian Guard다. Guard 여유는 모델 적용성 지표다. Nominal Mode
Match는 정규화된 Gaussian 필드 형상 중첩이며 Total Coupling은 `Uncomputed`다.

## 확인된 결함과 수정

| 관찰 | 변경 |
|---|---|
| #23에서 Elliptical → Rotation-symmetric만 선택하고 제출하면 기존 `[16,24] µm`가 `[16,16] µm`로 바뀌고 `Computed`가 됐다. | 다른 Mode 표현을 선택하면 해당 표현의 숫자 칸을 비운다. 입력을 다시 채우기 전에는 `Uncomputed`다. 기준면과 Phase 입력 안내를 보강했다. |
| 대안의 상단 설명에서 Model Guard 여유의 수치 차이는 상세 화면에 있었다. | 추천 대비 최대 투영 빔 반경과 Max 3w·κ 차이, Guard를 바로 표시한다. 후보 생성·순위와 수치는 기존 값을 쓴다. |
| A4에서 Perturbed Mode Overlap과 Patentability 상태가 빠졌다. | 두 상태를 A4에도 `Uncomputed`로 표시하고 PDF 텍스트를 비교했다. |

미해결 사용성 검증은 실제 사용자가 자기 Port의 Phase 및 기준면 자료를 확인해
입력하는 과정과 실기기 모바일 저장·인쇄다. 이번 검증은 Browser Viewport와
Chromium PDF에 해당한다. Mode를 바꾸면 선택한 표현의 숫자를 다시 입력하는
동작을 의도적으로 적용했다. 공선 입력에서 Fold Plane 선택은 사용자의 공통
Sagittal Axis에 의존한다. 이 값은 측정 또는 설계 정의를 확보해야 한다.

## Actual Input Readiness Checklist

| 구분 | 확인할 항목 |
|---|---|
| 필수 · 공통 조건 | Vacuum Wavelength λ₀ [nm 또는 m], 동일한 homogeneous external ambient n [무차원], right-handed 공통 World Frame. |
| 필수 · 각 Fixed Port | External Plane ID/side/frame, World XYZ 원점 [mm 또는 m], 전파 단위벡터. Source의 출사 방향과 Target의 도착 방향을 같은 전파 계약으로 기록한다. |
| 필수 · 각 Mode | 해당 External Plane의 1/e² intensity MFDₜ,ₛ [µm 또는 m]와 wavefront 1/Rₜ,ₛ [m⁻¹], 또는 ordinary complex qₜ,ₛ [mm 또는 m] 중 하나. Flat Phase는 명시적 0. 축별 크기·Phase가 다르면 실제 Sagittal Axis를 함께 제공한다. |
| 필수 · 의미와 출처 | 측정·시뮬레이션·공급사 또는 명시 가정, 단위, Plane과 불확도. 모델의 scalar polarization 처리와 Gaussian Fit 근거를 기록한다. 실제 Mode 적용성 판단에는 동일 Plane의 complex amplitude·phase, fit residual 및 grid/window 수렴이 필요하다. |
| 선택 · Package/제작 | 공통 Frame의 Available Volume, Keepout, Body Envelope 및 Clearance. 허용 Vertex/Normal/Curvature/Aperture, 재료·Coating·Surface figure, 조립 오차와 환경 조건을 제공할 수 있다. 현재 자동 설계에는 두 Reflector를 직접 입력할 필요가 없다. |

Plane 원점과 법선은 해당 면의 Position/Direction으로 지정할 수 있고, 유일한
Coplanar Fold와 rotation-symmetric complex Mode가 확인되면 Sagittal Axis와
`t = s × d`를 산출할 수 있다. 명시된 MFD와 Phase를 q로 변환할 수 있다. 실제
Field, Phase, 비대칭 Mode 축, 기준면 이동에 따른 Mode 변환, 외부 n, 계면·코팅
손실은 자료로 확인한다. Guided MFD/유효굴절률을 External Gaussian에 대입하지
않는다. 명시된 측정 출처와 별도 Plane ID는 기존 Engineering JSON 계약을 따른다.

입력이 확보되면 Input Contract, coplanarity 및 divergence, Fixed-Port 경로,
가드 범위의 Nominal Mode Match와 후보 Trade-off를 평가할 수 있다. 공급된
Package AABB의 범위 내 검사도 가능하다. Off-vertex Field, Perturbed Mode
Overlap, 실제 Assembly Tolerance, Package Yield, Total Coupling 및 Patentability는
`Uncomputed`다. Actual Applicability도 별도 실제 Field 및 적용성 증거가 필요하다.

## 재현과 다음 우선순위

```bash
python -m pip install -e '.[test]'
python scripts/validate.py
python scripts/validate_m5a.py --output-dir results/runtime-m6g-m5a
python scripts/validate_m5f.py --output-dir results/runtime-m6g-m5f
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install --with-deps chromium
# PDF 검증에는 poppler-utils와 fonts-noto-cjk 필요.
node scripts/check_workspace.cjs results/runtime-m6g-workspace results/runtime-m6g-m5a
node scripts/check_m5f_print.cjs results/runtime-m6g-m5f
```

Workspace Artifact의 `browser.json`은 두 Viewport의 Mode 전환, Export 후보와
Input SHA를 기록한다. `design.*`와 `candidate-review.pdf`는 Desktop 대안,
`mobile-alternative.*`는 Mobile 대안, `round-design.*`와 `round-review.pdf`는
XY-fold다. 세 Frozen 사례는 `acceptance.json`과 각 사례의 HTML/JSON/A4로 재현한다.
다음 개발 우선순위는 비기밀 실제 Fixed Port 한 쌍의 기준면과 Complex Mode 증거
확보다. 이 입력으로 먼저 기존 모델 Domain을 검사하고, 적용 가능하면 사용자
직접 입력과 후보 검토를 진행한다. M6-E Reference 연구는 독립 증거 확보 후 재개한다.
