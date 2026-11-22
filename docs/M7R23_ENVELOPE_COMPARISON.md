# M7-R23 · 1310 nm SMF–Glass의 Package Envelope 비교

Tutorial → Example A → **이 두 Port로 설계**에서 원본 두 Port를 열고, 공통 전파 조건 아래의 **Package Envelope**를 선택한 뒤 **Design**을 누른다. 두 조건을 같은 처방 집합으로 재평가한다. 표의 선택 표시와 아래의 Optical Path, Confidence, HTML·JSON Export가 같은 입력 SHA를 가리킨다. Envelope를 편집하면 이전 결과와 Export가 숨겨진다. 기본값 ‘적용 안 함’은 R22의 기존 Design 경로를 사용한다.

## 무엇을 비교했는가

[PR #53](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/53)이 병합된 main `e4c6b64173bb53fd2b10bf048274b641b4ffb402`에서 시작했다. [Main CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44961112542)에서 Physics, Browser, Workflow 및 Reference 검사가 통과했다.

두 조건은 R7의 Synthetic Backing, Keepout, Y/Z 범위와 50 µm AABB Clearance를 공유한다. 확장안은 R8의 **비대칭 X−/X+ 경계**와 수치 비교 여유를 SI 정밀도로 읽는다. 수동으로 표시 폭을 반올림해 경계를 재구성하지 않는다. 이 Keepout은 원본 Example A의 좌표에 귀속되므로 Port를 수정한 뒤 선택하면 적용 범위를 표시하고 추천을 보류한다.

각 Envelope에서 R8 기준 처방 2개를 원본 Aperture로 검사하고, 두 기준의 a/c를 중심으로 25 µm 간격 3×3 배치에서 R8의 Guard-limited Exact-q Seed를 재생성한다. 후자에는 기존 Equal-tail Aperture와 1.10 mm Half-aperture cap을 적용한다. 두 조건에 각각 74개 처방을 대조하며 별도 Optimizer 실행 없이 기존 Adapter, Geometry·Gaussian Guard, Backing·Keepout 검사, 0.135 Footprint–Curvature 및 0.095 rad Post-mirror Divergence 기준을 그대로 사용한다. 통과 수는 평가한 처방 건수다. 0.99 목표는 통과 후 별도 판정한다.

| 재계산 결과 | 4.30 mm | 5.023725 mm |
|---|---:|---:|
| 통과 처방 / 평가 | 19 / 74 | 48 / 74 |
| 최고 관측 후보 | R8-nominal | R8-expansion |
| Normalized Gaussian Overlap η | 0.9850444681668674 | 0.9900109725310262 |
| 저장 R9 기준과 η 절대차 | 0 | 0 |
| 독립 Quadrature와 최대 η 절대차 (로컬) | 6.67e−16 이하 | 3.34e−16 이하 |
| 최대 투영 Beam 반경 (1/e² intensity) | 248.37 µm | 290.17 µm |
| 최소 AABB Gap / 제한 위치 | 50.000 µm · M2 X− | 50.000 µm · M2 X− |
| η ≥ 0.99 | 미달 | 충족 |

Nominal SHA는 `34c3f41194cbf5738347c721db737ecdbd220de0f6ab5a9b101c1d715751b55b`, 확장 SHA는 `8ad9bb3c193736bb0b6ac133a206effd735663576234c3a86b45574b06e30a6b`다. 둘 다 R6 원본 Optical Port를 포함하고 Package가 다르다. 각 조건의 통과 처방별 η·Beam Footprint·최인접 Envelope 면과 탈락 사유·R9 재현 오차·독립 Quadrature는 Export의 `envelope_comparison.cases`에 있다. 기준 처방 재현 또는 독립 검산 실패 시 추천을 보류한다.

확장안의 η 여유는 약 1.10×10⁻⁵다. 기구 AABB의 명목 판정만으로는 전체 Finite-beam Clearance, 실물 Assembly Tolerance와 Total Coupling을 결정할 수 없어 모두 Uncomputed로 표시한다. 탐색 범위 밖에서 0.99를 만족할 최소 폭도 Uncomputed다.

## 재현 방법

```bash
python -m pip install -e '.[test]'
PYTHONPATH=src python -m scripts.m7r9_envelope_review --output-dir results/runtime-r9-replay
PYTHONPATH=src python scripts/validate.py
node scripts/check_m7d.cjs results/runtime-r23-browser
```

마지막 명령은 Playwright Chromium이 설치된 환경에서 실행한다. 기존 Windows CI는 압축을 푼 Review Package의 Python으로 같은 Browser 검사를 실행한다. 입력 편집 시 Export가 숨겨지는지, 새 SHA·Confidence·JSON과 오프라인 HTML이 일치하는지 확인하며 결과는 acceptance.json에 남긴다.
