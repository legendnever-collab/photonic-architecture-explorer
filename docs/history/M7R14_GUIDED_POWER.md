# M7-R14 — 1310 nm Glass Guided Mode 전달 Power

**명목 판정은 Uncomputed다.** 정규화된 Reciprocal E/H Projection은 해석해가 있는 Single Mode 및 Facet 대조를 통과했다. 고정 처방의 R12 저장장은 한 개의 scalar Helmholtz 해다. 두 반사면을 통과한 벡터 편광과 같은 여기 조건의 SMF 공기면 Launch Power를 복원할 자료가 부족하다.

## 물리량과 기준면

[사전 계산 계약](../../references/m7r14/plan.md)에 고정한 양은 SMF 공기면에서 전진하는 Power 중 Glass 내부의 지정 Fundamental Mode로 나가는 비율이다. 이 정의는 Glass Facet의 투과를 포함한다. SMF 내부에서 외부 기준면까지의 손실은 분모 앞에 있다. R6 두 Port, 확장안의 두 곡면·Aperture, 5.023725 mm Envelope와 Guard의 입력 해시를 R12 manifest와 대조했다.

같은 peak phasor 규약에서 Target의 법선 n은 Glass를 향한다. B는 공기면에서 실제 입사해 i와 내부 Glass Mode를 역으로 여기한 해 r의 Lorentz pairing이다. 폐곡면에 reciprocity를 적용할 때 공기면과 균일한 guided 단면 사이의 다른 경계항이 소거되어야 한다. 충분한 횡방향 적분면, reciprocal 경계, 고립된 수신계 또는 일관되게 취급한 재반사를 전제한다. 공기면에서 같은 쪽으로 나가는 파끼리의 pairing은 전체면에서 소거된다. 내부 lossless mode 쌍의 pairing 크기가 4P_r이므로

    B = ∫ [(E_r × H_i) − (E_i × H_r)] · n dA
    P_guided/P_launch = |B|² / (16 P_r P_launch)

P_r은 Glass 내부 역여기 Mode의 incident power 크기다. 외부 방출 Flux로 이를 대체하면 Facet 손실이 정규화에서 사라진다. i, r은 각각 임의 위상을 가질 수 있고 각 해의 Power와 일관된 진폭 스케일을 쓰면 그 스케일도 상쇄된다. [Reciprocity에 의한 모드 추출 근거](https://doi.org/10.1038/s41467-018-04662-2)

## 실행한 대조

| 대조 | 독립 기준 | 계산 결과 |
|---|---|---|
| 단일 진행 TE₁₀, 같은 lossless PEC Guide | Z_TE=Z₀/[1−(λ/2a)²]¹ᐟ², P=ab·abs(E_peak)²/(4Z_TE), 전달 비율 1 | 16/32점에서 1.0000000000000002 / 1.000000000000001 |
| Reverse 대신 같은 방향의 Guide 해 | 반대 부호의 두 항이 소거, 비율 0 | 두 격자에서 2e−34 미만 |
| n=1 → 1.5, 무코팅 평면 경계에 수직 입사 | Fresnel power 4n/(1+n)² = 0.96 | 0.9600000000000001 |
| R5 최종 Fourier E/H의 Target 좌표 변환 | 방출 좌표의 계수 Parseval 적분과 Target 격자의 Poynting 적분 크기 일치 | Target 법선 signed flux −1.2987693e−11 (상대 E·H 단위 × m²), 상대 차이 0 (float64) |

TE₁₀ 분모는 연속 모드의 닫힌식에서 계산했다. Fresnel 대조는 별도 횡편광에서 Glass 내부 역여기와 공기면 방출의 비례상수를 검사한다. 추가 회귀는 원편광에서 시간역전 쌍과 직교 쌍의 1/0을 검사한다. R5의 값은 저장장 단위에서 한 주기 셀에 대한 결과다. 이를 절대 W나 실제 수광면으로 해석할 근거는 없다.

## 저장장의 적용 범위

- [Glass R5](M7R5_SINGLE_PORT_FIELD.md)의 방출은 local +z다. World로 회전하면 local (x,y,z)는 (+Z,+Y,−X)에 대응한다. Target frame에서 방출장을 읽을 좌표는 (−t,s)이고 성분은 (−E_x,E_y,−E_z), H도 같은 회전을 따른다. 이 표기에는 추가적인 시간역전이 없다. [R6](M7R6_SMF_GLASS_FIXED_PORT.md)의 중심 Gaussian은 위상과 폭을 담지만 Vector Flux의 정규화를 제공하지 않는다.
- [R5 캡처](../../scripts/m7r5_capture.py)는 여섯 성분을 on-axis Ex로 나눈다. 내부 incident/reflected와 외부 outgoing power를 실행 중 계산하나 저장한 값은 balance residual이다. 단일 잔차는 역여기 Power와 외부 방출 Power의 비를 결정하지 않는다. R6 SMF의 상대 단위 방출장은 향후 Vector Source 입력으로 쓸 수 있다.
- [R12](M7R12_CURVED_QUADRATURE.md)의 두 Target 파일에는 ts_m, E, dE_dx가 있다. launch flux 0.9980217523은 주어진 Gaussian의 각 스펙트럼에 축 방향 파수 가중치를 적용한 scalar 값이다. 두 반사면의 scalar Dirichlet 조건에는 두 편광의 벡터 경계 응답이 없다. 균일한 공기에서조차 각 진행 평면파에는 두 독립 횡편광이 있어 한 전기장 성분과 그 축 방향 미분만으로 두 성분이 결정되지 않는다. 한 편광의 국소 평면파 임피던스를 모든 공간주파수에 대입하면 모델 가정이 추가된다.
- 사전 설정한 명목 수치 오차 1e−3은 연구용 예산이다. 누락된 편광·Flux 오차에 상한이 없으므로 명목 전달 비율과 U를 모두 Uncomputed로 둔다. R13의 192 µm half-window η=0.989810812816은 기존 유한면 결과다. R10 전체면 0.99 판정, M2 ±1 mrad 광학 응답, 실물 Total Coupling도 Uncomputed다.

## 재개에 필요한 최소 비기밀 Export

1. **Forward run.** 고정한 R6 Source 공기면에서 전진 E/H로 계산한 P_launch와, 같은 여기로 두 반사면을 지난 Target 공기면의 복소 E_t,E_s,H_t,H_s를 저장한다. 분모와 도착장의 공통 amplitude scale, 법선, m 단위 좌표와 면적 가중치, E/H 단위·phasor, solver/version, 편광별 반사 경계와 Aperture를 기록한다. 직사각 격자의 경우 독립 1D 축 두 개로 충분하다.
2. **Reverse run.** R5의 같은 Guide·Facet·Mode·주기로 역여기한다. 기존 상대단위 방출장을 재사용하려면 기존 캡처가 계산하는 T_rev = P_air,out/P_guide,in 한 값과 수치 오차를 같은 run에서 추가로 내보낸다. 저장장으로 구한 abs(P_air,out)를 T_rev로 나누면 그 E/H 단위로 P_r을 정할 수 있다. 한편 두 solver가 서로 다른 E/H 단위(특히 H 임피던스)를 쓰면 양쪽을 동일한 규약으로 변환해야 한다. 공통 시간 위상 원점은 임의이며 두 장의 축·phasor·상대 성분 위상은 일치해야 한다.
3. **적분과 대조.** 두 장을 같은 물리 평면에 두고 같은 면적 가중치로 B를 적분한다. R5의 40 µm 주기장은 임의의 넓은 창에 반복 복제하지 않는다. 격자 간격과 횡방향 영역, Fourier basis, Mirror edge를 각각 정련하고 계면·반사 경계 조건과 분모의 방향 분리를 확인한다. 동일 Vector 입력에 대해 Glass 내부의 독립 전진 mode monitor로 P_guided/P_launch를 비교한다. 각 항목 오차와 잔여분을 사전 계약의 절대 예산에 넣을 수 있을 때 명목 수치를 보고한다.

## 재현

저장소 루트에서 아래 명령을 실행한다. 마지막 두 명령은 R13 유한면 진단과 전체 회귀다.

```bash
python -m pip install -e '.[test]'
python -m scripts.m7r14_guided_power
python -m scripts.m7r13_target_acceptance
PYTHONPATH=src python scripts/validate.py
```

로컬 회귀 138건, Benchmark gate 및 M3-A Adapter gate가 통과했다.
