import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

import numpy as np

from scripts import m7r16_vector_reference as ref


class VectorRelayControls(unittest.TestCase):
    def test_saved_target_control_matches_frozen_export(self):
        with TemporaryDirectory() as temp:
            result = ref.run(Path(temp))
            self.assertIsNone(result["nominal_target_field"])
            name = result["control_export"]
            with np.load(Path(temp) / name) as new, np.load(ref.ROOT / "references/m7r16" / name) as old:
                for key in ("E_t", "E_s", "H_t", "H_s"):
                    self.assertLess(ref.relative(new[key], old[key]), ref.LIMIT)
                for key in ("t_m", "s_m", "center_m", "basis_tsn", "launch_power_m2", "case"):
                    np.testing.assert_array_equal(new[key], old[key])
