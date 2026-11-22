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

    def test_clearance_replays_r24_and_matches_raw_adapter(self):
        from photonic_architecture_explorer.envelope_geometry import package_evidence

        for key, x_limits, count, extra_um in (
            ("nominal", None, 19, 0), ("expansion", None, 48, 0),
            ("custom", (-.00136, .00337), 37, 210),
        ):
            with self.subTest(envelope=key):
                result = compare_envelopes(self.ports, key, x_limits_m=x_limits)
                summary = result["envelope_comparison"]["cases"][key]
                self.assertEqual(summary["evaluations"], 74)
                self.assertEqual(len(summary["passing_trials"]), count)
                for trial in summary["passing_trials"]:
                    self.assertEqual(trial["limiting_check"]["status"], "Pass")
                    self.assertGreaterEqual(trial["additional_clearance_m"], 0)
                candidate, = result["candidates"]
                proposal = candidate["prescription"]
                replay = evaluate_external(proposal)
                evidence = package_evidence(proposal, replay)
                expected_gap = min(evidence[field] for field in (
                    "minimum_boundary_gap_m", "mirror_pair_aabb_gap_m", "minimum_body_keepout_aabb_gap_m",
                ))
                clearance = candidate["clearance"]
                self.assertAlmostEqual(clearance["minimum_gap_m"], expected_gap, delta=1e-15)
                self.assertAlmostEqual(clearance["additional_clearance_m"] * 1e6, extra_um, delta=1e-5)
                check = dict(clearance["limiting_check"])
                self.assertEqual(check.pop("face"), "X-")
                self.assertEqual(check["path"], "body[1].volume")
                self.assertIn(check, replay["package_feasibility"]["envelope_geometry"]["checks"])
                winner = summary["clearance_selection"]
                if key == "expansion":
                    self.assertEqual(winner["status"], "Verified")
                    self.assertEqual(winner["eligible_count"], 1)
                    self.assertEqual(winner["candidate"]["id"], "R8-expansion")
                    self.assertTrue(all(abs(value - candidate["overlap"]) <= 1e-8
                                        and value >= .99 for value in winner["quadrature"]))
                else:
                    self.assertEqual(winner, {"status": "NoTargetCandidate", "candidate": None})

    def test_distinct_clearance_candidate_and_failed_validation(self):
        from photonic_architecture_explorer import envelope_search

        evaluate = envelope_search.evaluate_envelope

        def lower_target(snapshot, ports, case, trials, preset, reference):
            return evaluate(snapshot, ports, {**case, "min_normalized_gaussian_overlap": .25},
                            trials, preset, reference)

        with patch.object(envelope_search, "evaluate_envelope", side_effect=lower_target):
            result = compare_envelopes(self.ports, "custom", x_limits_m=(-.00136, .00337))
            best, alternative = result["candidates"]
            self.assertGreater(best["overlap"], alternative["overlap"])
            self.assertGreater(alternative["clearance"]["additional_clearance_m"],
                               best["clearance"]["additional_clearance_m"])
            self.assertEqual(alternative["recommendation_role"], "max_clearance")
            self.assertEqual(alternative["independent_validation"]["status"], "Pass")
            validate = envelope_search.validate_overlap

            def fail_alternative(candidate, ports, expected=None):
                if candidate["id"] == alternative["id"]:
                    raise envelope_search.EnvelopeValidationError("Quadrature")
                return validate(candidate, ports, expected)

            with patch.object(envelope_search, "validate_overlap", side_effect=fail_alternative):
                withheld = compare_envelopes(self.ports, "custom", x_limits_m=(-.00136, .00337))
                self.assertEqual(len(withheld["candidates"]), 1)
                selection = withheld["envelope_comparison"]["cases"]["custom"]["clearance_selection"]
                self.assertEqual(selection["status"], "VerificationWithheld")
                self.assertIsNone(selection["candidate"])

    def test_limiting_adapter_paths_include_pair_and_keepout(self):
        from photonic_architecture_explorer.envelope_geometry import clearance_margin
        from photonic_architecture_explorer.package_geometry import assess_package
        from photonic_architecture_explorer.external import adapt_external, read, InputIssue

        report = compare_envelopes(self.ports, "expansion")
        original = report["candidates"][0]["prescription"]
        for expected, kind in (("reflector_envelope_pair", "pair"), ("body[0].keepout[0]", "keepout")):
            with self.subTest(kind=kind):
                proposal = deepcopy(original)
                adapted = adapt_external(proposal)
                package = proposal["package"]
                outer = package["available_volume"]["value"]
                outer.update(min_m=[-.02] * 3, max_m=[.02] * 3)
                # Extend the first backing enclosures while preserving patch containment.
                first, second = [r["body_envelope"]["value"] for r in proposal["reflectors"]]
                if kind == "pair":
                    package["keepout_bodies"]["value"] = []
                    first["min_m"][0] = second["max_m"][0]
                    first["max_m"][2] = second["min_m"][2] - .00008
                else:
                    package["keepout_bodies"]["value"] = [{**outer,
                        "min_m": [first["min_m"][0], first["max_m"][1] + .00008, first["min_m"][2]],
                        "max_m": [first["max_m"][0], first["max_m"][1] + .00018, first["max_m"][2]]}]
                raw = assess_package(proposal, adapted, read, InputIssue)
                self.assertEqual(raw["envelope_geometry"]["status"], "Pass")
                result = clearance_margin(proposal, {"package_feasibility": raw})
                self.assertEqual(result["limiting_check"]["path"], expected)
                self.assertIsNone(result["limiting_check"]["face"])
                self.assertAlmostEqual(result["additional_clearance_m"], .00003, delta=1e-15)
