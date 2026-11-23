import type { Store } from './state';
import type { Candidate, Result } from './types';
import { STATUS_LABEL, el, fmt, nextStep, reasonLabel } from './util';

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
    if (current.candidates.length) {
      this.root.append(this.table(current.candidates));
      const selected = this.store.selectedCandidate;
      if (selected) this.root.append(this.detail(selected));
    }
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

  private table(candidates: Candidate[]) {
    const selected = this.store.selectedCandidate;
    const head = el('tr', {}, ...['#', '종류', '역할', '광경로 [mm]', 'η', '3w·|κ|', '정렬 민감도 [dB]', '최소 R [mm]'].map((h) => el('th', {}, h)));
    const rows = candidates.map((c) => {
      const kmax = c.metrics.max_abs_curvature_per_m;
      const row = el('tr', { class: c.id === selected?.id ? 'selected' : '', 'data-candidate': c.id, title: c.id },
        el('td', {}, String(c.rank)),
        el('td', {}, el('span', { class: `family ${c.family}` }, c.family === 'exact' ? 'Exact' : 'Near-match')),
        el('td', {}, c.role_labels.join(' · ')),
        el('td', {}, fmt(c.metrics.total_path_mm, 3)), el('td', {}, fmt(c.metrics.normalized_mode_overlap, 4)),
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
        'η는 Scalar Paraxial Normalized Mode Overlap이며 Total Coupling이 아닙니다. 정렬 민감도는 반사면 하나씩 ±5 µm·±1 mrad 오차를 줬을 때의 최악 Gaussian 손실이고, 3w·|κ| 한계는 0.15입니다.'));
  }

  private detail(c: Candidate) {
    const head = el('tr', {}, ...['반사면', 'Vertex [mm]', 'R t / s [mm]', '입사각 [°]', 'Aperture 반폭 t / s [mm]', 'Footprint w t / s [µm]'].map((h) => el('th', {}, h)));
    const rows = c.scene.mirrors.map((m) => el('tr', {},
      el('td', {}, m.id), el('td', { class: 'mono' }, m.vertex_mm.map((v) => fmt(v, 4)).join(', ')),
      el('td', {}, m.radius_of_curvature_ts_mm.map((r) => (r === null ? '∞' : fmt(r, 3))).join(' / ')),
      el('td', {}, fmt(m.incidence_deg, 2)), el('td', {}, m.half_aperture_ts_mm.map((a) => fmt(a, 4)).join(' / ')),
      el('td', {}, m.beam_footprint_radius_ts_um.map((w) => fmt(w, 2)).join(' / '))));
    const chips = el('div', { class: 'chips' }, ...Object.entries(c.status).map(([key, value]) =>
      el('span', { class: `chip st-${value}` }, `${STATUS_LABEL[key] ?? key}: ${value}`)));
    return el('section', { class: 'card', 'data-detail': c.id }, el('h3', {}, `${c.id} 상세`),
      el('table', { class: 'grid-table' }, el('thead', {}, head), el('tbody', {}, ...rows)), chips,
      el('div', { class: 'muted' }, `총 광경로 ${fmt(c.metrics.total_path_mm, 4)} mm · 최대 투영 Beam 반경 ${fmt(c.metrics.max_projected_beam_radius_um, 2)} µm · Mode mismatch ${fmt(c.metrics.mode_mismatch_db, 4)} dB`));
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
