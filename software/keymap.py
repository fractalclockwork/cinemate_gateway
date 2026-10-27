"""Load and validate IR→HID keymaps."""

from __future__ import annotations

from pathlib import Path

import yaml

from software.decode import IrFrame, frame_key
from software.hid import HidAction, resolve_action

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPO_ROOT / "software" / "keymap.example.yaml"
ACTIVE = REPO_ROOT / "software" / "keymap.yaml"


def load_keymap(path: Path | None = None) -> dict:
    target = path or (ACTIVE if ACTIVE.is_file() else EXAMPLE)
    data = yaml.safe_load(target.read_text()) or {}
    if "map" not in data or not isinstance(data["map"], dict):
        raise ValueError(f"{target} missing map: dict")
    # Validate all actions resolve.
    for ir_key, action_name in data["map"].items():
        resolve_action(str(action_name))
        if not isinstance(ir_key, str) or ":" not in ir_key:
            raise ValueError(f"bad IR key {ir_key!r}; expected protocol:aa:cc")
    return data


def lookup(frame: IrFrame, keymap: dict | None = None) -> HidAction | None:
    data = keymap if keymap is not None else load_keymap()
    ignore = set(data.get("ignore") or [])
    key = frame_key(frame)
    if key in ignore:
        return None
    action_name = data["map"].get(key)
    if action_name is None:
        return None
    return resolve_action(str(action_name))
