"""App profiles encode published UI controls. They do not invent IR codes."""

from __future__ import annotations

import pytest

from software.hid import resolve_action
from software.profile import (
    PROFILE_IDS,
    control_hid,
    known_personality_ids,
    load_profile,
    load_remote,
    personalities_from_remote,
    validate_controls,
)


def test_remote_record_is_aux_sony_dvr_20636():
    remote = load_remote()
    assert remote["library_code"] == "20636"
    assert remote["personality"] == "sony-dvr-20636"
    assert remote["source"] == "AUX"
    assert remote["list"] == "DVR"
    assert remote["on_off"]["confirmed"] is True
    assert remote["on_off"]["frame_key"] == "sony-sirc20:1a:15:9a"
    assert remote["working"][0]["library_code"] == "10178"
    personalities = personalities_from_remote(remote)
    assert "sony-dvr-20636" in personalities
    assert personalities["sony-dvr-20636"]["profile"] == "amazon"
    assert "tv-10178" in personalities
    assert personalities["vcr-20033"]["profile"] == "youtubetv"
    assert personalities["dvd-20533"]["profile"] == "kanopy"
    assert personalities["cblsat-21033"]["profile"] == "paramount"
    assert known_personality_ids() == set(personalities)


def test_profiles_load_and_reject_consumer_volume():
    known = known_personality_ids()
    for profile_id in PROFILE_IDS:
        profile = load_profile(profile_id)
        assert profile["remote"] in known
        for control in profile["controls"].values():
            hid = control["hid"]
            if hid is not None:
                assert not str(hid).upper().startswith("VOLUME")
                resolve_action(str(hid))
    with pytest.raises(ValueError):
        validate_controls({"up": {"hid": "VOLUME_UP", "ui": "volume_up"}})


def test_app_encodings_differ_where_the_pages_differ():
    amazon = load_profile("amazon")
    paramount = load_profile("paramount")
    kanopy = load_profile("kanopy")
    youtube = load_profile("youtubetv")

    assert control_hid(amazon, "ffw") == "RIGHT"
    assert control_hid(amazon, "up") == "MOUSE_UP"
    assert resolve_action("MOUSE_UP").kind == "mouse"
    assert control_hid(amazon, "enter") == "MOUSE_LEFT_CLICK"
    assert control_hid(amazon, "play") == "SPACE"
    assert control_hid(amazon, "quick_skip") == "ALT_TAB"
    assert control_hid(amazon, "instant_replay") == "SHIFT_ALT_TAB"
    assert control_hid(amazon, "record") == "F"
    assert resolve_action("ALT_TAB").modifier == 0x04
    assert resolve_action("SHIFT_ALT_TAB").modifier == 0x06
    assert control_hid(amazon, "channel_up") == "UP"
    assert control_hid(amazon, "channel_down") == "DOWN"
    assert control_hid(amazon, "page_up") is None  # shared IR with channel_up
    assert resolve_action("SHIFT_TAB").modifier == 0x02
    assert resolve_action("F").usage_id == 0x09

    assert control_hid(paramount, "ffw") == "L"
    assert control_hid(paramount, "frw") == "J"
    assert resolve_action("J").usage_id == 0x0D
    assert resolve_action("L").usage_id == 0x0F

    assert control_hid(kanopy, "ffw") == "RIGHT"
    assert control_hid(kanopy, "back") == "ESCAPE"
    assert control_hid(kanopy, "stop") is None

    assert youtube["remote"] == "vcr-20033"
    assert kanopy["remote"] == "dvd-20533"
    assert paramount["remote"] == "cblsat-21033"
    # YouTube TV mirrors Amazon button purpose until VCR IR is captured.
    assert control_hid(youtube, "enter") == "MOUSE_LEFT_CLICK"
    assert control_hid(youtube, "play") == "SPACE"
    assert control_hid(youtube, "ffw") == "RIGHT"
    assert control_hid(youtube, "up") == "MOUSE_UP"
    assert control_hid(youtube, "record") == "F"
    assert control_hid(youtube, "quick_skip") == "ALT_TAB"
    assert control_hid(youtube, "channel_up") == "UP"
    assert control_hid(youtube, "channel_down") == "DOWN"
    assert control_hid(youtube, "page_up") == "PAGE_UP"
    assert control_hid(youtube, "page_down") == "PAGE_DOWN"
