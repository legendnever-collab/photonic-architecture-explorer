# M7-R20 — Yee 격자의 H 추출과 Flux 정규화

**고정 Facet의 재계산을 보류했다.** 독립 Meep 직선 SMF에서 R19의 H 오차 4.468% 대부분을 같은 계산의 공간 샘플 위치로 설명할 수 있었다. 각 성분의 원래 Yee 위치에서 재구성한 뒤에도 24 pixels/µm의 HE11 접선 E/H 오차는 각각 2.266e−4, 1.123e−4였다. 두 값 모두 5e−5 예산을 초과한다. 명목 Guided Power 비율·U·M2 회전 응답은 Uncomputed다.

## 사전 조건과 대조

기준은 열린 #50의 검증 HEAD 9a81ebf503ce12746e963e46b1b4c97c36329c30이다. R19의 12 px/µm 저장장으로 직선 SMF H 상대차 0.0446805681과 공기면 재구성 Power/native monitor 상대차 0.0479086807을 재현했다. 같은 1310 nm, Meep 1.35.1, 무손실 모의 SMF와 R19의 기준면을 사용했다. 1D 균일 공기 및 cladding에서 8/12/24 px/µm, 원통 좌표의 직선 SMF에서 12/24 px/µm와 12 px/µm 여기 변경을 수행했다. [계산 전 예산](../../references/m7r20/plan.md) · [R19](M7R19_OPEN_FACET_REFERENCE.md)

각 실행에서 centered point DFT와 성분별 native Yee DFT를 동시에 수집했다. native array와 Solver가 반환한 좌표 범위·spacing을 확인하고 원통 배열을 (r,z) 순서로 보관했다. 축 방향에서는 가까운 8개 위치의 다항 보간을 6점 결과와 대조하고, radial profile은 동일한 172개 반경에서 평가했다. Meep DFT는 E에 t, H에 t−Δt/2를 각각 적용해 Fourier 변환한다. 저장된 H에는 추가 시간 위상 회전을 가하지 않았다. 12 px/µm에서 중복 반 스텝 회전은 0.09992 rad이다. [Meep DFT 구현](https://github.com/NanoComp/meep/blob/v1.35.1/src/dft.cpp) · [격자 위치 정의](https://github.com/NanoComp/meep/blob/v1.35.1/src/meep/vec.hpp)

| 성분 | Er | Eφ | Ez | Hr | Hφ | Hz |
|---|---:|---:|---:|---:|---:|---:|
| r 위치, 셀 내 분율 | ½ | 0 | 0 | 0 | ½ | ½ |
| z 위치, 셀 내 분율 | 0 | 0 | ½ | ½ | ½ | 0 |

## 평면파

단위 면적에서 해석 Power는 n∣E∣²/2, 재구성 Power는 Re(EH*)/2로 계산한다(H는 Z₀H 단위). 정수 z 위치에서 centered point의 E는 인접 중심으로의 보간과 관측면으로의 보간을 모두 거치고 H는 한 번 거친다. 단일 전진 차분 평면파에서 그 진폭계수는 각각 C²와 C다. 여기서 C=cos(k_h Δz/2)이고 k_h는 1D Yee 분산식 sin(k_h Δz/2)=n(Δz/Δt)sin(ωΔt/2)에서 구했다(c=1). 단순히 H/E를 취하면 n/C가 된다.

Meep의 native Flux는 각 cell center에서 E×H*를 만든 후 가중 적분한다. peak phasor의 평면파에서는 monitor/2를 물리 Power와 비교하며, 이 값에도 C가 남는다. 순수 평면파에서는 C로 나눌 수 있다. Guide의 angular harmonic을 x 선편광으로 복원할 때에는 시간평균 ½와 방위각 평균 ½를 적용해 monitor/4와 비교한다. Guide에서는 성분마다 실제 이웃값으로 center product 적분을 별도로 재구성했다.

| 24 px/µm 대조 | 공기 | Cladding |
|---|---:|---:|
| ∣E/H∣의 해석 임피던스 대비 상대차 | 4.56e−7 | 1.02e−6 |
| H/(nE)의 위상, rad | −1.44e−6 | −3.04e−6 |
| 재구성 Power vs 해석 Power 상대차 | 4.56e−7 | 1.02e−6 |
| 재구성한 이산 적분 vs native monitor | 2.25e−8 | 7.04e−8 |
| 보정 전 monitor/2 vs 물리 Power 상대차 | 5.00e−3 | 1.05e−2 |
| 단일 평면파 C 보정 후 monitor vs 해석 Power | 4.31e−7 | 8.93e−7 |

두 매질에서 24 px/µm의 국소 임피던스·위상·해석 Power 차이는 5e−5 이내였다. 같은 조건의 cladding에서 측정 k=6.960829 rad/µm, Yee 예측 6.960829, 연속계 6.939343이었다. 국소 대조의 통과만으로 장거리 절대 전파위상의 불확도를 보증할 수 없다. 12 px/µm의 평면파에서 R19의 공기/guide Power 환산 오차를 C_air²/C_clad²−1로 추정하면 **4.7473%**, 실제 R19는 **4.7909%**였다. 0.0435%p의 잔차가 남고 실제 Facet에는 여러 진행각이 있으므로 이 비율을 Facet 보정계수로 쓰지 않았다.

## 직선 HE11과 여기 민감도

기준면 z=−4 µm에서 E에 최소제곱으로 정한 복소 계수 하나를 H에도 적용했다. norm은 접선 두 성분을 반경 r로 가중한 상대 ℓ²다. 각 실행의 +5 µm 면도 직선 SMF 내부 대조다.

| 직선 SMF 입력면 | 12 px/µm | 24 px/µm |
|---|---:|---:|
| centered H 상대차 | 4.4681e−2 | 1.0665e−2 |
| native 위치 재구성 E / H 상대차 | 1.1755e−3 / 1.0014e−3 | 2.2662e−4 / 1.1228e−4 |
| 재구성 H 위상 잔차, rad | +3.35e−5 | −3.23e−6 |
| 재구성 물리 Power vs 같은 E 계수의 HE11 | 5.78e−5 | 1.62e−5 |
| 이산 center product 적분 vs native monitor | 6.47e−5 | 1.61e−5 |

같은 12 px/µm E/H에서 추출 방식만 변경해 H 오차가 약 45배 감소했다. 별도로 같은 mesh에서 전기 sheet에 해석 모드의 상보 자기 sheet를 추가했다. 뒤쪽과 앞쪽 monitor의 Power 비가 0.99992에서 4.75e−4로 감소했다. 전방 profile은 공통 E 계수 정렬 후 E 2.44e−4, H 2.82e−4 변화했다. 이 값은 여기 선택에 대한 민감도이며 비기본 모드의 Power 분율로 해석할 수 없다. 12→24 격자 변화는 같은 입력면에서 E 1.10e−3, H 9.61e−4였다.

해석 HE11을 실제 Yee 위치에 샘플링하고 같은 방식으로 보간하는 대조에서도 24 px/µm의 E/H 변화가 8.69e−5 / 1.20e−5였다. Er가 core 경계에서 불연속이므로 radial 보간은 별도 오차원이다. 해석해도 같은 샘플링을 거쳐 비교하면 E/H 잔차는 2.83e−4 / 1.15e−4로 남는다. 남은 장 차이에는 격자에 표현된 core 경계, 모드 여기와 전파가 함께 작용한다. 단일 원인별 절대 오차를 확정할 자료는 부족하다.

**대체 검증 경로.** 원형 경계에 mesh가 일치하는 단일 주파수 vector FEM eigenmode 해석에서 먼저 HE11을 검증한다. Er는 경계 양측에서 따로 비교하고 E와 H에 동일한 복소 계수를 사용한다. Mode port 여기, 폐곡면 Flux, mesh/order·개방경계 정련을 독립 검증한 경우에만 같은 facet의 +5 µm 장을 비교한다. 이번 결과로 R17 M1이나 Glass 수신측 Edge 투영을 갱신할 근거는 없다.

## 재현

[전체 수치](../../references/m7r20/summary.json) · [직선 SMF의 두 기준면 복소장](../../references/m7r20/profiles.npz). 저장 profile은 Meep의 원래 시간 규약이며 E/H에 임의 재보정을 적용하기 전 값이다. 회귀 149건과 Benchmark·M3-A Adapter 검사가 통과했다.

```bash
python -m pip install -e '.[test]'
PYTHONPATH=src python scripts/validate.py
micromamba create -y -n pae-r20 -c conda-forge 'pymeep=1.35.1=nompi*' scipy
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
for n in 8 12 24; do
  micromamba run -n pae-r20 python -m scripts.m7r20_capture /tmp/r20 --geometry plane --resolution "$n"
  micromamba run -n pae-r20 python -m scripts.m7r20_capture /tmp/r20 --geometry plane --resolution "$n" --cladding
done
for n in 12 24; do
  micromamba run -n pae-r20 python -m scripts.m7r20_capture /tmp/r20 --geometry guide --resolution "$n"
done
micromamba run -n pae-r20 python -m scripts.m7r20_capture /tmp/r20 --geometry guide --resolution 12 --dual
PYTHONPATH=src python -m scripts.m7r20_reference /tmp/r20 --profiles /tmp/r20/profiles.npz
```
