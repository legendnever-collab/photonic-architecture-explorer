# M7-R7 — 1310 nm Nominal Package와 Guard 여유

**선언한 Nominal Envelope와 Guard 여유에서 η ≥ 0.99에 도달한 후보는 없었다.** 같은 SMF–Glass Fixed-Port 조건에서 G036-NM과 G029-NM의 광학 결과를 재현했다. 둘 다 가정한 Nominal Envelope에서 탈락했다. G036-NM은 Reflector 위치와 Aperture가 한계를 넘고, G029-NM은 Aperture 한계를 통과하지만 두 Backing 포함 Envelope가 X 방향 경계 Clearance를 만족하지 못한다.

## 평가 전에 고정한 입력

| 항목 | Nominal 조건 |
|---|---|
| Port | M7-R6의 SMF–Glass, 1310 nm, Air, Source (0,0,0) mm와 Target (2,0,2) mm, 두 전파 방향 +X, 보존한 외부 Gaussian Mode |
| Available volume | World X −1.15…3.15, Y −1.35…1.35, Z −1.35…3.35 mm. 크기 4.30 × 2.70 × 4.70 mm |
| Keepout | SMF 뒤와 Glass 뒤에 각각 하나의 Package proxy AABB |
| Aperture | 두 축의 Full clear aperture 각각 최대 2.20 mm |
| Body와 Clearance | Local Quadratic Patch의 World AABB. 반사 Normal 반대쪽으로 Backing 0.15 mm를 추가하고 모든 면에 0.05 mm를 덧댄다. Boundary, 몸체 간 및 Keepout에 요구하는 AABB Clearance는 0.05 mm |
| 추가 설계 목표 | 정규화 Gaussian η ≥ 0.99, 최대 Footprint–Curvature ≤ 0.135, 두 반사 직후 Divergence ≤ 0.095 rad |
| 기존 Guard | Footprint–Curvature 0.15, 전 Segment와 양 Port Divergence 0.1 rad, 총 Gaussian-tail upper bound 1e−6 등 기존 Solver 판정을 적용 |

Package 치수와 Support/Keepout은 설계 비교를 위한 명시적 가정이다. 고객 치수나 CAD는 미제공이다. 추가 Divergence 목표는 반사 처방으로 조정할 수 있는 두 반사 직후에 적용한다. Fixed Glass Mode는 0.099701 rad이며 기존 Guard까지 0.299 mrad 여유가 있다.

[고정 입력과 근거](../../references/m7r7/case.json) · [두 Port의 복소장과 Adapter 입력](M7R6_SMF_GLASS_FIXED_PORT.md)

## R6 처방 재현과 배치 민감도

| 후보 | Nominal η | 광경로 | Full Aperture 최댓값 | X 방향 Clearance 부족 | 기존 0.15 한계까지 곡률 여유 |
|---|---:|---:|---:|---:|---:|
| G036-NM | 0.999089 | 20.840 mm | 4.327 mm | 2.821 mm | 7.18 × 10⁻⁸ |
| G029-NM | 0.998060 | 9.825 mm | 2.124 mm | 92.8 µm | 1.78 × 10⁻⁸ |

X 방향 수치는 가장 부족한 쪽에 요구된 50 µm Clearance를 포함한다. G029-NM은 Package에 독립적인 광학 평가에서 R6 값을 재현했고, Package를 입력한 평가에서는 Adapter가 Overlap을 보류했다.

M6-D와 동일하게 한 번에 한 Reflector를 ±5 µm 평행 이동하거나 Sagittal 축 주위로 ±1 mrad 회전했다. 각 후보의 12개 평행 이동 및 4개 회전에서 Chief Ray가 두 유한 반사면을 거쳐 Target Plane에 도달했다.

| 후보 | 평행 이동 최대 위치 / 각도 오차 | 회전 최대 위치 / 각도 오차 |
|---|---:|---:|
| G036-NM | 5.20 µm / 0.919 mrad | 11.31 µm / 2.000 mrad |
| G029-NM | 5.16 µm / 1.825 mrad | 5.66 µm / 2.000 mrad |

Maxima는 서로 다른 Perturbation에서 나올 수 있다. 민감도 수치는 성공한 Chief Ray의 상대 오프셋과 각도다. Perturbed Mode Overlap, 조립 허용 오차, 전체 Finite-beam Clearance는 Uncomputed다.

## Package 제약을 적용한 Near-Match

R6의 36개 Geometry, 후보 생성 방식, 기존 Guard, 평가 예산 및 Ranking을 사용했다. 각 후보의 Patch 전체와 Backing을 감싸는 World AABB를 Adapter에 전달했다. 일반 Aperture 배정은 각 축 4w를 1.10 mm Half-aperture cap까지 사용한다. 보조 배정은 각 축에 총 Tail Guard의 0.9/4를 배분해 Half-aperture `2.58870w`를 사용하고 동일 cap을 적용한다. 실제 Tail은 변경된 Aperture로 기존 Solver에서 다시 검사한다. Guard 여유를 적용한 탐색에서는 기존 4차원 Curvature 탐색 상자만 0.90배로 제한하고, Adapter 판정 후 반사 직후 Divergence 목표도 검사한다.

| 조건 | Adapter 평가 | 유효 Geometry | 기존 Ranking 최고 관측값 | 광경로 |
|---|---:|---:|---|---:|
| 4w · Package | 48,000 | 12 | G010-NM, η = 0.439585 | 4.125 mm |
| 4w · Package 및 Guard 여유 | 48,000 | 12 | G010-NM, η = 0.155791 | 4.125 mm |
| 2.58870w · Package 및 Guard 여유 | 51,808 | 13 | G005-NM, η = 0.334948 | 5.505 mm |

양쪽 R6 고효율 처방은 Package 경계에서 탈락했고, Package를 통과한 짧은 경로의 Overlap은 목표에 못 미쳤다. 4w 비교에서 Footprint–Curvature 목표를 0.135로 적용하자 최고 η가 0.439585에서 0.155791로 하락했다. 축소 Aperture는 유효 Geometry를 하나 늘렸으며, G005-NM의 최대 곡률 지표는 0.1349999994, Post-mirror Divergence는 0.04133 rad였다. 이 후보는 최소 Boundary gap이 50 µm에 가까워, 더 큰 Clearance 여유보다 높은 η를 찾는 단계에서 재검토가 필요하다.

전체 보조 배정 탐색의 첫 탈락 사유는 기존 Divergence Guard 초과가 8,993회로 가장 많았다. Package 및 Keepout 점검은 첫 탈락 사유와 별도로 기록했다. 보조 배정에서 가장 자주 실패한 Package 검사는 M2의 경계 Clearance 2,272회, M2와 Glass 쪽 Keepout의 Clearance 2,039회였다. 한 평가가 여러 Package 검사에서 실패할 수 있다. 이 결과는 주어진 36개 Geometry와 유한한 Near-Match 탐색 범위에서의 판정이다.

G029-NM의 두 Mirror 위치와 Curvature를 그대로 두고 Aperture 평면의 Full width 최댓값을 1.374 mm로 줄이면, Gaussian-tail upper bound는 9.0 × 10⁻⁷이다. Backing 포함 Envelope는 여전히 X 경계 밖으로 약 4.1 µm 돌출하며, 요구 Clearance까지 약 54.1 µm가 부족하다. Aperture 축소로 보완할 수 있는 범위를 수치화했고, 이 처방의 곡률 여유 목표도 충족되지 않았다.

[동일 Tail 배분 입력](../../references/m7r7/aperture_diagnostic.json) · [검증 결과](../../references/m7r7/summary.json)

## 재현

```bash
python -m pip install -e '.[test]'
python -m scripts.m7r7_package --output-dir results/runtime-m7r7
python -m scripts.m7r6_fixed_port --output-dir results/runtime-m7r6-replay
python -m unittest discover -s tests -q
python scripts/validate_m7c.py --output-dir results/runtime-m7c-r7-review
```

Review는 baseline, summary, 세 탐색의 Ledger를 기록한다. Ledger에는 각 고정 Geometry의 평가 수, 최다 Overlap 처방, 탈락 원인과 검산한 처방의 Adapter 결과가 있다. M7-R6 두 처방은 NumPy ABCD와 복소 Quadrature로 다시 확인했다. 1550 nm Proxy 회귀에서 선택 ID G036-NM과 η=0.9999366495865395를 재현했다.
