# Engineering Development 운영 정책

사용자가 승인한 M7-R21 Addendum이다. [Product Charter](PRODUCT_CHARTER.md), [장기 Product Vision](PATENT_ORIENTED_PRODUCT_VISION.md), [Roadmap](PATENT_ORIENTED_DEVELOPMENT_ROADMAP.md), [Repository Controls](../AGENTS.md)와 함께 적용한다.

## Engineering Ownership

사용자는 목적과 필수 제약을 제공한다. Agent가 Physics Model과 Solver Architecture, Candidate Generation·Optimization, Error Budget·검증 방법, Software Architecture, 우선순위, Milestone 및 Acceptance Criteria를 결정하고 그 근거를 기록한다. 사용자에게 일상적인 계산 순서나 광학 부품 수를 정하도록 요구하지 않는다. 주요 Product Scope·Architecture 변경, 외부 비용, 검증 기준 완화, Main 병합에는 별도 승인이 필요하다. 기존 Frozen Guard는 명시적 변경 승인과 새로운 검증 근거가 있어야 수정할 수 있다.

## 개발 순서

1. Physics Correctness와 Numerical Reliability를 확보한다.
2. 유효 후보를 실제로 생성하는 Architecture Generation을 개선한다.
3. 실제 사용자 입력의 편집과 Design 재계산을 연결한다.
4. 결과와 적용 범위, Evidence, Limitations를 설명한다.
5. Workspace, Visualization 및 재현 가능한 Report를 개선한다.
6. 설계 판단에 필요한 경우 추가 Solver Fidelity와 Architecture Family를 도입한다.

Fast Screening → Selective Wave Validation → Local Electromagnetic Verification 순서로 계산 비용을 배분한다. Gaussian / Ray / Reduced-Order Model로 후보를 줄이고 Diffraction, Vector 및 Nonparaxial Effects가 판정을 바꾸는 후보에 Wave 검증을 적용한다. 필요한 국소 문제에 Meep 또는 적합한 Maxwell Solver를 사용한다. Full-System 3D FDTD의 규모가 비현실적이면 Domain Decomposition이나 Hybrid Solver를 검토한다. Accuracy, Runtime Cost, Model Domain으로 경로를 선택한다. 이 단계적 통합은 장기 목표다.

## 언어와 Evidence 계약

UI, Tutorial, Engineering Report, 개발 결과 및 후속 지시문은 한국어 문장으로 쓴다. Variable, Equation, Solver, Mode, Physics Domain 및 Validation 용어는 표준 영어 표기를 유지한다. 기본 설명에서 설계 판단을 먼저 제시하고 수식·가정·오차·Artifact를 펼쳐 볼 수 있게 한다. 실측, 문헌, Simulated Reference와 Synthetic 가정을 식별한다. 각 판정은 해당 Input Snapshot, Candidate, Reference Plane과 Metric에 귀속한다. 입력이 바뀌면 결과의 동일성을 검증하고 근거가 없는 항목은 Evidence Insufficient 또는 Uncomputed로 표시한다. 정규화 Overlap, 실제 전달 Power, Package 및 Assembly 성능을 분리한다.

## Milestone 종료와 인수인계

완료 또는 Blocked 시 Agent가 아래 순서로 다음 Work Order를 작성한다.

1. 원격 Main, Draft Stack, 최신 HEAD, CI, Validation Artifacts를 확인한다. 실행한 검증, 미실행 검증, 실패 원인을 기록한다.
2. 구현 기능, 독립적으로 검증한 범위, 남은 Physics 및 Product 문제를 분리한다.
3. Charter에 비춰 실제 사용자가 할 수 있게 된 설계 판단과 아직 막힌 사용자 동작을 확인한다.
4. 그 판단을 가장 크게 개선할 병목 하나를 선택한다. 실패·중단한 연구와 재개 조건을 보존하고 Roadmap의 해당 Track만 갱신한다.
5. 아래 필드를 채운 실행 가능한 지시문을 **docs/NEXT_TASK.md 맨 위**에 저장한다. 과거 지시문은 History로 표시한다.
6. 새 대화에서도 시작 문서 네 개와 아래 원칙을 계승한다. 후속 지시문 작성까지 현재 Milestone에 포함한다. 다음 Milestone 실행과 Main 병합은 각각 사용자 승인을 기다린다.

| 필수 필드 | 작성할 내용 |
|---|---|
| Milestone ID, Mission, Objective | 해결할 Engineering Decision과 사용자 동작 |
| Recommended Execution Model | Sol 또는 Astra와 이유 |
| Repository, Verified Base SHA | 전체 SHA 및 Draft/병합 상태에 따른 시작 조건 |
| Related PR / CI / Evidence | 검증한 소스와 Artifact, 미확인 상태 |
| Recovery Procedure | 네 시작 문서, 재현할 입력과 결과 |
| Technical Implementation Scope | 기존 Normal Entry Point 및 재사용할 구성 |
| Physics / Engineering Acceptance Criteria | 입력·출력·Domain·Confidence·사용성의 판정 조건 |
| Numerical Error Budget / Stop Criteria | 해당 수치와 중단 동작, 해당 없으면 이유 |
| Regression Requirements | 기존 Physics, Workspace, Export, Windows 배포 검사 |
| Explicit Non-Goals | 현재 범위 밖의 Solver·기능·주장 |
| Deliverables / Remaining Uncomputed | 결과물, 근거, 잔여 공백 |
| Main Merge Approval Requirement | Draft 유지, 다음 실행 및 병합의 승인 경계 |

검증된 SHA를 자기 자신을 참조하는 Commit에 기록할 수 없으므로 실제로 확인한 이전 Implementation SHA와 CI를 적고, 인수 시점에 최신 문서 Commit의 Diff와 CI를 확인한다. CI 링크로 결과를 추정하지 않는다.

모든 지시문은 AI-Owned Engineering Decisions, Two-Port-First Workflow, Physics-Grounded Architecture Exploration, Evidence-Based Candidate Ranking, Minimal User Burden, 한국어 서술과 영어 Technical Terminology, Transparent Validation Status, Progressive Disclosure, Patent-Oriented Engineering Usefulness 및 재현 가능한 성능 근거를 계승한다.
