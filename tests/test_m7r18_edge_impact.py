import unittest

import numpy as np

from scripts import m7r18_edge_impact as impact


class SourceEdgeImpact(unittest.TestCase):
    def test_strip_union_has_exact_projected_area_including_each_corner_once(self):
        normal = (
            np.array(impact.r17.M1["illuminated_normal"]["value"]) @ impact.r17.BASIS.T
        )
        width = 16 * impact.WAVELENGTH
        projected = []
        for side in impact.SIDES:
            _, area = impact.strip_nodes(side, width, 16, 2)
            projected.append(-area.sum(axis=0) @ normal)
        u, v = impact.HALF_U, impact.HALF_V
        np.testing.assert_allclose(
            projected, [2 * v * width] * 2 + [2 * (u - width) * width] * 2
        )
        self.assertAlmostEqual(
            sum(projected), 4 * (u * v - (u - width) * (v - width)), places=18
        )

    def test_saved_edge_fields_replay_on_four_sides_and_shared_corners(self):
        ref = impact.r17.ROOT / "references/m7r18/edge_fields.npz"
        with np.load(ref) as saved:
            points = saved["points_tsd_m"][:, [0, 32, 64]]
            stored = saved["fields_E_Z0H"][:, [0, 32, 64]]
        field, _ = impact.r17.source(impact.r17.REF / "source48.npz", impact.PITCH)
        actual = impact.r17.direct(field, impact.PITCH, points.reshape(-1, 3))
        np.testing.assert_allclose(actual, stored.reshape(-1, 6), rtol=1e-9, atol=1e-13)
        np.testing.assert_allclose(stored[0, 0], stored[2, 0])
        np.testing.assert_allclose(stored[1, 2], stored[3, 2])
