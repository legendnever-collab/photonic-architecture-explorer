# M4-C pre-execution scope and acceptance budget

2026-11-11 KST. Written before Control calculations. Base: PR #8,
`c65c8b116ea9a016d62d2af97383b6c3ec44f6d5`.

## Decision and reuse

질문: Guided MFD만으로 실제 외부 Field 및 두 Reflector 성능을 평가할 수 있는가?
MFD만으로는 불가능하다. 문헌 입력의 완전성 조사와 별도로, 실행 가능한 최소
Planar Interface Reference 경로를 한 Synthetic Control에서 확인한다.

검토: 기존 PAE Fresnel tests는 paraxial scalar propagation이며 실제 Interface를
포함하지 않는다. 현재 환경에 Meep/NGSolve/Diffractio는 없다. tmm 0.2.0은 설치 가능하고
공개 interface_r/interface_t 및 Snell 구현을 제공한다. 이를 재사용한다.
NumPy FFT와 SciPy quadrature는 독립 수치 경로로 사용한다. 새 범용 Solver,
FE Space, full fold 또는 production Adapter 연결은 만들지 않는다.

## Frozen Control (실제 WAFT가 아님)

- ID M4C-TE-PLANAR-001. Local Cartesian x,y,z; interface z=0, propagation +z.
- λ0=1.310e-6 m; nonmagnetic, lossless homogeneous n1=1.5 at z<0, n2=1 at z>0.
  Both indices are explicit assumptions; n1 is NOT the paper's guided effective index.
- TE Ey(x), invariant along y; Ex=Ez=Hy=0, retain Hx and Hz. This is a 2D TE
  Maxwell control, NOT a finite-energy 3D elliptical Gaussian or the WAFT TE eigenmode.
- Incident scalar seed Ey=exp(-x²/w²), w=1.365e-6 m. 1/e² intensity diameter
  2.73 µm is only a literature-inspired selected scale, not a verified external MFD.
- Flat phase at z=0− is assumed. exp(+iωt), forward exp(-ikz z); conjugate the
  tmm exp(-iωt) Fresnel coefficients where complex. Select decaying outgoing waves.
- Bandlimit incident spectrum to |kx|<0.95 n1 k0; report analytic discarded
  Gaussian spectral norm bound. Retain transmitted evanescent waves.
- Normalize incident integrated Poynting flux to 1 W/m (per invariant y length).
  Evaluate outgoing complex E/H at z=0+ and z=5 µm. No Target, fit, or overlap.
- Two spatial samplings N=512,1024 on the SAME periodic x window [-40,40) µm;
  dx=156.25/78.125 nm. Fixed window comparison tests spatial sampling only,
  not angular-bin/window convergence. Continuous quadrature addresses that limitation.

## Budget and predeclared acceptance

- One Control, two grids, <=120 seconds per execution, <1 GB RAM.
- Independent quadrature at x=0,1,2,4 µm and z=0,5 µm: analytic Gaussian
  spectrum + TE boundary-admittance equations, no tmm or FFT coefficients reused.
- Relative L2 complex E and Z0H sampling difference <1e-6; no phase alignment/fitting.
- Relative differences in integrated flux and flux-weighted RMS sinθ <1e-6.
- Fractions of outgoing flux at |θ|>0.1 rad: sampling absolute difference <1e-6.
  This is a diagnostic, NOT the production Gaussian divergence guard metric.
- |1-R-T| and spatial/spectral Poynting flux mismatch <1e-10.
- Plane-wave normal incidence, oblique incidence, and TIR boundary residuals <1e-10;
  normal R=0.04,T=0.96 for assumed n1/n2; TIR transmitted normal flux zero.
- Continuous quadrature: field max absolute error / incident peak <1e-4,
  integrated flux and angular moment relative error <1e-4;
  above-0.1-rad flux fraction absolute error <0.02 (coarse angular-bin limit).
- Incident removed spectral norm <1e-12; finite window effects must be disclosed.
- If a criterion fails, preserve failure and stop expansion; no threshold relaxation.
  Debugging implementation errors is allowed; reruns and changes must be recorded.

## Independence and stop

Sampling agreement is self-consistency only. Boundary/admittance and continuous
quadrature are independently coded checks of the same planar Maxwell model;
not independent full-device EM/experimental validation. No guided eigenmode is solved.
Actual field absence prevents actual-device claims even if this Control passes.
Require external field export or reproducible material profile/interface geometry
before actual WAFT/PIC execution. Stop after package/report and Draft PR.
