"""
tools/check_imports.py – Dependency-Graph Validator

Enforces the immutable dependency order:
  config → audit → ports → memory → executor → kernel → agents

Run: python tools/check_imports.py
"""

import ast
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple
from collections import defaultdict


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

# Layers in dependency order (lower index can import from higher index)
DEPENDENCY_LAYERS = [
    "config",
    "audit",
    "ports",
    "memory",
    "executor",
    "kernel",
    "agents",
]

# Mapping from layer name to directory prefixes
LAYER_PREFIXES = {
    "config": ["core/config", "config/"],
    "audit": ["core/audit", "audit/"],
    "ports": ["core/ports.py"],
    "memory": ["core/memory", "memory/"],
    "executor": ["core/executor", "executor/"],
    "kernel": ["core/kernel", "kernel/"],
    "agents": ["core/agents", "agents/"],
}

# Third-party imports that are always allowed
ALLOWED_THIRD_PARTY = {
    "typing", "dataclasses", "enum", "abc", "collections",
    "torch", "snntorch", "chromadb", "sqlite3", "json",
    "logging", "pathlib", "datetime", "asyncio", "functools",
}


# ════════════════════════════════════════════════════════════════════════════
# AST PARSER
# ════════════════════════════════════════════════════════════════════════════

class ImportCollector(ast.NodeVisitor):
    """Extract all imports from a Python file."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.imports: Set[str] = set()

    def visit_Import(self, node):
        """Handle: import foo, import foo.bar"""
        for alias in node.names:
            self.imports.add(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Handle: from foo import bar"""
        if node.module:
            self.imports.add(node.module.split(".")[0])
        self.generic_visit(node)


def extract_imports(filepath: Path) -> Set[str]:
    """Parse Python file and extract all import names."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))
        collector = ImportCollector(str(filepath))
        collector.visit(tree)
        return collector.imports
    except Exception as e:
        print(f"⚠️  Error parsing {filepath}: {e}")
        return set()


# ════════════════════════════════════════════════════════════════════════════
# DEPENDENCY ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

def get_layer(filepath: Path) -> str:
    """Determine which layer a file belongs to."""
    filepath_str = str(filepath).replace("\\", "/")

    for layer, prefixes in LAYER_PREFIXES.items():
        for prefix in prefixes:
            if filepath_str.startswith(prefix):
                return layer

    return None  # Unknown layer


def is_internal_import(module_name: str, filepath: Path) -> bool:
    """Check if import is internal (Isaac) vs external."""
    # Map module names to file paths
    if module_name in ["core", "config", "audit", "ports", "memory", "executor", "kernel", "agents"]:
        return True
    return False


def analyze_file(filepath: Path) -> Tuple[str, Set[str], Set[str]]:
    """
    Analyze a file and return:
      (layer, internal_imports, external_imports)
    """
    layer = get_layer(filepath)
    if not layer:
        return None, set(), set()

    imports = extract_imports(filepath)

    internal_imports = set()
    external_imports = set()

    for imp in imports:
        if is_internal_import(imp, filepath):
            internal_imports.add(imp)
        elif imp not in ALLOWED_THIRD_PARTY:
            external_imports.add(imp)

    return layer, internal_imports, external_imports


# ════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ════════════════════════════════════════════════════════════════════════════

def validate_dependency_order(
    file_layer: str,
    imported_modules: Set[str]
) -> List[str]:
    """
    Check if imports violate dependency order.

    Returns list of violations.
    """
    violations = []

    file_layer_index = DEPENDENCY_LAYERS.index(file_layer)

    for imported_module in imported_modules:
        # Find which layer the import belongs to
        for layer, prefixes in LAYER_PREFIXES.items():
            for prefix in prefixes:
                if imported_module.startswith(layer) or prefix.startswith(imported_module):
                    imported_layer_index = DEPENDENCY_LAYERS.index(layer)

                    # Check: file_layer can only import from layers at same index or higher
                    if file_layer_index > imported_layer_index:
                        violations.append(
                            f"  ❌ {file_layer} (index {file_layer_index}) "
                            f"cannot import from {layer} (index {imported_layer_index})"
                        )
                    break

    return violations


def check_circular_imports(dependency_graph: Dict[str, Set[str]]) -> List[str]:
    """
    Detect circular dependencies using DFS.

    Returns list of cycles found.
    """
    cycles = []
    visited = set()
    rec_stack = set()

    def dfs(node: str, path: List[str]) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in dependency_graph.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor, path.copy())
            elif neighbor in rec_stack:
                cycle = " → ".join(path + [neighbor])
                cycles.append(f"  ⭕ Cycle detected: {cycle}")

        rec_stack.remove(node)

    for node in dependency_graph:
        if node not in visited:
            dfs(node, [])

    return cycles


# ════════════════════════════════════════════════════════════════════════════
# MAIN CHECK
# ════════════════════════════════════════════════════════════════════════════

def main():
    """Run full dependency check."""
    root = Path(".")
    python_files = list(root.rglob("*.py"))

    # Filter out test files and vendor code
    python_files = [
        f for f in python_files
        if not any(part.startswith(".") for part in f.parts)
        and "venv" not in f.parts
        and "node_modules" not in f.parts
    ]

    print("\n" + "=" * 80)
    print("ISAAC Dependency Checker – Validating Import Order")
    print("=" * 80)

    violations = []
    dependency_graph = defaultdict(set)
    files_by_layer = defaultdict(list)

    # Analyze each file
    for filepath in sorted(python_files):
        layer, internal_imports, external_imports = analyze_file(filepath)

        if not layer:
            continue

        files_by_layer[layer].append(filepath)

        # Add to dependency graph
        for imp in internal_imports:
            imp_layer = None
            for l, prefixes in LAYER_PREFIXES.items():
                if any(imp.startswith(p.split("/")[0]) for p in prefixes):
                    imp_layer = l
                    break
            if imp_layer:
                dependency_graph[layer].add(imp_layer)

        # Validate this file
        layer_violations = validate_dependency_order(layer, internal_imports)
        violations.extend(layer_violations)

        # Warn about external imports (not in allowed list)
        if external_imports:
            print(f"\n⚠️  {filepath} imports external: {external_imports}")

    # Print summary by layer
    print("\n📦 Files by Layer:")
    for layer in DEPENDENCY_LAYERS:
        count = len(files_by_layer[layer])
        print(f"  {layer:12} : {count:3} files")

    # Check for circular imports
    print("\n🔄 Checking for circular dependencies...")
    cycles = check_circular_imports(dependency_graph)
    if cycles:
        violations.extend(cycles)
        for cycle in cycles:
            print(cycle)
    else:
        print("  ✅ No circular dependencies detected")

    # Print violations
    if violations:
        print("\n❌ VIOLATIONS FOUND:")
        for v in violations:
            print(v)
        print("\n" + "=" * 80)
        print(f"FAILED: {len(violations)} dependency violations")
        print("=" * 80)
        return 1

    # Success
    print("\n✅ ALL CHECKS PASSED")
    print("  → Dependency order is correct")
    print("  → No circular imports")
    print("=" * 80 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
