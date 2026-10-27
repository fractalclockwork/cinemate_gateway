# Harness

Paths and ready predicates only.

## Allowed

- Load board YAML, read/write `reports/*/stage.json`, expose `require_*` gates.
- Unit tests and import lint.

## Forbidden

- Flashing firmware, prompting for assent, or driving IR TX/RX hardware.
- Importing `human` assent prompts into unlock predicates beyond reading stage files.
