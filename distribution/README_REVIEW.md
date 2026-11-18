# Photonic Architecture Explorer — Windows Review

1. ZIP 전체를 원하는 폴더에 압축 해제하세요. ZIP 안에서 직접 실행하지 마세요.
2. `Start-Photonic-Architecture-Explorer.cmd`를 더블클릭하세요.
3. 기본 Browser에서 Two-Port Workspace가 열립니다. 자동으로 열리지 않으면 콘솔에
   출력된 `http://127.0.0.1:...` 주소를 여세요. 콘솔은 실행 중 계속 열어 두세요.
4. `Synthetic Example → Design`으로 기준 설계를 확인하세요.
5. `SMF–Glass Proxy → Design`으로 자동 Near-Match를 확인하세요. 수분 걸릴 수 있으며
   취소하거나 입력을 수정할 수 있습니다. 입력 수정 후 이전 결과와 Export는 숨겨집니다.
6. 결과에서 Mode Match 상세, HTML/JSON 저장과 후보 요약 인쇄(A4)를 확인하세요.
7. 종료하려면 콘솔에서 Ctrl+C를 누르세요. 다시 실행할 때는 시작 파일을 여세요.

Windows x64 검토용입니다. CPython과 NumPy/SciPy가 포함돼 있어 별도의 Python 설치나
다운로드가 필요하지 않습니다. 앱은 이 컴퓨터의 Loopback에서 실행됩니다.
사용자가 제공한 실제 Field/Package/제조 증거를 포함한 패키지가 아닙니다.

SMF–Glass 예제는 공개 Width와 명시한 Gaussian/Flat Phase 가정입니다. Normalized
Mode Overlap은 Total Coupling이 아닙니다. Actual Applicability, 실제 Assembly Tolerance,
Package Yield, Total Coupling과 Patentability는 Uncomputed입니다. Guard Margin도
제조 공차가 아닙니다. `app/docs/M7D_BACKGROUND_WORKFLOW.md`에서 범위를 확인하세요.

`PACKAGE_MANIFEST.json`에 Source HEAD, Runtime/Dependency 버전, 입력과 배포 파일의
SHA-256이 기록됩니다. CPython License는 `runtime/LICENSE*`, NumPy/SciPy 및 포함된
Binary Library License는 `runtime/Lib/site-packages`의 관련 `.dist-info/licenses`와
패키지 License 파일에 보존됩니다. 이 ZIP은 Draft의 사용자 검토용 배포물입니다.
