# M5-E — Candidate Review Summary

Workspace에서 **Design**을 실행하고 후보를 선택한 뒤 **후보 요약 보기**를 누른다.
**후보 요약 인쇄**는 선택 후보를 A4 세로 한 페이지로 인쇄하거나 PDF로 저장한다.
저장한 오프라인 HTML에서도 같은 동작을 사용할 수 있다. 화면의 요약을 접고 있는
상태에서도 인쇄에는 선택 후보가 포함된다.

첫 부분에 후보 ID, 기존 순위, 입력 SHA, Fixed Port의 기준면·XYZ·방향·complex q를
표시한다. Optical Path는 반사면과 구간 길이, Nominal Mode Match는 기존 Overlap과
mismatch loss를 표시한다. Target 기준면 민감도 표는 M5-D의 Position/Angle 단일
perturbation 값과 Nominal 대비 변화량을 가져온다.

민감도 동률은 두 후보의 8개 시나리오에 대해 유한한 Δ loss가 모두 계산되어 있고
절대 차이가 1e-6 dB 이내일 때 표시한다. 이 수치는 표시용 비교 기준이다.
Nominal 설계 비교는 원래 순위에서 Path 길이, Max 3w·κ, Max Projected Radius를 보여준다.
Target 기준면 응답의 동률은 실제 반사면 배치 공차를 확정하지 않는다.
실제 부품 배치 공차·Off-vertex field handoff, Package Yield, Total Coupling은 Uncomputed다.

JSON의 `candidate_review` 필드가 화면과 인쇄에 쓰이는 요약 수치를 저장한다.
`viewed_candidate_id`는 저장할 때 본 후보를, `selected_candidate_id`는 계산 엔진의
추천을 나타낸다. 입력이 유효하지 않아 후보를 생성할 수 없으면 요약을 표시하지 않는다.

## 실행과 검증

```bash
python -m pip install -e '.[test]'
pae-workspace
# http://127.0.0.1:8765 → Design → 후보 선택 → 후보 요약 보기 / 인쇄
pae-design examples/m5a_two_ports.json --output-dir results/runtime-m5e-review
python scripts/validate.py
python scripts/validate_m5a.py --output-dir results/runtime-m5a-review
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install --with-deps chromium
# Browser test needs pdfinfo and pdftotext (poppler-utils), plus Korean fonts for PDF.
node scripts/check_workspace.cjs results/runtime-m5e-browser results/runtime-m5a-review
```

기준 [Draft PR #16](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/16)은
[CI 43982413969](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/43982413969)에서
88개 테스트를 통과했다. 이 변경의 CI는 이전 Workspace, Mode Match 및 민감도 검증을
재현하고 PDF 페이지 크기·수와 추출 텍스트를 확인한다. 실행 결과와 다운로드 경로는 Draft PR에 있다.
