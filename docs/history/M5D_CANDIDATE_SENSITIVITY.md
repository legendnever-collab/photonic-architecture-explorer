# M5-D — Candidate Sensitivity Review

Workspace에서 Design을 실행한 뒤 후보의 Mode Match 아래 **Target 기준면 민감도**를
펼친다. 추천 후보와 대안은 각자의 Nominal 경로, Reflector, Gaussian q를 유지한다.
Target external reference plane의 t = s × d 및 s에 동일한 상대 오차를 적용한다.
Nominal 외 8개 조건은 각각 t/s 방향의 위치 ±5 µm 또는 각도 ±10 mrad다.
매번 한 변수만 바꾼다. 이 숫자는 비교용 진단 조건이다.

상대 위치는 도착 Gaussian 중심의 평면 내 이동으로 적용한다. 상대 각도는
소각도 선형 Phase ramp로 적용한다. 두 조건 모두 기존 Gaussian complex overlap을
호출하고, 전체 Mode Mismatch Loss와 같은 후보의 Nominal 대비 변화량을 dB로
비교한다. 적용 범위를 벗어나면 Uncomputed다. Overlap이 0이면 loss는 ∞이며,
Nominal loss가 ∞인 경우 Δ는 Uncomputed다.

두 Port와 후보 순위는 기존 설계 결과를 따른다. 비교의 모든 조건에서 같은
Target 입력을 사용한다. 정확히 일치하는 nominal 도착 모드를 갖는 후보는
이 Target 기준면 비교에서 같은 민감도를 보일 수 있다.

M2의 부품 배치 진단은 개별 반사면 꼭짓점을 움직여 실제 quadratic patch와의
교차 및 위치·각도 closure를 검사한다. Off-vertex powered Gaussian handoff는
검증되지 않았다. 이번 진단은 부품 이동을 Target 오차로 변환하지 않으며,
실제 부품 배치 공차, Package Yield, Total Coupling은 Uncomputed다.

## 재현

```bash
python -m pip install -e '.[test]'
pae-workspace
# http://127.0.0.1:8765 → Design → Target 기준면 민감도
pae-design examples/m5a_two_ports.json --output-dir results/runtime-m5d-review
python scripts/validate.py
```

HTML과 JSON은 동일한 `candidate_sensitivity` 데이터를 사용한다. 이전 엔진
스키마의 평가·순위 정보와 별도로, 후보 ID, 입력 SHA, Target 기준면, SI 오차 벡터,
Nominal 및 perturbation 손실과 상태를 저장한다.

Base는 [M5-C Draft PR #15](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/15)
(`75566a8b6da0eb442d7c62b702bb7041f0e83360`)다.
[기준 CI 43981303100](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/43981303100)
에 84개 테스트와 Desktop/Mobile·오프라인 Export 증거가 있다. 이 PR의 CI는
M5-A 계산과 M5-C Workspace를 재현하고, flat Gaussian 해석식 및 curved Gaussian
복소장 수치적분과 새 민감도 값을 대조한다. Browser는 desktop/mobile, Fixed
Ports, 후보 순위, HTML/JSON과 화면 값의 일치를 확인한다.
