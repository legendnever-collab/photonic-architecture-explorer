# M6-F — Two-Port Design Workflow

M6-F는 Main `c3c66585d089c1c3c8a8a385dee192e18f89aec8`에서 시작한다.
[M6-E Draft #22](https://github.com/legendnever-collab/photonic-architecture-explorer/pull/22)의
Reference Not Ready 결정이 실측 Field에 대한 판단 기준이다. 세 기존 Synthetic
입력의 비교 기준은 [Main CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44018242353)와
[M6-E CI](https://github.com/legendnever-collab/photonic-architecture-explorer/actions/runs/44018850475)다.

## 입력과 조작 수

빈 입력에서 하나의 숫자 칸을 채우는 것을 입력 1개로 센다. 아래는 Fold Plane이
유일하고 두 Port가 rotation-symmetric Gaussian인 경우다.

| 항목 | 기존 | M6-F |
|---|---:|---:|
| 두 Port의 Position + Direction | 12 | 12 |
| 두 Port의 MFD + Wavefront Phase | 8 | 4 |
| 두 Port의 명시 Sagittal 성분 | 6 | 0 |
| Vacuum Wavelength + External Index | 2 | 2 |
| 숫자 입력 합계 | 28 | 18 |
| 기본 화면의 Mode 표현 선택기 / 열린 축 상세 | 2 / 2 | 0 / 0 |
| 예제에서 새 입력 선택 및 Design 제출 | 2 | 2 |
| 기본 Synthetic Example의 Design 제출 | 1 | 1 |

기본 새 입력의 Rotation-symmetric Mode는 사용자가 입력한 단일 MFD와 Wavefront
Curvature를 두 축에 똑같이 적용한다. 양쪽 Phase 값은 처음에 비어 있다. Flat
Phase는 0을 명시한다. 비대칭 크기 또는 Phase가 있으면 상세 입력에서 t/s 표현을
선택하고 해당 Port의 실제 Sagittal Axis를 제공한다. 일반 Complex q도 상세 입력에서
지정한다. 기존의 명시 t/s 값, q, Reference Plane ID/Frame, 기준축과 출처는 편집하지
않은 경우 그대로 사용한다. 다른 Mode 표현으로 전환하면 새 표현을 입력한다.

## 좌표와 결과

- Workspace의 Position/Direction은 각각 **External Reference Plane** 위의 점과
  전파 단위벡터다. 이 계약으로 Plane origin/normal을 기록한다. 이미 공급된
  별도 기준면은 기존 Adapter에서 검증한다. Target Direction은 도착 방향이다.
- Fold Plane은 두 Direction과 정규화된 Source→Target 변위가 만드는 span이다.
  세 쌍의 cross product 중 가장 큰 것을 검사하고 기존 Coplanarity 검사와 같은
  `1e-10` 수준을 사용한다. 공선이면 유일한 Plane이 없다. 세 벡터가 한 평면에
  있지 않으면 Skew다. 입력된 Sagittal Axis가 법선과 다르면 Rolled다.
- 축이 비어 있는 Port에서 두 복소 Mode 축이 정확히 같은 경우에만 Fold Plane
  법선을 사용한다. MFD와 Wavefront Curvature가 모두 같거나 두 복소 q가
  같아야 한다. 법선 부호는 기존 명시 축을 따르거나 절댓값이 가장 큰 성분을
  양수로 정한다. Engineering JSON의 Port 레코드 `source`에 산출 근거를
  포함한다. 기존 Adapter enum에서 출처가 명시된 값은 `supplied`로 전달한다.
- Design 후 추천 후보의 실제 Fold Plane 2D 그림, Nominal Mode Match 및 추천
  이유를 상단에 표시한다. 대안은 최대 두 개다. 광경로 길이 차이와 선택 이유를
  보여준다. 수치 비교, Sensitivity, Reflector Prescription 및 모델 범위는
  필요할 때 펼친다. 실세계 AABB 도면은 기존 XYZ 투영에서 검토한다.
- 입력을 편집하면 결과와 Export를 숨긴다. 제출한 입력 Snapshot의 SHA 및 보고
  중인 후보 ID를 HTML/Engineering JSON/A4에서 대조할 수 있다. Export는
  계산 결과를 재사용한다. `viewed_candidate_id`는 선택한 대안도 보존한다.
- Off-vertex Field, perturbed Mode Overlap, 실제 Assembly Tolerance, Package
  Yield, Total Coupling 및 Patentability는 Uncomputed다.

## 재현

```bash
python -m pip install -e '.[test]'
python scripts/validate.py
python scripts/validate_m5a.py --output-dir results/runtime-m6f-m5a
python scripts/validate_m5f.py --output-dir results/runtime-m6f-m5f
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install --with-deps chromium
# Install poppler-utils and fonts-noto-cjk for PDF checks.
node scripts/check_workspace.cjs results/runtime-m6f-workspace results/runtime-m6f-m5a
node scripts/check_m5f_print.cjs results/runtime-m6f-m5f
```

기존 equal-q와 different-q의 추천은 G009-B1, High Divergence는 Fail이다.
빈 Workspace에서 λ=1310 nm, n=1, +X 방향 두 Port, Target (2,2,0) mm,
공통 MFD 20 µm, Phase curvature +50/−50 m⁻¹인 새 Synthetic control에는 +Z
Sagittal Axis가 계산된다. Unit Test는 명시 +Z 입력과 후보 순서, Geometry,
Domain 및 Mode Match가 동일한지 검사한다. Browser 검사는 이 사례의 제출,
Fold 그림, 18개 노출 입력, 기준면·축 출처, HTML/JSON/A4 동일성과 모호한 입력의
안내를 기존 Desktop/Mobile 회귀와 함께 확인한다.
