# Workspace — Google Drive mirror

This tree is the local, Git-tracked equivalent of the intended Google Drive layout. Drive sync is **not** configured from this environment; when it is, mirror the same folder names so paths in the ledger stay meaningful.

```
agents/workspace/
├── 00_Inbox/            # customer requests, raw identifiers awaiting an engagement record
├── 10_Engagements/      # one folder per eng-id: scan JSON, raw logs, review notes
│   └── _readiness/      # latest readiness.json / readiness.md
├── 20_Deliverables/     # one folder per eng-id
│   └── <eng-id>/        #   DRAFT files here …
│       └── outbox/      #   … FINAL files here, awaiting human delivery (customer_communication gate)
├── 30_Records/          # ledger.jsonl (append-only, hash-chained)
├── 40_Sales_Training/   # editable .pptx decks (draft until publication gate)
└── 90_Archive/          # closed engagements (moved by a human)
```

Tracked in Git: this README, folder placeholders, the ledger, and the readiness report. Scan outputs and deliverables are ignored by `agents/.gitignore` except the curated copies in `agents/examples/`.
