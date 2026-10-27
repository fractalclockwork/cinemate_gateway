"""DUT presence is the present stage. Later commands use that record."""

from __future__ import annotations

import pytest

from hardware import probe, records
from hardware.firmware import deploy
from hardware.records import read_stages, write_stage
from hardware.stages import stage_workflow
from operator import assent


def _isolate_reports(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(records, "reports_root", lambda: tmp_path / "reports")
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


def test_require_adafruit_hid_fails_then_passes(tmp_path):
    from hardware.firmware import adafruit_hid_present, require_adafruit_hid

    assert adafruit_hid_present(tmp_path) is False
    with pytest.raises(SystemExit, match="adafruit_hid missing"):
        require_adafruit_hid(tmp_path)
    hid = tmp_path / "lib" / "adafruit_hid"
    hid.mkdir(parents=True)
    (hid / "__init__.py").write_text("")
    require_adafruit_hid(tmp_path)
    assert adafruit_hid_present(tmp_path) is True


def test_firmware_source_vendors_adafruit_hid():
    from hardware.firmware import FIRMWARE_SRC, adafruit_hid_present

    assert adafruit_hid_present(FIRMWARE_SRC)
