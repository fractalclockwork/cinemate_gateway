"""HWIL stages: present, then workflow."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from hardware import probe
from hardware.records import (
    STAGES,
    load_board,
    read_stages,
    run_report_dir,
    stage_passed,
    write_stage,
)
from operator import assent


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fail(board_id: str, stage: str, reason: str, next_cmd: str) -> None:
    write_stage(
        board_id,
        stage,
        {
            "status": "fail",
            "reason": reason,
            "next": next_cmd,
            "at": _utc_now(),
        },
    )
    raise SystemExit(f"{board_id} {stage} FAIL: {reason}. Next: {next_cmd}")


def _pass(board_id: str, stage: str, metrics: dict | None = None) -> None:
    record = {"status": "pass", "at": _utc_now()}
    if metrics:
        record["metrics"] = metrics
    write_stage(board_id, stage, record)
    print(f"{board_id} {stage}: pass")


def stage_present(board: dict) -> None:
    board_id = board["id"]
    assent.require_verify("present stage")
    found = probe.find_pico(board)
    if not found:
        _fail(
            board_id,
            "present",
            "no Pico USB device matching board YAML (or Adafruit CircuitPython VID)",
            f"OPERATOR_VERIFY=1 make stage BOARD={board_id} STAGE=present",
        )
    _pass(board_id, "present", {"usb": found})


def stage_workflow(board: dict) -> None:
    board_id = board["id"]
    assent.require_verify("workflow stage")
    if not stage_passed(board_id, "present"):
        _fail(
            board_id,
            "workflow",
            "present stage has not passed",
            f"OPERATOR_VERIFY=1 make stage BOARD={board_id} STAGE=present",
        )
    present = read_stages(board_id)["stages"].get("present") or {}
    usb = (present.get("metrics") or {}).get("usb")
    mount = probe.circuitpy_mount()
    firmware_dir = Path(__file__).resolve().parent / "firmware" / "pico"
    identity = {
        "usb": usb,
        "circuitpy_mount": str(mount) if mount else None,
        "firmware_tree": str(firmware_dir),
        "firmware_files": sorted(p.name for p in firmware_dir.glob("*.py")),
        "pins": board.get("pins"),
        "note": "USB identity is the present-stage record. CIRCUITPY mount is a workflow fact. No HID spam.",
    }
    report = run_report_dir(board_id)
    (report / "workflow.json").write_text(json.dumps(identity, indent=2) + "\n")
    _pass(board_id, "workflow", {"report": str(report), **identity})


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run Pico IR gateway HWIL stage")
    parser.add_argument("--board", default="pico")
    parser.add_argument("--stage", choices=STAGES, required=True)
    args = parser.parse_args(argv)
    board = load_board(args.board)
    if args.stage == "present":
        stage_present(board)
    elif args.stage == "workflow":
        stage_workflow(board)
    else:
        raise SystemExit(f"unknown stage {args.stage}")


if __name__ == "__main__":
    main()
