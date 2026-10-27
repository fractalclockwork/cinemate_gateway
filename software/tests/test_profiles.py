"""App profiles encode published UI controls. They do not invent IR codes."""

from __future__ import annotations

import pytest

from software.hid import resolve_action
from software.profile import PROFILE_IDS, control_hid, load_profile, load_remote, validate_controls


def test_remote_record_is_aux_sony_dvr_20636():
    remote = load_remote()
    assert remote["library_code"] == "20636"
    assert remote["personality"] == "sony-dvr-20636"
    assert remote["source"] == "AUX"
    assert remote["list"] == "DVR"
    assert remote["on_off"]["confirmed"] is True
    assert remote["on_off"]["frame_key"] == "sony-sirc20:1a:15:9a"
    assert remote["working"][0]["library_code"] == "10178"


def test_profiles_load_and_reject_consumer_volume():
    for profile_id in PROFILE_IDS:
        profile = load_profile(profile_id)
        assert profile["remote"] == "sony-dvr-20636"
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
    assert control_hid(amazon, "up") == "UP"
    assert resolve_action("UP").kind == "keyboard"
    assert control_hid(amazon, "enter") is None
    assert control_hid(amazon, "play") == "SPACE"

    assert control_hid(paramount, "ffw") == "L"
    assert control_hid(paramount, "frw") == "J"
    assert resolve_action("J").usage_id == 0x0D
    assert resolve_action("L").usage_id == 0x0F

    assert control_hid(kanopy, "ffw") == "RIGHT"
    assert control_hid(kanopy, "back") == "ESCAPE"
    assert control_hid(kanopy, "stop") is None

    assert control_hid(youtube, "enter") == "ENTER"
    assert control_hid(youtube, "play") is None
    assert control_hid(youtube, "ffw") is None
    assert control_hid(youtube, "up") is None
