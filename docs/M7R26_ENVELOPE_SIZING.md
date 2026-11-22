# M7-R26 · 고정 처방의 World X 경계 산출

Tutorial → Example A → **이 두 Port로 설계**에서 Package Envelope를 선택한다. **추가 AABB Clearance 목표 [µm]**를 입력하고 **Design**을 누르면 R8-expansion에 필요한 X 경계와 R9 대비 폭 증가량을 확인할 수 있다. 기존 Envelope 평가와 고정 처방 제안을 같은 보고서에서 확인한다. 제안에는 별도의 처방 SHA를 기록하며 입력을 편집하면 이전 결과와 Export를 숨긴다.

## 산출 방법

기본 50 µm와 목표 추가 여유의 합을 `C`로 둔다. 가장 작은 Backing AABB의 X min에서 `C`를 빼고 가장 큰 X max에 `C`를 더한다. 이 구간과 Source, 두 Reflector Vertex, Target의 X 좌표를 함께 포함한다. World AABB는 볼록하므로 Chief Path 선분 전체가 들어간다. R9의 수치 경계 여유를 재현하도록 X 양쪽을 각각 1 pm 바깥으로 둔다. Port, 처방, Aperture, Y/Z 및 Keepout은 고정한다.

World X로 늘릴 수 없는 여유는 Y/Z 경계, Reflector 간 AABB 거리 및 Keepout 거리에서 결정된다. 요청이 이 상한을 넘으면 상한보다 2 pm 높은 유한한 검증 입력으로 Adapter의 원본 실패 경로를 확인하고 경계 제안을 보류한다. 각 성공 제안에는 Adapter 원본 검사, 독립 ABCD·Quadrature, η, 목표 여유와 실제 계산값을 기록한다. 추가 검색은 기존 74개 처방을 사용하며, 입력한 목표에 대해서만 고정 처방의 Adapter 재평가를 한 번 수행한다.

## 재현 결과

기준은 [Draft #56](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/56)의 HEAD `f85a1360a8804010dffb25c0877a15e3f06363b3`다. #56의 Physics·Browser 및 Windows CI를 확인했다.

| 추가 목표 [µm] | World X min [mm] | World X max [mm] | 필요 폭 [mm] | R9 대비 증가 [mm] |
|---:|---:|---:|---:|---:|
| 0 | −1.582177423194 | 3.441547376467 | 5.023724800 | 0 |
| 50 | −1.632177423194 | 3.491547376467 | 5.123724800 | 0.100 |
| 100 | −1.682177423194 | 3.541547376467 | 5.223724800 | 0.200 |
| 500 | — | — | — | M2 Z+ 한계 · 493.626639 µm |

0 µm는 저장된 R9 X min/max와 로컬에서 수치상 일치했고 경계 허용 오차는 2 pm이다. 세 성공 제안 모두 Adapter와 독립 Quadrature에서 η ≥ 0.99를 통과했다. 로컬 η는 0.9900109725310262였고 독립 Quadrature와 최대 절대차는 3.34e−16 이하였다. 500 µm의 제한 검사는 `body[1].volume`의 M2 Z+ 면이다. 전체 처방 탐색에서 전역 최소 폭, 실제 Assembly Tolerance, Finite-beam Clearance 및 Total Coupling은 Uncomputed다.

## 검증 명령

```bash
python -m pip install -e '.[test]'
PYTHONPATH=src python scripts/validate.py
node scripts/check_m7d.cjs results/runtime-r26-browser
```

Linux와 압축을 푼 Windows Review Package에서 동일 Browser 검사를 실행한다. 0·50·100·500 µm, 처방 SHA, Adapter 상태, 입력 편집, Confidence, HTML·JSON Export 및 기존 취소 흐름을 확인한다.
