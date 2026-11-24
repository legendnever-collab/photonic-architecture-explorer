# Photonic Architecture Explorer — Windows 오프라인 패키지

설치 없이 실행되는 Windows x64 패키지입니다. CPython 3.12, NumPy, SciPy와 Workspace 화면이 들어 있습니다.

## 실행

1. ZIP을 원하는 폴더에 **압축 해제**합니다(ZIP 안에서 바로 실행하지 마세요).
2. `Start-Photonic-Architecture-Explorer.cmd`를 더블클릭합니다.
3. 기본 브라우저(Chrome 또는 Edge)에 `http://127.0.0.1:8770/`이 열립니다. 8770이 사용 중이면 다른 포트가 콘솔에 표시됩니다.
4. 사용을 마치면 콘솔 창에서 Ctrl+C를 누르거나 창을 닫습니다.

인터넷 연결이 필요 없고, 모든 계산은 이 PC 안(127.0.0.1)에서만 이루어집니다.

## 화면

| 영역 | 내용 |
|---|---|
| 왼쪽 | Port 입력(Preset, 위치, 방향, MFD, 위상)과 출처, 발산각 Guard, Glass 매질(굴절률·상면·두께), 공간·제작 제약 |
| 가운데 위 | 3D 장면. 드래그 회전, 휠 확대, Port를 더블클릭하거나 "3D에서 이동"을 누른 뒤 화살표로 이동 |
| 가운데 아래 | 2D 도면(주 평면 + Fold, 2×2, XY/XZ/YZ, Fold 전개 Beam Envelope, 탐색 지도) |
| 오른쪽 | 결과, 후보 비교(근축 η와 비근축 η), 반사면 상세, 실패 원인과 다음 단계 |

η는 Scalar Paraxial Normalized Mode Overlap, 비근축 η는 같은 처방을 근축 근사 없이 계산한 Scalar Overlap이며 둘 다 Total Coupling이 아닙니다. 근축 η가 1이어도 비근축 η가 낮으면(빨간 글씨) 반사면 수차(Coma) 때문에 실제로는 덜 결합됩니다. Total Coupling, 조립 공차, Package, 특허성은 계산하지 않습니다.

## 확인용

`PACKAGE_MANIFEST.json`에 빌드 Commit과 모든 파일의 SHA-256이 기록되어 있습니다.
