# M3-C — User-flow review and Integration Readiness

2026-11-10 KST. Base Draft PR #5 at
`e07aa98ba11155dea4a9494e4d938905a42c0625`, tree
`92b3744d8dd55ed0abc8f3e1e9d0de3140b456c4`.

## Recovery / Review 범위

PR #1–#5의 실제 Head/Base/CI를 복구했다. 모두 Open Draft, 미병합이며
각 Base와 다음 PR의 Head가 일치한다. PR #5 exact-HEAD CI 42757429094:
Python 3.11/3.12 59 tests PASS, Chromium Desktop/Mobile PASS.
기존 Artifact 13736705484 / 13736785052 / 13735424044는 metadata상 유효하다.
이전 단계에서 받은 Browser JSON/화면 자료와 현재 CI metadata를 함께 확인했다.
M3-C 시작 시 PR #5를 로컬에서 재실행해 59 tests / 두 Benchmark Gate PASS를 확인했다.

사용자가 새로 제시한 화면 피드백은 없으며 PR #5의 Issue/Review/Inline Comment도
비어 있었다. 따라서 이번 판단은 **Engineering 사용 흐름에 대한 개발자 Review**다.
사용자의 실제 Review·승인을 대체하지 않는다.

검토 흐름: 정상 Synthetic Relay → Projection 전환 → 실패 Case → 원인 확인 →
해당 JSON 입력 수정 → Adapter 재평가 → Fixed Ports/결과 상태 확인.

## 수정은 한 가지: 입력 진단에서 누락된 Field Path

Bad Unit Case에서 Adapter는 `path=source.position_m`을 반환하지만 사람용
`판정 근거 / 미계산 항목` 목록은 `input_contract: unsupported unit ...`만 표시했다.
Raw Result JSON에는 경로가 남아 있으나, 진단 목록만으로는 수정할 Field를 알 수 없었다.

기존 목록에 Adapter의 `path`를 HTML-escaped `<code>`로 함께 표시한다.
예: `input_contract · source.position_m: unsupported unit ...`.
Blank의 `wavelength_m`, Missing Phase의 `source`, JSON 문법 오류의 `JSON editor`도
같은 규칙을 사용한다. Adapter가 제공하지 않은 경로를 추정하거나 추가하지 않는다.
자동 입력 수정, 새 계산, 입력/상태 계약 변경, 다른 UI 개선은 하지 않았다.

## 검증

추가 Regression Test는 수정 전 실패를 재현하고 수정 후 통과했다. Human reason
목록에서 실제 경로가 보이는지, Fail/Uncomputed 때 Overlap이 보류되는지, Result가
수정되지 않는지, 경로 문자열의 HTML Escaping을 검증한다. 최종 Python Test 60개.
기존 59개 Test와 M1/M3-A Gate를 함께 재실행한다.

Chromium CI는 기존 Desktop 1440×1050 / Mobile 393×852 / Static HTML 검증에
진단 경로 확인을 추가한다. Bad Unit → `source.position_m` 확인 → Unit만 `m`으로
명시 수정 → Python 재평가 → 동일 Fixed Ports와 Approximate Overlap 1 복구를 검증한다.
Mobile과 독립 Static HTML에서도 경로 표시를 확인하고 진단 Screenshot을 남긴다.
실제 실행 결과는 M3-C PR의 정확한 HEAD CI와 Artifacts를 따른다.

Physics / external Adapter / 기존 Physics Tests / Fixtures / Guards와 기존 Benchmark
JSON은 PR #5와 동일하다. Actual Applicability / Total Coupling / Full Finite-Beam
Clearance는 Uncomputed이며 Nominal Overlap 1은 Approximate Scalar 진단이다.

## 실행 / 사용자 확인

```bash
python -m pip install -e '.[test]'
python -m photonic_architecture_explorer.inspector
python -m photonic_architecture_explorer.inspector --serve
# Static: results/m3b-inspector.html
# Editable: http://127.0.0.1:8765
```

Static HTML에서 `잘못된 단위`를 선택하고 `판정 근거 / 미계산 항목`을 연다.
`source.position_m`이 표시되는지 확인한다. 입력 수정은 Local Inspector에서 한다.
실행·물리 경계의 전체 설명은 M3B_INSPECTOR.md를 따른다.

Integration 의존 순서·충돌·필수 Gate: M3C_INTEGRATION_READINESS.md.
다음 제안: NEXT_TASK.md. 이번에는 Main을 병합하거나 다음 개발을 시작하지 않는다.
