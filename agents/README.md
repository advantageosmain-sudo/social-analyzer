# Skills & agents catalog (fork-owned)

Everything the business adds on top of upstream `qeeqbox/social-analyzer` lives in this directory. **Nothing outside `agents/` is modified** — the fork stays mergeable and GitHub remains the source of truth.

| | |
|---|---|
| Catalog (machine-readable) | [`catalog.json`](catalog.json) — existing product capabilities, gaps, skills, agents, gates, format mapping |
| Task & decision record | [`DECISION_RECORD.md`](DECISION_RECORD.md) |
| Implemented / tested / blocked | [`STATUS_REPORT.md`](STATUS_REPORT.md) |
| Owner approval gates | [`policies/approval-gates.md`](policies/approval-gates.md) · [`policies/permissions.md`](policies/permissions.md) |
| Working files (Drive mirror) | [`workspace/`](workspace/README.md) |
| Sample outputs | [`examples/`](examples/) |

## Skills
| Skill | Area | Entry point |
|---|---|---|
| [product-readiness-check](skills/product-readiness-check/SKILL.md) | Product Readiness | `node agents/skills/product-readiness-check/run.mjs` |
| [footprint-report-producer](skills/footprint-report-producer/SKILL.md) | Digital Product Production | `scan.sh` → `produce.py` |
| [deck-builder](skills/deck-builder/SKILL.md) | Digital Product Production | `python3 agents/skills/deck-builder/build_deck.py <outline.json>` |
| [business-records-ledger](skills/business-records-ledger/SKILL.md) | Business Records | `python3 agents/skills/business-records-ledger/ledger.py` |

## Agents
[readiness-agent](agents/readiness-agent.md) · [production-agent](agents/production-agent.md) · [records-agent](agents/records-agent.md)

## Setup
```bash
npm install --ignore-scripts          # geckodriver postinstall needs direct TLS to GitHub; skip it
pip3 install -r agents/requirements.txt
node agents/skills/product-readiness-check/run.mjs
```

## Rules in one paragraph
Agents never approve, send, publish or spend. The four gates — `production`, `publication`, `spending`, `customer_communication` — are recorded only by a human owner in the ledger, and the code refuses otherwise. No scheduler or background worker is configured; every run is a human-invoked command.
