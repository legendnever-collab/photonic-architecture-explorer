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
  medium?: Medium;
}

export type Medium = 'ambient' | 'block' | 'lens';

/** One glass block bounded by a planar top surface (and an optional parallel bottom). */
export interface MediumBlock {
  label?: string;
  index: number;
  surface_point_mm: Vec3;
  surface_normal: Vec3;   // points out of the block, into the ambient medium
  thickness_mm?: number | null;
  index_source?: Evidence;
}

export type PortName = 'source' | 'target';

export interface BoxMm { label?: string; min: Vec3; max: Vec3 }

export interface Constraints {
  port_body_halfspace?: boolean;
  envelope_mm?: BoxMm | null;
  keepouts_mm?: BoxMm[];
  clearance_um?: number;
  max_incidence_deg?: number;
  min_radius_of_curvature_mm?: number | null;
  source?: string;
}

export interface DesignDocument {
  schema: 'pae.design/1';
  title: string;
  scenario?: string | null;
  description?: string;
  wavelength_nm: number;
  ambient_index: number;
  ports: Record<PortName, PortSpec>;
  constraints?: Constraints;
  medium_block?: MediumBlock | null;
  families?: { lens_two_reflector?: 'auto' | 'compare' | 'off' };
  tolerances?: Partial<Record<ToleranceKey, number>>;
}

export type ToleranceKey = 'mirror_translation_um' | 'mirror_rotation_mrad' | 'lens_translation_um' | 'lens_axial_um'
  | 'lens_rotation_mrad' | 'bond_translation_um' | 'bond_rotation_mrad';
export interface AlignmentStats { median_db: number; p90_db: number; p99_db: number; yield_1db: number; yield_0p5db: number }
export interface AlignmentOption extends AlignmentStats {
  body: string; kind: string; dofs: 'translation' | 'rotation'; max_travel: number[]; travel_unit: string; practical: boolean;
}
export interface AlignmentStudy {
  status?: string; reason?: string; model: string; samples: number; distribution: string;
  tolerances: Record<ToleranceKey, number>; passive: AlignmentStats; active: AlignmentOption[];
  best_compensator: AlignmentOption | null; active_range: { translation_um: number; rotation_mrad: number };
  single: { body: string; dof: string; tolerance: number; unit: string; loss_db: number }[];
}

export interface FamilyRow {
  key: string; label: string; elements: number; status: string; count: number; reason: string | null;
  best_eta: number | null; best_reflector_pose_db: number | null; lens_decenter_1db_um: number | null;
  selected: boolean; why: string | null; mode?: string; passive_yield_1db?: number | null; active_p90_db?: number | null;
}
export interface LensPose {
  grid: number; reflectors_worst_loss_db: number; steps: { decenter_um: number; axial_um: number; tilt_mrad: number };
  lenses: { id: string; decenter_loss_db: number; axial_loss_db: number; tilt_loss_db: number;
    decenter_1db_um: number | null; axial_1db_um: number | null; tilt_1db_mrad: number | null }[];
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
  surface_grid_corrected_mm?: Vec3[][];  // P4: quadric + coma-correcting sag terms
  max_sag_change_um?: number;
  tir_possible?: boolean;
}

export interface Segment { start_mm: Vec3; end_mm: Vec3; length_mm: number; direction: Vec3; t_axis: Vec3; s_axis: Vec3; medium?: Medium }
/** General astigmatic beams (q-tensor): true 1/e² semi-axes; angle of the major axis from the segment t axis. */
export interface BeamEllipse { major_um: number; minor_um: number; angle_rad: number }
export interface BeamSample { segment: number; distance_mm: number; point_mm: Vec3; radius_t_um: number; radius_s_um: number; medium?: Medium; ellipse?: BeamEllipse }

/** P4 Lens Family: a rotationally symmetric two-asphere micro-lens (outline polylines in mm). */
export interface LensScene {
  id: string; side: PortName; flat_vertex_mm: Vec3; curved_vertex_mm: Vec3; axis: Vec3; focal_length_um: number;
  thickness_um: number; clear_radius_um: number; port_distance_um: number; relative_index: number; outline_mm: Vec3[][];
  material?: string; material_source?: string; uncoated_transmission?: number | null;
}
export interface LensCheck {
  max_direction_rad: number; max_sine_condition_error_m: number; rays_alive: boolean; checked_to_angle_rad: number;
  fitted_to_angle_rad: number; clear_radius_m: number; passes_to_sine?: number;
}

export interface CandidateScene {
  lenses?: LensScene[];
  mirrors: MirrorScene[];
  path: { points_mm: Vec3[]; segments: Segment[]; total_length_mm: number; surface_point_mm?: Vec3 };
  beam: { definition: string; samples: BeamSample[]; model?: 'qtensor' };
}

export interface Candidate {
  id: string;
  rank: number;
  role: string | null;
  roles: string[];
  role_labels: string[];
  family: 'exact' | 'near_match' | 'lens_two_reflector';
  review?: boolean;          // P4 Lens Family candidate not accepted (shown in the Lens card only)
  accepted?: boolean;        // P4 Lens Family candidate accepted as Computed (non-paraxial η, constraints)
  review_status?: string;
  theta_out_rad?: number;
  lens_checks?: LensCheck[];
  lens_constraint?: string | null;
  lens_pose?: LensPose | null;
  alignment?: AlignmentStudy | null;
  fit_history?: { step: string; eta: number }[];
  model?: 'separable' | 'qtensor';
  freeform?: {
    status: string; normalized_mode_overlap?: number; grid_change?: number; constraint?: string | null; reason?: string;
    reflectors?: { id: string; max_sag_change_um: number; terms: { u_power: number; v_power: number; coefficient_si: number }[];
      correction_size?: Record<'footprint' | 'aperture', { pv_um: number; rms_um: number; max_slope_mrad: number }> }[];
    pose?: { quadric_worst_loss_db: number | null; corrected_worst_loss_db: number | null; cases: string };
    surface?: string; meaning?: string;
  } | null;
  nonparaxial_check?: { status: string; normalized_mode_overlap?: number; grid_change?: number; clipped_power_fraction?: number; method?: string; omits?: string } | null;
  ray_transfer_check?: { q_tensor_relative_difference: number; symplectic_error: number; method: string } | null;
  parameters_mm: { a?: number; b?: number; c?: number };
  metrics: {
    max_abs_curvature_per_m: number | null;
    worst_pose_mismatch_db: number | null;
    total_path_mm: number;
    ambient_path_mm?: number;
    normalized_mode_overlap: number | null;
    nonparaxial_overlap?: number | null;
    corrected_nonparaxial_overlap?: number | null;
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

export interface Guidance { kind: string; phase?: string; port?: string; level?: 'info' | 'warning'; message: string; values?: Record<string, unknown> }

export interface StudyCase {
  a_mm: number; c_mm: number; total_path_mm: number; max_3w_footprint_curvature: number; max_divergence_rad: number;
  incidence_deg: number[]; paraxial_overlap: number; nonparaxial_overlap: number; nonparaxial_status: string; clipped_power_fraction: number;
}
export interface NonparaxialStudy { status: string; cases: StudyCase[]; meaning?: string; message?: string; reason?: string }

export interface SearchMap {
  a_mm: number[];
  c_mm: number[];
  cells: { status: string; reason: string; slope: number | null; path_m: number | null }[];
  near_match: { a_mm: number; c_mm: number; eta: number }[];
  slope_limit: number;
}

export interface Crossing {
  side: 'source' | 'target';
  surface_point_mm: Vec3;
  ambient_length_mm: number;
  incidence_deg: number;
  refraction_deg: number;
  q_scale_ts: [number, number];
  fresnel_transmission_uncoated: { s: number; p: number; mean: number };
  meaning: string;
}

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
  family?: 'exact' | 'near_match' | null;
  relay_medium?: Medium;
  crossing?: Crossing | null;
  guidance?: Guidance[];
  nonparaxial_study?: NonparaxialStudy | null;
  families?: FamilyRow[];
  lens_review?: { status: string; candidates: Candidate[]; fail_reasons?: string[]; meaning?: string;
    accept_rule?: { min_nonparaxial_overlap: number } } | null;
  search?: {
    status?: string; reason?: string; grid_points?: number; exact_feasible?: number; near_match_feasible?: number;
    screening_counts?: Record<string, number>; elapsed_seconds?: number; policy?: string; map?: SearchMap | null;
    closest_exact?: { a_m: number; c_m: number; max_footprint_slope: number; limit: number } | null;
  };
  limitations?: string[];
  uncomputed?: string[];
}
