# M7-R18 — Source 셀 변화의 원인과 M1 가장자리 조사량

**곡면 반사 계산은 보류한다.** 1310 nm 모의 SMF에서 공통 영역의 장 변화와 바깥 영역의 복원이 모두 M1 복소장 허용치 5e−5를 넘었다. 실제 처방의 네 가장자리에 입사하는 Flux를 정량화했다. 이 입사량에서 Glass Guided Mode 전달 오차의 상한을 얻으려면 수신측 가중치와 산란장 오차가 더 필요하다.

## 입력과 위상 기준

기준은 #48의 `2e7cd8c0be46ffa5d329116264ce7ed02c46e9ed`이다. 두 Port, 5.023725 mm 확장안, M1의 곡률·Aperture와 R15 공기면 Launch 1.7426507346302212e−11 m²(정규화 단위)를 고정했다. [사전 예산](../../references/m7r18/plan.md) · [R17](M7R17_ISOLATED_SOURCE_EDGE.md) · [R15 정규화](M7R15_PORT_POWER.md)

세 원본 Fourier export의 공통 기준은 공기 중 facet에서 +5 µm 평면, exp(+iωt), 중심 E_t=1이다. 중심 Fourier 합을 다시 계산한 최대 절대 위상은 4.55e−17 rad였다. 32/40/48 µm 전체 셀에 적용한 실수 Launch 진폭 계수는 각각 0.9998588074 / 1.0000000000 / 0.9999405290이다. 이후 절단한 장에는 추가 위상·진폭 보정을 적용하지 않았다. R17의 비주기 Love-current 적분, 0.5 µm Source pitch, 실제 M1의 28×28 Gauss 위치에서 세 저장 복소장을 재현했다.

## 40→48 µm 변화의 분해

A는 원래 40 µm 셀, B는 48 µm 장의 중앙 40 µm, C는 전체 48 µm 장이다. 아래 E/H는 각 Source를 같은 M1으로 전파한 뒤 얻은 복소 차이의 ℓ² norm을 A의 해당 norm으로 나눈 값이다. Flux는 실제 곡면의 입사 방향 면적 벡터로 적분한 시간평균 Poynting power다.

| 변화 | M1 E 상대차 | M1 H 상대차 | ΔFlux/Launch (부호 포함) |
|---|---:|---:|---:|
| B−A · 공통 영역 장 변화 | 6.70744e−4 | 6.70744e−4 | −4.46480e−7 |
| C−B · 바깥 영역 복원 | 8.01060e−4 | 8.01060e−4 | +9.98205e−7 |
| C−A · R17 전체 변화 | 9.51540e−4 | 9.51541e−4 | +5.51724e−7 |

복소 변화는 벡터로 더해진다. E의 정규화 제곱 norm에서 두 변화의 교차항은 −1.862e−7이다. Flux 열은 A→B→C를 따라 전체장 Power 차이를 취했으므로 간섭을 포함한다. 이 열의 값은 각 영역이 독립적으로 운반하는 Power와 구별된다. 공통 Source 평면 자체의 E/H 상대차도 각각 1.65637e−3 / 1.65635e−3이다. 이 변화에는 주기 셀, 채택 Fourier basis, 고유모드·facet 해와 전체 셀 Launch 계수의 변화가 함께 들어 있다. 원인을 고유모드 하나로 국한할 수 없다.

같은 48 µm 장을 32/40/48 µm로 잘랐을 때 M1 Flux/Launch는 0.9995892833 / 0.9996003266 / 0.9996013248이다. 32 µm 공통 영역에서는 B−A와 C−B의 M1 E 상대차가 각각 3.1613e−3과 3.1084e−3이었다. 더 넓은 셀에서 변화가 감소했으나, 마지막 차이로 무한 셀의 오차를 보증할 수 없다. [전체 E/H·Flux와 교차항](../../references/m7r18/summary.json)

## M1 네 가장자리

48 µm 모의 SMF로 M1을 조사했다. u,v는 각각 M1의 tangential/sagittal 국소 Aperture 좌표다. 아래 E와 Z₀H는 Source의 E_ref 단위로 표시한 65점 중 최대 벡터 크기다. 각 Strip의 폭은 M1 접평면 좌표에서 안쪽으로 잰 거리다. signed Flux는 곡면에서 적분하며 두 u 쪽 Strip에 네 모서리를 배정했다.

| 가장자리 | 최대 ∥E∥ | 최대 ∥Z₀H∥ | 1λ Flux (ppm Launch) | 4λ | 16λ |
|---|---:|---:|---:|---:|---:|
| u− | 1.29185e−4 | 1.29186e−4 | 0.58952 | 2.33840 | 9.00569 |
| u+ | 1.15881e−4 | 1.15881e−4 | 0.35071 | 1.39031 | 5.41950 |
| v− | 1.27318e−4 | 1.27318e−4 | 0.48028 | 1.89220 | 7.09649 |
| v+ | 1.27318e−4 | 1.27318e−4 | 0.48028 | 1.89220 | 7.09649 |
| 합집합 | | | **1.90078** | **7.51311** | **28.61819** |

λ=1.310 µm. 가장자리 길이·폭 Gauss 정련 16×2→24×4에서 한 가장자리에서 관측한 최대 Flux 변화는 9.79e−10 (한계 1e−7)이다. 16λ 합집합은 Source를 40→48 µm로 바꿨을 때 28.58987→28.61819 ppm이었다. 이는 고정된 모의 Source의 수치 진단이다. [Edge의 좌표와 6성분 복소장](../../references/m7r18/edge_fields.npz)

## Guided Mode 판정

R17의 단색 Edge 대조와 시간 제한 대조도 재실행했다. 단색 결과의 최대 절대 수치 차이는 1.15e−16 이내였고 시간 제한 결과 JSON은 일치했다. 당시 수 %의 국소 산란장 차이는 평면파와 한 직선 Edge에서 얻은 값이다. 이번 Strip Flux에 그 비율을 곱해 전체 결합 오차를 추정할 근거는 없다. 이 Flux는 입사 표면을 지나는 Power이고, 모서리·편광·상대 위상을 포함한 산란 오차의 norm은 아직 미확정이다.

최소 검증 경로는 같은 Glass 내부 역여기 Power로 정규화한 역방향 E/H를 M2를 거쳐 M1과 같은 면에 확보하고, 실제 SMF 입사 조건의 유한 PEC에 대해 검증한 등가전류 오차 또는 동등한 폐곡면의 접선 E/H 오차를 확보하는 것이다. 역방향 장과 오차의 Lorentz pairing을 사용하며, 근사적으로 Strip에만 적분하려면 그 외 면·모서리·재산란 기여도 제한해야 한다. 대안은 두 반사면과 Glass facet을 포함하는 독립 vector 해에서 에너지 수지와 내부 Guided Mode monitor를 정련·대조하는 것이다. [Reciprocity를 이용한 산란장 Mode 투영](https://doi.org/10.1038/s41467-018-04662-2)

[R14 정규화](M7R14_GUIDED_POWER.md)의 복소 진폭 b=B/(4√(P_r P_launch))에 대해 |δb|≤ε가 입증되면 Power fraction 변화는 2|b|ε+ε² 이하이다. 현재 b와 ε는 모두 미확정이다. R15는 Port 정규화를 제공하며, R16 무한 접평면과 R12 scalar 장은 이 배치의 수신측 역전파 가중치를 제공하지 않는다. 명목 전달 비율·U·M2 회전 광학 응답은 Uncomputed다.

## 재현

```bash
python -m pip install -e '.[test]'
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=6
python -m scripts.m7r18_edge_impact /tmp/r18
python -m scripts.m7r17_cw > /tmp/r18-cw.json
python -m scripts.m7r17_edge > /tmp/r18-edge.json
PYTHONPATH=src python scripts/validate.py
```

첫 계산은 summary.json과 edge_fields.npz를 생성한다. 단색 PEC 독립 재실행에는 Linux C++/OpenMP가 필요하다. 회귀 143건, 기존 Benchmark와 M3-A Adapter가 통과했다.
