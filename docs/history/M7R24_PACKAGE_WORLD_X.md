# M7-R24 · 사용자 지정 Package World X 경계

Tutorial → Example A → **이 두 Port로 설계** → **Package Envelope** → **World X 직접 입력**을 선택한다. World X min/max를 mm로 입력하고 **Design**을 누른다. X 위치를 좌표로 입력하므로 같은 폭을 다른 X 위치에 놓고 각각 평가할 수 있다. Y/Z, Keepout, Backing, Aperture 및 50 µm AABB Clearance는 기존 R7 Synthetic 가정을 사용한다. Package 범위는 원본 1310 nm Example A의 두 Port에 귀속된다.

두 Preset을 선택하면 표에서 정확한 World X min/max를 복사할 수 있다. 직접 입력 결과의 Snapshot에는 SI 좌표와 입력 출처를 기록한다. Preset과 물리 경계가 같더라도 사용자 입력의 출처가 반영되므로 SHA는 Preset과 다르다. 숫자나 선택 조건을 바꾸면 결과와 Export를 숨긴다.

## 회귀 기준과 결과

R23 Draft [#54](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/54)의 HEAD `b1b652053f1b5c5dbecf13a090e0c22502e922ff`에서 시작했다. [Physics·Browser CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44961978015)와 [Windows CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44961978017)가 통과했다.

| 직접 입력 X min / max [mm] | 통과 / 평가 | 최고 관측 후보 | Normalized Gaussian η |
|---|---:|---|---:|
| −1.15 / 3.15 | 19 / 74 | R8-nominal | 0.9850444681668674 |
| −1.5821774231937228 / 3.4415473764667017 | 48 / 74 | R8-expansion | 0.9900109725310262 |
| −1.36 / 3.37 | 37 / 74 | R8-nominal | 0.9850444681668674 |
| 0 / 2.00 | 0 / 74 | 통과 후보 없음 | Uncomputed |
| 2.00 / 2.00 | 평가 시작 전 입력 오류 | — | — |

정확한 Preset 경계에서는 R23의 통과 수와 최고 후보를 재현하고, 최고 η 및 두 독립 Quadrature를 R9 저장 η와 절대차 1e−8 이내로 대조해야 추천을 표시한다. 그 밖의 유효 경계에서는 해당 최고 후보의 η를 두 독립 Quadrature와 같은 오차 기준으로 검산한다. 기준 또는 독립 검산 불일치 시 검증 보류로 처리한다.

비대칭 중간 폭 4.73 mm에서는 4.30 mm Preset보다 18개 처방이 더 통과했고, 최고 η는 같았다. 최대 투영 Beam 반경은 248.37 µm, 최소 AABB Gap은 M2 X− 경계에서 260.00 µm였다. 통과 후보가 없는 유효 입력은 탈락 근거와 새 SHA를 Export할 수 있다. 잘못된 경계에서는 결과 Export가 표시되지 않는다.

## 재현

```bash
python -m pip install -e '.[test]'
PYTHONPATH=src python scripts/validate.py
node scripts/check_m7d.cjs results/runtime-r24-browser
```

Browser 검사는 Preset과 직접 입력의 결과, 유효한 무후보 입력과 입력 오류, 편집 직후 Export 숨김, 재계산 SHA와 Confidence, 오프라인 HTML과 JSON을 대조한다. 같은 검사를 압축을 푼 Windows Review Package에서 실행한다. 직접 입력은 한 Envelope에서 74개 처방을 평가한다. 실제 Total Coupling, Finite-beam Clearance, Assembly Tolerance 및 탐색 범위 밖의 최소 폭은 Uncomputed다.
