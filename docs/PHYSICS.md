# Physics assumptions and validity limits

## Port와 모델

Source/Target는 immutable Port이며 position, propagation direction, sagittal
axis, medium index, wavelength, 두 complex q를 가집니다. Tangential axis는
s × d이며 (t,s,d)는 right-handed입니다. Target direction은 도착하는 빛의
방향입니다. Normalized scalar external fields를 비교하며 actual guided mode,
SSC radiation pattern, device transmission을 구현한 것으로 해석하지 않습니다.
M1-001의 Mode 크기는 수학 검증용 선택값이며 measured/typical SSC 값이 아닙니다.

Global 좌표는 right-handed이고 길이 m, curvature/power m^-1, angle rad입니다.
λ0는 vacuum wavelength, n은 양의 실수 homogeneous ambient index입니다.
q는 ordinary q (reduced q/n이 아님)입니다. 따라서 전파는 q'=q+L이고,
1/q=1/R-i λ0/(π n w²), z_R=π n w0²/λ0입니다.
입출력 medium 또는 wavelength가 다르면 계산을 거절합니다.

시간 convention exp(+iωt), 전파방향 carrier exp(-ikz), k=2πn/λ0를 사용합니다.
Transverse field는 E=N exp[-t²/w_t²-s²/w_s²]
exp[-ik(K_t*t²+K_s*s²)/2]이며 N=sqrt[2/(π w_t w_s)]입니다.
적분 ∫|E|² dt ds=1. Piston/Gouy/global reflection phase는 이 단일 경로의
squared overlap에 영향을 주지 않아 저장하지 않습니다. 간섭계 분석에 사용하면 안 됩니다.

## 반사 Geometry와 Optical Power

d'=d-2(d·n_hat)n_hat. Normal은 incident ambient를 향하며 d·n_hat<0입니다.
θ는 normal에 대한 입사각, c=cosθ=-d·n_hat입니다.
면의 tangential/sagittal principal curvature는 κ_t,κ_s로, concave 양수,
flat 0입니다. Illuminated normal 방향 local sag h=(κ_t*u²+κ_s*v²)/2.
M1은 해당 local quadratic patch를 chief-ray interception에만 사용합니다.

P_t=2κ_t/c, P_s=2κ_s*c, q'_j=q_j/(1-P_j*q_j).
두 principal curvatures가 같아도 oblique incidence에서는 두 optical powers가
다릅니다. M1-001은 κ_t=353.5533906 m^-1, κ_s=707.1067812 m^-1로
P_t=P_s=1000 m^-1를 구성합니다. Principal radii는 각각 2.828427, 1.414214 mm.
이는 spherical mirror가 아닙니다. Spherical vertex-curvature control은 κ=500 m^-1.

한 번의 반사에서 geometrical tangential parity가 뒤집히고 sagittal parity는
유지됩니다. Centered separable Gaussian의 q와 크기는 이 parity에 불변입니다.
두 번 반사 후 transverse frame은 원래 방향으로 돌아옵니다. 이 범위에서
reflection을 complex conjugation이나 음의 전파거리로 처리하지 않습니다.
Skew folds와 arbitrary rolled elliptical fields는 cross-axis q tensor가 필요하여
M1에서 명시적으로 거절합니다. General 3D world rigid transform은 허용합니다.

## Mode Overlap

η_mode=|∫E_target* E_incident dA|² / (∫|E_target|² dA ∫|E_incident|² dA).
동일 transverse plane의 두 정규화된 Gaussian을 두 1D complex integral로 계산합니다.
두 field의 radius와 curvature를 모두 보존합니다. Low-level overlap 함수는
offset과 small-angle phase ramp도 지원하지만 M1 path solver는 vertex closure를
요구하며 alignment sweep을 제공하지 않습니다. Log overlap은 underflow 시에도
유한한 mismatch dB를 보존합니다. Mode mismatch dB는 physical insertion loss가 아닙니다.

## 유효범위와 미계산 항목

Guard 수치는 [Frozen Benchmark](M1_BENCHMARK.md)를 따릅니다.
3w footprint/curvature 및 divergence guard는 보수적인 screening rule이며
aberration 또는 overlap error의 엄밀한 상한이 아닙니다.
각 mirror의 tangent-plane projected radius는 (w_t/c,w_s)입니다.
직사각 aperture의 Gaussian-tail union estimate는
erfc(sqrt(2)*a_t/(w_t/c))+erfc(sqrt(2)*a_s/w_s).
이를 두 면에 합산하여 domain screening에만 사용합니다. Curved-surface footprint의
고차 보정과 diffraction이 없으므로 실제 throughput을 산출하거나 η_mode에 곱하지 않습니다.

검증된 범위: scalar paraxial free propagation, quadratic optical power,
aligned coplanar reflection frames, normalized overlap, chief-ray quadratic-patch checks.
Fresnel reference는 같은 paraxial model의 독립 수치 검증입니다. Differential ray
reference는 정확한 곡면 Reflection의 **vertex limit**를 검증하며 full-beam aberration
또는 실제 제품의 finite surface를 독립 검증한 것이 아닙니다.

Uncomputed: finite-beam aberration, finite-aperture diffraction, mirror coatings,
polarization-dependent phase/loss, actual PIC/glass interfaces, roughness/scatter,
support/body collision, manufacturability, placement tolerance, assembly yield,
total coupling. Surface-to-surface mechanical clearance 전체 검증도 포함하지 않습니다.

## 공개 이론 Reference

Franz X. Kärtner, MIT 6.977 *Ultrafast Optics*, Spring 2005,
§7.1.1, Eqs. (7.4)–(7.10), Table 7.1 (printed pp. 258–262):
[공식 MIT OCW 교재](https://ocw.mit.edu/courses/6-977-ultrafast-optics-spring-2005/f806ff596f9bffb74003360e2c05c086_MIT6_977S05_textbook.pdf).
Mirror tangential/sagittal ABCD와 ordinary Gaussian propagation을 확인했습니다.
Principal curvatures가 다른 경우는 local surface의 두 축 curvature를 각각
적용한 확장이며 exact-surface differential ray test로 독립 확인합니다.
Overlap은 위 normalized Gaussian integral에서 직접 유도하고 quadrature로 검증합니다.
