"""M3-B presentation/HTTP regressions; production optical kernels stay frozen."""

import copy
import http.client
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from xml.etree import ElementTree as ET
from unittest.mock import patch
from urllib.parse import urlencode

from photonic_architecture_explorer import inspector as ui
from photonic_architecture_explorer.external import evaluate_external

ROOT = Path(__file__).resolve().parents[1]


class Inspector(unittest.TestCase):
    def setUp(self):
        self.cases = ui.review_cases()
        self.nominal = copy.deepcopy(self.cases[0][2])

    def test_all_review_states_and_immutable_ports(self):
        expected = [('nominal', 'geometry', 'Pass'), ('blank', 'input_contract', 'Uncomputed'),
                    ('missing-phase', 'input_contract', 'Uncomputed'), ('bad-unit', 'input_contract', 'Fail'),
                    ('target-direction', 'geometry', 'Fail'), ('high-divergence', 'model_domain', 'Fail'),
                    ('bounds-fail', 'design_constraints', 'Fail'), ('package-fail', 'package_feasibility', 'Fail')]
        self.assertEqual(len(self.cases), len(expected))
        for (key, _, data), (want, group, state) in zip(self.cases, expected):
            with self.subTest(key=key):
                before = copy.deepcopy(data)
                result, _ = ui.evaluate_view(data)
                self.assertEqual(key, want)
                self.assertEqual(result, evaluate_external(data))
                self.assertEqual(result[group]['status'], state)
                self.assertEqual(data, before)
                self.assertIsNone(result['physical_losses']['total_coupling'])
                self.assertEqual(result['actual_applicability']['status'], 'Uncomputed')
                if key == 'nominal': self.assertAlmostEqual(ui.visible_overlap(result), 1.)
                else: self.assertIsNone(ui.visible_overlap(result))

    def test_each_view_calls_adapter_and_never_caches_overlap(self):
        with patch.object(ui, 'evaluate_external', wraps=evaluate_external) as call:
            for data in (self.nominal, self.cases[3][2], self.cases[1][2], self.nominal):
                result, _ = ui.evaluate_view(data)
                panel = ui.result_panel(result)
                self.assertEqual('data-overlap-value=' in panel, data == self.nominal)
            self.assertEqual(call.call_count, 4)
        result, adapted = ui.evaluate_view({}, 'invalid JSON')
        self.assertIsNone(adapted)
        self.assertEqual(result['input_contract']['status'], 'Fail')
        self.assertIsNone(ui.visible_overlap(result))

    def test_projection_coordinates_equal_scale_and_chief_withholding(self):
        result, adapted = ui.evaluate_view(self.nominal)
        for projection in ui.PROJECTIONS:
            svg = ui.plot_svg(self.nominal, result, adapted, projection, 'p')
            self.assertIn('data-scale="equal"', svg)
            self.assertEqual(svg.count('data-kind="fixed-port"'), 2)
            self.assertEqual(svg.count('data-kind="quadratic-surface"'), 12)
            self.assertEqual(svg.count('data-kind="verified-chief"'), 1)
            self.assertNotIn('nan', svg.lower())
            root = ET.fromstring(svg)
            circles = root.findall('.//circle')
            if projection == 'XZ':
                dx = float(circles[1].get('cx'))-float(circles[0].get('cx'))
                dy = float(circles[1].get('cy'))-float(circles[0].get('cy'))
                self.assertAlmostEqual(dx, -dy, places=10)  # equal 2 mm displacement
            volume = root.find('.//rect[@data-kind="volume"]')
            box = self.nominal['package']['available_volume']['value']
            a, b, _ = ui.PROJECTIONS[projection]
            physical_ratio = (box['max_m'][a]-box['min_m'][a])/(box['max_m'][b]-box['min_m'][b])
            self.assertAlmostEqual(float(volume.get('width'))/float(volume.get('height')), physical_ratio, places=10)
        bad, adapted = ui.evaluate_view(self.cases[4][2])
        self.assertNotIn('verified-chief', ui.plot_svg(self.cases[4][2], bad, adapted, 'XZ', 'p'))
        bad, adapted = ui.evaluate_view(self.cases[3][2])
        self.assertNotIn('<svg', ui.plot_svg(self.cases[3][2], bad, adapted, 'XZ', 'p'))

    def test_quadratic_display_samples_against_local_sag_prescription(self):
        _, design = ui.evaluate_view(self.nominal)
        # Frozen normals are in XZ with n=(±1,0,∓1)/sqrt(2).
        # Independent projection onto n and tangent=(nz,0,-nx).
        for mirror in design.reflectors:
            for line in ui.surface_lines(mirror, design.source.sagittal):
                for p in line:
                    dx, dy, dz = (p[i]-mirror.vertex[i] for i in range(3))
                    u = dx*mirror.normal[2]-dz*mirror.normal[0]
                    v = dy
                    h = dx*mirror.normal[0]+dz*mirror.normal[2]
                    self.assertAlmostEqual(h, (mirror.curvatures[0]*u*u+mirror.curvatures[1]*v*v)/2, delta=1e-18)
                    self.assertLessEqual(abs(u), mirror.half_aperture[0]+1e-18)
                    self.assertLessEqual(abs(v), mirror.half_aperture[1]+1e-18)
        self.nominal['design']['reflectors'][0]['illuminated_normal']['value'] = [0, 1, 0]
        # Unsupported orientation must not create a singular display basis.
        page = ui.render_report([('bad', 'unsupported', self.nominal)])
        self.assertIn('surface orientation unsupported', page)
        self.assertNotIn('data-kind="verified-chief"', page)

    def test_only_declared_common_frame_supported_boxes_are_displayed(self):
        _, design = ui.evaluate_view(self.nominal)
        self.assertEqual(len(ui.declared_boxes(self.nominal, design)), 3)
        for change in ('frame', 'unit', 'transform', 'nonfinite'):
            data = copy.deepcopy(self.nominal)
            if change == 'frame': data['package']['frame_id']['value'] = 'other'
            if change == 'unit': data['package']['available_volume']['unit'] = 'mm'
            if change == 'transform': data['package']['available_volume']['value']['transform'] = []
            if change == 'nonfinite': data['package']['available_volume']['value']['max_m'][0] = math.inf
            boxes = ui.declared_boxes(data, design)
            self.assertFalse(any(b[1] == 'volume' for b in boxes), change)

    def test_input_group_roundtrip_missing_and_duplicate_data(self):
        for _, _, data in self.cases:
            raw = {k: json.dumps(v) for k, v in ui.groups(data).items()}
            self.assertEqual(ui.parse_groups(raw), data)
        raw = {k: json.dumps(v) for k, v in ui.groups(self.nominal).items()}
        for text in ('[]', '{', '{"x":NaN}', '{"x":1e999}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                ui.parse_groups({**raw, 'ports': text})
        with self.assertRaises(ValueError): ui.parse_groups({**raw, 'package': '{"source":{}}'})
        with self.assertRaises(ValueError): ui.parse_groups({'ports': '{}'})

    def test_html_escaping_and_static_controls(self):
        self.nominal['description'] = '</textarea><script>alert(1)</script>'
        text = ui.render_report([('input', '<script>title</script>', self.nominal)])
        self.assertNotIn('<script>alert', text)
        self.assertNotIn('<script>title', text)
        self.assertIn('&lt;script&gt;', text)
        self.assertEqual(text.count(' readonly'), 3)
        self.assertNotIn('<button type="submit">', text)
        self.assertIn('Static Review', text)
        self.assertIn('생략 축 Y', text)
        for key in ('envelope_geometry', 'package_feasibility', 'physical_losses', 'actual_applicability', 'fabrication'):
            self.assertIn(f'data-result="{key}"', text)
        self.assertIn('data-overlap-value="1.0"', text)
        self.assertIn('2D Projection의 중첩은 3D 충돌 판정이 아닙니다.', text)

    def test_http_valid_invalid_valid_edit_flow(self):
        server = ui.make_server(self.cases, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
        try:
            connection.request('GET', '/')
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.getheader('Cache-Control'), 'no-store')
            self.assertIn('data-overlap-value="1.0"', response.read().decode())
            raw = {k: json.dumps(v) for k, v in ui.groups(self.nominal).items()}
            changed = copy.deepcopy(self.nominal)
            # Explicit design change; fixed Ports are untouched.
            changed['design']['reflectors'][0]['principal_curvature_ts_per_m']['value'][0] *= 1.01
            changed_raw = {k: json.dumps(v) for k, v in ui.groups(changed).items()}
            bodies = [changed_raw, {**raw, 'ports': '{'}, raw]
            for fields, valid in zip(bodies, (True, False, True)):
                connection.request('POST', '/evaluate', urlencode(fields), {'Content-Type': 'application/x-www-form-urlencoded'})
                response = connection.getresponse()
                page = response.read().decode()
                self.assertEqual(response.status, 200)
                self.assertEqual('data-overlap-value=' in page, valid)
                if not valid: self.assertIn('JSON editor', page)
                else: self.assertIn('기본 Review Cases로 돌아가기', page)
            self.assertEqual(self.nominal, self.cases[0][2])
        finally:
            connection.close(); server.shutdown(); server.server_close(); thread.join()

    def test_http_rejects_wrong_origin_host_and_invalid_bytes(self):
        server = ui.make_server(self.cases, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            for method, path, body, headers, code in (
                ('GET', '/', None, {'Host': 'remote.example'}, 403),
                ('GET', '/missing', None, {}, 404),
                ('POST', '/evaluate', 'ports={}', {'Origin': 'https://elsewhere.example'}, 403),
                ('POST', '/evaluate', b'\xff', {}, 400),
                ('POST', '/evaluate', '', {}, 413)):
                conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
                conn.request(method, path, body, headers)
                response = conn.getresponse(); response.read()
                self.assertEqual(response.status, code)
                conn.close()
        finally: server.shutdown(); server.server_close(); thread.join()

    def test_cli_static_default_and_blank_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'review.html'
            for args, nominal in (([], True), (['--input', str(ROOT/'examples/external_ports_unprovided.json')], False)):
                proc = subprocess.run([sys.executable, '-m', 'photonic_architecture_explorer.inspector', '--output', str(dest), *args], capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                page = dest.read_text()
                self.assertEqual('data-overlap-value=' in page, nominal)
                self.assertIn('Uncomputed', page)


if __name__ == '__main__': unittest.main()
