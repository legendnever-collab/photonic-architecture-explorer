# M7-R22 · 1310 nm Reference에서 입력을 바꿔 재설계

## 기준과 사용법

열린 Draft [#52](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/52)의 최종 HEAD `d0cd44ae677f3b6c070be04c9e56808827b5a017`에서 시작했다. Main은 `f7970886f42e0915ac8c96a6564bc4ac79b5597a`였다. [R21 Physics·Browser CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44895634761)와 [Windows CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44895634777)가 통과했다.

1. **Tutorial / How It Works → Example A → 이 두 Port로 설계**를 선택한다. 1310 nm의 Source·Target를 채운 Workspace가 열린다. **Design**을 누르면 기존 Exact-q 검사와 Guarded Near-Match Worker가 실행된다.
2. 원본 결과를 확인한 뒤 **입력 편집**에서 Target Position의 Z를 2.000 mm에서 2.100 mm로 바꾼다. 이전 결과와 Export가 숨겨진다. **Design**을 다시 실행하면 새 Input SHA와 후보가 표시된다.
3. **Engineering Confidence**와 **HTML / JSON 저장**에서 해당 결과의 SHA와 후보 ID를 확인한다. 결과의 R6 안내에는 바뀐 입력 항목과 원본 SHA가 함께 표시된다.

원본 폼은 R6의 MFD와 Wavefront Curvature를 반올림 없이 SI로 왕복해 동일한 q와 SHA를 재현한다. 단일 위치 편집은 Target의 Reference Plane 원점을 같이 이동시킨다. 이동한 Port는 기존 MFD·Phase 수치와 출처를 보존하면서 그 값을 새 배치에 적용한 Gaussian 가정으로 표시한다. 위치, 방향, 축, Mode 또는 공통 전파 조건을 수정했을 때 R6의 Overlap과 순위는 원본 SHA에 귀속된다.

## 결과를 공개하는 조건

원본에서 R6 Input SHA, Exact-q 배치 수·처방 수·유효 수가 일치해야 Worker를 시작한다. 원본 Worker 결과는 G036-NM과 저장 Overlap을 재현하고 독립 Quadrature가 η 절대차 1e−8 이내일 때 표시한다. 편집한 입력은 새 SHA로 계산한다. Worker의 Job ID, Revision, SHA 검사와 취소·시간 제한을 사용한다. Phase가 누락되면 Worker 실행 전에 Uncomputed를 표시한다. Edited 결과에서 Guard를 통과한 후보가 없으면 유한 탐색의 NoCandidate로 표시한다.

## 실행 결과

로컬 Workspace에서 실제 Worker를 실행했다. 원본과 편집 입력 모두 추천 처방을 별도 Adapter 호출로 평가했을 때 공개 Evaluation과 일치했다.

| Target Z | 원본 2.000 mm | 편집 2.100 mm |
|---|---:|---:|
| 추천 Candidate | G036-NM | G049-NM |
| Exact-q 배치 / 처방 / 유효 | 36 / 144 / 0 | 49 / 196 / 0 |
| Near-Match Adapter 호출 | 127,968 | 185,920 |
| Normalized Gaussian Overlap η | 0.9990889546173051 | 0.9990895739728913 |
| 독립 Quadrature와 최대 η 절대차 | 5.55e−16 | 8.88e−16 |
| 광로 | 20.839734 mm | 21.427004 mm |
| 로컬 Worker 실행 시간 | 83.1 s | 122.8 s |

원본 Input SHA는 `20461fd9868b9450c0df7eff0464e6454a06811e5f09c244f4bc579d66efbcad`다. 편집 Input SHA는 `a8301361c0938af20da3c10087781546fce2bea7ff4bf1f1de51c4b0ff5c0c84`다. 원본 R6 저장 Overlap과 차이는 0이다. 회귀 154개와 Benchmark, M3-A Adapter가 통과했다.

## 검증 재현

```bash
python -m pip install -e '.[test]'
PYTHONPATH=src python scripts/validate.py
node scripts/check_m7d.cjs results/runtime-m7d-r22
```

Playwright 검사는 1310 nm 원본·Target Z 편집·취소·늦게 도착한 응답·누락 Phase를 포함한다. 두 Worker 결과의 추천 처방을 별도 Adapter 호출로 재평가하고 모델 입력과 결과, 독립 Quadrature를 대조한다. 편집 결과의 HTML·JSON에서 현재 Candidate ID와 SHA를 확인한다. `acceptance.json`의 `r6_redesign`에 Case별 수치가 기록된다. 같은 Browser 검사를 압축 해제한 Windows 패키지에서 실행한다. 이 검사는 기존 1550 nm Proxy, Synthetic, A4 Print 및 Reference 입력 준비 흐름을 포함한다.

실제 Total Coupling, 명목 Guided Power 비율과 U, M2 회전 광학 응답, Assembly Tolerance는 Uncomputed다. 원본 R6과 편집 예제에서 Package 크기나 조립성을 판정하려면 해당 입력과 별도 검사가 필요하다.
