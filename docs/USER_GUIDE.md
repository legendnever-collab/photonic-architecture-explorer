# User Guide

> P0 기준. P1에서 3D/2D 시각 Workspace가 들어오면 이 안내를 새 화면 기준으로 바꾼다.

## 설치와 실행

```bash
python -m pip install -e .
pae-app --open            # 새 Workspace(P0: API Console), http://127.0.0.1:8770
pae-workspace             # 기존 Two-Port Workspace(P1까지 유지), http://127.0.0.1:8765
```

Windows에서는 CI가 만든 오프라인 ZIP을 풀고 `Start-Photonic-Architecture-Explorer.cmd`를 실행한다
(CPython·NumPy·SciPy 포함, Chrome 또는 Edge로 열림). ZIP 안에서 바로 실행하지 않는다.

## 기본 흐름

1. 시나리오를 고르거나 Design Document(`pae.design/1`)를 작성한다. [형식](DESIGN_DOCUMENT.md)
2. **Design**을 누르면 엔진이 고정 두 반사면 Family에서 후보를 만들고 검사한다.
3. 결과에서 Port별 발산각 Guard, 후보의 광경로·입사각·곡률반경·3w·|κ| 여유, 거절 사유를 확인한다.

## 결과를 읽는 법

| 표시 | 의미 |
|---|---|
| Computed | 모델 안에서 유효 후보가 있다. 실제 제품 성능 판정은 아니다 |
| Fail | 입력·Geometry·Model Domain에서 막혔다. 사유와 임계값을 함께 본다. 구조가 불가능하다는 증명은 아니다 |
| Invalid | 입력 문서 오류. 항목별 경로가 표시된다 |
| η (Normalized Overlap) | Scalar Paraxial Mode 일치도. Total Coupling이 아니다 |
| 최소 Waist MFD | 이 파장·매질에서 발산각 Guard(0.1 rad)를 통과하는 최소 MFD. 1310 nm 공기 중에서 약 8.34 µm |

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
