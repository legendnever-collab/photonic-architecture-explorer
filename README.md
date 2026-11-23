# Photonic Architecture Explorer

고정 Optical Port 두 개를 놓으면, 만들 수 있는 광학 연결 구조 후보를 물리 근거와 함께 보여 주는 R&D 도구.
초기 설계 판단과 특허용 개념 도출에 쓴다. 현재 검증 범위는 **두 개의 곡면 반사면, 동일평면, Scalar Paraxial Gaussian**이다.

> 2026-11-24 재설계 진행 중 — 현재 **P0(정리와 기반)**. 다음은 3D/2D 시각 Workspace(P1). [Roadmap](docs/ROADMAP.md)

## 빠른 시작

```bash
python -m pip install -e '.[test]'
pae-app --open                       # 새 Workspace(P0: API Console)
PYTHONPATH=src python -m unittest discover -s tests
```

Windows 오프라인 패키지: [Windows Review CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/workflows/windows-review.yml)의
`m7f-windows-review-package` Artifact를 받아 ZIP을 풀고 `Start-Photonic-Architecture-Explorer.cmd`를 실행한다.

## 시나리오(User Decision Benchmark)

| ID | Port A → Port B | 현재 | 목표 |
|---|---|---|---|
| S1 | SMF → SMF, 90° Fold | 후보 생성 | P0 |
| **S2a** | SMF-28 → LDW Glass WG(1310·1550 nm) | 고정 Family에 후보 없음 | P2(공기), P3(Glass 내부) |
| **S2b** | SMF-28 → IOX Glass WG(1550 nm) | 고정 Family에 후보 없음 | P2(공기), P3(Glass 내부) |
| S3 | SiPh SSC 3 µm → SMF | 발산각 Guard 초과 | P3·P4 |
| S4 | PIC Edge → 측면 수직 Fiber | 비동일평면 | P3 |
| S5 | Laser → SSC | 발산각 Guard 초과 | P4 |
| S6 | Channel 배열 → FAU | 범위 밖 | P6 |

Mode 값은 공개 문헌(Mode Library) 또는 Synthetic 대표값이며, 배치는 Synthetic이다. 회사 데이터는 넣지 않는다.

## 문서

| 문서 | 내용 |
|---|---|
| [User Guide](docs/USER_GUIDE.md) | 실행, 결과 읽는 법, Preset |
| [Design Document](docs/DESIGN_DOCUMENT.md) | 입력 `pae.design/1`과 결과 `pae.result/1` 형식 |
| [Physics](docs/PHYSICS.md) | 좌표·Gaussian·반사·Overlap 규약과 유효 범위 |
| [Validation](docs/VALIDATION.md) | 독립 Reference 검증과 근거의 한계 |
| [Roadmap](docs/ROADMAP.md) · [Decision Log](docs/DECISIONS.md) | 단계·Gate, 결정 이력 |
| [Product Charter](docs/PRODUCT_CHARTER.md) · [AGENTS.md](AGENTS.md) | 제품 약속과 개발 규칙 |
| [External Port Contract](docs/EXTERNAL_PORT_CONTRACT.md) | 엔진 입력 계약(M3A-1) |
| [history/](docs/history/) · [archive/](archive/wave-research/README.md) | 2026-11-24 이전 Milestone 기록과 보관 연구물 |

## 구조

```
src/photonic_architecture_explorer/
  gaussian.py geometry.py solver.py     검증된 물리 커널
  external.py design.py                 입력 계약, 두 반사면 Exact-q 후보 생성
  design_document.py scene.py api.py    P0: 입력 문서, 도면용 Geometry, API 함수
  app.py web/                           P0: 로컬 서버와 화면
  presets.py scenarios/                 P0: 공개 문헌 Preset, 시나리오 Fixture
  workspace.py inspector.py ...         기존 Workspace(P1에서 교체)
```

η(Normalized Mode Overlap)는 Total Coupling이 아니다. Total Coupling, 조립 공차, Package, 특허성은 Uncomputed다.
