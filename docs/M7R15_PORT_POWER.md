# M7-R15 — 1310 nm SMF·Glass Port Power 정규화

**동결된 두 FMMAX Port의 내부·외부 Power를 저장 E/H와 연결했다.** Glass의 내부 역여기 Power와 SMF의 공기면 Launch Power를 각각 최종 Fourier 장과 같은 정규화로 제공한다. 정련에서 Facet 투과율은 안정적이었고 중심 Ex=1 스케일에서 면적 적분 Power는 더 크게 변했다. 명목 Relay의 전달 비율과 불확도는 **Uncomputed**다.

## 기준과 단위

#41–#45를 Main에 순서대로 병합한 뒤 `5af007336e001740dfb630231c9e74c1a2f1d1cd`에서 시작했다. 이 Main과 검증된 #45 HEAD의 파일 트리가 같다. [사전 검증 범위](../references/m7r15/plan.md), [R5 Glass](M7R5_SINGLE_PORT_FIELD.md), [R6 SMF](M7R6_SMF_GLASS_FIXED_PORT.md), [R14 투영 규약](M7R14_GUIDED_POWER.md)을 적용했다.

두 Facet 모두 내부는 local z<0, 경계는 z=0, 공기면은 z=+5 µm다. 캡처의 법선은 local +z다. 이 방향은 Relay 세계 좌표에서 Glass 역방출 −X, SMF 순방향 +X다. 따라서 아래 reflected Power에는 음의 부호가 붙고, Glass outgoing도 R14의 수용 법선 +X에서 읽으면 음수다. R14에 넣는 내부 역여기 Power의 **크기**는 양수다.

공기에서 정상 입사 평면파로 FMMAX의 `H_export = Z₀ H/E_ref`, `E_export = E/E_ref` 규약을 검사했다. 캡처는 기존과 같이 FMMAX 장을 켤레변환해 exp(+iωt)로 맞춘 후 공통 복소계수 c=conj(Ex_solver(0,0))로 나눈다. c와 Solver의 signed 평균 Flux를 [Power ledger](../references/m7r15/power.json)에 저장했다. FMMAX monitor에 셀 면적 A를 곱하고 |c|²으로 나누면 저장장과 같은 Power가 된다. 표의 값은 이 기준에서 m² 단위를 가지며, 중심 전기장 스케일 E_ref를 V/m로 지정하면 E_ref²/Z₀를 곱해 W로 환산할 수 있다. [FMMAX Flux API](https://facebookresearch.github.io/fmmax/API/fields.amplitude_poynting_flux/)

## 최종 Window 결과

| 동결 Port | Guided incident [m²] | Guided reflected, signed [m²] | Air outgoing [m²] | T | R |
|---|---:|---:|---:|---:|---:|
| Glass 역여기 | 1.3442832907e−11 | −4.5513986198e−13 | 1.2987693045e−11 | 0.9661425635 | 0.0338574365 |
| SMF 순방향 | 1.8035852229e−11 | −6.0934488232e−13 | 1.7426507346e−11 | 0.9662147996 | 0.0337852004 |

T=P_air,out/P_guide,in, R=−P_guide,refl/P_guide,in이다. 내부 Flux는 incident와 reflected 모드를 따로 여기해 얻었고, 합을 두 성분을 같이 넣은 monitor와 대조했다. 모든 run에서 최대 |T+R−1|은 2.10e−15 미만, 내부 monitor 합의 상대차는 3.23e−16 미만이다. 이는 모델 내부의 Power 보존 검사다.

8개 기존 NPZ와 Case 해시를 확인했다. 새 캡처의 6성분 Fourier 계수는 기존 장과 상대 L² 9.56e−13 이내에서 일치했다. 기존 Fourier E/H를 공간 격자로 복원한 Poynting 적분은 정규화한 Solver monitor와 상대차 3.42e−14 이내에서 일치했다. 원본 R5/R6 NPZ와 Case는 각 manifest의 해시대로 유지했다.

| 정련 | Glass ΔT | SMF ΔT | 중심 Ex=1 Power의 최대 상대 변화 Glass / SMF |
|---|---:|---:|---:|
| Grid 128→256 | 2.21e−12 | 7.68e−7 | 6.54e−10 / 3.34e−3 |
| Basis 193→317 | 3.68e−7 | 4.79e−7 | 2.60e−3 / 6.70e−3 |
| Window 32→40 µm, 317→497 terms | 6.43e−8 | 8.10e−8 | 1.34e−4 / 2.82e−4 |

마지막 단계는 격자 간격 0.125 µm와 물리적 Fourier cutoff를 가깝게 유지한 Window 비교다. 두 Port에서 T/R 변화와 balance를 합한 진단값은 4.33e−7 및 1.33e−6으로 각각 2.5e−4 할당 내다. 중심 Ex=1 Power의 상대 변화 합은 약 0.274%, 1.032%다. 같은 2.5e−4 진단 기준을 넘는다. 이 변화에는 모드 폭과 형상에 대한 정련 영향이 포함된다. 동일 run에서 E/H와 Power를 함께 사용하면 임의 공통 스케일은 투영 비율에서 상쇄된다. 어느 정련 차이도 실제 장치나 Relay의 오차 상한을 입증하지 않는다.

## R14에 넘기는 값

- **Glass 내부 역여기 Power.** 최종 R5 역방출장과 표의 incident 크기 1.3442832907e−11 m²를 한 쌍으로 사용한다. 또는 같은 장의 outgoing 크기를 T로 나눠 복원한다. 이 기준은 Glass Facet의 역방출 투과를 반영한다.
- **SMF 공기면 Launch Power.** 최종 R6 장과 표의 outgoing 1.7426507346e−11 m²를 한 쌍으로 사용한다. 단위 Launch로 계산할 경우 두 E/H에 동일한 Power 정규화 계수를 적용한다. 새 전파 계산에서 그 Source 장과 동일한 스케일의 도착장을 저장해야 한다.
- **명목 Relay 평가.** 고정 Target 공기면의 복소 E_t,E_s,H_t,H_s와 동일 여기 기준의 Launch Power, 검증된 두 반사면의 편광별 경계 및 독립 Glass 내부 전진 Guided Mode monitor가 필요하다. R12의 Scalar 도착장은 E와 ∂xE를 제공한다. 명목 전달 비율과 U, M2 ±1 mrad 광학 응답, 실물 Total Coupling은 Uncomputed다.

## 재현

Python 3.12 CPU 환경에서 실행했다. `--power-ledger`는 기존 NPZ 쓰기에 각 run의 Power JSON을 추가한다.

```bash
python -m pip install -e '.[test]' fmmax==1.7.1 jax==0.12.1 jaxlib==0.12.1
export OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 JAX_PLATFORMS=cpu
python -m scripts.m7r5_capture /tmp/pae-r15-glass --power-ledger
python -m scripts.m7r5_capture /tmp/pae-r15-smf --case references/m7r6/case.json --power-ledger
python -m scripts.m7r15_port_power /tmp/pae-r15-glass /tmp/pae-r15-smf
python -m scripts.m7r14_guided_power
PYTHONPATH=src python scripts/validate.py
```

로컬 회귀 138건, Benchmark 및 M3-A Adapter gate가 통과했다.
