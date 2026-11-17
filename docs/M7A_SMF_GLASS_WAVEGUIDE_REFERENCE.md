# M7-A — SMF–Glass Waveguide Reference Case

1550 nm에서 SMF와 laser-written Glass Waveguide의 공개 Mode Width를 사용해,
두 Fixed Optical Port 사이에 기존 Two-Reflector Gaussian Design이 추천할 수 있는
후보가 있는지 확인했다. 이 Reference Case는
[Track A](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/25)의
첫 단계다. [Product Charter](PRODUCT_CHARTER.md)와
[M6-G Input Readiness](M6G_WORKFLOW_ACCEPTANCE.md#actual-input-readiness-checklist)를 적용했다.

**개념 설계 결과는 후보 0개, 실제 적용성은 Uncomputed다.** 두 Port의 Gaussian
Divergence는 입력 가드 안에 들었다. 그러나 이 Offset과 Mode 조건에서 유한 탐색으로
생성한 처방은 모두 Reflection Path의 Model Domain 검사에서 보류됐다.

## Fixed Ports와 입력 출처

아래 값은 [실행용 JSON](../examples/m7a_smf_glass_proxy.json)에 SI Units로 기록했다.
Source와 Target은 각각 Air-side External Reference Plane에 고정했다.
World Frame은 right-handed XYZ이며 두 전파 방향은 +X, 공통 Sagittal Axis는 +Y,
Tangential Axis는 −Z다.

| 항목 | Reference Case 값 | 출처와 적용 범위 |
|---|---|---|
| Wavelength | 1550 nm | SMF Datasheet와 AF45 Near-Field Figure에서 공통으로 확인한 파장 |
| Source MFD | 10.4 µm, 원형 Gaussian | Corning SMF-28 Ultra PI1424의 1550 nm 사양은 10.4 ± 0.5 µm. 중앙값을 External 1/e² Intensity Diameter로 쓰는 Proxy 가정 |
| Target MFD | 10.0 µm, 원형 Gaussian | Eaton et al. §3.3.1, Fig. 5(c)의 laser-written Schott AF45 Near-Field MFD. 두 축에 같은 External 1/e² Intensity Diameter를 적용하는 Proxy 가정 |
| Wavefront Curvature | 각 축 0 m⁻¹ | 두 External Plane에서 각각 명시한 개념용 Flat Phase. 공개 Width 자료에는 해당 Complex Field가 없음 |
| External Medium | homogeneous air, n = 1 | 개념 외부 전파 매질. Fiber와 Waveguide의 내부 매질은 계산 범위 밖 |
| Position | Source (0,0,0), Target (2,0,2) mm | [M5-A Fixture](../examples/m5a_two_ports.json)의 배치를 재사용한 Synthetic Offset. 두 공개 장치의 실제 배치와 별개 |
| Polarization 및 Package | Scalar Model, Package 미제공 | Jones Transport, Fabrication 및 실제 조립 조건은 증거 미제공 |

1550 nm를 선택한 이유는 두 공개 Width를 같은 파장에서 비교할 수 있기 때문이다.
Waveguide Width를 1310 nm로 환산하거나, 두 Width를 실제 장치의 외부 Complex Mode로
확정하지 않았다. Gaussian Proxy의 Width와 Phase는 모두 `assumed`로 저장한다.

- Corning, *SMF-28 Ultra Optical Fiber*, PI1424, Optical Specifications의
  Mode Field Diameter 표. [Datasheet](https://www.corning.com/media/worldwide/coc/documents/Fiber/product-information-sheets/PI-1424-AEN.pdf)
- Eaton et al., *Heat accumulation effects in femtosecond laser-written waveguides
  with variable repetition rate*, Optics Express 13, 4708–4716 (2005), §3.3.1과 Fig. 5(c).
  [DOI](https://doi.org/10.1364/OPEX.13.004708)

## 모델 적용성 결과

Flat-Phase Gaussian의 1/e² Divergence Half-Angle은 θ = 2λ₀/(πn·MFD)다.
직접 계산한 Source 0.094881 rad와 Target 0.098676 rad가 Adapter 결과와 일치했다.
0.1 rad 입력 가드의 Flat-Phase MFD 하한은 9.868 µm로, Target Proxy는 하한보다
약 0.132 µm 크다. 실제 Width와 Phase 증거가 확보되면 해당 값으로 다시 검사한다.

| 항목 | 실제 실행 결과 |
|---|---|
| Input Contract 및 Port Divergence | Pass, 기존 M3A-1 External Port 형식으로 탐색 시작 |
| Fixed-Port Geometry | 36개 Vertex 조합, 144개 exact-q 처방이 Geometry 검사를 통과 |
| Path Model Domain | Footprint–Curvature 첫 실패 141개, Divergence 첫 실패 3개 |
| Recommendation / Alternatives | 0개, 기존 유한 탐색 완료 |
| Normalized Mode Overlap | Uncomputed, 보류된 처방의 Overlap은 null |
| Actual Applicability / Full Package / Total Coupling | Uncomputed, 실제 외부 Field와 실장 증거 미제공 |

두 거절 건수는 각 처방의 **첫 실패**다. 한 처방에 가드 위반이 추가로 있을 수 있다.
예를 들어 G015-B1은 45° 반사 두 번으로 1–2–1 mm Chief Path를 닫는다. 첫 반사면
직전의 빔 반경을 \(w(z)=w_0\sqrt{1+(z/z_R)^2}\)로 검산하면 95.02 µm이며, Tangential
투영 반경은 134.38 µm다. 이 반사면의 처방 곡률로 계산한 3w·|κ|는 t/s 각각
0.13968 / **0.19754**다. Sagittal 값이 0.15를 초과해 이 구조의 Overlap을 보류한다.
이 수치는 Guard 판정 근거다. 이 탐색에서 후보가 없다는 결과로 다른 형상이나
Topology의 실현 가능성까지 판단할 수 없다.

## 재현과 후속 입력

```bash
PYTHONPATH=src python -m photonic_architecture_explorer.design \
  examples/m7a_smf_glass_proxy.json --output-dir /tmp/pae-m7a-reference
```

이 Fixture의 CLI는 설계 상태 `Fail`에 대응하는 exit 1과 함께
`design.html`, `design.json`을 출력한다. HTML에서 거절 상태와 탐색 근거를 확인하고
JSON에서 동일한 입력과 처방별 거절 사유를 확인할 수 있다. Input Snapshot SHA256은
`9d6d55bc8c4a06ca99c7ffcae205954a634678162986d2565c111b76df510988`이다.
회귀 검사는 Target Phase를 생략하면 `Uncomputed`에서 멈추는지도 확인한다.

| Milestone 기준 | M7-A 결과 |
|---|---|
| Physics | Port와 경로의 Gaussian 가드 결과를 확보했다. 실제 적용성은 각 Facet의 외부 Complex Field, Gaussian Fit과 불확도에 근거해 다시 판정한다. |
| Usability | 기존 Two-Port JSON과 CLI로 한 번에 실행한다. HTML·JSON에 거절 상태와 Input SHA를 남긴다. |
| Patent Utility | Fixed-Port Offset과 1–2–1 mm Fold의 제약을 설명할 수 있다. 검증을 통과한 대안이나 실제 성능 비교 그림을 만들 근거는 확보되지 않았다. |

실제 사례를 이어 평가할 최소 입력은 비기밀 SMF/Glass Waveguide 한 쌍의
파장, 공통 좌표계에서의 External Plane Pose, 매질, 각 Plane의 MFD와 Wavefront
Curvature 또는 Complex q다. 실제 Gaussian 적합성을 판정하려면 같은 Plane의
Complex Field와 Fit Residual 및 Sampling 근거가 필요하다. 이 조건에서 기존 경로
가드가 다시 지배하면 해당 경로와 가드에 한정해 독립 Field Reference를 선정한다.
