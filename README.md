# cinemate-gateway

A Raspberry Pi Pico receives the Bose CineMate universal remote in AUX mode and types ordinary USB HID into Chrome on Linux.

Phase 1 does not transmit IR to the CineMate Interface. An IR LED is only for a short optical loopback on the bench.

License: [MIT](LICENSE).

## Host check

No Pico and no operator flags:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make check
make sim
```

`make check` is decode, keymap, and HID report tests. `make sim` prints one synthetic HID fixture.

## On the bench

The operator sets the flags. Agents must not.

```bash
export OPERATOR_VERIFY=1
make stage BOARD=pico STAGE=present
make stage BOARD=pico STAGE=workflow

export OPERATOR_VERIFY=1 OPERATOR_FLASH=1
make firmware
```

Button codes are learned with a listen, then mapped. That is a capture, not a lesson:

```bash
OPERATOR_VERIFY=1 make capture FRESH=1
```

Bring-up detail: [`hardware/docs/bringup.md`](hardware/docs/bringup.md). Pins and CircuitPython: [`hardware/docs/boards/pico.md`](hardware/docs/boards/pico.md). Dev-host image: [`environment/README.md`](environment/README.md).

## Amazon keymap

Active map: [`software/keymap.yaml`](software/keymap.yaml) (profile amazon, AUX Sony DVR `20636`). Regenerate the on-device fragment with `make firmware-keymap`.

Player shortcuts and focus notes: [`docs/remote/amazon-chrome-shortcuts.md`](docs/remote/amazon-chrome-shortcuts.md).

## Docs

| Doc | What it is |
| --- | --- |
| [`docs/SPEC.md`](docs/SPEC.md) | Product requirements |
| [`STATUS.md`](STATUS.md) | What is decided and still open |
| [`docs/methodology/operator-loop.md`](docs/methodology/operator-loop.md) | What the host may prove, and what the operator confirms |
| [`docs/kicad/ir-gateway/`](docs/kicad/ir-gateway/) | Wire-wrap protoboard |

## Later

A small web app may drive IR transmit for CineMate power and volume, plus the same browser keys. That needs a new operator flag before any IR is aimed at the Interface. See [`docs/SPEC.md`](docs/SPEC.md).
