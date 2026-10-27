# Hardware (HWIL)

Bring-up ladder for board `pico`:

`present` probes USB once. That pass stands until you run `present` again.

```bash
export HUMAN_VERIFY=1
make stage BOARD=pico STAGE=present
make stage BOARD=pico STAGE=workflow

export HUMAN_IR_PATH=1
make hwil BOARD=pico   # image stage

export HUMAN_FLASH=1
make firmware BOARD=pico   # uses the present pass
```

Board policy: [`boards/pico.yaml`](boards/pico.md). Wiring: [`docs/boards/pico.md`](docs/boards/pico.md). Pipeline: [`docs/pipeline.md`](docs/pipeline.md).
