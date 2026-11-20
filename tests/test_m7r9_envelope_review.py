import unittest
from types import SimpleNamespace

import numpy as np
from test_m2 import newton_reference
from test_placement import rotation_reference

from photonic_architecture_explorer.external import adapt_external
from scripts.m7r7_package import CASE_PATH, INPUT_PATH, load
from scripts.m7r9_envelope_review import R8_SUMMARY, prescription, review


class EnvelopeReviewTests(unittest.TestCase):
    def test_replay_preserves_the_nominal_decision_and_all_signed_trace_cases(self):
        result = review()
        self.assertEqual(result["nominal_threshold_candidates"], ["expansion"])
        self.assertEqual(result["finite_beam_clearance"], "Uncomputed")
        self.assertEqual(result["perturbed_gaussian_mode_overlap"], "Uncomputed")
        self.assertIsNone(result["total_coupling"])

        archive, case, fixed = map(load, (R8_SUMMARY, CASE_PATH, INPUT_PATH))
        for name, candidate in result["candidates"].items():
            self.assertAlmostEqual(
                candidate["aabb_clearance_margin_m"], 0.0, delta=1.1e-12
            )
            self.assertEqual(candidate["limiting_envelope_boundary"]["face"], "X-")
            source_record = archive["candidates"][name]
            proposal = prescription(fixed, case, source_record)
            self.assertEqual(
                proposal["design"]["reflectors"], source_record["mirror_prescriptions"]
            )

            adapted = adapt_external(proposal)
            traced = candidate["chief_ray_placement"]["cases"]
            self.assertEqual(len(traced), 16)
            for row in traced:
                with self.subTest(
                    candidate=name,
                    mirror=row["mirror"],
                    axis=row["axis"],
                    delta=row.get("delta_m", row.get("delta_rad")),
                ):
                    self.assertEqual(row["status"], "Computed")
                    moved = list(adapted.reflectors)
                    index = row["mirror"] - 1
                    mirror = moved[index]
                    vertex, normal = mirror.vertex, mirror.normal
                    if row["kind"] == "translation":
                        vertex = (
                            np.array(vertex)
                            + np.eye(3)["XYZ".index(row["axis"])] * row["delta_m"]
                        )
                    else:
                        normal = rotation_reference(
                            mirror, adapted.source.sagittal, row["delta_rad"]
                        )
                    moved[index] = SimpleNamespace(
                        vertex=vertex, normal=normal, curvatures=mirror.curvatures
                    )
                    offset, slope = newton_reference(
                        adapted.source, adapted.target, moved
                    )
                    np.testing.assert_allclose(
                        row["target_offset_m"], offset, atol=1e-13, rtol=0
                    )
                    np.testing.assert_allclose(
                        row["target_angular_error_rad"],
                        np.arctan(slope),
                        atol=1e-11,
                        rtol=0,
                    )
