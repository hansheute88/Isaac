from __future__ import annotations

import unittest

from decision_trace import DecisionTrace, TracePhase
from benchmarks.isaac20_governance import build_governance_evidence
from benchmarks.isaac20_governance_f2 import build_reproducibility_manifest
from isaac_autonomy_cycle import begin_cycle, record_authorization
from isaac_autonomy_verification import (
    GATE_BASELINE,
    GATE_CYCLE,
    GATE_FINAL,
    GATE_INTEREST,
    GATE_LEARNING,
    GATE_PREFLIGHT,
    GATE_PROOF,
    AutonomyRunMetrics,
    evaluate_autonomy_gates,
)
from isaac_interest_derivation import build_interest_derivation
from isaac_learning_causality import build_learning_record


class TestIsaacAutonomyVerification(unittest.TestCase):
    def setUp(self):
        self.valid_cycle = {
            "cycle_id": "cycle-1",
            "intent": "Research optimization",
            "authorization_event_id": "auth-1",
            "authorization_allowed": True,
            "authorization_action_id": "action:research-optimization",
            "authorization_scope": "research:goal-1",
            "execution_action_id": "action:research-optimization",
            "execution_scope": "research:goal-1",
            "execution_event_id": "exec-1",
            "evaluation_event_id": "eval-1",
            "learning_id": "learn-1",
        }
        self.valid_learning = build_learning_record(
            learning_id="learn-1",
            research_id="res-1",
            goal_id="goal-1",
            subgoal_id="sub-1",
            source_cycle_id="cycle-1",
            pre_state={"latency_ms": 150},
            research_evidence=["ev-1"],
            post_state={"latency_ms": 110},
            measurable_delta={"latency_reduction_ms": 40},
            affected_decision_ids=["dec-10"],
            evidence_event_ids=["evt-1"],
        ).to_dict()

        interest_args_1 = {
            "interest_id": "interest-1",
            "owner_goal_id": "goal-1",
            "subgoal_id": "sub-1",
            "observation_research_id": "res-1",
            "new_information": "Information A",
            "inference": "Inference A",
            "interest_proposal": "Proposal A",
            "alignment_check": {"aligned": True},
            "scope_check": {"bounded": True},
            "risk_check": {"acceptable": True},
            "authorization": {"authorized": True, "authorization_event_id": "auth-interest-1"},
        }
        interest_args_2 = dict(interest_args_1, interest_id="interest-2", interest_proposal="Proposal B")

        self.valid_interest_1 = build_interest_derivation(**interest_args_1).to_dict()
        self.valid_interest_2 = build_interest_derivation(**interest_args_2).to_dict()

        self.evidence_package = build_governance_evidence(
            e1_report={"schema_version": "test-e1-v1", "passed": True},
            e2_report={"schema_version": "test-e2-v1", "passed": True},
            e3_report={"schema_version": "test-e3-v1", "passed": True},
        )
        self.provenance_manifest = build_reproducibility_manifest(
            evidence_package=self.evidence_package,
            source_revision="a" * 40,
            workflow_run_id="12345",
            workflow_name="unit-test",
        )
        self.trace = DecisionTrace()
        self.trace.add(TracePhase.GOVERNANCE, "lifecycle_started", {"run_id": "unit-test"})

        self.full_metrics = AutonomyRunMetrics(
            uptime_days=30.0,
            uptime_target_days=30.0,
            cycles=[self.valid_cycle],
            subgoals_count=5,
            research_cycles_count=10,
            learning_records=[self.valid_learning],
            interest_derivations=[self.valid_interest_1, self.valid_interest_2],
            unauthorized_actions_count=0,
            manual_state_mutations=0,
            has_lifecycle_trace=True,
            has_provenance_manifest=True,
            governance_evidence_package=self.evidence_package,
            provenance_manifest=self.provenance_manifest,
            report_exportable=True,
            independent_validation_passed=True,
            preflight_passed=True,
        )

    def test_full_successful_verification_reaches_final_gate(self):
        result = evaluate_autonomy_gates(self.full_metrics, trace=self.trace)

        self.assertTrue(result["dod_passed"])
        self.assertEqual(result["highest_passed_gate"], GATE_FINAL)
        self.assertEqual(len(result["passed_gates"]), 7)
        for gate in (GATE_BASELINE, GATE_CYCLE, GATE_LEARNING, GATE_INTEREST, GATE_PREFLIGHT, GATE_PROOF, GATE_FINAL):
            self.assertTrue(result["gate_states"][gate]["passed"], f"Gate {gate} should pass")

    def test_failed_baseline_blocks_all_subsequent_gates(self):
        metrics = self.full_metrics
        metrics.provenance_manifest = {}

        result = evaluate_autonomy_gates(metrics, trace=self.trace)

        self.assertFalse(result["gate_states"][GATE_BASELINE]["passed"])
        self.assertEqual(result["passed_gates"], [])
        self.assertIsNone(result["highest_passed_gate"])
        for gate in (GATE_CYCLE, GATE_LEARNING, GATE_INTEREST, GATE_PREFLIGHT, GATE_PROOF, GATE_FINAL):
            self.assertFalse(result["gate_states"][gate]["passed"])

    def test_tampered_provenance_manifest_blocks_baseline(self):
        metrics = self.full_metrics
        metrics.provenance_manifest = dict(self.provenance_manifest, manifest_hash="0" * 64)
        result = evaluate_autonomy_gates(metrics, trace=self.trace)
        self.assertFalse(result["gate_states"][GATE_BASELINE]["passed"])
        self.assertFalse(result["dod_status"]["11_provenance_manifest"])

    def test_failed_cycle_blocks_subsequent_gates(self):
        metrics = self.full_metrics
        metrics.cycles = []

        result = evaluate_autonomy_gates(metrics, trace=self.trace)

        self.assertTrue(result["gate_states"][GATE_BASELINE]["passed"])
        self.assertFalse(result["gate_states"][GATE_CYCLE]["passed"])
        self.assertEqual(result["highest_passed_gate"], GATE_BASELINE)
        for gate in (GATE_LEARNING, GATE_INTEREST, GATE_PREFLIGHT, GATE_PROOF, GATE_FINAL):
            self.assertFalse(result["gate_states"][gate]["passed"])

    def test_failed_learning_blocks_subsequent_gates(self):
        metrics = self.full_metrics
        metrics.learning_records = []

        result = evaluate_autonomy_gates(metrics, trace=self.trace)

        self.assertTrue(result["gate_states"][GATE_CYCLE]["passed"])
        self.assertFalse(result["gate_states"][GATE_LEARNING]["passed"])
        self.assertEqual(result["highest_passed_gate"], GATE_CYCLE)

    def test_insufficient_interests_blocks_subsequent_gates(self):
        metrics = self.full_metrics
        metrics.interest_derivations = [self.valid_interest_1]  # Only 1 < required 2

        result = evaluate_autonomy_gates(metrics, trace=self.trace)

        self.assertTrue(result["gate_states"][GATE_LEARNING]["passed"])
        self.assertFalse(result["gate_states"][GATE_INTEREST]["passed"])
        self.assertEqual(result["highest_passed_gate"], GATE_LEARNING)

    def test_failed_preflight_blocks_proof_and_final(self):
        metrics = self.full_metrics
        metrics.preflight_passed = False

        result = evaluate_autonomy_gates(metrics, trace=self.trace)

        self.assertTrue(result["gate_states"][GATE_INTEREST]["passed"])
        self.assertFalse(result["gate_states"][GATE_PREFLIGHT]["passed"])
        self.assertFalse(result["gate_states"][GATE_PROOF]["passed"])
        self.assertFalse(result["gate_states"][GATE_FINAL]["passed"])
        self.assertEqual(result["highest_passed_gate"], GATE_INTEREST)

    def test_manual_state_mutations_fail_proof(self):
        metrics = self.full_metrics
        metrics.manual_state_mutations = 1

        result = evaluate_autonomy_gates(metrics, trace=self.trace)

        self.assertFalse(result["dod_status"]["9_zero_manual_state_mutations"])
        self.assertFalse(result["gate_states"][GATE_PROOF]["passed"])

    def test_evaluates_trace_directly_for_reconstructable_cycles(self):
        trace = DecisionTrace()
        cycle = begin_cycle(trace, intent="Observe system health")
        record_authorization(trace, cycle, authorization_event_id="auth-99", allowed=True)

        metrics = AutonomyRunMetrics(
            has_lifecycle_trace=True,
            has_provenance_manifest=True,
            governance_evidence_package=self.evidence_package,
            provenance_manifest=self.provenance_manifest,
            cycles=[],
        )

        result = evaluate_autonomy_gates(metrics, trace=trace)

        self.assertTrue(result["gate_states"][GATE_CYCLE]["passed"])
        self.assertEqual(result["valid_cycles_count"], 1)

    def test_denied_authorization_invalidates_cycle_and_blocks_cycle_gate(self):
        denied = dict(self.valid_cycle, authorization_allowed=False)
        metrics = self.full_metrics
        metrics.cycles = [denied]

        result = evaluate_autonomy_gates(metrics, trace=self.trace)

        self.assertFalse(result["gate_states"][GATE_CYCLE]["passed"])
        self.assertEqual(result["highest_passed_gate"], GATE_BASELINE)

    def test_missing_authorization_outcome_invalidates_cycle(self):
        incomplete = dict(self.valid_cycle)
        incomplete.pop("authorization_allowed", None)
        metrics = self.full_metrics
        metrics.cycles = [incomplete]

        result = evaluate_autonomy_gates(metrics, trace=self.trace)

        self.assertFalse(result["gate_states"][GATE_CYCLE]["passed"])

    def test_execution_for_different_action_is_rejected(self):
        mismatched = dict(self.valid_cycle, execution_action_id="action:delete-data")
        result = evaluate_autonomy_gates(AutonomyRunMetrics(
            has_lifecycle_trace=True,
            has_provenance_manifest=True,
            governance_evidence_package=self.evidence_package,
            provenance_manifest=self.provenance_manifest,
            cycles=[mismatched],
        ))
        self.assertFalse(result["gate_states"][GATE_CYCLE]["passed"])
        self.assertEqual(result["valid_cycles_count"], 0)

    def test_execution_outside_authorized_scope_is_rejected(self):
        mismatched = dict(self.valid_cycle, execution_scope="filesystem:/")
        result = evaluate_autonomy_gates(AutonomyRunMetrics(
            has_lifecycle_trace=True,
            has_provenance_manifest=True,
            governance_evidence_package=self.evidence_package,
            provenance_manifest=self.provenance_manifest,
            cycles=[mismatched],
        ))
        self.assertFalse(result["gate_states"][GATE_CYCLE]["passed"])
        self.assertEqual(result["valid_cycles_count"], 0)

    def test_execution_before_authorization_is_rejected(self):
        trace = DecisionTrace()
        cycle = begin_cycle(trace, intent="Execute protected action")
        trace.add(
            TracePhase.EXECUTION,
            "autonomy_execution_observed",
            {"cycle_id": cycle.cycle_id, "execution_event_id": "exec-early"},
        )
        record_authorization(trace, cycle, authorization_event_id="auth-late", allowed=True)

        metrics = AutonomyRunMetrics(
            has_lifecycle_trace=True,
            has_provenance_manifest=True,
            governance_evidence_package=self.evidence_package,
            provenance_manifest=self.provenance_manifest,
            cycles=[],
        )
        result = evaluate_autonomy_gates(metrics, trace=trace)

        self.assertFalse(result["gate_states"][GATE_CYCLE]["passed"])
        self.assertEqual(result["valid_cycles_count"], 0)


if __name__ == "__main__":
    unittest.main()
