"""Replay the R8-expansion pose sweep and test applicability on the fixed Target."""
import argparse
from dataclasses import replace
from pathlib import Path

import numpy as np

from photonic_architecture_explorer.diagnostics import ray_to_target
from photonic_architecture_explorer.external import adapt_external
from photonic_architecture_explorer.placement import placement_cases, rotate_in_plane
from photonic_architecture_explorer.solver import evaluate
from scripts.m7r7_package import CASE_PATH, INPUT_PATH, ROOT, load, write
from scripts.m7r9_envelope_review import R8_SUMMARY, prescription, review_candidate
from scripts.m7r13_target_acceptance import ARCHIVE, verify_hash

R9 = ROOT / "references/m7r9/summary.json"
ETA_BUDGET = 2e-6


def fixed_plane_reference():
    """Integrate the two archived physical-optics fields on concentric fixed squares."""
    archive = load(ARCHIVE / "summary.json")
    for name, digest in archive["inputs"].items():
        verify_hash(ROOT / name, digest)
    fixed = load(INPUT_PATH)
    mode = fixed["target"]
    widths = np.array(mode["mfd_ts_m"]["value"]) / 2
    curvature = np.array(mode["wavefront_curvature_ts_per_m"]["value"])
    k = 2 * np.pi * fixed["ambient_index"]["value"] / fixed["wavelength_m"]["value"]
    by_grid = {(row["pitch_um"], row["half_window_um"]): row["eta"]
               for row in archive["runs"]["q14-14-edge1"]["target"]}
    rows = []
    for pitch, windows in ((2, (24, 48, 96, 192)), (0.5, (24, 48))):
        name = f"target-q14-14-edge1-{pitch}um.npz"
        verify_hash(ARCHIVE / name, archive["sha256"][name])
        with np.load(ARCHIVE / name) as field:
            axis, data = field["ts_m"], field["E"]
        np.testing.assert_allclose(np.diff(axis), pitch * 1e-6, rtol=0, atol=1e-16)
        for half in windows:
            use = np.abs(axis) < half * 1e-6
            grid = axis[use]
            actual = data[np.ix_(use, use)]
            factors = np.exp(-grid[None, :]**2 * (widths**-2 + 0.5j*k*curvature)[:, None])
            target = np.outer(*factors)
            eta = float(abs(np.vdot(target, actual))**2 /
                        (np.vdot(target, target).real * np.vdot(actual, actual).real))
            if abs(eta - by_grid[pitch, half]) > 1e-12:
                raise ValueError("Stored finite-window reference did not reproduce")
            rows.append(dict(pitch_um=pitch, half_window_um=half, eta_window=eta))
    return rows


def posed_mirrors(design, row):
    mirrors = list(design.reflectors)
    index = row["mirror"] - 1
    mirror = mirrors[index]
    if row["kind"] == "rotation":
        mirrors[index] = rotate_in_plane(mirror, design.source.sagittal, row["delta_rad"])
    else:
        vertex = list(mirror.vertex)
        vertex["XYZ".index(row["axis"])] += row["delta_m"]
        mirrors[index] = replace(mirror, vertex=vertex)
    return mirrors


def tangential_ray_response(design, mirrors):
    """Central differences of fixed-plane position and direction at the actual pose."""
    source, target = design.source, design.target
    tangent = np.cross(source.sagittal, source.direction)
    target_tangent = np.cross(target.sagittal, target.direction)
    results = []
    for step in (1e-6, 5e-7, 2.5e-7):
        # Scale length and direction separately. p is the transverse direction cosine.
        derivatives = []
        for height, momentum in ((step, 0.), (0., step / 1e-3)):
            readings = []
            for sign in (-1, 1):
                origin = source.position + sign * height * tangent
                direction = (np.sqrt(1 - momentum**2) * np.array(source.direction)
                             + sign * momentum * tangent)
                ray = ray_to_target(origin, direction, target, mirrors, source.sagittal)
                readings.append(np.array([ray["target_offset_m"][0],
                                          np.dot(ray["target_ray_direction"], target_tangent)]))
            derivatives.append((readings[1] - readings[0]) / (2 * (height or momentum)))
        matrix = np.column_stack(derivatives)
        results.append({"height_step_m": step, "direction_cosine_step": step / 1e-3,
                        "matrix": matrix.tolist(), "determinant": float(np.linalg.det(matrix))})
    return results


def review():
    r8, fixed, case = map(load, (R8_SUMMARY, INPUT_PATH, CASE_PATH))
    expansion = r8["candidates"]["expansion"]
    design = adapt_external(prescription(fixed, case, expansion))
    nominal = review_candidate(fixed, case, expansion)
    archived = load(R9)["candidates"]["expansion"]["chief_ray_placement"]["cases"]
    traces = placement_cases(design.source, design.target, design.reflectors)
    radius = design.target.mode.parameters()[0]["radius_m"]
    rows = []
    for ray, frozen in zip(traces["cases"], archived, strict=True):
        if ray["axis"] == "Y":
            continue
        identity = {k: ray[k] for k in ("mirror", "kind", "axis", "delta_rad", "delta_m") if k in ray}
        if any(frozen[k] != value for k, value in identity.items()):
            raise ValueError("R9 pose differs from frozen case")
        for key, atol in (("target_offset_m", 1e-13), ("target_angular_error_rad", 1e-11)):
            np.testing.assert_allclose(ray[key], frozen[key], atol=atol, rtol=0)
        mirrors = posed_mirrors(design, ray)
        evaluated = evaluate(design.source, design.target, mirrors)
        if evaluated["geometry"]["status"] != "Fail":
            raise ValueError("Changed vertex-geometry scope requires review of field evidence")
        hits = [float(np.linalg.norm(np.subtract(h["position_m"], m.vertex)))
                for h, m in zip(ray["hits"], mirrors, strict=True)]
        rows.append({**identity, "chief_ray_status": ray["status"],
                     "target_offset_ts_m": ray["target_offset_m"],
                     "target_angle_ts_rad": ray["target_angular_error_rad"],
                     "target_offset_t_over_target_radius_t": ray["target_offset_m"][0] / radius,
                     "tangential_ray_refinements": tangential_ray_response(design, mirrors),
                     "hit_distance_from_vertex_m": hits, "gaussian_geometry": evaluated["geometry"],
                     "gaussian_model_domain": evaluated["model_domain"]["status"],
                     "perturbed_gaussian_eta": None, "numerical_U": None,
                     "threshold_status": "Evidence Insufficient"})
    return {"candidate_id": "R8-expansion", "fixed_input_sha256": r8["fixed_input_sha256"],
            "target_radius_t_m": radius, "target_eta": 0.99, "required_maximum_U": ETA_BUDGET,
            "nominal_gaussian_eta": nominal["normalized_gaussian_overlap"],
            "nominal_independent_quadrature": nominal["quadrature_overlap"],
            "nominal_physical_optics_fixed_window": fixed_plane_reference(),
            "field_evidence": {"perturbed_complex_target_field": "Uncomputed",
                               "full_plane_output_norm_error_bound": None,
                               "scope": "Frozen nominal finite-window physical optics only"},
            "cases": rows, "actual_assembly_tolerance": "Uncomputed",
            "finite_beam_clearance": "Uncomputed", "total_coupling": "Uncomputed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    path = parser.parse_args().output
    path.parent.mkdir(parents=True, exist_ok=True)
    write(path, review())
