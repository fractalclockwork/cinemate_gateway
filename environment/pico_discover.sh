#!/usr/bin/env bash
# Host-side USB discover for Raspberry Pi Pico / CircuitPython (crt-drive discover pattern).
set -euo pipefail

echo "=== lsusb 2e8a (Raspberry Pi) / 239a (Adafruit CP) / cafe (serprog) ==="
if ! command -v lsusb >/dev/null 2>&1; then
  echo "lsusb not found; install usbutils on the Dev-Host" >&2
  exit 1
fi

lsusb -d 2e8a: 2>/dev/null || echo "(no 2e8a)"
lsusb -d 239a: 2>/dev/null || echo "(no 239a)"
lsusb -d cafe: 2>/dev/null || echo "(no cafe)"

echo "=== /dev/serial/by-id ==="
shopt -s nullglob
ids=(/dev/serial/by-id/usb-Raspberry_Pi* /dev/serial/by-id/usb-Adafruit*)
if ((${#ids[@]})); then
  ls -l "${ids[@]}"
else
  echo "(none — BOOTSEL has no ACM; CircuitPython CDC may show after UF2 load)"
fi

echo "=== ttyACM ==="
acms=(/dev/ttyACM*)
if ((${#acms[@]})); then
  ls -l "${acms[@]}"
else
  echo "(none)"
fi

echo "=== mode ==="
if lsusb -d 2e8a:0003 >/dev/null 2>&1; then
  echo "BOOTSEL (2e8a:0003) — after present has passed: OPERATOR_VERIFY=1 OPERATOR_FLASH=1 make load-circuitpython"
elif lsusb -d 2e8a:000a >/dev/null 2>&1; then
  echo "Pico SDK app CDC (2e8a:000a) — flash.sh will try picotool reboot -u -f then load -x"
elif lsusb -d 2e8a:0005 >/dev/null 2>&1 || lsusb -d 239a: >/dev/null 2>&1; then
  echo "CircuitPython — after present has passed: OPERATOR_VERIFY=1 OPERATOR_FLASH=1 make firmware"
elif lsusb -d cafe:4001 >/dev/null 2>&1; then
  echo "pico-serprog (cafe:4001) — picotool may not see this VID; hold BOOTSEL + replug for 2e8a:0003"
else
  echo "No Pico on USB (HIL skip)."
fi
