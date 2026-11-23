# M5-C — Mode Match View

Workspace에서 두 Port로 Design을 실행하고 후보의 **Mode Match 상세**를 펼친다.
Source는 Source Reference Plane에, 도착 빔과 Target Mode는 Target Reference Plane에
표시한다. Report는 t/s 축별 강도 주변분포를 보여준다. 각 축의 적분은 1이며
도착 빔과 Target Mode에는 동일한 µm 좌표, 범위, 강도 단위를 쓴다.
Target 곡선은 보라색 점선이고 도착 빔은 파란색 실선이다.

상대 Phase는 exp(+iωt) convention에서 도착 빔 − Target의 위상 차이다.
축 중심에서 전역 Phase를 제거하고 연속 위상 차이를 rad로 표시한다.
Source·Target은 기존 Adapter의 고정 Gaussian이고 도착 빔은 선택 후보의 평가에서
기록한 ordinary q를 사용한다. 강도 그림과 별개로 Normalize된 complex overlap은
기존 엔진 값을 사용한다. 예를 들어 동일 강도라도 두 축의 Wavefront Curvature가
다른 Synthetic control에서 50% / 3.0103 dB가 나오며 독립 복소수 적분으로 확인한다.

Mode Mismatch Loss는 −10 log10(η)이다. η=0은 ∞ dB, 결과가 없으면 Uncomputed다.
Gaussian 범위 안의 Mode Match이며, 경로·계면·개구 손실을 포함한 Total Coupling은
Uncomputed 상태다. 입력을 편집하거나 재계산에 실패하면 이전 Mode 결과가 숨겨진다.

Workspace의 HTML/JSON 저장은 현재 보고 있던 후보 ID를 기록한다.
`selected_candidate_id`는 엔진의 추천이고 `viewed_candidate_id`는 내보낼 때의
화면 선택이다. 오프라인 HTML을 열면 내보낼 때 본 후보로 시작한다.
Input SHA와 Source/Target Plane 및 Overlap은 원래 합격 후보의 기록에서 읽는다.

## 실행 및 검증

```bash
python -m pip install -e '.[test]'
pae-workspace
# http://127.0.0.1:8765 → Design → Mode Match 상세
python scripts/validate.py
python scripts/validate_m5a.py --output-dir results/runtime-m5a-review
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install --with-deps chromium
node scripts/check_workspace.cjs results/runtime-m5c-review results/runtime-m5a-review
```

Base는 [M5-B Draft PR #14](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/14)
(`3e4c1188c312a138b9888540ec0b4b13a878affb`)이며
[기준 CI 43977092609](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/43977092609)에서
81개 테스트를 통과했다. 새 CI에서는 fresh M5-A 결과를 Workspace 결과와 대조하고
Phase 누락·Domain Fail, Fixed Ports, 후보/입력 SHA/기준면/Overlap 일치, Desktop과
Mobile, 오프라인 내보내기를 확인한다. 구체적인 실행 결과는 Draft PR에 기록한다.
