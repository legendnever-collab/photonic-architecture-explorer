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

## 재현 결과와 기구 여유

M7-R9 재실행의 JSON은 [동결 결과](../references/m7r9/summary.json)와 일치했다.
확장안 명목 η는 `0.9900109725310262`이며 독립 Quadrature 두 결과와의 최대 차이는
`3.4e-16` 이하다. 이는 Gaussian 계산의 수치 일치다. 명목 Aperture-tail union
추정치 `9.0e-7`은 기존 `1e-6` Guard를 통과한다. 추정치는 평면 투영 Gaussian의
Screening 값이며 두 reflector의 Clipping·Diffraction을 정량화하려면 별도 계산이 필요하다.

| 고정 pose | Target Δt [µm] | Target θt [mrad] | 최소 기구 AABB 경계 간격 [µm] | 제한 위치 · 50 µm 기준 |
|---|---:|---:|---:|---|
| Nominal | 0 | 0 | 50.000001 | M2 X− · Pass |
| M2 −1 mrad | −6.432031 | −2.000000 | 50.000001 | M1 X+ · Pass |
| M2 +1 mrad | +6.432031 | +2.000000 | **49.289713** | **M2 X− · Fail** |

Δs와 θs는 0이다. 두 회전 상태의 Chief Ray는 M2 vertex에 도달한다. 유한 빔의
Off-Vertex 부분은 다른 sag와 법선을 만나므로 이 광선 결과와 Field 판정을 분리한다.
`+1 mrad`의 **0.710287 µm 부족**은 기존 Padded AABB와 고정 Envelope에서 발생했다.
이 Nominal 프록시는 이미 지정한 세 pose 전체에서 기구 기준을 만족하지 못한다.
실제 조립 판단에는 유효 Backing 형상과 Pivot의 확인이 필요하다. 양의 회전 조건은
향후 광학 Reference의 진단 사례로 유지한다.

## 기존 Reference 판정과 다음 검증

| 근거 | 재사용 범위 | 확장안에 부족한 근거 |
|---|---|---|
| M1 Gaussian / 독립 Fresnel·ABCD·Quadrature | Paraxial free propagation, quadratic phase, 고정면 η 양성 대조 | 기울어진 finite curved patch의 입사장·반사장 전달, Aperture-edge 회절 |
| M7-R9 Adapter / M6-D | 기구 AABB, Chief-Ray 교차·법선·Target 위치/각도. Nominal Gaussian tail Guard | Backing·Keepout의 빔 차폐, 편차 시 complex amplitude·phase 및 Target η |
| [M4-C planar control](M4C_EXTERNAL_FIELD_REFERENCE.md) / [별도 M4-C.1 Draft](https://github.com/legendnever-collab/photonic-architecture-explorer/blob/e164f7aa3c255a03f9c54f11af699b49c86c78e6/docs/M4C1_ANGULAR_VERIFICATION.md) | 1310 nm y-invariant TE 평면 계면의 field·flux와 독립 Angular-tail 적분. 고정 Window에서 pitch만 줄이면 bin 오차가 남는다 | 유한 2D transverse beam, 곡면 반사·가림·회전과 m 단위 횡단면의 총 Power. M4-C의 원래 tail Gate는 Fail이었고 M4-C.1의 수렴 개선은 별도 평면 사례에 해당 |
| [M6-E Draft #22](https://github.com/legendnever-collab/photonic-architecture-explorer/blob/e1434e7018b4288e0d952ed7e40d3b3e8c23dc2a/docs/M6E_OFF_VERTEX_REFERENCE_GATE.md) | Off-Vertex 비교의 phase·좌표·power·수렴 계약 | M6-E도 Reference Not Ready 판정이며 확장안에 적용할 새 curved-surface field 결과는 없음 |
| [M7-R5](M7R5_SINGLE_PORT_FIELD.md) / [M7-R6](M7R6_SMF_GLASS_FIXED_PORT.md) | Simulated Port 및 고정 Gaussian 입력의 출처 | 개별 Field Fit η는 Glass 0.990982, SMF 0.995323이며 기준면에서의 Fit 지표다. 링크 η에 대한 오차 상한을 제공하려면 해당 Field를 전파하고 고정 Target 모드에 투영해야 한다 |

**판정 — 독립 curved-surface Wave-Optics Reference 필요.** M7-R11에서는 Gaussian
양성 대조와 알려진 단일 Aperture 대조를 통과하는 독립 경로를 먼저 확보한다.
곡면 Benchmark는 명목 입사각 약 12.49°인 두 유한 Quadratic patch와 이상적인 scalar
반사 경계에서 Nominal 한 건부터 검증한다. 모델·버전·입력 Hash, edge 및
obliquity 처리, 국소 frame/parity·면적 Jacobian, 궤적 대조, 공통 Target plane의
raw complex field 및 power ledger를 제출한다. 기구 AABB를 광학 차폐면으로 대입하려면
별도의 합성 모델로 선언하고, 실물의 Backing·Keepout 차폐 판정에는 실제 광학 경계를
사용한다. 수치·모델 적용 조건을 충족하면 고정 M2 양방향 회전으로 확장한다.

이번 단계의 Wave-Optics 실행은 0건이다. Finite-beam Clearance, Aperture throughput,
교란 후 Mode Overlap 및 실물 Total Coupling은 **Uncomputed**다.

## 재현과 회귀

Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0에서 기존 검증 134개, M1 Benchmark,
M3-A Adapter Gate, M7-R9 회귀를 통과했다.

```bash
PYTHONPATH=src python -m scripts.m7r9_envelope_review --output-dir results/runtime-m7r9
PYTHONPATH=src python -m unittest discover -s tests -p 'test_m7r9_envelope_review.py' -v
PYTHONPATH=src python scripts/validate.py
```

기구 경계 세 조건에도 기존 M7-R7/R9 Package 생성과 M6-D 회전을 사용한다.

```bash
PYTHONPATH=src python - <<'PY'
from photonic_architecture_explorer.external import adapt_external, evaluate_external
from photonic_architecture_explorer.placement import rotate_in_plane
from scripts.m7r7_package import CASE_PATH, INPUT_PATH, apply_envelopes, load, record
from scripts.m7r9_envelope_review import R8_SUMMARY, limiting_boundary, prescription

fixed, case, r8 = map(load, (INPUT_PATH, CASE_PATH, R8_SUMMARY))
for angle_rad in (0.0, -0.001, 0.001):
    proposal = prescription(fixed, case, r8["candidates"]["expansion"])
    model = adapt_external(proposal)
    m2 = rotate_in_plane(model.reflectors[1], model.source.sagittal, angle_rad)
    proposal["design"]["reflectors"][1]["illuminated_normal"] = record(
        list(m2.normal), "1", "M6-D M2 pose"
    )
    apply_envelopes(proposal, case, aperture_scale=None)
    boundary = limiting_boundary(proposal)
    package = evaluate_external(proposal)["package_feasibility"]["envelope_geometry"]
    print(angle_rad, boundary, package["status"])
PY
```
