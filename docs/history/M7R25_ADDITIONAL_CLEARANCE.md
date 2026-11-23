# M7-R25 · Normalized Gaussian η 목표와 추가 AABB Clearance

Tutorial → Example A → **이 두 Port로 설계** → **Package Envelope**에서 Preset 또는 World X 직접 입력을 선택하고 **Design**을 누른다. 결과 표에서 최고 관측 η 후보와 η ≥ 0.99를 충족하는 최대 Clearance 후보를 비교한다. 처방 평가 상세에서 통과 처방별 추가 Clearance와 제한 검사를 확인할 수 있다.

추가 Clearance는 Envelope 경계, Reflector AABB 간 거리, Reflector AABB와 Keepout 간 거리의 최솟값에서 기본 50 µm를 뺀 값이다. JSON에는 실제 Gap, 추가 Clearance, Adapter의 원본 `path`·`status`·`reason`을 넣는다. Envelope 경계가 제한하면 해당 면을 함께 기록한다. 통과 처방의 거리 비교에 쓰이는 Adapter 검사는 모두 Pass를 요구한다.

추가 Clearance가 같으면 기존 η 순위를 적용하고, 두 기준이 같은 처방을 선택하면 후보 상세는 한 번만 제공한다. η 목표를 충족하는 최대 Clearance 처방은 독립 ABCD·Quadrature가 원본 η와 절대차 1e−8 이내이며 두 수치 적분값 모두 η ≥ 0.99를 충족해야 추천에 표시한다. 검산 실패는 보류로 표시한다.

## 재현 결과

[Draft #55](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/55)의 HEAD `bd7a23bd93f8791a64bbc2b7bc30007520bfc898`에서 시작했다. #54·#55 기준 HEAD의 Physics·Browser 및 Windows 검사가 통과했다.

| Envelope | 통과 / 평가 | 최고 관측 후보 | Normalized Gaussian η | 최고 η 후보의 추가 Clearance | η ≥ 0.99에서 최대 Clearance |
|---|---:|---|---:|---:|---|
| 4.30 mm | 19 / 74 | R8-nominal | 0.9850444682 | ≈ 0 µm | 목표 충족 후보 없음 |
| 5.023725 mm | 48 / 74 | R8-expansion | 0.9900109725 | ≈ 1 pm | R8-expansion · 유일한 목표 충족 후보 |
| 4.73 mm · X [−1.36, 3.37] mm | 37 / 74 | R8-nominal | 0.9850444682 | 210.000 µm | 목표 충족 후보 없음 |

세 최고 η 후보의 제한 검사는 `body[1].volume`의 M2 X− 면이다. 5.023725 mm Preset의 약 1 pm 여유는 R9의 수치 경계 여유에서 온다. 4.73 mm 입력은 최고 η 후보를 유지하면서 기구 여유가 210 µm 늘어난다. 사용자가 선택한 X 경계와 R7의 Synthetic Y/Z·Keepout·Backing 가정을 사용한다. 실제 Assembly Tolerance, Finite-beam Clearance 및 Total Coupling은 Uncomputed다.

## 검증 명령

```bash
python -m pip install -e '.[test]'
PYTHONPATH=src python scripts/validate.py
node scripts/check_m7d.cjs results/runtime-r25-browser
```

동일 Browser 검사를 압축을 푼 Windows Review Package에서 실행한다. 세 Envelope의 SHA·통과 수·최고 후보를 재현하고 제한 검사를 원본 Adapter와 대조한다. 단위 검사에서는 Reflector 간 거리 또는 Keepout이 제한하는 Fixture와, 별도 Clearance 후보가 검산에 실패하는 경우도 검사한다. Browser에서 후보의 SHA·Confidence, 입력 편집, 기존 Two-Port 취소와 HTML·JSON Export를 검증한다.
