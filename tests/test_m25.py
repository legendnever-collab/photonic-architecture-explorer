"""Independent mode-domain references and evidence semantics, no new solver."""

import copy
import json
import math
from pathlib import Path
import unittest
import numpy as np
from photonic_architecture_explorer.applicability import gaussian_port_domain, residual_scale_comparison


class ExternalDomainReferences(unittest.TestCase):
    def test_fft_angular_moments_independent_of_q_kernel(self):
        # 2*rms transverse wavevector/k equals Gaussian 1/e^2 angular width.
        # Manual complex fields and FFT, no production axis_field/propagate.
        for n, w, c in [(1., 8e-6, 0.), (1., 12e-6, 3000.), (1.45, 10e-6, -2000.)]:
            wavelength = 1.31e-6
            estimates = []
            for size in (2048, 4096):
                dx = 24*w/size
                x = (np.arange(size)-size//2)*dx
                k = 2*np.pi*n/wavelength
                field = np.exp(-x*x/(w*w)-0.5j*k*c*x*x)
                power = np.abs(np.fft.fft(field))**2
                kt = 2*np.pi*np.fft.fftfreq(size, d=dx)
                estimates.append(2*np.sqrt(np.sum(power*kt*kt)/np.sum(power))/k)
            result = gaussian_port_domain(wavelength, n, (2*w, 2*w), (c, c))
            predicted = result['axes'][0]['divergence_rad']
            self.assertAlmostEqual(estimates[-1]/predicted, 1., places=11)
            self.assertLess(abs(estimates[0]-estimates[1]), 1e-12)

    def test_independent_phase_width_formula_and_nonwaist_rejection(self):
        # Derived directly from Fourier moments: theta^2=(lambda/pi/n/w)^2+(C*w)^2.
        w, c, wave, n = 10e-6, 15000., 1.31e-6, 1.
        expected = math.hypot(wave/(math.pi*n*w), c*w)
        mode = gaussian_port_domain(wave, n, (2*w, 2*w), (c, c))
        self.assertAlmostEqual(mode['axes'][0]['divergence_rad'], expected)
        self.assertEqual(mode['status'], 'Fail')
        self.assertEqual(gaussian_port_domain(wave, n, (2*w, 2*w), (0., 0.))['status'], 'Pass')

    def test_waist_guard_boundary_and_index_scaling(self):
        for n in (1., 1.45):
            threshold = 2*1.31e-6/(math.pi*n*.1)
            for scale, expected in ((.999, 'Fail'), (1.001, 'Pass')):
                result = gaussian_port_domain(1.31e-6, n, (threshold*scale,)*2, (0., 0.))
                self.assertEqual(result['status'], expected)

    def test_missing_and_invalid_do_not_become_performance(self):
        args = [1.31e-6, 1., [16e-6, 24e-6], [0., 0.]]
        for index in range(4):
            missing = copy.deepcopy(args); missing[index] = None
            self.assertEqual(gaussian_port_domain(*missing)['status'], 'Uncomputed')
        for index, value in [(0, float('nan')), (1, 0.), (2, [0., 1e-5]), (3, [float('inf'), 0.])]:
            invalid = copy.deepcopy(args); invalid[index] = value
            result = gaussian_port_domain(*invalid)
            self.assertEqual(result['status'], 'Fail')
            self.assertNotIn('normalized_mode_overlap', result)
        self.assertEqual(gaussian_port_domain(1.31e-6, 1., [None, 24e-6], [0., 0.])['status'], 'Uncomputed')

    def test_residual_scale_is_not_loss_and_inputs_are_preserved(self):
        widths = [8e-6, 12e-6]; before = widths.copy()
        result = residual_scale_comparison(2.6796482990801002e-6, widths)
        self.assertAlmostEqual(result['norm_over_axis_radius'][0], .3349560373850125)
        self.assertEqual(widths, before)
        self.assertNotIn('normalized_mode_overlap', result)
        self.assertEqual(residual_scale_comparison(None, widths)['status'], 'Uncomputed')

    def test_blank_actual_sheet_keeps_every_physical_input_unprovided(self):
        root = Path(__file__).resolve().parents[1]
        sheet = json.loads((root/'examples/external_ports_unprovided.json').read_text())
        def check(value):
            if isinstance(value, dict) and 'provenance' in value:
                self.assertEqual(value['provenance'], 'unprovided')
                self.assertIsNone(value['value'])
            elif isinstance(value, dict):
                for item in value.values(): check(item)
            elif isinstance(value, list):
                for item in value: check(item)
        check(sheet)


if __name__ == '__main__':
    unittest.main()
