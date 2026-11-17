"""Workspace translation and missing-data regressions."""

import copy
import json
import unittest

from photonic_architecture_explorer.design import design_two_ports
from photonic_architecture_explorer.external import InputIssue
from photonic_architecture_explorer.workspace import (
    Workspace, build_document, initial_values, resolve_coordinates,
)


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

    def round_input(self):
        self.blank = self.workspace.templates["blank"]
        raw = initial_values(self.blank, "blank")
        raw.update(wavelength_m_0="1310", ambient_index_0="1")
        for name, position, phase in (("source", (0, 0, 0), "50"), ("target", (2, 2, 0), "-50")):
            for key, values in (("position_m", position), ("propagation_direction", (1, 0, 0))):
                for i, value in enumerate(values):
                    raw[f"{name}_{key}_{i}"] = str(value)
            raw[f"{name}_mfd_ts_m_0"] = "20"
            raw[f"{name}_wavefront_curvature_ts_per_m_0"] = phase
        return raw

    def test_round_modes_derive_unique_plane_and_reproduce_explicit_design(self):
        raw = self.round_input()
        inferred = build_document(self.blank, raw)
        resolve_coordinates(inferred)
        for name, phase in (("source", 50), ("target", -50)):
            port = inferred[name]
            self.assertEqual(port["sagittal_axis"]["value"], [0., 0., 1.])
            self.assertIn("Derived by Workspace", port["sagittal_axis"]["source"])
            self.assertEqual(port["wavefront_curvature_ts_per_m"]["value"], [phase] * 2)
            plane = port["reference_plane"]
            self.assertEqual(plane["value"]["origin_m"], port["position_m"]["value"])
            self.assertEqual(plane["value"]["normal"], port["propagation_direction"]["value"])
            self.assertIn("origin_m = position_m", plane["source"])
            raw.update({f"{name}_sagittal_axis_{i}": str(v) for i, v in enumerate((0, 0, 1))})
        explicit = build_document(self.blank, raw)
        resolve_coordinates(explicit)
        automatic, manual = design_two_ports(inferred), design_two_ports(explicit)
        self.assertEqual(automatic["status"], "Computed")
        self.assertEqual(automatic["selected_candidate_id"], "G008-B1")
        self.assertEqual(automatic["search"], manual["search"])
        self.assertNotEqual(automatic["input_sha256"], manual["input_sha256"])
        for auto, hand in zip(automatic["candidates"], manual["candidates"], strict=True):
            self.assertEqual(auto["id"], hand["id"])
            for key in ("geometry", "model_domain", "gaussian_mode_matching", "evaluated_ports"):
                self.assertEqual(auto["evaluation"][key], hand["evaluation"][key])
            for name in ("source", "target"):
                self.assertEqual(auto["prescription"][name], inferred[name])
        self.assertIsNone(self.blank["source"]["sagittal_axis"]["value"])

    def test_coordinate_gate_reports_anisotropy_skew_roll_and_ambiguity_separately(self):
        for changes, status, reason in (
            ({"source_mode": "mfd", "source_mfd_ts_m_1": "24",
              "source_wavefront_curvature_ts_per_m_1": "50"}, "Uncomputed", "Elliptical"),
            ({"source_mode": "mfd", "source_mfd_ts_m_1": "20",
              "source_wavefront_curvature_ts_per_m_1": "55"}, "Uncomputed", "Astigmatic"),
            ({"target_position_m_1": "0"}, "Uncomputed", "Ambiguous Fold Plane"),
            ({"target_propagation_direction_0": "0",
              "target_propagation_direction_2": "1"}, "Fail", "Skew"),
            ({"source_sagittal_axis_0": "0", "source_sagittal_axis_1": "1",
              "source_sagittal_axis_2": "0"}, "Fail", "Rolled"),
            ({"target_propagation_direction_0": "0"}, "Fail", "unit vector"),
            ({"source_wavefront_curvature_ts_per_m_0": ""}, "Uncomputed", "Wavefront Phase"),
        ):
            with self.subTest(reason=reason):
                raw = self.round_input()
                raw.update(changes)
                document = build_document(self.blank, raw)
                with self.assertRaisesRegex(InputIssue, reason) as context:
                    resolve_coordinates(document)
                self.assertEqual(context.exception.status, status)
                self.assertIsNone(document["target"]["sagittal_axis"]["value"])

    def test_retains_explicit_q_phase_frame_and_axis_metadata(self):
        document = copy.deepcopy(self.example)
        for name in ("source", "target"):
            port = document[name]
            port["reference_plane"]["value"].update(frame_id="package-frame", id=f"{name}-plane")
            q = port["complex_q_ts_m"] = copy.deepcopy(port["mfd_ts_m"])
            q["value"] = [[0.0, 0.0001534823891830128], [0.0, 0.00034533537566177886]]
        edited = build_document(document, initial_values(document, "example"))
        resolve_coordinates(edited)
        self.assertEqual(edited, document)
        self.assertEqual(design_two_ports(edited)["status"], "Computed")

    def test_oblique_round_q_preserves_explicit_axis_sign(self):
        raw = self.round_input()
        raw.update(target_position_m_1="1.2", target_position_m_2="1.6",
                   source_mode="q", source_complex_q_ts_m_0="-0.02", source_complex_q_ts_m_1="0.24",
                   source_complex_q_ts_m_2="-0.02", source_complex_q_ts_m_3="0.24",
                   target_sagittal_axis_0="0", target_sagittal_axis_1="-0.8",
                   target_sagittal_axis_2="0.6")
        document = build_document(self.blank, raw)
        resolve_coordinates(document)
        self.assertEqual(document["source"]["sagittal_axis"]["value"], [0, -0.8, 0.6])
        self.assertEqual(document["target"]["sagittal_axis"]["source"],
                         "User input in Two-Port Workspace")
        self.assertEqual(document["source"]["complex_q_ts_m"]["value"],
                         [[-0.00002, 0.00024]] * 2)
