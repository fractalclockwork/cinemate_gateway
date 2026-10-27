# GitHub readiness

Product requirements are in [`SPEC.md`](SPEC.md) and the working method in [`methodology/operator-loop.md`](methodology/operator-loop.md). The bring-up writeup is archived at [`history/postmortem-agentic-bringup.md`](history/postmortem-agentic-bringup.md); it is a record, not the process spec.

## Done locally

- MIT license at the repo root.
- Host CI in [`.github/workflows/check.yml`](../.github/workflows/check.yml) runs `make check` and `make sim` only.
- `.gitignore` keeps out `reports/*`, `local.env`, `*.uf2`, and KiCad `.history/`.
- No `local.env`, `.env`, `*.pem`, or credential files are in the tree.
- No owner's-guide PDF is in the tree.
- The lesson curriculum and the harness role are removed. Button codes remain a capture session, and the confirmation flags are `OPERATOR_*`.

## Still the operator's decision

- The first commit, the remote, and the push. Nothing is published from a docs task unless asked.
- Public versus private. Third-party manuals are not added without a copyright decision.
- Whether `reports/.gitkeep` stays empty, as it is now, or a redacted sample is added later.

## Do not commit

- `local.env` (operator flag exports)
- UF2 blobs and `archive/cache/**/*.uf2`
- Live `reports/pico/**` stamps
