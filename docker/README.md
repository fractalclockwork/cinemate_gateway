# pico-dev Docker image

Dev-Host RP2040 toolchain for this repo, adapted from crt-drive `docker/pico-dev` (Debian + Pico SDK + picotool). Edit on the Dev-Host; the repo is bind-mounted at `/workspace`.

Phase-1 application firmware remains **CircuitPython**. This image is for:

- reproducible SIL (`make check-docker`)
- interactive `shell` / `shell-usb`
- `picotool` UF2 load of CircuitPython after the operator confirms the bench

Quick path from the repository root:

```bash
make image              # ir-remote-bose/pico-dev:local
make smoke              # compilers + SDK + picotool USB build check
make check-docker       # pytest inside the container
make pico-discover      # host lsusb (+ picotool if BOOTSEL)
make shell              # unprivileged
make shell-usb          # privileged USB
```

CircuitPython UF2 (operator download → `archive/cache/circuitpython/raspberry_pi_pico.uf2`):

```bash
# Record DUT presence once (BOOTSEL or CircuitPython). Stands until present is run again.
OPERATOR_VERIFY=1 make stage BOARD=pico STAGE=present
# Pico in BOOTSEL
OPERATOR_VERIFY=1 OPERATOR_FLASH=1 make load-circuitpython
# Then after CIRCUITPY mounts:
OPERATOR_VERIFY=1 OPERATOR_FLASH=1 make firmware
```

Sources: [`pico-dev/Dockerfile`](pico-dev/Dockerfile), pins in [`TOOLCHAIN_VERSIONS`](TOOLCHAIN_VERSIONS), Compose in this directory. Make: [`Makefile`](Makefile) and repo-root [`Makefile`](../Makefile).
