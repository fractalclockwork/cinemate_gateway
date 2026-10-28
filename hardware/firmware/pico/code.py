# CircuitPython IR gateway (phase 1).
# Copy this tree to the CIRCUITPY drive after installing CircuitPython for Pico.
#
# Pins match hardware/boards/pico.yaml (GP14 RX / GP15 TX).
# KEYMAP is generated from software/keymap.yaml via `make firmware-keymap`.
# Do not invent electrical levels — see hardware/docs/boards/pico.md.
#
# MODE "capture" (device-code bring-up): USB HID off via boot.py CAPTURE_BUILD;
#   print frame_key lines only (no passthrough).
# MODE "map": IR → HID. Keep boot.py CAPTURE_BUILD = False when switching.

import time

import board
import digitalio

# Optional: pulseio available on CircuitPython Pico builds.
try:
    import pulseio
except ImportError:  # pragma: no cover - host SIL does not import this file
    pulseio = None

try:
    from deploy_stamp import DIGEST
except ImportError:  # pragma: no cover - missing stamp on first bring-up
    DIGEST = "unset"

# --- operator configuration ---
# Keep boot.py CAPTURE_BUILD in sync: True iff MODE == "capture".
MODE = "map"  # "capture" | "map"
IR_RX_PIN = board.GP14
IR_TX_PIN = board.GP15

# Face left → right: TV / CBL-SAT / DVD / VCR / AUX (operator tags source; Pico sees frames).
CAPTURE_SLOTS = (
    "TV   tv-10178        TV/10178    (no player)",
    "CBL  cblsat-21033    DVD/21033   paramount",
    "DVD  dvd-20533       DVD/20533   kanopy",
    "VCR  vcr-20033       VCR/20033   youtubetv",
    "AUX  sony-dvr-20636  DVR/20636   amazon",
)


def _capture_only():
    if MODE == "capture":
        return True
    try:
        open("/CAPTURE_ONLY", "r").close()
        return True
    except OSError:
        return False


# Keys and clicks fire once per press. A new press is the same frame after this
# much silence. Mouse / arrow holds are rate-limited — flooding HID+CDC on the
# same USB composite wedges CircuitPython until unplug (LED stops blinking).
KEY_RELEASE_S = 0.12
SEEK_KEYS = ("LEFT", "RIGHT", "UP", "DOWN", "PAGE_UP", "PAGE_DOWN")
# Hold-repeat interval: slow tap, then ramp to fast (slightly quicker than
# the mouse d-pad ramp). Used for seek arrows and Page Up/Down.
SEEK_REPEAT_MAX_S = 0.40
SEEK_REPEAT_MIN_S = 0.08
SEEK_CRAWL_S = 0.18
SEEK_RAMP_S = 0.85
# ~2× prior step (report rate stays capped — that fixed the USB wedge).
MOUSE_STEP_MIN = 10
MOUSE_STEP_MAX = 48
MOUSE_CRAWL_S = 0.25
MOUSE_RAMP_S = 1.20
# Cap mouse HID reports (~20/s). SIRC repeats faster than this while held.
MOUSE_REPORT_MIN_S = 0.05
MOUSE_DIR = {
    "MOUSE_UP": (0, -1),
    "MOUSE_DOWN": (0, 1),
    "MOUSE_LEFT": (-1, 0),
    "MOUSE_RIGHT": (1, 0),
}

# Sony SIRC timings (µs) — match software/decode.py
SONY_HDR_MARK = 2400
SONY_SPACE = 600
SONY_ZERO_MARK = 600
SONY_ONE_MARK = 1200
SONY_TOL = 0.35
SONY_GLITCH_US = 50
BURST_QUIET_S = 0.004
BURST_MAX_S = 0.08


def _hold_ramp(held_s, crawl_s, ramp_s):
    """0 at crawl, 1 at end of ramp (quadratic ease-in)."""
    if held_s <= crawl_s:
        return 0.0
    span = ramp_s - crawl_s
    t = (held_s - crawl_s) / span
    if t > 1:
        t = 1
    return t * t


def pointer_step(held_s):
    """Pixels per SIRC repeat. Flat for a tap, then accelerating while held."""
    return MOUSE_STEP_MIN + int(
        (MOUSE_STEP_MAX - MOUSE_STEP_MIN)
        * _hold_ramp(held_s, MOUSE_CRAWL_S, MOUSE_RAMP_S)
    )


def seek_repeat_interval(held_s):
    """Seconds between arrow HID events. Flat slow, then accelerates while held."""
    return SEEK_REPEAT_MAX_S + (
        (SEEK_REPEAT_MIN_S - SEEK_REPEAT_MAX_S)
        * _hold_ramp(held_s, SEEK_CRAWL_S, SEEK_RAMP_S)
    )


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


def frame_key(frame):
    """Host-style frame_key for serial capture logs."""
    if frame is None:
        return None
    if len(frame) == 2:
        return "sony-sirc12:%x:%x" % (frame[0], frame[1])
    if len(frame) == 3:
        return "sony-sirc20:%x:%x:%x" % (frame[0], frame[1], frame[2])
    return "sony-sirc:%r" % (frame,)


def _load_map_hid():
    """Lazy-import HID + keymap only in map mode (capture build has HID disabled)."""
    import usb_hid
    from adafruit_hid.consumer_control import ConsumerControl
    from adafruit_hid.consumer_control_code import ConsumerControlCode
    from adafruit_hid.keyboard import Keyboard
    from adafruit_hid.keycode import Keycode
    from adafruit_hid.mouse import Mouse

    from keymap_gen import KEYMAP

    keyboard_codes = {
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
    keyboard_chords = {
        "SHIFT_TAB": (Keycode.SHIFT, Keycode.TAB),
        "ALT_TAB": (Keycode.ALT, Keycode.TAB),
        "SHIFT_ALT_TAB": (Keycode.SHIFT, Keycode.ALT, Keycode.TAB),
    }
    consumer_codes = {
        "PLAY_PAUSE": ConsumerControlCode.PLAY_PAUSE,
        "NEXT": ConsumerControlCode.SCAN_NEXT_TRACK,
        "PREVIOUS": ConsumerControlCode.SCAN_PREVIOUS_TRACK,
        "VOLUME_UP": ConsumerControlCode.VOLUME_INCREMENT,
        "VOLUME_DOWN": ConsumerControlCode.VOLUME_DECREMENT,
        "MUTE": ConsumerControlCode.MUTE,
    }
    kbd = Keyboard(usb_hid.devices)
    cc = ConsumerControl(usb_hid.devices)
    mouse = Mouse(usb_hid.devices)
    mouse.release_all()
    return {
        "KEYMAP": KEYMAP,
        "KEYBOARD_CODES": keyboard_codes,
        "KEYBOARD_CHORDS": keyboard_chords,
        "CONSUMER_CODES": consumer_codes,
        "Mouse": Mouse,
        "kbd": kbd,
        "cc": cc,
        "mouse": mouse,
    }


def emit_hid(bundle, kind, name):
    kbd = bundle["kbd"]
    cc = bundle["cc"]
    mouse = bundle["mouse"]
    if kind == "keyboard":
        chord = bundle["KEYBOARD_CHORDS"].get(name)
        if chord is not None:
            kbd.press(*chord)
            kbd.release_all()
            return
        code = bundle["KEYBOARD_CODES"][name]
        kbd.press(code)
        kbd.release_all()
    elif kind == "consumer":
        cc.send(bundle["CONSUMER_CODES"][name])
    elif kind == "mouse":
        if name == "MOUSE_LEFT_CLICK":
            mouse.press(bundle["Mouse"].LEFT_BUTTON)
            time.sleep(0.03)
            mouse.release(bundle["Mouse"].LEFT_BUTTON)


def main():
    led = _status_led()
    capture = _capture_only()
    bundle = None if capture else _load_map_hid()
    held_frame = None
    seek_at = None
    seek_since = None
    quiet_since = None
    move_name = None
    move_since = None
    move_at = None
    last_capture_key = None

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
    mode_name = "capture" if capture else "map"
    # Boot banner only (digest gate for make firmware). Map mode stays silent
    # after this — serial prints are for capture/decode only.
    print(
        "ir-remote-bose firmware ready mode=%s rx=%s digest=%s"
        % (mode_name, IR_RX_PIN, DIGEST)
    )
    if capture:
        print("CAPTURE-ONLY — no HID passthrough. Note which Bose source is selected.")
        for slot in CAPTURE_SLOTS:
            print("  slot:", slot)
        print("Press a face key; lines look like: frame_key <key> raw <tuple>")

    while True:
        try:
            if pulsein is None:
                time.sleep(0.5)
                continue
            if len(pulsein) == 0:
                led.value = False
                now = time.monotonic()
                if held_frame is not None or last_capture_key is not None:
                    if quiet_since is None:
                        quiet_since = now
                    elif now - quiet_since >= KEY_RELEASE_S:
                        held_frame = None
                        seek_at = None
                        seek_since = None
                        move_name = None
                        move_since = None
                        move_at = None
                        last_capture_key = None
                        quiet_since = None
                time.sleep(0.005)
                continue
            quiet_since = None
            led.value = True
            pulses = read_burst(pulsein)
            led.value = False
            if not pulses:
                continue
            if capture:
                frames = frames_in(pulses)
                if not frames:
                    print("undecoded edges=", len(pulses), "head=", pulses[:8])
                    continue
                for frame in frames:
                    key = frame_key(frame)
                    # One line per press; SIRC repeats while held are suppressed.
                    if key == last_capture_key:
                        continue
                    last_capture_key = key
                    held_frame = frame
                    print("frame_key", key, "raw", frame)
                continue

            frames = frames_in(pulses)
            if not frames:
                continue
            keymap = bundle["KEYMAP"]
            for frame in frames:
                action = keymap.get(frame)
                if action is None:
                    continue
                kind, name = action
                if kind == "mouse" and name != "MOUSE_LEFT_CLICK":
                    now = time.monotonic()
                    if name != move_name or move_since is None:
                        move_name = name
                        move_since = now
                        move_at = None
                    if move_at is not None and now - move_at < MOUSE_REPORT_MIN_S:
                        continue
                    step = pointer_step(now - move_since)
                    sx, sy = MOUSE_DIR[name]
                    bundle["mouse"].move(x=sx * step, y=sy * step)
                    move_at = now
                    continue
                now = time.monotonic()
                if kind == "keyboard" and name in SEEK_KEYS:
                    if frame != held_frame or seek_since is None:
                        seek_since = now
                        seek_at = None
                    interval = seek_repeat_interval(now - seek_since)
                    if seek_at is not None and now - seek_at < interval:
                        continue
                    held_frame = frame
                    seek_at = now
                    emit_hid(bundle, kind, name)
                    continue
                if frame == held_frame:
                    continue
                held_frame = frame
                seek_at = None
                seek_since = None
                move_at = None
                emit_hid(bundle, kind, name)
        except Exception:
            # Keep IR loop alive; never print in map mode (USB CDC stalls HID).
            held_frame = None
            seek_at = None
            seek_since = None
            move_name = None
            move_since = None
            move_at = None
            try:
                if pulsein is not None:
                    pulsein.clear()
            except Exception:
                pass
            time.sleep(0.05)


if __name__ == "__main__":
    main()
