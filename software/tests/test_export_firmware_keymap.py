"""Host keymap → CircuitPython keymap_gen consistency."""

from __future__ import annotations

from pathlib import Path

from software.decode import frame_key, pulses_to_sony, sony_to_pulses
from software.export_firmware_keymap import (
    DEFAULT_OUT,
    keymap_entries,
    parse_frame_key,
    render_keymap_gen,
    write_keymap_gen,
)
from software.keymap import ACTIVE, load_keymap


def test_parse_sirc20_frame_key():
    proto, addr, cmd, ext = parse_frame_key("sony-sirc20:1a:5f:9a")
    assert proto == "sony-sirc20"
    assert (addr, cmd, ext) == (0x1A, 0x5F, 0x9A)


def test_parse_sirc12_frame_key():
    proto, addr, cmd, ext = parse_frame_key("sony-sirc12:2:1a")
    assert proto == "sony-sirc12"
    assert (addr, cmd, ext) == (0x02, 0x1A, None)


def test_firmware_keymap_keys_are_unique():
    """AUX and VCR (and any later mode) must not share a KEYMAP tuple."""
    entries = keymap_entries(load_keymap(ACTIVE))
    keys = [key for key, _ in entries]
    assert len(keys) == len(set(keys))
    # SIRC-12 (addr,cmd) must not collide with SIRC-20 (addr,cmd,ext).
    assert (0x02, 0x1A) in keys
    assert (0x1A, 0x1A, 0x9A) in keys


def test_keymap_entries_match_active_amazon_and_vcr_maps():
    data = load_keymap(ACTIVE)
    assert data.get("profile") == "amazon"
    assert any(p.get("id") == "sony-dvr-20636" for p in data.get("personalities") or [])
    assert any(p.get("id") == "vcr-20033" for p in data.get("personalities") or [])
    entries = keymap_entries(data)
    assert len(entries) == len(data["map"])
    by_key = {key: action for key, action in entries}
    assert by_key[(0x1A, 0x5F, 0x9A)] == ("mouse", "MOUSE_UP")
    assert by_key[(0x1A, 0x5E, 0x9A)] == ("mouse", "MOUSE_LEFT_CLICK")
    assert by_key[(0x1A, 0x63, 0x9A)] == ("keyboard", "ESCAPE")
    assert by_key[(0x1A, 0x72, 0x9A)] == ("keyboard", "ALT_TAB")
    assert by_key[(0x1A, 0x5B, 0x9A)] == ("keyboard", "SHIFT_ALT_TAB")
    assert by_key[(0x1A, 0x1D, 0x9A)] == ("keyboard", "F")
    assert by_key[(0x1A, 0x10, 0x9A)] == ("keyboard", "UP")
    assert by_key[(0x1A, 0x11, 0x9A)] == ("keyboard", "DOWN")
    # VCR / youtubetv mirrors amazon HID on labeled SIRC-12 frames.
    assert by_key[(0x02, 0x1A)] == ("keyboard", "SPACE")
    assert by_key[(0x02, 0x19)] == ("keyboard", "SPACE")
    assert by_key[(0x02, 0x1C)] == ("keyboard", "RIGHT")
    assert by_key[(0x02, 0x1B)] == ("keyboard", "LEFT")
    assert by_key[(0x02, 0x1D)] == ("keyboard", "F")
    assert by_key[(0x02, 0x42)] == ("mouse", "MOUSE_UP")
    assert by_key[(0x02, 0x43)] == ("mouse", "MOUSE_DOWN")
    assert by_key[(0x02, 0x51)] == ("mouse", "MOUSE_LEFT_CLICK")
    assert by_key[(0x02, 0x2A)] == ("keyboard", "ESCAPE")
    assert by_key[(0xB4, 0x5B)] == ("keyboard", "SHIFT_ALT_TAB")
    assert by_key[(0x02, 0x10)] == ("keyboard", "UP")
    assert by_key[(0x02, 0x11)] == ("keyboard", "DOWN")
    assert by_key[(0xB4, 0x60)] == ("keyboard", "PAGE_UP")
    assert by_key[(0xB4, 0x62)] == ("keyboard", "PAGE_DOWN")


def test_exporter_roundtrip_matches_checked_in_keymap_gen(tmp_path):
    out = tmp_path / "keymap_gen.py"
    write_keymap_gen(out=out, keymap_path=ACTIVE)
    generated = out.read_text()
    checked_in = DEFAULT_OUT.read_text()
    # Compare KEYMAP body ignoring Source path absolute/relative differences.
    assert "KEYMAP = {" in generated
    assert generated.split("KEYMAP = {", 1)[1] == checked_in.split("KEYMAP = {", 1)[1]


def test_sirc20_decode_matches_frame_key_lookup():
    """Pulses for UP decode to the same triple used in KEYMAP."""
    pulses = sony_to_pulses(0x1A, 0x5F, bits=20, extended=0x9A)
    frame = pulses_to_sony(pulses)
    assert frame is not None
    assert frame_key(frame) == "sony-sirc20:1a:5f:9a"
    entries = dict(keymap_entries())
    assert entries[(frame.address, frame.command, frame.extended)][1] == "MOUSE_UP"


def test_sirc12_decode_matches_vcr_keymap_lookup():
    """VCR play pulses decode to the SIRC-12 pair used in KEYMAP."""
    pulses = sony_to_pulses(0x02, 0x1A, bits=12)
    frame = pulses_to_sony(pulses)
    assert frame is not None
    # Host frame_key zero-pads; firmware/tio logs use unpadded %x (sony-sirc12:2:1a).
    assert frame_key(frame) == "sony-sirc12:02:1a"
    entries = dict(keymap_entries())
    assert entries[(frame.address, frame.command)][1] == "SPACE"


def test_render_is_importable_dict(tmp_path):
    entries = keymap_entries()
    text = render_keymap_gen(entries, Path("software/keymap.yaml"))
    out = tmp_path / "keymap_gen.py"
    out.write_text(text)
    namespace: dict = {}
    exec(compile(out.read_text(), str(out), "exec"), namespace)
    assert isinstance(namespace["KEYMAP"], dict)
    assert len(namespace["KEYMAP"]) == len(entries)
