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

## 평면 굴절 계면 (P3)

Glass Block은 평면 상면 하나(선택적으로 평행한 하면)를 가진 균질 매질이다. 외부 Port에서 나온 Beam은 상면에서
Snell 법칙으로 방향이 바뀌고, 축별 q는 평면 계면의 Coddington 관계로 바뀐다(물리 길이 q 규약).

- 입사면 안의 축(t): q₂ = q₁ · n₂ cos²θ₂ / (n₁ cos²θ₁)
- 입사면에 수직인 축(s): q₂ = q₁ · n₂ / n₁

수직 입사에서는 두 축 모두 q₂ = (n₂/n₁) q₁이라 반경은 그대로이고 곡률 1/R은 1/n배가 된다(테스트로 확인).
경사 입사는 s축이 입사면에 수직일 때만 받는다(Port 축이 기울어 있으면 거절). Target 쪽 통과는 같은 관계를
역방향으로 적용하며, 정·역방향의 일관성(q → −q*)을 테스트한다. Coddington 배율은 정확한 Snell Ray Trace와
0~40°에서 비교한다.

Relay는 상면 바로 안쪽의 등가 Port에서 Glass 굴절률을 균질 매질로 하여 기존 엔진으로 푼다. 따라서 Glass 안에서는
발산각이 1/n로 줄어 같은 Mode라도 Paraxial Guard 여유가 커진다.

계산하지 않는 것: 상면의 Fresnel 반사 손실(무코팅 평면파 투과율만 참고값으로 표시), AR Coating, 상면 거칠기·기울기
오차, Glass 분산·흡수, 이온 교환에 의한 굴절률 분포. Glass 안 반사면에서 TIR 가능 여부는 반사면 뒤가 외부 매질이라는
가정의 임계각 비교뿐이며, 실제 반사면 구조(Trench, Coating)는 다루지 않는다.

## 일반 비점수차 q-tensor (P3)

두 Port가 한 평면에 있지 않거나 축이 돌아가 있으면 반사마다 입사면이 바뀌어 Beam 축이 회전한다. 이때 Beam은
2×2 복소 대칭 행렬 Q(= q⁻¹)로 나타낸다. 횡단면 기저 A = [t s]에서 E(x) ∝ exp(−i k/2 · xᵀQx), k = 2πn/λ.

- 자유 전파: Q → Q (I + L Q)⁻¹
- 반사면: Q → Q − 2 cosθ · M⁻ᵀ K M⁻¹, M = AᵀE, 기저 A → (I − 2nnᵀ)A. E는 반사면 접평면 기저, K는 곡률 Tensor(오목 양수)

동일평면·축 정렬이면 이 식은 기존 Power (2κ_t/cosθ, 2κ_s cosθ)와 같다(테스트로 확인).

정확한 해: 반사면은 Q의 실수부(곡률)만 바꾸므로, M1 직후 Beam의 폭은 정해져 있고 곡률 R만 고를 수 있다. 강도 2차 모멘트
W는 W(b) = (I + bR)W₀(I + bR) + b²W₀⁻¹/(4k²)로 전파하므로, M2에서 Target이 요구하는 폭 W_req를 만드는 R은
Y² = W₀^½(W_req − b²W₀⁻¹/(4k²))W₀^½의 대칭 제곱근 Y로 닫힌 형태로 구해진다(부호 조합 최대 4개). K1, K2는 각 반사면에서의
Q 변화로 정해진다. 반사면 곡률 축은 Port 축과 다르며 각 반사면의 주곡률 방향이다.

3w·|κ| Guard는 각 반사면 주곡률 방향의 투영 Footprint(1/e² 반폭)로, 발산각은 각도 2차 모멘트의 최대 고유값으로 계산한다.
Near-match는 반사면마다 주축 각도와 두 곡률 좌표(±1 × Guard 한계)를 변수로 Overlap을 최대화한다.

독립 검산: 실제 이차곡면 Patch를 지나는 광선으로 4×4 Ray-transfer 행렬을 중앙 차분(0.1 µm, 1 µrad)으로 만들고,
일반화 ABCD 법칙 Q_out = (C + DQ)(A + BQ)⁻¹이 같은 도착 Q를 주는지(상대 1e-6)와 Symplectic 조건을 본다.
정렬 공차는 반사면 하나씩 XYZ ±5 µm, 두 주축 둘레 ±1 mrad(동일평면 모델은 한 축)로 계산한다.

## 비근축 Scalar 검산 (P3)

근축 q 모델은 Guard 안에서만 믿는다. 같은 처방을 근축 근사 없이 계산해 비교한다.

1. Source Mode를 평면파로 정확히 분해한다(Scalar 각스펙트럼). Gaussian은 A(p) ∝ exp(i pᵀq_s p / 2k)로 해석적이다.
2. 각 평면파 방향을 Source 점에서 나가는 광선으로 보고, 실제 이차곡면 Patch(Aperture로 잘림)를 지나 Target 면까지 추적한다.
   반사면이 두 Waist의 원거리(Rayleigh 거리보다 훨씬 멂)에 있으면 이 대응은 정상위상 근사로 정확하다(Debye 방식).
3. 도착 평면파의 진폭은 Flux 보존 |A|√(k_z / q_z / J), 위상은 −kW, W = 광경로 − d'·x_r(Target 면 위 위치에 따른 기울기 보정).
4. Target Mode의 각스펙트럼과 Parseval로 Overlap을 계산한다. 129² 방향 격자와 257² 격자의 차이가 1e-4 이하이면 수렴으로 본다.

포함: 큰 전파각의 정확한 위상, 경사 입사 반사면의 3차 이상 수차(Coma 등), Aperture 밖으로 나간 광선(별도 Power로 표시).
제외: Aperture 모서리 회절, 편광·Vector 효과, Fresnel 반사 계수, 다중 반사, Glass 상면 통과의 비근축 수차(상면 통과는 근축 Coddington).

검증: 평면 반사면 두 개는 자유공간과 같으므로 각스펙트럼 직접 적분과 비교했다(상대 1e-11). 발산각이 작아지면 근축 결과로
수렴한다. 같은 반사면 두 개를 Z형(반대 방향으로 꺾음)으로 두면 Coma가 상쇄되어 비근축 η > 0.999, 같은 방향으로 꺾으면
더해져 0.3~0.6이 된다(Czerny–Turner 배치의 Coma 상쇄 원리와 같은 결과).

해석: 국소 이차곡면(Vertex 기준 2차 Sag)은 경사 입사에서 점→점 결상이 완전하지 않다. 완전한 결상면(두 초점을 잇는
타원면, Off-axis 포물면)과는 3차 Sag 항이 다르고, 그 차이가 Coma로 나타난다. 3w·|κ| Guard는 이 효과를 충분히 막지 못한다.

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

- J. A. Arnaud, H. Kogelnik, "Gaussian light beams with general astigmatism," Appl. Opt. 8, 1687 (1969) — 일반 비점수차 Beam.
- B. Richards, E. Wolf, Proc. R. Soc. A 253, 358 (1959) — 각스펙트럼 + 기하광학(Debye) 결상 계산.
- I. H. Malitson, "Interspecimen comparison of the refractive index of fused silica," J. Opt. Soc. Am. 55, 1205 (1965) — Fused silica Sellmeier.
- SCHOTT D 263 T eco data sheet (nC, nd, nF) — 1550 nm 값은 2항 Cauchy 외삽 가정(±0.01).

Franz X. Kärtner, MIT 6.977 *Ultrafast Optics*, Spring 2005,
§7.1.1, Eqs. (7.4)–(7.10), Table 7.1 (printed pp. 258–262):
[공식 MIT OCW 교재](https://ocw.mit.edu/courses/6-977-ultrafast-optics-spring-2005/f806ff596f9bffb74003360e2c05c086_MIT6_977S05_textbook.pdf).
Mirror tangential/sagittal ABCD와 ordinary Gaussian propagation을 확인했습니다.
Principal curvatures가 다른 경우는 local surface의 두 축 curvature를 각각
적용한 확장이며 exact-surface differential ray test로 독립 확인합니다.
Overlap은 위 normalized Gaussian integral에서 직접 유도하고 quadrature로 검증합니다.
