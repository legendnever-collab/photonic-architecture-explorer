# Photonic Architecture Explorer

고정 Optical Port 두 개를 놓으면, 만들 수 있는 광학 연결 구조 후보를 물리 근거와 함께 보여 주는 R&D 도구.
초기 설계 판단과 특허용 개념 도출에 쓴다. 현재 검증 범위는 **두 개의 곡면 반사면, 동일평면, Scalar Paraxial Gaussian**이다.

> 2026-11-24 재설계 진행 중 — **P0·P1·P2** 완료(P2: 연속 탐색·제약·Near-match), 다음은 P3(Glass 매질·굴절 계면). [Roadmap](docs/ROADMAP.md)

## 빠른 시작

```bash
python -m pip install -e '.[test]'
pae-app --open                       # 3D/2D Workspace, http://127.0.0.1:8770/
PYTHONPATH=src python -m unittest discover -s tests
```

Windows 오프라인 패키지: [Windows offline package CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/workflows/windows-review.yml)의
`windows-offline-package` Artifact를 받아 ZIP을 풀고 `Start-Photonic-Architecture-Explorer.cmd`를 실행한다(Chrome/Edge).

Workspace에서는 Port를 표로 입력하거나 3D에서 끌어 배치하고, 후보를 3D 장면과 2D 도면(XY·XZ·YZ·Fold 전개 Beam Envelope)에서 비교한다.
도면은 엔진이 계산한 Geometry를 그대로 그린다.

## 시나리오(User Decision Benchmark)

| ID | Port A → Port B | 현재 | 목표 |
|---|---|---|---|
| S1 | SMF → SMF, 90° Fold | Exact 3개 | — |
| **S2a** | SMF-28 → LDW Glass WG(1310·1550 nm) | 1550: Exact 3개 · 1310: Near-match 3개(η ≥ 0.989) | P3(Glass 내부) |
| **S2b** | SMF-28 → IOX Glass WG(1550 nm) | Near-match 3개(η 0.981~0.990) | P3(Glass 내부) |
| S3 | SiPh SSC 3 µm → SMF | 발산각 Guard 초과 | P3·P4 |
| S4 | PIC Edge → 측면 수직 Fiber | 비동일평면 | P3 |
| S5 | Laser → SSC | 발산각 Guard 초과 | P4 |
| S6 | Channel 배열 → FAU | 범위 밖 | P6 |

Mode 값은 공개 문헌(Mode Library) 또는 Synthetic 대표값이며, 배치는 Synthetic이다. 회사 데이터는 넣지 않는다.

## 문서

| 문서 | 내용 |
|---|---|
| [User Guide](docs/USER_GUIDE.md) | 실행, 화면 구성, 결과 읽는 법, Preset |
| [Design Document](docs/DESIGN_DOCUMENT.md) | 입력 `pae.design/1`과 결과 `pae.result/1` 형식 |
| [Physics](docs/PHYSICS.md) | 좌표·Gaussian·반사·Overlap 규약과 유효 범위 |
| [Validation](docs/VALIDATION.md) | 독립 Reference 검증과 근거의 한계 |
| [Roadmap](docs/ROADMAP.md) · [Decision Log](docs/DECISIONS.md) | 단계·Gate, 결정 이력 |
| [Product Charter](docs/PRODUCT_CHARTER.md) · [AGENTS.md](AGENTS.md) | 제품 약속과 개발 규칙 |
| [External Port Contract](docs/EXTERNAL_PORT_CONTRACT.md) | 엔진 입력 계약(M3A-1) |
| [history/](docs/history/) · [archive/wave-research](archive/wave-research/README.md) · [archive/legacy-workspace](archive/legacy-workspace/README.md) | 2026-11-24 이전 Milestone 기록, 보관 연구물과 기존 Workspace |

## 구조

```
src/photonic_architecture_explorer/
  gaussian.py geometry.py solver.py     검증된 물리 커널
  external.py design.py search.py       입력 계약, M5-A 고정 Family(회귀 기준), P2 연속 탐색 생성기
  design_document.py scene.py api.py    입력 문서, 도면용 Geometry, API 함수
  app.py web/                           로컬 서버와 빌드된 Workspace(frontend/에서 생성)
  presets.py scenarios/                 공개 문헌 Preset, 시나리오 Fixture
frontend/                               TypeScript + three.js Workspace 소스(npm run build)
distribution/                           Windows 오프라인 패키지 실행기
archive/                                보관한 연구물과 기존 Workspace
```

η(Normalized Mode Overlap)는 Total Coupling이 아니다. Total Coupling, 조립 공차, Package, 특허성은 Uncomputed다.
