import type { Store } from './state';
import type { Candidate, PortName, Vec3 } from './types';
import { download, el, fmt, norm } from './util';
import { constraintBoxes, niceScale, sceneExtent } from './viewer3d';

export type ViewId = 'xy' | 'xz' | 'yz' | 'fold' | 'map';
export type ViewMode = ViewId | 'all' | 'auto';
const NS = 'http://www.w3.org/2000/svg';
const W = 640, H = 420, PAD = 40;
const FONT = '"Arial Narrow", "Malgun Gothic", Arial, sans-serif';
const VIEWS: Record<Exclude<ViewId, 'fold' | 'map'>, { title: string; axes: [number, number]; names: [string, string] }> = {
  xy: { title: 'Top · XY', axes: [0, 1], names: ['X', 'Y'] },
  xz: { title: 'Front · XZ', axes: [0, 2], names: ['X', 'Z'] },
  yz: { title: 'Side · YZ', axes: [1, 2], names: ['Y', 'Z'] },
};
const PORT_COLOR: Record<PortName, string> = { source: '#1f6feb', target: '#d9480f' };

type P2 = [number, number];

function svg(tag: string, attrs: Record<string, string | number> = {}, text?: string) {
  const node = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, String(v));
  if (text !== undefined) node.textContent = text;
  return node;
}

function niceStep(span: number, target = 6) {
  const raw = span / target;
  const exp = 10 ** Math.floor(Math.log10(raw));
  const base = raw / exp;
  return (base >= 5 ? 5 : base >= 2 ? 2 : 1) * exp;
}

/** Orthographic engineering views and the unfolded beam-envelope (Fold) view. */
export class Drawings {
  view: ViewMode = 'auto';

  constructor(private root: HTMLElement, private store: Store) {
    store.subscribe((_, changed) => {
      if (changed.has('doc') || changed.has('preview') || changed.has('result') || changed.has('selected')) this.render();
    });
  }

  setView(view: ViewMode) {
    this.view = view;
    this.render();
  }

  render() {
    this.root.replaceChildren();
    const views: ViewId[] = this.view === 'all' ? ['xy', 'xz', 'yz', 'fold'] : this.view === 'auto' ? [this.mainPlane(), this.store.selectedCandidate || !this.store.currentResult?.search?.map ? 'fold' : 'map'] : [this.view];
    this.root.className = views.length > 1 ? 'drawings grid' : 'drawings single';
    for (const view of views) this.root.append(view === 'fold' ? this.fold() : view === 'map' ? this.map() : this.ortho(view));
  }

  /** The orthographic view in which the design spreads widest (normally the fold plane). */
  mainPlane(): Exclude<ViewId, 'fold' | 'map'> {
    const doc = this.store.state.doc;
    const points: Vec3[] = [doc.ports.source.position_mm, doc.ports.target.position_mm,
      ...(this.store.selectedCandidate?.scene.path.points_mm ?? [])];
    const spread = (i: number) => Math.max(...points.map((p) => p[i])) - Math.min(...points.map((p) => p[i]));
    const [x, y, z] = [0, 1, 2].map(spread);
    const area = { xy: x * y + 1e-9 * (x + y), xz: x * z + 1e-9 * (x + z), yz: y * z + 1e-9 * (y + z) };
    return (Object.entries(area).sort((a, b) => b[1] - a[1])[0][0]) as Exclude<ViewId, 'fold' | 'map'>;
  }

  exportSvg() {
    const figures = [...this.root.querySelectorAll('svg')] as SVGSVGElement[];
    let out: SVGSVGElement;
    if (figures.length === 1) {
      out = figures[0].cloneNode(true) as SVGSVGElement;
    } else {
      out = svg('svg', { xmlns: NS, viewBox: `0 0 ${2 * W} ${2 * H}`, width: 2 * W, height: 2 * H }) as SVGSVGElement;
      figures.forEach((figure, i) => {
        const inner = figure.cloneNode(true) as SVGSVGElement;
        inner.setAttribute('x', String((i % 2) * W));
        inner.setAttribute('y', String(Math.floor(i / 2) * H));
        inner.setAttribute('width', String(W));
        inner.setAttribute('height', String(H));
        out.append(inner);
      });
    }
    out.setAttribute('xmlns', NS);
    const name = (this.store.state.doc.scenario || 'design').replace(/[^\w.-]+/g, '_');
    download(`${name}_${this.view}.svg`, new XMLSerializer().serializeToString(out), 'image/svg+xml');
  }

  private frame(title: string, subtitle: string) {
    const root = svg('svg', { xmlns: NS, viewBox: `0 0 ${W} ${H}`, class: 'drawing', 'font-family': FONT, 'font-size': 13 });
    root.append(svg('rect', { x: 0, y: 0, width: W, height: H, fill: '#ffffff' }));
    root.append(svg('text', { x: 12, y: 20, 'font-size': 15, 'font-weight': 700, fill: '#1b2733' }, title));
    root.append(svg('text', { x: 12, y: 37, 'font-size': 12, fill: '#57606a' }, subtitle));
    return root;
  }

  private ortho(view: Exclude<ViewId, 'fold' | 'map'>) {
    const spec = VIEWS[view];
    const [a, b] = spec.axes;
    const state = this.store.state;
    const result = this.store.currentResult;
    const candidates = result?.candidates ?? [];
    const selected = this.store.selectedCandidate;
    const extent = sceneExtent(state, candidates);
    const k = niceScale(extent.size, extent.maxRadiusUm) * 1e-3;
    const project = (p: Vec3): P2 => [p[a], p[b]];

    const boxes = constraintBoxes(state);
    const points: P2[] = [project(state.doc.ports.source.position_mm), project(state.doc.ports.target.position_mm),
      ...boxes.flatMap((b) => [project(b.min), project(b.max)])];
    for (const c of candidates) {
      points.push(...c.scene.path.points_mm.map(project));
      for (const m of c.scene.mirrors) points.push(...m.surface_grid_mm.flat().map(project));
    }
    let [u0, u1] = [Math.min(...points.map((p) => p[0])), Math.max(...points.map((p) => p[0]))];
    let [v0, v1] = [Math.min(...points.map((p) => p[1])), Math.max(...points.map((p) => p[1]))];
    const span = Math.max(u1 - u0, v1 - v0, extent.size * 0.25, 0.1);
    u0 -= span * 0.12; u1 += span * 0.12; v0 -= span * 0.12; v1 += span * 0.12;
    const s = Math.min((W - 2 * PAD) / (u1 - u0), (H - 2 * PAD - 20) / (v1 - v0));
    const cu = (u0 + u1) / 2, cv = (v0 + v1) / 2;
    const X = (u: number) => W / 2 + (u - cu) * s;
    const Y = (v: number) => H / 2 + 10 - (v - cv) * s;
    const xy = (p: P2) => `${X(p[0]).toFixed(2)},${Y(p[1]).toFixed(2)}`;

    const root = this.frame(spec.title, k === 1e-3 ? 'Beam 실제 크기' : `Beam 반경 ×${fmt(k * 1e3, 0)} 확대 · Geometry 실제 크기 · 단위 mm`);
    // grid and ticks
    const step = niceStep(Math.max(u1 - u0, v1 - v0));
    const grid = svg('g', { stroke: '#eef1f4', 'stroke-width': 1 });
    const ticks = svg('g', { fill: '#8c959f', 'font-size': 11 });
    for (let u = Math.ceil(u0 / step) * step; u <= u1; u += step) {
      grid.append(svg('line', { x1: X(u), y1: Y(v0), x2: X(u), y2: Y(v1) }));
      ticks.append(svg('text', { x: X(u), y: Y(v0) + 12, 'text-anchor': 'middle' }, fmt(u, step < 0.1 ? 2 : step < 1 ? 1 : 0)));
    }
    for (let v = Math.ceil(v0 / step) * step; v <= v1; v += step) {
      grid.append(svg('line', { x1: X(u0), y1: Y(v), x2: X(u1), y2: Y(v) }));
      ticks.append(svg('text', { x: X(u0) - 4, y: Y(v) + 3, 'text-anchor': 'end' }, fmt(v, step < 0.1 ? 2 : step < 1 ? 1 : 0)));
    }
    root.append(grid, ticks);
    root.append(svg('text', { x: W - 14, y: Y(v0) + 12, 'text-anchor': 'end', 'font-weight': 700, fill: '#57606a' }, `${spec.names[0]} →`));
    root.append(svg('text', { x: X(u0) - 4, y: 54, 'text-anchor': 'end', 'font-weight': 700, fill: '#57606a' }, `${spec.names[1]} ↑`));

    for (const box of boxes) {
      const [p0, p1] = [project(box.min), project(box.max)];
      const keepout = box.kind === 'keepout';
      root.append(svg('rect', { x: X(p0[0]), y: Y(p1[1]), width: (p1[0] - p0[0]) * s, height: (p1[1] - p0[1]) * s,
        fill: keepout ? '#d1242f' : 'none', 'fill-opacity': keepout ? 0.1 : 0, stroke: keepout ? '#d1242f' : '#57606a',
        'stroke-dasharray': keepout ? '' : '6 4', 'data-kind': box.kind }));
      root.append(svg('text', { x: X(p0[0]) + 3, y: Y(p1[1]) + 13, 'font-size': 11, fill: keepout ? '#d1242f' : '#57606a' }, box.label));
    }
    for (const c of candidates) if (c.id !== selected?.id) root.append(this.path(c, project, xy, false));
    if (selected) {
      root.append(this.envelope(selected, project, xy, k));
      root.append(this.path(selected, project, xy, true));
      selected.scene.path.segments.forEach((segment, j) => {
        const m = project([0, 1, 2].map((i) => (segment.start_mm[i] + segment.end_mm[i]) / 2) as Vec3);
        const d = project(segment.direction);
        const len = Math.hypot(d[0], d[1]);
        const nrm: P2 = len > 1e-9 ? [-d[1] / len, d[0] / len] : [0, 1];
        root.append(svg('text', { x: X(m[0]) + nrm[0] * 14, y: Y(m[1]) - nrm[1] * 14, 'text-anchor': 'middle', 'font-size': 12, fill: '#b42318', 'data-kind': 'segment', 'data-length-mm': segment.length_mm },
          `L${j + 1} ${fmt(segment.length_mm, 3)}`));
      });
      selected.scene.mirrors.forEach((mirror, index) => {
        const g = mirror.surface_grid_mm, n = g.length;
        const border = [...g[0], ...g.map((r) => r[n - 1]), ...[...g[n - 1]].reverse(), ...g.map((r) => r[0]).reverse()];
        root.append(svg('polygon', { points: border.map((q) => xy(project(q))).join(' '), fill: '#8b95a1', 'fill-opacity': 0.18, stroke: '#57606a', 'stroke-width': 0.8 }));
        const p = project(mirror.vertex_mm);
        const dy = index % 2 === 0 ? -8 : 18;
        const roc = mirror.radius_of_curvature_ts_mm.map((r) => (r === null ? '∞' : fmt(r, 2))).join('/');
        root.append(svg('rect', { x: X(p[0]) - 3, y: Y(p[1]) - 3, width: 6, height: 6, fill: '#1b2733', 'data-kind': 'mirror', 'data-id': mirror.id, 'data-u-mm': p[0], 'data-v-mm': p[1] }));
        root.append(svg('text', { x: X(p[0]) + 8, y: Y(p[1]) + dy, 'font-size': 12, fill: '#1b2733' }, `${mirror.id} R ${roc} · ${fmt(mirror.incidence_deg, 1)}°`));
      });
    }
    for (const name of ['source', 'target'] as PortName[]) root.append(this.port(name, project, X, Y));
    // scale bar
    const bar = niceStep(u1 - u0, 5);
    const bx = 16, by = H - 14;
    root.append(svg('line', { x1: bx, y1: by, x2: bx + bar * s, y2: by, stroke: '#1b2733', 'stroke-width': 2 }));
    root.append(svg('text', { x: bx + (bar * s) / 2, y: by - 5, 'text-anchor': 'middle', 'font-size': 11, fill: '#1b2733' }, `${fmt(bar, bar < 1 ? 2 : 0)} mm`));
    if (!result) root.append(svg('text', { x: W - 12, y: 20, 'text-anchor': 'end', 'font-size': 12, fill: '#57606a' }, 'Design 전: Port만 표시'));
    return el('figure', { class: 'figure', 'data-view': view }, root);
  }

  private path(c: Candidate, project: (p: Vec3) => P2, xy: (p: P2) => string, selected: boolean) {
    return svg('polyline', {
      points: c.scene.path.points_mm.map((p) => xy(project(p))).join(' '), fill: 'none',
      stroke: selected ? '#b42318' : '#9aa5b1', 'stroke-width': selected ? 1.6 : 1, 'stroke-dasharray': selected ? '' : '4 3',
      'data-kind': 'path', 'data-id': c.id,
    });
  }

  private envelope(c: Candidate, project: (p: Vec3) => P2, xy: (p: P2) => string, k: number) {
    const group = svg('g', { fill: '#e5484d', 'fill-opacity': 0.22, stroke: '#e5484d', 'stroke-width': 0.6 });
    c.scene.path.segments.forEach((segment, j) => {
      const d = project(segment.direction);
      const len = Math.hypot(d[0], d[1]);
      if (len < 1e-6) return; // travelling along the view axis: no visible envelope
      const n: P2 = [-d[1] / len, d[0] / len];
      const t = project(segment.t_axis), s = project(segment.s_axis);
      const tn = t[0] * n[0] + t[1] * n[1], sn = s[0] * n[0] + s[1] * n[1];
      const samples = c.scene.beam.samples.filter((x) => x.segment === j);
      const upper: P2[] = [], lower: P2[] = [];
      for (const sample of samples) {
        const p = project(sample.point_mm);
        const w = Math.hypot(sample.radius_t_um * tn, sample.radius_s_um * sn) * k;
        upper.push([p[0] + n[0] * w, p[1] + n[1] * w]);
        lower.push([p[0] - n[0] * w, p[1] - n[1] * w]);
      }
      group.append(svg('polygon', { points: [...upper, ...lower.reverse()].map(xy).join(' ') }));
    });
    return group;
  }

  private port(name: PortName, project: (p: Vec3) => P2, X: (u: number) => number, Y: (v: number) => number) {
    const spec = this.store.state.doc.ports[name];
    const p = project(spec.position_mm);
    const d = project(spec.direction);
    const color = PORT_COLOR[name];
    const group = svg('g', { 'data-kind': 'port', 'data-id': name, 'data-u-mm': p[0], 'data-v-mm': p[1] });
    const x = X(p[0]), y = Y(p[1]);
    const len = Math.hypot(d[0], d[1]);
    if (len > 1e-9) {
      const ux = d[0] / len, uy = -d[1] / len, L = 34 * Math.min(1, len / Math.max(norm(spec.direction), 1e-12));
      const [x0, y0, x1, y1] = name === 'source' ? [x, y, x + ux * L, y + uy * L] : [x - ux * L, y - uy * L, x, y];
      group.append(svg('line', { x1: x0, y1: y0, x2: x1, y2: y1, stroke: color, 'stroke-width': 2 }));
      const hx = x1 - ux * 8, hy = y1 - uy * 8;
      group.append(svg('polygon', { points: `${x1},${y1} ${hx - uy * 4},${hy + ux * 4} ${hx + uy * 4},${hy - ux * 4}`, fill: color }));
    } else {
      // direction normal to the view: ⊙ out of the page, ⊗ into it
      const out = spec.direction[[0, 1, 2].find((i) => !inView(project, i))!] > 0;
      group.append(svg('circle', { cx: x, cy: y, r: 7, fill: 'none', stroke: color, 'stroke-width': 1.5 }));
      group.append(out ? svg('circle', { cx: x, cy: y, r: 2, fill: color }) : svg('path', { d: `M${x - 4} ${y - 4}L${x + 4} ${y + 4}M${x + 4} ${y - 4}L${x - 4} ${y + 4}`, stroke: color, 'stroke-width': 1.5 }));
    }
    group.append(svg('circle', { cx: x, cy: y, r: 3, fill: color }));
    const label = `${name === 'source' ? 'Source' : 'Target'} (${spec.position_mm.map((c) => fmt(c, 3)).join(', ')})`;
    group.append(svg('text', { x: x + 8, y: y + 16, 'font-size': 12, fill: color }, label));
    return group;
  }

  private map() {
    const result = this.store.currentResult;
    const grid = result?.search?.map;
    const root = this.frame('탐색 지도 · 두 반사면 배치 공간', '가로 a = Source→M1, 세로 c = M2→Target [mm, 로그 축] · 색 = 배치별 판정 · 번호 = 후보');
    if (!grid) {
      root.append(svg('text', { x: W / 2, y: H / 2, 'text-anchor': 'middle', fill: '#57606a' }, 'Design을 실행하면 탐색한 배치 공간이 표시됩니다'));
      return el('figure', { class: 'figure', 'data-view': 'map' }, root);
    }
    const n = grid.a_mm.length, m = grid.c_mm.length;
    const x0 = 64, x1 = W - 190, y0 = 52, y1 = H - 46;
    const la = (v: number) => Math.log(v);
    const [a0, aN, c0, cN] = [la(grid.a_mm[0]), la(grid.a_mm[n - 1]), la(grid.c_mm[0]), la(grid.c_mm[m - 1])];
    const X = (a: number) => x0 + ((la(a) - a0) / (aN - a0)) * (x1 - x0);
    const Y = (c: number) => y1 - ((la(c) - c0) / (cN - c0)) * (y1 - y0);
    const dx = (x1 - x0) / (n - 1), dy = (y1 - y0) / (m - 1);
    const cells = svg('g', { 'data-kind': 'map-cells' });
    grid.cells.forEach((cell, k) => {
      const i = Math.floor(k / m), j = k % m;
      const rect = svg('rect', { x: (X(grid.a_mm[i]) - dx / 2).toFixed(2), y: (Y(grid.c_mm[j]) - dy / 2).toFixed(2), width: (dx + 0.3).toFixed(2), height: (dy + 0.3).toFixed(2), fill: cellColor(cell, grid.slope_limit) });
      rect.append(svg('title', {}, `a ${fmt(grid.a_mm[i], 3)} mm, c ${fmt(grid.c_mm[j], 3)} mm · ${cell.status}${cell.reason ? ': ' + cell.reason : ''}${cell.slope !== null ? ` · 3w|κ| ${fmt(cell.slope, 3)}` : ''}`));
      cells.append(rect);
    });
    root.append(cells, svg('rect', { x: x0 - dx / 2, y: y0 - dy / 2, width: x1 - x0 + dx, height: y1 - y0 + dy, fill: 'none', stroke: '#8c959f' }));
    const ticks = svg('g', { 'font-size': 11, fill: '#57606a' });
    for (let e = Math.floor(Math.log10(grid.a_mm[0])); e <= Math.ceil(Math.log10(grid.a_mm[n - 1])); e++) for (const k of [1, 2, 5]) {
      const v = k * 10 ** e;
      if (v >= grid.a_mm[0] && v <= grid.a_mm[n - 1]) ticks.append(svg('text', { x: X(v), y: y1 + dy / 2 + 14, 'text-anchor': 'middle' }, String(+v.toPrecision(2))));
      if (v >= grid.c_mm[0] && v <= grid.c_mm[m - 1]) ticks.append(svg('text', { x: x0 - dx / 2 - 4, y: Y(v) + 4, 'text-anchor': 'end' }, String(+v.toPrecision(2))));
    }
    root.append(ticks, svg('text', { x: (x0 + x1) / 2, y: H - 10, 'text-anchor': 'middle', 'font-size': 12, fill: '#1b2733' }, 'a = |Source → M1| [mm]'));
    const ylab = svg('text', { x: 14, y: (y0 + y1) / 2, 'text-anchor': 'middle', 'font-size': 12, fill: '#1b2733', transform: `rotate(-90 14 ${(y0 + y1) / 2})` }, 'c = |M2 → Target| [mm]');
    root.append(ylab);
    for (const p of grid.near_match) {
      const dot = svg('circle', { cx: X(p.a_mm), cy: Y(p.c_mm), r: 2.6, fill: '#0969da', 'fill-opacity': 0.75 });
      dot.append(svg('title', {}, `Near-match η ${fmt(p.eta, 4)} · a ${fmt(p.a_mm, 3)}, c ${fmt(p.c_mm, 3)} mm`));
      root.append(dot);
    }
    for (const c of result!.candidates) {
      const a = c.parameters_mm.a, cc = c.parameters_mm.c;
      if (a === undefined || cc === undefined) continue;
      const selected = c.id === this.store.selectedCandidate?.id;
      root.append(svg('circle', { cx: X(a), cy: Y(cc), r: 8, fill: '#ffffff', stroke: selected ? '#b42318' : '#1b2733', 'stroke-width': selected ? 2.4 : 1.4,
        'data-kind': 'map-candidate', 'data-id': c.id, 'data-a-mm': a, 'data-c-mm': cc }));
      root.append(svg('text', { x: X(a), y: Y(cc) + 4, 'text-anchor': 'middle', 'font-size': 11, 'font-weight': 700, fill: '#1b2733' }, String(c.rank)));
    }
    const legend = svg('g', { 'font-size': 11, fill: '#1b2733' });
    MAP_LEGEND.forEach(([color, text], k) => {
      legend.append(svg('rect', { x: W - 178, y: y0 + k * 22, width: 14, height: 14, fill: color, stroke: '#8c959f', 'stroke-width': 0.5 }));
      legend.append(svg('text', { x: W - 158, y: y0 + k * 22 + 11 }, text));
    });
    const ky = y0 + MAP_LEGEND.length * 22 + 8;
    legend.append(svg('circle', { cx: W - 171, cy: ky + 7, r: 3, fill: '#0969da' }), svg('text', { x: W - 158, y: ky + 11 }, 'Near-match 가능 배치'));
    legend.append(svg('circle', { cx: W - 171, cy: ky + 29, r: 7, fill: '#fff', stroke: '#1b2733' }), svg('text', { x: W - 158, y: ky + 33 }, '표시된 후보(번호)'));
    root.append(legend);
    return el('figure', { class: 'figure', 'data-view': 'map' }, root);
  }

  private fold() {
    const selected = this.store.selectedCandidate;
    const root = this.frame('Fold · 광축 전개 Beam Envelope', '가로: 광경로 거리 [mm] · 세로: 1/e² 반경 [µm] · 실선 t, 점선 s');
    if (!selected) {
      root.append(svg('text', { x: W / 2, y: H / 2, 'text-anchor': 'middle', fill: '#57606a' }, 'Design 결과를 선택하면 Beam Envelope가 표시됩니다'));
      return el('figure', { class: 'figure', 'data-view': 'fold' }, root);
    }
    const samples = selected.scene.beam.samples;
    const total = selected.scene.path.total_length_mm;
    const rmax = Math.max(...samples.map((s) => Math.max(s.radius_t_um, s.radius_s_um))) * 1.15;
    const x0 = 64, x1 = W - 24, yc = H / 2 + 14, half = (H - 120) / 2;
    const X = (d: number) => x0 + (d / total) * (x1 - x0);
    const Y = (r: number) => yc - (r / rmax) * half;
    const step = niceStep(total);
    const ticks = svg('g', { 'font-size': 11, fill: '#8c959f' });
    for (let d = 0; d <= total + 1e-12; d += step) {
      root.append(svg('line', { x1: X(d), y1: yc - half, x2: X(d), y2: yc + half, stroke: '#eef1f4' }));
      ticks.append(svg('text', { x: X(d), y: yc + half + 14, 'text-anchor': 'middle' }, fmt(d, step < 1 ? 2 : 1)));
    }
    const rstep = niceStep(rmax, 4);
    for (let r = rstep; r <= rmax; r += rstep) for (const sign of [1, -1]) {
      root.append(svg('line', { x1: x0, y1: Y(sign * r), x2: x1, y2: Y(sign * r), stroke: '#eef1f4' }));
      ticks.append(svg('text', { x: x0 - 6, y: Y(sign * r) + 3, 'text-anchor': 'end' }, fmt(sign * r, rstep < 1 ? 1 : 0)));
    }
    root.append(ticks, svg('line', { x1: x0, y1: yc, x2: x1, y2: yc, stroke: '#1b2733', 'stroke-dasharray': '2 3' }));
    for (const [key, dash] of [['radius_t_um', ''], ['radius_s_um', '5 3']] as const) for (const sign of [1, -1]) {
      root.append(svg('polyline', { points: samples.map((s) => `${X(s.distance_mm).toFixed(2)},${Y(sign * s[key]).toFixed(2)}`).join(' '), fill: 'none', stroke: '#b42318', 'stroke-width': 1.4, 'stroke-dasharray': dash }));
    }
    let travelled = 0;
    selected.scene.path.segments.forEach((segment, j) => {
      travelled += segment.length_mm;
      const mirror = selected.scene.mirrors[j];
      if (!mirror) return;
      const roc = mirror.radius_of_curvature_ts_mm.map((r) => (r === null ? '∞' : fmt(r, 2))).join(' / ');
      root.append(svg('line', { x1: X(travelled), y1: yc - half, x2: X(travelled), y2: yc + half, stroke: '#1b2733', 'stroke-width': 1.2, 'data-kind': 'fold-mirror', 'data-id': mirror.id, 'data-distance-mm': travelled }));
      root.append(svg('text', { x: X(travelled) + 4, y: yc - half + 14 + 16 * j, 'font-size': 12, fill: '#1b2733' }, `${mirror.id} · R ${roc} mm`));
    });
    const first = samples[0], last = samples[samples.length - 1];
    root.append(svg('text', { x: x0, y: yc + half + 30, 'font-size': 12, fill: PORT_COLOR.source }, `Source w ${fmt(first.radius_t_um, 2)} / ${fmt(first.radius_s_um, 2)} µm`));
    root.append(svg('text', { x: x1, y: yc + half + 30, 'text-anchor': 'end', 'font-size': 12, fill: PORT_COLOR.target }, `Target 도착 w ${fmt(last.radius_t_um, 2)} / ${fmt(last.radius_s_um, 2)} µm`));
    return el('figure', { class: 'figure', 'data-view': 'fold' }, root);
  }
}

const MAP_LEGEND: [string, string][] = [
  ['#2da44e', 'Exact 해, Guard·제약 통과'],
  ['#fb8f44', 'Exact 해, 3w·|κ| 한계 근처 초과'],
  ['#fff1e5', 'Exact 해, 3w·|κ| 크게 초과'],
  ['#d8b9ff', '발산각 Guard 초과'],
  ['#c9d1d9', 'Port 뒤 공간·Envelope·Keep-out 제약'],
  ['#eaeef2', '입사각 한계·짧은 구간'],
  ['#f6f8fa', '실수 Exact-q 해 없음'],
];

function cellColor(cell: { status: string; reason: string; slope: number | null }, limit: number): string {
  if (cell.status === 'ok') return MAP_LEGEND[0][0];
  if (cell.status === 'constraint') return MAP_LEGEND[4][0];
  if (cell.status === 'geometry') return MAP_LEGEND[5][0];
  if (cell.status === 'power') return MAP_LEGEND[6][0];
  if (/divergence/.test(cell.reason)) return MAP_LEGEND[3][0];
  const t = Math.min(1, Math.max(0, ((cell.slope ?? 2 * limit) - limit) / limit));
  const mix = (a: number, b: number) => Math.round(a + (b - a) * t);
  return `rgb(${mix(0xfb, 0xff)},${mix(0x8f, 0xf1)},${mix(0x44, 0xe5)})`;
}

function inView(project: (p: Vec3) => P2, axis: number) {
  const e: Vec3 = [0, 0, 0];
  e[axis] = 1;
  const p = project(e);
  return p[0] !== 0 || p[1] !== 0;
}
