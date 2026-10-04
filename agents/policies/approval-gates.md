# Owner approval gates

These four gates existed as working rules before this catalog; this document makes them explicit and the ledger makes them enforceable. **Only a human owner records a gate decision** (`ledger.py approve … --actor owner:<name>`); the ledger refuses `agent:`/`bot:` actors.

| Gate | Guards | Recorded how | Enforced where |
|---|---|---|---|
| `production` | Turning a draft into a FINAL customer deliverable | `ledger.py approve <eng> production` | `produce.py` (DRAFT watermark until approved), `ledger.py deliverable --status final` (refused, exit 3) |
| `publication` | Any public or customer-visible release of collateral: decks, web copy, README changes, pricing | `ledger.py approve <eng> publication` | Deck footers default to draft; no skill uploads or posts anything |
| `spending` | Any money: API keys/quotas (Google Custom Search), cloud/Selenium grid, paid data, subscriptions | `expense_request` record → `approve <eng> spending` | No skill holds credentials or purchasing ability; `--metadata`/Google API paths are off by default |
| `customer_communication` | Sending anything to a customer or subject: report delivery, status mails, quotes | `approve <eng> customer_communication` | No skill has e-mail/upload/chat capability; FINAL files only land in `outbox/` for a human to send |

## Non-negotiables for agents
1. An agent may **ask** for a gate (append an `expense_request`, `note` or `decision` record) but never **grant** one.
2. "Approved" means a ledger `approval` record with `status=approved` whose `scope` covers the action. Verbal/ chat approval is not sufficient until recorded.
3. A gate approval is per engagement and per scope; re-approval is needed for a new version of a deliverable.
4. If a gate's status is `rejected`, agents stop and report; they do not retry with changed wording.
5. No scheduler, cron, webhook or worker is configured by this catalog. **Nothing runs in the background.** Every run is a human-invoked command. (The upstream GitHub Action in `.github/workflows/main.yml` is qeeqbox's detection auto-updater; it is not an approval mechanism and the readiness check flags it.)

## Lawful-purpose rule (product-specific)
No scan is run unless an `engagement` record states the customer and a lawful purpose. Reports carry a use-restriction section. Agents refuse identifiers that appear to target minors, intimate partners or anyone where the purpose suggests harassment, and escalate to the owner.
