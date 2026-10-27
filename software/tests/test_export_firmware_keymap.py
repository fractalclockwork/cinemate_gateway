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


def test_keymap_entries_match_active_kanopy_map():
    data = load_keymap(ACTIVE)
    entries = keymap_entries(data)
    assert len(entries) == len(data["map"])
    by_key = {key: action for key, action in entries}
    assert by_key[(0x1A, 0x5F, 0x9A)] == ("keyboard", "UP")
    assert by_key[(0x1A, 0x63, 0x9A)] == ("keyboard", "ESCAPE")


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
    assert entries[(frame.address, frame.command, frame.extended)][1] == "UP"


def test_render_is_importable_dict(tmp_path):
    entries = keymap_entries()
    text = render_keymap_gen(entries, Path("software/keymap.yaml"))
    out = tmp_path / "keymap_gen.py"
    out.write_text(text)
    namespace: dict = {}
    exec(compile(out.read_text(), str(out), "exec"), namespace)
    assert isinstance(namespace["KEYMAP"], dict)
    assert len(namespace["KEYMAP"]) == len(entries)
