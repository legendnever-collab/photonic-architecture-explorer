// Mirrors docs/DESIGN_DOCUMENT.md. Lengths in mm, beam radii in µm.

export type Vec3 = [number, number, number];
export type Provenance = 'measured' | 'supplied' | 'independently_validated' | 'simulated' | 'assumed' | 'synthetic';

export interface Evidence { provenance: Provenance; source: string }

export interface PortSpec {
  label: string;
  preset: string | null;
  position_mm: Vec3;
  direction: Vec3;
  sagittal_axis: Vec3;
  mfd_um: [number, number];
  wavefront_curvature_per_m: [number, number];
  evidence: { placement?: Evidence; mode?: Evidence; phase?: Evidence };
}

export type PortName = 'source' | 'target';

export interface DesignDocument {
  schema: 'pae.design/1';
  title: string;
  scenario?: string | null;
  description?: string;
  wavelength_nm: number;
  ambient_index: number;
  ports: Record<PortName, PortSpec>;
}

export interface Preset {
  id: string;
  label: string;
  process: string;
  material: string;
  wavelength_nm: number;
  mfd_lateral_um: number;
  mfd_vertical_um: number;
  mode_provenance: Provenance;
  source: string;
  url: string | null;
  axis_note: string;
  phase_note: string;
}

export interface ScenarioEntry {
  id: string;
  title: string;
  file: string | null;
  decision: string;
  expect: { status: string; reason_contains?: string; target?: { status: string; phase: string } };
}

export interface ModeAxis {
  axis: 't' | 's';
  radius_um: number;
  waist_radius_um: number;
  waist_distance_mm: number;
  rayleigh_range_mm: number;
  divergence_rad: number;
  curvature_per_m: number;
}

export interface PortScene {
  name: PortName;
  position_mm: Vec3;
  direction: Vec3;
  sagittal_axis: Vec3;
  t_axis: Vec3;
  mode: ModeAxis[];
  divergence_guard: { status: 'Pass' | 'Fail'; max_divergence_rad: number; limit_rad: number; min_waist_mfd_um: number };
}

export interface MirrorScene {
  id: string;
  vertex_mm: Vec3;
  normal: Vec3;
  t_axis: Vec3;
  s_axis: Vec3;
  curvature_ts_per_m: [number, number];
  radius_of_curvature_ts_mm: [number | null, number | null];
  half_aperture_ts_mm: [number, number];
  incidence_deg: number;
  beam_footprint_radius_ts_um: [number, number];
  surface_grid_mm: Vec3[][];
}

export interface Segment { start_mm: Vec3; end_mm: Vec3; length_mm: number; direction: Vec3; t_axis: Vec3; s_axis: Vec3 }
export interface BeamSample { segment: number; distance_mm: number; point_mm: Vec3; radius_t_um: number; radius_s_um: number }

export interface CandidateScene {
  mirrors: MirrorScene[];
  path: { points_mm: Vec3[]; segments: Segment[]; total_length_mm: number };
  beam: { definition: string; samples: BeamSample[] };
}

export interface Candidate {
  id: string;
  rank: number;
  role: string | null;
  metrics: {
    total_path_mm: number;
    normalized_mode_overlap: number | null;
    mode_mismatch_db: number | null;
    max_projected_beam_radius_um: number;
    max_3w_footprint_curvature: number;
    footprint_curvature_limit: number;
    incidence_deg: number[];
    radius_of_curvature_ts_mm: [number | null, number | null][];
  };
  status: Record<string, string>;
  scene: CandidateScene;
}

export interface Issue { path: string; message: string }

export interface Result {
  schema: 'pae.result/1';
  status: 'Computed' | 'Fail' | 'Uncomputed' | 'Invalid' | 'Preview';
  reason?: string | null;
  issues?: Issue[];
  document_sha256: string | null;
  engine_input_sha256?: string;
  selected_candidate_id?: string | null;
  ports: { frame_id: string; ports: PortScene[] } | null;
  candidates: Candidate[];
  search?: { status?: string; reason?: string; accepted_count?: number; geometry_count?: number; rejection_counts?: Record<string, number> };
  limitations?: string[];
  uncomputed?: string[];
}
