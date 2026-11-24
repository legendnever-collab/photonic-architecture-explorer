import type { DesignDocument, MediumBlock, PortName, Vec3 } from './types';

const sub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

/** Fused silica (Malitson 1965 Sellmeier), used only as the default glass. */
export function silicaIndex(wavelengthNm: number): number {
  const l2 = (wavelengthNm / 1000) ** 2;
  const b = [0.6961663, 0.4079426, 0.8974794], c = [0.0684043, 0.1162414, 9.896161];
  return +Math.sqrt(1 + b.reduce((s, bi, i) => s + (bi * l2) / (l2 - c[i] * c[i]), 0)).toFixed(4);
}

/** Depth below the top surface: > 0 inside the block. */
export function depthMm(block: MediumBlock, p: Vec3): number {
  return -dot(sub(p, block.surface_point_mm), block.surface_normal);
}

/** A Port's medium follows its position; a Port exactly on the surface keeps its declared side. */
export function syncMedia(doc: DesignDocument): DesignDocument {
  const block = doc.medium_block;
  let changed = false;
  const ports = { ...doc.ports };
  for (const name of ['source', 'target'] as PortName[]) {
    const port = ports[name];
    let medium = port.medium;
    if (!block) medium = undefined;
    else {
      const d = depthMm(block, port.position_mm);
      if (Math.abs(d) > 1e-9) medium = d > 0 && (block.thickness_mm == null || d <= block.thickness_mm) ? 'block' : 'ambient';
      else medium = medium ?? 'ambient';
    }
    if (medium !== port.medium) {
      changed = true;
      const next = { ...port };
      if (medium === undefined) delete next.medium; else next.medium = medium;
      ports[name] = next;
    }
  }
  return changed ? { ...doc, ports } : doc;
}
