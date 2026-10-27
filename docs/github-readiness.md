# GitHub readiness notes

Post-mortem checklist: [`postmortem-agentic-bringup.md`](postmortem-agentic-bringup.md) §7.

## Done locally (2026-10-27)

| Item | Notes |
| --- | --- |
| LICENSE | MIT at repo root |
| SIL CI | [`.github/workflows/check.yml`](../.github/workflows/check.yml) — `make check` + `make sim` only |
| `.gitignore` | `reports/*`, `local.env`, `*.uf2`, KiCad `.history/` |
| Secret scan | No `local.env`, `.env`, `*.pem`, or `*credential*` / `*secret*` files outside `.venv` |
| Nested KiCad history | Ignored via `.gitignore` |

## Still operator decisions

- `git init` / first commit / remote / push — **human** initiates publish; this review does not push.
- Public vs private: owner’s guide / device-code PDFs are third-party manuals — confirm copyright policy before a public repo.
- Whether to ship empty `reports/.gitkeep` only (current) or curated redacted samples.

## Do not commit

- `local.env` (assent exports)
- UF2 blobs / `archive/cache/**/*.uf2`
- Live `reports/pico/**` stamps (local evidence)
