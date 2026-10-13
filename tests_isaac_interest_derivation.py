from __future__ import annotations

import unittest

from decision_trace import DecisionTrace
from isaac_interest_derivation import (
    INTEREST_SCHEMA,
    InterestDerivation,
    build_interest_derivation,
    record_interest_derivation,
    validate_interest_derivation,
)


class TestIsaacInterestDerivation(unittest.TestCase):
    def setUp(self):
        self.valid_args = {
            "interest_id": "interest-101",
            "owner_goal_id": "goal-owner-1",
            "subgoal_id": "subgoal-1",
            "observation_research_id": "res-42",
            "new_information": "Discovered new lightweight embedding optimization approach",
            "inference": "Optimizing memory usage directly supports goal to reduce footprint",
            "interest_proposal": "Research lightweight embedding models",
            "alignment_check": {"aligned": True, "reason": "Supports owner efficiency goal", "policy_id": "policy-01"},
            "scope_check": {"bounded": True, "max_depth": 2, "timebox": "48h"},
            "risk_check": {"acceptable": True, "risk_level": "low"},
            "authorization": {"authorized": True, "authorized_by": "owner_policy", "authorization_event_id": "auth-77"},
        }

    def test_valid_interest_derivation_passes(self):
        derivation = build_interest_derivation(**self.valid_args)
        result = validate_interest_derivation(derivation)

        self.assertTrue(result["valid"])
        self.assertEqual(result["schema"], INTEREST_SCHEMA)
        self.assertEqual(result["interest_id"], "interest-101")
        self.assertEqual(len(result["missing"]), 0)
        self.assertEqual(len(result["errors"]), 0)

    def test_records_interest_derivation_to_trace(self):
        trace = DecisionTrace()
        derivation = build_interest_derivation(**self.valid_args)
        validation = record_interest_derivation(trace, derivation)

        self.assertTrue(validation["valid"])
        events = trace.to_list()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "interest_derivation_recorded")
        self.assertEqual(events[0]["data"]["interest_id"], "interest-101")

    def test_missing_mandatory_fields_fail_validation(self):
        args = dict(self.valid_args)
        args["owner_goal_id"] = ""
        args["inference"] = ""

        derivation = build_interest_derivation(**args)
        result = validate_interest_derivation(derivation)

        self.assertFalse(result["valid"])
        self.assertIn("owner_goal_id", result["missing"])
        self.assertIn("inference", result["missing"])

    def test_unaligned_interest_fails_validation(self):
        args = dict(self.valid_args)
        args["alignment_check"] = {"aligned": False, "reason": "Not relevant to owner"}

        derivation = build_interest_derivation(**args)
        result = validate_interest_derivation(derivation)

        self.assertFalse(result["valid"])
        self.assertIn("alignment_check_failed", result["errors"])

    def test_unbounded_scope_fails_validation(self):
        args = dict(self.valid_args)
        args["scope_check"] = {"bounded": False, "reason": "Unbounded exploration"}

        derivation = build_interest_derivation(**args)
        result = validate_interest_derivation(derivation)

        self.assertFalse(result["valid"])
        self.assertIn("scope_check_failed", result["errors"])

    def test_unacceptable_risk_fails_validation(self):
        args = dict(self.valid_args)
        args["risk_check"] = {"acceptable": False, "reason": "High risk of resource exhaustion"}

        derivation = build_interest_derivation(**args)
        result = validate_interest_derivation(derivation)

        self.assertFalse(result["valid"])
        self.assertIn("risk_check_failed", result["errors"])

    def test_unauthorized_derivation_fails_validation(self):
        args = dict(self.valid_args)
        args["authorization"] = {"authorized": False, "reason": "Denied by policy"}

        derivation = build_interest_derivation(**args)
        result = validate_interest_derivation(derivation)

        self.assertFalse(result["valid"])
        self.assertIn("authorization_failed", result["errors"])


if __name__ == "__main__":
    unittest.main()
