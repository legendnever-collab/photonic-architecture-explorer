# M7-R8 — G029-NM 주변 Package 탐색

**M7-R7의 Package 안에서 η ≥ 0.99를 만족한 처방은 없었다.** 가장 높은 Package 통과값은 η = 0.985044였다. 같은 Guard 여유와 Aperture 조건으로 η ≥ 0.99를 만족한 관측 처방 중 가장 작게 Envelope를 확장하는 처방은, X 양쪽 경계를 각각 0.432 mm, 0.292 mm 옮긴 경우였다. 이 처방은 확장 Envelope에서 Adapter와 독립 ABCD·Quadrature를 통과했다.

## 동결 조건과 탐색 예산

두 1310 nm Port와 Gaussian Mode, 4.30 × 2.70 × 4.70 mm Nominal Envelope, Keepout, 두 축의 2.20 mm Full aperture cap, 50 µm AABB Clearance를 M7-R7에서 가져왔다. 최대 Footprint–Curvature 0.135, 반사 직후 Divergence 0.095 rad, η ≥ 0.99와 기존 Model Guard를 모두 적용했다. Aperture는 M7-R7의 Equal-tail (2.58870w) 배정을 사용한다. 실제 제품 치수, Finite-beam Clearance 및 제조 공차는 Uncomputed다.

`a`는 Source에서 M1, `c`는 M2에서 Target까지의 Chief-ray 거리다. 두 축 모두 G029-NM의 2.828427 mm를 중심으로 **2.428427–3.228427 mm**를 탐색했다.

| 단계 | 평가한 처방 |
|---|---:|
| 25 µm 간격의 33 × 33 배치, 배치마다 Exact-q 4개 | 4,356 |
| 동일 배치의 Guard 제한 시작점 | 4,356 |
| a/c와 네 개의 곡률 변수를 함께 탐색, 광학 및 Package 목적 2회 | 20,608 |
| 처방 합계 / Adapter 호출 | 29,320 / 46,576 |

연속 탐색은 기록한 고정 Seed와 계산 예산을 사용한다. Package 목적에는 Envelope 초과량 및 기타 Package 실패에 대한 페널티를 적용했다. 실제 Pass 판정은 기존 Adapter의 Geometry·Model·Package 및 두 Guard 여유 조건을 모두 사용한다. Package 제약이 실패한 처방의 η는 동일 반사면과 Aperture에 대해 Envelope 없이 재평가한 광학 진단에 해당한다. 확장 치수는 해당 처방의 거울 외접 AABB와 50 µm Clearance로 산정하고, Envelope만 확장한 입력에서 Adapter로 재검사했다.

[사전 탐색 계획과 예산](../../references/m7r8/search_plan.json) · [고정 Package 조건](M7R7_PACKAGE_AND_MARGIN.md)

## 결과

| 관측 처방 | a / c (mm) | η | 광경로 (mm) | 최대 Footprint–Curvature | 반사 직후 Divergence (rad) |
|---|---:|---:|---:|---:|---:|
| 고정 Package 최고 | 2.52549 / 2.76835 | 0.98504447 | 9.147 | 0.135000 | 0.08623 |
| Package 제외 최고 | 3.09293 / 3.22843 | 0.99010216 | 11.083 | 0.135000 | 0.08800 |
| η ≥ 0.99에서 가장 작은 관측 확장 | 3.07795 / 3.21601 | 0.99001097 | 11.031 | 0.135000 | 0.08795 |

원래 Envelope의 Package·Guard 여유 조건을 통과한 처방은 6,942개였고, 모두 η 목표보다 낮았다. 고정 Package의 최고 처방은 Boundary Clearance 50 µm와 Footprint–Curvature 0.135 경계에 닿았다. Package 실패에서 가장 자주 걸린 검사는 M2 Backing 포함 Envelope 17,755회와 M1 Backing 포함 Envelope 14,952회였다. 한 처방이 두 검사에 동시에 걸릴 수 있다. 원래 Model Guard 실패에서 가장 빈번한 사유는 Exact-q 시작점의 Footprint–Curvature 0.15 초과였다.

관측한 확장 처방의 필요 공간은 World **X− 0.432177 mm, X+ 0.291547 mm**다. X 범위는 약 **−1.582177…3.441547 mm**, 전체 X 폭은 **5.023725 mm**다. Y/Z, Keepout, Aperture 및 50 µm Clearance 조건을 적용한 채 확장 Envelope의 모든 Adapter 검사를 통과했다. 독립 Quadrature는 η = 0.9900109725310264와 0.9900109725310265를 반환했다. 이 치수는 재현한 한 처방의 요구량이며, 더 넓은 a/c 범위 또는 다른 후보에 대한 최솟값은 Uncomputed다. Total Coupling과 공차 적합성도 Uncomputed다.

[처방·검산·실패 집계](../../references/m7r8/summary.json)

## 재현

```bash
python -m pip install -e '.[test]'
python -m scripts.m7r8_local_search --output-dir results/runtime-m7r8
PYTHONPATH=src python scripts/validate.py
python scripts/validate_m7c.py --output-dir results/runtime-m7c-r8-review
```

1550 nm Proxy 회귀에서 G036-NM, η = 0.9999366495865395를 재현했다.
