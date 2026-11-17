# Photonic Architecture Explorer — Patent-Oriented Product Vision

Photonic Architecture Explorer는 물리적 근거에 기반해 Optical Interconnect 구조를 탐색하고
시각화하는 Patent-Oriented Engineering Tool이다. 두 Fixed Optical Port에서 구조 후보를
생성하고, 적합한 Optical Model로 실현 가능성을 평가하며, 대안 간 기술적 차이와 그 근거를
그림과 설계 기록으로 설명한다. 이 결과는 Invention Disclosure와 특허 명세서 작성의 기술
자료로 사용할 수 있다. Novelty, Inventive Step, Freedom to Operate는 별도로 조사한다.
[Product Charter](PRODUCT_CHARTER.md)의 설계·검증·통합 기준과
[Development Roadmap](PATENT_ORIENTED_DEVELOPMENT_ROADMAP.md)을 함께 적용한다.

## A. Architecture Exploration

첫 구현은 두 Local Quadratic Reflector를 사용하는 **Two-Reflector Gaussian Design
Explorer**다. 현재 Workspace는 Coplanar와 Aligned Separable Gaussian 범위에서 두 Fixed
Port로 후보를 생성하고, [Frozen Guards](M1_BENCHMARK.md)와
[현재 Recommendation 정책](M6C_ENGINEERING_RECOMMENDATION.md)을 적용한다.
정규화된 Mode Overlap과 Model Guard 여유는 각각 해당 모델 안의 진단값이다.
현재 지원과 미계산 범위는 [M6-G 검증](M6G_WORKFLOW_ACCEPTANCE.md)을 따른다.

장기적으로 후보 자동 생성과 비교를 다음 Architecture Family로 단계적으로 확장한다.

- 두 반사면 구조의 설계 범위 확장
- Lens–Mirror 조합
- Multi-Lens System
- Aspherical 및 Freeform Reflector
- Hybrid Refractive/Reflective Optical System

각 확장은 향후 후보이며, 현재 구현 및 검증 범위는 위 Two-Reflector Loop에 한정된다.
모든 대안은 동일한 Port Position, Propagation Direction, External Medium, Wavelength,
Complex Mode를 사용한다. 기본 흐름은 **Input Port → Output Port → Design →
Recommendation → Alternatives → Visualization → Export**다. 사용자는 기본 흐름을
시작할 때 Topology, Solver, Optimizer 또는 Reflector Prescription을 지정할 필요가 없다.

## B. Input / Output Optical Mode

| Level | 표현과 필요한 정보 | 구현 상태 |
|---|---|---|
| 0 — Theoretical Gaussian | 명시적 Gaussian 가정, MFD와 Wavefront Curvature 또는 ordinary Complex q, External Reference Plane | 현재 Workspace에서 지원 |
| 1 — Elliptical / Astigmatic Gaussian | 두 Transverse Axis의 Mode Field와 Phase 또는 축별 Complex q, 축 Orientation | 현재 Aligned Separable Gaussian 범위에서 지원 |
| 2 — Sampled Optical Field | Amplitude 및 Relative Phase를 재현할 수 있는 Complex Field Grid, Sampling, Coordinates, Units, Normalization | 향후 Data Contract |
| 3 — Measured / Simulated Field Import | 측정 Mode Data 또는 Electromagnetic Simulation Export, Reference-Plane Metadata, Provenance, Uncertainty | 향후 Import 및 적용성 검증 |

사용자 제공 데이터는 물리적 의미를 확인하고 검증된 모델의 입력 계약에 맞을 때 평가에
사용한다. 실측·시뮬레이션·공급사 자료·이론 가정·Synthetic 입력의 출처를 기록한다.
실제 데이터가 없으면 명시적으로 표시한 Theoretical Gaussian 또는 Synthetic 가정으로
개념을 탐색할 수 있다. 실제 제품의 Mode 특성은 해당 장치의 증거가 확보된 경우에만
보고한다. Intensity Image는 강도 증거로 취급한다. Complex Field에 필요한 Phase, 축,
기준면 등 필수 정보가 빠지면 해당 Actual-Design 계산은 **Uncomputed**로 유지한다.
[External Port Contract](EXTERNAL_PORT_CONTRACT.md)와
[Actual Input Readiness](M6G_WORKFLOW_ACCEPTANCE.md#actual-input-readiness-checklist)를 따른다.

## C. Optical Surface

장기 Surface 표현은 Plane, Sphere, Conic, Even-Order Asphere, XY Polynomial,
Zernike 기반 Surface, Higher-Order Freeform을 포함할 수 있다. Coordinate Frame,
Units, Coefficients, Aperture, Orientation, Reference Geometry를 명시한다.
Surface별로 네 수준의 근거를 기록한다.

1. **Data Representation** — Surface 식과 메타데이터를 해석할 수 있다.
2. **Geometric Visualization** — 지정 Aperture와 Frame에서 형상을 그릴 수 있다.
3. **Optical Propagation Support** — 해당 Surface와 Field를 평가하는 계산 경로가 있다.
4. **Independently Validated Applicability** — 해당 조건에서 계산 오차를 독립 Reference로 확인했다.

Data Contract에 임의의 최고 차수를 두지 않는다. 계산은 검증한 수치 방법, 수렴 기준 및
Model Domain 안에서만 수행한다. 현재 Local Quadratic Patch와 Vertex Optical Power의
역할은 [Physics 적용 범위](PHYSICS.md)를 따른다.

## D. Patent-Oriented Visualization

그림은 Optical Path와 설계 근거를 검토하고 기술적 차이를 전달하는 제품 기능이다.
현재의 2D Fold View, Mode Match 상세, HTML·JSON·A4 출력을 재사용하며 다음 범위를
단계적으로 확장한다.

| Figure | 표시할 정보 |
|---|---|
| Optical Mode | Source·Target Intensity, Relative Phase, Mode Mismatch, 지원되는 경우 도착 Field와 Target Field 비교 |
| Optical Architecture | Fixed Input/Output Port, Chief-Ray Path, Mirror/Lens와 배치, Beam Footprint, Package Constraint |
| Optical Surface | 2D Cross-Section, 필요한 경우 3D Surface, Sag Distribution, Curvature Variation, 고차항의 형상 기여 |
| Engineering Comparison | 추천과 대안의 Path Length, Beam Footprint, Mode Overlap, Model Validity, Sensitivity와 Trade-off |
| Patent-Oriented Concept | 단순화한 구조도, Component Reference Number, 주요 기하 관계, Alternative Embodiment, 기술적 차이를 설명하는 그림 |

향후 SVG 등 고품질 Vector Export를 지원한다. 그림의 라벨과 캡션은 계산 Geometry,
측정 정보, 명시 가정, 개념 Illustration을 구분하고, 해당 Input Snapshot 및 Candidate
기록을 가리킨다. 형상의 시각적 차이는 구조적 특징을 설명하는 자료다. 특허 신규성은
별도의 검토에서 판단한다.

## E. Explainable Engineering Recommendations

추천과 대안은 어떤 조건에서 생성됐는지, 무엇이 추천을 결정했는지, 어떤 Optical
Principle과 Model Domain이 이를 뒷받침하는지 설명한다. 서로 다른 구조와 절충점,
가정으로 남은 입력, 추가 검증이 필요한 Engineering Risk를 함께 표시한다.
예를 들어 현재 Path Length, Beam Footprint, Footprint–Curvature Guard 여유와 각종
Sensitivity는 의미와 적용 범위를 밝혀 비교한다. 실제 Assembly Tolerance, Package
Yield, Total Coupling은 각각의 검증 근거를 갖추기 전까지 **Uncomputed**다.

향후 Invention Disclosure는 후보 기술 특징, 구조적 차별점, Alternative Embodiment,
Engineering Evidence 요약, Figure Caption과 설계 설명을 후보별로 정리할 수 있다.
설명은 문서화한 비교와 증거에 근거하며 Patentability 결론은 별도 검토에 맡긴다.
