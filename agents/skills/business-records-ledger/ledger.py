#!/usr/bin/env python3
"""
business-records-ledger — append-only, hash-chained business records.

Records live in agents/workspace/30_Records/ledger.jsonl (one JSON object per
line). Every record carries the SHA-256 of the previous record so tampering or
out-of-band edits are detectable with `verify`.

Record types
  engagement       a customer engagement / job (the unit everything hangs off)
  approval         an OWNER decision on a gate: production | publication |
                   spending | customer_communication  (status approved|rejected)
  deliverable      a produced artifact (path + sha256 + status draft|final)
  decision         a task / architecture / policy decision (Pages-equivalent)
  expense_request  a request to spend money (never auto-approved)
  note             free-form operational note

This tool never sends anything, never spends anything and never publishes.
It only writes to the ledger file. Owner approvals must be recorded by a human
(actor must not start with "agent:").
"""
import argparse
import datetime as _dt
import hashlib
import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DEFAULT_LEDGER = os.path.join(REPO, "agents", "workspace", "30_Records", "ledger.jsonl")

GATES = ("production", "publication", "spending", "customer_communication")
TYPES = ("engagement", "approval", "deliverable", "decision", "expense_request", "note")


def _now():
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(obj):
    return hashlib.sha256(_canon(obj).encode("utf-8")).hexdigest()


def load(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"ledger corrupt at line {n}: {exc}")
    return out


def append(path, rec_type, payload, actor, ref=None):
    if rec_type not in TYPES:
        raise SystemExit(f"unknown record type {rec_type!r}; expected one of {TYPES}")
    records = load(path)
    prev_hash = records[-1]["hash"] if records else "GENESIS"
    body = {
        "id": f"{rec_type[:3]}-{uuid.uuid4().hex[:10]}",
        "type": rec_type,
        "ts": _now(),
        "actor": actor,
        "ref": ref,
        "payload": payload,
        "prev_hash": prev_hash,
    }
    body["hash"] = _hash(body)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(_canon(body) + "\n")
    return body


def verify(path):
    records = load(path)
    prev = "GENESIS"
    for i, rec in enumerate(records):
        stored = rec.get("hash")
        check = {k: v for k, v in rec.items() if k != "hash"}
        if rec.get("prev_hash") != prev:
            return False, f"record {i} ({rec.get('id')}) prev_hash mismatch"
        if _hash(check) != stored:
            return False, f"record {i} ({rec.get('id')}) content hash mismatch"
        prev = stored
    return True, f"{len(records)} records verified, chain intact"


def gate_status(path, engagement_id, gate):
    """Return the latest OWNER decision for a gate on an engagement."""
    if gate not in GATES:
        raise SystemExit(f"unknown gate {gate!r}; expected one of {GATES}")
    latest = None
    for rec in load(path):
        if rec["type"] != "approval" or rec.get("ref") != engagement_id:
            continue
        if rec["payload"].get("gate") != gate:
            continue
        latest = rec
    if latest is None:
        return {"gate": gate, "engagement": engagement_id, "status": "missing"}
    return {
        "gate": gate,
        "engagement": engagement_id,
        "status": latest["payload"].get("status"),
        "approval_id": latest["id"],
        "actor": latest["actor"],
        "ts": latest["ts"],
        "scope": latest["payload"].get("scope"),
    }


def sha256_file(fp):
    h = hashlib.sha256()
    with open(fp, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _kv(pairs):
    out = {}
    for p in pairs or []:
        if "=" not in p:
            raise SystemExit(f"expected key=value, got {p!r}")
        k, v = p.split("=", 1)
        out[k] = v
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER, help="ledger path (default: workspace/30_Records/ledger.jsonl)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="append a record")
    a.add_argument("type", choices=TYPES)
    a.add_argument("--actor", required=True, help="who is recording, e.g. owner:jane or agent:production-agent")
    a.add_argument("--ref", help="related record id (usually an engagement id)")
    a.add_argument("-f", "--field", action="append", default=[], metavar="KEY=VALUE", help="payload field (repeatable)")

    ap_ = sub.add_parser("approve", help="record an OWNER decision on a gate")
    ap_.add_argument("engagement")
    ap_.add_argument("gate", choices=GATES)
    ap_.add_argument("--status", choices=("approved", "rejected"), default="approved")
    ap_.add_argument("--actor", required=True, help="must be a human, e.g. owner:jane")
    ap_.add_argument("--scope", default="", help="what exactly is approved (file, amount, recipient...)")
    ap_.add_argument("--note", default="")

    g = sub.add_parser("gate", help="show latest decision on a gate")
    g.add_argument("engagement")
    g.add_argument("gate", choices=GATES)

    d = sub.add_parser("deliverable", help="register a produced file (hash recorded)")
    d.add_argument("engagement")
    d.add_argument("path")
    d.add_argument("--status", choices=("draft", "final"), default="draft")
    d.add_argument("--actor", required=True)
    d.add_argument("--kind", default="pdf")

    l = sub.add_parser("list", help="list records")
    l.add_argument("--type", choices=TYPES)
    l.add_argument("--ref")
    l.add_argument("--json", action="store_true")

    sub.add_parser("verify", help="verify hash chain")

    args = ap.parse_args(argv)
    path = args.ledger

    if args.cmd == "add":
        rec = append(path, args.type, _kv(args.field), args.actor, args.ref)
        print(json.dumps(rec, indent=2))
        return 0

    if args.cmd == "approve":
        if args.actor.startswith("agent:") or args.actor.startswith("bot:"):
            print("REFUSED: gate approvals must be recorded by a human owner actor (e.g. owner:jane).", file=sys.stderr)
            return 2
        payload = {"gate": args.gate, "status": args.status, "scope": args.scope, "note": args.note}
        rec = append(path, "approval", payload, args.actor, args.engagement)
        print(json.dumps(rec, indent=2))
        return 0

    if args.cmd == "gate":
        print(json.dumps(gate_status(path, args.engagement, args.gate), indent=2))
        return 0

    if args.cmd == "deliverable":
        if not os.path.exists(args.path):
            raise SystemExit(f"no such file: {args.path}")
        if args.status == "final":
            gs = gate_status(path, args.engagement, "production")
            if gs["status"] != "approved":
                print(f"REFUSED: cannot register FINAL deliverable; production gate is {gs['status']} for {args.engagement}.", file=sys.stderr)
                return 3
        rel = os.path.relpath(os.path.abspath(args.path), REPO)
        payload = {"path": rel, "sha256": sha256_file(args.path), "status": args.status, "kind": args.kind,
                   "bytes": os.path.getsize(args.path)}
        rec = append(path, "deliverable", payload, args.actor, args.engagement)
        print(json.dumps(rec, indent=2))
        return 0

    if args.cmd == "list":
        recs = load(path)
        if args.type:
            recs = [r for r in recs if r["type"] == args.type]
        if args.ref:
            recs = [r for r in recs if r.get("ref") == args.ref or r.get("id") == args.ref]
        if args.json:
            print(json.dumps(recs, indent=2))
        else:
            for r in recs:
                summary = ", ".join(f"{k}={v}" for k, v in list(r["payload"].items())[:4])
                print(f"{r['ts']}  {r['id']:<16} {r['type']:<16} {r['actor']:<24} ref={r.get('ref') or '-':<16} {summary}")
        return 0

    if args.cmd == "verify":
        ok, msg = verify(path)
        print(("OK: " if ok else "FAIL: ") + msg)
        return 0 if ok else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
