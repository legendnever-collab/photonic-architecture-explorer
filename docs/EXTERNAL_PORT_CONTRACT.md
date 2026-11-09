# External Optical Port Contract — M25-1

이 Contract는 실제 PIC SSC ↔ Glass Waveguide의 **external field reference plane**을
정의한다. Guided effective index / core 내부 MFD를 external ambient Gaussian에
직접 넣지 않는다. Device facet, SSC, 굴절계면을 지난 field와 reciprocal accepted
Target field를 같은 물리적 의미로 제공해야 한다. 계면 손실은 별도 항목이다.

## 좌표·단위·고정 조건

Right-handed world XYZ, 길이 m, wavelength λ0는 vacuum m, angle rad,
curvature C=1/R 및 surface κ는 m^-1. 두 curvature는 서로 다른 물리량이다.
각 Port의 d는 Source→Target 전파 방향, s는 transverse sagittal unit vector,
t=s×d이다. Target outward normal을 d로 사용하지 않는다. X/Y MFD를 사용하려면
그 X/Y가 world 축인지 local t/s인지 명시하고 local transverse basis로 변환한다.
Arbitrary rotated ellipse / t-s cross term은 현재 지원하지 않는다.

Port reference plane은 origin=position, normal=d인 external transverse plane.
이 plane에서 Position/Direction/Mode/ambient/λ0를 모두 고정한다. Reference plane
변경은 q를 물리적으로 전파시키고 위치도 변경하는 명시적 새 입력이다.
Target를 계산된 output에 맞춰 이동하거나 Mode를 재정의하지 않는다.

## 입력 필드

| Field | 표현·필수 조건 | 미제공/지원 범위 |
|---|---|---|
| λ0 | Source/Target 공통 양의 finite vacuum wavelength | 미제공 Uncomputed; mismatch Fail |
| Ambient n | 양의 finite 실수, homogeneous external medium | core n_eff 대입 금지; 불균일/복소 medium 지원 밖 |
| Position | Source/Target 각각 world [x,y,z] | 항상 Fixed |
| Propagation d | nonzero finite 3-vector; 정규화는 명시 | Target는 incoming propagation |
| Transverse s | d에 수직; t=s×d | 공통 coplanar sagittal 필요 |
| MFD_t/s | 해당 plane의 1/e² **intensity diameter**, w=MFD/2 | FWHM/second-moment/D4σ면 정의 및 변환 근거 필요 |
| Phase | C_t/s=1/R_t/s, flat=0 explicitly; 또는 ordinary q_t/s | phase 누락 시 waist로 가정하지 않음 |
| q 입력 | 각 q=[real,imag] m; Im(q)>0 | reduced q/n과 구별; q와 MFD+C 동시 제공 시 consistency 검사 |
| Polarization | local basis의 Jones vector 또는 scalar ignored라는 명시적 가정 | engine은 vector field/TE-TM/coating phase를 전파하지 않음 |
| Reference plane | plane id, external side/material, frame, position과 d | facet plane/guided plane/external plane 혼용 금지 |
| Mode evidence | 측정/EM simulation/공급사 complex field와 plane, Gaussian fit 근거 | MFD만으로 Gaussian field 적합성 확정 불가 |
| Available package | world-coordinate closed volume 및 keepouts | empty keepout도 명시적 입력; 현재 mechanical engine 없음 |
| Reflector constraints | 두 면 각각 vertex/normal/κ_t,s/aperture bounds, surface prescription | 범위 누락 시 해당 engineering feasibility Uncomputed |
| Reflector bodies | backing/support envelopes, required clearance | local patch와 실체 body를 구분 |

Blank sheet: `examples/external_ports_unprovided.json`. 물리 입력의 value는 전부
null이고 provenance=unprovided이다. q와 MFD+C는 **대안 표현**이다. 두 표현을 모두
채울 필요는 없다. ranges/uncertainty는 uncertainty에 단위와 함께 기록하되,
현재 point solver는 범위를 자동 sweep하거나 대표값으로 바꾸지 않는다.
이 sheet는 입력 수집 양식이며 이번 단계에서 full external adapter는 구현하지 않았다.
`gaussian_port_domain`은 MFD+C의 **per-Port divergence precheck**만 수행한다.

## 출처·상태와 결과 의미

각 물리값에 value, unit, provenance, source, uncertainty를 보존한다.
provenance: measured / supplied / independently_validated / simulated / assumed /
synthetic / unprovided. 출처 및 검증 범위를 추가로 명시한다. simulated라는 태그
자체는 independent validation을 뜻하지 않는다. 본 단계의 실제 입력은 전부 unprovided,
M1/M2는 synthetic이다. Assumed 값으로 계산했다면 결과에 assumption을 상속한다.

Result state는 별도 필드다: Computed=명시 모델에서 계산됨,
Approximate=근사 및 domain 명시, Uncomputed=null+reason, Fail=invalid/outside supported
model 또는 해당 Geometry 제약 위반. Fail은 architecture 자체가 불가능하다는 증명이
아니다. Pass는 특정 검사 통과이며 실제 제품 성능의 합격이 아니다.

Geometry / Gaussian domain / normalized Mode Overlap / physical losses /
package feasibility / fabrication·yield를 따로 표시한다. 알 수 없는 loss를 0으로
채우거나 ideal normalized overlap을 total coupling으로 승격하지 않는다.

## Phase·Gaussian fit의 최소 증거

1/q_j=C_j-i λ0/(π n w_j²), q=z+i z_R, z_R=π n w0²/λ0.
Positive C와 negative C는 PHYSICS.md의 exp(+iωt), exp(-ikz) convention을 따른다.
q와 C는 입력 plane에 정의한다. Beam waist에 있다고 선언할 때만 C=0이다.

실제 Mode의 Gaussian 적합성은 동일 plane/basis에서 complex amplitude와 phase를
함께 fit하고 normalized field overlap, phase residual, fit window/grid convergence를
보고해야 한다. 허용 오차는 요구 coupling/error budget에서 정해야 하며 이번에
임의 threshold를 정하지 않는다. Intensity MFD만 있는 경우 fit 적합성 Uncomputed.
Polarization/evanescent/high-NA/nonseparable 성분이 중요하면 Path C 검토가 필요하다.
