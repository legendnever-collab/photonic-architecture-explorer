# M3-B — Minimal 2D Inspector

2026-11-10 KST. Recovered unpushed `a890cfb` scope and `inspector.py` prototype
from the previous checkout. Base remains PR #4, `61bafc61d50b0c934e9fa17c4220bb44dbaf5b96`.
PR #1–#4 remain Draft and unmerged; Main is unchanged.

## 실행

```bash
python -m pip install -e '.[test]'
python -m photonic_architecture_explorer.inspector
# Portable, read-only review: results/m3b-inspector.html
python -m photonic_architecture_explorer.inspector --serve --port 8765
# Open http://127.0.0.1:8765
python -m photonic_architecture_explorer.inspector --input examples/external_ports_unprovided.json --output results/blank.html
python scripts/validate.py
```

설치 후 `pae-inspector`도 지원한다. Static HTML은 별도 서버 없이 Case/Projection을
전환한다. 입력 수정·재평가는 Python Local Inspector에서 수행한다. Local Inspector는
127.0.0.1에만 Bind하며 파일을 쓰지 않는다. 임의 Remote Host/Origin 요청을 거부한다.
Wheel 배포는 이번 범위가 아니며 위 실행은 Repository checkout을 전제로 한다.

## Engineering 경계

- `evaluate_external`이 계산을 담당하고 `adapt_external`의 immutable Geometry를
  그린다. JavaScript는 사전 계산한 Case/Projection을 선택하고 Dirty Result를 숨긴다.
- Fixed Port Boundary Conditions / Reflector Design Variables / Package JSON을
  나눈다. Port를 직접 수정하면 다음 평가의 새로운 고정 조건이며 자동 이동·Fit은 없다.
- XZ/XY/YZ, 생략 축과 mm 단위를 명시하고 두 축을 같은 Scale로 그린다.
  실제 quadratic-patch prescription의 wireframe이며 Spherical Mirror로 대체하지 않는다.
  Surface orientation이 기존 coplanar basis 밖이면 해당 Surface를 표시 보류한다.
- Chief path는 기존 Geometry 검사 Pass일 때만 그린다. 잘못된 Unit/Missing Input에서는
  Geometry를 보류한다. 명시 SI/공통 Frame의 지원되는 AABB만 투영한다.
- Input / Chief-Ray Geometry / Gaussian Domain / Design Bounds / Approximate Overlap /
  Envelope Geometry / Full Package / Physical Losses / Fabrication / Actual Applicability를
  분리한다. 2D 중첩은 3D 충돌의 증거가 아니다. Beam Envelope는 그리지 않는다.
- Input 변경 즉시 이전 Plot/Overlap/입력 요약/Hash를 숨긴다. Adapter 재평가 후에만
  새 결과를 표시한다. Invalid JSON도 이전 Overlap을 보존하지 않는다.
- Approximate Normalized Scalar Mode Overlap은 실제 Coupling Efficiency가 아니다.
  Actual Applicability / Total Coupling / Full Finite-Beam Clearance는 Uncomputed다.
  Input SHA256, Provenance를 포함한 JSON 및 원래 Adapter Result/Samples를 열어볼 수 있다.

## 검증과 User Review

기존 49개 Test를 재실행한 뒤 Inspector Test 10개를 추가했다. `tests/test_inspector.py`:
8개 Case 상태, 실제 Adapter 호출, Fixed Port 불변, 결과 비보존, Surface Sag/Projection,
지원 AABB만 표시, JSON Roundtrip/오류, HTML Escaping, HTTP Valid→Invalid→Valid,
Local Request 경계, CLI Static/Blank를 검증한다. 기존 Optical Source/Tests/Fixture/Guard와
M1/M2/M2.5/M3-A Benchmark JSON은 변경하지 않는다.

`results/m3b_001.json`은 8개 Case의 상태와 Published Overlap이다. 로컬 Browser launch는
실행 환경의 Socket 제한으로 실패했고 Cloud Browser도 로컬 서버에 접근하지 못했다.
따라서 로컬 화면 검증을 완료로 기록하지 않는다. CI의 별도 `inspector-browser` Job은
Chromium에서 1440×1050 / 393×852, 세 Projection, 모든 Case 전환, 명시 Curvature 변경,
Valid→Invalid JSON→Valid, Dirty Result 숨김, Fixed Port 보존, 가로 Overflow 및 독립 Static
HTML 전환을 실행한다. `results/m3b_browser.json`과 Desktop/Mobile PNG를 Artifact로
남긴다. 실제 결과는 해당 SHA의 CI/Artifact에서 확인한다.

Browser Test 재현(선택 개발 의존성, Physics runtime에는 불필요):

```bash
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install --with-deps chromium
python -m photonic_architecture_explorer.inspector
node scripts/check_inspector.cjs
```

사용자 Review 순서:

1. Synthetic Relay의 Source→M1→M2→Target 경로와 두 Surface를 확인한다.
2. XZ/XY/YZ를 전환하고 생략 축·고정 Port Direction을 확인한다.
3. Missing Phase, 잘못된 단위/Target Direction, High Divergence, Bounds/Package Fail을
   선택하여 Overlap이 `—`로 바뀌는지 확인한다.
4. Envelope Pass와 Full Package Uncomputed가 별개임을 확인한다.
5. Local Inspector에서 Reflector JSON을 수정하고 재평가한다. 입력 중에는 이전 결과가
   사라져야 한다. Static HTML의 JSON은 Read-only다.

사용자 Review는 아직 Pending이다. 다음 Checkpoint와 복사용 지시문은 NEXT_TASK.md.
