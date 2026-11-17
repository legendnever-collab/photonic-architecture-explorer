"""Workspace translation and missing-data regressions."""

import copy
import json
import unittest

from photonic_architecture_explorer.design import design_two_ports
from photonic_architecture_explorer.workspace import Workspace, build_document, initial_values


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Workspace()
        self.example = self.workspace.templates["example"]
        self.raw = initial_values(self.example, "example")

    def test_example_submits_exact_fixed_ports_and_no_implicit_design(self):
        before = copy.deepcopy(self.example)
        self.assertNotIn('id="design-review"', self.workspace.get("example"))
        document = build_document(self.example, self.raw)
        self.assertEqual(document, before)
        result = design_two_ports(document)
        self.assertEqual(result["status"], "Computed")
        for candidate in result["candidates"]:
            for name in ("source", "target"):
                self.assertEqual(candidate["prescription"][name], before[name])
        self.assertEqual(self.example, before)

    def test_port_edit_updates_reference_plane_and_retains_unedited_port(self):
        self.raw["target_position_m_2"] = "2.2"
        document = build_document(self.example, self.raw)
        target = document["target"]
        self.assertEqual(document["source"], self.example["source"])
        self.assertEqual(target["position_m"]["value"], [0.002, 0, 0.0022])
        self.assertEqual(target["reference_plane"]["value"]["origin_m"], target["position_m"]["value"])
        self.assertEqual(target["position_m"]["provenance"], "supplied")
        self.assertEqual(target["mode_evidence"]["value"]["kind"], "gaussian_assumption")
        self.assertEqual(design_two_ports(document)["input_snapshot"], document)

    def test_phase_absence_stays_uncomputed_and_q_is_explicit(self):
        self.raw["source_wavefront_curvature_ts_per_m_0"] = ""
        self.raw["source_wavefront_curvature_ts_per_m_1"] = ""
        result = design_two_ports(build_document(self.example, self.raw))
        self.assertEqual(result["status"], "Uncomputed")
        self.assertEqual(result["candidates"], [])
        self.raw["source_mode"] = "q"
        for index, value in enumerate(("0", "0.153484", "0", "0.345337")):
            self.raw[f"source_complex_q_ts_m_{index}"] = value
        document = build_document(self.example, self.raw)
        self.assertEqual(document["source"]["complex_q_ts_m"]["value"],
                         [[0, 0.000153484], [0, 0.000345337]])
        self.assertNotIn("wavefront_curvature_ts_per_m", document["source"])
        self.assertEqual(design_two_ports(document)["input_contract"]["status"], "Pass")

    def test_new_input_and_failed_value_never_inherit_synthetic_data(self):
        blank = self.workspace.templates["blank"]
        raw = initial_values(blank, "blank")
        document = build_document(blank, raw)
        self.assertEqual(design_two_ports(document)["status"], "Uncomputed")
        self.assertIsNone(document["wavelength_m"]["value"])
        for name in ("source", "target"):
            self.assertIsNone(document[name]["position_m"]["value"])
            self.assertIsNone(document[name]["wavefront_curvature_ts_per_m"]["value"])
        raw["source_position_m_0"] = '<script>alert(1)</script>'
        page, status = self.workspace.post(raw)
        self.assertEqual(status, 200)
        self.assertIn('role="alert"', page)
        self.assertNotIn('<script>alert(1)</script>', page)
        self.assertNotIn('id="design-review"', page)

    def test_workspace_engine_input_can_be_serialized_without_aliases(self):
        document = build_document(self.example, self.raw)
        snapshot = json.loads(json.dumps(document))
        document["source"]["position_m"]["value"][0] = 0.25
        self.assertEqual(self.example, snapshot)
