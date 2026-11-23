"""Lifecycle checks for the isolated trial, without optional optimizer dependencies."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("m7c_trial_test", ROOT / "scripts/m7c_workflow_trial.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)
from photonic_architecture_explorer import near_match as trial


def fixture(name):
    return json.loads((ROOT / "examples" / name).read_text())


class WorkflowTrialTests(unittest.TestCase):
    def test_exact_frozen_results_are_unchanged_and_never_start_fallback(self):
        for name, state in (("m5a_two_ports.json", "NotNeeded"),
                            ("m5f_different_q.json", "NotNeeded"),
                            ("m5f_high_divergence.json", "Ineligible")):
            document = fixture(name)
            original = copy.deepcopy(document)
            expected = trial.design_two_ports(document)
            with patch.object(trial, "search_near_match", side_effect=AssertionError("unexpected fallback")) as search:
                report = trial.run_workflow(document)
            self.assertEqual(report["state"], state)
            self.assertEqual(report["exact_result"], expected)
            self.assertEqual(report["design_result"], expected)
            self.assertEqual(document, original)
            search.assert_not_called()

    def test_missing_phase_and_skew_remain_ineligible(self):
        missing = fixture("m7a_smf_glass_proxy.json")
        del missing["target"]["wavefront_curvature_ts_per_m"]
        skew = fixture("m7a_smf_glass_proxy.json")
        skew["target"]["position_m"]["value"][1] = .001
        for document in (missing, skew, None):
            with patch.object(trial, "search_near_match") as search:
                report = trial.run_workflow(document)
            self.assertEqual(report["state"], "Ineligible")
            self.assertFalse(report["design_result"]["candidates"])
            search.assert_not_called()

    def test_cancelled_before_start_does_not_evaluate_inputs(self):
        with patch.object(trial, "design_two_ports") as exact:
            report = trial.run_workflow(None, cancelled=lambda: True)
        self.assertEqual(report["state"], "Cancelled")
        self.assertIsNone(report["design_result"])
        exact.assert_not_called()

    def test_cancel_during_fallback_keeps_partial_evidence_out_of_recommendation(self):
        flag = [False]
        def partial(document, exact, report, checkpoint, progress):
            report["fallback"]["adapter_calls"] = 1
            progress({"completed_geometries": 0})
            flag[0] = True
            checkpoint()
        with patch.object(trial, "search_near_match", side_effect=partial):
            report = trial.run_workflow(fixture("m7a_smf_glass_proxy.json"), cancelled=lambda: flag[0])
        self.assertEqual(report["state"], "Cancelled")
        self.assertIsNone(report["design_result"])
        self.assertEqual(report["fallback"]["adapter_calls"], 1)
        self.assertNotIn('data-candidate=', cli.render_trial(report))

    def test_timeout_and_independent_check_failure_withhold_results(self):
        now = [0.]
        def timeout(document, exact, report, checkpoint, progress):
            now[0] = 601.
            checkpoint()
        for action, state in ((timeout, "TimedOut"), (AssertionError("quadrature mismatch"), "Failed")):
            now[0] = 0.
            with patch.object(trial, "search_near_match", side_effect=action):
                report = trial.run_workflow(fixture("m7a_smf_glass_proxy.json"), clock=lambda: now[0])
            self.assertEqual(report["state"], state)
            self.assertIsNone(report["design_result"])

    def test_exhausted_search_is_no_candidate_not_impossibility(self):
        empty = trial.design_two_ports(fixture("m7a_smf_glass_proxy.json"))
        with patch.object(trial, "search_near_match", return_value=empty):
            report = trial.run_workflow(fixture("m7a_smf_glass_proxy.json"))
        self.assertEqual(report["state"], "NoCandidate")
        self.assertIsNone(report["design_result"]["selected_candidate_id"])

    def test_output_directory_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sys, "argv", ["trial", "missing.json", "--output-dir", directory]):
                with self.assertRaises(FileExistsError):
                    cli.main()

    def test_changed_execution_source_prevents_publication(self):
        before = {"source_sha256": {"worker": "before"}, "contract_sha256": "contract"}
        after = {**before, "source_sha256": {"worker": "after"}}
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "fresh"
            argv = ["trial", str(ROOT / "examples/m5a_two_ports.json"), "--output-dir", str(target)]
            with patch.object(sys, "argv", argv), patch.object(cli, "provenance", side_effect=[before, after]):
                with patch("sys.stdout", new=io.StringIO()):
                    self.assertEqual(cli.main(), 1)
            report = json.loads((target / "trial.json").read_text())
            self.assertEqual(report["state"], "Failed")
            self.assertIsNone(report["design_result"])
            self.assertNotIn('data-candidate=', (target / "trial.html").read_text())


if __name__ == "__main__":
    unittest.main()
