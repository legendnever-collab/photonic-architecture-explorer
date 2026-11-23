import json
import unittest

from photonic_architecture_explorer.confidence import render_confidence
from photonic_architecture_explorer.design import design_two_ports
from photonic_architecture_explorer.inspector import ROOT
from photonic_architecture_explorer.tutorial import render_tutorial


class EvidenceScopeTests(unittest.TestCase):
    def test_tutorial_tracks_archived_results_and_guide_stop(self):
        html = render_tutorial()
        archived = json.loads((ROOT / "references/m7r6/design_summary.json").read_text())
        selected = next(c for c in archived["candidates"] if c["id"] == archived["selected"])
        self.assertIn(archived["input_sha256"], html)
        self.assertIn(f'{selected["overlap"]:.8f}', html)
        control = json.loads((ROOT / "references/m7r20/summary.json").read_text())
        self.assertEqual(control["guide_input_field_within_limit"], {"E": False, "H": False})
        self.assertIn("Facet 재계산은 보류", html)
        self.assertIn("Model Domain은 Fail", html)

    def test_live_candidate_is_scoped_to_current_input_and_guard(self):
        ports = json.loads((ROOT / "examples/m5a_two_ports.json").read_text())
        original = design_two_ports(ports)
        ports["target"]["position_m"]["value"][2] += 1e-4
        ports["target"]["reference_plane"]["value"]["origin_m"][2] += 1e-4
        edited = design_two_ports(ports)
        self.assertNotEqual(original["input_sha256"], edited["input_sha256"])
        for candidate in edited["candidates"]:
            panel = render_confidence(candidate, edited["input_sha256"])
            self.assertIn(edited["input_sha256"], panel)
            self.assertNotIn(original["input_sha256"], panel)
            self.assertNotIn("G036-NM", panel)
            self.assertEqual(panel.count("scope='row'"), 9)
        self.assertTrue(edited["candidates"])
        candidate = edited["candidates"][0]
        candidate["evaluation"]["model_domain"]["status"] = "Fail"
        panel = render_confidence(candidate, edited["input_sha256"])
        self.assertIn("Fail", panel)
        self.assertNotIn("η =", panel)
