# M7-R13 — 1310 nm Glass Target의 수광 범위

**판정.** 고정 Glass Port에는 수용 Mode와 외부 기준면이 정의되어 있다. 이 Port에 대응하는 실제 수광면·Pupil·수집 NA는 제공된 자료에서 확인되지 않았다. R12의 192 µm half-window η는 **0.989810812816**으로 재현됐다. R10 전체면 η의 존재와 절대 수치 불확도 U는 미확정이다. 0.99 목표, M2 ±1 mrad 광학 응답 및 실물 Total Coupling은 **Uncomputed**다.

## 어떤 입력이 수광을 정의하는가

| 근거 | 확인된 양 | 적용 범위 |
|---|---|---|
| [R5 Guide 모델](../references/m7r5/case.json) 및 [Field 기록](M7R5_SINGLE_PORT_FIELD.md) | 무코팅 이상 Facet의 공기 쪽 +5 µm, z 방출, 1310 nm 기본 Mode의 6성분 E/H. 연속적인 Gaussian 굴절률 증가량과 4/3 µm index radii | 독립 모의 Guide의 Mode 선택성을 기술한다. 32/40 µm 주기 Supercell과 Fourier cutoff는 Solver 정련 조건이다. 굴절률 반경이나 NA 추산치로 hard stop을 정할 근거는 없다. |
| [R6의 고정 Target](../examples/m7r6_smf_glass_1310.json) | World (2,0,2) mm, X=2 mm 평면, 도착 방향 +X, t=−Z, s=+Y. 수용장 변환 E_acc(t,s)=conj(E_emit(−t,s)). Fit MFD 9.25835/8.42460 µm, curvature −1921.10/−2816.82 m⁻¹ | 기준면에서 Phase를 포함하는 Mode 가중치. MFD와 0.09052/0.09970 rad Gaussian divergence로 수광 경계나 Objective NA를 확정할 수 없다. |
| [측정 근거 검토](M7R4_1310_EXTERNAL_FIELD_EVIDENCE.md) | Southampton 55 mW의 폭 자료는 별도 사례. 고정 Guide는 M7R5-SIM-GLASS-001이며 해당 실물과 동일하다는 근거가 없다. | 측정 광학계의 NA나 영상 Crop은 그 장치의 취득 조건이다. 현재 Port에 귀속되는 stop 위치·형상·투과율은 확인되지 않았다. |
| [R10 광기구 계약](M7R10_FINITE_BEAM_SCOPE.md) | M1/M2 clear Aperture, Package Envelope, Backing·Keepout AABB | Reflector와 기구 프록시의 경계. M2 +1 mrad에서 기구 Clearance는 49.289713 µm로 요구보다 0.710287 µm 작다. |

## 저장 복소장 재적분

[R12](M7R12_CURVED_QUADRATURE.md)의 해시를 대조한 두 Target NPZ에서 셀 중심의 복소장과 고정 수용 Gaussian을 같은 정사각형에서 적분했다. 일정한 셀 면적은 정규화 비에서 소거된다. Port와 처방에 새 가정값을 추가하지 않았다.

| Half-window [µm] | Pitch [µm] | η_W | 수용 Gaussian 제곱노름의 Window 밖 분율 상한 (log₁₀) |
|---:|---:|---:|---:|
| 48 | 0.5 | 0.989810941839 | −94.80 |
| 192 | 2 | 0.989810812816 | −1496.22 |

마지막 열은 두 축에 대해 erfc(√2 L/w)를 합한 union bound다. L은 half-window, w는 각 축의 MFD/2이다. 이 상한은 **Target Gaussian**에만 적용된다. R12 도착장에는 별도의 꼬리 성분이 있다. 두 표 행은 pitch와 window가 함께 달라진다. 독립적인 pitch/window 정련은 R12 보고서의 동일 조건 비교를 사용한다.

## R10 전체면 정규화 조건

R10의 η는 같은 전체면에서 0보다 크고 유한한 L² norm을 갖는 도착장 E와 수용장 g의 정규화 제곱 내적이다. g는 Gaussian이므로 이 조건을 만족한다. R11–R12의 도착장은 유한 M2 patch의 Helmholtz single layer다. 매끄럽고 적분 가능한 유한 지지 density의 원거리장에서 E는 exp(−ikr)F(r̂)/r + O(r⁻²)이다. Target 평면을 따라 멀어지면 r̂는 그 평면에 평행한 방향에 접근한다. [Single-layer far-field 식 (4)](https://stsynkov.math.ncsu.edu/publications/Waves_2007_proceedings.pdf)

- Grazing 방향의 한 점에서라도 연속인 F가 0이 아니면 근방 각도 구간에서도 성분이 남고 ∫|E|²dA에 ∫dr/r 꼬리가 생긴다. 이때 전체면 L² 정규화는 정의되지 않는다.
- 모든 grazing 방위에서 F가 0이고 각도 도함수와 원거리 전개의 나머지가 균일하게 제한되면, 평면에서 E=O(r⁻²)가 되어 외부 제곱노름은 유한하다. **정량적인 U**를 산출하려면 계수 상한과 적용 시작 반경, 내부 적분 오차까지 필요하다.
- R12의 +Z grazing 계수 크기는 Gauss와 midpoint에서 약 1.71e−4 및 1.62e−3이었다. 두 방위의 점 표본과 수치 차이만으로 연속 density의 비영 하한 또는 전체 방위의 소거를 입증할 수 없다. Normal flux 잔차로 비가중 |E|² norm의 꼬리를 한정할 수도 없다.

조건부로 전체면 norm이 유한하다고 놓으면, α를 g의 Window **밖** norm² 분율, β를 E의 대응 분율로 두고 Cauchy–Schwarz를 적용할 수 있다.

    √η ≤ √[(1−α)(1−β)η_W] + √(αβ)
    η ≤ (1−α)η_W + α

두 번째 식은 첫 식의 우변을 모든 β에서 최대화한 결과다. 따라서 정확한 η_W와 작은 α는 전체면 η의 **단측 상한**에 도움이 된다. β의 상한과 유한면 적분의 검증된 오차 없이는 전체면 η의 두 방향 오차 U ≤ 5e−6을 입증할 수 없다. 위 진단값에는 기존 목표의 통과·미달 판정을 적용하지 않는다.

## 최소 재개 입력과 판정

| 설계 질문 | 필요한 최소 근거와 처리 |
|---|---|
| 실제 공간 수광면이 있는가? | 동일 Case의 stop/Facet 도면 또는 교정된 측정으로 기준면, 중심, 축, 단위, 형상, edge와 amplitude/phase transmission 및 공차를 제공한다. 다른 평면이면 해당 면까지의 전파가 필요하다. |
| 수집 NA가 광로를 제한하는가? | 매질 n, 광축, Pupil 위치, 각도 전달함수와 편광 의존성 또는 검증된 hard-cutoff 근사, 그 불확도를 확보한다. 단일 NA 숫자에는 Pupil apodization 정보가 없다. |
| 원하는 값이 특정 guided mode로의 전달 Power인가? | R5 모드의 E/H·방향·상호성 규약 및 mode power 정규화와 입사 E/H·launch power가 같은 기준에서 일관돼야 한다. R12의 scalar E와 ∂xE에서 누락된 벡터 성분을 복원할 근거가 필요하다. |
| R10 전체면 η 자체가 필요한가? | 위 존재 조건과 외부장 norm 또는 이에 상당하는 양측 오차 상한, R10의 grid/window/surface/reference별 예산을 검증한다. |

별도 수광 경계가 확인되면 물리적으로 Pupil을 거친 도착장과 고정 수용 모드의 기준면을 먼저 정한다. Pupil 전달 power, 수광 영역 내부의 조건부 Overlap, launch 대비 투영 power는 분모가 다르므로 각각 정의한다. 측정 불확도와 수치 적분 예산, 합격 기준은 그 metric의 최초 계산 전에 기록한다. 이번에는 실제 경계를 갖는 별도 metric을 평가할 입력이 없다.

## 재현

```bash
python -m scripts.m7r13_target_acceptance
PYTHONPATH=src python scripts/validate.py
```
