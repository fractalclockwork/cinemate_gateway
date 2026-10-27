"""Board manifests and stage records for the Pico bench."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
HARDWARE_ROOT = REPO_ROOT / "hardware"
STAGES = ("present", "workflow")


def board_path(board_id: str) -> Path:
    path = HARDWARE_ROOT / "boards" / f"{board_id}.yaml"
    if not path.is_file():
        raise SystemExit(f"unknown board {board_id}")
    return path


def load_board(board_id: str) -> dict:
    data = yaml.safe_load(board_path(board_id).read_text())
    data["id"] = board_id
    return data


def reports_root() -> Path:
    return REPO_ROOT / "reports"


def stage_path(board_id: str) -> Path:
    return reports_root() / board_id / "stage.json"


def run_report_dir(board_id: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = reports_root() / board_id / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_stages(board_id: str) -> dict:
    path = stage_path(board_id)
    if not path.is_file():
        return {"board": board_id, "stages": {}}
    return json.loads(path.read_text())


def write_stage(board_id: str, stage: str, record: dict) -> dict:
    document = read_stages(board_id)
    document["board"] = board_id
    document.setdefault("stages", {})[stage] = record
    path = stage_path(board_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n")
    return document


def stage_passed(board_id: str, stage: str) -> bool:
    record = read_stages(board_id)["stages"].get(stage) or {}
    return record.get("status") == "pass"
