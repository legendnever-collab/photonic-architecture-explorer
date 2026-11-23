# User Guide

## 설치와 실행

| 환경 | 방법 |
|---|---|
| Windows(설치 없음) | [Windows offline package CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/workflows/windows-review.yml)의 `windows-offline-package` Artifact를 받아 ZIP을 풀고 `Start-Photonic-Architecture-Explorer.cmd` 실행. 기본 브라우저(Chrome/Edge)로 열림 |
| Python 3.11+ | `python -m pip install -e .` 후 `pae-app --open` → `http://127.0.0.1:8770/` |
| Frontend 개발 | `cd frontend && npm ci && npm run build`(결과는 `src/photonic_architecture_explorer/web/`에 들어가며 커밋한다) |

서버는 127.0.0.1에서만 열리고 외부 통신을 하지 않는다.

## 화면 구성

| 영역 | 내용 |
|---|---|
| 상단 | 시나리오 선택, **Design**(Ctrl+Enter), 열기(Design Document JSON), 내보내기(입력 JSON, 결과 JSON, 도면 SVG) |
| 왼쪽 | 공통(파장, 외부 매질 n), Source/Target Port: Preset, Position, Direction, Sagittal 축, MFD t/s, 1/R t/s, 출처 Chip, 발산각 Guard |
| 가운데 위 | 3D 장면(Z가 위). Port 기준면·전파 화살표·Mode 타원, 반사면 실제 Sag 형상, 주광선, 1/e² Beam 튜브 |
| 가운데 아래 | 2D 도면: 주 평면 + Fold(기본), 2×2, Top XY, Front XZ, Side YZ, Fold 전개 Beam Envelope |
| 오른쪽 | 결과 상태와 사유, 다음 단계, 후보 비교 표, 선택 후보의 반사면 상세와 엔진 판정, 거절 사유 분포, 미계산 항목 |

## 기본 흐름

1. 시나리오를 고르거나 Port 값을 입력한다. 입력이 바뀔 때마다 Port 배치와 Guard가 바로 다시 계산된다(Preview).
2. Port 위치는 3D에서 직접 옮길 수 있다. Port를 더블클릭하거나 "3D에서 이동"을 누른 뒤 화살표를 끈다(0.1 µm 단위로 반올림).
3. **Design**을 누르면 엔진이 후보를 만든다. 후보 표에서 행을 누르면 3D·2D에서 그 후보가 강조된다.
4. 입력을 바꾸면 이전 결과는 "입력이 바뀌었습니다"로 표시되고 도면에서 사라진다. Design을 다시 실행한다.
5. 필요한 도면을 SVG로, 입력·결과를 JSON으로 내보낸다. 결과 JSON에는 입력 SHA-256이 들어 있어 재현할 수 있다.

## 표시 규칙

| 항목 | 의미 |
|---|---|
| Beam 확대 표시 | Beam·Mode 반경이 mm 단위 Geometry보다 너무 작으면 반경만 ×N으로 키워 그린다. 배율은 화면 왼쪽 아래와 도면 부제에 표시된다. "Beam 실제 크기"로 끌 수 있다 |
| 반사면 | 엔진이 정한 Aperture 안의 이차곡면(Vertex 기준 Sag)을 그대로 그린다 |
| 2D 도면 좌표 | 엔진 값을 그대로 쓰며, 브라우저 검사가 1 nm 이내 일치를 확인한다 |
| ⊙ / ⊗ | 전파 방향이 도면 평면에 수직일 때 앞으로 나오는 방향 / 들어가는 방향 |
| Direction | Source는 빛이 나가는 방향, Target은 **도착하는 빛의 진행 방향** |
| t / s 축 | s = Sagittal 축, t = s × d. 문헌 Preset은 "t = vertical(기판 수직)"을 기본으로 하고 바꿀 수 있다 |

## 결과를 읽는 법

| 표시 | 의미 |
|---|---|
| Computed | 모델 안에서 유효 후보가 있다. 실제 제품 성능 판정은 아니다 |
| Fail | 입력·Geometry·Model Domain에서 막혔다. 사유, 임계값, 다음 단계를 함께 본다. 물리적 불가능의 증명은 아니다 |
| Invalid | 입력 문서 오류. 왼쪽 패널에 항목별 경로가 표시된다 |
| η | Scalar Paraxial Normalized Mode Overlap. Total Coupling이 아니다 |
| 3w·\|κ\| / 0.15 | 반사면 곡률 대비 Beam 크기 Guard. 1에 가까울수록 모델 여유가 작다 |
| 통과 최소 MFD | 이 파장·매질에서 발산각 Guard(0.1 rad)를 통과하는 최소 Waist MFD(1310 nm 공기 중 약 8.34 µm) |

## Port Preset

| ID | 내용 | 출처 |
|---|---|---|
| `smf28-ultra-1310` / `-1550` | SMF-28 Ultra, MFD 9.2 / 10.4 µm | Corning PI1424 |
| `sun-fldw-55mw-1310` | LDW(Fused silica), 11 × 18 µm | Sun 2021 Thesis Fig. 3.5 |
| `desmet-fldw-1550` | LDW(Fused silica), 12.8 × 12.1 µm | Desmet 2021 IEEE Photonics J. |
| `lee-uncracked-y-1550` | LDW(Fused silica), 10.2 × 10.0 µm | Lee 2021 Sci. Rep. |
| `brusberg-iox-1550` | IOX(D263Teco), 18.8 × 12.0 µm | Brusberg 2012 ECTC |
| `synthetic-siph-ssc-3um` | SSC 계열 대표값 3 µm | Synthetic |

문헌 값은 Intensity 기반 폭이다. Phase는 Flat으로 가정하고, 문헌 축을 lateral/vertical로 읽는 대응도 가정으로 표시한다.
숫자를 직접 고치면 Preset 연결이 풀리고 출처가 "가정(User-edited)"으로 바뀐다.
