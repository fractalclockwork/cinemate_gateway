"""Operator verification and permissions before a hardware test runs.

The operator validates and verifies the bench. The Pico is the device under
test. USB presence is the present stage, not a flag in this module. Agents
must not invent YES, bench verification, flash permission, or IR path
confirmation. Only a person may set HUMAN_* flags or type YES at the prompt.
A HWIL test waits until HUMAN_VERIFY=1.
"""

from __future__ import annotations

import os
import sys

VERIFY_ENV = "HUMAN_VERIFY"
FLASH_ENV = "HUMAN_FLASH"
IR_PATH_ENV = "HUMAN_IR_PATH"
BUTTON_OK_ENV = "HUMAN_BUTTON_OK"
SIM_ENV = "IR_GATEWAY_HWIL_SIM"


def is_sim() -> bool:
    return os.environ.get(SIM_ENV) == "1"


def require_verify(reason: str = "operator verifies the bench") -> None:
    """Stop until the operator has verified the bench for this test."""
    if os.environ.get(VERIFY_ENV) != "1":
        raise SystemExit(
            f"set {VERIFY_ENV}=1 before this test begins ({reason}). "
            "The operator verifies the bench, then the test may start."
        )


def require_flash(board_id: str = "pico") -> None:
    if os.environ.get(FLASH_ENV) != "1":
        raise SystemExit(
            f"set {FLASH_ENV}=1 before firmware write for {board_id}. "
            "Operator allows the firmware write."
        )


def require_ir_path(reason: str = "IR RX aimed; LED safe for short optical loopback") -> None:
    if os.environ.get(IR_PATH_ENV) != "1":
        raise SystemExit(
            f"set {IR_PATH_ENV}=1 before IR HWIL ({reason}). "
            "Operator asserts the optical path is set up and phase-1 LED use is loopback-only."
        )


def confirm_ir(reason: str) -> None:
    """Require explicit operator confirmation before IR LED energize."""
    if is_sim():
        return
    if os.environ.get(IR_PATH_ENV) == "1":
        return
    if sys.stdin.isatty():
        prompt = (
            f"IR path about to run: {reason}\n"
            "Confirm RX/LED optical path (phase 1: loopback only, not CineMate TX). "
            f"Type YES to proceed, or set {IR_PATH_ENV}=1 for a scripted run: "
        )
        answer = input(prompt)
        if answer.strip() != "YES":
            raise SystemExit("refusing IR path without YES")
        return
    raise SystemExit(
        f"set {IR_PATH_ENV}=1 before IR HWIL ({reason}); non-interactive stdin"
    )


def confirm_button(button: str, frame_key: str, hid: str | None) -> None:
    """Optional strict gate. Capture accepts on agreeing a/b samples instead."""
    if is_sim():
        return
    if os.environ.get(BUTTON_OK_ENV) == "1":
        return
    hid_note = hid if hid else "(no HID binding in the selected profile)"
    prompt = (
        f"Button {button}: decode {frame_key} → HID {hid_note}. "
        "Confirm this is the key you pressed and the decode looks right. "
        f"Type YES, or set {BUTTON_OK_ENV}=1 for a scripted run: "
    )
    if sys.stdin.isatty():
        answer = input(prompt)
        if answer.strip() != "YES":
            raise SystemExit(f"refusing to validate {button} without YES")
        return
    raise SystemExit(
        f"set {BUTTON_OK_ENV}=1 to validate {button}={frame_key}; non-interactive stdin"
    )


def clamp_ir_tx_ms(board: dict, requested_ms: float | None = None) -> float:
    if requested_ms is None:
        requested_ms = float(board.get("ir_tx_ms", 50))
    else:
        requested_ms = float(requested_ms)
    ceiling = float(board.get("max_ir_tx_ms", requested_ms))
    if requested_ms > ceiling:
        raise SystemExit(
            f"ir_tx_ms {requested_ms} exceeds max_ir_tx_ms {ceiling}; refuse IR TX"
        )
    return requested_ms


def clamp_ir_tx_duty(board: dict, requested: float | None = None) -> float:
    if requested is None:
        requested = float(board.get("ir_tx_duty", 0.3))
    else:
        requested = float(requested)
    ceiling = float(board.get("max_ir_tx_duty", requested))
    if requested > ceiling:
        raise SystemExit(
            f"ir_tx_duty {requested} exceeds max_ir_tx_duty {ceiling}; refuse IR TX"
        )
    return requested
