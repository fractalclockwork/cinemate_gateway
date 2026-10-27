"""USB HID report packing for keyboard and consumer-control (SIL).

Usage IDs follow HID Usage Tables. Firmware mirrors these names; packing here
is for unit tests only.
"""

from __future__ import annotations

from dataclasses import dataclass


# Keyboard page 0x07 — subset used by the example keymap.
KEYCODE = {
    "ENTER": 0x28,
    "ESCAPE": 0x29,
    "SPACE": 0x2C,
    # Letters used by published player shortcuts (J rewind, L fast-forward).
    "J": 0x0D,
    "L": 0x0F,
    "RIGHT": 0x4F,
    "LEFT": 0x50,
    "DOWN": 0x51,
    "UP": 0x52,
    # Keyboard page digits. Names are the digits so keymap entries stay readable.
    "1": 0x1E,
    "2": 0x1F,
    "3": 0x20,
    "4": 0x21,
    "5": 0x22,
    "6": 0x23,
    "7": 0x24,
    "8": 0x25,
    "9": 0x26,
    "0": 0x27,
}

# Consumer page 0x0C
CONSUMER = {
    "PLAY_PAUSE": 0xCD,
    "PAUSE": 0xB1,
    "FAST_FORWARD": 0xB3,
    "REWIND": 0xB4,
    "NEXT": 0xB5,
    "PREVIOUS": 0xB6,
    "STOP": 0xB7,
    "MUTE": 0xE2,
    "VOLUME_UP": 0xE9,
    "VOLUME_DOWN": 0xEA,
}


@dataclass(frozen=True)
class HidAction:
    kind: str  # "keyboard" | "consumer"
    usage_name: str
    usage_id: int


def resolve_action(name: str) -> HidAction:
    key = name.strip().upper()
    if key in KEYCODE:
        return HidAction("keyboard", key, KEYCODE[key])
    if key in CONSUMER:
        return HidAction("consumer", key, CONSUMER[key])
    raise ValueError(f"unknown HID action {name!r}")


def pack_keyboard_report(usage_id: int, modifier: int = 0) -> bytes:
    """Boot keyboard report: modifier, reserved, 6 key slots."""
    return bytes([modifier & 0xFF, 0x00, usage_id & 0xFF, 0, 0, 0, 0, 0])


def pack_consumer_report(usage_id: int) -> bytes:
    """16-bit little-endian consumer usage."""
    return bytes([usage_id & 0xFF, (usage_id >> 8) & 0xFF])


def pack_action(action: HidAction) -> bytes:
    if action.kind == "keyboard":
        return pack_keyboard_report(action.usage_id)
    if action.kind == "consumer":
        return pack_consumer_report(action.usage_id)
    raise ValueError(f"bad kind {action.kind}")
