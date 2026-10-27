# GitHub readiness notes

Post-mortem checklist: [`postmortem-agentic-bringup.md`](postmortem-agentic-bringup.md) §7. Product requirements: [`SPEC.md`](SPEC.md) (replaces retired root `PROMPT.md`).

## Done locally

| Item | Notes |
| --- | --- |
| LICENSE | MIT at repo root |
| SIL CI | [`.github/workflows/check.yml`](../.github/workflows/check.yml) — `make check` + `make sim` only |
| `.gitignore` | `reports/*`, `local.env`, `*.uf2`, KiCad `.history/` |
| Secret scan | No `local.env`, `.env`, `*.pem`, or `*credential*` / `*secret*` files outside `.venv` (as of docs polish) |
| Nested KiCad history | Ignored via `.gitignore` |
| Spec | [`SPEC.md`](SPEC.md); early `PROMPT.md` removed |

## Still operator decisions

- First commit / remote / push — **human** initiates publish; do not push from review/docs tasks unless asked.
- Public vs private: owner’s guide / device-code PDFs are third-party manuals — confirm copyright policy before a public repo.
- Whether to ship empty `reports/.gitkeep` only (current) or curated redacted samples.

## Do not commit

- `local.env` (assent exports)
- UF2 blobs / `archive/cache/**/*.uf2`
- Live `reports/pico/**` stamps (local evidence)
