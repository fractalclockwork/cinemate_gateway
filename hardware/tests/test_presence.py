"""DUT presence is the present stage. Later commands use that record."""

from __future__ import annotations

import pytest

from harness import boards
from harness.boards import read_stages, write_stage
from hardware import probe
from hardware.firmware import deploy
from hardware.stages import stage_workflow
from human import assent


def _isolate_reports(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(boards, "reports_root", lambda: tmp_path / "reports")
    monkeypatch.setenv(assent.VERIFY_ENV, "1")


def test_workflow_refuses_without_present(tmp_path, monkeypatch):
    _isolate_reports(tmp_path, monkeypatch)

    def boom(_board):
        raise AssertionError("find_pico")

    monkeypatch.setattr(probe, "find_pico", boom)
    with pytest.raises(SystemExit, match="present stage has not passed"):
        stage_workflow({"id": "pico", "pins": {}})


def test_workflow_uses_stored_presence(tmp_path, monkeypatch):
    _isolate_reports(tmp_path, monkeypatch)
    usb = {"vendor": "239a", "product": "80f4", "name": "Adafruit Pico"}
    write_stage("pico", "present", {"status": "pass", "metrics": {"usb": usb}})

    def boom(_board):
        raise AssertionError("find_pico")

    monkeypatch.setattr(probe, "find_pico", boom)
    monkeypatch.setattr(probe, "circuitpy_mount", lambda: None)
    stage_workflow({"id": "pico", "pins": {"ir_rx": 14}})
    record = read_stages("pico")["stages"]["workflow"]
    assert record["status"] == "pass"
    assert record["metrics"]["usb"] == usb
    assert record["metrics"]["circuitpy_mount"] is None


def test_deploy_refuses_without_present(tmp_path, monkeypatch):
    _isolate_reports(tmp_path, monkeypatch)
    monkeypatch.setenv(assent.FLASH_ENV, "1")

    def boom():
        raise AssertionError("circuitpy_mount")

    monkeypatch.setattr(probe, "circuitpy_mount", boom)
    with pytest.raises(SystemExit, match="present stage has not passed"):
        deploy({"id": "pico"})


def test_warn_if_adafruit_hid_missing(tmp_path, capsys):
    from hardware.firmware import warn_if_adafruit_hid_missing

    warn_if_adafruit_hid_missing(tmp_path)
    assert "adafruit_hid not found" in capsys.readouterr().out
    hid = tmp_path / "lib" / "adafruit_hid"
    hid.mkdir(parents=True)
    (hid / "__init__.py").write_text("")
    warn_if_adafruit_hid_missing(tmp_path)
    assert capsys.readouterr().out == ""
