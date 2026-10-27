# Instantiation checklist mapping

Mapped from the rad-lab methodology checklist onto this repo.

| Item | Instantiation |
| --- | --- |
| 1 Roles | `human/`, `hardware/`, `software/`, `environment/`, `lesson/`, `harness/` + root `AGENTS.md` |
| 2 Evidence | `reports/pico/stage.json`; `require_image` (SIL); `require_ir_map` (capture `validated.json`) |
| 3 Assent vs sim | `HUMAN_VERIFY` (bench), `HUMAN_FLASH`, `HUMAN_IR_PATH`; DUT presence is the `present` stage; sim via `IR_GATEWAY_HWIL_SIM=1` (sim does not forge `HUMAN_VERIFY`) |
| 4 Identity | No hardcoded operator identity; DUT serial optional in board YAML |
| 5 Power / duration | `max_ir_tx_ms`, `max_ir_tx_duty`, HID debounce/repeat ceilings |
| 6 Writeups | Stage records include `reason` / `next`; capture stamps under `reports/pico/<UTC>/` |
| 7 Import lint | `harness/tests/test_import_lint.py` |
| 8 Make / CI | `Makefile`: `check`/`sim`/`check-docker` SIL; `image`/`smoke` environment; `stage`/`hwil`/`firmware`/`load-circuitpython` after assent |
| 9 Two loops | Documented in `domain.md` |
| 10 Deferrals | CineMate TX + web app deferred; no fat orchestrator |
