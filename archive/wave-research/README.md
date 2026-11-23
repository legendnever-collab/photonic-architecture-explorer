# 보관: Wave·Vector·FDTD 연구 산출물 (M4-C, M7-R11~R20)

2026-11-24 재설계(P0)에서 기본 실행 경로와 CI에서 분리한 연구 산출물이다. 삭제하지 않고
원래 디렉터리 구조(`scripts/`, `references/`, `tests/`) 그대로 보관한다.

| 묶음 | 내용 | 원래 문서 |
|---|---|---|
| M4-C | Planar Control과 외부 Field 요청 | `docs/history/M4C_*.md` |
| M7-R11~R12 | 곡면 반사면 Scalar 회절 적분(Filon/Quadrature) | `docs/history/M7R11_*.md`, `M7R12_*.md` |
| M7-R14~R16 | Guided Power, Port Power, Vector Relay | `docs/history/M7R14_*.md` ~ `M7R16_*.md` |
| M7-R17~R18 | 독립 Source와 PEC Edge 회절 | `docs/history/M7R17_*.md`, `M7R18_*.md` |
| M7-R19~R20 | Open-boundary Facet, Yee Field 추출 | `docs/history/M7R19_*.md`, `M7R20_*.md` |

예외: `references/m7r12`(M7-R13·R27이 사용)와 `references/m7r20`(Tutorial이 사용)은
런타임 의존성 때문에 원래 위치에 남겼다. P1에서 기존 Workspace를 걷어낼 때 함께 정리한다.

## 재개 조건

비근축(발산각 0.1 rad 이상) 또는 Vector 효과가 후보의 순위나 채택 여부를 바꾸는지 판단해야
할 때 재개한다(로드맵 P3). 재개하려면 해당 파일을 원래 위치로 `git mv` 하고,
스크립트의 `ROOT` 기준 경로와 `requirements-m4c.txt`를 확인한다.
