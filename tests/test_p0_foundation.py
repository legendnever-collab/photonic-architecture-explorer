"""P0: Design Document, presets, scene geometry, scenarios and the local API."""

import copy
import json
import math
from pathlib import Path
import sys
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))

from photonic_architecture_explorer import api  # noqa: E402
from photonic_architecture_explorer.app import make_server, scenario_index  # noqa: E402
from photonic_architecture_explorer.design_document import (  # noqa: E402
    DocumentError, document_sha256, to_engine_input, validate_document)
from photonic_architecture_explorer.external import adapt_external  # noqa: E402
from photonic_architecture_explorer.presets import load_presets  # noqa: E402

SCENARIOS = ROOT / 'src/photonic_architecture_explorer/scenarios'


def load(name):
    return json.loads((SCENARIOS / f'{name}.json').read_text(encoding='utf-8'))


class DesignDocumentTest(unittest.TestCase):
    def test_scenarios_are_valid_and_convert_with_si_units_and_provenance(self):
        document = load('S2b-1550')
        self.assertEqual(validate_document(document), [])
        engine = to_engine_input(document)
        target = engine['target']
        self.assertEqual(engine['wavelength_m']['value'], 1550 * 1e-9)
        self.assertEqual(target['position_m']['value'], [3.0e-3, 0.0, 1.0e-3])
        self.assertEqual(target['mfd_ts_m']['value'], [12.0e-6, 18.8e-6])  # t = vertical
        self.assertEqual(target['mfd_ts_m']['provenance'], 'measured')
        self.assertEqual(target['wavefront_curvature_ts_per_m']['provenance'], 'assumed')
        self.assertEqual(target['reference_plane']['value']['origin_m'], target['position_m']['value'])

    def test_every_problem_is_reported_without_silent_repair(self):
        document = copy.deepcopy(load('S1'))
        document['schema'] = 'other'
        document['ports']['source']['direction'] = [1, 1, 0]
        document['ports']['target']['sagittal_axis'] = [0, 0, 1]
        document['ports']['target']['mfd_um'] = [9.2, -1]
        document['ports']['source']['evidence']['mode'] = {'provenance': 'guess', 'source': 'x'}
        paths = {issue['path'] for issue in validate_document(document)}
        self.assertEqual(paths, {'schema', 'ports.source.direction', 'ports.target.sagittal_axis',
                                 'ports.target.mfd_um', 'ports.source.evidence.mode'})
        with self.assertRaises(DocumentError):
            to_engine_input(document)

    def test_document_hash_ignores_key_order(self):
        document = load('S1')
        reordered = json.loads(json.dumps(document, sort_keys=False)[::-1][::-1])
        reordered = dict(reversed(list(reordered.items())))
        self.assertEqual(document_sha256(document), document_sha256(reordered))


class PresetTest(unittest.TestCase):
    def test_published_widths_and_labels(self):
        presets = {p['id']: p for p in load_presets()}
        expected = {'smf28-ultra-1310': (9.2, 9.2), 'smf28-ultra-1550': (10.4, 10.4),
                    'sun-fldw-55mw-1310': (11.0, 18.0), 'desmet-fldw-1550': (12.8, 12.1),
                    'brusberg-iox-1550': (18.8, 12.0), 'synthetic-siph-ssc-3um': (3.0, 3.0)}
        for key, (lateral, vertical) in expected.items():
            self.assertAlmostEqual(presets[key]['mfd_lateral_um'], lateral, places=9)
            self.assertAlmostEqual(presets[key]['mfd_vertical_um'], vertical, places=9)
        self.assertEqual(presets['synthetic-siph-ssc-3um']['mode_provenance'], 'synthetic')
        self.assertTrue(all('Flat phase' in p['phase_note'] for p in presets.values()))


class SceneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = api.design(load('S1'))

    def test_scene_matches_engine_geometry(self):
        result = self.result
        self.assertEqual(result['status'], 'Computed')
        report = result['engine_report']
        for candidate, engine in zip(result['candidates'], report['candidates']):
            design = adapt_external(engine['prescription'])
            points = candidate['scene']['path']['points_mm']
            expected = [design.source.position, *(m.vertex for m in design.reflectors), design.target.position]
            for drawn, exact in zip(points, expected):
                self.assertLess(max(abs(a - b * 1e3) for a, b in zip(drawn, exact)), 1e-9)  # 1 pm
            lengths = engine['evaluation']['geometry']['lengths']
            self.assertAlmostEqual(candidate['metrics']['total_path_mm'], sum(lengths) * 1e3, places=12)

    def test_beam_samples_agree_with_engine_planes(self):
        for candidate, engine in zip(self.result['candidates'], self.result['engine_report']['candidates']):
            samples = candidate['scene']['beam']['samples']
            planes = {s['plane']: s for s in engine['evaluation']['samples']}
            first, last = samples[0], samples[-1]
            for axis, key in ((0, 'radius_t_um'), (1, 'radius_s_um')):
                self.assertAlmostEqual(first[key], planes['source']['axes'][axis]['radius_m'] * 1e6, places=9)
                self.assertAlmostEqual(last[key], planes['target']['axes'][axis]['radius_m'] * 1e6, places=9)
            for j, mirror in enumerate(candidate['scene']['mirrors']):
                engine_radii = planes[f'M{j + 1}_before']['surface_radii_m']
                for drawn, exact in zip(mirror['beam_footprint_radius_ts_um'], engine_radii):
                    self.assertAlmostEqual(drawn, exact * 1e6, places=9)

    def test_surface_grid_centre_is_vertex_and_lies_on_patch(self):
        for candidate in self.result['candidates']:
            for mirror in candidate['scene']['mirrors']:
                grid = mirror['surface_grid_mm']
                centre = grid[len(grid) // 2][len(grid) // 2]
                self.assertLess(max(abs(a - b) for a, b in zip(centre, mirror['vertex_mm'])), 1e-12)
                corner = grid[0][0]
                kt, ks = mirror['curvature_ts_per_m']
                at, as_ = (v * 1e-3 for v in mirror['half_aperture_ts_mm'])
                offset = [(c - v) * 1e-3 for c, v in zip(corner, mirror['vertex_mm'])]
                height = sum(o * n for o, n in zip(offset, mirror['normal']))
                self.assertAlmostEqual(height, (kt * at * at + ks * as_ * as_) / 2, delta=1e-15)

    def test_preview_reports_divergence_guard_threshold(self):
        preview = api.preview(load('S3'))
        source = preview['ports']['ports'][0]
        self.assertEqual(source['divergence_guard']['status'], 'Fail')
        expected = 2 * 1310e-9 / (math.pi * 1.0 * 0.1) * 1e6
        self.assertAlmostEqual(source['divergence_guard']['min_waist_mfd_um'], expected, places=9)
        self.assertEqual(preview['candidates'], [])

    def test_invalid_document_is_not_designed(self):
        document = copy.deepcopy(load('S1'))
        document['ports']['source']['direction'] = [2, 0, 0]
        result = api.design(document)
        self.assertEqual(result['status'], 'Invalid')
        self.assertEqual(result['issues'][0]['path'], 'ports.source.direction')


class ScenarioTest(unittest.TestCase):
    def test_every_scenario_meets_its_recorded_expectation(self):
        for entry in scenario_index()['scenarios']:
            with self.subTest(entry['id']):
                expect = entry['expect']
                if entry['file'] is None:
                    self.assertEqual(expect['status'], 'Unsupported')
                    continue
                result = api.design(load(entry['file'][:-5]))
                self.assertEqual(result['status'], expect['status'])
                self.assertGreaterEqual(len(result['candidates']), expect.get('min_candidates', 0))
                self.assertIn(expect.get('reason_contains', ''), result['reason'] or '')
                self.assertIn('phase', expect['target'])

    def test_fixtures_match_their_generator(self):
        import build_scenarios
        for sid, _, filename, _, document, _ in build_scenarios.SCENARIOS:
            with self.subTest(sid):
                self.assertEqual(load(filename[:-5]), json.loads(json.dumps(document)))


class AppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(0)
        cls.base = f'http://127.0.0.1:{cls.server.server_address[1]}'
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def get(self, path):
        with urlopen(self.base + path, timeout=30) as response:
            return response.status, response.headers.get('Content-Type'), response.read()

    def test_read_endpoints_and_static_page(self):
        status, kind, body = self.get('/api/health')
        self.assertEqual((status, json.loads(body)['design_schema']), (200, 'pae.design/1'))
        self.assertTrue(json.loads(self.get('/api/presets')[2])['presets'])
        self.assertEqual(json.loads(self.get('/api/scenarios/S1')[2])['scenario'], 'S1')
        status, kind, body = self.get('/')
        self.assertTrue(kind.startswith('text/html'))
        self.assertIn(b'assets/app.js', body)
        status, kind, script = self.get('/assets/app.js')
        self.assertTrue(kind.startswith(('text/javascript', 'application/javascript')))
        self.assertIn(b'api/design', script)

    def test_design_round_trip(self):
        body = json.dumps(load('S1')).encode('utf-8')
        request = Request(self.base + '/api/design', data=body, headers={'Content-Type': 'application/json'})
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read())
        self.assertEqual(result['schema'], 'pae.result/1')
        self.assertEqual(result['status'], 'Computed')

    def test_unknown_paths_and_traversal_are_refused(self):
        for path in ('/api/nothing', '/../pyproject.toml', '/%2e%2e/app.py', '/.hidden'):
            with self.subTest(path), self.assertRaises(HTTPError) as caught:
                self.get(path)
            self.assertEqual(caught.exception.code, 404)


if __name__ == '__main__':
    unittest.main()
