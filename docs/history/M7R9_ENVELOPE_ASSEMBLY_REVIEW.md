# M7-R9 — 1310 nm Envelope와 조립 여유 비교

**η ≥ 0.99가 필요한 경우, 비교한 두 처방 중 5.023725 mm 확장안만 명목상 통과한다.**
확장안의 η 여유는 0.00001097이다. 두 처방 모두 M2의 X− 경계에서 50 µm AABB Clearance를
거의 다 사용하고, 요청한 Footprint–Curvature 한계 0.135에 닿는다. 고객 치수와 조립 공차 자료는
미제공이다. 아래 값은 M7-R7의 비기밀 Nominal 가정과 M7-R8의 관측 처방을 사용한 검토다.

## 명목 Package 및 광학 여유

| 항목 | 4.30 mm 고정 Envelope | 5.023725 mm 확장 Envelope |
|---|---:|---:|
| 정규화 Gaussian Overlap η | 0.985044468 | 0.990010973 |
| η = 0.99 대비 여유 | −0.004955532 | **+0.000010973** |
| 광경로 | 9.147 mm | 11.031 mm |
| 최소 기구 AABB Clearance | 50.000 µm | 50.000 µm |
| 최소 50 µm를 넘는 Clearance 여유 | 0.000 µm | 0.000 µm |
| 제한 위치 | M2 Backing · X− 경계 | M2 Backing · X− 경계 |
| 최대 Footprint–Curvature | 0.1349999999865 | 0.1349999999865 |
| Footprint–Curvature 0.135 목표까지 여유 | 약 1.35 × 10⁻¹¹ | 약 1.35 × 10⁻¹¹ |
| 기본 Model Guard 0.15까지 여유 | 0.015 | 0.015 |
| 반사 직후 Divergence 최대 / 0.095 rad 목표까지 여유 | 0.08623 / 0.00877 rad | 0.08795 / 0.00705 rad |

최소 기구 AABB Clearance는 Backing을 포함한 반사면 몸체와 Envelope 경계,
반사경 몸체 쌍, 몸체와 Keepout 사이의 기존 검사값 중 최솟값이다. 확장안에는 M7-R8 재검사의
수치 비교용 약 1 pm 여유가 포함됐다. 두 η 값은 같은 1310 nm Fixed Port와 동결 처방에서
기존 Adapter 및 독립 ABCD·Quadrature로 재현했다.

[Nominal Package 입력](../../references/m7r7/case.json) · [동결 처방](../../references/m7r8/summary.json)

## M6-D Chief-Ray 배치 민감도

한 번에 반사면 하나에 World X/Y/Z 축별 ±5 µm 이동 또는 공통 sagittal 축 주위 ±1 mrad 회전을
적용했다. 처방마다 16개 조건이 모두 고정 Target Plane에 도달했다. 아래 각 셀은
성공한 Ray의 최대 위치 오차 / 최대 각도 오차이며, 두 최댓값은 서로 다른 조건에서 발생할 수 있다.
부호 있는 Target t/s 위치·각도는 결과 JSON에 기록했다. 32개 교란 모두 독립 Newton 교차 계산과
일치했다.

| 교란 | 4.30 mm 고정 Envelope | 5.023725 mm 확장 Envelope |
|---|---:|---:|
| M1 이동 | 5.141 µm / 0.977 mrad | 5.067 µm / 0.783 mrad |
| M2 이동 | 5.180 µm / 1.852 mrad | 5.098 µm / 1.572 mrad |
| M1 회전 | 5.216 µm / 0.901 mrad | 6.230 µm / 1.010 mrad |
| M2 회전 | 5.537 µm / 2.000 mrad | 6.432 µm / 2.000 mrad |

확장안은 이 교란 범위에서 이동에 대한 최대 각도 오차가 작고 회전에 대한 최대 위치 오차가 크다.
이 값은 Chief-Ray 민감도를 비교한다. 실물 조립 상태에서 η ≥ 0.99가 유지되는지는 Uncomputed다.
Finite-beam Clearance, Perturbed Mode Overlap, 실제 조립 공차, Total Coupling도 Uncomputed다.

[배치 민감도 계약](M6D_REFLECTOR_PLACEMENT.md) · [조건별 부호 있는 결과](../../references/m7r9/summary.json)

## 실물 조립 판단에 필요한 입력

| 입력 | 판단에 필요한 내용 |
|---|---|
| Package 및 Keepout | World 좌표계에서 X±/Y±/Z± 형상과 제조 하한, Reflector Backing·지지대·접착층 형상, 간섭물과 조립 접근 여유 |
| 반사면과 조립 공차 | 유효 Aperture 및 곡률·형상 공차, M1/M2의 이동·회전 및 회전 중심, 기준면과 공차 결합 규칙 |
| Port와 합격 기준 | 실제 1310 nm Port 기준면의 위치·방향·Mode, η 평가 방식과 허용 손실, 필요한 경우 코팅·계면 사양 |

이 자료가 확보되면 실제 Beam의 Aperture·지지대 간섭과 이동·회전 상태의 필드 전파를 검증하고,
고정 Target Plane에서 Mode Overlap과 Total Coupling의 근거를 각각 확보한다.

## 재현

```bash
PYTHONPATH=src python -m scripts.m7r9_envelope_review --output-dir results/runtime-m7r9
PYTHONPATH=src python -m unittest discover -s tests -p 'test_m7r9_envelope_review.py' -v
PYTHONPATH=src python scripts/validate.py
```
