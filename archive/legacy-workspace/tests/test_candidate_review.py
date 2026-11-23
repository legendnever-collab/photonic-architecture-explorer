"""Check the review summary against the canonical design and sensitivity records."""

import copy
import json
from pathlib import Path
import re
import unittest

from photonic_architecture_explorer.candidate_review import build_candidate_review
from photonic_architecture_explorer.design import design_two_ports
from photonic_architecture_explorer.design_report import render_design_report, review_snapshot


ROOT = Path(__file__).resolve().parents[1]


class CandidateReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads((ROOT / "examples/m5a_two_ports.json").read_text())
        cls.result = design_two_ports(cls.document)
        cls.report = review_snapshot(cls.result)

    def test_review_uses_existing_candidate_order_ports_and_metrics(self):
        review = self.report["candidate_review"]
        self.assertEqual(review["input_sha256"], self.result["input_sha256"])
        self.assertEqual(review["recommended_candidate_id"], self.result["selected_candidate_id"])
        self.assertEqual([d["id"] for d in review["nominal_designs"]],
                         [c["id"] for c in self.result["candidates"]])
        samples = {x["candidate_id"]: x["samples"] for x in self.report["candidate_sensitivity"]["candidates"]}
        for candidate in self.result["candidates"]:
            selected = review["candidates"][candidate["id"]]
            evaluation = candidate["evaluation"]
            self.assertEqual(selected["total_path_m"], candidate["ranking"]["total_path_m"])
            self.assertEqual(selected["segment_lengths_m"], evaluation["geometry"]["lengths"])
            self.assertEqual(selected["overlap"], evaluation["gaussian_mode_matching"]["normalized_mode_overlap"])
            self.assertEqual(selected["sensitivity_samples"], samples[candidate["id"]])
            for port in ("source", "target"):
                self.assertEqual(selected["ports"][port]["position_m"], self.document[port]["position_m"]["value"])
                self.assertEqual(selected["ports"][port]["complex_q_ts_m"],
                                 evaluation["evaluated_ports"][port]["complex_q_ts_m"])
        self.assertEqual({key: self.report[key] for key in self.result}, self.result)
        self.assertEqual([review[key] for key in ("part_placement_status", "package_yield_status",
                                                  "total_coupling_status")], ["Uncomputed"] * 3)

    def test_ties_require_every_scenario_to_be_computed_and_close(self):
        sensitivity = copy.deepcopy(self.report["candidate_sensitivity"])
        a, b, c = [row["candidate_id"] for row in sensitivity["candidates"]]
        row = next(row["id"] for row in sensitivity["scenarios"] if row["id"] != "nominal")
        self.assertEqual(self.report["candidate_review"]["candidates"][a]["sensitivity_ties"], [b, c])
        sensitivity["candidates"][1]["samples"][row]["delta_loss_db"] += 2e-6
        sensitivity["candidates"][2]["samples"][row] = {"status": "Uncomputed"}
        changed = build_candidate_review(self.result, sensitivity)
        self.assertEqual(changed["candidates"][a]["sensitivity_ties"], [])
        self.assertEqual(changed["recommended_candidate_id"], a)

    def test_html_embeds_same_review_and_withholds_invalid_sheet(self):
        html = render_design_report(self.report)
        raw = re.search(r'<script type="application/json" id="design-result">(.*?)</script>', html).group(1)
        self.assertEqual(json.loads(raw)["candidate_review"], self.report["candidate_review"])
        self.assertEqual(html.count("data-review-candidate="), len(self.result["candidates"]))
        bad = review_snapshot(design_two_ports({}))
        self.assertEqual(bad["candidate_review"]["status"], "Uncomputed")
        self.assertNotIn('id="candidate-review"', render_design_report(bad))
