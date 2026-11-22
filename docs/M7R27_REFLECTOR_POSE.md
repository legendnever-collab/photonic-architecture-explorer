# M7-R27 · Reflector 오차에서 η ≥ 0.99가 유지되는가?

**명목 Gaussian η는 0.9900109725310262로 재현됐다. 12개 단일 오차에서 목표 유지 여부는 모두 Evidence Insufficient다.** 두 유한 Quadratic Patch를 반사한 Chief Ray는 모든 경우에 고정 Target Plane에 도달했다. 가장 큰 Target 오차는 M2 sagittal 회전 양방향에서 나타났다. 이때 두 반사 모두 Vertex에 입사하지만 출사각과 Target의 도착축이 달라진다.

기준은 열린 [R26 Draft #57](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/57)의 `109ffb42d726aa984646cdf89022106ceb319080`이며 Physics·Browser 44968264860, Windows 44968264872가 성공했다. R8-expansion의 1310 nm SMF·Glass 외부 Gaussian Fit, 두 고정 Port, 회전 Pivot, Curvature, Aperture와 R9 Envelope를 계승했다. [조건별 SI 값과 검증 결과](../references/m7r27/summary.json)

## 어느 방향의 오차가 큰가?

각 셀은 부호 있는 Target Δt [µm] / θt [mrad]이다. t는 World −Z, s는 +Y이다. 회전은 해당 Vertex를 지나는 +Y 축에 대한 오른손 회전이며 Δs·θs는 모두 0이다.

| 오차 | 음의 방향 | 양의 방향 |
|---|---:|---:|
| M1 X ±5 µm | −0.0454 / −0.6705 | +0.0449 / +0.6704 |
| M1 Z ±5 µm | +4.9454 / −0.6510 | −4.9466 / +0.6506 |
| M1 s ±1 mrad | +6.2291 / −1.0079 | −6.2300 / +1.0096 |
| M2 X ±5 µm | +0.0482 / +0.6704 | −0.0420 / −0.6705 |
| M2 Z ±5 µm | +5.0958 / +1.4394 | −5.0980 / −1.4396 |
| M2 s ±1 mrad | −6.4320 / −2.0000 | +6.4320 / +2.0000 |

M2 양방향 회전의 중심 이동은 고정 Target의 tangential 1/e Field radius 4.6292 µm의 1.3895배다. 이동 오차만 비교하면 M2 +Z가 위치와 각도 모두 가장 크다. M1 회전에서는 M2 입사점이 Vertex에서 최대 9.7060 µm 벗어난다. 이 값들은 정렬 민감도를 보여준다. 어느 방향에서 η가 가장 낮은지는 미확정이다. R10의 M2 +1 mrad 기구 검사에서는 기존 Envelope의 50 µm AABB Clearance도 0.7103 µm 부족했다. [R10 기구 근거](M7R10_FINITE_BEAM_SCOPE.md)

## 검증한 경로와 중단 근거

1. 원본 Adapter의 명목 η를 독립 ABCD와 두 Complex Quadrature로 재검산했다. 12개 오차의 부호 있는 위치와 각도를 [R9](M7R9_ENVELOPE_ASSEMBLY_REVIEW.md)와 대조하고, 별도 Newton 교차·반사 계산으로 위치 1e−13 m, 각도 1e−11 rad 이내에서 확인했다.
2. 각 오차의 실제 곡면 교차점 주위에서 주변 광선을 추적해 **고정 Target Plane**의 tangential Ray Transfer Matrix를 Central Difference로 계산했다. 입력·출력은 각 면의 (t, 방향벡터의 t 성분)이다. 높이 1 / 0.5 / 0.25 µm, 방향 성분 0.001 / 0.0005 / 0.00025를 독립적으로 줄였다. 길이 단위 1 mm로 무차원화했을 때 연속 Matrix 성분 최대 변화는 1.05e−7 → 2.61e−8이었다. 마지막 단계의 최대 |det M − 1|은 2.13e−9 미만이며 독립 Newton 유한차분과 대조했다. 이 수렴은 국소 광선 전달에 적용된다. Beam 전체의 Amplitude·Phase와 η 수치 오차에는 별도의 근거가 필요하다.
3. 원본 Gaussian Solver에 각 오차 처방을 다시 입력했다. M1 Z 이동은 Source→M1 Vertex 조건, M2 Z 이동은 Target 도착축 조건, 다른 8개는 Vertex 간 정반사 경로 조건에서 멈췄다. 명목 q를 이동된 Chief Ray에 얹어 η를 산출하면 이 검사와 Off-vertex Field 검증이 빠진다.
4. 별도 Physical Optics 경로는 [R12 저장 복소장](M7R12_CURVED_QUADRATURE.md)의 SHA를 대조한 뒤 같은 고정면과 수용 Mode로 재적분했다. 다음 표는 **명목** 유한 Window의 진단값이다.

| Half-window [µm] | η · pitch 2 µm | η · pitch 0.5 µm |
|---:|---:|---:|
| 24 | 0.989811091935 | 0.989811098632 |
| 48 | 0.989810942641 | 0.989810941839 |
| 96 | 0.989810854184 | — |
| 192 | 0.989810812816 | — |

192 µm Window 결과와 명목 Gaussian η의 차이는 약 2.00e−4다. 두 모델과 적분 범위가 달라 이 차이를 Gaussian 계산의 Numerical Error로 사용할 수 없다. 좁은 pitch나 큰 Window에서의 변화량만으로는 도착장 전체면 Norm의 오차를 제한할 수 없다. [R13 분석](M7R13_TARGET_ACCEPTANCE.md)

12개 오차의 Complex Field에 대해 검증된 Off-vertex 반사·고정면 재투영과 절대 η 불확도 U ≤ 2e−6이 확보되지 않았다. 따라서 각 행에서 η와 U는 null이며, η ≥ 0.99는 판정 보류다. 실제 Assembly Tolerance, Finite-beam Clearance 및 Total Coupling은 Uncomputed다. 기존 74개 처방 검색과 사용자 입력의 Runtime 판정은 원래 경로를 사용한다.

## 재현

```bash
python -m pip install -e '.[test]'
python -m scripts.m7r27_pose_gate --output results/runtime-m7r27/summary.json
python scripts/validate.py
```

Linux Browser와 압축 해제한 Windows Review Package에서 기존 Two-Port 입력 편집, 74개 처방 검색, 취소·SHA 및 HTML/JSON Export 검사를 실행한다.
