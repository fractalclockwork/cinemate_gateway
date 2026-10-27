# Hardware (HWIL)

Bring-up ladder for board `pico`:

`present` probes USB once. That pass stands until you run `present` again.

```bash
export OPERATOR_VERIFY=1
make stage BOARD=pico STAGE=present
make stage BOARD=pico STAGE=workflow

export OPERATOR_FLASH=1
make firmware BOARD=pico   # uses the present pass
```

Optical loopback, when the LED is aimed only at the receiver:

```bash
export OPERATOR_IR_PATH=1
make loopback BOARD=pico
```

Board policy: [`boards/pico.yaml`](boards/pico.yaml). Wiring: [`docs/boards/pico.md`](docs/boards/pico.md). Pipeline: [`docs/pipeline.md`](docs/pipeline.md).
