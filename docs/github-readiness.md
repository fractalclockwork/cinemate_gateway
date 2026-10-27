# GitHub readiness

Product requirements: [`SPEC.md`](SPEC.md). Working method: [`methodology/operator-loop.md`](methodology/operator-loop.md). The bring-up writeup is archived at [`history/postmortem-agentic-bringup.md`](history/postmortem-agentic-bringup.md) and is not the process spec.

## Done locally

- MIT license at the repo root.
- Host CI: [`.github/workflows/check.yml`](../.github/workflows/check.yml) runs `make check` and `make sim` only.
- `.gitignore` keeps out `reports/*`, `local.env`, `*.uf2`, and KiCad `.history/`.
- No `local.env`, `.env`, `*.pem`, or credential files are part of the tree.
- No owner's-guide PDF is in the tree.
- Lesson curriculum and the harness role are removed. Button codes stay a capture session. Confirmation flags are `OPERATOR_*`.

## Still the operator's decision

- First commit, remote, and push. Do not publish from a docs task unless asked.
- Public versus private. Do not add third-party manuals without a copyright decision.
- Whether `reports/.gitkeep` stays empty (current) or a redacted sample is added later.

## Do not commit

- `local.env` (operator flag exports)
- UF2 blobs and `archive/cache/**/*.uf2`
- Live `reports/pico/**` stamps
