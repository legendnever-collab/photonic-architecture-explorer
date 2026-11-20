"""Small controls for the reference quadrature; no relay run in CI."""
import unittest

import numpy as np
from numpy.polynomial.legendre import leggauss

from scripts import m7r12_filon as filon
from scripts import m7r12_quadrature as ref


class CurvedQuadratureControls(unittest.TestCase):
    def test_filon_cardinals_at_both_frequency_signs(self):
        n = 8
        nodes, _ = leggauss(n)
        fine, weights = leggauss(128)
        alpha = np.array([-42.5, -0.1, 0.0, 0.1, 42.5])
        coeff = filon.fitted_weights(n, alpha)
        for degree in range(n):
            direct = np.exp(-1j*alpha[:, None]*fine) @ (weights*fine**degree)
            np.testing.assert_allclose(coeff @ nodes**degree, direct, atol=3e-14, rtol=0)

    def test_edge_splits_preserve_measure_and_interior(self):
        half = 0.000751
        order = 6
        initial, _ = ref.axis(half, order, 1)
        for split in (1, 2, 4):
            u, weights = ref.axis(half, order, split)
            np.testing.assert_array_equal(u[order*split:-order*split], initial[order:-order])
            self.assertAlmostEqual(weights.sum()/(2*half), 1.0)
            self.assertAlmostEqual(np.dot(weights, u**2)/(2*half**3/3), 1.0)
            self.assertTrue(np.all((abs(u) < half) & (weights > 0)))
