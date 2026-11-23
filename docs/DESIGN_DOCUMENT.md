# Design Document `pae.design/1` 와 Result `pae.result/1`

Workspace, API, 시나리오 Fixture가 주고받는 단일 입력 기록이다. 엔지니어링 단위를 쓰고, Port의 모든 값에 출처를 붙인다.
변환기(`design_document.to_engine_input`)는 기본값이나 정규화 없이 기존 [External Port Contract](EXTERNAL_PORT_CONTRACT.md)(M3A-1)로 바꾼다.

## 입력

```json
{
  "schema": "pae.design/1",
  "title": "S2b · SMF-28 → IOX (Brusberg 2012), 1550 nm",
  "scenario": "S2b-1550",
  "description": "자유 서술",
  "wavelength_nm": 1550.0,
  "ambient_index": 1.0,
  "ports": {
    "source": {
      "label": "Corning SMF-28 Ultra · 1550 nm",
      "preset": "smf28-ultra-1550",
      "position_mm": [0, 0, 0],
      "direction": [1.0, 0.0, 0.0],
      "sagittal_axis": [0.0, 1.0, 0.0],
      "mfd_um": [10.4, 10.4],
      "wavefront_curvature_per_m": [0.0, 0.0],
      "evidence": {
        "placement": {"provenance": "synthetic", "source": "Synthetic scenario placement"},
        "mode": {"provenance": "measured", "source": "Corning PI1424 · Optical Specifications, p. 1"},
        "phase": {"provenance": "assumed", "source": "Flat phase at the external reference plane"}
      }
    },
    "target": { "...": "같은 형식" }
  }
}
```

| 필드 | 단위·규칙 |
|---|---|
| `position_mm` | 외부 기준면 원점, mm, World 좌표(오른손 XYZ) |
| `direction` | 단위 벡터(오차 1e-10). Source는 출사 방향, Target은 **도착하는 빛의 진행 방향**. 자동 정규화하지 않는다 |
| `sagittal_axis` | 단위 벡터, `direction`에 수직. t축은 s × d |
| `mfd_um` | [t, s] 1/e² Intensity 지름, µm |
| `wavefront_curvature_per_m` | [t, s] 1/R, m⁻¹. Flat은 0 |
| `evidence.*.provenance` | `measured`, `supplied`, `independently_validated`, `simulated`, `assumed`, `synthetic` |

### 제약 `constraints` (선택)

```json
"constraints": {
  "port_body_halfspace": true,
  "envelope_mm": {"min": [-0.5, -1, -2], "max": [3.5, 1, 3]},
  "keepouts_mm": [{"label": "connector", "min": [0.6, -0.2, 0.3], "max": [1.2, 0.2, 0.7]}],
  "clearance_um": 10,
  "max_incidence_deg": 70,
  "min_radius_of_curvature_mm": null
}
```

| 필드 | 의미 |
|---|---|
| `port_body_halfspace` | 기본 `true`. Port 본체(Fiber·Chip)가 각 기준면 뒤쪽 반공간을 차지한다고 가정하고, 반사면과 광로가 들어가지 못하게 한다 |
| `envelope_mm` | 반사면 Patch 전체와 주광선이 이 World AABB 안에 있어야 한다 |
| `keepouts_mm` | 반사면 Patch가 `clearance_um`보다 가까이 가면 안 되고, 주광선이 지나가면 안 되는 AABB 목록 |
| `max_incidence_deg` | 0 초과 70 이하. Frozen Guard(70°)를 더 좁힐 수만 있다 |
| `min_radius_of_curvature_mm` | 곡면 축의 \|R\| 하한(제작성). `null`이면 제한 없음 |

Envelope·Keep-out은 엔진 입력의 `package`(available_volume, keepout_bodies, required_clearance_m)로도 전달되어
기존 Adapter가 후보마다 독립적으로 다시 검사한다.

`evidence`의 항목이 없으면 `assumed`(사용자 입력)로 기록한다. 검증 오류는 첫 오류에서 멈추지 않고 전부 `{path, message}`로 돌려준다.

## 결과 `pae.result/1`

| 필드 | 내용 |
|---|---|
| `status` | `Computed`, `Fail`, `Uncomputed`, `Invalid`(입력 오류), `Preview` |
| `document_sha256` | 입력 문서의 정규화 JSON SHA-256 |
| `ports.ports[]` | 기준면, t/s 축, 축별 Mode(반경, Waist, Rayleigh range, 발산각), 발산각 Guard와 통과에 필요한 최소 Waist MFD |
| `family` | `exact`(두 축 q 일치, η = 1) 또는 `near_match`(Guard 안 Overlap 최대, η < 1) |
| `candidates[]` | `id`, `rank`, `roles`·`role_labels`(최단 광경로, Guard 여유, 작은 Beam, 완만한 곡률, 정렬 공차, 최대 Overlap, Pareto 대안), `family`, `parameters_mm`(a, b, c), `metrics`(광경로, η, 3w·\|κ\|, 최대 \|κ\|, 정렬 민감도 dB, 입사각, 곡률반경), `status`(엔진 판정), `scene` |
| `guidance[]` | `kind`, `phase`, `message`, `values`: 발산각 초과 시 필요한 굴절률, Guard 밖 Exact 해까지의 거리, 제약으로 제외된 배치 수, 비동일평면 등 |
| `search.map` | 탐색한 (a, c) 격자(64 × 64)의 판정과 3w·\|κ\|, Near-match 가능 배치 |
| `constraints` | 적용된 제약(SI 단위) |
| `candidates[].scene` | 반사면(Vertex, Normal, 축, 곡률, Aperture, Beam Footprint, 13×13 표면 Grid), 경로 점, 구간별 Beam 반경 샘플 |
| `search` | 정책 `P2-CONTINUOUS-1`, 격자 수, Exact/Near-match 가능 배치 수, 판정별 개수, 가장 가까운 Exact 해, 계산 시간 |
| `uncomputed` | 계산하지 않은 항목(Total Coupling, Vector 검증, 조립 공차, Package, 특허성) |
| `engine_report` | 엔진 원본 결과(재현·감사용) |

길이는 mm, Beam 반경은 µm다. η는 Scalar Paraxial Normalized Mode Overlap이며 Total Coupling이 아니다.
