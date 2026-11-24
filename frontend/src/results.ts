import type { Store } from './state';
import type { Candidate, NonparaxialStudy, Result } from './types';
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
      if (selected) this.root.append(this.detail(selected));
    }
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
        el('td', {}, el('span', { class: `family ${c.family}` }, c.family === 'exact' ? 'Exact' : 'Near-match')),
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
