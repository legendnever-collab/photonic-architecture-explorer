# Photonic Architecture Explorer — Patent-Oriented Development Roadmap

[Product Charter](PRODUCT_CHARTER.md)와 [Product Vision](PATENT_ORIENTED_PRODUCT_VISION.md)에
따라 두 Fixed Port를 연결하는 개념을 탐색하고, 물리적 타당성과 후보 간 차이를 설명할 수 있는
Engineering Evidence를 단계적으로 확보한다. 각 Track의 번호는 내부 선후 관계를 나타낸다.
실제 Milestone은 당면한 설계 판단에 필요한 작업으로 한정한다.

## Track A — Physical Design & Validation

1. **M7-A SMF–Glass Waveguide Reference Case.** 비기밀 SMF와 Glass Waveguide 한 쌍의
   외부 기준면, 위치, 방향, 파장, 매질, Mode 및 출처를
   [M6-G Input Readiness](M6G_WORKFLOW_ACCEPTANCE.md#actual-input-readiness-checklist)에
   맞춰 확인한다. Actual Applicability와 개념 입력의 출처를 명확히 기록한다.
2. **Gaussian Applicability와 Two-Reflector 평가.** 확보한 Mode 증거로 기존 Domain을
   검사하고 지원되는 조건에 기존 Two-Port Design을 적용한다. 후보가 나오면 현재
   Ranking으로 추천과 대안을 비교한다. 필수 Field 증거가 부족하거나 Domain을 벗어나면
   근거와 Uncomputed 항목을 기록한다. M7-A는 이 Reference Case에 집중한다.
3. **Independent Field Validation.** 실제 Field가 확보되면 같은 Reference Plane의
   Gaussian Fit, Sampled Field 및 비교 대상 Metric에 대해 적절한 독립 Reference를
   선택하고 검증한다. Off-Vertex Field 평가는 별도 Reference 증거를 요구한다.
4. **Package와 Manufacturing.** 제공된 Envelope와 Keepout부터 확인한다. Body
   Clearance, 제조 제약, Assembly Tolerance와 Yield는 각 판단에 필요한 모델과 입력을
   확보해 순차적으로 평가한다. Total Coupling은 실제 손실 항목의 검증을 요구한다.

**PIC SSC → Glass Waveguide**는 장기 적용 대상으로 유지한다. SMF Reference Case의
결과는 해당 Port와 Model Domain에 귀속된다.

## Track B — Mode Input & Visualization

1. 기존 Gaussian 계산과 [Mode Match View](M5C_MODE_MATCH_VIEW.md)를 재사용해
   Source/Target Profile을 이해하기 쉽게 표시한다.
2. Source 기준면의 Profile과 Target 기준면의 도착 빔·Target Mode Intensity 및
   Relative Phase를 같은 비교 조건에서 설명한다. 현재 Plot과 Export를 기반으로 한다.
3. Complex Field Grid, Phase Convention, Sampling, Coordinates, Normalization을
   담는 Sampled-Field Data Contract를 정의한다.
4. 측정 및 Simulation Mode Import에 Reference-Plane Metadata, 출처, Uncertainty를 연결한다.
5. 독립 Reference와 수렴 검증을 통과한 범위에서 Field-Based Optical Evaluation을 지원한다.

초기 Visualization은 기존 모델의 계산값을 사용한다. 신규 Electromagnetic Solver에는
별도의 Engineering 필요성과 검증 근거가 필요하다.

## Track C — Surface Representation & Architecture Diversity

1. 현재 Quadratic Surface의 단면과 면 배치 표시를 개선한다.
2. Frame, Units, Coefficients, Aperture 및 Reference Geometry를 위한 Generalized
   Surface Data Contract를 정의한다.
3. Higher-Order Surface의 Sag, Curvature, 고차항 기여를 기하학적으로 표시한다.
4. 독립 Reference로 적용성을 확인한 Surface와 조건에 Optical Evaluation을 추가한다.
5. Lens–Mirror, Multi-Lens 및 Hybrid 등 새 Topology Family를 실사용 설계 질문에 맞춰
   하나씩 평가한다.

확장마다 지원하는 Geometry와 Field, 독립 Reference, 비교 Metric 및 수치 오차 기준을
먼저 명시한다. 표현·표시 확장은 해당 형상 검증을, 전파 모델 확장은 물리 오차와
수렴 검증을 요구한다. 검증된 영역만 Optical Result에 사용한다.

## Track D — Patent-Oriented Engineering Outputs

1. 기존 Concept Diagram에서 Fixed Port와 주요 경로·부품·기하 관계를 명료하게 표시한다.
2. Candidate Comparison Figure에 추천 사유와 대안의 측정 가능한 차이, 가정, Model Domain을 표시한다.
3. Surface와 Mode Profile Figure를 해당 Candidate 기록에 연결한다.
4. SVG 등 Vector Export에 필요한 Label, Component Reference Number와 Figure Caption을 보존한다.
5. 후보 기술 특징, Alternative Embodiment, Engineering Evidence와 설명을 묶어
   Invention Disclosure에 활용한다.

Figure와 Export마다 사용한 Input Snapshot ID 또는 SHA, Candidate ID, 입력 출처와
가정, 해당 수치 및 단위, Model Domain과 결과 상태를 추적할 수 있게 한다.
현재 HTML·Engineering JSON·A4의 Snapshot 및 Candidate ID 기록을 재사용한다.
개념 Illustration은 가정과 근거를 표시하고 해당 설계 기록에 연결한다.

## Milestone handoff

**M7-A가 다음 우선순위다.** Two-Port Workflow와 기존 검증을 기준으로 SMF–Glass Waveguide
Reference Case를 진행한다. Visualization이나 Data Contract 작업은 해당 Case에서 필요한
입력, 설계 판단 또는 결과 설명을 지원하는 작은 변경으로 제한한다. Generalized Optical
CAD는 이 로드맵의 Milestone 범위 밖이다.

향후 Work Order에는 참조할 Track과 그 작업이 지원하는 설계 판단을 적고, 검토 결과에
아래 세 질문의 답과 근거를 남긴다.

| 기준 | Milestone에서 확인할 질문 |
|---|---|
| Physics | 사용한 모델과 적용 범위가 문서화돼 있고 결과의 물리적 근거를 확인했는가? |
| Usability | 사용자가 두 Port를 입력하고, 추천 이유와 대안의 절충점을 이해할 수 있는가? |
| Patent Utility | 구조의 기술적 특징과 대안 대비 차이를 설명할 수 있고, 그림과 Engineering Evidence를 추적할 수 있는가? |

Milestone 범위와 변경 심사는 [Product Charter](PRODUCT_CHARTER.md) 및
[Repository Controls](../AGENTS.md)를 따른다.

## M7-R21 Addendum · 현재 Handoff

위 M7-A Handoff는 역사적 기록이다. 현재 실행 순서는 [NEXT_TASK](NEXT_TASK.md)의 첫 지시문을 따른다.
R6–R20의 1310 nm Reference는 고정 입력에 귀속된다. R21에서 계산 흐름·Reference와 현재 후보의 판정 근거를 Workspace에서 확인할 수 있다.
다음 Track A/B 병목은 1310 nm의 두 Port를 사용자가 열고 한 조건을 바꾼 뒤 동일한 Design 경로로 후보와 근거를 다시 받는 과정이다. 해당 흐름을 검증한 뒤 실제 사용 결과로 다음 우선순위를 정한다.
경계 일치형 HE11 독립 대조는 Facet 정확도가 설계 결정을 좌우할 때 재개할 수 있는 Physics Backlog로 유지한다.

## M7-R22 Addendum · Package 비교 우선순위

Tutorial에서 1310 nm 두 Port를 열어 Design하고 편집한 입력을 새 SHA로 재계산할 수 있다. 다음 Track A 과제는 같은 두 Port에서 Envelope 조건을 바꿔 후보의 광학 성능과 선언 Package 범위를 비교하는 것이다. R7–R9의 동결 조건에서 기존 기구 검사를 재현하고 사용자 입력으로 넓힐 수 있는 범위를 판단한다. [현재 Work Order](NEXT_TASK.md)

## M7-R23 · Package 비교 범위

원본 Example A에서 두 Synthetic Envelope를 비교하고 새 SHA에 귀속된 후보와 한계 여유를 확인할 수 있다. 같은 두 Port에서 사용자가 가진 Package 공간을 적용하는 것이 Track A의 남은 제약이다. Milestone 종료 시 다음 실행 지시문과 모델 추천을 대화에서 전달한다. [R23 설계 및 검증 기록](M7R23_ENVELOPE_COMPARISON.md)

## M7-R24 · 사용자 지정 World X 경계

원본 Example A에서 X min/max를 지정하고 R7 Synthetic Y/Z 조건에서 후보와 제한 면을 검토할 수 있다. 실제 Assembly 판단에서 필요한 기구 여유와 Gaussian Mode Overlap의 관계는 추가 검증이 필요하다. [R24 설계 및 검증 기록](M7R24_PACKAGE_WORLD_X.md)
