import unittest

import numpy as np

from scripts import m7r17_source as source
from scripts import m7r17_edge as edge


class FiniteEdgeReference(unittest.TestCase):
    def test_sommerfeld_total_field_satisfies_both_pec_conditions(self):
        x = np.array([0.5, 2.0, 7.0])
        k = 2 * np.pi

        def total(z, sign):
            incident = np.exp(-1j * k * (edge.SIN * x - edge.COS * z))
            return edge.sommerfeld(x, z, k, sign) + incident

        np.testing.assert_allclose(total(0, -1), 0, atol=1e-12)
        h = 1e-4
        derivative = (-3 * total(0, 1) + 4 * total(h, 1) - total(2 * h, 1)) / (2 * h)
        self.assertLess(np.max(abs(derivative)) / k, 1e-6)

    def test_frozen_huygens_fields_replay_at_common_receivers(self):
        pts, weights = source.receivers(28)
        selection = [57, 291, 391, 601]
        data, _ = source.source(source.REF / "source48.npz", 0.5e-6)
        field = source.direct(data, 0.5e-6, pts[selection])
        with np.load(source.REF / "m1.npz") as stored:
            np.testing.assert_allclose(
                field, stored["fields_32_40_48"][2, selection], rtol=2e-10, atol=1e-13
            )
            np.testing.assert_allclose(weights, stored["incident_area_vectors_m2"])
