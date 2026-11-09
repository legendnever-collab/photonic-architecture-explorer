# Selective reuse review — 2026-11-09

Read-only inspection of `legendnever-collab/photonic-connector-studio`, main SHA
`5045c8f367267f8fbcc1a59b0662193a036b25a5`.
Reviewed `AGENTS.md`, `src/physics.ts`, `src/project/physicalGaussian.ts`,
`src/project/tensorOverlap.ts`, `tests/physicalGaussian.test.ts`,
`tests/tensorOverlap.test.ts`. No writes to that repository.

| 기존 구현의 검토 항목 | M1 선택 |
|---|---|
| Rayleigh range, ABCD q, beam parameters | 검증된 수식·convention을 재사용, Python complex 기반의 작은 구현 |
| Normalized field, curvature-aware overlap, log-domain underflow | 의미와 검증 전략을 재사용, two-curved-field integral을 독립 구현 |
| Unit-normalized quadrature, homogeneous medium, rigid transform tests | 동일 검증 원칙을 M1의 새 독립 Reference로 적용 |
| Full tensor overlap | M1은 coplanar aligned ellipse로 한정하여 의존성·일반 tensor engine 제외 |
| 기존 refracting surface/GUI/project graph | 이식하지 않음 |
| Unresolved wave / finite-aperture / spherical-lens reference | 이식하거나 검증 완료로 간주하지 않음 |

기존 tests의 존재와 내용을 검토했으며 이번 세션에서 기존 TypeScript test suite를
실행한 것은 아닙니다. 기존 저장소의 green CI를 이번 구현의 검증 근거로 사용하지 않습니다.
M1의 공개 저장소에는 private repository source/fixtures를 복사하지 않았습니다.
공개 optical equations, modeling conventions, validation strategy만 선택적으로
재사용했습니다. 검증 결과는 이 Python 구현의 실제 실행에 근거합니다.

기존 straight refracting solver의 reduced Q=q/n convention을 그대로 섞지 않고,
homogeneous reflective M1에는 ordinary q를 사용합니다. 이 차이를 명시하고
air/non-air propagation reference tests로 n/λ convention을 검증했습니다.
