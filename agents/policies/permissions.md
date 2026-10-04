# Permission matrix

Legend: ✅ allowed · ⛔ forbidden · 🔒 only after the named owner gate is `approved` in the ledger · — not applicable

| Capability / resource | product-readiness-check | footprint-report-producer | deck-builder | business-records-ledger |
|---|---|---|---|---|
| Read repo files | ✅ | ✅ | ✅ | ✅ |
| Modify upstream product files (`app.js`, `modules/`, `data/`, `public/`, `package.json`, …) | ⛔ | ⛔ | ⛔ | ⛔ |
| Write under `agents/workspace/` | `10_Engagements/_readiness/` | `10_Engagements/<eng>/`, `20_Deliverables/<eng>/` | `40_Sales_Training/` | `30_Records/ledger.jsonl` (append) |
| Spawn `node app.js` fast scan | ✅ one smoke scan | ✅ per engagement | — | — |
| `--mode slow` (webdriver / grid) | ⛔ | 🔒 spending (infra) + owner instruction | — | — |
| `--metadata`, Google/DuckDuckGo API | ⛔ | 🔒 spending | — | — |
| Outbound HTTPS | github.com HEAD only | target sites via existing CLI | ⛔ | ⛔ |
| Install packages / change env | ⛔ | ⛔ (sets `NODE_EXTRA_CA_CERTS` for its own process only) | ⛔ | ⛔ |
| Append `deliverable` record | — | ✅ draft; 🔒 production for final | ✅ draft | ✅ draft; 🔒 production for final |
| Append `approval` record | ⛔ | ⛔ | ⛔ | human owner only |
| Edit/delete ledger records | ⛔ | ⛔ | ⛔ | ⛔ (no such command) |
| Mark deliverable FINAL | — | 🔒 production | ⛔ | 🔒 production |
| Send e-mail / upload / post / publish | ⛔ | ⛔ | ⛔ | ⛔ |
| Spend money / hold credentials | ⛔ | ⛔ | ⛔ | ⛔ |
| `git commit` / `git push` | ⛔ | ⛔ | ⛔ | ⛔ (humans commit the ledger) |
| Run unattended / scheduled | ⛔ | ⛔ | ⛔ | ⛔ |

Agents (`agents/agents/*.md`) inherit exactly the union of the skills they are allowed to call — nothing more.
