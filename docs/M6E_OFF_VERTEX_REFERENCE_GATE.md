# M6-E — Off-vertex Field Applicability Decision

2026-11-17 KST. **B — Reference Not Ready.**

현재 확보한 코드·데이터·실행 환경에는 G015-B1의 유한 Quadratic Reflector를
회전시킨 뒤 Fixed Target Plane의 Complex Field를 독립 검증한 Reference가 없다.
새 Field 계산은 **0회**다. 이것은 실제 Architecture의 실패나 Gaussian 근사의
정량적 오차가 확인됐다는 판정이 아니다. 기존 Chief-Ray Diagnostic은 유효한
기하학적 범위에서 유지한다. Product Charter, 추천, Fixed Ports, Guards, UI는 그대로다.

## 1. Recovery / M6-D integration

- 이전 Main: `5b747eead870bcd7b3ba4a4ebd7a043b115aa378`.
- PR #21: `4d94aa5e59f471c5ff0d8faac2f8b2323bc57d43`, Main 기준 1 commit,
  9 files, +509/−14. 승인된 placement diagnostic, 표시, 검증 및 문서 범위다.
- CI [43999963198](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/43999963198): 4 jobs success.
  Python 3.11/3.12, Workspace Desktop/Mobile, standalone HTML/JSON/A4 및 legacy Stop.
- Artifact 14291043918의 ZIP SHA256은
  `864233d4fe89183d3cbff87bef3e93ab9d8d317f59cb985acff115d644f2638c`로 API와 일치.
  acceptance/print evidence의 HEAD, 세 입력 SHA와 출력 상태를 확인했다.
- 새 detached checkout에서 97 tests, Benchmark/Adapter, M5-A 및 M5-F 재현.
  80 placement cases의 independent Newton/normal/reflection 검사 통과.
  Review threads 없음, merge preview와 PR HEAD의 Tree 차이 없음.
- 승인 조건을 만족하여 #21을 Merge Commit으로 병합했다. 최종 Main:
  **`c3c66585d089c1c3c8a8a385dee192e18f89aec8`**.
  Main Tree는 #21 HEAD와 동일하다. Main 새 checkout에서도 97 tests와 세 사례 재현.
- Main CI: [44018242353](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44018242353).
  4 jobs success. Artifact 14299118316 (세 사례 HTML/JSON/A4), 14299368029
  (Desktop/Mobile Workspace), 14300011104 (legacy Stop)를 다운로드해 API digest와
  HEAD를 대조했다. 세 사례 전체 Design JSON은 다른-q aperture-tail 값 하나의
  3.95e−31 roundoff 차이를 제외하고 새 로컬 결과와 일치한다. 추천/상태는 동일하다.
  M4 provenance의 모든 Source Hash도 현재 Tree와 일치한다. M6-E 제출 HEAD/CI는
  이 Draft PR 본문에 기록한다.
- M4-C.1 #10 (`e164f7aa3c255a03f9c54f11af699b49c86c78e6`),
  M4-D #11 (`cfd7f4087089faabbe7c6c323637ddad84eda12e`)는 열린 Draft로 별도 유지.
  #11의 Base는 #10이다. 해당 변경을 이번 Main에 가져오지 않았다.

## 2. Scope and budget gate

이번 추가 작업은 기존 구현/기록과 외부 Reference의 적합성 audit이다.
Field 실행 예산은 gate가 열릴 때까지 **0 cases / 0 solver runs**다.
검증할 입력은 아래 3개로 고정하며 전체 80개로 Field 범위를 확대하지 않는다.
기존 회귀 실행은 Field Reference 확보와 구분한다. 수치 기준을 낮추지 않는다.

Field 실행 개시 조건은 (1) 독립 구현/버전과 재현 가능한 model 또는 export,
(2) 아래 surface/coordinate/power 계약, (3) 수렴 증거와 비교 기준의 사전 고정이다.
어느 하나라도 없으면 B로 중단한다. Reference가 없으므로 Field의 오차 수치,
Runtime/Memory 또는 convergence를 통과했다고 보고하지 않는다.
새 solver 설치·작성, threshold 탐색, 새로운 Synthetic Control은 수행하지 않았다.

## 3. Frozen cases and available information

`examples/m5a_two_ports.json`, input SHA256:
`349546f1a3f4955aa8a6d4cc96fb49b28b360c3924b20ec8d0089fcad6b86196`.
Candidate **G015-B1**. Source/Target는 Synthetic external Gaussian이며 phase가
명시돼 있다. 실제 PIC/Glass 측정값이 아니다.

- λ0=1.310 µm, homogeneous n=1; global right-handed XYZ, fold XZ.
- Source (0,0,0) m, Target (0.002,0,0.002) m, 두 direction +X.
  s=+Y, t=s×d=−Z. Target plane은 x=0.002 m로 고정한다.
- 각 Port q(t,s)=(i·0.0001534823891830128, i·0.00034533537566177886) m;
  waist radii (8,12) µm, 명시된 curvature (0,0) m⁻¹.
- M1 vertex (0.001,0,0), M2 (0.001,0,0.002) m;
  illuminated normals (−1,0,1)/√2, (1,0,−1)/√2.
- 두 면의 κ(t,s)=(353.5533905932737,707.1067811865476) m⁻¹.
  Local sag h=(κt u²+κs v²)/2. Rectangular half-aperture
  (298.30628827483334,147.04998517080882) µm. 이는 자동 4w concept prescription이며
  M1 benchmark의 수동 aperture와 구분한다. 실제 mirror material/coating/body는 미제공.
- 회전은 M1 nominal vertex를 중심으로 공통 +Y 축의 right-hand rotation.
  Local curvature/aperture는 면에 부착되어 함께 회전한다. M2는 고정한다.

기존 M6-D exact-ray 값을 재현하여 추출했다. **새 Field 결과가 아니다.**

| Frozen condition | Target Δt [µm] | Target Δs [µm] | θt [mrad] | θs [mrad] |
|---|---:|---:|---:|---:|
| Nominal | 0 | 0 | 0 | 0 |
| M1 +1 mrad | −2.004026689 | 0 | +2.003991975 | 0 |
| M1 −1 mrad | +1.996026644 | 0 | −1.995992025 | 0 |

θj=atan2(k·ej,k·d), dimensionless slope=(k·ej)/(k·d).
Nominal/perturbed rays, both hits, normals, directions and full nominal prescription
are copied into [m6e_reference_gate.json](../results/m6e_reference_gate.json).
M1 rotates about its illuminated vertex, so this chief ray still hits M1's vertex;
it then hits M2 off vertex. The finite beam encounters varying sag/normals on both
surfaces. A chief ray at M1's vertex does not establish a vertex-centred field model
for the complete perturbed optical path.

Existing independent geometry tests use 1e−13 m surface/position and 1e−11 rad
angular tolerances. These are numerical ray-test tolerances, not Field error bounds.
Nominal normalized overlap remains approximately 1 in the existing paraxial model.

## 4. Reference feasibility audit

| Evidence | What it provides | Gate limitation |
|---|---|---|
| Production Gaussian/q and `tests/test_m1.py` Fresnel kernels | Independent sampled propagation and quadratic phase-screen checks of scalar paraxial Gaussian transport | Screens use prescribed vertex optical powers; no finite tilted curved-surface field handoff. Re-running them cannot validate missing off-vertex physics |
| M2 / M6-D analytic roots versus independent Newton + vector reflection | Intersections, normals, specular chief-ray directions and fixed-plane crossing | No complex amplitude transport, diffraction, wavefront or energy-weighted beam moments |
| M5-D Target-plane Gaussian sensitivity | Complex overlap with imposed relative offset or linear phase ramp, nominal q retained | No mapping from mirror displacement to output q/field; cannot combine its loss with M6-D to infer assembly tolerance |
| M4 tmm/FFT + independent admittance/quadrature | Homogeneous planar-interface, y-invariant 2D TE E/H and flux | No curved mirror, two-dimensional finite beam, moving surface, fold or attached aperture |
| M4-C.1, separate #10 | Window/angular-bin convergence for that same planar control | Improved angular integration does not enlarge its physical model |
| M4-D, separate #11 | Missing actual field/facet input audit | No provided complex export or reproducible curved-reflector model |
| POPPY Fresnel documentation [R1–R2] | Established scalar Fresnel propagation and quadratic phase optics | No ready case-specific curved-surface export/model. `inclination` documentation describes geometric projection alone, not a complete rotated-surface phase law |
| SRW curved-mirror work [R3] | Stationary-phase/Fourier method with grazing-incidence mirror benchmarks and aperture diffraction | Potential external route; those benchmarks do not certify our 1310 nm, 45° two-quadratic-patch case. A reproducible model, approximation justification and convergence evidence are still needed |

Audit covers tracked repository files, the two separate M4 branches, this request
(no attached Field/model), available Python modules and the cited primary sources.
It is not a claim that no suitable solver exists anywhere. Local NumPy 2.3.5 and
SciPy 1.17.0 are present. tmm, poppy, srwpy/srwlib, meep, ngsolve, diffractio and
lumapi were not importable in this interpreter. tmm is already pinned in the M4
CI requirements; its local absence does not change the model-applicability decision.
No licensed external simulation session or exact case export was supplied.

M4-C's historical angular-tail absolute error **0.0277776636 > 0.02** remains a
numerical Fail/Stop. #10 separately records **0.000203618350** after bounded window
verification. Neither is evidence for curved-reflector fields or actual WAFT failure.

Primary sources accessed 2026-11-17:

- [R1 POPPY Fresnel propagation](https://poppy-optics.readthedocs.io/en/latest/fresnel.html):
  independent Fresnel checks against PROPER and the quadratic-phase optical-power model.
- [R2 POPPY release notes, inclination definition](https://poppy-optics.readthedocs.io/en/latest/relnotes.html):
  geometric cosine projection; no wavefront tilt from this attribute alone.
- [R3 Canestrari, Chubar & Reininger (2014), J. Synchrotron Rad. 21, 1110–1121](https://doi.org/10.1107/S1600577514013058):
  curved grazing-incidence wave-optics method and its stated benchmark scope.

## 5. Minimum conditions to resume

Obtain **one** reproducible, independently implemented curved-surface scalar
Reference or corresponding complex-field export for these three prescribed cases.
An established external physical-optics tool is preferred. No new generic solver
is required by this decision. Synthetic scalar evidence can qualify only its stated
approximation, never actual vector coupling.

Before running it, record and freeze:

1. Solver/version/model hash; exact Source field, surface sag, attached rectangular
   apertures and both reference planes. Declare the reflection boundary model
   (e.g. an explicitly ideal scalar reflector), its oblique-incidence validity and
   treatment of edge diffraction/obliquity. No guessed real coating/material.
2. exp(+iωt), forward exp(−ikz) mapping; world/local bases, transverse reflection
   parity, rotated-surface mapping and Target-plane area/Jacobian. Both output
   fields must be on the original Target t/s grid. No re-aiming or q fitting to Target.
3. Incident normalization and absolute power ledger (accepted/outgoing, reflected,
   clipped, absorbed if modeled, and numerical residual). Preserve absolute power
   before optional unit-norm shape comparison. M4's 1 W/m invariant-TE convention
   cannot be used as finite 3D beam power. Report scalar norm as scalar norm unless
   a physical Poynting interpretation is established.
4. Separately refine spatial pitch, transverse window and angular support/resolution;
   include mirror-surface sampling and aperture-edge convergence. Record at least
   successive refinements and the smallest resolved features. Agreement at one
   fixed window is insufficient. Supply raw complex arrays and completion hashes.
5. Predeclare model-specific numerical tolerances, Runtime/Memory and maximum runs
   for only these 3 cases. Include complex relative L2 error (at most one common
   piston removal; no fitted shift/tilt/curvature), power residual, intensity-weighted
   relative-phase/curvature errors, second-moment widths and non-Gaussian residual.
   Report centroid/direction moments separately from the geometric chief ray.
   Their equality is not assumed in an aberrated field. Fit metrics, if used for
   diagnostics, must preserve the original reference field and cannot tune physics.
6. Validate reference geometry against existing ray hit/normal/direction checks;
   then compare a clearly labelled shift/tilt-only Gaussian hypothesis against
   the Reference field. That hypothesis preserves nominal q and is presently
   unvalidated. No overlap or loss is calculated from it in M6-E.

If physical validity, normalization or independent convergence cannot be shown,
retain B (or C only with positive evidence of model inapplicability), withhold field
acceptance and stop. The precise Field thresholds/budget depend on the supplied
Reference and must be recorded before its first calculation; none are retrofitted
here to unavailable results. M4A actual input and M4B literature proxy remain separate.

## 6. Product decision / result boundary

| Quantity | Status after M6-E |
|---|---|
| Nominal Gaussian/q/Mode Match | Existing bounded validation retained |
| Perturbed Chief-Ray hit, normal, Target position/angle | Computed within M6-D ray contract |
| Off-vertex footprint, complex reflected/output field, width/curvature change, non-Gaussian residual | Uncomputed |
| Perturbed Gaussian Mode Overlap, actual Assembly Tolerance | Uncomputed |
| Finite-aperture field throughput, Package Yield, Total Coupling, Patentability | Uncomputed |
| Reference-vs-shift/tilt Field error | Uncomputed; no Reference execution |

Chief-ray sensitivity is useful for comparing geometric responses. It does not
measure field overlap, because width, wavefront curvature, aberration, clipping and
frame transport remain unresolved. Preserve M6-C order and M5-D/M6-D diagnostics
as separate results. Hold the Field path until the minimum evidence is available.
Next product work should improve two-port entry and candidate understanding (M6-F).

## 7. Reproduce / evidence integrity

Use a new checkout/output directory for each run. Scripts must exit successfully
and emit the current HEAD; a stale JSON or ImportError is not a Control Stop.
The main CI uses a fresh checkout of the exact push SHA. Browser/PDF reproduction
runs in GitHub's Chromium environment; local execution here covers Python tests,
CLI and Workspace Python model. PDF remains the existing nominal A4 summary;
placement detail remains in HTML/JSON and is not newly added to that print sheet.

```bash
git checkout c3c66585d089c1c3c8a8a385dee192e18f89aec8
python -m pip install -e '.[test]'
PYTHONPATH=src python scripts/validate.py
PYTHONPATH=src python scripts/validate_m5a.py --output-dir results/runtime-m6e-main-m5a
PYTHONPATH=src python scripts/validate_m5f.py --output-dir results/runtime-m6e-main-m5f
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install --with-deps chromium
# Install poppler-utils and fonts-noto-cjk, as in CI.
node scripts/check_workspace.cjs results/runtime-m6e-browser results/runtime-m6e-main-m5a
node scripts/check_m5f_print.cjs results/runtime-m6e-main-m5f
```

The decision JSON copies G015-B1's `prescription`, `reflector_placement.nominal`
and its two `kind=rotation, mirror=1` cases from fresh equal-q `design.json`.
It includes that file's SHA256, input identity and checkout. Reproduce those values
with `validate_m5f.py`; JSON object comparisons ignore formatting. No new Field
kernel, tests, fixture or historical result is introduced. M6-E is a separate
Draft PR, not merged in this milestone. See [next task](NEXT_TASK.md).
