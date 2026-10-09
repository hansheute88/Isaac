"""Isaac 30-Day Autonomy — Bounded Interest Derivation Contract.

This module models and validates the 11-step derivation chain required for
a new bounded interest to be created from an owner goal:

OWNER GOAL -> SUBGOAL -> OBSERVATION/RESEARCH -> NEW INFORMATION -> INFERENCE ->
INTEREST PROPOSAL -> ALIGNMENT CHECK -> SCOPE CHECK -> RISK CHECK ->
AUTHORIZATION -> INTEREST CREATED
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import uuid

from decision_trace import DecisionTrace, TracePhase

INTEREST_SCHEMA = "isaac.autonomy.interest.v1"


@dataclass(frozen=True)
class InterestDerivation:
    interest_id: str
    owner_goal_id: str
    subgoal_id: str
    observation_research_id: str
    new_information: str
    inference: str
    interest_proposal: str
    alignment_check: dict[str, Any]
    scope_check: dict[str, Any]
    risk_check: dict[str, Any]
    authorization: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": INTEREST_SCHEMA,
            "interest_id": self.interest_id,
            "owner_goal_id": self.owner_goal_id,
            "subgoal_id": self.subgoal_id,
            "observation_research_id": self.observation_research_id,
            "new_information": self.new_information,
            "inference": self.inference,
            "interest_proposal": self.interest_proposal,
            "alignment_check": dict(self.alignment_check or {}),
            "scope_check": dict(self.scope_check or {}),
            "risk_check": dict(self.risk_check or {}),
            "authorization": dict(self.authorization or {}),
        }


def validate_interest_derivation(derivation: InterestDerivation | dict[str, Any]) -> dict[str, Any]:
    data = derivation.to_dict() if isinstance(derivation, InterestDerivation) else dict(derivation or {})

    missing: list[str] = []
    errors: list[str] = []

    if data.get("schema") != INTEREST_SCHEMA:
        errors.append("invalid_schema")

    string_fields = (
        "interest_id",
        "owner_goal_id",
        "subgoal_id",
        "observation_research_id",
        "new_information",
        "inference",
        "interest_proposal",
    )
    for field in string_fields:
        if not str(data.get(field) or "").strip():
            missing.append(field)

    align = data.get("alignment_check")
    if not isinstance(align, dict) or not align:
        missing.append("alignment_check")
    elif not align.get("aligned"):
        errors.append("alignment_check_failed")

    scope = data.get("scope_check")
    if not isinstance(scope, dict) or not scope:
        missing.append("scope_check")
    elif not scope.get("bounded"):
        errors.append("scope_check_failed")

    risk = data.get("risk_check")
    if not isinstance(risk, dict) or not risk:
        missing.append("risk_check")
    elif not risk.get("acceptable"):
        errors.append("risk_check_failed")

    auth = data.get("authorization")
    if not isinstance(auth, dict) or not auth:
        missing.append("authorization")
    elif not auth.get("authorized"):
        errors.append("authorization_failed")

    is_valid = (len(missing) == 0) and (len(errors) == 0)
    return {
        "schema": INTEREST_SCHEMA,
        "valid": is_valid,
        "missing": missing,
        "errors": errors,
        "interest_id": str(data.get("interest_id") or ""),
    }


def build_interest_derivation(
    *,
    interest_id: str = "",
    owner_goal_id: str,
    subgoal_id: str,
    observation_research_id: str,
    new_information: str,
    inference: str,
    interest_proposal: str,
    alignment_check: dict[str, Any],
    scope_check: dict[str, Any],
    risk_check: dict[str, Any],
    authorization: dict[str, Any],
) -> InterestDerivation:
    iid = interest_id.strip() if interest_id else f"interest_{uuid.uuid4().hex}"
    return InterestDerivation(
        interest_id=iid,
        owner_goal_id=owner_goal_id,
        subgoal_id=subgoal_id,
        observation_research_id=observation_research_id,
        new_information=new_information,
        inference=inference,
        interest_proposal=interest_proposal,
        alignment_check=alignment_check,
        scope_check=scope_check,
        risk_check=risk_check,
        authorization=authorization,
    )


def record_interest_derivation(
    trace: DecisionTrace,
    derivation: InterestDerivation | dict[str, Any],
) -> dict[str, Any]:
    validation = validate_interest_derivation(derivation)
    payload = derivation.to_dict() if isinstance(derivation, InterestDerivation) else dict(derivation)
    payload["validation"] = validation
    trace.add(
        TracePhase.MOTIVATION,
        "interest_derivation_recorded",
        payload,
    )
    return validation
