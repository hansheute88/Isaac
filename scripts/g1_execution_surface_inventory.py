#!/usr/bin/env python3
"""Read-only G1 candidate inventory. AST evidence, NOT a complete call graph.

Usage: python3 scripts/g1_execution_surface_inventory.py --root . --output /tmp/isaac-g1.json
No Isaac modules are imported or executed. All candidates require manual tracing.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

EXCLUDED_PARTS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".worktrees", "worktrees"}
ENTRYPOINTS = {
    "run_selected_tool", "_run_selected_tool_body", "run_tool", "_run_registry_tool",
    "invoke_mcp_tool", "execute_owner_action", "execute_file_command", "apply_edit",
    "apply_from_model_text", "git_commit", "git_restore", "run_git_ops",
    "run_code_edit_from_model_text", "run_parsed_git_op", "_execute_code",
    "_execute_file", "_maybe_use_tool", "_check_tool_execution_capability",
    "_check_required_capabilities", "execute",
}
EFFECT_CALLS = {
    "subprocess.run", "subprocess.call", "subprocess.check_call",
    "subprocess.check_output", "subprocess.Popen", "asyncio.create_subprocess_exec",
    "asyncio.create_subprocess_shell", "os.system", "os.popen", "os.remove",
    "os.unlink", "os.rename", "os.replace", "shutil.rmtree", "shutil.move",
    "shutil.copy", "shutil.copy2", "os.execv", "os.execve", "os.spawnv",
    "eval", "exec", "open", "Path.write_text", "Path.write_bytes",
}
GUARD_MARKERS = {
    "evaluate_with_audit", "_check_tool_execution_capability",
    "_check_required_capabilities", "apply_constitution_gate",
    "constitution_gate_for_tool", "require", "verify_chain",
}


def dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = dotted(node.value)
        return f"{left}.{node.attr}" if left else node.attr
    return ""


def scan(root: Path) -> dict:
    root = root.resolve()
    files = 0
    parse_errors = []
    defs = []
    calls = []
    for file in sorted(root.rglob("*.py")):
        rel = file.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        files += 1
        try:
            tree = ast.parse(file.read_text(encoding="utf-8-sig"), filename=str(rel))
        except (SyntaxError, UnicodeError, OSError) as exc:
            parse_errors.append({"file": str(rel), "error": str(exc)})
            continue
        category = "test" if (file.name.startswith(("test_", "tests_")) or "tests" in rel.parts) else "production"

        class Visitor(ast.NodeVisitor):
            def __init__(self):
                self.stack = []

            def visit_ClassDef(self, node):
                self.stack.append(node.name)
                self.generic_visit(node)
                self.stack.pop()

            def visit_FunctionDef(self, node):
                self._function(node)

            def visit_AsyncFunctionDef(self, node):
                self._function(node)

            def _function(self, node):
                owner = ".".join(self.stack + [node.name])
                defs.append({"file": str(rel), "line": node.lineno, "symbol": owner,
                             "category": category, "entry_candidate": node.name in ENTRYPOINTS})
                self.stack.append(node.name)
                self.generic_visit(node)
                self.stack.pop()

            def visit_Call(self, node):
                target = dotted(node.func)
                name = target.rsplit(".", 1)[-1]
                special = target in EFFECT_CALLS or name in ENTRYPOINTS or name in GUARD_MARKERS
                # Common direct write/network methods: receiver type is not inferred.
                heuristic = name in {"write_text", "write_bytes", "unlink", "remove", "delete",
                                     "rmtree", "post", "put", "patch", "send", "request", "execute_script"}
                if special or heuristic:
                    kind = ("effect_candidate" if target in EFFECT_CALLS or heuristic
                            else "guard_reference" if name in GUARD_MARKERS
                            else "execution_reference")
                    calls.append({"file": str(rel), "line": node.lineno,
                                  "caller": ".".join(self.stack) or "<module>",
                                  "callee": target, "kind": kind, "category": category})
                self.generic_visit(node)

        Visitor().visit(tree)
    return {"schema": "isaac-g1-ast-candidates-v1", "root": str(root),
            "files_scanned": files, "parsed_files": files - len(parse_errors),
            "parse_errors": parse_errors, "definitions": defs, "call_candidates": calls,
            "complete_call_graph": False,
            "limitations": [
                "No dynamic dispatch, reflection, import alias resolution, dependency or C-extension analysis",
                "Reachability and effective authorization are NOT proven by AST matches",
                "False positives expected for generic names like execute/post/send",
                "Manual entrypoint->guard->effect review and runtime tests required",
            ]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = scan(args.root)
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    if result["parse_errors"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
