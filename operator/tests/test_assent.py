"""Confirmation gates refuse without OPERATOR_* flags."""

from __future__ import annotations

import pytest

from operator import assent


def test_require_verify_refuses_until_operator(monkeypatch):
    monkeypatch.delenv(assent.VERIFY_ENV, raising=False)
    monkeypatch.setenv(assent.SIM_ENV, "1")
    with pytest.raises(SystemExit, match="OPERATOR_VERIFY"):
        assent.require_verify()


def test_require_verify_accepts_operator(monkeypatch):
    monkeypatch.setenv(assent.VERIFY_ENV, "1")
    assent.require_verify()


def test_clamp_ir_tx_ms():
    board = {"ir_tx_ms": 50, "max_ir_tx_ms": 200}
    assert assent.clamp_ir_tx_ms(board) == 50.0
    with pytest.raises(SystemExit):
        assent.clamp_ir_tx_ms(board, 500)


def test_stdlib_operator_still_imports():
    from operator import itemgetter

    assert itemgetter(0)(("a",)) == "a"
