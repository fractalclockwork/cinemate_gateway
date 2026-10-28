"""Deploy helpers and firmware digest gates — no USB required."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from hardware import firmware as fw
from hardware.loopback import parse_digest_from_banner


def _seed_tree(root: Path, *, code: str = "print(1)\n") -> None:
    (root / "boot.py").write_text("CAPTURE_BUILD = False\n")
    (root / "code.py").write_text(code)
    (root / "keymap_gen.py").write_text("KEYMAP = {}\n")


def test_flush_circuitpy_syncs(tmp_path: Path):
    _seed_tree(tmp_path)
    (tmp_path / "deploy_stamp.py").write_text('DIGEST = "abc"\n')
    with patch("hardware.firmware.os.sync") as sync:
        with patch("hardware.firmware.os.fsync") as fsync:
            fw._flush_circuitpy(tmp_path)
    assert sync.called
    assert fsync.called


def test_firmware_tree_digest_stable_and_changes_with_code(tmp_path: Path):
    _seed_tree(tmp_path, code="v1\n")
    first = fw.firmware_tree_digest(tmp_path)
    second = fw.firmware_tree_digest(tmp_path)
    assert first == second
    assert len(first) == 12
    _seed_tree(tmp_path, code="v2\n")
    assert fw.firmware_tree_digest(tmp_path) != first


def test_render_and_read_deploy_stamp(tmp_path: Path):
    path = fw.write_deploy_stamp(tmp_path, "deadbeefcafe")
    assert path.name == "deploy_stamp.py"
    assert fw.read_stamp_digest(tmp_path) == "deadbeefcafe"
    assert 'DIGEST = "deadbeefcafe"' in path.read_text()


def test_parse_digest_from_banner_single_token():
    banner = (
        "ir-remote-bose firmware ready mode=map rx=board.GP14 digest=abc123def456\n"
    )
    assert parse_digest_from_banner(banner) == "abc123def456"


def test_verify_running_digest_passes(tmp_path: Path):
    _seed_tree(tmp_path)
    digest = fw.firmware_tree_digest(tmp_path)
    fw.write_deploy_stamp(tmp_path, digest)
    banner = f"firmware ready mode=map digest={digest}\n"
    fw.verify_running_digest(expected=digest, banner=banner, mount=tmp_path)


def test_verify_running_digest_fails_on_serial_mismatch(tmp_path: Path):
    _seed_tree(tmp_path)
    digest = fw.firmware_tree_digest(tmp_path)
    fw.write_deploy_stamp(tmp_path, digest)
    with pytest.raises(SystemExit, match="digest mismatch on serial"):
        fw.verify_running_digest(
            expected=digest,
            banner="firmware ready mode=map digest=000000000000\n",
            mount=tmp_path,
        )


def test_verify_running_digest_fails_on_stale_mount_tree(tmp_path: Path):
    _seed_tree(tmp_path, code="deployed\n")
    digest = fw.firmware_tree_digest(tmp_path)
    fw.write_deploy_stamp(tmp_path, digest)
    # Host thinks digest is X, but mount tree was overwritten with other code.
    (tmp_path / "code.py").write_text("stale\n")
    banner = f"firmware ready digest={digest}\n"
    with pytest.raises(SystemExit, match="CIRCUITPY tree digest"):
        fw.verify_running_digest(expected=digest, banner=banner, mount=tmp_path)


def test_circuitpy_block_device_parses_findmnt(tmp_path: Path):
    with patch(
        "hardware.firmware.subprocess.check_output",
        return_value="/dev/sdd1\n",
    ):
        assert fw.circuitpy_block_device(tmp_path) == Path("/dev/sdd1")


def test_unmount_circuitpy_prefers_udisksctl(tmp_path: Path):
    with patch(
        "hardware.firmware.circuitpy_block_device",
        return_value=Path("/dev/sdd1"),
    ):
        with patch("hardware.firmware.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stderr = ""
            run.return_value.stdout = "Unmounted /dev/sdd1."
            fw.unmount_circuitpy(tmp_path)
    assert run.call_args.args[0][:2] == ["udisksctl", "unmount"]


def test_reload_after_deploy_verifies_digest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    _seed_tree(tmp_path)
    digest = fw.firmware_tree_digest(tmp_path)
    fw.write_deploy_stamp(tmp_path, digest)
    banner = f"ir-remote-bose firmware ready mode=map digest={digest}\n"
    with patch("hardware.firmware._flush_circuitpy"):
        with patch("hardware.firmware.unmount_circuitpy"):
            with patch(
                "hardware.firmware.soft_reset_pico",
                return_value=(
                    Path("/dev/serial/by-id/usb-Raspberry_Pi_Pico_x-if00"),
                    banner,
                ),
            ):
                with patch(
                    "hardware.firmware.wait_circuitpy_mount",
                    return_value=tmp_path,
                ):
                    fw.reload_after_deploy(tmp_path, expected_digest=digest)
    out = capsys.readouterr().out
    assert f"firmware digest ok ({digest})" in out


def test_reload_after_deploy_raises_on_digest_mismatch(tmp_path: Path):
    _seed_tree(tmp_path)
    digest = fw.firmware_tree_digest(tmp_path)
    fw.write_deploy_stamp(tmp_path, digest)
    with patch("hardware.firmware._flush_circuitpy"):
        with patch("hardware.firmware.unmount_circuitpy"):
            with patch(
                "hardware.firmware.soft_reset_pico",
                return_value=(
                    Path("/dev/serial/by-id/x-if00"),
                    "firmware ready digest=deadbeefcafe\n",
                ),
            ):
                with patch(
                    "hardware.firmware.wait_circuitpy_mount",
                    return_value=tmp_path,
                ):
                    with pytest.raises(SystemExit, match="digest mismatch"):
                        fw.reload_after_deploy(tmp_path, expected_digest=digest)


def test_clean_circuitpy_junk_removes_trash(tmp_path: Path):
    trash = tmp_path / ".Trash-1000"
    trash.mkdir()
    (trash / "x").write_text("x")
    (tmp_path / ".fseventsd").mkdir()
    fw.clean_circuitpy_junk(tmp_path)
    assert not trash.exists()
    assert not (tmp_path / ".fseventsd").exists()


def test_sim_deploy_skips_reload_without_operator_flash(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setenv("IR_GATEWAY_HWIL_SIM", "1")
    monkeypatch.setenv("OPERATOR_VERIFY", "1")
    monkeypatch.delenv("OPERATOR_FLASH", raising=False)
    monkeypatch.setattr(fw, "stage_passed", lambda *_a, **_k: True)
    monkeypatch.setattr(fw, "FIRMWARE_SRC", tmp_path / "src")
    src = tmp_path / "src"
    (src / "lib" / "adafruit_hid").mkdir(parents=True)
    (src / "lib" / "adafruit_hid" / "__init__.py").write_text("")
    _seed_tree(src)

    def _boom(*_a, **_k):
        raise AssertionError("reload must not run in sim")

    monkeypatch.setattr(fw, "reload_after_deploy", _boom)
    with patch("hardware.firmware.probe.is_sim", return_value=True):
        fw.deploy({"id": "pico"})
    assert fw.read_stamp_digest(src) not in (None, "unset")
