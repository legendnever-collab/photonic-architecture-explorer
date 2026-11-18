"""Regression checks for provenance, safe previews and published report identity."""

import hashlib
import json
import math
import unittest

from scripts.m7r1_mode_report import CATALOG, OUTPUT, gaussian_intensity, render


class ModeReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog_bytes = CATALOG.read_bytes()
        cls.catalog = json.loads(cls.catalog_bytes)
        cls.records = {record["id"]: record for record in cls.catalog["records"]}

    def test_catalog_has_usable_source_locators_and_no_external_fields(self):
        self.assertEqual(self.catalog["actual_external_port"]["status"], "Uncomputed")
        self.assertEqual(len(self.catalog["records"]), len(self.records))
        self.assertEqual(len(self.catalog["sources"]), 5)
        self.assertEqual({record["process"] for record in self.records.values()}, {"SMF", "LDW", "IOX"})
        for record in self.records.values():
            with self.subTest(record=record["id"]):
                source = self.catalog["sources"][record["source_id"]]
                self.assertTrue(source["links"])
                self.assertTrue(all(link["url"].startswith("https://") for link in source["links"]))
                evidence = record["mode_evidence"]
                self.assertTrue(evidence["locator"])
                self.assertIsNone(evidence["raw_intensity_grid"])
                self.assertIsNone(evidence["complex_field"])
                width = evidence["width"]
                if width is None:
                    self.assertIsNone(record["gaussian_intensity_preview"])
                    continue
                self.assertEqual(len(width["axes"]), len(width["diameter_m"]))
                self.assertTrue(all(0 < value < 1e-3 for value in width["diameter_m"]))
                if width["plus_minus_m"] is not None:
                    self.assertEqual(len(width["axes"]), len(width["plus_minus_m"]))
                    self.assertTrue(width["plus_minus_meaning"])

    def test_preview_requires_explicit_assumptions_at_a_known_wavelength(self):
        selected = {
            key for key, record in self.records.items() if record["gaussian_intensity_preview"] is not None
        }
        self.assertEqual(
            selected, {"smf28-ultra-1310", "smf28-ultra-1550", "desmet-fldw-1550", "lee-uncracked-y-1550"}
        )
        for key in selected:
            record = self.records[key]
            self.assertIn(record["wavelength_m"], (1.31e-6, 1.55e-6))
            self.assertIn("Phase remains unspecified", record["gaussian_intensity_preview"]["assumption"])

    def test_gaussian_intensity_uses_a_diameter_not_a_radius_or_field_amplitude(self):
        diameter = 10.4e-6
        self.assertEqual(gaussian_intensity(0, diameter), 1)
        self.assertAlmostEqual(gaussian_intensity(diameter / 2, diameter), math.exp(-2))
        self.assertAlmostEqual(gaussian_intensity(-diameter / 4, diameter), math.exp(-0.5))

    def test_noninterchangeable_loss_metrics_keep_their_provenance(self):
        desmet = {obs["quantity"]: obs for obs in self.records["desmet-fldw-1550"]["observations"]}
        self.assertEqual(desmet["passive V-groove coupling loss"]["provenance"], "measured")
        self.assertEqual(desmet["perfectly aligned mode mismatch"]["provenance"], "simulated")
        active = desmet["active-alignment coupling loss"]
        self.assertEqual(active["provenance"], "inferred_from_measurements")
        self.assertEqual(active["unit"], "dB/facet")
        wang = self.records["wang-ocms-grin-1550"]
        self.assertIn("single-mode GRIN fiber", wang["observations"][0]["conditions"])
        iox = self.records["brusberg-iox-1550"]
        self.assertEqual(iox["observations"][1]["unit"], "dB")
        self.assertIn("output MMF", iox["observations"][1]["conditions"])

    def test_checked_in_report_matches_catalog_and_plot_scope(self):
        report = render(self.catalog_bytes)
        self.assertEqual(report, OUTPUT.read_text(encoding="utf-8"))
        self.assertIn(hashlib.sha256(self.catalog_bytes).hexdigest(), report)
        self.assertEqual(report.count('<svg viewBox='), 3)
        self.assertEqual(report.count('<polyline '), 7)
        self.assertIn("Actual external Port: Uncomputed", report)
        for record_id in self.records:
            self.assertIn(f'<article id="{record_id}">', report)


if __name__ == "__main__":
    unittest.main()
