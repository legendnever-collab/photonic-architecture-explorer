import { clone, type Store } from './state';
import type { DesignDocument, Medium, MediumBlock, PortName, Provenance, Vec3 } from './types';
import { depthMm, silicaIndex } from './media';
import { AXES, PROVENANCE_LABEL, axisName, el } from './util';

function defaultBlock(doc: DesignDocument): MediumBlock {
  const zs = [doc.ports.source.position_mm[2], doc.ports.target.position_mm[2]];
  const top = Math.max(...zs);
  return {
    label: 'Fused silica (기본값, 교체 필요)', index: silicaIndex(doc.wavelength_nm),
    surface_point_mm: [0, 0, +(top - 0.1).toFixed(3)], surface_normal: [0, 0, 1], thickness_mm: 1.1,
    index_source: { provenance: 'assumed', source: `Fused silica Sellmeier (Malitson 1965) at ${doc.wavelength_nm} nm; default, replace with the actual glass` },
  };
}

export function glassCard(store: Store) {
  const doc = store.state.doc;
  const block = doc.medium_block ?? null;
  const edit = (mutate: (d: DesignDocument) => void) => {
    const next = clone(doc);
    mutate(next);
    store.set({ doc: next });
  };
  const card = el('section', { class: 'card', 'data-card': 'glass' }, el('h3', {}, 'Glass 매질 (P3)'));
  const toggle = el('input', { type: 'checkbox', 'data-key': 'glass.enabled' }) as HTMLInputElement;
  toggle.checked = Boolean(block);
  toggle.addEventListener('change', () => edit((d) => { d.medium_block = toggle.checked ? defaultBlock(d) : null; if (!toggle.checked) delete d.medium_block; }));
  card.append(el('label', { class: 'check', title: '평면 상면을 가진 Glass Block 하나. 반사면은 Port가 있는 매질 쪽에 둡니다.' }, toggle, ' Glass Block 사용 (평면 상면 + 선택 두께)'));
  if (!block) {
    card.append(el('div', { class: 'muted' }, 'Glass 안에서는 발산각이 1/n로 줄어듭니다. 수직 Fiber → Glass 상면 → 내부 반사면 → 매립 도파로 경로를 계산합니다.'));
    return card;
  }
  const setBlock = (mutate: (b: MediumBlock) => void, provenanceTouched = false) => edit((d) => {
    mutate(d.medium_block!);
    if (provenanceTouched) d.medium_block!.index_source = { provenance: 'assumed', source: 'User-entered glass index' };
  });

  const label = el('input', { type: 'text', 'data-key': 'glass.label' }) as HTMLInputElement;
  label.value = block.label ?? '';
  label.addEventListener('change', () => setBlock((b) => { b.label = label.value; }));
  card.append(el('div', { class: 'field' }, el('label', {}, '이름'), label));

  const index = numberInput('glass.index', block.index, 0.0001);
  index.addEventListener('change', () => { const v = Number(index.value); if (Number.isFinite(v)) setBlock((b) => { b.index = v; }, true); });
  card.append(el('div', { class: 'field' }, el('label', {}, `굴절률 n (외부 ${doc.ambient_index}보다 커야 함)`), index));

  const prov = el('select', { 'data-key': 'glass.provenance' }) as HTMLSelectElement;
  for (const key of ['measured', 'supplied', 'simulated', 'assumed', 'synthetic'] as Provenance[]) prov.append(el('option', { value: key }, PROVENANCE_LABEL[key]));
  prov.value = block.index_source?.provenance ?? 'assumed';
  const src = el('input', { type: 'text', 'data-key': 'glass.index_source' }) as HTMLInputElement;
  src.value = block.index_source?.source ?? '';
  const commitSource = () => setBlock((b) => { b.index_source = { provenance: prov.value as Provenance, source: src.value || 'User-entered glass index' }; });
  prov.addEventListener('change', commitSource);
  src.addEventListener('change', commitSource);
  card.append(el('div', { class: 'field' }, el('label', {}, '굴절률 근거'), el('div', { class: 'pair' }, prov, src)));

  const point = block.surface_point_mm.map((v, i) => {
    const input = numberInput(`glass.surface_point.${i}`, v, 0.01);
    input.title = 'XYZ'[i];
    input.addEventListener('change', () => {
      const next = point.map((x) => Number(x.value)) as Vec3;
      if (next.every(Number.isFinite)) setBlock((b) => { b.surface_point_mm = next; });
    });
    return input;
  });
  card.append(el('div', { class: 'field' }, el('label', {}, '상면 위의 한 점 XYZ [mm]'), el('div', { class: 'triple' }, ...point)));

  const normal = el('select', { 'data-key': 'glass.normal' }) as HTMLSelectElement;
  for (const name of Object.keys(AXES)) normal.append(el('option', { value: name }, name));
  normal.value = axisName(block.surface_normal) ?? '+Z';
  normal.addEventListener('change', () => setBlock((b) => { b.surface_normal = AXES[normal.value]; }));
  card.append(el('div', { class: 'field' }, el('label', {}, '상면 법선 (Glass 밖을 향함)'), normal));

  const thickness = numberInput('glass.thickness_mm', block.thickness_mm ?? null, 0.05);
  thickness.addEventListener('change', () => {
    const raw = thickness.value.trim();
    const v = Number(raw);
    if (raw === '' || (Number.isFinite(v) && v > 0)) setBlock((b) => { b.thickness_mm = raw === '' ? null : v; });
  });
  card.append(el('div', { class: 'field' }, el('label', {}, '두께 [mm] (비우면 바닥 없음)'), thickness));

  const media = el('div', { class: 'media' });
  for (const name of ['source', 'target'] as PortName[]) {
    const medium: Medium = doc.ports[name].medium ?? 'ambient';
    const d = depthMm(block, doc.ports[name].position_mm);
    media.append(el('div', { class: 'chip', 'data-medium': `${name}:${medium}` },
      `${name === 'source' ? 'Source' : 'Target'}: ${medium === 'block' ? `Glass 안 (깊이 ${d.toFixed(3)} mm)` : `외부 (상면 위 ${(-d).toFixed(3)} mm)`}`));
  }
  card.append(media, el('div', { class: 'muted' },
    'Port의 매질은 위치로 정해집니다. 외부 Port는 상면에서 굴절한 등가 Port로 바꿔 Glass 안에서 Relay를 풉니다. '
    + '반사면은 Glass 안(한쪽 Port가 Glass 안일 때)이나 밖(둘 다 외부일 때)에만 둡니다. Fresnel 투과는 참고값이며 Total Coupling에 넣지 않습니다.'));
  return card;
}

function numberInput(key: string, value: number | null, step: number) {
  const input = el('input', { type: 'number', step: String(step), 'data-key': key }) as HTMLInputElement;
  input.value = value === null ? '' : String(value);
  return input;
}
