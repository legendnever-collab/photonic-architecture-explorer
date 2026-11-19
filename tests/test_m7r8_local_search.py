import unittest

import numpy as np
from scipy.special import erfcinv

from photonic_architecture_explorer.design import POLICY
from photonic_architecture_explorer.external import evaluate_external
from photonic_architecture_explorer.solver import MAX_APERTURE_TAIL
from scripts.m7r7_package import apply_envelopes, load, package_record, record
from scripts.m7r8_local_search import (
    APERTURE_DIAGNOSTIC_PATH,
    CASE_PATH,
    INPUT_PATH,
    REFERENCE_PATH,
    expansion_recheck,
    expansion_required,
)


class LocalPackageSearchTests(unittest.TestCase):
    def test_archived_prescription_face_expansion_preserves_optics(self):
        case = load(CASE_PATH)
        fixed = load(INPUT_PATH)
        row = next(
            r for r in load(REFERENCE_PATH)["candidates"] if r["id"] == "G029-NM"
        )
        tail = load(APERTURE_DIAGNOSTIC_PATH)["fraction_of_existing_tail_guard"]
        scale = erfcinv(tail * MAX_APERTURE_TAIL / 4) / (
            2**0.5 * POLICY["aperture_projected_radius_factor"]
        )
        proposal = apply_envelopes(
            {
                **fixed,
                "package": package_record(case),
                "design": {"reflectors": row["reflectors"]},
                "reflectors": [
                    {"surface_prescription": record("quadratic_patch", "model", "R6")}
                    for _ in range(2)
                ],
            },
            case,
            float(scale),
        )
        original = evaluate_external(proposal)
        self.assertEqual(
            original["package_feasibility"]["envelope_geometry"]["status"], "Fail"
        )
        self.assertIsNone(original["gaussian_mode_matching"]["normalized_mode_overlap"])
        shifts = expansion_required(proposal)
        np.testing.assert_allclose(
            [shifts[0][0], shifts[1][0]],
            [0.0540683e-3, 0.0532926e-3],
            atol=0.5e-6,
            rtol=0,
        )
        np.testing.assert_array_equal(np.array(shifts)[:, 1:], 0.0)
        expanded = expansion_recheck(
            {"prescription": proposal, "expansion_m": shifts, "overlap": row["overlap"]}
        )
        self.assertGreater(
            expanded["max_m"][0],
            proposal["package"]["available_volume"]["value"]["max_m"][0],
        )
