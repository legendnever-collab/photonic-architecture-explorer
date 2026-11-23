# M5-F — Two-Port Concept Acceptance

범위는 1310 nm, 외부 매질 n=1의 두 Fixed Gaussian Port 사이에서 기존의
coplanar 두 반사면 설계와 그 결과를 검토하는 흐름이다. 세 입력은 비기밀
수학 검증용 Synthetic이다. Source 위치는 (0, 0, 0) mm, Target 위치는
(2, 0, 2) mm다. 두 전파 방향은 +X, sagittal 축은 +Y, tangential 축은
−Z이며 reference plane은 각 포트의 외부 기준면이다.

| 케이스 | 출처 | Source MFD t/s [µm] | Target MFD t/s [µm] | Target 파면 곡률 t/s [m⁻¹] | 기대 결과 |
|---|---|---|---|---|---|
| 같은 q | [Frozen M5-A](../../examples/m5a_two_ports.json), M1-001 수학 기준 | 16 / 24 | 16 / 24 | 0 / 0 | Computed |
| 서로 다른 q | [M5F-002](../../examples/m5f_different_q.json), M5-A 위치·방향에 폭과 곡률을 독립 지정 | 16 / 24 | 20 / 28 | +400 / −350 | Computed |
| 고발산 | [M5F-003](../../examples/m5f_high_divergence.json), Source의 좁은 MFD로 기존 가드를 검증 | 2 / 2.4 | 16 / 24 | 0 / 0 | Fail, 탐색 시작 전 차단 |

Source 파면 곡률은 모두 0이다. ordinary q는 \(1/q=K-i\lambda_0/(\pi n w^2)\),
\(w=\mathrm{MFD}/2\)로 결정되며 서로 다른 q 케이스는 t/s 두 축이 모두 다르다.
고발산 입력에서 Source의 1/e² 각 발산은 약 0.417/0.347 rad여서
기존 0.1 rad 가드를 초과한다. 해당 케이스의 Overlap과 민감도는 Uncomputed다.

## 검증과 범위

CLI와 Workspace의 동일 입력에서 같은 리포트를 생성한다. 독립 specular 식과
ABCD 행렬로 Fixed Port 방향 및 도착 q를 대조한다. 저장된 민감도는 같은 q의
shift/tilt 중첩 닫힌식과 대조한다. t/s 각 축의 손실 항은
\((h/w)^2 + [kw(\theta-Kh)/2]^2\)이며, 이를 합산한 뒤 \(10/\ln 10\)을 곱하면
Nominal 대비 dB가 된다. Chromium에서 오프라인 HTML과 JSON을 비교하고,
각 케이스의 A4 한 페이지 PDF를 생성한다. 적합 케이스는 후보 ID·입력 SHA·경로·
Overlap과 8개 민감도 행을 확인한다. 고발산 케이스는 거절 근거와 Input SHA,
Uncomputed 상태를 인쇄하고 후보 요약을 숨긴다.

거절 리포트에서 Input SHA가 화면과 출력에 드러나지 않던 점을 보완했다.
설계에 사용할 수 있는 근거는 Frozen family의 후보 생성 및 거절, nominal
Gaussian match, Target 기준면 상대 오차 비교다. 실제 부품 배치 공차,
Package Yield, Total Coupling은 Uncomputed이며 입력은 제품 사양이 아니다.

```bash
python -m pip install -e '.[test]'
python scripts/validate.py
python scripts/validate_m5a.py --output-dir results/runtime-m5a-review
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install --with-deps chromium
# Print checks use poppler-utils and Korean fonts.
node scripts/check_workspace.cjs results/runtime-m5e-browser results/runtime-m5a-review
python scripts/validate_m5f.py --output-dir results/runtime-m5f-acceptance
node scripts/check_m5f_print.cjs results/runtime-m5f-acceptance
```

Base는 [Draft PR #17](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/17)이다.
[기준 CI 43985937358](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/43985937358)의
91개 테스트와 M5-E 인쇄를 후속 CI에서 재현한다. 실행별 케이스·SHA·후보·PDF는
Draft PR의 CI artifact에 기록한다.
