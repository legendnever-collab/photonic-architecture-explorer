# M3-A — External Adapter / Fixed-Port Result Contract

2026-11-10 KST. Base PR #3, 17bd1ad6bfa5715f6371fe0e41f52a6d1a93e199.
Recovery 및 고정 범위: M3A_CONTRACT.md. Main/PR #1/#2/#3은 변경·병합하지 않았다.
실제 Port 데이터는 미제공이며 이번 예제는 모두 Synthetic이다.

## 실행 / API

```bash
PYTHONPATH=src python -m photonic_architecture_explorer.external examples/m3a_synthetic.json --output results/external.json
PYTHONPATH=src python -m photonic_architecture_explorer.external examples/external_ports_unprovided.json
PYTHONPATH=src python scripts/validate.py
```

설치 후 `pae-external`도 지원한다. CLI exit 1은 Input/Geometry/Domain/Bounds/Package
중 Fail이 있다는 뜻이다. Exit 0은 실행 성공이며 설계 합격이 아니다.
Uncomputed를 포함한 정상 진단도 exit 0일 수 있다.

`adapt_external(document)`는 frozen AdaptedDesign을 반환한다. 구성은 immutable
Source/Target, 두 Reflector, 공통 Frame ID, 전체 입력의 immutable JSON snapshot이다.
`evaluate_external(document)`는 JSON-safe classified result를 반환한다.
기존 evaluate/Port/Reflector/Gaussian을 재사용하며 UI와 새 Optical Solver는 없다.

## 실행 가능한 입력 형태

기존 M25-1 blank sheet는 수정하지 않았다. M25-1도 읽지만 부족한 입력은 Uncomputed다.
실행 예제 examples/m3a_synthetic.json은 M1-001 external fields와 명시적으로 선언한
Synthetic Package 가정을 사용한다. 실제 PIC/Glass 사양을 가정한 값이 아니다.

물리 record는 value/unit/provenance/source/uncertainty를 보존한다. 제공값에는
비어 있지 않은 출처 문자열 source가 필요하다. Measured/simulated/synthetic 등의
provenance는 결과 검증 상태와 별개다. Uncertainty는 metadata로 보존하며
propagation/yield는 계산하지 않는다. 미제공 값은 null/unprovided로 유지한다.

| Field | 실행 가능한 value 형태 | canonical unit |
|---|---|---|
| wavelength_m / ambient_index | finite positive real; n에는 quantity도 명시 | m / 1 |
| Port position / propagation_direction / sagittal_axis | world 3-vector; d와 s는 unit, s⊥d | m / 1 / 1 |
| mfd_ts_m / wavefront_curvature_ts_per_m | [t,s], MFD=1/e² intensity diameter, C=1/R | m / m^-1 |
| complex_q_ts_m | [[Re(q_t),Im(q_t)],[Re(q_s),Im(q_s)]], ordinary q | m |
| reference_plane | {id,frame_id,side:'external',origin_m:[...],normal:[...]} | plane |
| polarization | {treatment:'scalar_ignored',jones_ts:[[re,im],[re,im]]}; Jones는 선택 입력 | 1 |
| mode_evidence | {kind:'synthetic_gaussian'/'gaussian_assumption'/'complex_field_fit',...} | evidence |
| design.reflectors[0/1] | vertex_m, illuminated_normal, principal_curvature_ts_per_m, half_aperture_ts_m 각각의 record | m / 1 / m^-1 / m |
| reflectors[0/1].surface_prescription | 'quadratic_patch' | model |
| vertex_bounds_m | [[xmin,ymin,zmin],[xmax,ymax,zmax]] | m |
| principal_curvature_bounds_per_m / half_aperture_bounds_m | [[t_min,t_max],[s_min,s_max]] | m^-1 / m |
| normal_constraints | {axis:[nx,ny,nz],max_angle_rad:α} | rad |
| package.frame_id | Port reference planes와 같은 공통 Frame ID | frame |
| available_volume / body_envelope | {type:'aabb',min_m:[...],max_m:[...]}; 선택 frame_id는 공통 Frame과 일치해야 함 | m |
| keepout_bodies / required_clearance_m | 명시 AABB 목록 / finite nonnegative scalar | m / m |

Top-level coordinate_convention은 기존 blank sheet와 같은 상수를 요구한다.
모든 값은 하나의 right-handed world frame에 둔다. 자동 Frame Transform은 없다.
서로 다른 Frame, Plane origin≠Port position, Plane normal≠Propagation Direction을
거부한다. Target d는 도착하는 빛의 방향이며 outward device normal과 구별한다.

ambient_index record에는 `quantity:'external_ambient_refractive_index'`가 필요하다.
quantity 미지정은 Uncomputed, guided_effective_index 등은 Fail이다.
수치 n만으로 실제 Ambient인지 Guided Index인지 판별할 수 있다는 뜻은 아니다.
공통 n·λ0만 지원하며, Port별 별도 n/λ0 등 지원하지 않는 Optical Field 이름은 거부한다.

Canonical SI 표기와 M25 blank sheet의 알려진 unit 설명문만 허용한다.
mm/µm/FWHM/reduced-q를 암묵적으로 변환하지 않는다. Direction은 norm 오차 1e-10 이내의
Unit Vector만 허용하며 기존 constructor의 정규화는 그 수치 범위 안에서 수행된다.
MFD/q 일치 허용치는 relative 1e-9, MFD absolute 1e-15 m, C absolute 1e-8 m^-1다.
MFD+C 또는 q 중 하나면 충분하다. 추가한 중복 성분은 일부만 있어도 일치성을 확인한다.
Phase/q가 없으면 C=0으로 대체하지 않는다. 구간값을 평균해 Nominal로 바꾸지 않는다.

## Geometry / Envelope 범위

명시된 Vertex로 고정 Source→M1→M2→Target 경로를 기존 Engine에서 검증한다.
Port를 이동하지 않는다. 정확히 두 Reflector, 같은 Incidence Plane에 정렬된
Separable Axes만 지원한다. Bounds는 Nominal 값의 Inclusive Interval 검사다.
Normal Cone은 Unit-Vector Chord로 안정적으로 검사한다(direction tolerance 1e-10).
Bounds는 Optimization이나 Assembly Tolerance가 아니며 미제공 Bounds는 Uncomputed다.

Quadratic Patch h=(κ_t u²+κ_s v²)/2, |u|≤a_t, |v|≤a_s의 World 좌표 각 성분은
두 독립 1D Quadratic의 합이다. 각 구간의 양 끝과 내부 Stationary Point로
**Surface 전체의 정확한 Coordinate AABB**를 구한다. Vertex만 검사하지 않는다.
Total Reflector+Support Envelope가 Surface 전체를 포함하고, Available Volume이
Patch와 Envelope를 포함하는지 확인한다.

선언된 AABB 쌍은 Euclidean Box Distance, Volume Boundary는 좌표별 Margin으로
Required Clearance를 검사한다. Closed Envelope 사이의 접촉도 거부한다.
Keepout은 명시 AABB만 지원한다. Envelope–Keepout 거리에는 지정 Clearance를 적용하고,
Chief-Ray Segment–Keepout에는 Slab Intersection으로 Centreline 교차만 검사한다.
Envelope는 보수적 제약이므로 중복 Fail이 실제 Body 충돌의 증명은 아니다.

지원하지 않는 Mesh/Solid/Transform이나 누락 Envelope는 Uncomputed다.
공통 Frame을 선언하지 않으면 좌표를 비교하지 않는다. 확인된 Package 제약 위반은 Fail이다.
**모든 Envelope Check가 Pass여도 package_feasibility는 Uncomputed**다.
Finite Beam–Mirror Backing/Support 거리, 의도한 Mirror 접촉, 제조 Clearance와
Thermal/Mechanical 변형을 평가하지 않았기 때문이다.

## Result 상태와 거부 조건

| Result Group | 의미 |
|---|---|
| input_contract | Pass / Uncomputed / Fail; 입력 구조와 물리량의 명시성 검사 |
| geometry | 기존 Engine의 Fixed-Port Chief-Ray / Patch Closure |
| model_domain | 기존 Coplanarity / Divergence / Incidence / Footprint / Aperture Guards |
| design_constraints | 명시 Nominal Position / Curvature / Aperture / Normal Bounds |
| gaussian_mode_matching | 계산 가능하면 Approximate; Scalar Paraxial Normalized Overlap |
| package_feasibility.envelope_geometry | 선언된 AABB 범위의 Pass / Uncomputed / Fail |
| package_feasibility | 확인된 제약 위반은 Fail, 그 외에는 이번 범위에서 Uncomputed |
| physical_losses / fabrication / actual_applicability | Uncomputed, total_coupling=null |

Optical Input 부족·오류, Geometry/Domain Fail에서는 normalized_mode_overlap=null이다.
명시 Bounds/Package Fail에서도 Published Overlap을 보류한다. Package 정보나 Bounds만
부족하고 Optical Input/Model이 유효하면 조건부 Approximate Diagnostic은 계산한다.
그 결과를 제품 실현 가능성이나 실제 Coupling Efficiency로 해석하지 않는다.

input_snapshot은 모든 record를 JSON으로 복제·보존한다. Evaluated Ports도 별도로
출력하여 입력 일치와 Target 불변을 추적한다. Source/Target Mode를 계산 Output에
맞추지 않는다. Invalid Input으로 조기 종료하면 input_contract의 path/reason을
반환하며 Optical Performance 수치를 만들지 않는다.

## 검증 결과

기존 32 tests 재실행 Pass, 신규 17 methods(subcases 포함)를 추가하여 최종 49 tests.
M1/M2/M2.5의 Kernels, Tests, Fixture, Frozen Guards와 기존 Benchmark JSON은 변경 없다.
Synthetic 예제의 Geometry/Domain/Bounds는 Pass, Normalized Overlap=1(Approximate),
Envelope Checks는 Pass, Full Package/Actual Applicability/Total Coupling은 Uncomputed다.
기존 M1 Ideal Relay를 External Input으로 같은 범위에서 재현한 결과다.

독립 Reference: q=z+i zR에서 직접 구한 Non-Waist w/C, 양·음 Phase Curvature,
q-only/MFD+Phase/중복 입력 변환 일치, 3-4-5 Box Distance, Parallel/Nonparallel Segment,
501×501 Quadratic Surface Sampling의 Coordinate Bounds 포함·Tightness 확인
(Sampling과 차이<1e-8 m). 기존 FFT/Fresnel/Newton References도 재실행한다.
새 Finite-Field Propagation을 검증한 것은 아니다.

Negative Cases: Phase/q 누락, 부분 Complex Pair, Unit/Provenance/Source/NaN 오류,
잘못된 Plane/Target Direction/Frame/Basis, Guided Index, Jones-only, High Divergence,
Rolled Axes, Tiny Aperture, Reflector 개수/Prescription 오류, Vertex 이동,
Bounds 위반, Vertex만 포함하는 Volume, 작은 Body, Envelope/Keepout 충돌.
누락·지원 외 Package에 Full-Clearance Pass를 생성하지 않는 것도 확인한다.

재현: scripts/validate.py → results/m3a_001.json, validation.json, unittest.txt.
Input/Assumptions/SI Units/Base SHA/Source Hashes/Test Result를 기록한다.
CI Artifact는 실제 Checkout한 Exact PR HEAD에서 재생성한다.

## M3-B 제안 — 이번에는 시작하지 않음

Sol Work로 최소 2D Inspector를 별도 Checkpoint에서 구현하는 것을 제안한다.
Example/Blank JSON 읽기, Fixed Ports·두 Surface·Chief Path·명시 Package AABB의
2D Projection과 Result State 목록만 연결한다. Beam Envelope를 표시한다면 기존
samples를 사용하고 Approximate로 명시하며 Clearance/Coupling 증명에 쓰지 않는다.
곡면은 기존 Quadratic Prescription으로 그리며 별도 Spherical Surface로 대체하지 않는다.
Port와 Design Variables를 구분하고 변경 후 Adapter로 재평가한다.
Invalid/Uncomputed 때 이전 유효 Overlap을 남기지 않는다. 자동 Synthesis나 새 Solver,
복잡한 UI는 추가하지 않는다. 본 Checkpoint에서는 UI를 구현하지 않았다.
