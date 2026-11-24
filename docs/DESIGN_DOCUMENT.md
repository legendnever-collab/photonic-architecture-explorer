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

### Glass 매질 `medium_block` (선택, P3)

```json
"medium_block": {
  "label": "Fused silica", "index": 1.444,
  "surface_point_mm": [0, 0, 0], "surface_normal": [0, 0, 1], "thickness_mm": 2.0,
  "index_source": {"provenance": "measured", "source": "Malitson 1965, 1550 nm"}
},
"ports": {"source": {"...": "...", "medium": "ambient"}, "target": {"...": "...", "medium": "block"}}
```

| 필드 | 의미 |
|---|---|
| `index` | Glass 굴절률. `ambient_index`보다 커야 한다 |
| `surface_point_mm`, `surface_normal` | 평면 상면 위의 한 점과 단위 법선(Glass 밖, 외부 매질 쪽을 향함) |
| `thickness_mm` | 상면과 평행한 하면까지 두께. `null`이면 하면 없음 |
| `index_source` | 굴절률의 출처(provenance, source). 없으면 문서 공통 가정으로 기록 |
| `ports.*.medium` | `ambient` 또는 `block`. Port 위치가 선언한 쪽에 있어야 하며, 상면 위에 정확히 놓인 Port만 어느 쪽이든 선언할 수 있다. Block이 없으면 `ambient`만 허용 |

`to_engine_problem`은 외부 Port를 상면에서 굴절시킨 **등가 Port**(상면 바로 안쪽, 굴절된 방향, Coddington q 배율)로 바꾸고,
엔진은 Glass 굴절률을 균질 매질로 하여 변경 없이 Relay를 푼다. 등가 Port의 출처 문자열에는 원래 출처와 변환 내용이 함께 남는다.
반사면은 한쪽 Port라도 Glass 안이면 Glass 안(상면 아래, 하면 위)에만, 두 Port가 모두 외부면 Glass 밖에만 둔다.

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
| `candidates[].scene` | 반사면(Vertex, Normal, 축, 곡률, Aperture, Beam Footprint, 13×13 표면 Grid), 경로 점, 구간별 Beam 반경 샘플. Glass를 통과하면 외부 구간이 경로 앞(Source 쪽) 또는 뒤(Target 쪽)에 붙고, 구간·샘플마다 `medium`이 있다 |
| `search` | 정책 `P3-CONTINUOUS-2`(P2-CONTINUOUS-1 + Glass 영역·Beam 여유·자세 여유), 격자 수, Exact/Near-match 가능 배치 수, 판정별 개수, 가장 가까운 Exact 해, 계산 시간 |
| `candidates[].model` | `separable`(동일평면, 기존 엔진 Adapter 검산) 또는 `qtensor`(비동일평면·축 회전, Ray-transfer 검산) |
| `candidates[].ray_transfer_check` | q-tensor 후보: 실제 곡면 광선의 4×4 행렬로 재현한 Q의 상대차, Symplectic 오차 |
| `candidates[].nonparaxial_check`, `metrics.nonparaxial_overlap` | 비근축 Scalar 검산: η, 격자 수렴(129²→257² 변화), Aperture 밖 Power 비율, 방법과 제외 항목 |
| `candidates[].roles`의 `best_nonparaxial` | 후보 중 비근축 η가 가장 높은 후보(탐색 단계에서 최대 400개 배치를 65² 격자로 순위화) |
| `nonparaxial_study` | Port 발산각이 Guard를 넘을 때만: Guard를 끈 근축 Exact 설계의 비근축 η(후보 아님) |
| `candidates[].scene.beam.samples[].ellipse` | q-tensor 후보: 1/e² 강도 타원의 장·단반경과 구간 t축 기준 장축 각도 |
| `relay_medium` | `ambient` 또는 `block`(Relay를 푼 매질) |
| `crossing` | 외부 Port가 있을 때: 통과 쪽(`source`/`target`), 상면 통과점, 외부 구간 길이, 입사·굴절각, Coddington q 배율 t/s, 무코팅 평면파 Fresnel 투과(참고값, η에 포함 안 함) |
| `candidates[].metrics.ambient_path_mm` | 총 광경로 중 외부 매질 구간 |
| `candidates[].scene.mirrors[].tir_possible` | Glass 안 반사면에서 뒤쪽이 외부 매질이라면 TIR이 가능한 입사각인지. 아니면 반사 Coating이 필요 |
| `uncomputed` | 계산하지 않은 항목(Total Coupling, Vector 검증, 조립 공차, Package, 특허성) |
| `engine_report` | 엔진 원본 결과(재현·감사용) |

길이는 mm, Beam 반경은 µm다. η는 Scalar Paraxial Normalized Mode Overlap이며 Total Coupling이 아니다.
