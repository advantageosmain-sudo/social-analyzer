# Task & decision record — skills/agents catalog bootstrap

*Pages-equivalent. Pages is not reachable from this environment; this file plus `decision` records in the ledger are the record of truth. Owner: advantageosmain-sudo. Branch: `arena/01a10754-social-analyzer`.*

## Task (2026-10-04)
Build the highest-value missing skills and agents for the existing business(es), prioritising Product Readiness, Digital Product Production and Business Records; reuse before duplicating; preserve architecture, GitHub source of truth and owner approval gates; report implemented / tested / blocked.

## Findings from the catalog inspection
| # | Finding | Evidence |
|---|---|---|
| F1 | The repository is an unmodified fork of `qeeqbox/social-analyzer` (0 ahead / 0 behind). | `gh api …/compare/qeeqbox:main...main` |
| F2 | No skills/agents catalog, business definitions, approval gates, scheduler or worker exist in the repo, the sandbox, or the owner's other 25 GitHub repos (all upstream forks). | repo grep, `gh repo list` |
| F3 | Pages, Google Drive and Presentations connectors are not available in this environment. | tool inventory |
| F4 | The product works, but **all scans silently fail** under TLS interception because Node ignores the OS trust store (`UNABLE_TO_VERIFY_LEAF_SIGNATURE`). With `NODE_EXTRA_CA_CERTS` set, `johndoe@github` detects at 100 %. | manual run + readiness check |
| F5 | `npm install` fails at the geckodriver postinstall for the same TLS reason; `--ignore-scripts` installs everything else. Slow mode (webdriver) and OCR are unavailable here. | npm log |
| F6 | `.github/workflows/main.yml` is qeeqbox's auto-commit updater (`git push` on every push). It is upstream tooling, not an owner gate. | workflow file |

## Decisions
| ID | Decision | Rationale | Alternatives rejected |
|---|---|---|---|
| D1 | Treat the business as a **Digital Footprint Reports** service built on social-analyzer. *Assumption — owner to confirm or rename.* | Only product in the repo; owner's other forks (sherlock, maigret, holehe) are the same product family. | Inventing multiple businesses; business-agnostic placeholders (less testable). |
| D2 | Put everything fork-owned under `agents/`; **never modify upstream files**. | Keeps the fork mergeable with upstream and keeps GitHub as the source of truth. | Adding npm scripts / editing `package.json` (would conflict with upstream). |
| D3 | Reuse `app.js` fast scan via a thin `scan.sh` wrapper instead of re-implementing detection. | Avoids duplicating the 999-site detection engine and its rating logic. | Python re-implementation; calling the GUI API. |
| D4 | Implement the four owner gates as **ledger records enforced in code**: agents cannot approve; FINAL requires `production` approved; nothing sends/spends/publishes. | Gates must be checkable, not just written down. | Prose-only policy. |
| D5 | Ledger = append-only, hash-chained JSONL committed to Git. | Tamper-evident without an external service; Git history is the second line of defence. | SQLite (binary diffs), external SaaS (not reachable). |
| D6 | Formats: Markdown for Pages, `agents/workspace/` tree for Drive, reportlab PDF for deliverables, python-pptx for decks. | Only options available here; all editable/importable later. | Waiting for connectors (blocks all value). |
| D7 | Readiness check runs one real smoke scan and briefly boots the GUI. | A readiness verdict without a live detection is not evidence. | Static checks only. |
| D8 | **No background operation claimed.** No cron/worker/webhook configured. | Instruction; nothing here is verified to run unattended. | GitHub Action scheduling (would need owner opt-in and a spending/publication decision). |
| D9 | Python deps (`reportlab`, `python-pptx`) are listed in `agents/requirements.txt`, not added to the upstream `requirements.txt`. | D2. | — |
| D10 | `sites.json_new` drift is surfaced by the readiness check but not acted on. | Detection-database updates are a product decision for the owner. | Auto-apply. |

## Open items for the owner
1. Confirm or correct D1 (business name, product, pricing — pricing is a spending/publication decision and was left as a placeholder in the sales deck).
2. Decide whether the upstream auto-commit workflow should stay enabled on this fork (F6).
3. If slow mode / OCR / search-engine lookups are to be sold, approve the related spending (firefox + geckodriver install or the docker grid; Google API key).
4. When Drive/Pages/Slides are connected, mirror `agents/workspace/` and import `.pptx` files; record the mapping as a `decision` record.
5. Set the real ledger actor names (`owner:<name>`) and commit the ledger after each session.
