import './style.css';
import { api } from './api';
import { Drawings, type ViewMode } from './drawings';
import { InputPanel } from './panel';
import { ResultsPanel } from './results';
import { Store } from './state';
import type { DesignDocument } from './types';
import { download, el } from './util';
import { Viewer3D } from './viewer3d';

const app = document.getElementById('app')!;
const scenarioSelect = el('select', { id: 'scenario', title: 'User Decision Benchmark 시나리오' }) as HTMLSelectElement;
const designButton = el('button', { id: 'design', class: 'primary', title: 'Ctrl+Enter' }, 'Design');
const openInput = el('input', { type: 'file', accept: 'application/json,.json', hidden: '' }) as HTMLInputElement;
const openButton = el('button', {}, '열기');
const exportDoc = el('button', { title: 'pae.design/1' }, '입력 JSON');
const exportResult = el('button', { title: 'pae.result/1' }, '결과 JSON');
const exportSvg = el('button', { title: '현재 2D 도면' }, '도면 SVG');
const title = el('div', { class: 'doc-title' });

const left = el('aside', { class: 'left' });
const viewerBox = el('div', { class: 'viewer' });
const drawingsBox = el('div', { class: 'drawings' });
const right = el('aside', { class: 'right' });
const tabs = el('div', { class: 'tabs' });
const tools = el('div', { class: 'viewer-tools' });

app.append(
  el('header', {}, el('div', { class: 'brand' }, 'Photonic Architecture Explorer'), scenarioSelect, title,
    el('div', { class: 'spacer' }), designButton, openButton, openInput, el('span', { class: 'sep' }), exportDoc, exportResult, exportSvg),
  el('main', {}, left, el('section', { class: 'center' }, el('div', { class: 'viewer-wrap' }, viewerBox, tools), tabs, drawingsBox), right),
);

const store = new Store({
  doc: null as unknown as DesignDocument, presets: [], scenarios: [], preview: null, result: null, resultFor: null,
  selected: null, activePort: null, busy: false, error: null,
});

(window as unknown as { __paeStore: Store }).__paeStore = store; // read-only hook for the browser acceptance check

let previewTimer = 0;
let previewSeq = 0;
store.subscribe((state, changed) => {
  if (changed.has('doc')) {
    title.textContent = state.doc.title;
    window.clearTimeout(previewTimer);
    previewTimer = window.setTimeout(async () => {
      const seq = ++previewSeq;
      try {
        const preview = await api.preview(state.doc);
        if (seq === previewSeq) store.set({ preview, error: null });
      } catch (e) {
        store.set({ error: String(e) });
      }
    }, 150);
  }
});

const panel = new InputPanel(left, store);
const viewer = new Viewer3D(viewerBox, store);
const drawings = new Drawings(drawingsBox, store);
new ResultsPanel(right, store);

for (const [id, label] of [['auto', '주 평면 + Fold'], ['all', '2×2'], ['xy', 'Top XY'], ['xz', 'Front XZ'], ['yz', 'Side YZ'], ['fold', 'Fold'], ['map', '탐색 지도']] as const) {
  const button = el('button', { class: id === 'auto' ? 'tab active' : 'tab', 'data-view': id }, label);
  button.addEventListener('click', () => {
    tabs.querySelectorAll('.tab').forEach((b) => b.classList.toggle('active', b === button));
    drawings.setView(id as ViewMode);
  });
  tabs.append(button);
}
if (!viewer.ok) document.querySelector('.center')!.classList.add('no-3d');
if (viewer.ok) {
  const fit = el('button', { class: 'small' }, '화면 맞춤');
  fit.addEventListener('click', () => viewer.fit());
  const scaleSelect = el('select', { class: 'small', title: 'Beam과 Mode 반경 표시 배율' }) as HTMLSelectElement;
  scaleSelect.append(el('option', { value: 'auto' }, 'Beam 확대 표시'), el('option', { value: 'true' }, 'Beam 실제 크기'));
  scaleSelect.addEventListener('change', () => viewer.setScaleMode(scaleSelect.value as 'auto' | 'true'));
  tools.append(fit, scaleSelect, el('span', { class: 'hint' }, '드래그 회전 · 휠 확대 · Port 더블클릭 후 화살표로 이동'));
}

async function runDesign() {
  const doc = store.state.doc;
  store.set({ busy: true, error: null });
  try {
    const result = await api.design(doc);
    store.set({ result, resultFor: JSON.stringify(doc), selected: result.selected_candidate_id ?? result.candidates[0]?.id ?? null, busy: false });
  } catch (e) {
    store.set({ busy: false, error: String(e) });
  }
}

async function loadScenario(id: string) {
  const doc = await api.scenario(id);
  store.set({ doc, result: null, resultFor: null, selected: null, activePort: null });
}

designButton.addEventListener('click', runDesign);
document.addEventListener('keydown', (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) runDesign(); });
scenarioSelect.addEventListener('change', () => loadScenario(scenarioSelect.value));
openButton.addEventListener('click', () => openInput.click());
openInput.addEventListener('change', async () => {
  const file = openInput.files?.[0];
  if (!file) return;
  try {
    const doc = JSON.parse(await file.text()) as DesignDocument;
    store.set({ doc, result: null, resultFor: null, selected: null, activePort: null });
    scenarioSelect.value = '';
  } catch (e) {
    store.set({ error: `JSON을 읽을 수 없습니다: ${e}` });
  }
  openInput.value = '';
});
const stem = () => (store.state.doc.scenario || store.state.doc.title || 'design').replace(/[^\w.-]+/g, '_');
exportDoc.addEventListener('click', () => download(`${stem()}.pae-design.json`, JSON.stringify(store.state.doc, null, 2), 'application/json'));
exportResult.addEventListener('click', () => {
  const result = store.currentResult;
  if (result) download(`${stem()}.pae-result.json`, JSON.stringify(result, null, 2), 'application/json');
  else store.set({ error: '현재 입력에 대한 Design 결과가 없습니다' });
});
exportSvg.addEventListener('click', () => drawings.exportSvg());

(async () => {
  const [presets, scenarios] = await Promise.all([api.presets(), api.scenarios()]);
  scenarioSelect.append(el('option', { value: '' }, '시나리오 선택…'));
  for (const s of scenarios) {
    const option = el('option', { value: s.id }, s.title) as HTMLOptionElement;
    if (!s.file) option.disabled = true;
    scenarioSelect.append(option);
  }
  const doc = await api.scenario('S1');
  scenarioSelect.value = 'S1';
  store.set({ presets, scenarios, doc });
  panel.render();
  document.body.dataset.ready = '1';
})();
