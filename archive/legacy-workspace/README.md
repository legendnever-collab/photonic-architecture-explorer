# 보관: 기존 Two-Port Workspace와 HTML Inspector (M3-B ~ M7-R28)

2026-11-24 P1에서 3D/2D 시각 Workspace(`pae-app`)로 교체하면서 기본 실행 경로와 CI에서 분리했다.
삭제하지 않고 원래 디렉터리 구조(`src/`, `tests/`, `scripts/`, `distribution/`, `references/`)로 보관한다.

| 묶음 | 내용 |
|---|---|
| `workspace.py`, `inspector.py`, `design_report.py`, `candidate_review.py`, `confidence.py`, `tutorial.py` | 서버 렌더링 HTML 화면, 후보 보고서, 신뢰도 표, Tutorial |
| `workflow_jobs.py`, `workflow_worker.py` | Near-match 백그라운드 작업(M7-C/D) |
| `envelope_search.py`, `pose_envelope.py`, `reference_redesign.py` | M7-R6~R28 Reference case 재설계와 Package Envelope 화면 |
| `scripts/validate_m5a.py` 등, `check_*.cjs` | 기존 화면의 브라우저·인쇄 검사 |
| `distribution/review_launcher.py` | 기존 Windows Review 실행기 |
| `references/m7r20` | Tutorial이 쓰던 Yee Field Profile |

엔진 쪽에 필요한 함수는 옮겨 두었다: `visible_overlap` → `mode_match.py`, `review_cases`/`evaluate_view` → `review_cases.py`,
`review_snapshot` → `design.py`(HTML 없이 Sensitivity·Placement 진단만 추가).

## 재개 조건

Near-match 백그라운드 탐색이나 Package Envelope 화면이 새 Workspace에 필요해지면(P2 후보 생성, Package 단계),
여기 있는 로직을 참고해 새 API·화면에 다시 구현한다. 그대로 되살리려면 `git mv`로 원래 위치에 옮기고,
`pyproject.toml`의 `pae-workspace`/`pae-inspector` 진입점과 CI Job을 함께 복원한다.
