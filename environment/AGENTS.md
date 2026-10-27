# Environment

Host toolchain and Docker image ownership.

## Allowed

- Build/document `docker/pico-dev` (`make image`, `make smoke`, `make check-docker`).
- Document CircuitPython UF2 cache paths and picotool load steps.
- Help venv / compose setup.

## Forbidden

- Setting `OPERATOR_*` assent.
- Running `load-circuitpython` or `make firmware` without operator confirmation (those targets refuse unless the operator exported the flags).
- Flashing toward the CineMate (phase 1 has no amp TX).
