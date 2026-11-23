# M2.5 — External Port Applicability / M3 Readiness

2026-11-10 KST. Frozen scope: M25_CONTRACT.md; base M2
`074930aab1b941d58c428b0644c1553dd23e9271`.

**개발 경로는 Path B. 실제 PIC SSC ↔ Glass Waveguide Applicability는 Uncomputed.**
기존 모델은 제한된 centered/vertex/coplanar scalar paraxial screening에 유효하다.
최종 Engineering Tool에 필요한 external input adapter, package 제약 및
placement의 off-vertex Gaussian handoff가 아직 없다. 실제 Port가 없으므로
특정 Port에 Physics extension이 반드시 필요하다거나 구조가 가능/불가능하다고
판정하지 않는다. Path B는 최종 목표 대비 capability gap에 대한 선택이다.

## 1. Recovery / preservation

| Ref | Recovered SHA | 상태 / dependency | 기존 CI |
|---|---|---|---|
| Main | fe730295672047878274d9013edc255b88d16ce2 | 변경·병합 없음 | 별도 physics implementation 없음 |
| M1 PR #1 | 55de4c5f26d3bacc9e22ec64ba385de8acfc4dbe | Draft → Main | 42620976531 success |
| M2 PR #2 | 074930aab1b941d58c428b0644c1553dd23e9271 | Draft → feature/m1-two-reflector | 42623160229 success |
| M2.5 | 이 PR의 exact HEAD 및 CI artifact | Draft → feature/m2-bounded-diagnostics | 최종 PR/Checks 참조 |

M1을 detached worktree에서 재실행: 19 tests + benchmark gate Pass.
M2 exact base 재실행: 26 tests + benchmark gate Pass. M2.5는 기존 26개에
6개 reference/semantics test를 추가한다. 최종 실행 기록은 results/unittest.txt,
validation.json(평가 checkout SHA/pre-run dirty flag 및 source hashes), m25_001.json.
로컬 source가 미커밋이면 checkout SHA는 parent이고 hashes가 평가 내용을 식별한다.
CI는 exact HEAD에서 재생성하여 artifact를 업로드한다. 생성 evidence를 commit할 때
자기 자신의 SHA를 문서에 넣는 순환은 만들지 않는다.

Remote recovery에서 확인한 M1 artifacts: 13675662634 (3.11), 13676071794 (3.12).
M2 artifacts: 13676574748 (3.11), 13676248615 (3.12), 모두 non-expired.
M2 jobs의 validate 및 upload steps는 두 Python 버전에서 success.
이 metadata 확인과 로컬 benchmark 재현을 구분하며, 기존 artifact ZIP을 다시
다운로드·비교했다고 주장하지 않는다. M1/M2 benchmark JSON 및 frozen fixture,
기존 solver/geometry/gaussian/diagnostics와 tests는 변경하지 않는다.

## 2. Physics Applicability Matrix

| 항목 | 검증된 모델 범위 | 실제 설계 상태 / 제한 |
|---|---|---|
| Fixed-Port closure | chief ray가 두 vertices에서 specular law 만족, Target 도착 방향 일치 | 실제 positions/directions 미제공 → Uncomputed |
| Surface intersection | finite local quadratic patches의 exact roots, independent Newton check | 제조용 spherical/toroidal/freeform prescription 미정 |
| Gaussian propagation | ordinary q, homogeneous n, scalar paraxial | 실제 external MFD/phase/n 미제공 → Uncomputed |
| Astigmatism | aligned t/s의 독립 q; oblique mirror principal powers | rolled/skew/cross-axis tensor 입력 Fail/unsupported |
| Divergence/NA | 모든 source/target/after-mirror waist divergence ≤0.1 rad | 실제 NA 미제공; chief-ray fold angle과 divergence는 별개 |
| Finite footprint | 3w projected slope ≤0.15; aperture-tail sum ≤1e-6 guards | guards가 full-field error 보증은 아님 |
| Normalized Mode Overlap | valid centered same-plane Gaussian integral | 실제 non-Gaussian fit/finite-field correction Uncomputed |
| Placement | shifted patches의 chief-ray miss 검증 | powered off-vertex Gaussian handoff Uncomputed |
| Package volume | 이번엔 입력 Contract만 정의 | physical bodies/clearance/volume feasibility Uncomputed |
| Polarization / device interfaces | scalar normalized field만 계산 | Jones transport, coating/SSC/device loss Uncomputed |
| Fabrication / assembly | 공차 perturbation은 diagnostic | process capability 및 yield Uncomputed |

기존 guard를 변경하지 않는다. Geometry fail 시 overlap 없음. Model-domain fail도
숫자 overlap을 생성하지 않는다. Data 부족은 Uncomputed이고 0%가 아니다.

## 3. Gaussian domain: 실제 적용 전에 필요한 계산

w=MFD/2, C=1/R인 입력 plane에서 각 축에 대해

- 1/q = C - i λ0/(π n w²)
- w0² = λ0 Im(q)/(π n)
- θ0 = λ0/(π n w0) = sqrt[(λ0/(π n w))² + (C w)²]
- 작은 각도에서 Gaussian 1/e² divergence의 NA scale ≈ n θ0.

위 식은 paraxial Gaussian 내부의 관계이며 실제 high-NA field를 검증하지 않는다.
θ0는 global chief-ray fold angle이 아니다. Incidence는 normal 기준 70° 이하이며,
fold가 90°여도 그 주변의 Gaussian divergence는 작을 수 있다.

Frozen guard θ0≤0.1 rad는 waist plane에서 MFD≥2λ0/(π n·0.1)를 요구한다.
**Synthetic λ0=1310 nm, n=1에서 8.339719 µm/axis**.
이는 typical SSC MFD가 아니며, necessary port check일 뿐이다. Non-waist에서는
같은 MFD라도 C에 의해 θ0가 커진다. 실제 input을 평탄 위상으로 바꾸지 않는다.
동일 입력으로 after-mirror divergence, footprint/aperture와 geometry도 검사해야 한다.

M1 waist radii 8/12 µm의 θ0는 0.05212324/0.03474883 rad. 이때의 per-Port
precheck만 Pass이다. M1 full path의 다른 guards는 기존 solver가 따로 통과했다.
Intensity MFD만으로 Gaussian 적합성, vector content, phase를 판단하지 않는다.
현재 실제 Port complex field도 없으므로 Gaussian fit은 Uncomputed.

이론 확인: MIT OCW, Kärtner, *Ultrafast Optics* (2005), §7.1.1 Eqs. 7.2–7.10,
Table 7.1: ordinary q, waist/divergence, paraxial ABCD.
[공식 교재](https://ocw.mit.edu/courses/6-977-ultrafast-optics-spring-2005/f806ff596f9bffb74003360e2c05c086_MIT6_977S05_textbook.pdf).
위 homogeneous ambient 식에서는 매질 wavelength=λ0/n을 사용했다.
직접 유도한 curvature 포함 divergence는 independent Fourier moment로 확인했다.

## 4. Geometry / package domain

정확히 두 Reflector; 현재 solver는 Source→M1 vertex→M2 vertex→Target의
fixed specular path만 평가한다. Chief ray의 surface interception과 unintended patch
hit 검사까지 수행하며 body/support clearance는 검사하지 않는다. Port를 옮기거나
입사 방향을 꺾어 closure를 맞추는 것은 허용하지 않는다.

또한 fixed Source axis와 backward Target axis가 정해지면 vertex는 각각 그 axis
위에서만 움직일 수 있다. 제한된 2D domain에서는 거리 l1,l3>0를 design variables로
삼고 p1=p_source+l1*d_source, p2=p_target-l3*d_target로 parameterize할 수 있다.
두 점을 잇는 middle segment가 specular normals를 결정한다. Surface principal
curvatures와 apertures는 별도 design variables이다. Ports는 design variables가 아니다.
새 optimizer는 이번에 구현하지 않았다.

Vertex가 volume 안에 있다는 사실만으로 reflector patch/body나 full beam이 그 안에
있음을 보증하지 않는다. Available-volume, keepout solids, body envelopes,
clearance, signed principal curvature bounds, surface sag prescription이 필요하다.
현재 모든 실제 package 입력은 미제공. Manufacturing feasibility는 Uncomputed.

## 5. Finite-footprint significance

동일한 **M1 synthetic fixture의 Target waist**와만 비교한다.
δ는 9개 sparse ray의 exact-vs-linear transverse residual **norm의 최대값**이다.
아래 δ/w는 각 축 오차 자체가 아니라 norm과 해당 축 scale의 비교다.

| Fan extent | δ [µm] | δ / w_t (8 µm) | δ / w_s (12 µm) |
|---|---:|---:|---:|
| 0.5w | 0.059644 | 0.007456 | 0.004970 |
| 1w | 0.380172 | 0.047522 | 0.031681 |
| 2w | 2.679648 | 0.334956 | 0.223304 |

2w residual을 무시할 수 있다는 근거가 부족하다. 반대로 높은 intensity의 beam 전체가
그만큼 벗어났다고 해석할 수도 없다. Uniform sparse fan은 power-weighted sampling,
field phase/OPD, diffraction, full-aperture worst-case 또는 Gaussian centroid를 주지
않는다. 따라서 이 표에서 exp(-δ²/w²), dB loss, coupling efficiency를 만들지 않는다.
M2 residual을 실제 SSC MFD만으로 재조정하거나 다른 Geometry에 이전하지 않는다.
실제 Modes가 주어지면 그 Modes/Geometry로 diagnostic을 재실행해야 한다.

## 6. Independent validation and limits

기존 M1 analytic/Fresnel/field quadrature/differential exact-ray 및 M2 independent
Newton reference를 재실행했다. M2.5는 manual complex Gaussian field의 FFT angular
second moment를 2048/4096 grid에서 확인한다. θ0=2*rms(k_transverse)/k와
production q의 divergence가 1e-11 relative 수준 test tolerance에서 일치하며 두 grid
차이는 1e-12 rad 미만. Flat phase 및 ±curvature, n=1/1.45의 synthetic math cases.
별도 closed form sqrt[(λ0/πnw)²+(Cw)²]와 non-waist rejection도 확인했다.

이는 q normalization/phase dependence와 paraxial 내부 계산의 independent check다.
실제 SSC Mode, nonparaxial Maxwell field 또는 finite curved-reflector aberration의
독립 검증이 아니다. M1의 unity overlap도 ideal 4f reference로만 유지한다.

## 7. Decision: B, with conditional A/C

- **A (좁은 현재 범위):** centered vertex, aligned separable low-divergence Gaussian의
  이상적 Architecture screening에는 현 모델 사용 가능. 실물 coupling/yield 순위는 아님.
- **B (선택한 개발 경로):** external adapter/explicit geometry constraints를 먼저 연결.
  Placement Gaussian performance가 실제 요구일 때만 다음 bounded off-vertex
  formulation을 검토. 아직 구현하지 않는다.
- **C (조건부 전환):** high-NA/vector/non-Gaussian/skew modes, finite-surface field
  aberration이 성능 결론을 지배하면 external wave reference 필요. 실제 입력 없으므로
  지금 상용 solver 계산이나 Maxwell project를 시작할 근거는 부족하다.

### Proposed minimal physics extension — 미구현

Off-vertex first-order handoff: existing exact ray/surface trace로 nominal hit,
local normal, outgoing chief ray를 구하고 그 주위의 transverse ray map을 선형화한다.
Coplanar aligned separable case만 유지한다. 각 축에서 affine centroid map와
2×2 Jacobian J=[[A,B],[C,D]], q_out=(Aq_in+B)/(Cq_in+D)를 사용한다.
Unit은 A,D dimensionless; B m; C m^-1. Reflection parity와 same-medium
canonical convention을 명시하여 frame 변환 후 conservation/symplectic check를 한다.
Cross-axis terms가 유의미하면 2개 scalar q를 강제 적용하지 않고 중단한다.
Target는 그대로 두고 incident field를 **fixed Target plane**으로 handoff한다.
Plane이 nominal output axis와 다르면 oblique plane resampling의 적용 범위를
명시해야 한다. 검증 전에는 low-level offset/tilt overlap에 ray miss만 대입하지 않는다.

Independent gates: analytic flat tilt/decenter, zero-perturbation M1 limit,
independent Newton differential rays at successively halved step (3 scales),
phase-screen Fresnel controls in their paraxial domain. Fourier/Fresnel 같은-model
검증만으로 exact finite patch field의 정확성을 주장하지 않는다.

제안 예산: formulation 1 checkpoint; M1 nominal+flat analytic controls+기존 12 placement,
Jacobian 3 step scales; new tests ≤10, 기존 suite 포함 ordinary local runtime 60 s 이내.
실패 시 1회의 원인 분류까지만 하고 결과 보존. 새 FE space/범용 POP/tensor engine이
필요하면 중단·Path C 실행 package를 제안. 이 예산은 후속 승인된 work order에서만 실행.

Finite-beam performance는 위 handoff와 별개다. 실제 input이 low-NA domain 안이어도
finite aberration이 중요하면 externally validated physical-optics tool에서 **동일
finite surfaces/incident complex field/reference plane**의 한 nominal case+flat control,
두 sampling resolutions로 power/phase/overlap을 비교하는 bounded reference를 제안한다.
Tool이 exact geometry/material을 지원하는지 먼저 확인한다. 새 scalar propagator를
자체 개발하지 않는다. Vector/high-NA라면 vector wave reference로 전환한다.

## 8. M3 readiness and remaining risks

| Gate | 현재 판정 | M3 선행 작업 |
|---|---|---|
| Fixed Port semantics | 문서 및 기존 immutable Port로 명확 | full external adapter + roundtrip/invariance test |
| Engine/UI separation | 기존 Python evaluate는 UI 독립 | adapter와 result schema도 UI 독립 유지 |
| Design variables | vertex distances, supported curvatures/apertures로 제한 | fixed Ports 및 bounds 강제, no automatic synthesis |
| Result reliability | Geometry/domain/overlap/loss 상태 분리 가능 | Computed/Approximate/Uncomputed/Fail를 각각 표시 |
| Invalid rejection | 기존 guards 검증됨 | 입력 누락/phase/units/roll/geometry/body 미지원도 명시 |
| Actual engineering use | **Uncomputed / not ready** | 실제 non-confidential inputs 및 constraints 필요 |
| Minimal 2D inspector | 조건부 준비 가능 | M3-A adapter gates 통과 후 synthetic inspector 허용 |

즉시 큰 UI나 physics rewrite를 시작할 필요가 없다. M3-A에서 validated input/result
boundary와 bounded package representation부터 만들고, M3-B에서 그 결과만 보여주는
2D inspector로 연결한다. Off-vertex/finite-field 성능은 별도 checkpoint로 남긴다.
실제 입력이 계속 없어도 synthetic controls로 adapter/UI의 정확성은 검증할 수 있지만
actual applicability와 total coupling은 계속 Uncomputed로 표시한다.

가장 큰 remaining risks: 실제 Gaussian fit/phase 부재, package geometry 부재,
exact manufacturing surface와 quadratic patch의 차이, finite-field aberration,
polarization/interface/coating losses, correlated tolerance 및 assembly yield.
다음 copyable instruction: NEXT_TASK.md. M3 구현은 이 단계에서 시작하지 않는다.
