"""HWIL stages: present → workflow → image."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from harness.boards import (
    STAGES,
    load_board,
    read_stages,
    run_report_dir,
    stage_passed,
    write_stage,
)
from hardware import probe
from human import assent
from software.fixture import run_image_fixture


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
            f"HUMAN_VERIFY=1 make stage BOARD={board_id} STAGE=present",
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
            f"HUMAN_VERIFY=1 make stage BOARD={board_id} STAGE=present",
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


def stage_image(board: dict) -> None:
    board_id = board["id"]
    assent.require_verify("image stage")
    for prior in ("present", "workflow"):
        if not stage_passed(board_id, prior):
            _fail(
                board_id,
                "image",
                f"{prior} stage has not passed",
                f"HUMAN_VERIFY=1 make stage BOARD={board_id} STAGE={prior}",
            )
    # image stage is SIL HID fixture only (not optical / live IR→HID).
    tx_ms = assent.clamp_ir_tx_ms(board)
    duty = assent.clamp_ir_tx_duty(board)

    result = run_image_fixture(board, ir_tx_ms=tx_ms, ir_tx_duty=duty)
    report = run_report_dir(board_id)
    (report / "image.json").write_text(json.dumps(result, indent=2) + "\n")
    captures = report / "captures"
    captures.mkdir(exist_ok=True)
    (captures / "README.md").write_text(
        "Place AUX button capture JSON dumps here during human bring-up.\n"
        "Physical IR evidence is capture/loopback stamps, not the image SIL fixture.\n"
    )
    if not result.get("ok"):
        _fail(
            board_id,
            "image",
            result.get("reason", "image fixture failed"),
            f"HUMAN_VERIFY=1 make hwil BOARD={board_id}",
        )
    _pass(
        board_id,
        "image",
        {
            "report": str(report),
            "ir_tx_ms": tx_ms,
            "ir_tx_duty": duty,
            "fixture": result,
        },
    )


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
    elif args.stage == "image":
        stage_image(board)
    else:
        raise SystemExit(f"unknown stage {args.stage}")


if __name__ == "__main__":
    main()
