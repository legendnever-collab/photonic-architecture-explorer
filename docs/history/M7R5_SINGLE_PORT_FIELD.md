# M7-R5 — 1310 nm Glass Waveguide 한 Port의 External Field

**M7R5-SIM-GLASS-001의 단일 Port Gaussian Fit은 Pass다.** 이상화한 매립 Glass Waveguide를 공기 중에서 평면으로 끝내고 Facet에서 +5 µm 떨어진 곳의 복소장을 계산했다. 이 기준면의 Transverse Field를 Gaussian으로 표현할 때의 Fit 손실은 **0.03934 dB**다. 이 수치는 특정 설계 모델에 귀속된다. Southampton 실물, 두 Port 사이의 Overlap, Total Coupling 및 Fabrication Tolerance는 Uncomputed다.

## 입력과 출처

| 항목 | 값과 근거 |
|---|---|
| Guide | 독립 모의 설계. z<0에서 직선·등방성 Fused Silica. 1310 nm, 20 °C에서 Malitson 분산식으로 cladding n=1.44680432를 계산했다. 횡방향 굴절률 증가량은 설계 가정 Δn=0.007 exp[−(x/4 µm)²−(y/3 µm)²]이다. Gaussian은 여기서 **Index Profile**에만 지정했다. Incident Field는 Solver의 Eigenmode다. |
| Source | Guide의 가장 높은 유효굴절률 두 Mode 중 +X 선형편광 성분이 큰 Forward Mode. 최종 n_eff=1.44917810, 입사 Transverse x 성분 비율 0.9999993. 공기에서 들어오는 파동은 0. |
| Plane·좌표 | Facet 중앙 (0,0,0), Facet 법선 및 전파 +Z, t=+X, s=+Y. 무코팅 평면 Facet 뒤 공기 n=1.000의 z=+5 µm. 재료·형상은 nominal 값이며 실제 Guide의 공정·측정 불확도는 미제공이다. |
| Field·위상 | FMMAX의 Vector Eigenmode와 Facet Scattering Matrix에서 Ex,Ey,Ez,Hx,Hy,Hz를 얻었다. Solver의 exp(−iωt) 출력을 켤레변환해 exp(+iωt)로 기록했다. 모든 성분에 동일한 복소 상수를 적용해 중심 Ex=1로 정규화했다. E/H는 Solver의 상대 단위이며 절대 W 또는 V/m 보정값은 없다. |
| Southampton | M7-R4에서 Chapter 3 배포 목록을 확인했으나 원본 ZIP을 받지 못했다. 이번 작업에 해당 원본은 제공되지 않았다. Fig. 3.5(c–d)의 55 mW 사례와의 파일 대조, 그 사례의 Phase·Fit은 미확인이다. |

[고정 입력·사전 예산](../../references/m7r5/case.json) · [Malitson, JOSA 55 (1965)](https://doi.org/10.1364/JOSA.55.001205) · [FMMAX 알고리즘·시간 Convention](https://github.com/facebookresearch/fmmax) · [Southampton 자료 검토 기록](M7R4_1310_EXTERNAL_FIELD_EVIDENCE.md)

## Fit과 오차 예산

이 독립 모델의 초기 설계에서 단일 Port를 Gaussian으로 치환하는 데 허용할 Normalized Mode-Mismatch를 **0.10 dB**로 먼저 배정했다. 약 2.28%의 제곱 Overlap 감소에 해당한다. 이 중 **0.01 dB**를 수치 여유로 남겨 최종 Fit 손실에 더한 값이 0.10 dB 이하여야 한다. Phase RMS 한계는 **0.10 rad**다. 실물 또는 고객의 허용치, 링크 전체의 오차 상한은 별도 입력이다.

중심·축·방향은 고정하고 두 1/e² Intensity Radius와 두 Wavefront Curvature만 최적화했다. 면적 적분에서 x 편광 Gaussian과 (Ex,Ey)의 정규화 제곱 Overlap을 최대화한다. 전체 Window의 Ey가 분모에 포함된다. Ez는 별도 보고한다. Phase RMS는 Ex 최대 Intensity의 1% 이상 영역에서 하나의 공통 Piston을 제거한 Phase 차이를 Ex Intensity로 가중했다. 이 영역에 Ex 에너지의 97.88%가 들어간다.

| 최종 외부 기준면 | 결과 |
|---|---:|
| Transverse Field Overlap η | 0.99098187 |
| Fit 손실 / 수치 여유 포함 | 0.03934 / 0.04934 dB |
| Phase Residual RMS | 0.02818 rad |
| MFD, t / s | 9.2584 / 8.4246 µm |
| Wavefront Curvature, t / s | +1921.10 / +2816.82 m⁻¹ |
| Ey / Transverse E 제곱노름 | 1.95 × 10⁻⁶ |
| Ez / 전체 E 제곱노름 | 0.2112% |
| 기존 단일 Port Divergence, t / s | 0.09052 / 0.09970 rad |

s축의 기존 0.1 rad 가드까지 여유는 0.00030 rad다. 이 가드는 Fitted Gaussian의 Nominal Divergence를 검사한다. 실제 Guide 편차를 포함하는 여유 또는 두 반사면을 통과하는 설계의 합격 여부는 별도 검증이 필요하다.

## Sampling과 독립 검산

FMMAX의 주기 Supercell을 확장해 인접 Guide 복제의 영향을 점검했다. 입력 굴절률은 셀 중앙에서 샘플링한다. 각 NPZ에는 동일 Plane의 6개 성분에 대한 Complex Fourier Coefficients, Integer Orders, Case ID·입력 SHA, 파장, 기준면 위치, 격자 정보가 들어 있다. 배열 순서는 (component, order)다. 중심 좌표 (x,y)에서 각 항의 공간 인자는 exp[+2πi(m(x/L+½)+n(y/L+½))]이며 x,y,L은 µm다. Fit은 좌표 iL/N−L/2에서 복원한 전체 면적을 사용한다.

| Run | Window / Samples per axis / Fourier terms | Fit 손실 (dB) | Phase RMS (rad) |
|---|---|---:|---:|
| Base | 32 µm / 128 / 193 | 0.03955845 | 0.02816933 |
| Grid | 32 µm / 256 / 193 | 0.03955845 | 0.02816921 |
| Basis | 32 µm / 256 / 317 | 0.03971757 | 0.02819659 |
| Window | 40 µm / 320 / 497 | 0.03934292 | 0.02818331 |

Window 비교는 격자 간격 0.125 µm와 거의 같은 물리적 Fourier Cutoff를 유지한다. 세 비교에서 최대 변화는 손실 0.000375 dB, Phase RMS 0.0000274 rad, 공통 좌표에서 Piston·정규화 후 Vector E 상대 L² 0.00360이다. 각각의 판정 한계는 0.01 dB, 0.01 rad, 0.02다. 이는 관측된 수치 수렴이며 실물 재료·Facet 거칠기·형상 오차의 불확도를 정량화하지 않는다.

공간 Grid로 Fit한 Gaussian을 고정하고 Fourier 계수와 축별 96점 Gauss–Legendre 적분으로 Overlap을 별도 계산했다. 네 Run에서 두 적분의 η 차이는 1.3 × 10⁻¹⁰ 이하다. Solver 자체의 좌표별 복소장과 Export를 대조했고, 모든 Run에서 Facet Flux Balance 오차는 2 × 10⁻¹⁵ 이하이다. 실수 매질에서 Forward Eigenvalue 부호 선택을 안정화하기 위해 Guide 유전율에 +i10⁻¹⁰의 수치 항을 사용했다. 측정 흡수율로 사용하지 않는다. 이 계산에는 독립 실물 측정 또는 별도 Maxwell Solver와의 교차 검증이 없다.

[최종 6성분 Fourier Field](../../references/m7r5/window.npz) · [전체 수렴 결과·해시](../../references/m7r5/result.json)

## 재현

저장된 Monitor의 Fit과 회귀는 기본 프로젝트 의존성으로 실행한다.

```bash
python -m pip install -e '.[test]'
python scripts/m7r5_fit.py
python -m unittest discover -s tests -q
python -m photonic_architecture_explorer.external examples/m7r3_sun_1310_readiness.json
python scripts/validate_m7c.py --output-dir results/runtime-m7c-r5-review
```

Field를 처음부터 계산하려면 별도 Python 3.12 CPU 환경에서 실행한다. 주 앱에는 FMMAX가 필요하지 않다.

```bash
python -m pip install -e . fmmax==1.7.1 jax==0.12.1 jaxlib==0.12.1
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 JAX_PLATFORMS=cpu python scripts/m7r5_capture.py /tmp/m7r5-capture
python scripts/m7r5_fit.py /tmp/m7r5-capture
```

저장된 파일은 SHA-256으로 대조한다. 독립 재계산에서는 BLAS·플랫폼에 따른 반올림 차이를 고려해 Fit 값과 수렴 판정을 비교한다. 1550 nm Proxy 회귀에서 G036-NM의 η=0.9999366495865395를 재현했다. 1310 nm Southampton 예제는 기존 Adapter의 첫 누락 항목 ambient_index에서 Uncomputed가 되고 Overlap과 Total Coupling은 null이다.
