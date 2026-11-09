# Photonic Architecture Explorer

고정된 두 Optical Port를 두 curved reflector로 연결하는 작은 Python Engineering Tool.
M1은 **Synthetic external Gaussian field의 paraxial feasibility**를 평가합니다.
실제 PIC SSC/Glass Waveguide의 총 Coupling Efficiency나 특허 신규성은 평가하지 않습니다.

## 실행

Python 3.11 이상. 계산 엔진은 Standard Library만 사용합니다.
독립 Fresnel/수치 검증은 NumPy 2.x를 사용합니다.

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

- [Frozen Benchmark](docs/M1_BENCHMARK.md), [Physics assumptions](docs/PHYSICS.md)
- [검증 방법·결과](docs/VALIDATION.md), [재사용 검토](docs/REUSE_REVIEW.md)
- [MVP 범위](docs/MVP_SCOPE.md), [M2 최소 제안](docs/NEXT_TASK.md)
- `src/photonic_architecture_explorer/`: Gaussian, Geometry, classified solver, benchmark CLI
- `examples/m1_001.json`: 고정 입력; `results/m1_001.json`: 각 면의 beam parameters 포함
- `tests/test_m1.py`: 독립 Reference kernels와 invalid-domain 검증

Source/Target Port의 direction은 모두 **Source→Target으로 전파하는 방향**입니다.
Target의 outward-facing normal로 해석하면 안 됩니다. Mode radii는 MFD/2입니다.
M1에서는 Port의 medium을 homogeneous external ambient로 정의합니다.

UI, topology synthesis, freeform inverse design, Maxwell solver, 특허 scoring,
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
UI는 아직 구현하지 않았습니다.
