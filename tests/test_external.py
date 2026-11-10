"""M3-A independent conversions, fixed inputs and adversarial result gates."""

import copy
from dataclasses import FrozenInstanceError
import json
import math
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np
from photonic_architecture_explorer.benchmark import load_case
from photonic_architecture_explorer.external import adapt_external, evaluate_external
from photonic_architecture_explorer.geometry import Reflector
from photonic_architecture_explorer.package_geometry import patch_world_aabb, box_distance, segment_hits_box

ROOT = Path(__file__).resolve().parents[1]


def case():
    return json.loads((ROOT/'examples/m3a_synthetic.json').read_text())


def put(node, key, value):
    node[key]['value'] = value


def aabb(lo, hi):
    return {'type': 'aabb', 'min_m': lo, 'max_m': hi}


class ExternalAdapter(unittest.TestCase):
    def assert_withheld(self, result):
        self.assertIsNone(result['gaussian_mode_matching']['normalized_mode_overlap'])
        self.assertIsNone(result['physical_losses']['total_coupling'])
        json.dumps(result, allow_nan=False)

    def test_equivalence_immutable_ports_snapshot_and_roundtrip(self):
        data = case(); before = copy.deepcopy(data)
        adapted = adapt_external(data)
        old_source, old_target, old_mirrors = load_case(ROOT/'examples/m1_001.json')
        self.assertEqual((adapted.source, adapted.target), (old_source, old_target))
        for new, old in zip(adapted.reflectors, old_mirrors):
            self.assertEqual((new.vertex, new.curvatures, new.half_aperture), (old.vertex, old.curvatures, old.half_aperture))
            np.testing.assert_allclose(new.normal, old.normal, rtol=0, atol=1e-15)
        with self.assertRaises(FrozenInstanceError): adapted.target = old_source
        with self.assertRaises(FrozenInstanceError): adapted.target.position = (0, 0, 0)
        result = evaluate_external(data)
        self.assertEqual(result['gaussian_mode_matching']['status'], 'Approximate')
        self.assertAlmostEqual(result['gaussian_mode_matching']['normalized_mode_overlap'], 1.)
        self.assertEqual(result['input_snapshot'], data)
        self.assertEqual(data, before)
        self.assertEqual(adapt_external(json.loads(adapted.input_json)), adapted)
        data['target']['position_m']['value'][0] += 1
        self.assertEqual(adapted.target.position, old_target.position)
        self.assertEqual(json.loads(adapted.input_json), before)

    def test_independent_nonwaist_formula_mfd_phase_and_q_only(self):
        data = case(); wavelength = data['wavelength_m']['value']
        # Independent q=z+i*zR -> width from w0 sqrt(1+(z/zR)^2).
        q_values, widths, phase = [], [], []
        for z, zr in ((50e-6, 180e-6), (-70e-6, 300e-6)):
            q_values.append([z, zr])
            widths.append(2*math.sqrt(wavelength*zr/math.pi)*math.sqrt(1+(z/zr)**2))
            phase.append(z/(z*z+zr*zr))
        for port in ('source', 'target'):
            put(data[port], 'complex_q_ts_m', q_values)
            put(data[port], 'mfd_ts_m', widths)
            put(data[port], 'wavefront_curvature_ts_per_m', phase)
        redundant = adapt_external(data)
        for port in ('source', 'target'):
            del data[port]['complex_q_ts_m']
        mfd_only = adapt_external(data)
        np.testing.assert_allclose(mfd_only.source.mode.q, [complex(*q) for q in q_values], rtol=1e-13)
        for port in ('source', 'target'):
            data[port]['complex_q_ts_m'] = case()[port]['complex_q_ts_m']
            put(data[port], 'complex_q_ts_m', q_values)
            del data[port]['mfd_ts_m']; del data[port]['wavefront_curvature_ts_per_m']
        q_only = adapt_external(data)
        self.assertEqual(q_only.source.mode, redundant.source.mode)
        self.assertLess(q_only.source.mode.q_s.real, 0)

    def test_redundant_mode_mismatch_including_partial_inputs(self):
        for field, value in (('mfd_ts_m', [17e-6, 24e-6]),
                             ('wavefront_curvature_ts_per_m', [500., 0.])):
            for partial in (False, True):
                data = case(); put(data['target'], field, value)
                if partial:
                    del data['target']['wavefront_curvature_ts_per_m' if field == 'mfd_ts_m' else 'mfd_ts_m']
                result = evaluate_external(data)
                self.assertEqual(result['input_contract']['status'], 'Fail')
                self.assert_withheld(result)

    def test_missing_phase_q_or_partial_components_do_not_default(self):
        for change in ('phase', 'mode', 'component', 'q_component', 'ambient_identity', 'missing_target'):
            data = case()
            if change in ('phase', 'mode', 'component'):
                del data['source']['complex_q_ts_m']
                if change == 'component': put(data['source'], 'wavefront_curvature_ts_per_m', [None, 0.])
                else: del data['source']['wavefront_curvature_ts_per_m']
                if change == 'mode': del data['source']['mfd_ts_m']
            if change == 'q_component': put(data['source'], 'complex_q_ts_m', [[None, .001], [0, .001]])
            if change == 'ambient_identity': del data['ambient_index']['quantity']
            if change == 'missing_target': del data['target']
            result = evaluate_external(data)
            self.assertEqual(result['input_contract']['status'], 'Uncomputed', (change, result))
            self.assert_withheld(result)

    def test_invalid_units_provenance_nonfinite_and_unknown_fields(self):
        for change in ('mm', 'bad_provenance', 'no_source', 'nan', 'q_imag', 'boolean', 'unknown', 'bad_record'):
            data = case()
            if change == 'mm': data['source']['position_m']['unit'] = 'mm'
            if change == 'bad_provenance': data['wavelength_m']['provenance'] = 'typical'
            if change == 'no_source': data['ambient_index']['source'] = None
            if change == 'nan': put(data, 'wavelength_m', float('nan'))
            if change == 'q_imag': put(data['source'], 'complex_q_ts_m', [[0, -1e-4], [0, 1e-4]])
            if change == 'boolean': put(data, 'ambient_index', True)
            if change == 'unknown': data['source']['wavelength_m'] = data['wavelength_m']
            if change == 'bad_record': data['wavelength_m']['unit'] = []
            result = evaluate_external(data)
            self.assertEqual(result['input_contract']['status'], 'Fail', change)
            self.assert_withheld(result)

    def test_reference_plane_frame_axis_and_target_direction(self):
        for change in ('origin', 'side', 'frame', 'plane_normal', 'nonunit', 'nontransverse', 'incoming_direction'):
            data = case(); p = data['target']
            if change == 'origin': p['reference_plane']['value']['origin_m'][0] += 1e-6
            if change == 'side': p['reference_plane']['value']['side'] = 'guided'
            if change == 'frame': p['reference_plane']['value']['frame_id'] = 'another-frame'
            if change == 'plane_normal': p['reference_plane']['value']['normal'] = [-1, 0, 0]
            if change == 'nonunit': put(p, 'propagation_direction', [2, 0, 0])
            if change == 'nontransverse': put(p, 'sagittal_axis', [1, 0, 0])
            if change == 'incoming_direction':
                put(p, 'propagation_direction', [-1, 0, 0]); p['reference_plane']['value']['normal'] = [-1, 0, 0]
            result = evaluate_external(data)
            key = 'geometry' if change == 'incoming_direction' else 'input_contract'
            self.assertEqual(result[key]['status'], 'Fail', change)
            self.assert_withheld(result)

    def test_polarization_assumption_and_external_ambient_identity(self):
        for change in ('Jones_only', 'zero_jones', 'guided_index'):
            data = case()
            if change == 'Jones_only': del data['source']['polarization']['value']['treatment']
            if change == 'zero_jones': data['source']['polarization']['value']['jones_ts'] = [[0, 0], [0, 0]]
            if change == 'guided_index': data['ambient_index']['quantity'] = 'guided_effective_index'
            result = evaluate_external(data)
            self.assertEqual(result['input_contract']['status'], 'Fail')
            self.assert_withheld(result)
        data = case(); data['source']['position_m']['uncertainty'] = {'sigma_m': 1e-6, 'distribution': 'unspecified'}
        result = evaluate_external(data)
        self.assertEqual(result['input_snapshot']['source']['position_m']['uncertainty'], data['source']['position_m']['uncertainty'])
        self.assertEqual(result['fabrication']['status'], 'Uncomputed')

    def test_geometry_closure_and_exactly_two_reflectors(self):
        for change in ('count', 'moved_vertex', 'unsupported_surface'):
            data = case()
            if change == 'count': data['design']['reflectors'].pop()
            if change == 'moved_vertex': data['design']['reflectors'][0]['vertex_m']['value'][2] += 1e-6
            if change == 'unsupported_surface': put(data['reflectors'][0], 'surface_prescription', 'sphere')
            result = evaluate_external(data)
            self.assertEqual(result['input_contract' if change != 'moved_vertex' else 'geometry']['status'], 'Fail')
            self.assert_withheld(result)
            if change == 'moved_vertex': self.assertEqual(result['evaluated_ports']['target']['position_m'], tuple(case()['target']['position_m']['value']))

    def test_engine_domain_rejections_preserve_frozen_guards(self):
        for change in ('high_NA', 'rolled', 'tiny_aperture'):
            data = case()
            if change == 'high_NA':
                for label in ('source', 'target'):
                    del data[label]['complex_q_ts_m']; put(data[label], 'mfd_ts_m', [2e-6, 2e-6])
            if change == 'rolled': put(data['target'], 'sagittal_axis', [0, 0, 1])
            if change == 'tiny_aperture': put(data['design']['reflectors'][0], 'half_aperture_ts_m', [1e-6, 1e-6])
            result = evaluate_external(data)
            self.assertEqual(result['model_domain']['status'], 'Fail', change)
            self.assert_withheld(result)

    def test_declared_bounds_fail_or_remain_separately_uncomputed(self):
        for key, value in (
            ('vertex_bounds_m', [[0, 0, 0], [0, 0, 0]]),
            ('principal_curvature_bounds_per_m', [[0, 1], [0, 1]]),
            ('half_aperture_bounds_m', [[0, 1e-6], [0, 1e-6]]),
            ('normal_constraints', {'axis': [0, 0, 1], 'max_angle_rad': .01}),
            ('principal_curvature_bounds_per_m', [[10, -10], [0, 1]])):
            data = case(); put(data['reflectors'][0], key, value)
            result = evaluate_external(data)
            self.assertEqual(result['geometry']['status'], 'Pass')
            self.assertEqual(result['design_constraints']['status'], 'Fail')
            self.assert_withheld(result)
        data = case(); del data['reflectors'][0]['vertex_bounds_m']
        result = evaluate_external(data)
        self.assertEqual(result['design_constraints']['status'], 'Uncomputed')
        self.assertEqual(result['gaussian_mode_matching']['status'], 'Approximate')

    def test_envelope_pass_is_not_full_package_clearance_pass(self):
        result = evaluate_external(case())
        package = result['package_feasibility']
        self.assertEqual(package['envelope_geometry']['status'], 'Pass')
        self.assertEqual(package['status'], 'Uncomputed')
        self.assertEqual(package['finite_beam_clearance']['status'], 'Uncomputed')
        self.assertEqual(result['actual_applicability']['status'], 'Uncomputed')
        self.assertIsNone(result['physical_losses']['total_coupling'])

    def test_volume_uses_whole_patch_not_vertices(self):
        data = case()
        put(data['package'], 'available_volume', aabb([-.0001, -.0001, -.0001], [.0021, .0001, .0021]))
        result = evaluate_external(data)
        self.assertEqual(result['package_feasibility']['status'], 'Fail')
        checks = result['package_feasibility']['envelope_geometry']['checks']
        self.assertTrue(any(c['path'] == 'patch[0].volume' and c['status'] == 'Fail' for c in checks))
        self.assertTrue(all(c['status'] == 'Pass' for c in checks if c['path'].startswith('path_point')))
        self.assert_withheld(result)

    def test_missing_unsupported_package_and_frame_units(self):
        for change in ('missing', 'solid', 'body_missing', 'frame', 'unit', 'clearance'):
            data = case()
            if change == 'missing': del data['package']
            if change == 'solid': put(data['package'], 'available_volume', {'type': 'mesh', 'path': 'unloaded.stl'})
            if change == 'body_missing': del data['reflectors'][1]['body_envelope']
            if change == 'frame': put(data['package'], 'frame_id', 'another-frame')
            if change == 'unit': data['package']['available_volume']['unit'] = 'mm'
            if change == 'clearance': put(data['package'], 'required_clearance_m', -1.)
            result = evaluate_external(data)
            status = 'Fail' if change in ('frame', 'unit', 'clearance') else 'Uncomputed'
            self.assertEqual(result['package_feasibility']['status'], status, change)
            if status == 'Fail': self.assert_withheld(result)
            else: self.assertEqual(result['gaussian_mode_matching']['status'], 'Approximate')

    def test_body_envelope_must_contain_surface(self):
        data = case()
        put(data['reflectors'][0], 'body_envelope', aabb([.000999, -1e-6, -1e-6], [.001001, 1e-6, 1e-6]))
        result = evaluate_external(data)
        checks = result['package_feasibility']['envelope_geometry']['checks']
        self.assertTrue(any(c['path'] == 'body[0].patch' and c['status'] == 'Fail' for c in checks))
        self.assert_withheld(result)

    def test_envelope_collisions_distance_and_chief_keepout(self):
        # Euclidean distance between separated boxes is a known 3-4-5 triangle.
        self.assertEqual(box_distance(((0, 0, 0), (1, 1, 1)), ((4, 5, 0), (5, 6, 1))), 5.)
        self.assertTrue(segment_hits_box((-1, .5, .5), (2, .5, .5), ((0, 0, 0), (1, 1, 1))))
        self.assertFalse(segment_hits_box((-1, 2, .5), (2, 2, .5), ((0, 0, 0), (1, 1, 1))))
        for change in ('body_pair', 'body_keepout', 'chief_keepout', 'boundary_clearance'):
            data = case()
            if change == 'body_pair': put(data['reflectors'][0], 'body_envelope', aabb([.0002, -.0006, -.0007], [.0018, .0006, .0027]))
            if change == 'body_keepout': put(data['package'], 'keepout_bodies', [aabb([.0004, -.0001, .0003], [.0005, .0001, .0004])])
            if change == 'chief_keepout': put(data['package'], 'keepout_bodies', [aabb([.0001, -1e-5, -1e-5], [.0002, 1e-5, 1e-5])])
            if change == 'boundary_clearance': put(data['package'], 'required_clearance_m', .0005)
            result = evaluate_external(data)
            self.assertEqual(result['package_feasibility']['status'], 'Fail', change)
            self.assert_withheld(result)

    def test_quadratic_patch_extent_independent_dense_surface_reference(self):
        for kt, ks in ((10000., -5000.), (-10000., 7000.)):
            mirror = Reflector((.001, .002, .003), (.6, 0, .8), (kt, ks), (.0007, .0005))
            lo, hi = patch_world_aabb(mirror, (0, 1, 0))
            u, v = np.meshgrid(np.linspace(-.0007, .0007, 501), np.linspace(-.0005, .0005, 501))
            # Manual actual quadratic-sag surface, independently sampled.
            tangent = np.array([.8, 0, -.6]); s = np.array([0, 1, 0]); n = np.array([.6, 0, .8])
            points = np.array(mirror.vertex)+u[..., None]*tangent+v[..., None]*s+(.5*(kt*u*u+ks*v*v))[..., None]*n
            for j in range(3):
                self.assertGreaterEqual(points[..., j].min(), lo[j]-1e-16)
                self.assertLessEqual(points[..., j].max(), hi[j]+1e-16)
                self.assertLess(abs(points[..., j].min()-lo[j]), 1e-8)
                self.assertLess(abs(points[..., j].max()-hi[j]), 1e-8)

    def test_blank_sheet_and_cli_no_actual_coupling(self):
        blank = json.loads((ROOT/'examples/external_ports_unprovided.json').read_text())
        result = evaluate_external(blank)
        self.assertEqual(result['input_contract']['status'], 'Uncomputed')
        self.assert_withheld(result)
        proc = subprocess.run([sys.executable, '-m', 'photonic_architecture_explorer.external',
                               str(ROOT/'examples/m3a_synthetic.json')], text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result['gaussian_mode_matching']['status'], 'Approximate')
        self.assertEqual(result['actual_applicability']['status'], 'Uncomputed')


if __name__ == '__main__':
    unittest.main()
