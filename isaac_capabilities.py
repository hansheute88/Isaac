"""Isaac 2.0 capability model.

R/W/X is an additive capability layer. It does not replace privilege.py,
security_policy.py or constitution.py. Those remain authoritative gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class Capability(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"


@dataclass(frozen=True)
class RWXPolicy:
    """Explicit capabilities for one resource."""

    resource: str
    read: bool = False
    write: bool = False
    execute: bool = False
    source: str = "default"
    version: int = 1

    def allows(self, capability: Capability | str) -> bool:
        cap = Capability(capability)
        return {
            Capability.READ: self.read,
            Capability.WRITE: self.write,
            Capability.EXECUTE: self.execute,
        }[cap]

    def as_dict(self) -> dict[str, Any]:
        return {
            "resource": self.resource,
            "read": self.read,
            "write": self.write,
            "execute": self.execute,
            "source": self.source,
            "version": self.version,
        }


@dataclass(frozen=True)
class CapabilityRequest:
    resource: str
    capability: Capability | str
    principal: str = "isaac"
    reason: str = ""
    task_id: str = ""

    def normalized_capability(self) -> Capability:
        return Capability(self.capability)


@dataclass(frozen=True)
class CapabilityDecision:
    allowed: bool
    resource: str
    capability: Capability
    principal: str
    reason: str
    policy_source: str
    policy_version: int
    task_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "resource": self.resource,
            "capability": self.capability.value,
            "principal": self.principal,
            "reason": self.reason,
            "policy_source": self.policy_source,
            "policy_version": self.policy_version,
            "task_id": self.task_id,
        }


class RWXRegistry:
    """In-memory registry; persistence is intentionally deferred to A1."""

    def __init__(self, policies: Mapping[str, RWXPolicy] | None = None):
        self._policies: dict[str, RWXPolicy] = dict(policies or {})

    def set_policy(self, policy: RWXPolicy) -> RWXPolicy:
        if not policy.resource.strip():
            raise ValueError("resource must not be empty")
        self._policies[policy.resource] = policy
        return policy

    def get_policy(self, resource: str) -> RWXPolicy:
        return self._policies.get(
            resource,
            RWXPolicy(resource=resource, source="implicit-deny"),
        )

    def evaluate(self, request: CapabilityRequest) -> CapabilityDecision:
        cap = request.normalized_capability()
        policy = self.get_policy(request.resource)
        allowed = policy.allows(cap)
        reason = (
            "capability granted by policy"
            if allowed
            else "capability denied by policy"
        )
        return CapabilityDecision(
            allowed=allowed,
            resource=request.resource,
            capability=cap,
            principal=request.principal,
            reason=reason,
            policy_source=policy.source,
            policy_version=policy.version,
            task_id=request.task_id,
        )


def evaluate_with_audit(registry: RWXRegistry, request: CapabilityRequest) -> CapabilityDecision:
    """Evaluate R/W/X and emit an immutable audit event; no legacy gate is bypassed."""
    decision = registry.evaluate(request)
    from audit import AuditLog

    AuditLog._record("capability", decision.as_dict())
    return decision


def capability_from_legacy_action(action: str) -> Capability:
    """Map existing privileged actions to R/W/X without changing their gates."""
    normalized = (action or "").strip().lower()
    if normalized in {"read_memory", "read_audit", "file_read"}:
        return Capability.READ
    if normalized in {"write_memory", "file_write"}:
        return Capability.WRITE
    if normalized in {"execute_code", "system_command", "browser_navigate"}:
        return Capability.EXECUTE
    raise ValueError(f"No R/W/X mapping for legacy action: {action!r}")
