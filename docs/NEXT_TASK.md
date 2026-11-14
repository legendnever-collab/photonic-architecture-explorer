# M4-D handoff — Awaiting non-confidential external input

상태: **Intake Unprovided / Actual Applicability Uncomputed**.
실제 complex E/H export 또는 재현 가능한 국소 Facet Model이 없어 성능 평가는 중단했다.
기존 Synthetic Reference와 Regression은 그대로 유지한다.
[누락 항목·대안 입력 경로·재개 조건](M4D_EXTERNAL_INPUT_AUDIT.md)을 먼저 확인한다.

다음은 **새 데이터가 제공됐을 때만** 실행하는 M4-D 재개 지시문이다.
추천: Astra Work — Reference plane, Vector Field, Power normalization과 적용성 판단이 필요하다.

```text
Photonic Architecture Explorer — M4-D Resume
Recommended Mode: Astra Work
Mission: Supplied External Field Intake & Applicability Gate
Repository: https://github.com/legendnever-collab/photonic-architecture-explorer
Base: M4-D Draft PR (병합됐다면 최신 Main)

1. 원격 HEAD/Base/CI/Artifacts를 복구하고 AGENTS.md,
   docs/M4D_EXTERNAL_INPUT_AUDIT.md, docs/EXTERNAL_PORT_CONTRACT.md,
   references/m4c_external_field_request.json을 읽어라.
2. 새로 제공된 비기밀 complex E/H export 또는 국소 Facet Model의 파일·출처·단위·
   기준면/basis·phase·field decomposition·normalization·power accounting·수렴 증거를 확인하라.
   새 입력이 없으면 미제공 상태와 재개 조건만 보고하고 중단하라.
3. 입력이 있으면 기존 Tests/legacy Stop/M4-C.1을 실행별 격리해 재현하고,
   실제 입력에 대한 계산 전에 범위·예산·오차 지표·성공/중단 기준을 기록하라.
4. 현재 구현으로 검증 가능한 범위만 평가하라. 새 fitting/Vector adapter/solver가
   필요하면 최소 후속 범위만 제안하고 구현하지 마라. Guided MFD/n_eff나 임의
   index/phase로 빈 입력을 채우지 마라. Reciprocal Target는 별도로 요구하라.
5. Gaussian complex fit 증거와 Frozen Domain 검사를 분리하고 Fixed Ports·Guards·
   기존 결과를 보존하라. 미검증 Overlap·Total Coupling·Package는 Uncomputed로 유지하라.
   새 입력에 따른 결과·한계·재현 명령·다음 지시문을 기록하고 별도 Draft PR을 생성하라.
6. 새 범용 Solver·FE Space·UI·Optimizer·Topology·Reflector Reference·전체 Fold Maxwell,
   Main 병합 및 후속 자동 실행은 하지 마라.
```
