# M7-R12 — 1310 nm M1→M2 곡면 적분

**명목 R11 Power 초과는 M1 면적 적분을 정련하면 사라진다.** 48개 panel에 축별 14점 Gauss–Legendre를 적용한 M2/M1은 0.9999994722다. 고정 Target에서 half-window 192 µm의 정규화된 제곱 Overlap은 0.9898108128이다. 전체 Target 면 η의 수치 불확도 상한은 미확정이다. 0.99 판정과 양방향 회전 광학 성능은 **Uncomputed**다.

## 기준과 재현

[사전 계산 계획](../references/m7r12/plan.md)과 [R10 정의](M7R10_FINITE_BEAM_SCOPE.md)를 사용했다. Main `7e523aca`의 [Physics CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44706481909), 열린 Draft #41 `7222853b`의 [Physics](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44712436098)·[Windows](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44712436028), 열린 Draft #42 `e21c165d`의 [Physics](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44717579561)·[Windows](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44717579424)를 확인했다.

#42에서 [R11](M7R11_CURVED_FIELD_REFERENCE.md)의 세 Control과 324 midpoint 명목 1건을 원래 kernel로 재실행했다. 원본과 재계산의 Target 좌표, E, ∂xE 및 Power Ledger 차이는 모두 0이었다. 두 Gaussian Port와 기준면, 1310 nm, 두 개의 유한 quadratic patch, 5.023725 mm Envelope와 Guard를 고정했다. R6/R7/R8 입력 SHA는 실행 시 확인한다. 모델은 R11과 같은 단일 진행 경로의 scalar Dirichlet Physical Optics다.

## M1 면에서 사라지지 않는 위상

Source 중심 S, M1 적분점 P, M2 관측점 D에 대해 빠른 위상의 기준 광로를 L=|P−S|+|D−P|로 잡았다. Chief 경로의 중심에서 두 항의 접선 기울기가 상쇄된다. Aperture 주변에서 다른 M2 점으로 가는 성분에는 큰 기울기가 남는다. M1을 48×48 panel로 나누고 M2의 9×9 고정 관측점으로 향하는 경로의 기울기를 계산했다. R11의 324 midpoint 셀 폭으로 환산한 최대 국소 위상 변화는 u, v에서 각각 6.42, 6.33 rad다. 이는 연속한 복소장 표본을 unwrap한 값이 아니라 합성 광로의 미분값으로 계산한 진단이다.

**Filon 대조.** 각 panel 중심에서 L의 선형 위상을 분리하고 잔여 integrand를 Legendre 다항식으로 보간했다. 선형 위상에 대해서는 Fourier moment를 해석적으로 반영했다. 관측점마다 실제 sag, 거리, ∂nG, 면적 Jacobian을 사용했다. 사전 계산한 M1 입사장은 원래 RS launch kernel을 공유한다. 따라서 이 대조는 M1→M2 적분을 검사한다. 절대 piston을 조정하지 않았다. Fourier moment 대조의 최대 오차는 4.77e−15 미만이다. [NIST DLMF 10.54.2](https://dlmf.nist.gov/10.54.E2)

| M1 적분 | Filon 12 대비 M2 E 상대 ℓ² | ∂nE 상대 ℓ² |
|---|---:|---:|
| R11 324 midpoint | 2.68e−3 | 2.74e−3 |
| Gauss 6 | 6.15e−1 | 6.17e−1 |
| Gauss 8 | 7.94e−2 | 7.96e−2 |
| Gauss 10 | 4.07e−3 | 4.02e−3 |
| Gauss 14 | 8.45e−6 | 8.49e−6 |
| Filon 8 | 3.14e−8 | 3.14e−8 |
| Filon 10 | 1.36e−10 | 1.36e−10 |

81개 점에서의 상대 ℓ²는 무가중 복소장 진단이다. 면 전체의 Flux는 별도로 적분했다. 입사 Current는 illuminated normal 방향의 부호를 뒤집은 Im(E*∂nE)/k이다. 여기서 E*는 복소켤레다. Gauss 14와 Filon 12의 공통점 Current 상대 차이는 5.71e−8이다. M2의 672×672 수신점과 면적 가중치를 고정하고 M1만 512 midpoint로 바꾸면 E의 면적 가중 상대 L² 차이는 3.62e−5, M2/M1 변화는 6.40e−9다. 두 방법이 동일한 scalar boundary와 launch를 공유한다는 점은 이 비교의 한계다.

M2 수신점 적분 자체의 영향을 분리하기 위해, 640 midpoint로 얻은 면 법선 Current를 원래 R11의 324×324 수신점에 cubic 및 quintic spline으로 다시 표본화했다. 원래 면적 가중치에서 얻은 M2/M1은 각각 0.9999994150과 0.9999994103이다. Gauss 14 Current로 같은 검사를 하면 1.0000002462와 0.9999997024다. 재표본화 오차는 남지만 어떤 조합도 R11의 +5.523 ppm을 재현하지 않는다. 공통 M2 점의 R11 복소장 오차와 함께 보면 M1의 진동 적분 undersampling이 초과의 주원인이다.

## 정련과 Power Ledger

Gauss 표기의 숫자는 축별 48개 panel 각각의 적분 차수다. Edge ×2, ×4는 가장 바깥쪽 panel만 나눈다. 원래 Aperture 가장자리와 내부 panel은 유지한다. R11을 제외한 각 계산은 8개 명목 relay 예산 안에 포함했다. 표의 Target pitch는 1 µm, half-window는 48 µm다.

| M1 / M2 적분 | M1/launch | M2/M1 | Target/launch | η |
|---|---:|---:|---:|---:|
| R11 midpoint 324 / 324 | 0.9999992162 | 1.0000055229 | 1.0000036547 | 0.9898105569 |
| Gauss 6 / 6 | 0.9999992154 | 1.2645102090 | 1.0539220416 | 0.9313948916 |
| Gauss 8 / 8 | 0.9999992154 | 1.0070561728 | 1.0006382211 | 0.9895927471 |
| Gauss 10 / 10 | 0.9999992154 | 1.0000541969 | 1.0000001853 | 0.9898102077 |
| Gauss 14 / 14 | 0.9999992154 | 0.9999994722 | 0.9999985231 | 0.9898109419 |
| Midpoint 512 / Gauss 14 | 0.9999992157 | 0.9999994786 | 0.9999985237 | 0.9898109435 |
| Gauss 14 / 14, edge ×2 | 0.9999992154 | 0.9999994725 | 0.9999985233 | 0.9898109421 |
| Gauss 14 / 14, edge ×4 | 0.9999992154 | 0.9999994725 | 0.9999985233 | 0.9898109421 |
| Midpoint 640 / 640 | 0.9999992156 | 0.9999994765 | 0.9999985244 | 0.9898109441 |

**Target 적분.** Gauss 14에서 48 µm half-window를 고정한 pitch 2→1→0.5 µm의 마지막 η 변화는 1.66e−11이다. 2 µm pitch를 고정한 half-window 24, 48, 96, 192 µm의 η는 각각 0.9898110919, 0.9898109426, 0.9898108542, 0.9898108128이다. 96→192 µm의 η 변화는 4.14e−8이다. 마지막 Window에서 Target/launch는 0.9999986511, (M2−Target)/launch는 +3.65e−8이다. 같은 Window에서 2 µm pitch를 사용한 값에 대해 48 및 96 µm에서 더 작은 pitch와 교차 대조했다. [전체 수치·입력/복소장 해시](../references/m7r12/summary.json)

Gauss 10→14의 48 µm η 변화는 7.34e−7이다. 같은 Gauss 14에서 edge ×1→×2는 2.53e−10, ×2→×4는 3.33e−16이다. 전혀 다른 640 midpoint 양면 격자에서 192 µm η는 0.9898108141이다. Gauss 14와 η 차이는 1.26e−9, 같은 좌표의 E 상대 L² 차이는 2.20e−6이다. 양면을 함께 정련한 결과와 같은 M2 격자에서 M1 적분법만 바꾼 결과가 모두 1 미만이다.

## U와 설계 판정

R10은 Δgrid, Δwindow, Δsurface+edge에 각각 1e−6, 독립 대조와 잔여 오차에 2e−6을 배정했다. 유한 Window 간 변화량은 작지만 밖에 남은 제곱장 norm에 대한 상한은 따르지 않는다. Normal flux에는 전파각에 따른 projection이 포함되고, η의 분모는 |E|²의 면적 적분이기 때문이다. 작은 Power Ledger 잔차를 η의 절대 오차로 대입할 수 없다.

이를 확인하기 위해 추가 relay 없이 M2의 저장된 density에서 Target 평면과 **평행한** ±Z 방향의 원거리 계수를 계산했다. 단일층에서는 F(g)=∫ρ(p) exp(+ik g·p)dS/(4π)이고 원거리 E의 선두항은 exp(−ikr)F(g)/r이다. 축 방향의 빠른 위상은 Filon moment로 처리했다. [단일층 원거리 표현](https://stsynkov.math.ncsu.edu/publications/Waves_2007_proceedings.pdf)

Gauss 14 기본·교차·edge 정련에서 |F(+Z)|는 1.71e−4 전후였고 640 midpoint 노드에서 별도로 보간하면 1.62e−3이었다. 따라서 넓은 Window의 η가 비슷한 두 규칙조차 grazing 성분의 크기에는 합의하지 않는다. 이 값은 원래 launch field 정규화에서 계산한 진폭 계수다.

연속적인 F가 grazing 방향의 어느 구간에서라도 0이 아니면, 무한 Target 평면에서 그 구간의 제곱장 norm 꼬리는 ∫dr/r에 비례한다. 이것은 이상화한 scalar single layer에서 생기는 수학적 조건이다. 유한 수광면의 실제 발산이나 제품 손실을 뜻하지 않는다. 관측값만으로 F의 엄밀한 하한이나 모든 각도의 tail 상한을 증명하지 않았다. 따라서 192 µm 값을 무한면 η로 인증할 근거가 없고, 각 적분의 successive difference만으로 유한면 전체 오차도 보증할 수 없다.

**판정.** 명목 수치는 0.99를 약 1.89e−4 밑돈다. R10의 U ≤ 5e−6을 입증하지 못해 명목 목표의 공식 통과·미달은 보류했다. 검증된 Aperture Throughput, Finite-beam Clearance, M2 ±1 mrad Mode Overlap 및 실물 Total Coupling은 Uncomputed다. R10 기구 계산을 다시 실행한 세 gap은 명목 50.000001 µm, −1 mrad 50.000001 µm, +1 mrad 49.289713 µm다. +1 mrad에서 M2 X−가 50 µm 요구치에 0.710287 µm 부족하다.

다음 판단은 Target의 실제 유효 수광면 또는 수집 NA를 근거와 함께 정의할 수 있는지다. 유한 수광면을 적용하면 그 경계에 대한 지표를 별도 이름으로 명시하고 유한 영역 적분의 잔여 오차를 검증한다. 수광 경계 미제공 시에는 현 설계의 Window 진단값을 유지한다.

## 복소장과 재현

- [M2 원시 복소장](../references/m7r12/M2-q14-14-edge1.npz)에는 Gauss 14의 u, 양의 v, m² 단위 면적 가중치, complex128 E와 illuminated-normal ∂nE가 있다. World Y 대칭에 따라 음의 v를 반사 복원한다. 전체 입사 Flux는 양의 v 쪽의 가중합을 두 배한다.
- [공통 M2 관측점](../references/m7r12/common-M2-probes.npz)에는 World 좌표·법선과 Filon, Gauss, midpoint의 E·∂nE가 있다.
- Target은 X=2 mm, t=−Z, s=+Y에 고정했다. [half-window 48 µm, pitch 0.5 µm](../references/m7r12/target-q14-14-edge1-0.5um.npz)와 [half-window 192 µm, pitch 2 µm](../references/m7r12/target-q14-14-edge1-2um.npz)에 같은 기준면의 ts_m, complex128 E[t,s], ∂xE[t,s]가 있다. 모든 field에서 원래 위상과 진폭을 보존했다.

로컬 회귀 136개, M1 Benchmark 및 M3-A Adapter Gate가 통과했다. 기존 회귀 134개에 양·음 주파수에서 Filon cardinal의 다항식 적분과 edge 분할의 면적·내부 노드 보존 검사를 추가했다.

Linux·Python 3.12.14·g++ 14.2·OpenMP, NumPy 2.3.5, SciPy 1.17.0. 다음 명령은 빈 작업 디렉터리에 모든 정련의 원시장을 생성한다. 음수 order는 해당 개수의 uniform midpoint를 나타낸다.

```bash
set -e
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1
out=$(mktemp -d)
python -m scripts.m7r12_quadrature "$out" --replay
for q in 6 8 10; do
  python -m scripts.m7r12_quadrature "$out" --orders "$q" "$q"
done
python -m scripts.m7r12_quadrature "$out" --orders 14 14 --wide
python -m scripts.m7r12_quadrature "$out" --orders -512 14
for edge in 2 4; do
  python -m scripts.m7r12_quadrature "$out" --orders 14 14 --edge "$edge"
done
python -m scripts.m7r12_quadrature "$out" --orders -640 -640 --wide
python -m scripts.m7r12_filon "$out"
python -m scripts.m7r12_summary "$out"
PYTHONPATH=src python scripts/validate.py
```
