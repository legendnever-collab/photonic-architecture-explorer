"""Lens materials: public-literature dispersion formulas (no proprietary data)."""

import math

from .gaussian import DomainError


def silica_index(wavelength_m):
    """Fused silica, I. H. Malitson, J. Opt. Soc. Am. 55, 1205 (1965), three-term Sellmeier, 20 °C, 0.21–3.71 µm."""
    um = wavelength_m * 1e6
    if not 0.21 <= um <= 3.71:
        raise DomainError(f'fused silica formula valid 0.21–3.71 µm, got {um:.3f} µm')
    l2 = um * um
    return math.sqrt(1 + 0.6961663 * l2 / (l2 - 0.0684043 ** 2) + 0.4079426 * l2 / (l2 - 0.1162414 ** 2)
                     + 0.8974794 * l2 / (l2 - 9.896161 ** 2))


def silicon_index(wavelength_m):
    """Crystalline silicon at 293 K, H. H. Li, J. Phys. Chem. Ref. Data 9, 561 (1980), 1.2–14 µm
    (n² = ε + A/λ² + B λ₁²/(λ² − λ₁²), ε 11.6858, A 0.939816 µm², B 0.00810461, λ₁ 1.1071 µm)."""
    um = wavelength_m * 1e6
    if not 1.2 <= um <= 14.0:
        raise DomainError(f'silicon is absorbing or outside the formula below 1.2 µm (got {um:.3f} µm)')
    l2 = um * um
    return math.sqrt(11.6858 + 0.939816 / l2 + 0.00810461 * 1.1071 ** 2 / (l2 - 1.1071 ** 2))


MATERIALS = {
    'fused_silica': {'label': 'Fused silica', 'index': silica_index,
                     'source': 'I. H. Malitson, J. Opt. Soc. Am. 55, 1205 (1965)'},
    'silicon': {'label': 'Silicon', 'index': silicon_index,
                'source': 'H. H. Li, J. Phys. Chem. Ref. Data 9, 561 (1980), 293 K'},
}


def lens_material(key, wavelength_m):
    material = MATERIALS[key]
    n = material['index'](wavelength_m)
    reflectance = ((n - 1) / (n + 1)) ** 2
    return {'key': key, 'label': material['label'], 'index': n, 'source': material['source'],
            'provenance': 'public_literature', 'uncoated_normal_transmission_two_faces': (1 - reflectance) ** 2}
