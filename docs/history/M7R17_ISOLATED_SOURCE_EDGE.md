# M7-R17 — 고립 SMF의 M1 입사장과 유한 PEC Edge

**곡면 반사 계산은 보류한다.** 고립 Source의 셀을 40→48 µm로 늘리면 M1의 적분 Flux/Launch 변화는 5.52e−7이지만 표본 복소 E/H는 각각 9.52e−4 변했다. 사전 한계는 5e−5다. 유한 평면 PEC의 직선 Edge에서도 표준 Physical Optics(PO) 전류의 편광별 오차가 1e−4 한계보다 크다. 명목 전달 비율·U·M2 회전 광학 응답은 Uncomputed다.

## 고정 입력과 Source 검증

검증된 #46과 #47을 병합한 Main f2479ce42564ea32f4af2e5adbbbbae19a5ef614에서 시작했다. R15 Ledger의 SMF 공기면 Launch 1.7426507346302212e−11 m², R8 확장안 M1의 vertex (3.077955, 0, 0) mm, normal, sag, Aperture를 사용했다. [사전 예산](../../references/m7r17/plan.md) · [R15](M7R15_PORT_POWER.md) · [R16 접평면 대조](M7R16_VECTOR_RELAY.md)

같은 SMF를 32/40/48 µm 주기 셀, 각각 317/497/717 Fourier 성분과 0.125 µm 재료 격자에서 비교했다. 마지막 셀은 동일 FMMAX 캡처를 다시 실행했다. 각 셀에서 방출장을 한 셀만 취하고 중심·상대 위상을 보존했다. 공동 진폭계수 0.9998588074, 1.0000000000, 0.9999405290을 E/H에 곱해 R15 Launch를 맞췄다. 무한 개방 SMF의 정확한 장은 아직 확정되지 않았다. [48 µm 고정 입력](../../references/m7r17/source48.json) · [6성분 Field](../../references/m7r17/source48.npz) · [Flux 기록](../../references/m7r17/source48.power.json)

Source 평면의 J=n×H와 M=−n×E를 하나의 고립 셀에서 자유공간 dyadic Green 함수로 방사시켰다. 각 M1 표본은 실제 곡면 위에 있다. E/H 오차는 같은 28×28 Gauss 노드에서 위상 정렬 없이 계산한 상대 ℓ²다. Flux는 곡면 Jacobian과 조사면의 법선 부호를 포함한 Poynting 적분이다. E/H는 E/E_ref 및 Z₀H/E_ref 단위, 좌표와 성분은 Source 기준 (t,s,d) 순이다. [M1 복소장·면적 벡터](../../references/m7r17/m1.npz)

| 비교 | E 상대차 | H 상대차 | Flux/Launch | 이전 셀과 Flux 차이 |
|---|---:|---:|---:|---:|
| 32 µm | — | — | 0.999595274 | — |
| 40 µm | 4.667e−3 | 4.667e−3 | 0.999600773 | 5.50e−6 |
| 48 µm | 9.515e−4 | 9.515e−4 | 0.999601325 | 5.52e−7 |

48 µm Source에서 적분 pitch 1→0.5 µm 차이는 E/H 각각 1.47e−5, Flux 2.27e−9다. 1 µm pitch에서 M1 수신 quadrature를 축당 28→40점으로 높이면 Flux는 1.48e−8 변한다. 셀 정련에 따른 Field 변화가 이들보다 크다.

같은 48 µm Source에서 zero-padding한 Angular Spectrum 전파 창만 독립적으로 바꿨다. 동결 셀을 1 µm로 샘플링하고 6성분 equivalent-current 스펙트럼을 실제 M1 좌표에 직접 합산했다. 이 pitch의 주파수 사각형은 light cone 안에 있다. 아래는 고립 셀의 비주기 공간 적분(0.5 µm pitch)에 대한 차이다. 768 µm 창의 비물리적인 Flux는 반복 복제장의 합에서 나온다. 1536 µm에서도 Flux·Field 모두 기준을 넘었다. [전체 수치](../../references/m7r17/source_result.json)

| 전파 창 | E 상대차 | H 상대차 | Flux/Launch 차이 |
|---|---:|---:|---:|
| 768 µm | 2.797 | 2.797 | 1.716 |
| 1152 µm | 0.1651 | 0.1652 | 8.08e−3 |
| 1536 µm | 0.02703 | 0.02702 | 1.89e−4 |

## 유한 평면 PEC의 독립 Edge 대조

M1과 같은 1.451494 × 1.420204 mm 직사각형, 12.48734° 입사, 이상적 무두께 PEC를 사용했다. 단위 TE와 TM 평면파를 각각 조사하고 왼쪽 Edge 중앙에서 안쪽으로 −2, 0, 2, 8 λ, 높이 +3 λ인 네 점을 관측했다. PO는 조사면의 J=2n×H_inc를 유한판 전체에 적분한다. 독립 기준은 Sommerfeld half-plane의 Dirichlet(E_y)·Neumann(H_y) 해이며 반대 벡터는 Maxwell curl로 구했다. [Sommerfeld 해와 전자기 경계조건](https://kirkmcd.princeton.edu/examples/sommerfeld.pdf)

**1310 nm 단색파.** 열린 3D Green dyadic으로 반대쪽 Edge와 모서리를 포함한 전체 직사각형 PO 산란장을 계산했다. 독립 half-plane 기준은 선택한 직선 Edge 근방을 기술한다. 단색 차이에는 유한판의 다른 경계도 기여할 수 있다. 아래 Flux 오차는 네 점 중 최대 법선 산란 Flux 차이를 peak 입사 법선 Flux로 나눈 값이다. [정련별 E/H·Flux](../../references/m7r17/cw_result.json)

| 편광 | E 상대차 | H 상대차 | 정규화 Flux 차이 | PO pitch λ/8→λ/16의 E / H 상대 변화 |
|---|---:|---:|---:|---:|
| TE | 7.274% | 6.869% | 0.09692 | 1.09e−3 / 9.79e−4 |
| TM | 7.273% | 7.355% | 0.10945 | 8.25e−4 / 8.24e−4 |

**다른 Edge의 영향 분리.** 1310 nm carrier에 32주기 sin⁴ envelope를 씌우고 20주기 시점의 복소 산란장을 비교했다. 빛이 이 시간에 이동하는 거리는 20λ이고 가장 가까운 옆 Edge도 542λ 이상 떨어져 있다. 조사 전면의 지연 x sinθ/c는 판 위에서 음수가 될 수 없다. 따라서 이 시간 구간의 유한판 응답은 선택된 직선 Edge의 causal 해를 사용해 대조할 수 있다. PO 측은 유한판 retarded current와 시간 도함수·적분으로 계산하고, 기준 측은 독립 주파수-domain Sommerfeld 해로 펄스를 합성했다. Flux는 복소장 진단량 ½ Re(E×H*)의 법선 성분이다. [시간 구간별 검증 근거와 최종 복소장](../../references/m7r17/edge_result.json)

| 편광 | E 상대차 | H 상대차 | 정규화 Flux 차이 | PO pitch λ/16→λ/32의 E / H 상대 변화 |
|---|---:|---:|---:|---:|
| TE | 6.468% | 6.476% | 0.09276 | 2.45e−4 / 2.44e−4 |
| TM | 6.436% | 6.480% | 0.10826 | 2.02e−4 / 2.02e−4 |

Reference 합성 주기 512→1024, 시간 간격 1/8→1/12 주기와 공간 미분 간격 절반 대조에서 가장 큰 E/H 상대 변화는 4.52e−8 미만이다. PO 마지막 mesh 변화도 1e−4에 도달하지 못했으며, 관측된 모델 간 차이는 마지막 mesh 변화보다 두 자릿수 이상 크다. 이 비교는 평면파로 강하게 조사한 한 Edge의 국소 진단이다. 실제 SMF의 Edge 조사량과 Glass Mode 투영 가중치가 있어야 명목 전달 오차로 연결할 수 있다.

## 재현

```bash
python -m pip install -e '.[test]'
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=6
python -m scripts.m7r16_vector_reference /tmp/r16-replay
python -m scripts.m7r17_source /tmp/r17-results
python -m scripts.m7r17_cw
python -m scripts.m7r17_edge
PYTHONPATH=src python scripts/validate.py
```

Source 및 단색 PO 실행은 Linux C++/OpenMP를 사용한다. 48 µm Source 자체의 재캡처는 R15의 Python 3.12, FMMAX 1.7.1, JAX/JAXLIB 0.12.1 환경에서 아래와 같이 별도 디렉터리에 실행한다. 회귀 141건, Benchmark와 M3-A Adapter 검사가 통과했다.

```bash
JAX_PLATFORMS=cpu python -m scripts.m7r5_capture /tmp/r17-new --case references/m7r17/source48.json --run window --power-ledger
```
