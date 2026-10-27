"""USB HID report packing for keyboard, consumer-control, and mouse (SIL).

Usage IDs follow HID Usage Tables. Firmware mirrors these names; packing here
is for unit tests only.
"""

from __future__ import annotations

from dataclasses import dataclass


# Keyboard page 0x07 — subset used by the example keymap.
KEYCODE = {
    "ENTER": 0x28,
    "ESCAPE": 0x29,
    "TAB": 0x2B,
    "SPACE": 0x2C,
    # Letters used by published player shortcuts (F fullscreen, J/L seek).
    "F": 0x09,
    "J": 0x0D,
    "L": 0x0F,
    "PAGE_UP": 0x4B,
    "PAGE_DOWN": 0x4E,
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

# Named keyboard chords: (base keycode name, modifier byte).
# Left Ctrl = 0x01, Left Shift = 0x02, Left Alt = 0x04.
KEYBOARD_CHORDS = {
    "SHIFT_TAB": ("TAB", 0x02),
    "ALT_TAB": ("TAB", 0x04),
    "SHIFT_ALT_TAB": ("TAB", 0x06),
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

# Relative mouse stubs for SIL packing (firmware uses a fixed step).
MOUSE_STEP = 40
MOUSE = {
    "MOUSE_UP": 0x01,
    "MOUSE_DOWN": 0x02,
    "MOUSE_LEFT": 0x03,
    "MOUSE_RIGHT": 0x04,
    "MOUSE_LEFT_CLICK": 0x10,
}
MOUSE_DELTA = {
    "MOUSE_UP": (0, -MOUSE_STEP),
    "MOUSE_DOWN": (0, MOUSE_STEP),
    "MOUSE_LEFT": (-MOUSE_STEP, 0),
    "MOUSE_RIGHT": (MOUSE_STEP, 0),
    "MOUSE_LEFT_CLICK": (0, 0),
}


@dataclass(frozen=True)
class HidAction:
    kind: str  # "keyboard" | "consumer" | "mouse"
    usage_name: str
    usage_id: int
    modifier: int = 0


def resolve_action(name: str) -> HidAction:
    key = name.strip().upper()
    if key in KEYBOARD_CHORDS:
        base_name, modifier = KEYBOARD_CHORDS[key]
        return HidAction("keyboard", key, KEYCODE[base_name], modifier)
    if key in KEYCODE:
        return HidAction("keyboard", key, KEYCODE[key])
    if key in CONSUMER:
        return HidAction("consumer", key, CONSUMER[key])
    if key in MOUSE:
        return HidAction("mouse", key, MOUSE[key])
    raise ValueError(f"unknown HID action {name!r}")


def pack_keyboard_report(usage_id: int, modifier: int = 0) -> bytes:
    """Boot keyboard report: modifier, reserved, 6 key slots."""
    return bytes([modifier & 0xFF, 0x00, usage_id & 0xFF, 0, 0, 0, 0, 0])


def pack_consumer_report(usage_id: int) -> bytes:
    """16-bit little-endian consumer usage."""
    return bytes([usage_id & 0xFF, (usage_id >> 8) & 0xFF])


def pack_mouse_report(dx: int = 0, dy: int = 0, buttons: int = 0) -> bytes:
    """Boot mouse report: buttons, dx, dy (relative, signed 8-bit)."""
    return bytes([buttons & 0xFF, dx & 0xFF, dy & 0xFF])


def pack_action(action: HidAction) -> bytes:
    if action.kind == "keyboard":
        return pack_keyboard_report(action.usage_id, action.modifier)
    if action.kind == "consumer":
        return pack_consumer_report(action.usage_id)
    if action.kind == "mouse":
        if action.usage_name == "MOUSE_LEFT_CLICK":
            return pack_mouse_report(buttons=0x01)
        dx, dy = MOUSE_DELTA[action.usage_name]
        return pack_mouse_report(dx=dx, dy=dy)
    raise ValueError(f"bad kind {action.kind}")
