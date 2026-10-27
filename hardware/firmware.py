"""Flash / deploy CircuitPython app after operator verification and a present pass."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from hardware.records import load_board, stage_passed
from hardware import probe
from operator import assent

FIRMWARE_SRC = Path(__file__).resolve().parent / "firmware" / "pico"
ADAFRUIT_HID_REL = Path("lib") / "adafruit_hid"


def adafruit_hid_present(root: Path) -> bool:
    hid_dir = root / ADAFRUIT_HID_REL
    marker = hid_dir / "__init__.py"
    return hid_dir.is_dir() and (marker.is_file() or any(hid_dir.glob("*.mpy")))


def require_adafruit_hid(root: Path) -> None:
    """Fail deploy when CIRCUITPY (or sim dest) lacks adafruit_hid after copy."""
    if adafruit_hid_present(root):
        return
    raise SystemExit(
        "adafruit_hid missing under "
        f"{root / ADAFRUIT_HID_REL}. "
        "Vendor copy belongs at hardware/firmware/pico/lib/adafruit_hid/ "
        "(see that folder's VENDOR.md). Deploy refuses a non-bootable tree."
    )


def _copy_firmware_tree(dest: Path) -> None:
    """Recursively copy firmware sources including lib/adafruit_hid."""
    dest.mkdir(parents=True, exist_ok=True)
    for path in FIRMWARE_SRC.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(FIRMWARE_SRC)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        print(f"copied {rel.as_posix()} → {target}")


def deploy(board: dict) -> None:
    board_id = board["id"]
    assent.require_verify(f"firmware write for {board_id}")
    assent.require_flash(board_id)
    if not stage_passed(board_id, "present"):
        raise SystemExit(
            f"{board_id} present stage has not passed. "
            f"Next: OPERATOR_VERIFY=1 make stage BOARD={board_id} STAGE=present"
        )

    if not adafruit_hid_present(FIRMWARE_SRC):
        raise SystemExit(
            f"firmware source missing {FIRMWARE_SRC / ADAFRUIT_HID_REL}. "
            "Restore the vendored Adafruit HID package before deploy."
        )

    if probe.is_sim():
        dest = Path("/tmp/IR_GATEWAY_SIM_CIRCUITPY")
        if dest.exists():
            shutil.rmtree(dest)
        _copy_firmware_tree(dest)
        require_adafruit_hid(dest)
        print(f"sim deploy: copied firmware to {dest}")
        return

    mount = probe.circuitpy_mount()
    if mount is None:
        raise SystemExit(
            "CIRCUITPY volume not mounted. "
            "Next: OPERATOR_VERIFY=1 OPERATOR_FLASH=1 make firmware. "
            "Re-run present when the USB identity to record has changed. "
            f"Expected sources in {FIRMWARE_SRC}"
        )
    _copy_firmware_tree(mount)
    require_adafruit_hid(mount)
    print("firmware deploy complete; reset Pico if code did not autoreload")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Deploy Pico CircuitPython firmware")
    parser.add_argument("--board", default="pico")
    args = parser.parse_args(argv)
    board = load_board(args.board)
    deploy(board)


if __name__ == "__main__":
    main()
