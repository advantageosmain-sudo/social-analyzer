# Skill: business-records-ledger

**Area:** Business Records · **Owner approval gates:** this skill *is* where the four gates are recorded — `production`, `publication`, `spending`, `customer_communication` · **Status:** implemented & tested

## Purpose
A single, append-only, hash-chained record of engagements, owner approvals, deliverables (with SHA-256), decisions and expense requests. It gives every other skill a place to check "is this allowed yet?" and gives the owner a tamper-evident audit trail without any external service.

Ledger file: `agents/workspace/30_Records/ledger.jsonl` (one JSON object per line; each record stores the hash of the previous one).

## Instructions
```bash
L=agents/skills/business-records-ledger/ledger.py
python3 $L add engagement --actor owner:jane -f customer="Acme" -f subject=johndoe -f purpose="…lawful purpose…" -f scope="all"
python3 $L add decision   --actor owner:jane -f topic="pricing" -f decision="…" -f rationale="…"
python3 $L add expense_request --actor agent:production-agent --ref eng-xxxx -f item="Google Custom Search quota" -f amount_usd=25
python3 $L approve eng-xxxx production --actor owner:jane --scope "report v1"            # or --status rejected
python3 $L approve eng-xxxx spending  --actor owner:jane --scope "USD 25 Google CSE"
python3 $L gate   eng-xxxx customer_communication                                      # → missing | approved | rejected
python3 $L deliverable eng-xxxx path/to/file.pdf --status draft --actor agent:production-agent
python3 $L list [--type approval] [--ref eng-xxxx] [--json]
python3 $L verify                                                                       # exit 1 on any tampering
```
Record ids are prefixed by type (`eng-`, `app-`, `del-`, `dec-`, `exp-`, `not-`). Actors are free text but **gate approvals are refused for actors starting with `agent:` or `bot:`**.

## Permission boundaries
- MAY: append records; read records; compute file hashes.
- MAY NOT: edit or delete records (there is no command for it — fix mistakes by appending a correcting record), approve gates as an agent, register a `final` deliverable while the production gate is not approved (exit 3), spend, send, or publish anything.
- Ledger integrity is only as good as the file's protection: keep it in Git (it is committed) so history shows any rewrite.

## Verification example (2026-10-04)
```
$ ledger.py approve eng-001cee7bf7 production --actor agent:production-agent
REFUSED: gate approvals must be recorded by a human owner actor (e.g. owner:jane).        exit=2
$ ledger.py deliverable eng-001cee7bf7 …DRAFT.pdf --status final --actor agent:production-agent
REFUSED: cannot register FINAL deliverable; production gate is missing for eng-001cee7bf7.  exit=3
$ ledger.py verify
OK: 5 records verified, chain intact
$ cp ledger.jsonl /tmp/t.jsonl && sed -i '2s/"status":"draft"/"status":"final"/' /tmp/t.jsonl && ledger.py --ledger /tmp/t.jsonl verify
FAIL: record 1 (del-f13b6a2b4a) content hash mismatch                                        exit=1
```

## Invocation prompt
> Using the business-records-ledger skill, list every engagement with its latest status on all four gates and any deliverables registered against it, then run verify and report the result. Do not record any approvals — only the owner does that.
