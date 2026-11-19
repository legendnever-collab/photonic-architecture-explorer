import json
import unittest

import numpy as np

from scripts.m7r5_fit import REFERENCE, fit, replay


class SinglePortReferenceTests(unittest.TestCase):
    def test_signed_curvature_and_orthogonal_polarization(self):
        case = json.loads((REFERENCE / "case.json").read_text())
        axis = np.arange(-16.0, 16.0, 0.25)
        x, y = axis[:, None], axis[None, :]
        k = 2 * np.pi / case["vacuum_wavelength_um"]
        g = np.exp(
            -((x / 3.0) ** 2)
            - (y / 4.0) ** 2
            - 0.5j * k * (0.01 * x**2 - 0.02 * y**2)
            + 0.73j
        )
        result = fit(axis, (g, 0.2j * g, 0 * g), case)
        self.assertAlmostEqual(result["eta_transverse"], 1 / 1.04, places=10)
        np.testing.assert_allclose(result["MFD_um_xy"], [6, 8], rtol=1e-6)
        np.testing.assert_allclose(result["curvature_per_m_xy"], [1e4, -2e4], rtol=1e-5)
        self.assertLess(result["phase_rms_rad"], 1e-6)

    def test_captured_case(self):
        expected = json.loads((REFERENCE / "result.json").read_text())
        actual = replay(REFERENCE)
        self.assertEqual(
            actual["nominal_simulated_fit"], expected["nominal_simulated_fit"]
        )
        for name, run in actual["runs"].items():
            self.assertEqual(run["sha256"], expected["runs"][name]["sha256"])
            self.assertAlmostEqual(
                run["eta_transverse"],
                expected["runs"][name]["eta_transverse"],
                places=8,
            )
            self.assertAlmostEqual(
                run["phase_rms_rad"], expected["runs"][name]["phase_rms_rad"], places=6
            )
        for key in ("actual_device_fit", "two_port_overlap", "total_coupling"):
            self.assertIsNone(actual[key])


if __name__ == "__main__":
    unittest.main()
