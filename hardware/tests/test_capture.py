"""Receive-only capture gates. No USB and no IR TX."""

from __future__ import annotations

from pathlib import Path

import pytest

from hardware.capture import (
    DEVICE_CODE,
    MAP_BUTTONS,
    PERSONALITY,
    append_measured_fact,
    build_button_table,
    build_device_script,
    keymap_pairs,
    persist_confirm_map_evidence,
    render_keymap,
    sync_session_from_validated,
    validated_from_confirm_map,
)
from software.decode import classify_pulses, nec_to_pulses
from software.keymap import load_keymap


def test_device_script_holds_tx_low_and_does_not_transmit():
    src = build_device_script(rx_pin=14, tx_pin=15)
    assert "pwmio" not in src
    assert "duty_cycle" not in src
    assert "board.GP14" in src
    assert "board.GP15" in src
    assert "maxlen=256" in src
    assert "idle_state=True" in src
    assert "5.000" in src
    assert src.index("tx.value = False") < src.index("PulseIn")
    assert src.rindex("tx.value = False") > src.index("finally:")
    assert "_cap_tx" in src
    assert "hold = digitalio" not in src
    assert src.count("tx.deinit()") >= 1


def test_device_script_refuses_shared_pins():
    with pytest.raises(SystemExit):
        build_device_script(rx_pin=14, tx_pin=14)


def test_device_script_lights_onboard_led_from_new_edges():
    src = build_device_script(rx_pin=14, tx_pin=15)
    assert "pwmio" not in src
    assert "board.LED" in src
    assert src.index("led.value = False") < src.index("PulseIn")
    assert "count > seen" in src
    assert "0.2" in src
    assert "sleep(0.05)" not in src
    assert "sleep(0.5)" not in src


def _hit(button: str, sample: str, address: int, command: int) -> dict:
    pulses = nec_to_pulses(address, command)
    return {
        "button": button,
        "sample": sample,
        "miss": False,
        "edges": len(pulses),
        "classification": classify_pulses(pulses),
    }


def _miss(button: str, sample: str) -> dict:
    return {
        "button": button,
        "sample": sample,
        "miss": True,
        "edges": 0,
        "classification": classify_pulses([]),
    }


def _map_and_on_off() -> list[dict]:
    samples = [
        _hit("on_off", "a", 0x40, 0x50),
        _hit("on_off", "b", 0x40, 0x50),
    ]
    for index, button in enumerate(MAP_BUTTONS):
        samples.append(_hit(button, "a", 0x40, index + 1))
        samples.append(_hit(button, "b", 0x40, index + 1))
    return samples


def test_button_table_maps_only_a_stable_unique_nec_wave(tmp_path: Path):
    samples = _map_and_on_off()
    validated = {
        "buttons": [
            {
                "button": "on_off",
                "frame_key": "nec-like:40:50",
                "hid": None,
                "validated": True,
            }
        ]
        + [
            {
                "button": button,
                "frame_key": f"nec-like:40:{index + 1:02x}",
                "hid": None,
                "validated": True,
            }
            for index, button in enumerate(MAP_BUTTONS)
        ]
    }
    table = build_button_table(samples, validated)
    assert table["device_code"] == DEVICE_CODE
    assert table["aux_personality"] == PERSONALITY
    assert table["on_off_confirmed"] is True
    assert table["on_off"]["frame_key"] == "nec-like:40:50"
    assert table["stable"] is True
    assert table["waves"]["center"]["protocol"] == "nec-like"
    assert table["waves"]["center"]["address"] == 0x40
    assert keymap_pairs(table, "kanopy") is not None
    held = dict(table)
    held["on_off_confirmed"] = False
    assert keymap_pairs(held, "kanopy") is None
    pairs = keymap_pairs(table, "kanopy")
    assert pairs is not None
    assert pairs[0] == ("nec-like:40:01", "UP")
    assert pairs[4] == ("nec-like:40:05", "ENTER")
    text = render_keymap(pairs, "stamp", "kanopy")
    assert "mode_gate: aux" in text
    assert f"personality: {PERSONALITY}" in text
    assert "profile: kanopy" in text
    keymap_path = tmp_path / "keymap.yaml"
    keymap_path.write_text(text)
    keymap = load_keymap(keymap_path)
    assert keymap["map"]["nec-like:40:01"] == "UP"
    amazon = dict(keymap_pairs(table, "amazon"))
    paramount = dict(keymap_pairs(table, "paramount"))
    youtube = dict(keymap_pairs(table, "youtubetv"))
    up_key = next(row["frame_key"] for row in table["buttons"] if row["button"] == "up")
    enter_key = next(row["frame_key"] for row in table["buttons"] if row["button"] == "enter")
    ffw_key = next(row["frame_key"] for row in table["buttons"] if row["button"] == "ffw")
    assert amazon[up_key] == "MOUSE_UP"
    assert amazon[enter_key] == "MOUSE_LEFT_CLICK"
    assert amazon[ffw_key] == "RIGHT"
    assert paramount[ffw_key] == "L"
    assert ffw_key not in youtube
    assert "FAST_FORWARD" not in youtube.values()
    assert youtube["nec-like:40:05"] == "ENTER"


def test_on_off_confirmation_accepts_a_shared_unclassified_signature():
    rejected = classify_pulses([2400, 600, 1200, 600])
    samples = [
        {
            "button": "on_off",
            "sample": "a",
            "miss": False,
            "edges": 4,
            "classification": rejected,
        },
        {
            "button": "on_off",
            "sample": "b",
            "miss": False,
            "edges": 4,
            "classification": rejected,
        },
    ]
    table = build_button_table(samples)
    assert table["on_off_confirmed"] is True
    assert table["on_off"]["frame_key"] == "unclassified"
    assert table["on_off"]["signature"]["count"] == 4
    assert keymap_pairs(table, "amazon") is None


def test_button_table_hides_collisions_and_incomplete_waves(tmp_path: Path):
    samples = [
        _hit("up", "a", 0x40, 1),
        _hit("up", "b", 0x40, 1),
        _hit("down", "a", 0x40, 1),
        _hit("down", "b", 0x40, 1),
    ]
    table = build_button_table(samples)
    assert table["stable"] is False
    assert keymap_pairs(table, "kanopy") is None
    by_name = {row["button"]: row for row in table["buttons"]}
    assert by_name["up"]["agreed"] is True
    assert by_name["up"]["validated"] is False
    assert by_name["up"]["frame_key"] == "nec-like:40:01"
    assert by_name["down"]["frame_key"] == "nec-like:40:01"
    collided = build_button_table(
        samples,
        {
            "buttons": [
                {
                    "button": "up",
                    "frame_key": "nec-like:40:01",
                    "hid": "UP",
                    "validated": True,
                },
                {
                    "button": "down",
                    "frame_key": "nec-like:40:01",
                    "hid": "DOWN",
                    "validated": True,
                },
            ]
        },
    )
    collided_names = {row["button"]: row for row in collided["buttons"]}
    assert collided_names["up"]["frame_key"] == "unclassified"
    assert collided_names["down"]["frame_key"] == "unclassified"

    rejected = classify_pulses([2400, 600, 1200, 600])
    mixed = [
        _hit("up", "a", 0x40, 1),
        _hit("up", "b", 0x40, 1),
        {
            "button": "down",
            "sample": "a",
            "miss": False,
            "edges": 4,
            "classification": rejected,
        },
        {
            "button": "down",
            "sample": "b",
            "miss": False,
            "edges": 4,
            "classification": rejected,
        },
    ]
    mixed_table = build_button_table(mixed)
    mixed_names = {row["button"]: row for row in mixed_table["buttons"]}
    assert mixed_names["up"]["agreed"] is True
    assert mixed_names["up"]["validated"] is False
    assert mixed_names["up"]["frame_key"] == "nec-like:40:01"
    assert mixed_names["down"]["agreed"] is True
    assert mixed_names["down"]["frame_key"] == "unclassified"
    assert mixed_table["waves"]["center"]["protocol"] == "unclassified"

    facts = tmp_path / "manual-facts.md"
    facts.write_text("# Notes\n\n## Phase 1 policy for this project\n\n- stay\n")
    bullet = f"- TV `{DEVICE_CODE}` on AUX, session `reports/pico/stamp/captures/`: none"
    append_measured_fact(facts, bullet)
    append_measured_fact(facts, bullet)
    body = facts.read_text()
    assert body.count(bullet) == 1
    assert body.index("## Measured capture") < body.index("## Phase 1 policy")


def test_sync_session_from_validated_sets_on_off(tmp_path):
    import json

    captures = tmp_path / "captures"
    captures.mkdir()
    (captures / "session.json").write_text(
        json.dumps(
            {
                "status": "open",
                "on_off_confirmed": False,
                "validated": [],
                "buttons": [],
            }
        )
    )
    (captures / "validated.json").write_text(
        json.dumps(
            {
                "buttons": [
                    {
                        "button": "on_off",
                        "frame_key": "sony-sirc20:1a:15:9a",
                        "validated": True,
                    },
                    {
                        "button": "up",
                        "frame_key": "sony-sirc20:1a:5f:9a",
                        "validated": True,
                    },
                ]
            }
        )
    )
    session = sync_session_from_validated(captures)
    assert session["on_off_confirmed"] is True
    assert session["validated"] == ["on_off", "up"]
    assert session["on_off"]["frame_key"] == "sony-sirc20:1a:15:9a"
    disk = json.loads((captures / "session.json").read_text())
    assert disk["on_off_confirmed"] is True


def test_persist_confirm_map_evidence_writes_validated_and_session(tmp_path):
    import json

    captures = tmp_path / "captures"
    data = {
        "personality": PERSONALITY,
        "library_code": DEVICE_CODE,
        "buttons": {
            "on_off": {
                "frame_key": "sony-sirc20:1a:15:9a",
                "status": "confirmed",
                "evidence": "confirm-map-test",
            },
            "stop": {"frame_key": None, "status": "unbound"},
        },
    }
    assert validated_from_confirm_map(data)["buttons"][0]["button"] == "on_off"
    persist_confirm_map_evidence(data, captures)
    validated = json.loads((captures / "validated.json").read_text())
    session = json.loads((captures / "session.json").read_text())
    assert validated["buttons"][0]["validated"] is True
    assert session["on_off_confirmed"] is True
    assert "on_off" in session["validated"]
