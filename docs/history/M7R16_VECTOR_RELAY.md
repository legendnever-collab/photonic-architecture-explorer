# M7-R16 — 1310 nm Vector Relay 검증 경로

**고정 SMF의 복소 E/H와 Launch Power를 한 쌍으로 전파해 고정 Target의 네 접선 성분을 내보냈다.** 독립적으로 확인한 범위는 균질 공기 전파와 무한 PEC 평면의 선택한 정반사 경로다. 유한 곡면 처방은 아래의 surface-current 경로로 검증한다. 명목 Target 장, P_guided/P_launch와 U, M2 ±1 mrad 광학 응답 및 실물 Total Coupling은 Uncomputed다.

## 사용한 입력과 검증 결과

열린 #46 HEAD c4876ab2927a0eee0b9159add7cb965e6a3785ef에서 출발했다. [사전 경계 모델·수치 예산](../../references/m7r16/plan.md), [R15 Ledger](../../references/m7r15/power.json), R6 SMF 최종 NPZ 및 R12가 기록한 Port·R7·R8 입력 해시를 사용했다. Source는 40 µm 주기 셀에서 공기 쪽 +5 µm 평면의 497개 전진 Fourier order를 갖는다. 원본의 셀 중심 위상과 여섯 복소 계수를 함께 읽었다. 원래 규약에서 E는 E/E_ref, H는 Z₀H/E_ref이고, 셀마다 측정한 +X Launch Power는 1.7426507346302212e−11 m²이다. 이 스케일로 두 reflector의 vertex와 illuminated normal이 정하는 접평면에 입사시켰다.

| 검사 | 독립 기준 | 최대 오차 또는 결과 |
|---|---|---:|
| 비축 TE/TM 성분 두 개의 coherent 합, 서로 다른 3점 | 각 Cartesian 성분의 해석 복소 평면파 합 | 상대 E 2.96e−15, H 2.93e−15, 법선 Flux 8.91e−16 |
| R15 Source의 Maxwell 관계 | H=k̂×E 및 k̂·E=0 | 상대 1.92e−16, 1.16e−17 |
| Source와 +25 µm에서 셀 적분 | R15 monitor와 독립인 공간 Poynting 적분 | 상대 1.36e−14 이내 |
| PEC, 0°·30°·60°, TE·TM·복소 혼합 | 편광별 반사 성분, 접선 전기장 소거, 입사·반사 법선 Flux 상쇄 | 시험한 조합에서 float64 오차 0 |
| R8의 두 무한 접평면을 순서대로 반사한 경로 | Target 관측점 5개를 역순으로 펼친 영상점에서 평가 | 상대 E/H 각각 2.15e−12 이내 |

PEC에서 Q=I−2nnᵀ로 두면 k_r=Qk_i, E_r=−QE_i, H_r=QH_i다. 각 반사 vertex에서 광로 위상을 이어서 보존했다. 두 평면 대조는 해당 순서의 reflected field를 평가한다. [실행 결과](../../references/m7r16/result.json)

[복소장 NPZ](../../references/m7r16/infinite-plane-control.npz)는 World (2,0,2) mm에서 t=−Z, s=+Y, n=+X 기준이다. E_t,E_s,H_t,H_s는 각각 complex128 [t,s] = 64×64, pitch 0.625 µm이다. 좌표·기저·면적·정규화·시간 규약·원본 해시와 control case ID를 함께 저장했다. 이 40 µm 창은 파일 전달 검사에 사용한 계산 창이다.

## 유한 곡면 Nominal 검증 경로

1. **고립 Source 구성.** Source와 M1 사이 거리는 3.078 mm이고 원본 Fourier 셀 폭은 40 µm다. 원본의 이산 order를 그대로 장거리 전파하면 주기 복제 빔들이 함께 전파된다. Source 평면에서 외곽장을 확인하고, 확장한 독립 Port 셀과 충분히 큰 zero-padding/창의 결과를 같은 launch 기준에서 대조한다. Evanescent·backward 성분 처리와 Maxwell 일관성을 기록한다. M1에서의 입사 E/H 차이가 projection 예산에 미치는 영향을 한정한다.
2. **유한 PEC screen.** R11의 surface 좌표·sag·법선·Jacobian과 R8의 두 Aperture를 재사용한다. 고주파 Vector Physical Optics의 첫 경로는 illuminated patch의 등가 전류 J≈2 n×H_inc로부터 복소 dyadic Green 적분으로 다음 면의 E와 H를 함께 계산하는 것이다. n은 조사되는 쪽 공기를 향한다. 정규화 H를 사용하면 전류와 방사 연산자에도 동일 임피던스 규약을 사용한다. M1→M2→Target에서 R12의 진동 위상 sampling, edge panel, 수신 격자·창을 개별 정련한다. 근사 전류가 가장자리, 차폐, 다중 산란을 재현하는 범위는 추가 검증 대상이다.
3. **독립 경계 대조.** 유한 평면 PEC의 edge diffraction부터 open-screen EFIE 또는 독립 full-wave 해와 대조하고, 같은 곡률·Aperture에서 local PO 오차를 평가한다. 명목 두 면 면적은 투영 기준 약 4.23 mm²다. λ/8 간격이면 평면 셀만 약 1.6×10⁸개이므로 dense BEM을 기본 실행 경로로 삼기 어렵다. 축소 사례 통과만으로 명목 오차를 승격할 수 없다. 명목 규모 독립해 또는 적용 범위가 입증된 상한이 필요하다. [Open-screen 경계 적분](https://backoffice.biblio.ugent.be/download/01JAD1HF3FRDSSDEHNE0GQH7MW/01JAD1MFAARXBPQFT1KSQACGM2)
4. **Glass 수신 대조.** 같은 Target 입사 E/H와 Source Power로 두 계산을 수행한다. 첫 계산은 R14의 bilinear reciprocal pairing을 적용하고 R15 Glass 역여기 incident power 1.3442832907e−11 m²로 정규화한다. 두 번째는 입사장을 Glass local 방출 좌표로 회전하고 FMMAX의 exp(−iωt)로 변환한 뒤 공기에서 −z로 향하는 incoming amplitudes를 복원한다. +5 µm 면에서 Facet까지 전파해 guide→air 순의 기존 stack에 a₀=0으로 입력하면 b₀=S₂₂ b_N이다. 균일 Glass 단면에서 정해진 편광의 backward guided mode를 분리하고 그 Power 크기를 P_launch로 나눈다. 네 접선 성분 복원 residual, 분모, 셀 밖 기여, 재반사 조건을 같게 맞춘다. 이 방법은 수신 projection을 독립 점검하며 공유된 입사 Relay 장의 오차는 3번 경계 대조로 검증한다.
5. 두 결과 차이와 정련 잔차를 [R14](M7R14_GUIDED_POWER.md) 절대 예산과 비교한다. 측정되지 않은 coating, mounting 및 backing 광학 응답은 이상 PEC 모델 바깥에 있다. +1 mrad 기계 Clearance는 기존 기준보다 0.710 µm 부족하다.

## 재현

```bash
python -m pip install -e '.[test]'
OPENBLAS_NUM_THREADS=2 python -m scripts.m7r16_vector_reference results/runtime-m7r16
OPENBLAS_NUM_THREADS=2 PYTHONPATH=src python scripts/validate.py
```

로컬 회귀에는 저장된 네 복소 성분, 축, Power 및 case 표기의 재현 검사가 포함된다.
