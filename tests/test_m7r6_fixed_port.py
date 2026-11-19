import json
import unittest

from photonic_architecture_explorer.design import design_two_ports
from photonic_architecture_explorer.external import adapt_ports
from scripts.m7r5_fit import replay
from scripts.m7r6_fixed_port import GLASS, ROOT, SMF, build_document


class SmfGlassFixedPortTests(unittest.TestCase):
    def test_capture_fit_and_reciprocal_input(self):
        expected = json.loads((SMF / "fit.json").read_text(encoding="utf-8"))
        smf = replay(SMF, SMF / "case.json")
        self.assertEqual(smf["nominal_simulated_fit"], "Pass")
        self.assertEqual(smf["fitted_port_divergence"]["status"], "Pass")
        self.assertEqual(
            smf["runs"]["window"]["sha256"], expected["runs"]["window"]["sha256"]
        )
        self.assertAlmostEqual(
            smf["runs"]["window"]["eta_transverse"],
            expected["runs"]["window"]["eta_transverse"],
            places=8,
        )

        glass = json.loads((GLASS / "result.json").read_text(encoding="utf-8"))
        layout = json.loads((SMF / "layout.json").read_text(encoding="utf-8"))
        candidate_input = build_document(layout, expected, glass)
        fixture = json.loads(
            (ROOT / "examples/m7r6_smf_glass_1310.json").read_text(encoding="utf-8")
        )
        self.assertEqual(candidate_input, fixture)
        ports = adapt_ports(fixture)
        self.assertEqual(ports.source.position, tuple(layout["source"]["position_m"]))
        self.assertEqual(ports.target.position, tuple(layout["target"]["position_m"]))
        self.assertEqual(ports.target.direction, (1, 0, 0))
        for q, outward in zip(
            ports.target.mode.q, glass["fitted_port_divergence"]["axes"]
        ):
            emitted_q = complex(
                -outward["waist_distance_m"], outward["rayleigh_range_m"]
            )
            self.assertAlmostEqual(abs(q + emitted_q.conjugate()), 0.0, places=14)

        exact = design_two_ports(fixture)
        self.assertEqual(exact["search"]["status"], "Completed")
        self.assertEqual(exact["search"]["accepted_count"], 0)
        self.assertEqual(
            exact["search"]["rejection_counts"],
            {
                "model_domain: 3w projected footprint/curvature exceeds 0.15": 141,
                "model_domain: Gaussian divergence exceeds 0.1 rad": 3,
            },
        )
        self.assertIsNone(exact["physical_losses"]["total_coupling"])
