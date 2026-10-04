#!/usr/bin/env bash
# footprint-report-producer/scan.sh — run the EXISTING social-analyzer CLI and
# store its JSON in the engagement folder. No detection logic is reimplemented.
#
# Usage: agents/skills/footprint-report-producer/scan.sh <engagement-id> <username[,username2]> [websites|"all"] [extra app.js args...]
# Example: agents/skills/footprint-report-producer/scan.sh eng-abc123 johndoe "github reddit"
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
ENG="${1:?engagement id required}"; USER_="${2:?username required}"; SITES="${3:-all}"; shift 3 || shift $#
OUT_DIR="$REPO/agents/workspace/10_Engagements/$ENG"
mkdir -p "$OUT_DIR"
SAFE="$(printf '%s' "$USER_" | tr -c 'A-Za-z0-9_,.-' '_')"
RAW="$OUT_DIR/scan-${SAFE}.raw.txt"; JSON="$OUT_DIR/scan-${SAFE}.json"

# Node ignores the OS trust store; in TLS-intercepting environments scans fail
# with UNABLE_TO_VERIFY_LEAF_SIGNATURE unless the system bundle is supplied.
if [ -z "${NODE_EXTRA_CA_CERTS:-}" ] && [ -f /etc/ssl/certs/ca-certificates.crt ]; then
  export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
fi

cd "$REPO"
node app.js --username "$USER_" --websites "$SITES" --output json --options "link,rate,title" \
  --profiles all --filter all --method all "$@" > "$RAW" 2>&1 || true

# stdout mixes log lines with the JSON document; keep the outermost object.
python3 - "$RAW" "$JSON" "$USER_" "$SITES" <<'PY'
import json, sys, datetime
raw, out, user, sites = sys.argv[1:5]
txt = open(raw, encoding="utf-8", errors="replace").read()
i, j = txt.find("{"), txt.rfind("}")
if i < 0 or j < 0:
    sys.exit(f"no JSON found in {raw}")
doc = json.loads(txt[i:j+1])
doc["_meta"] = {"username": user, "websites": sites, "tool": "social-analyzer (node app.js, fast mode)",
                "captured": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()}
json.dump(doc, open(out, "w", encoding="utf-8"), indent=2)
print(f"scan saved -> {out}  detected={len(doc.get('detected', []))} unknown={len(doc.get('unknown', []))} failed={len(doc.get('failed', []))}")
PY
