# M4-A — Actual Input Readiness / Applicability Decision

2026-11-10 KST. Base Main: `f2781ba2955b4ccda4202165c778cd3dc58a07ec`.
이 문서는 한 사례 **M4A-001: PIC SSC ↔ Glass Waveguide**의 입력 준비 판정이다.
실제 수치가 제공되지 않았으므로 실물 성능·실제 적용성 평가 완료를 뜻하지 않는다.

## 결과

**AwaitingInput. Actual Applicability = Uncomputed.**
이번 지시문과 기존 Repository에는 이 사례에 사용할 사용자 제공 비기밀 수치가 없다.
기존 `examples/external_ports_unprovided.json`을 수정하지 않고 `evaluate_external`에
그대로 전달했다. JSON의 36개 physical record는 모두 null / unprovided다.
두 Reflector의 nominal `design.reflectors`와 외부 매질 선언도 보완이 필요하다.
36은 누락 Inventory 수이며, 36개를 모두 동시에 채워야 한다는 뜻은 아니다.

M1/M3-A의 Synthetic 값, 다른 프로젝트의 Fiber Benchmark, 문헌의 일반값을
실제 입력으로 가져오지 않았다. Missing Phase를 flat phase로, 모르는 keepout을
빈 목록으로, 미상 loss를 0으로 채우지 않았다. 기존 UI/Solver/Optimizer는 변경 없다.

기계 판독 결과: `results/m4a_001.json`. 입력 파일 SHA256:
`924c68622e4549c35ab45020ea2a5d268d04751141320235e50f4391261c2ed0`.

| 판정 항목 | 현재 결과 | 근거와 한계 |
|---|---|---|
| Input Contract | Uncomputed | 첫 중단은 `wavelength_m`: value not supplied |
| Geometry | Uncomputed | 고정 Port의 Position/Direction 및 두 nominal Reflector가 없음; trace 미실행 |
| Model Domain | Uncomputed | Mode/Phase/매질/경로가 없어 적용 범위 검사 미실행; Outside Domain 판정도 아님 |
| Approximate Overlap | Uncomputed / null | Gaussian 성능 계산을 실행하지 않음 |
| Design Bounds | Uncomputed | 명시한 제약과 nominal candidate가 없음 |
| Envelope Geometry / Package | Uncomputed | Volume/Frame/Keepout/Body/Clearance 미제공; Full Clearance는 별도 미검증 |
| Physical Losses / Total Coupling | Uncomputed / null | 실제 계면·Coating·Polarization·Scatter 등 미계산 |
| Actual Applicability | Uncomputed | 입력 누락과 실제 Field/Package의 독립 검증 부족 |

Adapter는 첫 누락에서 중단한다. 이 첫 중단이 유일한 누락이라는 뜻은 아니다.
`results/m4a_001.json`은 전체 누락 Inventory와 실제 Adapter Result를 구분해 보존한다.

## 기존 양식에서 필요한 입력

새 Input Form을 만들지 않는다. `EXTERNAL_PORT_CONTRACT.md`의 물리적 의미와
`M3A_ADAPTER.md`의 실행 형식을 그대로 사용한다. 각 record의 value / unit /
provenance / source / uncertainty를 보존하며 출처가 있는 비기밀 값만 채운다.

| 구분 | 필요한 명시값 | 기존 JSON 경로 / 형식 |
|---|---|---|
| 공통 Optical 조건 | Vacuum wavelength, homogeneous external ambient n | `wavelength_m`, `ambient_index`; 양수 finite, 단위 m / 1 |
| 매질의 의미 | Guided effective index가 아닌 external ambient임을 선언 | `ambient_index.quantity = external_ambient_refractive_index` |
| Source / Target Geometry | 고정 위치, 도착/출사 전파 방향, 공통 sagittal basis | 각 `position_m`, `propagation_direction`, `sagittal_axis`; m / unit vector |
| External Plane | 공통 Frame ID, plane ID/side/origin/normal | 각 `reference_plane`; origin=Position, normal=Propagation Direction |
| 각 Port의 Mode | **MFD_t/s + C_t/s** 또는 **ordinary complex q_t/s** 중 하나 | `mfd_ts_m` + `wavefront_curvature_ts_per_m`, 또는 `complex_q_ts_m` |
| Mode 의미 / 근거 | MFD 정의, Field/fit 출처, Scalar Polarization 가정 | 각 `mode_evidence`, `polarization`; 실제 Gaussian 적합성은 별도 근거 필요 |
| 두 평가 대상 Reflector | Vertex, illuminated normal, principal curvatures, half aperture | `design.reflectors[0/1]`에 4개 record씩; Source/Target를 자동으로 맞추지 않음 |
| Surface 형식 | 평가할 면의 명시 prescription | `reflectors[0/1].surface_prescription`; 현 지원은 quadratic_patch |
| Design 제약 | Position/Normal/Curvature/Aperture 범위 | `reflectors[0/1]`의 기존 bounds/cone record |
| Package | 공통 Frame, Available Volume, Keepout, Body Envelope, Clearance | `package.*`, 각 `body_envelope`; 현재 world AABB diagnostic만 지원 |

MFD는 해당 External Plane의 1/e² **intensity diameter**, C는 Wavefront Curvature
1/R이다. Mirror Surface Curvature κ와 구별한다. Phase가 없으면 waist로 가정하지 않는다.
Target 방향은 도착하는 빛의 방향이며 device outward normal이 아니다.
FWHM / reduced q / mm를 값의 의미 확인 없이 대입하지 않는다.

기존 M25 blank는 M3-A에서도 지원한다. 다만 값만 채우는 것으로 완성되지 않는다.
`ambient_index.quantity`와 nominal `design.reflectors`는 M3-A 실행 형식에 따라
명시적으로 추가해야 한다. 여기에 필요한 8개 nominal record와 누락 구조 경로도
JSON 결과에 기록했다. 이 문서는 값을 새로 선택하거나 채운 실행용 Fixture가 아니다.

Reflector nominal은 평가 대상 **설계 변수**이며 실제 측정값일 필요는 없다. 사용자가
선택한 후보/가정과 출처를 명시할 수 있다. 고정 Port Boundary Conditions와 구별한다.
이번 범위에는 후보 자동 생성이나 Optimizer가 없어 candidate가 없으면 Geometry는
계산할 수 없다. Port를 이동하거나 Target Mode를 fit하는 방법으로 보완하지 않는다.

## 입력 Gate를 나누어 적용

1. **Port 입력 확인**: External Plane/Frame/Mode 표현·출처·매질 의미를 확정한다.
   MFD+C와 q는 대안이며, 중복 제공 성분은 Adapter의 일치 검사를 받아야 한다.
2. **Nominal Optical 평가**: 고정 Ports + 정확히 두 explicit quadratic Reflector를
   명시하고 기존 Adapter를 실행한다. Geometry와 Gaussian Domain을 별도로 확인한다.
3. **Engineering 제약 평가**: Bounds/Package를 별도로 검사한다. 이 정보만 누락되고
   Optical/Model이 유효하면 조건부 Approximate Overlap은 가능하다. 명시 Bounds/Package
   Fail에서는 Published Overlap이 보류된다. 이를 입력 필수성 혼동으로 바꾸지 않는다.
4. **실제 성능 주장**: 입력이 모두 있어도 Actual Applicability/Total Coupling은
   자동 Pass되지 않는다. 실제 Complex Field의 Gaussian fit, Finite Field/계면/손실과
   Package에 대한 독립 Reference 범위를 따로 확보해야 한다.

## Astra 검토가 필요한 조건

현재는 입력 누락이므로 **Astra Physics 확장 검토를 시작할 근거가 없다**.
기존 구현에서 결과를 얻지 못한다는 사실만으로 모델 밖이라고 판정하지 않는다.
아래는 사용자 입력이 제공된 뒤의 조건부 의사결정이며 현재 사례의 계산 결과가 아니다.

| 관찰된 근거 | 우선 조치 | Astra에서 검토할 최소 범위 |
|---|---|---|
| 누락값, 단위/Frame/방향/출처 오류 | 기존 Contract에 맞게 입력 보완 | 필요 없음 |
| Fixed-Port Geometry Fail | Direction/Normal/명시 candidate와 반사 경로 확인 | 올바른 입력에서도 구조 변경이 필요할 때만 별도 범위 결정 |
| Gaussian Domain Fail | frozen guard와 실패 사유 보존 | 문제를 일으킨 Mode·경로 한 사례의 모델/외부 Reference 선택 |
| Skew/rolled/nonseparable Field | 기존 scalar/separable 결과 사용 보류 | 축 결합·좌표/Field 표현 및 독립 검증 가능성 |
| Off-vertex 성능·공차 주장이 필요 | 기존 M2 결과와 미계산 Gaussian handoff 보존 | 한 perturbation의 Field handoff와 Mode Projection 검증 경로 |
| Envelope Pass 이후 Full Clearance가 필요 | AABB 결과와 미계산 범위 구분 | Finite Beam–Backing/Support 판정의 필요한 Geometry/Reference |
| 실제 Coupling/Polarization/Coating loss가 필요 | Approximate Overlap과 실제 효율 분리 | 해당 Interface/Field/Loss의 외부 검증 경로와 오차 예산 |

현재 frozen guard는 divergence ≤0.1 rad, incidence ≤70°, 3w projected
footprint×|κ| ≤0.15, cumulative aperture-tail screening ≤1e-6 등이다.
이는 기존 모델의 Screening 기준이며 실제 사례의 입력값·성능 보증·오차 상한이 아니다.
입력이 없으므로 이 사례가 기준 안/밖인지 계산하지 않았다. Guard를 완화하지 않는다.
필요 시 Astra는 실패 원인·성공/중단 기준·계산 예산부터 고정하며 새 범용 Solver나
Maxwell 구현을 자동으로 시작하지 않는다.

## Recovery / 재현과 보존

Main은 제시된 Base와 동일하다. PR #1–#6은 이미 Main에 병합되어 있으며,
Main CI 42785703605와 세 Artifact의 SHA/유효 상태를 복구했다.
로컬 기존 60 Tests 및 M1/M3-A Gate를 재실행해 PASS를 확인했다.
M4-A는 문서와 기존 Blank의 실행 결과만 추가한다. 새 Test나 Engine/Adapter/UI
변경은 없다. 이전 Physics Tests / Fixtures / Benchmarks도 그대로다.
Main 병합과 다음 Checkpoint의 자동 실행은 하지 않는다.

실제 Adapter 호출:

```bash
PYTHONPATH=src python -m photonic_architecture_explorer.external examples/external_ports_unprovided.json --output /tmp/m4a-external.json
```

이 실행의 exit 0은 진단 실행 성공이며 설계/실제 적용성 Pass가 아니다.
별도 감사 명령으로 Blank의 모든 record를 순회하고 `value is None` /
`provenance == unprovided` 36개, `design` 및 ambient quantity 부재를 확인했다.
입력 및 읽은 Engine/Contract 파일 SHA256을 `results/m4a_001.json`에 남겼다.
최종 Draft PR의 정확한 HEAD와 CI/Artifacts는 PR Description과 채팅에서 확인한다.

## 다음 실행 조건

사용자가 사용할 비기밀 값과 평가 대상 candidate를 명시할 때 M4A-001을 갱신한다.
부분 입력도 받을 수 있으며 확정된 항목만 보존하고 나머지는 Uncomputed로 유지한다.
새 입력이 없으면 이 누락 표와 기존 양식을 재사용하고 입력 대기를 유지한다.
실제 회사 기밀 자료의 외부 제공은 요청하지 않는다.
