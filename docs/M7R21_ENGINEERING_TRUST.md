# M7-R21 · 설계 결과의 신뢰 범위와 Interactive Tutorial

## 기준과 설계 판단

Main의 R18 통합점은 f7970886f42e0915ac8c96a6564bc4ac79b5597a였다. 열린 R20 Draft [#51](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/51)은 #50의 9a81ebf503ce12746e963e46b1b4c97c36329c30을 Base로 한다. R20에서 변경된 9개 파일에는 사전 예산, Yee 추출·여기 대조 스크립트, 원본 Profile 및 수치 Summary가 포함된다. R21은 #51의 ddf8ce0bca3a887f24fae45671a93e11ce7760ec에서 분기했다. 이 SHA의 [Physics CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44893958127) 및 [Windows Package와 Evidence](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44893958128)는 통과했다. Main SHA에 대해서는 PR용 조회에서 직접 대응하는 CI를 확인할 수 없었다.

## 사용자 검토

1. Two-Port Workspace에서 **Tutorial / How It Works** 탭을 연다. 계산 흐름의 8개 단계를 열어 Runtime·오프라인 Reference·장기 계획을 확인한다. **Show Equations**에서 Convention, 정규화 및 제약을 검토한다.
2. Example A의 저장된 1310 nm R6 처방에서 XZ Fold, M1 입사 Beam의 축별 반경, Target의 t축 Intensity·상대 Phase를 본다. R20 직선 SMF Profile의 두 성분은 별도 입력면 대조다. R6 G036-NM의 η와 R9의 다른 Envelope 처방은 각각의 조건에만 귀속된다.
3. Example B의 M4B Proxy에서 Geometry Pass, Gaussian Domain Fail과 그 결과로 보류한 Overlap을 확인한다. 실제 SSC의 Field·Power·조립 조건은 근거가 부족하다.
4. Workspace로 돌아와 Synthetic Example의 **Design**을 누른다. 결과에서 **Engineering Confidence**를 열고 추천과 대안을 바꾸면 선택한 처방의 아홉 판정과 Input SHA를 볼 수 있다. HTML Export는 선택 후보와 같은 Panel을 보존하고 JSON은 원래 Engine Evidence를 보존한다. 입력을 편집하면 결과와 Export가 숨겨지고 다시 Design을 실행해야 한다.

## Evidence 적용 규칙

| 범위 | 어떤 결론을 내릴 수 있는가 |
|---|---|
| Candidate evaluation, ranking, 독립 Quadrature가 있는 경우 해당 기록 | 고정 입력과 처방의 Geometry Closure, Gaussian Guard, Model 내 Normalized Mode Overlap을 해석한다. Overlap 공개는 기존 visible_overlap 조건을 따른다. |
| R6 / M4B 읽기 전용 Reference | 저장 처방으로 기존 Geometry Plot을 그린다. R6의 저장된 q와 기존 Gaussian/Profile 함수를 이용해 설명용 단면을 샘플링한다. M4B Domain Fail에는 Field 값을 표시하지 않는다. |
| R20의 직선 Guide와 평면파 | E/H는 실제 Yee 위치와 Solver 시간 규약으로 비교한다. 평면파 Power 일치와 직선 HE11 Profile의 5×10⁻⁵ 기준 초과를 각각 표시한다. 평면파 환산을 Facet에 적용할 근거는 없다. |
| 후보의 Vector·Power·제조 | 명목 유한 Relay의 Guided Fraction, U, M2 회전 광학 응답과 실제 Total Coupling·Assembly Tolerance는 미계산이다. 선언 Envelope 검사와 전체 Package Feasibility는 별개다. |

튜토리얼은 고정된 정적 Reference를 별도 주소에서 요청할 때만 읽는다. 현재 후보의 ID가 Reference 사례와 같아도 Reference 성능을 주입하지 않는다. 기본 결과와 Background Worker 결과는 같은 Report Renderer를 사용하며 기존 Job ID·Revision·SHA 검사를 유지한다. Windows 패키지는 예제와 읽기 전용 원본 수치만 추가로 동봉한다.

## 회귀와 재현

기준 R20의 149개 검사와 R21의 151개 검사를 각각 실행해 Benchmark와 M3-A Adapter Gate 통과를 확인했다. 별도 M5-A 검사에서 Synthetic 추천, Missing Phase 및 Domain Fail을 재현했다. 아래 경로는 Checkout에서 새 출력 디렉터리를 사용한다.

```bash
python -m pip install -e '.[test]'
PYTHONPATH=src python scripts/validate.py
python scripts/validate_m5a.py --output-dir results/runtime-m5a-r21
node scripts/check_workspace.cjs results/runtime-m5e-r21 results/runtime-m5a-r21
```

Browser 검사는 기존 CI 환경의 Playwright·Chromium·PDF 도구·한국어 글꼴을 사용한다. Desktop과 393 px의 Tutorial, 수식 열기, 예제 전환, 키보드 복귀, 후보별 Confidence와 기존 HTML/JSON/A4 흐름을 검사한다. Windows CI는 추출한 패키지의 실제 Launcher HTTP 경로에서 Tutorial을 읽고 기존 Background Near-Match와 Manifest 무결성을 검증한다. 이 Milestone의 수치 예산은 기존 Reference 표시 정밀도 및 Frozen Guard를 계승한다.

## 다음 설계 판단

Reference 설명에서 1310 nm의 실제 편집·재계산까지 연결하는 것이 다음 병목이다. R22는 R6 Two-Port 입력의 출처·정밀도를 보존해 기존 Worker로 재실행하고, 입력이 바뀐 경우 새 SHA와 새 근거로만 후보를 제시한다. HE11 FEM 대조는 Facet 판단이 필요할 때 재개한다. [실행 지시문](NEXT_TASK.md)
