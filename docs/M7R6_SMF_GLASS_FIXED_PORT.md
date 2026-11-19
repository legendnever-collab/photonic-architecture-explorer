# M7-R6 — 1310 nm SMF–Glass Fixed-Port 평가

**동결한 Nominal 배치에서 Exact-q 후보는 0개였고, Guarded Near-Match에서 G036-NM을 선택했다.** 기존 scalar Gaussian 모델의 정규화된 Overlap은 0.99908895, Mode Mismatch는 0.00396 dB다. 광경로는 20.84 mm이며 두 번째 반사면의 (3w_{projected}|\kappa|)는 0.149999928로 0.15 한계에 거의 닿는다. 실제 광결합 효율, Package 및 제조·조립 적합성은 Uncomputed다.

## SMF 외부 Field와 사전 Fit 예산

`M7R6-SIM-SMF-001`은 1310 nm 원형 Step-index SMF의 독립 Nominal Simulation이다. 공개 Core Diameter 8.2 µm를 적용했다. Cladding n=1.44680432는 Malitson의 Fused Silica 분산식에서 계산했고 Δn=0.0045는 명시적 모델 가정이다. 이 두 index로 계산한 V는 2.2457이다. Corning의 1310 nm MFD 9.2 ± 0.4 µm는 공개 스케일 확인에 사용했다. FMMAX에는 이 MFD를 입력하거나 이에 맞춰 굴절률을 재조정하지 않았다. 실제 Fiber의 굴절률 분포, Facet 가공 편차 및 공차는 미제공이다.

[Corning PI1450 Core Geometry](https://www.corning.com/media/worldwide/coc/documents/Fiber/PI1450_3-2015.pdf) · [Corning PI1424 MFD](https://www.corning.com/media/worldwide/coc/documents/Fiber/product-information-sheets/PI-1424-AEN.pdf) · [Malitson 분산식](https://doi.org/10.1364/JOSA.55.001205) · [FMMAX](https://github.com/facebookresearch/fmmax)

무코팅 평면 Facet의 중심이 로컬 원점이고 방출 방향은 +Z다. 공기 n=1의 Facet 바깥 5 µm에서 로컬 t=+X, s=+Y로 E/H의 6개 복소 성분을 기록했다. FMMAX가 푼 두 편광 Eigenmode의 n_eff 차이가 1e−8 이내일 때 중심 Ey가 0인 선형 t 편광 조합을 입사시켰다. 최종 n_eff는 1.44900353이다. 외부 입사장은 0이며 `exp(+iωt)`, 전진 Carrier `exp(−ikz)` 기준으로 복소장을 저장했다. 중심 Ex=1로 정규화했고 E/H는 Solver 상대 단위다.

SMF Fit은 계산 전에 Port당 손실 ≤0.10 dB와 Phase RMS ≤0.10 rad로 고정했다. 0.10 dB는 수치 여유 0.01 dB를 포함하는 이 개념 모델의 배정값이다. Ex Intensity가 Peak의 1% 이상인 영역에서 Phase RMS를 계산한다. η는 전체 Window에서 Ex와 Ey를 포함한 Transverse Norm을 사용한다. Ez 비율은 전체 E 제곱노름의 0.202%였다.

| 계산 조건 | Window / Samples per axis / Fourier terms | 최종 Fit 지표 |
|---|---|---:|
| 최종 Window | 40 µm / 320 / 497 | η 0.995322714 |
| 독립 Fourier Quadrature | 같은 Field와 Fit | η 0.995322714 |
| Gaussian Fit 손실 / 여유 포함 | s/t 구분 없는 총 Fit 지표 | 0.02036 / 0.03036 dB |
| Phase Residual RMS | Ex Intensity 가중 | 0.02152 rad |
| 수치 수렴 최대 변화 | Grid·Basis·Window | 손실 0.000498 dB, Phase 0.00201 rad, Vector E 상대 L² 0.00680 |
| MFD / Curvature, t / s | Air +5 µm 기준면 | 9.4368 / 9.4169 µm, +1777.23 / +1792.44 m⁻¹ |
| 단일 Port Divergence, t / s | Guard 0.1 rad | 0.08877 / 0.08896 rad |

수렴 비교는 32 µm / 128 / 193에서 Grid만 256으로 높이고, Basis를 317로 높인 다음 40 µm / 320 / 497로 Window를 확장했다. 마지막 비교에서 샘플 간격 0.125 µm와 물리적 Fourier Cutoff를 거의 유지했다. 세 비교의 한계는 각각 0.01 dB, 0.01 rad, 0.02다. 독립 적분은 저장된 Fourier 계수에 Gauss–Legendre 적분을 적용한다. 근사 범위는 이상적 원형 계단 분포와 평면 Facet, 유한 주기 Supercell 및 표의 수치 수렴까지다. 실제 Fiber 측정과 교차 검증은 Uncomputed다.

[사전 입력·예산](../references/m7r6/case.json) · [6성분 최종 Field](../references/m7r6/window.npz) · [4개 Run의 Fit·수렴·해시](../references/m7r6/fit.json)

## Fixed-Port 변환과 배치

M7-A의 기존 비기밀 배치를 사용했다. 아래 좌표는 Facet 중심에서 5 µm 떨어진 각 공기 쪽 Reference Plane의 중심이다. 두 Port의 위치·방향·Mode는 탐색 중 고정됐다.

| Port | World Position (mm) | 전파 d | Transverse (t, s) | Mode |
|---|---|---|---|---|
| SMF Source | (0, 0, 0) | +X | (−Z, +Y) | 위 FMMAX 방출장 Fit |
| Glass Target | (2, 0, 2) | +X 입사 | (−Z, +Y) | M7-R5의 방출장에 대한 Reciprocal 수용장 |

Glass의 로컬 방출 방향을 World −X로 회전한 뒤 수용장으로 변환했다. 동일 평면에서 `E_acc(t,s) = conj(E_out(-t,s))`를 적용한다. 중심이 고정된 Separable Gaussian의 MFD는 그대로이며 Curvature 부호가 뒤집힌다. 계약의 ordinary q로는 `q_acc = -conj(q_out)`이다. M7-R5의 Field 해시와 Fit을 고정했고 Target의 s축 Divergence는 0.09970 rad다. Mirror의 Jones transport와 편광별 위상은 scalar 설계 범위 밖이다.

[동결한 배치](../references/m7r6/layout.json) · [External Adapter 입력](../examples/m7r6_smf_glass_1310.json) · [M7-R5 Glass Field](M7R5_SINGLE_PORT_FIELD.md)

## 설계 후보와 실제 적용 한계

Exact-q 탐색은 36개 Geometry의 처방 144개를 검사했다. 141개는 (3w_{projected}|\kappa| > 0.15), 3개는 Divergence >0.1 rad에서 먼저 탈락했다. Near-Match는 같은 36개 Geometry에 대해 127,968회 Adapter 평가를 수행했고 33개 Geometry에서 유효한 처방을 찾았다. 주요 탈락은 Divergence 25,829회와 의도하지 않은 Reflector Interception 2,757회다.

| 비교 지표 | G036-NM · 기존 Ranking 추천 | G029-NM · 두 번째 Overlap 관측값 |
|---|---:|---:|
| 정규화된 Gaussian Overlap | 0.99908895 | 0.99806030 |
| Gaussian Mode Mismatch | 0.00396 dB | 0.00843 dB |
| 광경로 길이 | 20.840 mm | 9.825 mm |
| 최대 (3w_{projected}|\kappa|) | 0.149999928 | 0.149999982 |

추천 후보 G036-NM은 5.657 / 9.526 / 5.657 mm 세 구간으로 진행하며 두 Mirror Vertex의 World x좌표가 +5.657 mm, −3.657 mm다. 장치의 x 방향 기준면 간격 2 mm보다 넓은 공간을 쓴다. 입사각은 양쪽 모두 약 6.06°이며 가장 큰 full clear aperture는 약 4.33 mm다. G029-NM은 더 짧은 경로에서 비슷한 Nominal η를 보이지만 이 곡률 Guard에도 여유가 거의 없다. 둘 다 실제 Package AABB/백킹/Keepout 자료가 없다. 이 배치에서 광학적 Guard를 통과한 처방은 확인했으며, 실제 조립을 위한 여유와 경로 Clearance는 Uncomputed다.

기존 Adapter로 추천 처방의 Fixed-Port Geometry·Model Domain을 통과시켰고 NumPy ABCD와 복소 적분으로 q와 η를 독립 검산했다. 개별 Port Fit 손실과 Gaussian 설계 Overlap은 각기 특정 투영을 평가한다. 실제 E/H의 두 반사면 통과, 개구 회절, 코팅과 계면 손실 및 조립 수율에 대한 결합 결과는 Uncomputed다.

[추천·비교 처방과 Guard 증거](../references/m7r6/design_summary.json)

## 재현과 회귀

```bash
python -m pip install -e '.[test]'
python -m scripts.m7r6_fixed_port --output-dir results/runtime-m7r6
python -m unittest discover -s tests -q
python scripts/validate_m7c.py --output-dir results/runtime-m7c-r6-review
```

`results/runtime-m7r6`에 Fit, 고정 Input, 전체 Workflow Ledger, Summary, 기존 Design Report HTML을 생성한다. 저장된 Fit을 기준으로 두 Port를 구성해 플랫폼별 Fit 반올림이 설계 입력을 바꾸지 않게 한다. 1550 nm Proxy 회귀에서 G036-NM η=0.9999366495865395를 재현했다. Southampton 55 mW 사례는 `ambient_index`부터 미공급 상태이며 실물 적용성은 Uncomputed다.

SMF Field 취득을 처음부터 재실행할 때 별도 Python 3.12 CPU 환경에서 아래 명령을 사용한다.

```bash
python -m pip install -e . fmmax==1.7.1 jax==0.12.1 jaxlib==0.12.1
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 JAX_PLATFORMS=cpu python scripts/m7r5_capture.py /tmp/m7r6-capture --case references/m7r6/case.json
python -m scripts.m7r6_fixed_port --capture-dir /tmp/m7r6-capture --output-dir /tmp/m7r6-review
```
