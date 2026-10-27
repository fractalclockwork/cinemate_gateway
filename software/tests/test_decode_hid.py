"""SIL tests for decode, HID packing, and keymap."""

from __future__ import annotations

from software.decode import (
    classify_pulses,
    frame_key,
    nec_to_pulses,
    pd24_to_pulses,
    pulses_to_nec,
    pulses_to_pd24,
    pulses_to_sony,
    sony_to_pulses,
)
from software.fixture import run_fixture, run_image_fixture
from software.hid import pack_action, resolve_action
from software.keymap import EXAMPLE, load_keymap, lookup


def test_nec_roundtrip():
    pulses = nec_to_pulses(0x01, 0x05)
    frame = pulses_to_nec(pulses)
    assert frame is not None
    assert frame.address == 0x01
    assert frame.command == 0x05
    assert frame_key(frame) == "nec-like:01:05"


def test_hid_keyboard_and_consumer():
    enter = resolve_action("ENTER")
    assert pack_action(enter)[2] == 0x28
    vol = resolve_action("VOLUME_UP")
    assert pack_action(vol) == bytes([0xE9, 0x00])


def test_transport_and_digit_usages():
    assert resolve_action("PAUSE").usage_id == 0xB1
    assert resolve_action("STOP").usage_id == 0xB7
    assert resolve_action("FAST_FORWARD").usage_id == 0xB3
    assert resolve_action("REWIND").usage_id == 0xB4
    assert resolve_action("PLAY_PAUSE").usage_id == 0xCD
    assert resolve_action("0").usage_id == 0x27
    assert resolve_action("1").usage_id == 0x1E
    assert resolve_action("9").usage_id == 0x26
    assert pack_action(resolve_action("5"))[2] == 0x22


def test_sony_sirc20_roundtrip_and_classify():
    pulses = sony_to_pulses(0x1A, 0x15, bits=20, extended=0x9A)
    frame = pulses_to_sony(pulses)
    assert frame is not None
    assert frame.protocol == "sony-sirc20"
    assert frame.address == 0x1A
    assert frame.command == 0x15
    assert frame.extended == 0x9A
    assert frame_key(frame) == "sony-sirc20:1a:15:9a"
    classified = classify_pulses(pulses)
    assert classified["protocol"] == "sony-sirc20"
    assert classified["frame_key"] == "sony-sirc20:1a:15:9a"
    assert classified["extended"] == 0x9A


def test_pd24_roundtrip_and_classify():
    pulses = pd24_to_pulses(0x14, 0x1E, 0xBE)
    frame = pulses_to_pd24(pulses)
    assert frame is not None
    assert frame.protocol == "pd24"
    assert frame.address == 0x14
    assert frame.command == 0x1E
    assert frame.extended == 0xBE
    assert frame_key(frame) == "pd24:14:1e:be"
    classified = classify_pulses(pulses)
    assert classified["protocol"] == "pd24"
    assert classified["frame_key"] == "pd24:14:1e:be"


def test_classify_nec_and_leave_other_timings_unclassified():
    pulses = nec_to_pulses(0x20, 0x15)
    nec = classify_pulses(pulses)
    assert nec["protocol"] == "nec-like"
    assert nec["frame_key"] == "nec-like:20:15"
    assert nec["address"] == 0x20
    assert nec["frame_count"] == 1

    other = [3000, 900, 900, 900]
    rejected = classify_pulses(other)
    assert rejected["protocol"] == "unclassified"
    assert rejected["frame_key"] is None
    assert "address" not in rejected
    assert "command" not in rejected
    assert rejected["signature"]["count"] == len(other)
    assert rejected["signature"]["first_mark"] == 3000
    assert rejected["signature"]["first_space"] == 900


def test_classify_keeps_repeat_out_of_the_command_frame():
    pulses = nec_to_pulses(0x10, 0x22) + [560, 20000, 9000, 2250, 560]
    result = classify_pulses(pulses)
    assert result["frame_count"] == 2
    assert result["frame_key"] == "nec-like:10:22"


def test_keymap_example_loads_and_lookups():
    km = load_keymap(EXAMPLE)
    pulses = nec_to_pulses(0x01, 0x01)
    frame = pulses_to_nec(pulses)
    assert frame is not None
    action = lookup(frame, km)
    assert action is not None
    assert action.usage_name == "UP"


def test_run_fixture_ok():
    result = run_fixture({})
    assert result["ok"] is True
    assert result["count"] >= 10


def test_run_image_fixture_ok():
    board = {
        "max_ir_tx_ms": 200,
        "max_ir_tx_duty": 0.5,
        "pins": {"ir_rx": None, "ir_tx": None},
    }
    result = run_image_fixture(board, ir_tx_ms=50, ir_tx_duty=0.33)
    assert result["ok"] is True
    assert result["mode"] == "sil-hid-fixture"
    assert result["loopback_sample"]["hid"] == "ENTER"
