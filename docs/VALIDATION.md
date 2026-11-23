# Validation

무엇을 어떤 독립 Reference로 검증했고, 어디까지가 근거인지 정리한다. 세부 기록은 [history/](history/)에 있다.

## 실행

```bash
python -m pip install -e '.[test]'
PYTHONPATH=src python scripts/validate.py          # 물리 Benchmark + 전체 단위 테스트 + SHA 매니페스트
PYTHONPATH=src python -m unittest discover -s tests
python scripts/build_scenarios.py                  # 시나리오 Fixture 재생성과 기대 상태 확인
```

## 검증된 물리 커널

| 커널 | 독립 Reference | 기준 | 기록 |
|---|---|---|---|
| 자유공간 Gaussian(q 전파) | 닫힌 형식 w(z)/R(z), 샘플링 Fresnel 전파 | Field overlap 1e-11, Power 1e-12 | [M1](history/VALIDATION.md) |
| 평면·곡면 반사, q 변환 | 정확한 이차곡면 Ray/Normal 반사, 위상 Mask + Fresnel | Principal power 2e-5 m⁻¹, Profile overlap 1e-10 | [M1](history/VALIDATION.md) |
| Mode Overlap | 해석 사례, 2개 Grid의 복소장 적분 | 1e-12 | [M1](history/VALIDATION.md) |
| 유한 Fan·곡률·배치 진단 | Newton 표면 교차 | 문서 기준 | [M2](history/M2_RESULTS.md) |
| External Adapter(M3A-1) | 계약 테스트 | 거절·미계산 분류 | [M3-A](history/M3A_ADAPTER.md) |
| 두 반사면 Exact-q 설계 | 기존 Adapter로 재평가 | 후보마다 독립 재검사 | [M5-A](history/M5A_AUTONOMOUS_DESIGN.md) |

## P0에서 추가한 검사

| 대상 | 검사 |
|---|---|
| Design Document | 모든 오류를 경로와 함께 보고, 자동 정규화 없음, SI 변환과 출처 보존 |
| Scene | 경로 점 = 엔진 Vertex(1 pm), Beam 반경 = 엔진 평면값(1e-9 µm), 반사면 Footprint 일치, 표면 Grid가 이차곡면 위에 있음 |
| 시나리오 | S1~S6의 현재 상태와 사유를 고정. Fixture가 생성 스크립트와 같은지 확인 |
| API | 엔드포인트, Round trip, 경로 Traversal 거절 |

## P1에서 추가한 검사

| 대상 | 검사 |
|---|---|
| Workspace(브라우저) | `scripts/check_app.py`: 3D 렌더, S1 Design, 2D 도면의 반사면·Port 좌표와 Fold 반사면 거리 = 엔진 Scene(1 nm), 입력 변경 시 결과 무효화, S2b·S3 실패 사유와 다음 단계, 입력 JSON Export 왕복, WebGL 없는 환경의 2D 동작 |
| Frontend 빌드 | CI가 `npm ci && npm run build` 결과와 커밋된 `web/`가 같은지 확인 |
| Windows 패키지 | 파일 SHA 매니페스트, 오염된 환경 변수 무시, `.cmd` 실행, HTTP로 모든 시나리오 결과가 Checkout 엔진과 동일, Edge·Chrome 브라우저 검사 |

## 근거의 한계

- 모든 결과는 Scalar Paraxial, 동일평면, 축 정렬 분리형 Gaussian 범위다.
- Guard(발산각 0.1 rad, 3w·|κ| 0.15)는 보수적 Screening 규칙이며 오차의 엄밀한 상한이 아니다.
- Total Coupling, Vector Field, 조립 공차·수율, 전체 Package Clearance, 특허성은 Uncomputed다.
- 비근축·Vector 연구 산출물은 [archive/wave-research](../archive/wave-research/README.md)에 보관했고 P3에서 필요할 때 재개한다.
