"""Flash / deploy CircuitPython app after operator verification and a present pass."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from harness.boards import load_board, stage_passed
from hardware import probe
from human import assent

FIRMWARE_SRC = Path(__file__).resolve().parent / "firmware" / "pico"


def warn_if_adafruit_hid_missing(root: Path) -> None:
    """Warn when CIRCUITPY lacks adafruit_hid (does not invent a install)."""
    hid_dir = root / "lib" / "adafruit_hid"
    marker = hid_dir / "__init__.py"
    if hid_dir.is_dir() and (marker.is_file() or any(hid_dir.glob("*.mpy"))):
        return
    print(
        "WARNING: adafruit_hid not found under "
        f"{root / 'lib' / 'adafruit_hid'}. "
        "code.py will ImportError until you copy adafruit_hid from the "
        "Adafruit CircuitPython Library Bundle into CIRCUITPY/lib/. "
        "See hardware/firmware/pico/README.md and environment/README.md."
    )


def deploy(board: dict) -> None:
    board_id = board["id"]
    assent.require_verify(f"firmware write for {board_id}")
    assent.require_flash(board_id)
    if not stage_passed(board_id, "present"):
        raise SystemExit(
            f"{board_id} present stage has not passed. "
            f"Next: HUMAN_VERIFY=1 make stage BOARD={board_id} STAGE=present"
        )

    if probe.is_sim():
        dest = Path("/tmp/IR_GATEWAY_SIM_CIRCUITPY")
        dest.mkdir(parents=True, exist_ok=True)
        for path in FIRMWARE_SRC.glob("*"):
            if path.is_file():
                shutil.copy2(path, dest / path.name)
        print(f"sim deploy: copied firmware to {dest}")
        warn_if_adafruit_hid_missing(dest)
        return

    mount = probe.circuitpy_mount()
    if mount is None:
        raise SystemExit(
            "CIRCUITPY volume not mounted. "
            "Next: HUMAN_VERIFY=1 HUMAN_FLASH=1 make firmware. "
            "Re-run present when the USB identity to record has changed. "
            f"Expected sources in {FIRMWARE_SRC}"
        )
    for path in FIRMWARE_SRC.glob("*"):
        if path.is_file():
            shutil.copy2(path, mount / path.name)
            print(f"copied {path.name} → {mount / path.name}")
    warn_if_adafruit_hid_missing(mount)
    print("firmware deploy complete; reset Pico if code did not autoreload")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Deploy Pico CircuitPython firmware")
    parser.add_argument("--board", default="pico")
    args = parser.parse_args(argv)
    board = load_board(args.board)
    deploy(board)


if __name__ == "__main__":
    main()
