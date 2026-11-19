# M7-R4 — 1310 nm External Field Evidence and Gaussian Fit

**판정: Uncomputed.** 1310 nm 외부 기준면에 등록된 Complex Field가 확보되지 않았다.
Gaussian Fit, Actual Applicability 및 Two-Port Mode Overlap을 판정할 증거가 부족하다.
Total Coupling도 Uncomputed다. 공개 Intensity와 Width는 아래 각 사례의 문헌 근거다.

## 원본 자료 확인

| 자료 | 확인한 범위 | Port 입력 판정 |
|---|---|---|
| Sun, Southampton, 55 mW Fused-Silica FLDW | 논문 Fig. 3.5(c–d)는 1310 nm Intensity와 x/y Width 11/18 µm를 제시한다. ePrints 레코드와 OAI-PMH METS에서 Chapter 3 자료와 ReadMe·Code의 배포 주소를 확인했다. | 공식 Chapter 3 다운로드가 접근을 거부해 ZIP 내부나 Figure 대응 파일을 확인할 수 없었다. Width 정의·등록된 외부 기준면·Phase의 수록 여부는 미확인이다. |
| Fernandez et al., KCAS/NCAS, 독립 검토 사례 | Fig. 10과 본문은 1310/1550 nm InGaAs Near-Field Intensity를 보고한다. Figure Width는 D4σ와 Gaussian 1/e²를 구분한다. 본문의 RNF Index Map은 635 nm 측정이고, Bend Simulation에는 보정 계수를 썼다. | 공개 본문에서 1310 nm 외부 Complex Field, Phase 및 해당 기준면의 등록 정보를 확보할 수 없었다. Data Availability Statement는 교신저자 요청 경로를 제시한다. |

[Sun 논문 · Fig. 3.5(c–d)](https://eprints.soton.ac.uk/467364/1/Qi_Sun_Thesis_for_Award.pdf) ·
[Southampton 자료 목록](https://eprints.soton.ac.uk/id/eprint/453747/) ·
[Fernandez et al. · Fig. 10 및 Data Availability](https://doi.org/10.1002/adom.202403427)

Southampton의 OAI-PMH METS 응답에는 `Chapter3.zip` (517,159,203 bytes),
`ReadMe.txt` (2,795 bytes), `CODE.zip` (65,196,470 bytes) 등이 등록돼 있다.
직접 요청은 HTTP 401 보안 확인 페이지를 반환했고, 배포 목록에서 Chapter 3를 연
브라우저 요청은 HTTP 403 Access Denied를 반환했다. 파일 형식·크기는 METS 메타데이터의 값이다.
[DataCite 등록](https://api.datacite.org/dois/10.5258/soton/d2043) ·
[Southampton METS](https://eprints.soton.ac.uk/cgi/oai2?verb=GetRecord&metadataPrefix=mets&identifier=oai:eprints.soton.ac.uk:453747)

## 외부 기준면 자료를 확보하는 최소 경로

1. **한 Port를 먼저 고정한다.** 1310 nm에서 사용할 편광과 Mode ID를 정하고, Facet 대비 Plane 위치, 좌표 원점, 전파 방향 및 두 Transverse Axis, 외부 매질 굴절률을 기록한다. Target을 역방향 여기해 측정하면 측정 기준과 Adapter의 도착 방향 및 Phase Convention 사이의 변환을 함께 기록한다.
2. **같은 Plane에서 복소장을 취득한다.** 측정은 배율·배경·광학계 전달 위상을 교정한 1310 nm Near-Field Intensity와 간섭계 Relative Phase를 같은 좌표에 등록한다. 시뮬레이션은 사례별 1310 nm Index Profile·Facet 형상·외부 매질이 확보되면 기존 Eigenmode/Facet Solver의 외부 Plane 출력을 사용한다. 기록에는 좌표 벡터 및 배열 축 순서, Complex transverse E 또는 진폭·Phase, 마스크, 반복 측정 또는 모델 불확도, 출처가 포함된다. 전력·편광 보존까지 평가할 때는 기존 [External Field Export 요청 양식](../references/m4c_external_field_request.json)의 E/H·Flux 항목을 사용한다.
3. **입력·오차 예산을 고정한 뒤 Fit을 판단한다.** 같은 Plane과 고정된 축·원점에서 진폭과 상대 위상을 맞춘다. 위상 비교 시 전역 위상 상수만 제거한다. 정규화된 제곱 복소장 Overlap과 신호 유효 영역의 Phase Residual을 보고하고, 유효 영역·가중치·불확도와 설계의 Mode-Mismatch 오차 예산을 기록한다. Grid 간격과 Window 크기를 별도로 바꿔 수렴을 확인한다. 수렴한 Overlap의 Fit 손실은 `−10 log10(η_fit)`으로 표현한다. 이 값은 해당 Port의 Gaussian 근사 오차에 귀속된다.
4. **검증된 범위에서 기존 설계를 연결한다.** 한 Port만 준비되면 해당 Fit까지만 판정한다. 두 Port의 Field 또는 검증된 MFD+Curvature / Ordinary Complex q가 확보되면 공통 Frame·외부 매질·고정 배치를 기준으로 기존 Adapter와 Guard를 실행한다. 예산이 제공되지 않으면 Fit 진단의 수치와 허용 여부를 분리하고 실제 적용성은 Uncomputed로 둔다.

## 재현 및 회귀 기준

```bash
PYTHONPATH=src python -m photonic_architecture_explorer.external examples/m7r3_sun_1310_readiness.json
PYTHONPATH=src python -m unittest discover -s tests -q
python scripts/validate_m7c.py --output-dir results/runtime-m7c-r4-review
```

1310 nm 예제는 첫 필수 누락인 `ambient_index`에서 멈춘다. 출력의 Model Domain과 Actual
Applicability는 Uncomputed이며, Mode Overlap과 Total Coupling은 `null`이다. 이 순서는
Adapter의 첫 누락 검사 결과다. 실제 Fit에는 위 항목을 함께 확보해야 한다. 1550 nm M7-A
Proxy는 M7-C 회귀 기준이다. 로컬 재현에서 입력 SHA-256
`9d6d55bc8c4a06ca99c7ffcae205954a634678162986d2565c111b76df510988`, M7-B의 36개 배치 기록,
후보 `G036-NM` 및 normalized Mode Overlap `0.9999366495865395`가 일치했다.
