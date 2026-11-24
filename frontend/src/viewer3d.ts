import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { TransformControls } from 'three/examples/jsm/controls/TransformControls.js';
import { CSS2DObject, CSS2DRenderer } from 'three/examples/jsm/renderers/CSS2DRenderer.js';
import { clone, type AppState, type Store } from './state';
import type { BeamSample, Candidate, MediumBlock, PortName, PortScene, Segment, Vec3 } from './types';
import { cross, el, fmt, unit } from './util';

const COLOR = { lens: 0x1a7f37, source: 0x1f6feb, target: 0xd9480f, path: 0xb42318, beam: 0xe5484d, mirror: 0x8b95a1, faint: 0x9aa5b1, glass: 0x0a7ea4 };
const v3 = (p: Vec3) => new THREE.Vector3(p[0], p[1], p[2]);

/** Choose a display magnification so beam radii are visible next to mm-scale geometry. */
export function niceScale(extentMm: number, maxRadiusUm: number): number {
  if (!(extentMm > 0) || !(maxRadiusUm > 0)) return 1;
  const raw = (0.025 * extentMm) / (maxRadiusUm * 1e-3);
  if (raw <= 1) return 1;
  const exp = Math.floor(Math.log10(raw));
  const base = raw / 10 ** exp;
  const step = base >= 5 ? 5 : base >= 2 ? 2 : 1;
  return step * 10 ** exp;
}

export function sceneExtent(state: AppState, candidates: Candidate[]): { center: Vec3; size: number; maxRadiusUm: number } {
  const points: Vec3[] = [state.doc.ports.source.position_mm, state.doc.ports.target.position_mm];
  let maxRadiusUm = Math.max(...state.doc.ports.source.mfd_um, ...state.doc.ports.target.mfd_um) / 2;
  for (const box of constraintBoxes(state)) points.push(box.min, box.max);
  for (const c of candidates) {
    points.push(...c.scene.path.points_mm);
    for (const s of c.scene.beam.samples) maxRadiusUm = Math.max(maxRadiusUm, s.radius_t_um, s.radius_s_um);
  }
  const lo = [0, 1, 2].map((i) => Math.min(...points.map((p) => p[i])));
  const hi = [0, 1, 2].map((i) => Math.max(...points.map((p) => p[i])));
  const size = Math.max(Math.hypot(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]), 0.5);
  return { center: [0, 1, 2].map((i) => (lo[i] + hi[i]) / 2) as Vec3, size, maxRadiusUm };
}

export interface DrawBox { kind: 'envelope' | 'keepout'; label: string; min: Vec3; max: Vec3 }

/** Envelope and keep-out boxes from the Design Document constraints (mm). */
export function constraintBoxes(state: AppState): DrawBox[] {
  const c = state.doc?.constraints;
  if (!c) return [];
  const out: DrawBox[] = [];
  if (c.envelope_mm) out.push({ kind: 'envelope', label: 'Envelope', min: c.envelope_mm.min, max: c.envelope_mm.max });
  (c.keepouts_mm ?? []).forEach((k, i) => out.push({ kind: 'keepout', label: k.label || `Keep-out ${i + 1}`, min: k.min, max: k.max }));
  return out;
}

export class Viewer3D {
  readonly ok: boolean;
  private renderer?: THREE.WebGLRenderer;
  private labels?: CSS2DRenderer;
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(35, 1, 0.001, 1e5);
  private orbit?: OrbitControls;
  private gizmo?: TransformControls;
  private world = new THREE.Group();
  private ports: Partial<Record<PortName, THREE.Group>> = {};
  private dragging = false;
  private lastFitKey = '';
  beamScale = 1;
  scaleMode: 'auto' | 'true' = 'auto';
  private badge: HTMLElement;

  constructor(private root: HTMLElement, private store: Store) {
    this.badge = el('div', { class: 'viewer-badge' });
    try {
      const probe = document.createElement('canvas');
      if (!(probe.getContext('webgl2') || probe.getContext('webgl'))) throw new Error('WebGL unavailable');
      this.renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
      this.ok = true;
    } catch {
      this.ok = false;
      root.append(el('div', { class: 'fallback' }, '이 브라우저에서 WebGL을 쓸 수 없어 3D 화면을 끕니다. 2D 도면은 그대로 사용할 수 있습니다.'));
      return;
    }
    const renderer = this.renderer;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0xffffff, 1);
    root.append(renderer.domElement);
    this.labels = new CSS2DRenderer();
    this.labels.domElement.className = 'labels';
    root.append(this.labels.domElement, this.badge);

    this.camera.up.set(0, 0, 1);
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0xd0d7de, 2.2));
    const sun = new THREE.DirectionalLight(0xffffff, 1.6);
    sun.position.set(3, -4, 6);
    this.scene.add(sun, this.world);

    this.orbit = new OrbitControls(this.camera, this.labels.domElement);
    this.orbit.enableDamping = false;
    this.orbit.addEventListener('change', () => this.draw());
    this.gizmo = new TransformControls(this.camera, this.labels.domElement);
    this.gizmo.setMode('translate');
    this.gizmo.addEventListener('dragging-changed', (event) => {
      this.dragging = Boolean(event.value);
      this.orbit!.enabled = !this.dragging;
      if (!this.dragging) this.commitDrag();
    });
    this.gizmo.addEventListener('objectChange', () => this.commitDrag());
    this.gizmo.addEventListener('change', () => this.draw());
    this.scene.add(this.gizmo.getHelper());

    this.labels.domElement.addEventListener('dblclick', (event) => this.pick(event));
    new ResizeObserver(() => this.resize()).observe(root);
    store.subscribe((_, changed) => {
      if (changed.has('doc') || changed.has('preview') || changed.has('result') || changed.has('selected') || changed.has('activePort')) this.update();
    });
    (window as unknown as { __paeViewer: Viewer3D }).__paeViewer = this;
  }

  setScaleMode(mode: 'auto' | 'true') {
    this.scaleMode = mode;
    this.update();
  }

  fit() {
    this.lastFitKey = '';
    this.update();
  }

  private resize() {
    if (!this.renderer || !this.labels) return;
    const { clientWidth: w, clientHeight: h } = this.root;
    if (!w || !h) return;
    this.renderer.setSize(w, h);
    this.labels.setSize(w, h);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.draw();
  }

  private draw() {
    if (!this.renderer || !this.labels) return;
    this.renderer.render(this.scene, this.camera);
    this.labels.render(this.scene, this.camera);
  }

  private commitDrag() {
    const name = this.store.state.activePort;
    const object = name ? this.ports[name] : undefined;
    if (!name || !object) return;
    const p = object.position;
    const round = (x: number) => Math.round(x * 1e4) / 1e4; // 0.1 µm grid keeps inputs readable
    const doc = clone(this.store.state.doc);
    doc.ports[name].position_mm = [round(p.x), round(p.y), round(p.z)];
    doc.ports[name].evidence.placement = { provenance: 'assumed', source: 'User placement (3D drag)' };
    this.store.set({ doc });
  }

  private pick(event: MouseEvent) {
    const rect = this.labels!.domElement.getBoundingClientRect();
    const ray = new THREE.Raycaster();
    ray.setFromCamera(new THREE.Vector2(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1), this.camera);
    for (const name of ['source', 'target'] as PortName[]) {
      const group = this.ports[name];
      if (group && ray.intersectObject(group, true).length) return this.store.set({ activePort: name });
    }
  }

  update() {
    if (!this.ok) return;
    const state = this.store.state;
    const result = this.store.currentResult;
    const candidates = this.store.drawnCandidates;
    const extent = sceneExtent(state, candidates);
    this.beamScale = this.scaleMode === 'true' ? 1 : niceScale(extent.size, extent.maxRadiusUm);
    this.badge.textContent = this.beamScale === 1 ? 'Beam·Mode 실제 크기' : `Beam·Mode 반경 ×${this.beamScale} 확대 표시 (Geometry는 실제 크기)`;

    const activeName = state.activePort;
    if (!this.dragging) {
      this.gizmo!.detach();
      for (const child of [...this.world.children]) this.dispose(child);
      this.world.clear();
      this.ports = {};
      this.world.add(this.helpers(extent.size, extent.center));
      const scenes = state.preview?.ports?.ports ?? result?.ports?.ports ?? [];
      for (const name of ['source', 'target'] as PortName[]) {
        const group = this.portGlyph(name, scenes.find((p) => p.name === name) ?? null, extent.size);
        this.ports[name] = group;
        this.world.add(group);
      }
      for (const box of constraintBoxes(state)) this.world.add(this.box(box));
      if (state.doc.medium_block) this.world.add(this.glass(state.doc.medium_block, extent));
      const selected = this.store.selectedCandidate;
      for (const c of candidates) this.world.add(this.candidate(c, c.id === selected?.id));
      if (activeName && this.ports[activeName]) this.gizmo!.attach(this.ports[activeName]!);
      this.gizmo!.size = 0.8;
    }
    const fitKey = `${state.doc.scenario ?? state.doc.title}|${result?.document_sha256 ?? ''}`;
    if (fitKey !== this.lastFitKey) {
      this.lastFitKey = fitKey;
      this.frame(extent.center, extent.size);
    }
    this.draw();
  }

  private frame(center: Vec3, size: number) {
    const target = v3(center);
    const distance = (size / 2 / Math.sin(THREE.MathUtils.degToRad(this.camera.fov / 2))) * 1.15;
    const view = new THREE.Vector3(0.55, -1.0, 0.55).normalize();
    this.camera.position.copy(target.clone().addScaledVector(view, distance));
    this.camera.near = distance / 1000;
    this.camera.far = distance * 100;
    this.camera.updateProjectionMatrix();
    this.orbit!.target.copy(target);
    this.orbit!.update();
  }

  private helpers(size: number, center: Vec3) {
    const group = new THREE.Group();
    const step = 10 ** Math.floor(Math.log10(size / 4));
    const cells = Math.max(4, Math.ceil(size / step) + 4);
    const grid = new THREE.GridHelper(cells * step, cells, 0xd0d7de, 0xeef1f4);
    grid.rotation.x = Math.PI / 2;
    grid.position.set(Math.round(center[0] / step) * step, Math.round(center[1] / step) * step, 0);
    group.add(grid);
    const axisLength = size * 0.12;
    for (const [label, dir, color] of [['X', [1, 0, 0], 0xcf222e], ['Y', [0, 1, 0], 0x1a7f37], ['Z', [0, 0, 1], 0x0969da]] as const) {
      group.add(new THREE.ArrowHelper(v3(dir as unknown as Vec3), new THREE.Vector3(), axisLength, color, axisLength * 0.2, axisLength * 0.1));
      group.add(this.label(label, v3((dir as unknown as number[]).map((c) => c * axisLength * 1.15) as Vec3), 'axis-label'));
    }
    const ruler = this.label(`격자 ${fmt(step, step < 1 ? 3 : 1)} mm`, v3([grid.position.x - (cells * step) / 2, grid.position.y - (cells * step) / 2, 0]), 'axis-label');
    group.add(ruler);
    return group;
  }

  private box(box: DrawBox) {
    const group = new THREE.Group();
    const size = v3(box.max).sub(v3(box.min));
    const center = v3(box.min).add(v3(box.max)).multiplyScalar(0.5);
    const geometry = new THREE.BoxGeometry(size.x, size.y, size.z);
    const keepout = box.kind === 'keepout';
    if (keepout) {
      const mesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({ color: 0xd1242f, transparent: true, opacity: 0.12, depthWrite: false }));
      mesh.position.copy(center);
      group.add(mesh);
    }
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry),
      keepout ? new THREE.LineBasicMaterial({ color: 0xd1242f }) : new THREE.LineDashedMaterial({ color: 0x57606a, dashSize: size.length() / 60, gapSize: size.length() / 90 }));
    edges.position.copy(center);
    if (!keepout) edges.computeLineDistances();
    group.add(edges, this.label(box.label, v3(box.max), keepout ? 'scene-label keepout-label' : 'axis-label'));
    return group;
  }

  /** Glass block drawn as a translucent slab around the scene; a block without bottom is drawn one scene size deep. */
  private glass(block: MediumBlock, extent: { center: Vec3; size: number }) {
    const group = new THREE.Group();
    const n = v3(block.surface_normal).normalize();
    const thickness = block.thickness_mm ?? extent.size;
    const width = extent.size * 1.3;
    const geometry = new THREE.BoxGeometry(width, width, thickness);
    const orient = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), n);
    const surface = v3(block.surface_point_mm);
    const center = v3(extent.center);
    const onSurface = center.clone().addScaledVector(n, -center.clone().sub(surface).dot(n));
    const position = onSurface.addScaledVector(n, -thickness / 2);
    const mesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({ color: COLOR.glass, transparent: true, opacity: 0.1, depthWrite: false, side: THREE.DoubleSide }));
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry), new THREE.LineBasicMaterial({ color: COLOR.glass, transparent: true, opacity: 0.6 }));
    for (const object of [mesh, edges]) { object.quaternion.copy(orient); object.position.copy(position); }
    mesh.userData.kind = 'glass';
    const corner = position.clone().addScaledVector(n, thickness / 2);
    group.add(mesh, edges, this.label(`${block.label || 'Glass'} · n ${block.index}${block.thickness_mm ? ` · t ${block.thickness_mm} mm` : ''}`, corner, 'scene-label glass-label'));
    return group;
  }

  private label(text: string, at: THREE.Vector3, className = 'scene-label') {
    const object = new CSS2DObject(el('div', { class: className }, text));
    object.position.copy(at);
    return object;
  }

  private portGlyph(name: PortName, scene: PortScene | null, size: number) {
    const spec = this.store.state.doc.ports[name];
    const color = COLOR[name];
    const group = new THREE.Group();
    group.position.copy(v3(spec.position_mm));
    group.userData = { port: name };
    let d: Vec3, s: Vec3, t: Vec3;
    try {
      d = unit(spec.direction);
      s = unit(spec.sagittal_axis);
      t = scene ? scene.t_axis : unit(cross(s, d));
    } catch {
      return group;
    }
    if (![...d, ...s, ...t].every(Number.isFinite)) return group;
    const half = size * 0.04;
    const basis = new THREE.Matrix4().makeBasis(v3(t), v3(s), v3(d));
    const plane = new THREE.Mesh(new THREE.PlaneGeometry(2 * half, 2 * half),
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.16, side: THREE.DoubleSide, depthWrite: false }));
    plane.setRotationFromMatrix(basis);
    group.add(plane);
    const edge = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(2 * half, 2 * half)), new THREE.LineBasicMaterial({ color }));
    edge.setRotationFromMatrix(basis);
    group.add(edge);
    const arrowLength = size * 0.12;
    group.add(new THREE.ArrowHelper(v3(d), name === 'target' ? v3(d).multiplyScalar(-arrowLength) : new THREE.Vector3(), arrowLength, color, arrowLength * 0.22, arrowLength * 0.12));
    const radii = scene ? scene.mode.map((m) => m.radius_um) : spec.mfd_um.map((m) => m / 2);
    const k = this.beamScale * 1e-3;
    const ring: THREE.Vector3[] = [];
    for (let i = 0; i <= 64; i++) {
      const a = (i / 64) * Math.PI * 2;
      ring.push(v3(t).multiplyScalar(Math.cos(a) * radii[0] * k).add(v3(s).multiplyScalar(Math.sin(a) * radii[1] * k)));
    }
    group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(ring), new THREE.LineBasicMaterial({ color })));
    const tLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints([v3(t).multiplyScalar(-half), v3(t).multiplyScalar(half)]),
      new THREE.LineDashedMaterial({ color, dashSize: half / 8, gapSize: half / 10 }));
    tLine.computeLineDistances();
    group.add(tLine);
    const guard = scene?.divergence_guard.status === 'Fail' ? ' · Guard Fail' : '';
    group.add(this.label(`${name === 'source' ? 'Source' : 'Target'}${guard}`, v3(s).multiplyScalar(half * 1.3), `scene-label port-${name}`));
    return group;
  }

  private candidate(c: Candidate, selected: boolean) {
    const group = new THREE.Group();
    const opacity = selected ? 1 : 0.25;
    const path = new THREE.Line(new THREE.BufferGeometry().setFromPoints(c.scene.path.points_mm.map(v3)),
      new THREE.LineBasicMaterial({ color: selected ? COLOR.path : COLOR.faint, transparent: !selected, opacity }));
    group.add(path);
    for (const mirror of c.scene.mirrors) {
      const grid = mirror.surface_grid_corrected_mm ?? mirror.surface_grid_mm;
      const n = grid.length;
      const positions: number[] = [];
      for (const row of grid) for (const p of row) positions.push(...p);
      const index: number[] = [];
      for (let i = 0; i < n - 1; i++) for (let j = 0; j < n - 1; j++) {
        const a = i * n + j, b = a + 1, cc = a + n, dd = cc + 1;
        index.push(a, cc, b, b, cc, dd);
      }
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geometry.setIndex(index);
      geometry.computeVertexNormals();
      group.add(new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: selected ? COLOR.mirror : 0xc9d1d9, metalness: 0.35, roughness: 0.35, side: THREE.DoubleSide, transparent: !selected, opacity: selected ? 1 : 0.35 })));
      const border = [...grid[0], ...grid.map((r) => r[n - 1]), ...[...grid[n - 1]].reverse(), ...grid.map((r) => r[0]).reverse()];
      group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(border.map(v3)), new THREE.LineBasicMaterial({ color: 0x57606a, transparent: !selected, opacity })));
      if (selected) {
        const roc = mirror.radius_of_curvature_ts_mm.map((r) => (r === null ? '∞' : fmt(r, 2))).join(' / ');
        group.add(this.label(`${mirror.id} · R ${roc} mm · ${fmt(mirror.incidence_deg, 1)}°${mirror.tir_possible === undefined ? '' : mirror.tir_possible ? ' · TIR 가능' : ' · 반사 Coating 필요'}`, v3(mirror.vertex_mm).addScaledVector(v3(mirror.normal), mirror.half_aperture_ts_mm[0] * 1.6)));
      }
    }
    for (const lens of c.scene.lenses ?? []) {
      const material = new THREE.LineBasicMaterial({ color: COLOR.lens, transparent: !selected, opacity });
      for (const line of lens.outline_mm) group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(line.map(v3)), material));
      if (selected) group.add(this.label(`${lens.id} · f ${fmt(lens.focal_length_um, 0)} µm · Ø ${fmt(2 * lens.clear_radius_um, 0)} µm`,
        v3(lens.curved_vertex_mm).add(new THREE.Vector3(...lens.axis).multiplyScalar(lens.clear_radius_um * 2e-3)), 'scene-label lens-label'));
    }
    if (selected) group.add(this.beamTube(c));
    return group;
  }

  private beamTube(c: Candidate) {
    const k = this.beamScale * 1e-3;
    const sides = 24;
    const positions: number[] = [];
    const index: number[] = [];
    c.scene.path.segments.forEach((segment, j) => {
      const samples = c.scene.beam.samples.filter((s) => s.segment === j);
      const base = positions.length / 3;
      for (const sample of samples) for (let i = 0; i < sides; i++) {
        const a = (i / sides) * Math.PI * 2;
        const [u, v, ru, rv] = beamAxes(segment, sample);
        const p = v3(sample.point_mm).addScaledVector(u, Math.cos(a) * ru * k).addScaledVector(v, Math.sin(a) * rv * k);
        positions.push(p.x, p.y, p.z);
      }
      for (let r = 0; r < samples.length - 1; r++) for (let i = 0; i < sides; i++) {
        const a = base + r * sides + i, b = base + r * sides + ((i + 1) % sides), cc = a + sides, dd = b + sides;
        index.push(a, cc, b, b, cc, dd);
      }
    });
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setIndex(index);
    geometry.computeVertexNormals();
    return new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: COLOR.beam, transparent: true, opacity: 0.32, side: THREE.DoubleSide, depthWrite: false }));
  }

  private dispose(object: THREE.Object3D) {
    object.traverse((node) => {
      const mesh = node as THREE.Mesh;
      mesh.geometry?.dispose?.();
      const material = mesh.material as THREE.Material | THREE.Material[] | undefined;
      if (Array.isArray(material)) material.forEach((m) => m.dispose());
      else material?.dispose?.();
      if (node instanceof CSS2DObject) node.element.remove();
    });
  }
}

/** Ellipse axes of one beam sample: the true semi-axes for q-tensor beams, else the segment t/s axes. */
function beamAxes(segment: Segment, sample: BeamSample): [THREE.Vector3, THREE.Vector3, number, number] {
  const t = v3(segment.t_axis), s = v3(segment.s_axis);
  if (!sample.ellipse) return [t, s, sample.radius_t_um, sample.radius_s_um];
  const { major_um, minor_um, angle_rad } = sample.ellipse;
  const u = t.clone().multiplyScalar(Math.cos(angle_rad)).addScaledVector(s, Math.sin(angle_rad));
  const v = t.clone().multiplyScalar(-Math.sin(angle_rad)).addScaledVector(s, Math.cos(angle_rad));
  return [u, v, major_um, minor_um];
}
