# Photonic Architecture Explorer

고정된 두 Optical Port를 두 curved reflector로 연결하는 작은 Python Engineering Tool.
M1은 **Synthetic external Gaussian field의 paraxial feasibility**를 평가합니다.
실제 PIC SSC/Glass Waveguide의 총 Coupling Efficiency나 특허 신규성은 평가하지 않습니다.

## Windows 사용자 검토 패키지 — M7-F

[Windows Review CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/workflows/windows-review.yml)의 성공한 실행에서
`m7f-windows-review-package` Artifact를 받습니다. Artifact 안의
`Photonic-Architecture-Explorer-M7F-Windows-x64.zip`을 전체 압축 해제한 뒤
`Start-Photonic-Architecture-Explorer.cmd`를 실행하세요. Python/NumPy/SciPy가 포함됩니다.
[검토 절차·검증 범위](docs/M7F_INTEGRATED_WINDOWS_REVIEW.md)를 참고하세요.

## 화면에서 두 Port로 설계 — M5-B

```bash
python -m pip install -e .
pae-workspace
```

[로컬 Workspace](http://127.0.0.1:8765)에서 두 Port를 입력하고 **Design**을 실행합니다.
후보와 2D Projection을 선택하고 결과 HTML·JSON을 각각 저장할 수 있습니다.
[추천 정책](docs/M6C_ENGINEERING_RECOMMENDATION.md)은 같은 Overlap 구간의 짧은 경로를 기본으로 제시하고
Beam Footprint 및 Gaussian 모델 한계 여유가 더 나은 후보를 대안으로 표시합니다.
[Reflector Placement Sensitivity](docs/M6D_REFLECTOR_PLACEMENT.md)에서 각 반사면의 이동·회전에 따른
Fixed Target 기준면의 Chief-Ray 응답을 비교할 수 있습니다.
선택 후보의 [Mode Match 상세](docs/M5C_MODE_MATCH_VIEW.md)에서 도착 빔과 Target의
강도·상대 Phase, Normalized Mode Overlap 및 Mode Mismatch Loss를 비교합니다.
[Target 기준면 민감도](docs/M5D_CANDIDATE_SENSITIVITY.md)에서 같은 위치·각도 오차를
적용했을 때 추천과 대안의 Nominal 대비 손실을 비교합니다.
**후보 요약 인쇄**로 현재 선택의 [A4 검토 요약](docs/M5E_CANDIDATE_REVIEW_SUMMARY.md)을
저장합니다. 같은 화면은 오프라인 HTML에서도 열 수 있습니다.
[입력 단위·재현·검증 범위](docs/M5B_TWO_PORT_WORKSPACE.md)를 참고하세요.

## 두 Port에서 자동 Design — M5-A

Reflector 값을 입력하지 않고 개념 설계 후보를 생성합니다.

```bash
python -m pip install -e '.[test]'
pae-design examples/m5a_two_ports.json --output-dir results/my-design
```

생성된 `results/my-design/design.html`을 브라우저로 열면 됩니다.
[미리 생성된 Read-only Report](results/m5a/design.html)와
[후보별 JSON](results/m5a/design.json), [검증·한계](docs/M5A_AUTONOMOUS_DESIGN.md)를 제공합니다.
Synthetic 예제에서 유효 후보 56개, 대표 3개. 실제 Package와 Total Coupling은 Uncomputed입니다.
Missing Phase나 Domain Fail은 임의 보완하지 않습니다.

[M7-A SMF–Glass Waveguide Reference Case](docs/M7A_SMF_GLASS_WAVEGUIDE_REFERENCE.md)에서
1550 nm 공개 Mode Width를 사용한 개념 입력과 기존 가드의 판정 근거를 확인할 수 있습니다.
[M7-B Near-Match 결과](docs/M7B_GUARDED_NEAR_MATCH.md)와
[M7-C Workflow 통합 Prototype·후속 계획](docs/M7C_NEAR_MATCH_WORKFLOW.md)을 제공합니다.
[M7-D Background Workflow](docs/M7D_BACKGROUND_WORKFLOW.md)에서는 exact-q 후보가 없을 때
같은 **Design** 동작으로 Near-Match를 자동 탐색합니다. `SMF–Glass Proxy` 예제로 확인할 수
있으며, 진행 표시·취소·입력 변경 시 결과 무효화와 기존 HTML/JSON/A4 출력을 지원합니다.
전체 탐색은 수분 걸릴 수 있습니다. 이 Proxy는 공개 Width와 가정 Phase를 사용하며
실제 Device Field, Assembly Tolerance 및 Total Coupling은 Uncomputed입니다.

[M7-R1 Mode Reference Library](docs/M7R1_MODE_REFERENCE_LIBRARY.md)는 1310/1550 nm SMF와
공개 LDW·IOX의 Mode Width, Intensity Image 출처 및 측정 조건을 제공합니다.
[Offline Mode Comparison](results/m7r1-mode-library.html)에서 Gaussian Intensity
Preview와 문헌 근거를 확인할 수 있습니다.
Workspace의 **SMF–Glass Mode Reference**에서 1550 nm Mode를 비교하고 1310 nm
입력 준비 상태를 확인할 수 있습니다. [M7-R2 사용법](docs/M7R2_REFERENCE_PORT_HANDOFF.md)

## 실행

Python 3.11 이상. Gaussian/Geometry 계산 커널은 Standard Library를 사용합니다.
앱 설치에는 Near-Match 탐색과 독립 검산용 NumPy 2.3.5 / SciPy 1.17.0이 포함됩니다.

```bash
python -m pip install -e '.[test]'
python -m photonic_architecture_explorer.benchmark examples/m1_001.json --output results/m1_001.json
python scripts/validate.py
```

설치 없이 실행하려면 `PYTHONPATH=src`를 설정합니다.
`pae-benchmark examples/m1_001.json`도 지원합니다.

## M1 결과

1310 nm, ambient n=1, 1–2–1 mm 경로, 두 번의 45° 반사.
Source/Target 모두 waist radii (t,s)=(8,12) µm. 모든 비교에서 Port는 고정됩니다.

| 조건 | Target plane radii (t,s), µm | Normalized Mode Overlap | Mode mismatch, dB |
|---|---:|---:|---:|
| Flat | 208.646, 139.512 | 0.0130192 | 18.8541 |
| Curved, independent principal curvatures | 8.000, 12.000 | 1.0000000 | 0.0000 |
| Spherical vertex-curvature control | 25.835, 28.132 | 0.3889688 | 4.1009 |

Curved 조건은 유효 초점거리 1 mm의 이상적인 4f Relay로 구성했습니다.
기하학적 존재와 Curvature Effects를 검증하는 synthetic positive control이며,
설계 최적화 결과나 실제 제작 성능이 아닙니다. 특히 작은 실제 SSC Mode가
paraxial domain 밖이면 이 결과를 적용할 수 없습니다.

| 분류 | M1 상태 | 의미 |
|---|---|---|
| Geometry | Pass | Fixed Port closure, reflection law, quadratic-patch chief-ray interception 검사 |
| Gaussian domain | Pass | Coplanar/separable, divergence/footprint/aperture guards |
| Gaussian transformations | Pass | Analytical, sampled Fresnel, differential surface-ray reference tests |
| Normalized Mode Overlap | Pass | 모델 안의 scalar overlap 계산 완료; 요구 효율 합격이라는 뜻 아님 |
| Physical losses / total coupling | Uncomputed | Coating, interfaces, polarization, roughness, aberration 제외 |
| Fabrication / assembly | Uncomputed | 실제 면형상, body clearance, process/tolerance 입력 없음 |

19개 test methods와 parameterized subcases를 실행했습니다. CI는 Draft PR의
Checks에서 확인하며, 로컬 검증을 원격 CI 성공으로 대체해 표현하지 않습니다.

## 문서와 구조

- [Product Charter](docs/PRODUCT_CHARTER.md), [Patent-Oriented Product Vision](docs/PATENT_ORIENTED_PRODUCT_VISION.md), [Development Roadmap](docs/PATENT_ORIENTED_DEVELOPMENT_ROADMAP.md)
- [Frozen Benchmark](docs/M1_BENCHMARK.md), [Physics assumptions](docs/PHYSICS.md)
- [검증 방법·결과](docs/VALIDATION.md), [재사용 검토](docs/REUSE_REVIEW.md)
- [MVP 범위](docs/MVP_SCOPE.md), [M2 최소 제안](docs/NEXT_TASK.md)
- `src/photonic_architecture_explorer/`: Gaussian, Geometry, classified solver, benchmark CLI
- `examples/m1_001.json`: 고정 입력; `results/m1_001.json`: 각 면의 beam parameters 포함
- `tests/test_m1.py`: 독립 Reference kernels와 invalid-domain 검증

Source/Target Port의 direction은 모두 **Source→Target으로 전파하는 방향**입니다.
Target의 outward-facing normal로 해석하면 안 됩니다. Mode radii는 MFD/2입니다.
M1에서는 Port의 medium을 homogeneous external ambient로 정의합니다.

Topology synthesis, freeform inverse design, Maxwell solver, 특허 scoring,
회사 기밀 데이터는 포함하지 않습니다. Main 병합에는 사용자 승인이 필요합니다.

## M2 bounded diagnostics

`python scripts/validate.py` also writes `results/m2_001.json`.
[Contract](docs/M2_CONTRACT.md) and [results/limits](docs/M2_RESULTS.md) define
8 individual curvature perturbations, 12 individual placement perturbations,
and a 27-ray finite-wavefront diagnostic per Flat/Curved control. Independent
Newton-surface references verify exact patch intersections. 26 tests pass.

개별 곡률 ±1%의 paraxial overlap은 99.944–99.987%입니다. 반면 Curved의 2w
finite fan은 linear reference에 비해 최대 2.680 µm의 위치 차이를 보입니다.
이는 field coupling 또는 full-aperture worst case가 아닙니다. Placement별
Gaussian overlap 및 actual SSC 적용성은 Uncomputed로 유지합니다.

## M2.5 external Port applicability gate

[External input contract](docs/EXTERNAL_PORT_CONTRACT.md)과
[Physics applicability / M3 readiness](docs/M25_ASSESSMENT.md)를 추가했습니다.
실제 Port/Package 입력은 전부 미제공이므로 실제 Applicability는 Uncomputed입니다.
Path B는 최종 Engineering 목표 대비 최소 확장 경로이며 실물 성능 판정이 아닙니다.
`python scripts/validate.py`가 `results/m25_001.json`도 생성합니다.
추가 per-Port check는 divergence만 검사하며 full external adapter는 M3-A 범위입니다.
[다음 개발 지시문](docs/NEXT_TASK.md)을 참조하세요.

## M3-A external adapter

[실행 가능한 Input/Result Contract](docs/M3A_ADAPTER.md)를 통해 기존 Physics Engine을
호출합니다. 설치 후 `pae-external`을 사용하거나 다음과 같이 실행합니다.

```bash
PYTHONPATH=src python -m photonic_architecture_explorer.external examples/m3a_synthetic.json
```

MFD+Phase / Complex q, Fixed Ports, Provenance, Bounds 및 제한된 AABB 검사를 지원합니다.
Overlap은 Approximate normalized scalar diagnostic입니다. Envelope 검사가 통과해도
Full Package Clearance·Actual Applicability·Total Coupling은 Uncomputed입니다.
M3-B Inspector에서 이 Adapter를 호출합니다.

## M3-B minimal 2D Inspector

```bash
python -m photonic_architecture_explorer.inspector
python -m photonic_architecture_explorer.inspector --serve
```

첫 명령은 `results/m3b-inspector.html` 정적 Review를 생성합니다. 두 번째 명령은
`http://127.0.0.1:8765`에서 입력 수정 후 Python Adapter로 재평가합니다.
[실행·검증·User Review](docs/M3B_INSPECTOR.md)를 참조하세요.
Fixed Ports·두 Quadratic Surfaces·검증된 Chief Path·명시 AABB의 2D Projection과
결과 상태를 표시합니다. Static HTML은 Case/Projection 선택이 가능한 Read-only
Snapshot이며, Actual Applicability와 Total Coupling은 Uncomputed입니다.
