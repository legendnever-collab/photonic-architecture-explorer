# M7-R2 — Reference Mode to Two-Port Handoff

\`pae-workspace\` 실행 후 **SMF–Glass Mode Reference**를 엽니다. Reference 화면은 별도
탭에서 열리므로 편집하던 Workspace 입력을 유지한 채 비교할 수 있습니다.

| 확인 항목 | Workspace 동작 |
|---|---|
| 1550 nm SMF–Glass | SMF-28 Ultra, Desmet FLDW, Lee Uncracked의 nominal Width에서 계산한 Gaussian Intensity를 ±12 µm의 공통 가로축과 0–1 Peak-normalized 세로축에서 비교합니다. Desmet과 Lee의 실측 Intensity Image는 각 카드의 원문 링크에서 확인합니다. |
| 1310 nm SMF–Glass | SMF-28 Ultra 공급사 MFD 9.2 ± 0.4 µm와 Sun의 Glass Waveguide Intensity Cut에서 보고된 x/y 11/18 µm를 표시합니다. Actual External Port는 Uncomputed입니다. 누락된 Width 정의, Phase 또는 Curvature, External Reference Plane, 외부 매질 및 Mode Axis를 안내합니다. [M7-R3 판정](M7R3_1310_PORT_READINESS.md) |
| 개념 검토 | **1550 nm SMF–Glass 개념 Proxy 열기**는 [M7-A 예제](M7A_SMF_GLASS_WAVEGUIDE_REFERENCE.md)를 불러옵니다. 고정 배치, AF45 Width와 가정 Flat Phase를 포함합니다. 통합 Workspace의 Design은 기존 exact-q를 평가하고 유효 후보가 없는 정상 완료에 한해 Background Near-Match를 시작합니다. |
| 사용자 Mode | **검증한 Port 데이터로 새 입력 열기**에서 입력을 시작합니다. 1/e² MFD와 Wavefront Curvature 또는 Ordinary Complex q를 실제 기준면·축에 맞춰 입력합니다. 출처 레코드까지 보존해야 하는 Gaussian Fit은 기존 \`pae-design <external-port.json>\` 입력 계약을 사용합니다. |

Reference 페이지에 접속하거나 그림의 항목을 선택하면 화면만 갱신됩니다. Design은
기존 External Port Adapter의 필수값·단위·기준면 검사와 Gaussian Domain Guard를
통과한 입력에 대해 진행합니다. Optical Port의 Complex Field 적합성 및 Total Coupling
평가는 **Uncomputed**입니다. [External Port Contract](EXTERNAL_PORT_CONTRACT.md)

## 재현

\`\`\`bash
python -m pip install -e '.[test]'
pae-workspace
PYTHONPATH=src python -m unittest discover -s tests -q
\`\`\`

Catalog JSON은 앱의 리소스로 패키징됩니다. 기존 Offline Report는 같은 JSON에서 다시
생성되며, SHA-256과 보고서 내용을 대조할 수 있습니다. CI Browser 검사는 Desktop Reference
탭, Mobile 비교 및 입력 누락·사용자 직접 입력을 확인합니다.
[Mode Reference Library](M7R1_MODE_REFERENCE_LIBRARY.md)
