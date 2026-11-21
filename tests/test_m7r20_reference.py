import json
import unittest

import numpy as np

from scripts import m7r20_reference as r20


class YeeExtractionTests(unittest.TestCase):
    def test_complex_transverse_alignment_keeps_relative_H_bias(self):
        r = np.array([0.5, 1.5, 2.5])
        _, mode = r20.source.guided_mode()
        ref = mode(r)
        trial = ref * (2 - 1j)
        trial[:, 3:5] *= 1.02
        result = r20.modal_difference(trial, ref, r)
        self.assertAlmostEqual(result["E"], 0)
        self.assertAlmostEqual(result["H"], 0.02)

    def test_frozen_native_guide_profiles_replay(self):
        root = r20.source.ROOT / "references/m7r20"
        summary = json.loads((root / "summary.json").read_text())
        with np.load(root / "profiles.npz") as f:
            r = f["r_um"]
            _, mode = r20.source.guided_mode()
            for key, guide in summary["guides"].items():
                for plane, row in guide["planes"].items():
                    actual = r20.modal_difference(f[key + "_" + plane], mode(r), r)
                    for component in ["E", "H"]:
                        self.assertAlmostEqual(
                            actual[component], row["HE11"][component], places=11
                        )

    def test_staggered_interpolation_uses_physical_coordinates(self):
        z = (np.arange(12) + 0.5) / 12
        values = (1 + 2j) * z**3 - z
        self.assertAlmostEqual(
            abs(r20.interpolate_z(z, values, 0.5, 6) - ((1 + 2j) * 0.5**3 - 0.5)), 0
        )
