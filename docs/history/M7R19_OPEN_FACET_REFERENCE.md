# M7-R19 — 독립 개방경계 SMF Facet Reference

**독립 복소장을 확보했으나 M1 입사장의 절대 정확도는 미확정이다.** 12 pixels/µm의 Meep Facet 장과 R17의 48 µm 장을 같은 M1으로 전파하면 E/H 상대차가 각각 1.443%, signed ΔFlux/Launch는 −3.9171e−4였다. 세 관측 차이가 각각 5e−5 예산을 넘는다. 독립 해 자체의 격자 변화와 H 추출 오차도 예산보다 크므로 R17에 이 차이를 그대로 오차로 배정할 수 없다. 명목 전달 비율·U·M2 회전 응답은 Uncomputed다.

## 입력과 독립성

#48과 #49를 차례로 병합한 Main `f7970886f42e0915ac8c96a6564bc4ac79b5597a`에서 시작했다. R6 모의 SMF, 고정 Glass Port, R8 확장 처방·Aperture, R15 공기면 Launch 1.7426507346302212e−11 m²(정규화 단위)를 사용했다. 측정 데이터는 포함하지 않는다. [R6 단면](../../references/m7r6/case.json) · [R18](M7R18_SOURCE_EDGE_IMPACT.md) · [계산 전 예산과 중단 조건](../../references/m7r19/plan.md)

- Meep 1.35.1 CPU FDTD에서 λ₀=1.310 µm, core 반경 4.1 µm, n_clad=1.446804317553, n_core=1.451304317553, 공기 n=1, 평탄한 무코팅 facet z=0을 적용했다. R6의 1e−10 허수 유전율 regulator는 고유값 가지 선택용이므로 독립 해는 명시적으로 무손실 극한을 사용했다. 원통 좌표 m=+1 성분과 y 반사 대칭으로 x-편광 실험을 구성했다. 같은 단면의 무한 직선 SMF에서 J₁/K₁를 사용해 네 접선 연속조건을 만족하는 hybrid fundamental 해를 구했다(n_eff=1.449006490364). [Meep 원통 좌표](https://meep.readthedocs.io/en/stable/Python_Tutorials/Cylindrical_Coordinates/)
- 전류면 z=−7 µm에서 모드의 접선 H로 전기 표면전류를 설정했다. 양방향 여기 중 +z 진행 성분은 z=−4 µm 직선 guide에서 독립 측정했다. Facet 실행에서는 같은 입력면, 공기면 z=+5 µm와 두 면을 잇는 반경 43 µm 측면 Flux를 기록했다. 개방영역 반경 44 µm와 z=±12 µm 밖에는 두께 2 µm PML을 두었다. 8 및 12 pixels/µm 각각 직선 guide와 Facet을 실행했다.
- 두 기준면에 0.25 µm 간격으로 등록한 radial point DFT monitor가 (Er,Eφ,Ez,Z₀Hr,Z₀Hφ,Z₀Hz)를 제공한다. ±m의 선형결합, 공통 축 중심 위상, exp(+iωt)로의 켤레 변환을 적용했다. 입사광축은 Source의 +d, x/y는 t/s다. 단일 실수 진폭으로 반경 43 µm 원판의 복원 Power를 R15 Launch에 맞춘 후 모든 crop에 같은 계수를 사용했다. 연속축 위상은 축 대칭으로 보간한 (Er−iEφ)/2에서 정했다. [네 원시 Export와 Monitor](../../references/m7r19/)
- Source를 구한 FDTD는 R17 FMMAX와 독립이다. Source 이후는 양쪽 모두 R17의 비주기 Love-current 적분, 0.5 µm pitch, 같은 곡면 28×28 위치와 면적 벡터를 사용했다. 따라서 비교는 Source 교체 효과를 진단한다.

## 대조 및 중단

| 측정량 | 8 pixels/µm | 12 pixels/µm |
|---|---:|---:|
| 직선 SMF 접선 E / H 상대차 | 5.2451e−3 / 1.0935e−1 | 7.8453e−4 / 4.4681e−2 |
| Native input-net − output − side, 절대값 / incident | 2.1225e−6 | 8.3001e−7 |
| 직선장 차감 반사 + 투과 + 측면 수지 잔차 | 7.0164e−5 | 1.0189e−5 |
| 복원한 공기면 Power와 native monitor 상대차 | 1.2110e−1 | 4.7909e−2 |
| 공기면 DFT 추가 시간에 따른 E / H 변화 | 1.891e−6 / 1.907e−6 | 1.314e−6 / 1.324e−6 |

직선 Mode 오차는 반경 가중치 r을 사용한 접선 성분 norm이다. E에서 공통 복소 여기 계수 하나를 정하고 H에도 그대로 적용했다. 공기면 대조는 직선 guide에서 구한 radial export/native monitor Power 비를 Facet에 그대로 사용했다. Native flux 폐합이 잘 되어도, 그 Power를 운반하는 복소 E/H가 정확하게 추출됐는지는 별도 검사가 필요하다. DFT 시간 연장은 25 µm/c다. [부호를 포함한 Power ledger·위상·정규화 계수](../../references/m7r19/summary.json)

## M1의 공통 영역과 외곽 기여

모든 상대 norm의 분모는 R17 전체 48 µm Source가 만드는 M1 E 또는 H norm이다. ΔFlux는 첫 장에서 기준장의 M1 입사 Flux를 뺀 값을 R15 Launch로 나눴다. 원판은 Meep 출력을 측정한 반경 43 µm까지만 포함한다.

| M1에서 비교한 두 입력 | E 상대차 | H 상대차 | signed ΔFlux/Launch |
|---|---:|---:|---:|
| 12 px/µm 중앙 40 µm − R17 48 µm 장의 중앙 40 µm | 0.01442594 | 0.01442594 | −3.91648e−4 |
| 12 px/µm 중앙 48 µm − R17 48 µm | 0.01442562 | 0.01442562 | −3.91856e−4 |
| 12 px/µm 원판 − 같은 장의 중앙 48 µm | 8.34260e−5 | 8.34263e−5 | +1.49048e−7 |
| 12 px/µm 원판 − R17 48 µm | 0.01442586 | 0.01442586 | −3.91707e−4 |
| 12 − 8 px/µm 원판 | 0.01059931 | 0.01059931 | −6.84703e−4 |

공기면 자체의 공통 48 µm 영역에서 12 px/µm와 R17의 6성분 비교는 E 1.882%, H 1.875%였다. 이번 독립 비교에서는 공통 48 µm 내 장 차이가 바깥을 복원한 기여보다 크다. R18의 40→48 µm 셀 변화에서 공통 영역과 외곽 복원의 M1 E 기여는 각각 6.7074e−4와 8.0106e−4였다. 두 실험의 기준장이 다르다. 이번 격자 변화와 직선 대조의 H 차이가 사전 중단 기준(5e−5의 10배)을 초과해 18 pixels/µm, PML 두께·경계 거리의 독립 정련은 보류했다. 원판 외부 잔여장과 불확도 상한은 미확정이다.

## 재현과 외부 실행 입력

기존 프로젝트 환경에서 저장장을 즉시 재분석할 수 있다.

```bash
python -m pip install -e '.[test]'
OPENBLAS_NUM_THREADS=1 PYTHONPATH=src python -m scripts.m7r19_reference references/m7r19
PYTHONPATH=src python scripts/validate.py
```

같은 네 계산을 새로 실행하려면 별도 conda-forge 환경에서 수행한다. Linux x86-64 CPU로 실행했고 Meep는 앱의 런타임 의존성에 추가하지 않았다.

```bash
micromamba create -y -n pae-r19 -c conda-forge 'pymeep=1.35.1=nompi*' scipy
mkdir -p /tmp/r19
for n in 8 12; do
  micromamba run -n pae-r19 python -m scripts.m7r19_capture /tmp/r19/straight$n.npz --resolution "$n" --straight
  micromamba run -n pae-r19 python -m scripts.m7r19_capture /tmp/r19/facet$n.npz --resolution "$n"
done
OPENBLAS_NUM_THREADS=1 PYTHONPATH=src python -m scripts.m7r19_reference /tmp/r19
```

외부 고정밀 해석도 같은 원형 단면·facet·x-편광 여기와 +5 µm 공기면을 사용해야 한다. Solver/버전, 위상·좌표계, 격자별 6개 복소 성분 및 collocation, 내부 incident/reflected와 측면·공기면 outgoing monitor, 기준면 밖 누락 Power를 함께 제출한다. 우선 직선 guide와 균일 평면파에서 E/H 비와 native Flux를 대조한 후 격자·PML·창·export pitch를 독립 정련하고 잔여 오차를 합산한다. M1에서 각 관측 차이에 정당화된 불확도를 더해 5e−5 이내일 때 Source 정확도를 판정한다. 수신측에는 R18의 별도 Edge 투영 검증이 필요하다.

로컬 회귀 146건, Benchmark와 M3-A Adapter 검사가 통과했다.
