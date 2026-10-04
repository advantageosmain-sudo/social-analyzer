# Status report — 2026-10-04

## Implemented
| Area | Capability | Files |
|---|---|---|
| Product Readiness | `product-readiness-check` skill — 19 checks (runtime, data, CLI, TLS, live scan, GUI, optional layers, source-of-truth, CI) → `readiness.{json,md}` | `agents/skills/product-readiness-check/` |
| Product Readiness | `readiness-agent` | `agents/agents/readiness-agent.md` |
| Digital Product Production | `footprint-report-producer` skill — `scan.sh` (wraps existing `app.js`) + `produce.py` (PDF + MD, DRAFT watermark until production approved, FINAL to `outbox/`) | `agents/skills/footprint-report-producer/` |
| Digital Product Production | `deck-builder` skill — JSON outline → editable `.pptx`; sales + training templates | `agents/skills/deck-builder/` |
| Digital Product Production | `production-agent` | `agents/agents/production-agent.md` |
| Business Records | `business-records-ledger` skill — append-only hash-chained ledger; engagements, approvals (4 gates), deliverables with SHA-256, decisions, expense requests; `verify` | `agents/skills/business-records-ledger/` |
| Business Records | `records-agent` | `agents/agents/records-agent.md` |
| Governance | Approval-gate policy, permission matrix, catalog (`catalog.json`), decision record, Drive-mirror workspace layout | `agents/policies/`, `agents/catalog.json`, `agents/DECISION_RECORD.md`, `agents/workspace/README.md` |

Every skill has: instructions, permission boundaries, a verification example from a real run, and an invocation prompt (in its `SKILL.md`).

## Tested (all in the Arena sandbox, 2026-10-04)
| Test | Result |
|---|---|
| `npm install --ignore-scripts`; `node app.js --help`; `python3 app.py -h` | pass |
| Live fast scan `johndoe` on `github reddit twitter` via existing CLI | pass — github detected %100.00; reddit + 2 twitter entries unreachable (reported) |
| Full `all` scan (999 sites) | ran in ≈100 s; 1 detected (accidental run during testing, output discarded) |
| Readiness check full mode | READY WITH CAVEATS (0 FAIL, 4 WARN, 15 PASS); GUI probe, scan smoke, TLS probe all exercised |
| Readiness check `--skip-network --skip-gui` | pass, exit 0 |
| Draft PDF with gate missing → watermark, `status=draft` record | pass (rendered pages inspected) |
| Agent attempts `approve` | REFUSED, exit 2 |
| Agent attempts FINAL registration without approval | REFUSED, exit 3 |
| Owner approval → FINAL PDF in `outbox/`, `status=final` record | pass |
| `customer_communication` gate remains `missing` after FINAL | pass (nothing sent) |
| Sales deck + training deck build; reopened with python-pptx (8 slides each, notes present) | pass |
| Ledger `verify` on 5 records | OK |
| Ledger tamper test (edit draft→final on a copy) | FAIL detected at the edited record |
| Upstream files untouched (`git status` shows only `agents/`) | pass |

Sample artefacts: `agents/examples/` (scan JSON, DRAFT and FINAL PDFs, FINAL markdown, both decks, readiness report).

## Blocked / not done (honest list)
| Item | Why | Unblock |
|---|---|---|
| Pages task/decision record | No Pages connector in this environment | Paste `agents/DECISION_RECORD.md` into Pages, or connect Pages and re-run |
| Google Drive organised working files | No Drive connector | Mirror `agents/workspace/` tree into Drive; keep the same folder names |
| Google Slides versions of decks | No Slides connector | Upload the `.pptx` files from `agents/examples/` / `40_Sales_Training/` |
| Slow-mode (webdriver) & OCR detection | firefox, geckodriver binary and tesseract absent; geckodriver download blocked by sandbox TLS | Owner spending/infra decision: `apt-get install firefox-esr tesseract-ocr` + `npm rebuild geckodriver`, or docker grid |
| Search-engine / metadata lookups | Need Google API key = spending gate | `expense_request` → owner `spending` approval |
| Background / scheduled operation | **None configured and none claimed.** All skills are human-invoked | If wanted: owner decision on a GitHub Action or cron, with explicit gates |
| Business identity, pricing, actor names | Owner input required (assumption D1) | Confirm in `DECISION_RECORD.md`; prices remain placeholders in the sales deck |
| Upstream auto-commit workflow | Upstream tooling pushes on every push to the fork | Owner decision to disable Actions on the fork or keep |
| Multi-business coverage | Only one business/product is evidenced in the repo | Provide names + GitHub repos for others; the catalog format is reusable |

## How to run it yourself
```bash
pip3 install -r agents/requirements.txt && npm install --ignore-scripts
node agents/skills/product-readiness-check/run.mjs
L=agents/skills/business-records-ledger/ledger.py
python3 $L add engagement --actor owner:<you> -f customer="…" -f subject=<username> -f purpose="…" -f scope="github reddit"
agents/skills/footprint-report-producer/scan.sh <eng-id> <username> "github reddit"
python3 agents/skills/footprint-report-producer/produce.py --engagement <eng-id> --customer "…" --subject <username> --scan agents/workspace/10_Engagements/<eng-id>/scan-<username>.json
python3 $L approve <eng-id> production --actor owner:<you> --scope "report v1"      # owner only
python3 agents/skills/footprint-report-producer/produce.py …same…                    # → FINAL in outbox/
python3 agents/skills/deck-builder/build_deck.py agents/skills/deck-builder/templates/sales-deck.json
python3 $L verify
```
