"""SIL fixtures for decode + HID + image-stage evidence."""

from __future__ import annotations

from software.decode import IrFrame, frame_key, nec_to_pulses, pulses_to_nec
from software.hid import pack_action
from software.keymap import EXAMPLE, load_keymap, lookup


def run_fixture(board: dict | None = None) -> dict:
    """Offline SIL: round-trip NEC synth → decode → keymap → HID bytes.

    Always uses the example NEC fixture map. Measured AUX keymaps (SIRC-20,
    pd24, …) live in reports/ and software/keymap.yaml for HWIL, not this synth.
    """
    del board  # board ceilings checked in HWIL image path
    keymap = load_keymap(EXAMPLE)
    results = []
    for ir_key, action_name in keymap["map"].items():
        parts = ir_key.split(":")
        if len(parts) != 3 or parts[0] != "nec-like":
            return {"ok": False, "reason": f"SIL fixture expects nec-like keys, got {ir_key}"}
        _proto, addr_s, cmd_s = parts
        address = int(addr_s, 16)
        command = int(cmd_s, 16)
        pulses = nec_to_pulses(address, command)
        frame = pulses_to_nec(pulses)
        if frame is None:
            return {"ok": False, "reason": f"decode failed for {ir_key}"}
        if frame_key(frame) != ir_key:
            return {
                "ok": False,
                "reason": f"frame key mismatch {frame_key(frame)} != {ir_key}",
            }
        action = lookup(frame, keymap)
        if action is None or action.usage_name != str(action_name).upper():
            return {"ok": False, "reason": f"lookup failed for {ir_key}"}
        report = pack_action(action)
        results.append(
            {
                "ir": ir_key,
                "action": action.usage_name,
                "kind": action.kind,
                "report_hex": report.hex(),
            }
        )
    return {"ok": True, "count": len(results), "samples": results[:3]}


def run_image_fixture(
    board: dict,
    ir_tx_ms: float,
    ir_tx_duty: float,
) -> dict:
    """Evidence used by the `image` stage — SIL HID fixture only (no live IR).

    Physical IR claims come from capture / loopback stamps, not this stage.
    Validates example keymap→HID under board TX ceilings.
    """
    ceiling_ms = float(board.get("max_ir_tx_ms", ir_tx_ms))
    ceiling_duty = float(board.get("max_ir_tx_duty", ir_tx_duty))
    if ir_tx_ms > ceiling_ms or ir_tx_duty > ceiling_duty:
        return {
            "ok": False,
            "reason": "IR TX request exceeds board ceilings",
        }
    base = run_fixture(board)
    if not base.get("ok"):
        return base
    # Synthetic SIL sample stays on the example map. A measured keymap.yaml
    # must not be required to contain the fixture address.
    frame = IrFrame("nec-like", 0x01, 0x05, ())
    action = lookup(frame, load_keymap(EXAMPLE))
    if action is None:
        return {"ok": False, "reason": "example ENTER mapping missing"}
    return {
        "ok": True,
        "mode": "sil-hid-fixture",
        "ir_tx_ms": ir_tx_ms,
        "ir_tx_duty": ir_tx_duty,
        "pins": board.get("pins"),
        "loopback_sample": {
            "ir": frame_key(frame),
            "hid": action.usage_name,
            "report_hex": pack_action(action).hex(),
        },
        "fixture": base,
        "note": (
            "SIL HID fixture only. Physical IR = capture/loopback under "
            "reports/pico/<stamp>/; use harness.ready.require_ir_map for IR identity."
        ),
    }
