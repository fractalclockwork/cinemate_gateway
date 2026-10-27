"""Judge and script gates for the optical loopback. No USB, no IR TX."""

from __future__ import annotations

import pytest

from hardware.loopback import build_device_script, check_tx_echo, judge_loopback


def _sample(n: int, low: int, **extra: object) -> dict:
    sample = {"n": n, "low": low}
    sample.update(extra)
    return sample


def _payload(**overrides: object) -> dict:
    payload = {
        "idle": _sample(1000, 10),
        "off_carrier": _sample(1000, 20, hz=100_000, hz_readback=100_000),
        "carrier": [
            _sample(1000, 950, hz_readback=38_000),
            _sample(1000, 940, hz_readback=38_000),
            _sample(1000, 960, hz_readback=38_000),
        ],
        "after": _sample(1000, 15),
        "carrier_hz": 38_000,
    }
    payload.update(overrides)
    return payload


def test_judge_passes_demodulated_loopback():
    result = judge_loopback(_payload())
    assert result["ok"] is True
    assert result["reason"] is None
    assert result["fractions"]["carrier_low"][0] == pytest.approx(0.95)


def test_judge_fails_when_receiver_ignores_carrier():
    result = judge_loopback(
        _payload(carrier=[_sample(1000, 20), _sample(1000, 25), _sample(1000, 15)])
    )
    assert result["ok"] is False
    assert "38 kHz" in result["reason"]


def test_judge_fails_when_off_carrier_also_asserts():
    result = judge_loopback(_payload(off_carrier=_sample(1000, 900, hz=100_000)))
    assert result["ok"] is False
    assert "100000" in result["reason"] or "off-carrier" in result["reason"]


def test_tx_echo_requires_frequency_readback():
    payload = _payload()
    payload.update(
        {
            "duty_count": 21626,
            "burst_ms": 20.0,
            "rx_pin": 14,
            "tx_pin": 15,
        }
    )
    check_tx_echo(payload, duty_count=21626, burst_ms=20, rx_pin=14, tx_pin=15)
    payload["off_carrier"]["hz_readback"] = 38_000
    with pytest.raises(RuntimeError):
        check_tx_echo(payload, duty_count=21626, burst_ms=20, rx_pin=14, tx_pin=15)


def test_judge_fails_when_idle_is_stuck_low():
    result = judge_loopback(_payload(idle=_sample(1000, 980)))
    assert result["ok"] is False
    assert "idle" in result["reason"]


def test_judge_fails_on_short_samples():
    result = judge_loopback(_payload(idle=_sample(3, 0)))
    assert result["ok"] is False
    assert "unreadable" in result["reason"]


def test_device_script_turns_carrier_off_and_stays_inside_ceilings():
    src = build_device_script(
        rx_pin=14,
        tx_pin=15,
        duty=0.33,
        burst_ms=20,
        max_duty=0.5,
        max_burst_ms=200,
    )
    assert "board.GP14" in src
    assert "board.GP15" in src
    assert "DUTY_COUNT = 21626" in src
    assert "variable_frequency=True" in src
    assert "finally:" in src
    assert src.rindex("duty_cycle = 0") > src.index("finally:")
    assert "hold.value = False" in src


def test_device_script_refuses_over_ceiling():
    with pytest.raises(SystemExit):
        build_device_script(
            rx_pin=14,
            tx_pin=15,
            duty=0.9,
            burst_ms=20,
            max_duty=0.5,
            max_burst_ms=200,
        )
    with pytest.raises(SystemExit):
        build_device_script(
            rx_pin=14,
            tx_pin=15,
            duty=0.33,
            burst_ms=500,
            max_duty=0.5,
            max_burst_ms=200,
        )
