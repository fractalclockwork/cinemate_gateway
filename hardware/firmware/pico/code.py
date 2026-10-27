# CircuitPython IR → USB HID gateway (phase 1: RX + map; LED loopback helper).
# Copy this tree to the CIRCUITPY drive after installing CircuitPython for Pico.
#
# Pins match hardware/boards/pico.yaml (GP14 RX / GP15 TX).
# KEYMAP is generated from software/keymap.yaml via `make firmware-keymap`.
# Do not invent electrical levels — see hardware/docs/boards/pico.md.

import time

import board
import digitalio
import usb_hid
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse

from keymap_gen import KEYMAP

# Optional: pulseio available on CircuitPython Pico builds.
try:
    import pulseio
except ImportError:  # pragma: no cover - host SIL does not import this file
    pulseio = None

# --- operator configuration ---
MODE = "map"  # "capture" | "map"
IR_RX_PIN = board.GP14
IR_TX_PIN = board.GP15
# Keys and clicks fire once per press. A new press is the same frame after this
# much silence. Mouse moves ignore it and follow every SIRC repeat.
# Seek (Left/Right) repeats while held, slower than the IR repeat rate.
KEY_RELEASE_S = 0.12
SEEK_REPEAT_S = 0.35
SEEK_KEYS = ("LEFT", "RIGHT")
# Pointer feel. A tap stays at MIN. After CRAWL_S the step grows (t^2) and
# reaches MAX at RAMP_S. Raise RAMP_S or lower MAX when a hold feels too fast.
MOUSE_STEP_MIN = 5
MOUSE_STEP_MAX = 24
MOUSE_CRAWL_S = 0.25
MOUSE_RAMP_S = 1.20

# Sony SIRC timings (µs) — match software/decode.py
SONY_HDR_MARK = 2400
SONY_SPACE = 600
SONY_ZERO_MARK = 600
SONY_ONE_MARK = 1200
SONY_TOL = 0.35
SONY_GLITCH_US = 50
# PulseIn records an edge only when it ends. Wait out one frame, then decode.
# Quiet is longer than a bit space (~1.2 ms) and shorter than a repeat gap.
BURST_QUIET_S = 0.004
BURST_MAX_S = 0.08

KEYBOARD_CODES = {
    "UP": Keycode.UP_ARROW,
    "DOWN": Keycode.DOWN_ARROW,
    "LEFT": Keycode.LEFT_ARROW,
    "RIGHT": Keycode.RIGHT_ARROW,
    "ENTER": Keycode.ENTER,
    "ESCAPE": Keycode.ESCAPE,
    "SPACE": Keycode.SPACE,
    "TAB": Keycode.TAB,
    "PAGE_UP": Keycode.PAGE_UP,
    "PAGE_DOWN": Keycode.PAGE_DOWN,
    "A": Keycode.A,
    "C": Keycode.C,
    "F": Keycode.F,
    "J": Keycode.J,
    "L": Keycode.L,
    "M": Keycode.M,
}

# Modifier chords. Names match software/hid.py KEYBOARD_CHORDS.
KEYBOARD_CHORDS = {
    "SHIFT_TAB": (Keycode.SHIFT, Keycode.TAB),
    "ALT_TAB": (Keycode.ALT, Keycode.TAB),
    "SHIFT_ALT_TAB": (Keycode.SHIFT, Keycode.ALT, Keycode.TAB),
}

CONSUMER_CODES = {
    "PLAY_PAUSE": ConsumerControlCode.PLAY_PAUSE,
    "NEXT": ConsumerControlCode.SCAN_NEXT_TRACK,
    "PREVIOUS": ConsumerControlCode.SCAN_PREVIOUS_TRACK,
    "VOLUME_UP": ConsumerControlCode.VOLUME_INCREMENT,
    "VOLUME_DOWN": ConsumerControlCode.VOLUME_DECREMENT,
    "MUTE": ConsumerControlCode.MUTE,
}

MOUSE_DIR = {
    "MOUSE_UP": (0, -1),
    "MOUSE_DOWN": (0, 1),
    "MOUSE_LEFT": (-1, 0),
    "MOUSE_RIGHT": (1, 0),
}


def pointer_step(held_s):
    """Pixels per SIRC repeat. Flat for a tap, then accelerating while held."""
    if held_s <= MOUSE_CRAWL_S:
        return MOUSE_STEP_MIN
    span = MOUSE_RAMP_S - MOUSE_CRAWL_S
    t = (held_s - MOUSE_CRAWL_S) / span
    if t > 1:
        t = 1
    return MOUSE_STEP_MIN + int((MOUSE_STEP_MAX - MOUSE_STEP_MIN) * t * t)


def _near(value, target, tol=SONY_TOL):
    return abs(value - target) <= target * tol


def scrub_glitches(pulses, min_us=SONY_GLITCH_US):
    return [int(pulse) for pulse in pulses if int(pulse) >= min_us]


def _pack_lsb(bits):
    value = 0
    for index, bit in enumerate(bits):
        value |= (bit & 1) << index
    return value


def _frame_from_bits(bits):
    bit_count = len(bits)
    if bit_count not in (12, 15, 20):
        return None
    command = _pack_lsb(bits[0:7])
    if bit_count == 12:
        return (_pack_lsb(bits[7:12]), command)
    if bit_count == 15:
        return (_pack_lsb(bits[7:15]), command)
    address = _pack_lsb(bits[7:12])
    extended = _pack_lsb(bits[12:20])
    return (address, command, extended)


def _decode_at(values, start):
    """Decode one SIRC frame at start. Return (frame, index_after) or (None, start)."""
    if start + 2 + 12 > len(values):
        return None, start
    if not _near(values[start], SONY_HDR_MARK) or not _near(values[start + 1], SONY_SPACE):
        return None, start
    bits = []
    index = start + 2
    while len(bits) < 20 and index < len(values):
        mark = values[index]
        index += 1
        if _near(mark, SONY_ZERO_MARK):
            bits.append(0)
        elif _near(mark, SONY_ONE_MARK):
            bits.append(1)
        else:
            index -= 1
            break
        if len(bits) in (12, 15, 20) and (
            index >= len(values) or not _near(values[index], SONY_SPACE)
        ):
            break
        if index >= len(values):
            break
        if not _near(values[index], SONY_SPACE):
            break
        index += 1
    frame = _frame_from_bits(bits)
    if frame is None:
        return None, start
    return frame, index


def decode_sony_sirc(pulses):
    """Decode the first Sony SIRC-12/15/20 frame; return (addr, cmd) or (addr, cmd, ext)."""
    frames = frames_in(pulses)
    if not frames:
        return None
    return frames[0]


def frames_in(pulses):
    """Every SIRC frame in a PulseIn dump, including dumps that start with the idle gap."""
    values = scrub_glitches(pulses)
    found = []
    index = 0
    while index < len(values):
        frame, after = _decode_at(values, index)
        if frame is None:
            index += 1
            continue
        found.append(frame)
        index = after if after > index else index + 1
    return found


def _status_led():
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT
    return led


def read_burst(pulsein):
    """Block until edges stop, then take the whole buffer."""
    if len(pulsein) == 0:
        return []
    last = -1
    stable = time.monotonic()
    deadline = stable + BURST_MAX_S
    while time.monotonic() < deadline:
        count = len(pulsein)
        now = time.monotonic()
        if count != last:
            last = count
            stable = now
            if count >= pulsein.maxlen - 4:
                break
        elif now - stable >= BURST_QUIET_S:
            break
        time.sleep(0.001)
    pulses = [pulsein[i] for i in range(len(pulsein))]
    pulsein.clear()
    return pulses


def emit_hid(kbd, cc, mouse, kind, name):
    if kind == "keyboard":
        chord = KEYBOARD_CHORDS.get(name)
        if chord is not None:
            kbd.press(*chord)
            kbd.release_all()
            return
        code = KEYBOARD_CODES[name]
        kbd.press(code)
        kbd.release_all()
    elif kind == "consumer":
        cc.send(CONSUMER_CODES[name])
    elif kind == "mouse":
        if name == "MOUSE_LEFT_CLICK":
            mouse.click(Mouse.LEFT_BUTTON)


def main():
    led = _status_led()
    kbd = Keyboard(usb_hid.devices)
    cc = ConsumerControl(usb_hid.devices)
    mouse = Mouse(usb_hid.devices)
    # Last key or click still held. Cleared after KEY_RELEASE_S with no IR.
    held_frame = None
    seek_at = None
    quiet_since = None
    move_name = None
    move_since = None
    printed_step = None

    # Hold TX low (phase 1: no radiated IR toward CineMate).
    tx = digitalio.DigitalInOut(IR_TX_PIN)
    tx.direction = digitalio.Direction.OUTPUT
    tx.value = False

    pulsein = None
    if pulseio is not None and IR_RX_PIN is not None:
        pulsein = pulseio.PulseIn(IR_RX_PIN, maxlen=128, idle_state=True)
        pulsein.pause()
        pulsein.clear()
        pulsein.resume()

    led.value = False
    print("ir-remote-bose firmware ready mode=", MODE, "rx=", IR_RX_PIN)
    while True:
        if pulsein is None:
            time.sleep(0.5)
            continue
        if len(pulsein) == 0:
            led.value = False
            now = time.monotonic()
            if held_frame is not None:
                if quiet_since is None:
                    quiet_since = now
                elif now - quiet_since >= KEY_RELEASE_S:
                    held_frame = None
                    seek_at = None
                    move_name = None
                    move_since = None
                    printed_step = None
                    quiet_since = None
            time.sleep(0.005)
            continue
        quiet_since = None
        led.value = True
        pulses = read_burst(pulsein)
        led.value = False
        if not pulses:
            continue
        if MODE == "capture":
            print("pulses", len(pulses), pulses[:12])
            continue
        frames = frames_in(pulses)
        if not frames:
            if len(pulses) >= 8:
                print("undecoded", len(pulses), pulses[:8])
            continue
        for frame in frames:
            action = KEYMAP.get(frame)
            if action is None:
                print("unmapped", frame)
                continue
            kind, name = action
            if kind == "mouse" and name != "MOUSE_LEFT_CLICK":
                now = time.monotonic()
                if name != move_name or move_since is None:
                    move_name = name
                    move_since = now
                    printed_step = None
                step = pointer_step(now - move_since)
                sx, sy = MOUSE_DIR[name]
                mouse.move(x=sx * step, y=sy * step)
                if step != printed_step:
                    print("hid", action, "step", step)
                    printed_step = step
                continue
            now = time.monotonic()
            if kind == "keyboard" and name in SEEK_KEYS:
                if (
                    frame == held_frame
                    and seek_at is not None
                    and now - seek_at < SEEK_REPEAT_S
                ):
                    continue
                held_frame = frame
                seek_at = now
                emit_hid(kbd, cc, mouse, kind, name)
                print("hid", action, "frame", frame)
                continue
            if frame == held_frame:
                continue
            held_frame = frame
            seek_at = None
            emit_hid(kbd, cc, mouse, kind, name)
            print("hid", action, "frame", frame)


if __name__ == "__main__":
    main()
