"""Run the frozen JSON benchmark, without fitting target fields or geometry."""

import argparse
import hashlib
import json
import math
from pathlib import Path
from .gaussian import Gaussian
from .geometry import Port, Reflector
from .solver import evaluate


def load_case(path, case='curved'):
    data = json.loads(Path(path).read_text())
    ports = []
    for label in ('source', 'target'):
        p = data[label]
        ports.append(Port(p['position_m'], p['direction'], data['sagittal_axis'],
                          Gaussian.from_radii(p['waist_radii_m'], data['wavelength_m'], data['medium_index'])))
    f, cosine = data['curved_focal_length_m'], math.sqrt(0.5)
    choices = {'flat': (0., 0.), 'curved': (cosine/(2*f), 1/(2*f*cosine)),
               'spherical_control': (data['spherical_curvature_per_m'],)*2}
    mirrors = tuple(Reflector(m['vertex_m'], m['normal'], choices[case], m['half_aperture_m'])
                    for m in data['reflectors'])
    return (*ports, mirrors)


def run(path):
    outputs = {case: evaluate(*load_case(path, case)) for case in ('flat', 'curved', 'spherical_control')}
    flat, curved = (outputs[c]['gaussian_mode_matching'] for c in ('flat', 'curved'))
    passed = all(outputs[c][k]['status'] == 'Pass' for c in ('flat', 'curved')
                 for k in ('geometry', 'model_domain', 'gaussian_mode_matching'))
    source, _, _ = load_case(path)
    expected_flat = math.prod((1+(0.004/(2*q.imag))**2)**-0.5 for q in source.mode.q)
    if passed:
        passed = (abs(curved['normalized_mode_overlap']-1) < 1e-10
                  and abs(flat['normalized_mode_overlap']-expected_flat) < 1e-10
                  and curved['normalized_mode_overlap']-flat['normalized_mode_overlap'] > 0.5
                  and all(abs(a['radius_m']-b['radius_m'])/b['radius_m'] > 0.2
                          for a, b in zip(flat['output_axes'], curved['output_axes'])))
    return dict(benchmark_id='M1-001', input_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                completion_gate={'status': 'Pass' if passed else 'Fail',
                                 'scope': 'benchmark model gate; independent tests separately required'},
                analytical_flat_overlap=expected_flat, cases=outputs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = run(args.input)
    text = json.dumps(report, indent=2, allow_nan=False)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end='')
    return 0 if report['completion_gate']['status'] == 'Pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
