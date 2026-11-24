import { clone, type Store } from './state';
import type { BoxMm, Constraints, ToleranceKey, Vec3 } from './types';
import { el } from './util';

/** Constraint card: they can only tighten the frozen guards (incidence ≤ 70°). */
export function constraintsCard(store: Store, rerender: () => void) {
  const doc = store.state.doc;
  const c: Constraints = doc.constraints ?? {};
  const edit = (mutate: (c: Constraints) => void) => {
    const next = clone(doc);
    next.constraints = { ...(next.constraints ?? {}) };
    mutate(next.constraints);
    next.constraints.source = 'User constraints in the Workspace';
    store.set({ doc: next });
    rerender();
  };
  const card = el('section', { class: 'card', 'data-card': 'constraints' }, el('h3', {}, '공간·제작 제약'));

  const half = el('input', { type: 'checkbox', 'data-key': 'constraints.port_body_halfspace' }) as HTMLInputElement;
  half.checked = c.port_body_halfspace ?? true;
  half.addEventListener('change', () => edit((x) => { x.port_body_halfspace = half.checked; }));
  card.append(el('label', { class: 'check', title: 'Fiber·Chip 본체가 각 Port 기준면 뒤쪽 공간을 차지한다고 가정합니다' }, half,
    ' Port 뒤 공간 사용 금지 (Port 본체 가정)'));

  card.append(numberRow('constraints.max_incidence_deg', '최대 입사각 [°] (≤ 70)', c.max_incidence_deg ?? 70, 1,
    (v) => edit((x) => { x.max_incidence_deg = v ?? 70; })));
  card.append(numberRow('constraints.min_roc', '최소 곡률반경 [mm] (비우면 제한 없음)', c.min_radius_of_curvature_mm ?? null, 0.1,
    (v) => edit((x) => { x.min_radius_of_curvature_mm = v; })));
  card.append(numberRow('constraints.clearance_um', 'Keep-out 여유 [µm]', c.clearance_um ?? 0, 1,
    (v) => edit((x) => { x.clearance_um = v ?? 0; })));

  const mode = doc.families?.lens_two_reflector ?? 'auto';
  const select = el('select', { 'data-key': 'families.lens_two_reflector' },
    ...[['auto', '자동 (Lens 없이 발산각 실패할 때만)'], ['compare', '항상 비교 (두 반사면과 함께 계산)'], ['off', '사용 안 함']]
      .map(([value, label]) => el('option', { value }, label))) as HTMLSelectElement;
  select.value = mode;
  select.addEventListener('change', () => {
    const next = clone(doc);
    next.families = { ...(next.families ?? {}), lens_two_reflector: select.value as 'auto' | 'compare' | 'off' };
    store.set({ doc: next });
    rerender();
  });
  card.append(el('div', { class: 'field', title: '비교 모드는 Lens를 붙일 수 있는 모든 Port(발산각 > 0.02 rad)에 Micro-lens를 두고 따로 계산합니다(수십 초)' },
    el('label', {}, 'Lens Family (P4)'), select));

  const tol = doc.tolerances ?? {};
  const setTol = (key: ToleranceKey, v: number | null) => {
    const next = clone(doc);
    const t = { ...(next.tolerances ?? {}) };
    if (v === null) delete t[key]; else t[key] = v;
    next.tolerances = t;
    store.set({ doc: next });
    rerender();
  };
  const tolRows: [ToleranceKey, string, number][] = [
    ['mirror_translation_um', '반사면 위치 ± [µm]', 5], ['mirror_rotation_mrad', '반사면 기울기 ± [mrad]', 1],
    ['lens_translation_um', 'Lens 편심 ± [µm]', 1], ['lens_axial_um', 'Lens 축 방향 ± [µm]', 1], ['lens_rotation_mrad', 'Lens 기울기 ± [mrad]', 1],
    ['bond_translation_um', 'Active 정렬 후 고정 이동 ± [µm]', 0.2], ['bond_rotation_mrad', 'Active 정렬 후 고정 기울기 ± [mrad]', 0.05]];
  card.append(el('div', { class: 'subhead' }, '정렬 공차 (P4b, 가정값)'));
  for (const [key, label, fallback] of tolRows) {
    card.append(numberRow(`tolerances.${key}`, label, tol[key] ?? fallback, key.endsWith('mrad') ? 0.01 : 0.1, (v) => setTol(key, v)));
  }

  const envToggle = el('input', { type: 'checkbox', 'data-key': 'constraints.envelope_on' }) as HTMLInputElement;
  envToggle.checked = Boolean(c.envelope_mm);
  envToggle.addEventListener('change', () => edit((x) => { x.envelope_mm = envToggle.checked ? defaultEnvelope(store) : null; }));
  card.append(el('label', { class: 'check' }, envToggle, ' Package Envelope(이 박스 안에 반사면·광로)'));
  if (c.envelope_mm) card.append(boxEditor('constraints.envelope', c.envelope_mm, (box) => edit((x) => { x.envelope_mm = box; })));

  const keepouts = c.keepouts_mm ?? [];
  keepouts.forEach((box, i) => {
    const remove = el('button', { class: 'small', title: '삭제' }, '×');
    remove.addEventListener('click', () => edit((x) => { x.keepouts_mm = keepouts.filter((_, j) => j !== i); }));
    const label = el('input', { type: 'text', 'data-key': `constraints.keepout.${i}.label` }) as HTMLInputElement;
    label.value = box.label ?? `Keep-out ${i + 1}`;
    label.addEventListener('change', () => edit((x) => { x.keepouts_mm = keepouts.map((k, j) => (j === i ? { ...k, label: label.value } : k)); }));
    card.append(el('div', { class: 'keepout' }, el('div', { class: 'keepout-head' }, label, remove),
      boxEditor(`constraints.keepout.${i}`, box, (b) => edit((x) => { x.keepouts_mm = keepouts.map((k, j) => (j === i ? { ...b, label: k.label } : k)); }))));
  });
  const add = el('button', { class: 'small', 'data-action': 'add-keepout' }, '+ Keep-out 박스');
  add.addEventListener('click', () => edit((x) => { x.keepouts_mm = [...keepouts, defaultKeepout(store, keepouts.length)]; }));
  card.append(add, el('div', { class: 'muted' }, '제약은 Frozen Guard를 완화하지 않고 더 좁히기만 합니다. Envelope·Keep-out은 Engine Package 검사에도 그대로 전달됩니다.'));
  return card;
}

function numberRow(key: string, label: string, value: number | null, step: number, commit: (v: number | null) => void) {
  const input = el('input', { type: 'number', step: String(step), 'data-key': key }) as HTMLInputElement;
  input.value = value === null ? '' : String(value);
  input.addEventListener('change', () => {
    if (input.value.trim() === '') return commit(null);
    const v = Number(input.value);
    if (Number.isFinite(v)) commit(v);
  });
  return el('div', { class: 'field' }, el('label', {}, label), input);
}

function boxEditor(key: string, box: BoxMm, commit: (b: BoxMm) => void) {
  const row = (which: 'min' | 'max') => {
    const inputs = box[which].map((v, i) => {
      const input = el('input', { type: 'number', step: '0.05', 'data-key': `${key}.${which}.${i}`, title: 'XYZ'[i] }) as HTMLInputElement;
      input.value = String(v);
      input.addEventListener('change', () => {
        const next = inputs.map((x) => Number(x.value)) as Vec3;
        if (next.every(Number.isFinite)) commit({ ...box, [which]: next });
      });
      return input;
    });
    return el('div', { class: 'field' }, el('label', {}, `${which === 'min' ? '최소' : '최대'} XYZ [mm]`), el('div', { class: 'triple' }, ...inputs));
  };
  return el('div', { class: 'box-editor' }, row('min'), row('max'));
}

function bounds(store: Store): { lo: Vec3; hi: Vec3 } {
  const p = [store.state.doc.ports.source.position_mm, store.state.doc.ports.target.position_mm];
  const lo = [0, 1, 2].map((i) => Math.min(p[0][i], p[1][i])) as Vec3;
  const hi = [0, 1, 2].map((i) => Math.max(p[0][i], p[1][i])) as Vec3;
  return { lo, hi };
}

function defaultEnvelope(store: Store): BoxMm {
  const { lo, hi } = bounds(store);
  const pad = Math.max(0.5, Math.max(...hi.map((h, i) => h - lo[i])) * 0.25);
  return { min: lo.map((v) => +(v - pad).toFixed(3)) as Vec3, max: hi.map((v) => +(v + pad).toFixed(3)) as Vec3 };
}

function defaultKeepout(store: Store, index: number): BoxMm {
  const { lo, hi } = bounds(store);
  const mid = lo.map((v, i) => (v + hi[i]) / 2);
  const half = 0.15;
  return { label: `Keep-out ${index + 1}`, min: mid.map((v) => +(v - half).toFixed(3)) as Vec3, max: mid.map((v) => +(v + half).toFixed(3)) as Vec3 };
}
