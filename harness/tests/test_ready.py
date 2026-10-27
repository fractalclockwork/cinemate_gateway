"""Ready-gate behavior with synthetic stage records."""

from __future__ import annotations

import json

import pytest

from harness import boards, ready


def test_require_image_refuses_without_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(boards, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(boards, "reports_root", lambda: tmp_path / "reports")
    with pytest.raises(SystemExit) as exc:
        ready.require_image("pico")
    assert "present" in str(exc.value)


def test_require_image_passes_when_image_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(boards, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(boards, "reports_root", lambda: tmp_path / "reports")
    stage_file = tmp_path / "reports" / "pico" / "stage.json"
    stage_file.parent.mkdir(parents=True)
    stage_file.write_text(
        json.dumps(
            {
                "board": "pico",
                "stages": {
                    "present": {"status": "pass"},
                    "workflow": {"status": "pass"},
                    "image": {"status": "pass"},
                },
            }
        )
    )
    ready.require_image("pico")


def test_require_ir_map_refuses_without_validated(tmp_path, monkeypatch):
    monkeypatch.setattr(boards, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(boards, "reports_root", lambda: tmp_path / "reports")
    (tmp_path / "reports" / "pico").mkdir(parents=True)
    with pytest.raises(SystemExit) as exc:
        ready.require_ir_map("pico")
    assert "IR map evidence missing" in str(exc.value)


def test_require_ir_map_passes_with_validated_button(tmp_path, monkeypatch):
    monkeypatch.setattr(boards, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(boards, "reports_root", lambda: tmp_path / "reports")
    captures = tmp_path / "reports" / "pico" / "20261027T000000Z" / "captures"
    captures.mkdir(parents=True)
    (captures / "validated.json").write_text(
        json.dumps(
            {
                "buttons": [
                    {
                        "button": "up",
                        "frame_key": "sony-sirc20:1a:5f:9a",
                        "validated": True,
                    }
                ]
            }
        )
    )
    path = ready.require_ir_map("pico")
    assert path.name == "validated.json"
