from copy import deepcopy
import json
from unittest import TestCase
from unittest.mock import patch

from photonic_architecture_explorer.envelope_search import compare_envelopes, digest
from photonic_architecture_explorer.external import evaluate_external
from photonic_architecture_explorer.inspector import ROOT
from photonic_architecture_explorer.reference_redesign import PORTS_FILE


class EnvelopeSearchTests(TestCase):
    def setUp(self):
        self.ports = json.loads((ROOT / PORTS_FILE).read_text(encoding="utf-8"))

    def test_recompute_both_limits_and_scope_each_selected_candidate(self):
        reference = json.loads((ROOT / "references/m7r9/summary.json").read_text(encoding="utf-8"))
        previous = None
        for key in ("nominal", "expansion"):
            result = compare_envelopes(self.ports, key)
            snapshot = result["input_snapshot"]
            self.assertEqual({k: v for k, v in snapshot.items() if k != "package"}, self.ports)
            case = result["envelope_comparison"]["cases"][key]
            self.assertEqual(digest(snapshot), case["input_sha256"])
            self.assertNotEqual(result["input_sha256"], previous)
            self.assertEqual(result["input_sha256"], case["input_sha256"])
            previous = result["input_sha256"]
            candidate, = result["candidates"]
            self.assertEqual(candidate["prescription"]["package"], snapshot["package"])
            self.assertEqual(candidate["id"], case["selected"])
            replay = evaluate_external(candidate["prescription"])
            self.assertEqual(replay["physical_losses"]["status"], "Uncomputed")
            self.assertEqual(replay["fabrication"]["status"], "Uncomputed")
            self.assertEqual(replay["package_feasibility"]["envelope_geometry"]["status"], "Pass")
            self.assertGreaterEqual(case["minimum_gap_m"], 50e-6)
            self.assertEqual(case["limiting_boundary"]["face"], "X-")
            self.assertEqual(case["limiting_boundary"]["mirror"], 2)
            accepted_ids = [row["id"] for row in case["passing_trials"]]
            self.assertEqual(accepted_ids[0], case["selected"])
            self.assertEqual(case["passing_trials"][0]["max_projected_radius_m"], case["max_projected_radius_m"])
            self.assertEqual(case["evaluations"], len(accepted_ids) + len(case["rejected"]))
            self.assertEqual(case["evaluations"], 74)
            self.assertTrue(any("-G" in identifier for identifier in accepted_ids))
            eta = reference["candidates"][key]["normalized_gaussian_overlap"]
            self.assertAlmostEqual(case["r9_replay"]["overlap"], eta, delta=1e-8)
            self.assertAlmostEqual(replay["gaussian_mode_matching"]["normalized_mode_overlap"], case["overlap"], delta=1e-12)
            for q in case["r9_replay"]["quadrature"]:
                self.assertAlmostEqual(q, eta, delta=1e-8)
            self.assertEqual(case["threshold_met"], key == "expansion")
            if key == "nominal":
                self.assertIn("R8-expansion", case["rejected"])
            else:
                self.assertIn("R8-nominal", accepted_ids)

    def test_edited_ports_or_failed_quadrature_withhold_results(self):
        edited = deepcopy(self.ports)
        edited["target"]["position_m"]["value"][2] += .0001
        with self.assertRaisesRegex(ValueError, "원본 Example A"):
            compare_envelopes(edited, "nominal")
        with patch("photonic_architecture_explorer.envelope_search.independent_check", side_effect=AssertionError):
            with self.assertRaisesRegex(ValueError, "Quadrature"):
                compare_envelopes(self.ports, "expansion")

    def test_custom_exact_preset_boundaries_match_r23_and_preserve_input_provenance(self):
        for preset, limits in (
            ("nominal", (-0.00115, 0.00315)),
            ("expansion", (-0.0015821774231937228, 0.0034415473764667017)),
        ):
            with self.subTest(preset=preset):
                baseline = compare_envelopes(self.ports, preset)
                result = compare_envelopes(self.ports, "custom", x_limits_m=limits)
                expected = baseline["envelope_comparison"]["cases"][preset]
                evaluated = result["envelope_comparison"]["cases"]["custom"]
                self.assertEqual({k: v for k, v in evaluated.items() if k != "input_sha256"},
                                 {k: v for k, v in expected.items() if k != "input_sha256"})
                package = result["input_snapshot"]["package"]
                self.assertEqual(package["available_volume"]["provenance"], "supplied")
                for key in ("keepout_bodies", "frame_id", "required_clearance_m"):
                    self.assertEqual(package[key], baseline["input_snapshot"]["package"][key])
                for key in ("min_m", "max_m"):
                    self.assertEqual(package["available_volume"]["value"][key][1:],
                                     expected["envelope"][key][1:])
                self.assertEqual(result["input_sha256"], digest(result["input_snapshot"]))

    def test_custom_midrange_and_no_candidate_are_scoped_to_new_inputs(self):
        mid = compare_envelopes(self.ports, "custom", x_limits_m=(-.00136, .00337))
        narrow = compare_envelopes(self.ports, "custom", x_limits_m=(0.0, .002))
        self.assertNotEqual(mid["input_sha256"], narrow["input_sha256"])
        self.assertEqual(mid["selected_candidate_id"], "R8-nominal")
        self.assertEqual(mid["search"]["accepted_count"], 37)
        self.assertIsNone(mid["envelope_comparison"]["cases"]["custom"]["r9_replay"])
        self.assertEqual(narrow["status"], "NoCandidate")
        self.assertEqual(narrow["candidates"], [])
        self.assertEqual(narrow["input_contract"]["status"], "Pass")
        summary = narrow["envelope_comparison"]["cases"]["custom"]
        self.assertEqual(len(summary["rejected"]), 74)
        for field in ("overlap", "threshold_met", "max_projected_radius_m", "minimum_gap_m"):
            self.assertIsNone(summary[field])

    def test_custom_rejects_invalid_bounds_and_withholds_failed_replay(self):
        for limits in [(1.0, 1.0), (2.0, 1.0), (0.0, float("inf"))]:
            with self.assertRaisesRegex(ValueError, "World X"):
                compare_envelopes(self.ports, "custom", x_limits_m=limits)
        failing_quadrature = {"status": "Pass", "quadrature_overlap": [0.98, 0.98]}
        with patch("photonic_architecture_explorer.envelope_search.independent_check",
                   return_value=failing_quadrature):
            with self.assertRaisesRegex(ValueError, "허용 오차"):
                compare_envelopes(self.ports, "custom", x_limits_m=(-0.00115, 0.00315))
