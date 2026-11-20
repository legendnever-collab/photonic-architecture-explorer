# M7-R11 — 1310 nm 확장 처방의 명목 복소장

**독립 scalar Physical Optics 계산은 고정 Target 면까지 도달했다. η ≥ 0.99 판정은 보류한다.** 324×324 midpoint에서 η 진단값은 0.9898105563이다. 두 반사면의 면적 적분과 Window 수렴에서 M7-R10의 절대 오차 예산을 입증하지 못했다. M2 ±1 mrad 광학 계산은 명목 Gate에서 중단했다.

## 모델과 재현 조건

[사전 계획](../references/m7r11/plan.md)에 따라 NumPy와 독립 C++ 직접 적분으로 5.023725 mm 확장안만 계산했다. R6 Source/Target의 Gaussian Fit, World 좌표·방향, R8의 두 Quadratic patch와 유한 직사각 Aperture를 읽는다. 설계 및 Guard 변경은 없다. 입력 SHA-256은 [결과 JSON](../references/m7r11/summary.json)에 있다.

시간 규약 exp(+iωt)에서 G=exp(−ikr)/(4πr)이다. Launch 면에서는 Rayleigh–Sommerfeld 적분과 수신면 법선 방향 미분을 계산한다. 반사면에서는 illuminated normal n에 대해 국소 Dirichlet 반사의 single-layer density −2∂nE_inc를 clear patch에 적분한다. 각 점에 실제 sag, 법선, dS를 적용한다. 이 이상화는 단일 진행 경로와 국소 접평면 반사를 가정한다. 모서리 유도 전류, 상호 다중 산란, Backing 및 Keepout의 광학 차폐에는 추가 근거가 필요하다. [평면 전파식](https://qiweb.tudelft.nl/aoi/scalardiffractiontheory/scalardiffractiontheory/) · [Colton & Kress, 식 2.20–2.22](https://num.math.uni-goettingen.de/bibi/preprintserie/preprints/kress/colton-kress-2009.pdf)

| 명목 계산 전 대조 | 오차 | 사전 한계 |
|---|---:|---:|
| 저 NA Gaussian 복소장 / paraxial 해, 상대 L² | 2.27e−5 | 1e−3 |
| 평면 반사 / 부호가 뒤집힌 unfolded Gaussian, 상대 L² | 4.48e−5 | 1e−3 |
| 단일 원형 Aperture 축상 복소장 / 정확한 RS 축상 적분, 절대 | 5.95e−13 | 1e−4 |

## 명목 곡면 정련과 Power Balance

Target은 X=2 mm에서 고정된 t=−Z, s=+Y이다. 아래 η는 같은 Target mode와 도착장 사이의 정규화 제곱 Overlap이다. 기준 표에는 Target pitch 0.5 µm, half-window 48 µm를 사용했다. M1과 M2는 각 clear patch에서 안쪽 방향 scalar current를 적분했다. M1은 launch의 forward angular-spectrum flux로 정규화했고 M2/M1은 이상 반사를 가정한 두 intercepted flux의 비다. Target flux는 같은 launch로 정규화했다.

| Mirror nodes/axis · 적분 | M1/launch | M2/M1 | Target/launch | η 진단값 |
|---|---:|---:|---:|---:|
| 96 midpoint | 0.999999224 | 13.163623011 | 12.952825648 | 0.2301580110 |
| 144 midpoint | 0.999999219 | 6.037816461 | 5.752868462 | 0.1725345515 |
| 216 midpoint | 0.999999217 | 1.257147332 | 1.234904618 | 0.7852633260 |
| 216 gauss2 | 0.999999215 | 1.371365531 | 1.103713124 | 0.8180528416 |
| 324 midpoint | 0.999999216 | 1.000005523 | 1.000003655 | 0.9898105563 |
| 216 midpoint · edge ×2 | 0.999999217 | 1.257231678 | 1.212275883 | 0.8003775223 |
| 216 midpoint · edge ×4 | 0.999999218 | 1.257232462 | 1.212268609 | 0.8003815017 |
| 324 midpoint · edge ×4 | 0.999999216 | 1.000005246 | 1.000002490 | 0.9898111760 |

216→324 midpoint에서 η 변화는 약 0.205다. 324 midpoint에서 Target pitch 1→0.5 µm의 변화는 약 6e−10이지만 half-window 24→48 µm의 변화는 1.47e−6으로 Window 예산 1e−6을 초과한다. 같은 216 격자에서 가장자리 두 셀만 이등분·사등분한 두 결과 사이에도 약 3.98e−6의 차이가 있다. Interior와 경계를 함께 바꾼 composite Gauss 대조도 결과 JSON에 보존했다.

324 midpoint에서 (M2 intercepted flux − Target window flux)/launch는 1.08e−6이고 M2/M1은 약 1.00000552다. Raw ledger의 Power 초과와 유한 Window 밖 에너지는 물리적 손실값으로 쓸 수 없다. 곡면의 빠른 위상 변화를 직접 적분하는 데 필요한 sampling이 주된 수치 문제로 보인다. M7-R10 목표는 U ≤ 5e−6 및 η_est − U ≥ 0.99이다. 이번 U는 미확정이며 Gaussian 예측 0.990010973과 이번 진단값의 차이로 목표 통과나 미달을 확정할 수 없다.

[저장 복소장](../references/m7r11/nominal-target.npz)은 324 midpoint 명목 진단의 complex128 E와 dE/dx, m 단위 공통 축 ts_m이다. 배열 순서는 [t,s]이며 192×192 cell center를 사용했다. 기준 결과에서는 수렴한 Aperture Throughput, 검증된 Finite-beam η, Perturbed Mode Overlap, 실물 Total Coupling을 Uncomputed로 기록한다. [M7-R10](M7R10_FINITE_BEAM_SCOPE.md)의 M2 +1 mrad 기구 프록시는 49.289713 µm로, 50 µm 기준에 0.710287 µm 부족하다.

## 재현

Linux, Python 3.12, NumPy 2.3.5, g++ 14.2 및 OpenMP. 빈 출력 경로를 지정한다. 아래 명령은 각 곡면 정련의 raw complex field와 JSON을 생성한다. 기준 회귀는 134 tests, M1 Benchmark, M3-A Adapter를 통과했다.

```bash
OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 python -m scripts.m7r11_wave /tmp/pae-r11-replay
PYTHONPATH=src python scripts/validate.py
```
