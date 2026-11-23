import type { Store } from './state';
import type { Candidate, Result } from './types';
import { ROLE_LABEL, STATUS_LABEL, el, fmt, nextStep, reasonLabel } from './util';

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
    } else if (current.search?.rejection_counts) {
      this.root.append(this.rejections(current.search.rejection_counts, current.search.geometry_count));
    }
    this.root.append(this.limits(current));
  }

  private verdict(result: Result) {
    const card = el('section', { class: 'card', 'data-result-status': result.status },
      el('div', { class: 'card-head' }, el('h3', {}, '결과'), el('span', { class: `status ${result.status}` }, `${result.status} · ${STATUS_TEXT[result.status] ?? ''}`)),
      el('div', {}, reasonLabel(result.reason)));
    const step = nextStep(result.reason);
    if (step) card.append(el('div', { class: 'next' }, el('strong', {}, '다음 단계 '), step));
    for (const issue of result.issues ?? []) card.append(el('div', { class: 'issue' }, `${issue.path}: ${issue.message}`));
    card.append(el('div', { class: 'muted mono' }, `입력 SHA-256 ${result.document_sha256?.slice(0, 16) ?? '—'}…`));
    return card;
  }

  private table(candidates: Candidate[]) {
    const selected = this.store.selectedCandidate;
    const head = el('tr', {}, ...['#', '후보', '역할', '광경로 [mm]', 'η', '입사각 M1/M2 [°]', '3w·|κ| / 0.15'].map((h) => el('th', {}, h)));
    const rows = candidates.map((c) => {
      const row = el('tr', { class: c.id === selected?.id ? 'selected' : '', 'data-candidate': c.id },
        el('td', {}, String(c.rank)), el('td', { class: 'mono' }, c.id), el('td', {}, ROLE_LABEL[c.role ?? ''] ?? c.role ?? ''),
        el('td', {}, fmt(c.metrics.total_path_mm, 3)), el('td', {}, fmt(c.metrics.normalized_mode_overlap, 6)),
        el('td', {}, c.metrics.incidence_deg.map((a) => fmt(a, 1)).join(' / ')),
        el('td', {}, fmt(c.metrics.max_3w_footprint_curvature, 3)));
      row.addEventListener('click', () => this.store.set({ selected: c.id }));
      return row;
    });
    return el('section', { class: 'card' }, el('h3', {}, `후보 비교 (${candidates.length})`),
      el('table', { class: 'grid-table' }, el('thead', {}, head), el('tbody', {}, ...rows)),
      el('div', { class: 'muted' }, 'η는 Scalar Paraxial Normalized Mode Overlap입니다. 현재 후보는 Exact-q 해라 모두 1에 가깝고, 실제 구분은 광경로·Beam 크기·모델 여유로 합니다(P2에서 공차·제작성 기준 추가).'));
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

  private rejections(counts: Record<string, number>, geometryCount?: number) {
    const total = Object.values(counts).reduce((a, b) => a + b, 0);
    const rows = Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([reason, n]) => el('tr', {},
      el('td', {}, reasonLabel(reason.split(': ').slice(1).join(': ')) || reason), el('td', {}, String(n)), el('td', {}, `${fmt((100 * n) / total, 0)}%`)));
    return el('section', { class: 'card', 'data-rejections': '' }, el('h3', {}, `거절 사유 분포 (시도 ${total}${geometryCount ? ` · Geometry ${geometryCount}` : ''})`),
      el('table', { class: 'grid-table' }, el('thead', {}, el('tr', {}, el('th', {}, '사유'), el('th', {}, '개수'), el('th', {}, '비율'))), el('tbody', {}, ...rows)));
  }

  private limits(result: Result) {
    return el('details', { class: 'card' }, el('summary', {}, '계산하지 않은 항목과 모델 한계'),
      el('ul', {}, ...(result.uncomputed ?? []).map((u) => el('li', {}, `Uncomputed · ${u}`)),
        ...(result.limitations ?? []).map((l) => el('li', {}, l))));
  }
}
