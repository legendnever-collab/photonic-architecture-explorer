# M5-B — Two-Port Design Workspace

```bash
python -m pip install -e .
pae-workspace
```

브라우저에서 http://127.0.0.1:8765 을 엽니다. 기본 Synthetic Example은 M5-A와
같은 입력입니다. **Design**을 누르면 추천과 대안 후보를 비교할 수 있습니다. 실제로
새 Port를 지정하려면 **새 입력**을 선택합니다. CLI로도 실행할 수 있습니다.

```bash
PYTHONPATH=src python -m photonic_architecture_explorer.workspace --port 8765
```

Position은 mm, MFD는 1/e² 강도 직경으로 µm, Wavefront Curvature는 부호를 포함한
1/R [m⁻¹]입니다. Flat Phase를 명시할 경우에만 두 축에 0을 입력합니다. Complex q를
선택하면 두 축의 실수부·허수부를 mm로 입력합니다. Vacuum Wavelength는 nm,
Ambient Index는 외부 전파 매질의 값입니다. Target Direction은 들어오는 빔의 단위
전파 벡터입니다. External Reference Plane의 원점과 법선은 각 Position과 Direction에서
기록하고, Mode 기준축은 두 Port의 공통 sagittal unit vector입니다.

입력 변경 즉시 이전 후보·Overlap·내보내기를 숨깁니다. Design이 실행되면 서버가
입력값을 SI로 변환해 기존 design_two_ports에 전달하고, Fixed Port 정보와 입력
SHA256을 계산 결과에 보관합니다. 수정된 입력은 사용자 제공 값과 Gaussian 가정으로
기록합니다. 새 입력에 Synthetic 파장·굴절률·Phase를 채우지 않습니다.

결과 화면은 M5-A Read-only Report를 재사용합니다. 후보 경로, Footprint–Curvature
여유와 더 짧은 경로의 Trade-off, 제한된 탐색 실패 사유를 표시합니다. 후보의 Package
상태는 Conceptual Geometry / Uncomputed입니다. Normalize한 Gaussian Mode Overlap과
Total Coupling은 각각 표시하며, Total Coupling은 Uncomputed입니다. 외부 E/H나
Package 조건을 직접 제공하는 작업은 기존 계약과 CLI를 사용합니다.

HTML/JSON은 각각 다운로드할 수 있습니다. HTML은 연결 없이 브라우저에서 열 수 있고,
내장 JSON은 별도 JSON 다운로드와 같은 결과·입력 Snapshot을 포함합니다.
입력 및 계산 서버는 Loopback에서 실행되며 입력을 파일로 자동 저장하지 않습니다.

## 검증

Base PR #13 HEAD `111e12a5716280bc6047fdbe58c7bf36dcbd7e2e`는 Draft 상태입니다.
[Base CI 43907574747](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/43907574747)
에서 76개 테스트가 통과했고
[M5-A 검증 Artifact 14246830507](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/43907574747/artifacts/14246830507)
에 Synthetic 결과와 Missing Phase/Domain Fail 증거가 있습니다.

```bash
python -m pip install -e '.[test]'
python scripts/validate.py
python scripts/validate_m5a.py --output-dir results/runtime-m5a-review
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install --with-deps chromium
node scripts/check_workspace.cjs results/runtime-m5b-review results/runtime-m5a-review
```

실행마다 아직 존재하지 않는 runtime 디렉터리를 사용합니다. Chromium은 새 M5-A
Synthetic 결과와 기본 Workspace 결과가 정확히 같은지 확인합니다. Port 편집 및
Fixed Port 보존, 누락 Phase와 복구, 잘못된 Direction·High-NA, HTML/JSON 동일성과
Desktop/Mobile 출력도 확인합니다. CI의 m5b-workspace-evidence Artifact에 HEAD가
포함된 browser.json, 개별 내보내기 파일 및 두 스크린샷이 저장됩니다.
CI 링크와 결과는 Draft PR에서 확인합니다.

다음 단계는 [M5-C Mode Match View](NEXT_TASK.md)입니다.
