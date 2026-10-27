# cinemate-gateway

A Raspberry Pi Pico receives the Bose CineMate universal remote in AUX mode and types ordinary USB HID keystrokes and mouse motion into Chrome on Linux.

Phase 1 does not transmit IR toward the CineMate Interface. The only IR LED on the bench is for a short optical loopback.

License: [MIT](LICENSE).

## Host check

These run with no Pico attached and no operator flags set:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make check
make sim
```

`make check` runs the decode, keymap, and HID report tests. `make sim` prints one synthetic HID fixture.

## On the bench

The operator sets the flags; agents must not.

```bash
export OPERATOR_VERIFY=1
make stage BOARD=pico STAGE=present
make stage BOARD=pico STAGE=workflow

export OPERATOR_VERIFY=1 OPERATOR_FLASH=1
make firmware
```

Button codes are learned by listening to the remote and then mapping what was heard. That is a capture session, not a lesson:

```bash
OPERATOR_VERIFY=1 make capture FRESH=1
```

Bring-up detail is in [`hardware/docs/bringup.md`](hardware/docs/bringup.md), pins and CircuitPython in [`hardware/docs/boards/pico.md`](hardware/docs/boards/pico.md), and the dev-host image in [`environment/README.md`](environment/README.md).

## Amazon keymap

The active map is [`software/keymap.yaml`](software/keymap.yaml) (profile amazon, AUX Sony DVR `20636`). Regenerate the on-device fragment with `make firmware-keymap`. Player shortcuts and focus notes are in [`docs/remote/amazon-chrome-shortcuts.md`](docs/remote/amazon-chrome-shortcuts.md).

## Docs

| Doc | What it is |
| --- | --- |
| [`docs/SPEC.md`](docs/SPEC.md) | Product requirements |
| [`STATUS.md`](STATUS.md) | What is decided and what is still open |
| [`docs/methodology/operator-loop.md`](docs/methodology/operator-loop.md) | What the host may prove, and what the operator confirms |
| [`docs/design-process.md`](docs/design-process.md) | How this repo was designed, including the board and bring-up |
| [`docs/kicad/ir-gateway/`](docs/kicad/ir-gateway/) | Wire-wrap protoboard |

## Later

A small web app may eventually drive IR transmit for CineMate power and volume alongside the same browser keys. That work needs a new operator flag before any IR is aimed at the Interface. See [`docs/SPEC.md`](docs/SPEC.md).
