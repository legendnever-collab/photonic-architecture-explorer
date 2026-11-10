# M4-C.1 — Angular Metric Verification & External Input Readiness

2026-11-11 KST. **Synthetic Control의 Angular-tail 수치 검증은 Pass. 실제 입력은 미제공.**
Main `f42a6b1701eeb8c0500092a95e0b4202be86aa8b`에서 분기했다.
[사전 계획](M4C1_VERIFICATION_PLAN.md)은 추가 Window 계산 전 commit `eb8c7c7`로 기록했다.
기존 M4-C 결과/계획은 유지한다. 기존 실패는 WAFT의 물리적 실패가 아니다.

## Recovery와 원인

Main CI [42910559738](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/42910559738)
의 4 jobs가 success이고 4 Artifacts가 유효함을 확인했다. Planar Artifact
13807885298을 다운로드하여 ZIP digest, provenance HEAD, 모든 Source Hash를 Main Git tree와
대조했다. [Recovery record](../results/m4c1_recovery.json)에 식별자와 범위를 기록했다.
Main의 61 tests, Benchmark/Adapter Gate를 재실행했고, 역사적 M4-C JSON은 삭제 후
새로 생성하여 저장된 파일과 byte-identical임을 확인했다. 알려진 단일 Gate Fail 및
exit 1, 절대 오차 **0.027777663568040678**, 기준 **<0.02**를 그대로 재현했다.

Δkx=2π/L, Δu=λ0/L (u=kx/k0). 같은 L에서 N을 늘리는 것은 dx와 Nyquist 범위만 바꾼다.
0.1 rad 경계의 이산 bin 포함/제외 오차는 그대로이므로 Sampling 일치가 정확성을
입증하지 못한다. Bin-boundary 보간을 새로 작성하는 대신 기존 grid/synthesis에 optional
window_m만 추가했다. Default L=80 µm 및 기존 numerical model은 동일하다.

## 새 검증 결과 — M4C1-TE-WINDOW-001

결과 snapshot: [m4c1_window_control.json](../results/m4c1_window_control.json).
Raw spectra/complex arrays/provenance는 별도 CI Artifact `m4c1-window-reference-evidence`에 있다.
독립 Continuous Quadrature의 tail fraction은 **0.5105569849105428**이다.

| Window L, µm | N (두 Sampling) | Δu | FFT tail fraction (fine) | 독립 적분 대비 절대 오차 |
|---:|---:|---:|---:|---:|
| 80 | 512 / 1024 | 0.016375 | 0.482779321343 | **0.027777663568 — 기존 Fail** |
| 160 | 1024 / 2048 | 0.0081875 | 0.499931044386 | 0.010625940524 |
| 320 | 2048 / 4096 | 0.00409375 | 0.508583210717 | 0.001973774194 |
| 640 | 4096 / 8192 | 0.002046875 | 0.512928354406 | 0.002371369495 |
| 1280 | 8192 / 16384 | 0.0010234375 | 0.510760603260 | **0.000203618350** |

모든 L에서 dx=156.25/78.125 nm이다. 마지막 두 Window의 상호 tail 차이는
0.002167751145로 <0.02이며, 두 결과 모두 독립 적분과 기존 기준을 만족한다.
320→640 µm에서는 경계의 bin 내 위치가 바뀌어 오차가 증가한다. 단조 수렴,
모든 L에 대한 오차 상한 또는 이 Window가 모든 입력에 충분하다는 주장은 하지 않는다.

| 항목 | 결과 | 판단 |
|---|---:|---|
| Exact-coordinate complex E/Z0H error / incident peak, final L | 2.605e-8 | <1e-4 Pass |
| 위 Field 오차, 전체 Window 최대 | 2.026e-6 | <1e-4 Pass |
| Continuous T / RMS sinθ | 0.958670105054 / 0.151702389564 | 명시한 Synthetic Control에만 해당 |
| T/RMS relative error, 전체 최대 | 8.049e-12 이하 | <1e-4 Pass |
| Independent R relative error, 전체 최대 | 8.721e-12 이하 | <1e-4 Pass |
| Spatial/spectral flux mismatch, 전체 최대 | 4.441e-16 이하 | <1e-10 Pass |
| Discrete abs(1−R−T), 전체 최대 | 3.331e-16 이하 | <1e-10 Pass |
| Continuous abs(1−R−T) | 1.111e-16 | <1e-10 Pass |
| E/H, flux, RMS, tail의 동일 L Sampling 비교 | 모든 L 통과 | Self-consistency이며 독립 검증을 대체하지 않음 |

Complex Ey, Hx, Hz를 z=0/5 µm, x=0/1/2/4 µm에서 비교하며 phase alignment/fit은 없다.
E와 Z0H를 같은 단위로 비교하고, full sampled arrays도 보존한다. Ex=Ez=Hy=0은
2D TE symmetry이며 실제 3D Vector Field 검증을 뜻하지 않는다. Integrated Flux는
공간 Poynting 적분과 spectral sum을 비교한다. Angular Content는 RMS sinθ, tail,
raw spectrum으로 기록하며 evanescent 성분은 field에 유지하고 normal-flux tail에서 제외한다.
독립 적분은 기존 analytic Gaussian + direct Maxwell admittance를 재사용하고,
R도 별도 direct-admittance quadrature로 적분한다. tmm/FFT coefficient를 참조하지 않는다.
두 방식은 **같은 planar model의 독립 수치 구현**이며 실제 장치에 대한 실험 검증은 아니다.

첫 Window 실행은 약 1.12 s, peak RSS 약 76.3 MB로 120 s/<1 GB 예산 안에서 끝났다.
최종 정확한 HEAD별 시간/환경/Raw Hash는 각 CI Artifact의 provenance를 따른다.
추가 수치 탐색이나 threshold 변경은 하지 않았다.

## 실행 신뢰성과 재현

`run_m4c_stop.py`는 새 exclusive directory를 만든 다음 child를 실행한다. 기존 directory는
재사용하지 않는다. Child exit 1만으로 Stop을 승인하지 않고, run UUID, exact HEAD,
completion marker, source/result/raw-array SHA256와 모든 역사적 Gate를 확인한다.
ImportError나 조기 종료는 completion evidence를 만들지 못하므로 실패한다.
직접 `check_m4c_stop.py 1`을 사용하면 historical integrity만 검사하고 fresh execution은
Unverified로 표시한다. Fresh certificate에는 아래 launcher를 사용한다.

새 Window script도 exclusive directory와 completion/hash manifest를 사용하며,
계산/검증 오류 시 nonzero exit로 CI가 실패한다. 예전 결과 파일로 대체하지 않는다.
7개의 새 execution tests는 stale UUID, wrong HEAD, missing completion, missing/corrupt
raw arrays, changed source/result, unexpected exit, ImportError와 기존 directory 재사용을 거절한다.
전체 **68 tests** 및 Benchmark/Adapter Gate가 로컬에서 Pass했다.

```bash
python -m pip install -r requirements-m4c.txt
PYTHONPATH=src python scripts/validate.py
# 68 tests + Benchmark/Adapter; optional reference dependencies는 별도 requirements로 설치
python scripts/run_m4c_stop.py
# fresh UUID directory 출력; legacy acceptance=Fail, evidence check=Pass
python scripts/m4c1_window_control.py
# 별도의 fresh UUID directory 출력; new bounded verification=Pass
```

CI는 고정 경로 `results/runtime/m4c-legacy` 및 `results/runtime/m4c1-window`를
새 checkout에서 독점 생성한다. 재실행 시 새 checkout이어야 하며, 수동 로컬 실행은
기본 UUID 경로를 사용한다. 원래 `python scripts/m4c_planar_control.py`도 동일한
historical numerical result와 exit 1을 재현한다. 새 실행은 역사적 JSON을 덮어쓰지 않는다.

## 실제 입력 Audit와 적용 판단

이번 요청에는 비기밀 실제 Field 파일/Interface model이 첨부되지 않았다.
`references/m4c_external_field_request.json`에는 32개의 null leaf가 남아 있다.
이는 누락된 data/metadata 목록이며 모두 독립적으로 mandatory라는 schema 검증은 아니다.
Field-export 경로와 reproducible-model 경로는 대안이다. 자동 적합성 승인은 구현하지 않았다.
M4A-001은 실제 입력 미제공, M4B-LIT-001은 문헌 Proxy, M4C/M4C1은 Synthetic Control로 구분한다.

| 구분 | 이번 결과의 사용 범위 |
|---|---|
| 검증된 수치 범위 | 고정된 2D TE homogeneous planar interface의 명시 grid/window/planes에서 E/H, flux, angular metrics 및 power balance |
| 현재 Tool에서 가능한 판단 | Angular metrics 예산은 dx와 L을 분리하고 독립 적분으로 검사해야 한다. 기존 Gaussian valid-domain 판단만 유지하며 Proxy의 Domain Fail을 뒤집지 않음 |
| 추가 입력이 필요한 주장 | 실제 external NA/phase/Vector Field/Interface Transmission, Gaussian fit 적합성, normalized Overlap, Total Coupling 및 Package feasibility |

실제 실행 재개 조건:

- 한 Port의 homogeneous external reference plane에서 complex Ex/Ey/Ez/Hx/Hy/Hz,
  origin/normal/transverse basis, grid/units/staggering, λ0/medium, phase convention,
  outgoing/incident/total decomposition, guided power와 outgoing/reflected/absorbed/other
  flux accounting, solver/version과 convergence 증거를 제공한다.
- 또는 실제 n(x,y,z,λ), material/taper/termination geometry, eigenmode/source
  normalization, boundaries/mesh 설정을 포함한 재현 가능한 국소 facet 모델을 제공한다.
- Coupling에는 reciprocal accepted Target field를 별도로 제공해야 한다.

Guided MFD/n_eff로 실제 Phase/Vector Field/Transmission을 대체하지 않는다.
임의 Index Profile을 만들지 않는다. Actual Field·Overlap·Total Coupling·Full Package는
계속 **Uncomputed**다. Production src, 기존 Fixtures/Examples, Fixed Ports, Frozen Guards,
Physics와 Adapter Contract는 변경하지 않았다. Main 병합과 후속 자동 진행은 하지 않는다.

후속 제안: [NEXT_TASK.md](NEXT_TASK.md). 이 단계는 actual-data intake를 준비하며,
새 Solver/FE Space/UI/Optimizer/Topology/Reflector Reference/full Fold 계산을 시작하지 않는다.
