# M7-R1 — SMF–Glass Waveguide Mode Reference Library

SMF, femtosecond LDW와 IOX의 공개 Mode Width, Mode Image, Loss를 설계 검토에
사용할 수 있도록 기록했다. JSON의 각 record는 파장, 재료, 형상, polarization,
측정 기준면, 값의 출처, 원문 위치를 보존한다. 읽기 전용 HTML은 같은 JSON에서
생성하며, 출처별 Mode Image와 측정 조건을 바로 확인할 수 있다.
[Reference JSON](../../src/photonic_architecture_explorer/data/m7r1_mode_references.json) ·
[Mode Comparison HTML](../../results/m7r1-mode-library.html)

| Source | Vacuum wavelength | Mode evidence 및 실무 적용 |
|---|---:|---|
| Corning SMF-28 Ultra | 1310 / 1550 nm | 공급사 MFD 각각 9.2 ± 0.4 / 10.4 ± 0.5 µm. WP7071과 ITU-T G.650.1은 Petermann II far-field 정의를 제공한다. PI1424는 제품별 MFD 산출 방법을 명시하지 않는다. ±는 Specification Tolerance다. [PI1424](https://www.corning.com/media/worldwide/coc/documents/Fiber/product-information-sheets/PI-1424-AEN.pdf) |
| Sun, Fused Silica FLDW | 1310 nm | Fig. 3.5(c–d)의 55 mW 사례에서 Intensity Cut 기반 MFD 표기는 x 11 µm, y 18 µm다. Width Threshold, 불확도 및 외부 기준면의 Phase는 미확인이다. [M7-R3 판정](M7R3_1310_PORT_READINESS.md) |
| Desmet et al., Fused silica FLDW | 1550 nm | 12.8 ± 0.4 µm lateral, 12.1 ± 1.3 µm vertical, 1/e² Intensity Diameter. Fig. 5(b)는 실측 Intensity Image다. [Fig. 5(b)](https://www.photonics.intec.ugent.be/download/pub_4648.pdf#page=8) |
| Lee et al., Fused silica FLDW | 1550 nm | Fig. 5(a–c)의 x × y MFD는 Uncracked y-pol 10.2 × 10.0 µm, Microcrack x-pol 9.3 × 9.6 µm, Microcrack y-pol 9.4 × 10.0 µm. 세 패널 모두 Peak-normalized Intensity이며 폭은 1/e² 기준이다. Cracked Guide의 비대칭은 원문 그림으로 확인한다. 원저자는 요청 시 데이터를 제공한다고 명시한다. [Fig. 5](https://eprints.soton.ac.uk/452944/1/s41598_021_03116_y.pdf#page=5) |
| Wang et al., EAGLE XG OCMS | 실험별 상이 | Fig. 2(c)와 Supplement Fig. S9의 Fundamental Guide Family는 MFD 8–18 µm, Circularity >97%·최고 99.5%다. Supplement S7의 정의는 minor/major axis다. Fig. 3은 LP₁₁(1500–1610 nm)와 LP₂₁(980–1160 nm)의 Mode-selective Directional Coupler다. [원문과 Supplement](https://link.springer.com/article/10.1038/s41377-024-01473-7) |
| Brusberg et al., D263Teco IOX | 1550 nm | Fig. 5의 실측 광학 Mode Intensity와 18.8 × 12 µm의 수평·수직 주석을 기록했다. Width Threshold는 미확인이다. Fig. 4는 678 nm에서 측정한 별도 Refractive-index Map이다. 1310 nm Bend Loss가 있지만 1310 nm Mode Width는 제공된 그림에서 확인되지 않았다. [Figs. 4–5](https://www.izm.fraunhofer.de/content/dam/izm/de/documents/Abteilungen/System_Integration_Interconnection_Technologies/Photonik_Packaging/EOCB/IEEE%20ECTC2012%20Brusberg%20et%20al.pdf#page=3) |

## Coupling Loss의 측정 조건

| Source | 값 | 근거와 적용 범위 |
|---|---|---|
| Desmet FLDW | 0.88 dB/cm | OFDR one-way Propagation Loss |
| Desmet FLDW | 0.43 dB/facet | 1.5 cm의 실측 Insertion Loss 2.17 ± 0.01 dB에서 Propagation Loss를 빼고 두 Facet에 균등 배분 |
| Desmet FLDW | 1.24 ± 0.32 dB | 최적 높이 Offset에서 Passive V-groove Fiber-to-Guide Coupling, 7.5 mm Guide, 3회 측정 평균 |
| Desmet FLDW | 0.22 dB | 완전 정렬 상태의 Simulated Mode Mismatch |
| Wang OCMS | 0.29 dB 및 0.045 dB/facet | Fig. 2(b)에서 single-mode GRIN fiber로 보고한 10 mm Guide의 Insertion Loss 및 Propagation 차감 추정값. 일반 Methods에는 index-matching oil과 Corning SMF-28 양단 접속을 명시한다. GRIN 수치는 해당 Fig. 2 조건에 귀속한다. |
| Fraunhofer IOX | 약 0.05 dB/cm 및 0.3 dB | 6-axis 정렬 Input SMF, Output MMF로 검출한 1550 nm straight cut-back 조건. 원문 signed dB 표기를 양의 Loss Magnitude로 표시했다. Input SMF 모델과 독립적인 양단 Facet Loss는 미확인이다. |

LP₁₁·LP₂₁의 Transfer Ratio와 Mode Extinction Ratio는 Guide 간 Power Transfer와
Mode Purity를 설명한다. Facet Coupling Loss는 표의 해당 Interface 측정에 귀속한다.

## Visualization 및 Data Contract

- `mode_evidence.kind`는 공급사 MFD, 논문 실측 Intensity Image, Loss Reference를
  식별한다. `source_id`와 `locator`로 출처 및 정확한 Figure/표를 찾는다.
  JSON의 파장과 Mode Diameter 단위는 m다. Loss는 원문과 대조할 수 있도록 행마다 단위를 명시한다.
- HTML에서 그리는 곡선은 명시적으로 표시한 Gaussian Intensity Preview다. 중앙을 0으로
  두고 각 축에 $I/I_{\mathrm{peak}}=\exp[-2(2x/D)^2]$를 사용한다. $D$는 Preview의
  1/e² Intensity Diameter다. Corning은 nominal scalar MFD를 원형 (D)로 사용하는
  이론 가정을, Desmet과 Lee Uncracked는 두 실측 Width를 쓰는 separable Gaussian
  가정을 적용한다. Phase, Wavefront Curvature와 World Frame은 미제공이다.
- Microcrack, IOX 및 OCMS 원문 이미지는 링크로 연결한다. Microcrack은 비대칭,
  IOX는 Width Threshold 미확인, OCMS는 서로 다른 Family 및 Higher-order Mode를
  포함하므로 이 자료의 단일 Gaussian 재구성은 생략했다. 공개 Figure를 Pixel Grid로
  Digitize하지 않았다. Wang Supplement DOCX의 Fig. S9에는 Origin Graph가
  포함돼 있으며, 검토한 자료에서 calibrated raw Mode Grid나 Phase는 확인되지 않았다.
- Actual External Port, Complex Overlap 및 새 설계의 Total Coupling은 **Uncomputed**다.
  실제 설계를 재개하려면 사용할 Facet의 비기밀 Intensity/Phase 또는 검증된 Gaussian
  Fit, 파장, External Plane과 매질, 두 Transverse Axis와 Polarization을 확보한다.
  1310 nm Sun 사례의 Intensity와 Width는 문헌 근거로 표시한다.
  [External Port Contract](../EXTERNAL_PORT_CONTRACT.md)
- M7-A/B 재현은 기존 Eaton AF45 Proxy 및 입력 SHA를 기준으로 한다. 이 Catalog는
  Workspace의 Fixed Port, Ranking, Frozen Guards와 Near-Match Worker에 연결되지 않는다.
  [M7-A Proxy](M7A_SMF_GLASS_WAVEGUIDE_REFERENCE.md) ·
  [M7-B Evidence](M7B_GUARDED_NEAR_MATCH.md)

```bash
python scripts/m7r1_mode_report.py
PYTHONPATH=src python -m unittest discover -s tests -p 'test_m7r1_mode_reference.py'
```

HTML의 Catalog SHA-256으로 표시된 데이터와 원본 JSON을 대조할 수 있다. HTML은
로컬에서 열 수 있으며, 원문 링크를 열 때 인터넷 연결이 필요하다.
