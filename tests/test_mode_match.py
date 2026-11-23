"""Synthetic and display checks for the existing Gaussian Mode Overlap."""

import json
import math
from pathlib import Path
import unittest

import numpy as np

from photonic_architecture_explorer.design import design_two_ports
from photonic_architecture_explorer.gaussian import Gaussian, mode_overlap
from photonic_architecture_explorer.mode_match import axis_profiles, loss_label


ROOT = Path(__file__).resolve().parents[1]


class ModeMatchViewTests(unittest.TestCase):
    def test_phase_changes_overlap_with_identical_intensity(self):
        radii = (10e-6, 13e-6)
        target = Gaussian.from_radii(radii)
        k = 2 * math.pi * target.index / target.wavelength
        curvature = [4 / (k * width**2) for width in radii]
        incidence = Gaussian.from_radii(radii, curvature=curvature)
        predicted = 0.5
        eta = mode_overlap(incidence, target)["normalized_mode_overlap"]
        self.assertAlmostEqual(eta, predicted, places=13)
        self.assertEqual(loss_label(eta), "3.0103 dB")

        quadrature = 1.
        for axis, width in enumerate(radii):
            coordinates, arrived, desired, phase = axis_profiles(incidence, axis, target)
            self.assertEqual(coordinates[60], 0)
            np.testing.assert_allclose(arrived, desired, rtol=1e-13, atol=1e-16)
            self.assertAlmostEqual(phase[60], 0, places=14)
            self.assertAlmostEqual(phase[-1], -18, places=12)
            x = np.linspace(-7 * width, 7 * width, 4001)
            fields = [np.array([mode.axis_field(v, axis) for v in x]) for mode in (incidence, target)]
            norms = [np.trapezoid(abs(field)**2, x) for field in fields]
            for norm in norms:
                self.assertAlmostEqual(norm, 1, places=13)
            quadrature *= abs(np.trapezoid(fields[0] * fields[1].conj(), x))**2 / math.prod(norms)
        self.assertAlmostEqual(quadrature, predicted, places=12)

    def test_report_uses_fixed_reference_planes_and_original_overlap(self):
        document = json.loads((ROOT / "examples/m5a_two_ports.json").read_text())
        result = design_two_ports(document)
        self.assertEqual(result["status"], "Computed")
        for candidate in result["candidates"]:
            self.assertAlmostEqual(candidate["evaluation"]["gaussian_mode_matching"]["normalized_mode_overlap"],
                                   1, places=12)
            for name in ("source", "target"):
                self.assertEqual(candidate["prescription"][name], document[name])

        for change, expected in (("phase", "Uncomputed"), ("divergence", "Fail")):
            invalid = json.loads(json.dumps(document))
            if change == "phase":
                del invalid["source"]["wavefront_curvature_ts_per_m"]
            else:
                invalid["source"]["mfd_ts_m"]["value"] = [2e-6, 2e-6]
            rejected = design_two_ports(invalid)
            self.assertEqual(rejected["status"], expected)
            self.assertEqual(rejected["candidates"], [])

    def test_loss_distinguishes_zero_and_missing_overlap(self):
        self.assertEqual(loss_label(0), "∞ dB")
        self.assertEqual(loss_label(None), "Uncomputed")
        self.assertEqual(loss_label(1), "0 dB")
