"""Optical loopback: Pico IR LED → IR receiver, phase 1 only.

Energizes the LED only after the operator verifies the bench and
confirms the IR path, and only inside the board TX ceilings. The receiver
must respond to a 38 kHz carrier and stay quiet for an off-carrier burst
at the same duty and duration.
"""

from __future__ import annotations

import argparse
import json
import os
import select
import termios
import time
from pathlib import Path

from hardware.records import load_board, read_stages, run_report_dir, stage_passed
from hardware import probe
from operator import assent

CARRIER_HZ = 38_000
# Far above the receiver bandpass. A 10 kHz square wave still has harmonics
# near 38 kHz, so it is not a useful "off-carrier" control at short range.
CONTROL_HZ = 100_000
FREQ_READBACK_TOL_HZ = 2_000
MIN_SAMPLES = 100
IDLE_LOW_MAX = 0.20
OFF_CARRIER_LOW_MAX = 0.30
CARRIER_LOW_MIN = 0.55
AFTER_LOW_MAX = 0.30
CARRIER_SEPARATION = 0.40
_PWM_FULL_SCALE = 65535


def build_device_script(
    *,
    rx_pin: int,
    tx_pin: int,
    duty: float,
    burst_ms: float,
    max_duty: float,
    max_burst_ms: float,
) -> str:
    """CircuitPython one-shot. Duty is forced to 0 in finally."""
    rx_pin = int(rx_pin)
    tx_pin = int(tx_pin)
    duty = float(duty)
    burst_ms = float(burst_ms)
    max_duty = float(max_duty)
    max_burst_ms = float(max_burst_ms)
    if not 0 <= rx_pin <= 28 or not 0 <= tx_pin <= 28 or rx_pin == tx_pin:
        raise SystemExit(f"refusing IR loopback on pins rx={rx_pin} tx={tx_pin}")
    if duty <= 0 or duty > max_duty:
        raise SystemExit(
            f"ir_tx_duty {duty} exceeds max_ir_tx_duty {max_duty}; refuse IR TX"
        )
    if burst_ms <= 0 or burst_ms > max_burst_ms:
        raise SystemExit(
            f"ir burst {burst_ms} ms exceeds max_ir_tx_ms {max_burst_ms}; refuse IR TX"
        )
    duty_count = int(duty * _PWM_FULL_SCALE)
    if duty_count < 1 or duty_count / _PWM_FULL_SCALE > max_duty:
        raise SystemExit(
            f"PWM duty count {duty_count} outside ceiling; refuse IR TX"
        )
    return f"""import board
import digitalio
import json
import pwmio
import time

RX = board.GP{rx_pin}
TX = board.GP{tx_pin}
CARRIER_HZ = {CARRIER_HZ}
CONTROL_HZ = {CONTROL_HZ}
DUTY_COUNT = {duty_count}
BURST_S = {burst_ms / 1000.0:.5f}
IDLE_S = 0.030
GAP_S = 0.050
N_CARRIER = 3

def sample(pin, seconds):
    n = 0
    low = 0
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        n += 1
        if not pin.value:
            low += 1
    return {{"n": n, "low": low}}

rx = None
tx = None
try:
    rx = digitalio.DigitalInOut(RX)
    rx.direction = digitalio.Direction.INPUT
    rx.pull = digitalio.Pull.UP
    tx = pwmio.PWMOut(TX, frequency=CARRIER_HZ, duty_cycle=0, variable_frequency=True)
    result = {{}}
    result["idle"] = sample(rx, IDLE_S)
    bursts = []
    for _ in range(N_CARRIER):
        tx.frequency = CARRIER_HZ
        tx.duty_cycle = DUTY_COUNT
        try:
            burst = sample(rx, BURST_S)
        finally:
            tx.duty_cycle = 0
        burst["hz_readback"] = tx.frequency
        bursts.append(burst)
        time.sleep(GAP_S)
    result["carrier"] = bursts
    tx.frequency = CONTROL_HZ
    tx.duty_cycle = DUTY_COUNT
    try:
        off = sample(rx, BURST_S)
    finally:
        tx.duty_cycle = 0
    off["hz"] = CONTROL_HZ
    off["hz_readback"] = tx.frequency
    result["off_carrier"] = off
    time.sleep(GAP_S)
    result["after"] = sample(rx, IDLE_S)
    result["carrier_hz"] = CARRIER_HZ
    result["duty_count"] = DUTY_COUNT
    result["burst_ms"] = {burst_ms:.1f}
    result["rx_pin"] = {rx_pin}
    result["tx_pin"] = {tx_pin}
    print("LOOPBACK_JSON " + json.dumps(result))
finally:
    if tx is not None:
        tx.duty_cycle = 0
        tx.deinit()
    hold = digitalio.DigitalInOut(TX)
    hold.direction = digitalio.Direction.OUTPUT
    hold.value = False
    if rx is not None:
        rx.deinit()
"""


def _frac(sample: dict) -> float:
    n = int(sample["n"])
    low = int(sample["low"])
    if n < MIN_SAMPLES:
        raise ValueError(f"sample count {n} < {MIN_SAMPLES}")
    if low < 0 or low > n:
        raise ValueError(f"low count {low} outside 0..{n}")
    return low / n


def judge_loopback(payload: dict) -> dict:
    """Pass only when RX tracks the 38 kHz envelope and ignores 10 kHz."""
    try:
        idle = _frac(payload["idle"])
        off = _frac(payload["off_carrier"])
        after = _frac(payload["after"])
        carriers = [_frac(sample) for sample in payload["carrier"]]
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        return {"ok": False, "reason": f"unreadable samples: {exc}", "fractions": {}}
    fractions = {
        "idle_low": idle,
        "off_carrier_low": off,
        "carrier_low": carriers,
        "after_low": after,
    }
    reasons: list[str] = []
    if payload.get("carrier_hz") != CARRIER_HZ:
        reasons.append(f"carrier_hz {payload.get('carrier_hz')} != {CARRIER_HZ}")
    if payload.get("off_carrier", {}).get("hz") != CONTROL_HZ:
        reasons.append(
            f"off-carrier hz {payload.get('off_carrier', {}).get('hz')} != {CONTROL_HZ}"
        )
    if not carriers:
        reasons.append("no 38 kHz bursts")
    if idle > IDLE_LOW_MAX:
        reasons.append(
            f"RX idle low fraction {idle:.2f} (expected released/high, max {IDLE_LOW_MAX:.2f})"
        )
    if off > OFF_CARRIER_LOW_MAX:
        reasons.append(
            f"{CONTROL_HZ} Hz control low fraction {off:.2f} "
            f"(expected quiet, max {OFF_CARRIER_LOW_MAX:.2f})"
        )
    if any(value < CARRIER_LOW_MIN for value in carriers):
        shown = ", ".join(f"{value:.2f}" for value in carriers)
        reasons.append(
            f"38 kHz low fractions [{shown}] below {CARRIER_LOW_MIN:.2f}"
        )
    if after > AFTER_LOW_MAX:
        reasons.append(
            f"RX stayed low after TX ({after:.2f}, max {AFTER_LOW_MAX:.2f})"
        )
    if carriers and min(carriers) - off < CARRIER_SEPARATION:
        reasons.append(
            "38 kHz response is not distinct from the off-carrier control "
            f"({min(carriers):.2f} vs {off:.2f})"
        )
    return {
        "ok": not reasons,
        "reason": "; ".join(reasons) if reasons else None,
        "fractions": fractions,
    }


class RawRepl:
    """Minimal CircuitPython raw REPL over USB CDC."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.fd = os.open(path, os.O_RDWR | os.O_NOCTTY)

    def close(self) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def _configure(self) -> None:
        attrs = termios.tcgetattr(self.fd)
        attrs[0] = 0
        attrs[1] = 0
        attrs[2] = termios.CS8 | termios.CLOCAL | termios.CREAD
        attrs[3] = 0
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)

    def write(self, data: bytes) -> None:
        os.write(self.fd, data)

    def read_for(self, seconds: float) -> bytes:
        end = time.monotonic() + seconds
        buf = b""
        while time.monotonic() < end:
            ready, _, _ = select.select([self.fd], [], [], 0.05)
            if not ready:
                continue
            chunk = os.read(self.fd, 4096)
            if chunk:
                buf += chunk
                end = max(end, time.monotonic() + 0.05)
        return buf

    def read_until(self, pred, timeout: float) -> bytes:
        end = time.monotonic() + timeout
        buf = b""
        while time.monotonic() < end:
            ready, _, _ = select.select([self.fd], [], [], 0.05)
            if not ready:
                continue
            chunk = os.read(self.fd, 4096)
            if not chunk:
                continue
            buf += chunk
            if pred(buf):
                return buf
        raise TimeoutError(buf)

    def enter(self) -> None:
        self._configure()
        self.read_for(0.2)
        self.write(b"\x03\x03")
        time.sleep(0.1)
        self.write(b"\x02")
        time.sleep(0.1)
        self.write(b"\x03\x01")
        self.read_until(
            lambda buf: b"raw REPL" in buf and buf.rstrip().endswith(b">"),
            3.0,
        )

    def exec(self, source: str, timeout: float = 8.0) -> tuple[str, str]:
        payload = source.replace("\n", "\r\n").encode()
        if not payload.endswith(b"\r\n"):
            payload += b"\r\n"
        for offset in range(0, len(payload), 32):
            self.write(payload[offset : offset + 32])
            time.sleep(0.008)
        self.write(b"\x04")
        buf = self.read_until(lambda data: data.count(b"\x04") >= 2, timeout)
        ok_at = buf.find(b"OK")
        if ok_at < 0:
            raise RuntimeError(f"raw REPL missing OK: {buf!r}")
        parts = buf[ok_at + 2 :].split(b"\x04")
        stdout = parts[0].decode("utf-8", "replace")
        stderr = parts[1].decode("utf-8", "replace") if len(parts) > 1 else ""
        return stdout, stderr

    def restore_firmware(self) -> str:
        """Stop the REPL and soft-reboot so code.py owns the pins again."""
        self.write(b"\x03\x03")
        time.sleep(0.1)
        self.write(b"\x02")
        time.sleep(0.15)
        self.write(b"\x04")
        return self.read_for(2.5).decode("utf-8", "replace")


def find_pico_serial() -> Path:
    by_id = Path("/dev/serial/by-id")
    matches = sorted(by_id.glob("usb-Raspberry_Pi_Pico_*-if00"))
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SystemExit("no Raspberry Pi Pico USB serial device")
    raise SystemExit(f"multiple Pico serial devices: {matches}")


def check_tx_echo(
    payload: dict,
    *,
    duty_count: int,
    burst_ms: float,
    rx_pin: int,
    tx_pin: int,
) -> None:
    """Reject a device report that did not run the requested TX schedule."""
    if payload.get("duty_count") != duty_count:
        raise RuntimeError("device duty_count does not match the clamped duty")
    if float(payload.get("burst_ms", -1)) != float(f"{burst_ms:.1f}"):
        raise RuntimeError("device burst_ms does not match the clamped burst")
    if payload.get("rx_pin") != rx_pin or payload.get("tx_pin") != tx_pin:
        raise RuntimeError("device pins do not match the board YAML")
    off_hz = int(payload["off_carrier"]["hz_readback"])
    if abs(off_hz - CONTROL_HZ) > FREQ_READBACK_TOL_HZ:
        raise RuntimeError(
            f"off-carrier PWM readback {off_hz} Hz is not {CONTROL_HZ} Hz"
        )
    for burst in payload["carrier"]:
        hz = int(burst["hz_readback"])
        if abs(hz - CARRIER_HZ) > FREQ_READBACK_TOL_HZ:
            raise RuntimeError(f"carrier PWM readback {hz} Hz is not {CARRIER_HZ} Hz")


def _payload_from_stdout(stdout: str) -> dict:
    for line in stdout.splitlines():
        if line.startswith("LOOPBACK_JSON "):
            return json.loads(line[len("LOOPBACK_JSON ") :])
    raise RuntimeError(f"no LOOPBACK_JSON in stdout: {stdout!r}")


def run_loopback(board: dict) -> dict:
    board_id = board["id"]
    assent.require_verify("optical loopback")
    for prior in ("present", "workflow"):
        if not stage_passed(board_id, prior):
            raise SystemExit(
                f"{prior} stage has not passed. "
                f"Next: OPERATOR_VERIFY=1 make stage BOARD={board_id} STAGE={prior}"
            )
    assent.require_ir_path("IR LED aimed at the IR receiver; loopback only")
    assent.confirm_ir("optical loopback from IR LED to IR receiver")
    if assent.is_sim():
        raise SystemExit("optical loopback refuses IR_GATEWAY_HWIL_SIM")

    pins = board.get("pins") or {}
    if pins.get("ir_rx") is None or pins.get("ir_tx") is None:
        raise SystemExit("board pins.ir_rx and pins.ir_tx must be set before loopback")
    tx_ms = assent.clamp_ir_tx_ms(board)
    duty = assent.clamp_ir_tx_duty(board)
    burst_ms = min(20.0, tx_ms)
    script = build_device_script(
        rx_pin=int(pins["ir_rx"]),
        tx_pin=int(pins["ir_tx"]),
        duty=duty,
        burst_ms=burst_ms,
        max_duty=float(board.get("max_ir_tx_duty", duty)),
        max_burst_ms=float(board.get("max_ir_tx_ms", tx_ms)),
    )

    report_dir = run_report_dir(board_id)
    evidence: dict = {
        "mode": "optical-loopback",
        "ok": False,
        "pins": {"ir_rx": int(pins["ir_rx"]), "ir_tx": int(pins["ir_tx"])},
        "ir_tx_ms": burst_ms,
        "ir_tx_duty": duty,
        "carrier_hz": CARRIER_HZ,
        "control_hz": CONTROL_HZ,
        "phase": "loopback-only",
    }
    mount = probe.circuitpy_mount()
    if mount is not None:
        boot_out = mount / "boot_out.txt"
        if boot_out.is_file():
            evidence["boot_out"] = boot_out.read_text().strip()
    present = read_stages(board_id)["stages"].get("present") or {}
    usb = (present.get("metrics") or {}).get("usb")
    if usb:
        evidence["usb"] = usb

    session: RawRepl | None = None
    try:
        port = find_pico_serial()
        evidence["serial"] = str(port)
        session = RawRepl(port)
        session.enter()
        stdout, stderr = session.exec(script, timeout=8.0)
        evidence["stdout"] = stdout
        evidence["stderr"] = stderr
        if stderr.strip():
            evidence["reason"] = stderr.strip()
        else:
            payload = _payload_from_stdout(stdout)
            check_tx_echo(
                payload,
                duty_count=int(duty * _PWM_FULL_SCALE),
                burst_ms=burst_ms,
                rx_pin=int(pins["ir_rx"]),
                tx_pin=int(pins["ir_tx"]),
            )
            judged = judge_loopback(payload)
            evidence["samples"] = {
                "idle": payload.get("idle"),
                "carrier": payload.get("carrier"),
                "off_carrier": payload.get("off_carrier"),
                "after": payload.get("after"),
            }
            evidence["fractions"] = judged["fractions"]
            evidence["ok"] = judged["ok"]
            evidence["reason"] = judged["reason"]
    except (OSError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
        evidence["ok"] = False
        evidence["reason"] = str(exc)
    finally:
        if session is not None:
            try:
                evidence["reboot"] = session.restore_firmware()
            except (OSError, TimeoutError) as exc:
                evidence["cleanup_error"] = str(exc)
            session.close()
        path = report_dir / "loopback.json"
        path.write_text(json.dumps(evidence, indent=2) + "\n")
        evidence["report"] = str(path)
    return evidence


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="IR LED to IR receiver optical loopback")
    parser.add_argument("--board", default="pico")
    args = parser.parse_args(argv)
    board = load_board(args.board)
    result = run_loopback(board)
    report = result.get("report", "")
    if not result.get("ok"):
        raise SystemExit(
            f"{board['id']} loopback FAIL: {result.get('reason')}. Evidence: {report}"
        )
    fractions = result.get("fractions") or {}
    carriers = fractions.get("carrier_low") or []
    carrier_text = ", ".join(f"{value:.2f}" for value in carriers)
    print(
        f"{board['id']} loopback: pass "
        f"(38 kHz low {carrier_text}; "
        f"{CONTROL_HZ // 1000} kHz low {fractions.get('off_carrier_low', 0):.2f}). "
        f"Evidence: {report}"
    )


if __name__ == "__main__":
    main()
