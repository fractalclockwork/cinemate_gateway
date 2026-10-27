"""Archive / firmware cache path helpers."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = REPO_ROOT / "archive" / "cache"


def circuitpython_uf2_hint() -> Path:
    """Expected local cache path for Pico CircuitPython UF2 (may not exist yet)."""
    return ARCHIVE / "circuitpython" / "raspberry_pi_pico.uf2"
