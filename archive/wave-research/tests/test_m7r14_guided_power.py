import unittest

import numpy as np

from scripts import m7r14_guided_power as ref


class GuidedPowerControls(unittest.TestCase):
    def test_circular_mode_uses_bilinear_reverse_field(self):
        e = np.array([1, 1j]) / np.sqrt(2)
        h = np.array([-e[1], e[0]]) / ref.Z0
        power = 0.5 / ref.Z0  # unit area
        for reverse_e, reverse_h, expected in [
            (e.conj(), -h.conj(), 1), (e, -h, 0)
        ]:
            actual = ref.projected_fraction(e, h, reverse_e, reverse_h, 1, power, power)
            self.assertAlmostEqual(actual, expected, places=12)

    def test_archived_scalar_fields_preserve_uncomputed_gate(self):
        result = ref.review()
        self.assertEqual(result["status"], "Uncomputed")
        self.assertIsNone(result["nominal_guided_fraction"])
        self.assertIsNone(result["nominal_absolute_uncertainty"])
