# M4-B — Literature-guided one-case application

2026-11-10 KST. Base PR #7: `a76fd01ac28443fe71223a2ad1c7329f8b12f0a6`.
사용자가 문헌을 근거로 값 선택·적용을 요청하여 **M4B-LIT-001**을 평가했다.
실제 회사 사례 M4A-001은 변경하지 않았다. 이 사례는 **Literature-guided Gaussian
Proxy + 명시적 Engineering 가정**이며 논문 장치의 재현이나 실제 제품 평가가 아니다.

## 문헌과 값의 선택

L1: Ipsita Chakraborty et al., *Glass Interposer Assisted Edge Coupling to SiN
Photonic Integrated Circuits*, ACS Photonics 13, 2120–2127 (2026).
[DOI 10.1021/acsphotonics.5c02702](https://doi.org/10.1021/acsphotonics.5c02702),
[저자 논문 원문 / PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13088358/).
2026-11-10 원문 Table 1의 TE / 1310 nm 행을 확인했다. CC-BY-4.0.

이 논문은 Glass WAFT와 SiN PIC를 직접 연결한다. 본 Tool의 두 Curved Reflector
구조는 논문에 없으므로 별도 가정이다. 여러 논문의 장치 조건을 혼합하지 않았다.

| 항목 | 적용값 | 출처 / 성격 |
|---|---|---|
| Wavelength | 1310 nm | L1 Table 1의 해당 동작 조건 |
| Glass WAFT PIC 측 Width | Horizontal 3.79 µm, Vertical 2.73 µm | L1 Table 1의 guided-mode MFD scale |
| Target Gaussian MFD (t,s) | (2.73,3.79) µm | 위 Width를 외부 1/e² intensity Gaussian diameter로 해석하는 **가정** |
| Source Gaussian MFD (t,s) | (2.73,3.79) µm | Width-matched PIC Proxy를 선택한 **가정**; 논문이 제시한 SiN MFD가 아님 |
| External Ambient | n=1 | Air에서 전파하는 제안 Fold의 **가정** |
| Phase Curvature | C_t=C_s=0 at both Port planes | 유리한 Flat-Phase Gaussian screen을 위한 **가정**; 논문값이 아님 |
| Polarization | horizontal TE label, scalar_ignored | [t,s] Jones=(0,1) 표기만 보존; Vector/Coating 전파는 미계산 |

논문은 Fiber 쪽 Mode와 PIC 쪽 Mode를 구별한다. Fiber 쪽 10 µm를 PIC 면의 값으로
가져오지 않았고, guided effective index 1.525025를 외부 Ambient n으로 넣지 않았다.
Table의 MFD만으로 실제 외부 Complex Field나 그 Gaussian 적합성이 확정되지 않는다.
Interface를 지난 Field의 Width/Phase/Vector 성분 및 MFD 정의의 일치성은 추가 검증이
필요하다. 따라서 Input의 Mode record는 `assumed`이며 `measured`로 표기하지 않았다.

각 Port d=+X, s=+Y, t=s×d=−Z로 선택했다. Horizontal=Y는 s,
Vertical=Z는 t에 대응하므로 Input은 [t,s]=[2.73,3.79] µm 순서다.
수치 변환은 µm→m, nm→m를 명시적으로 수행했다. q를 중복 제공하지 않아 기존
M1의 큰 Mode에 해당하는 q가 남지 않도록 했다.

## 선택한 후보 Geometry / Package — 문헌값 아님

기존 검증된 M1/M3-A의 single-channel candidate를 명시 가정으로 재사용했다.
새 Optimizer나 Topology Synthesis는 실행하지 않았다.

| 항목 | 선택값 |
|---|---|
| Source / Target Position | (0,0,0) / (2,0,2) mm |
| M1 / M2 Vertex | (1,0,0) / (1,0,2) mm |
| 경로 | +X → +Z → +X, 길이 1–2–1 mm |
| Illuminated Normals | M1=(−1,0,+1)/√2, M2=(+1,0,−1)/√2 |
| 각 면 Principal Curvatures (t,s) | (353.5533906,707.1067812) m⁻¹ |
| 각 면 Half Apertures (t,s) | (0.7,0.5) mm |
| Package AABB | min=(−1,−1,−1), max=(3,1,3) mm |
| Keepouts / Required Clearance | 명시 가정 [], 10 µm |

Nominal Bounds와 Surface를 포함하는 Body Envelopes도 기존 candidate 값으로
가정했다. 모든 값과 출처가 `examples/m4b_literature_proxy.json`에 들어 있다.
이 Package는 논문의 고밀도 Pitch/채널 배열을 재현하지 않는다. 두 면은 서로 다른
principal curvatures를 가진 quadratic patch이며 두 spherical mirror가 아니다.
입력된 Source/Target를 결과에 맞춰 이동하거나 Mode를 Fit하지 않았다.

## 실제 실행 결과

기존 `evaluate_external`과 `gaussian_port_domain`을 그대로 호출했다.
`results/m4b_literature_001.json`은 문헌 위치, 가정, 입력 Hash, per-Port 진단과
원래 Adapter Result를 분리해 보존한다.

| 항목 | 결과 | 해석 |
|---|---|---|
| Input Contract | Pass | 선언한 Nominal 형식의 입력으로 실행 가능; 실제 Field 검증을 뜻하지 않음 |
| Geometry | Pass | 선택한 Fixed-Port Chief Path와 두 Surface의 반사 경로 검사 통과 |
| Design Bounds | Pass | 선택한 Nominal Bounds 안에 있음 |
| Gaussian Model Domain | **Fail** | 선언한 Proxy의 Divergence가 기존 0.1 rad guard 초과 |
| Approximate Overlap | **Uncomputed / null** | 유효하지 않은 모델 영역에서 효율 수치를 만들지 않음 |
| Envelope Geometry | Pass | 명시 AABB와 Patch 범위의 검사만 통과 |
| Full Package / Actual Applicability / Total Coupling | Uncomputed | Finite-Beam·Backing·Interface·Coating·Vector/실제 Mode 검증은 미수행 |

각 Port에서 Flat-Phase Gaussian의 독립 수식 θ=2λ/(π n MFD)를 계산하면
[t,s]=[0.3054842131,0.2200453567] rad다. 기존 per-Port precheck와 일치한다.
현재 λ/n에서 0.1 rad 기준을 만족하는 waist MFD 하한은 각 축 약 8.339719 µm다.
이는 **현재 Gaussian 가정의 수학적 비교**이며 실측 NA나 논문 장치의 성능 판정이 아니다.

주어진 Gaussian Width에서 θ²=(λ/(π n w))²+(Cw)²이므로 Flat Phase는 이 모델의
가장 작은 Divergence를 준다. Phase를 바꾸거나 기준면만 이동하여 free propagation한
동일 q로 바꾸는 것으로 asymptotic Divergence가 낮아지지는 않는다. Guard를 바꾸지 않았다.
단, guided Width→외부 Gaussian 자체가 가정이므로 실제 외부 Field의 NA를 확정한 것은 아니다.

이 결과는 **논문 장치가 불가능하다거나 두 Reflector 연결이 불가능하다는 증명은 아니다**.
논문의 Coupling Loss를 가져와 이 Fold의 Loss 또는 Overlap으로 사용하지 않았다.
Target만의 Gaussian precheck도 Fail이므로 선택한 PIC Source Proxy를 변경하는 것만으로
현재 조건에서 Target Domain 문제를 해결할 수 없다.

## 검증과 재현

```bash
PYTHONPATH=src python -m photonic_architecture_explorer.external examples/m4b_literature_proxy.json --output /tmp/m4b-adapter.json
# exit 1: expected domain rejection, not a test failure
PYTHONPATH=src python -m photonic_architecture_explorer.inspector --input examples/m4b_literature_proxy.json --output results/m4b_literature_inspector.html
PYTHONPATH=src python scripts/validate.py
```

한 Data-contract Regression을 추가했다. H/V→t/s 순서, assumption provenance,
독립 Gaussian 식, Fixed Ports/입력 불변, Geometry와 Domain의 분리 및 Overlap 보류를
검사한다. 기존 Physics/Adapter/Guards/Fixtures/Tests는 변경하지 않았다.
Browser CI는 기존 화면 검증에 더해 기존 Python CLI로 이 사례를 재평가·재렌더하고,
예상 exit 1과 기록된 Result의 일치, Desktop/Mobile에서 Domain Fail·Overlap 보류를 검사한다.
UI 소스와 Optical Solver의 변경은 없다. 실제 CI/Artifact는 해당 PR의 정확한 HEAD를 따른다.

## 다음 최소 Astra 검토 제안 — 미실행

현재는 **선택한 Gaussian Proxy가 모델 밖이라는 재현 가능한 근거**가 생겼다.
사용자가 이 Mode scale의 실제 Fold 성능을 요구할 때 Astra Work로 다음 Gate를 제안한다.

1. 한 WAFT/PIC 외부 기준면의 Complex Field 또는 재현 가능한 외부 Mode/Interface 모델부터
   확보한다. Table MFD를 곧바로 실제 Air Field로 간주하지 않는다.
2. 한 Mode의 planar glass/air interface control로 시작하고 두 Sampling에서 Field·Flux·
   Angular Content를 비교할 수 있는 검증된 외부 Solver/Library 경로를 결정한다.
3. 지원 Geometry·Material·Polarization과 오차 예산을 고정한 뒤에만 한 Mirror 경계 검증을
   별도 범위로 제안한다. MM-scale 전체 Fold의 Maxwell 계산을 즉시 시작하지 않는다.
4. 계산 전에 예산·성공/중단 기준을 고정한다. 필요한 Field/외부 Tool이 없거나 새로운
   FE Space/범용 Solver 구현이 필요하면 확보한 결과를 보존하고 실행 Package만 제안한다.

M4A-001 실제 입력은 계속 미제공이다. M4B-LIT-001은 그 입력을 대체하지 않는다.
Main 병합과 후속 개발은 이번 작업에서 실행하지 않는다.
