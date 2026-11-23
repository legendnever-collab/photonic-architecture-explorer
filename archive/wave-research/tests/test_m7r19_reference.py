import unittest

import numpy as np

from scripts import m7r19_capture as capture
from scripts import m7r19_reference as reference


class OpenFacetReference(unittest.TestCase):
    def test_vector_guided_mode_satisfies_dielectric_interface(self):
        beta, mode = capture.guided_mode()
        self.assertLess(capture.NCL, beta / capture.K)
        self.assertLess(beta / capture.K, capture.NCO)
        inner, outer = mode([capture.A - 1e-9, capture.A + 1e-9])
        np.testing.assert_allclose(inner[1:], outer[1:], rtol=1e-8)
        np.testing.assert_allclose(
            inner[0] * capture.NCO**2, outer[0] * capture.NCL**2, rtol=1e-8
        )

    def test_linear_reconstruction_and_common_phase_scale(self):
        r = (np.arange(16) + 0.5) / 4
        radial = np.ones((len(r), 1)) * np.array([1, 1j, 0, -1j, 1, 0])
        field, _ = reference.grid_field(radial * np.exp(0.7j), r, 0.5)
        np.testing.assert_allclose(field[[1, 2, 3, 5]], 0, atol=1e-13)
        np.testing.assert_allclose(field[0], field[4])
        self.assertTrue(np.all(field[0].real >= 0))
        self.assertLess(np.max(abs(field[0].imag)), 1e-13)
        self.assertAlmostEqual(reference.radial_flux(radial, r), np.pi * 4**2 / 2)

    def test_archived_straight_control_and_power_ledger(self):
        root = capture.ROOT / "references/m7r19"
        with (
            np.load(root / "facet12.npz") as facet,
            np.load(root / "straight12.npz") as straight,
        ):
            ctrl = reference.controls(straight, facet)
        self.assertLess(ctrl["closed_monitor_balance_abs"], 5e-5)
        self.assertGreater(ctrl["straight_transverse_error"]["H"], 0.04)
        self.assertGreater(ctrl["air_export_vs_native_rel"], 0.04)
