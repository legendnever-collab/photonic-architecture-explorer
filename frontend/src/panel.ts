import { constraintsCard } from './constraints';
import { clone, type Store } from './state';
import type { DesignDocument, PortName, PortScene, PortSpec, Preset, Vec3 } from './types';
import { AXES, PROVENANCE_LABEL, axisName, dot, el, fmt, norm } from './util';

const PORT_TITLE: Record<PortName, string> = { source: 'Source Port', target: 'Target Port' };
const PORT_HINT: Record<PortName, string> = {
  source: 'direction = 빛이 나가는 방향',
  target: 'direction = 도착하는 빛의 진행 방향',
};

/** Left panel: every Port quantity, its provenance and the per-Port guard from /api/preview. */
export class InputPanel {
  private note = '';

  constructor(private root: HTMLElement, private store: Store) {
    store.subscribe((_, changed) => {
      if (changed.has('doc') || changed.has('preview') || changed.has('presets') || changed.has('activePort')) this.render();
    });
  }

  private edit(mutate: (doc: DesignDocument) => void) {
    const doc = clone(this.store.state.doc);
    mutate(doc);
    this.store.set({ doc });
  }

  private editPort(name: PortName, mutate: (port: PortSpec) => void) {
    this.edit((doc) => mutate(doc.ports[name]));
  }

  render() {
    const active = document.activeElement as HTMLElement | null;
    const focusKey = active?.dataset?.key ?? null;
    const { doc, preview } = this.store.state;
    if (!doc) return;
    this.root.replaceChildren();
    const issues = preview?.status === 'Invalid' ? preview.issues ?? [] : [];

    const common = el('section', { class: 'card' }, el('h3', {}, '공통'));
    common.append(
      this.number('wavelength_nm', '파장 [nm]', doc.wavelength_nm, (v) => this.edit((d) => { d.wavelength_nm = v; }), 1),
      this.number('ambient_index', '외부 매질 굴절률 n', doc.ambient_index, (v) => this.edit((d) => { d.ambient_index = v; }), 0.0001),
    );
    this.root.append(common);
    if (issues.length) {
      this.root.append(el('section', { class: 'card issues' }, el('h3', {}, '입력 오류'),
        ...issues.map((i) => el('div', { class: 'issue' }, `${i.path}: ${i.message}`))));
    }
    if (this.note) this.root.append(el('div', { class: 'note' }, this.note));
    for (const name of ['source', 'target'] as PortName[]) {
      const scene = preview?.ports?.ports.find((p) => p.name === name) ?? null;
      this.root.append(this.port(name, doc.ports[name], scene));
    }
    this.root.append(constraintsCard(this.store, () => {}));
    if (focusKey) (this.root.querySelector(`[data-key="${focusKey}"]`) as HTMLElement | null)?.focus();
  }

  private port(name: PortName, port: PortSpec, scene: PortScene | null) {
    const { presets, activePort, doc } = this.store.state;
    const card = el('section', { class: `card port${activePort === name ? ' active' : ''}`, 'data-port': name });
    const pick = el('button', { class: 'small', title: '3D 화면에서 이 Port를 끌어 옮깁니다' }, activePort === name ? '이동 중' : '3D에서 이동');
    pick.addEventListener('click', () => this.store.set({ activePort: activePort === name ? null : name }));
    card.append(el('div', { class: 'card-head' }, el('h3', {}, PORT_TITLE[name]), pick));

    // Preset
    const select = el('select', { 'data-key': `${name}.preset` }) as HTMLSelectElement;
    select.append(el('option', { value: '' }, '직접 입력'));
    for (const p of presets) select.append(el('option', { value: p.id }, `${p.label} · ${p.wavelength_nm} nm`));
    select.value = port.preset ?? '';
    select.addEventListener('change', () => {
      const preset = presets.find((p) => p.id === select.value);
      if (preset) this.applyPreset(name, preset, 'vertical');
      else this.editPort(name, (p) => { p.preset = null; });
    });
    card.append(this.row('Preset', select));
    const preset = presets.find((p) => p.id === port.preset);
    if (preset && Math.abs(preset.wavelength_nm - doc.wavelength_nm) > 0.5) {
      card.append(el('div', { class: 'warn' }, `Preset 파장 ${preset.wavelength_nm} nm ≠ 문서 파장 ${doc.wavelength_nm} nm`));
    }

    card.append(this.vector(`${name}.position_mm`, 'Position [mm]', port.position_mm,
      (v) => this.editPort(name, (p) => { p.position_mm = v; p.evidence.placement = { provenance: 'assumed', source: 'User placement' }; }), 0.01));
    card.append(this.axisChoice(name, 'direction', `Direction (${PORT_HINT[name]})`, port.direction, null));
    card.append(this.axisChoice(name, 'sagittal_axis', 'Sagittal 축 s (t = s × d)', port.sagittal_axis, port.direction));

    const mfd = el('div', { class: 'pair' },
      this.number(`${name}.mfd_t`, 'MFD t [µm]', port.mfd_um[0], (v) => this.editMode(name, 0, v), 0.1),
      this.number(`${name}.mfd_s`, 'MFD s [µm]', port.mfd_um[1], (v) => this.editMode(name, 1, v), 0.1));
    const curvature = el('div', { class: 'pair' },
      this.number(`${name}.curv_t`, '1/R t [1/m]', port.wavefront_curvature_per_m[0], (v) => this.editPhase(name, 0, v), 1),
      this.number(`${name}.curv_s`, '1/R s [1/m]', port.wavefront_curvature_per_m[1], (v) => this.editPhase(name, 1, v), 1));
    card.append(mfd, curvature);
    if (preset) {
      const map = el('select', { 'data-key': `${name}.taxis` }) as HTMLSelectElement;
      map.append(el('option', { value: 'vertical' }, 't = vertical (기판 수직)'), el('option', { value: 'lateral' }, 't = lateral (기판 면내)'));
      map.value = Math.abs(port.mfd_um[0] - preset.mfd_vertical_um) < 1e-9 ? 'vertical' : 'lateral';
      map.addEventListener('change', () => this.applyPreset(name, preset, map.value as 'vertical' | 'lateral'));
      card.append(this.row('문헌 축 대응', map));
    }

    const chips = el('div', { class: 'chips' });
    for (const key of ['placement', 'mode', 'phase'] as const) {
      const ev = port.evidence[key];
      const label = { placement: '배치', mode: 'Mode', phase: 'Phase' }[key];
      chips.append(el('span', { class: `chip prov-${ev?.provenance ?? 'assumed'}`, title: ev?.source ?? '사용자 입력' },
        `${label}: ${PROVENANCE_LABEL[ev?.provenance ?? 'assumed']}`));
    }
    card.append(chips);
    if (scene) card.append(this.guard(scene));
    return card;
  }

  private guard(scene: PortScene) {
    const g = scene.divergence_guard;
    const pass = g.status === 'Pass';
    return el('div', { class: `guard ${pass ? 'pass' : 'fail'}`, 'data-guard': scene.name },
      el('strong', {}, `발산각 Guard ${pass ? 'Pass' : 'Fail'}`),
      ` · ${fmt(g.max_divergence_rad, 3)} / ${g.limit_rad} rad · 통과 최소 MFD ${fmt(g.min_waist_mfd_um, 2)} µm`,
      el('div', { class: 'muted' }, `Waist ${scene.mode.map((m) => fmt(2 * m.waist_radius_um, 2)).join(' × ')} µm · Rayleigh ${scene.mode.map((m) => fmt(m.rayleigh_range_mm, 3)).join(' / ')} mm`));
  }

  private applyPreset(name: PortName, preset: Preset, tIs: 'vertical' | 'lateral') {
    this.editPort(name, (p) => {
      p.preset = preset.id;
      p.label = preset.label;
      p.mfd_um = tIs === 'vertical' ? [preset.mfd_vertical_um, preset.mfd_lateral_um] : [preset.mfd_lateral_um, preset.mfd_vertical_um];
      p.wavefront_curvature_per_m = [0, 0];
      p.evidence.mode = { provenance: preset.mode_provenance, source: `${preset.source} · t=${tIs} axis (${preset.axis_note})` };
      p.evidence.phase = { provenance: preset.mode_provenance === 'synthetic' ? 'synthetic' : 'assumed', source: preset.phase_note };
    });
  }

  private editMode(name: PortName, index: 0 | 1, value: number) {
    this.editPort(name, (p) => {
      p.mfd_um[index] = value;
      p.preset = null;
      p.evidence.mode = { provenance: 'assumed', source: `User-edited MFD${p.label ? ` (started from ${p.label})` : ''}` };
    });
  }

  private editPhase(name: PortName, index: 0 | 1, value: number) {
    this.editPort(name, (p) => {
      p.wavefront_curvature_per_m[index] = value;
      p.evidence.phase = { provenance: 'assumed', source: 'User-edited wavefront curvature' };
    });
  }

  private axisChoice(name: PortName, key: 'direction' | 'sagittal_axis', label: string, value: Vec3, perpendicularTo: Vec3 | null) {
    const wrap = el('div', { class: 'field' }, el('label', {}, label));
    const select = el('select', { 'data-key': `${name}.${key}` }) as HTMLSelectElement;
    for (const [axis, v] of Object.entries(AXES)) {
      if (perpendicularTo && Math.abs(dot(v, perpendicularTo)) > 1e-12) continue;
      select.append(el('option', { value: axis }, axis));
    }
    select.append(el('option', { value: 'custom' }, '직접 입력 (벡터)'));
    const current = axisName(value);
    select.value = current && select.querySelector(`option[value="${current}"]`) ? current : 'custom';
    select.addEventListener('change', () => {
      if (select.value === 'custom') return this.render();
      const axis = AXES[select.value];
      this.note = '';
      this.editPort(name, (p) => {
        p[key] = [...axis] as Vec3;
        p.evidence.placement = { provenance: 'assumed', source: 'User placement' };
        if (key === 'direction' && Math.abs(dot(p.sagittal_axis, axis)) > 1e-12) {
          const replacement = Object.entries(AXES).find(([, v]) => Math.abs(dot(v, axis)) < 1e-12)!;
          p.sagittal_axis = [...replacement[1]] as Vec3;
          this.note = `${PORT_TITLE[name]}: direction과 수직이 되도록 Sagittal 축을 ${replacement[0]}로 바꿨습니다.`;
        }
      });
    });
    wrap.append(select);
    if (select.value === 'custom') {
      wrap.append(this.vector(`${name}.${key}.custom`, '', value, (v) => this.editPort(name, (p) => { p[key] = v; }), 0.001));
      const n = norm(value);
      const normalize = el('button', { class: 'small', title: '엔진은 자동 정규화하지 않습니다. 버튼을 누르면 입력값을 단위 벡터로 바꿉니다.' }, `정규화 (|v| = ${fmt(n, 6)})`);
      normalize.addEventListener('click', () => this.editPort(name, (p) => { p[key] = value.map((c) => c / n) as Vec3; }));
      wrap.append(normalize);
    }
    return wrap;
  }

  private number(key: string, label: string, value: number, commit: (v: number) => void, step: number) {
    const input = el('input', { type: 'number', step: String(step), 'data-key': key }) as HTMLInputElement;
    input.value = String(value);
    input.addEventListener('change', () => {
      const v = Number(input.value);
      if (input.value.trim() !== '' && Number.isFinite(v)) commit(v);
      else input.value = String(value);
    });
    return el('div', { class: 'field' }, el('label', {}, label), input);
  }

  private vector(key: string, label: string, value: Vec3, commit: (v: Vec3) => void, step: number) {
    const inputs = value.map((c, i) => {
      const input = el('input', { type: 'number', step: String(step), 'data-key': `${key}.${i}`, title: 'XYZ'[i] }) as HTMLInputElement;
      input.value = String(c);
      input.addEventListener('change', () => {
        const next = inputs.map((x) => Number(x.value));
        if (next.every(Number.isFinite)) commit(next as Vec3);
      });
      return input;
    });
    return el('div', { class: 'field' }, ...(label ? [el('label', {}, label)] : []), el('div', { class: 'triple' }, ...inputs));
  }

  private row(label: string, control: HTMLElement) {
    return el('div', { class: 'field' }, el('label', {}, label), control);
  }
}
