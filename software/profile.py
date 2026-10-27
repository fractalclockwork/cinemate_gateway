"""Streaming-app HID encodings for one stored AUX remote.

The remote record is the programmed library code. Each app profile encodes
remote buttons as the keyboard usages that app's published UI handles.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from software.hid import resolve_action

REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = REPO_ROOT / "software" / "profiles"
REMOTE_PATH = PROFILE_DIR / "remote.yaml"
PROFILE_IDS = ("amazon", "paramount", "kanopy", "youtubetv")


def load_remote(path: Path | None = None) -> dict:
    target = path or REMOTE_PATH
    data = yaml.safe_load(target.read_text()) or {}
    personality = data.get("personality")
    library_code = str(data.get("library_code") or "")
    if not personality or not library_code:
        raise ValueError(f"{target} needs personality and library_code")
    if not str(personality).endswith(library_code):
        raise ValueError(
            f"{target} personality {personality!r} does not end with library_code {library_code}"
        )
    on_off = data.get("on_off")
    if not isinstance(on_off, dict) or "confirmed" not in on_off:
        raise ValueError(f"{target} missing on_off.confirmed")
    if on_off.get("confirmed") and not on_off.get("frame_key") and not on_off.get("signature"):
        raise ValueError(f"{target} confirmed on_off needs frame_key or signature")
    return data


def validate_controls(controls: dict) -> None:
    if not isinstance(controls, dict) or not controls:
        raise ValueError("profile controls must be a non-empty dict")
    for button, control in controls.items():
        if not isinstance(control, dict) or "hid" not in control or "ui" not in control:
            raise ValueError(f"control {button!r} must have hid and ui")
        hid = control.get("hid")
        if hid is None:
            continue
        name = str(hid).strip().upper()
        if name.startswith("VOLUME"):
            raise ValueError(f"control {button!r} must not use consumer {name}")
        resolve_action(name)


def validate_profile(data: dict, remote_personality: str) -> dict:
    if data.get("remote") != remote_personality:
        raise ValueError(
            f"profile remote {data.get('remote')!r} != {remote_personality}"
        )
    if not data.get("id") or not data.get("source"):
        raise ValueError("profile needs id and source")
    validate_controls(data.get("controls"))
    return data


def load_profile(profile_id: str, path: Path | None = None) -> dict:
    if profile_id not in PROFILE_IDS:
        raise ValueError(f"unknown profile {profile_id!r}")
    target = path or (PROFILE_DIR / f"{profile_id}.yaml")
    data = yaml.safe_load(target.read_text()) or {}
    if data.get("id") != profile_id:
        raise ValueError(f"{target} id is {data.get('id')!r}")
    return validate_profile(data, load_remote()["personality"])


def control_hid(profile: dict, button: str) -> str | None:
    control = (profile.get("controls") or {}).get(str(button))
    if not isinstance(control, dict):
        return None
    hid = control.get("hid")
    if hid is None:
        return None
    return str(hid).strip().upper()
