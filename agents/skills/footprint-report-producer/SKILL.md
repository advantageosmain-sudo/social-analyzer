# Skill: footprint-report-producer

**Area:** Digital Product Production · **Owner approval gates touched:** `production` (read/enforce only), `customer_communication` (never crossed) · **Status:** implemented & tested

## Purpose
Turn a social-analyzer scan into the sellable unit of this business: a customer-facing **Digital Footprint Report (PDF + Markdown source)**. The report is DRAFT until the owner approves production in the ledger; it is never sent by this skill.

## Reuses (does not duplicate)
- `scan.sh` calls the **existing** `app.js --output json` CLI. No detection, rating or site logic is reimplemented.
- `ledger.py` (business-records-ledger) for gate lookup and deliverable registration.

## Instructions
1. Open or locate the engagement (`eng-…`) in the ledger (see business-records-ledger).
2. Scan with the existing CLI:
   ```bash
   agents/skills/footprint-report-producer/scan.sh <eng-id> <username> "github reddit twitter"   # or "all" (≈100 s, 999 sites)
   ```
   → `agents/workspace/10_Engagements/<eng-id>/scan-<username>.json` (+ raw log).
3. Produce the report:
   ```bash
   python3 agents/skills/footprint-report-producer/produce.py \
     --engagement <eng-id> --customer "Acme Legal" --subject <username> \
     --scan agents/workspace/10_Engagements/<eng-id>/scan-<username>.json --analyst "Jane Doe"
   ```
   - Production gate **missing/rejected** → `20_Deliverables/<eng-id>/…-DRAFT.pdf` with a diagonal *DRAFT — INTERNAL REVIEW* watermark; ledger `deliverable` record `status=draft`.
   - Production gate **approved** → `20_Deliverables/<eng-id>/outbox/…-FINAL.pdf`; ledger record `status=final`.
4. Human review of Medium/Low bands before asking the owner for approval.
5. Delivery to the customer is a **separate human step** behind the `customer_communication` gate.

Report contents: cover, summary with confidence bands (High ≥90 / Medium 50–89 / Low <50), detected-profile table (link, rate, title), inconclusive/unreachable table, method & limitations, use restrictions, footer with engagement id and status on every page.

## Permission boundaries
- MAY: run `node app.js` fast scans, read/write under `agents/workspace/10_Engagements/<eng-id>/` and `agents/workspace/20_Deliverables/<eng-id>/`, append `deliverable` records to the ledger.
- MAY NOT: record approvals, mark anything FINAL without an approved production gate, e-mail/upload/post the report, use `--mode slow` or `--metadata`/Google API paths without owner instruction (webdriver & API keys are environment/spend decisions), scan identifiers that lack an engagement with a stated lawful purpose.
- Sets `NODE_EXTRA_CA_CERTS` to the system bundle when unset; it does not disable TLS verification.

## Verification example (run 2026-10-04, real scan)
```
$ ledger.py add engagement --actor owner:demo -f customer="Example Legal LLP" -f subject=johndoe -f purpose="pre-litigation identity corroboration" -f scope="github reddit twitter"
  "id": "eng-001cee7bf7"
$ scan.sh eng-001cee7bf7 johndoe "github reddit twitter"
scan saved -> …/10_Engagements/eng-001cee7bf7/scan-johndoe.json  detected=1 unknown=0 failed=3
$ produce.py --engagement eng-001cee7bf7 --customer "Example Legal LLP" --subject johndoe --scan … 
status     : DRAFT — INTERNAL REVIEW
pdf        : agents/workspace/20_Deliverables/eng-001cee7bf7/footprint-report-johndoe-2026-10-04-DRAFT.pdf
ledger rec : del-f13b6a2b4a  (production gate = missing)
$ ledger.py approve eng-001cee7bf7 production --actor agent:production-agent
REFUSED: gate approvals must be recorded by a human owner actor            (exit 2)
$ ledger.py approve eng-001cee7bf7 production --actor owner:demo --scope "footprint report johndoe v1"
  "id": "app-23d4990b2c", "status": "approved"
$ produce.py … (same arguments)
status     : FINAL
pdf        : agents/workspace/20_Deliverables/eng-001cee7bf7/outbox/footprint-report-johndoe-2026-10-04-FINAL.pdf
$ ledger.py gate eng-001cee7bf7 customer_communication   →  "status": "missing"
```
Detected: `https://github.com/johndoe` (%100.00, title "johndoe · GitHub"). Reddit and the two Twitter entries were unreachable in fast mode — reported, not hidden. Sample outputs are kept in `agents/examples/`.

## Invocation prompt
> Using the footprint-report-producer skill, open an engagement for customer "<name>" with purpose "<lawful purpose>", scan identifier "<username>" on sites "<list or all>", and produce the DRAFT report. Summarise the detected profiles by confidence band and list what a human must corroborate. Do not request or record approval, and do not send anything.
