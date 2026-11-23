# M7-B — Guarded Near-Match Feasibility

## 실행 전 고정한 탐색 계약

Base는 M7-A #26 HEAD 98b9f6f3cf46b800f3f508a2218e32d54d0afd5a다.
#25와 #26은 Draft이며 각 CI 44071463656, 44072816225는 성공이다.
Main은 e40e5b8b7acc6b14e1630b3f9ea2ed8768c5316f다.
M6-E의 Off-Vertex Field Reference는 Reference Not Ready다.

입력은 examples/m7a_smf_glass_proxy.json 한 개다. 두 Port와 기존 distances()의
36개 Vertex 조합을 고정한다. 각 Geometry에서 네 개의 무차원 변수 u를 [-1,1]로
탐색한다. 각 반사면의 입사 반경 w와 입사각 cosine c에 대해
κt = u_t·0.15c/(3w_t), κs = u_s·0.15/(3w_s)로 설정한다.
따라서 Power 범위는 |Pt| ≤ 0.1/w_t, |Ps| ≤ 0.1c/w_s다.
구현은 부동소수점 경계 오차를 피하도록 한계에 (1−1e−10)을 곱한다.
M2의 반경은 각 M1 후보를 기존 Gaussian으로 전파해 산출한다.
Aperture는 기존 4w concept prescription을 사용한다.

SciPy 1.17.0 differential_evolution, best1bin, population 32,
maxiter 120, mutation (0.5,1), recombination 0.7, tol=0, atol=0,
polish=False, single worker, immediate update다. Seed는 Geometry 번호+7100이다.
초기 32개는 동일 Seed의 uniform [-1,1]이고 첫 개는 Flat (0,0,0,0)이다.
Geometry별 최대 3,872회, 합계 최대 139,392회 Adapter 평가로 제한한다.
모든 후보는 evaluate_external로 검사하고, 합격 후보만 Overlap 목적함수에 쓴다.
거절 시 목적값 2를 반환하며 실패 단계와 사유만 집계한다. 수치 오류는 실행 실패다.
전체 실행 600 s 제한, 제한 도달 시 Fail manifest를 남긴다.
재실행은 동일 입력·Seed의 재현에 한정하며 범위·Seed 변경은 새 계약을 요구한다.

Geometry별 최선 후보를 보존하고 Overlap 내림차순으로 상위 세 Geometry를 검산한다.
이는 Benchmark 비교 순서다. 개념 기준은 η ≥0.90이며 약 0.458 dB Mode Mismatch다.
독립 NumPy ABCD 및 Gaussian complex-field quadrature를 사용한다.
q 상대오차 ≤1e−10, Specular direction 절대오차 ≤1e−12,
Overlap 절대오차 ≤1e−8와 두 Grid의 차이 ≤1e−8를 요구한다.
각 후보의 전체 Adapter 결과에 모든 반사면 Footprint·Divergence를 저장한다.
유한 탐색의 최고 관측값이며 전역 최적성 증명은 추가 근거를 요구한다.

## 재현

```bash
python -m pip install -e '.[test]' scipy==1.17.0
python scripts/m7b_near_match.py --output-dir /tmp/pae-m7b-new
```

출력 디렉터리는 새 경로를 사용한다. manifest.json은 실행 상태, 입력·Source Hash,
HEAD, 버전과 실행 시간을 기록한다. result.json은 exact-q 기준, 평가 건수,
거절 사유와 Geometry별 최선 후보를 저장한다. Actual Applicability, 실제 Assembly
Tolerance, Package Yield 및 Total Coupling은 Uncomputed다.

## 결과와 Engineering 판단

Exact-q 기준을 재현했고 기존 102개 회귀가 통과했다. 첫 실행에서 124,160회 Adapter
평가 중 95,533회가 유효했다. 이는 재방문을 포함한 평가 횟수다. 36개 Geometry 중
32개에서 유효 후보를 찾았고, 4개 Geometry의 최선값이 0.90 이상이었다.
Divergence 첫 실패는 26,496회, unintended reflector interception은 2,131회다.
Footprint–Curvature는 위 Parameterization으로 범위를 제한했다.

| Geometry | 최고 관측 Overlap | Mode Mismatch [dB] | Path [mm] |
|---|---:|---:|---:|
| G036 | 0.99993665 | 0.000275 | 20.840 |
| G029 | 0.99961272 | 0.001682 | 9.825 |
| G030 | 0.93351521 | 0.298786 | 15.272 |
| G023 | 0.91246709 | 0.39783 | 7.248 |

상위 세 후보는 Specular Closure, 독립 ABCD 및 두 Grid의 Complex Field 적분을 통과했다.
G036의 M1/M2 max 3w·κ는 0.14056631 / 0.14999866이다.
G029의 M2 값도 0.14999970으로 가드에 가깝다. 이 가드의 여유는 조립 공차나
Aberration 오차를 정량화하지 않는다. Nominal Gaussian 결과로 실제 Robustness나
Total Coupling을 주장할 근거는 아직 부족하다.

Near-Match는 이번 Proxy에서 높은 정규화 Overlap을 유지하며 가드를 만족하는 후보의
존재를 확인했다. 실제 Target q는 고정이며 도착 q의 차이를 Overlap 적분에 반영했다.
G023은 이번에 관측한 기준 충족 후보 중 최단 경로다. G036은 이번에 관측한 최고
Overlap이다. 이 Benchmark의 순서는 현재 Production Recommendation 정책과 별개다.

G031–G034는 초기와 첫 세대에서 유효 후보를 찾지 못해 동일 penalty에서 조기 종료했다.
Optimizer의 success 메시지는 수치 종료 상태이며 이 네 Geometry의 실현 가능성
판정으로 사용하지 않는다. 나머지 32개는 120세대 예산을 소진했다.
탐색의 수렴이나 전역 최적성은 이 결과로 확정하지 않는다.
첫 실행 시간은 약 75 s였다. 독립 검산을 보강한 동일 Seed 재실행 기록과 최상위
처방은 [실행 증거](../../results/m7b_near_match.json)를 따른다.

실행 증거의 `manifest.head`는 계산 당시의 로컬 Commit
`efa87859e460d1a77b41b063a7197bcf1f82db86`을 식별한다. GitHub 게시 Commit과는
별개이며, 게시된 Benchmark·Production Source·입력은 manifest의 SHA-256으로
대조했다. `contract_sha256`은 결과를 추가하기 전 탐색 계약을, `result_sha256`은
실행 시 생성한 원본 result.json을 식별한다. 저장된 실행 증거는 그 원본의 요약과
상위 세 후보의 전체 처방·평가·독립 검산을 포함한다. 원본은 위 명령으로 재생성한다.

## 다음 개발 지시문

**M7-C — Near-Match Workflow Integration Design**, 추천 모델 Sol Work.

1. #25·#26·M7-B Draft의 최신 HEAD, Base와 CI를 복구하고 Product Vision과 이 결과를 읽는다.
2. 기존 Two-Port Design에서 exact-q 유효 후보가 0개일 때 적용할 Near-Match fallback의
   최소 통합안을 작성한다. 사용자 Solver 선택과 Target 변경을 요구하지 않는다.
3. 이번 75 s Benchmark를 근거로 실행 시간과 응답 방식, 실패·취소·재시도 처리,
   입력 SHA 및 후보·가정 추적 계약을 정한다. 탐색 축소가 필요하면 같은 36개 Geometry의
   일반적 규칙으로 정의하고 M7-A와 기존 Frozen 사례에서 품질과 시간을 검증한다.
4. 기존 Overlap 순위와 구간 기준에 따라 비교하고, 가드에 근접한 후보의 수치와 모델
   한계를 보여주는 방법을 정한다. 고정 0.90은 이번 개념 판단 기준으로 기록한다.
5. 최소 변경의 Draft PR과 검증 결과를 제출한다. Main 병합은 별도 승인 후 진행한다.
