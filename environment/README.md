# Environment

Dev-Host toolchain for the IR gateway. Owns the **pico-dev** Docker image (adapted from crt-drive); does not set `HUMAN_*` assent.

## Host venv (fast SIL)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make check
make sim
```

## Docker pico-dev (reproducible)

```bash
make image          # build ir-remote-bose/pico-dev:local
make smoke          # SDK + picotool sanity
make check-docker   # pytest inside bind-mounted container
make shell          # interactive, no USB privilege
make shell-usb      # privileged USB (picotool / ACM)
make pico-discover  # host lsusb + optional picotool if BOOTSEL
```

Details: [`../docker/README.md`](../docker/README.md).

## CircuitPython UF2 (operator) — crt-drive HIL flash pattern

Follow the same Dev-Host rules as crt-drive [`.cursor/skills/pico-dev-hil`](/home/plastic/src/crt-drive/.cursor/skills/pico-dev-hil/SKILL.md): flash only through Make → pico-dev USB compose → [`flash.sh`](flash.sh). **Never** `picotool load -f` (serial mismatch after BOOTSEL). `flash.sh` does `picotool reboot -u -f`, waits for BOOTSEL, then `picotool load -x`.

1. `make pico-discover` — expect `2e8a:0003` (BOOTSEL), `2e8a:000a` (SDK CDC), CircuitPython VID, or `cafe:4001` (serprog). No matching Pico = HIL skip, not a pass.
2. Place CircuitPython UF2 at `archive/cache/circuitpython/raspberry_pi_pico.uf2` (already cached if downloaded).
3. If discover shows **SDK CDC** (`2e8a:000a`), `make load-circuitpython` can reboot into BOOTSEL without holding the button.
4. If discover shows **pico-serprog** (`cafe:4001`) or nothing RP-visible, picotool cannot reboot it — hold **BOOTSEL**, replug until `2e8a:0003`, then load.
5. Record DUT presence once (BOOTSEL or CircuitPython). That pass stands until you run `present` again:

   ```bash
   HUMAN_VERIFY=1 make stage BOARD=pico STAGE=present
   ```

6. Load uses the present pass. Re-run `present` when the USB identity to record has changed:

   ```bash
   HUMAN_VERIFY=1 HUMAN_FLASH=1 make load-circuitpython
   ```

7. After reboot, mount `CIRCUITPY` and install **`adafruit_hid`** (required for HID map mode):

   - Download the [Adafruit CircuitPython Library Bundle](https://circuitpython.org/libraries) matching your CircuitPython major version.
   - Copy the `adafruit_hid` folder into `CIRCUITPY/lib/adafruit_hid/`.
   - `make firmware` warns if `lib/adafruit_hid` is missing after copy.

8. Deploy app + regenerated keymap:

   ```bash
   HUMAN_VERIFY=1 HUMAN_FLASH=1 make firmware
   ```

Alternate host path: drag the UF2 onto the RPI-RP2 volume, then still use `HUMAN_VERIFY=1 HUMAN_FLASH=1 make firmware` for `code.py` / `keymap_gen.py` after `present` has passed.

Agents must never set `HUMAN_VERIFY` / `HUMAN_FLASH`. Do not leave an interactive shell open in the container for flashing.
