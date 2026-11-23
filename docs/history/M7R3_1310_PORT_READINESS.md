# M7-R3 — 1310 nm Glass Waveguide Port Readiness

## 공개 실측 사례

Qi Sun의 2021년 University of Southampton 박사학위 논문에서 55 mW로 기록한
Fused-Silica FLDW 한 사례를 선택했다. Fig. 3.5(c)는 **1310 nm** 출력 Intensity
Image, Fig. 3.5(d)는 x/y Intensity Cut에 Gaussian을 fit한 결과다. 그림의 MFD
표기는 x 11 µm, y 18 µm다. 55 mW는 제작 시 Writing Power다. §2.2와 Fig. 2.6은
Fiber Butt Launch와 출력 측 0.6 NA Objective·IR Camera를 설명한다.
[원문 · Fig. 3.5(c–d), 인쇄 p. 36 및 §2.2](https://eprints.soton.ac.uk/467364/1/Qi_Sun_Thesis_for_Award.pdf)

연계 데이터셋은 DataCite에 등록돼 있다. 등록 정보에는 파일 목록이 없었고
저장소의 첨부 파일에 접근할 수 없어 Phase·Plane·Width 정의의 포함 여부는 미확인이다.
[데이터셋 DOI 10.5258/SOTON/D2043](https://doi.org/10.5258/SOTON/D2043)
후속 파일 목록 및 접근 결과는 [M7-R4](M7R4_1310_EXTERNAL_FIELD_EVIDENCE.md)에 기록한다.

| 근거 | Adapter 입력 판단 |
|---|---|
| Fig. 3.5(c–d)의 1310 nm | Vacuum Wavelength 1.31 × 10⁻⁶ m로 기록한다. |
| Fig. 3.5(d)의 x/y MFD 11/18 µm | 문헌 Figure의 nominal label로 기록한다. Fit Width의 1/e² 정의와 불확도는 해당 자료에서 확인되지 않았다. |
| Objective로 관측한 출력 Intensity | 등록된 외부 기준면의 위치·방향·매질, x/y에서 공통 World Frame t/s로의 변환, Complex Field, Phase/Curvature, Polarization은 확보되지 않았다. |
| SMF-28 Ultra 공급사 1310 nm MFD 9.2 ± 0.4 µm | 별도 공급사 Reference의 사양값이다. 해당 실험의 Launch Fiber 식별이나 설계에 사용할 Source의 외부 기준면·Phase 정보는 확보되지 않았다. |

Reference 탭과 Offline Catalog에서 문헌값과 원문 링크를 볼 수 있다. Sun 사례의
Gaussian Preview와 Port 자동 입력은 보류한다. Intensity Cut의 가로·세로 폭은
Wavefront Curvature나 동일 기준면의 2D Complex Gaussian Fit을 결정할 수 없다.

## 기존 Adapter에서 재현

```bash
PYTHONPATH=src python -m photonic_architecture_explorer.external examples/m7r3_sun_1310_readiness.json
python scripts/m7r1_mode_report.py
```

예제는 입증된 파장만 입력한다. Adapter는 첫 누락인 `ambient_index`에서 멈추고
Input Contract, Geometry, Gaussian Model Domain, Actual Applicability를 `Uncomputed`로
반환한다. Mode Overlap과 Total Coupling의 수치는 `null`이다. 1550 nm M7-A Proxy는
독립 개념 사례이며 Source/Target 입력과 SHA-256은 기존 값을 사용한다.

## 적용성을 결정할 최소 증거

1. **측정 경로** — 사용하려는 두 Port에 대해 1310 nm의 외부 Transverse Reference Plane을 각각 지정한다. Facet 대비 Plane 위치, 공통 Frame의 원점·전파 방향·t/s, 외부 매질, Polarization을 기록한다. 1310 nm에서 교정한 Near-Field Intensity와 간섭 측정한 Relative Phase를 동일 Plane에 등록한다. Objective의 배율과 전달 Phase를 교정하고 반복 측정과 배경 보정으로 불확도를 기록한다. Guide를 역방향으로 여기해 Target 자료를 얻는 경우 도착 방향과 Phase 부호가 External Port Contract와 일치하도록 변환한다.
2. **시뮬레이션 경로** — 1310 nm의 검증된 Refractive-Index Profile, Facet Geometry·외부 매질·경계조건이 있으면 기존 Vector Eigenmode와 Facet Field 전파를 사용한다. 동일 외부 Plane에 Complex transverse field, 좌표 간격·단위·Normalization·Polarization을 저장하고 grid/window refinement로 수렴을 확인한다.
3. **판정** — 같은 Plane의 Complex Field에서 Gaussian Field Overlap, Phase Residual, Grid/Window 의존성을 함께 확인한다. 오차 기준은 사례의 Mode-Mismatch 예산에서 앞서 정한다. 검증된 1/e² MFD와 Curvature 또는 Ordinary Complex q가 확보되고 기존 Guard가 통과하면 Fixed-Port Two-Reflector 개념 설계를 진행할 수 있다. 비분리 성분이나 Facet 전파 오차가 중요하면 독립 Field Reference 검증이 다음 범위다.

[External Port Contract](../EXTERNAL_PORT_CONTRACT.md) · [Actual Input Readiness](M6G_WORKFLOW_ACCEPTANCE.md#actual-input-readiness-checklist)
