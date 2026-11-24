import type { Store } from './state';
import type { AlignmentStats, Candidate, NonparaxialStudy, Result } from './types';

type LensReview = NonNullable<Result['lens_review']>;
import { STATUS_LABEL, el, fmt, nextStep, reasonLabel } from './util';

const TITLES: Record<string, string> = {
  '비근축 η': '이차곡면 처방을 근축 근사 없이(각스펙트럼 + 실제 곡면 광선) 계산한 Scalar Overlap',
  '보정 곡면 η': '3·4차 Sag(Coma 보정)를 더한 곡면의 비근축 Overlap. 근축 설계(꼭짓점·법선·곡률)는 그대로',
};

const STATUS_TEXT: Record<string, string> = {
  Computed: '후보 생성', Fail: '후보 없음', Uncomputed: '미계산', Invalid: '입력 오류', Preview: 'Preview',
};

/** Right panel: verdict, candidate comparison, selected-candidate detail and honest limits. */
export class ResultsPanel {
  constructor(private root: HTMLElement, private store: Store) {
    store.subscribe((_, changed) => {
      if (changed.has('result') || changed.has('selected') || changed.has('doc') || changed.has('busy') || changed.has('error')) this.render();
    });
  }

  render() {
    const { result, busy, error } = this.store.state;
    const current = this.store.currentResult;
    this.root.replaceChildren();
    if (busy) this.root.append(el('div', { class: 'card busy' }, '계산 중…'));
    if (error) this.root.append(el('div', { class: 'card issues' }, `오류: ${error}`));
    if (!result) {
      this.root.append(el('div', { class: 'card muted' }, 'Port를 배치하고 Design을 누르면 후보가 여기에 나타납니다. 3D 화면에서 Port를 더블클릭하면 끌어서 옮길 수 있습니다.'));
      return;
    }
    if (!current) {
      this.root.append(el('div', { class: 'card stale' }, '입력이 바뀌었습니다. 표시 중인 결과는 이전 입력의 것이라 도면에서 숨겼습니다. Design을 다시 실행하세요.'));
      return;
    }
    this.root.append(this.verdict(current));
    if (current.crossing) this.root.append(this.crossing(current));
    if (current.candidates.length) {
      this.root.append(this.table(current.candidates));
      const selected = this.store.selectedCandidate;
      if (selected && selected.family !== 'lens_two_reflector') this.root.append(this.detail(selected));
    }
    if ((current.families ?? []).length > 1) this.root.append(this.familyCard(current.families!));
    if (current.lens_review) this.root.append(this.lensReview(current.lens_review));
    const chosen = this.store.selectedCandidate;
    if (chosen?.family === 'lens_two_reflector') this.root.append(this.lensDetail(chosen));
    if (chosen?.alignment) this.root.append(this.alignmentCard(chosen));
    if (current.nonparaxial_study?.cases?.length) this.root.append(this.study(current.nonparaxial_study));
    if (current.search?.screening_counts) {
      this.root.append(this.rejections(current.search.screening_counts, current.search.grid_points, current.search.elapsed_seconds));
    }
    this.root.append(this.limits(current));
  }

  private verdict(result: Result) {
    const card = el('section', { class: 'card', 'data-result-status': result.status },
      el('div', { class: 'card-head' }, el('h3', {}, '결과'), el('span', { class: `status ${result.status}` }, `${result.status} · ${STATUS_TEXT[result.status] ?? ''}`)),
      el('div', {}, reasonLabel(result.reason)));
    const guidance = result.guidance ?? [];
    if (guidance.length) {
      card.append(el('div', { class: 'next' }, el('strong', {}, '해석과 다음 단계'),
        el('ul', { class: 'guidance' }, ...guidance.map((g) => el('li', { 'data-guidance': g.kind },
          ...(g.phase ? [el('span', { class: 'phase' }, `[${g.phase}] `)] : []), g.message)))));
    } else {
      const step = nextStep(result.reason);
      if (step) card.append(el('div', { class: 'next' }, el('strong', {}, '다음 단계 '), step));
    }
    for (const issue of result.issues ?? []) card.append(el('div', { class: 'issue' }, `${issue.path}: ${issue.message}`));
    card.append(el('div', { class: 'muted mono' }, `입력 SHA-256 ${result.document_sha256?.slice(0, 16) ?? '—'}…`));
    return card;
  }

  private crossing(result: Result) {
    const x = result.crossing!;
    const block = this.store.state.doc.medium_block;
    const t = x.fresnel_transmission_uncoated;
    return el('section', { class: 'card', 'data-crossing': x.side },
      el('h3', {}, `Glass 상면 통과 (${x.side === 'source' ? 'Source 쪽' : 'Target 쪽'})`),
      el('div', {}, `${block?.label || 'Glass'} n ${block?.index ?? '—'} · 외부 구간 ${fmt(x.ambient_length_mm, 4)} mm · 입사각 ${fmt(x.incidence_deg, 2)}° → 굴절각 ${fmt(x.refraction_deg, 2)}°`),
      el('div', {}, `q 배율 t/s ${x.q_scale_ts.map((v) => fmt(v, 4)).join(' / ')} (Coddington) · 무코팅 Fresnel 투과 s ${fmt(t.s, 4)} / p ${fmt(t.p, 4)}`),
      el('div', { class: 'muted' }, 'Relay는 상면 바로 안쪽의 등가 Port에서 Glass 굴절률로 풉니다. Fresnel 투과는 평면파 참고값이며 η나 Total Coupling에 넣지 않습니다(AR Coating 미반영).'));
  }

  private study(study: NonparaxialStudy) {
    const head = el('tr', {}, ...['a [mm]', 'c [mm]', '광경로 [mm]', '3w·|κ|', '입사각 [°]', '근축 η', '비근축 η', '수렴'].map((h) => el('th', {}, h)));
    const rows = study.cases.map((x) => el('tr', { 'data-study': '' },
      el('td', {}, fmt(x.a_mm, 3)), el('td', {}, fmt(x.c_mm, 3)), el('td', {}, fmt(x.total_path_mm, 3)),
      el('td', {}, fmt(x.max_3w_footprint_curvature, 3)), el('td', {}, x.incidence_deg.map((v) => fmt(v, 1)).join(' / ')),
      el('td', {}, fmt(x.paraxial_overlap, 4)), el('td', { class: 'warn' }, fmt(x.nonparaxial_overlap, 4)),
      el('td', {}, x.nonparaxial_status === 'Computed' ? '예' : '격자 변화 > 1e-4')));
    return el('section', { class: 'card', 'data-card': 'nonparaxial-study' }, el('h3', {}, 'Guard 밖 비근축 검산 (후보 아님)'),
      el('table', { class: 'grid-table' }, el('thead', {}, head), el('tbody', {}, ...rows)),
      el('div', { class: 'muted' }, 'Frozen Guard를 끈 근축 Exact 설계를 비근축 Scalar로 다시 계산했습니다. Aperture는 1e-6 Power 꼬리 반경(2.63 w)입니다. '
        + '후보로 채택하지 않으며, 다른 Family나 Guard 재검토(사용자 승인)를 판단하는 근거입니다.'));
  }

  /** P4b simultaneous placement errors: passive assembly and active alignment (chief-ray linear model). */
  private alignmentCard(c: Candidate) {
    const a = c.alignment!;
    if (!a.passive) return el('section', { class: 'card', 'data-card': 'alignment' }, el('h3', {}, '정렬 공차'), el('div', { class: 'muted' }, `계산하지 않음: ${a.reason ?? ''}`));
    const pct = (v: number) => `${fmt(100 * v, 1)} %`;
    const row = (label: string, s: AlignmentStats, extra: string, attrs: Record<string, string> = {}) => el('tr', attrs, el('td', {}, label),
      el('td', {}, fmt(s.median_db, 2)), el('td', { class: s.p90_db > 1 ? 'warn' : 'good' }, fmt(s.p90_db, 2)), el('td', {}, fmt(s.p99_db, 2)),
      el('td', {}, pct(s.yield_1db)), el('td', {}, extra));
    const head = el('tr', {}, ...['조립', '중앙값 [dB]', '90 % [dB]', '99 % [dB]', '1 dB 이내', '보정량(최대)'].map((h) => el('th', {}, h)));
    const rows = [row('Passive(모두 공차 안 무작위)', a.passive, '—', { 'data-alignment-passive': String(a.passive.p90_db) })];
    a.active.forEach((o, i) => rows.push(row(`Active: ${o.body} ${o.dofs === 'translation' ? '위치' : '기울기'}${o.practical ? '' : ' (범위 밖)'}`, o,
      `${o.max_travel.map((v) => fmt(v, 1)).join(' / ')} ${o.travel_unit === 'um' ? 'µm' : 'mrad'}`,
      i === 0 && a.best_compensator ? { 'data-alignment-best': String(o.p90_db) } : {})));
    const worst = [...a.single].sort((x, y) => y.loss_db - x.loss_db).slice(0, 4)
      .map((s) => `${s.body} ${s.dof} ±${fmt(s.tolerance, 2)} ${s.unit === 'um' ? 'µm' : 'mrad'} → ${fmt(s.loss_db, 2)} dB`).join(' · ');
    return el('section', { class: 'card', 'data-card': 'alignment' }, el('h3', {}, `정렬 공차 — ${c.id}`),
      el('table', { class: 'grid-table' }, el('thead', {}, head), el('tbody', {}, ...rows)),
      el('div', { class: 'muted' }, `가장 민감한 단일 오차: ${worst}`),
      el('div', { class: 'muted' }, `모델: 주광선 Jacobian + Gaussian 위치·각도 어긋남의 정확한 Overlap(크기·초점 변화 제외). 모든 소자의 5자유도를 공차 안에서 독립 균일 분포로 ${a.samples}회 추출. `
        + `Active는 한 소자의 위치(3) 또는 기울기(2)를 최적값으로 맞춘 뒤 고정 이동(±${fmt(a.tolerances.bond_translation_um, 2)} µm, ±${fmt(a.tolerances.bond_rotation_mrad, 2)} mrad)을 더한 결과. `
        + `보정량이 ${fmt(a.active_range.translation_um, 0)} µm 또는 ${fmt(a.active_range.rotation_mrad, 0)} mrad를 넘으면 범위 밖으로 표시합니다. 공차 값은 왼쪽 카드에서 바꿉니다(가정값).`));
  }

  /** P4 Family comparison and the automatic choice. */
  private familyCard(rows: NonNullable<Result['families']>) {
    const head = el('tr', {}, ...['Family', '상태', '후보', '최고 η', '반사면 정렬 최악 [dB]', 'Lens 1 dB 편심 [µm]', 'Passive 1 dB 수율', 'Active 90 % [dB]', '소자', '선택'].map((h) => el('th', {}, h)));
    const body = rows.map((r) => el('tr', { class: r.selected ? 'selected' : '', 'data-family-row': r.key, 'data-selected': String(r.selected) },
      el('td', {}, r.label), el('td', { title: r.reason ?? '' }, r.status), el('td', {}, String(r.count)),
      el('td', {}, fmt(r.best_eta, 4)), el('td', {}, fmt(r.best_reflector_pose_db, 2)), el('td', {}, fmt(r.lens_decenter_1db_um, 2)),
      el('td', {}, r.passive_yield_1db != null ? `${fmt(100 * r.passive_yield_1db, 1)} %` : '—'), el('td', {}, fmt(r.active_p90_db ?? null, 2)),
      el('td', {}, String(r.elements)), el('td', {}, r.selected ? `선택 · ${r.why ?? ''}` : '')));
    return el('section', { class: 'card', 'data-card': 'families' }, el('h3', {}, 'Family 비교'),
      el('table', { class: 'grid-table' }, el('thead', {}, head), el('tbody', {}, ...body)),
      el('div', { class: 'muted' }, '선택 규칙: 최종 η(보정 곡면 비근축 → 비근축 → 근축 순으로 있는 값)가 가장 높은 Family. 다만 최고 η와 0.01 이내면 소자가 적은 Family를 고릅니다. '
        + '정렬 최악은 반사면 하나를 ±5 µm·±1 mrad 움직였을 때의 손실이고, Lens 1 dB 편심은 다른 소자를 다시 맞추지 않을 때 Lens 편심 허용치입니다. '
        + '정렬 공차는 선택 규칙에 넣지 않았으니 표에서 함께 보세요.'));
  }

  /** P4 Lens Family candidates (accepted ones are also in the main table). */
  private lensReview(review: LensReview) {
    const selected = this.store.selectedCandidate;
    const head = el('tr', {}, ...['#', '채택', '비근축 η', '수렴', 'Lens f / Ø [µm]', '광경로 [mm]', '입사각 [°]', '제약'].map((h) => el('th', {}, h)));
    const rows = review.candidates.map((c) => {
      const lenses = c.scene.lenses ?? [];
      const ok = !!c.accepted;
      const row = el('tr', { class: c.id === selected?.id ? 'selected' : '', 'data-lens-candidate': c.id, title: c.id },
        el('td', {}, String(c.rank)),
        el('td', { 'data-lens-accepted': String(ok) }, ok ? 'Computed' : '미채택'),
        el('td', { class: ok ? 'good' : 'warn', 'data-lens-eta': String(c.metrics.nonparaxial_overlap ?? '') }, fmt(c.metrics.nonparaxial_overlap ?? null, 4)),
        el('td', {}, c.review_status === 'Computed' ? '예' : c.review_status === 'Unconverged' ? '미수렴' : c.review_status ?? '—'),
        el('td', {}, lenses.map((l) => `${l.id} ${fmt(l.focal_length_um, 0)} / ${fmt(2 * l.clear_radius_um, 0)}`).join(' · ')),
        el('td', {}, fmt(c.metrics.total_path_mm, 3)),
        el('td', {}, c.metrics.incidence_deg.map((v) => fmt(v, 1)).join(' / ')),
        el('td', { class: c.lens_constraint ? 'warn' : '' }, c.lens_constraint ? reasonLabel(c.lens_constraint) : '통과'));
      row.addEventListener('click', () => this.store.set({ selected: c.id }));
      return row;
    });
    const reasons = review.fail_reasons ?? [];
    const count = review.candidates.filter((c) => c.accepted).length;
    const limit = review.accept_rule?.min_nonparaxial_overlap ?? 0.95;
    return el('section', { class: 'card', 'data-card': 'lens-review' },
      el('div', { class: 'card-head' }, el('h3', {}, `Lens Family 후보 (${review.candidates.length})`),
        el('span', { class: `status ${count ? 'Computed' : 'Review'}` }, count ? `Computed ${count}개` : '채택 없음')),
      ...(review.candidates.length ? [el('table', { class: 'grid-table' }, el('thead', {}, head), el('tbody', {}, ...rows))] : []),
      ...(reasons.length && !review.candidates.length ? [el('div', { class: 'issue' }, reasons.map((r) => reasonLabel(r)).join(' / '))] : []),
      el('div', { class: 'muted' }, `Port 바로 앞에 두 면 비구면 Micro-lens(발산각 0.39 rad 이하 Fused silica, 넘으면 Silicon; 평평한 쪽이 Port)를 두어 출사 발산각을 θ' ${fmt(review.candidates[0]?.theta_out_rad ?? null, 3)} rad로 줄인 뒤`
        + ', 등가 Port 사이에서 두 반사면 Relay를 근축으로 설계했습니다. '
        + 'Lens는 Aplanatic(평행 출사 + Abbe 사인 조건)으로 맞추고, Lens·반사면 전체를 비근축 η로만 판정하며 반사면은 3·4차 Sag로 보정합니다. '
        + `채택 기준: 비근축 검산 수렴, η ≥ ${limit}, Lens 몸체가 Keep-out·Envelope 안, 다른 구간 Beam(1e-6 꼬리)과 반사면이 Lens 몸체를 지나지 않음. `
        + '근축 Guard 대신 비근축 검산으로 채택하는 Family입니다. 행을 누르면 3D/2D에 Lens와 Beam이 그려집니다. Lens 공차·코팅은 아직 계산하지 않았습니다.'));
  }

  private lensDetail(c: Candidate) {
    const lenses = c.scene.lenses ?? [];
    const checks = c.lens_checks ?? [];
    const head = el('tr', {}, ...['Lens', '재료 · n', 'f [µm]', '중심 두께 [µm]', 'Clear Ø [µm]', 'Port→Lens [µm]', '출사 방향 잔차 [mrad]', '사인 조건 오차 [nm]', '통과 sin', '무코팅 투과'].map((h) => el('th', {}, h)));
    const rows = lenses.map((l, i) => {
      const k = checks[i];
      return el('tr', { 'data-lens-material': l.material ?? '' }, el('td', {}, `${l.id} (${l.side === 'source' ? 'Source' : 'Target'})`),
        el('td', { title: l.material_source ?? '' }, `${l.material ?? '—'} · ${fmt(l.relative_index, 4)}`), el('td', {}, fmt(l.focal_length_um, 1)),
        el('td', {}, fmt(l.thickness_um, 1)), el('td', {}, fmt(2 * l.clear_radius_um, 0)), el('td', {}, fmt(l.port_distance_um, 2)),
        el('td', {}, k ? fmt(k.max_direction_rad * 1e3, 3) : '—'),
        el('td', {}, k ? fmt(k.max_sine_condition_error_m * 1e9, 1) : '—'), el('td', {}, k?.passes_to_sine != null ? fmt(k.passes_to_sine, 3) : '—'),
        el('td', { class: (l.uncoated_transmission ?? 1) < 0.9 ? 'warn' : '' }, l.uncoated_transmission != null ? fmt(l.uncoated_transmission, 3) : '—'));
    });
    const mirrors = c.scene.mirrors.map((m) => el('tr', {}, el('td', {}, m.id), el('td', { class: 'mono' }, m.vertex_mm.map((v) => fmt(v, 4)).join(', ')),
      el('td', {}, m.radius_of_curvature_ts_mm.map((r) => (r === null ? '∞' : fmt(r, 3))).join(' / ')), el('td', {}, fmt(m.incidence_deg, 2))));
    const history = (c.fit_history ?? []).map((h) => `${h.step} ${fmt(h.eta, 4)}`).join(' → ');
    const pose = c.lens_pose;
    const poseTable = pose ? el('table', { class: 'grid-table', 'data-lens-pose': '' },
      el('thead', {}, el('tr', {}, ...['Lens', `편심 ±${pose.steps.decenter_um} µm [dB]`, `축 방향 ±${pose.steps.axial_um} µm [dB]`, `기울기 ±${pose.steps.tilt_mrad} mrad [dB]`,
        '1 dB 편심 [µm]', '1 dB 축 방향 [µm]', '1 dB 기울기 [mrad]'].map((h) => el('th', {}, h)))),
      el('tbody', {}, ...pose.lenses.map((l) => el('tr', {}, el('td', {}, l.id), el('td', { class: l.decenter_loss_db > 1 ? 'warn' : '' }, fmt(l.decenter_loss_db, 2)),
        el('td', {}, fmt(l.axial_loss_db, 3)), el('td', {}, fmt(l.tilt_loss_db, 3)), el('td', { 'data-decenter-1db': String(l.decenter_1db_um ?? '') }, fmt(l.decenter_1db_um, 2)),
        el('td', {}, fmt(l.axial_1db_um, 2)), el('td', {}, fmt(l.tilt_1db_mrad, 1)))))) : null;
    return el('section', { class: 'card', 'data-detail': c.id, 'data-lens-detail': '' }, el('h3', {}, `${c.id} 상세 (Lens Family${c.accepted ? '' : ' · 미채택'})`),
      el('table', { class: 'grid-table' }, el('thead', {}, head), el('tbody', {}, ...rows)),
      el('table', { class: 'grid-table' }, el('thead', {}, el('tr', {}, ...['반사면', 'Vertex [mm]', 'R t / s [mm]', '입사각 [°]'].map((h) => el('th', {}, h)))), el('tbody', {}, ...mirrors)),
      el('div', { class: 'muted' }, `비근축 η ${fmt(c.metrics.nonparaxial_overlap ?? null, 4)} (${c.review_status}) · 격자 변화 ${(c.nonparaxial_check?.grid_change ?? 0).toExponential(1)} · `
        + `Aperture 밖 Power ${(c.nonparaxial_check?.clipped_power_fraction ?? 0).toExponential(1)} · 등가 Port 사이 근축 η ${fmt(c.metrics.normalized_mode_overlap, 4)}`),
      el('div', { class: 'muted' }, `맞춤 과정: ${history}`),
      ...(poseTable ? [poseTable, el('div', { class: 'muted' }, `비근축 정렬 연구(격자 ${pose!.grid}², 한 번에 하나씩, 다른 소자는 다시 맞추지 않음): `
        + `반사면 하나를 ±5 µm·±1 mrad 움직일 때 최악 ${fmt(pose!.reflectors_worst_loss_db, 2)} dB. 1 dB 허용치는 계산한 손실로 2차 추정 후 한 번 더 계산해 보정한 값입니다.`)] : []),
      el('div', { class: 'muted' }, '방향 잔차와 사인 조건 오차는 Port 1/e² 각의 1.5배(통과 sin 이내)까지 자오면 광선으로 확인한 값입니다. '
        + 'Clear 구경은 출사 방향 오차 1 mrad 이내인 광선까지이고, 그 밖의 Power는 비근축 검산에서 잘린 Power로 셉니다. '
        + '무코팅 투과는 두 면 수직 입사 Fresnel 값이며 η에는 넣지 않습니다(Silicon은 AR 코팅 전제). Lens 계수와 반사면 보정 계수는 결과 JSON(lens_review)에 있습니다.'));
  }

  private freeform(c: Candidate) {
    const f = c.freeform!;
    const names = (t: { u_power: number; v_power: number }) => `u${sup(t.u_power)}v${sup(t.v_power)}`;
    const rows = (f.reflectors ?? []).map((r) => el('tr', {},
      el('td', {}, r.id),
      el('td', {}, r.correction_size ? `${fmt(r.correction_size.footprint.pv_um, 3)} / ${fmt(r.correction_size.footprint.rms_um, 3)}` : '—'),
      el('td', {}, r.correction_size ? fmt(r.correction_size.footprint.max_slope_mrad, 2) : '—'),
      el('td', {}, fmt(r.max_sag_change_um, 1)),
      el('td', { class: 'mono' }, r.terms.filter((t) => t.coefficient_si !== 0)
        .map((t) => `${names(t)} ${t.coefficient_si.toExponential(3)}`).join(' · '))));
    return el('div', { 'data-freeform': f.status },
      el('div', { class: 'muted' }, `보정 곡면(P4): 비근축 η ${fmt(c.metrics.nonparaxial_overlap ?? null, 4)} → ${fmt(f.normalized_mode_overlap ?? null, 4)}`
        + (f.status !== 'Computed' ? ` (${f.status})` : '') + (f.constraint ? ` · 제약 위반: ${reasonLabel(f.constraint)}` : '')
        + ' · h = ½(κ₁u² + κ₂v²) + Σ c·uᵐvⁿ (u = t축, v = s축, SI 단위)'),
      el('table', { class: 'grid-table' }, el('thead', {}, el('tr', {}, ...['반사면', 'Footprint 안 보정 PV / RMS [µm]', '최대 기울기 변화 [mrad]', 'Aperture 모서리 Sag [µm]', '3·4차 계수'].map((h) => el('th', {}, h)))),
        el('tbody', {}, ...rows)),
      ...(f.pose ? [el('div', { class: 'muted', 'data-freeform-pose': '' },
        `비근축 정렬 민감도(반사면 하나씩 ±5 µm·두 주축 ±1 mrad, 최악 손실): 이차곡면 ${fmt(f.pose.quadric_worst_loss_db, 2)} dB · 보정 곡면 ${fmt(f.pose.corrected_worst_loss_db, 2)} dB. `
        + 'Footprint 값은 1/e² 발자국 타원 안, 가장자리 값은 처방 Aperture(4w) 모서리까지입니다. 빛이 거의 없는 가장자리 Sag는 Aperture를 줄이면 작아집니다.')] : []));
  }

  private table(candidates: Candidate[]) {
    const selected = this.store.selectedCandidate;
    const head = el('tr', {}, ...['#', '종류', '역할', '광경로 [mm]', 'η', '비근축 η', '보정 곡면 η', '3w·|κ|', '정렬 민감도 [dB]', '최소 R [mm]'].map((h) => el('th', { title: TITLES[h] ?? '' }, h)));
    const rows = candidates.map((c) => {
      const kmax = c.metrics.max_abs_curvature_per_m;
      const row = el('tr', { class: c.id === selected?.id ? 'selected' : '', 'data-candidate': c.id, title: c.id },
        el('td', {}, String(c.rank)),
        el('td', {}, el('span', { class: `family ${c.family}` }, c.family === 'exact' ? 'Exact' : c.family === 'lens_two_reflector' ? 'Lens + 2 반사면' : 'Near-match')),
        el('td', {}, c.role_labels.join(' · ')),
        el('td', {}, fmt(c.metrics.total_path_mm, 3)), el('td', {}, fmt(c.metrics.normalized_mode_overlap, 4)),
        el('td', { 'data-nonparaxial': String(c.metrics.nonparaxial_overlap ?? ''),
          class: (c.metrics.nonparaxial_overlap ?? 1) < 0.95 ? 'warn' : '' }, fmt(c.metrics.nonparaxial_overlap ?? null, 4)),
        el('td', { 'data-corrected': String(c.metrics.corrected_nonparaxial_overlap ?? ''),
          class: c.freeform?.constraint ? 'warn' : 'good', title: c.freeform?.constraint ?? '' },
          c.freeform?.status === 'Computed' ? fmt(c.metrics.corrected_nonparaxial_overlap ?? null, 4) + (c.freeform.constraint ? ' ⚠' : '')
            : c.freeform?.status ? `${fmt(c.metrics.corrected_nonparaxial_overlap ?? null, 4)} (${c.freeform.status === 'Unconverged' ? '미수렴' : c.freeform.status})` : '—'),
        el('td', {}, fmt(c.metrics.max_3w_footprint_curvature, 3)),
        el('td', {}, fmt(c.metrics.worst_pose_mismatch_db, 2)),
        el('td', {}, kmax ? fmt(1000 / kmax, 2) : '∞'));
      row.addEventListener('click', () => this.store.set({ selected: c.id }));
      return row;
    });
    const near = candidates.some((c) => c.family === 'near_match');
    return el('section', { class: 'card' }, el('h3', {}, `후보 비교 (${candidates.length})`),
      el('table', { class: 'grid-table' }, el('thead', {}, head), el('tbody', {}, ...rows)),
      el('div', { class: 'muted' }, near
        ? 'Near-match는 Frozen Guard 안에서 Overlap을 최대로 한 배치입니다(η < 1). '
        : 'Exact는 두 축 모두 q가 정확히 맞는 배치입니다(η = 1). ',
        'η는 Scalar Paraxial Normalized Mode Overlap이며 Total Coupling이 아닙니다. 비근축 η는 같은 처방을 근축 근사 없이(각스펙트럼 + 실제 곡면 광선) 계산한 값으로, 경사 반사면의 Coma 같은 고차 수차를 포함합니다. 정렬 민감도는 반사면 하나씩 ±5 µm·±1 mrad 오차를 줬을 때의 최악 Gaussian 손실이고, 3w·|κ| 한계는 0.15입니다.'));
  }

  private detail(c: Candidate) {
    const glass = c.scene.mirrors.some((m) => m.tir_possible !== undefined);
    const tensor = c.model === 'qtensor';
    const head = el('tr', {}, ...['반사면', 'Vertex [mm]', tensor ? 'R 주곡률 1 / 2 [mm]' : 'R t / s [mm]', '입사각 [°]', tensor ? 'Aperture 반폭 1 / 2 [mm]' : 'Aperture 반폭 t / s [mm]', tensor ? 'Footprint w 1 / 2 [µm]' : 'Footprint w t / s [µm]', ...(glass ? ['반사 방식'] : [])].map((h) => el('th', {}, h)));
    const rows = c.scene.mirrors.map((m) => el('tr', {},
      el('td', {}, m.id), el('td', { class: 'mono' }, m.vertex_mm.map((v) => fmt(v, 4)).join(', ')),
      el('td', {}, m.radius_of_curvature_ts_mm.map((r) => (r === null ? '∞' : fmt(r, 3))).join(' / ')),
      el('td', {}, fmt(m.incidence_deg, 2)), el('td', {}, m.half_aperture_ts_mm.map((a) => fmt(a, 4)).join(' / ')),
      el('td', {}, m.beam_footprint_radius_ts_um.map((w) => fmt(w, 2)).join(' / ')),
      ...(glass ? [el('td', { 'data-tir': String(m.tir_possible) }, m.tir_possible ? 'TIR 가능(뒤가 외부 매질일 때)' : '반사 Coating 필요')] : [])));
    const chips = el('div', { class: 'chips' }, ...Object.entries(c.status).map(([key, value]) =>
      el('span', { class: `chip st-${value}` }, `${STATUS_LABEL[key] ?? key}: ${value}`)));
    return el('section', { class: 'card', 'data-detail': c.id }, el('h3', {}, `${c.id} 상세`),
      el('table', { class: 'grid-table' }, el('thead', {}, head), el('tbody', {}, ...rows)), chips,
      ...(c.nonparaxial_check?.status ? [el('div', { class: 'muted', 'data-nonparaxial-detail': c.nonparaxial_check.status },
        c.nonparaxial_check.status === 'Uncomputed' ? '비근축 검산: 계산 안 됨'
          : `비근축 Scalar 검산 η ${fmt(c.nonparaxial_check.normalized_mode_overlap ?? null, 4)} (근축 η ${fmt(c.metrics.normalized_mode_overlap, 4)}) · `
            + `격자 변화 ${(c.nonparaxial_check.grid_change ?? 0).toExponential(1)} · Aperture 밖 Power ${(c.nonparaxial_check.clipped_power_fraction ?? 0).toExponential(1)} · `
            + '각스펙트럼 + 실제 곡면 광선, 모서리 회절·편광·Fresnel 계수 제외')] : []),
      ...(c.freeform?.reflectors ? [this.freeform(c)] : []),
      ...(tensor && c.ray_transfer_check ? [el('div', { class: 'muted', 'data-model': 'qtensor' },
        `q-tensor 모델(평면 밖 경로): 반사면 곡률 축은 각 반사면의 주곡률 방향입니다(3D에서 확인). Ray-transfer 검산 상대차 `
        + `${c.ray_transfer_check.q_tensor_relative_difference.toExponential(1)}, Symplectic 오차 ${c.ray_transfer_check.symplectic_error.toExponential(1)}`)] : []),
      el('div', { class: 'muted' }, `총 광경로 ${fmt(c.metrics.total_path_mm, 4)} mm${c.metrics.ambient_path_mm ? ` (외부 ${fmt(c.metrics.ambient_path_mm, 4)} mm 포함)` : ''} · 최대 투영 Beam 반경 ${fmt(c.metrics.max_projected_beam_radius_um, 2)} µm · Mode mismatch ${fmt(c.metrics.mode_mismatch_db, 4)} dB`));
  }

  private rejections(counts: Record<string, number>, total?: number, elapsed?: number) {
    const sum = total ?? Object.values(counts).reduce((a, b) => a + b, 0);
    const rows = Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([key, n]) => el('tr', {},
      el('td', {}, key === 'ok' ? 'Exact 해, 모든 Guard·제약 통과' : reasonLabel(key.split(': ').slice(1).join(': ')) || key),
      el('td', {}, String(n)), el('td', {}, `${fmt((100 * n) / sum, 1)}%`)));
    return el('details', { class: 'card', 'data-rejections': '' },
      el('summary', {}, `탐색 결과 분포 (${sum}개 배치${elapsed !== undefined ? ` · ${fmt(elapsed, 1)} s` : ''})`),
      el('table', { class: 'grid-table' }, el('thead', {}, el('tr', {}, el('th', {}, '판정'), el('th', {}, '개수'), el('th', {}, '비율'))), el('tbody', {}, ...rows)),
      el('div', { class: 'muted' }, '두 반사면 배치는 a(Source→M1)와 c(M2→Target) 두 길이로 정해집니다. 아래 "탐색 지도"에서 위치별 판정을 볼 수 있습니다.'));
  }

  private limits(result: Result) {
    return el('details', { class: 'card' }, el('summary', {}, '계산하지 않은 항목과 모델 한계'),
      el('ul', {}, ...(result.uncomputed ?? []).map((u) => el('li', {}, `Uncomputed · ${u}`)),
        ...(result.limitations ?? []).map((l) => el('li', {}, l))));
  }
}

function sup(n: number) {
  return '⁰¹²³⁴'[n] ?? String(n);
}
