import type { Vec3 } from './types';

export const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
export const norm = (a: Vec3) => Math.sqrt(dot(a, a));
export const cross = (a: Vec3, b: Vec3): Vec3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
export const scale = (a: Vec3, k: number): Vec3 => [a[0] * k, a[1] * k, a[2] * k];
export const add = (a: Vec3, b: Vec3): Vec3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
export const sub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
export const unit = (a: Vec3): Vec3 => scale(a, 1 / norm(a));

export function fmt(value: number | null | undefined, digits = 3): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—';
  return value.toFixed(digits);
}

export function el<K extends keyof HTMLElementTagNameMap>(tag: K, attrs: Record<string, string> = {}, ...children: (Node | string)[]) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  node.append(...children);
  return node;
}

export function download(name: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = el('a', { href: url, download: name });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const AXES: Record<string, Vec3> = {
  '+X': [1, 0, 0], '-X': [-1, 0, 0], '+Y': [0, 1, 0], '-Y': [0, -1, 0], '+Z': [0, 0, 1], '-Z': [0, 0, -1],
};

export function axisName(v: Vec3): string | null {
  for (const [name, axis] of Object.entries(AXES)) if (axis.every((c, i) => c === v[i])) return name;
  return null;
}

export const PROVENANCE_LABEL: Record<string, string> = {
  measured: '측정·문헌', supplied: '제공', independently_validated: '독립 검증', simulated: '시뮬레이션', assumed: '가정', synthetic: 'Synthetic',
};

export const STATUS_LABEL: Record<string, string> = {
  input_contract: '입력 계약', geometry: 'Geometry', model_domain: 'Model Domain', gaussian_mode_matching: 'Mode Matching',
  package_feasibility: 'Package', physical_losses: '물리 손실', fabrication: '제조', actual_applicability: '실제 적용성',
};

const REASONS: [RegExp, string][] = [
  [/unintended reflector interception/, '경로가 다른 반사면에 걸림'],
  [/incidence exceeds 70/, '입사각 70° 초과'],
  [/footprint\/curvature exceeds 0\.15/, '3w·|κ| > 0.15 (반사면 곡률 대비 Beam이 큼)'],
  [/divergence exceeds 0\.1 rad/, '발산각 0.1 rad 초과 (Paraxial Guard)'],
  [/no real exact-q/i, '실수 Exact-q 곡률 해 없음'],
  [/noncoplanar/, '두 Port가 한 평면에 있지 않음 (비동일평면)'],
  [/No valid candidate in bounded exact-q family/, '고정 Exact-q 탐색 범위에 유효 후보 없음 (물리적 불가능의 증명 아님)'],
  [/Valid conceptual candidates generated|Valid exact-q candidates generated/, 'Exact-q 후보 생성 (두 축 모두 q 일치)'],
  [/Near-match candidates generated/, 'Guard 안에 Exact-q 해가 없어 Near-match 후보(η < 1)를 생성'],
  [/No valid two-reflector candidate/, '두 반사면 Family 안에서 Guard·제약을 모두 만족하는 배치 없음 (물리적 불가능의 증명 아님)'],
  [/Source body half-space/, 'Source 뒤 공간(Port 본체) 침범'],
  [/Target body half-space/, 'Target 뒤 공간(Port 본체) 침범'],
  [/outside the package envelope/, 'Package Envelope 밖'],
  [/keep-out/, 'Keep-out 침범'],
  [/radius of curvature below/, '최소 곡률반경 미달'],
  [/incidence exceeds limit/, '입사각 한계 초과'],
  [/zero\/short middle segment/, '가운데 구간이 너무 짧음'],
  [/invalid paraxial transformation/, 'Paraxial 변환 불가'],
  [/corrected surface enters the Source body/, '보정 곡면이 Source 본체 쪽으로 들어감'],
  [/corrected surface enters the Target body/, '보정 곡면이 Target 본체 쪽으로 들어감'],
  [/corrected surface crosses the block surface/, '보정 곡면이 Glass 상면을 넘음'],
  [/corrected surface/, '보정 곡면이 공간 제약을 넘음'],
  [/beam clips another reflector/, 'Beam이 다른 반사면에 걸림'],
  [/crosses the block surface/, '반사면이 Glass 상면을 넘음'],
  [/leaves the block bottom/, '반사면이 Glass 하면을 넘음'],
  [/enters the block/, '반사면이 Glass 안으로 들어감'],
];

export function reasonLabel(reason: string | null | undefined): string {
  if (!reason) return '';
  for (const [pattern, label] of REASONS) if (pattern.test(reason)) return label;
  return reason;
}

/** What the user can do next, per failure reason; ties each limit to the roadmap phase. */
export function nextStep(reason: string | null | undefined): string | null {
  if (!reason) return null;
  if (/divergence/.test(reason)) return 'Mode가 작아 공기 중 Paraxial 범위를 벗어납니다. Glass 매질 내부 전파(P3)나 Lens Family(P4)가 필요합니다. Port별 최소 MFD는 왼쪽 패널에 표시됩니다.';
  if (/noncoplanar/.test(reason)) return '평면 밖으로 꺾이는 경로는 3D q-tensor 모델(P3)에서 다룹니다. 지금은 두 Port를 한 평면에 두면 계산할 수 있습니다.';
  if (/bounded exact-q family/.test(reason)) return '현재 엔진은 거리 비율 5개의 고정 배치만 시도합니다. 연속 탐색(P2)에서 S2a·S2b 후보를 찾는 것이 다음 단계입니다. 아래 거절 사유 분포를 참고하세요.';
  return null;
}
