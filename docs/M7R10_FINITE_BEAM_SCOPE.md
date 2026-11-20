# M7-R10 — 1310 nm 확장안 Finite-beam 검증 범위

## 동결 입력

기준 Main은 `7e523aca5e05a96f29ad1a54d3b5546109177832` ([CI 44706481909](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44706481909))이다.
[M7-R8의 expansion 처방](../references/m7r8/summary.json), [M7-R7 Package](../references/m7r7/case.json),
[M7-R6 Fixed Ports](../examples/m7r6_smf_glass_1310.json)를 입력으로 사용한다.
Port 양쪽은 시뮬레이션의 외부 Gaussian Fit이고, 배치는 비기밀 Nominal 가정이다.
5.023725 mm X Envelope, 50 µm 기구 Clearance, 2.2 mm per-axis full aperture cap,
기존 Solver Guard와 M7-R7의 여유 목표를 고정한다.

| 항목 | 고정한 좌표와 모델 |
|---|---|
| Source / Target | World XYZ에서 (0, 0, 0) / (2, 0, 2) mm. 두 외부면은 각각 X=0 / X=2 mm. 모두 전파축 +X, s=+Y, t=s×d=−Z |
| Field | 1310 nm vacuum, homogeneous n=1, exp(+iωt), forward exp(−ikz). 고정 JSON의 MFD 및 곡률에 대응하는 정규화된 scalar Gaussian. Target은 Reciprocal acceptance convention 사용 |
| M1 / M2 | vertex X=3.077955 / −1.216011 mm, Y=0, Z=0 / 2 mm. 정확한 vertex·illuminated normal·곡률은 동결 JSON에 보존 |
| 유효 Aperture | local (u,v) rectangular half width. M1 (725.747, 710.102) µm, M2 (751.167, 723.565) µm. u축 s×n, v축 s, illuminated normal 방향 sag h=(κt·u²+κs·v²)/2 |
| Package | World AABB는 약 (−1.582177, −1.35, −1.35)에서 (3.441547, 1.35, 3.35) mm. 각 patch AABB는 −normal 방향 150 µm Backing sweep으로 확장하고 World 축마다 50 µm Padding. Source/Target 쪽에 고정 Keepout AABB 2개 |
| 실제 자료 | 유효 개구의 Edge·Bevel·Coating 경계, Surface figure, Backing·Mount·접착층의 실제 불투명 형상, Package/Keepout CAD와 Datums, M1/M2의 설치 위치·회전축·Pivot 및 조합 공차가 미제공. M7-R7 AABB는 기구 검사용 포락 형상이고 광학 차폐면은 별도 입력 |

## 사전 검증 범위와 합격 기준

확장안의 **Nominal, M2 −1 mrad, M2 +1 mrad** 3개를 고정한다. M6-D와 같이
M2 vertex를 통과하는 World +Y 축 주위에서 오른손 규약으로 회전한다.
M2의 normal, aperture 및 부착 body를 같은 pose로 이동한다. 기구 프록시는 기존
방식으로 회전한 patch와 Backing의 World AABB를 다시 만들고 같은 World Padding을 적용한다.
M1, Package, Keepout, 두 Port, Target 중심·방향을 유지한다. 각도는 진단값이며 실제 공차는 미제공이다.

이번 범위의 추가 계산은 3개 pose의 기구 AABB 비교까지다. Wave-Optics 실행은
아래 계약을 만족하는 독립 모델이나 Field Export가 확보되면 Nominal부터 시작한다.
Nominal에서 적용성과 수렴이 확인되면 두 회전 상태를 비교한다.

| 출력 | 정의와 검증 |
|---|---|
| Aperture 통과 Power | 각 mirror에서 해당 면에 도달한 incident power 대비 clear patch로 들어가는 power. Backing/Keepout 차폐 및 수치 잔차를 따로 기록하고, 두 mirror의 aperture ratio를 더하지 않는다. Tilted surface에 incident flux projection을 일관되게 적용한다. Scalar reference의 power는 정규화된 scalar 모델의 값으로 표기 |
| Fixed Target Mode Overlap η | 고정 X=2 mm 평면의 동일한 (t,s) Grid와 동일한 면적 가중치로 η=\|⟨E_target,E_out⟩\|²/(\|E_target\|²·\|E_out\|²). 위상 비교에는 공통 Piston 하나만 허용한다. 재중심화, 각도 보정 및 Target 재피팅 없이 원래 complex field를 보존 |
| 전달 및 투영 | 같은 정규화에서 별도로 T=output norm² / launch norm² 및 T·η를 기록할 수 있다. T·η는 이상화한 scalar 모델의 launch 대비 mode projection이다. 실제 코팅·계면·편광 손실과 실물 Total Coupling은 해당 물리 근거가 필요 |
| Finite-beam Clearance | 측정 또는 명시 가정의 광학 차폐 경계와 power interception 기준을 함께 제시한다. Gaussian tail에는 단일 경계가 없으므로 power 기준 없이 실제 Clearance를 mm 값으로 판정하지 않는다. 실물 허용 차폐 손실과 도면이 필요 |

명목 Gaussian η의 목표 여유는 약 `1.10e-5`다. 같은 정의의 η를 0.99와 비교하는
Nominal scalar 검증에 **절대 수치 불확도 U ≤ 5e-6**을 제안한다. 다음 배분은 실제
Solver 결과의 오차를 보기 전에 고정한 목표이며, 단위는 모두 절대 η다.

| 항목 | 배정 | 검증 방법 |
|---|---:|---|
| Transverse Grid / Target 적분 | 1e-6 | 동일 Window에서 pitch를 독립 축소하고 quadrature를 확인 |
| Window / Angular bin | 1e-6 | pitch를 유지해 Window를 확대. Angular support와 bin resolution을 각각 확인 |
| Mirror surface / Aperture edge | 1e-6 | 면 sampling과 edge 표현을 별도로 정련. 손실·power ledger도 함께 대조 |
| 독립 Reference / 잔여 수치 오차 | 2e-6 | 독립 계산과 비교하고 교차 정련·잔여 오차를 평가. 기준법의 불확도를 포함 |

각 변화에 대해 기준과 두 번의 successive refinements를 기록하고, 최종 교차 정련과
독립 대조로 각 상한을 뒷받침해야 한다. 변화량이나 두 방법의 일치만으로 상한을 확정하지 않는다.
`η_est − U ≥ 0.99`일 때만 같은 metric의 목표 통과를 인정한다.
`η_est + U < 0.99`이면 미달이고, 오차가 경계에 걸치거나 상한을 뒷받침할 수 없으면
판정을 보류한다. 이 예산은 고정 Gaussian Ports와 명시한 반사 경계 모델의 **수치** 기준이다.
Port Fit·모델 오차나 실제 제작 변동은 별도의 근거를 요구한다.
