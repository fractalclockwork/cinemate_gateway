"""Watch firmware sources and auto-deploy on change (no OPERATOR_FLASH)."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from hardware.firmware import DIGEST_FILES, FIRMWARE_SRC, deploy, prepare_firmware_tree
from hardware.records import load_board

REPO_ROOT = Path(__file__).resolve().parents[1]
WATCH_EXTRA = (
    REPO_ROOT / "software" / "keymap.yaml",
    FIRMWARE_SRC / "boot.py",
    FIRMWARE_SRC / "code.py",
    FIRMWARE_SRC / "keymap_gen.py",
)


def _fingerprint() -> tuple:
    """Cheap mtime/size tuple over watched files (+ keymap drives keymap_gen)."""
    rows = []
    for path in WATCH_EXTRA:
        if not path.is_file():
            rows.append((str(path), None, None))
            continue
        st = path.stat()
        rows.append((str(path), st.st_mtime_ns, st.st_size))
    return tuple(rows)


def watch(board_id: str, *, interval_s: float = 1.0) -> None:
    board = load_board(board_id)
    print(
        f"firmware-watch: board={board_id} interval={interval_s}s "
        "(Ctrl-C to stop). OPERATOR_VERIFY=1 required; OPERATOR_FLASH not used."
    )
    last = None
    while True:
        fp = _fingerprint()
        if fp != last:
            reason = "startup" if last is None else "change detected"
            print(f"{reason} — exporting keymap and deploying…")
            try:
                from software.export_firmware_keymap import write_keymap_gen

                write_keymap_gen()
                digest = prepare_firmware_tree()
                print(f"watch deploy digest {digest}")
                deploy(board)
            except SystemExit as exc:
                print(f"deploy failed: {exc}")
            except Exception as exc:  # noqa: BLE001 — keep watch alive
                print(f"deploy error: {exc}")
            last = fp
        time.sleep(interval_s)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Auto-deploy Pico firmware on change")
    parser.add_argument("--board", default="pico")
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args(argv)
    watch(args.board, interval_s=args.interval)


if __name__ == "__main__":
    main()
