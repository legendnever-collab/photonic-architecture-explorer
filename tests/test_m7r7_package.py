import unittest

from scripts.m7r7_package import (
    CASE_PATH,
    INPUT_PATH,
    load,
    package_record,
    replay_baseline,
)


class NominalPackageReviewTests(unittest.TestCase):
    def test_baseline_package_failure_withholds_overlap(self):
        case = load(CASE_PATH)
        fixed = load(INPUT_PATH)
        incoming = {label: fixed[label].copy() for label in ("source", "target")}
        baseline = {
            row["id"]: row for row in replay_baseline(fixed, package_record(case), case)
        }
        long = baseline["G036-NM"]
        short = baseline["G029-NM"]
        self.assertAlmostEqual(
            long["normalized_gaussian_overlap"], 0.9990889546173051, places=12
        )
        self.assertAlmostEqual(
            short["normalized_gaussian_overlap"], 0.9980603001813527, places=12
        )
        self.assertIn(
            "reflectors[0].half_aperture_bounds_m", long["package"]["failed_checks"]
        )
        self.assertEqual(
            short["package"]["failed_checks"], ["body[0].volume", "body[1].volume"]
        )
        self.assertAlmostEqual(
            short["package"]["minimum_boundary_gap_m"], -4.2814308599422885e-5
        )
        for row in baseline.values():
            self.assertEqual(row["package"]["finite_beam_clearance"], "Uncomputed")
            self.assertIsNone(row["package_screen_overlap"])
            self.assertFalse(row["margin_targets_met"])
            self.assertEqual(row["placement"]["summary"]["translation"]["computed"], 12)
            self.assertEqual(row["placement"]["summary"]["rotation"]["computed"], 4)
        self.assertEqual(incoming, {label: fixed[label] for label in incoming})

    def test_body_clearance_is_specific_to_declared_package(self):
        case = load(CASE_PATH)
        fixed = load(INPUT_PATH)
        package = package_record(case)
        package["available_volume"]["value"]["min_m"][0] -= 0.10e-3
        package["available_volume"]["value"]["max_m"][0] += 0.10e-3
        _, short = replay_baseline(fixed, package, case)
        self.assertEqual(short["id"], "G029-NM")
        self.assertEqual(short["package"]["envelope_geometry"], "Pass")
        self.assertEqual(short["package"]["finite_beam_clearance"], "Uncomputed")
        self.assertAlmostEqual(
            short["package_screen_overlap"],
            short["normalized_gaussian_overlap"],
            places=12,
        )
        self.assertFalse(short["margin_targets_met"])
