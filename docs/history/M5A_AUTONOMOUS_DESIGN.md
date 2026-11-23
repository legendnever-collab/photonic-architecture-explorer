# M5-A — Two-Port Autonomous Design

## 달성한 Design Loop

Source/Target 정보만으로 Vertex, Illuminated Normal, Tangential/Sagittal Curvature와
개념 Aperture를 자동 설계하고 기존 Geometry/Gaussian/Adapter로 검사한다.
사용자는 Reflector 또는 Solver 설정을 입력하지 않는다.
`pae-design` 한 번으로 JSON과 독립 실행 가능한 Read-only HTML을 생성한다.
HTML은 기존 Inspector의 동일한 Quadratic Patch/Chief Path 표시를 재사용한다.

- Input: [Two-Port Synthetic Example](../../examples/m5a_two_ports.json)
- [열어볼 Report](../../results/m5a/design.html), [Engineering JSON](../../results/m5a/design.json)
- [계산 전 범위·예산·순위 계약](M5A_DESIGN_CONTRACT.md)
- [원격 복구 기록](../../results/m5a_recovery.json)

## Synthetic 결과와 Engineering 판단

M1과 같은 Port: λ=1310 nm, external ambient n=1, radii (8,12) µm,
Source (0,0,0), Target (2,0,2) mm, 모두 +X 전파, 명시 Flat Phase.
이 Flat Phase는 Synthetic 입력이다. 미제공 Phase를 보완한 값이 아니다.

36 Geometry에서 real exact-q branches 120개를 평가했다. 56개는 기존 Guards 통과,
64개는 Footprint–Curvature Guard로 거절했다. 6 Geometry는 한 축 이상에 real
exact-q solution이 없었다. 실제 실행 예제의 거리 set은 6개이며 일반 상한은
8×8 Geometry / 256 Curvature combinations다.

| 대표 | ID | Segment Lengths [mm] | η_mode | max 3w·κ | max projected radius [µm] |
|---|---|---|---:|---:|---:|
| 추천 | G036-B1 | 5.657 / 9.526 / 5.657 | ≈1 | 0.078205 | 296.62 |
| 대안 2 | G029-B1 | 2.828 / 4.168 / 2.828 | ≈1 | 0.078239 | 152.39 |
| 대안 3 | G022-B1 | 1.414 / 2.165 / 1.414 | ≈1 | 0.078426 | 89.18 |

첫 후보는 Footprint–Curvature 수치가 더 작지만 Path 20.840 mm로 가장 길다.
대안은 각각 9.825/4.993 mm로 더 짧고 절대 Beam Footprint도 작다. 차이가 작은
slope를 우선 비교하는 사전 고정 Lexicographic 정책의 결과이며, 실물 성능 우위나
Robustness의 유의미한 차이를 입증하지 않는다. 임의 가중합 Score와 최적해 주장은 없다.
각 Geometry의 최상위 branch 중 3개를 선택한다. 정확한 값·Mirror prescription·
모든 거절 사유·입력/가정은 JSON에 있다.

M1의 1–2–1 mm Relay와 1000 m⁻¹ powers도 자동 생성 family에서 재현된다.
기존 Reflector fixture 값을 Generator에 넣지 않았다. 개념 Aperture는 자동 4w로
설계하므로 M1 수동 Aperture와 동일하다는 주장은 하지 않는다.

## 수학과 재사용 경계

두 Vertex는 Source forward ray와 Target backward ray 위에 놓는다.
Normal=unit(d_out−d_in), 기존 Engine의 specular law/closure/patch interception
검사로 검증한다. 각 축에 두 개의 실수 power를 갖는 exact-q 조건을 풀어 최대
2개 branch를 얻는다. 독립 t/s 조합은 최대 4개다. 상세 수식은 사전 계약에 있다.

`external.adapt_ports`는 기존 Adapter의 Port 파싱을 추출한 것이다. 단위·출처·
기준면·Phase·Mode Evidence 규칙은 바꾸지 않았다. 생성된 처방은 수동 입력과 같은
`evaluate_external`을 거친다. Gaussian/Geometry/Solver/Package Engine과 Frozen
Guards, 기존 Fixtures 및 Historical Results는 변경하지 않았다.

실제 Package가 없으면 `Conceptual Geometry / Package Uncomputed`다. 4w Aperture는
자동 개념 처방이며 실제 제조 가능한 Aperture/Body/clearance를 만들지 않는다.
명시된 Package envelope에서 실패한 후보는 거절한다. Package 일부 검사가 Pass여도
전반적인 제작 가능성을 Pass로 승격하지 않는다.

## 검증 범위

Baseline PR #12: 61 tests, Benchmark/Adapter Gate Pass. M5-A: **76 tests**
(기존 61 + 신규 15), Benchmark/Adapter Gate Pass. 로컬 실행 약 3 s,
3개 evidence cases를 각각 2회 생성하는 bounded run 약 0.2 s (<30 s).
정확한 시간/HEAD/Source Hash는 각 실행 manifest와 CI artifact를 따른다.

| 검증 | 독립 근거 / acceptance |
|---|---|
| Fixed Ports | 원본 records deep equality, 재실행 JSON 일치, rigid rotation/nonwaist q 입력 |
| Reflection / Closure | NumPy의 직접 반사식 및 segment vectors, absolute tolerance 1e-12 |
| Power / q | 독립 ABCD matrix product; q relative error <1e-10; 알려진 +/- powers를 역으로 복구 |
| Surface curvature | 독립 실제 Quadratic Surface ray derivative; relative tolerance 2e-6 |
| Field / Overlap | 기존 독립 FFT Fresnel + quadratic phase screen; 세 후보 모두 두 Window/Grid에서 eta agreement 9 decimal places, 두 결과 10 places |
| Normalization | FFT 각 축 integrated power=1, 11 decimal places |
| Negatives | Missing Phase, zero/nonunit/NaN direction, high divergence, coincident/skew/rolled Ports, no-real-q branch, Package rejection |
| Failure artifacts | CLI 성공→invalid JSON에서 이전 Overlap 제거; 기존 evidence directory 재사용 거절 |
| Manual Solver | 모든 대표 후보의 수동 Adapter 결과와 전체 JSON exact equality |
| Report | embedded JSON equality/escaping; CI browser에서 3 후보×3 Projection, Desktop/Mobile, 실패 시 Overlap 없음 |

Fresnel reference는 1D separable scalar paraxial phase-screen 검증이다.
두 grid는 (N,L)=(16384,4 mm), (32768,6 mm); 경계/샘플링 변화에 민감하지 않은
선정 후보의 수치 일치를 검사한다. 실제 finite reflector Maxwell 검증이나 M4-C의
sharp angular-tail 적분 검증을 대체하지 않는다. 이전 0.0277776636 > 0.02 Fail/Stop을
유지하며 이 수치 오차를 실제 WAFT의 물리적 실패로 해석하지 않는다.

Local Chromium은 실행환경의 socket 제한으로 시작하지 못했다. Browser Pass 여부는
원격 CI의 `browser.json`과 실제 스크린샷으로 확인하며 local Pass로 표기하지 않는다.

## 재현 및 실행 증거

```bash
python -m pip install -e '.[test]'
pae-design examples/m5a_two_ports.json --output-dir results/my-design
# 결과 검토: results/my-design/design.html (서버 없이 열기)
python scripts/validate.py
# 실행마다 아직 존재하지 않는 디렉터리 지정; 기존 파일을 증거로 재사용하지 않음
python scripts/validate_m5a.py --output-dir results/runtime-m5a-001
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install --with-deps chromium
node scripts/check_design.cjs results/runtime-m5a-001
```

`validate_m5a.py`는 exclusive directory 생성 후 Running marker를 쓰고, 기대한
Computed/Uncomputed/Fail 및 반복 실행 일치를 확인한 뒤에만 Pass manifest를 쓴다.
HEAD, dirty flag, source hashes, 생성 artifact hashes, Python, CI run ID를 기록한다.
ImportError·예외·시간 예산 초과는 nonzero exit이며 정상적인 design rejection과 구분한다.
`pae-design`은 후보 생성 성공이면 0, 실패/미제공이면 1을 반환한다.

Committed HTML/JSON은 재현 가능한 Synthetic snapshot이며 CI 실행으로 위장하지 않는다.
현재 HEAD 검증은 CI의 `runtime-m5a-ci/provenance.json` 또는
`m5a-design-evidence/provenance.json`에 기록된다. CI links/IDs는 Draft PR에 기록한다.

## Recovery와 미검증 영역

| Remote | HEAD | Base | CI recovered |
|---|---|---|---|
| Main | f42a6b1701eeb8c0500092a95e0b4202be86aa8b | — | 42910559738 success |
| #10 M4-C.1 | e164f7aa3c255a03f9c54f11af699b49c86c78e6 | Main | 42920925168 success |
| #11 M4-D | cfd7f4087089faabbe7c6c323637ddad84eda12e | #10 | 43590592868 success |
| #12 Product Charter | c1525d7750476d03f675feee12a3198b1a76c02f | Main | 43629756434 success |

#10/#11/#12 모두 Draft/unmerged로 복구했다. M5-A는 #12를 Base로 하며 #10/#11을
병합하거나 cherry-pick하지 않았다. Product Charter는 byte-for-byte 보존한다.
M4-C.1/M4-D의 Window 검증/실제 입력 audit는 별도 진행 경로다.

현재 Tool에서 가능한 판단: 명시 Gaussian Port 조건 아래 Two-Reflector Geometry와
Gaussian Domain을 만족하는 bounded 후보, Mode Matching, Footprint 및 Path 비교.
추가 외부 증거가 필요한 주장: 실제 SSC/Glass WG vector field의 Gaussian 적용성,
Interface/Coating/Polarization/finite-aperture aberration losses, Total Coupling,
Package/Assembly tolerance/Fabrication Yield/Patentability. 모두 Uncomputed다.
정확한 q matching family에서 후보가 없다고 Approximate matching이나 다른 Topology까지
불가능하다고 결론 내리지 않는다. 다음 M5-B는 [별도 지시문](NEXT_TASK.md)이며 자동 실행하지 않는다.
