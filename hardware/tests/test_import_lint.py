"""Import rules: host software must not pull hardware flash or operator confirmation."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATOR_DIR = REPO_ROOT / "operator"
SOFTWARE_DIR = REPO_ROOT / "software"

FORBIDDEN_HARDWARE = {
    "hardware",
    "hardware.stages",
    "hardware.firmware",
    "hardware.probe",
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                found.add(parts[0])
                if len(parts) > 1:
                    found.add(".".join(parts[:2]))
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            found.add(parts[0])
            if len(parts) > 1:
                found.add(".".join(parts[:2]))
            found.add(node.module)
    return found


def test_operator_assent_does_not_import_hardware():
    for path in sorted(OPERATOR_DIR.glob("*.py")):
        mods = _imports(path)
        assert not (mods & FORBIDDEN_HARDWARE), f"{path.name} imported {mods & FORBIDDEN_HARDWARE}"


def test_software_does_not_import_hardware_operator_or_environment():
    forbidden = FORBIDDEN_HARDWARE | {"operator", "environment"}
    for path in sorted(SOFTWARE_DIR.rglob("*.py")):
        if "tests" in path.parts:
            continue
        mods = _imports(path)
        assert not (mods & forbidden), f"{path.relative_to(REPO_ROOT)} imported {mods & forbidden}"
