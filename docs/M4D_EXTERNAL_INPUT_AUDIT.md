# M4-D — External Field Intake & Applicability Gate

2026-11-14 (America/Los_Angeles). **Intake: Unprovided / 실제 성능 평가 중단.**
이번 요청에 실제 비기밀 complex E/H export 또는 재현 가능한 국소 Facet Model이
제공되지 않았다. 기존 Reference의 수치 검증 통과를 실제 입력 확보로 간주하지 않는다.
새 Physics 계산·Fit·Adapter·Solver 구현은 하지 않았다.

## Recovery와 실행 범위

Main은 `f42a6b1701eeb8c0500092a95e0b4202be86aa8b`, Draft PR #10은 미병합이며
HEAD는 `e164f7aa3c255a03f9c54f11af699b49c86c78e6`이다. 따라서 이번 별도 Draft PR은
`assessment/m4c1-angular-verification`을 Base로 한다. Main 병합은 하지 않는다.

- Main CI 42910559738 및 PR #10 CI 42920925168: success.
- PR #10 Artifact 5개: 유효함을 재확인. 이전에 다운로드한 동일 ZIP의 API SHA256,
  Physics/Control provenance HEAD·Source Hash와 Control output manifest를 다시 대조했다.
- Base HEAD의 별도 detached worktree에서 기존 68 tests, Benchmark/Adapter Gate 및
  legacy Stop/M4-C.1 Window 검증을 재현했다. Control은 각각 새 exclusive directory를 사용한다.
- 초기 legacy 실행은 환경의 `tmm` 누락으로 `ModuleNotFoundError`가 발생했다.
  Fresh report가 없어서 checker가 실행 실패로 거절했다. 이를 정상 Control Stop으로
  보고하지 않았다. 실패 log를 보존하고 기존 requirements-m4c.txt의 버전을 복원한 후
  새 directory에서 재실행했다. Physics source나 허용 기준은 수정하지 않았다.

실행 결과·run identity·복구 Artifact 식별자는
[기계 판독 가능한 Audit](../results/m4d_input_audit.json)와
[복구 실행 Log](../results/m4d_recovery_log.txt)에 기록했다.
이 문서의 M4-D 결과는 **입력이 없다는 Intake 판정**이며 새로운 수치 성능 결과가 아니다.
정확한 제출 HEAD의 CI와 Artifact 식별자는 이 Draft PR 본문에서 확인한다.

## 확인한 입력과 누락

확인 범위는 이번 요청의 첨부 목록, Repository의 tracked files,
`references/m4c_external_field_request.json` 및 아래 기존 Examples/결과다.
이번 요청의 첨부 목록은 비어 있다. 다른 서비스나 회사 내부에 데이터가 존재하지
않는다는 주장은 하지 않는다. 이전 Synthetic runtime arrays는 실제 입력으로 재사용하지 않는다.

| 자료 | 분류 | 실제 외부 입력으로 사용 가능 여부 |
|---|---|---|
| M4A-001 / external_ports_unprovided.json | 실제 입력 수집 양식; 물리값 미제공 | 불가 |
| M4B-LIT-001 / m4b_literature_proxy.json | 문헌 Guided MFD와 명시 가정의 Proxy | 실제 Phase/Vector Field/Interface Transmission 근거로 사용 불가 |
| M1/M3-A Examples | Synthetic external Gaussian | 기존 모델의 회귀검증용 |
| M4C-TE-PLANAR-001 / M4C1-TE-WINDOW-001 | Synthetic 2D TE planar reference | 수치 검증용; 실제 WAFT/PIC 아님 |
| m4c_external_field_request.json | Unprovided export request | 실행 가능한 Field 또는 Adapter 입력 아님 |

요청서에 **32개 null leaf**가 남아 있다. 아래 표는 같은 누락을 의미별로 묶은 것이다.
32개 전부를 동시에 채워야 한다는 새 Schema는 만들지 않는다. Field export와
reproducible model은 대안이며, width/fit 항목은 Gaussian 적합성 주장에 필요한 증거다.

| 누락 그룹 | 필요한 정보 | 없을 때 보류하는 판단 |
|---|---|---|
| 출처·추적성 | source, provenance, uncertainty, solver name/version 및 공유 가능한 데이터 | 실제 입력의 출처와 신뢰 범위 |
| Reference plane | origin, normal, transverse basis, external-side material, facet 상대 위치 | Fixed Port 기준면 및 좌표 변환 |
| 파장·매질 | vacuum wavelength, 외부 매질의 permittivity/index 및 정의 | 전파 상수·외부 공간 모델 |
| Sampling | x/y grid, array axis order, staggering | E/H 배열 해석·적분·Sampling/Window 검증 |
| Complex Field | 동일 plane의 Ex/Ey/Ez/Hx/Hy/Hz, 단위·복소수 encoding | 실제 Phase, Vector Field, Angular Content |
| Convention·분해 | 시간/공간 phase convention, polarization/mode ID, incident/outgoing/total 구분 | Forward/reciprocal 해석 및 실제 outgoing flux |
| Power accounting | incident guided power, outgoing plane flux, reflected/absorbed/other-boundary flux | Interface Transmission 및 손실의 물리적 의미 |
| 재현·수렴·Fit | material/geometry 또는 export, mesh/boundary/source, sampling/window/plane convergence, width definition/fit method | 수치 신뢰도·Gaussian complex fit 적합성 |

없다는 이유로 0, flat phase, air index 또는 guessed profile을 채우지 않는다.
물리적 대칭으로 어떤 성분이 0이라면, 누락과 구별되는 명시적 배열 또는 대칭 근거가 필요하다.

## 재개 조건 — 두 경로 중 하나

**A. Field-export 경로:** 한 Source Port의 homogeneous external reference plane에서
complex E/H와 위 좌표·단위·매질·convention·normalization·출처·수렴 metadata를 제공한다.
동일 plane에서 E/H를 해석할 수 있어야 하며, outgoing field인지 total field인지 구분한다.
Amplitude와 intensity 이미지, MFD 또는 n_eff만으로는 이 조건을 충족하지 않는다.

**B. Reproducible-model 경로:** 실제 material/index distribution, taper/termination/facet
geometry, wavelength/polarization, eigenmode/source normalization, solver/version,
boundary/PML/mesh 및 convergence 설정이 있는 비기밀 국소 모델을 제공한다.
모델 제공은 결과 검증 완료를 뜻하지 않는다. 실행 환경·license·예산을 먼저 확인하고,
현재 도구가 처리하지 못하면 필요한 최소 외부 실행 경로만 제안한다.

Coupling을 평가하려면 **reciprocal accepted Target field를 별도로** 확보해야 한다.
Source 하나의 Intake 검토에는 Target를 임의 생성하지 않으며, Target 미제공 상태에서
Overlap/Total Coupling을 계산하지 않는다. Package 판정에는 별도 실제 기하·제약이 필요하다.

입력이 제공되면 다음 순서로 재개한다.

1. 원본 파일 hash, non-confidential 사용 범위, source/units 및 metadata를 확인한다.
2. 새 계산 전에 해당 입력에 맞는 scope·계산 예산·오차 지표·성공/중단 기준을 기록한다.
   Synthetic Control의 특정 Window 크기를 실제 입력의 수렴 보증으로 전용하지 않는다.
3. 기존 코드가 해석할 수 있는 범위를 확인한다. 새 fitting/Vector adapter/solver가
   필요하면 구현을 시작하지 않고 최소 후속 범위를 제안한다.
4. Gaussian fit의 complex amplitude/phase residual과 수렴 증거, Frozen Domain 검사,
   Interface 손실, Overlap 및 Package 판정을 분리한다. Fit이 좋더라도 Guard를 우회하지 않는다.

## 이번에 유지하는 판단과 상태

| 구분 | 결과 |
|---|---|
| 검증된 수치 범위 | 기존 Synthetic Reference 및 회귀검증 범위 그대로 |
| 현재 Tool에 적용할 판단 | 실제 입력이 없으므로 Actual Applicability를 승인할 수 없음. 기존 valid-domain Synthetic 계산만 기존 의미로 사용 |
| Actual external Field / Gaussian complex fit / actual applicability | Uncomputed |
| Actual normalized Overlap / Total Coupling / Package | Uncomputed |
| 새 성능 계산 | 실행하지 않음 — 입력 미제공 |

Fixed Ports·Frozen Guards·기존 Fixtures·Physics·Adapter Contract·M4-C 실패 기록과
M4-C.1 통과 기록을 보존한다. 입력 누락은 실제 Architecture의 물리적 Fail이 아니다.

## 재현과 다음 작업

```bash
python -m pip install -r requirements-m4c.txt
PYTHONPATH=src python scripts/validate.py
python scripts/run_m4c_stop.py
python scripts/m4c1_window_control.py
```

`validate.py`는 현재 checkout의 results를 갱신하므로 실행별 detached worktree에서
사용하면 기존 작업과 분리할 수 있다. 두 Reference launcher는 기본값으로 서로 다른
UUID directory를 사용한다. Legacy Control acceptance=Fail과 evidence check=Pass를 구분한다.
M4-C.1 success를 실제 장치 성능 Pass로 해석하지 않는다.

다음 단계는 새 개발 Milestone이 아니라 **실제 입력이 제공된 뒤 M4-D 재개**다.
[복사 가능한 재개 지시문](NEXT_TASK.md)을 기록했다. 입력이 없으면 자료 대기 상태를 유지하며
반복적인 Synthetic 확장이나 새 기능 개발은 진행하지 않는다.
