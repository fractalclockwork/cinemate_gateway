"""USB presence probe for the Pico DUT."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


def is_sim() -> bool:
    return os.environ.get("IR_GATEWAY_HWIL_SIM") == "1"


def list_usb_devices() -> list[dict]:
    """Return USB device dicts with vendor/product hex strings."""
    if is_sim():
        return [
            {
                "vendor": "2e8a",
                "product": "0005",
                "name": "simulated CircuitPython Pico",
            }
        ]
    try:
        out = subprocess.check_output(["lsusb"], text=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"lsusb failed: {exc}") from exc
    devices = []
    for line in out.splitlines():
        match = re.search(r"ID ([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\s*(.*)$", line)
        if not match:
            continue
        devices.append(
            {
                "vendor": match.group(1).lower(),
                "product": match.group(2).lower(),
                "name": match.group(3).strip(),
            }
        )
    return devices


def find_pico(board: dict) -> dict | None:
    vendor = str(board.get("usb_vendor", "2e8a")).lower()
    allowed = {
        str(board.get("usb_product_boot", "0003")).lower(),
        str(board.get("usb_product_circuitpython", "0005")).lower(),
    }
    for dev in list_usb_devices():
        if dev["vendor"] == vendor and dev["product"] in allowed:
            return dev
    # Also accept Adafruit VID used by many CircuitPython builds.
    for dev in list_usb_devices():
        if dev["vendor"] == "239a":
            return {**dev, "note": "Adafruit VID CircuitPython device"}
    return None


def circuitpy_mount() -> Path | None:
    if is_sim():
        return Path("/tmp/IR_GATEWAY_SIM_CIRCUITPY")
    candidates = [
        Path("/media") / os.environ.get("USER", "user") / "CIRCUITPY",
        Path("/run/media") / os.environ.get("USER", "user") / "CIRCUITPY",
        Path("/mnt/CIRCUITPY"),
    ]
    for path in candidates:
        if path.is_dir():
            return path
    return None
