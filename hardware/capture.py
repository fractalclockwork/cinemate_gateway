"""Receive-only IR capture. The IR LED stays off.

Unique mode (default): listen-only. Decode whatever IR arrives, keep unique
frame keys (attempted decode is enough). No button prompts. Ctrl+C stops.

Confirm-map mode (--confirm-map): prompt each unbound AUX button once; bind
sony-sirc20:1a:*:9a decodes into aux_dvr_20636_map.yaml.

Validate mode (--validate): agreeing a/b pairs accept one button at a time.
The library code is not an IR address; classification comes from the pulses.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import yaml

from harness.boards import REPO_ROOT, load_board, reports_root, run_report_dir, stage_passed
from hardware.loopback import RawRepl, find_pico_serial
from human import assent
from software.decode import MAPPED_PROTOCOLS, classify_pulses, split_frames
from software.profile import PROFILE_IDS, control_hid, load_profile

CONFIRM_MAP_DIR = (
    REPO_ROOT / "reports" / "pico" / "20261027T043341Z" / "captures"
)
CONFIRM_MAP_PATH = CONFIRM_MAP_DIR / "aux_dvr_20636_map.yaml"
CONFIRM_REPORT_PATH = CONFIRM_MAP_DIR / "aux_dvr_20636_sirc20.md"
SIRC_AUX_PREFIX = "sony-sirc20:1a:"
SIRC_AUX_SUFFIX = ":9a"

LISTEN_S = 5.0
LED_QUIET_S = 0.2
# One Sony SIRC-20 frame is 42 mark/space values. Stop after a short burst so
# auto-repeat does not fill PulseIn (maxlen 256) and truncate the capture.
MIN_BURST_EDGES = 42
CARRIER_NOTE = "CHQ1838 demodulated envelope, not the 38 kHz carrier"
# Operator: AUX holds Sony DVR 20636. Also collect TV source 10178.
PERSONALITIES: dict[str, dict[str, str]] = {
    "sony-dvr-20636": {
        "id": "sony-dvr-20636",
        "source": "AUX",
        "brand": "Sony",
        "list": "DVR",
        "code": "20636",
    },
    "tv-10178": {
        "id": "tv-10178",
        "source": "TV",
        "brand": "Universal",
        "list": "TV",
        "code": "10178",
    },
}
DEFAULT_UNIQUE_PASS = ("sony-dvr-20636", "tv-10178")
# Staged defaults for --validate path (AUX Sony DVR).
PERSONALITY = "sony-dvr-20636"
DEVICE_BRAND = "Sony"
DEVICE_LIST = "DVR"
DEVICE_CODE = "20636"
DEVICE_SOURCE = "AUX"
FACTS_PATH = REPO_ROOT / "docs" / "manual-facts.md"

# Plan waves: center `back` is the remote Exit key (HID escape on app profiles).
WAVES: dict[str, tuple[str, ...]] = {
    "on_off": ("on_off",),
    "center": ("up", "down", "left", "right", "enter", "back"),
    "transport": ("stop", "pause", "play", "ffw", "frw"),
    "digits": tuple(str(number) for number in range(10)),
}
# Extra face/guide keys for confirm-map only (not keymap stability gate).
INVENTORY_EXTRA: tuple[str, ...] = (
    "instant_replay",  # curved Instant Replay; not plan `back`
    "menu",
    "info",
    "guide",
    "page_up",
    "page_down",
    "record",
    "quick_skip",
    "channel_up",
    "channel_down",
    "previous",
    "tv_video",
    "vcr_tv",
    "widescreen",
    "list",
    "a",
    "b",
    "c",
    "setup",
)
MAP_WAVES = ("center", "transport", "digits")
MAP_BUTTONS: tuple[str, ...] = tuple(name for wave in MAP_WAVES for name in WAVES[wave])
ALL_BUTTONS: tuple[str, ...] = WAVES["on_off"] + MAP_BUTTONS
CONFIRM_BUTTONS: tuple[str, ...] = ALL_BUTTONS + INVENTORY_EXTRA
WAVE_OF = {name: wave for wave, names in WAVES.items() for name in names}
for _inv in INVENTORY_EXTRA:
    WAVE_OF.setdefault(_inv, "inventory")


def build_device_script(
    *,
    rx_pin: int,
    tx_pin: int,
    listen_s: float = LISTEN_S,
) -> str:
    """CircuitPython one-shot. TX is driven low for the whole listen. No PWM."""
    rx_pin = int(rx_pin)
    tx_pin = int(tx_pin)
    listen_s = float(listen_s)
    if not 0 <= rx_pin <= 28 or not 0 <= tx_pin <= 28 or rx_pin == tx_pin:
        raise SystemExit(f"refusing IR capture on pins rx={rx_pin} tx={tx_pin}")
    if listen_s <= 0 or listen_s > 5:
        raise SystemExit(f"listen window {listen_s} s is outside 0..5")
    return f"""import board
import digitalio
import json
import pulseio
import time

# Free pins left by a prior listen in this Raw REPL session (retries).
for _name in ("_cap_tx", "_cap_rx", "_cap_led", "hold", "tx", "rx", "led"):
    _obj = globals().get(_name)
    if _obj is not None:
        try:
            _obj.deinit()
        except Exception:
            pass
        globals()[_name] = None

tx = None
rx = None
led = None
try:
    tx = digitalio.DigitalInOut(board.GP{tx_pin})
    tx.direction = digitalio.Direction.OUTPUT
    tx.value = False
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT
    led.value = False
    rx = pulseio.PulseIn(board.GP{rx_pin}, maxlen=256, idle_state=True)
    rx.pause()
    rx.clear()
    rx.resume()
    deadline = time.monotonic() + {listen_s:.3f}
    seen = 0
    quiet_since = None
    while time.monotonic() < deadline:
        count = len(rx)
        if count > seen:
            seen = count
            led.value = True
            quiet_since = None
        elif seen > 0:
            now = time.monotonic()
            if quiet_since is None:
                quiet_since = now
            elif now - quiet_since >= {LED_QUIET_S:.1f}:
                led.value = False
                if seen >= {MIN_BURST_EDGES}:
                    break
                quiet_since = None
        else:
            time.sleep(0.01)
    rx.pause()
    led.value = False
    pulses = [rx[i] for i in range(len(rx))]
    print("CAPTURE_JSON " + json.dumps({{
        "pulses": pulses,
        "rx_pin": {rx_pin},
        "tx_pin": {tx_pin},
        "listen_s": {listen_s:.3f},
    }}))
finally:
    # Drive TX low, then release every pin so the next listen can claim them.
    if rx is not None:
        rx.deinit()
    if led is not None:
        led.value = False
        led.deinit()
    if tx is not None:
        tx.value = False
        tx.deinit()
    _cap_tx = None
    _cap_rx = None
    _cap_led = None
"""


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def _payload_from_stdout(stdout: str) -> dict:
    for line in stdout.splitlines():
        if line.startswith("CAPTURE_JSON "):
            return json.loads(line[len("CAPTURE_JSON ") :])
    raise RuntimeError(f"no CAPTURE_JSON in stdout: {stdout!r}")


def _label_frames(pulses: list[int]) -> list[dict]:
    return [
        {"role": "command" if index == 0 else "repeat", "pulses": frame}
        for index, frame in enumerate(split_frames(pulses))
    ]


def _sample_record(
    *,
    button: str,
    sample: str,
    pulses: list[int],
    attempt: int,
    rx_pin: int,
    tx_pin: int,
    personality: dict[str, str] | None = None,
) -> dict:
    person = personality or {
        "id": PERSONALITY,
        "source": DEVICE_SOURCE,
        "brand": DEVICE_BRAND,
        "list": DEVICE_LIST,
        "code": DEVICE_CODE,
    }
    return {
        "button": button,
        "sample": sample,
        "wave": WAVE_OF.get(button),
        "aux_personality": person["id"],
        "device_source": person["source"],
        "device_brand": person["brand"],
        "device_list": person["list"],
        "device_code": person["code"],
        "rx_pin": rx_pin,
        "tx_pin": tx_pin,
        "listen_s": LISTEN_S,
        "attempt": attempt,
        "miss": not pulses,
        "edges": len(pulses),
        "truncated": len(pulses) >= 256,
        "pulses": pulses,
        "frames": _label_frames(pulses),
        "classification": classify_pulses(pulses),
        "carrier_note": CARRIER_NOTE,
    }


def _frame_identity(classification: dict) -> str:
    key = classification.get("frame_key")
    if key:
        return str(key)
    sig = classification.get("signature") or {}
    return (
        f"unclassified:"
        f"{sig.get('first_mark')}/{sig.get('first_space')}:"
        f"{sig.get('count')}"
    )


def _load_unique_catalog(captures: Path) -> dict:
    path = captures / "unique_codes.json"
    if not path.is_file():
        return {"codes": {}, "hits": []}
    return json.loads(path.read_text())


def _save_unique_catalog(captures: Path, catalog: dict) -> None:
    _write_json(captures / "unique_codes.json", catalog)


def _listen_once(
    repl: RawRepl, script: str, rx_pin: int, tx_pin: int
) -> list[int]:
    """One listen window. Empty is normal; does not re-prompt."""
    stdout, stderr = repl.exec(script, timeout=LISTEN_S + 6.0)
    if stderr.strip():
        raise RuntimeError(stderr.strip())
    payload = _payload_from_stdout(stdout)
    if int(payload.get("rx_pin", -1)) != rx_pin or int(payload.get("tx_pin", -1)) != tx_pin:
        raise RuntimeError("device pins do not match the board YAML")
    return [int(value) for value in payload.get("pulses") or []]


def _wave_protocol(samples: list[dict]) -> dict:
    classes = []
    for sample in samples:
        if sample.get("miss") or int(sample.get("edges") or 0) == 0:
            continue
        classes.append(sample.get("classification") or {})
    if not classes or any(
        item.get("protocol") not in MAPPED_PROTOCOLS or not item.get("frame_key")
        for item in classes
    ):
        return {"protocol": "unclassified", "address": None}
    protocols = {item.get("protocol") for item in classes}
    addresses = {item.get("address") for item in classes}
    if len(protocols) != 1 or len(addresses) != 1:
        return {"protocol": "unclassified", "address": None}
    return {"protocol": protocols.pop(), "address": addresses.pop()}


def confirm_pair(pair: dict | None) -> dict:
    """Agreeing presses: shared frame key, or one shared unclassified signature."""
    empty = {"confirmed": False, "frame_key": None, "signature": None}
    if not pair:
        return empty
    classes = []
    for slot in ("a", "b"):
        sample = pair.get(slot)
        if sample is None or sample.get("miss") or not int(sample.get("edges") or 0):
            return empty
        classes.append(sample.get("classification") or {})
    keys = [item.get("frame_key") for item in classes]
    if keys[0] and keys[0] == keys[1]:
        return {"confirmed": True, "frame_key": keys[0], "signature": None}
    signatures = [item.get("signature") for item in classes]
    if (
        all(item.get("protocol") == "unclassified" for item in classes)
        and signatures[0]
        and signatures[0] == signatures[1]
    ):
        return {"confirmed": True, "frame_key": "unclassified", "signature": signatures[0]}
    return empty


confirm_on_off = confirm_pair


def _validated_path(captures: Path) -> Path:
    return captures / "validated.json"


def load_validated(captures: Path) -> dict:
    path = _validated_path(captures)
    if not path.is_file():
        return {
            "aux_personality": PERSONALITY,
            "device_code": DEVICE_CODE,
            "profile": None,
            "buttons": [],
        }
    return json.loads(path.read_text())


def sync_session_from_validated(captures: Path) -> dict:
    """Align session.json with validated.json (on_off_confirmed, validated list)."""
    validated = load_validated(captures)
    session_path = captures / "session.json"
    if session_path.is_file():
        session = json.loads(session_path.read_text())
    else:
        session = _session_document(rx_pin=0, tx_pin=0)
        session["status"] = "open"
    confirmed = [
        str(row["button"])
        for row in validated.get("buttons") or []
        if row.get("validated")
    ]
    session["validated"] = confirmed
    if "on_off" in confirmed:
        session["on_off_confirmed"] = True
        for row in validated.get("buttons") or []:
            if row.get("button") == "on_off" and row.get("validated"):
                session["on_off"] = {
                    "confirmed": True,
                    "frame_key": row.get("frame_key"),
                    "signature": row.get("signature"),
                }
                break
    elif confirmed:
        # Keep prior True if already set; never clear a True with empty logic above.
        pass
    _write_json(session_path, session)
    return session


def save_validated(captures: Path, data: dict) -> None:
    _write_json(_validated_path(captures), data)
    sync_session_from_validated(captures)


def validated_from_confirm_map(data: dict) -> dict:
    """Build validated.json payload from confirm-map YAML buttons."""
    buttons = []
    for name, row in (data.get("buttons") or {}).items():
        if str(row.get("status") or "") != "confirmed":
            continue
        key = row.get("frame_key")
        if not key:
            continue
        buttons.append(
            {
                "button": str(name),
                "frame_key": key,
                "hid": None,
                "validated": True,
                "evidence": row.get("evidence"),
            }
        )
    return {
        "aux_personality": data.get("personality") or PERSONALITY,
        "device_code": str(data.get("library_code") or DEVICE_CODE),
        "profile": None,
        "source": CONFIRM_MAP_PATH.name,
        "buttons": buttons,
    }


def persist_confirm_map_evidence(
    data: dict,
    captures: Path | None = None,
) -> None:
    """Write validated.json + synced session.json for the confirm-map stamp."""
    target = captures if captures is not None else CONFIRM_MAP_DIR
    target.mkdir(parents=True, exist_ok=True)
    save_validated(target, validated_from_confirm_map(data))


def validated_names(data: dict) -> list[str]:
    return [str(row["button"]) for row in data.get("buttons") or []]


def next_required_button(validated: list[str]) -> str | None:
    for name in ALL_BUTTONS:
        if name not in validated:
            return name
    return None


def build_button_table(samples: list[dict], validated: dict | None = None) -> dict:
    """Draft frame keys from samples; validated rows come from operator YES gates."""
    by_button: dict[str, dict[str, dict]] = {}
    for sample in samples:
        by_button.setdefault(str(sample["button"]), {})[str(sample["sample"])] = sample

    wave_info = {
        wave: _wave_protocol(
            [
                sample
                for name in names
                for sample in by_button.get(name, {}).values()
            ]
        )
        for wave, names in WAVES.items()
    }
    on_off = confirm_pair(by_button.get("on_off"))
    validated_rows = list((validated or {}).get("buttons") or [])
    validated_set = {str(row["button"]) for row in validated_rows}

    drafts: list[tuple[str, str, bool]] = []
    for name in ALL_BUTTONS:
        pair = by_button.get(name)
        if not pair:
            continue
        result = confirm_pair(pair)
        if result["confirmed"] and result["frame_key"] != "unclassified":
            drafts.append((name, str(result["frame_key"]), True))
        elif result["confirmed"]:
            drafts.append((name, "unclassified", True))
        else:
            keys = [
                (pair.get(slot) or {}).get("classification", {}).get("frame_key")
                for slot in ("a", "b")
            ]
            agreed = keys[0] is not None and keys[0] == keys[1]
            drafts.append((name, "unclassified", agreed))

    counts: dict[str, int] = {}
    for name, key, _agreed in drafts:
        if key != "unclassified" and name in validated_set:
            counts[key] = counts.get(key, 0) + 1

    rows = []
    for name, key, agreed in drafts:
        if name not in validated_set:
            rows.append(
                {
                    "button": name,
                    "frame_key": key if agreed else "unclassified",
                    "agreed": agreed,
                    "validated": False,
                }
            )
        elif key != "unclassified" and counts.get(key, 0) > 1:
            rows.append(
                {
                    "button": name,
                    "frame_key": "unclassified",
                    "agreed": agreed,
                    "validated": True,
                }
            )
        else:
            rows.append(
                {
                    "button": name,
                    "frame_key": key,
                    "agreed": agreed,
                    "validated": True,
                }
            )

    map_validated = [row for row in validated_rows if row["button"] in MAP_BUTTONS]
    stable = [str(row["button"]) for row in map_validated] == list(MAP_BUTTONS) and all(
        row.get("frame_key") and row["frame_key"] != "unclassified" for row in map_validated
    )
    return {
        "aux_personality": PERSONALITY,
        "device_source": DEVICE_SOURCE,
        "device_brand": DEVICE_BRAND,
        "device_list": DEVICE_LIST,
        "device_code": DEVICE_CODE,
        "carrier_note": CARRIER_NOTE,
        "waves": wave_info,
        "on_off_confirmed": on_off["confirmed"] or "on_off" in validated_set,
        "on_off": on_off,
        "stable": stable,
        "validated": validated_rows,
        "buttons": rows,
    }


def keymap_pairs(table: dict, profile_id: str) -> list[tuple[str, str]] | None:
    if not table.get("on_off_confirmed"):
        return None
    profile = load_profile(profile_id)
    pairs = []
    for row in table.get("validated") or []:
        if row.get("button") == "on_off":
            continue
        key = row.get("frame_key")
        if not key or key == "unclassified":
            continue
        hid = row.get("hid")
        if hid is None:
            hid = control_hid(profile, row["button"])
        if hid is None:
            continue
        pairs.append((key, str(hid)))
    keys = [key for key, _action in pairs]
    if len(keys) != len(set(keys)):
        return None
    if not pairs:
        return None
    return pairs


def render_keymap(pairs: list[tuple[str, str]], stamp: str, profile_id: str) -> str:
    lines = [
        f"# {DEVICE_BRAND} {DEVICE_LIST} library code {DEVICE_CODE} staged on AUX.",
        "# Frame keys are measured; agreeing a/b samples accept each button.",
        f"# Evidence: reports/pico/{stamp}/captures/validated.json",
        "version: 1",
        "mode_gate: aux",
        f"personality: {PERSONALITY}",
        f"profile: {profile_id}",
        "ignore_speaker_always: true",
        "ignore: []",
        "map:",
    ]
    for ir_key, action in pairs:
        shown = f'"{action}"' if action.isdigit() else action
        lines.append(f"  {ir_key}: {shown}")
    return "\n".join(lines) + "\n"


def _record_remote_on_off(stamp: str, result: dict) -> None:
    """Write On-Off evidence into software/profiles/remote.yaml after an agreeing pair."""
    import yaml

    path = REPO_ROOT / "software" / "profiles" / "remote.yaml"
    data = yaml.safe_load(path.read_text()) or {}
    data["code_check"] = [int(digit) for digit in DEVICE_CODE]
    data["on_off"] = {
        "confirmed": True,
        "evidence": f"reports/pico/{stamp}/captures",
        "frame_key": result.get("frame_key"),
        "signature": result.get("signature"),
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def append_measured_fact(facts_path: Path, bullet: str) -> None:
    bullet = bullet if bullet.startswith("- ") else f"- {bullet}"
    text = facts_path.read_text()
    if bullet in text:
        return
    heading = "## Phase 1 policy for this project\n"
    if heading not in text:
        raise RuntimeError(f"{facts_path} missing phase 1 heading")
    block = "## Measured capture\n\n" + bullet + "\n\n"
    if "## Measured capture\n" in text:
        text = text.replace("## Measured capture\n", "## Measured capture\n\n" + bullet + "\n", 1)
    else:
        text = text.replace(heading, block + heading, 1)
    facts_path.write_text(text)


def _empty_aux_bullet(stamp: str, buttons: list[str]) -> str:
    listed = ", ".join(f"`{name}`" for name in buttons)
    return (
        f"- {DEVICE_LIST} `{DEVICE_CODE}` on AUX, session `reports/pico/{stamp}/captures/`: "
        f"listen windows for {listed} recorded no IR edges on GPIO14. "
        "The wave stopped before later buttons were requested."
    )


def _session_document(rx_pin: int, tx_pin: int) -> dict:
    return {
        "aux_personality": PERSONALITY,
        "device_source": DEVICE_SOURCE,
        "device_brand": DEVICE_BRAND,
        "device_list": DEVICE_LIST,
        "device_code": DEVICE_CODE,
        "rx_pin": rx_pin,
        "tx_pin": tx_pin,
        "carrier_note": CARRIER_NOTE,
        "status": "open",
        "stop_reason": None,
        "on_off_confirmed": False,
        "validated": [],
        "buttons": [],
    }


def find_open_session(board_id: str) -> Path | None:
    """Resume the incomplete session with the most validated buttons."""
    root = reports_root() / board_id
    if not root.is_dir():
        return None
    best: tuple[int, Path, dict] | None = None
    for path in sorted(root.glob("*/captures/session.json")):
        data = json.loads(path.read_text())
        if data.get("aux_personality") != PERSONALITY:
            continue
        if data.get("status") not in {"open", "stopped", "parked"}:
            continue
        captures = path.parent
        done = validated_names(load_validated(captures))
        if next_required_button(done) is None:
            continue
        # Prefer more validated buttons; on a tie keep an already-open session.
        score = (len(done), 1 if data.get("status") == "open" else 0)
        if best is None or score > best[0]:
            best = (score, captures, data)
    if best is None:
        return None
    _, captures, data = best
    if data.get("status") != "open":
        data["status"] = "open"
        data["stop_reason"] = None
        _write_json(captures / "session.json", data)
    # Park other open sessions for this personality so only one stays live.
    for path in root.glob("*/captures/session.json"):
        if path.parent == captures:
            continue
        other = json.loads(path.read_text())
        if (
            other.get("status") == "open"
            and other.get("aux_personality") == PERSONALITY
        ):
            other["status"] = "parked"
            other["stop_reason"] = "superseded by resumed capture session"
            _write_json(path, other)
    return captures


def park_open_sessions(board_id: str) -> None:
    root = reports_root() / board_id
    if not root.is_dir():
        return
    for path in root.glob("*/captures/session.json"):
        data = json.loads(path.read_text())
        if data.get("status") == "open" and data.get("aux_personality") == PERSONALITY:
            data["status"] = "parked"
            data["stop_reason"] = "superseded by a new capture session"
            _write_json(path, data)


def _create_session(board_id: str, rx_pin: int, tx_pin: int) -> Path:
    captures = run_report_dir(board_id) / "captures"
    captures.mkdir(parents=True, exist_ok=True)
    _write_json(captures / "session.json", _session_document(rx_pin, tx_pin))
    return captures


def _load_samples(captures: Path) -> list[dict]:
    rows = []
    for path in sorted(captures.glob("*-*.json")):
        data = json.loads(path.read_text())
        if data.get("sample") in {"a", "b"} and data.get("button") in WAVE_OF:
            rows.append(data)
    return rows


def _any_edges(samples: list[dict]) -> bool:
    return any(int(sample.get("edges") or 0) > 0 for sample in samples)


def _write_table(captures: Path, profile_id: str | None = None) -> dict:
    validated = load_validated(captures)
    if profile_id and not validated.get("profile"):
        validated["profile"] = profile_id
        save_validated(captures, validated)
    table = build_button_table(_load_samples(captures), validated)
    _write_json(captures / "buttons.json", table)
    if profile_id is None:
        return table
    pairs = keymap_pairs(table, profile_id)
    if pairs is None:
        return table
    from software.keymap import ACTIVE

    stamp = captures.parent.name
    ACTIVE.write_text(render_keymap(pairs, stamp, profile_id))
    return table


def _pair_samples(captures: Path, button: str) -> dict[str, dict] | None:
    slots: dict[str, dict] = {}
    for sample in ("a", "b"):
        path = captures / f"{button}-{sample}.json"
        if not path.is_file():
            return None
        data = json.loads(path.read_text())
        if data.get("miss") or not data.get("edges"):
            return None
        # Reclassify so older archives pick up Sony / multi-frame fixes.
        data["classification"] = classify_pulses(data.get("pulses") or [])
        slots[sample] = data
    return slots


def _clear_button_samples(captures: Path, button: str) -> None:
    for sample in ("a", "b"):
        path = captures / f"{button}-{sample}.json"
        if path.is_file():
            path.unlink()


def _already_captured(captures: Path, button: str) -> bool:
    return _pair_samples(captures, button) is not None


def _acquire(repl: RawRepl, script: str, rx_pin: int, tx_pin: int, button: str, sample: str) -> tuple[list[int], int]:
    """Listen until edges arrive. Empty windows re-prompt; they do not stop the wave."""
    attempt = 0
    while True:
        attempt += 1
        print(
            f"PRESS {button} sample {sample} — short press now "
            f"(listening {LISTEN_S:.0f}s, attempt {attempt})",
            flush=True,
        )
        stdout, stderr = repl.exec(script, timeout=LISTEN_S + 6.0)
        if stderr.strip():
            raise RuntimeError(stderr.strip())
        payload = _payload_from_stdout(stdout)
        if int(payload.get("rx_pin", -1)) != rx_pin or int(payload.get("tx_pin", -1)) != tx_pin:
            raise RuntimeError("device pins do not match the board YAML")
        pulses = [int(value) for value in payload.get("pulses") or []]
        print(f"  {button} sample {sample}: {len(pulses)} edges", flush=True)
        if pulses:
            return pulses, attempt
        print(
            f"  {button} sample {sample}: no edges — press {button} again when ready",
            flush=True,
        )


def _print_decode(button: str, sample: str, record: dict) -> None:
    classification = record.get("classification") or {}
    key = classification.get("frame_key")
    if key:
        print(f"  decode {button}-{sample}: {key}", flush=True)
        return
    sig = classification.get("signature") or {}
    print(
        f"  decode {button}-{sample}: unclassified "
        f"edges={record.get('edges')} "
        f"first={sig.get('first_mark')}/{sig.get('first_space')} "
        f"count={sig.get('count')}",
        flush=True,
    )


def _accept_button(
    captures: Path,
    session: dict,
    button: str,
    result: dict,
    profile_id: str | None,
) -> str | None:
    """Record an agreeing IR pair. HID/profile mapping is deferred."""
    _ = profile_id
    print(
        f"{button}: agreed frame_key={result['frame_key']} — accepted",
        flush=True,
    )
    row = {
        "button": button,
        "frame_key": result["frame_key"],
        "validated": True,
    }
    validated = load_validated(captures)
    validated["aux_personality"] = PERSONALITY
    validated["device_code"] = DEVICE_CODE
    validated["buttons"] = [
        item for item in validated.get("buttons") or [] if item.get("button") != button
    ]
    validated["buttons"].append(row)
    save_validated(captures, validated)
    done = validated_names(validated)
    session["validated"] = done
    if button == "on_off":
        session["on_off_confirmed"] = True
        session["on_off"] = result
        _record_remote_on_off(captures.parent.name, result)
    next_name = next_required_button(done)
    if next_name is None:
        session["status"] = "complete"
    _write_json(captures / "session.json", session)
    if next_name:
        print(f"accepted {button}. next: {next_name}", flush=True)
    else:
        print(f"accepted {button}. All buttons validated.", flush=True)
    return next_name


def run_unique_session(
    board: dict,
    *,
    personalities: list[str],
    ready_wait: float = 0,
    fresh: bool = False,
) -> int:
    """Listen-only unique IR decode. No prompts. Ctrl+C finishes."""
    board_id = board["id"]
    assent.require_verify("unique IR capture")
    if assent.is_sim():
        raise SystemExit("IR capture refuses IR_GATEWAY_HWIL_SIM")
    for prior in ("present", "workflow"):
        if not stage_passed(board_id, prior):
            raise SystemExit(
                f"{prior} stage has not passed. "
                f"Next: HUMAN_VERIFY=1 make stage BOARD={board_id} STAGE={prior}"
            )
    pins = board.get("pins") or {}
    if pins.get("ir_rx") is None or pins.get("ir_tx") is None:
        raise SystemExit("board pins.ir_rx and pins.ir_tx must be set before capture")
    rx_pin = int(pins["ir_rx"])
    tx_pin = int(pins["ir_tx"])
    unknown = [name for name in personalities if name not in PERSONALITIES]
    if unknown:
        raise SystemExit(f"unknown personalities: {unknown}")
    # Tag hits with the first listed personality as the expected remote slot;
    # operator may also switch sources (e.g. TV) while listening.
    person = PERSONALITIES[personalities[0]]

    if fresh:
        root = reports_root() / board_id
        if root.is_dir():
            for path in root.glob("*/captures/session.json"):
                data = json.loads(path.read_text())
                if data.get("status") == "open":
                    data["status"] = "parked"
                    data["stop_reason"] = "superseded by unique capture"
                    _write_json(path, data)
        captures = _create_session(board_id, rx_pin, tx_pin)
    else:
        captures = find_open_session(board_id) or _create_session(board_id, rx_pin, tx_pin)

    session = json.loads((captures / "session.json").read_text())
    session["mode"] = "unique-listen"
    session["personalities"] = list(personalities)
    session["status"] = "open"
    session["stop_reason"] = None
    _write_json(captures / "session.json", session)

    catalog = _load_unique_catalog(captures)
    catalog.setdefault("codes", {})
    catalog.setdefault("hits", [])

    script = build_device_script(rx_pin=rx_pin, tx_pin=tx_pin)
    port = find_pico_serial()
    print(
        "Listen-only unique IR decode. No button prompts. "
        "Press any keys freely (source LED blink = TX). "
        "Attempted decode is recorded; map buttons later. "
        "Ctrl+C to stop.",
        flush=True,
    )
    for name in personalities:
        slot = PERSONALITIES[name]
        print(
            f"  expected slot {slot['id']}: {slot['source']} / {slot['list']} "
            f"{slot['code']} code-check {[int(d) for d in slot['code']]}",
            flush=True,
        )
    print(f"Listening on {person['source']} tag={person['id']}…", flush=True)
    if ready_wait > 0:
        print(f"Starting in {ready_wait:.0f} seconds.", flush=True)
        time.sleep(ready_wait)

    repl = RawRepl(port)
    entered = False
    hit_index = len(catalog["hits"])
    try:
        repl.enter()
        entered = True
        while True:
            pulses = _listen_once(repl, script, rx_pin, tx_pin)
            if not pulses:
                continue
            hit_index += 1
            sample = f"{hit_index:05d}"
            record = _sample_record(
                button="listen",
                sample=sample,
                pulses=pulses,
                attempt=1,
                rx_pin=rx_pin,
                tx_pin=tx_pin,
                personality=person,
            )
            path = captures / f"hit-{sample}.json"
            _write_json(path, record)
            classification = record.get("classification") or {}
            identity = _frame_identity(classification)
            is_new = identity not in catalog["codes"]
            entry = catalog["codes"].setdefault(
                identity,
                {
                    "frame_key": classification.get("frame_key"),
                    "protocol": classification.get("protocol"),
                    "count": 0,
                    "personalities": {},
                },
            )
            entry["count"] = int(entry.get("count") or 0) + 1
            entry["personalities"][person["id"]] = (
                int(entry["personalities"].get(person["id"]) or 0) + 1
            )
            catalog["hits"].append(
                {
                    "file": path.name,
                    "personality": person["id"],
                    "identity": identity,
                    "edges": record.get("edges"),
                    "new": is_new,
                }
            )
            _save_unique_catalog(captures, catalog)
            session["hit_count"] = hit_index
            session["unique_count"] = len(catalog["codes"])
            _write_json(captures / "session.json", session)
            mark = "NEW" if is_new else "dup"
            key = classification.get("frame_key") or identity
            print(
                f"  [{mark}] {key} edges={record.get('edges')} "
                f"unique={len(catalog['codes'])} hits={hit_index}",
                flush=True,
            )
    except KeyboardInterrupt:
        print("\nStopping unique capture (Ctrl+C).", flush=True)
        session["status"] = "stopped"
        session["stop_reason"] = "operator stop"
        session["unique_count"] = len(catalog["codes"])
        _write_json(captures / "session.json", session)
        _save_unique_catalog(captures, catalog)
        print(
            f"unique_codes: {captures / 'unique_codes.json'} "
            f"codes={len(catalog['codes'])} hits={len(catalog['hits'])}",
            flush=True,
        )
        return 0
    finally:
        if entered:
            try:
                repl.restore_firmware()
            except (OSError, TimeoutError):
                pass
        repl.close()
    return 0


def _is_aux_sirc20(frame_key: str | None) -> bool:
    if not frame_key:
        return False
    return frame_key.startswith(SIRC_AUX_PREFIX) and frame_key.endswith(SIRC_AUX_SUFFIX)


def _load_confirm_map(path: Path = CONFIRM_MAP_PATH) -> dict:
    if not path.is_file():
        raise SystemExit(f"missing map file {path}")
    data = yaml.safe_load(path.read_text()) or {}
    data.setdefault("buttons", {})
    return data


def _save_confirm_map(data: dict, path: Path = CONFIRM_MAP_PATH) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def _buttons_needing_confirm(data: dict) -> list[str]:
    buttons = data.get("buttons") or {}
    needed: list[str] = []
    for name in CONFIRM_BUTTONS:
        row = buttons.get(name)
        if row is None:
            needed.append(name)
            continue
        status = str(row.get("status") or "")
        if status in {"unbound", "silent", "confirmed"}:
            continue
        if status in {"provisional", "reconfirm"} or not _is_aux_sirc20(
            row.get("frame_key")
        ):
            needed.append(name)
    return needed


def _rewrite_confirm_report(data: dict, path: Path = CONFIRM_REPORT_PATH) -> None:
    if not path.is_file():
        return
    text = path.read_text()
    marker = "## Confirmed button map\n"
    if marker not in text:
        return
    head = text.split(marker, 1)[0] + marker
    rest = text.split(marker, 1)[1]
    notes = ""
    if "\n### Confirm notes\n" in rest:
        notes = "\n### Confirm notes\n" + rest.split("\n### Confirm notes\n", 1)[1]
    rows = []
    collisions: dict[str, list[str]] = {}
    for name in CONFIRM_BUTTONS:
        row = (data.get("buttons") or {}).get(name) or {}
        if str(row.get("status")) != "confirmed":
            continue
        key = str(row.get("frame_key") or "")
        rows.append(f"| {name} | `{key}` | {row.get('evidence', '')} |")
        collisions.setdefault(key, []).append(name)
    collided = {key: names for key, names in collisions.items() if len(names) > 1}
    body = (
        "\n_Updated after `MODE=confirm` guided pass "
        "(two agreeing SIRC presses)._\n\n"
    )
    if rows:
        body += (
            "| Button | frame_key | Evidence |\n| --- | --- | --- |\n"
            + "\n".join(rows)
            + "\n"
        )
    else:
        body += "(none yet)\n"
    if collided and "### Confirm notes\n" not in notes:
        lines = [
            "",
            "### Confirm notes",
            "",
            "- Frame-key collisions on this pass:",
        ]
        for key, names in sorted(collided.items()):
            lines.append(f"  - `{key}` ← {', '.join(names)}")
        notes = "\n".join(lines) + "\n"
    elif collided:
        # Refresh collision bullets at top of notes if present.
        pass
    path.write_text(head + body + (notes if notes.startswith("\n") else ("\n" + notes if notes else "")))


def run_confirm_map_session(
    board: dict,
    *,
    ready_wait: float = 0,
    map_path: Path = CONFIRM_MAP_PATH,
) -> int:
    """Guided AUX SIRC-20 button→frame_key confirm. Ctrl+C saves partial map."""
    board_id = board["id"]
    assent.require_verify("AUX SIRC map confirm")
    if assent.is_sim():
        raise SystemExit("IR capture refuses IR_GATEWAY_HWIL_SIM")
    for prior in ("present", "workflow"):
        if not stage_passed(board_id, prior):
            raise SystemExit(
                f"{prior} stage has not passed. "
                f"Next: HUMAN_VERIFY=1 make stage BOARD={board_id} STAGE={prior}"
            )
    pins = board.get("pins") or {}
    if pins.get("ir_rx") is None or pins.get("ir_tx") is None:
        raise SystemExit("board pins.ir_rx and pins.ir_tx must be set before capture")
    rx_pin = int(pins["ir_rx"])
    tx_pin = int(pins["ir_tx"])
    person = PERSONALITIES["sony-dvr-20636"]
    data = _load_confirm_map(map_path)
    queue = _buttons_needing_confirm(data)
    if not queue:
        print("All buttons already confirmed in the map.", flush=True)
        _rewrite_confirm_report(data)
        return 0

    script = build_device_script(rx_pin=rx_pin, tx_pin=tx_pin)
    port = find_pico_serial()
    print(
        f"Confirm AUX SIRC-20 map ({person['id']}). "
        f"Select {person['source']}; code-check "
        f"{[int(d) for d in person['code']]}. "
        "Source LED blink = TX. Rejects Bose/unclassified/nec-like. "
        "Two agreeing SIRC presses bind the button. "
        "Three empty listens (no source-LED TX) marks unbound. "
        "Ctrl+C saves partial map.",
        flush=True,
    )
    print(f"Queue ({len(queue)}): {', '.join(queue)}", flush=True)
    print(
        "OPERATOR: select AUX, hold remote at CHQ1838, watch source LED. "
        "Press only the named button when prompted.",
        flush=True,
    )
    if ready_wait > 0:
        print(
            f"Operator ready-wait: {ready_wait:.0f}s before first listen.",
            flush=True,
        )
        time.sleep(ready_wait)

    repl = RawRepl(port)
    entered = False

    def _read_sirc(button: str, sample: str, silent: list[int]) -> str | None:
        """Return frame_key, or None when three empty listens mark unbound."""
        while True:
            if silent[0] >= 3:
                return None
            print(f"PRESS {button} sample {sample} — short press now", flush=True)
            pulses = _listen_once(repl, script, rx_pin, tx_pin)
            if not pulses:
                silent[0] += 1
                print(
                    f"  {button}-{sample}: no edges "
                    f"(silent {silent[0]}/3 → unbound)",
                    flush=True,
                )
                continue
            record = _sample_record(
                button=button,
                sample=sample,
                pulses=pulses,
                attempt=1,
                rx_pin=rx_pin,
                tx_pin=tx_pin,
                personality=person,
            )
            key = (record.get("classification") or {}).get("frame_key")
            print(
                f"  decode {button}-{sample}: {key or 'unclassified'} "
                f"edges={record.get('edges')}",
                flush=True,
            )
            if not _is_aux_sirc20(key):
                print(
                    f"  {button}-{sample}: not AUX SIRC-20 (1a/9a) — press again",
                    flush=True,
                )
                continue
            silent[0] = 0
            return str(key)

    try:
        repl.enter()
        entered = True
        for button in queue:
            while True:
                silent = [0]
                first = _read_sirc(button, "a", silent)
                if first is None:
                    data.setdefault("buttons", {})[button] = {
                        "frame_key": None,
                        "status": "unbound",
                        "note": (
                            "confirm-map: three empty listens "
                            "(no source-LED TX on AUX+20636)"
                        ),
                        "evidence": (
                            f"confirm-map-silent "
                            f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
                        ),
                    }
                    _save_confirm_map(data, map_path)
                    persist_confirm_map_evidence(data, CONFIRM_MAP_DIR)
                    print(f"  unbound {button} (silent)", flush=True)
                    break
                second = _read_sirc(button, "b", silent)
                if second is None:
                    data.setdefault("buttons", {})[button] = {
                        "frame_key": None,
                        "status": "unbound",
                        "note": (
                            "confirm-map: three empty listens "
                            "(no source-LED TX on AUX+20636)"
                        ),
                        "prior_frame_key": first,
                        "evidence": (
                            f"confirm-map-silent "
                            f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
                        ),
                    }
                    _save_confirm_map(data, map_path)
                    persist_confirm_map_evidence(data, CONFIRM_MAP_DIR)
                    print(f"  unbound {button} (silent after {first})", flush=True)
                    break
                if first != second:
                    print(
                        f"  {button}: presses disagreed ({first} vs {second}) — "
                        f"press {button} twice again",
                        flush=True,
                    )
                    continue
                prior = ((data.get("buttons") or {}).get(button) or {}).get(
                    "prior_frame_key"
                ) or ((data.get("buttons") or {}).get(button) or {}).get("frame_key")
                row = {
                    "frame_key": first,
                    "status": "confirmed",
                    "evidence": (
                        f"confirm-map-2x {time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
                    ),
                }
                if prior and prior != first:
                    row["prior_frame_key"] = prior
                    row["note"] = f"changed from {prior}"
                data.setdefault("buttons", {})[button] = row
                _save_confirm_map(data, map_path)
                persist_confirm_map_evidence(data, CONFIRM_MAP_DIR)
                print(f"  confirmed {button} → {first}", flush=True)
                break
        _rewrite_confirm_report(data)
        persist_confirm_map_evidence(data, CONFIRM_MAP_DIR)
        print(f"map: {map_path}", flush=True)
        return 0
    except KeyboardInterrupt:
        print("\nStopping confirm-map (Ctrl+C); saving partial map.", flush=True)
        _save_confirm_map(data, map_path)
        persist_confirm_map_evidence(data, CONFIRM_MAP_DIR)
        _rewrite_confirm_report(data)
        print(f"map: {map_path}", flush=True)
        return 0
    finally:
        if entered:
            try:
                repl.restore_firmware()
            except (OSError, TimeoutError):
                pass
        repl.close()


def run_session(
    board: dict,
    buttons: list[str] | None = None,
    *,
    ready_wait: float = 0,
    fresh: bool = False,
    profile_id: str | None = None,
) -> int:
    board_id = board["id"]
    assent.require_verify("AUX IR capture")
    if assent.is_sim():
        raise SystemExit("IR capture refuses IR_GATEWAY_HWIL_SIM")
    for prior in ("present", "workflow"):
        if not stage_passed(board_id, prior):
            raise SystemExit(
                f"{prior} stage has not passed. "
                f"Next: HUMAN_VERIFY=1 make stage BOARD={board_id} STAGE={prior}"
            )
    pins = board.get("pins") or {}
    if pins.get("ir_rx") is None or pins.get("ir_tx") is None:
        raise SystemExit("board pins.ir_rx and pins.ir_tx must be set before capture")
    rx_pin = int(pins["ir_rx"])
    tx_pin = int(pins["ir_tx"])
    buttons = list(buttons or [])
    unknown = [name for name in buttons if name not in WAVE_OF]
    if unknown:
        raise SystemExit(f"unknown buttons: {unknown}")
    if len(buttons) > 1:
        raise SystemExit("pass at most one --button to start from that key")

    if fresh:
        park_open_sessions(board_id)
        captures = _create_session(board_id, rx_pin, tx_pin)
    else:
        captures = find_open_session(board_id) or _create_session(board_id, rx_pin, tx_pin)

    validated = load_validated(captures)
    done = validated_names(validated)
    required = next_required_button(done)
    if required is None:
        raise SystemExit("every button is already validated")
    if buttons and buttons[0] != required:
        raise SystemExit(
            f"validate {required} before {buttons[0]}. "
            f"Next: HUMAN_VERIFY=1 make capture BUTTON={required}"
        )
    queue = [name for name in ALL_BUTTONS if name not in done]

    script = build_device_script(rx_pin=rx_pin, tx_pin=tx_pin)
    port = find_pico_serial()
    print(
        f"Staged personality: {DEVICE_SOURCE} / {DEVICE_LIST} {DEVICE_CODE} "
        f"({PERSONALITY}). Program Setup → {DEVICE_SOURCE} → {DEVICE_CODE} if "
        f"needed; code-check expect {[int(d) for d in DEVICE_CODE]} "
        f"(0 = long blink). Leave {DEVICE_SOURCE} selected; aim at CHQ1838. "
        "Short+double flash after entry is accept on this unit. "
        "Selected source LED blinks when a press actually TX's IR "
        "(no blink = silent key for this personality). "
        "Onboard LED = IR edges only. IR LED stays off. "
        "Agreeing a/b samples accept the button and advance.",
        flush=True,
    )
    print(f"Queue: {', '.join(queue)}", flush=True)
    if ready_wait > 0:
        print(f"Starting in {ready_wait:.0f} seconds.", flush=True)
        time.sleep(ready_wait)

    repl = RawRepl(port)
    entered = False
    exit_code = 0
    try:
        repl.enter()
        entered = True
        session = json.loads((captures / "session.json").read_text())
        for button in queue:
            print(f"Validate button: {button}", flush=True)
            if button not in session["buttons"]:
                session["buttons"].append(button)
            while True:
                _clear_button_samples(captures, button)
                for sample in ("a", "b"):
                    pulses, attempt = _acquire(
                        repl, script, rx_pin, tx_pin, button, sample
                    )
                    record = _sample_record(
                        button=button,
                        sample=sample,
                        pulses=pulses,
                        attempt=attempt,
                        rx_pin=rx_pin,
                        tx_pin=tx_pin,
                    )
                    _write_json(captures / f"{button}-{sample}.json", record)
                    _print_decode(button, sample, record)
                pair = _pair_samples(captures, button)
                result = confirm_pair(pair)
                if result["confirmed"] and result["frame_key"] not in (None, "unclassified"):
                    _accept_button(captures, session, button, result, profile_id)
                    break
                a_key = (pair or {}).get("a", {}).get("classification", {}).get("frame_key")
                b_key = (pair or {}).get("b", {}).get("classification", {}).get("frame_key")
                print(
                    f"{button}: presses did not agree (a={a_key} b={b_key}) — "
                    f"press {button} twice again",
                    flush=True,
                )
        _write_json(captures / "session.json", session)
        if (captures / "session.json").is_file() and _load_samples(captures):
            table = _write_table(captures, profile_id)
            print(
                f"buttons: {captures / 'buttons.json'} "
                f"stable={table['stable']} on_off_confirmed={table['on_off_confirmed']}",
                flush=True,
            )
    finally:
        if entered:
            try:
                repl.restore_firmware()
            except (OSError, TimeoutError):
                pass
        repl.close()
    return exit_code


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Receive-only IR capture (unique, confirm-map, or validate)"
    )
    parser.add_argument("--board", default="pico")
    parser.add_argument("--button", choices=ALL_BUTTONS)
    parser.add_argument("--profile", choices=PROFILE_IDS)
    parser.add_argument("--ready-wait", type=float, default=0)
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument(
        "--unique",
        action="store_true",
        help="listen-only unique-code decode (Ctrl+C to finish)",
    )
    parser.add_argument(
        "--confirm-map",
        action="store_true",
        help="guided AUX SIRC-20 button→frame_key confirm",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="staged per-button a/b validation (legacy)",
    )
    parser.add_argument(
        "--personality",
        action="append",
        choices=sorted(PERSONALITIES),
        help="tag hits with this personality (default AUX 20636; TV 10178 also listed)",
    )
    args = parser.parse_args(argv)
    modes = sum(bool(flag) for flag in (args.unique, args.confirm_map, args.validate))
    if modes > 1:
        raise SystemExit("pass only one of --unique, --confirm-map, or --validate")
    if args.confirm_map:
        code = run_confirm_map_session(
            load_board(args.board),
            ready_wait=args.ready_wait,
        )
    elif args.unique or (not args.validate and not args.button):
        people = args.personality or list(DEFAULT_UNIQUE_PASS)
        code = run_unique_session(
            load_board(args.board),
            personalities=people,
            ready_wait=args.ready_wait,
            fresh=args.fresh,
        )
    else:
        code = run_session(
            load_board(args.board),
            [args.button] if args.button else None,
            ready_wait=args.ready_wait,
            fresh=args.fresh,
            profile_id=args.profile,
        )
    if code:
        raise SystemExit(code)


if __name__ == "__main__":
    main()
