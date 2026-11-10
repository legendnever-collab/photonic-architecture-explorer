"""Literature proxy data contract and honest high-divergence result gate."""

import copy
import json
import math
from pathlib import Path
import unittest

from photonic_architecture_explorer.external import evaluate_external
from photonic_architecture_explorer.applicability import gaussian_port_domain
from photonic_architecture_explorer.inspector import render_report

ROOT = Path(__file__).resolve().parents[1]


class LiteratureProxy(unittest.TestCase):
    def test_waft_pic_side_axes_assumptions_and_domain_withholding(self):
        data = json.loads((ROOT/'examples/m4b_literature_proxy.json').read_text())
        before = copy.deepcopy(data)
        self.assertEqual(data['wavelength_m']['value'], 1310e-9)
        self.assertEqual(data['ambient_index']['value'], 1.)  # never use guided n_eff
        for label in ('source', 'target'):
            port = data[label]
            self.assertEqual(port['mfd_ts_m']['value'], [2.73e-6, 3.79e-6])  # vertical t, horizontal s
            self.assertEqual(port['mfd_ts_m']['provenance'], 'assumed')
            self.assertEqual(port['wavefront_curvature_ts_per_m']['provenance'], 'assumed')
            self.assertEqual(port['mode_evidence']['value']['kind'], 'gaussian_assumption')
            self.assertNotIn('complex_q_ts_m', port)  # no stale M1 q after changing widths
            pre = gaussian_port_domain(1310e-9, 1., port['mfd_ts_m']['value'], [0., 0.])
            self.assertEqual(pre['status'], 'Fail')
            for axis, diameter in zip(pre['axes'], (2.73e-6, 3.79e-6)):
                independent = 2*1310e-9/(math.pi*diameter)
                self.assertAlmostEqual(axis['divergence_rad'], independent, places=14)
                self.assertGreater(independent, .1)
        result = evaluate_external(data)
        self.assertEqual(result['input_contract']['status'], 'Pass')
        self.assertEqual(result['geometry']['status'], 'Pass')
        self.assertEqual(result['design_constraints']['status'], 'Pass')
        self.assertEqual(result['package_feasibility']['envelope_geometry']['status'], 'Pass')
        self.assertEqual(result['model_domain']['status'], 'Fail')
        self.assertIn('0.1 rad', result['model_domain']['reason'])
        self.assertIsNone(result['gaussian_mode_matching']['normalized_mode_overlap'])
        self.assertIsNone(result['physical_losses']['total_coupling'])
        self.assertEqual(result['package_feasibility']['status'], 'Uncomputed')
        self.assertEqual(result['actual_applicability']['status'], 'Uncomputed')
        self.assertEqual(data, before)
        self.assertEqual(result['input_snapshot'], data)
        for label in ('source', 'target'):
            self.assertEqual(result['evaluated_ports'][label]['position_m'], tuple(data[label]['position_m']['value']))
            self.assertEqual(result['evaluated_ports'][label]['direction'], tuple(data[label]['propagation_direction']['value']))
        page = render_report([('literature', 'Literature proxy', data)])
        self.assertNotIn('data-overlap-value=', page)
        self.assertIn('data-overlap-withheld', page)


if __name__ == '__main__': unittest.main()
