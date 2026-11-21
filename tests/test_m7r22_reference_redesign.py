import unittest

from photonic_architecture_explorer.design import design_two_ports
from photonic_architecture_explorer.reference_redesign import (
    ENTRY, nominal_exact_matches, nominal_replay_matches, reference_context,
)
from photonic_architecture_explorer.workspace import (
    Workspace, build_document, initial_values, resolve_coordinates,
)


class ReferenceRedesignTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Workspace()
        self.original = self.workspace.templates[ENTRY]
        self.summary = self.workspace.r6_summary
        self.raw = initial_values(self.original, ENTRY)

    def test_form_round_trip_retains_all_records_and_frozen_hash(self):
        submitted = build_document(self.original, self.raw)
        resolve_coordinates(submitted)
        self.assertEqual(submitted, self.original)
        result = design_two_ports(submitted)
        self.assertTrue(nominal_exact_matches(result, self.summary))
        self.assertEqual(reference_context(self.original, submitted, self.summary)["scope"], "Original")

    def test_single_position_edit_preserves_unedited_port_and_field_values(self):
        self.raw["target_position_m_2"] = "2.1"
        submitted = build_document(self.original, self.raw)
        resolve_coordinates(submitted)
        self.assertEqual(submitted["source"], self.original["source"])
        target = submitted["target"]
        self.assertEqual(target["position_m"]["value"], [0.002, 0, 0.0021])
        self.assertEqual(target["reference_plane"]["value"]["origin_m"], [0.002, 0, 0.0021])
        self.assertEqual(target["mfd_ts_m"], self.original["target"]["mfd_ts_m"])
        self.assertEqual(target["mode_evidence"]["value"]["kind"], "gaussian_assumption")
        context = reference_context(self.original, submitted, self.summary)
        self.assertEqual(context["changed_fields"], ["Target Position"])
        self.assertEqual(context["scope"], "Edited")
        self.assertNotEqual(design_two_ports(submitted)["input_sha256"], self.summary["input_sha256"])

    def test_replay_gate_withholds_wrong_candidate_or_bad_quadrature(self):
        benchmark = self.summary["candidates"][0]
        eta = benchmark["overlap"]
        candidate = {"id": benchmark["id"],
                     "evaluation": {"gaussian_mode_matching": {"normalized_mode_overlap": eta}},
                     "independent_validation": {"status": "Pass", "quadrature_overlap": [eta, eta]}}
        result = {"selected_candidate_id": benchmark["id"], "candidates": [candidate]}
        self.assertTrue(nominal_replay_matches(result, self.summary))
        candidate["independent_validation"]["quadrature_overlap"][1] += 2e-8
        self.assertFalse(nominal_replay_matches(result, self.summary))
        result["selected_candidate_id"] = "other"
        self.assertFalse(nominal_replay_matches(result, self.summary))
