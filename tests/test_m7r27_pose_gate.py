from types import SimpleNamespace
import unittest

import numpy as np

from photonic_architecture_explorer.external import adapt_external
from scripts.m7r7_package import CASE_PATH, INPUT_PATH, ROOT, load
from scripts.m7r9_envelope_review import R8_SUMMARY, prescription
from scripts.m7r27_pose_gate import posed_mirrors, review
from test_m2 import newton_reference


class PoseGateTests(unittest.TestCase):
    def test_signed_crossings_and_decision_evidence(self):
        report = review()
        frozen = load(ROOT / "references/m7r27/summary.json")
        expansion = load(R8_SUMMARY)["candidates"]["expansion"]
        model = adapt_external(prescription(load(INPUT_PATH), load(CASE_PATH), expansion))
        self.assertAlmostEqual(report["nominal_gaussian_eta"], 0.9900109725310262, delta=1e-12)
        for eta in report["nominal_independent_quadrature"]:
            self.assertAlmostEqual(eta, report["nominal_gaussian_eta"], delta=1e-12)
        self.assertEqual(len(report["cases"]), 12)
        self.assertEqual(report["fixed_input_sha256"], frozen["fixed_input_sha256"])
        for row, stored in zip(report["cases"], frozen["cases"], strict=True):
            mirrors = posed_mirrors(model, row)
            offset, slope = newton_reference(model.source, model.target, mirrors)
            np.testing.assert_allclose(row["target_offset_ts_m"], offset, atol=1e-13, rtol=0)
            np.testing.assert_allclose(row["target_angle_ts_rad"], np.arctan(slope), atol=1e-11, rtol=0)
            np.testing.assert_allclose(row["hit_distance_from_vertex_m"],
                                       stored["hit_distance_from_vertex_m"], atol=1e-13, rtol=0)
            # Independently differentiate Newton crossings in the actual fixed plane.
            # World -Z is the frozen tangential axis at both Ports.
            fine = row["tangential_ray_refinements"][-1]
            for column, step in enumerate((fine["height_step_m"], fine["direction_cosine_step"])):
                readings = []
                for sign in (-1, 1):
                    height, momentum = (step, 0.) if column == 0 else (0., step)
                    ray = SimpleNamespace(position=(0., 0., -sign * height),
                                          direction=(np.sqrt(1 - momentum**2), 0., -sign * momentum),
                                          sagittal=model.source.sagittal)
                    crossing, slope = newton_reference(ray, model.target, mirrors)
                    readings.append(np.array([crossing[0], slope[0] / np.sqrt(1 + np.dot(slope, slope))]))
                expected = (readings[1] - readings[0]) / (2 * step)
                np.testing.assert_allclose(np.array(fine["matrix"])[:, column],
                                           expected, atol=1e-8, rtol=1e-8)
            self.assertLess(abs(fine["determinant"] - 1), 1e-8)
            self.assertEqual(row["gaussian_geometry"], stored["gaussian_geometry"])
            self.assertEqual(row["chief_ray_status"], "Computed")
            self.assertEqual(row["threshold_status"], "Evidence Insufficient")
            self.assertIsNone(row["perturbed_gaussian_eta"])
            self.assertIsNone(row["numerical_U"])
        self.assertEqual(len(report["nominal_physical_optics_fixed_window"]), 6)
        for key in ("actual_assembly_tolerance", "finite_beam_clearance", "total_coupling"):
            self.assertEqual(report[key], "Uncomputed")
