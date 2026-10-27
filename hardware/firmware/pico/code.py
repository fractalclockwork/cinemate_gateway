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
DEBOUNCE_S = 0.08

# Sony SIRC timings (µs) — match software/decode.py
SONY_HDR_MARK = 2400
SONY_SPACE = 600
SONY_ZERO_MARK = 600
SONY_ONE_MARK = 1200
SONY_TOL = 0.35
SONY_GLITCH_US = 50

KEYBOARD_CODES = {
    "UP": Keycode.UP_ARROW,
    "DOWN": Keycode.DOWN_ARROW,
    "LEFT": Keycode.LEFT_ARROW,
    "RIGHT": Keycode.RIGHT_ARROW,
    "ENTER": Keycode.ENTER,
    "ESCAPE": Keycode.ESCAPE,
    "SPACE": Keycode.SPACE,
    "J": Keycode.J,
    "L": Keycode.L,
}

CONSUMER_CODES = {
    "PLAY_PAUSE": ConsumerControlCode.PLAY_PAUSE,
    "NEXT": ConsumerControlCode.SCAN_NEXT_TRACK,
    "PREVIOUS": ConsumerControlCode.SCAN_PREVIOUS_TRACK,
    "VOLUME_UP": ConsumerControlCode.VOLUME_INCREMENT,
    "VOLUME_DOWN": ConsumerControlCode.VOLUME_DECREMENT,
    "MUTE": ConsumerControlCode.MUTE,
}


def _near(value, target, tol=SONY_TOL):
    return abs(value - target) <= target * tol


def scrub_glitches(pulses, min_us=SONY_GLITCH_US):
    return [int(pulse) for pulse in pulses if int(pulse) >= min_us]


def _pack_lsb(bits):
    value = 0
    for index, bit in enumerate(bits):
        value |= (bit & 1) << index
    return value


def decode_sony_sirc(pulses):
    """Decode Sony SIRC-12/15/20; return (addr, cmd) or (addr, cmd, ext)."""
    values = scrub_glitches(pulses)
    if len(values) < 2 + 12:
        return None
    if not _near(values[0], SONY_HDR_MARK) or not _near(values[1], SONY_SPACE):
        return None
    bits = []
    index = 2
    while index < len(values):
        mark = values[index]
        index += 1
        if _near(mark, SONY_ZERO_MARK):
            bits.append(0)
        elif _near(mark, SONY_ONE_MARK):
            bits.append(1)
        else:
            return None
        if index >= len(values):
            break
        space = values[index]
        index += 1
        if not _near(space, SONY_SPACE):
            return None
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


def _status_led():
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT
    return led


def emit_hid(kbd, cc, kind, name):
    if kind == "keyboard":
        code = KEYBOARD_CODES[name]
        kbd.press(code)
        kbd.release_all()
    elif kind == "consumer":
        cc.send(CONSUMER_CODES[name])


def main():
    led = _status_led()
    kbd = Keyboard(usb_hid.devices)
    cc = ConsumerControl(usb_hid.devices)
    last = 0.0

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
            time.sleep(0.01)
            continue
        led.value = True
        pulses = [pulsein[i] for i in range(len(pulsein))]
        pulsein.clear()
        led.value = False
        now = time.monotonic()
        if now - last < DEBOUNCE_S:
            continue
        frame = decode_sony_sirc(pulses)
        if MODE == "capture":
            print("pulses", pulses[:20], "..." if len(pulses) > 20 else "", "frame", frame)
            last = now
            continue
        if frame is None:
            print("undecoded", len(pulses), "pulses")
            last = now
            continue
        action = KEYMAP.get(frame)
        if action:
            emit_hid(kbd, cc, action[0], action[1])
            print("hid", action, "frame", frame)
        else:
            print("unmapped", frame)
        last = now


if __name__ == "__main__":
    main()
