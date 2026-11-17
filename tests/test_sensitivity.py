"""Verify the sensitivity comparison against independent Synthetic references."""

import copy
import json
import math
from pathlib import Path
import re
import unittest

import numpy as np

from photonic_architecture_explorer.design import design_two_ports
from photonic_architecture_explorer.design_report import render_design_report, review_snapshot
from photonic_architecture_explorer.gaussian import Gaussian
from photonic_architecture_explorer.sensitivity import evaluate_perturbation, target_scenarios


ROOT = Path(__file__).resolve().parents[1]


class CandidateSensitivityTests(unittest.TestCase):
    def test_matched_flat_gaussian_closed_form(self):
        widths = (8e-6, 12e-6)
        mode = Gaussian.from_radii(widths)
        k = 2 * math.pi / mode.wavelength
        for row in target_scenarios():
            with self.subTest(scenario=row["id"]):
                expected_log_loss = sum((displacement / w)**2 + (k * w * tilt / 2)**2
                                        for w, displacement, tilt in
                                        zip(widths, row["offset_m"], row["slope_rad"]))
                actual = evaluate_perturbation(mode, mode, 1., row)
                self.assertAlmostEqual(actual["normalized_mode_overlap"], math.exp(-expected_log_loss), places=14)
                self.assertAlmostEqual(actual["delta_loss_db"], 10 * expected_log_loss / math.log(10), places=12)

    def test_curved_offset_and_tilt_match_independent_quadrature(self):
        w_arrival, c_arrival = (9e-6, 12e-6), (3500., -1200.)
        w_target, c_target = (10e-6, 11e-6), (1000., 600.)
        arrival = Gaussian.from_radii(w_arrival, curvature=c_arrival)
        target = Gaussian.from_radii(w_target, curvature=c_target)
        k = 2 * math.pi / target.wavelength
        offsets, slopes = (2e-6, -4e-6), (-0.009, 0.007)

        def reference(positions, angles):
            overlap = 1.
            for j, (offset, tilt) in enumerate(zip(positions, angles)):
                x = np.linspace(-100e-6, 100e-6, 20001)
                shifted = x - offset
                left = np.exp(-(shifted / w_arrival[j])**2
                              - 1j * k * (0.5 * c_arrival[j] * shifted**2 + tilt * shifted))
                right = np.exp(-(x / w_target[j])**2 - 0.5j * k * c_target[j] * x**2)
                overlap *= abs(np.trapezoid(left * right.conj(), x))**2 / (
                    np.trapezoid(abs(left)**2, x) * np.trapezoid(abs(right)**2, x))
            return overlap

        baseline = reference((0., 0.), (0., 0.))
        expected = reference(offsets, slopes)
        actual = evaluate_perturbation(arrival, target, baseline, {
            "id": "curved-control", "offset_m": offsets, "slope_rad": slopes})
        self.assertAlmostEqual(actual["normalized_mode_overlap"], expected, places=12)
        self.assertAlmostEqual(actual["delta_loss_db"], -10 * math.log10(expected / baseline), places=11)

    def test_guard_and_infinite_loss_are_distinct(self):
        mode = Gaussian.from_radii((8e-6, 12e-6))
        declined = evaluate_perturbation(mode, mode, 1., {
            "id": "over-guard", "offset_m": (0., 0.), "slope_rad": (0.04, 0.04)})
        self.assertEqual(declined["status"], "Uncomputed")
        self.assertIn("50 mrad", declined["reason"])
        self.assertNotIn("normalized_mode_overlap", declined)
        zero = evaluate_perturbation(mode, mode, 0., {"id": "nominal"})
        self.assertEqual(zero["loss_status"], "Infinite")
        self.assertIsNone(zero["mode_mismatch_loss_db"])
        self.assertEqual(zero["delta_status"], "Uncomputed")
        json.dumps(zero, allow_nan=False)

    def test_snapshot_preserves_ports_and_ranking_and_matches_html(self):
        document = json.loads((ROOT / "examples/m5a_two_ports.json").read_text())
        result = design_two_ports(document)
        before = copy.deepcopy(result)
        report = review_snapshot(result)
        self.assertEqual(result, before)
        self.assertEqual({key: report[key] for key in before}, before)
        diagnostic = report["candidate_sensitivity"]
        self.assertEqual(diagnostic["status"], "Approximate")
        self.assertEqual(diagnostic["input_sha256"], before["input_sha256"])
        self.assertEqual(diagnostic["target_reference_plane"], document["target"]["reference_plane"]["value"])
        self.assertEqual(diagnostic["recommended_candidate_id"], before["selected_candidate_id"])
        self.assertEqual([item["candidate_id"] for item in diagnostic["candidates"]],
                         [item["id"] for item in before["candidates"]])
        self.assertEqual(len(diagnostic["scenarios"]), 9)
        for candidate, entry in zip(before["candidates"], diagnostic["candidates"]):
            self.assertEqual(entry["samples"]["nominal"]["normalized_mode_overlap"],
                             candidate["evaluation"]["gaussian_mode_matching"]["normalized_mode_overlap"])
            self.assertEqual(entry["samples"]["nominal"]["delta_loss_db"], 0.)
        html = render_design_report(report)
        embedded = re.search(r'<script type="application/json" id="design-result">(.*?)</script>', html).group(1)
        self.assertEqual(json.loads(embedded), report)
        self.assertEqual(html.count("data-sensitivity="), len(before["candidates"]))

        rejected = review_snapshot(design_two_ports({}))
        self.assertEqual(rejected["candidate_sensitivity"]["status"], "Uncomputed")
        self.assertNotIn("data-sensitivity-cell", render_design_report(rejected))
