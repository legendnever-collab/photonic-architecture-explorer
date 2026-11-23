# M3-C — Draft Stack Integration Readiness

2026-11-10 KST. 이 문서는 **통합 준비 판정**이며 Main 병합 승인이 아니다.
복구한 원격 Snapshot과 read-only `git merge-tree` 결과: results/m3c_stack.json.

## 현재 고정 Stack / 권장 순서

| 순서 | PR / 내용 | Head | Base | Exact-HEAD CI |
|---|---|---|---|---|
| 1 | #1 M1 Physics | 55de4c5f26d3bacc9e22ec64ba385de8acfc4dbe | Main fe730295672047878274d9013edc255b88d16ce2 | 42620976531 Success |
| 2 | #2 M2 Diagnostics | 074930aab1b941d58c428b0644c1553dd23e9271 | PR #1 | 42623160229 Success |
| 3 | #3 M2.5 Applicability | 17bd1ad6bfa5715f6371fe0e41f52a6d1a93e199 | PR #2 | 42702995771 Success |
| 4 | #4 M3-A Adapter | 61bafc61d50b0c934e9fa17c4220bb44dbaf5b96 | PR #3 | 42705770777 Success |
| 5 | #5 M3-B Inspector | e07aa98ba11155dea4a9494e4d938905a42c0625 | PR #4 | 42757429094 Success |
| 6 | M3-C Input-path Review | 이 PR의 Metadata 참조 | PR #5 | 이 PR의 Checks 참조 |

전체는 Main → #1 → #2 → #3 → #4 → #5 → M3-C의 누적 의존 관계다.
각 PR을 Main에 독립적으로 적용하는 Stack이 아니다. 모든 PR은 Draft·미병합이다.
M3-C의 최종 SHA/CI/Artifacts는 채팅과 PR Description에 정확하게 기록한다.

## 충돌 판정 / 한계

PR #1–#5 각각의 Base가 Head의 Ancestor임을 확인했다. 각 쌍의
`git merge-tree --write-tree BASE HEAD` exit code는 0이며 출력 Tree는 해당 Head Tree와
동일하다. Main→PR #5 전체 누적 변경도 exit 0 / PR #5와 동일한 Tree다.
현재 고정 Snapshot을 이 의존 순서대로 통합할 때 Text Conflict는 발견되지 않았다.
이 명령은 Git Object만 계산하며 Main/PR Ref 변경이나 Merge Commit 생성은 하지 않는다.

여러 PR에서 겹치는 경로가 있다: workflow, README, docs/NEXT_TASK.md,
scripts/validate.py, results/validation.json, results/unittest.txt, pyproject.toml,
docs/EXTERNAL_PORT_CONTRACT.md. 순차 이력에서 의도된 갱신이다. 생성 결과는 가장
오래된 파일을 선택하거나 합치지 말고 최종 Source에서 다시 생성해야 한다.

M3-C는 PR #5 위에 UI 진단 1건·Regression·Review 문서만 추가한다. Source/Fixture
보존 Diff와 M3-C→PR #5 Ancestor / merge-tree 검사를 최종 HEAD에서 확인한다.
새 Head 이동, Rebase, Squash 또는 Base 변경 이후에도 충돌이 없다는 보장은 아니다.
특히 중간 PR을 Squash하면 Ancestor 관계가 달라져 상위 PR은 재정렬·검증이 필요하다.

## 통합 전에 필요한 Gate

1. 사용자 화면 Review와 Main 통합의 명시적 승인. 개발자 Review와 CI는 이를 대체하지 않는다.
2. 모든 Head/Base를 다시 복구하고 위 Snapshot과 비교한다. 변경이 있으면 Diff·충돌을 재검토한다.
3. 최종 누적 Source의 Python 3.11/3.12 Tests와 M1/M3-A Gate, Chromium Desktop/Mobile/
   Static HTML/입력 수정 회귀가 모두 Pass여야 한다. Artifact는 실제 Checkout한 SHA와 일치해야 한다.
4. Physics/Adapter/기존 Tests/Fixtures/Guards/Benchmark 값 보존을 확인한다.
   Actual Applicability / Total Coupling / Full Clearance의 Uncomputed를 유지한다.
5. 승인 후 이력을 보존하는 Merge를 #1부터 순차 수행하는 방식을 권장한다. 각 단계 뒤
   다음 PR의 Base를 실제 Main으로 명시적으로 옮기고 Diff·CI·충돌을 재확인한다.
   현재 단계에서 어떤 Base/Ready/Draft/Auto-merge 설정도 바꾸지 않는다.
6. 마지막 통합 후 실제 Main SHA에서 검증·HTML을 재생성하고 해당 SHA의 CI/Artifacts를
   확인한다. 검증한 Tree와 일치하지 않는 Main을 완료로 보고하지 않는다.

## 판정

**조건부 통합 준비 가능**: 현재 Stack의 원격 CI와 Text/Ancestor 검사는 통과했으며,
M3-C 최종 CI/Artifact 확인이 필요하다. 사용자 Review와 Main 통합 승인은 별도 Gate다.
실제 Port 데이터·Physical Loss·Finite-Field 성능 검증은 이 Synthetic Tool 통합의
완료 주장에 포함하지 않는다. 실제품 성능과 제조 가능성은 계속 미검증이다.

다음 단계는 새 Physics가 아닌 승인된 Stack 통합·Release 점검이다.
이번 작업에서는 Main 병합·Release Publish·후속 개발을 실행하지 않는다.
