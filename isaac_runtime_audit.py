"""Auditable instrumentation contract for Isaac's existing runtime paths.

This module observes execution; it does not authorize actions or introduce a
second executor. Readiness is emitted only after the concrete hook inventory
is verified at kernel startup.
"""
from __future__ import annotations

import functools
import inspect
import os
import uuid
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any, Callable, Iterator

AUDIT_CONTRACT = "isaac.runtime.audit.v1"
REQUIRED_SURFACES = (
    "executor_tools",
    "owner_actions",
    "browser_missions",
    "mcp_tools",
    "state_store_writes",
    "filesystem_state",
)

# Each surface is tied to the actual function(s) wrapped below. Multiple
# functions may contribute to one surface; every listed hook is mandatory.
REQUIRED_HOOKS = {
    "executor_tools": (("tool_runtime", "run_selected_tool"),),
    "owner_actions": (("owner_action", "execute_owner_action"),),
    "browser_missions": (("isaac_core", "IsaacKernel._run_browser_flow_bounded"),),
    "mcp_tools": (("isaac_mcp", "IsaacMCPService.invoke"),),
    "state_store_writes": (
        ("goal_store", "GoalStore.save"),
        ("task_tool_state", "TaskToolStateStore._save"),
        ("memory", "Memory.add_epistemic_memory"),
    ),
    "filesystem_state": (("file_access", "execute_file_command"),),
}


def _emit(event_type: str, payload: dict[str, Any]) -> bool:
    from isaac_30day_evidence import emit_runtime_event
    return emit_runtime_event(event_type, payload)


def _result_ok(result: Any) -> bool:
    if isinstance(result, dict) and isinstance(result.get("ok"), bool):
        return bool(result["ok"])
    if isinstance(result, tuple) and len(result) > 1 and isinstance(result[1], bool):
        return bool(result[1])
    return True


_ACTION_ID: ContextVar[str] = ContextVar("isaac_runtime_action_id", default="")


def current_action_id() -> str:
    """Return the action ID propagated through the current async call chain."""
    return _ACTION_ID.get()


@contextmanager
def bind_action_id(action_id: str) -> Iterator[None]:
    """Propagate the executor's real authorization ID into nested runtime hooks."""
    token = _ACTION_ID.set(str(action_id or ""))
    try:
        yield
    finally:
        _ACTION_ID.reset(token)


def record_tool_authorization_decision(
    action_id: str,
    allowed: bool,
    surface: str,
    operation: str,
    reason: str = "",
    parent_action_id: str = "",
) -> None:
    payload = {
        "action_id": str(action_id or ""),
        "allowed": bool(allowed),
        "surface": surface,
        "operation": operation,
        "reason": str(reason or "")[:160],
    }
    if parent_action_id:
        payload["parent_action_id"] = str(parent_action_id)
    _emit("tool_authorization_decision", payload)


def record_tool_execution_result(
    action_id: str,
    invoked: bool,
    ok: bool,
    surface: str,
    operation: str,
    parent_action_id: str = "",
) -> None:
    payload = {
        "action_id": str(action_id or ""),
        "invoked": bool(invoked),
        "ok": bool(ok),
        "surface": surface,
        "operation": operation,
    }
    if parent_action_id:
        payload["parent_action_id"] = str(parent_action_id)
    _emit("tool_execution_result", payload)


def _record_boundary_decision(surface: str, operation: str, action_id: str, result: Any) -> None:
    denied = False
    if surface == "browser_missions":
        denied = bool(
            isinstance(result, dict)
            and (
                result.get("source") == "constitution"
                or "Verfassung blockiert" in str(result.get("error") or "")
            )
        )
    elif surface == "filesystem_state":
        denied = bool(
            isinstance(result, tuple)
            and result
            and "Verfassung blockiert" in str(result[0])
        )
    else:
        return

    # A positive authorization event must come from the actual policy gate,
    # not from the absence of a denial-shaped return value.
    if denied:
        record_tool_authorization_decision(
            action_id, False, surface, operation, "constitution_denied"
        )
        record_tool_execution_result(
            action_id, invoked=False, ok=False, surface=surface, operation=operation
        )
    else:
        record_tool_execution_result(
            action_id, invoked=True, ok=_result_ok(result), surface=surface, operation=operation
        )


def audited_surface(surface: str) -> Callable:
    """Decorate a real runtime entry point with start/finish evidence events."""
    if surface not in REQUIRED_SURFACES:
        raise ValueError("unknown runtime audit surface: %s" % surface)

    def decorate(function: Callable) -> Callable:
        operation = function.__name__

        def started() -> tuple[str, Token]:
            action_id = current_action_id() or uuid.uuid4().hex
            token = _ACTION_ID.set(action_id)
            try:
                _emit("runtime_surface_event", {
                    "contract": AUDIT_CONTRACT,
                    "surface": surface,
                    "operation": operation,
                    "phase": "started",
                    "action_id": action_id,
                })
            except Exception:
                _ACTION_ID.reset(token)
                raise
            return action_id, token

        def completed(
            action_id: str, phase: str, ok: bool, error_type: str = ""
        ) -> None:
            payload = {
                "contract": AUDIT_CONTRACT,
                "surface": surface,
                "operation": operation,
                "phase": phase,
                "action_id": action_id,
                "ok": bool(ok),
            }
            if error_type:
                payload["error_type"] = error_type
            _emit("runtime_surface_event", payload)

        if inspect.iscoroutinefunction(function):
            @functools.wraps(function)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                action_id, token = started()
                phase, ok, error_type = "completed", True, ""
                try:
                    result = await function(*args, **kwargs)
                    ok = _result_ok(result)
                    _record_boundary_decision(surface, operation, action_id, result)
                    return result
                except Exception as exc:
                    phase, ok, error_type = "failed", False, type(exc).__name__
                    raise
                finally:
                    try:
                        completed(action_id, phase, ok, error_type)
                    finally:
                        _ACTION_ID.reset(token)
            wrapped = async_wrapper
        else:
            @functools.wraps(function)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                action_id, token = started()
                phase, ok, error_type = "completed", True, ""
                try:
                    result = function(*args, **kwargs)
                    ok = _result_ok(result)
                    _record_boundary_decision(surface, operation, action_id, result)
                    return result
                except Exception as exc:
                    phase, ok, error_type = "failed", False, type(exc).__name__
                    raise
                finally:
                    try:
                        completed(action_id, phase, ok, error_type)
                    finally:
                        _ACTION_ID.reset(token)
            wrapped = sync_wrapper

        setattr(wrapped, "__isaac_audit_surface__", surface)
        setattr(wrapped, "__isaac_audit_contract__", AUDIT_CONTRACT)
        return wrapped

    return decorate


def audit_hook_inventory() -> dict[str, Any]:
    """Return the actual decorated entry points; never infer from test fixtures."""
    import importlib

    found: dict[str, list[str]] = {}
    missing: list[str] = []
    for surface, hooks in REQUIRED_HOOKS.items():
        found[surface] = []
        for module_name, dotted_name in hooks:
            try:
                target: Any = importlib.import_module(module_name)
                for part in dotted_name.split("."):
                    target = getattr(target, part)
                if getattr(target, "__isaac_audit_surface__", None) != surface:
                    missing.append(module_name + "." + dotted_name.split(".")[-1])
                else:
                    found[surface].append(module_name + "." + dotted_name.split(".")[-1])
            except (ImportError, AttributeError):
                missing.append(module_name + "." + dotted_name.split(".")[-1])
    complete = not missing and all(found.get(surface) for surface in REQUIRED_SURFACES)
    return {
        "contract": AUDIT_CONTRACT,
        "coverage_complete": complete,
        "surfaces": [surface for surface in REQUIRED_SURFACES if found.get(surface)],
        "hooks": found,
        "missing_hooks": missing,
    }


def emit_proof_audit_readiness() -> dict[str, Any]:
    """Emit readiness only when every production entry point carries its hook."""
    inventory = audit_hook_inventory()
    if not inventory["coverage_complete"]:
        if os.environ.get("ISAAC_30DAY_OFFICIAL", "").strip() == "1":
            raise RuntimeError(
                "official proof blocked: runtime audit hooks missing: "
                + ", ".join(inventory["missing_hooks"])
            )
        return inventory
    _emit("proof_audit_readiness", {
        **inventory,
        "coverage_complete": True,
        "verified_at_runtime": True,
    })
    return inventory
