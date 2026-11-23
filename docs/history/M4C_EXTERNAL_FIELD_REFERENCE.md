# M4-C — External Field Reference Feasibility Gate

2026-11-11 KST. **결론: 외부 데이터·자원 확보 후 재개.** 실제 WAFT/PIC 외부 Field
입력은 미확보다. 별도의 Synthetic Planar Control은 실행 가능하지만, 사전 정의한
Angular-tail 오차 기준 하나가 실패하여 Reference 전체 승인을 보류하고 중단했다.
현재 Gaussian Engine으로 M4B-LIT-001의 효율을 출력할 근거는 생기지 않았다.

## 1. Recovery / 보존

| 대상 | HEAD | Base / Diff | 확인한 CI run |
|---|---|---|---|
| Main | `f2781ba2955b4ccda4202165c778cd3dc58a07ec` | 변경 없음 | 42785703605 success |
| Draft #7 | `a76fd01ac28443fe71223a2ad1c7329f8b12f0a6` | Main, 3 files +301/−19 | 42792973697 success |
| Draft #8 | `c65c8b116ea9a016d62d2af97383b6c3ec44f6d5` | #7, 8 files +3115/−22 | 42802128845 success |

Main 및 #7/#8의 Physics/Browser Artifact 각각 3개, 만료되지 않음을 확인했다.
Python 3.12 ZIP 13749896085 / 13751776922 / 13756077968을 다운로드하고,
API의 SHA256 digest, validation.json의 정확한 HEAD, 모든 기록된 Source Hash를
해당 Git tree와 대조했다. Main은 commit-workflow 검색 API가 PR-trigger만 반환하여
빈 결과였으나, 위 run의 jobs와 Artifact의 head_sha로 직접 확인했다.
`results/m4c_recovery.json`에 식별자와 digest를 기록했다.

PR #8 clean baseline에서 기존 61 tests, M1 Benchmark Gate, M3-A Adapter Gate를
재실행하여 Pass를 확인했다. 계산 결과 파일은 동일하며 runtime validation/test log만
달라졌다. Production src, 기존 tests/fixtures/examples, Frozen Guards, PHYSICS 및
External Port/Adapter Contract는 변경하지 않았다. M4A-001과 M4B-LIT-001도 그대로다.
새 Reference는 `scripts/`에 격리하고 production에 연결하지 않았다.

## 2. Input Evidence — 확보와 미확보

원문 L1: Chakraborty et al., ACS Photonics (2026),
[DOI](https://doi.org/10.1021/acsphotonics.5c02702),
[원문 PDF](https://publica-rest.fraunhofer.de/server/api/core/bitstreams/85c371fe-a919-4520-baa4-b77147c16c76/content).
Supporting Information L1-SI:
[DOI](https://doi.org/10.1021/acsphotonics.5c02702.s001),
[공식 Figshare metadata](https://api.figshare.com/v2/articles/31868683),
[PDF](https://ndownloader.figshare.com/files/63168334?download=1).
14쪽 전부 text로 읽고 Table S3의 S13을 렌더하여 항목/단위를 확인했다.
SI 1,490,254 bytes, publisher MD5 `23beb4ac1d5627341984fcb986ec4713` 일치,
SHA256 `2f4b084b66f6826ef3fa6ed239d53314c325f2ece371a3051f4f4cdba626eb51`.

| 항목 | 원문 / SI에서 확인한 것 | 아직 부족한 것 / 취급 |
|---|---|---|
| Guided Mode scale | Table 1, TE 1310 nm, H/V MFD=3.79/2.73 µm, n_eff=1.525025 | External n/Field로 대체 불가 |
| Width 정의 | MFD라는 명칭과 near-Gaussian 설명 | 1/e² intensity/FWHM/second moment, fit procedure 미명시 |
| Material | SI S12–S13, buried substrate n≈1.524–1.525 at 1310 nm, maximum Δn≈0.05, effective vertical diffusion depth σ≈1.45 µm | 정확한 surface-section n(x,y,λ), lateral profile, depth origin, boundary 미제공 |
| Surface section | SI S12: buried section에서 surface waveguide로 adiabatic transition; S13 mask opening ≈2 µm, surface peak n≈1.518–1.525 범위 | buried Δn/σ와 surface peak를 조합해 임의의 Index Profile을 만들지 않음 |
| 기준면 / 외부 매질 | Main Fig. 1/2: guided cross sections 및 facet 구조. SI S4–S5: spectrum의 FP 분석에서 air gap 추정 | 정량적 external export plane, facet relative position, 정확한 gap/tilt가 있는 solver model 없음 |
| Phase / Vector Field | Main mode images, TE/TM label; FDE/EME/3D FDTD 사용 명시 | complex Ex/Ey/Ez/Hx/Hy/Hz 배열, phase convention, modal power normalization 없음 |
| Air gap | SI Table S2: O-band 10.71 µm, C-band 18.09 µm의 추정 cavity length | 독립 측정된 facet separation이나 reference plane으로 확정하지 않음 |
| Data archive | Main Data Availability 및 ref. 26의 Southampton dataset 인용 | 원문 ref. 26에 DOI/직접 다운로드 링크 없음; 제목 기반 검색으로 검증 가능한 archive를 찾지 못함 |

이는 공개 원문/SI에서 **재현 입력을 확보하지 못했다**는 판정이지, 저자가 원자료를
가지고 있지 않다거나 dataset이 존재하지 않는다는 뜻이 아니다. Near-Gaussian이라는
서술은 external complex Gaussian fit, flat phase, lossless transmission의 증거가 아니다.
Guided Mode가 homogeneous bulk glass Gaussian인 것도 아니다. 실제 facet은 횡방향
불균일 Waveguide의 termination이므로 uniform planar Fresnel multiplier만으로
그 전체 scattering을 재현할 수 없다.

## 3. 최소 Reference의 선택과 독립성

[Pre-execution Plan](M4C_REFERENCE_PLAN.md)은 첫 수치 실행 전에 local commit
`c80197e`로 고정했다. 기존 PAE scalar Fresnel tests는 paraxial propagation만 검증한다.
Meep/NGSolve/Diffractio는 초기 환경에 없었다. 새 FE/Maxwell 구현은 하지 않았다.

선택: [tmm 0.2.0](https://pypi.org/project/tmm/0.2.0/)의 Snell 및 TE Fresnel API와
NumPy FFT. [저자 Source](https://github.com/sbyrnes321/tmm/blob/master/tmm_core.py)와
[저자 Test suite](https://github.com/sbyrnes321/tmm/blob/master/tests.py)를 검토했다.
Library 전체를 검증 완료했다고 주장하지 않고, 이번에 사용하는 subset을 Boundary
조건·정상/경사 입사·TIR 및 독립 적분으로 확인했다.

- Control: homogeneous n=1.5→1, 1310 nm, Ey(x)=exp(−x²/w²), w=1.365 µm,
  y-invariant 2D TE. Index/Phase/Reference plane 모두 명시 가정이다.
- z=0 및 5 µm에서 Ey, Hx, Hz를 복소수로 보존한다. Ex=Ez=Hy=0은 TE symmetry다.
  이는 실제 H/V 타원형 Mode나 3D Vector calibration을 검증하지 않는다.
- tmm의 exp(−iωt)를 프로젝트 exp(+iωt) convention으로 conjugate 변환한다.
  k_z의 outgoing evanescent branch는 Im(k_z)<0, exp(−ik_z z)로 감쇠한다.
- Plane-wave flux는 Re(k_z/k0)|A|²/(2Z0), 공간에서는
  −Re(Ey Hx*)/2를 적분한다. Incident power는 1 W/m으로 정규화한다.
  실제 guided-port power 또는 finite 3D beam power 1 W가 아니다.
- Independent check: SciPy adaptive quadrature + analytic Gaussian Fourier transform
  + Maxwell TE admittance boundary equation. tmm coefficient/FFT/production kernel을
  재사용하지 않는다. 같은 Planar Physics의 독립 구현·적분이지 다른 EM 모델/실험은 아니다.
- |kx|≥0.95 n1 k0의 incident spectrum은 제거하고 그 norm bound를 기록한다.
  Transmitted evanescent 성분은 유지한다. 제거한 norm은 1.0643e−20 이하다.

## 4. 실행 결과와 중단 근거

결과: `results/m4c_planar_control.json`; raw complex arrays: CI의
`m4c-planar-reference-evidence` 안 `m4c_fields_512.npz`, `m4c_fields_1024.npz`.
N=512/1024, window 80 µm, dx=156.25/78.125 nm. 최초 수치 실행 약 0.40 s.

| Metric | 결과 | 사전 기준 / 판단 |
|---|---:|---|
| E sampling relative L2, max | 2.94e−16 | <1e−6 Pass |
| Z0H sampling relative L2, max | 2.87e−16 | <1e−6 Pass |
| R / T (assumed interface only) | 0.041329895 / 0.958670105 | Fold Total Coupling 아님 |
| abs(1−R−T) | 0 (floating-point result) | <1e−10 Pass, 물리적 오차 0의 주장 아님 |
| Spatial vs spectral flux error | 2.23e−16 이하 | <1e−10 Pass |
| Independent E/H quadrature error / incident peak | 2.03e−6 | <1e−4 Pass |
| T / RMS sinθ quadrature relative error | 6.83e−14 / 1.05e−12 | <1e−4 Pass |
| Outgoing flux fraction at abs(θ)>0.1, FFT bins | 0.4827793213 | 두 Sampling 동일 |
| 같은 fraction, continuous quadrature | 0.5105569849 | Gaussian divergence guard와 다른 metric |
| 두 방식 fraction 절대 오차 | **0.0277776636** | **<0.02 실패 → Stop** |

11개 Gate 중 10개 Pass, `continuous_flux_angular` Fail이다. 모든 수치는 Synthetic
Control에만 해당한다. 실제 WAFT의 NA/전송률/고각 성분으로 해석하지 않는다.

원인: 같은 L에서 N만 두 배로 늘리면 Nyquist 범위는 늘지만 Δkx=2π/L는 그대로다.
0.1 rad 경계에서 spectral-bin 포함/제외의 staircase 오차가 두 Grid에 공통으로
남는다. 따라서 두 Sampling의 거의 완벽한 일치는 angular-tail accuracy의 증거가
아니다. 별도 quadrature가 이 blind spot을 드러냈다. 적분 R/T/부드러운 angular
moment가 정확해도 sharp threshold power fraction이 정확하다는 보장은 없다.

Plan의 중단 기준대로 Window 확장, bin integration, 추가 Field/Reflector 계산은
실행하지 않았다. 기준값도 바꾸지 않았다. 후속 재현 실행은 동일 Control/동일 두 Grid의
결과 보존 확인만 수행한다. 최초 실패 이후 Physics/metric 계산은 변경하지 않았다.
추가한 것은 runtime memory 기록과 실패를 보존하는 CI evidence checker다.

## 5. Engineering 판단과 추가 Reference

| 구분 | 이번 결론 |
|---|---|
| 이번에 검증한 범위 | 명시한 2D TE planar control의 E/H continuity, flux, TIR branch, selected-point complex field와 smooth angular moment. Sharp angular-tail metric은 미승인 |
| 현재 Tool에서 사용할 판단 | 기존 valid-domain Gaussian 사례는 기존 검증 범위에서 사용. M4B Proxy는 Domain Fail 유지. Guided MFD만으로 실제 Field를 대체하지 않음. Angular sampling과 spatial sampling을 별개로 예산화 |
| 추가 Reference가 필요한 주장 | Actual external Field/NA, Gaussian fit adequacy, reciprocal Target mode, finite reflector vector/diffraction/coating loss, normalized overlap, Total Coupling 및 full Package |

현재 자료로는 실제 두 Reflector 연결에 Gaussian 모델을 사용할 수 있는지 확정할 수 없다.
M4B의 Domain Fail은 **선언한 Proxy**에 관한 결과이며 논문 장치 실패가 아니다.
실제 Field 확보 후 complex fit과 Frozen Domain을 별도로 통과해야 production
Gaussian 평가의 후보가 된다. Fit을 잘했다는 이유로 Domain Guard를 생략하지 않는다.

## 6. 실행 Package / 재개 조건

`requirements-m4c.txt`, `scripts/m4c_planar_control.py`,
`scripts/check_m4c_stop.py`, `references/m4c_external_field_request.json`과 이 문서가
최소 실행 Package다. 마지막 JSON은 외부 Solver export 요청서이며 Adapter 입력이 아니다.

실제 실행에 필요한 최소 입력은 두 경로 중 하나다.

1. **Field export 경로**: 한 Port, 동일 기준면의 complex E/H Cartesian components,
   grid/units/phase convention/medium, incident guided power 및 outgoing flux 제공.
   Target는 별도로 reciprocal accepted mode의 같은 정의가 필요하다.
2. **Reproducible model 경로**: 정확한 n(x,y,z,λ) 또는 material/taper/termination geometry,
   polarization/eigenmode/source normalization, boundaries/PML, mesh convergence 조건.
   논문에 사용된 Lumerical FDE + 국소 3D FDTD 등 검증된 외부 경로를 우선 검토한다.
   현재 환경에는 해당 license/session이 확인되지 않았다. 전체 mm Fold는 제외한다.

Lumerical을 쓰더라도 eigenmode를 얻은 것과 air-side outgoing field를 얻은 것은 다르다.
국소 facet/interface simulation 후 homogeneous external plane에서 export하고,
반사/투과/흡수/측면 방사 power accounting과 두 mesh/plane convergence를 보고해야 한다.
Plane 이동 시 phase와 좌표를 함께 전파하며 Fixed Target에 fit하지 않는다.

재현 (Python 3.12, Linux):

```bash
python -m pip install -r requirements-m4c.txt
PYTHONPATH=src python scripts/validate.py
# 기존 61 tests / Benchmark / Adapter Pass
python scripts/m4c_planar_control.py
# 예상 exit 1: frozen angular-tail criterion FAIL. 수정해 숨기지 않는다.
python scripts/check_m4c_stop.py 1
# evidence check Pass = 알려진 중단 결과/자원/Hash 확인. Reference Pass가 아님.
```

CI dedicated step은 실제 exit code를 checker에 전달한다. 예상 실패 원인 외 다른
실패 또는 잘못된 성공도 CI에서 거절한다. CI success와 **Control acceptance Fail**은
분리하여 Artifact와 Job Summary에 기록한다. 정확한 release HEAD/run/Artifact는 PR
본문을 따르며, Artifact provenance는 실제 체크아웃 SHA와 관련 Source Hash를 포함한다.
후속 지시문은 [NEXT_TASK.md](NEXT_TASK.md). Main 병합/후속 실행은 하지 않았다.
