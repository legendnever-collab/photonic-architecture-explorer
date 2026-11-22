# M7-R28 · 단일 Reflector 오차를 포함한 World X 경계

R8-expansion의 명목 및 R27의 단일 오차 12개에 공통으로 적용할 World X 폭은 **5.033724800 mm**다. R26의 명목 폭 대비 **10 µm** 증가하며 최소 기구 AABB Gap은 13개 조건에서 **50.000001 µm**다. Y/Z, Keepout, Aperture와 Backing 정의에는 R9의 Synthetic 입력을 사용했다.

| 면 | 명목 World X [mm] | 공통 World X [mm] | 명목 대비 [µm] | 제한 Pose 및 Body |
|---|---:|---:|---:|---|
| X− | −1.582177423194 | −1.587177423194 | −5 | M2 World X −5 µm · M2 Backing AABB |
| X+ | +3.441547376467 | +3.446547376467 | +5 | M1 World X +5 µm · M1 Backing AABB |

명목 경계는 로컬 R26의 0 µm 추가 여유 결과와 일치했다. R9 Envelope에서 M2 sagittal +1 mrad의 X− Gap은 **49.289712562 µm**로 R10의 49.289713 µm를 0.001 µm 이내에서 재현했다. 이 Pose의 공통 경계 Gap은 **54.289712562 µm**다. [R10 기구 결과](M7R10_FINITE_BEAM_SCOPE.md) · [R26 명목 경계](M7R26_ENVELOPE_SIZING.md) · [R27 Pose 기록](M7R27_REFLECTOR_POSE.md)

## 산출과 검증

1. R27에 따라 한 번에 Reflector 하나를 이동 또는 회전한다. Pose마다 유한 Quadratic Patch에 실제 반사하는 두 교차점과 고정 Target Plane의 교차점을 기존 Chief Ray 엔진에서 구한다. 기존 Backing 깊이와 World Padding으로 각 Pose의 Body AABB를 다시 계산한다.
2. 왼쪽 한계는 모든 Body의 X min에서 50 µm를 뺀 값과 Chief Ray 꼭짓점 X 좌표의 최솟값이다. 오른쪽 한계는 Body의 X max에 50 µm를 더한 값과 Chief Ray 꼭짓점 X 좌표의 최댓값이다. 볼록한 AABB에서 꼭짓점 포함은 전체 선분 포함을 보장한다. R26과 같이 두 바깥 방향에 각각 1 pm을 더한다.
3. 명목과 12개 Pose를 모두 기존 Package Adapter 검사로 평가한다. Chief Ray 검사에는 각 Pose에서 실제 추적한 교차점을 전달한다. 기구 Gap이 50 µm 미만이거나 Y/Z·Reflector 간 거리·Keepout·Chief Ray 검사에 실패하면 제안을 보류한다. 명목 경계 검증 허용차는 2 pm이다.

## Workspace 및 재현

Example A에서 Package Envelope를 선택하고 **Design**을 실행한다. **Reflector 오차를 포함한 World X 경계**에 공통 경계, 명목 대비 이동량과 폭 증가량, 제한 Pose와 Input SHA256이 표시된다. Compact·Expansion·사용자 지정 X와 별도로 고정 R8-expansion의 공통 경계를 제공한다. HTML/JSON에 같은 입력 SHA와 13개 Pose의 원본 및 제안 기구 판정, 실제 Chief Ray 경로와 Backing AABB를 기록한다. 후보 탐색에는 기존 74개 처방을 사용한다.

교란 후 η, 복합 오차의 실제 Assembly Tolerance, Finite-beam Clearance, Total Coupling은 Uncomputed다. 공통 경계는 지정한 13개 이산 Pose에 적용된다.

```bash
PYTHONPATH=src python scripts/validate.py
node scripts/check_m7d.cjs results/runtime-m7r28-browser
```
