"""Port presets drawn from the public-literature Mode Library (M7-R1 data).

Each preset keeps the published width, its locator and the explicit assumptions needed
to use it as a Gaussian Port: flat phase at the external plane and an axis mapping.
Nothing here is a measured complex field or a company value.
"""

import json
from importlib import resources

LIBRARY = 'm7r1_mode_references.json'
FLAT_PHASE = 'Flat phase (1/R = 0) at the external reference plane is an assumption; the source reports intensity only'

# record id -> (lateral index, vertical index) into the published width axes, and a note.
# "lateral" lies in the substrate plane, "vertical" is normal to it.
AXIS_MAP = {
    'smf28-ultra-1310': (0, 0, 'Circular scalar MFD'),
    'smf28-ultra-1550': (0, 0, 'Circular scalar MFD'),
    'sun-fldw-55mw-1310': (0, 1, 'Published x/y read as lateral/vertical; the source gives no registered mapping'),
    'desmet-fldw-1550': (0, 1, 'Published lateral/vertical axes'),
    'lee-uncracked-y-1550': (0, 1, 'Published x/y read as lateral/vertical; the source gives no registered mapping'),
    'brusberg-iox-1550': (0, 1, 'Published horizontal/vertical axes'),
}

SYNTHETIC = [{
    'id': 'synthetic-siph-ssc-3um',
    'label': 'SiPh SSC class · 3 µm (Synthetic)',
    'process': 'SSC',
    'material': 'Silicon photonics edge coupler class',
    'wavelength_nm': 1310.0,
    'mfd_lateral_um': 3.0,
    'mfd_vertical_um': 3.0,
    'mode_provenance': 'synthetic',
    'source': 'Representative class value for scenario S3; not a specific device or measurement',
    'locator': None,
    'url': None,
    'axis_note': 'Circular synthetic mode',
    'phase_note': 'Flat phase is a synthetic assumption',
    'notes': [],
}]


def _library():
    return json.loads(resources.files(__package__).joinpath('data', LIBRARY).read_text(encoding='utf-8'))


def load_presets():
    library = _library()
    sources = library['sources']
    presets = []
    for record in library['records']:
        if record['id'] not in AXIS_MAP or not record.get('wavelength_m'):
            continue
        width = record['mode_evidence']['width']
        lateral, vertical, axis_note = AXIS_MAP[record['id']]
        source = sources[record['source_id']]
        citation = f"{source['authors']}, {source['title']}, {source['publication']}"
        presets.append({
            'id': record['id'],
            'label': record['label'],
            'process': record['process'],
            'material': record['material'],
            'wavelength_nm': round(record['wavelength_m'] * 1e9, 6),
            'mfd_lateral_um': round(width['diameter_m'][lateral] * 1e6, 6),
            'mfd_vertical_um': round(width['diameter_m'][vertical] * 1e6, 6),
            'mode_provenance': 'measured',
            'source': f"{citation} · {record['mode_evidence'].get('locator', '')}".strip(' ·'),
            'locator': record['mode_evidence'].get('locator'),
            'url': source.get('url'),
            'axis_note': axis_note,
            'phase_note': FLAT_PHASE,
            'notes': [width.get('definition', '')] + list(record.get('notes', [])),
        })
    return presets + SYNTHETIC


def preset(preset_id):
    for item in load_presets():
        if item['id'] == preset_id:
            return item
    raise KeyError(preset_id)


def port_from_preset(preset_id, *, position_mm, direction, sagittal_axis, t_is='vertical',
                     placement_source='Synthetic scenario placement'):
    """Build a Design Document Port. `t_is` says which published axis lies in the fold plane."""
    item = preset(preset_id)
    lateral, vertical = item['mfd_lateral_um'], item['mfd_vertical_um']
    mfd = [vertical, lateral] if t_is == 'vertical' else [lateral, vertical]
    return {
        'label': item['label'],
        'preset': item['id'],
        'position_mm': list(position_mm),
        'direction': list(direction),
        'sagittal_axis': list(sagittal_axis),
        'mfd_um': mfd,
        'wavefront_curvature_per_m': [0.0, 0.0],
        'evidence': {
            'placement': {'provenance': 'synthetic', 'source': placement_source},
            'mode': {'provenance': item['mode_provenance'],
                     'source': f"{item['source']} · t={t_is} axis ({item['axis_note']})"},
            'phase': {'provenance': 'assumed' if item['mode_provenance'] != 'synthetic' else 'synthetic',
                      'source': item['phase_note']},
        },
    }
