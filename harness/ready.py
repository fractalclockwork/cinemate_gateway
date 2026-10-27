"""Stage-record gates for lessons and consumers."""

from __future__ import annotations

import json
from pathlib import Path

from harness.boards import ORDER, reports_root, stage_passed


def _next_command(board_id: str, stage: str) -> str:
    if stage == "image":
        return f"HUMAN_VERIFY=1 make hwil BOARD={board_id}"
    return f"make stage BOARD={board_id} STAGE={stage}"


def require_image(board_id: str = "pico") -> None:
    """Require SIL `image` stage pass (host HID fixture — not live IR)."""
    if stage_passed(board_id, "image"):
        return
    for stage in ("present", "workflow", "image"):
        if not stage_passed(board_id, stage):
            raise SystemExit(
                f"{board_id} {stage} stage has not passed; "
                f"refusing consumer. Next: {_next_command(board_id, stage)}"
            )
    raise SystemExit(
        f"{board_id} image stage has not passed; "
        f"refusing consumer. Next: {_next_command(board_id, 'image')}"
    )


def latest_validated_path(board_id: str = "pico") -> Path | None:
    """Newest captures/validated.json under reports/<board>/ with any true row."""
    root = reports_root() / board_id
    if not root.is_dir():
        return None
    candidates: list[tuple[float, Path]] = []
    for path in root.glob("*/captures/validated.json"):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        buttons = data.get("buttons") or []
        if any(bool(row.get("validated")) for row in buttons):
            candidates.append((path.stat().st_mtime, path))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def require_ir_map(board_id: str = "pico") -> Path:
    """Require a capture stamp with ≥1 validated IR button (physical map evidence)."""
    path = latest_validated_path(board_id)
    if path is not None:
        return path
    raise SystemExit(
        f"{board_id} IR map evidence missing "
        f"(no reports/{board_id}/*/captures/validated.json with validated buttons). "
        f"Next: HUMAN_VERIFY=1 make capture MODE=confirm "
        f"or MODE=validate after present/workflow"
    )


def require_lessons() -> None:
    for board_id in ORDER:
        require_image(board_id)
